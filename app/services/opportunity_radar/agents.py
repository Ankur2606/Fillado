"""
app/services/opportunity_radar/agents.py

LangGraph agent definitions for the Opportunity Radar pipeline:
  - HyperLocalScout   : ingests and classifies raw events from sources.
  - VerificationAgent : cross-references events against multiple sources
                        and assigns a confidence score.
  - CausalMapper      : maps verified events to a causal chain of
                        affected companies via the Neo4j knowledge graph.

The three agents are wired into a stateful LangGraph workflow below.
"""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, StateGraph

from app.services.opportunity_radar.models import Alert, Event, SignalStrength


# ── Shared state schema ────────────────────────────────────────────────────────

class RadarState(TypedDict):
    """Mutable state passed between Opportunity Radar agents."""

    raw_payload: dict          # Raw ingested payload from an ingestion source
    event: Event | None        # Structured event after HyperLocalScout
    verified: bool             # Whether VerificationAgent confirmed the event
    confidence_score: float    # Confidence assigned by VerificationAgent
    alert: Alert | None        # Final alert produced by CausalMapper


# ── Agent node implementations ─────────────────────────────────────────────────

async def hyper_local_scout(state: RadarState) -> RadarState:
    """
    HyperLocalScout: Parses a raw ingestion payload into a structured Event.

    Steps:
      1. Detect language (and translate if vernacular).
      2. Classify event type using the LLM.
      3. Extract affected company tickers.
      4. Persist the raw event to the vector DB for future similarity search.

    # TODO: Call the configured LLM to classify event_type and extract entities.
    # TODO: Use the vector_client to embed and upsert the event.
    # TODO: Handle multi-language input (vernacular news).
    """
    import uuid
    from datetime import datetime

    from app.services.opportunity_radar.models import EventType

    payload = state["raw_payload"]
    event = Event(
        event_id=str(uuid.uuid4()),
        event_type=EventType.OTHER,  # TODO: LLM classification
        headline=payload.get("title", ""),
        summary=payload.get("title", ""),  # TODO: LLM summarisation
        source_url=payload.get("url"),
        language=payload.get("language", "en"),
        detected_at=datetime.utcnow(),
        companies_affected=[],          # TODO: NER / LLM entity extraction
        confidence_score=0.0,
    )
    return {**state, "event": event}


async def verification_agent(state: RadarState) -> RadarState:
    """
    VerificationAgent: Cross-references an event against multiple sources
    and assigns a confidence score.

    Steps:
      1. Query the Neo4j graph for related historical events.
      2. Search the vector DB for similar past events.
      3. Use the LLM to assess credibility and assign a confidence score.

    # TODO: Query Neo4j via neo4j_client to find related company nodes.
    # TODO: Use vector_client.similarity_search() to find similar past events.
    # TODO: Call the LLM to synthesise a final confidence score (0–1).
    """
    event = state["event"]
    if event is None:
        return {**state, "verified": False, "confidence_score": 0.0}

    # TODO: Real verification logic
    confidence = 0.5  # placeholder
    verified = confidence >= 0.4
    event.confidence_score = confidence
    return {**state, "event": event, "verified": verified, "confidence_score": confidence}


async def causal_mapper(state: RadarState) -> RadarState:
    """
    CausalMapper: Maps a verified event to a causal chain of affected companies
    using the Neo4j knowledge graph, then produces a trade Alert.

    Steps:
      1. Run a Cypher traversal from the primary company node to find
         downstream suppliers, customers, and competitors.
      2. Determine signal direction (bullish / bearish) via LLM reasoning.
      3. Construct and persist the Alert to PostgreSQL.
      4. Publish the alert to the Redis pub/sub channel for real-time delivery.

    # TODO: Implement Cypher traversal in neo4j_client.
    # TODO: Use LLM to determine bullish/bearish direction from event + graph context.
    # TODO: Persist Alert to PostgreSQL via the postgres module.
    # TODO: Publish to Redis pub/sub channel 'alerts'.
    """
    import uuid
    from datetime import datetime

    event = state["event"]
    if not state["verified"] or event is None:
        return {**state, "alert": None}

    alert = Alert(
        alert_id=str(uuid.uuid4()),
        event=event,
        symbol=event.companies_affected[0] if event.companies_affected else "UNKNOWN",
        signal_strength=SignalStrength.MEDIUM,  # TODO: derive from confidence
        direction="neutral",                     # TODO: LLM direction reasoning
        reasoning="[STUB] Causal mapping not yet implemented.",
        created_at=datetime.utcnow(),
    )
    return {**state, "alert": alert}


# ── LangGraph workflow ─────────────────────────────────────────────────────────

def _should_proceed_after_verification(state: RadarState) -> str:
    """Conditional edge: only map causality for verified events."""
    return "causal_mapper" if state["verified"] else END


def build_radar_graph() -> Any:
    """
    Builds and compiles the Opportunity Radar LangGraph workflow.

    Graph topology:
        hyper_local_scout → verification_agent →[if verified]→ causal_mapper → END
                                                →[if not verified]→ END
    """
    graph = StateGraph(RadarState)

    graph.add_node("hyper_local_scout", hyper_local_scout)
    graph.add_node("verification_agent", verification_agent)
    graph.add_node("causal_mapper", causal_mapper)

    graph.set_entry_point("hyper_local_scout")
    graph.add_edge("hyper_local_scout", "verification_agent")
    graph.add_conditional_edges(
        "verification_agent",
        _should_proceed_after_verification,
        {"causal_mapper": "causal_mapper", END: END},
    )
    graph.add_edge("causal_mapper", END)

    return graph.compile()


# Singleton compiled graph (import and invoke from API layer)
radar_graph = build_radar_graph()
