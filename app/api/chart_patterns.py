"""
app/api/chart_patterns.py

FastAPI router for the Chart Pattern Intelligence product.

Endpoints:
  GET /chart-patterns/{symbol} — Detect chart patterns for an NSE symbol.
"""

from __future__ import annotations

from fastapi import APIRouter, Path, Query

from app.services.chart_patterns.backtest_engine import run_backtest
from app.services.chart_patterns.explanations import generate_explanation
from app.services.chart_patterns.models import PatternHit, PatternStats, PatternType
from app.services.chart_patterns.pattern_detector import detect_patterns

router = APIRouter()


class ChartPatternResponse(PatternHit):
    """PatternHit enriched with a plain-English explanation."""
    # plain_english_explanation is already a field on PatternHit;
    # this subclass exists for router-specific documentation purposes.
    pass


@router.get(
    "/chart-patterns/{symbol}",
    response_model=list[ChartPatternResponse],
    summary="Detect chart patterns for an NSE symbol",
    description=(
        "Scans the most recent OHLCV candles for *symbol* and returns a list "
        "of detected chart patterns (e.g. Head & Shoulders, Cup & Handle). "
        "Each result includes a plain-English explanation and, when available, "
        "a price target and stop-loss level.\n\n"
        "Pattern detection is backed by the Chart Pattern Intelligence engine. "
        "Back-test statistics for each pattern can be retrieved separately."
    ),
)
async def get_chart_patterns(
    symbol: str = Path(
        ...,
        description="NSE ticker symbol (case-insensitive), e.g. 'RELIANCE' or 'INFY'",
        example="RELIANCE",
    ),
    timeframe: str = Query(
        "1d",
        description="Candle timeframe: '1d' | '1h' | '15m' | '5m'",
        example="1d",
    ),
) -> list[ChartPatternResponse]:
    """
    Detect and explain chart patterns for the given NSE symbol.

    Pipeline:
      1. Fetch OHLCV candles from the NSE data source.
      2. Run all pattern detectors against the candle series.
      3. Generate plain-English explanations for each detected hit.

    Returns the list of PatternHit objects with explanations populated.

    # TODO: Add Redis caching with a short TTL (e.g. 5 minutes) so repeated
    #       requests for the same symbol/timeframe don't re-run the detectors.
    # TODO: Validate that *symbol* exists on NSE before running detection.
    """
    hits = await detect_patterns(symbol.upper(), timeframe)

    # Enrich each hit with a plain-English explanation
    enriched: list[ChartPatternResponse] = []
    for hit in hits:
        hit.plain_english_explanation = await generate_explanation(hit)
        enriched.append(ChartPatternResponse(**hit.model_dump()))

    return enriched


@router.get(
    "/chart-patterns/{symbol}/backtest",
    response_model=PatternStats,
    summary="Back-test a specific pattern for an NSE symbol",
    description=(
        "Runs a historical back-test for a given pattern type on *symbol* "
        "and returns aggregated performance statistics including win rate, "
        "average return, and average holding period."
    ),
)
async def get_pattern_backtest(
    symbol: str = Path(..., description="NSE ticker symbol", example="RELIANCE"),
    pattern_type: PatternType = Query(
        PatternType.HEAD_AND_SHOULDERS,
        description="Chart pattern type to back-test",
    ),
    timeframe: str = Query("1d", description="Candle timeframe"),
    lookback_days: int = Query(
        365, ge=30, le=1825, description="Historical lookback window in calendar days"
    ),
) -> PatternStats:
    """
    Run a per-stock back-test for a specific chart pattern.

    # TODO: Cache back-test results in PostgreSQL and only re-run when
    #       new candle data is available.
    """
    return await run_backtest(
        symbol=symbol.upper(),
        pattern_type=pattern_type,
        timeframe=timeframe,
        lookback_days=lookback_days,
    )
