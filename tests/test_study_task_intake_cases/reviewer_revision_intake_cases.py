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
    assert override["same_line_route_truth"]["same_line_state"] == "bounded_analysis"


def test_reviewer_task_intake_preserves_publication_gate_work_unit_identity(tmp_path: Path) -> None:
    intake_module = importlib.import_module("med_autoscience.study_task_intake")
    outer_loop_intake = importlib.import_module("med_autoscience.controllers.study_outer_loop_task_intake")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        intake_module.latest_task_intake_json_path(study_root=study_root),
        {
            "task_id": "study-task::002-dm-china-us-mortality-attribution::20260427T020548Z",
            "task_intent": (
                "用户已对糖尿病002投稿包给出明确审稿式反馈：必须作为 reviewer_revision / "
                "manuscript revision 重新激活同一论文线。"
            ),
            "first_cycle_outputs": ["paper/rebuttal/review_matrix.md and action_plan.md"],
            "constraints": ["不要直接手工 patch manuscript/current_package 投影作为最终修复。"],
        },
    )
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "medical_publication_surface_blocked",
            "claim_evidence_consistency_failed",
            "submission_hardening_incomplete",
        ],
        "medical_publication_surface_status": "blocked",
        "medical_publication_surface_blockers": [
            "missing_medical_story_contract",
            "figure_semantics_manifest_missing_or_incomplete",
        ],
        "current_required_action": "return_to_publishability_gate",
    }

    action = outer_loop_intake.recommended_task_intake_action(
        study_root=study_root,
        publishability_gate_report=gate_report,
    )

    assert action is not None
    assert action["work_unit_fingerprint"].startswith("publication-blockers::")
    assert action["route_key_question"].startswith("analysis_claim_evidence_repair:")
    assert action["source_route_key_question"]
    assert action["next_work_unit"]["unit_id"] == "analysis_claim_evidence_repair"
    assert action["next_work_unit"]["lane"] == "analysis-campaign"
    assert action["blocking_work_units"][0]["unit_id"] == "analysis_claim_evidence_repair"


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
        "discussion_claim_guardrails",
        "handoff_evidence_surface",
    ]
    assert summary["revision_intake"]["reactivation_required"] is True
    assert (
        summary["revision_intake"]["current_package_edit_policy"]["direct_current_package_edit_allowed"]
        is False
    )
    assert summary["revision_intake"]["handoff_required"] is True

    markdown = module.render_task_intake_markdown(payload)
    assert "## Revision Intake Checklist" in markdown
    assert "text revisions" in markdown
    assert "handoff/evidence surface" in markdown
    assert "stopped/submission-ready/finalize" in markdown
    assert "先通过 MAS-owned launch/resume 接管 canonical paper surface" in markdown

    runtime_context = module.render_task_intake_runtime_context(payload)
    assert "Revision intake: reviewer_revision" in runtime_context
    assert "stopped milestone state is not foreground current_package edit permission" in runtime_context
    assert "Relaunch/resume through MAS-owned runtime before editing canonical paper sources." in runtime_context


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
