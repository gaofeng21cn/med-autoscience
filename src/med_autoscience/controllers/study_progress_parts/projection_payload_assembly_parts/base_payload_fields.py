from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_progress_parts.parked_projection import parked_progress_fields
from med_autoscience.controllers.study_progress_parts.shared import (
    SCHEMA_VERSION,
    _mapping_copy,
    _non_empty_text,
)


def progress_payload_identity_fields(
    *,
    generated_at: str,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    quest_root: Path | None,
    study_truth_snapshot: dict[str, Any],
    runtime_health_snapshot: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "generated_at": generated_at,
        "truth_epoch": _non_empty_text(study_truth_snapshot.get("truth_epoch")),
        "runtime_health_epoch": _non_empty_text(runtime_health_snapshot.get("runtime_health_epoch")),
        "study_id": study_id,
        "study_root": str(study_root),
        "quest_id": quest_id,
        "quest_root": str(quest_root) if quest_root is not None else None,
    }


def progress_supervision_fields(
    *,
    autonomous_runtime_notice: dict[str, Any],
    current_active_run_id: str | None,
    supervision_health_status: str | None,
    supervisor_tick_audit: dict[str, Any],
    refs: dict[str, Any],
) -> dict[str, Any]:
    return {
        "browser_url": _non_empty_text(autonomous_runtime_notice.get("browser_url")),
        "quest_session_api_url": _non_empty_text(autonomous_runtime_notice.get("quest_session_api_url")),
        "active_run_id": current_active_run_id,
        "health_status": supervision_health_status,
        "supervisor_tick_status": _non_empty_text(supervisor_tick_audit.get("status")),
        "supervisor_tick_required": bool(supervisor_tick_audit.get("required")),
        "supervisor_tick_summary": _non_empty_text(supervisor_tick_audit.get("summary")),
        "supervisor_tick_latest_recorded_at": _non_empty_text(supervisor_tick_audit.get("latest_recorded_at")),
        "launch_report_path": refs["launch_report_path"],
    }


def progress_stage_and_operator_fields(
    *,
    current_stage: str,
    current_stage_summary: str,
    paper_stage: str | None,
    paper_stage_summary: str,
    status_narration_contract: dict[str, Any],
    latest_events: list[dict[str, Any]],
    current_blockers: list[str],
    next_system_action: str,
    current_active_run_id: str | None,
    auto_runtime_parked: dict[str, Any],
    intervention_lane: dict[str, Any],
    operator_verdict: dict[str, Any],
    operator_status_card: dict[str, Any],
    recommended_command: str | None,
    recommended_commands: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "current_stage": current_stage,
        "current_stage_summary": current_stage_summary,
        "paper_stage": paper_stage,
        "paper_stage_summary": paper_stage_summary,
        "status_narration_contract": status_narration_contract,
        "latest_events": latest_events,
        "current_blockers": current_blockers,
        "next_system_action": next_system_action,
        "active_run_id": current_active_run_id,
        **parked_progress_fields(auto_runtime_parked),
        "intervention_lane": intervention_lane,
        "operator_verdict": operator_verdict,
        "operator_status_card": operator_status_card,
        "recommended_command": recommended_command,
        "recommended_commands": recommended_commands,
    }


def progress_control_contract_fields(
    *,
    autonomy_contract: dict[str, Any],
    autonomy_soak_status: dict[str, Any],
    recovery_contract: dict[str, Any],
    needs_physician_decision: bool,
    physician_decision_summary: str | None,
    status: dict[str, Any],
    continuation_state: dict[str, Any],
    family_checkpoint_lineage: dict[str, Any],
    interaction_arbitration: dict[str, Any],
    manual_finish_contract: dict[str, Any] | None,
    task_intake: dict[str, Any],
    progress_freshness: dict[str, Any],
) -> dict[str, Any]:
    return {
        "autonomy_contract": autonomy_contract,
        "autonomy_soak_status": autonomy_soak_status,
        "recovery_contract": recovery_contract,
        "needs_physician_decision": needs_physician_decision,
        "needs_user_decision": needs_physician_decision,
        "physician_decision_summary": physician_decision_summary,
        "user_decision_summary": physician_decision_summary,
        **_runtime_decision_fields(status),
        "domain_transition": _mapping_copy(status.get("domain_transition")) or None,
        "runtime_closeout_invalidation": _mapping_copy(status.get("runtime_closeout_invalidation")) or None,
        "continuation_state": continuation_state or None,
        "family_checkpoint_lineage": family_checkpoint_lineage or None,
        "interaction_arbitration": interaction_arbitration or None,
        "manual_finish_contract": manual_finish_contract,
        "task_intake": task_intake,
        "progress_freshness": progress_freshness,
    }


def progress_quality_fields(
    *,
    quality_closure_truth: dict[str, Any],
    quality_execution_lane: dict[str, Any],
    same_line_route_truth: dict[str, Any],
    same_line_route_surface: dict[str, Any],
    quality_closure_basis: dict[str, Any],
    quality_review_agenda: dict[str, Any],
    quality_revision_plan: dict[str, Any],
    quality_review_loop: dict[str, Any],
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
    quality_review_followthrough: dict[str, Any],
) -> dict[str, Any]:
    return {
        "quality_closure_truth": quality_closure_truth or None,
        "quality_execution_lane": quality_execution_lane or None,
        "same_line_route_truth": same_line_route_truth or None,
        "same_line_route_surface": same_line_route_surface or None,
        "quality_closure_basis": quality_closure_basis or None,
        "quality_review_agenda": quality_review_agenda or None,
        "quality_revision_plan": quality_revision_plan or None,
        "quality_review_loop": quality_review_loop or None,
        "quality_repair_batch_followthrough": quality_repair_batch_followthrough or None,
        "gate_clearing_batch_followthrough": gate_clearing_batch_followthrough or None,
        "quality_review_followthrough": quality_review_followthrough or None,
    }


def _runtime_decision_fields(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_decision": _non_empty_text(status.get("decision")),
        "runtime_reason": _non_empty_text(status.get("reason")),
    }
