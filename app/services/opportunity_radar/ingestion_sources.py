"""
app/services/opportunity_radar/ingestion_sources.py

Async ingestion sources for the Opportunity Radar.

Each source is an async generator that yields raw text/JSON payloads.
The HyperLocalScout agent (see agents.py) consumes these payloads.
"""

from __future__ import annotations

import asyncio
from typing import AsyncGenerator

import httpx

from config import settings


async def fetch_et_markets_headlines() -> AsyncGenerator[dict, None]:
    """
    Async generator that fetches the latest headlines from ET Markets.

    Yields one dict per article with keys: title, url, published_at, language.
    # TODO: Implement real HTTP scraping / RSS parsing against
    #       settings.et_markets_base_url using httpx or aiohttp.
    #       Respect rate limits and add retry logic via tenacity.
    """
    # TODO: Replace stub with real ET Markets ingestion
    await asyncio.sleep(0)
    yield {
        "title": "[STUB] ET Markets headline",
        "url": f"{settings.et_markets_base_url}/stub",
        "published_at": "2024-01-01T09:00:00Z",
        "language": "en",
    }


async def fetch_vernacular_news() -> AsyncGenerator[dict, None]:
    """
    Async generator that fetches vernacular (Hindi, Marathi, Tamil, etc.) news
    from regional sources and translates headlines using the configured LLM.

    Yields one dict per article with keys: title, url, published_at, language,
    translated_title.
    # TODO: Integrate with regional news RSS feeds (e.g. NavBharat Times, Lokmat).
    #       Use the LLM to translate non-English headlines before processing.
    """
    await asyncio.sleep(0)
    yield {
        "title": "[STUB] वर्नाक्युलर खबर",
        "url": "https://stub.vernacular.example/article/1",
        "published_at": "2024-01-01T09:05:00Z",
        "language": "hi",
        "translated_title": "[STUB] Vernacular news headline (translated)",
    }


async def fetch_nse_corporate_filings() -> AsyncGenerator[dict, None]:
    """
    Async generator that polls the NSE API for new corporate filings,
    insider trades, and bulk deal announcements.

    Yields one dict per filing with keys: symbol, filing_type, filing_date,
    description, document_url.
    # TODO: Integrate with NSE's public filing API at settings.nse_api_base_url.
    #       Handle session cookies / authentication required by NSE.
    """
    await asyncio.sleep(0)
    yield {
        "symbol": "RELIANCE",
        "filing_type": "insider_trade",
        "filing_date": "2024-01-01",
        "description": "[STUB] Director acquired 10,000 shares",
        "document_url": f"{settings.nse_api_base_url}/stub-filing",
    }


async def fetch_live_nse_quotes(symbols: list[str]) -> AsyncGenerator[dict, None]:
    """
    Async generator that fetches live quotes for the given NSE symbols.

    Yields one dict per symbol with keys: symbol, ltp, change_pct, volume,
    timestamp.
    # TODO: Use NSE's public API or a third-party market data provider.
    #       Implement circuit-breaker logic for API outages.
    """
    for symbol in symbols:
        await asyncio.sleep(0)
        yield {
            "symbol": symbol,
            "ltp": 0.0,
            "change_pct": 0.0,
            "volume": 0,
            "timestamp": "2024-01-01T09:30:00Z",
        }
