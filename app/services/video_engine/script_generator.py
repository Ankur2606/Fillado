"""
app/services/video_engine/script_generator.py

Generates a structured VideoScript from a daily market summary.

The generator uses the configured LLM to convert raw market data and
news headlines into a narrated script with intro, body segments, and outro.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime

from app.services.video_engine.models import VideoScript


async def generate_daily_wrap_script(
    market_date: str | None = None,
    top_gainers: list[str] | None = None,
    top_losers: list[str] | None = None,
    key_events: list[str] | None = None,
) -> VideoScript:
    """
    Generate a VideoScript for the daily market wrap.

    Args:
        market_date: ISO date string for the session (defaults to today).
        top_gainers: List of NSE symbols that gained the most.
        top_losers: List of NSE symbols that fell the most.
        key_events: List of key event headlines to cover in the script.

    Returns:
        A VideoScript with title, intro, segments, and outro.

    # TODO: Fetch live market data (index levels, top movers) from NSE API if
    #       not provided.
    # TODO: Build a prompt with market data and key events, then call the LLM
    #       to generate intro, segment narrations, and outro.
    # TODO: Estimate total_duration_sec based on average speaking rate (~130 wpm).
    """
    if market_date is None:
        market_date = date.today().isoformat()

    top_gainers = top_gainers or []
    top_losers = top_losers or []
    key_events = key_events or []

    intro = (
        f"[STUB] Welcome to the Fillado daily market wrap for {market_date}. "
        "Here is a summary of today's key market movements."
    )

    segments: list[str] = []
    if top_gainers:
        segments.append(
            f"[STUB] Top gainers today: {', '.join(top_gainers)}. "
            "These stocks saw strong buying interest driven by positive catalysts."
        )
    if top_losers:
        segments.append(
            f"[STUB] Top losers today: {', '.join(top_losers)}. "
            "Selling pressure was observed amid weak macro cues."
        )
    for event in key_events:
        segments.append(f"[STUB] Key event: {event}")

    if not segments:
        segments = ["[STUB] No market data provided. Segments will be auto-generated once LLM is wired up."]

    outro = "[STUB] That's a wrap for today. Stay tuned for tomorrow's market update."

    # Rough estimate: ~3 seconds per word
    word_count = sum(len(s.split()) for s in [intro, *segments, outro])
    duration_sec = round(word_count / 130 * 60, 1)  # 130 wpm

    return VideoScript(
        script_id=str(uuid.uuid4()),
        title=f"Fillado Daily Market Wrap — {market_date}",
        date=market_date,
        intro=intro,
        segments=segments,
        outro=outro,
        total_duration_sec=duration_sec,
        created_at=datetime.utcnow(),
    )
