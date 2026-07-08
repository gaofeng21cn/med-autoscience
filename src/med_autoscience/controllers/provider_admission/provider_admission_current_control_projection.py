from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)


def audit_only_unscanned_handoff(
    *,
    output_studies: list[dict[str, Any]],
    output_actions: list[dict[str, Any]],
    scanned_study_ids: set[str],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    retained_ids = {
        study_id
        for study in output_studies
        if (study_id := _non_empty_text(study.get("study_id"))) is not None
        and study_id not in scanned_study_ids
    }
    if not retained_ids:
        return output_studies, output_actions, _unscanned_handoff_retention_payload(
            retained_ids=[],
            active_action_suppressed_count=0,
        )
    sanitized_studies: list[dict[str, Any]] = []
    suppressed_count = 0
    for study in output_studies:
        study_id = _non_empty_text(study.get("study_id"))
        if study_id not in retained_ids:
            sanitized_studies.append(dict(study))
            continue
        action_queue = [
            dict(action)
            for action in study.get("action_queue") or []
            if isinstance(action, Mapping)
        ]
        suppressed_count += len(action_queue)
        payload = dict(study)
        payload["retained_unscanned_study"] = True
        payload["active_provider_admission_allowed"] = False
        payload["unscanned_action_queue_retained_for_audit"] = action_queue
        payload["action_queue"] = []
        sanitized_studies.append(payload)
    active_actions = [
        dict(action)
        for action in output_actions
        if _non_empty_text(action.get("study_id")) not in retained_ids
    ]
    suppressed_count += len(output_actions) - len(active_actions)
    return (
        sanitized_studies,
        active_actions,
        _unscanned_handoff_retention_payload(
            retained_ids=sorted(retained_ids),
            active_action_suppressed_count=suppressed_count,
        ),
    )


def _unscanned_handoff_retention_payload(
    *,
    retained_ids: list[str],
    active_action_suppressed_count: int,
) -> dict[str, Any]:
    return {
        "surface_kind": "provider_admission_current_control_unscanned_handoff_retention",
        "retained_unscanned_study_ids": retained_ids,
        "active_action_suppressed_count": active_action_suppressed_count,
        "active_queue_semantics": "scanned_studies_only",
        "retention_semantics": "audit_only",
    }


def terminal_precedence_by_study(
    scanned_studies: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for study in scanned_studies:
        study_id = _non_empty_text(study.get("study_id"))
        evidence = _mapping(study.get("terminal_closeout_precedence_evidence"))
        if study_id is not None and evidence:
            result[study_id] = dict(evidence)
    return result


def study_with_terminal_precedence(
    study: dict[str, Any],
    *,
    terminal_precedence_by_study: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    study_id = _non_empty_text(study.get("study_id"))
    evidence = (
        _mapping(terminal_precedence_by_study.get(study_id))
        if study_id is not None
        else {}
    )
    if not evidence:
        return study
    payload = dict(study)
    payload["terminal_closeout_precedence_evidence"] = dict(evidence)
    payload["stale_running_projection_suppressed"] = True
    payload["running_provider_attempt"] = False
    payload["active_run_id"] = None
    payload["active_stage_attempt_id"] = None
    payload["active_workflow_id"] = None
    runtime_health = _mapping(payload.get("runtime_health"))
    payload["runtime_health"] = {
        **runtime_health,
        "health_status": _non_empty_text(runtime_health.get("health_status"))
        or "provider_admission_pending",
        "runtime_liveness_status": "not_running",
        "stale_running_projection_suppressed": True,
    }
    return payload


__all__ = [
    "audit_only_unscanned_handoff",
    "study_with_terminal_precedence",
    "terminal_precedence_by_study",
]
