from __future__ import annotations

from pathlib import Path
from typing import Any

import med_autoscience.controllers.autonomy_ai_doctor as autonomy_ai_doctor
import med_autoscience.controllers.open_auto_research_projection as open_auto_research_projection
import med_autoscience.controllers.pi_action_projection as pi_action_projection
from med_autoscience.controllers.production_blocker_impact_projection import (
    build_production_blocker_impact_projection,
)
import med_autoscience.controllers.runtime_health_kernel as runtime_health_kernel
import med_autoscience.controllers.study_truth_kernel as study_truth_kernel

from .ai_first_runtime_projection import attach_ai_first_runtime_projection
from .macro_state_projection import compact_study_macro_state_from_payload
from .parked_projection import parked_progress_fields
from .shared import SCHEMA_VERSION, _mapping_copy, _non_empty_text
from .user_visible_projection import build_user_visible_projection


def _progress_payload_identity_fields(
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


def _runtime_decision_fields(status: dict[str, Any]) -> dict[str, Any]:
    return {
        "runtime_decision": _non_empty_text(status.get("decision")),
        "runtime_reason": _non_empty_text(status.get("reason")),
    }


def _progress_supervision_fields(
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


def _last_meaningful_progress_at(autonomy_slo_status: dict[str, Any] | None) -> str | None:
    if autonomy_slo_status is None:
        return None
    return _non_empty_text(autonomy_slo_status.get("last_meaningful_progress_at"))


def _progress_stage_and_operator_fields(
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


def _progress_control_contract_fields(
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
        "continuation_state": continuation_state or None,
        "family_checkpoint_lineage": family_checkpoint_lineage or None,
        "interaction_arbitration": interaction_arbitration or None,
        "manual_finish_contract": manual_finish_contract,
        "task_intake": task_intake,
        "progress_freshness": progress_freshness,
    }


def _progress_quality_fields(
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


def _progress_publication_and_runtime_fields(
    *,
    medical_writing_quality_surfaces: dict[str, Any],
    medical_paper_readiness_surface: dict[str, Any],
    medical_paper_ops_health_surface: dict[str, Any],
    artifact_runtime_proof_surface: dict[str, Any],
    submission_hygiene_truth: dict[str, Any],
    delivery_inspection: dict[str, Any] | None,
    research_runtime_control_projection: dict[str, Any],
    open_auto_research_state: dict[str, Any],
    ai_reviewer_request_lifecycle: dict[str, Any] | None,
    portable_supervisor_dashboard: dict[str, Any] | None,
    gate_specificity_request: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "medical_writing_quality_surfaces": medical_writing_quality_surfaces,
        "medical_paper_readiness": medical_paper_readiness_surface,
        "medical_paper_ops_health": medical_paper_ops_health_surface,
        "artifact_runtime_proof": artifact_runtime_proof_surface,
        "submission_hygiene_truth": submission_hygiene_truth,
        "delivery_inspection": delivery_inspection,
        "product_recommended_flow": submission_hygiene_truth.get("recommended_flow"),
        "research_runtime_control_projection": research_runtime_control_projection,
        "open_auto_research_projection": open_auto_research_state,
        "ai_reviewer_request_lifecycle": ai_reviewer_request_lifecycle,
        "portable_supervisor_dashboard": portable_supervisor_dashboard,
        "publication_gate_specificity_request": gate_specificity_request,
    }


def _progress_ai_first_and_snapshot_fields(
    *,
    ai_first_default_entry_state: dict[str, Any],
    paper_orchestra_operator_projection: dict[str, Any],
    ai_first_observability_snapshots: dict[str, Any],
    ai_first_operations_dashboard: dict[str, Any],
    study_truth_snapshot: dict[str, Any],
    runtime_health_snapshot: dict[str, Any],
    control_plane_snapshot: dict[str, Any],
    module_surfaces: dict[str, Any],
    runtime_efficiency: dict[str, Any],
    runtime_reconcile_trigger: dict[str, Any],
    paper_progress_stall: dict[str, Any],
    outer_supervision_slo: dict[str, Any],
    autonomy_slo_status: dict[str, Any] | None,
    ai_doctor_state: dict[str, Any],
    repair_recommendation: dict[str, Any],
    ai_repair_lifecycle: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "ai_first_default_entry_state": ai_first_default_entry_state,
        "paper_orchestra_operator_projection": paper_orchestra_operator_projection or None,
        "ai_first_observability_snapshots": ai_first_observability_snapshots,
        "ai_first_operations_dashboard": ai_first_operations_dashboard,
        "study_truth_snapshot": study_truth_snapshot or None,
        "runtime_health_snapshot": runtime_health_snapshot or None,
        "control_plane_snapshot": control_plane_snapshot or None,
        "module_surfaces": module_surfaces,
        "runtime_efficiency": runtime_efficiency,
        "runtime_reconcile_trigger": runtime_reconcile_trigger,
        "paper_progress_stall": paper_progress_stall,
        "outer_supervision_slo": outer_supervision_slo,
        "autonomy_slo": autonomy_slo_status,
        "ai_doctor_state": ai_doctor_state,
        "repair_recommendation": repair_recommendation or None,
        "ai_repair_lifecycle": ai_repair_lifecycle,
        "last_meaningful_progress_at": _last_meaningful_progress_at(autonomy_slo_status),
    }


def assemble_study_progress_payload(
    *,
    generated_at: str,
    study_id: str,
    study_root: Path,
    quest_id: str | None,
    quest_root: Path | None,
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
    medical_writing_quality_surfaces: dict[str, Any],
    medical_paper_readiness_surface: dict[str, Any],
    medical_paper_ops_health_surface: dict[str, Any],
    artifact_runtime_proof_surface: dict[str, Any],
    submission_hygiene_truth: dict[str, Any],
    delivery_inspection: dict[str, Any] | None,
    research_runtime_control_projection: dict[str, Any],
    open_auto_research_state: dict[str, Any],
    ai_reviewer_request_lifecycle: dict[str, Any] | None,
    portable_supervisor_dashboard: dict[str, Any] | None,
    gate_specificity_request: dict[str, Any] | None,
    ai_first_default_entry_state: dict[str, Any],
    paper_orchestra_operator_projection: dict[str, Any],
    ai_first_observability_snapshots: dict[str, Any],
    ai_first_operations_dashboard: dict[str, Any],
    study_truth_snapshot: dict[str, Any],
    runtime_health_snapshot: dict[str, Any],
    control_plane_snapshot: dict[str, Any],
    module_surfaces: dict[str, Any],
    runtime_efficiency: dict[str, Any],
    runtime_reconcile_trigger: dict[str, Any],
    paper_progress_stall: dict[str, Any],
    outer_supervision_slo: dict[str, Any],
    autonomy_slo_status: dict[str, Any] | None,
    ai_doctor_state: dict[str, Any],
    repair_recommendation: dict[str, Any],
    ai_repair_lifecycle: dict[str, Any] | None,
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    supervision_health_status: str | None,
    refs: dict[str, Any],
) -> dict[str, Any]:
    payload = {
        **_progress_payload_identity_fields(
            generated_at=generated_at,
            study_id=study_id,
            study_root=study_root,
            quest_id=quest_id,
            quest_root=quest_root,
            study_truth_snapshot=study_truth_snapshot,
            runtime_health_snapshot=runtime_health_snapshot,
        ),
        **_progress_stage_and_operator_fields(
            current_stage=current_stage,
            current_stage_summary=current_stage_summary,
            paper_stage=paper_stage,
            paper_stage_summary=paper_stage_summary,
            status_narration_contract=status_narration_contract,
            latest_events=latest_events,
            current_blockers=current_blockers,
            next_system_action=next_system_action,
            current_active_run_id=current_active_run_id,
            auto_runtime_parked=auto_runtime_parked,
            intervention_lane=intervention_lane,
            operator_verdict=operator_verdict,
            operator_status_card=operator_status_card,
            recommended_command=recommended_command,
            recommended_commands=recommended_commands,
        ),
        **_progress_control_contract_fields(
            autonomy_contract=autonomy_contract,
            autonomy_soak_status=autonomy_soak_status,
            recovery_contract=recovery_contract,
            needs_physician_decision=needs_physician_decision,
            physician_decision_summary=physician_decision_summary,
            status=status,
            continuation_state=continuation_state,
            family_checkpoint_lineage=family_checkpoint_lineage,
            interaction_arbitration=interaction_arbitration,
            manual_finish_contract=manual_finish_contract,
            task_intake=task_intake,
            progress_freshness=progress_freshness,
        ),
        **_progress_quality_fields(
            quality_closure_truth=quality_closure_truth,
            quality_execution_lane=quality_execution_lane,
            same_line_route_truth=same_line_route_truth,
            same_line_route_surface=same_line_route_surface,
            quality_closure_basis=quality_closure_basis,
            quality_review_agenda=quality_review_agenda,
            quality_revision_plan=quality_revision_plan,
            quality_review_loop=quality_review_loop,
            quality_repair_batch_followthrough=quality_repair_batch_followthrough,
            gate_clearing_batch_followthrough=gate_clearing_batch_followthrough,
            quality_review_followthrough=quality_review_followthrough,
        ),
        **_progress_publication_and_runtime_fields(
            medical_writing_quality_surfaces=medical_writing_quality_surfaces,
            medical_paper_readiness_surface=medical_paper_readiness_surface,
            medical_paper_ops_health_surface=medical_paper_ops_health_surface,
            artifact_runtime_proof_surface=artifact_runtime_proof_surface,
            submission_hygiene_truth=submission_hygiene_truth,
            delivery_inspection=delivery_inspection,
            research_runtime_control_projection=research_runtime_control_projection,
            open_auto_research_state=open_auto_research_state,
            ai_reviewer_request_lifecycle=ai_reviewer_request_lifecycle,
            portable_supervisor_dashboard=portable_supervisor_dashboard,
            gate_specificity_request=gate_specificity_request,
        ),
        **_progress_ai_first_and_snapshot_fields(
            ai_first_default_entry_state=ai_first_default_entry_state,
            paper_orchestra_operator_projection=paper_orchestra_operator_projection,
            ai_first_observability_snapshots=ai_first_observability_snapshots,
            ai_first_operations_dashboard=ai_first_operations_dashboard,
            study_truth_snapshot=study_truth_snapshot,
            runtime_health_snapshot=runtime_health_snapshot,
            control_plane_snapshot=control_plane_snapshot,
            module_surfaces=module_surfaces,
            runtime_efficiency=runtime_efficiency,
            runtime_reconcile_trigger=runtime_reconcile_trigger,
            paper_progress_stall=paper_progress_stall,
            outer_supervision_slo=outer_supervision_slo,
            autonomy_slo_status=autonomy_slo_status,
            ai_doctor_state=ai_doctor_state,
            repair_recommendation=repair_recommendation,
            ai_repair_lifecycle=ai_repair_lifecycle,
        ),
        "supervision": _progress_supervision_fields(
            autonomous_runtime_notice=autonomous_runtime_notice,
            current_active_run_id=current_active_run_id,
            supervision_health_status=supervision_health_status,
            supervisor_tick_audit=supervisor_tick_audit,
            refs=refs,
        ),
        "refs": refs,
    }
    payload["production_blocker_impact"] = build_production_blocker_impact_projection(
        payload,
        status,
        study_id=study_id,
    )
    payload["study_macro_state"] = compact_study_macro_state_from_payload(payload)
    payload["pi_action_projection"] = pi_action_projection.build_pi_action_projection(payload)
    payload["user_visible_projection"] = build_user_visible_projection(payload)
    payload = _apply_terminal_delivery_user_visible_status(payload)
    return attach_ai_first_runtime_projection(
        payload,
        study_root=study_root,
        generated_at=generated_at,
    )


def _apply_terminal_delivery_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    if not _terminal_delivery_closed(payload):
        return payload
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    updated = dict(payload)
    updated["current_stage"] = _non_empty_text(user_visible.get("current_stage")) or "parked"
    updated["current_stage_summary"] = _non_empty_text(user_visible.get("current_stage_summary")) or (
        _non_empty_text(user_visible.get("state_summary")) or "投稿包已交付，系统已自动停驻。"
    )
    if _non_empty_text(user_visible.get("paper_stage_summary")) is not None:
        updated["paper_stage_summary"] = _non_empty_text(user_visible.get("paper_stage_summary"))
    updated["current_blockers"] = [
        str(item)
        for item in (user_visible.get("current_blockers") or [])
        if str(item or "").strip()
    ]
    updated["next_system_action"] = _non_empty_text(user_visible.get("next_system_action")) or (
        _non_empty_text(user_visible.get("next_step")) or "投稿包已交付；系统保持自动停驻。"
    )
    user_action_required = bool(user_visible.get("user_action_required"))
    updated["needs_user_decision"] = user_action_required
    updated["needs_physician_decision"] = user_action_required
    if not user_action_required:
        updated["physician_decision_summary"] = None
        updated["user_decision_summary"] = None
    updated["operator_status_card"] = _terminal_delivery_operator_status_card(
        payload=updated,
        user_visible=user_visible,
    )
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        stage = _mapping_copy(status_contract.get("stage"))
        stage["current_stage"] = updated["current_stage"]
        status_contract["stage"] = stage
        readiness = _mapping_copy(status_contract.get("readiness"))
        readiness["needs_physician_decision"] = user_action_required
        status_contract["readiness"] = readiness
        status_contract["current_blockers"] = list(updated["current_blockers"])
        status_contract["latest_update"] = updated["current_stage_summary"]
        status_contract["next_step"] = updated["next_system_action"]
        updated["status_narration_contract"] = status_contract
    return updated


def _terminal_delivery_closed(payload: Mapping[str, Any]) -> bool:
    user_visible = _mapping_copy(payload.get("user_visible_projection"))
    paper_progress = _mapping_copy(user_visible.get("paper_progress_state"))
    if user_visible.get("package_delivered") is not True:
        return False
    if _non_empty_text(paper_progress.get("state")) != "terminal_delivered":
        return False
    delivery = _mapping_copy(payload.get("delivery_inspection"))
    delivery_freshness = _mapping_copy(delivery.get("freshness"))
    if _non_empty_text(delivery.get("status")) != "current" and _non_empty_text(
        delivery_freshness.get("delivery_status")
    ) != "current":
        return False
    followthrough = _mapping_copy(payload.get("gate_clearing_batch_followthrough"))
    return (
        _non_empty_text(followthrough.get("gate_replay_status")) == "clear"
        and int(followthrough.get("failed_unit_count") or 0) == 0
    )


def _terminal_delivery_operator_status_card(
    *,
    payload: Mapping[str, Any],
    user_visible: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _mapping_copy(payload.get("operator_status_card"))
    user_action_required = bool(user_visible.get("user_action_required"))
    handling_state = "external_metadata_pending" if user_action_required else "package_ready_handoff"
    label = "外部投稿元数据待补" if user_action_required else "投稿包/人审包交付停驻"
    focus = _non_empty_text(user_visible.get("next_step")) or _non_empty_text(user_visible.get("state_summary"))
    if focus is None:
        focus = "投稿包已与 controller-authorized source 对齐；系统保持自动停驻。"
    next_signal = (
        "看外部作者、单位、伦理、基金和声明等投稿元数据是否补齐。"
        if user_action_required
        else "看是否出现新的审阅反馈、外部条件解除或显式 resume/rerun/relaunch。"
    )
    return {
        **existing,
        "surface_kind": "study_operator_status_card",
        "study_id": _non_empty_text(payload.get("study_id")),
        "handling_state": handling_state,
        "handling_state_label": label,
        "owner_summary": "MAS 已完成 controller-authorized 投稿包交付闭环；自动运行资源已释放。",
        "current_focus": focus,
        "human_surface_freshness": "current",
        "human_surface_summary": "给人看的投稿包镜像已与 controller-authorized source 对齐；当前没有 stale/QC 刷新告警。",
        "next_confirmation_signal": next_signal,
        "user_visible_verdict": _non_empty_text(user_visible.get("state_label")) or "投稿包已交付，自动停驻",
    }


def build_projection_refs(
    *,
    launch_report_path: Path,
    publication_eval_path: Path,
    controller_decision_path: Path,
    controller_confirmation_summary_path: Path,
    controller_confirmation_summary: dict[str, Any] | None,
    controller_module_surface: dict[str, Any] | None,
    runtime_supervision_path: Path,
    runtime_supervision_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    runtime_watch_path: Path | None,
    runtime_module_surface: dict[str, Any],
    runtime_efficiency_refs: dict[str, Any],
    study_root: Path,
    autonomy_slo_status: dict[str, Any] | None,
    ai_repair_lifecycle: dict[str, Any] | None,
    evaluation_module_surface: dict[str, Any] | None,
    medical_writing_quality_surfaces: dict[str, Any],
    gate_specificity_request_path: Path | None,
    gate_specificity_request: dict[str, Any] | None,
    artifact_runtime_proof_surface: dict[str, Any],
    submission_hygiene_truth: dict[str, Any],
    bash_summary_path: Path | None,
    details_projection_path: Path | None,
    ai_first_observability_snapshots: dict[str, Any],
    portable_supervisor_dashboard: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "launch_report_path": str(launch_report_path),
        "publication_eval_path": str(publication_eval_path),
        "controller_decision_path": str(controller_decision_path),
        "controller_confirmation_summary_path": (
            str(controller_confirmation_summary_path) if controller_confirmation_summary is not None else None
        ),
        "controller_summary_path": (
            controller_module_surface["summary_ref"] if controller_module_surface is not None else None
        ),
        "runtime_supervision_path": str(runtime_supervision_path) if runtime_supervision_payload is not None else None,
        "runtime_escalation_path": str(runtime_escalation_path) if runtime_escalation_path is not None else None,
        "runtime_watch_report_path": str(runtime_watch_path) if runtime_watch_path is not None else None,
        "runtime_status_summary_path": runtime_module_surface["summary_ref"],
        **runtime_efficiency_refs,
        "autonomy_slo_status_path": (
            str(autonomy_ai_doctor.stable_slo_status_path(study_root=study_root))
            if autonomy_slo_status is not None
            else None
        ),
        "ai_repair_lifecycle_path": (
            str(study_root / "artifacts" / "autonomy" / "repair_lifecycle" / "latest.json")
            if ai_repair_lifecycle is not None
            else None
        ),
        "evaluation_summary_path": (
            evaluation_module_surface["summary_ref"] if evaluation_module_surface is not None else None
        ),
        "medical_manuscript_blueprint_path": medical_writing_quality_surfaces["blueprint"]["path"],
        "medical_journal_style_corpus_path": medical_writing_quality_surfaces["style_corpus"]["path"],
        "medical_prose_review_request_path": medical_writing_quality_surfaces["prose_review_request"]["path"],
        "medical_prose_review_path": medical_writing_quality_surfaces["prose_review"]["path"],
        "retrospective_medical_prose_audit_request_path": (
            medical_writing_quality_surfaces["retrospective_audit_request"]["path"]
        ),
        "retrospective_medical_prose_audit_path": medical_writing_quality_surfaces["retrospective_audit"]["path"],
        "medical_paper_readiness_path": str(
            medical_paper_readiness_path(study_root=study_root)
        ),
        "open_auto_research_projection_path": str(
            open_auto_research_projection.stable_open_auto_research_projection_path(study_root=study_root)
        ),
        "portable_supervisor_hourly_path": (
            portable_supervisor_dashboard.get("source_path") if portable_supervisor_dashboard is not None else None
        ),
        "publication_gate_specificity_request_path": (
            str(gate_specificity_request_path) if gate_specificity_request is not None else None
        ),
        "artifact_runtime_proof_delivery_manifest_path": (
            (artifact_runtime_proof_surface.get("refs") or {}).get("delivery_manifest_path")
        ),
        "submission_hygiene_submission_manifest_path": (
            (submission_hygiene_truth.get("refs") or {}).get("submission_manifest_path")
        ),
        "study_truth_snapshot_path": str(study_truth_kernel.truth_snapshot_path(study_root=study_root)),
        "runtime_health_snapshot_path": str(
            runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root)
        ),
        "promotion_gate_path": (
            evaluation_module_surface["promotion_gate_ref"] if evaluation_module_surface is not None else None
        ),
        "bash_summary_path": str(bash_summary_path) if bash_summary_path is not None else None,
        "details_projection_path": str(details_projection_path) if details_projection_path is not None else None,
        "ai_first_observability_publication_eval_path": ai_first_observability_snapshots["refs"][
            "publication_eval_path"
        ],
        "ai_first_observability_runtime_health_path": ai_first_observability_snapshots["refs"][
            "runtime_health_path"
        ],
        "ai_first_observability_delivery_manifest_path": ai_first_observability_snapshots["refs"][
            "delivery_manifest_path"
        ],
    }


def medical_paper_readiness_path(*, study_root: Path) -> Path:
    from med_autoscience.controllers import medical_paper_readiness

    return medical_paper_readiness.stable_medical_paper_readiness_path(study_root=study_root)
