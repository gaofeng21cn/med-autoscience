from __future__ import annotations

import json
from pathlib import Path


def _medical_quality_mappings() -> list[dict[str, object]]:
    contract_path = Path(__file__).resolve().parents[2] / "contracts" / "agent_lab_handoff.json"
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    return contract["meta_agent_work_order_contract"]["external_suite_improvement_policy"][
        "medical_manuscript_quality"
    ]["change_ref_mappings"]


def test_agent_lab_handoff_contract_exposes_prediction_model_quality_target_refs() -> None:
    prediction_mapping = next(
        mapping
        for mapping in _medical_quality_mappings()
        if mapping["study_quality_target_family"] == "prediction_model_external_validation"
    )

    assert {
        "hdl_harmonization_and_sensitivity",
        "model_reproducibility_and_baseline_survival",
        "visible_baseline_and_performance_tables",
        "methods_reproducibility_complete_case_external_validation",
        "numeric_abstract_results_with_uncertainty",
        "uncertainty_intervals_and_validation_metrics",
        "nhanes_weighting_or_unweighted_framing",
        "calibration_risk_collapse_figure_quality",
        "grouped_calibration_with_observed_rate_intervals",
        "claim_evidence_display_alignment_without_runtime_language",
        "ai_reviewer_record_current_manuscript_binding",
        "owner_chain_authority_monotonicity",
        "quality_repair_writer_handoff_currentness",
        "publication_work_unit_registry_consistency",
        "story_surface_delta_or_typed_blocker",
        "medical_manuscript_no_runtime_language",
        "methods_results_numeric_reproducibility_floor",
    }.issubset(set(prediction_mapping["quality_target_refs"]))
    assert {
        "mechanism-edit-ref:mas/ai-reviewer-record-current-manuscript-binding",
        "mechanism-edit-ref:mas/owner-chain-authority-monotonicity",
        "mechanism-edit-ref:mas/quality-repair-writer-handoff-currentness",
        "mechanism-edit-ref:mas/publication-work-unit-registry-consistency",
        "mechanism-edit-ref:mas/story-surface-delta-or-typed-blocker",
        "mechanism-edit-ref:mas/medical-manuscript-no-runtime-language",
        "mechanism-edit-ref:mas/methods-results-numeric-reproducibility-floor",
    }.issubset(set(prediction_mapping["target_surface_refs"]))


def test_agent_lab_handoff_contract_exposes_observational_owner_chain_quality_refs() -> None:
    observational_mapping = next(
        mapping
        for mapping in _medical_quality_mappings()
        if mapping["study_quality_target_family"] == "observational_phenotype_treatment_gap"
    )

    assert {
        "owner_chain_authority_monotonicity",
        "quality_repair_writer_handoff_currentness",
        "publication_work_unit_registry_consistency",
        "story_surface_delta_or_typed_blocker",
        "medical_manuscript_no_runtime_language",
        "methods_results_numeric_reproducibility_floor",
    }.issubset(set(observational_mapping["quality_target_refs"]))
    assert {
        "mechanism-edit-ref:mas/owner-chain-authority-monotonicity",
        "mechanism-edit-ref:mas/quality-repair-writer-handoff-currentness",
        "mechanism-edit-ref:mas/publication-work-unit-registry-consistency",
        "mechanism-edit-ref:mas/story-surface-delta-or-typed-blocker",
        "mechanism-edit-ref:mas/medical-manuscript-no-runtime-language",
        "mechanism-edit-ref:mas/methods-results-numeric-reproducibility-floor",
    }.issubset(set(observational_mapping["target_surface_refs"]))
