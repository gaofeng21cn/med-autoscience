from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any


STAGE_OUTCOME_TASK_KIND = "paper_mission/stage-outcome"
STAGE_OUTCOME_SURFACE = "paper_mission_stage_outcome"


def stage_outcome_for_owner_callable_receipt(
    *,
    study_id: str,
    action_type: str,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    owner_route = _mapping(dispatch.get("owner_route")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("owner_route")
    )
    source_refs = _mapping(owner_route.get("source_refs"))
    return {
        "surface": STAGE_OUTCOME_SURFACE,
        "task_kind": STAGE_OUTCOME_TASK_KIND,
        "study_id": study_id,
        "action_type": action_type,
        "outcome": _text(execution.get("execution_status")) or "unknown",
        "blocked_reason": _text(execution.get("blocked_reason")),
        "owner": _text(execution.get("next_executable_owner"))
        or _text(dispatch.get("next_executable_owner"))
        or _text(owner_route.get("next_owner")),
        "work_unit_id": _text(execution.get("work_unit_id"))
        or _text(dispatch.get("work_unit_id"))
        or _text(source_refs.get("work_unit_id")),
        "work_unit_fingerprint": _text(execution.get("work_unit_fingerprint"))
        or _text(dispatch.get("work_unit_fingerprint"))
        or _text(source_refs.get("work_unit_fingerprint")),
        "dispatch_ref": str(dispatch_path),
        "owner_result_present": isinstance(execution.get("owner_result"), Mapping),
        "typed_blocker_present": isinstance(execution.get("typed_blocker"), Mapping),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "STAGE_OUTCOME_SURFACE",
    "STAGE_OUTCOME_TASK_KIND",
    "stage_outcome_for_owner_callable_receipt",
]
