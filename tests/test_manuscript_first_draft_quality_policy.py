from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.authority_handlers._generation_manifest import (
    FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    FIRST_DRAFT_VALIDATION_DESIGNS,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
)


ROOT = Path(__file__).resolve().parents[1]
POLICY_REF = "contracts/manuscript_first_draft_quality_policy.json"


def _load(relative_path: str) -> dict[str, object]:
    return json.loads((ROOT / relative_path).read_text(encoding="utf-8"))


def _read(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def test_prediction_model_first_draft_contract_preserves_current_semantics() -> None:
    policy = _load(POLICY_REF)
    prediction = policy["prediction_model_first_draft"]
    generation_schema = _load(
        "contracts/schemas/v2/mas-evidence-generation-manifest.schema.json"
    )
    application_schema = generation_schema["$defs"][
        "first_draft_quality_application"
    ]

    assert policy["version"] == "mas-manuscript-first-draft-quality-policy.v3"
    assert set(prediction["supported_validation_designs"]) == (
        set(FIRST_DRAFT_VALIDATION_DESIGNS) - {"not_applicable"}
    )
    assert set(
        application_schema["properties"]["validation_design"]["enum"]
    ) == set(FIRST_DRAFT_VALIDATION_DESIGNS)
    assert prediction[
        "external_transportability_skill_may_be_required_for_internal_validation"
    ] is False
    assert prediction[
        "external_transportability_skill_may_be_required_for_internal_external"
    ] is False
    assert "linked_prediction_performance_ref" in prediction["required_candidate_refs"]
    assert "active_reference_currentness_ref" in policy["base_first_draft_contract"][
        "required_upstream_candidate_refs"
    ]
    assert set(
        policy["base_first_draft_contract"]["conditional_authoring_candidate_refs"][
            "reader_pdf"
        ]
    ) == {
        "document_display_scope_coverage_ref",
        "display_render_integrity_ref",
    }

    adequacy = prediction["model_complexity_and_sparse_event_adequacy"]
    ph_contract = adequacy["conditional_evidence"]["ph_assessment_ref"]
    nonlinearity = adequacy["conditional_evidence"][
        "nonlinearity_assessment_ref"
    ]
    assert "ph_assessment_applicability" in adequacy["must_bind"]
    assert ph_contract["applicability_field"] == "ph_assessment_applicability"
    assert ph_contract["applicability_values"] == [
        "required",
        "not_applicable_with_reason",
    ]
    assert ph_contract["required_when"] == (
        "ph_assessment_applicability_is_required"
    )
    assert ph_contract["model_family_text_inference_allowed"] is False
    assert nonlinearity["required_when"] == "continuous_predictor_count_is_positive"

    horizon = prediction["fixed_horizon_risk_semantics"]
    assert horizon["recorded_event_count_fraction_role"] == (
        "descriptive_count_fraction_not_risk_estimate"
    )
    assert horizon[
        "binary_event_fraction_may_be_called_observed_risk_with_early_censoring"
    ] is False
    assert {
        "censored_before_horizon_count",
        "independent_censoring_assumption",
        "survey_weighting_boundary",
    }.issubset(horizon["must_bind"])

    decision_curve = prediction["decision_curve_validity"]
    assert {
        "calibration_basis_ref",
        "calibration_basis_status",
        "uncertainty_method",
        "uncertainty_interval_ref",
        "analysis_set_policy",
        "clinical_action_scenarios",
    }.issubset(decision_curve["must_bind"])
    assert decision_curve["clinical_action_scenarios_required_count"] == 1
    assert decision_curve["unverified_calibration_basis_disposition"] == (
        "route_back_required"
    )

    table_one = prediction["baseline_table_traceability"]
    assert {
        "variable_level_denominator",
        "missingness_count_and_percent",
        "standardized_mean_difference",
        "source_numeric_trace",
    }.issubset(table_one["must_bind"])
    display = prediction["document_display_scope_coverage"]
    assert {
        "composed_paper_pdf_exact_ref",
        "page_render_or_page_hash_evidence",
    }.issubset(display["must_bind"])
    assert display["successful_render_exit_proves_display_quality"] is False


def test_v2_application_and_skill_receipts_are_exact_and_readback_visible() -> None:
    policy = _load(POLICY_REF)
    generation_schema = _load(
        "contracts/schemas/v2/mas-evidence-generation-manifest.schema.json"
    )
    output_schema = _load(
        "contracts/schemas/v2/mas-paper-mission-authority.output.schema.json"
    )
    stage_pack = _load("contracts/mas-paper-study-stage-pack.json")
    readback = stage_pack["reviewer_revision_default_mechanism"][
        "stage_attempt_readback_contract"
    ]
    routing = readback["first_draft_professional_skill_routing"]
    revision_sync = stage_pack["reviewer_revision_default_mechanism"][
        "reviewer_response_sync_contract"
    ]

    base = policy["base_first_draft_contract"]
    assert base["current_application_schema_version"] == 2
    assert base["legacy_application_schema_version_read_compatible"] is True
    assert base["legacy_application_cannot_satisfy_current_first_draft_ready"] is True
    assert base[
        "current_selected_build_requires_scholar_v2_semantic_policy_bindings"
    ] is True
    assert base[
        "legacy_v2_without_selected_build_preserves_exact_owner_receipt_abi"
    ] is True
    assert set(base["candidate_disposition_statuses"]) == set(
        FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES
    )
    assert base["candidate_disposition_requires_exact_ref_when"] == [
        "satisfied",
        "route_back_required",
    ]
    assert base["current_applicable_candidate_ref_minimum_size_bytes"] == 1
    assert policy["progress_and_quality"]["route_priority"] == list(
        FIRST_DRAFT_QUALITY_ROUTE_PRIORITY
    )
    invariants = policy["cross_stage_generation_invariants"]
    assert invariants["candidate_adjudicator_acceptance_required_for_clinical_identity"] is True
    assert invariants[
        "selected_build_dependency_currentness_requires_expanded_sealed_owner_receipt"
    ] is True
    assert invariants[
        "selected_build_dependency_currentness_requires_separate_current_owner_authority"
    ] is True
    assert invariants[
        "generation_producer_cannot_issue_build_dependency_currentness_authority"
    ] is True
    assert invariants[
        "selected_build_currentness_applies_to_every_paper_mission_request"
    ] is True
    assert invariants[
        "frozen_reviewer_response_replacement_requires_new_revision_generation"
    ] is True
    assert invariants[
        "external_synthesis_must_bind_original_frozen_response_bytes"
    ] is True
    assert invariants[
        "independently_reviewed_response_requires_current_manifest_independent_reviewer_receipt"
    ] is True
    assert invariants["professional_payloads_remain_owned_by"] == "mas-scholar-skills"
    assert revision_sync["early_analysis_generation_is_not_gated"] is True
    assert revision_sync[
        "higher_scope_manifest_does_not_preempt_earlier_mission_stage"
    ] is True
    assert revision_sync["applicable_mission_stages"] == [
        "manuscript_authoring",
        "review_and_quality_gate",
        "finalize_and_publication_handoff",
    ]
    assert revision_sync["candidate_status_cannot_claim_owner_acceptance"] is True
    assert revision_sync["owner_acceptance_requires_paper_mission_owner_receipt"] is True
    assert revision_sync["action_matrix_item_ids_must_equal_response_comment_ids"] is True
    assert revision_sync[
        "implemented_or_independently_reviewed_requires_nonempty_exact_evidence_refs"
    ] is True
    assert revision_sync[
        "build_dependency_currentness_authority_is_separately_host_injected"
    ] is True
    assert revision_sync[
        "build_dependency_currentness_authority_ref_and_issuer_attempt_are_host_context_bound"
    ] is True
    assert revision_sync[
        "build_dependency_currentness_authority_epoch_must_match_current_review_authority_epoch"
    ] is True
    assert revision_sync[
        "build_dependency_currentness_authority_issuer_attempt_must_differ_from_generation_producer"
    ] is True
    assert revision_sync["implemented_candidate_evidence_kind"] == "mas_evidence"
    assert revision_sync["independently_reviewed_candidate_evidence_kind"] == (
        "mas_reviewer_receipt"
    )
    assert revision_sync[
        "independently_reviewed_candidate_receipt_must_match_current_manifest_review_receipt"
    ] is True
    assert revision_sync["frozen_response_prior_exact_identity_required"] is True
    assert revision_sync["frozen_response_owner_ledger_history_ref_required"] is True
    assert revision_sync[
        "frozen_response_history_must_reuse_build_currentness_owner_ledger_ref"
    ] is True
    assert revision_sync[
        "same_generation_response_byte_replacement_requires_new_revision"
    ] is True
    assert revision_sync[
        "external_synthesis_must_bind_original_frozen_response_bytes"
    ] is True

    source_authority = policy["professional_skill_source_authority"]
    assert source_authority == {
        "package_id": "mas-scholar-skills",
        "package_version": "0.2.15",
        "source_commit": "5c1015a90cfd937d01f69b419ddbcce84398891a",
        "content_lock": {
            "algorithm": "sha256",
            "canonicalization": "ordered_path_length_file_length_bytes",
            "digest": (
                "sha256:c7c35cb51d72c2d0f8de45d296997e04350dafd8d630fb88"
                "f18d880fc4e331bc"
            ),
        },
        "bound_quality_contract_sections": [
            "cross_stage_generation_invariants",
            "initial_draft_evidence_integrity_requirements",
        ],
        "source_can_issue_mas_authority": False,
    }

    invocation_schema = generation_schema["$defs"][
        "professional_manuscript_skill_invocation"
    ]
    disposition_schema = generation_schema["$defs"][
        "first_draft_candidate_disposition"
    ]
    assert set(
        disposition_schema["properties"]["earliest_route_back_owner"]["enum"]
    ) == {None, *FIRST_DRAFT_QUALITY_ROUTE_PRIORITY}
    assert set(invocation_schema["properties"]["skill_id"]["enum"]) == set(
        PROFESSIONAL_MANUSCRIPT_SKILL_ROLES
    )
    v2_invocation_rule = next(
        rule
        for rule in invocation_schema["allOf"]
        if rule["if"]["properties"]["schema_version"]["const"] == 2
    )
    assert set(v2_invocation_rule["then"]["required"]) == {
        "invocation_ref",
        "receipt_ref",
        "input_artifact_bindings",
    }
    assert set(PROFESSIONAL_MANUSCRIPT_SKILL_ROLES).issubset(
        readback["professional_skill_ref_families"]
    )

    disposition = routing["candidate_disposition_contract"]
    assert set(disposition["statuses"]) == set(
        FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES
    )
    assert disposition["satisfied_or_route_back_requires_nonempty_candidate_ref"] is True
    assert routing["route_priority"] == list(FIRST_DRAFT_QUALITY_ROUTE_PRIORITY)
    exact_readback = routing["exact_receipt_readback"]
    assert exact_readback["exact_invocation_ref_required"] is True
    assert exact_readback["exact_skill_receipt_ref_required"] is True
    assert exact_readback["exact_input_artifact_bindings_required"] is True
    semantic = routing["scholar_v2_semantic_policy_consumption"]
    assert semantic["required_for_current_selected_build"] is True
    assert semantic["legacy_v2_without_selected_build_read_compatible"] is True
    assert semantic["reference_and_display_reuse_preflight_umbrella_policy"] is True
    assert semantic[
        "exact_invocation_receipt_policy_and_candidate_member_required"
    ] is True
    assert semantic["scholar_candidate_can_issue_mas_authority"] is False
    assert semantic["opl_runtime_integration_status"] == "declared_not_current"
    assert set(semantic["policy_ids"]) == {
        "scholarskills_medical_initial_draft_preflight.v2",
        "scholarskills_linked_prediction_performance.v2",
    }
    invocation_contract = policy["professional_invocation_contract"]
    assert invocation_contract[
        "missing_duplicate_legacy_or_orphan_semantic_invocation_fails_closed"
    ] is True
    assert set(invocation_contract["semantic_policy_ids"]) == {
        "scholarskills_medical_initial_draft_preflight.v2",
        "scholarskills_linked_prediction_performance.v2",
    }
    assert invocation_contract["umbrella_policy_validators"] == {
        "active_reference_currentness": "audit_active_reference_currentness",
        "display_render_integrity": "validate_display_render_integrity",
    }
    assert invocation_contract["external_skill_receipt_is_candidate_not_authority"] is True

    owner_receipt = output_schema["$defs"]["owner_receipt"]
    assert exact_readback["owner_receipt_projection_field"] in owner_receipt[
        "required"
    ]
    projection = owner_receipt["properties"][
        exact_readback["owner_receipt_projection_field"]
    ]
    assert set(projection["items"]["required"]) == {
        "skill_id",
        "target_id",
        "invocation_ref",
        "receipt_ref",
    }


def test_effective_authoring_surfaces_consume_current_first_draft_contract() -> None:
    manifest = _load("agent/stages/manifest.json")
    stage_pack = _load("contracts/mas-paper-study-stage-pack.json")
    cycle_policy = _load("contracts/stage_quality_cycle_policy.json")
    pack_input = _load("contracts/pack_compiler_input.json")
    prompt = " ".join(_read("agent/prompts/manuscript_authoring.md").split())
    stage_policy = " ".join(
        _read("agent/stages/manuscript_authoring.policy.md").split()
    )

    authoring = next(
        stage
        for stage in manifest["stages"]
        if stage["stage_id"] == "manuscript_authoring"
    )
    routing = authoring["stage_contract_extension"][
        "first_draft_professional_skill_routing"
    ]
    paper_routing = stage_pack["reviewer_revision_default_mechanism"][
        "stage_attempt_readback_contract"
    ]["first_draft_professional_skill_routing"]

    assert routing["quality_policy_ref"] == POLICY_REF
    assert paper_routing["quality_policy_ref"] == POLICY_REF
    assert routing["current_application_schema_version"] == 2
    assert routing["current_first_draft_required_specialists"] == [
        "medical-reference-integrity-auditor"
    ]
    assert routing["conditional_specialist_routes"] == {
        "uses_clinical_or_registry_data": (
            "medical-data-freeze-and-analysis-readiness-reviewer"
        ),
        "prediction_model": "medical-statistical-review",
        "fixed_horizon_or_competing_risk": "medical-survival-analysis-plan",
        "external_validation_only": (
            "medical-risk-model-transportability-reviewer"
        ),
        "table_one": "medical-table-design",
        "reader_pdf": "medical-display-qc",
    }
    assert routing["route_priority"] == paper_routing["route_priority"]
    assert routing["satisfied_or_route_back_requires_nonempty_candidate_ref"] is True
    assert routing["exact_skill_invocation_ref_required"] is True
    assert routing["exact_skill_receipt_ref_required"] is True
    assert routing["exact_input_artifact_bindings_required"] is True
    assert routing["owner_receipt_projects_exact_skill_refs"] is True

    artifact_gate = "agent/quality_gates/artifact_source_authority_gate.md"
    assert artifact_gate in authoring["quality_gate_refs"]
    assert artifact_gate in cycle_policy["stage_policies"]["manuscript_authoring"][
        "quality_rubric_refs"
    ]
    assert artifact_gate in stage_policy

    assert pack_input["required_domain_pack_paths"].count(POLICY_REF) == 1
    assert pack_input["source_refs"][
        "manuscript_first_draft_quality_policy_ref"
    ] == POLICY_REF
    assert pack_input["source_refs"]["required_domain_pack_paths"].count(
        POLICY_REF
    ) == 1
    for required_text in (
        "application schema v2",
        "route_back_required",
        "internal-external",
        "baseline, analysis, authoring, then review order",
        "ph_assessment_applicability=required",
        "document_display_scope_coverage_ref",
        "size_bytes >= 1",
        "recorded event fraction is descriptive",
    ):
        assert required_text in prompt


def test_specialist_skill_writeback_uses_current_developer_route_not_oma_work_order() -> None:
    stage_pack = _load("contracts/mas-paper-study-stage-pack.json")
    mechanism = stage_pack["reviewer_revision_default_mechanism"]
    writeback = mechanism["specialist_skill_writeback_contract"]
    handoff = writeback["work_order_handoff"]

    assert all(
        "OMA developer work order" not in route
        for route in mechanism["trigger"]["large_revision_routes"]
    )
    assert writeback["route"].startswith("OPL developer-supervisor")
    assert set(PROFESSIONAL_MANUSCRIPT_SKILL_ROLES).issubset(
        writeback["target_skill_ref_families"]
    )
    assert handoff["source_owner"] == "one-person-lab"
    assert handoff["source_surface"] == (
        "developer_supervisor_direct_repo_fix_or_pr_route"
    )
    assert handoff["oma_can_emit_work_order"] is False


def test_initial_draft_integrity_contract_machine_binds_all_eight_requirements() -> None:
    policy = _load(POLICY_REF)
    integrity = policy["initial_draft_evidence_integrity_requirements"]
    requirements = integrity["requirements"]
    expected_owners = {
        "fixed_horizon_censoring_aware_estimand": "baseline_and_evidence_setup",
        "prediction_claim_family_separation": "bounded_analysis_campaign",
        "analysis_scope_qualifier_propagation": "baseline_and_evidence_setup",
        "numeric_verification_scope": "bounded_analysis_campaign",
        "construct_comparability_stop": "baseline_and_evidence_setup",
        "non_mutating_anomaly_sensitivity": "bounded_analysis_campaign",
        "immutable_candidate_review": "manuscript_authoring",
        "structured_source_and_renderer_provenance": "manuscript_authoring",
    }

    assert integrity["requirement_ids"] == list(expected_owners)
    assert set(requirements) == set(expected_owners)
    for requirement_id, earliest_owner in expected_owners.items():
        requirement = requirements[requirement_id]
        assert requirement["earliest_owner"] == earliest_owner
        assert requirement["must_bind"]
        assert requirement["fail_closed_for_ready_claims"] is True

    horizon = requirements["fixed_horizon_censoring_aware_estimand"]
    assert {
        "recorded_event_count_and_fraction",
        "censored_before_horizon_count",
        "censoring_aware_observed_risk_estimator",
        "censoring_aware_prediction_error_estimator",
    }.issubset(horizon["must_bind"])
    assert horizon["recorded_event_fraction_role"] == "descriptive_only"
    assert horizon[
        "observed_risk_and_prediction_error_must_remain_distinct"
    ] is True
    assert horizon[
        "binary_event_fraction_may_replace_observed_risk_with_early_censoring"
    ] is False

    claim_families = requirements["prediction_claim_family_separation"]
    assert {
        "discrimination_evidence",
        "calibration_in_the_large_evidence",
        "calibration_slope_or_grouped_calibration_evidence",
        "prediction_range_compression_evidence",
        "recalibration_status",
        "clinical_utility_status",
        "transport_causal_attribution_status",
    }.issubset(claim_families["must_bind"])
    assert claim_families[
        "discrimination_may_authorize_absolute_risk_or_utility_claim"
    ] is False
    assert claim_families[
        "observed_transport_difference_may_be_labeled_causal_without_causal_design"
    ] is False

    qualifiers = requirements["analysis_scope_qualifier_propagation"]
    assert {
        "development_or_validation_status",
        "apparent_performance_status",
        "complete_case_status",
        "weighting_status",
        "target_population_inference_boundary",
    }.issubset(qualifiers["must_bind"])
    assert qualifiers[
        "surfaces_requiring_qualifier_when_corresponding_claim_appears"
    ] == [
        "title",
        "abstract",
        "results",
        "tables",
        "figures",
        "machine_readable_claims",
    ]
    assert qualifiers[
        "analysis_sample_may_be_promoted_to_target_population_without_design_support"
    ] is False
    assert qualifiers[
        "apparent_performance_may_be_presented_as_validated_performance"
    ] is False

    verification = requirements["numeric_verification_scope"]
    assert {
        "verification_evidence_class",
        "included_quantities",
        "excluded_quantities",
        "replicate_provenance",
        "independent_rerun_status",
    }.issubset(verification["must_bind"])
    assert verification[
        "bare_pass_count_may_be_called_independent_reproduction"
    ] is False
    assert verification["verification_scope_may_exceed_bound_quantities"] is False

    comparability = requirements["construct_comparability_stop"]
    assert comparability["missing_mapping_or_identity_linkage_disposition"] == (
        "not_estimable"
    )
    assert comparability[
        "proxy_substitution_for_non_isomorphic_construct_allowed"
    ] is False
    assert comparability[
        "non_estimability_may_be_interpreted_as_null_equivalence_or_difference"
    ] is False

    anomaly = requirements["non_mutating_anomaly_sensitivity"]
    assert {
        "frozen_source_value_ref",
        "derived_sensitivity_analysis_set_ref",
        "exact_estimate_deltas",
        "materiality_rule_and_status",
    }.issubset(anomaly["must_bind"])
    assert anomaly["sensitivity_analysis_may_mutate_frozen_source_values"] is False
    assert anomaly["materiality_may_be_claimed_without_a_defined_rule"] is False

    snapshot = requirements["immutable_candidate_review"]
    assert snapshot["reviewer_input_surface"] == "immutable_snapshot_only"
    assert snapshot["reviewer_may_reopen_live_workspace_files"] is False
    assert snapshot["changed_member_invalidates_dependent_lane_binding"] is True

    renderer = requirements["structured_source_and_renderer_provenance"]
    assert {
        "canonical_structured_evidence_ref",
        "canonical_structured_evidence_hash",
        "source_fingerprint",
        "render_request_bytes_hash",
        "renderer_identity_and_version",
        "output_fingerprints",
        "clean_rebuild_equality_status",
    }.issubset(renderer["must_bind"])
    assert set(renderer["derived_surfaces"]) == {
        "manuscript",
        "tables",
        "figures",
        "claim_ledger",
    }
    assert renderer[
        "all_derived_surfaces_require_one_generation_consistent_structured_source"
    ] is True
    assert renderer[
        "renderer_success_alone_proves_source_currentness_or_display_quality"
    ] is False


def test_four_stages_consume_only_their_declared_integrity_responsibilities() -> None:
    policy = _load(POLICY_REF)
    integrity = policy["initial_draft_evidence_integrity_requirements"]
    requirements = integrity["requirements"]
    stage_consumption = integrity["stage_consumption"]
    expected_consumption = {
        "baseline_and_evidence_setup": {
            "fixed_horizon_censoring_aware_estimand",
            "analysis_scope_qualifier_propagation",
            "construct_comparability_stop",
        },
        "bounded_analysis_campaign": {
            "fixed_horizon_censoring_aware_estimand",
            "prediction_claim_family_separation",
            "numeric_verification_scope",
            "non_mutating_anomaly_sensitivity",
        },
        "manuscript_authoring": {
            "analysis_scope_qualifier_propagation",
            "immutable_candidate_review",
            "structured_source_and_renderer_provenance",
        },
        "review_and_quality_gate": set(requirements),
    }

    assert set(stage_consumption) == set(expected_consumption)
    for stage_id, expected_requirements in expected_consumption.items():
        assert set(stage_consumption[stage_id]) == expected_requirements
        prompt = _read(f"agent/prompts/{stage_id}.md")
        stage_policy = _read(f"agent/stages/{stage_id}.policy.md")
        assert "initial_draft_evidence_integrity_requirements" in prompt
        assert "initial_draft_evidence_integrity_requirements" in stage_policy

    assert "non-isomorphic construct" in _read(
        "agent/prompts/baseline_and_evidence_setup.md"
    )
    assert "numeric verification claim" in _read(
        "agent/prompts/bounded_analysis_campaign.md"
    )
    assert "one generation-consistent structured evidence source" in _read(
        "agent/prompts/manuscript_authoring.md"
    )
    assert "never fill a gap by reopening live workspace files" in _read(
        "agent/prompts/review_and_quality_gate.md"
    )


def test_primary_skill_mirror_is_exact_and_routes_initial_draft_integrity() -> None:
    primary = _read("agent/primary_skill/SKILL.md")
    plugin_mirror = _read("plugins/med-autoscience/skills/med-autoscience/SKILL.md")

    assert primary == plugin_mirror
    assert "For every initial draft" in primary
    assert "initial_draft_evidence_integrity_requirements" in primary
    assert "at their declared earliest Stage owners" in primary
    assert "MAS retains medical, evidence, artifact, quality" in primary
    assert "OPL may transport and persist refs but cannot author medical truth" in primary


def test_learning_is_general_and_does_not_weaken_authority_boundaries() -> None:
    policy = _load(POLICY_REF)
    authority = policy["authority_boundary"]
    invocation = policy["professional_invocation_contract"]
    governed_surfaces = [
        POLICY_REF,
        "agent/prompts/baseline_and_evidence_setup.md",
        "agent/prompts/bounded_analysis_campaign.md",
        "agent/prompts/manuscript_authoring.md",
        "agent/prompts/review_and_quality_gate.md",
        "agent/stages/baseline_and_evidence_setup.policy.md",
        "agent/stages/bounded_analysis_campaign.policy.md",
        "agent/stages/manuscript_authoring.policy.md",
        "agent/stages/review_and_quality_gate.policy.md",
        "agent/primary_skill/SKILL.md",
        "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
    ]
    combined = "\n".join(_read(path) for path in governed_surfaces).casefold()

    for prohibited_study_specific_text in (
        "study 002",
        "study002",
        "nhanes",
        "diabetes",
        "dbp",
        "5,659",
        "1,387",
        "14.12%",
        "2.33%",
        "6.05",
        "0.134",
        "0.734",
        "0.752",
    ):
        assert prohibited_study_specific_text not in combined

    assert authority == {
        "professional_skills_supply_quality_rules_and_candidate_refs_only": True,
        "mas_owns_study_truth_and_candidate_admission": True,
        "mas_owns_artifact_mutation_and_publication_verdict": True,
        "opl_owns_transport_and_stage_attempt_lifecycle": True,
        "template_render_test_or_provider_completion_can_authorize_quality": False,
    }
    assert invocation["external_skill_receipt_is_candidate_not_authority"] is True
    assert policy["progress_and_quality"]["missing_ref_authorizes_content_invention"] is False
