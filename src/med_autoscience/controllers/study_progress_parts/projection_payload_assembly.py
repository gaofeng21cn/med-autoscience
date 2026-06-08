from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

import med_autoscience.controllers.autonomy_ai_doctor as autonomy_ai_doctor
import med_autoscience.controllers.open_auto_research_projection as open_auto_research_projection
import med_autoscience.controllers.pi_action_projection as pi_action_projection
from med_autoscience.controllers.production_blocker_impact_projection import (
    build_production_blocker_impact_projection,
)
import med_autoscience.controllers.runtime_health_kernel as runtime_health_kernel
import med_autoscience.controllers.study_truth_kernel as study_truth_kernel
from med_autoscience.controllers import current_execution_envelope

from .ai_first_runtime_projection import attach_ai_first_runtime_projection
from .current_owner_handoff_projection import (
    apply_current_owner_handoff_user_visible_status,
    current_owner_redrive_domain_transition,
)
from .current_executable_owner_action import build_current_executable_owner_action
from .current_owner_action_projection_reconcile import (
    current_execution_envelope_actions,
    reconcile_current_owner_action_projection,
)
from .macro_state_projection import compact_study_macro_state_from_payload
from .parked_projection import parked_progress_fields
from .progress_first_projection import build_progress_first_projection
from .progress_first_monitoring import build_progress_first_monitoring_summary
from .research_pack_progress_projection import build_research_pack_progress_summary_projection
from .shared import SCHEMA_VERSION, _mapping_copy, _non_empty_text
from .stage_kernel_projection import stage_kernel_projection_from_artifact_index
from .user_visible_projection import build_user_visible_projection


def _progress_delta_metrics(
    *,
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_efficiency: dict[str, Any],
) -> dict[str, Any]:
    quality_followthrough = (
        quality_repair_batch_followthrough
        if isinstance(quality_repair_batch_followthrough, dict)
        else {}
    )
    gate_followthrough = (
        gate_clearing_batch_followthrough
        if isinstance(gate_clearing_batch_followthrough, dict)
        else {}
    )
    efficiency = runtime_efficiency if isinstance(runtime_efficiency, dict) else {}
    token_usage = _mapping_copy(efficiency.get("token_usage"))
    total_tokens = _token_usage_total(token_usage)
    paper_triggered = _paper_progress_triggered(
        quality_repair_batch_followthrough=quality_followthrough,
        gate_clearing_batch_followthrough=gate_followthrough,
    )
    terminal_paper_triggered = _terminal_stage_paper_progress_triggered(
        opl_current_control_state_handoff=opl_current_control_state_handoff,
    )
    paper_triggered = paper_triggered or terminal_paper_triggered
    platform_triggered = _platform_repair_triggered(opl_current_control_state_handoff=opl_current_control_state_handoff)
    paper_tokens = total_tokens if paper_triggered and not platform_triggered else 0
    platform_tokens = total_tokens if platform_triggered else 0
    deliverable_delta = {
        "count": 1 if paper_triggered else 0,
        "token_usage_total": paper_tokens,
        "sources": _paper_progress_sources(
            quality_repair_batch_followthrough=quality_followthrough,
            gate_clearing_batch_followthrough=gate_followthrough,
            terminal_paper_triggered=terminal_paper_triggered,
        ),
    }
    platform_delta = {
        "count": 1 if platform_triggered else 0,
        "token_usage_total": platform_tokens,
        "sources": _platform_repair_sources(opl_current_control_state_handoff=opl_current_control_state_handoff),
    }
    return {
        "deliverable_progress_delta": deliverable_delta,
        "paper_progress_delta": deliverable_delta,
        "platform_repair_delta": platform_delta,
        "progress_delta_classification": _progress_delta_classification(
            deliverable_triggered=paper_triggered,
            platform_triggered=platform_triggered,
        ),
    }


def _paper_progress_triggered(
    *,
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
) -> bool:
    quality_status = _non_empty_text(quality_repair_batch_followthrough.get("status"))
    gate_status = _non_empty_text(gate_clearing_batch_followthrough.get("status"))
    if quality_status in {"executed", "handoff_ready", "pending"}:
        return True
    if gate_status in {"executed", "pending"}:
        return True
    if _non_empty_text(quality_repair_batch_followthrough.get("gate_replay_status")) is not None:
        return True
    return _non_empty_text(gate_clearing_batch_followthrough.get("gate_replay_status")) is not None


def _platform_repair_triggered(*, opl_current_control_state_handoff: dict[str, Any] | None) -> bool:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    if not handoff:
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    next_owner = _non_empty_text(handoff.get("next_owner"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    if blocked_reason in {
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
        "opl_stage_attempt_admission_required",
    }:
        return True
    if health_status in {"recover_runtime", "escalated", "degraded"}:
        return True
    reason_blob = " ".join(
        text
        for text in (blocked_reason, next_owner, health_status)
        if text is not None
    ).lower()
    if any(
        token in reason_blob
        for token in (
            "currentness",
            "controller",
            "read_model",
            "provider",
            "runtime_recovery",
            "opl_stage_attempt_admission_required",
        )
    ):
        return True
    return False


def _paper_progress_sources(
    *,
    quality_repair_batch_followthrough: dict[str, Any],
    gate_clearing_batch_followthrough: dict[str, Any],
    terminal_paper_triggered: bool = False,
) -> list[str]:
    result: list[str] = []
    if _non_empty_text(quality_repair_batch_followthrough.get("status")) is not None:
        result.append("quality_repair_batch_followthrough")
    if _non_empty_text(gate_clearing_batch_followthrough.get("status")) is not None:
        result.append("gate_clearing_batch_followthrough")
    if _non_empty_text(quality_repair_batch_followthrough.get("gate_replay_status")) is not None:
        result.append("quality_repair_gate_replay")
    if _non_empty_text(gate_clearing_batch_followthrough.get("gate_replay_status")) is not None:
        result.append("gate_clearing_gate_replay")
    if terminal_paper_triggered:
        result.append("opl_current_control_state.latest_terminal_stage_log.paper_stage_log")
    return result


def _terminal_stage_paper_progress_triggered(
    *,
    opl_current_control_state_handoff: dict[str, Any] | None,
) -> bool:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    terminal = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    if not terminal or not paper_stage_log:
        return False
    if _non_empty_text(terminal.get("typed_blocker_reason")) is not None:
        return False
    if _non_empty_text(terminal.get("status")) == "typed_blocker":
        return False
    if _non_empty_text(paper_stage_log.get("outcome")) == "typed_blocker":
        return False
    classification = _non_empty_text(paper_stage_log.get("progress_delta_classification"))
    if classification is not None and classification not in {"deliverable_progress", "mixed"}:
        return False
    blocking_missing_fields = [
        field
        for field in _text_list(terminal.get("missing_user_stage_log_fields"))
        if field != "progress_delta_classification"
    ]
    if blocking_missing_fields:
        return False
    if not _text_list(paper_stage_log.get("changed_paper_surfaces")):
        return False
    return _terminal_stage_paper_delta_backed(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
    )


def _terminal_stage_paper_delta_backed(
    *,
    terminal: dict[str, Any],
    paper_stage_log: dict[str, Any],
) -> bool:
    if _text_list(terminal.get("closeout_refs")):
        return True
    for field in (
        "accepted_artifact_refs",
        "owner_receipt_refs",
        "product_delta_refs",
        "semantic_delta_refs",
        "stage_owner_answer_refs",
        "reviewer_gate_delta_refs",
    ):
        if _text_list(paper_stage_log.get(field)):
            return True
    return False


def _platform_repair_sources(*, opl_current_control_state_handoff: dict[str, Any] | None) -> list[str]:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    result: list[str] = []
    if _non_empty_text(handoff.get("blocked_reason")) is not None:
        result.append("opl_current_control_state.blocked_reason")
    if _mapping_copy(handoff.get("stage_progress_log")):
        result.append("opl_current_control_state.stage_progress_log")
    if _mapping_copy(handoff.get("runtime_health")):
        result.append("opl_current_control_state.runtime_health")
    return result


def _progress_delta_classification(
    *,
    deliverable_triggered: bool,
    platform_triggered: bool,
) -> str:
    if deliverable_triggered and platform_triggered:
        return "mixed"
    if deliverable_triggered:
        return "deliverable_progress"
    if platform_triggered:
        return "platform_repair"
    return "typed_blocker"


def _token_usage_total(token_usage: dict[str, Any]) -> int:
    total = _number(
        token_usage.get("total_tokens")
        if token_usage
        else None
    )
    if total is not None:
        return total
    partial = _sum_numbers(
        token_usage.get("input_tokens") if token_usage else None,
        token_usage.get("cached_input_tokens") if token_usage else None,
        token_usage.get("output_tokens") if token_usage else None,
        token_usage.get("reasoning_tokens") if token_usage else None,
    )
    return partial or 0


def _number(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None
    return None


def _sum_numbers(*values: object) -> int | None:
    present = [_number(value) for value in values]
    numbers = [value for value in present if value is not None]
    if not numbers:
        return None
    return sum(numbers)


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


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
        "domain_transition": _mapping_copy(status.get("domain_transition")) or None,
        "runtime_closeout_invalidation": _mapping_copy(status.get("runtime_closeout_invalidation")) or None,
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
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_medical_publication_surface: dict[str, Any] | None,
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
        "opl_current_control_state_handoff": opl_current_control_state_handoff,
        "runtime_medical_publication_surface": runtime_medical_publication_surface,
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
    authority_snapshot: dict[str, Any],
    module_surfaces: dict[str, Any],
    runtime_efficiency: dict[str, Any],
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
        "authority_snapshot": authority_snapshot or None,
        "module_surfaces": module_surfaces,
        "runtime_efficiency": runtime_efficiency,
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
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_medical_publication_surface: dict[str, Any] | None,
    gate_specificity_request: dict[str, Any] | None,
    ai_first_default_entry_state: dict[str, Any],
    paper_orchestra_operator_projection: dict[str, Any],
    ai_first_observability_snapshots: dict[str, Any],
    ai_first_operations_dashboard: dict[str, Any],
    study_truth_snapshot: dict[str, Any],
    runtime_health_snapshot: dict[str, Any],
    authority_snapshot: dict[str, Any],
    module_surfaces: dict[str, Any],
    runtime_efficiency: dict[str, Any],
    paper_progress_stall: dict[str, Any],
    outer_supervision_slo: dict[str, Any],
    autonomy_slo_status: dict[str, Any] | None,
    ai_doctor_state: dict[str, Any],
    repair_recommendation: dict[str, Any],
    ai_repair_lifecycle: dict[str, Any] | None,
    stage_artifact_index: dict[str, Any] | None,
    autonomous_runtime_notice: dict[str, Any],
    execution_owner_guard: dict[str, Any],
    supervisor_tick_audit: dict[str, Any],
    runtime_facts: Any,
    supervision_health_status: str | None,
    refs: dict[str, Any],
) -> dict[str, Any]:
    handoff = _mapping_copy(opl_current_control_state_handoff)
    current_active_run_id = _active_run_id_with_live_handoff(
        current_active_run_id,
        handoff=handoff,
    )
    progress_delta = _progress_delta_metrics(
        quality_repair_batch_followthrough=quality_repair_batch_followthrough,
        gate_clearing_batch_followthrough=gate_clearing_batch_followthrough,
        opl_current_control_state_handoff=opl_current_control_state_handoff,
        runtime_efficiency=runtime_efficiency,
    )
    research_pack_progress_summary = build_research_pack_progress_summary_projection(
        opl_current_control_state_handoff=opl_current_control_state_handoff,
    )
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
            opl_current_control_state_handoff=opl_current_control_state_handoff,
            runtime_medical_publication_surface=runtime_medical_publication_surface,
            gate_specificity_request=gate_specificity_request,
        ),
        **_progress_ai_first_and_snapshot_fields(
            ai_first_default_entry_state=ai_first_default_entry_state,
            paper_orchestra_operator_projection=paper_orchestra_operator_projection,
            ai_first_observability_snapshots=ai_first_observability_snapshots,
            ai_first_operations_dashboard=ai_first_operations_dashboard,
            study_truth_snapshot=study_truth_snapshot,
            runtime_health_snapshot=runtime_health_snapshot,
            authority_snapshot=authority_snapshot,
            module_surfaces=module_surfaces,
            runtime_efficiency=runtime_efficiency,
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
        "opl_runtime_refs": _runtime_refs_with_live_handoff(
            runtime_facts.to_runtime_refs_dict(),
            handoff=handoff,
        ),
        "deliverable_progress_delta": progress_delta["deliverable_progress_delta"],
        "paper_progress_delta": progress_delta["paper_progress_delta"],
        "platform_repair_delta": progress_delta["platform_repair_delta"],
        "progress_delta_classification": progress_delta["progress_delta_classification"],
        "research_pack_progress_summary": research_pack_progress_summary,
        "refs": refs,
    }
    if stage_artifact_index is not None:
        payload["stage_artifact_index"] = dict(stage_artifact_index)
        payload["stage_kernel_projection"] = stage_kernel_projection_from_artifact_index(
            stage_artifact_index
        )
    payload.update(build_progress_first_projection(payload))
    payload["production_blocker_impact"] = build_production_blocker_impact_projection(
        payload,
        status,
        study_id=study_id,
    )
    payload["current_executable_owner_action"] = build_current_executable_owner_action(payload)
    payload = reconcile_current_owner_action_projection(payload)
    payload["pi_action_projection"] = pi_action_projection.build_pi_action_projection(payload)
    payload["user_visible_projection"] = build_user_visible_projection(payload)
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    envelope_actions = current_execution_envelope_actions(
        handoff=handoff,
        current_executable_owner_action=_mapping_copy(payload.get("current_executable_owner_action")),
        paper_progress_delta_counted=_mapping_copy(payload.get("progress_first_sprint_state")).get(
            "paper_progress_delta_counted"
        )
        is True,
    )
    payload["current_execution_envelope"] = current_execution_envelope.build_current_execution_envelope(
        status=status,
        progress=payload,
        actions=envelope_actions,
        blocked_reason=_non_empty_text(handoff.get("blocked_reason")),
        next_owner=_non_empty_text(handoff.get("next_owner")),
        runtime_health=runtime_health_snapshot,
        live_provider_attempt=handoff,
    )
    payload["current_executable_owner_action"] = _current_action_aligned_with_execution_envelope(
        action=_mapping_copy(payload.get("current_executable_owner_action")),
        envelope=_mapping_copy(payload.get("current_execution_envelope")),
    )
    payload["current_execution_evidence"] = current_execution_envelope.build_current_execution_evidence(
        action_queue=envelope_actions,
        runtime_health=runtime_health_snapshot,
        extra={
            "opl_current_control_state_handoff": handoff or None,
        },
    )
    payload = apply_current_owner_handoff_user_visible_status(payload)
    payload = _apply_runtime_medical_publication_surface_user_visible_status(payload)
    payload = _apply_terminal_delivery_user_visible_status(payload)
    payload["progress_first_monitoring_summary"] = build_progress_first_monitoring_summary(
        {**payload, "execution_owner_guard": execution_owner_guard}
    )
    return attach_ai_first_runtime_projection(
        payload,
        study_root=study_root,
        generated_at=generated_at,
    )


def _current_action_aligned_with_execution_envelope(
    *,
    action: Mapping[str, Any],
    envelope: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not action:
        return None
    if _non_empty_text(action.get("surface_kind")) != "current_executable_owner_action":
        return None
    if _non_empty_text(envelope.get("state_kind")) != "executable_owner_action":
        return None
    envelope_work_unit = _work_unit_identity(envelope.get("next_work_unit"))
    action_work_units = {
        item
        for item in (
            _non_empty_text(action.get("work_unit_id")),
            _non_empty_text(action.get("action_type")),
            *_text_list(action.get("allowed_actions")),
        )
        if item is not None
    }
    if envelope_work_unit is not None and action_work_units and envelope_work_unit not in action_work_units:
        return None
    return dict(action)


def _work_unit_identity(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _non_empty_text(value.get("unit_id")) or _non_empty_text(value.get("work_unit_id"))
    return _non_empty_text(value)


def _active_run_id_with_live_handoff(
    active_run_id: str | None,
    *,
    handoff: Mapping[str, Any],
) -> str | None:
    if handoff.get("running_provider_attempt") is not True:
        return active_run_id
    return _non_empty_text(handoff.get("active_run_id")) or active_run_id


def _runtime_refs_with_live_handoff(
    refs: Mapping[str, Any],
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(refs)
    active_run_id = _active_run_id_with_live_handoff(
        _non_empty_text(result.get("active_run_id")),
        handoff=handoff,
    )
    if active_run_id is None:
        return result
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    result.update(
        {
            "active_run_id": active_run_id,
            "active_run_id_source": "opl_current_control_state_handoff.active_run_id",
            "runtime_liveness_status": _non_empty_text(runtime_health.get("runtime_liveness_status"))
            or _non_empty_text(runtime_health.get("health_status"))
            or "live",
            "worker_running": True,
            "strict_live": True,
            "missing_live_session": False,
            "recovery_pending": False,
        }
    )
    return result


def _apply_runtime_medical_publication_surface_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    blockers = _current_runtime_medical_publication_surface_blockers(payload)
    if not blockers:
        return payload
    updated = dict(payload)
    updated["current_blockers"] = _merge_blockers(updated.get("current_blockers"), blockers)
    user_visible = _mapping_copy(updated.get("user_visible_projection"))
    if user_visible:
        user_visible["current_blockers"] = _merge_blockers(user_visible.get("current_blockers"), blockers)
        user_visible["state_summary"] = _non_empty_text(user_visible.get("state_summary")) or blockers[0]
        user_visible["current_stage_summary"] = (
            _non_empty_text(user_visible.get("current_stage_summary")) or user_visible["state_summary"]
        )
        updated["user_visible_projection"] = user_visible
    status_contract = _mapping_copy(updated.get("status_narration_contract"))
    if status_contract:
        status_contract["current_blockers"] = _merge_blockers(status_contract.get("current_blockers"), blockers)[:8]
        updated["status_narration_contract"] = status_contract
    return updated


def _current_runtime_medical_publication_surface_blockers(payload: Mapping[str, Any]) -> list[str]:
    surface = _mapping_copy(payload.get("runtime_medical_publication_surface"))
    if _non_empty_text(surface.get("status")) != "blocked":
        return []
    return [
        text
        for item in surface.get("blocker_summaries") or surface.get("blockers") or []
        if (text := _non_empty_text(item)) is not None
    ]


def _merge_blockers(existing: object, blockers: list[str]) -> list[str]:
    merged: list[str] = []
    for item in [*(existing or []), *blockers]:
        text = _non_empty_text(item)
        if text is not None and text not in merged:
            merged.append(text)
    return merged


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
    if current_owner_redrive_domain_transition(payload):
        return False
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
    opl_runtime_owner_handoff_path: Path,
    opl_runtime_owner_handoff_payload: dict[str, Any] | None,
    runtime_escalation_path: Path | None,
    domain_health_diagnostic_path: Path | None,
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
    opl_current_control_state_handoff: dict[str, Any] | None,
    runtime_medical_publication_surface: dict[str, Any] | None,
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
        "opl_runtime_owner_handoff_path": str(opl_runtime_owner_handoff_path) if opl_runtime_owner_handoff_payload is not None else None,
        "runtime_escalation_path": str(runtime_escalation_path) if runtime_escalation_path is not None else None,
        "domain_health_diagnostic_report_path": str(domain_health_diagnostic_path) if domain_health_diagnostic_path is not None else None,
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
        "opl_current_control_state_handoff_path": (
            opl_current_control_state_handoff.get("source_path") if opl_current_control_state_handoff is not None else None
        ),
        "runtime_medical_publication_surface_report_path": (
            runtime_medical_publication_surface.get("source_path")
            if runtime_medical_publication_surface is not None
            else None
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
