"""
app/services/market_chatgpt/workflows.py

LangGraph workflow for the Market ChatGPT 2.0 research assistant.

Graph: market_research

Node flow:
  router → [portfolio_retrieval?] → knowledge_graph_search
         → vector_search → synthesiser → END

The router decides whether to start with portfolio context (if holdings
are provided) or jump straight to knowledge graph search.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.services.market_chatgpt.models import (
    QueryRequest,
    QueryResponse,
    SourceReference,
)
from app.services.market_chatgpt.tools import (
    fetch_portfolio,
    query_knowledge_graph,
    search_vector_db,
)


# ── State schema ───────────────────────────────────────────────────────────────

class ResearchState(TypedDict):
    request: QueryRequest
    portfolio_context: list[dict]
    graph_results: list[dict]
    vector_results: list[dict]
    reasoning_steps: list[str]
    answer: str
    sources: list[SourceReference]
    portfolio_context_used: bool


# ── Node implementations ───────────────────────────────────────────────────────

async def portfolio_retrieval(state: ResearchState) -> ResearchState:
    """
    Fetch and inject the user's portfolio context so that downstream
    retrieval steps can prioritise holdings.

    # TODO: Call fetch_portfolio tool and filter vector / graph results to
    #       prioritise symbols present in the portfolio.
    """
    request = state["request"]
    if request.portfolio:
        portfolio_data = [h.model_dump() for h in request.portfolio]
    else:
        result = await fetch_portfolio.ainvoke({"user_id": request.user_id})
        portfolio_data = result

    steps = state["reasoning_steps"] + [
        f"Retrieved portfolio: {len(portfolio_data)} holdings"
    ]
    return {**state, "portfolio_context": portfolio_data, "reasoning_steps": steps, "portfolio_context_used": True}


async def knowledge_graph_search(state: ResearchState) -> ResearchState:
    """
    Query the Neo4j causal graph to find entities and relationships relevant
    to the user's question.

    # TODO: Use the LLM to generate an appropriate Cypher query from the
    #       user's natural-language question.
    # TODO: If portfolio context is available, bias the Cypher query towards
    #       the user's holdings.
    """
    query = state["request"].query
    cypher = f"MATCH (c:Company) WHERE c.name CONTAINS '{query[:30]}' RETURN c LIMIT 5"
    # TODO: generate real Cypher via LLM
    graph_results = await query_knowledge_graph.ainvoke({"cypher_query": cypher})
    steps = state["reasoning_steps"] + [f"Queried knowledge graph: {len(graph_results)} results"]
    return {**state, "graph_results": graph_results, "reasoning_steps": steps}


async def vector_search(state: ResearchState) -> ResearchState:
    """
    Perform a semantic search over the news/filings vector index.

    # TODO: Bias search towards portfolio holdings when portfolio_context_used is True.
    """
    query_text = state["request"].query
    results = await search_vector_db.ainvoke({"query_text": query_text, "top_k": 5})
    steps = state["reasoning_steps"] + [f"Vector search: {len(results)} chunks retrieved"]
    return {**state, "vector_results": results, "reasoning_steps": steps}


async def synthesiser(state: ResearchState) -> ResearchState:
    """
    Synthesise a final answer from all retrieved context using the LLM.

    # TODO: Construct a prompt that includes:
    #         - the user's question,
    #         - portfolio holdings (if any),
    #         - Neo4j graph results,
    #         - vector search chunks,
    #       and call the configured LLM to produce a grounded answer.
    # TODO: Extract and format source references from the retrieved context.
    """
    sources: list[SourceReference] = []
    for chunk in state["vector_results"]:
        sources.append(
            SourceReference(
                title=chunk.get("text", "")[:60],
                source_type="vector_chunk",
                relevance_score=chunk.get("score", 0.0),
                snippet=chunk.get("text", ""),
            )
        )

    answer = (
        "[STUB] LLM synthesis not yet implemented. "
        f"Retrieved {len(state['graph_results'])} graph results and "
        f"{len(state['vector_results'])} vector chunks for query: "
        f"'{state['request'].query[:80]}'"
    )
    steps = state["reasoning_steps"] + ["Synthesised final answer"]
    return {**state, "answer": answer, "sources": sources, "reasoning_steps": steps}


# ── Router ─────────────────────────────────────────────────────────────────────

def _router(state: ResearchState) -> str:
    """Route to portfolio_retrieval if no portfolio was provided, else skip."""
    if not state["request"].portfolio:
        return "portfolio_retrieval"
    return "knowledge_graph_search"


# ── Build graph ────────────────────────────────────────────────────────────────

def build_market_research_graph() -> Any:
    """
    Compile the market_research LangGraph workflow.

    Topology:
        START → router → portfolio_retrieval → knowledge_graph_search
                       → knowledge_graph_search (direct, if portfolio provided)
        knowledge_graph_search → vector_search → synthesiser → END
    """
    graph = StateGraph(ResearchState)

    graph.add_node("portfolio_retrieval", portfolio_retrieval)
    graph.add_node("knowledge_graph_search", knowledge_graph_search)
    graph.add_node("vector_search", vector_search)
    graph.add_node("synthesiser", synthesiser)

    graph.set_conditional_entry_point(
        _router,
        {
            "portfolio_retrieval": "portfolio_retrieval",
            "knowledge_graph_search": "knowledge_graph_search",
        },
    )
    graph.add_edge("portfolio_retrieval", "knowledge_graph_search")
    graph.add_edge("knowledge_graph_search", "vector_search")
    graph.add_edge("vector_search", "synthesiser")
    graph.add_edge("synthesiser", END)

    return graph.compile()


market_research_graph = build_market_research_graph()


async def run_market_research(request: QueryRequest) -> QueryResponse:
    """
    Invoke the market_research LangGraph and return a QueryResponse.

    This is the primary entry point called by the API layer.
    """
    initial_state: ResearchState = {
        "request": request,
        "portfolio_context": [],
        "graph_results": [],
        "vector_results": [],
        "reasoning_steps": [],
        "answer": "",
        "sources": [],
        "portfolio_context_used": bool(request.portfolio),
    }

    final_state = await market_research_graph.ainvoke(initial_state)

    return QueryResponse(
        query_id=str(uuid.uuid4()),
        answer=final_state["answer"],
        reasoning_steps=final_state["reasoning_steps"],
        sources=final_state["sources"],
        portfolio_context_used=final_state["portfolio_context_used"],
        created_at=datetime.utcnow(),
    )
