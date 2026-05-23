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
    handoff_summary = profile_payload.get("opl_runtime_owner_handoff_summary")
    status_counts = (
        handoff_summary.get("status_counts")
        if isinstance(handoff_summary, Mapping)
        else {}
    )
    if not isinstance(status_counts, Mapping):
        status_counts = {}
    handoff_required_count = _int(status_counts.get("handoff_required"))
    handoff_event_count = (
        _int(handoff_summary.get("event_count"))
        if isinstance(handoff_summary, Mapping)
        else 0
    )
    dedupe_summary = profile_payload.get("domain_health_diagnostic_wakeup_dedupe_summary")
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
        "opl_runtime_owner_handoff_required_count": handoff_required_count,
        "opl_runtime_owner_handoff_event_count": handoff_event_count,
        "opl_runtime_owner_handoff_clear_ratio": _ratio(
            max(handoff_event_count - handoff_required_count, 0),
            handoff_event_count,
        ),
        "duplicate_dispatch_active": dedupe_status not in {"dedupe_confirmed", "work_unit_dispatched"},
        "next_work_unit_id": (
            str(next_work_unit.get("unit_id") or "").strip()
            if isinstance(next_work_unit, Mapping)
            else None
        ),
        "package_stale_is_current_bottleneck": package_status == "stale" and not upstream_scientific_blocked,
    }
