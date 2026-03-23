"""
app/services/market_chatgpt/models.py

Pydantic models for the Market ChatGPT 2.0 research assistant.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class PortfolioHolding(BaseModel):
    """A single holding in a user's portfolio."""

    symbol: str = Field(..., description="NSE ticker symbol")
    quantity: float
    avg_buy_price: float = Field(..., description="Average purchase price (INR)")
    current_price: Optional[float] = Field(None, description="Latest market price (INR)")


class QueryRequest(BaseModel):
    """Incoming research query from the user."""

    user_id: str = Field(..., description="Authenticated user identifier")
    query: str = Field(..., description="Natural-language research question")
    portfolio: list[PortfolioHolding] = Field(
        default_factory=list,
        description="User's current holdings; used to prioritise retrieval context",
    )
    max_steps: int = Field(
        default=5,
        ge=1,
        le=10,
        description="Maximum LangGraph reasoning steps before returning an answer",
    )


class SourceReference(BaseModel):
    """A single source document used to ground the response."""

    title: str
    url: Optional[str] = None
    source_type: str = Field(
        ..., description="'neo4j_node' | 'vector_chunk' | 'et_article' | 'nse_filing'"
    )
    relevance_score: float = Field(ge=0.0, le=1.0)
    snippet: str = Field(default="", description="Short excerpt from the source")


class QueryResponse(BaseModel):
    """Response returned by the Market ChatGPT 2.0 endpoint."""

    query_id: str = Field(..., description="Unique query trace identifier (UUID)")
    answer: str = Field(..., description="Final synthesised answer")
    reasoning_steps: list[str] = Field(
        default_factory=list,
        description="Ordered list of reasoning steps taken by the LangGraph agent",
    )
    sources: list[SourceReference] = Field(
        default_factory=list,
        description="Grounding sources used to generate the answer",
    )
    portfolio_context_used: bool = Field(
        default=False,
        description="Whether portfolio holdings influenced the retrieval",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)
