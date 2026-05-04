from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_progress, study_runtime_router
from med_autoscience.controllers.study_progress_parts.publication_runtime import _publication_eval_specificity_request
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SUPERVISION_LATEST_RELATIVE_PATH = Path("artifacts/supervision/hourly/latest.json")


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _latest_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_LATEST_RELATIVE_PATH


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _study_root(profile: WorkspaceProfile, study_id: str) -> Path:
    return profile.studies_root / study_id


def _active_run_id(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    supervision = _mapping(progress.get("supervision"))
    runtime_audit = _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit"))
    for value in (
        supervision.get("active_run_id"),
        status.get("active_run_id"),
        _mapping(status.get("runtime_liveness_audit")).get("active_run_id"),
        runtime_audit.get("active_run_id"),
    ):
        if text := _text(value):
            return text
    return None


def _worker_running(status: Mapping[str, Any]) -> bool:
    runtime_audit = _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit"))
    if runtime_audit.get("worker_running") is False:
        return False
    if _mapping(status.get("runtime_liveness_audit")).get("worker_running") is False:
        return False
    return bool(runtime_audit.get("worker_running") or _mapping(status.get("runtime_liveness_audit")).get("worker_running"))


def _blocking_reasons(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    control_plane = _mapping(status.get("control_plane_snapshot"))
    progress_control = _mapping(progress.get("control_plane_snapshot"))
    return list(
        dict.fromkeys(
            [
                *_string_items(status.get("blocking_reasons")),
                *_string_items(runtime_health.get("blocking_reasons")),
                *_string_items(control_plane.get("blocking_reasons")),
                *_string_items(_mapping(control_plane.get("dispatch_gate")).get("blocking_reasons")),
                *_string_items(progress_control.get("blocking_reasons")),
                *_string_items(progress.get("current_blockers")),
            ]
        )
    )


def _retry_exhausted(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    reasons = set(_blocking_reasons(status, progress))
    return (
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or _text(runtime_health.get("attempt_state")) == "escalated"
        or runtime_health.get("retry_budget_remaining") == 0
    )


def _publication_eval_payload(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any]:
    from_status = _mapping(status.get("publication_eval"))
    if from_status:
        return from_status
    refs = _mapping(progress.get("refs"))
    publication_eval_path = _text(refs.get("publication_eval_path"))
    if publication_eval_path is None:
        return {}
    return _read_json_object(Path(publication_eval_path)) or {}


def _next_work_unit_needs_specificity(value: object) -> bool:
    next_work_unit = _mapping(value)
    return _text(next_work_unit.get("unit_id")) in {"gate_needs_specificity", "needs_specificity"}


def _publication_gate_specificity_required(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    reasons = set(_blocking_reasons(status, progress))
    if _text(status.get("reason")) == "publication_gate_specificity_required":
        reasons.add("publication_gate_specificity_required")
    if _text(_mapping(progress.get("ai_repair_lifecycle")).get("blocked_reason")) == "publication_gate_specificity_required":
        reasons.add("publication_gate_specificity_required")
    operator_status = _mapping(progress.get("operator_status_card"))
    no_op_suppression = _mapping(operator_status.get("no_op_suppression"))
    specificity_request = _publication_eval_specificity_request(dict(publication_eval_payload) or None)
    required = (
        "publication_gate_specificity_required" in reasons
        or _text(_mapping(progress.get("intervention_lane")).get("lane_id")) == "publication_gate_specificity_required"
        or _text(_mapping(progress.get("operator_verdict")).get("lane_id")) == "publication_gate_specificity_required"
        or _text(operator_status.get("handling_state")) == "publication_gate_specificity_required"
        or _text(no_op_suppression.get("outcome")) == "needs_specificity"
        or _next_work_unit_needs_specificity(no_op_suppression.get("next_work_unit"))
        or specificity_request is not None
    )
    return {
        "required": required,
        "request": specificity_request,
        "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
    }


def _ai_reviewer_assessment(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
) -> dict[str, Any]:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    owner = _text(provenance.get("owner"))
    reasons = set(_blocking_reasons(status, progress))
    required = bool(provenance.get("ai_reviewer_required")) or "publication_eval.ai_reviewer_required" in reasons
    present = owner == "ai_reviewer"
    missing = not present and (required or bool(progress.get("quality_review_loop")))
    return {
        "present": present,
        "owner": owner,
        "required": required,
        "missing": missing,
    }


def _supervisor_only(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _mapping(status.get("execution_owner_guard")).get("supervisor_only") is True:
        return True
    return "execution_owner_guard.supervisor_only" in set(_blocking_reasons(status, progress))


def _runtime_platform_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    active_run_id = _active_run_id(status, progress)
    no_live_worker = not active_run_id or not _worker_running(status)
    return _retry_exhausted(status, progress) and no_live_worker and _text(status.get("quest_status")) in {
        "active",
        "running",
    }


def _action_queue(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> list[dict[str, Any]]:
    actions: list[dict[str, Any]] = []
    if _runtime_platform_repair_required(status, progress):
        actions.append(
            {
                "action_type": "runtime_platform_repair",
                "authority": "external_supervisor",
                "reason": "runtime_recovery_retry_budget_exhausted",
                "paper_package_mutation_allowed": False,
            }
        )
    if gate_specificity.get("required") is True:
        actions.append(
            {
                "action_type": "publication_gate_specificity_required",
                "authority": "observability_only",
                "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
                "paper_package_mutation_allowed": False,
            }
        )
    if ai_reviewer_assessment.get("missing") is True:
        actions.append(
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "authority": "observability_only",
                "paper_package_mutation_allowed": False,
            }
        )
    return actions


def _why_not_applied(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> str | None:
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _retry_exhausted(status, progress):
        return "runtime_recovery_retry_budget_exhausted"
    if text := _text(lifecycle.get("blocked_reason")):
        return text
    if actions:
        return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
    return None


def _study_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply_safe_actions: bool,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    status = study_runtime_router.study_runtime_status(profile=profile, study_id=study_id, study_root=study_root)
    progress = study_progress.read_study_progress(profile=profile, study_id=study_id, study_root=study_root)
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    publication_eval_payload = _publication_eval_payload(status_payload, progress_payload)
    gate_specificity = _publication_gate_specificity_required(
        status_payload,
        progress_payload,
        publication_eval_payload,
    )
    ai_reviewer_assessment = _ai_reviewer_assessment(
        status_payload,
        progress_payload,
        publication_eval_payload,
    )
    actions = _action_queue(
        status_payload,
        progress_payload,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    lifecycle = _mapping(progress_payload.get("ai_repair_lifecycle"))
    external_supervisor_required = bool(
        lifecycle.get("external_supervisor_required")
        or any(_text(action.get("authority")) == "external_supervisor" for action in actions)
    )
    supervision = _mapping(progress_payload.get("supervision"))
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": _text(status_payload.get("quest_id")) or _text(progress_payload.get("quest_id")),
        "quest_root": _text(status_payload.get("quest_root")) or _text(progress_payload.get("quest_root")),
        "quest_status": _text(status_payload.get("quest_status")),
        "current_stage": _text(progress_payload.get("current_stage")),
        "active_run_id": _active_run_id(status_payload, progress_payload),
        "supervision_url": _text(supervision.get("browser_url")),
        "paper_stage": _text(progress_payload.get("paper_stage")),
        "runtime_health": _mapping(status_payload.get("runtime_health_snapshot"))
        or _mapping(progress_payload.get("runtime_health_snapshot")),
        "meaningful_artifact_delta": bool(progress_payload.get("last_meaningful_progress_at")),
        "gate_specificity": gate_specificity,
        "ai_reviewer_assessment": ai_reviewer_assessment,
        "ai_repair_lifecycle": lifecycle or None,
        "action_queue": actions,
        "why_not_applied": _why_not_applied(status=status_payload, progress=progress_payload, actions=actions),
        "escalation_reason": _why_not_applied(status=status_payload, progress=progress_payload, actions=actions),
        "external_supervisor_required": external_supervisor_required,
        "supervisor_only": _supervisor_only(status_payload, progress_payload),
        "paper_package_mutated": False,
        "apply_safe_actions": apply_safe_actions,
    }


def supervisor_scan(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    apply_safe_actions: bool = False,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    generated_at = _utc_now()
    studies = [
        _study_projection(profile=profile, study_id=study_id, apply_safe_actions=apply_safe_actions)
        for study_id in resolved_study_ids
    ]
    latest_path = _latest_path(profile)
    payload = {
        "surface": "portable_runtime_supervisor_scan",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "scheduler_contract": {
            "codex_app_heartbeat_required": False,
            "supported_schedulers": ["systemd_user", "cron", "docker_one_shot", "launchd"],
        },
        "apply_safe_actions": apply_safe_actions,
        "studies": studies,
        "action_queue": [
            {"study_id": study["study_id"], **action}
            for study in studies
            for action in study.get("action_queue", [])
            if isinstance(action, Mapping)
        ],
        "refs": {"latest_path": str(latest_path)},
    }
    _write_json(latest_path, payload)
    return payload


__all__ = [
    "SCHEMA_VERSION",
    "SUPERVISION_LATEST_RELATIVE_PATH",
    "supervisor_scan",
]
