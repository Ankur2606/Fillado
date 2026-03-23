"""
app/services/video_engine/shot_planner.py

Converts a VideoScript into a list of Shot objects.

The planner determines the type, duration, narration, and visual
description for each shot based on the script segments.
"""

from __future__ import annotations

from app.services.video_engine.models import Shot, ShotType, VideoScript


async def plan_shots(script: VideoScript) -> list[Shot]:
    """
    Convert a VideoScript into an ordered shot list.

    Shot assignment logic (stub):
      - Intro → TITLE_CARD shot.
      - Each segment → DATA_VIZ shot (for numeric data) or TALKING_HEAD.
      - Outro → OUTRO shot.

    Args:
        script: A fully populated VideoScript.

    Returns:
        Ordered list of Shot objects ready for the renderer.

    # TODO: Use the LLM to assign the most appropriate ShotType to each segment
    #       based on the segment's content (chart data → CHART_OVERLAY,
    #       index moves → DATA_VIZ, event news → NEWS_TICKER, etc.).
    # TODO: Extract structured data payloads (price series, ticker symbols) from
    #       segment text and populate Shot.data_payload.
    # TODO: Calibrate duration per shot based on narration length.
    """
    shots: list[Shot] = []
    index = 0

    # Title card
    shots.append(
        Shot(
            shot_index=index,
            shot_type=ShotType.TITLE_CARD,
            duration_sec=3.0,
            narration="",
            visual_description=f"Title: {script.title}",
            data_payload={"title": script.title, "date": script.date},
        )
    )
    index += 1

    # Intro
    if script.intro:
        shots.append(
            Shot(
                shot_index=index,
                shot_type=ShotType.TALKING_HEAD,
                duration_sec=max(3.0, len(script.intro.split()) / 130 * 60),
                narration=script.intro,
                visual_description="Anchor introducing the daily wrap.",
            )
        )
        index += 1

    # One shot per segment
    for segment in script.segments:
        shot_type = ShotType.DATA_VIZ  # TODO: classify with LLM
        shots.append(
            Shot(
                shot_index=index,
                shot_type=shot_type,
                duration_sec=max(3.0, len(segment.split()) / 130 * 60),
                narration=segment,
                visual_description="[STUB] Visual to be determined by LLM classifier.",
            )
        )
        index += 1

    # Outro
    if script.outro:
        shots.append(
            Shot(
                shot_index=index,
                shot_type=ShotType.OUTRO,
                duration_sec=max(3.0, len(script.outro.split()) / 130 * 60),
                narration=script.outro,
                visual_description="Outro card with Fillado branding.",
            )
        )

    return shots
