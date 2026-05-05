from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_ai_repair_policy import two_layer_ai_repair_policy_payload
from med_autoscience.controllers import study_progress, study_runtime_router
from med_autoscience.controllers.runtime_supervisor_scan_parts import gate_specificity as gate_specificity_part
from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair
from med_autoscience.controllers.runtime_supervisor_scan_parts import queue_slo
from med_autoscience.controllers.runtime_supervisor_scan_parts import request_packets
from med_autoscience.controllers.runtime_supervisor_scan_parts import submission_milestone_parking
from med_autoscience.controllers.runtime_supervisor_scan_parts import submission_milestone_projection
from med_autoscience.developer_supervisor_mode import (
    DeveloperSupervisorMode,
    resolve_developer_supervisor_mode,
)
from med_autoscience.profiles import WorkspaceProfile


SCHEMA_VERSION = 1
OWNER_PICKUP_OVERDUE_HOURS = 2
DEVELOPER_SUPERVISOR_ATTENTION_HOURS = 6
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


def resolve_supervisor_scan_study_ids(profile: WorkspaceProfile) -> tuple[str, ...]:
    if not profile.studies_root.is_dir():
        return ()
    study_ids: list[str] = []
    for child in sorted(profile.studies_root.iterdir(), key=lambda item: item.name):
        if not child.is_dir():
            continue
        if any((child / marker).is_file() for marker in ("study.yaml", "study.yml", "study.toml")):
            study_ids.append(child.name)
    return tuple(study_ids)


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


def _parse_utc_datetime(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _duration_hours(*, start_at: object, end_at: object) -> float:
    start = _parse_utc_datetime(start_at)
    end = _parse_utc_datetime(end_at)
    if start is None or end is None or end < start:
        return 0.0
    return round((end - start).total_seconds() / 3600, 3)


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
    return _text(next_work_unit.get("unit_id")) in platform_repair.SPECIFICITY_WORK_UNIT_IDS


def _publication_gate_specificity_required(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return gate_specificity_part.publication_gate_specificity_required(
        status=status,
        progress=progress,
        publication_eval_payload=publication_eval_payload,
        blocking_reasons=_blocking_reasons(status, progress),
    )


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


def _owner_from_action(action: Mapping[str, Any]) -> str | None:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _text(handoff_packet.get("next_executable_owner"))
    )


def _handoff_packet(*, study_id: str, quest_id: str | None, action: Mapping[str, Any]) -> dict[str, Any]:
    authority = _text(action.get("authority")) or "observability_only"
    owner = _owner_from_action(action)
    recommended_owner = owner or (
        "external_engineering_agent"
        if authority == "external_supervisor"
        else authority
    )
    return {
        "packet_type": "external_supervisor_handoff",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": _text(action.get("action_type")),
        "reason": _text(action.get("reason")) or _text(action.get("action_type")),
        "authority": authority,
        "owner": owner,
        "request_owner": _text(action.get("request_owner")) or owner,
        "recommended_owner": recommended_owner,
        "next_executable_owner": recommended_owner,
        "supervisor_authority_boundary": "request_only" if authority == "observability_only" else "control_handoff",
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
                "owner": "external_engineering_agent",
                "recommended_owner": "external_engineering_agent",
                "reason": "runtime_recovery_retry_budget_exhausted",
                "summary": "Runtime recovery retry budget is exhausted and no live worker is attached.",
                "paper_package_mutation_allowed": False,
            }
        )
    if gate_specificity.get("required") is True:
        missing_target_kinds = _string_items(gate_specificity.get("missing_target_kinds")) or [
            "claim",
            "figure",
            "table",
            "metric",
            "source_path",
        ]
        actions.append(
            {
                "action_type": "publication_gate_specificity_required",
                "authority": "observability_only",
                "owner": "publication_gate",
                "request_owner": "publication_gate",
                "recommended_owner": "publication_gate",
                "reason": "publication_gate_specificity_required",
                "summary": "Publication gate must name concrete claim/figure/table/metric/source_path targets.",
                "required_target_kinds": ["claim", "figure", "table", "metric", "source_path"],
                "missing_target_kinds": missing_target_kinds,
                "gate_owner": _text(gate_specificity.get("gate_owner")) or "publication_gate",
                "next_controller_write": _mapping(gate_specificity.get("next_controller_write")),
                "paper_package_mutation_allowed": False,
            }
        )
    if ai_reviewer_assessment.get("missing") is True:
        actions.append(
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "authority": "observability_only",
                "owner": "ai_reviewer",
                "request_owner": "ai_reviewer",
                "recommended_owner": "ai_reviewer",
                "reason": "ai_reviewer_assessment_required",
                "summary": "Request an AI reviewer-owned publication_eval assessment.",
                "required_output_surface": "artifacts/publication_eval/latest.json",
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
    return gate_specificity_part.gate_specificity_status(gate_specificity)


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


def _read_study_projection_inputs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
) -> tuple[dict[str, Any], dict[str, Any], str | None, dict[str, Any]]:
    status = study_runtime_router.study_runtime_status(profile=profile, study_id=study_id, study_root=study_root)
    progress = study_progress.read_study_progress(profile=profile, study_id=study_id, study_root=study_root)
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    resolved_quest_id = _text(status_payload.get("quest_id")) or _text(progress_payload.get("quest_id"))
    publication_eval_payload = _publication_eval_payload(status_payload, progress_payload)
    return status_payload, progress_payload, resolved_quest_id, publication_eval_payload


def _maybe_blocked_lifecycle_from_scan(
    *,
    developer_mode: DeveloperSupervisorMode,
    lifecycle: Mapping[str, Any],
    actions: list[dict[str, Any]],
    gate_specificity: Mapping[str, Any],
    ai_reviewer_assessment: Mapping[str, Any],
    study_root: Path,
    study_id: str,
    quest_id: str | None,
) -> Mapping[str, Any]:
    blocked_reason = _blocked_reason_from_scan(
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
    )
    if not _should_refresh_blocked_lifecycle(
        developer_mode=developer_mode,
        lifecycle=lifecycle,
        blocked_reason=blocked_reason,
    ):
        return lifecycle
    repair_payload = _repair_action_payload(study_root=study_root)
    if repair_payload is None or blocked_reason is None:
        return lifecycle
    return _blocked_lifecycle_from_repair(
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        repair_payload=repair_payload,
        blocked_reason=blocked_reason,
        next_owner=_next_owner_for_blocked_reason(blocked_reason),
    ) or {}


def _should_refresh_blocked_lifecycle(
    *,
    developer_mode: DeveloperSupervisorMode,
    lifecycle: Mapping[str, Any],
    blocked_reason: str | None,
) -> bool:
    if not developer_mode.safe_actions_enabled:
        return False
    if not lifecycle:
        return True
    return bool(
        blocked_reason is not None
        and (
            lifecycle.get("projection_only") is True
            or _text(lifecycle.get("blocked_reason")) != blocked_reason
        )
    )


def _apply_runtime_platform_repair_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    apply_runtime_platform_repair: bool,
    submission_milestone_parked: bool,
) -> tuple[dict[str, Any] | None, Mapping[str, Any] | None]:
    apply_result = platform_repair.apply_runtime_platform_repair(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status=status_payload,
        progress=progress_payload,
        publication_eval_payload=publication_eval_payload,
        developer_mode=developer_mode,
        enabled=apply_runtime_platform_repair,
        repair_required=(
            not submission_milestone_parked
            and _runtime_platform_repair_required(status_payload, progress_payload)
        ),
    )
    if apply_result is None:
        return None, None
    lifecycle = platform_repair.write_runtime_platform_repair_lifecycle(
        study_root=study_root,
        supervision_latest_relative_path=SUPERVISION_LATEST_RELATIVE_PATH,
        study_id=study_id,
        quest_id=quest_id,
        apply_result=apply_result,
    )
    return apply_result, lifecycle


def _resolve_why_not_applied(
    *,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    actions: list[dict[str, Any]],
    lifecycle: Mapping[str, Any],
    runtime_platform_repair_apply: Mapping[str, Any] | None,
    submission_milestone_parked: bool,
) -> str | None:
    why_not_applied = _why_not_applied(status=status_payload, progress=progress_payload, actions=actions)
    if runtime_platform_repair_apply is not None and _text(runtime_platform_repair_apply.get("dispatch_status")) == "applied":
        return None
    if submission_milestone_parked:
        return None
    if why_not_applied is None and lifecycle:
        return _text(lifecycle.get("blocked_reason"))
    return why_not_applied


def _projection_block_state(
    *,
    lifecycle: Mapping[str, Any],
    actions: list[dict[str, Any]],
    why_not_applied: str | None,
) -> dict[str, Any]:
    external_supervisor_required = bool(
        lifecycle.get("external_supervisor_required")
        or any(_text(action.get("authority")) == "external_supervisor" for action in actions)
    )
    blocked_reason = _text(lifecycle.get("blocked_reason"))
    if why_not_applied is not None and any(_text(action.get("reason")) == why_not_applied for action in actions):
        blocked_reason = why_not_applied
    next_owner = _next_owner_for_blocked_reason(blocked_reason) if blocked_reason else _text(lifecycle.get("next_owner"))
    return {
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": external_supervisor_required,
    }


def _study_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    apply_safe_actions: bool,
    apply_runtime_platform_repair: bool,
    developer_mode: DeveloperSupervisorMode,
) -> dict[str, Any]:
    study_root = _study_root(profile, study_id)
    status_payload, progress_payload, resolved_quest_id, publication_eval_payload = _read_study_projection_inputs(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    submission_milestone_parked_refresh = submission_milestone_projection.refresh_if_platform_repair_required(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload=status_payload,
        developer_mode=developer_mode,
        enabled=developer_mode.safe_actions_enabled,
        runtime_platform_repair_required=_runtime_platform_repair_required(status_payload, progress_payload),
    )
    if submission_milestone_projection.applied(submission_milestone_parked_refresh):
        status_payload, progress_payload, resolved_quest_id, publication_eval_payload = _read_study_projection_inputs(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
        )
    if submission_milestone_parked_refresh is None:
        submission_milestone_parked_refresh = submission_milestone_projection.reconcile_stopped_parking(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            status_payload=status_payload,
            developer_mode=developer_mode,
            enabled=developer_mode.safe_actions_enabled,
        )
        if submission_milestone_projection.applied(submission_milestone_parked_refresh):
            progress_payload = _mapping(
                study_progress.read_study_progress(profile=profile, study_id=study_id, study_root=study_root)
            )
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
    lifecycle = _mapping(_maybe_blocked_lifecycle_from_scan(
        developer_mode=developer_mode,
        lifecycle=lifecycle,
        actions=actions,
        gate_specificity=gate_specificity,
        ai_reviewer_assessment=ai_reviewer_assessment,
        study_root=study_root,
        study_id=study_id,
        quest_id=resolved_quest_id,
    ))
    if developer_mode.safe_actions_enabled:
        request_packets.materialize_request_packets(
            study_root=study_root,
            study_id=study_id,
            quest_id=resolved_quest_id,
            publication_eval_payload=publication_eval_payload,
            actions=actions,
        )
    submission_milestone_parked = (
        _text(_mapping(submission_milestone_parked_refresh).get("dispatch_status")) == "applied"
    )
    if submission_milestone_parked:
        lifecycle = _mapping(_mapping(submission_milestone_parked_refresh).get("repair_lifecycle"))
    runtime_platform_repair_apply, platform_lifecycle = _apply_runtime_platform_repair_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=resolved_quest_id,
        status_payload=status_payload,
        progress_payload=progress_payload,
        publication_eval_payload=publication_eval_payload,
        developer_mode=developer_mode,
        apply_runtime_platform_repair=apply_runtime_platform_repair,
        submission_milestone_parked=submission_milestone_parked,
    )
    if platform_lifecycle is not None:
        lifecycle = _mapping(platform_lifecycle)
    why_not_applied = _resolve_why_not_applied(
        status_payload=status_payload,
        progress_payload=progress_payload,
        actions=actions,
        lifecycle=lifecycle,
        runtime_platform_repair_apply=runtime_platform_repair_apply,
        submission_milestone_parked=submission_milestone_parked,
    )
    block_state = _projection_block_state(
        lifecycle=lifecycle,
        actions=actions,
        why_not_applied=why_not_applied,
    )
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
        "submission_milestone_parked_refresh": submission_milestone_parked_refresh,
        "runtime_platform_repair_apply": runtime_platform_repair_apply,
        "why_not_applied": why_not_applied,
        "why_not_applied_timeline": _why_not_applied_timeline(why_not_applied),
        "escalation_reason": why_not_applied,
        "next_owner": block_state["next_owner"]
        or ("external_supervisor" if block_state["external_supervisor_required"] else None),
        "blocked_reason": block_state["blocked_reason"] or why_not_applied,
        "external_supervisor_required": block_state["external_supervisor_required"],
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
    apply_runtime_platform_repair: bool = False,
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
            apply_runtime_platform_repair=apply_runtime_platform_repair,
            developer_mode=developer_mode,
        )
        for study_id in resolved_study_ids
    ]
    queue_slo_payload = queue_slo.decorate_action_queue_slo(
        studies=studies,
        previous_payload=previous_payload,
        generated_at=generated_at,
    )
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
            "owner_pickup_overdue_count": int(_mapping(study.get("queue_slo")).get("owner_pickup_overdue_count") or 0),
            "developer_supervisor_attention_required_count": int(
                _mapping(study.get("queue_slo")).get("developer_supervisor_attention_required_count") or 0
            ),
        }
    queue_history = {
        "history_path": str(history_path),
        "latest_action_count": len(action_queue),
        "previous_action_count": len(previous_action_ids),
        **queue_slo_payload,
    }
    payload = {
        "surface": "portable_runtime_supervisor_scan",
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "workspace_root": str(profile.workspace_root),
        "scheduler_contract": {
            "codex_app_heartbeat_required": False,
            "supported_schedulers": ["systemd_user", "cron", "launchd", "external_container_scheduler"],
            "developer_supervisor_mode": developer_mode.to_dict(),
        },
        "developer_supervisor_mode": developer_mode.to_dict(),
        "apply_safe_actions": developer_mode.safe_actions_enabled,
        "apply_runtime_platform_repair": bool(apply_runtime_platform_repair),
        "two_layer_ai_repair_policy": two_layer_ai_repair_policy_payload(),
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
