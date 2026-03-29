"""
backend/main.py
FastAPI application entrypoint.

Routes:
  POST /api/trigger-event          → kick off the LangGraph debate
  GET  /api/graphrag               → standalone GraphRAG query
  GET  /api/mcp/manifest           → list MCP tools
  WS   /ws/trading-floor           → real-time streaming of debate tokens
  /mcp/tools/*                     → MCP tool endpoints (sub-router)
  /docs                            → Swagger UI
"""
import asyncio
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend.core.config import get_settings
from backend.graph.graphrag import GraphRAGTransformer
from backend.agents.trading_floor import run_trading_floor, register_queue, unregister_queue
from backend.mcp_server.server import router as mcp_router

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 Fillado backend starting up…")
    yield
    logger.info("🛑 Fillado backend shutting down…")


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Fillado – Reality-Anchored Market Intelligence",
    description="AI-native market intelligence for the Indian investor. ET GenAI Hackathon.",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount MCP router
app.include_router(mcp_router)


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class TriggerEventRequest(BaseModel):
    event: str = "Transport Strike in Gujarat – Truck operators call indefinite bandh"
    simulate_hallucination: bool = True  # intentionally triggers Thought Policeman once


class TriggerEventResponse(BaseModel):
    status: str
    event: str
    graph_context: dict
    message: str


# ---------------------------------------------------------------------------
# REST Endpoints
# ---------------------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok", "service": "fillado-backend"}


@app.post("/api/trigger-event", response_model=TriggerEventResponse, tags=["Market Events"])
async def trigger_event(req: TriggerEventRequest):
    """
    Trigger a vernacular market event.
    1. Runs GraphRAGTransformer to get causal context.
    2. Fires the LangGraph debate asynchronously (results stream via WS).
    """
    transformer = GraphRAGTransformer()
    try:
        graph_ctx = await transformer.transform(req.event)
    finally:
        transformer.close()

    async def _safe_run_trading_floor():
        try:
            await run_trading_floor(topic=req.event, graph_context=graph_ctx)
        except Exception as exc:
            logger.error(f"Trading floor task crashed: {exc}")
            from backend.agents.trading_floor import _broadcast
            await _broadcast({"type": "error", "message": f"LangGraph Error: {str(exc)}"})

    # Run debate in the background so the REST response returns immediately
    asyncio.create_task(_safe_run_trading_floor())

    return TriggerEventResponse(
        status="debate_started",
        event=req.event,
        graph_context=graph_ctx,
        message="LangGraph debate initiated. Connect to /ws/trading-floor for live stream.",
    )


@app.get("/api/graphrag", tags=["GraphRAG"])
async def graphrag_query(query: str = "Transport Strike in Gujarat"):
    """Standalone GraphRAGTransformer query (no debate)."""
    transformer = GraphRAGTransformer()
    try:
        result = await transformer.transform(query)
    finally:
        transformer.close()
    return result


@app.get("/api/mock-event", tags=["Market Events"])
async def get_mock_event():
    """Returns a sample vernacular event for the UI's pre-fill."""
    return {
        "events": [
            {
                "id": "ev-001",
                "title": "Transport Strike in Gujarat",
                "description": "Truck operators in Gujarat call indefinite bandh, Mundra port cargo movement halted.",
                "severity": "HIGH",
                "tickers": ["ADANIPORTS", "CONCOR", "GUJGASLTD"],
                "timestamp": "2024-08-15T09:30:00+05:30",
            },
            {
                "id": "ev-002",
                "title": "Hosur Factory Strike – Ashok Leyland",
                "description": "Workers at Ashok Leyland Hosur plant call strike over wage dispute.",
                "severity": "MEDIUM",
                "tickers": ["ASHOKLEY", "MRF", "APOLLOTYRE"],
                "timestamp": "2024-08-12T11:00:00+05:30",
            },
            {
                "id": "ev-003",
                "title": "Cyclone Warning – Andhra Pradesh Coast",
                "description": "IMD issues cyclone alert for AP coast, fishing and port activity suspended.",
                "severity": "HIGH",
                "tickers": ["KPITTECH", "HINDPETRO", "KARURVYSYA"],
                "timestamp": "2024-08-10T14:00:00+05:30",
            },
        ]
    }


# ---------------------------------------------------------------------------
# WebSocket
# ---------------------------------------------------------------------------

@app.websocket("/ws/trading-floor")
async def trading_floor_ws(websocket: WebSocket):
    """
    Real-time streaming WebSocket for LangGraph debate output.
    Messages are JSON objects with shape:
      { type: string, ... }
    Types: debate_start | speaker_change | token | hallucination_detected |
           mcp_tool | graph_update | synthesis_complete | debate_end
    """
    await websocket.accept()
    logger.info("WebSocket client connected")

    queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
    register_queue(queue)

    # Send a welcome heartbeat
    await websocket.send_json({"type": "connected", "message": "Fillado WebSocket ready."})

    async def _send_loop():
        try:
            while True:
                msg = await queue.get()
                await websocket.send_json(msg)
        except Exception:
            pass

    send_task = asyncio.create_task(_send_loop())

    try:
        while True:
            # Keeps connection alive and detects client disconnect instantly
            _ = await websocket.receive_text()
    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected")
    except Exception as exc:
        logger.error(f"WebSocket error: {exc}")
    finally:
        send_task.cancel()
        unregister_queue(queue)
