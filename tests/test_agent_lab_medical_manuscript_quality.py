from __future__ import annotations

import importlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

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
    assert "source_provenance_owner_recovery" in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    assert "source_provenance_terminal_blocker_route_back" in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    assert "methodology_reframe_decision_owner_route" in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    assert (
        "ai_native_expert_judgment_first_quality_boundary"
        in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    )
    assert (
        "cross_stage_vulnerability_audit_routing"
        in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    )
    assert (
        "internal_error_debug_history_paper_story_exclusion"
        in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    )
    assert task["improvement_candidate"]["target_agent_capability_gap"]["status"] == "candidate_only"
    assert "quality_contract_ref:prediction_model_first_draft_quality" in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/analysis-harmonization-owner-routing" in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/source-provenance-owner-recovery" in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    assert (
        "mechanism-edit-ref:mas/ai-native-expert-judgment-first-quality-boundary"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert (
        "mechanism-edit-ref:mas/cross-stage-vulnerability-audit-routing"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert (
        "mechanism-edit-ref:mas/internal-error-debug-history-paper-story-exclusion"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert (
        "mechanism-edit-ref:mas/source-provenance-terminal-blocker-route-back"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert (
        "mechanism-edit-ref:mas/methodology-reframe-decision-owner-route"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert (
        "mechanism-edit-ref:mas/domain-route-analysis-harmonization-owner-result-consumption"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert (
        "mechanism-edit-ref:mas/invalid-analysis-history-body-free-projection"
        in task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"]
    )
    assert "hdl-harmonization-and-sensitivity" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "nhanes-survey-weighting-and-unweighted-framing" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "uncertainty-intervals-and-validation-metrics" in " ".join(task["improvement_candidate"]["evidence_refs"])
    assert "hard-methodology-unit-harmonization-route" in " ".join(task["promotion_gate"]["regression_suite_refs"])
    assert "analysis-harmonization-owner-routing" in " ".join(mechanism_inputs["target_editable_surface_refs"])
    assert (
        "domain_route_analysis_harmonization_owner_result_consumption"
        in task["improvement_candidate"]["developer_patch_work_order"]["required_patch_scopes"]
    )
    judgment_boundary = mechanism_inputs["quality_judgment_boundary"]
    assert judgment_boundary["judgment_priority"] == "ai_native_expert_judgment_first"
    assert judgment_boundary["contract_rubric_role"] == "floor_and_route_baseline_not_ceiling"
    assert judgment_boundary["contracts_can_authorize_quality_ready"] is False
    assert judgment_boundary["rubric_can_authorize_quality_ready"] is False
    assert judgment_boundary["opl_meta_agent_can_patch_mas_repo"] is True
    assert judgment_boundary["opl_meta_agent_can_write_study_truth"] is False
    assert task["improvement_candidate"]["developer_patch_work_order"]["quality_judgment_boundary"] == (
        judgment_boundary
    )
    vulnerability_audit = mechanism_inputs["cross_stage_vulnerability_audit"]
    assert vulnerability_audit["audit_kind"] == "cross_stage_quality_vulnerability_scan"
    assert "stage:mas/review" in vulnerability_audit["must_scan_stage_refs"]
    assert "stage:mas/publication-gate" in vulnerability_audit["must_scan_stage_refs"]
    assert "mechanical_gate_overrides_ai_reviewer_judgment" in vulnerability_audit["vulnerability_classes"]
    assert vulnerability_audit["can_authorize_quality_ready"] is False
    story_exclusion = mechanism_inputs["paper_story_exclusion_policy"]
    assert story_exclusion["internal_error_debug_history_role"] == (
        "runtime_diagnostics_and_mechanism_learning_only"
    )
    assert story_exclusion["paper_story_can_use_debug_history"] is False
    assert story_exclusion["debug_history_can_authorize_quality_ready"] is False
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
        {
            "review_items": [{"ref": "review-ref:hdl-harmonization"}],
            "mechanism_patch_refs": ["mechanism-patch-ref:reviewer-route-hardening"],
        },
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "evidence_refs": ["evidence-ref:raw-cox-transport-output"],
            "raw_evidence_refs": ["raw-evidence-ref:cox-transport-jsonl"],
        },
    )
    _write_json(
        study_root / "artifacts" / "raw_evidence" / "latest.json",
        {
            "raw_evidence_refs": ["raw-evidence-ref:cox-transport-jsonl"],
            "source_refs": ["source-ref:transport-model-provenance"],
        },
    )
    _write_json(
        study_root / "paper" / "claim_evidence_map.json",
        {
            "claims": [{"claim_ref": "claim-ref:external-validation-performance"}],
            "evidence_refs": ["evidence-ref:cox-transport-validation"],
            "reviewer_refs": ["review-ref:hdl-harmonization"],
            "display_refs": ["display-ref:table-2-performance"],
        },
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
        study_root / "artifacts" / "analysis_campaign" / "queue_manifest.json",
        {
            "queue_ref": "analysis-campaign-queue:dm002/reviewer-repair",
            "state": "recoverable",
            "items": [
                {
                    "ref": "analysis-campaign-item:dm002/provenance-recovery",
                    "state": "blocked",
                    "source_refs": ["raw-evidence-ref:cox-transport-jsonl"],
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
    write_text(
        study_root / ".ds" / "events.jsonl",
        (
            '{"event_ref":"runtime-event:dm002/controller-route","event_type":"controller_route_selected",'
            '"body":"not projected"}\n'
        ),
    )
    write_text(
        study_root / "artifacts" / "runtime" / "events.jsonl",
        (
            '{"event_ref":"runtime-event:dm002/reviewer-redrive","event_type":"ai_reviewer_redrive",'
            '"body":"not projected"}\n'
        ),
    )
    _write_json(
        study_root / "artifacts" / "controller_decisions" / "latest.json",
        {"runtime_event_refs": ["runtime-event:dm002/controller-decision-recorded"]},
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "provider_state.json",
        {
            "provider_refs": ["provider-ref:temporal-production"],
            "fallback_refs": ["provider-fallback-ref:local-diagnostic-only"],
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "executor_context.json",
        {
            "executor_refs": ["executor-ref:codex_cli"],
            "context_isolation_refs": ["context-isolation-ref:reviewer-no-shared-context"],
        },
    )
    _write_json(
        study_root / "artifacts" / "reports" / "publishability_gate" / "latest.json",
        {
            "source_kind": "publication_gate_report",
            "current_required_action": "return_to_publishability_gate",
            "blockers": ["source_provenance_recovery_required"],
            "evidence_refs": ["evidence-ref:raw-cox-transport-output"],
            "review_refs": ["review-ref:hdl-harmonization"],
        },
    )
    _write_json(
        study_root / "artifacts" / "submission_targets" / "latest.json",
        {"target_venue_refs": ["venue-route-ref:target-journal"]},
    )
    _write_json(
        study_root / "paper" / "citation_audit.json",
        {
            "citation_refs": ["citation-ref:hdl-unit-source"],
            "missing_citation_refs": ["citation-gap-ref:calibration-model-source"],
        },
    )
    _write_json(
        study_root / "paper" / "kill_argument_review.json",
        {
            "kill_argument_refs": ["kill-argument-ref:unmeasured-treatment-confounding"],
            "strongest_counterargument_refs": ["counterargument-ref:registry-coding-bias"],
        },
    )
    _write_json(
        study_root / "artifacts" / "submission_assurance" / "latest.json",
        {
            "citation_audit_refs": ["submission-assurance-ref:citation-audit"],
            "kill_argument_review_refs": ["submission-assurance-ref:kill-argument-review"],
            "evidence_claim_alignment_refs": ["submission-assurance-ref:evidence-claim-alignment"],
            "submission_hygiene_refs": ["submission-assurance-ref:submission-hygiene"],
            "independent_reviewer_assurance_refs": [
                "submission-assurance-ref:independent-reviewer-assurance"
            ],
        },
    )
    _write_json(study_root / "paper" / "anonymity_check.json", {})
    write_text(study_root / "talk" / "slides.pptx", "pptx placeholder")
    write_text(study_root / "artifacts" / "overleaf" / "status.json", "{}\n")

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
    assert {
        "ref": "analysis-queue:hdl-harmonization",
        "state": "ready",
        "retry_count": 1,
        "budget_cost": 3,
        "source_refs": ["review-ref:hdl-harmonization"],
    } in queue["items"]
    assert {
        "ref": "analysis-campaign-item:dm002/provenance-recovery",
        "state": "blocked",
        "retry_count": 0,
        "budget_cost": 0,
        "source_refs": ["raw-evidence-ref:cox-transport-jsonl"],
    } in queue["items"]
    assert queue["authority_boundary"]["can_authorize_quality_verdict"] is False
    assert inputs["developer_patch_work_order"]["quality_judgment_boundary"][
        "requires_independent_ai_reviewer_receipt_for_quality_closure"
    ] is True
    assert inputs["developer_patch_work_order"]["paper_story_exclusion_policy"][
        "forbidden_projection"
    ] == "paper_main_story_or_medical_claim_support"
    runtime_events = inputs["runtime_event_ledger"]
    assert runtime_events["surface_kind"] == "mas_runtime_event_ledger"
    assert runtime_events["body_included"] is False
    assert runtime_events["event_count"] == 2
    assert any(".ds/events.jsonl" in ref for ref in runtime_events["event_source_refs"])
    assert any("runtime/events.jsonl" in ref for ref in runtime_events["event_source_refs"])
    assert runtime_events["controller_event_refs"] == ["runtime-event:dm002/controller-decision-recorded"]
    assert (
        "runtime-event-type:mas/002-dm-china-us-mortality-attribution/controller_route_selected"
        in runtime_events["event_type_refs"]
    )
    assert (
        "runtime-event-type:mas/002-dm-china-us-mortality-attribution/ai_reviewer_redrive"
        in runtime_events["event_type_refs"]
    )
    provider = inputs["provider_switch_hygiene"]
    assert provider["surface_kind"] == "mas_provider_switch_hygiene"
    assert provider["body_included"] is False
    assert provider["read_only"] is True
    assert provider["can_switch_provider"] is False
    assert provider["executor_refs"] == ["executor-ref:codex_cli"]
    assert provider["provider_refs"] == ["provider-ref:temporal-production"]
    assert provider["context_isolation_refs"] == ["context-isolation-ref:reviewer-no-shared-context"]
    assert provider["fallback_refs"] == ["provider-fallback-ref:local-diagnostic-only"]
    claim_map = inputs["claim_assurance_map"]
    assert claim_map["surface_kind"] == "mas_claim_assurance_map"
    assert claim_map["body_included"] is False
    assert claim_map["claim_body_included"] is False
    assert claim_map["can_authorize_claim"] is False
    assert claim_map["can_authorize_quality_verdict"] is False
    assert claim_map["claim_refs"] == [
        "claim-ref:external-validation-performance",
        "claim-ref:hdl-unit-contamination",
    ]
    assert claim_map["evidence_refs"] == ["evidence-ref:cox-transport-validation"]
    assert claim_map["reviewer_refs"] == ["review-ref:hdl-harmonization"]
    assert claim_map["display_refs"] == ["display-ref:table-2-performance"]
    assert any("paper/claim_evidence_map.json" in ref for ref in claim_map["claim_map_refs"])
    assurance = inputs["assurance_contract"]
    assert assurance["surface_kind"] == "mas_agent_lab_assurance_contract"
    assert assurance["contract_kind"] == "body_free_raw_evidence_review_publication_gate_contract"
    assert assurance["body_included"] is False
    assert assurance["raw_evidence_body_included"] is False
    assert assurance["review_ledger_body_included"] is False
    assert assurance["publication_gate_body_included"] is False
    assert any("artifacts/raw_evidence/latest.json" in ref for ref in assurance["raw_evidence_refs"])
    assert any("paper/evidence_ledger.json" in ref for ref in assurance["evidence_ledger_refs"])
    assert any("paper/review/review_ledger.json" in ref for ref in assurance["review_ledger_refs"])
    assert any("publishability_gate/latest.json" in ref for ref in assurance["publication_gate_refs"])
    assert "raw-evidence-ref:cox-transport-jsonl" in assurance["raw_evidence_item_refs"]
    assert "evidence-ref:raw-cox-transport-output" in assurance["evidence_item_refs"]
    assert "review-ref:hdl-harmonization" in assurance["review_item_refs"]
    assert "mechanism-patch-ref:reviewer-route-hardening" in assurance["mechanism_patch_refs"]
    assert assurance["can_authorize_submission_action"] is False
    review_gate = inputs["adversarial_review_gate"]
    assert review_gate["surface_kind"] == "mas_agent_lab_adversarial_review_gate"
    assert review_gate["gate_kind"] == "independent_reviewer_body_free_mechanism_gate"
    assert review_gate["independent_ai_reviewer_required"] is True
    assert review_gate["executor_context_reuse_allowed"] is False
    assert review_gate["can_promote_mechanism_patch"] is False
    assert review_gate["can_authorize_quality_verdict"] is False
    assert "review-ref:hdl-harmonization" in review_gate["review_ledger_item_refs"]
    assert "evidence-ref:raw-cox-transport-output" in review_gate["publication_gate_evidence_refs"]
    recovery = inputs["experiment_queue_recovery"]
    assert recovery["surface_kind"] == "mas_agent_lab_experiment_queue_recovery"
    assert recovery["recovery_kind"] == "body_free_analysis_campaign_queue_recovery"
    assert recovery["body_included"] is False
    assert recovery["can_authorize_analysis_completion"] is False
    assert any("analysis_campaign/queue_manifest.json" in ref for ref in recovery["campaign_queue_refs"])
    assert "analysis-campaign-item:dm002/provenance-recovery" in recovery["queue_item_refs"]
    assert "raw-evidence-ref:cox-transport-jsonl" in recovery["queue_source_refs"]
    aftercare = inputs["publication_aftercare_plan"]
    assert aftercare["surface_kind"] == "mas_publication_aftercare_plan"
    assert aftercare["body_included"] is False
    assert aftercare["can_push_submission"] is False
    assert aftercare["can_authorize_submission_action"] is False
    assert "publication-aftercare-plan:mas/002-dm-china-us-mortality-attribution" in aftercare[
        "publication_aftercare_plan_refs"
    ]
    assert "venue-route-ref:target-journal" in aftercare["venue_route_refs"]
    assert any("analysis_campaign/queue_manifest.json" in ref for ref in aftercare["external_suite_task_refs"])
    citation_audit = inputs["citation_audit"]
    assert citation_audit["surface_kind"] == "mas_agent_lab_citation_audit"
    assert citation_audit["audit_kind"] == "body_free_citation_audit_refs"
    assert citation_audit["body_included"] is False
    assert citation_audit["citation_body_included"] is False
    assert citation_audit["can_authorize_citation_correctness"] is False
    assert citation_audit["can_authorize_quality_verdict"] is False
    assert "citation-ref:hdl-unit-source" in citation_audit["citation_refs"]
    assert "citation-gap-ref:calibration-model-source" in citation_audit["missing_citation_refs"]
    kill_argument = inputs["kill_argument_review"]
    assert kill_argument["surface_kind"] == "mas_agent_lab_kill_argument_review"
    assert kill_argument["review_kind"] == "body_free_kill_argument_and_strongest_counterargument_refs"
    assert kill_argument["body_included"] is False
    assert kill_argument["claim_body_included"] is False
    assert kill_argument["review_body_included"] is False
    assert kill_argument["can_authorize_claim"] is False
    assert kill_argument["can_authorize_quality_verdict"] is False
    assert "kill-argument-ref:unmeasured-treatment-confounding" in kill_argument["kill_argument_refs"]
    assert "counterargument-ref:registry-coding-bias" in kill_argument["strongest_counterargument_refs"]
    submission_gate = inputs["submission_assurance_gate"]
    assert submission_gate["surface_kind"] == "mas_agent_lab_submission_assurance_gate"
    assert submission_gate["gate_kind"] == "body_free_five_layer_submission_assurance_gate"
    assert submission_gate["body_included"] is False
    assert submission_gate["can_authorize_publication_verdict"] is False
    assert submission_gate["can_authorize_submission_readiness"] is False
    assert submission_gate["can_mutate_submission_package"] is False
    assert submission_gate["required_layer_count"] == 5
    assert submission_gate["layer_count"] == 5
    assert {layer["layer_name"] for layer in submission_gate["gate_layers"]} == {
        "citation_audit",
        "kill_argument_review",
        "evidence_claim_alignment",
        "submission_hygiene",
        "independent_reviewer_assurance",
    }
    assert all(layer["body_included"] is False for layer in submission_gate["gate_layers"])
    assert all(layer["can_authorize_submission_readiness"] is False for layer in submission_gate["gate_layers"])
    assert all(layer["can_authorize_quality_verdict"] is False for layer in submission_gate["gate_layers"])
    effort_axes = inputs["effort_assurance_axes"]
    assert effort_axes["surface_kind"] == "mas_agent_lab_effort_assurance_axes"
    assert effort_axes["axis_kind"] == "body_free_effort_assurance_mechanism_inputs"
    assert effort_axes["body_included"] is False
    assert effort_axes["can_authorize_quality_verdict"] is False
    assert effort_axes["can_authorize_submission_readiness"] is False
    assert "analysis-queue:dm002/reviewer-repair" in effort_axes["effort_refs"]
    assert "submission-assurance-ref:independent-reviewer-assurance" in effort_axes["assurance_refs"]
    assert any("paper/citation_audit.json" in ref for ref in inputs["citation_audit_refs"])
    assert any("paper/kill_argument_review.json" in ref for ref in inputs["kill_argument_review_refs"])
    assert any("submission_assurance/latest.json" in ref for ref in inputs["submission_assurance_gate_refs"])
    assert "analysis-queue:dm002/reviewer-repair" in inputs["effort_assurance_axis_refs"]
    assert "submission-assurance-ref:independent-reviewer-assurance" in inputs["effort_assurance_axis_refs"]
    evidence_delta_refs = inputs["evidence_delta_refs"]
    assert "runtime-event:dm002/controller-decision-recorded" in evidence_delta_refs
    assert "provider-fallback-ref:local-diagnostic-only" in evidence_delta_refs
    assert "claim-ref:external-validation-performance" in evidence_delta_refs
    assert "evidence-ref:cox-transport-validation" in evidence_delta_refs
    assert "raw-evidence-ref:cox-transport-jsonl" in evidence_delta_refs
    assert "analysis-campaign-item:dm002/provenance-recovery" in evidence_delta_refs
    assert "publication-aftercare-plan:mas/002-dm-china-us-mortality-attribution" in evidence_delta_refs
    assert "citation-ref:hdl-unit-source" in evidence_delta_refs
    assert "kill-argument-ref:unmeasured-treatment-confounding" in evidence_delta_refs
    assert "submission-assurance-ref:submission-hygiene" in evidence_delta_refs
    assert "mechanism-edit-ref:mas/analysis-campaign-queue-routing" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/runtime-event-ledger-body-free-projection" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/provider-switch-hygiene-body-free-projection" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/claim-assurance-map-body-free-projection" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/assurance-contract-body-free-projection" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/adversarial-review-gate-body-free-projection" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/experiment-queue-recovery-body-free-projection" in inputs[
        "target_editable_surface_refs"
    ]
    assert "mechanism-edit-ref:mas/publication-aftercare-plan-body-free-projection" in inputs[
        "target_editable_surface_refs"
    ]
    assert "mechanism-edit-ref:mas/citation-audit-body-free-projection" in inputs["target_editable_surface_refs"]
    assert "mechanism-edit-ref:mas/kill-argument-counterargument-body-free-projection" in inputs[
        "target_editable_surface_refs"
    ]
    assert "mechanism-edit-ref:mas/submission-assurance-five-layer-gate-body-free-projection" in inputs[
        "target_editable_surface_refs"
    ]
    assert "mechanism-edit-ref:mas/effort-assurance-axes-body-free-projection" in inputs[
        "target_editable_surface_refs"
    ]
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
            "surface": "portable_domain_route_scan",
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
    assert "domain_route_analysis_harmonization_owner_result_consumption" in work_order["required_patch_scopes"]
    assert "cross_stage_vulnerability_audit_routing" in work_order["required_patch_scopes"]
    assert any("analysis-harmonization-result-requeued" in ref for ref in work_order["evidence_refs"])
    assert work_order["can_modify_mas_repo"] is True
    assert work_order["can_write_study_truth"] is False
    assert work_order["quality_judgment_boundary"]["contracts_can_authorize_quality_ready"] is False
    assert work_order["cross_stage_vulnerability_audit"]["can_authorize_quality_ready"] is False
    assert work_order["paper_story_exclusion_policy"]["paper_story_can_use_debug_history"] is False
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
