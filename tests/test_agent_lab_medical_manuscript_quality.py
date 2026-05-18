from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.study_runtime_test_helpers import write_text


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_medical_manuscript_quality_agent_lab_suite_projects_blocked_domain_scorecard(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    write_text(study_root / "paper" / "draft.md", "# Draft\n")
    _write_json(study_root / "paper" / "evidence_ledger.json", {"items": []})
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must re-evaluate manuscript quality.",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": "reviewer_revision",
            "summary": "Manual review requests HDL harmonization, tables, CI, calibration, and prose repair.",
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]

    assert suite["suite_kind"] == "agent_lab_external_suite"
    assert suite["suite_role"] == "domain_quality_suite_with_meta_evolution_projection"
    assert task["task_family"] == "high_quality_medical_manuscript_self_evolution"
    assert "stage:mas/write/pre_draft_prediction_model_reporting" in task["stage_refs"]
    assert "scorer:mas/prediction-model-first-draft-quality" in task["scorer_refs"]
    assert task["scorecard"]["domain_owned"] is True
    assert task["scorecard"]["opl_scorecard_role"] == "scorecard_ref_projection_only"
    assert task["scorecard"]["passed"] is False
    assert task["promotion_gate"]["gate_status"] == "blocked"
    mechanism_inputs = task["mechanism_evolution_inputs"]
    graph = mechanism_inputs["research_memory_graph"]
    queue = mechanism_inputs["analysis_queue_manifest"]
    assert graph["body_included"] is False
    assert graph["paper_refs"] == [
        "research-memory-ref:mas/002-dm-china-us-mortality-attribution/paper_refs/body-free-default"
    ]
    assert graph["failed_route_refs"] == [
        "failed-route:mas/002-dm-china-us-mortality-attribution/medical-manuscript-quality-gap"
    ]
    assert queue["state"] == "blocked"
    assert queue["items"] == [
        {
            "ref": (
                "analysis-queue-item:mas/002-dm-china-us-mortality-attribution/"
                "medical-manuscript-quality-blocked"
            ),
            "state": "blocked",
            "retry_count": 0,
            "budget_cost": 0,
            "source_refs": [
                "analysis-queue-missing:mas/002-dm-china-us-mortality-attribution/"
                "medical-manuscript-quality"
            ],
        }
    ]
    assert task["improvement_candidate"]["candidate_kind"] == "rubric_gap"
    assert task["improvement_candidate"]["developer_patch_work_order"]["work_order_id"] == (
        "oma_developer_patch_work_order_99fdc0d34111"
    )
    assert task["improvement_candidate"]["developer_patch_work_order"]["owner_agent"] == "opl-meta-agent"
    assert task["improvement_candidate"]["developer_patch_work_order"]["role"] == "developer_direct_repo_patch"
    assert task["improvement_candidate"]["developer_patch_work_order"]["can_modify_mas_repo"] is True
    assert task["improvement_candidate"]["developer_patch_work_order"]["can_write_study_truth"] is False
    assert "analysis_harmonization_owner_callable" in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    assert task["improvement_candidate"]["target_agent_capability_gap"]["status"] == "candidate_only"
    assert "quality_contract_ref:prediction_model_first_draft_quality" in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/analysis-harmonization-owner-routing" in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    assert (
        "mechanism-edit-ref:mas/runtime-supervisor-analysis-harmonization-owner-result-consumption"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert "hdl-harmonization-and-sensitivity" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "nhanes-survey-weighting-and-unweighted-framing" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "uncertainty-intervals-and-validation-metrics" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "hard-methodology-unit-harmonization-route" in " ".join(task["promotion_gate"]["regression_suite_refs"])
    assert "analysis-harmonization-owner-routing" in " ".join(mechanism_inputs["target_editable_surface_refs"])
    assert (
        "runtime_supervisor_analysis_harmonization_owner_result_consumption"
        in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    )
    assert task["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert task["authority_boundary"]["can_mutate_domain_artifact"] is False


def test_medical_manuscript_quality_agent_lab_suite_projects_research_wiki_reviewer_and_analysis_queue(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must re-evaluate manuscript quality.",
                }
            },
        },
    )
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {"review_items": [{"ref": "review-ref:hdl-harmonization"}]},
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {"task_intent": "reviewer_revision", "summary": "HDL harmonization and calibration repair."},
    )
    _write_json(
        study_root / "artifacts" / "analysis_queue" / "latest.json",
        {
            "queue_ref": "analysis-queue:dm002/reviewer-repair",
            "state": "active",
            "retry_policy": {
                "policy_ref": "retry-policy:mas/analysis-campaign/manual-owner-retry",
                "max_retry_count": 2,
            },
            "budget": {"budget_ref": "analysis-budget:dm002/reviewer-repair", "max_cost": 8},
            "items": [
                {
                    "id": "analysis-queue:hdl-harmonization",
                    "state": "ready",
                    "retry_count": 1,
                    "budget_cost": 3,
                    "source_refs": ["review-ref:hdl-harmonization"],
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "research_wiki" / "latest.json",
        {
            "paper_refs": [{"ref": "paper-ref:dm002-current-draft"}],
            "claim_refs": [{"claim_ref": "claim-ref:hdl-unit-contamination"}],
            "experiment_refs": ["experiment-ref:external-validation-replay"],
            "failed_idea_refs": [{"id": "failed-idea:mechanical-completeness-gate"}],
            "negative_result_refs": [{"ref": "negative-result:uncalibrated-risk-collapse"}],
            "reusable_rationale_refs": ["rationale-ref:ai-reviewer-quality-route-back"],
            "failed_routes": [{"ref": "failed-route:internal-quality-language"}],
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]
    inputs = task["mechanism_evolution_inputs"]

    assert inputs["surface_kind"] == "mas_agent_lab_mechanism_evolution_inputs"
    assert inputs["target_opl_surface"] == "opl_agent_lab_evolution_result"
    assert inputs["automatic_mechanism_promotion_route"] == "risk_tiered_auto_promotion_with_independent_ai_review"
    assert inputs["authority_boundary"]["can_write_memory_body"] is False
    assert inputs["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert inputs["developer_patch_work_order"]["owner_agent"] == "opl-meta-agent"
    assert inputs["developer_patch_work_order"]["role"] == "developer_direct_repo_patch"
    assert inputs["developer_patch_work_order"]["can_modify_mas_repo"] is True
    assert inputs["developer_patch_work_order"]["can_write_study_truth"] is False
    assert any("research_wiki/latest.json" in ref for ref in inputs["research_wiki_refs"])
    assert any("failed-route" in ref for ref in inputs["failed_route_refs"])
    graph = inputs["research_memory_graph"]
    assert graph["surface_kind"] == "mas_research_memory_graph"
    assert graph["body_included"] is False
    assert graph["paper_refs"] == ["paper-ref:dm002-current-draft"]
    assert graph["claim_refs"] == ["claim-ref:hdl-unit-contamination"]
    assert graph["experiment_refs"] == ["experiment-ref:external-validation-replay"]
    assert graph["failed_idea_refs"] == ["failed-idea:mechanical-completeness-gate"]
    assert graph["negative_result_refs"] == ["negative-result:uncalibrated-risk-collapse"]
    assert graph["reusable_rationale_refs"] == ["rationale-ref:ai-reviewer-quality-route-back"]
    assert graph["failed_route_refs"] == ["failed-route:internal-quality-language"]
    assert graph["authority_boundary"]["can_write_memory_body"] is False
    assert any("review_ledger.json" in ref for ref in inputs["reviewer_direct_evidence_refs"])
    assert any("task_intake/latest.json" in ref for ref in inputs["reviewer_direct_evidence_refs"])
    assert any("analysis_queue/latest.json" in ref for ref in inputs["analysis_queue_manifest_refs"])
    queue = inputs["analysis_queue_manifest"]
    assert queue["surface_kind"] == "mas_analysis_queue_manifest"
    assert queue["body_included"] is False
    assert queue["queue_ref"] == "analysis-queue:dm002/reviewer-repair"
    assert queue["state"] == "active"
    assert queue["retry_policy"]["policy_ref"] == "retry-policy:mas/analysis-campaign/manual-owner-retry"
    assert queue["budget"] == {"budget_ref": "analysis-budget:dm002/reviewer-repair", "max_cost": 8}
    assert queue["items"] == [
        {
            "ref": "analysis-queue:hdl-harmonization",
            "state": "ready",
            "retry_count": 1,
            "budget_cost": 3,
            "source_refs": ["review-ref:hdl-harmonization"],
        }
    ]
    assert queue["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert "mechanism-edit-ref:mas/analysis-campaign-queue-routing" in inputs["target_editable_surface_refs"]
    assert "regression-suite:mas/agent-lab-research-wiki-reviewer-analysis-queue" in task["promotion_gate"]["regression_suite_refs"]


def test_medical_manuscript_quality_agent_lab_suite_records_controller_read_model_defect_refs(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "underdefined",
                    "summary": "AI reviewer must re-evaluate manuscript quality.",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "analysis_harmonization" / "latest.json",
        {
            "surface": "analysis_harmonization_owner_result",
            "owner": "analysis_harmonization_owner",
            "work_unit": "unit_harmonized_external_validation_rerun",
            "status": "blocked",
            "blocked_reason": "unit_harmonized_rerun_required",
            "typed_blocker_owner": "analysis_harmonization_owner",
            "typed_blocker": {"blocker_id": "unit_harmonized_rerun_required"},
            "unit_harmonized_rerun_completed": False,
        },
    )
    _write_json(
        study_root / "artifacts" / "supervision" / "hourly" / "latest.json",
        {
            "surface": "portable_runtime_supervisor_scan",
            "studies": [
                {
                    "study_id": study_root.name,
                    "action_queue": [{"action_type": "unit_harmonized_external_validation_rerun"}],
                }
            ],
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]
    inputs = task["mechanism_evolution_inputs"]
    refs = inputs["controller_read_model_feedback_refs"]

    assert any("analysis_harmonization/latest.json" in ref for ref in refs)
    assert any("supervision/hourly/latest.json" in ref for ref in refs)
    assert any("analysis-harmonization-result-requeued" in ref for ref in refs)
    assert refs[-1].startswith("mechanism-defect-ref:mas/002-dm-china-us-mortality-attribution/")
    work_order = inputs["developer_patch_work_order"]
    assert "runtime_supervisor_analysis_harmonization_owner_result_consumption" in work_order["required_patch_scopes"]
    assert any("analysis-harmonization-result-requeued" in ref for ref in work_order["evidence_refs"])
    assert work_order["can_modify_mas_repo"] is True
    assert work_order["can_write_study_truth"] is False
    assert "publication_eval/latest.json" in work_order["forbidden_writes"]


def test_medical_manuscript_quality_agent_lab_suite_materializes_refs_only_surface(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "002-dm-china-us-mortality-attribution"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "ready",
                    "summary": "AI reviewer judged the manuscript ready.",
                }
            },
        },
    )

    result = module.materialize_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    path = Path(result["suite_path"])
    payload = json.loads(path.read_text(encoding="utf-8"))

    assert result["surface_kind"] == "mas_agent_lab_medical_manuscript_quality_suite"
    assert result["status"] == "materialized"
    assert payload["tasks"][0]["scorecard"]["passed"] is True
    assert payload["tasks"][0]["promotion_gate"]["gate_status"] == "passed"
    assert payload["authority_boundary"]["can_write_domain_truth"] is False
