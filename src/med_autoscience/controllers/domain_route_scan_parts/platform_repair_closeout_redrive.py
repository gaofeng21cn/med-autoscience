from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_route_scan_parts import current_truth_owner
from med_autoscience.controllers.domain_route_scan_parts.owner_tokens import owner_token
from med_autoscience.controllers.domain_route_scan_parts import pending_user_messages
from med_autoscience.controllers.domain_route_scan_parts import platform_current_controller
from med_autoscience.controllers.domain_route_scan_parts import platform_repair_owner_route
from med_autoscience.publication_eval_specificity_targets import specificity_target_status


SPECIFICITY_WORK_UNIT_IDS = {"gate_needs_specificity", "needs_specificity"}
RUNTIME_PLATFORM_REPAIR_RUNTIME_ACTIONS = {
    "ensure_study_runtime",
    "ensure_study_runtime_relaunch_stopped",
    "run_gate_clearing_batch",
    "run_quality_repair_batch",
}
REDRIVE_CONTROLLER_WORK_UNIT_IDS = {"publication_gate_replay"}
PACKAGE_FRESHNESS_TERMINAL_REASONS = {
    "current_package_freshness_required",
    "stale_submission_minimal_authority",
    "submission_minimal_refresh",
    "publication_gate_replay",
}


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _append_json_line(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(dict(payload), ensure_ascii=False, sort_keys=True) + "\n")


def stale_publication_gate_closeout_targets_resolved(
    *,
    status: Mapping[str, Any],
    runtime_state: Mapping[str, Any],
    runtime_state_path: Path | None = None,
    gate_specificity: Mapping[str, Any] | None,
) -> bool:
    if _text(status.get("quest_status")) != "waiting_for_user":
        return False
    continuation_state = _mapping(status.get("continuation_state"))
    blocked_closeout = _mapping(status.get("blocked_turn_closeout"))
    runtime_blocked_closeout = _mapping(runtime_state.get("blocked_turn_closeout"))
    next_owner = owner_token(blocked_closeout.get("next_owner") or runtime_blocked_closeout.get("next_owner"))
    return bool(
        _text(continuation_state.get("continuation_policy")) == "wait_for_user_or_resume"
        and _text(continuation_state.get("continuation_anchor")) == "turn_closeout"
        and _text(continuation_state.get("continuation_reason")) == "blocked_turn_closeout_waiting_for_owner"
        and (
            int(continuation_state.get("pending_user_message_count") or 0) == 0
            or _pending_queue_is_control_plane_only(
                runtime_state=runtime_state,
                runtime_state_path=runtime_state_path,
            )
        )
        and next_owner in {"publication_gate", "mas_controller"}
        and (
            next_owner == "publication_gate"
            or _runtime_authorization_stale_specificity(runtime_state)
            or _runtime_authorization_target_ready_specificity(runtime_state)
            or not _mapping(runtime_state.get("last_controller_decision_authorization"))
        )
        and _mapping(gate_specificity).get("specific_targets_present") is True
    )


def clear_stale_publication_gate_closeout(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    source: str,
    allow_pending_control_messages: bool = False,
) -> dict[str, Any]:
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"cleared": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    if int(runtime_state.get("pending_user_message_count") or 0) > 0 and not (
        allow_pending_control_messages
        and _pending_queue_is_control_plane_only(runtime_state=runtime_state, runtime_state_path=runtime_state_path)
    ):
        return {"cleared": False, "reason": "pending_user_messages_present", "path": str(runtime_state_path)}
    blocked_closeout = _mapping(runtime_state.get("blocked_turn_closeout"))
    if _text(runtime_state.get("continuation_reason")) != "blocked_turn_closeout_waiting_for_owner":
        return {"cleared": False, "reason": "blocked_turn_closeout_wait_not_found", "path": str(runtime_state_path)}
    next_owner = owner_token(blocked_closeout.get("next_owner"))
    if next_owner == "publication_gate":
        pass
    elif next_owner == "mas_controller" and (
        _runtime_authorization_stale_specificity(runtime_state)
        or _runtime_authorization_target_ready_specificity(runtime_state)
        or not _mapping(runtime_state.get("last_controller_decision_authorization"))
    ):
        pass
    else:
        return {"cleared": False, "reason": "specificity_closeout_not_found", "path": str(runtime_state_path)}

    clearable_keys: list[str] = []
    for key in (
        "last_controller_decision_authorization",
        "control_intent_lifecycle",
        "last_live_controller_reroute_restart",
        "retry_state",
        "last_stage_fingerprint",
        "last_stage_fingerprint_at",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ):
        if key in runtime_state:
            clearable_keys.append(key)
    return _runtime_state_clear_handoff(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=source,
        clear_reason="stale_publication_gate_closeout_targets_resolved",
        clearable_keys=clearable_keys,
    )


def _runtime_authorization_stale_specificity(runtime_state: Mapping[str, Any]) -> bool:
    authorization = _mapping(runtime_state.get("last_controller_decision_authorization"))
    next_work_unit = _mapping(authorization.get("next_work_unit"))
    lifecycle = _mapping(authorization.get("controller_work_unit_lifecycle"))
    return bool(
        (
            _text(authorization.get("work_unit_id")) == "gate_needs_specificity"
            or _text(next_work_unit.get("unit_id")) == "gate_needs_specificity"
        )
        and _text(authorization.get("non_executable_reason")) == "gate_needs_specificity_without_targets"
        and authorization.get("controller_work_unit_executable") is False
        and _text(lifecycle.get("block_reason")) == "needs_specificity"
    )


def _runtime_authorization_target_ready_specificity(runtime_state: Mapping[str, Any]) -> bool:
    authorization = _mapping(runtime_state.get("last_controller_decision_authorization"))
    next_work_unit = _mapping(authorization.get("next_work_unit"))
    return bool(
        (
            _text(authorization.get("work_unit_id")) in SPECIFICITY_WORK_UNIT_IDS
            or _text(next_work_unit.get("unit_id")) in SPECIFICITY_WORK_UNIT_IDS
        )
        and specificity_target_status(authorization.get("specificity_targets")).get("complete") is True
        and _text(authorization.get("non_executable_reason")) != "gate_needs_specificity_without_targets"
        and _text(next_work_unit.get("non_executable_reason")) != "gate_needs_specificity_without_targets"
        and authorization.get("controller_work_unit_executable") is not False
        and next_work_unit.get("controller_work_unit_executable") is not False
    )


def _next_work_unit_needs_specificity(value: object) -> bool:
    next_work_unit = _mapping(value)
    return _text(next_work_unit.get("unit_id")) in SPECIFICITY_WORK_UNIT_IDS


def _recommended_actions_need_specificity(value: object) -> bool:
    if not isinstance(value, list):
        return False
    for action in value:
        if not isinstance(action, Mapping):
            continue
        if _next_work_unit_needs_specificity(action.get("next_work_unit")):
            return True
        blocking_units = action.get("blocking_work_units")
        if isinstance(blocking_units, list) and any(_next_work_unit_needs_specificity(item) for item in blocking_units):
            return True
    return False


def publication_eval_specificity_targets_complete(publication_eval_payload: Mapping[str, Any]) -> bool:
    actions = publication_eval_payload.get("recommended_actions")
    if not isinstance(actions, list):
        return False
    for action in actions:
        if not isinstance(action, Mapping) or "specificity_targets" not in action:
            continue
        if specificity_target_status(action.get("specificity_targets")).get("complete") is True:
            return True
    return False


def runtime_state_has_stale_specificity_terminal(runtime_state: Mapping[str, Any]) -> bool:
    authorization = _mapping(runtime_state.get("last_controller_decision_authorization"))
    lifecycle = _mapping(authorization.get("controller_work_unit_lifecycle"))
    next_work_unit = _mapping(authorization.get("next_work_unit"))
    markers = {
        _text(runtime_state.get("continuation_reason")),
        _text(authorization.get("work_unit_id")),
        _text(next_work_unit.get("unit_id")),
        _text(lifecycle.get("lifecycle_state")),
        _text(lifecycle.get("latest_event_type")),
        _text(lifecycle.get("block_reason")),
    }
    return any(marker in SPECIFICITY_WORK_UNIT_IDS for marker in markers)


def runtime_state_has_controller_terminal(runtime_state: Mapping[str, Any]) -> bool:
    authorization = _mapping(runtime_state.get("last_controller_decision_authorization"))
    lifecycle = _mapping(authorization.get("controller_work_unit_lifecycle"))
    retry_state = _mapping(runtime_state.get("retry_state"))
    markers = {
        _text(runtime_state.get("continuation_reason")),
        _text(authorization.get("work_unit_id")),
        _text(lifecycle.get("lifecycle_state")),
        _text(lifecycle.get("latest_event_type")),
        _text(lifecycle.get("block_reason")),
    }
    terminal_markers = set(SPECIFICITY_WORK_UNIT_IDS) | set(PACKAGE_FRESHNESS_TERMINAL_REASONS)
    return (
        any(marker in terminal_markers for marker in markers)
        or retry_state.get("terminal") is True
        or lifecycle.get("terminal_consumed") is True
        or lifecycle.get("delivery_blocked") is True
    )


def controller_decision_supersedes_specificity(
    *,
    study_root: Path,
    runtime_state: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> dict[str, Any]:
    decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    payload = _read_json_object(decision_path)
    if payload is None:
        return {"supersedes": False, "reason": "controller_decision_missing", "path": str(decision_path)}
    if payload.get("requires_human_confirmation") is True:
        return {"supersedes": False, "reason": "controller_decision_requires_human_confirmation", "path": str(decision_path)}
    current_decision_id = _text(payload.get("decision_id"))
    old_decision_id = _text(_mapping(runtime_state.get("last_controller_decision_authorization")).get("decision_id"))
    if current_decision_id is not None and old_decision_id is not None and current_decision_id == old_decision_id:
        if not (
            runtime_state_has_stale_specificity_terminal(runtime_state)
            and publication_eval_specificity_targets_complete(publication_eval_payload)
        ):
            return {"supersedes": False, "reason": "controller_decision_not_superseded", "path": str(decision_path)}
    current_work_unit_id = _text(_mapping(payload.get("next_work_unit")).get("unit_id"))
    action_types = platform_current_controller.controller_action_types(payload)
    if current_work_unit_id in SPECIFICITY_WORK_UNIT_IDS:
        if (
            runtime_state_has_stale_specificity_terminal(runtime_state)
            and publication_eval_specificity_targets_complete(publication_eval_payload)
        ):
            return {
                "supersedes": True,
                "reason": "publication_eval_specificity_targets_complete",
                "decision_id": current_decision_id,
                "work_unit_id": current_work_unit_id,
                "route_target": _text(payload.get("route_target")),
                "controller_actions": sorted(action_types),
                "path": str(decision_path),
            }
        return {"supersedes": False, "reason": "controller_decision_still_needs_specificity", "path": str(decision_path)}
    if (
        _recommended_actions_need_specificity(publication_eval_payload.get("recommended_actions"))
        and not publication_eval_specificity_targets_complete(publication_eval_payload)
    ):
        return {"supersedes": False, "reason": "publication_eval_still_needs_specificity", "path": str(decision_path)}
    if not (action_types & RUNTIME_PLATFORM_REPAIR_RUNTIME_ACTIONS):
        return {"supersedes": False, "reason": "controller_decision_runtime_action_missing", "path": str(decision_path)}
    route_target = _text(payload.get("route_target"))
    if route_target in {"controller", "decision"} and current_work_unit_id not in REDRIVE_CONTROLLER_WORK_UNIT_IDS:
        return {"supersedes": False, "reason": "controller_decision_still_terminal_controller_route", "path": str(decision_path)}
    return {
        "supersedes": True,
        "decision_id": current_decision_id,
        "work_unit_id": current_work_unit_id,
        "route_target": route_target,
        "controller_actions": sorted(action_types),
        "path": str(decision_path),
    }


def clear_stale_controller_runtime_state(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    clear_reason: str,
    source: str,
    allow_pending_user_messages: bool = False,
    allow_pending_control_messages: bool = False,
) -> dict[str, Any]:
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"cleared": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    if int(runtime_state.get("pending_user_message_count") or 0) > 0 and not (
        allow_pending_user_messages
        or (
            allow_pending_control_messages
            and _pending_queue_is_control_plane_only(runtime_state=runtime_state, runtime_state_path=runtime_state_path)
        )
    ):
        return {"cleared": False, "reason": "pending_user_messages_present", "path": str(runtime_state_path)}
    if not runtime_state_has_controller_terminal(runtime_state):
        return {"cleared": False, "reason": "stale_controller_terminal_not_found", "path": str(runtime_state_path)}
    clearable_keys: list[str] = []
    for key in (
        "last_controller_decision_authorization",
        "control_intent_lifecycle",
        "last_live_controller_reroute_restart",
        "retry_state",
        "last_stage_fingerprint",
        "last_stage_fingerprint_at",
        "blocked_turn_closeout",
        "last_liveness_reconcile_reason",
    ):
        if key in runtime_state:
            clearable_keys.append(key)
    return _runtime_state_clear_handoff(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=source,
        clear_reason=clear_reason,
        clearable_keys=clearable_keys,
    )


def clear_stale_specificity_runtime_state(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    source: str,
    allow_pending_user_messages: bool = False,
    allow_pending_control_messages: bool = False,
) -> dict[str, Any]:
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None:
        return {"cleared": False, "reason": "runtime_state_missing_or_invalid", "path": str(runtime_state_path)}
    if not runtime_state_has_stale_specificity_terminal(runtime_state):
        return {"cleared": False, "reason": "stale_specificity_terminal_gate_not_found", "path": str(runtime_state_path)}
    return clear_stale_controller_runtime_state(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        clear_reason="stale_specificity_terminal",
        source=source,
        allow_pending_user_messages=allow_pending_user_messages,
        allow_pending_control_messages=allow_pending_control_messages,
    )


def clear_stale_controller_terminal_for_current_route(
    *,
    runtime_state_path: Path,
    study_root: Path,
    study_id: str,
    quest_id: str | None,
    publication_eval_payload: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    runtime_state = _read_json_object(runtime_state_path)
    if runtime_state is None or not runtime_state_has_controller_terminal(runtime_state):
        return None
    route = current_truth_owner.current_controller_runtime_route(
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )
    if route is None:
        return None
    authorization = _mapping(runtime_state.get("last_controller_decision_authorization"))
    if (
        _text(authorization.get("decision_id")) == _text(route.get("decision_id"))
        and _text(authorization.get("work_unit_id")) == _text(route.get("work_unit_id"))
    ):
        return None
    clear_result = clear_stale_controller_runtime_state(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        clear_reason="current_controller_runtime_route",
        source=source,
    )
    return {
        "cleared": clear_result.get("cleared") is True,
        "reason": _text(clear_result.get("reason")),
        "clear_result": clear_result,
        "controller_route": route,
    }


def apply_if_targets_resolved(
    *,
    profile: Any,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    runtime_state_path: Path,
    status: Mapping[str, Any],
    runtime_state: Mapping[str, Any],
    gate_specificity: Mapping[str, Any] | None,
    gate_status: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    base: Mapping[str, Any],
    source: str,
) -> dict[str, Any] | None:
    if not stale_publication_gate_closeout_targets_resolved(
        status=status,
        runtime_state=runtime_state,
        runtime_state_path=runtime_state_path,
        gate_specificity=gate_specificity,
    ):
        return None
    allow_pending_control_messages = _pending_queue_is_control_plane_only(
        runtime_state=runtime_state,
        runtime_state_path=runtime_state_path,
    )
    clear_result = clear_stale_publication_gate_closeout(
        runtime_state_path=runtime_state_path,
        study_id=study_id,
        quest_id=quest_id,
        source=source,
        allow_pending_control_messages=allow_pending_control_messages,
    )
    blocked_turn_closeout_clear = blocked_turn_closeout_clear_result(clear_result)
    if clear_result.get("cleared") is not True:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": _text(clear_result.get("reason")),
            "stale_specificity_clear": clear_result,
            "gate_status": gate_status,
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
        }
    authorization = _controller_authorization_handoff(
        runtime_state_path=runtime_state_path,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
        allow_specificity_work_unit=True,
    )
    if authorization is None:
        return {
            **dict(base),
            "dispatch_status": "blocked",
            "reason": "current_controller_authorization_missing",
            "stale_specificity_clear": clear_result,
            "stale_specificity_cleared": True,
            "gate_status": gate_status,
            "existing_pending_user_message_resume": None,
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
            "current_controller_authorization": None,
            "current_controller_authorization_written": False,
        }
    _ = (profile, study_root, source)
    return platform_repair_owner_route.apply_result(
        base=base,
        study_root=study_root,
        study_id=study_id,
        quest_id=quest_id,
        runtime_state_path=runtime_state_path,
        reason="stale_publication_gate_closeout_targets_resolved",
        repair_kind="stale_publication_gate_closeout_targets_resolved",
        authorization=authorization,
        authorization_written=False,
        extra={
            "stale_specificity_clear": clear_result,
            "stale_specificity_cleared": True,
            "gate_status": gate_status,
            "existing_pending_user_message_resume": None,
            "blocked_turn_closeout_clear": blocked_turn_closeout_clear,
        },
    )


def blocked_turn_closeout_clear_result(clear_result: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if not isinstance(clear_result, Mapping):
        return None
    cleared_keys = _string_items(clear_result.get("cleared_keys"))
    if not any(key in {"blocked_turn_closeout", "last_liveness_reconcile_reason"} for key in cleared_keys):
        return None
    return {
        "cleared": True,
        "cleared_keys": [key for key in cleared_keys if key in {"blocked_turn_closeout", "last_liveness_reconcile_reason"}],
        "path": _text(clear_result.get("path")),
        "runtime_state_mutated": clear_result.get("runtime_state_mutated") is True,
        "delegated_runtime_owner": _text(clear_result.get("delegated_runtime_owner")),
    }


def _runtime_state_clear_handoff(
    *,
    runtime_state_path: Path,
    study_id: str,
    quest_id: str | None,
    source: str,
    clear_reason: str,
    clearable_keys: list[str],
) -> dict[str, Any]:
    return {
        "cleared": True,
        "cleared_keys": clearable_keys,
        "path": str(runtime_state_path),
        "runtime_state_mutated": False,
        "events_jsonl_mutated": False,
        "delegated_runtime_owner": "one-person-lab",
        "source": source,
        "study_id": study_id,
        "quest_id": quest_id,
        "clear_reason": clear_reason,
        "proposed_runtime_state": {
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "runtime_platform_repair_redrive",
            "active_run_id": None,
            "worker_running": False,
            "same_fingerprint_auto_turn_count": 0,
        },
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
    }


def _controller_authorization_handoff(
    *,
    runtime_state_path: Path,
    study_root: Path,
    publication_eval_payload: Mapping[str, Any],
    allow_specificity_work_unit: bool = False,
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
    return {
        "written": False,
        "handoff_ready": True,
        "runtime_state_mutated": False,
        "events_jsonl_mutated": False,
        "delegated_runtime_owner": "one-person-lab",
        "path": str(runtime_state_path),
        "proposed_runtime_state": {
            "continuation_policy": "auto",
            "continuation_anchor": "decision",
            "continuation_reason": "controller_work_unit_pending",
            "active_run_id": None,
            "worker_running": False,
            "same_fingerprint_auto_turn_count": 0,
            "last_controller_decision_authorization": authorization,
        },
        **authorization,
    }


def _pending_queue_is_control_plane_only(
    *,
    runtime_state: Mapping[str, Any],
    runtime_state_path: Path | None,
) -> bool:
    count = pending_user_messages.pending_count(runtime_state)
    return bool(
        count > 0
        and runtime_state_path is not None
        and pending_user_messages.only_control_plane_messages(
            runtime_state_path=runtime_state_path,
            expected_count=count,
        )
    )


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))
