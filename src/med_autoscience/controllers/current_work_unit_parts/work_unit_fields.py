from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    PROVIDER_ADMISSION_AUTHORITIES,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
)


def route_work_unit_id(route: Mapping[str, Any]) -> str | None:
    payload = _mapping(route)
    return _work_unit_id(payload.get("work_unit_id")) or _work_unit_id(payload.get("next_work_unit"))


def provider_admission_pending(provider_admission: Mapping[str, Any] | None) -> bool:
    payload = _mapping(provider_admission)
    if not payload:
        return False
    if payload.get("running_provider_attempt") is True:
        return False
    return (
        payload.get("provider_admission_pending_count") not in (None, 0)
        or payload.get("provider_attempt_or_lease_required") is True
        or _text(payload.get("execution_status")) == "handoff_ready"
        or any(
            _text(item.get("authority")) in PROVIDER_ADMISSION_AUTHORITIES
            for item in payload.get("action_queue") or []
            if isinstance(item, Mapping)
        )
    )


def pending_provider_admission_evidence(provider_admission: Mapping[str, Any] | None) -> dict[str, Any]:
    payload = _mapping(provider_admission)
    return {
        "provider_admission_pending_count": payload.get("provider_admission_pending_count"),
        "execution_status": _text(payload.get("execution_status")),
        "provider_attempt_or_lease_required": payload.get("provider_attempt_or_lease_required") is True,
        "running_provider_attempt": payload.get("running_provider_attempt") is True,
    }


def action_owner(action: Mapping[str, Any], *, next_owner: str | None) -> str:
    return (
        _text(action.get("owner"))
        or _text(action.get("recommended_owner"))
        or _text(action.get("next_owner"))
        or _text(next_owner)
        or "med-autoscience"
    )


def action_source(action: Mapping[str, Any]) -> str | None:
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source is not None:
        return source
    if (
        _mapping(action.get("repair_progress_followup")).get("accepted_owner_receipt") is True
        or _mapping(action.get("repair_progress_precedence")).get("accepted_owner_receipt") is True
    ):
        return "repair_progress_projection.mas_owner_repair_execution_evidence"
    return None


def source_refs(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    source_refs: Sequence[str] | None,
) -> list[str]:
    refs: list[str] = []
    for item in source_refs or []:
        ref = _text(item)
        if ref is not None:
            refs.append(ref)
    refs.extend(_refs_from(_mapping(progress.get("refs"))))
    refs.extend(_refs_from(_mapping(status.get("refs"))))
    return sorted(dict.fromkeys(refs))


def stage_id(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    status: Mapping[str, Any],
) -> str | None:
    action_payload = _mapping(action)
    return (
        _text(action_payload.get("stage_id"))
        or _text(progress.get("current_stage"))
        or _text(status.get("current_stage"))
        or _text(status.get("stage_id"))
    )


def delta_count(value: Mapping[str, Any]) -> int:
    try:
        return int(value.get("count") or 0)
    except (TypeError, ValueError):
        return 0


def _refs_from(value: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("controller_decision_path", "publication_eval_path", "runtime_status_summary_path"):
        if (ref := _text(value.get(key))) is not None:
            refs.append(ref)
    return refs


__all__ = [
    "action_owner",
    "action_source",
    "delta_count",
    "pending_provider_admission_evidence",
    "provider_admission_pending",
    "route_work_unit_id",
    "source_refs",
    "stage_id",
]
