from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent

from ..study_runtime_status import StudyRuntimeDecision, StudyRuntimeStatus
from .controller_authorization_context import (
    _WORK_UNIT_TARGET_CONTEXT_KEYS,
    _controller_decision_authorization_identity,
)
from .control_intent_lifecycle import lifecycle_for_authorization


_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY = "last_controller_decision_authorization"
_CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS = {
    "run_gate_clearing_batch",
}
_CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS = {
    "ensure_study_runtime_relaunch_stopped",
}
_QUALITY_REPAIR_DOWNSTREAM_WORK_UNIT_IDS = {
    "publication_gate_replay",
    "submission_authority_sync_closure",
    "submission_delivery_sync_closure",
    "submission_minimal_refresh",
}
_CONTROL_INTENT_LIFECYCLE_STATE_KEY = "control_intent_lifecycle"
_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY = "last_live_controller_reroute_restart"
_CLOSED_PUBLICATION_WORK_UNIT_LIFECYCLE_STATUSES = frozenset({"done"})


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _active_run_id_from_status_or_state(*, status: StudyRuntimeStatus, runtime_state: dict[str, Any]) -> str | None:
    active_run_id = str(runtime_state.get("active_run_id") or "").strip()
    if active_run_id:
        return active_run_id
    payload = status.extras.get("runtime_liveness_audit")
    if isinstance(payload, dict):
        active_run_id = str(payload.get("active_run_id") or "").strip()
        if active_run_id:
            return active_run_id
        runtime_audit = payload.get("runtime_audit")
        if isinstance(runtime_audit, dict):
            active_run_id = str(runtime_audit.get("active_run_id") or "").strip()
            if active_run_id:
                return active_run_id
    return None


def _controller_decision_authorization_already_relayed(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
) -> bool:
    marker = runtime_state.get(_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if not isinstance(marker, dict):
        return False
    current_active_run_id = _text(active_run_id)
    marker_active_run_id = _text(marker.get("active_run_id"))
    if current_active_run_id is not None and marker_active_run_id != current_active_run_id:
        return False
    if not _controller_target_context_matches(marker=marker, authorization_context=authorization_context):
        return False
    intent_match = _controller_intent_key_match(marker=marker, authorization_context=authorization_context)
    if intent_match is not None:
        return intent_match
    return _controller_route_marker_match(marker=marker, authorization_context=authorization_context)


def _controller_target_context_matches(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return all(
        key not in authorization_context or marker.get(key) == authorization_context.get(key)
        for key in _WORK_UNIT_TARGET_CONTEXT_KEYS
    )


def _controller_authorization_marker_lacks_target_context(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    marker = runtime_state.get(_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if not isinstance(marker, dict):
        return False
    return any(
        key in authorization_context and marker.get(key) != authorization_context.get(key)
        for key in _WORK_UNIT_TARGET_CONTEXT_KEYS
    )


def _controller_intent_key_match(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool | None:
    expected_intent_key = str(authorization_context.get("control_intent_key") or "").strip()
    marker_intent_key = str(marker.get("control_intent_key") or "").strip()
    if not expected_intent_key or not marker_intent_key:
        return None
    return marker_intent_key == expected_intent_key


def _controller_route_marker_match(
    *,
    marker: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    return (
        str(marker.get("decision_id") or "").strip() == str(authorization_context.get("decision_id") or "").strip()
        and str(marker.get("route_target") or "").strip() == str(authorization_context.get("route_target") or "").strip()
        and str(marker.get("route_key_question") or "").strip()
        == str(authorization_context.get("route_key_question") or "").strip()
    )


def _controller_decision_authorization_lifecycle(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
    active_run_id: str | None = None,
) -> dict[str, Any]:
    return lifecycle_for_authorization(
        study_root=study_root,
        identity=_controller_decision_authorization_identity(authorization_context),
        authorization_context=authorization_context,
        active_run_id=active_run_id,
    )


def _closed_publication_work_unit_lifecycle(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    lifecycle_path = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "publication_work_unit_lifecycle"
        / "latest.json"
    )
    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if _text(payload.get("status")) not in _CLOSED_PUBLICATION_WORK_UNIT_LIFECYCLE_STATUSES:
        return None
    source_eval_id = _text(payload.get("source_eval_id"))
    authorization_eval_id = _text(authorization_context.get("publication_eval_id"))
    if source_eval_id is None or authorization_eval_id is None or source_eval_id != authorization_eval_id:
        return None
    lifecycle_work_unit = payload.get("work_unit")
    if not isinstance(lifecycle_work_unit, dict):
        return None
    work_unit_id = _text(authorization_context.get("work_unit_id"))
    if work_unit_id is None or _text(lifecycle_work_unit.get("unit_id")) != work_unit_id:
        return None
    return {
        "reason": "publication_work_unit_lifecycle_done",
        "status": _text(payload.get("status")),
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "lifecycle_path": str(lifecycle_path),
        "gate_replay_status": payload.get("gate_replay_status"),
        "unit_statuses": list(payload.get("unit_statuses") or []),
    }


def _controller_decision_authorization_dedupe_key(
    *,
    authorization_context: dict[str, Any],
    active_run_id: str | None,
) -> str:
    intent_key = str(authorization_context.get("control_intent_key") or "").strip()
    if intent_key:
        return intent_key
    canonical_payload = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
    }
    encoded = json.dumps(canonical_payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode(
        "utf-8"
    )
    return f"controller-decision-authorization:{hashlib.sha256(encoded).hexdigest()}"


def _controller_work_unit_lifecycle_projection(lifecycle: dict[str, Any] | None) -> dict[str, Any]:
    payload = lifecycle if isinstance(lifecycle, dict) else {}
    return {
        "lifecycle_state": str(payload.get("lifecycle_state") or "new").strip() or "new",
        "latest_event_type": payload.get("latest_event_type"),
        "delivery_blocked": bool(payload.get("delivery_blocked")),
        "block_reason": payload.get("block_reason"),
        "terminal_consumed": bool(payload.get("terminal_consumed")),
    }


def _runtime_message_id(payload: dict[str, Any] | None) -> str | None:
    if not isinstance(payload, dict):
        return None
    nested_message = payload.get("message")
    if isinstance(nested_message, dict):
        message_id = str(nested_message.get("id") or nested_message.get("message_id") or "").strip()
        if message_id:
            return message_id
    message_id = str(payload.get("message_id") or payload.get("id") or "").strip()
    return message_id or None


def _write_runtime_state(*, quest_root: Path, runtime_state: dict[str, Any]) -> None:
    runtime_state_path = Path(quest_root).expanduser().resolve() / ".ds" / "runtime_state.json"
    runtime_state_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_state_path.write_text(
        json.dumps(runtime_state, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )


def _reset_same_fingerprint_count_for_new_control_intent(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    current_key = str(authorization_context.get("control_intent_key") or "").strip()
    if not current_key:
        return False
    previous_keys: list[str] = []
    marker = runtime_state.get(_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY)
    if isinstance(marker, dict):
        previous_keys.append(str(marker.get("control_intent_key") or "").strip())
    lifecycle = runtime_state.get(_CONTROL_INTENT_LIFECYCLE_STATE_KEY)
    if isinstance(lifecycle, dict):
        previous_keys.append(str(lifecycle.get("control_intent_key") or "").strip())
    if not any(previous_key and previous_key != current_key for previous_key in previous_keys):
        return False
    runtime_state["same_fingerprint_auto_turn_count"] = 0
    runtime_state.pop(_CONTROL_INTENT_LIFECYCLE_STATE_KEY, None)
    runtime_state.pop(_LIVE_CONTROLLER_REROUTE_RESTART_STATE_KEY, None)
    return True


def _mark_controller_decision_authorization_relayed(
    *,
    quest_root: Path,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
    active_run_id: str | None,
    delivery_mode: str,
    message_id: str | None,
    source: str,
) -> None:
    _reset_same_fingerprint_count_for_new_control_intent(
        runtime_state=runtime_state,
        authorization_context=authorization_context,
    )
    runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY] = {
        "decision_id": str(authorization_context.get("decision_id") or "").strip(),
        "route_target": str(authorization_context.get("route_target") or "").strip(),
        "route_key_question": str(authorization_context.get("route_key_question") or "").strip(),
        "source_route_key_question": str(authorization_context.get("source_route_key_question") or "").strip() or None,
        "work_unit_id": str(authorization_context.get("work_unit_id") or "").strip() or None,
        "work_unit_fingerprint": str(authorization_context.get("work_unit_fingerprint") or "").strip() or None,
        "next_work_unit": dict(authorization_context.get("next_work_unit") or {}),
        "blocking_work_units": list(authorization_context.get("blocking_work_units") or []),
        "control_intent_key": str(authorization_context.get("control_intent_key") or "").strip() or None,
        "control_intent_identity": dict(authorization_context.get("control_intent_identity") or {}),
        "active_run_id": active_run_id,
        "delivery_mode": delivery_mode,
        "message_id": message_id,
        "source": source,
        "controller_work_unit_lifecycle": _controller_work_unit_lifecycle_projection(
            authorization_context.get("controller_work_unit_lifecycle")
        ),
    }
    for key in _WORK_UNIT_TARGET_CONTEXT_KEYS:
        if key in authorization_context:
            runtime_state[_CONTROLLER_DECISION_AUTHORIZATION_STATE_KEY][key] = authorization_context[key]
    _write_runtime_state(quest_root=quest_root, runtime_state=runtime_state)


def _runtime_state_awaits_artifact_delta_or_gate_replay(
    *,
    runtime_state: dict[str, Any],
    authorization_context: dict[str, Any],
) -> bool:
    lifecycle = runtime_state.get(_CONTROL_INTENT_LIFECYCLE_STATE_KEY)
    if not isinstance(lifecycle, dict):
        return False
    if str(lifecycle.get("state") or "").strip() != control_intent.AWAIT_ARTIFACT_DELTA_OR_GATE_REPLAY:
        return False
    lifecycle_key = str(lifecycle.get("control_intent_key") or "").strip()
    current_key = str(authorization_context.get("control_intent_key") or "").strip()
    return bool(lifecycle_key and current_key and lifecycle_key == current_key)


def _controller_decision_authorization_allowed_while_waiting(
    *,
    status: StudyRuntimeStatus,
    authorization_context: dict[str, Any],
) -> bool:
    controller_actions = {
        str(action).strip()
        for action in authorization_context.get("controller_actions") or ()
        if str(action).strip()
    }
    if controller_actions & _CONTROLLER_DECISION_AUTHORIZATION_WAIT_ALLOWED_ACTIONS:
        return True
    if (
        "run_quality_repair_batch" in controller_actions
        and _quality_repair_authorization_has_current_work_unit(
            status=status,
            authorization_context=authorization_context,
        )
    ):
        return True
    if (
        status.decision is StudyRuntimeDecision.RELAUNCH_STOPPED
        and controller_actions & _CONTROLLER_DECISION_AUTHORIZATION_WAIT_RECOVERY_ACTIONS
    ):
        return True
    return False


def _quality_repair_authorization_has_current_work_unit(
    *,
    status: StudyRuntimeStatus,
    authorization_context: dict[str, Any],
) -> bool:
    next_work_unit = authorization_context.get("next_work_unit")
    if not isinstance(next_work_unit, dict):
        return False
    unit_id = _text(next_work_unit.get("unit_id"))
    work_unit_fingerprint = _text(authorization_context.get("work_unit_fingerprint"))
    if unit_id is None or work_unit_fingerprint is None:
        return False
    supervisor_payload = status.extras.get("publication_supervisor_state")
    if (
        isinstance(supervisor_payload, dict)
        and bool(supervisor_payload.get("bundle_tasks_downstream_only"))
        and unit_id in _QUALITY_REPAIR_DOWNSTREAM_WORK_UNIT_IDS
    ):
        return False
    return True
