from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_progress, study_runtime_router
from med_autoscience.controllers import supervisor_action_requests
from med_autoscience.controllers.study_progress_parts.publication_runtime import _publication_eval_specificity_request
from med_autoscience.developer_supervisor_mode import (
    DeveloperSupervisorMode,
    resolve_developer_supervisor_mode,
)
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
SUPERVISION_LATEST_RELATIVE_PATH = Path("artifacts/supervision/hourly/latest.json")
SUPERVISION_HISTORY_RELATIVE_PATH = Path("artifacts/supervision/hourly/history.jsonl")
SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES = ["artifacts/supervision/**"]
SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/**",
    "artifacts/autonomy/repair_lifecycle/latest.json",
    "artifacts/autonomy/repair_actions/latest.json",
]
SUPERVISION_FORBIDDEN_ACTIONS = [
    "paper_package_mutation",
    "manual_study_patch",
    "quality_gate_relaxation",
    "medical_claim_authoring",
]


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


def _history_path(profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / SUPERVISION_HISTORY_RELATIVE_PATH


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _read_last_json_line(path: Path) -> dict[str, Any] | None:
    try:
        lines = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    except OSError:
        return None
    for line in reversed(lines):
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, Mapping):
            return dict(payload)
    return None


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
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    quest_status = _text(status.get("quest_status"))
    zero_budget_in_recovery_context = runtime_health.get("retry_budget_remaining") == 0 and (
        quest_status in {"active", "running"}
        or attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
        or canonical_runtime_action in {"recover_runtime", "probe_runtime", "relaunch_runtime", "external_supervisor_required"}
    )
    return (
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or attempt_state == "escalated"
        or zero_budget_in_recovery_context
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


def _action_id(*, study_id: str, action_type: str, reason: str | None) -> str:
    suffix = reason or action_type
    return f"supervisor-action::{study_id}::{action_type}::{suffix}"


def _handoff_packet(*, study_id: str, quest_id: str | None, action: Mapping[str, Any]) -> dict[str, Any]:
    authority = _text(action.get("authority")) or "observability_only"
    return {
        "packet_type": "external_supervisor_handoff",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": _text(action.get("action_type")),
        "reason": _text(action.get("reason")) or _text(action.get("action_type")),
        "authority": authority,
        "recommended_owner": (
            "external_engineering_agent"
            if authority == "external_supervisor"
            else authority
        ),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "allowed_write_surfaces": (
            list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES)
            if authority == "external_supervisor"
            else list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES)
        ),
        "forbidden_actions": list(SUPERVISION_FORBIDDEN_ACTIONS),
    }


def _decorate_action(
    *,
    study_id: str,
    quest_id: str | None,
    action: Mapping[str, Any],
) -> dict[str, Any]:
    decorated = dict(action)
    action_type = _text(decorated.get("action_type")) or "unknown_action"
    reason = _text(decorated.get("reason")) or action_type
    decorated.setdefault("reason", reason)
    decorated["action_id"] = _action_id(study_id=study_id, action_type=action_type, reason=reason)
    decorated["handoff_packet"] = _handoff_packet(study_id=study_id, quest_id=quest_id, action=decorated)
    decorated.setdefault("status", "queued")
    decorated.setdefault("quality_gate_relaxation_allowed", False)
    decorated.setdefault("paper_package_mutation_allowed", False)
    decorated.setdefault("manual_study_patch_allowed", False)
    decorated.setdefault("medical_claim_authoring_allowed", False)
    decorated.setdefault("allowed_write_surfaces", list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES))
    decorated.setdefault("forbidden_actions", list(SUPERVISION_FORBIDDEN_ACTIONS))
    return decorated


def _action_queue(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    study_id: str,
    quest_id: str | None,
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
                "summary": "Runtime recovery retry budget is exhausted and no live worker is attached.",
                "paper_package_mutation_allowed": False,
            }
        )
    if gate_specificity.get("required") is True:
        actions.append(
            {
                "action_type": "publication_gate_specificity_required",
                "authority": "observability_only",
                "reason": "publication_gate_specificity_required",
                "summary": "Publication gate must name concrete claim/figure/table/metric/source_path targets.",
                "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
                "paper_package_mutation_allowed": False,
            }
        )
    if ai_reviewer_assessment.get("missing") is True:
        actions.append(
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "authority": "observability_only",
                "reason": "ai_reviewer_assessment_required",
                "summary": "Request an AI reviewer-owned publication_eval assessment.",
                "paper_package_mutation_allowed": False,
            }
        )
    return [
        _decorate_action(study_id=study_id, quest_id=quest_id, action=action)
        for action in actions
    ]


def _why_not_applied(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> str | None:
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _retry_exhausted(status, progress):
        return "runtime_recovery_retry_budget_exhausted"
    if actions:
        return _text(actions[0].get("reason")) or _text(actions[0].get("action_type"))
    if text := _text(lifecycle.get("blocked_reason")):
        return text
    return None


def _why_not_applied_timeline(reason: str | None) -> list[dict[str, Any]]:
    if reason is None:
        return []
    return [{"reason": reason, "state": "blocked", "recorded_at": _utc_now()}]


def _artifact_delta(progress: Mapping[str, Any]) -> dict[str, Any]:
    last_delta = _text(progress.get("last_meaningful_progress_at"))
    if last_delta is not None:
        return {"status": "fresh", "latest_meaningful_delta_at": last_delta}
    return {"status": "not_observed", "summary": "No meaningful artifact delta observed by supervisor scan."}


def _gate_specificity_status(gate_specificity: Mapping[str, Any]) -> dict[str, Any]:
    status = dict(gate_specificity)
    status["status"] = "blocked" if gate_specificity.get("required") is True else "not_required"
    if gate_specificity.get("required") is True:
        status.setdefault("blocked_reason", "publication_gate_specificity_required")
    return status


def _ai_reviewer_status(ai_reviewer_assessment: Mapping[str, Any]) -> dict[str, Any]:
    if ai_reviewer_assessment.get("present") is True:
        status = "present"
    elif ai_reviewer_assessment.get("missing") is True:
        status = "trace_missing"
    else:
        status = "not_required"
    return {
        "status": status,
        "owner": _text(ai_reviewer_assessment.get("owner")),
        "trace_complete": ai_reviewer_assessment.get("present") is True,
        "blocked_reason": "ai_reviewer_assessment_required" if ai_reviewer_assessment.get("missing") is True else None,
    }


def _repair_action_payload(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json")


def _first_repair_action(repair_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if _text(repair_payload.get("state")) != "ready_for_repair":
        return None
    actions = repair_payload.get("actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if isinstance(action, Mapping):
            return dict(action)
    return None


def _sanitize_repair_action_for_supervision(action: Mapping[str, Any]) -> dict[str, Any]:
    sanitized = dict(action)
    sanitized["paper_package_mutation_allowed"] = False
    sanitized["manual_study_patch_allowed"] = False
    sanitized["quality_gate_relaxation_allowed"] = False
    sanitized["medical_claim_authoring_allowed"] = False
    sanitized["requested_write_surfaces"] = list(SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES)
    sanitized["forbidden_actions"] = list(SUPERVISION_FORBIDDEN_ACTIONS)
    return sanitized


def _blocked_lifecycle_from_repair(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    repair_payload: Mapping[str, Any],
    blocked_reason: str,
    next_owner: str,
) -> dict[str, Any] | None:
    action = _first_repair_action(repair_payload)
    if action is None:
        return None
    safe_action = _sanitize_repair_action_for_supervision(action)
    authority = "external_supervisor" if next_owner == "external_supervisor" else "observability_only"
    payload = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": _text(repair_payload.get("study_id")) or study_id,
        "quest_id": _text(repair_payload.get("quest_id")) or quest_id,
        "state": "blocked",
        "authority": authority,
        "allowed_write_surfaces": list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
        "forbidden_actions": list(SUPERVISION_FORBIDDEN_ACTIONS),
        "top_action": safe_action,
        "auto_apply_allowed": bool(safe_action.get("auto_apply_allowed")),
        "last_apply_attempt_at": _utc_now(),
        "applied_at": None,
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": True,
        "quality_gate_relaxation_allowed": False,
        "last_apply_attempt": {
            "state": "blocked",
            "dispatch_status": "not_dispatched",
            "reason": blocked_reason,
            "source": "runtime_supervisor_scan",
        },
        "refs": {
            "repair_action_path": str(study_root / "artifacts" / "autonomy" / "repair_actions" / "latest.json"),
        },
    }
    _write_json(study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json", payload)
    return payload


def _publication_eval_source_action(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any]:
    actions = publication_eval_payload.get("recommended_actions")
    if isinstance(actions, list):
        for action in actions:
            if isinstance(action, Mapping):
                return dict(action)
    return {
        "action_id": "publication-gate-specificity-required",
        "next_work_unit": {"unit_id": "gate_needs_specificity"},
        "work_unit_fingerprint": "publication-blockers::specificity_required",
    }


def _materialize_request_packets(
    *,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    actions: list[dict[str, Any]],
) -> None:
    action_types = {_text(action.get("action_type")) for action in actions}
    if "publication_gate_specificity_required" in action_types:
        packet = supervisor_action_requests.build_publication_gate_specificity_request(
            study_id=study_id,
            quest_id=quest_id,
            source_surface="publication_eval/latest.json",
            source_action=_publication_eval_source_action(publication_eval_payload),
            blocking_gaps=[],
        )
        packet["required_target_kinds"] = list(packet.get("requested_target_types") or [])
        _write_json(
            study_root / "artifacts" / "supervision" / "requests" / "publication_gate_specificity" / "latest.json",
            packet,
        )
    if "return_to_ai_reviewer_workflow" in action_types:
        packet = supervisor_action_requests.build_ai_reviewer_publication_eval_request(
            study_id=study_id,
            quest_id=quest_id,
            source_surface="runtime_supervisor_scan",
            workflow_state={
                "quality_authority": {
                    "owner": _text(_mapping(publication_eval_payload.get("assessment_provenance")).get("owner")),
                    "state": "projection_only",
                },
                "route_back": {
                    "required": True,
                    "target": "ai_reviewer",
                },
                "blockers": ["publication_eval_not_ai_reviewer_authority"],
            },
        )
        packet["target_assessment_owner"] = "ai_reviewer"
        packet["may_authorize_quality_gate"] = False
        _write_json(study_root / "artifacts" / "supervision" / "requests" / "ai_reviewer" / "latest.json", packet)


def _blocked_reason_from_scan(
    *,
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
) -> str | None:
    for action in actions:
        if _text(action.get("action_type")) in {
            "runtime_platform_repair",
            "publication_gate_specificity_required",
            "return_to_ai_reviewer_workflow",
        }:
            return _text(action.get("reason")) or _text(action.get("action_type"))
    if gate_specificity.get("required") is True:
        return "publication_gate_specificity_required"
    if ai_reviewer_assessment.get("missing") is True:
        return "ai_reviewer_assessment_required"
    return None


def _next_owner_for_blocked_reason(blocked_reason: str | None) -> str:
    if blocked_reason == "publication_gate_specificity_required":
        return "publication_gate"
    if blocked_reason == "ai_reviewer_assessment_required":
        return "ai_reviewer"
    return "external_supervisor"


def _study_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply_safe_actions: bool,
    developer_mode: DeveloperSupervisorMode,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    status = study_runtime_router.study_runtime_status(profile=profile, study_id=study_id, study_root=study_root)
    progress = study_progress.read_study_progress(profile=profile, study_id=study_id, study_root=study_root)
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    resolved_quest_id = _text(status_payload.get("quest_id")) or _text(progress_payload.get("quest_id"))
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
        study_id=study_id,
        quest_id=resolved_quest_id,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    if developer_mode.mode == "external_observe":
        actions = []
    lifecycle = _mapping(progress_payload.get("ai_repair_lifecycle"))
    blocked_reason_from_scan = _blocked_reason_from_scan(
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    if developer_mode.safe_actions_enabled and (
        not lifecycle
        or (
            blocked_reason_from_scan is not None
            and (
                lifecycle.get("projection_only") is True
                or _text(lifecycle.get("blocked_reason")) != blocked_reason_from_scan
            )
        )
    ):
        repair_payload = _repair_action_payload(study_root=study_root)
        if repair_payload is not None:
            if blocked_reason_from_scan is not None:
                lifecycle = _blocked_lifecycle_from_repair(
                    study_root=study_root,
                    study_id=study_id,
                    quest_id=resolved_quest_id,
                    repair_payload=repair_payload,
                    blocked_reason=blocked_reason_from_scan,
                    next_owner=_next_owner_for_blocked_reason(blocked_reason_from_scan),
                ) or {}
    if developer_mode.safe_actions_enabled:
        _materialize_request_packets(
            study_root=study_root,
            study_id=study_id,
            quest_id=resolved_quest_id,
            publication_eval_payload=publication_eval_payload,
            actions=actions,
        )
    why_not_applied = _why_not_applied(status=status_payload, progress=progress_payload, actions=actions)
    if why_not_applied is None and lifecycle:
        why_not_applied = _text(lifecycle.get("blocked_reason"))
    external_supervisor_required = bool(
        lifecycle.get("external_supervisor_required")
        or any(_text(action.get("authority")) == "external_supervisor" for action in actions)
    )
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if why_not_applied is not None and any(_text(action.get("reason")) == why_not_applied for action in actions):
        blocked_reason = why_not_applied
    next_owner = _next_owner_for_blocked_reason(blocked_reason) if blocked_reason else _text(lifecycle.get("next_owner"))
    supervision = _mapping(progress_payload.get("supervision"))
    return {
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": resolved_quest_id,
        "quest_root": _text(status_payload.get("quest_root")) or _text(progress_payload.get("quest_root")),
        "quest_status": _text(status_payload.get("quest_status")),
        "current_stage": _text(progress_payload.get("current_stage")),
        "active_run_id": _active_run_id(status_payload, progress_payload),
        "supervision_url": _text(supervision.get("browser_url")),
        "paper_stage": _text(progress_payload.get("paper_stage")),
        "runtime_health": _mapping(status_payload.get("runtime_health_snapshot"))
        or _mapping(progress_payload.get("runtime_health_snapshot")),
        "meaningful_artifact_delta": bool(progress_payload.get("last_meaningful_progress_at")),
        "artifact_delta": _artifact_delta(progress_payload),
        "gate_specificity": _gate_specificity_status(gate_specificity),
        "ai_reviewer_assessment": ai_reviewer_assessment,
        "ai_reviewer_status": _ai_reviewer_status(ai_reviewer_assessment),
        "ai_repair_lifecycle": lifecycle or None,
        "action_queue": actions,
        "why_not_applied": why_not_applied,
        "why_not_applied_timeline": _why_not_applied_timeline(why_not_applied),
        "escalation_reason": why_not_applied,
        "next_owner": next_owner or ("external_supervisor" if external_supervisor_required else None),
        "blocked_reason": blocked_reason or why_not_applied,
        "external_supervisor_required": external_supervisor_required,
        "supervisor_only": _supervisor_only(status_payload, progress_payload),
        "paper_package_mutated": False,
        "apply_safe_actions": developer_mode.safe_actions_enabled,
        "developer_supervisor_mode": developer_mode.to_dict(),
    }


def supervisor_scan(
    *,
    profile: WorkspaceProfile,
    study_ids: Iterable[str],
    apply_safe_actions: bool = False,
    developer_supervisor_mode: str | None = None,
) -> dict[str, Any]:
    resolved_study_ids = tuple(study_id for item in study_ids if (study_id := _text(item)) is not None)
    generated_at = _utc_now()
    developer_mode = resolve_developer_supervisor_mode(
        profile=profile,
        requested_mode=developer_supervisor_mode,
        apply_safe_actions=apply_safe_actions,
        scheduler_owner="portable_supervisor",
    )
    latest_path = _latest_path(profile)
    history_path = _history_path(profile)
    previous_payload = _read_json_object(latest_path)
    previous_action_ids = {
        _text(action.get("action_id"))
        for action in (_mapping(previous_payload).get("action_queue") if previous_payload is not None else []) or []
        if isinstance(action, Mapping)
    }
    previous_action_ids.discard(None)
    studies = [
        _study_projection(
            profile=profile,
            study_id=study_id,
            apply_safe_actions=apply_safe_actions,
            developer_mode=developer_mode,
        )
        for study_id in resolved_study_ids
    ]
    action_queue = [
        {"study_id": study["study_id"], **action}
        for study in studies
        for action in study.get("action_queue", [])
        if isinstance(action, Mapping)
    ]
    for study in studies:
        study_actions = [
            action
            for action in study.get("action_queue", [])
            if isinstance(action, Mapping) and _text(action.get("action_id")) is not None
        ]
        study["scan_delta"] = {
            "previous_scan_seen": any(_text(action.get("action_id")) in previous_action_ids for action in study_actions),
            "new_action_count": sum(_text(action.get("action_id")) not in previous_action_ids for action in study_actions),
        }
    queue_history = {
        "history_path": str(history_path),
        "latest_action_count": len(action_queue),
        "previous_action_count": len(previous_action_ids),
    }
    payload = {
        "surface": "portable_runtime_supervisor_scan",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "scheduler_contract": {
            "codex_app_heartbeat_required": False,
            "supported_schedulers": ["systemd_user", "cron", "docker_one_shot", "launchd"],
            "developer_supervisor_mode": developer_mode.to_dict(),
        },
        "developer_supervisor_mode": developer_mode.to_dict(),
        "apply_safe_actions": developer_mode.safe_actions_enabled,
        "studies": studies,
        "action_queue": action_queue,
        "queue_history": queue_history,
        "refs": {"latest_path": str(latest_path), "history_path": str(history_path)},
    }
    _write_json(latest_path, payload)
    _append_json_line(
        history_path,
        {
            "generated_at": generated_at,
            "study_ids": list(resolved_study_ids),
            "action_ids": [_text(action.get("action_id")) for action in action_queue],
            "latest_action_count": len(action_queue),
        },
    )
    return payload


__all__ = [
    "SCHEMA_VERSION",
    "SUPERVISION_LATEST_RELATIVE_PATH",
    "supervisor_scan",
]
