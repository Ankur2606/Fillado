"""
main.py — FastAPI application entry point.

Initialises the app, wires up all feature routers, and exposes a
liveness/readiness health-check endpoint.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.alerts import router as alerts_router
from app.api.chart_patterns import router as chart_patterns_router
from app.api.market_chatgpt import router as market_chatgpt_router
from app.api.videos import router as videos_router
from config import settings

app = FastAPI(
    title="Fillado ET Intelligence Layer",
    description=(
        "Modular AI system that turns ET Markets data into actionable signals "
        "for Indian retail and pro investors. Exposes four products: "
        "Opportunity Radar, Chart Pattern Intelligence, Market ChatGPT 2.0, "
        "and AI Market Video Engine."
    ),
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(alerts_router, tags=["Opportunity Radar"])
app.include_router(chart_patterns_router, tags=["Chart Pattern Intelligence"])
app.include_router(market_chatgpt_router, tags=["Market ChatGPT 2.0"])
app.include_router(videos_router, tags=["AI Market Video Engine"])


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """Liveness probe — returns service status and current environment."""
    return {"status": "ok", "env": settings.app_env}
