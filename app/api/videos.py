"""
app/api/videos.py

FastAPI router for the AI Market Video Engine.

Endpoints:
  POST /videos/daily-wrap      — Trigger daily market wrap video generation.
  GET  /videos/{job_id}        — Get status and result of a video job.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Path
from pydantic import BaseModel

from app.services.video_engine.models import VideoJob, VideoJobStatus, VideoScript
from app.services.video_engine.renderer_stub import render_video
from app.services.video_engine.script_generator import generate_daily_wrap_script
from app.services.video_engine.shot_planner import plan_shots

router = APIRouter()

# In-memory job store (stub — replace with PostgreSQL persistence)
_job_store: dict[str, VideoJob] = {}


class DailyWrapRequest(BaseModel):
    """Optional parameters for the daily wrap video job."""

    market_date: str | None = None
    top_gainers: list[str] = []
    top_losers: list[str] = []
    key_events: list[str] = []


class DailyWrapResponse(BaseModel):
    """Response returned when a new video job is successfully created."""

    job_id: str
    status: VideoJobStatus
    message: str


@router.post(
    "/videos/daily-wrap",
    response_model=DailyWrapResponse,
    status_code=202,
    summary="Trigger daily market wrap video generation",
    description=(
        "Enqueues a new video generation job for the daily market wrap.\n\n"
        "The pipeline stages are:\n"
        "  1. **Script generation** — LLM writes a narrated script from market data.\n"
        "  2. **Shot planning** — Converts the script into a timed shot list.\n"
        "  3. **Rendering** — Assembles the final video from shots and narration.\n\n"
        "The endpoint returns immediately with a job_id. Poll "
        "GET /videos/{job_id} to check progress."
    ),
)
async def create_daily_wrap(body: DailyWrapRequest) -> DailyWrapResponse:
    """
    Enqueue a daily market wrap video job and begin processing.

    Returns a 202 Accepted response with the job_id for status polling.

    # TODO: Persist the VideoJob to PostgreSQL instead of the in-memory store.
    # TODO: Push the job_id to a Redis queue so the video_worker picks it up
    #       asynchronously rather than processing it inline.
    # TODO: Add authentication so only authorised users can trigger video jobs.
    """
    job_id = str(uuid.uuid4())
    job = VideoJob(job_id=job_id, status=VideoJobStatus.PENDING)
    _job_store[job_id] = job

    # Process inline (stub — move to video_worker for production)
    script = await generate_daily_wrap_script(
        market_date=body.market_date,
        top_gainers=body.top_gainers or None,
        top_losers=body.top_losers or None,
        key_events=body.key_events or None,
    )
    job.script = script
    job.status = VideoJobStatus.PLANNING

    shots = await plan_shots(script)
    job.shots = shots
    job = await render_video(job)
    job.updated_at = datetime.utcnow()
    _job_store[job_id] = job

    return DailyWrapResponse(
        job_id=job_id,
        status=job.status,
        message=f"Video job {job_id} created successfully.",
    )


@router.get(
    "/videos/{job_id}",
    response_model=VideoJob,
    summary="Get video job status and result",
    description=(
        "Returns the current status and result of a video generation job.\n\n"
        "Possible statuses: pending | scripting | planning | rendering | "
        "completed | failed.\n\n"
        "Once status is **completed**, the response includes an `output_url` "
        "pointing to the rendered video."
    ),
)
async def get_video_job(
    job_id: str = Path(..., description="Video job ID returned by POST /videos/daily-wrap"),
) -> VideoJob:
    """
    Retrieve a VideoJob by its ID.

    Returns 404 if no job with the given ID exists.

    # TODO: Query PostgreSQL instead of the in-memory store.
    """
    job = _job_store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Video job '{job_id}' not found.")
    return job
