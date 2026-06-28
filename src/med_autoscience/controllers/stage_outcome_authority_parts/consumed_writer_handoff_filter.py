from __future__ import annotations

from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from . import current_writer_handoff


def without_consumed_quality_repair_writer_handoffs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatches: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        dispatch
        for dispatch in dispatches
        if not current_writer_handoff.consumed_quality_repair_writer_handoff_dispatch(
            profile=profile,
            study_id=study_id,
            action_type=_text(dispatch.get("action_type")) or "",
            dispatch=dispatch,
        )
    ]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["without_consumed_quality_repair_writer_handoffs"]
