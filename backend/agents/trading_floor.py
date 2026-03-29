"""
backend/agents/trading_floor.py

LangGraph multi-agent debate:
  - retail_trader  (Groq llama-3.3-70b-versatile) — bullish retail sentiment
  - whale_trader   (Groq llama-3.3-70b-versatile + execute_graphrag_query tool)
  - contrarian     (Groq llama-3.3-70b-versatile + execute_graphrag_query tool)
  - synthesis      (Groq llama-3.3-70b-versatile, summarises + writes causal link)

State keys: messages, topic, current_speaker, turn_count, graph_context,
            hallucination_detected, mcp_tool_called, final_signal, causal_chain
"""
import json
import logging
import asyncio
from typing import TypedDict, Annotated, AsyncIterator
import operator

from langgraph.graph import StateGraph, END
from groq import AsyncGroq

from backend.core.config import get_settings
from backend.mcp_server.tools.read_tools import (
    execute_graphrag_query,
    fetch_et_news_mock,
    get_nse_price_mock,
)
from backend.mcp_server.tools.write_tools import append_causal_link
from backend.middleware.thought_policeman import ThoughtPoliceman

logger = logging.getLogger(__name__)

MAX_TURNS = 3  # total debate cycles (each cycle = all 3 personas speak once)


# ---------------------------------------------------------------------------
# LangGraph State
# ---------------------------------------------------------------------------

class DebateState(TypedDict):
    messages: Annotated[list[dict], operator.add]   # accumulated transcript
    topic: str                                        # original vernacular event
    current_speaker: str                              # retail | whale | contrarian | synthesis
    turn_count: int                                   # incremented each FULL cycle
    graph_context: dict                               # GraphRAG result
    hallucination_detected: bool
    mcp_tool_called: str                              # which MCP tool was invoked
    final_signal: dict                                # trading alert from synthesis
    causal_chain: list[dict]                          # causal links discovered


# ---------------------------------------------------------------------------
# Groq client factory
# ---------------------------------------------------------------------------

def _groq_client() -> AsyncGroq:
    return AsyncGroq(api_key=get_settings().groq_api_key)


# ---------------------------------------------------------------------------
# Helper: Groq streaming wrapper (collects full text and yields chunks)
# ---------------------------------------------------------------------------

async def _stream_groq(
    system: str,
    user: str,
    model: str = "llama-3.3-70b-versatile",
    max_tokens: int = 512,
) -> AsyncIterator[str]:
    """Yields text chunks from Groq streaming."""
    client = _groq_client()
    try:
        stream = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.75,
            max_tokens=max_tokens,
            stream=True,
        )
        async for chunk in stream:
            delta = chunk.choices[0].delta.content or ""
            if delta:
                yield delta
    except Exception as e:
        logger.error(f"[_stream_groq] API Error: {str(e)}")
        yield f"\n[System Error: LLM API connection failed - {str(e)}]"


async def _collect_groq(system: str, user: str, model: str = "llama-3.3-70b-versatile") -> str:
    """Collects full response (non-streaming)."""
    client = _groq_client()
    response = await client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        temperature=0.75,
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ---------------------------------------------------------------------------
# Persona system prompts
# ---------------------------------------------------------------------------

RETAIL_SYSTEM = """You are "Ravi" – an enthusiastic retail trader on Zerodha.
You believe any local disruption is a massive opportunity. You talk about momentum, delivery volumes, and social media sentiment.
Keep replies to 3-4 punchy sentences. Always mention at least one NSE ticker."""

WHALE_SYSTEM = """You are "The Whale" – an institutional fund manager handling ₹5,000 Cr.
You rely on supply-chain data, sector rotation models, and macro positioning. You always cite quantitative data from the graph.
Keep replies to 3-4 analytical sentences. Name the sector impact and specific tickers."""

CONTRARIAN_SYSTEM = """You are "Vikram" – a contrarian trader who profits from reversals.
You challenge consensus, look for the opposite trade, and highlight structural headwinds the others miss.
Keep replies to 3-4 contrarian sentences. Disagree with the last speaker and justify it with data."""

SYNTHESIS_SYSTEM = """You are the "Synthesis Agent" – you read the full debate and surface a final, objective trading signal.
Produce:
1. CONSENSUS: (BULLISH / BEARISH / NEUTRAL) with confidence %
2. PRIMARY_TICKER: top NSE ticker to watch
3. SECONDARY_TICKERS: up to 3 others
4. TIME_HORIZON: (intraday / swing / positional)
5. CAUSAL_CHAIN: one newly discovered market connection (source ➜ relationship ➜ target)
6. RATIONALE: 2-sentence summary

Format your output as valid JSON only. No markdown."""


# ---------------------------------------------------------------------------
# In-memory broadcast queue (populated by the graph runner)
# The main WebSocket handler reads from this queue.
# ---------------------------------------------------------------------------

_active_queues: list[asyncio.Queue] = []


def register_queue(q: asyncio.Queue):
    _active_queues.append(q)


def unregister_queue(q: asyncio.Queue):
    _active_queues.discard(q) if hasattr(_active_queues, 'discard') else None
    if q in _active_queues:
        _active_queues.remove(q)


async def _broadcast(message: dict):
    """Push a WebSocket message to all connected clients."""
    for q in list(_active_queues):
        try:
            q.put_nowait(message)
        except asyncio.QueueFull:
            pass


# ---------------------------------------------------------------------------
# Agent node builders
# ---------------------------------------------------------------------------

async def _run_agent_turn(
    state: DebateState,
    persona_key: str,
    persona_name: str,
    system_prompt: str,
    use_graph_tool: bool = False,
) -> DebateState:
    """Generic agent turn runner with streaming + Thought Policeman."""
    logger.info(f"========== 🎙 STARTING TURN: {persona_name} ==========")
    print(f"\n[LANGGRAPH] Executing Node for Persona: {persona_name}")

    topic = state["topic"]
    history = "\n".join(
        f"[{m['speaker']}]: {m['content']}" for m in state["messages"][-6:]
    )
    graph_ctx = json.dumps(state.get("graph_context", {}), indent=2)[:800]

    # Optionally fetch fresh GraphRAG context for whale/contrarian
    if use_graph_tool and not state.get("graph_context"):
        logger.info(f"[{persona_name}] Calling MCP tool: execute_graphrag_query")
        print(f"[{persona_name}] 🔌 Calling MCP Tool: execute_graphrag_query for topic: {topic}")
        try:
            ctx = await execute_graphrag_query(topic)
            state = {**state, "graph_context": ctx}
            await _broadcast({"type": "mcp_tool", "tool": "execute_graphrag_query", "data": ctx})
            print(f"[{persona_name}] 🔌 GraphRAG Result -> {json.dumps(ctx)[:100]}...")
        except Exception as exc:
            logger.warning(f"GraphRAG tool error: {exc}")
            print(f"[{persona_name}] ❌ GraphRAG tool failed: {exc}")

    user_prompt = f"""Event: {topic}

Recent Debate:
{history}

GraphRAG Context:
{graph_ctx}

Now give YOUR perspective as {persona_name}."""

    # --- Stream and monitor ---
    buffer = ""
    token_count = 0
    policeman = ThoughtPoliceman()
    hallucination_triggered = False

    await _broadcast({"type": "speaker_change", "speaker": persona_key})
    # Pulse Check Broadcast to verify pipe is open before LLM request
    await asyncio.sleep(0.01)
    await _broadcast({"type": "token", "speaker": persona_key, "content": " *[Groq API connecting...]* "})

    async def on_hallucination():
        nonlocal hallucination_triggered
        hallucination_triggered = True
        await _broadcast({"type": "hallucination_detected", "speaker": persona_key})
        # Force MCP tool call to ground the agent
        news = fetch_et_news_mock(query=topic)
        await _broadcast({"type": "mcp_tool", "tool": "fetch_et_news_mock", "data": news})

    try:
        async for chunk in _stream_groq(system_prompt, user_prompt):
            buffer += chunk
            token_count += 1
            await _broadcast({"type": "token", "speaker": persona_key, "content": chunk})

            # Thought Policeman check
            if not hallucination_triggered:
                await policeman.check_drift(
                    objective=topic,
                    generation_buffer=buffer,
                    on_hallucination=on_hallucination,
                    token_count=token_count,
                )
    except Exception as e:
        err_msg = f" \n🛑 **LLM Deadlock/Error**: {type(e).__name__} - {str(e)}\n "
        logger.error(f"[_run_agent_turn] {err_msg}", exc_info=True)
        print(f"[_run_agent_turn] FATAL ERROR: {err_msg}")
        buffer += err_msg
        await _broadcast({"type": "token", "speaker": persona_key, "content": err_msg})

    # If hallucination was detected, append a correction notice
    if hallucination_triggered:
        correction = "\n\n[Context corrected via MCP. Continuing with grounded data.]"
        buffer += correction
        await _broadcast({"type": "token", "speaker": persona_key, "content": correction})

    print(f"\n[{persona_name} FINISHED] Generated {token_count} tokens")
    logger.info(f"========== 🏁 END TURN: {persona_name} ==========")

    new_msg = {"speaker": persona_key, "content": buffer, "hallucinated": hallucination_triggered}
    return {
        **state,
        "messages": [new_msg],
        "current_speaker": persona_key,
        "hallucination_detected": state.get("hallucination_detected", False) or hallucination_triggered,
        "mcp_tool_called": "fetch_et_news_mock" if hallucination_triggered else state.get("mcp_tool_called", ""),
    }


# ---------------------------------------------------------------------------
# Node functions
# ---------------------------------------------------------------------------

async def retail_node(state: DebateState) -> DebateState:
    return await _run_agent_turn(state, "retail", "Retail Trader", RETAIL_SYSTEM, use_graph_tool=False)


async def whale_node(state: DebateState) -> DebateState:
    return await _run_agent_turn(state, "whale", "Whale", WHALE_SYSTEM, use_graph_tool=True)


async def contrarian_node(state: DebateState) -> DebateState:
    res = await _run_agent_turn(state, "contrarian", "Contrarian", CONTRARIAN_SYSTEM, use_graph_tool=True)
    res["turn_count"] = state.get("turn_count", 0) + 1
    return res


async def synthesis_node(state: DebateState) -> DebateState:
    """Reads the full debate and generates the final trading signal."""
    logger.info("========== 🧠 STARTING SYNTHESIS AGENT ==========")
    print("\n[LANGGRAPH] Executing Node: Synthesis Agent (Consensus Builder)")
    await _broadcast({"type": "speaker_change", "speaker": "synthesis"})

    transcript = "\n".join(
        f"[{m['speaker']}]: {m['content']}" for m in state["messages"]
    )
    graph_ctx = json.dumps(state.get("graph_context", {}), indent=2)[:1200]

    user_prompt = f"""Event: {state['topic']}

Full Debate Transcript:
{transcript}

GraphRAG Context:
{graph_ctx}

Generate the final trading signal JSON."""

    raw = await _collect_groq(SYNTHESIS_SYSTEM, user_prompt)

    # Stream the synthesis to frontend
    for ch in raw:
        await _broadcast({"type": "token", "speaker": "synthesis", "content": ch})
        await asyncio.sleep(0.005)

    # Parse signal
    signal = {}
    causal_chain = state.get("causal_chain", [])
    try:
        clean = raw.replace("```json", "").replace("```", "").strip()
        signal = json.loads(clean)
        # If synthesis found a new causal link, write it to Neo4j via MCP
        if "CAUSAL_CHAIN" in signal:
            link = signal["CAUSAL_CHAIN"]
            parts = [p.strip() for p in str(link).split("➜")]
            if len(parts) == 3:
                logger.info(f"[Synthesis] Calling MCP tool: append_causal_link with {parts}")
                print(f"[Synthesis] 🔌 Calling MCP Tool: append_causal_link -> {parts}")
                result = await append_causal_link(
                    source=parts[0], relationship=parts[1], target=parts[2]
                )
                await _broadcast({"type": "graph_update", "data": result})
                causal_chain.append({"source": parts[0], "relationship": parts[1], "target": parts[2]})
                print(f"[Synthesis] 🔌 Causal link saved successfully!")
    except Exception as exc:
        logger.warning(f"Synthesis JSON parse error: {exc}")
        signal = {"raw": raw}

    await _broadcast({"type": "synthesis_complete", "signal": signal, "causal_chain": causal_chain})

    return {
        **state,
        "messages": [{"speaker": "Synthesis", "content": raw}],
        "current_speaker": "synthesis",
        "final_signal": signal,
        "causal_chain": causal_chain,
    }


# ---------------------------------------------------------------------------
# Routing logic
# ---------------------------------------------------------------------------

def route_after_retail(state: DebateState) -> str:
    return "whale"


def route_after_whale(state: DebateState) -> str:
    return "contrarian"


def route_after_contrarian(state: DebateState) -> str:
    turn = state.get("turn_count", 0)
    if turn >= MAX_TURNS:
        return "synthesis"
    return "retail"


def increment_turn(state: DebateState) -> DebateState:
    return {**state, "turn_count": state.get("turn_count", 0) + 1}


# ---------------------------------------------------------------------------
# Build the graph
# ---------------------------------------------------------------------------

def build_trading_floor_graph():
    """Builds and compiles the LangGraph StateGraph."""
    graph = StateGraph(DebateState)

    graph.add_node("retail", retail_node)
    graph.add_node("whale", whale_node)
    graph.add_node("contrarian", contrarian_node)
    graph.add_node("synthesis", synthesis_node)

    graph.set_entry_point("retail")

    graph.add_edge("retail", "whale")
    graph.add_edge("whale", "contrarian")
    graph.add_conditional_edges(
        "contrarian",
        route_after_contrarian,
        {"retail": "retail", "synthesis": "synthesis"},
    )
    graph.add_edge("synthesis", END)

    return graph.compile()


trading_floor_graph = build_trading_floor_graph()


# ---------------------------------------------------------------------------
# Public runner
# ---------------------------------------------------------------------------

async def run_trading_floor(topic: str, graph_context: dict) -> DebateState:
    """
    Invoke the full LangGraph debate for a given vernacular event.
    Returns the final state after synthesis.
    """
    initial_state: DebateState = {
        "messages": [],
        "topic": topic,
        "current_speaker": "retail",
        "turn_count": 0,
        "graph_context": graph_context,
        "hallucination_detected": False,
        "mcp_tool_called": "",
        "final_signal": {},
        "causal_chain": [],
    }

    await _broadcast({"type": "debate_start", "topic": topic})
    final_state = await trading_floor_graph.ainvoke(initial_state)
    await _broadcast({"type": "debate_end"})
    return final_state
