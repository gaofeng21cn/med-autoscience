from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_reviewer_revision_intake_detects_chinese_submission_review_feedback_reactivation() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intent": (
            "用户已对修改后投稿包给出新的审稿式反馈；这不是 submission metadata 收口，"
            "而是显式重新激活同一论文线，要求 MAS/MDS 以 revision/rebuttal 模式重新处理。"
            "必须先把反馈拆成可审计 action matrix，然后完成结构性返修与重建投稿包。"
        ),
        "constraints": ["不得手工 patch current_package 投影作为最终修复。"],
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    assert module.summarize_task_intake(payload)["revision_intake"]["kind"] == "reviewer_revision"


def test_explicit_reviewer_revision_kind_materializes_revision_intake_without_text_marker() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intake_kind": "reviewer_revision",
        "task_intent": (
            "DM002 high-priority methodology correction: current external-validation claims are "
            "potentially invalid because the active transportability input uses incompatible HDL units. "
            "Roll back from manuscript improvement to analysis/harmonization owner."
        ),
        "constraints": [
            "Do not continue prose polishing or submission readiness until the harmonization issue is resolved."
        ],
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    summary = module.summarize_task_intake(payload)
    assert summary["revision_intake"]["kind"] == "reviewer_revision"
    assert summary["revision_intake"]["reactivation_required"] is True
    trigger = summary["revision_intake"]["self_evolution_trigger"]
    assert trigger["surface_kind"] == "mas_reviewer_revision_self_evolution_trigger"
    assert trigger["status"] == "queued_for_agent_lab_external_suite"
    assert trigger["adapter_role"] == "domain_thin_feedback_adapter"
    assert trigger["oma_evolution_skill_ref"] == "opl-meta-agent:oma-agent-evolution"
    assert trigger["agent_lab_suite_materialization"]["required"] is True
    assert trigger["agent_lab_suite_materialization"]["contract_itself_triggers_execution"] is False
    assert trigger["target_actions"]["oma_materialization"] == (
        "opl-meta-agent.improve-from-external-agent-lab-suite"
    )
    assert trigger["target_actions"]["opl_work_order_execution"] == (
        "opl work-order execute"
    )
    assert trigger["status_projection"]["opl_app_should_show"] is True
    assert "reviewer_revision_coverage_audit_ref" in trigger["required_packet_refs"]
    assert "stage_attempt_readback_ref" in trigger["required_packet_refs"]
    assert trigger["closeout_acceptance_requirements"]["coverage_audit"][
        "closeout_without_audit_allowed"
    ] is False
    assert trigger["closeout_acceptance_requirements"]["stage_attempt_readback"][
        "missing_reason_fields"
    ] == [
        "missing_duration_reason",
        "missing_token_usage_reason",
        "missing_cost_reason",
    ]
    assert trigger["authority_boundary"]["can_write_owner_receipt"] is False
    assert trigger["authority_boundary"]["can_mutate_current_package"] is False
    selected_lane = summary["revision_intake"]["selected_revision_execution_lane"]
    assert selected_lane["lane_id"] == "reviewer_revision_general"
    assert selected_lane["agent_lab_suite_required"] is True
    assert selected_lane["agent_lab_suite_status"] == "pending"


def test_methodology_correction_routes_reviewer_revision_back_to_analysis() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intake_kind": "reviewer_revision",
        "task_intent": (
            "DM002 high-priority methodology correction: current external-validation claims are "
            "potentially invalid because the active transportability input uses incompatible HDL units. "
            "Roll back from manuscript improvement to analysis/harmonization owner."
        ),
        "constraints": [
            "Do not continue prose polishing until unit-harmonized external validation has been rerun."
        ],
        "first_cycle_outputs": [
            "analysis/harmonization route-back decision; unit-harmonized rerun or typed blocker"
        ],
    }

    override = module.build_task_intake_progress_override(payload)

    assert override is not None
    assert override["current_required_action"] == "return_to_analysis_campaign"
    assert override["paper_stage"] == "analysis-campaign"
    assert override["quality_execution_lane"]["route_target"] == "analysis-campaign"
    assert override["quality_execution_lane"]["lane_id"] == "reviewer_revision_general"
    assert (
        override["quality_execution_lane"]["selected_revision_execution_lane"]["lane_id"]
        == "reviewer_revision_general"
    )
    assert override["same_line_route_truth"]["same_line_state"] == "bounded_analysis"


def test_materialized_reviewer_revision_suite_projects_oma_pending_and_owner_callable_foreground(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "001-risk"
    payload = {
        "task_intake_kind": "reviewer_revision",
        "study_root": str(study_root),
        "task_intent": "Structural and first-draft-quality reviewer revision feedback.",
        "agent_lab_suite_materialization": {
            "status": "materialized",
            "suite_path": "artifacts/agent_lab/medical_manuscript_quality/latest_suite.json",
        },
    }

    summary = module.summarize_task_intake(payload)
    selected_lane = summary["revision_intake"]["selected_revision_execution_lane"]
    assert selected_lane["lane_id"] == "oma_self_evolution_pending"
    assert selected_lane["contract_itself_triggers_execution"] is False
    assert selected_lane["feedbackops_dispatch_request_status"] == "ready_for_opl_feedbackops"
    assert selected_lane["next_owner"] == "one-person-lab.feedbackops_then_opl-meta-agent"
    dispatch_request = module.build_reviewer_revision_feedbackops_dispatch_request(payload)
    assert dispatch_request["surface_kind"] == "mas_reviewer_revision_feedbackops_dispatch_request"
    assert dispatch_request["status"] == "ready_for_opl_feedbackops"
    assert dispatch_request["dispatch_is_automatic_request"] is True
    assert dispatch_request["contract_itself_triggers_execution"] is False
    assert dispatch_request["target_agent_id"] == "med-autoscience"
    assert dispatch_request["opl_feedbackops_target_agent_id"] == "mas"
    assert dispatch_request["dispatch_chain"] == [
        "opl feedback submit",
        "opl feedback read/reconcile",
        "opl-meta-agent improve-from-external-agent-lab-suite",
        "opl work-order execute",
        "med-autoscience paper_mission_readback_ref owner closeout consumption",
    ]
    assert dispatch_request["opl_feedback_submit"]["argv"][:2] == ["--target-agent", "mas"]
    assert dispatch_request["authority_boundary"]["can_write_study_truth"] is False
    override = module.build_task_intake_progress_override(payload, study_root=study_root)
    assert override["quality_execution_lane"]["lane_id"] == "oma_self_evolution_pending"

    _write_json(
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapter_receipts"
        / "latest.json",
        {
            "surface": "owner_callable_adapter_receipt_study_latest",
            "executions": [{"execution_status": "executed", "work_unit_id": "reviewer_revision"}],
        },
    )

    foreground_override = module.build_task_intake_progress_override(payload, study_root=study_root)
    foreground_lane = foreground_override["quality_execution_lane"]["selected_revision_execution_lane"]
    assert foreground_override["quality_execution_lane"]["lane_id"] == "owner_callable_foreground"
    assert foreground_lane["owner_callable_receipt_ref"].endswith(
        "owner_callable_adapter_receipts/latest.json"
    )
    assert "not a full OPL stage execution claim" in foreground_lane["summary"]


def test_final_micro_revision_with_no_new_analyses_uses_manuscript_fast_lane() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intake_kind": "reviewer_revision",
        "entry_mode": "manuscript_revision",
        "task_intent": (
            "Final pre-submission micro-revision for DM003: do not add analyses; "
            "preserve current scientific story; clean duplicated Discussion site "
            "fixed-effect wording; rename Figure 2 title to care-review gap profiles; "
            "clarify Table 2 Not assessed footnote; keep renal-risk exploratory and "
            "preserve supplementary material."
        ),
        "constraints": [
            "Use MAS owner route; do not directly edit submission authority surfaces outside controller-authorized manuscript/package flow.",
            "No new analyses; only terminology, duplicate sentence cleanup, abstract shortening if useful, and Table 2 footnote clarification.",
        ],
        "evidence_boundary": ["Current accepted evidence and figures/tables only; preserve supplementary material."],
    }

    summary = module.summarize_task_intake(payload)

    selected_lane = summary["revision_intake"]["selected_revision_execution_lane"]
    assert selected_lane["lane_id"] == "manuscript_fast_lane"
    assert selected_lane["agent_lab_suite_required"] is False
    assert selected_lane["agent_lab_suite_status"] == "bypassed"
    trigger = summary["revision_intake"]["self_evolution_trigger"]
    assert trigger["agent_lab_suite_materialization"]["required"] is False
    assert trigger["agent_lab_suite_materialization"]["bypass_allowed"] is True
    assert trigger["agent_lab_suite_materialization"]["bypass_reason"] == "text_only_fast_lane"
    assert summary["revision_intake"]["manuscript_fast_lane"]["status"] == "requested"


def test_reviewer_first_user_feedback_intake_detects_revision_reactivation() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intent": (
            "Resume the same 001 manuscript line for reviewer-first revision based on explicit user feedback. "
            "Do not directly edit manuscript/current_package; use paper/rebuttal/input as trusted input and route "
            "the work back through MAS/MDS write/review/publication gate surfaces. Tighten Methods, calibration "
            "and clinical-claim boundaries, table/figure legends, TRIPOD/PROBAST reporting, and paper-facing wording."
        ),
        "constraints": [
            "Do not frame the model as ready for direct clinical decision-making; state internal validation and external-validation needs."
        ],
        "trusted_inputs": [
            "studies/001-dm-cvd-mortality-risk/paper/rebuttal/input/2026-04-26_user_feedback_methods_calibration_scope.md"
        ],
        "first_cycle_outputs": [
            "Create or update paper/rebuttal review matrix/action plan, revise paper-facing source surfaces, run publication/reporting gate."
        ],
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    summary = module.summarize_task_intake(payload)
    assert summary["revision_intake"]["kind"] == "reviewer_revision"
    assert summary["revision_intake"]["reactivation_required"] is True
    contract = summary["submission_revision_operating_contract"]
    assert contract["surface_kind"] == "submission_revision_operating_contract"
    assert contract["state"] == "reviewer_revision"
    assert contract["canonical_write_surface"] == "paper/"
    assert contract["projection_surface"] == "manuscript/current_package/"
    assert contract["completion_claim_policy"] == {
        "projection_exists_equals_submission_ready": False,
        "current_package_direct_edit_completes_task": False,
        "authority_note_is_manuscript_surface": False,
        "requires_ai_reviewer_backed_quality_record": True,
        "requires_publication_gate_clear": True,
        "requires_source_signature_current": True,
        "requires_package_freshness": True,
    }


def test_reviewer_revision_intake_is_detected_and_summarized() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "study_id": "study-revision",
        "emitted_at": "2026-04-24T00:00:00+00:00",
        "task_intent": "根据导师反馈和审稿意见推进论文修改，补齐 Introduction/Methods/Results/Figure/Table feedback。",
        "constraints": ["前台直接改稿后必须留下 durable handoff。"],
        "trusted_inputs": ["reviewer feedback letter", "导师反馈截图"],
        "first_cycle_outputs": ["revision checklist", "MDS handoff note"],
    }

    summary = module.summarize_task_intake(payload)
    assert summary["revision_intake"]["kind"] == "reviewer_revision"
    assert summary["revision_intake"]["status"] == "active"
    assert summary["revision_intake"]["checklist"] == [
        "text_revisions",
        "methods_completeness",
        "statistical_analysis",
        "tables_figures",
        "follow_up_evidence",
        "scientific_finding_pattern",
        "analysis_gap_route_back",
        "discussion_claim_guardrails",
        "figure_table_terminology_retention",
        "coverage_audit",
        "handoff_evidence_surface",
    ]
    assert summary["revision_intake"]["reactivation_required"] is True
    trigger = summary["revision_intake"]["self_evolution_trigger"]
    assert trigger["feedbackops_event_kind"] == "target_agent_feedback_external_suite"
    assert trigger["accepted_feedback_profile"] == "target_agent_feedback_external_suite"
    assert trigger["feedback_profiles"] == [
        "target_agent_feedback_external_suite",
        "reviewer_revision_feedback",
    ]
    assert trigger["target_agent_id"] == "med-autoscience"
    assert trigger["idempotency_key"] == (
        "feedbackops:mas/study-revision/reviewer_revision/2026-04-24T00:00:00+00:00"
    )
    assert trigger["feedback_capture_requires_execution_authorization"] is False
    assert trigger["repo_fix_execution_requires_opl_execution_authorization"] is True
    assert "runtime-ref:trusted_opl_execution_authorization" in trigger[
        "opl_execution_authorization_refs"
    ]
    assert trigger["refs_only"] is True
    assert trigger["writes_study_truth"] is False
    assert trigger["paper_mission_subordination"]["mainline_route"] == [
        "PaperMission",
        "submission_authority",
        "submission_authority_owner_gate_or_typed_blocker",
    ]
    assert trigger["default_route"] == (
        "paper_mission_to_submission_authority_to_agent_lab_to_oma_then_owner_gate_or_typed_blocker"
    )
    assert trigger["owner_chain"] == [
        "med-autoscience:reviewer_revision_intake",
        "med-autoscience:agent_lab_medical_manuscript_quality_suite",
        "one-person-lab:feedbackops_agent_lab_projection",
        "opl-meta-agent:oma-agent-evolution",
        "med-autoscience:owner_closeout_readback",
    ]
    assert trigger["target_actions"]["mas_acceptance_readback"] == "paper_mission_readback_ref"
    assert trigger["owner_closeout_readback_refs"] == [
        "paper_mission_readback_ref",
        "submission_authority_owner_gate_readback_ref",
        "target_owner_receipt_or_typed_blocker_ref",
    ]
    assert summary["revision_intake"]["closeout_acceptance_requirements"]["coverage_audit"][
        "required_for_closeout"
    ] is True
    assert summary["revision_intake"]["closeout_acceptance_requirements"]["stage_attempt_readback"][
        "required_observability_fields"
    ] == ["duration", "token_usage", "cost"]
    assert trigger["authority_boundary"]["can_write_study_truth"] is False
    assert trigger["authority_boundary"]["can_write_typed_blocker"] is False
    assert (
        summary["revision_intake"]["current_package_edit_policy"]["direct_current_package_edit_allowed"]
        is False
    )
    assert summary["revision_intake"]["handoff_required"] is True

    markdown = module.render_task_intake_markdown(payload)
    assert "## Revision Intake Checklist" in markdown
    assert "text revisions" in markdown
    assert "coverage audit" in markdown
    assert "handoff/evidence surface" in markdown
    assert "stopped/submission-ready/finalize" in markdown
    assert "先通过 OPL current_control_state 按 MAS owner refs 接管 stage attempt" in markdown

    runtime_context = module.render_task_intake_runtime_context(payload)
    assert "Revision intake: reviewer_revision" in runtime_context
    assert "stopped milestone state is not foreground current_package edit permission" in runtime_context
    assert "OPL hydrates/resumes the provider attempt from MAS owner refs before MAS domain handlers edit canonical paper sources." in runtime_context


def test_non_revision_intake_does_not_emit_revision_checklist() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "study_id": "study-scout",
        "emitted_at": "2026-04-24T00:00:00+00:00",
        "task_intent": "为新队列做 early evidence framing。",
        "trusted_inputs": ["dataset dictionary"],
    }

    summary = module.summarize_task_intake(payload)
    assert summary.get("revision_intake") is None
    assert "Revision Intake Checklist" not in module.render_task_intake_markdown(payload)
