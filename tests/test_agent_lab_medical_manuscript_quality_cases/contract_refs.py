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
    capability_map_path = Path(__file__).resolve().parents[2] / "contracts" / "capability_map.json"
    capability_map = json.loads(capability_map_path.read_text(encoding="utf-8"))
    contract_text = json.dumps(handoff, ensure_ascii=False)
    policy = handoff["meta_agent_work_order_contract"]["external_suite_improvement_policy"]
    mappings = {
        item["feedback_target"]: item
        for item in capability_map["feedback_target_mappings"]
    }
    registry_ref = "opl-framework:contracts/opl-framework/agent-lab-failure-token-registry.json"

    assert "skill_ref:medical-research-write" not in contract_text
    assert "src/med_autoscience/overlay/templates/medical-research-write.SKILL.md" not in contract_text
    assert "capability_target_mappings" not in policy
    assert policy["capability_routing_ref"] == {
        "ref": "contracts/capability_map.json#/feedback_target_mappings",
        "role": "canonical_feedback_target_to_professional_skill_map",
        "body_included": False,
    }
    assert policy["failure_token_registry_ref"] == registry_ref
    assert policy["medical_failure_type_mappings_ref"] == (
        "contracts/capability_map.json#/medical_failure_type_mappings"
    )
    assert policy["owner_closeout_boundary"]["scholar_skills_or_oma_may_close_out_owner_loop"] is False
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
    assert f"{registry_ref}#/medical_failure_types/figure" in mappings["figure_quality"]["failure_token_refs"]
    assert f"{registry_ref}#/medical_failure_types/citation" in mappings["citation_literature"]["failure_token_refs"]
    assert f"{registry_ref}#/medical_failure_types/literature" in mappings["citation_literature"]["failure_token_refs"]
    assert all(
        mapping["owner_closeout_boundary_ref"] == "contracts/capability_map.json#/owner_closeout_boundary"
        for mapping in mappings.values()
    )
    assert "contracts/capability_map.json" in handoff["meta_agent_work_order_contract"]["editable_surface_refs"]


def test_mas_capability_map_keeps_scholar_skills_refs_only_boundary() -> None:
    capability_map_path = Path(__file__).resolve().parents[2] / "contracts" / "capability_map.json"
    capability_map = json.loads(capability_map_path.read_text(encoding="utf-8"))
    policy = capability_map["consumer_policy"]
    mappings = {
        item["feedback_target"]: item
        for item in capability_map["feedback_target_mappings"]
    }
    failure_mappings = {
        item["failure_type"]: item
        for item in capability_map["medical_failure_type_mappings"]
    }
    registry_ref = "opl-framework:contracts/opl-framework/agent-lab-failure-token-registry.json"

    assert capability_map["external_capability_pack_target"]["domain_id"] == "mas-scholar-skills"
    assert capability_map["external_capability_pack_target"]["delivery_domain"] == "capability_pack"
    assert capability_map["failure_token_registry_ref"] == registry_ref
    assert set(failure_mappings) == {
        "literature",
        "citation",
        "writing",
        "review",
        "figure",
        "statistics",
        "table",
        "submission",
        "data_governance",
    }
    assert policy["mas_stage_prompts_remain_in_mas"] is True
    assert policy["mas_owner_authority_remains_in_mas"] is True
    assert policy["scholar_skills_outputs_are_refs_only_candidates"] is True
    assert policy["scholar_skills_may_write_mas_truth"] is False
    owner_closeout = capability_map["owner_closeout_boundary"]
    assert owner_closeout["scholar_skills_or_oma_may_close_out_owner_loop"] is False


def test_mas_capability_map_declares_academicforge_skill_first_boundary() -> None:
    capability_map_path = Path(__file__).resolve().parents[2] / "contracts" / "capability_map.json"
    capability_map = json.loads(capability_map_path.read_text(encoding="utf-8"))
    policy = capability_map["consumer_policy"]["skill_first_capability_policy"]
    external_policy = capability_map["consumer_policy"]["external_specialist_library_policy"]
    owner_closeout = capability_map["owner_closeout_boundary"]
    mappings = {
        item["feedback_target"]: item
        for item in capability_map["feedback_target_mappings"]
    }
    failure_mappings = {
        item["failure_type"]: item
        for item in capability_map["medical_failure_type_mappings"]
    }
    registry_ref = "opl-framework:contracts/opl-framework/agent-lab-failure-token-registry.json"

    assert "contracts/academicforge_claude_science_learning_adoption.json" in (
        capability_map["source_of_truth"]
    )
    assert policy == {
        "professional_skill_is_first_class_capability_entry": True,
        "scripts_are_optional_deterministic_helpers": True,
        "contract_light_boundary_only": True,
        "ops_modularity_does_not_replace_skill_judgment": True,
        "missing_optional_specialist_skill_blocks_ordinary_progress": False,
        "mas_registry_exposes_descriptor_refs_not_runtime_ownership": True,
    }
    assert external_policy["skill_first_external_specialists"][
        "default_behavior"
    ] == "sync_only_when_current_delta_or_user_request_declares_specialist_need"
    assert external_policy["skill_first_external_specialists"]["bulk_load_allowed"] is False
    assert external_policy["skill_first_external_specialists"][
        "outputs_are_refs_only_candidates"
    ] is True
    assert "AlphaFold2" in external_policy["example_specialist_gaps"]
    assert "scientific compute runner" in external_policy["example_specialist_gaps"]
    assert "mas_owner_receipt_ref" in owner_closeout["closeout_requires_one_of"]
    assert "stable_typed_blocker_ref" in owner_closeout["closeout_requires_one_of"]
    assert mappings["figure_quality"]["target_skill_ref"] == (
        "external_repo:mas-scholar-skills/skills/medical-figure-design/SKILL.md"
    )
    assert mappings["manuscript_quality"]["target_capability_id"] == "medical-manuscript-writing"
    assert failure_mappings["literature"]["target_capability_id"] == "medical-research-lit"
    assert failure_mappings["citation"]["target_capability_id"] == "medical-research-lit"
    assert failure_mappings["writing"]["target_skill_ref"] == (
        "external_repo:mas-scholar-skills/skills/medical-manuscript-writing/SKILL.md"
    )
    assert all(registry_ref in item["verification_refs"] for item in failure_mappings.values())
    assert all(item["target_capability_id"] != "omics" for item in failure_mappings.values())
    assert all(item["target_capability_id"] != "intake" for item in failure_mappings.values())


def test_academicforge_learning_contract_classifies_all_claude_science_skills() -> None:
    contract_path = (
        Path(__file__).resolve().parents[2]
        / "contracts"
        / "academicforge_claude_science_learning_adoption.json"
    )
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    matrix = contract["parity_matrix"]
    items = matrix["items"]
    by_skill = {item["source_skill"]: item for item in items}

    assert matrix["source_skill_count"] == 32
    assert len(items) == 32
    assert len(by_skill) == 32
    assert matrix["live_evidence_excluded_from_this_contract"] is True
    assert matrix["coverage_status"] == "all_skills_classified_except_live_provider_evidence"
    for key, expected_count in matrix["classification_counts"].items():
        assert sum(1 for item in items if item["classification"] == key) == expected_count

    assert by_skill["figure-style"]["local_landing"] == (
        "mas-scholar-skills/skills/medical-figure-design/SKILL.md"
    )
    assert by_skill["paper-narrative"]["classification"] == "enhanced_existing_skill"
    assert by_skill["pdf-explore"]["local_landing"] == (
        "mas-scholar-skills/skills/research-pdf-evidence-explorer/SKILL.md"
    )
    assert by_skill["skill-creator"] == {
        "source_skill": "skill-creator",
        "classification": "skill_quality_absorbed",
        "local_landing": (
            "MAS Scholar Skills skill quality policy and scripts/verify.sh "
            "trigger/frontmatter/no-authority checks"
        ),
        "completion": "skill_quality_loop_landed",
    }
    assert by_skill["remote-compute-ssh"][
        "completion"
    ] == "skill_descriptor_landed_live_provider_evidence_pending"
    assert by_skill["self-awareness"]["classification"] == "watch_only"


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
