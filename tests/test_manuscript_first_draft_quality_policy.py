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

    assert policy["version"] == "mas-manuscript-first-draft-quality-policy.v2"
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

    base = policy["base_first_draft_contract"]
    assert base["current_application_schema_version"] == 2
    assert base["legacy_application_schema_version_read_compatible"] is True
    assert base["legacy_application_cannot_satisfy_current_first_draft_ready"] is True
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
