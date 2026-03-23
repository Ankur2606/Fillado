"""
app/workers/video_worker.py

Background worker that processes pending VideoJob records.

Workflow:
  1. Poll PostgreSQL for VideoJobs with status=PENDING.
  2. For each job, run the full pipeline:
       script_generator → shot_planner → renderer_stub.
  3. Update the VideoJob record in PostgreSQL with the final status and URL.

This worker is designed to run as an independent asyncio task launched
at application startup or as a standalone process.
"""

from __future__ import annotations

import asyncio
import logging

from app.services.video_engine.models import VideoJob, VideoJobStatus
from app.services.video_engine.renderer_stub import render_video
from app.services.video_engine.script_generator import generate_daily_wrap_script
from app.services.video_engine.shot_planner import plan_shots

logger = logging.getLogger(__name__)


async def _process_video_job(job: VideoJob) -> VideoJob:
    """
    Run the full video generation pipeline for a single VideoJob.

    Stages:
      1. SCRIPTING  – generate a VideoScript.
      2. PLANNING   – convert the script into a shot list.
      3. RENDERING  – render the shots into a video file.

    # TODO: Persist job status transitions to PostgreSQL after each stage.
    # TODO: Add timeout handling to prevent stuck jobs.
    """
    from datetime import datetime

    try:
        # Stage 1: Script generation
        job.status = VideoJobStatus.SCRIPTING
        job.updated_at = datetime.utcnow()
        script = await generate_daily_wrap_script()
        job.script = script
        logger.info("Job %s: script generated (%s)", job.job_id, script.title)

        # Stage 2: Shot planning
        job.status = VideoJobStatus.PLANNING
        job.updated_at = datetime.utcnow()
        shots = await plan_shots(script)
        job.shots = shots
        logger.info("Job %s: %d shots planned", job.job_id, len(shots))

        # Stage 3: Rendering
        job = await render_video(job)
        logger.info("Job %s: rendering complete → %s", job.job_id, job.output_url)

    except Exception as exc:
        job.status = VideoJobStatus.FAILED
        job.error_message = str(exc)
        job.updated_at = datetime.utcnow()
        logger.exception("Job %s failed: %s", job.job_id, exc)

    return job


async def run_video_worker(poll_interval_sec: float = 30.0) -> None:
    """
    Main video worker loop.

    Polls PostgreSQL every *poll_interval_sec* seconds for PENDING VideoJobs
    and processes them.

    # TODO: Query PostgreSQL for jobs with status=PENDING.
    # TODO: Lock rows with SELECT ... FOR UPDATE SKIP LOCKED to prevent
    #       multiple workers processing the same job.
    # TODO: Replace polling with a Redis queue (BRPOP) for lower latency.
    """
    logger.info("Video worker started (poll interval: %ss)", poll_interval_sec)
    while True:
        try:
            # TODO: Replace with real DB query for pending jobs
            pending_jobs: list[VideoJob] = []  # TODO: fetch from PostgreSQL
            for job in pending_jobs:
                await _process_video_job(job)
                # TODO: Persist updated job back to PostgreSQL
        except Exception as exc:
            logger.exception("Video worker encountered an error: %s", exc)

        await asyncio.sleep(poll_interval_sec)
