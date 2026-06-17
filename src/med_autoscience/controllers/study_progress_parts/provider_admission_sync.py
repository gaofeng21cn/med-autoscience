from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .owner_action_admission import build_owner_action_admission_projection
from .owner_action_admission import admission_authority_boundary
from .shared import _mapping_copy, _non_empty_text


def sync_progress_first_owner_action_admission(payload: dict[str, Any]) -> dict[str, Any]:
    monitoring = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    admission = _mapping_copy(monitoring.get("owner_action_admission"))
    current_action = _mapping_copy(payload.get("current_executable_owner_action"))
    if current_action:
        admission = _rebuild_owner_action_admission(payload, current_action=current_action) or admission
        monitoring["owner_action_admission"] = admission or None
    if not admission:
        return payload
    updated = dict(payload)
    if _admission_mismatches_current_execution(payload, admission=admission):
        admission = _suppressed_stale_admission(admission)
        monitoring["owner_action_admission"] = admission
        updated["progress_first_monitoring_summary"] = monitoring
    else:
        updated["progress_first_monitoring_summary"] = monitoring
    updated["owner_action_admission"] = admission
    return updated


def _rebuild_owner_action_admission(
    payload: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    latest_terminal_stage_log = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    return build_owner_action_admission_projection(
        payload=payload,
        current_action=current_action,
        handoff=handoff,
        stage_progress_log=_mapping_copy(handoff.get("stage_progress_log")),
        latest_terminal_stage_log=latest_terminal_stage_log,
    )


def _admission_mismatches_current_execution(
    payload: Mapping[str, Any],
    *,
    admission: Mapping[str, Any],
) -> bool:
    current_identity = _current_execution_identity(payload)
    if not current_identity:
        return False
    admission_identity = _owner_action_admission_identity(admission)
    if not admission_identity:
        return False
    current_action = _non_empty_text(current_identity.get("action_type"))
    admission_action = _non_empty_text(admission_identity.get("action_type"))
    if current_action is not None and admission_action is not None and current_action != admission_action:
        return True
    current_work_unit = _non_empty_text(current_identity.get("work_unit_id"))
    admission_work_unit = _non_empty_text(admission_identity.get("work_unit_id"))
    if (
        current_work_unit is not None
        and admission_work_unit is not None
        and current_work_unit != admission_work_unit
    ):
        return True
    current_fingerprint = _non_empty_text(current_identity.get("work_unit_fingerprint"))
    admission_fingerprint = _non_empty_text(admission_identity.get("work_unit_fingerprint"))
    return (
        current_fingerprint is not None
        and admission_fingerprint is not None
        and current_fingerprint != admission_fingerprint
    )


def _current_execution_identity(payload: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping_copy(payload.get("current_work_unit"))
    envelope = _mapping_copy(payload.get("current_execution_envelope"))
    return {
        key: value
        for key, value in {
            "action_type": _non_empty_text(current.get("action_type")),
            "work_unit_id": _non_empty_text(current.get("work_unit_id"))
            or _non_empty_text(envelope.get("next_work_unit")),
            "work_unit_fingerprint": _non_empty_text(current.get("work_unit_fingerprint"))
            or _non_empty_text(current.get("action_fingerprint")),
        }.items()
        if value is not None
    }


def _owner_action_admission_identity(admission: Mapping[str, Any]) -> dict[str, Any]:
    allowed_actions = [
        _non_empty_text(item)
        for item in admission.get("allowed_actions") or []
        if _non_empty_text(item) is not None
    ]
    return {
        key: value
        for key, value in {
            "action_type": _non_empty_text(admission.get("action_type"))
            or (allowed_actions[0] if len(allowed_actions) == 1 else None),
            "work_unit_id": _non_empty_text(admission.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(admission.get("work_unit_fingerprint"))
            or _non_empty_text(admission.get("action_fingerprint")),
        }.items()
        if value is not None
    }


def _suppressed_stale_admission(admission: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **dict(admission),
        "admission_requested": False,
        "admission_pending": False,
        "provider_attempt_start_requested": False,
        "provider_attempt_started": False,
        "provider_attempt_running_proven": False,
        "blocked_by": "current_execution_identity_mismatch",
        "stale_admission_suppressed": True,
        "admission_authority_boundary": admission_authority_boundary(),
    }


__all__ = ["sync_progress_first_owner_action_admission"]
