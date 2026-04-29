from __future__ import annotations


def stop_loss_route_contract(*, controller_stage_note: str) -> dict[str, str]:
    return {
        "route_target": "stop",
        "route_key_question": "当前论文线是否还有独立临床意义和强论文路径？",
        "route_rationale": (
            controller_stage_note
            or "The publication gate indicates that the current paper line should stop instead of continuing manuscript repair."
        ),
    }


def report_requests_stop_loss(report: dict[str, object]) -> bool:
    current_required_action = str(report.get("current_required_action") or "").strip()
    route_back_recommendation = str(report.get("medical_publication_surface_route_back_recommendation") or "").strip()
    return current_required_action in {"stop_runtime", "stop_loss"} or route_back_recommendation == "stop_loss"


def should_keep_action_through_non_actionable_gate(*, action_type: str) -> bool:
    return action_type == "stop_loss"


def non_actionable_gate_overrides(
    *,
    status: str,
    action_type: str,
    work_unit_payload: dict[str, object],
) -> bool:
    return (
        status != "clear"
        and not should_keep_action_through_non_actionable_gate(action_type=action_type)
        and str(work_unit_payload.get("actionability_status") or "").strip() == "blocked_by_non_actionable_gate"
    )
