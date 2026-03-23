"""
app/services/chart_patterns/explanations.py

Plain-English explanation generator for detected chart patterns.

Uses the configured LLM to produce investor-friendly, jargon-free
descriptions of each PatternHit.
"""

from __future__ import annotations

from app.services.chart_patterns.models import PatternHit


_PATTERN_TEMPLATES: dict[str, str] = {
    "head_and_shoulders": (
        "A Head and Shoulders pattern on {symbol} suggests the uptrend may be "
        "reversing. The stock formed three peaks — a higher middle peak (the 'head') "
        "flanked by two lower peaks (the 'shoulders'). A break below the neckline "
        "({neckline}) would typically signal a sell opportunity targeting {target}."
    ),
    "cup_and_handle": (
        "A Cup and Handle pattern on {symbol} is a bullish continuation signal. "
        "The stock formed a U-shaped base (the 'cup') and is now consolidating "
        "in a short pullback (the 'handle'). A breakout above the rim typically "
        "targets {target}."
    ),
    "double_top": (
        "A Double Top on {symbol} is a bearish reversal pattern. The stock tested "
        "resistance at approximately {resistance} twice without breaking through, "
        "suggesting sellers are in control. A break below support would confirm "
        "the pattern."
    ),
    "double_bottom": (
        "A Double Bottom on {symbol} is a bullish reversal pattern. The stock found "
        "support at approximately {support} twice, suggesting buyers are stepping in "
        "at that level. A break above the pattern's neckline would confirm the reversal."
    ),
}


async def generate_explanation(hit: PatternHit) -> str:
    """
    Generate a plain-English explanation for a PatternHit.

    First attempts a template-based explanation (fast, no LLM call).
    If no template exists, falls back to an LLM-generated explanation.

    # TODO: For the LLM fallback, construct a prompt that includes the pattern
    #       type, symbol, timeframe, confidence, and price levels, then call
    #       the configured LLM via the provider-agnostic wrapper in config.py.
    # TODO: Cache LLM explanations in Redis to avoid repeated identical calls.
    """
    template = _PATTERN_TEMPLATES.get(hit.pattern_type.value)
    if template:
        explanation = template.format(
            symbol=hit.symbol,
            neckline=hit.stop_loss or "N/A",
            target=hit.price_target or "N/A",
            resistance=hit.price_target or "N/A",
            support=hit.stop_loss or "N/A",
        )
    else:
        # TODO: LLM fallback
        explanation = (
            f"[STUB] A {hit.pattern_type.value.replace('_', ' ').title()} pattern "
            f"was detected on {hit.symbol} ({hit.timeframe} timeframe) with "
            f"{hit.confidence:.0%} confidence. "
            "A detailed AI explanation will be generated once the LLM integration "
            "is complete."
        )

    return explanation
