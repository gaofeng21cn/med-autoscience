from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner
from med_autoscience.controllers.runtime_supervisor_scan_parts import abnormal_stopped_runtime
from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_current_controller
from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair_closeout_redrive
from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair_owner_handoff_redrive
from med_autoscience.controllers.runtime_supervisor_scan_parts import platform_repair_pending_redrive
from med_autoscience.controllers.runtime_supervisor_scan_parts import runtime_facts
from med_autoscience.controllers import study_runtime_router
from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile
from .platform_repair_lifecycle import (
    write_runtime_platform_repair_lifecycle as _write_runtime_platform_repair_lifecycle,
)


SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/**",
    "artifacts/autonomy/repair_lifecycle/latest.json",
    "artifacts/autonomy/repair_actions/latest.json",
]
RUNTIME_PLATFORM_REPAIR_ALLOWED_WRITE_SURFACES = [
    *SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES,
    "quest_root/.ds/runtime_state.json",
    "quest_root/.ds/events.jsonl",
    "artifacts/runtime/**",
]
SUPERVISION_FORBIDDEN_ACTIONS = [
    "paper_package_mutation",
    "manual_study_patch",
    "quality_gate_relaxation",
    "medical_claim_authoring",
]
RUNTIME_PLATFORM_REPAIR_SOURCE = "runtime_supervisor_scan_platform_repair"
SPECIFICITY_WORK_UNIT_IDS = platform_repair_closeout_redrive.SPECIFICITY_WORK_UNIT_IDS
CONCRETE_BUNDLE_STAGE_REQUIRED_ACTIONS = {
    "complete_bundle_stage",
    "continue_bundle_stage",
    "continue_write_stage",
}
CONCRETE_BUNDLE_STAGE_SUPERVISOR_PHASES = {
    "bundle_stage_blocked",
    "bundle_stage_ready",
    "write_stage_ready",
}
PACKAGE_FRESHNESS_TERMINAL_REASONS = platform_repair_closeout_redrive.PACKAGE_FRESHNESS_TERMINAL_REASONS
DOWNSTREAM_PACKAGE_FRESHNESS_WORK_UNIT_IDS = {
    "publication_gate_replay",
    "submission_authority_sync_closure",
    "submission_delivery_sync_closure",
    "submission_minimal_refresh",
}


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


def _next_work_unit_needs_specificity(value: object) -> bool:
    return platform_repair_closeout_redrive._next_work_unit_needs_specificity(value)


def _recommended_actions_need_specificity(value: object) -> bool:
    return platform_repair_closeout_redrive._recommended_actions_need_specificity(value)


def _publication_eval_specificity_targets_complete(publication_eval_payload: Mapping[str, Any]) -> bool:
    return platform_repair_closeout_redrive.publication_eval_specificity_targets_complete(publication_eval_payload)


def _runtime_state_path(quest_root: str | None) -> Path | None:
    if quest_root is None:
        return None
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _runtime_state_has_stale_specificity_terminal(runtime_state: Mapping[str, Any]) -> bool:
    return platform_repair_closeout_redrive.runtime_state_has_stale_specificity_terminal(runtime_state)


def _runtime_state_has_controller_terminal(runtime_state: Mapping[str, Any]) -> bool:
    return platform_repair_closeout_redrive.runtime_state_has_controller_terminal(runtime_state)


def _resume_result_active_run_id(resume_result: Mapping[str, Any]) -> str | None:
    runtime_liveness = _mapping(resume_result.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    snapshot = _mapping(resume_result.get("snapshot"))
    postcondition = _mapping(resume_result.get("resume_postcondition"))
    for value in (
        resume_result.get("active_run_id"),
        postcondition.get("active_run_id"),
        runtime_liveness.get("active_run_id"),
        runtime_audit.get("active_run_id"),
        snapshot.get("active_run_id"),
    ):
        if text := _text(value):
            return text
    return None


def _resume_result_worker_running(resume_result: Mapping[str, Any]) -> bool:
    runtime_liveness = _mapping(resume_result.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    if runtime_audit.get("worker_running") is False:
        return False
    if runtime_liveness.get("worker_running") is False:
        return False
    return bool(runtime_audit.get("worker_running") or runtime_liveness.get("worker_running"))


def _controller_authorization_points_to_upstream_work_unit(
    controller_authorization: Mapping[str, Any] | None,
) -> bool:
    return platform_current_controller.controller_authorization_points_to_upstream_work_unit(
        controller_authorization
    )


def _runtime_relaunch_postcondition_failure(
    resume_result: Mapping[str, Any],
    *,
    controller_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    postcondition = _mapping(resume_result.get("resume_postcondition"))
    terminal_markers = {
        _text(resume_result.get("blocked_reason")),
        _text(resume_result.get("terminal_reason")),
        _text(postcondition.get("blocked_reason")),
        _text(postcondition.get("terminal_reason")),
    }
    if any(marker in SPECIFICITY_WORK_UNIT_IDS for marker in terminal_markers):
        return {
            "reason": "publication_gate_specificity_required",
            "resume_postcondition": postcondition or None,
        }
    if any(marker in PACKAGE_FRESHNESS_TERMINAL_REASONS for marker in terminal_markers):
        if _controller_authorization_points_to_upstream_work_unit(controller_authorization):
            return {
                "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON,
                "resume_postcondition": postcondition or None,
            }
        return {
            "reason": "current_package_freshness_required",
            "resume_postcondition": postcondition or None,
        }
    if postcondition and postcondition.get("effective") is not True:
        return {
            "reason": "runtime_relaunch_no_live_run_started",
            "resume_postcondition": postcondition,
        }
    if _resume_result_active_run_id(resume_result) is None and not _resume_result_worker_running(resume_result):
        return {
            "reason": "runtime_relaunch_no_live_run_started",
            "resume_postcondition": postcondition or None,
        }
    return None


def _apply_abnormal_stopped_runtime_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    base: Mapping[str, Any],
    repair_kind: str,
    controller_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    allow_stopped_relaunch = repair_kind in {
        "abnormal_stopped_runtime_relaunch",
        "failed_non_resumable_relaunch",
    }
    try:
        resume_result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            allow_stopped_relaunch=allow_stopped_relaunch,
            source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        )
    except Exception as exc:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": "abnormal_stopped_runtime_relaunch_failed",
            "repair_kind": repair_kind,
            "error": str(exc),
        }
    resume_payload = dict(resume_result) if isinstance(resume_result, Mapping) else {}
    postcondition_failure = _runtime_relaunch_postcondition_failure(
        resume_payload,
        controller_authorization=controller_authorization,
    )
    if postcondition_failure is not None:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": _text(postcondition_failure.get("reason")),
            "repair_kind": repair_kind,
            "resume_result": resume_payload,
            "resume_postcondition": postcondition_failure.get("resume_postcondition"),
        }
    return {
        **dict(base),
        "dispatch_status": "applied",
        "reason": "abnormal_stopped_runtime_relaunch_requested",
        "repair_kind": repair_kind,
        "resume_result": resume_payload,
    }


def _apply_current_controller_runtime_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
    repair_kind: str,
) -> dict[str, Any]:
    authorization = _write_current_controller_authorization(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
    )
    if authorization is not None and authorization.get("written") is not True:
        if _text(authorization.get("reason")) == "pending_user_messages_present":
            pending_resume = platform_repair_pending_redrive.mark_existing_pending_user_message_redrive(
                runtime_state_path=runtime_state_path,
                study_id=study_id,
                quest_id=quest_id,
                source=RUNTIME_PLATFORM_REPAIR_SOURCE,
            )
            if pending_resume.get("marked") is not True:
                return {
                    **dict(base),
                    "dispatch_status": "blocked",
                    "reason": _text(pending_resume.get("reason")) or "existing_pending_user_message_redrive_not_marked",
                    "repair_kind": repair_kind,
                    "current_controller_authorization": authorization,
                    "existing_pending_user_message_resume": pending_resume,
                }
            apply_result = _apply_abnormal_stopped_runtime_repair(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                base=base,
                repair_kind=repair_kind,
                controller_authorization=None,
            )
            return {
                **apply_result,
                "current_controller_authorization": authorization,
                "current_controller_authorization_written": False,
                "existing_pending_user_message_resume": pending_resume,
            }
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": _text(authorization.get("reason")) or "current_controller_authorization_not_written",
            "repair_kind": repair_kind,
            "current_controller_authorization": authorization,
        }
    apply_result = _apply_abnormal_stopped_runtime_repair(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        base=base,
        repair_kind=repair_kind,
        controller_authorization=authorization,
    )
    if authorization is not None:
        return {
            **apply_result,
            "current_controller_authorization": authorization,
            "current_controller_authorization_written": authorization.get("written") is True,
        }
    return apply_result


def _controller_redrive_result(apply_result: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(apply_result)
    if _text(payload.get("dispatch_status")) is not None:
        payload["reason"] = current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON
    return payload


def _apply_live_activity_timeout_current_controller_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
) -> dict[str, Any]:
    return _controller_redrive_result(
        _apply_current_controller_runtime_redrive(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            runtime_state_path=runtime_state_path,
            quest_id=quest_id,
            publication_eval_payload=publication_eval_payload,
            base={**dict(base), "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON},
            repair_kind="live_activity_timeout_current_controller_redrive",
        )
    )


def _apply_current_controller_owner_handoff_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
) -> dict[str, Any]:
    clear_result = platform_repair_owner_handoff_redrive.clear_current_controller_owner_handoff(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        read_json_object=_read_json_object,
        write_json=_write_json,
        append_json_line=_append_json_line,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
    )
    blocked_turn_closeout_clear = platform_repair_pending_redrive.blocked_turn_closeout_clear_result(
        clear_result
    )
    if clear_result.get("cleared") is not True:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": _text(clear_result.get("reason")) or current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON,
            "repair_kind": "current_controller_owner_handoff_redrive",
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            "owner_handoff_clear": clear_result,
        }
    apply_result = _controller_redrive_result(
        _apply_current_controller_runtime_redrive(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            runtime_state_path=runtime_state_path,
            quest_id=quest_id,
            publication_eval_payload=publication_eval_payload,
            base={**dict(base), "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON},
            repair_kind="current_controller_owner_handoff_redrive",
        )
    )
    return {
        **apply_result,
        "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
        "owner_handoff_clear": clear_result,
    }


def _runtime_platform_repair_redrive_pending(runtime_state: Mapping[str, Any]) -> bool:
    return bool(
        _text(runtime_state.get("continuation_policy")) == "auto"
        and _text(runtime_state.get("continuation_anchor")) == "decision"
        and _text(runtime_state.get("continuation_reason")) == "runtime_platform_repair_redrive"
        and int(runtime_state.get("pending_user_message_count") or 0) == 0
        and not _mapping(runtime_state.get("last_controller_decision_authorization"))
    )


def _apply_pending_runtime_platform_repair_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
) -> dict[str, Any]:
    authorization = platform_current_controller.write_current_controller_authorization(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_object,
        write_json=_write_json,
        append_json_line=_append_json_line,
        continuation_reason="runtime_platform_repair_redrive",
        repair_clear_reason="pending_runtime_platform_repair_redrive",
        allow_specificity_work_unit=True,
    )
    if authorization is None:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": "current_controller_authorization_missing",
            "repair_kind": "pending_runtime_platform_repair_redrive",
            "current_controller_authorization": None,
            "current_controller_authorization_written": False,
        }
    if authorization.get("written") is not True:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": _text(authorization.get("reason")) or "current_controller_authorization_not_written",
            "repair_kind": "pending_runtime_platform_repair_redrive",
            "current_controller_authorization": authorization,
            "current_controller_authorization_written": False,
        }
    try:
        resume_result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        )
    except Exception as exc:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": "resume_after_platform_repair_failed",
            "repair_kind": "pending_runtime_platform_repair_redrive",
            "error": str(exc),
            "current_controller_authorization": authorization,
            "current_controller_authorization_written": True,
        }
    return {
        **dict(base),
        "dispatch_status": "applied",
        "reason": "runtime_platform_repair_redrive_pending_authorization",
        "repair_kind": "pending_runtime_platform_repair_redrive",
        "current_controller_authorization": authorization,
        "current_controller_authorization_written": True,
        "resume_result": dict(resume_result) if isinstance(resume_result, Mapping) else resume_result,
    }


def _publication_gate_ready_for_specificity_redrive(quest_root: str | None) -> dict[str, Any]:
    if quest_root is None:
        return {"ready": False, "clear": False, "reason": "quest_root_missing"}
    report_path = Path(quest_root).expanduser().resolve() / "artifacts" / "reports" / "publishability_gate" / "latest.json"
    payload = _read_json_object(report_path)
    if payload is None:
        return {"ready": False, "clear": False, "reason": "publishability_gate_report_missing"}
    blockers = _string_items(payload.get("blockers"))
    status = _text(payload.get("status"))
    clear = status == "clear" and not blockers
    current_required_action = _text(payload.get("current_required_action"))
    supervisor_phase = _text(payload.get("supervisor_phase"))
    concrete_bundle_stage = (
        bool(blockers)
        and not any(blocker in SPECIFICITY_WORK_UNIT_IDS for blocker in blockers)
        and current_required_action in CONCRETE_BUNDLE_STAGE_REQUIRED_ACTIONS
        and supervisor_phase in CONCRETE_BUNDLE_STAGE_SUPERVISOR_PHASES
    )
    ready = clear or concrete_bundle_stage
    return {
        "ready": ready,
        "clear": clear,
        "status": status,
        "blockers": blockers,
        "current_required_action": current_required_action,
        "supervisor_phase": supervisor_phase,
        "path": str(report_path),
        "reason": None if ready else "publishability_gate_not_ready_for_specificity_redrive",
    }


def _controller_action_types(payload: Mapping[str, Any]) -> set[str]:
    return platform_current_controller.controller_action_types(payload)


def _mapping_has_actionable_controller_target(payload: Mapping[str, Any]) -> bool:
    return platform_current_controller.mapping_has_actionable_controller_target(payload)


def _publication_action_for_work_unit(
    *,
    publication_eval_payload: Mapping[str, Any],
    work_unit_fingerprint: str | None,
) -> dict[str, Any] | None:
    return platform_current_controller.publication_action_for_work_unit(
        publication_eval_payload=publication_eval_payload,
        work_unit_fingerprint=work_unit_fingerprint,
    )


def _current_controller_authorization_payload(
    *,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return platform_current_controller.current_controller_authorization_payload(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_object,
    )


def _write_current_controller_authorization(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return platform_current_controller.write_current_controller_authorization(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_object,
        write_json=_write_json,
        append_json_line=_append_json_line,
    )


def _controller_decision_supersedes_specificity(
    *,
    study_root: Path,
    runtime_state: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return platform_repair_closeout_redrive.controller_decision_supersedes_specificity(
        study_root=study_root,
        runtime_state=runtime_state,
        publication_eval_payload=publication_eval_payload,
    )


def _stale_specificity_redrive_can_apply(
    *,
    study_root: Path,
    quest_root: str | None,
    runtime_state: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> tuple[bool, dict[str, Any], dict[str, Any]]:
    gate_status = _publication_gate_ready_for_specificity_redrive(quest_root)
    supersession = _controller_decision_supersedes_specificity(
        study_root=study_root,
        runtime_state=runtime_state,
        publication_eval_payload=publication_eval_payload,
    )
    if (
        supersession.get("supersedes") is True
        and _text(supersession.get("reason")) == "publication_eval_specificity_targets_complete"
    ):
        return True, gate_status, supersession
    if gate_status.get("ready") is not True:
        return False, gate_status, supersession
    return supersession.get("supersedes") is True, gate_status, supersession


def _clear_stale_controller_runtime_state(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    clear_reason: str,
    allow_pending_user_messages: bool = False,
) -> dict[str, Any]:
    return platform_repair_closeout_redrive.clear_stale_controller_runtime_state(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        clear_reason=clear_reason,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        allow_pending_user_messages=allow_pending_user_messages,
    )


def _clear_stale_specificity_runtime_state(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    allow_pending_user_messages: bool = False,
) -> dict[str, Any]:
    return platform_repair_closeout_redrive.clear_stale_specificity_runtime_state(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        allow_pending_user_messages=allow_pending_user_messages,
    )


def _clear_stale_controller_terminal_for_current_route(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return platform_repair_closeout_redrive.clear_stale_controller_terminal_for_current_route(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
    )


def write_runtime_platform_repair_lifecycle(
    *,
    study_root: Path,
    supervision_latest_relative_path: Path,
    study_id: str,
    quest_id: str | None,
    apply_result: Mapping[str, Any],
) -> dict[str, Any]:
    return _write_runtime_platform_repair_lifecycle(
        study_root=study_root,
        supervision_latest_relative_path=supervision_latest_relative_path,
        study_id=study_id,
        quest_id=quest_id,
        apply_result=apply_result,
        allowed_write_surfaces=RUNTIME_PLATFORM_REPAIR_ALLOWED_WRITE_SURFACES,
        forbidden_actions=SUPERVISION_FORBIDDEN_ACTIONS,
    )


def apply_runtime_platform_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    developer_mode: DeveloperSupervisorMode,
    enabled: bool,
    repair_required: bool,
    gate_specificity: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    if not repair_required:
        return None
    base = {
        "action_type": "runtime_platform_repair",
        "source": RUNTIME_PLATFORM_REPAIR_SOURCE,
        "paper_package_mutation_allowed": False,
        "manual_study_patch_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "medical_claim_authoring_allowed": False,
        "allowed_write_surfaces": list(RUNTIME_PLATFORM_REPAIR_ALLOWED_WRITE_SURFACES),
        "forbidden_actions": list(SUPERVISION_FORBIDDEN_ACTIONS),
    }
    if not enabled:
        return None
    if not developer_mode.safe_actions_enabled:
        return {**base, "dispatch_status": "blocked", "reason": "developer_supervisor_safe_actions_not_enabled"}
    quest_root = _text(status.get("quest_root")) or _text(progress.get("quest_root"))
    runtime_path = _runtime_state_path(quest_root)
    if runtime_path is None:
        return {**base, "dispatch_status": "blocked", "reason": "quest_root_missing"}
    runtime_state = _read_json_object(runtime_path)
    if runtime_state is None:
        return {**base, "dispatch_status": "blocked", "reason": "runtime_state_missing_or_invalid"}
    closeout_redrive = platform_repair_closeout_redrive.apply_if_targets_resolved(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
        runtime_state_path=runtime_path,
        status=status,
        runtime_state=runtime_state,
        gate_specificity=gate_specificity,
        gate_status=_publication_gate_ready_for_specificity_redrive(quest_root),
        publication_eval_payload=publication_eval_payload,
        base=base,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
    )
    if closeout_redrive is not None:
        return closeout_redrive
    if _runtime_platform_repair_redrive_pending(runtime_state):
        return _apply_pending_runtime_platform_repair_redrive(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            runtime_state_path=runtime_path,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            publication_eval_payload=publication_eval_payload,
            base=base,
        )
    if runtime_facts.current_controller_owner_handoff_redrive_required(
        status=status,
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return _apply_current_controller_owner_handoff_redrive(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            runtime_state_path=runtime_path,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            publication_eval_payload=publication_eval_payload,
            base=base,
        )
    pending_platform_redrive = _mapping(status.get("interaction_arbitration"))
    if _text(pending_platform_redrive.get("classification")) == "pending_user_message_redrive":
        pending_resume = platform_repair_pending_redrive.mark_existing_pending_user_message_redrive(
            runtime_state_path=runtime_path,
            study_id=study_id,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        )
        blocked_turn_closeout_clear = platform_repair_pending_redrive.blocked_turn_closeout_clear_result(
            pending_resume
        )
        if pending_resume.get("marked") is not True:
            return {
                **base,
                "dispatch_status": "blocked",
                "reason": _text(pending_resume.get("reason")) or "existing_pending_user_message_redrive_not_marked",
                "existing_pending_user_message_resume": pending_resume,
                "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            }
        try:
            resume_result = study_runtime_router.ensure_study_runtime(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                source=RUNTIME_PLATFORM_REPAIR_SOURCE,
            )
        except Exception as exc:
            return {
                **base,
                "dispatch_status": "blocked",
                "reason": "resume_after_platform_repair_failed",
                "error": str(exc),
                "existing_pending_user_message_resume": pending_resume,
                "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            }
        return {
            **base,
            "dispatch_status": "applied",
            "reason": "stale_blocked_turn_closeout_pending_queue_redrive",
            "existing_pending_user_message_resume": pending_resume,
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            "resume_result": dict(resume_result) if isinstance(resume_result, Mapping) else resume_result,
        }
    if runtime_facts.live_activity_timeout_current_controller_redrive_required(status, progress):
        return _apply_live_activity_timeout_current_controller_redrive(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            runtime_state_path=runtime_path,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            publication_eval_payload=publication_eval_payload,
            base=base,
        )
    abnormal_repair_kind = abnormal_stopped_runtime.repair_kind(status, progress)
    if abnormal_repair_kind is not None:
        stale_redrive_can_apply, _, _ = _stale_specificity_redrive_can_apply(
            study_root=study_root,
            quest_root=quest_root,
            runtime_state=runtime_state,
            publication_eval_payload=publication_eval_payload,
        )
        if not stale_redrive_can_apply:
            stale_controller_clear = _clear_stale_controller_terminal_for_current_route(
                runtime_state_path=runtime_path,
                study_root=study_root,
                study_id=study_id,
                quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
                publication_eval_payload=publication_eval_payload,
            )
            if stale_controller_clear is not None and stale_controller_clear.get("cleared") is True:
                apply_result = _apply_current_controller_runtime_redrive(
                    profile=profile,
                    study_id=study_id,
                    study_root=study_root,
                    runtime_state_path=runtime_path,
                    quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
                    publication_eval_payload=publication_eval_payload,
                    base=base,
                    repair_kind=abnormal_repair_kind,
                )
                return {
                    **apply_result,
                    "stale_controller_terminal_clear": stale_controller_clear,
                    "stale_controller_terminal_cleared": True,
                }
            return _apply_current_controller_runtime_redrive(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                runtime_state_path=runtime_path,
                quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
                publication_eval_payload=publication_eval_payload,
                base=base,
                repair_kind=abnormal_repair_kind,
            )
    gate_status = _publication_gate_ready_for_specificity_redrive(quest_root)
    supersession = _controller_decision_supersedes_specificity(
        study_root=study_root,
        runtime_state=runtime_state,
        publication_eval_payload=publication_eval_payload,
    )
    superseded_by_targets = (
        supersession.get("supersedes") is True
        and _text(supersession.get("reason")) == "publication_eval_specificity_targets_complete"
    )
    if gate_status.get("ready") is not True and not superseded_by_targets:
        return {**base, "dispatch_status": "blocked", "reason": _text(gate_status.get("reason")), "gate_status": gate_status}
    if supersession.get("supersedes") is not True:
        return {
            **base,
            "dispatch_status": "blocked",
            "reason": _text(supersession.get("reason")),
            "controller_supersession": supersession,
            "gate_status": gate_status,
        }
    clear_result = _clear_stale_specificity_runtime_state(
        runtime_state_path=runtime_path,
        study_id=study_id,
        quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
        allow_pending_user_messages=superseded_by_targets,
    )
    if clear_result.get("cleared") is not True:
        return {
            **base,
            "dispatch_status": "blocked",
            "reason": _text(clear_result.get("reason")),
            "controller_supersession": supersession,
            "gate_status": gate_status,
            "stale_specificity_clear": clear_result,
        }
    pending_resume: dict[str, Any] | None = None
    blocked_turn_closeout_clear = platform_repair_pending_redrive.blocked_turn_closeout_clear_result(clear_result)
    if superseded_by_targets and int(runtime_state.get("pending_user_message_count") or 0) > 0:
        pending_resume = platform_repair_pending_redrive.mark_existing_pending_user_message_redrive(
            runtime_state_path=runtime_path,
            study_id=study_id,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        )
        blocked_turn_closeout_clear = (
            platform_repair_pending_redrive.blocked_turn_closeout_clear_result(pending_resume)
            or blocked_turn_closeout_clear
        )
        if pending_resume.get("marked") is not True:
            return {
                **base,
                "dispatch_status": "blocked",
                "reason": _text(pending_resume.get("reason")) or "existing_pending_user_message_redrive_not_marked",
                "controller_supersession": supersession,
                "gate_status": gate_status,
                "stale_specificity_clear": clear_result,
                "stale_specificity_cleared": True,
                "existing_pending_user_message_resume": pending_resume,
                "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            }
    try:
        resume_result = study_runtime_router.ensure_study_runtime(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        )
    except Exception as exc:
        return {
            **base,
            "dispatch_status": "blocked",
            "reason": "resume_after_platform_repair_failed",
            "error": str(exc),
            "controller_supersession": supersession,
            "gate_status": gate_status,
            "stale_specificity_clear": clear_result,
            "stale_specificity_cleared": True,
            "existing_pending_user_message_resume": pending_resume,
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
        }
    return {
        **base,
        "dispatch_status": "applied",
        "reason": (
            "stale_specificity_terminal_targets_resolved"
            if _text(supersession.get("reason")) == "publication_eval_specificity_targets_complete"
            else "stale_specificity_terminal_gate_cleared"
        ),
        "controller_supersession": supersession,
        "gate_status": gate_status,
        "stale_specificity_clear": clear_result,
        "stale_specificity_cleared": True,
        "existing_pending_user_message_resume": pending_resume,
        "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
        "resume_result": dict(resume_result) if isinstance(resume_result, Mapping) else resume_result,
    }


__all__ = [
    "SPECIFICITY_WORK_UNIT_IDS",
    "apply_runtime_platform_repair",
    "write_runtime_platform_repair_lifecycle",
]
