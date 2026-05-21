from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner
from med_autoscience.controllers.domain_route_scan_parts import abnormal_stopped_runtime
from med_autoscience.controllers.domain_route_scan_parts import pending_user_messages
from med_autoscience.controllers.domain_route_scan_parts import platform_current_controller
from med_autoscience.controllers import study_domain_transition_guard as domain_transition_guard
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_closeout_redrive
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_domain_transition
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_owner_handoff_redrive
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_owner_route
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_pending_redrive
from med_autoscience.controllers.domain_route_scan_parts import runtime_facts
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
]
SUPERVISION_FORBIDDEN_ACTIONS = [
    "paper_package_mutation",
    "manual_study_patch",
    "quality_gate_relaxation",
    "medical_claim_authoring",
]
RUNTIME_PLATFORM_REPAIR_SOURCE = "domain_route_scan_platform_repair"
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





def _runtime_state_path(quest_root: str | None) -> Path | None:
    if quest_root is None:
        return None
    return Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"


def _opl_runtime_owner_route_apply_result(
    *,
    base: Mapping[str, Any],
    study_id: str,
    quest_id: str | None,
    runtime_state_path: Path,
    reason: str,
    repair_kind: str,
    authorization: Mapping[str, Any] | None = None,
    authorization_written: bool | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    owner_route_base = {
        **dict(base),
        "allowed_write_surfaces": list(SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
    }
    return platform_repair_owner_route.apply_result(
        base=owner_route_base,
        study_id=study_id,
        quest_id=quest_id,
        runtime_state_path=runtime_state_path,
        reason=reason,
        repair_kind=repair_kind,
        authorization=authorization,
        authorization_written=authorization_written,
        extra=extra,
    )


def _owner_route_reason_for_repair(repair_kind: str) -> str:
    return platform_repair_owner_route.owner_route_reason_for_repair(repair_kind)





def _apply_abnormal_stopped_runtime_repair(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    base: Mapping[str, Any],
    repair_kind: str,
    controller_authorization: Mapping[str, Any] | None = None,
    force_fresh_turn: bool = False,
) -> dict[str, Any]:
    _ = (profile, study_root, force_fresh_turn)
    return _opl_runtime_owner_route_apply_result(
        base=base,
        study_id=study_id,
        quest_id=quest_id,
        runtime_state_path=runtime_state_path,
        reason=_owner_route_reason_for_repair(repair_kind),
        repair_kind=repair_kind,
        authorization=controller_authorization,
        authorization_written=controller_authorization is not None,
    )


def _force_fresh_runtime_turn(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    repair_kind: str,
) -> dict[str, Any]:
    _ = (profile, study_id, study_root)
    return {
        "forced": False,
        "reason": "opl_runtime_owner_route_required",
        "repair_kind": repair_kind,
        "queue_owner": "one-person-lab",
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
    force_fresh_turn: bool = False,
) -> dict[str, Any]:
    authorization = _write_current_controller_authorization(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
    )
    if (
        authorization is not None
        and authorization.get("written") is not True
        and authorization.get("handoff_ready") is not True
    ):
        if _text(authorization.get("reason")) == "pending_user_messages_present":
            pending_resume = platform_repair_pending_redrive.mark_existing_pending_user_message_redrive(
                runtime_state_path=runtime_state_path,
                study_id=study_id,
                quest_id=quest_id,
                source=RUNTIME_PLATFORM_REPAIR_SOURCE,
                runtime_state=_read_json_object(runtime_state_path),
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
            apply_result = _opl_runtime_owner_route_apply_result(
                base=base,
                study_id=study_id,
                quest_id=quest_id,
                runtime_state_path=runtime_state_path,
                reason=_owner_route_reason_for_repair(repair_kind),
                repair_kind=repair_kind,
                authorization=None,
                authorization_written=False,
                extra={
                    "existing_pending_user_message_resume": pending_resume,
                    "force_fresh_turn": _force_fresh_runtime_turn(
                        profile=profile,
                        study_id=study_id,
                        study_root=study_root,
                        repair_kind=repair_kind,
                    )
                    if force_fresh_turn
                    else None,
                },
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
    apply_result = _opl_runtime_owner_route_apply_result(
        base=base,
        study_id=study_id,
        quest_id=quest_id,
        runtime_state_path=runtime_state_path,
        reason=_owner_route_reason_for_repair(repair_kind),
        repair_kind=repair_kind,
        authorization=authorization,
        authorization_written=authorization is not None and authorization.get("written") is True,
        extra={
            "force_fresh_turn": _force_fresh_runtime_turn(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                repair_kind=repair_kind,
            )
            if force_fresh_turn
            else None,
        },
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
            force_fresh_turn=True,
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
    if int(runtime_state.get("pending_user_message_count") or 0) > 0:
        return False
    return bool(
        _text(runtime_state.get("continuation_policy")) == "auto"
        and _text(runtime_state.get("continuation_anchor")) == "decision"
        and _text(runtime_state.get("continuation_reason")) == "controller_work_unit_pending"
        and bool(_mapping(runtime_state.get("last_controller_decision_authorization")))
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
    runtime_state = _read_json_object(runtime_state_path) or {}
    if (
        _text(runtime_state.get("continuation_reason")) == "controller_work_unit_pending"
        and _mapping(runtime_state.get("last_controller_decision_authorization"))
    ):
        authorization: dict[str, Any] | None = {
            "written": False,
            "handoff_ready": True,
            "existing_runtime_authorization": True,
            "runtime_state_mutated": False,
            "delegated_runtime_owner": "one-person-lab",
            "path": str(runtime_state_path),
            **_mapping(runtime_state.get("last_controller_decision_authorization")),
        }
    else:
        authorization = _write_current_controller_authorization(
            runtime_state_path=runtime_state_path,
            study_root=study_root,
            study_id=study_id,
            quest_id=quest_id,
            publication_eval_payload=publication_eval_payload,
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
    if authorization.get("written") is not True and authorization.get("handoff_ready") is not True:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": _text(authorization.get("reason")) or "current_controller_authorization_not_written",
            "repair_kind": "pending_runtime_platform_repair_redrive",
            "current_controller_authorization": authorization,
            "current_controller_authorization_written": False,
        }
    return _opl_runtime_owner_route_apply_result(
        base=base,
        study_id=study_id,
        quest_id=quest_id,
        runtime_state_path=runtime_state_path,
        reason=current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON,
        repair_kind="pending_runtime_platform_repair_redrive",
        authorization=authorization,
        authorization_written=authorization.get("written") is True,
    )


def _apply_controller_work_unit_pending_redrive(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    runtime_state_path: Path,
    quest_id: str | None,
    base: Mapping[str, Any],
) -> dict[str, Any]:
    _ = (profile, study_root)
    return _opl_runtime_owner_route_apply_result(
        base=base,
        study_id=study_id,
        quest_id=quest_id,
        runtime_state_path=runtime_state_path,
        reason=current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON,
        repair_kind="controller_work_unit_pending_redrive",
    )


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


def _write_current_controller_authorization(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    return _current_controller_authorization_handoff(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        publication_eval_payload=publication_eval_payload,
        allow_specificity_work_unit=False,
    )


def _current_controller_authorization_handoff(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    allow_specificity_work_unit: bool,
) -> dict[str, Any] | None:
    authorization = platform_current_controller.current_controller_authorization_payload(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        read_json_object=_read_json_object,
        allow_specificity_work_unit=allow_specificity_work_unit,
    )
    if authorization is None:
        authorization = platform_current_controller.story_surface_delta_authorization_payload(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
            read_json_object=_read_json_object,
        )
    if authorization is None:
        return None
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None:
        return {
            "written": False,
            "handoff_ready": False,
            "reason": "runtime_state_missing_or_invalid",
            "path": str(runtime_state_path),
        }
    if pending_user_messages.pending_count(runtime_state) > 0:
        return {
            "written": False,
            "handoff_ready": False,
            "reason": "pending_user_messages_present",
            "path": str(runtime_state_path),
            **authorization,
        }
    clearable_keys: list[str] = []
    for key in (
        "retry_state",
        "last_stage_fingerprint",
        "last_stage_fingerprint_at",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ):
        if key in runtime_state:
            clearable_keys.append(key)
    return {
        "written": False,
        "handoff_ready": True,
        "runtime_state_mutated": False,
        "events_jsonl_mutated": False,
        "delegated_runtime_owner": "one-person-lab",
        "path": str(runtime_state_path),
        "study_id": study_id,
        "quest_id": _text(runtime_state.get("quest_id")) or quest_id,
        "cleared_keys": clearable_keys,
        "proposed_runtime_state": {
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "active_run_id": None,
            "worker_running": False,
            "same_fingerprint_auto_turn_count": 0,
            "last_controller_decision_authorization": authorization,
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        **authorization,
    }


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
    allow_pending_control_messages: bool = False,
) -> dict[str, Any]:
    return platform_repair_closeout_redrive.clear_stale_controller_runtime_state(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        clear_reason=clear_reason,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        allow_pending_user_messages=allow_pending_user_messages,
        allow_pending_control_messages=allow_pending_control_messages,
    )


def _clear_stale_specificity_runtime_state(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    allow_pending_user_messages: bool = False,
    allow_pending_control_messages: bool = False,
) -> dict[str, Any]:
    return platform_repair_closeout_redrive.clear_stale_specificity_runtime_state(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=RUNTIME_PLATFORM_REPAIR_SOURCE,
        allow_pending_user_messages=allow_pending_user_messages,
        allow_pending_control_messages=allow_pending_control_messages,
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
    transition_block = domain_transition_guard.redrive_block_payload(status)
    if transition_block is not None:
        return {**base, **transition_block}
    domain_transition_redrive = platform_repair_domain_transition.apply_domain_transition_runtime_redrive(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        runtime_state_path=runtime_path,
        quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
        status=status,
        publication_eval_payload=publication_eval_payload,
        base=base,
        apply_current_controller_runtime_redrive=_apply_current_controller_runtime_redrive,
    )
    if domain_transition_redrive is not None:
        return domain_transition_redrive
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
    interaction_arbitration = _mapping(status.get("interaction_arbitration"))
    if _text(interaction_arbitration.get("classification")) == "controller_work_unit_pending_redrive":
        return _apply_controller_work_unit_pending_redrive(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            runtime_state_path=runtime_path,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            base=base,
        )
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
            runtime_state=runtime_state,
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
        return _opl_runtime_owner_route_apply_result(
            base=base,
            study_id=study_id,
            quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
            runtime_state_path=runtime_path,
            reason="stale_blocked_turn_closeout_pending_queue_redrive",
            repair_kind="pending_user_message_redrive",
            extra={
                "existing_pending_user_message_resume": pending_resume,
                "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            },
        )
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
    current_controller_route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if current_controller_route is not None:
        return _controller_redrive_result(
            _apply_current_controller_runtime_redrive(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                runtime_state_path=runtime_path,
                quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
                publication_eval_payload=publication_eval_payload,
                base={**base, "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON},
                repair_kind="current_controller_runtime_route_redrive",
            )
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
            runtime_state=runtime_state,
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
    apply_reason = (
            "stale_specificity_terminal_targets_resolved"
            if _text(supersession.get("reason")) == "publication_eval_specificity_targets_complete"
            else "stale_specificity_terminal_gate_cleared"
    )
    return _opl_runtime_owner_route_apply_result(
        base=base,
        study_id=study_id,
        quest_id=_text(status.get("quest_id")) or _text(progress.get("quest_id")),
        runtime_state_path=runtime_path,
        reason=apply_reason,
        repair_kind="stale_specificity_terminal_gate_redrive",
        extra={
            "controller_supersession": supersession,
            "gate_status": gate_status,
            "stale_specificity_clear": clear_result,
            "stale_specificity_cleared": True,
            "existing_pending_user_message_resume": pending_resume,
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
        },
    )


__all__ = [
    "SPECIFICITY_WORK_UNIT_IDS",
    "apply_runtime_platform_repair",
    "write_runtime_platform_repair_lifecycle",
]
