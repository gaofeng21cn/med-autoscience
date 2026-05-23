from __future__ import annotations

from typing import Any, Mapping


_ACTION_BY_BOTTLENECK = {
    "opl_runtime_owner_handoff_required": {
        "action_type": "request_opl_handoff_hydration",
        "controller_surface": "domain_health_diagnostic",
        "priority": "now",
        "summary": "Require OPL current_control_state to hydrate the MAS owner handoff.",
    },
    "repeated_controller_decision": {
        "action_type": "dedupe_controller_dispatch",
        "controller_surface": "domain_health_diagnostic",
        "priority": "now",
        "summary": "Suppress repeated controller dispatches for the same blocker fingerprint.",
    },
    "publication_gate_blocked": {
        "action_type": "run_publication_work_unit",
        "controller_surface": "gate_clearing_batch",
        "priority": "now",
        "summary": "Route active publication blockers into the next bounded work unit.",
    },
    "stale_current_package": {
        "action_type": "refresh_current_package_after_settle",
        "controller_surface": "gate_clearing_batch",
        "priority": "next",
        "summary": "Refresh the human-facing current package after authority surfaces settle.",
    },
    "non_actionable_gate": {
        "action_type": "request_gate_specificity",
        "controller_surface": "publication_gate",
        "priority": "now",
        "summary": "Request concrete blocker targets before dispatching another research run.",
    },
}


def optimization_action_units_for_study(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = str(study.get("study_id") or "").strip()
    action_units: list[dict[str, Any]] = []
    bottlenecks = study.get("bottlenecks")
    if not isinstance(bottlenecks, list):
        return action_units
    for index, bottleneck in enumerate(bottlenecks, start=1):
        if not isinstance(bottleneck, Mapping):
            continue
        bottleneck_id = str(bottleneck.get("bottleneck_id") or "").strip()
        action = _ACTION_BY_BOTTLENECK.get(bottleneck_id)
        if action is None:
            continue
        action_units.append(
            {
                "action_unit_id": f"optimization-action::{study_id}::{bottleneck_id}",
                "study_id": study_id,
                "study_root": study.get("study_root"),
                "quest_id": study.get("quest_id"),
                "source_bottleneck_id": bottleneck_id,
                "source_bottleneck_severity": str(bottleneck.get("severity") or "").strip() or None,
                "schedule_rank": index,
                "apply_mode": "controller_only",
                **action,
            }
        )
    return action_units


def workspace_scheduler(action_units: list[dict[str, Any]]) -> dict[str, Any]:
    priority_weight = {"now": 0, "next": 1, "later": 2}
    ordered = sorted(
        action_units,
        key=lambda item: (
            priority_weight.get(str(item.get("priority") or ""), 9),
            int(item.get("schedule_rank") or 999),
            str(item.get("study_id") or ""),
            str(item.get("action_unit_id") or ""),
        ),
    )
    return {
        "ready_count": len(ordered),
        "ready_action_unit_ids": [str(item["action_unit_id"]) for item in ordered],
        "ready_action_units": ordered,
    }


__all__ = ["optimization_action_units_for_study", "workspace_scheduler"]
