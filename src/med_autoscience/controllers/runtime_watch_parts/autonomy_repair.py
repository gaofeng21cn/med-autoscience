from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor
from med_autoscience.profiles import WorkspaceProfile


AI_DOCTOR_REPAIR_SOURCE = "runtime_watch_ai_doctor_repair"
AUTO_APPLY_CONTROLLER_REPAIR_KINDS = frozenset(
    {
        "analysis_claim_evidence_redrive",
        "bounded_work_unit_redrive",
    }
)
EXECUTED_RUNTIME_RECOVERY_DECISIONS = frozenset(
    {
        "create_and_start",
        "create_only",
        "resume",
        "relaunch_stopped",
    }
)
RUNTIME_RECOVERY_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "quest_waiting_on_invalid_blocking",
        "quest_stopped_by_controller_guard",
    }
)
REPAIR_LIFECYCLE_RELATIVE_PATH = Path("artifacts/autonomy/repair_lifecycle/latest.json")
EXTERNAL_SUPERVISOR_BLOCK_REASONS = frozenset(
    {
        "ai_doctor_platform_repair_requires_repo_level_fix",
        "runtime_recovery_not_authorized",
        "publication_gate_specificity_required",
    }
)
SUBMISSION_HANDOFF_GAP_TYPES = frozenset({"delivery", "reporting", "package", "metadata", "administrative"})
SUBMISSION_HANDOFF_TERMS = frozenset(
    {
        "admin",
        "administrative",
        "author",
        "bundle",
        "declaration",
        "handoff",
        "human review",
        "metadata",
        "package",
        "proofing",
        "provenance",
        "submission",
        "title-page",
    }
)
SUBMISSION_HANDOFF_BLOCKING_TERMS = frozenset(
    {
        "analysis",
        "calibration",
        "claim",
        "cohort",
        "endpoint",
        "evidence",
        "evidence gap",
        "external validation",
        "figure",
        "manuscript-body",
        "method",
        "model",
        "result",
        "scientific",
        "statistical",
        "data cleaning",
        "table",
        "validation",
    }
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else None


def _write_json_object(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _read_study_json_object(study_root: Path, relative_path: str) -> dict[str, Any] | None:
    return _read_json_object(Path(study_root).expanduser().resolve() / relative_path)


def _latest_ai_doctor_repair_path(*, study_root: Path) -> Path:
    return autonomy_ai_doctor.repair_actions_root(study_root=study_root) / "latest.json"


def ai_repair_lifecycle_path(*, study_root: Path) -> Path:
    return Path(study_root).expanduser().resolve() / REPAIR_LIFECYCLE_RELATIVE_PATH


def _first_ai_doctor_repair_action(repair_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if _non_empty_text(repair_payload.get("state")) != "ready_for_repair":
        return None
    if repair_payload.get("quality_gate_relaxation_allowed") is True:
        return None
    actions = repair_payload.get("actions")
    if not isinstance(actions, list):
        return None
    for action in actions:
        if isinstance(action, Mapping):
            return dict(action)
    return None


def read_ready_ai_doctor_repair(*, study_root: Path) -> dict[str, Any] | None:
    repair_payload = _read_json_object(_latest_ai_doctor_repair_path(study_root=study_root))
    if repair_payload is None:
        return None
    if _first_ai_doctor_repair_action(repair_payload) is None:
        return None
    return repair_payload


def read_ai_repair_lifecycle(*, study_root: Path) -> dict[str, Any] | None:
    return _read_json_object(ai_repair_lifecycle_path(study_root=study_root))


def _serialize_ai_doctor_repair_result(
    *,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    state: str,
    dispatch_status: str,
    reason: str | None = None,
) -> dict[str, Any]:
    result = {
        "study_id": _non_empty_text(repair_payload.get("study_id")),
        "quest_id": _non_empty_text(repair_payload.get("quest_id")),
        "state": state,
        "action_type": _non_empty_text(action.get("action_type")),
        "repair_kind": _non_empty_text(action.get("repair_kind")),
        "owner": _non_empty_text(action.get("owner")),
        "auto_apply_allowed": bool(action.get("auto_apply_allowed")),
        "quality_gate_relaxation_allowed": False,
        "dispatch_status": dispatch_status,
        "source": AI_DOCTOR_REPAIR_SOURCE,
    }
    if reason is not None:
        result["reason"] = reason
    return result


def _string_items(value: object) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _non_empty_text(item)) is not None}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _quality_dimension_status(*, payload: Mapping[str, Any], dimension: str) -> str | None:
    quality_assessment = _mapping(payload.get("quality_assessment"))
    dimension_payload = _mapping(quality_assessment.get(dimension))
    return _non_empty_text(dimension_payload.get("status"))


def _submission_handoff_gap(gap: object) -> bool:
    if not isinstance(gap, Mapping):
        return False
    severity = _non_empty_text(gap.get("severity"))
    if severity == "optional":
        return True
    if severity != "important":
        return False
    gap_type = _non_empty_text(gap.get("gap_type"))
    if gap_type not in SUBMISSION_HANDOFF_GAP_TYPES:
        return False
    text = " ".join(
        str(value or "").strip().lower()
        for value in (
            gap.get("gap_id"),
            gap.get("gap_type"),
            gap.get("summary"),
        )
        if str(value or "").strip()
    )
    if any(term in text for term in SUBMISSION_HANDOFF_BLOCKING_TERMS):
        return False
    return any(term in text for term in SUBMISSION_HANDOFF_TERMS)


def _publication_eval_has_only_submission_handoff_gaps(publication_eval: Mapping[str, Any]) -> bool:
    gaps = publication_eval.get("gaps")
    if not isinstance(gaps, list):
        return False
    return all(_submission_handoff_gap(gap) for gap in gaps)


def status_is_submission_milestone_parked(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> bool:
    quest_status = _non_empty_text(status_payload.get("quest_status"))
    if quest_status not in {"stopped", "waiting_for_user", "paused"}:
        return False
    if _non_empty_text(status_payload.get("active_run_id")) is not None:
        return False
    continuation = _mapping(status_payload.get("continuation_state"))
    if _non_empty_text(continuation.get("active_run_id")) is not None:
        return False
    publication_eval = _read_study_json_object(study_root, "artifacts/publication_eval/latest.json")
    evaluation_summary = _read_study_json_object(study_root, "artifacts/eval_hygiene/evaluation_summary/latest.json")
    if publication_eval is None or evaluation_summary is None:
        return False
    quality_closure_truth = _mapping(evaluation_summary.get("quality_closure_truth"))
    quality_review_loop = _mapping(evaluation_summary.get("quality_review_loop"))
    closure_state = (
        _non_empty_text(quality_closure_truth.get("state"))
        or _non_empty_text(quality_review_loop.get("closure_state"))
    )
    if closure_state != "bundle_only_remaining":
        return False
    route_target = _non_empty_text(quality_closure_truth.get("route_target"))
    if route_target and route_target != "finalize":
        return False
    verdict = _mapping(publication_eval.get("verdict"))
    if _non_empty_text(verdict.get("overall_verdict")) != "promising":
        return False
    human_review_status = (
        _quality_dimension_status(payload=publication_eval, dimension="human_review_readiness")
        or _quality_dimension_status(payload=evaluation_summary, dimension="human_review_readiness")
    )
    if human_review_status != "ready":
        return False
    return _publication_eval_has_only_submission_handoff_gaps(publication_eval)


def _submission_milestone_park_result(
    *,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
) -> dict[str, Any]:
    return _serialize_ai_doctor_repair_result(
        repair_payload=repair_payload,
        action=action,
        state="parked",
        dispatch_status="not_dispatched",
        reason="submission_milestone_parked",
    )


def _execution_owner_supervisor_only(status_payload: Mapping[str, Any]) -> bool:
    guard = _mapping(status_payload.get("execution_owner_guard"))
    if guard.get("supervisor_only") is True:
        return True
    control_plane = _mapping(status_payload.get("control_plane_snapshot"))
    return "execution_owner_guard.supervisor_only" in _string_items(control_plane.get("blocking_reasons"))


def _runtime_recovery_authorized(status_payload: Mapping[str, Any]) -> bool:
    control_plane = _mapping(status_payload.get("control_plane_snapshot"))
    dispatch_gate = _mapping(control_plane.get("dispatch_gate"))
    if dispatch_gate and (
        _non_empty_text(dispatch_gate.get("state")) != "open"
        or dispatch_gate.get("dispatch_allowed") is not True
    ):
        return False
    route_authorization = _mapping(control_plane.get("route_authorization"))
    return route_authorization.get("runtime_recovery_allowed") is True


def _repair_authorization(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    for key in ("controller_repair_authorization", "controller_repair_authorization_ref"):
        value = payload.get(key)
        if isinstance(value, Mapping):
            return value
    control_plane = _mapping(payload.get("control_plane_snapshot"))
    for key in ("controller_repair_authorization", "controller_repair_authorization_ref"):
        value = control_plane.get(key)
        if isinstance(value, Mapping):
            return value
    return {}


def _repair_authorization_allows_runtime_recovery(payload: Mapping[str, Any]) -> bool:
    authorization = _repair_authorization(payload)
    if not authorization:
        return False
    if authorization.get("authorized") is not True:
        return False
    action = _non_empty_text(authorization.get("action"))
    if action not in {"runtime_recovery", "ensure_study_runtime", "recover_runtime", "relaunch_runtime"}:
        return False
    work_unit_id = _non_empty_text(authorization.get("work_unit_id"))
    if work_unit_id and work_unit_id != "runtime_recovery":
        return False
    return True


def _has_controller_owned_runtime_recovery(status_payload: Mapping[str, Any]) -> bool:
    reason = _non_empty_text(status_payload.get("reason"))
    runtime_health = _mapping(status_payload.get("runtime_health_snapshot"))
    runtime_action = _non_empty_text(runtime_health.get("canonical_runtime_action"))
    attempt_state = _non_empty_text(runtime_health.get("attempt_state"))
    runtime_reasons = _string_items(runtime_health.get("blocking_reasons"))
    if runtime_action in {"recover_runtime", "relaunch_runtime"} and (
        attempt_state in {"recovering", "probe_required"} or "runtime_recovery_retry_budget_exhausted" in runtime_reasons
    ):
        return True
    control_reasons = _string_items(_mapping(status_payload.get("control_plane_snapshot")).get("blocking_reasons"))
    if reason in RUNTIME_RECOVERY_REASONS:
        return True
    if "runtime_recovery_retry_budget_exhausted" in control_reasons:
        return True
    return False


def _status_allows_mas_controller_ai_doctor_repair(status_payload: Mapping[str, Any]) -> bool:
    return (
        _runtime_recovery_authorized(status_payload)
        and _repair_authorization_allows_runtime_recovery(status_payload)
        and _has_controller_owned_runtime_recovery(status_payload)
    )


def status_allows_ai_doctor_repair(status_payload: Mapping[str, Any]) -> bool:
    return (
        not _execution_owner_supervisor_only(status_payload)
        and _status_allows_mas_controller_ai_doctor_repair(status_payload)
    )


def _status_block_reason(status_payload: Mapping[str, Any]) -> str:
    if _execution_owner_supervisor_only(status_payload):
        return "execution_owner_guard_supervisor_only"
    if not _runtime_recovery_authorized(status_payload):
        return "runtime_recovery_not_authorized"
    if not _repair_authorization_allows_runtime_recovery(status_payload):
        return "controller_repair_authorization_missing"
    return "ai_doctor_repair_requires_controller_authorized_runtime_recovery"


def _repair_targets_status(*, repair_payload: Mapping[str, Any], status_payload: Mapping[str, Any]) -> bool:
    repair_study_id = _non_empty_text(repair_payload.get("study_id"))
    repair_quest_id = _non_empty_text(repair_payload.get("quest_id"))
    status_study_id = _non_empty_text(status_payload.get("study_id"))
    status_quest_id = _non_empty_text(status_payload.get("quest_id"))
    return (
        repair_study_id is not None
        and status_study_id is not None
        and repair_study_id == status_study_id
        and repair_quest_id is not None
        and status_quest_id is not None
        and repair_quest_id == status_quest_id
    )


def _runtime_recovery_executed(payload: Mapping[str, Any]) -> bool:
    return _non_empty_text(payload.get("decision")) in EXECUTED_RUNTIME_RECOVERY_DECISIONS


def _runtime_retry_exhausted(payload: Mapping[str, Any]) -> bool:
    runtime_health = _mapping(payload.get("runtime_health_snapshot"))
    control_plane = _mapping(payload.get("control_plane_snapshot"))
    reasons = {
        *_string_items(runtime_health.get("blocking_reasons")),
        *_string_items(control_plane.get("blocking_reasons")),
        *_string_items(_mapping(control_plane.get("dispatch_gate")).get("blocking_reasons")),
    }
    return (
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _non_empty_text(runtime_health.get("attempt_state")) == "escalated"
        or runtime_health.get("retry_budget_remaining") == 0
    )


def _repair_next_owner(*, result: Mapping[str, Any], action: Mapping[str, Any]) -> str | None:
    reason = _non_empty_text(result.get("reason"))
    if reason in EXTERNAL_SUPERVISOR_BLOCK_REASONS:
        return "external_supervisor"
    if reason == "controller_repair_authorization_missing":
        return "mas_controller"
    if reason == "execution_owner_guard_supervisor_only":
        return "supervisor_only"
    owner = _non_empty_text(action.get("owner"))
    return owner or _non_empty_text(result.get("owner"))


def _external_supervisor_required(
    *,
    result: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    runtime_recovery_payload: Mapping[str, Any] | None,
) -> bool:
    if _non_empty_text(result.get("state")) == "parked":
        return False
    if _non_empty_text(result.get("reason")) in EXTERNAL_SUPERVISOR_BLOCK_REASONS:
        return True
    if _runtime_retry_exhausted(status_payload):
        return True
    return bool(runtime_recovery_payload is not None and _runtime_retry_exhausted(runtime_recovery_payload))


def _materialize_ai_repair_lifecycle(
    *,
    study_root: Path,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    result: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    runtime_recovery_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    recorded_at = utc_now()
    external_supervisor_required = _external_supervisor_required(
        result=result,
        status_payload=status_payload,
        runtime_recovery_payload=runtime_recovery_payload,
    )
    result_state = _non_empty_text(result.get("state")) or "blocked"
    state = "external_supervisor_required" if result_state == "blocked" and external_supervisor_required else result_state
    payload = {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": _non_empty_text(repair_payload.get("study_id")) or _non_empty_text(result.get("study_id")),
        "quest_id": _non_empty_text(repair_payload.get("quest_id")) or _non_empty_text(result.get("quest_id")),
        "state": state,
        "top_action": dict(action),
        "auto_apply_allowed": bool(action.get("auto_apply_allowed")),
        "last_apply_attempt_at": recorded_at,
        "applied_at": recorded_at if result_state == "applied" else None,
        "blocked_reason": _non_empty_text(result.get("reason")) if result_state not in {"applied", "parked"} else None,
        "next_owner": (
            "external_supervisor"
            if external_supervisor_required and result_state != "applied"
            else (None if result_state == "parked" else _repair_next_owner(result=result, action=action))
        ),
        "external_supervisor_required": external_supervisor_required and result_state != "applied",
        "quality_gate_relaxation_allowed": False,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "last_apply_attempt": dict(result),
        "refs": {
            "repair_action_path": str(_latest_ai_doctor_repair_path(study_root=study_root)),
        },
    }
    _write_json_object(ai_repair_lifecycle_path(study_root=study_root), payload)
    return payload


def _mark_ai_doctor_repair_applied(
    *,
    repair_path: Path,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
    result: Mapping[str, Any],
) -> None:
    updated = {
        **dict(repair_payload),
        "state": "applied",
        "applied_at": utc_now(),
        "applied_action": dict(action),
        "application_result": dict(result),
        "quality_gate_relaxation_allowed": False,
    }
    _write_json_object(repair_path, updated)


def _apply_ai_doctor_repair_action(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any],
    runtime_recovery_payload: Mapping[str, Any] | None,
    repair_payload: Mapping[str, Any],
    action: Mapping[str, Any],
) -> dict[str, Any]:
    if status_is_submission_milestone_parked(study_root=study_root, status_payload=status_payload):
        return _submission_milestone_park_result(repair_payload=repair_payload, action=action)
    block_reason = _ai_doctor_repair_preflight_block_reason(
        repair_payload=repair_payload,
        status_payload=status_payload,
        action=action,
    )
    if block_reason is not None:
        return _serialize_ai_doctor_repair_result(
            repair_payload=repair_payload,
            action=action,
            state="blocked",
            dispatch_status="not_dispatched",
            reason=block_reason,
        )
    if _runtime_recovery_payload_satisfies_repair(
        repair_payload=repair_payload,
        runtime_recovery_payload=runtime_recovery_payload,
    ):
        return _serialize_ai_doctor_repair_result(
            repair_payload=repair_payload,
            action=action,
            state="applied",
            dispatch_status="executed",
        )
    if not _status_allows_mas_controller_ai_doctor_repair(status_payload):
        return _serialize_ai_doctor_repair_result(
            repair_payload=repair_payload,
            action=action,
            state="blocked",
            dispatch_status="not_dispatched",
            reason=_status_block_reason(status_payload),
        )
    return _serialize_ai_doctor_repair_result(
        repair_payload=repair_payload,
        action=action,
        state="blocked",
        dispatch_status="not_dispatched",
        reason="ai_doctor_repair_requires_executed_runtime_recovery_contract",
    )


def _ai_doctor_repair_preflight_block_reason(
    *,
    repair_payload: Mapping[str, Any],
    status_payload: Mapping[str, Any],
    action: Mapping[str, Any],
) -> str | None:
    action_type = _non_empty_text(action.get("action_type"))
    repair_kind = _non_empty_text(action.get("repair_kind"))
    owner = _non_empty_text(action.get("owner"))
    risk = _non_empty_text(action.get("risk")) or "medium"
    auto_apply_allowed = action.get("auto_apply_allowed") is True
    if not _repair_targets_status(repair_payload=repair_payload, status_payload=status_payload):
        return "ai_doctor_repair_target_mismatch"
    if action_type == "platform_repair":
        return "ai_doctor_platform_repair_requires_repo_level_fix"
    if not auto_apply_allowed or action.get("quality_gate_relaxation_allowed") is True:
        return "ai_doctor_repair_not_auto_applicable"
    if action_type != "controller_repair" or owner != "mas_controller":
        return "ai_doctor_repair_requires_controller_owned_runtime_recovery"
    if repair_kind not in AUTO_APPLY_CONTROLLER_REPAIR_KINDS or risk not in {"low", "medium"}:
        return "ai_doctor_repair_action_not_in_runtime_recovery_allowlist"
    return None


def _runtime_recovery_payload_satisfies_repair(
    *,
    repair_payload: Mapping[str, Any],
    runtime_recovery_payload: Mapping[str, Any] | None,
) -> bool:
    return bool(
        runtime_recovery_payload is not None
        and _repair_targets_status(repair_payload=repair_payload, status_payload=runtime_recovery_payload)
        and _runtime_recovery_executed(runtime_recovery_payload)
        and _status_allows_mas_controller_ai_doctor_repair(runtime_recovery_payload)
    )


def apply_ready_ai_doctor_repair(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: Mapping[str, Any],
    runtime_recovery_payload: Mapping[str, Any] | None = None,
    repair_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    repair_path = _latest_ai_doctor_repair_path(study_root=study_root)
    repair_payload = dict(repair_payload) if isinstance(repair_payload, Mapping) else _read_json_object(repair_path)
    if repair_payload is None:
        return None
    action = _first_ai_doctor_repair_action(repair_payload)
    if action is None:
        return None
    result = _apply_ai_doctor_repair_action(
        profile=profile,
        study_root=study_root,
        status_payload=status_payload,
        runtime_recovery_payload=runtime_recovery_payload,
        repair_payload=repair_payload,
        action=action,
    )
    if result.get("state") == "applied":
        _mark_ai_doctor_repair_applied(
            repair_path=repair_path,
            repair_payload=repair_payload,
            action=action,
            result=result,
        )
    _materialize_ai_repair_lifecycle(
        study_root=study_root,
        repair_payload=repair_payload,
        action=action,
        result=result,
        status_payload=status_payload,
        runtime_recovery_payload=runtime_recovery_payload,
    )
    return result


__all__ = [
    "AI_DOCTOR_REPAIR_SOURCE",
    "REPAIR_LIFECYCLE_RELATIVE_PATH",
    "ai_repair_lifecycle_path",
    "apply_ready_ai_doctor_repair",
    "read_ai_repair_lifecycle",
    "read_ready_ai_doctor_repair",
]
