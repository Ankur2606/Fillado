"""
app/services/chart_patterns/models.py

Pydantic models for the Chart Pattern Intelligence feature.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class PatternType(str, Enum):
    """Classical chart pattern categories."""

    HEAD_AND_SHOULDERS = "head_and_shoulders"
    INVERSE_HEAD_AND_SHOULDERS = "inverse_head_and_shoulders"
    CUP_AND_HANDLE = "cup_and_handle"
    DOUBLE_TOP = "double_top"
    DOUBLE_BOTTOM = "double_bottom"
    ASCENDING_TRIANGLE = "ascending_triangle"
    DESCENDING_TRIANGLE = "descending_triangle"
    SYMMETRICAL_TRIANGLE = "symmetrical_triangle"
    BULL_FLAG = "bull_flag"
    BEAR_FLAG = "bear_flag"
    WEDGE_RISING = "wedge_rising"
    WEDGE_FALLING = "wedge_falling"
    CHANNEL_UP = "channel_up"
    CHANNEL_DOWN = "channel_down"
    OTHER = "other"


class PatternHit(BaseModel):
    """A single detected chart pattern instance for a specific symbol."""

    hit_id: str = Field(..., description="Unique hit identifier (UUID)")
    symbol: str = Field(..., description="NSE ticker symbol")
    pattern_type: PatternType
    timeframe: str = Field(
        ..., description="Candle timeframe, e.g. '1d', '1h', '15m'"
    )
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    start_date: datetime = Field(..., description="Pattern start candle timestamp")
    end_date: datetime = Field(..., description="Pattern end / breakout candle timestamp")
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Pattern detection confidence score"
    )
    breakout_direction: str = Field(
        ..., description="Expected breakout direction: 'bullish' | 'bearish'"
    )
    price_target: Optional[float] = Field(
        None, description="Projected price target based on pattern measurement"
    )
    stop_loss: Optional[float] = Field(None, description="Suggested stop-loss level")
    plain_english_explanation: str = Field(
        default="", description="Human-readable explanation of the pattern"
    )


class PatternStats(BaseModel):
    """Back-test statistics for a pattern type on a given symbol."""

    symbol: str
    pattern_type: PatternType
    timeframe: str
    total_occurrences: int = Field(
        ..., description="Total number of times this pattern appeared historically"
    )
    win_rate: float = Field(
        ..., ge=0.0, le=1.0, description="Fraction of occurrences that hit the target"
    )
    avg_return_pct: float = Field(
        ..., description="Average return (%) after pattern breakout"
    )
    avg_holding_days: float = Field(
        ..., description="Average number of days to reach target or stop"
    )
    best_return_pct: float
    worst_return_pct: float
    last_updated: datetime = Field(default_factory=datetime.utcnow)
