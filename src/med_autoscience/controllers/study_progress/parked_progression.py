from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def publication_supervisor_blocks_handoff(publication_supervisor_state: Mapping[str, Any]) -> bool:
    supervisor_phase = _text(publication_supervisor_state.get("supervisor_phase"))
    current_required_action = _text(publication_supervisor_state.get("current_required_action"))
    return (
        bool(publication_supervisor_state.get("bundle_tasks_downstream_only"))
        or supervisor_phase in {"publishability_gate_blocked", "bundle_stage_blocked"}
        or current_required_action == "return_to_publishability_gate"
    )


def parked_intervention_lane(
    parked_projection: Mapping[str, Any] | None,
    *,
    current_stage_summary: str,
    next_system_action: str,
) -> dict[str, Any] | None:
    if not bool((parked_projection or {}).get("parked")):
        return None
    return {
        "lane_id": "auto_runtime_parked",
        "title": _text((parked_projection or {}).get("parked_state_label")) or "自动运行已停驻",
        "severity": "handoff",
        "summary": _text((parked_projection or {}).get("summary")) or current_stage_summary or next_system_action,
        "recommended_action_id": "inspect_progress",
        "parked_state": _text((parked_projection or {}).get("parked_state")),
        "parked_owner": _text((parked_projection or {}).get("parked_owner")),
        "resource_release_expected": bool((parked_projection or {}).get("resource_release_expected")),
        "awaiting_explicit_wakeup": bool((parked_projection or {}).get("awaiting_explicit_wakeup")),
        "auto_execution_complete": bool((parked_projection or {}).get("auto_execution_complete")),
        "reopen_policy": _text((parked_projection or {}).get("reopen_policy")),
    }


def task_intake_quality_lane(
    task_intake_progress_override: Mapping[str, Any] | None,
    *,
    current_stage_summary: str,
    next_system_action: str,
) -> dict[str, Any] | None:
    if not task_intake_progress_override:
        return None
    same_line_route_truth = _mapping(task_intake_progress_override.get("same_line_route_truth"))
    payload = {
        "lane_id": "quality_floor_blocker",
        "title": (
            "优先完成有限补充分析"
            if _text(same_line_route_truth.get("same_line_state")) == "bounded_analysis"
            else "优先收口同线质量硬阻塞"
        ),
        "severity": "critical",
        "summary": (
            _text(task_intake_progress_override.get("next_system_action"))
            or _text(task_intake_progress_override.get("blocker_summary"))
            or current_stage_summary
            or next_system_action
        ),
        "recommended_action_id": _text(task_intake_progress_override.get("current_required_action"))
        or "inspect_progress",
    }
    if same_line_route_truth:
        payload.update(
            {
                "repair_mode": _text(same_line_route_truth.get("same_line_state")),
                "route_target": _text(same_line_route_truth.get("route_target")),
                "route_target_label": _text(same_line_route_truth.get("route_target_label")),
                "route_key_question": _text(same_line_route_truth.get("current_focus")),
                "route_summary": _text(same_line_route_truth.get("summary")),
            }
        )
    return payload
