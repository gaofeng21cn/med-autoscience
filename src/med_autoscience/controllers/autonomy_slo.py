from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import runtime_failure_taxonomy


_RUNTIME_LIVE_RATIO_TARGET = 0.95
_QUALITY_AUTHORITY_SURFACES = [
    "study_charter",
    "evidence_ledger",
    "review_ledger",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
]

_ACTION_BY_INCIDENT = {
    "runtime_recovery_churn": {
        "action_type": "probe_runtime_recovery",
        "controller_surface": "runtime_watch",
        "priority": "now",
        "summary": "Confirm runtime liveness before any blind resume.",
    },
    "repeated_controller_decision": {
        "action_type": "dedupe_controller_dispatch",
        "controller_surface": "runtime_watch",
        "priority": "now",
        "summary": "Suppress repeated dispatch for the same blocker fingerprint.",
    },
    "publication_gate_blocked": {
        "action_type": "run_publication_work_unit",
        "controller_surface": "gate_clearing_batch",
        "priority": "now",
        "summary": "Route active gate blockers into one bounded work unit.",
    },
    "non_actionable_gate": {
        "action_type": "request_gate_specificity",
        "controller_surface": "publication_gate",
        "priority": "now",
        "summary": "Request concrete blocker targets before dispatching another run.",
    },
    "stale_current_package": {
        "action_type": "refresh_current_package_after_settle",
        "controller_surface": "gate_clearing_batch",
        "priority": "next",
        "summary": "Refresh the human-facing package after authority surfaces settle.",
    },
}

_PRIORITY_WEIGHT = {"now": 0, "next": 1, "monitor": 2}
_SEVERITY_WEIGHT = {"high": 0, "medium": 1, "low": 2, "unknown": 3}


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _float(value: object) -> float | None:
    if value is None:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _current_blockers(gate_summary: Mapping[str, Any]) -> list[str]:
    return [
        blocker
        for item in _list(gate_summary.get("current_blockers"))
        if (blocker := _text(item)) is not None
    ]


def _incident_types(profile_payload: Mapping[str, Any]) -> list[str]:
    types: list[str] = []
    for candidate in _list(profile_payload.get("autonomy_incident_candidates")):
        if isinstance(candidate, Mapping):
            incident_type = _text(candidate.get("incident_type"))
            if incident_type is not None:
                types.append(incident_type)
    return types


def _bottleneck_types(profile_payload: Mapping[str, Any]) -> list[str]:
    types: list[str] = []
    for bottleneck in _list(profile_payload.get("bottlenecks")):
        if isinstance(bottleneck, Mapping):
            bottleneck_id = _text(bottleneck.get("bottleneck_id"))
            if bottleneck_id is not None:
                types.append(bottleneck_id)
    return types


def _long_run_health(
    *,
    sli_summary: Mapping[str, Any],
    mds_activity: Mapping[str, Any],
    incident_types: list[str],
) -> dict[str, Any]:
    live_ratio = _float(sli_summary.get("runtime_live_ratio"))
    recovery_observations = _int(sli_summary.get("runtime_recovery_observations"))
    flapping_transitions = _int(sli_summary.get("runtime_flapping_transitions"))
    activity_state = _text(mds_activity.get("activity_state"))
    heartbeat_state = _text(mds_activity.get("heartbeat_state"))
    if (
        "runtime_recovery_churn" in incident_types
        or activity_state == "recovering"
        or heartbeat_state == "missing_live_session"
    ):
        state = "breach"
    elif live_ratio is None:
        state = "unknown"
    elif live_ratio >= _RUNTIME_LIVE_RATIO_TARGET and recovery_observations == 0 and flapping_transitions == 0:
        state = "met"
    elif live_ratio >= _RUNTIME_LIVE_RATIO_TARGET:
        state = "watch"
    else:
        state = "breach"
    return {
        "state": state,
        "runtime_live_ratio": live_ratio,
        "runtime_live_ratio_target": _RUNTIME_LIVE_RATIO_TARGET,
        "runtime_recovery_observations": recovery_observations,
        "runtime_flapping_transitions": flapping_transitions,
        "worker_activity_state": activity_state,
        "worker_heartbeat_state": heartbeat_state,
    }


def _progress_health(
    *,
    sli_summary: Mapping[str, Any],
    gate_summary: Mapping[str, Any],
    incident_types: list[str],
    bottleneck_types: list[str],
) -> dict[str, Any]:
    duplicate_dispatch_active = bool(sli_summary.get("duplicate_dispatch_active"))
    no_progress_reasons: list[str] = []
    if duplicate_dispatch_active or "repeated_controller_decision" in incident_types:
        no_progress_reasons.append("repeated_controller_dispatch")
    if "runtime_recovery_churn" in incident_types:
        no_progress_reasons.append("runtime_recovery_churn")
    if "non_actionable_gate" in incident_types or "non_actionable_gate" in bottleneck_types:
        no_progress_reasons.append("non_actionable_gate")
    blockers = _current_blockers(gate_summary)
    if "publication_gate_blocked" in incident_types or "publication_gate_blocked" in bottleneck_types:
        state = "incident_candidate"
    elif no_progress_reasons:
        state = "no_progress_candidate"
    elif blockers:
        state = "blocked_with_actionable_work"
    else:
        state = "progressing_or_insufficient_evidence"
    return {
        "state": state,
        "no_progress_candidate": bool(no_progress_reasons),
        "no_progress_reasons": no_progress_reasons,
        "incident_candidate": bool(incident_types),
        "duplicate_dispatch_active": duplicate_dispatch_active,
        "next_work_unit_id": _text(sli_summary.get("next_work_unit_id")),
        "current_blockers": blockers,
    }


def _default_next_work_unit(profile_payload: Mapping[str, Any]) -> Mapping[str, Any]:
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    return _mapping(gate_summary.get("next_work_unit"))


def _recovery_actions(profile_payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = _text(profile_payload.get("study_id")) or "unknown-study"
    default_next_work_unit = _default_next_work_unit(profile_payload)
    actions: list[dict[str, Any]] = []
    seen_action_types: set[str] = set()

    def append_action(
        *,
        incident_type: str,
        severity: str,
        source: str,
        source_ref: str | None,
        next_work_unit: Mapping[str, Any],
        source_rank: int,
    ) -> None:
        policy = _ACTION_BY_INCIDENT.get(incident_type)
        if policy is None:
            return
        action_type = str(policy["action_type"])
        if action_type in seen_action_types:
            return
        seen_action_types.add(action_type)
        actions.append(
            {
                "action_id": f"autonomy-slo-action::{study_id}::{incident_type}",
                "study_id": study_id,
                "source": source,
                "source_ref": source_ref,
                "source_incident_type": incident_type,
                "source_severity": severity,
                "next_work_unit_id": _text(next_work_unit.get("unit_id")),
                "apply_mode": "controller_only",
                "quality_gate_relaxation_allowed": False,
                "source_rank": source_rank,
                **policy,
            }
        )

    for source_rank, candidate in enumerate(_list(profile_payload.get("autonomy_incident_candidates")), start=1):
        if not isinstance(candidate, Mapping):
            continue
        incident_type = _text(candidate.get("incident_type"))
        if incident_type is None:
            continue
        next_work_unit = _mapping(candidate.get("next_work_unit")) or default_next_work_unit
        append_action(
            incident_type=incident_type,
            severity=_text(candidate.get("severity")) or "unknown",
            source="autonomy_incident_candidate",
            source_ref=_text(candidate.get("incident_id")),
            next_work_unit=next_work_unit,
            source_rank=source_rank,
        )

    for source_rank, bottleneck in enumerate(_list(profile_payload.get("bottlenecks")), start=100):
        if not isinstance(bottleneck, Mapping):
            continue
        bottleneck_id = _text(bottleneck.get("bottleneck_id"))
        if bottleneck_id is None:
            continue
        append_action(
            incident_type=bottleneck_id,
            severity=_text(bottleneck.get("severity")) or "unknown",
            source="study_cycle_bottleneck",
            source_ref=bottleneck_id,
            next_work_unit=default_next_work_unit,
            source_rank=source_rank,
        )

    ordered = sorted(
        actions,
        key=lambda item: (
            _PRIORITY_WEIGHT.get(str(item.get("priority") or ""), 9),
            _SEVERITY_WEIGHT.get(str(item.get("source_severity") or "unknown"), 9),
            int(item.get("source_rank") or 999),
            str(item.get("action_id") or ""),
        ),
    )
    for rank, action in enumerate(ordered, start=1):
        action["restore_rank"] = rank
        action.pop("source_rank", None)
    return ordered


def _runtime_failure_action(
    *,
    study_id: str,
    classification: Mapping[str, Any],
) -> dict[str, Any] | None:
    action_mode = _text(classification.get("action_mode"))
    blocker_class = _text(classification.get("blocker_class"))
    diagnosis_code = _text(classification.get("diagnosis_code"))
    if action_mode in {"external_fix_required", "provider_backoff_and_recheck"}:
        return {
            "action_id": f"autonomy-slo-action::{study_id}::{diagnosis_code or blocker_class}",
            "study_id": study_id,
            "source": "mds_failure_taxonomy",
            "source_ref": diagnosis_code,
            "source_incident_type": blocker_class,
            "source_severity": "high" if action_mode == "external_fix_required" else "medium",
            "next_work_unit_id": None,
            "apply_mode": "human_required" if action_mode == "external_fix_required" else "controller_only",
            "quality_gate_relaxation_allowed": False,
            "action_type": "external_runtime_blocker",
            "controller_surface": "runtime_watch",
            "priority": "now",
            "summary": "Resolve the external runtime/provider blocker before retrying MAS work.",
            "restore_rank": 0,
        }
    if action_mode == "platform_repair_required":
        return {
            "action_id": f"autonomy-slo-action::{study_id}::{diagnosis_code or blocker_class}",
            "study_id": study_id,
            "source": "mds_failure_taxonomy",
            "source_ref": diagnosis_code,
            "source_incident_type": blocker_class,
            "source_severity": "high",
            "next_work_unit_id": None,
            "apply_mode": "platform_repair",
            "quality_gate_relaxation_allowed": False,
            "action_type": "platform_runtime_repair",
            "controller_surface": "runtime_watch",
            "priority": "now",
            "summary": "Repair the MAS/MDS runtime protocol path before resuming the study.",
            "restore_rank": 0,
        }
    if action_mode == "wait_for_user_or_explicit_resume":
        return {
            "action_id": f"autonomy-slo-action::{study_id}::{diagnosis_code or blocker_class}",
            "study_id": study_id,
            "source": "mds_failure_taxonomy",
            "source_ref": diagnosis_code,
            "source_incident_type": blocker_class,
            "source_severity": "medium",
            "next_work_unit_id": None,
            "apply_mode": "human_required",
            "quality_gate_relaxation_allowed": False,
            "action_type": "human_resume_gate",
            "controller_surface": "runtime_watch",
            "priority": "now",
            "summary": "Wait for the explicit user/resume gate instead of relaunching blindly.",
            "restore_rank": 0,
        }
    return None


def _slo_execution_plan(
    *,
    runtime_failure_action: Mapping[str, Any] | None,
    runtime_failure_classification: Mapping[str, Any],
    recovery_actions: list[dict[str, Any]],
) -> dict[str, Any]:
    steps = (
        [dict(runtime_failure_action)]
        if runtime_failure_action is not None
        else [dict(action) for action in recovery_actions]
    )
    action_mode = _text(runtime_failure_classification.get("action_mode"))
    if action_mode in {"external_fix_required", "provider_backoff_and_recheck"}:
        state = "blocked_by_external_runtime"
    elif action_mode in {"platform_repair_required", "wait_for_user_or_explicit_resume"}:
        state = "blocked_by_runtime_gate"
    elif steps:
        state = "ready_for_controller_execution"
    else:
        state = "monitor_only"
    return {
        "surface": "autonomy_slo_execution_plan",
        "schema_version": 1,
        "state": state,
        "step_count": len(steps),
        "steps": steps,
        "gate_relaxation_allowed": False,
        "apply_mode": steps[0].get("apply_mode") if steps else "monitor",
        "quality_authority_surfaces": list(_QUALITY_AUTHORITY_SURFACES),
    }


def _efficiency_signals(
    *,
    sli_summary: Mapping[str, Any],
    mds_activity: Mapping[str, Any],
    long_run_health: Mapping[str, Any],
) -> list[dict[str, Any]]:
    live_ratio = _float(sli_summary.get("runtime_live_ratio"))
    duplicate_dispatch_active = bool(sli_summary.get("duplicate_dispatch_active"))
    package_stale = bool(sli_summary.get("package_stale_is_current_bottleneck"))
    flapping_transitions = _int(sli_summary.get("runtime_flapping_transitions"))
    heartbeat_state = _text(mds_activity.get("heartbeat_state"))
    signals = [
        {
            "signal_id": "runtime_live_ratio",
            "source": "profile_sli",
            "state": long_run_health.get("state"),
            "value": live_ratio,
            "target": f">={_RUNTIME_LIVE_RATIO_TARGET}",
        },
        {
            "signal_id": "controller_duplicate_dispatch",
            "source": "profile_sli",
            "state": "breach" if duplicate_dispatch_active else "met",
            "value": duplicate_dispatch_active,
            "target": False,
        },
        {
            "signal_id": "runtime_flapping_transitions",
            "source": "profile_sli",
            "state": "breach" if flapping_transitions > 0 else "met",
            "value": flapping_transitions,
            "target": 0,
        },
        {
            "signal_id": "current_package_staleness",
            "source": "profile_sli",
            "state": "watch" if package_stale else "met",
            "value": package_stale,
            "target": False,
        },
    ]
    if heartbeat_state is not None:
        signals.append(
            {
                "signal_id": "worker_heartbeat",
                "source": "mds_worker_activity",
                "state": "breach" if heartbeat_state == "missing_live_session" else "met",
                "value": heartbeat_state,
                "target": "live",
            }
        )
    return signals


def build_autonomy_slo_signals(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    sli_summary = _mapping(profile_payload.get("sli_summary"))
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    mds_activity = _mapping(profile_payload.get("mds_worker_activity"))
    incident_types = _incident_types(profile_payload)
    bottleneck_types = _bottleneck_types(profile_payload)
    long_run_health = _long_run_health(
        sli_summary=sli_summary,
        mds_activity=mds_activity,
        incident_types=incident_types,
    )
    progress_health = _progress_health(
        sli_summary=sli_summary,
        gate_summary=gate_summary,
        incident_types=incident_types,
        bottleneck_types=bottleneck_types,
    )
    runtime_failure_classification = runtime_failure_taxonomy.classify_runtime_failure_from_profile(profile_payload)
    recovery_actions = _recovery_actions(profile_payload)
    runtime_failure_action = _runtime_failure_action(
        study_id=_text(profile_payload.get("study_id")) or "unknown-study",
        classification=runtime_failure_classification,
    )
    slo_execution_plan = _slo_execution_plan(
        runtime_failure_action=runtime_failure_action,
        runtime_failure_classification=runtime_failure_classification,
        recovery_actions=recovery_actions,
    )
    top_action = (slo_execution_plan["steps"][0] if slo_execution_plan["steps"] else {})
    efficiency_signals = _efficiency_signals(
        sli_summary=sli_summary,
        mds_activity=mds_activity,
        long_run_health=long_run_health,
    )
    breach_signal_ids = [
        str(signal["signal_id"])
        for signal in efficiency_signals
        if isinstance(signal, Mapping) and signal.get("state") == "breach"
    ]
    watch_signal_ids = [
        str(signal["signal_id"])
        for signal in efficiency_signals
        if isinstance(signal, Mapping) and signal.get("state") == "watch"
    ]
    return {
        "surface": "autonomy_slo",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "slo_targets": {
            "runtime_live_ratio_min": _RUNTIME_LIVE_RATIO_TARGET,
            "runtime_flapping_transitions_max": 0,
            "duplicate_dispatch_allowed": False,
            "quality_gate_relaxation_allowed": False,
        },
        "long_run_health": long_run_health,
        "progress_health": progress_health,
        "incident_loop": {
            "candidate_count": len(incident_types),
            "candidate_types": incident_types,
            "restore_priority": top_action.get("priority") or "monitor",
            "top_action_type": top_action.get("action_type") or "monitor_autonomy_slo",
            "top_controller_surface": top_action.get("controller_surface"),
        },
        "runtime_failure_classification": runtime_failure_classification,
        "recovery_actions": recovery_actions,
        "slo_execution_plan": slo_execution_plan,
        "efficiency_summary": {
            "signal_count": len(efficiency_signals),
            "breach_signal_ids": breach_signal_ids,
            "watch_signal_ids": watch_signal_ids,
        },
        "efficiency_signals": efficiency_signals,
        "quality_constraint": {
            "mode": "quality_preserving_recovery",
            "allowed_apply_mode": "controller_only",
            "gate_relaxation_allowed": False,
            "requires_concrete_publication_blocker": (
                gate_summary.get("actionability_status") == "blocked_by_non_actionable_gate"
            ),
            "must_preserve_authority_surfaces": [
                *_QUALITY_AUTHORITY_SURFACES,
            ],
        },
    }
