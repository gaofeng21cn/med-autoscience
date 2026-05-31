from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_agent_lab_quality_suite_projects_owner_chain_regression_family(
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
                    "summary": "Current owner-chain repair still needs canonical story-surface evidence.",
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": "reviewer_revision",
            "summary": "DM002 owner-chain regression: writer handoff, work-unit registry, and story surface delta.",
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]
    inputs = task["mechanism_evolution_inputs"]
    work_order = task["improvement_candidate"]["developer_patch_work_order"]
    target_refs = set(task["improvement_candidate"]["target_agent_capability_gap"]["target_editable_surface_refs"])
    regression_refs = set(task["promotion_gate"]["regression_suite_refs"])
    failure_refs = set(task["promotion_gate"]["failure_delta_refs"])
    target_ids = {target["target_id"] for target in work_order["study_quality_targets"]}

    assert {
        "owner_chain_authority_monotonicity",
        "quality_repair_writer_handoff_currentness",
        "publication_work_unit_registry_consistency",
        "story_surface_delta_or_typed_blocker",
        "stale_ai_reviewer_current_eval_drift",
        "dead_letter_stabilizes_to_owner_blocker",
        "macro_state_no_stale_live",
        "medical_manuscript_no_runtime_language",
        "methods_results_numeric_reproducibility_floor",
        "structured_evidence_text_table_consistency",
    }.issubset(target_ids)
    assert {
        "owner_chain_authority_monotonicity",
        "quality_repair_writer_handoff_currentness",
        "publication_work_unit_registry_consistency",
        "story_surface_delta_or_typed_blocker",
        "stale_ai_reviewer_current_eval_drift",
        "dead_letter_stabilizes_to_owner_blocker",
        "macro_state_no_stale_live",
    }.issubset(set(inputs["owner_chain_regression_family"]["required_regression_targets"]))
    assert {
        "mechanism-edit-ref:mas/owner-chain-authority-monotonicity",
        "mechanism-edit-ref:mas/quality-repair-writer-handoff-currentness",
        "mechanism-edit-ref:mas/publication-work-unit-registry-consistency",
        "mechanism-edit-ref:mas/story-surface-delta-or-typed-blocker",
        "mechanism-edit-ref:mas/stale-ai-reviewer-current-eval-drift",
        "mechanism-edit-ref:mas/dead-letter-stabilizes-to-owner-blocker",
        "mechanism-edit-ref:mas/macro-state-no-stale-live",
        "mechanism-edit-ref:mas/medical-manuscript-no-runtime-language",
        "mechanism-edit-ref:mas/methods-results-numeric-reproducibility-floor",
        "mechanism-edit-ref:mas/structured-evidence-text-table-consistency",
    }.issubset(target_refs)
    assert {
        "regression-suite:mas/owner-chain-authority-monotonicity",
        "regression-suite:mas/quality-repair-writer-handoff-currentness",
        "regression-suite:mas/publication-work-unit-registry-consistency",
        "regression-suite:mas/story-surface-delta-or-typed-blocker",
        "regression-suite:mas/stale-ai-reviewer-current-eval-drift",
        "regression-suite:mas/dead-letter-stabilizes-to-owner-blocker",
        "regression-suite:mas/macro-state-no-stale-live",
        "regression-suite:mas/medical-manuscript-quality-floor",
        "regression-suite:mas/structured-evidence-text-table-consistency",
    }.issubset(regression_refs)
    assert {
        "owner_chain_authority_monotonicity_regression",
        "quality_repair_writer_handoff_currentness_regression",
        "publication_work_unit_registry_consistency_regression",
        "story_surface_delta_or_typed_blocker_regression",
        "stale_ai_reviewer_current_eval_drift_regression",
        "dead_letter_stabilizes_to_owner_blocker_regression",
        "macro_state_no_stale_live_regression",
        "medical_manuscript_quality_floor_regression",
    }.issubset(set(work_order["required_patch_scopes"]))
    assert {
        "failure-delta:mas/002-dm-china-us-mortality-attribution/owner-chain-authority-monotonicity",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/quality-repair-writer-handoff-currentness",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/publication-work-unit-registry-consistency",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/story-surface-delta-or-typed-blocker",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/stale-ai-reviewer-current-eval-drift",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/dead-letter-stabilizes-to-owner-blocker",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/macro-state-no-stale-live",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/medical-manuscript-quality-floor",
    }.issubset(failure_refs)
    assert inputs["owner_chain_regression_family"]["can_authorize_quality_verdict"] is False
    assert inputs["owner_chain_regression_family"]["can_write_study_truth"] is False


def test_agent_lab_quality_suite_projects_first_draft_quality_route_back_checklist(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.agent_lab_medical_manuscript_quality")
    study_root = tmp_path / "studies" / "003-dpcc-primary-care-phenotype-treatment-gap"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {"owner": "ai_reviewer", "ai_reviewer_required": False},
            "quality_assessment": {
                "medical_journal_prose_quality": {
                    "status": "blocked",
                    "summary": (
                        "Draft lacks reproducible Methods, numeric Results with uncertainty, "
                        "formal displays, claim-evidence alignment, and runtime-language purge."
                    ),
                }
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_intent": "reviewer_revision",
            "summary": "Treat manuscript quality feedback as executable route-back, not report-only blocker.",
        },
    )

    suite = module.build_medical_manuscript_quality_agent_lab_suite(study_root=study_root)
    task = suite["tasks"][0]
    checklist = task["mechanism_evolution_inputs"]["first_draft_quality_route_back_checklist"]
    work_order = task["improvement_candidate"]["developer_patch_work_order"]

    assert checklist["surface_kind"] == "first_draft_quality_route_back_checklist"
    assert checklist["status"] == "blocked"
    assert checklist["can_authorize_quality_verdict"] is False
    assert checklist["can_write_study_truth"] is False
    assert checklist["quality_gate_relaxation_allowed"] is False

    required_blockers = {
        "methods_reproducibility_floor_missing",
        "results_numeric_uncertainty_floor_missing",
        "formal_figure_table_quality_floor_missing",
        "abstract_hard_metrics_uncertainty_missing",
        "discussion_result_driven_non_defensive_floor_missing",
        "runtime_language_purge_required",
        "claim_evidence_alignment_required",
    }
    items_by_blocker = {item["blocker"]: item for item in checklist["items"]}
    assert required_blockers.issubset(items_by_blocker)
    for blocker in required_blockers:
        item = items_by_blocker[blocker]
        assert item["route_target"]
        assert item["owner"]
        assert item["next_work_units"]
        assert item["evidence_refs"]
        assert item["expected_repair_result"]

    runtime_item = items_by_blocker["runtime_language_purge_required"]
    assert runtime_item["owner"] == "write"
    assert "MAS" in runtime_item["forbidden_terms"]
    assert "AI reviewer" in runtime_item["forbidden_terms"]
    assert "submission readiness" in runtime_item["forbidden_terms"]
    assert "source gaps" in runtime_item["forbidden_terms"]
    assert runtime_item["expected_repair_result"] == (
        "canonical manuscript body contains no runtime/control-plane or internal QA terminology"
    )

    assert work_order["first_draft_quality_route_back_checklist"] == checklist
    assert "first_draft_quality_route_back_regression" in work_order["required_patch_scopes"]
