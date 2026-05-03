from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import (
    auto_runtime_parking,
    control_plane_facts,
    control_plane_reconciler,
    runtime_failure_taxonomy,
    study_control_plane_kernel,
)


CONTROL_PLANE_STATES: tuple[str, ...] = (
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
        "resource_release_expected": False,
        "long_write_turn_allowed": True,
        "recovery_route": "continue_supervising_live_runtime",
        "human_gate_required": False,
        "operator_summary": "Managed runtime is live; continue supervising the active run without changing quality gates.",
    },
    "queued": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "resource_release_expected": False,
        "long_write_turn_allowed": False,
        "recovery_route": "dispatch_or_wait_for_runtime_slot",
        "human_gate_required": False,
        "operator_summary": "No active worker evidence is present yet; keep the study queued for controller-owned dispatch.",
    },
    "running": {
        "owner": "mds_runtime_worker",
        "auto_recovery_allowed": True,
        "resource_release_expected": False,
        "long_write_turn_allowed": False,
        "recovery_route": "observe_worker_until_live_or_stalled",
        "human_gate_required": False,
        "operator_summary": "Runtime reports a running worker but live heartbeat is not yet decisive.",
    },
    "stalled": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "resource_release_expected": False,
        "long_write_turn_allowed": False,
        "recovery_route": "runtime_watch_stall_recovery",
        "human_gate_required": False,
        "operator_summary": "Runtime progress is stalled; route through runtime watch recovery before new work dispatch.",
    },
    "no_live": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "resource_release_expected": False,
        "long_write_turn_allowed": False,
        "recovery_route": "reconcile_no_live_worker_then_resume",
        "human_gate_required": False,
        "operator_summary": "Study surface still expects a worker, but no live worker is attached; reconcile liveness first.",
    },
    "recovering": {
        "owner": "mas_controller",
        "auto_recovery_allowed": True,
        "resource_release_expected": False,
        "long_write_turn_allowed": False,
        "recovery_route": "wait_for_recovery_confirmation",
        "human_gate_required": False,
        "operator_summary": "Controller recovery is already in flight; wait for the next live confirmation.",
    },
    "blocked_human": {
        "owner": "human_operator",
        "auto_recovery_allowed": False,
        "resource_release_expected": True,
        "long_write_turn_allowed": False,
        "recovery_route": "wait_for_explicit_human_gate_release",
        "human_gate_required": True,
        "operator_summary": "Execution is intentionally parked behind an explicit human or resume gate.",
    },
    "blocked_external": {
        "owner": "external_runtime_or_operator",
        "auto_recovery_allowed": False,
        "resource_release_expected": True,
        "long_write_turn_allowed": False,
        "recovery_route": "resolve_external_blocker_then_recheck_runtime",
        "human_gate_required": True,
        "operator_summary": "An external provider or account blocker must be cleared before MAS resumes work.",
    },
    "blocked_platform": {
        "owner": "mas_platform_sre",
        "auto_recovery_allowed": False,
        "resource_release_expected": True,
        "long_write_turn_allowed": False,
        "recovery_route": "repair_platform_contract_before_resume",
        "human_gate_required": True,
        "operator_summary": "A MAS/MDS platform protocol failure owns the next step; repair the controller surface first.",
    },
}

_GATE_BLOCKER_REASONS = frozenset(
    {
        "quest_waiting_on_invalid_blocking",
        "quest_completion_requested_before_publication_gate_clear",
        "quest_drifting_into_write_without_gate_approval",
        "quest_stale_decision_after_write_stage_ready",
    }
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def control_plane_state_catalog() -> dict[str, dict[str, Any]]:
    return {state: {"state": state, **dict(_STATE_SPECS[state])} for state in CONTROL_PLANE_STATES}


def control_plane_state_spec(state: str) -> dict[str, Any]:
    if state not in _STATE_SPECS:
        raise ValueError(f"unsupported control-plane state: {state}")
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
    if action_mode in {"platform_repair_required", "platform_startup_backoff_and_recheck"}:
        return "blocked_platform"
    if blocker_class in {"platform_protocol_or_runner_bug", "platform_runtime_startup_noise"}:
        return "blocked_platform"
    if action_mode == "wait_for_user_or_explicit_resume":
        return "blocked_human"
    if diagnosis_code == "daemon_no_live_worker":
        return "no_live"
    if diagnosis_code == "daemon_stalled_live_turn":
        return "stalled"
    return None


def _state_from_auto_runtime_parked(projection: Mapping[str, Any]) -> str | None:
    if not bool(projection.get("parked")):
        return None
    owner = _text(projection.get("parked_owner"))
    if owner == "external_provider":
        return "blocked_external"
    if owner in {"mas_platform", "controller"}:
        return "blocked_platform"
    return "blocked_human"


def _state_from_control_plane_facts(facts: control_plane_facts.ControlPlaneFacts) -> str | None:
    if facts.reason in _GATE_BLOCKER_REASONS:
        return None
    if facts.strict_live:
        return "live"
    if facts.missing_live_session:
        return "no_live"
    if facts.recovery_pending:
        return "recovering"
    if facts.worker_running is True:
        return "running"
    if facts.worker_pending is True:
        return "queued"
    if facts.quest_status in {"running", "active"} and facts.active_run_id is not None:
        return "running"
    if facts.quest_status in {"queued", "pending"}:
        return "queued"
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
    state = _text(current_state.get("state"))
    if runtime_reason in _GATE_BLOCKER_REASONS:
        return None
    if runtime_reason == "quest_marked_running_but_no_live_session":
        return "no_live"
    if state == "auto_runtime_parked":
        parked_state = _state_from_auto_runtime_parked(current_state)
        if parked_state is not None:
            return parked_state
    if runtime_reason == "quest_waiting_for_submission_metadata" or state == "manual_finishing":
        return "blocked_human"
    if runtime_health_status == "live":
        return "live"
    if runtime_health_status == "recovering":
        return "recovering"
    if runtime_health_status in {"degraded", "escalated"}:
        return "stalled"
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


def resolve_control_plane_state(profile_payload: Mapping[str, Any]) -> str:
    return build_control_plane_state_surface(profile_payload)["current_state"]


def build_control_plane_state_surface(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    status_payload = _mapping(profile_payload)
    control_plane_snapshot = study_control_plane_kernel.build_control_plane_snapshot(status_payload)
    supervisor_tick_audit = _mapping(status_payload.get("supervisor_tick_audit"))
    facts = control_plane_facts.resolve_control_plane_facts(
        status_payload,
        supervisor_tick_audit=supervisor_tick_audit,
    )
    runtime_failure = _runtime_failure(status_payload)
    existing_parked_projection = _mapping(status_payload.get("auto_runtime_parked"))
    auto_runtime_parked = (
        existing_parked_projection
        if "parked" in existing_parked_projection
        else auto_runtime_parking.build_auto_runtime_parked_projection(
            status_payload,
            runtime_failure_classification=runtime_failure,
        )
    )
    state = (
        _state_from_runtime_failure(runtime_failure)
        or _state_from_auto_runtime_parked(auto_runtime_parked)
        or _state_from_control_plane_facts(facts)
        or _state_from_worker_activity(_mapping(status_payload.get("mds_worker_activity")))
        or _state_from_current_summary(_mapping(status_payload.get("current_state_summary")))
        or _state_from_sli(_mapping(status_payload.get("sli_summary")))
        or "queued"
    )
    state_spec = control_plane_state_spec(state)
    reconciler = control_plane_reconciler.reconcile_next_action(
        current_state=state,
        state_spec=state_spec,
        profile_payload=status_payload,
        auto_runtime_parked=auto_runtime_parked,
        runtime_failure_classification=runtime_failure,
    )
    return {
        "surface": "control_plane_state",
        "schema_version": 1,
        "study_id": _text(status_payload.get("study_id")),
        "quest_id": _text(status_payload.get("quest_id")),
        "control_plane_snapshot": control_plane_snapshot,
        "control_plane_epoch": (
            control_plane_snapshot["authority_refs"]["study_truth"].get("epoch")
            if isinstance(control_plane_snapshot.get("authority_refs"), Mapping)
            and isinstance(control_plane_snapshot["authority_refs"].get("study_truth"), Mapping)
            else None
        ),
        "current_state": state,
        "current_state_spec": state_spec,
        "control_plane_facts": facts.to_runtime_facts_dict(),
        "control_plane_reconciler": reconciler,
        "canonical_next_action": reconciler["canonical_next_action"],
        "auto_runtime_parked": auto_runtime_parked,
        "runtime_failure_classification": dict(runtime_failure) or None,
        "states": control_plane_state_catalog(),
        "transition_policy": {
            "allowed_states": list(CONTROL_PLANE_STATES),
            "quality_gate_relaxation_allowed": False,
        },
        "quality_constraint": {"gate_relaxation_allowed": False},
        "gate_relaxation_allowed": False,
        "owner": state_spec["owner"],
        "auto_recovery_allowed": state_spec["auto_recovery_allowed"],
        "resource_release_expected": state_spec["resource_release_expected"],
        "long_write_turn_allowed": state_spec["long_write_turn_allowed"],
        "operator_summary": state_spec["operator_summary"],
    }
