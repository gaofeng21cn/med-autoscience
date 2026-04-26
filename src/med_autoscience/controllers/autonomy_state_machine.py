from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import runtime_failure_taxonomy


AUTONOMY_STATES: tuple[str, ...] = (
    "live",
    "queued",
    "running",
    "stalled",
    "no_live",
    "recovering",
    "blocked_human",
    "blocked_external",
    "blocked_platform",
)

_STATE_SPECS: dict[str, dict[str, Any]] = {
    "live": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "recovery_route": "continue_supervising_live_runtime",
        "human_gate_required": False,
        "operator_summary": "Managed runtime is live; continue supervising the active run without changing quality gates.",
    },
    "queued": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "recovery_route": "dispatch_or_wait_for_runtime_slot",
        "human_gate_required": False,
        "operator_summary": "No active worker evidence is present yet; keep the study queued for controller-owned dispatch.",
    },
    "running": {
        "owner": "mds_runtime_worker",
        "auto_recovery_allowed": True,
        "recovery_route": "observe_worker_until_live_or_stalled",
        "human_gate_required": False,
        "operator_summary": "Runtime reports a running worker but live heartbeat is not yet decisive.",
    },
    "stalled": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "recovery_route": "runtime_watch_stall_recovery",
        "human_gate_required": False,
        "operator_summary": "Runtime progress is stalled; route through runtime watch recovery before new work dispatch.",
    },
    "no_live": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "recovery_route": "reconcile_no_live_worker_then_resume",
        "human_gate_required": False,
        "operator_summary": "Study surface still expects a worker, but no live worker is attached; reconcile liveness first.",
    },
    "recovering": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "recovery_route": "wait_for_recovery_confirmation",
        "human_gate_required": False,
        "operator_summary": "Controller recovery is already in flight; wait for the next live confirmation.",
    },
    "blocked_human": {
        "owner": "human_operator",
        "auto_recovery_allowed": False,
        "recovery_route": "wait_for_explicit_human_gate_release",
        "human_gate_required": True,
        "operator_summary": "Execution is intentionally parked behind an explicit human or resume gate.",
    },
    "blocked_external": {
        "owner": "external_runtime_or_operator",
        "auto_recovery_allowed": False,
        "recovery_route": "resolve_external_blocker_then_recheck_runtime",
        "human_gate_required": True,
        "operator_summary": "An external provider or account blocker must be cleared before MAS resumes work.",
    },
    "blocked_platform": {
        "owner": "mas_platform_sre",
        "auto_recovery_allowed": False,
        "recovery_route": "repair_platform_contract_before_resume",
        "human_gate_required": True,
        "operator_summary": "A MAS/MDS platform protocol failure owns the next step; repair the controller surface first.",
    },
}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def autonomy_state_catalog() -> dict[str, dict[str, Any]]:
    return {state: {"state": state, **dict(_STATE_SPECS[state])} for state in AUTONOMY_STATES}


def state_spec(state: str) -> dict[str, Any]:
    if state not in _STATE_SPECS:
        raise ValueError(f"unsupported autonomy state: {state}")
    return {"state": state, **dict(_STATE_SPECS[state])}


def _runtime_failure(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = _mapping(profile_payload.get("runtime_failure_classification"))
    if direct:
        return direct
    nested = _mapping(_mapping(profile_payload.get("autonomy_slo")).get("runtime_failure_classification"))
    if nested:
        return nested
    return runtime_failure_taxonomy.classify_runtime_failure_from_profile(profile_payload)


def _state_from_runtime_failure(classification: Mapping[str, Any]) -> str | None:
    action_mode = _text(classification.get("action_mode"))
    blocker_class = _text(classification.get("blocker_class"))
    diagnosis_code = _text(classification.get("diagnosis_code"))
    if action_mode in {"external_fix_required", "provider_backoff_and_recheck"}:
        return "blocked_external"
    if action_mode == "platform_repair_required" or blocker_class == "platform_protocol_or_runner_bug":
        return "blocked_platform"
    if action_mode == "wait_for_user_or_explicit_resume":
        return "blocked_human"
    if diagnosis_code == "daemon_no_live_worker":
        return "no_live"
    if diagnosis_code == "daemon_stalled_live_turn":
        return "stalled"
    return None


def _state_from_worker_activity(activity: Mapping[str, Any]) -> str | None:
    activity_state = _text(activity.get("activity_state"))
    heartbeat_state = _text(activity.get("heartbeat_state"))
    quest_status = _text(activity.get("quest_status"))
    reason = _text(activity.get("reason")) or _text(activity.get("runtime_reason"))
    if heartbeat_state == "missing_live_session" or reason == "quest_marked_running_but_no_live_session":
        return "no_live"
    if activity_state == "recovering":
        return "recovering"
    if activity_state == "stalled":
        return "stalled"
    if activity_state == "running" and heartbeat_state == "live":
        return "live"
    if quest_status == "running" or activity_state == "running":
        return "running"
    if quest_status in {"waiting_for_user", "parked"}:
        return "blocked_human"
    if quest_status in {"queued", "pending"}:
        return "queued"
    return None


def _state_from_current_summary(current_state: Mapping[str, Any]) -> str | None:
    runtime_health_status = _text(current_state.get("runtime_health_status"))
    runtime_reason = _text(current_state.get("runtime_reason"))
    runtime_decision = _text(current_state.get("runtime_decision"))
    state = _text(current_state.get("state"))
    if runtime_reason == "quest_waiting_for_submission_metadata" or state == "manual_finishing":
        return "blocked_human"
    if runtime_reason == "quest_marked_running_but_no_live_session":
        return "no_live"
    if runtime_health_status == "live":
        return "live"
    if runtime_health_status == "recovering":
        return "recovering"
    if runtime_health_status in {"degraded", "escalated"}:
        return "stalled"
    if runtime_health_status == "inactive" and runtime_decision in {"blocked", "pause"}:
        return "blocked_human"
    return None


def _state_from_sli(sli_summary: Mapping[str, Any]) -> str | None:
    recovery_observations = int(sli_summary.get("runtime_recovery_observations") or 0)
    flapping_transitions = int(sli_summary.get("runtime_flapping_transitions") or 0)
    if flapping_transitions > 0:
        return "stalled"
    if recovery_observations > 0:
        return "recovering"
    live_ratio = sli_summary.get("runtime_live_ratio")
    if live_ratio is not None:
        try:
            if float(live_ratio) >= 1.0:
                return "live"
        except (TypeError, ValueError):
            return None
    return None


def resolve_autonomy_state(profile_payload: Mapping[str, Any]) -> str:
    runtime_state = _state_from_runtime_failure(_runtime_failure(profile_payload))
    if runtime_state is not None:
        return runtime_state
    activity_state = _state_from_worker_activity(_mapping(profile_payload.get("mds_worker_activity")))
    if activity_state is not None:
        return activity_state
    current_state = _state_from_current_summary(_mapping(profile_payload.get("current_state_summary")))
    if current_state is not None:
        return current_state
    sli_state = _state_from_sli(_mapping(profile_payload.get("sli_summary")))
    if sli_state is not None:
        return sli_state
    return "queued"


def build_autonomy_state_machine_surface(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    current_state = resolve_autonomy_state(profile_payload)
    current_state_spec = state_spec(current_state)
    return {
        "surface": "autonomy_state_machine",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "current_state": current_state,
        "current_state_spec": current_state_spec,
        "states": autonomy_state_catalog(),
        "transition_policy": {
            "allowed_states": list(AUTONOMY_STATES),
            "quality_gate_relaxation_allowed": False,
        },
        "quality_constraint": {"gate_relaxation_allowed": False},
        "gate_relaxation_allowed": False,
        "operator_summary": current_state_spec["operator_summary"],
    }
