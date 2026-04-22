from __future__ import annotations

from typing import Any

QUALITY_EXECUTION_LANE_LABELS = {
    "reviewer_first": "reviewer-first 收口",
    "claim_evidence": "claim-evidence 修复",
    "submission_hardening": "submission hardening 收口",
    "write_ready": "同线写作推进",
    "general_quality_repair": "质量修复",
}


def _required_text(label: str, field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def derive_quality_closure_truth(
    *,
    promotion_gate_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
    quality_closure_basis: dict[str, Any],
) -> dict[str, Any]:
    current_required_action = _required_text(
        "promotion gate",
        "current_required_action",
        promotion_gate_payload.get("current_required_action"),
    )
    evidence_strength_status = str((quality_closure_basis.get("evidence_strength") or {}).get("status") or "").strip()
    if current_required_action in {"continue_bundle_stage", "complete_bundle_stage"} and evidence_strength_status == "ready":
        return {
            "state": "bundle_only_remaining",
            "summary": "核心科学质量已经闭环；剩余工作收口在 finalize / submission bundle，同一论文线可以继续自动推进。",
            "current_required_action": current_required_action,
            "route_target": "finalize",
        }
    if current_required_action == "continue_write_stage" and evidence_strength_status == "ready":
        return {
            "state": "write_line_ready",
            "summary": "核心科学质量已经够稳；当前可以继续同一论文线的写作与有限补充收口。",
            "current_required_action": current_required_action,
            "route_target": "write",
        }
    route_target = str((route_repair_plan or {}).get("route_target") or "").strip()
    if route_target:
        summary = f"核心科学质量还没有闭环；当前应先回到 {route_target} 完成最窄补充修复。"
    else:
        summary = "核心科学质量还没有闭环；当前仍需先补齐论文质量缺口。"
    return {
        "state": "quality_repair_required",
        "summary": summary,
        "current_required_action": current_required_action,
        "route_target": route_target or None,
    }


def derive_quality_execution_lane(
    *,
    promotion_gate_payload: dict[str, Any],
    route_repair_plan: dict[str, str] | None,
) -> dict[str, Any]:
    current_required_action = _required_text(
        "promotion gate",
        "current_required_action",
        promotion_gate_payload.get("current_required_action"),
    )
    named_blockers = [
        str(item).strip()
        for item in (promotion_gate_payload.get("medical_publication_surface_named_blockers") or [])
        if str(item).strip()
    ]
    route_target = str((route_repair_plan or {}).get("route_target") or "").strip()
    route_key_question = str((route_repair_plan or {}).get("route_key_question") or "").strip()
    route_rationale = str((route_repair_plan or {}).get("route_rationale") or "").strip()
    repair_mode = (
        "bounded_analysis"
        if str((route_repair_plan or {}).get("action_type") or "").strip() == "bounded_analysis"
        else "same_line_route_back"
        if route_repair_plan is not None
        else None
    )

    if "reviewer_first_concerns_unresolved" in named_blockers:
        lane_id = "reviewer_first"
    elif "claim_evidence_consistency_failed" in named_blockers:
        lane_id = "claim_evidence"
    elif "submission_hardening_incomplete" in named_blockers or current_required_action in {
        "continue_bundle_stage",
        "complete_bundle_stage",
    }:
        lane_id = "submission_hardening"
    elif current_required_action == "continue_write_stage":
        lane_id = "write_ready"
    else:
        lane_id = "general_quality_repair"

    if lane_id == "submission_hardening":
        route_target = "finalize"
        route_key_question = "当前论文线还差哪一步 finalize / submission bundle 收口？"
        repair_mode = "same_line_route_back"
        if str((route_repair_plan or {}).get("route_target") or "").strip() != "finalize":
            route_rationale = _required_text(
                "promotion gate",
                "controller_stage_note",
                promotion_gate_payload.get("controller_stage_note"),
            )

    lane_label = QUALITY_EXECUTION_LANE_LABELS[lane_id]
    if route_target and route_key_question:
        verb = "进入" if repair_mode == "bounded_analysis" else "回到"
        summary = f"当前质量执行线聚焦 {lane_label}；先{verb} {route_target}，回答“{route_key_question}”。"
    elif route_target:
        verb = "进入" if repair_mode == "bounded_analysis" else "回到"
        summary = f"当前质量执行线聚焦 {lane_label}；先{verb} {route_target} 收口当前缺口。"
    elif current_required_action == "continue_write_stage":
        summary = "当前质量执行线已经进入同线写作推进；核心科学面允许继续往写作收口。"
    else:
        summary = f"当前质量执行线聚焦 {lane_label}；应先收口当前质量缺口。"

    why_now = route_rationale or _required_text(
        "promotion gate",
        "controller_stage_note",
        promotion_gate_payload.get("controller_stage_note"),
    )
    return {
        "lane_id": lane_id,
        "lane_label": lane_label,
        "repair_mode": repair_mode,
        "route_target": route_target or None,
        "route_key_question": route_key_question or None,
        "summary": summary,
        "why_now": why_now,
    }
