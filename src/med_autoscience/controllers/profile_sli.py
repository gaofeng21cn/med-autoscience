from __future__ import annotations

from typing import Any, Mapping


def _int(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _ratio(numerator: int, denominator: int) -> float | None:
    if denominator <= 0:
        return None
    return round(numerator / denominator, 3)


def build_sli_summary(profile_payload: Mapping[str, Any]) -> dict[str, Any]:
    runtime_summary = profile_payload.get("runtime_transition_summary")
    health_counts = (
        runtime_summary.get("health_status_counts")
        if isinstance(runtime_summary, Mapping)
        else {}
    )
    if not isinstance(health_counts, Mapping):
        health_counts = {}
    live_count = _int(health_counts.get("live"))
    recovery_observations = sum(_int(health_counts.get(status)) for status in ("recovering", "degraded", "escalated"))
    total_observations = live_count + recovery_observations + _int(health_counts.get("inactive"))
    dedupe_summary = profile_payload.get("runtime_watch_wakeup_dedupe_summary")
    dedupe_status = (
        str(dedupe_summary.get("status") or "").strip()
        if isinstance(dedupe_summary, Mapping)
        else ""
    )
    gate_summary = profile_payload.get("gate_blocker_summary")
    next_work_unit = gate_summary.get("next_work_unit") if isinstance(gate_summary, Mapping) else None
    current_blockers = gate_summary.get("current_blockers") if isinstance(gate_summary, Mapping) else []
    blockers = [str(item or "").strip() for item in current_blockers or [] if str(item or "").strip()]
    package_currentness = profile_payload.get("package_currentness")
    package_status = (
        str(package_currentness.get("status") or "").strip()
        if isinstance(package_currentness, Mapping)
        else ""
    )
    upstream_scientific_blocked = any(
        "claim" in blocker
        or "evidence" in blocker
        or "medical_publication_surface" in blocker
        for blocker in blockers
    )
    return {
        "runtime_live_ratio": _ratio(live_count, total_observations),
        "runtime_recovery_observations": recovery_observations,
        "runtime_flapping_transitions": sum(
            _int(value)
            for value in (
                runtime_summary.get("transition_counts", {}).values()
                if isinstance(runtime_summary, Mapping)
                and isinstance(runtime_summary.get("transition_counts"), Mapping)
                else []
            )
        ),
        "duplicate_dispatch_active": dedupe_status not in {"dedupe_confirmed", "work_unit_dispatched"},
        "next_work_unit_id": (
            str(next_work_unit.get("unit_id") or "").strip()
            if isinstance(next_work_unit, Mapping)
            else None
        ),
        "package_stale_is_current_bottleneck": package_status == "stale" and not upstream_scientific_blocked,
    }
