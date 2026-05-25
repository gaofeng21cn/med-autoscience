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
        "medical_manuscript_no_runtime_language",
        "methods_results_numeric_reproducibility_floor",
    }.issubset(target_ids)
    assert {
        "owner_chain_authority_monotonicity",
        "quality_repair_writer_handoff_currentness",
        "publication_work_unit_registry_consistency",
        "story_surface_delta_or_typed_blocker",
    }.issubset(set(inputs["owner_chain_regression_family"]["required_regression_targets"]))
    assert {
        "mechanism-edit-ref:mas/owner-chain-authority-monotonicity",
        "mechanism-edit-ref:mas/quality-repair-writer-handoff-currentness",
        "mechanism-edit-ref:mas/publication-work-unit-registry-consistency",
        "mechanism-edit-ref:mas/story-surface-delta-or-typed-blocker",
        "mechanism-edit-ref:mas/medical-manuscript-no-runtime-language",
        "mechanism-edit-ref:mas/methods-results-numeric-reproducibility-floor",
    }.issubset(target_refs)
    assert {
        "regression-suite:mas/owner-chain-authority-monotonicity",
        "regression-suite:mas/quality-repair-writer-handoff-currentness",
        "regression-suite:mas/publication-work-unit-registry-consistency",
        "regression-suite:mas/story-surface-delta-or-typed-blocker",
        "regression-suite:mas/medical-manuscript-quality-floor",
    }.issubset(regression_refs)
    assert {
        "owner_chain_authority_monotonicity_regression",
        "quality_repair_writer_handoff_currentness_regression",
        "publication_work_unit_registry_consistency_regression",
        "story_surface_delta_or_typed_blocker_regression",
        "medical_manuscript_quality_floor_regression",
    }.issubset(set(work_order["required_patch_scopes"]))
    assert {
        "failure-delta:mas/002-dm-china-us-mortality-attribution/owner-chain-authority-monotonicity",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/quality-repair-writer-handoff-currentness",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/publication-work-unit-registry-consistency",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/story-surface-delta-or-typed-blocker",
        "failure-delta:mas/002-dm-china-us-mortality-attribution/medical-manuscript-quality-floor",
    }.issubset(failure_refs)
    assert inputs["owner_chain_regression_family"]["can_authorize_quality_verdict"] is False
    assert inputs["owner_chain_regression_family"]["can_write_study_truth"] is False
