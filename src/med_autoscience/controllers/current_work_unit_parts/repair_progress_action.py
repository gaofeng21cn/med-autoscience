from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_type as _action_type,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)
from med_autoscience.controllers.study_progress_parts.current_executable_owner_action_parts.repair_progress import (
    owner_action_from_repair_progress_projection,
)


REPAIR_PROGRESS_EVIDENCE_SOURCE = "repair_progress_projection.mas_owner_repair_execution_evidence"
QUALITY_REPAIR_ACTION = "run_quality_repair_batch"


def repair_progress_action_consuming_current_action(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any] | None,
    surface_kind: str,
) -> dict[str, Any] | None:
    repair_action = owner_action_from_repair_progress_projection(
        progress,
        surface_kind=surface_kind,
    )
    if not _repair_progress_consumes_current_action(
        repair_action=repair_action,
        current_action=current_action,
        progress=progress,
    ):
        return None
    return repair_action


def _repair_progress_consumes_current_action(
    *,
    repair_action: Mapping[str, Any] | None,
    current_action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    repair = _mapping(repair_action)
    current = _mapping(current_action)
    if not repair or not current:
        return False
    if (_text(repair.get("source_surface")) or _text(repair.get("source"))) != REPAIR_PROGRESS_EVIDENCE_SOURCE:
        return False
    if _action_type(current) != QUALITY_REPAIR_ACTION:
        return False
    progress_projection = _mapping(progress.get("repair_progress_projection"))
    if progress_projection.get("paper_delta_observed") is not True:
        return False
    if progress_projection.get("accepted_owner_receipt") is not True:
        return False
    precedence = _mapping(repair.get("repair_progress_precedence"))
    source_work_unit = _work_unit_id(precedence.get("source_work_unit_id")) or _work_unit_id(
        progress_projection.get("work_unit_id")
    )
    if source_work_unit is None or source_work_unit != _work_unit_id(current.get("work_unit_id")):
        return False
    repair_eval = _text(repair.get("source_eval_id")) or _text(progress_projection.get("source_eval_id"))
    current_eval = _text(current.get("source_eval_id"))
    if repair_eval is not None and current_eval is not None and repair_eval != current_eval:
        return False
    return True


__all__ = ["repair_progress_action_consuming_current_action"]
