"""
app/services/opportunity_radar/models.py

Pydantic models for the Opportunity Radar feature.
These models represent core domain entities used across ingestion,
agent processing, and API responses.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class EventType(str, Enum):
    """Category of a market-moving event."""

    INSIDER_TRADE = "insider_trade"
    REGULATORY_FILING = "regulatory_filing"
    SUPPLY_CHAIN_SHOCK = "supply_chain_shock"
    EARNINGS_SURPRISE = "earnings_surprise"
    VERNACULAR_NEWS = "vernacular_news"
    CORPORATE_ACTION = "corporate_action"
    ANALYST_UPGRADE = "analyst_upgrade"
    ANALYST_DOWNGRADE = "analyst_downgrade"
    OTHER = "other"


class SignalStrength(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class Company(BaseModel):
    """Represents a publicly listed company on NSE/BSE."""

    nse_symbol: str = Field(..., description="NSE ticker symbol, e.g. 'RELIANCE'")
    name: str = Field(..., description="Full company name")
    sector: Optional[str] = Field(None, description="SEBI sector classification")
    isin: Optional[str] = Field(None, description="ISIN code")
    market_cap_cr: Optional[float] = Field(
        None, description="Market capitalisation in Indian Crores"
    )


class Event(BaseModel):
    """A market-moving event detected by an ingestion source or agent."""

    event_id: str = Field(..., description="Unique event identifier (UUID)")
    event_type: EventType
    headline: str = Field(..., description="Short headline or title of the event")
    summary: str = Field(..., description="Brief AI-generated summary")
    source_url: Optional[str] = Field(None, description="Original source URL")
    language: str = Field(
        default="en", description="ISO 639-1 language code of the source"
    )
    detected_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="UTC timestamp when the event was detected",
    )
    companies_affected: list[str] = Field(
        default_factory=list,
        description="NSE symbols of companies directly affected by this event",
    )
    causal_chain: list[str] = Field(
        default_factory=list,
        description="Ordered list of NSE symbols in the causal propagation chain",
    )
    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Verification confidence score (0–1)",
    )


class Alert(BaseModel):
    """A trade signal derived from a verified Event."""

    alert_id: str = Field(..., description="Unique alert identifier (UUID)")
    event: Event
    symbol: str = Field(..., description="Primary NSE ticker this alert targets")
    signal_strength: SignalStrength
    direction: str = Field(
        ..., description="Expected price direction: 'bullish' | 'bearish' | 'neutral'"
    )
    reasoning: str = Field(
        ..., description="Plain-English explanation of why this alert was generated"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = Field(
        None, description="UTC timestamp after which this alert should be considered stale"
    )
