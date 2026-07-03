from __future__ import annotations

import json
from pathlib import Path


def _agent_lab_handoff_contract() -> dict[str, object]:
    contract_path = Path(__file__).resolve().parents[2] / "contracts" / "agent_lab_handoff.json"
    return json.loads(contract_path.read_text(encoding="utf-8"))


def _medical_quality_mappings() -> list[dict[str, object]]:
    contract = _agent_lab_handoff_contract()
    return contract["meta_agent_work_order_contract"]["external_suite_improvement_policy"][
        "medical_manuscript_quality"
    ]["change_ref_mappings"]


def test_agent_lab_handoff_routes_feedback_targets_to_scholar_skills_single_source() -> None:
    handoff = _agent_lab_handoff_contract()
    contract_text = json.dumps(handoff, ensure_ascii=False)
    policy = handoff["meta_agent_work_order_contract"]["external_suite_improvement_policy"]
    mappings = policy["capability_target_mappings"]

    assert "skill_ref:medical-research-write" not in contract_text
    assert "src/med_autoscience/overlay/templates/medical-research-write.SKILL.md" not in contract_text
    assert mappings["figure_quality"]["target_skill_ref"] == (
        "external_repo:mas-scholar-skills/skills/medical-figure-design/SKILL.md"
    )
    assert mappings["manuscript_quality"]["target_capability_id"] == "medical-manuscript-writing"
    assert mappings["review_quality"]["target_capability_id"] == "medical-manuscript-review"
    assert mappings["citation_literature"]["target_capability_id"] == "medical-research-lit"
    assert mappings["stats"]["target_capability_id"] == "medical-statistical-review"
    assert mappings["table"]["target_capability_id"] == "medical-table-design"
    assert mappings["submission"]["target_capability_id"] == "medical-submission-prep"
    assert mappings["data_governance"]["target_capability_id"] == "medical-data-governance"
    assert "contracts/capability_map.json" in handoff["meta_agent_work_order_contract"]["editable_surface_refs"]


def test_mas_capability_map_keeps_scholar_skills_refs_only_boundary() -> None:
    capability_map_path = Path(__file__).resolve().parents[2] / "contracts" / "capability_map.json"
    capability_map = json.loads(capability_map_path.read_text(encoding="utf-8"))
    policy = capability_map["consumer_policy"]
    mappings = {
        item["feedback_target"]: item
        for item in capability_map["feedback_target_mappings"]
    }

    assert capability_map["external_capability_pack_target"]["domain_id"] == "mas-scholar-skills"
    assert capability_map["external_capability_pack_target"]["delivery_domain"] == "capability_pack"
    assert policy["mas_stage_prompts_remain_in_mas"] is True
    assert policy["mas_owner_authority_remains_in_mas"] is True
    assert policy["scholar_skills_outputs_are_refs_only_candidates"] is True
    assert policy["scholar_skills_may_write_mas_truth"] is False
    assert mappings["figure_quality"]["target_skill_ref"] == (
        "external_repo:mas-scholar-skills/skills/medical-figure-design/SKILL.md"
    )
    assert mappings["manuscript_quality"]["target_capability_id"] == "medical-manuscript-writing"


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
        "stale_ai_reviewer_current_eval_drift",
        "dead_letter_stabilizes_to_owner_blocker",
        "macro_state_no_stale_live",
        "medical_manuscript_no_runtime_language",
        "methods_results_numeric_reproducibility_floor",
        "structured_evidence_text_table_consistency",
    }.issubset(set(prediction_mapping["quality_target_refs"]))
    assert {
        "mechanism-edit-ref:mas/ai-reviewer-record-current-manuscript-binding",
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
        "stale_ai_reviewer_current_eval_drift",
        "dead_letter_stabilizes_to_owner_blocker",
        "macro_state_no_stale_live",
        "medical_manuscript_no_runtime_language",
        "methods_results_numeric_reproducibility_floor",
    }.issubset(set(observational_mapping["quality_target_refs"]))
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
    }.issubset(set(observational_mapping["target_surface_refs"]))
