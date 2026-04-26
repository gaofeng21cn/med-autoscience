from __future__ import annotations

from datetime import datetime
from typing import Any, Mapping

from med_autoscience.controllers import paper_line_delivery_metrics


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _parse_time(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None


def _duration_seconds(start: datetime | None, end: datetime | None) -> int | None:
    if start is None or end is None:
        return None
    return max(0, int((end - start).total_seconds()))


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


def _window_bounds(category_windows: Mapping[str, Any]) -> tuple[datetime | None, datetime | None]:
    starts: list[datetime] = []
    ends: list[datetime] = []
    for window in category_windows.values():
        if not isinstance(window, Mapping):
            continue
        first = _parse_time(window.get("first_at"))
        latest = _parse_time(window.get("latest_at"))
        if first is not None:
            starts.append(first)
        if latest is not None:
            ends.append(latest)
    return (min(starts) if starts else None, max(ends) if ends else None)


def _step_duration(step_timings: object, *, from_step: str, to_step: str) -> int | None:
    for item in _list(step_timings):
        if not isinstance(item, Mapping):
            continue
        if _text(item.get("from_step")) == from_step and _text(item.get("to_step")) == to_step:
            return _int(item.get("duration_seconds"))
    return None


def _repeated_dispatch_count(controller_fingerprints: Mapping[str, Any]) -> int:
    total = 0
    for item in _list(controller_fingerprints.get("top_repeats")):
        if isinstance(item, Mapping):
            total += max(0, _int(item.get("count")) - 1)
    return total


def build_cycle_observability(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    category_windows = _mapping(profile_payload.get("category_windows"))
    first_event_at, latest_event_at = _window_bounds(category_windows)
    step_timings = profile_payload.get("step_timings")
    runtime_summary = _mapping(profile_payload.get("runtime_transition_summary"))
    controller_fingerprints = _mapping(profile_payload.get("controller_decision_fingerprints"))
    sli_summary = _mapping(profile_payload.get("sli_summary"))
    gate_summary = _mapping(profile_payload.get("gate_blocker_summary"))
    autonomy_slo = _mapping(profile_payload.get("autonomy_slo"))
    long_run_health = _mapping(autonomy_slo.get("long_run_health"))
    quality_constraint = _mapping(autonomy_slo.get("quality_constraint"))

    repeated_dispatch_count = _repeated_dispatch_count(controller_fingerprints)
    runtime_recovery_observations = _int(sli_summary.get("runtime_recovery_observations"))
    runtime_flapping_transitions = _int(sli_summary.get("runtime_flapping_transitions"))
    open_blockers = [
        str(item)
        for item in _list(gate_summary.get("current_blockers"))
        if str(item or "").strip()
    ]
    blocker_state = "open_quality_gate" if open_blockers else "no_open_quality_gate"
    no_progress_signal = bool(repeated_dispatch_count or runtime_recovery_observations or runtime_flapping_transitions)
    trace_identity = paper_line_delivery_metrics.normalize_trace_identity(profile_payload)

    payload = {
        "surface": "cycle_observability",
        "schema_version": 1,
        "study_id": _text(profile_payload.get("study_id")),
        "quest_id": _text(profile_payload.get("quest_id")),
        "trace_identity": trace_identity,
        "flow_metrics": {
            "observed_event_count": _int(_mapping(profile_payload.get("profiling_window")).get("event_count")),
            "first_observed_at": first_event_at.isoformat() if first_event_at is not None else None,
            "latest_observed_at": latest_event_at.isoformat() if latest_event_at is not None else None,
            "observed_lead_time_seconds": _duration_seconds(first_event_at, latest_event_at),
            "task_intake_to_run_start_seconds": _step_duration(
                step_timings,
                from_step="task_intake",
                to_step="run_start",
            ),
            "run_start_to_latest_eval_seconds": _step_duration(
                step_timings,
                from_step="run_start",
                to_step="publication_eval",
            ),
        },
        "stability_metrics": {
            "runtime_live_ratio": _float(sli_summary.get("runtime_live_ratio")),
            "runtime_recovery_observations": runtime_recovery_observations,
            "runtime_flapping_transitions": runtime_flapping_transitions,
            "repeated_controller_dispatch_count": repeated_dispatch_count,
            "runtime_health_status_counts": dict(_mapping(runtime_summary.get("health_status_counts"))),
            "long_run_health_state": _text(long_run_health.get("state")),
        },
        "quality_preservation": {
            "blocker_state": blocker_state,
            "open_blocker_count": len(open_blockers),
            "gate_relaxation_allowed": bool(quality_constraint.get("gate_relaxation_allowed")),
            "must_preserve_authority_surfaces": list(
                _list(quality_constraint.get("must_preserve_authority_surfaces"))
            ),
        },
        "acceleration_readiness": {
            "state": "restore_before_accelerating" if no_progress_signal else "ready_for_bounded_fast_lane",
            "no_progress_signal": no_progress_signal,
            "requires_quality_gate_preservation": True,
            "next_work_unit_id": _text(sli_summary.get("next_work_unit_id")),
        },
    }
    delivery_metrics = profile_payload.get("paper_line_delivery_metrics")
    if isinstance(delivery_metrics, Mapping):
        payload["paper_line_delivery_metrics"] = dict(delivery_metrics)
    return payload
