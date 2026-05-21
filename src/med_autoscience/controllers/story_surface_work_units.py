from __future__ import annotations


STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS = frozenset(
    {
        "manuscript_story_repair",
        "medical_prose_write_repair",
    }
)


def is_story_surface_delta_write_work_unit(unit_id: object) -> bool:
    return str(unit_id or "").strip() in STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS


__all__ = [
    "STORY_SURFACE_DELTA_WRITE_WORK_UNIT_IDS",
    "is_story_surface_delta_write_work_unit",
]
