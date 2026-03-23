"""
app/services/video_engine/models.py

Pydantic models for the AI Market Video Engine feature.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class VideoJobStatus(str, Enum):
    PENDING = "pending"
    SCRIPTING = "scripting"
    PLANNING = "planning"
    RENDERING = "rendering"
    COMPLETED = "completed"
    FAILED = "failed"


class ShotType(str, Enum):
    TITLE_CARD = "title_card"
    CHART_OVERLAY = "chart_overlay"
    NEWS_TICKER = "news_ticker"
    TALKING_HEAD = "talking_head"
    DATA_VIZ = "data_viz"
    OUTRO = "outro"


class Shot(BaseModel):
    """A single shot in the video shot plan."""

    shot_index: int = Field(..., description="Ordered position in the video")
    shot_type: ShotType
    duration_sec: float = Field(..., gt=0, description="Duration of this shot in seconds")
    narration: str = Field(default="", description="Narration or caption text for this shot")
    visual_description: str = Field(
        default="", description="Brief description of the visual for the renderer"
    )
    data_payload: dict = Field(
        default_factory=dict,
        description="Arbitrary structured data (chart data, tickers, etc.) for the renderer",
    )


class VideoScript(BaseModel):
    """Auto-generated script for a market wrap video."""

    script_id: str = Field(..., description="Unique script identifier (UUID)")
    title: str = Field(..., description="Video title")
    date: str = Field(..., description="Market session date, e.g. '2024-01-15'")
    intro: str = Field(default="", description="Opening narration paragraph")
    segments: list[str] = Field(
        default_factory=list,
        description="Ordered list of script segments (one per major market story)",
    )
    outro: str = Field(default="", description="Closing narration paragraph")
    total_duration_sec: float = Field(
        default=0.0, description="Estimated total video duration in seconds"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)


class VideoJob(BaseModel):
    """A video generation job tracking the full pipeline state."""

    job_id: str = Field(..., description="Unique job identifier (UUID)")
    status: VideoJobStatus = Field(default=VideoJobStatus.PENDING)
    script: Optional[VideoScript] = Field(
        None, description="Generated script (populated after scripting stage)"
    )
    shots: list[Shot] = Field(
        default_factory=list,
        description="Shot plan (populated after planning stage)",
    )
    output_url: Optional[str] = Field(
        None, description="URL of the rendered video (populated after rendering)"
    )
    error_message: Optional[str] = Field(
        None, description="Error details if the job failed"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
