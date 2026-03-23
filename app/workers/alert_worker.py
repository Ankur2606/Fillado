"""
app/workers/alert_worker.py

Background worker that continuously processes the Opportunity Radar pipeline.

Workflow:
  1. Poll ingestion sources for new payloads.
  2. Invoke the radar_graph LangGraph for each payload.
  3. Publish generated Alerts to the Redis 'alerts' pub/sub channel.
  4. Persist Alerts to PostgreSQL.

This worker is designed to run as an independent asyncio task launched
at application startup (see main.py lifespan) or as a standalone process.
"""

from __future__ import annotations

import asyncio
import logging

from app.core.db.redis_client import redis_client
from app.services.opportunity_radar.agents import RadarState, radar_graph
from app.services.opportunity_radar.ingestion_sources import (
    fetch_et_markets_headlines,
    fetch_nse_corporate_filings,
    fetch_vernacular_news,
)

logger = logging.getLogger(__name__)


async def _process_payload(payload: dict) -> None:
    """
    Run the full Opportunity Radar pipeline for a single raw payload.

    # TODO: Add structured logging with correlation IDs.
    # TODO: Add dead-letter queue logic for payloads that fail repeatedly.
    """
    initial_state: RadarState = {
        "raw_payload": payload,
        "event": None,
        "verified": False,
        "confidence_score": 0.0,
        "alert": None,
    }

    try:
        final_state = await radar_graph.ainvoke(initial_state)
        alert = final_state.get("alert")
        if alert:
            alert_json = alert.model_dump_json()
            await redis_client.publish("alerts", alert_json)
            # TODO: Persist alert to PostgreSQL via app.core.db.postgres.
            logger.info("Alert published: %s", alert.alert_id)
        else:
            logger.debug("Payload did not produce an alert (confidence too low).")
    except Exception as exc:
        logger.exception("Error processing payload: %s", exc)


async def run_alert_worker(poll_interval_sec: float = 60.0) -> None:
    """
    Main alert worker loop.

    Polls all ingestion sources every *poll_interval_sec* seconds and
    processes each payload through the Opportunity Radar pipeline.

    # TODO: Replace polling with push-based ingestion (webhooks, RSS with
    #       Conditional-GET) where supported by the data source.
    # TODO: Track processed event IDs (in Redis or PostgreSQL) to prevent
    #       duplicate processing.
    """
    logger.info("Alert worker started (poll interval: %ss)", poll_interval_sec)
    while True:
        try:
            async for payload in fetch_et_markets_headlines():
                await _process_payload(payload)

            async for payload in fetch_vernacular_news():
                await _process_payload(payload)

            async for payload in fetch_nse_corporate_filings():
                await _process_payload(payload)

        except Exception as exc:
            logger.exception("Alert worker encountered an error: %s", exc)

        await asyncio.sleep(poll_interval_sec)
