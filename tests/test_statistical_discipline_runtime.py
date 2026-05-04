from __future__ import annotations

import pytest

from med_autoscience.controllers.statistical_discipline_runtime import (
    FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS,
    REQUIRED_CANDIDATE_FIELDS,
    REQUIRED_STATISTICAL_DISCIPLINE_FIELDS,
    REQUIRED_STATISTICAL_REVIEWER_AUDIT_SECTIONS,
    REQUIRED_STATISTICAL_REVIEWER_TEMPLATE_FIELDS,
    STATISTICAL_DISCIPLINE_OPERATION_FIELDS,
    WAIVER_MACHINE_CHECKABLE_FIELDS,
    SUPPORTED_STUDY_ARCHETYPES,
    build_statistical_reviewer_discipline_library,
    build_statistical_reviewer_template_projection,
    build_statistical_discipline_operations_projection,
    build_statistical_discipline_contract,
    validate_bounded_analysis_candidate_board,
    validate_statistical_discipline_contract,
    validate_statistical_reviewer_audit,
)


def _machine_checkable_waiver(field: str, **overrides: object) -> dict[str, object]:
    waiver: dict[str, object] = {
        "field": field,
        "reason": "The active claim is explicitly bounded away from this evidence domain.",
        "claim_boundary": "The manuscript states that this domain is outside the target claim.",
        "evidence_refs": [f"methods/{field}_claim_boundary.json"],
        "reviewer_visible_artifact": f"paper/{field}_claim_boundary.md",
    }
    waiver.update(overrides)
    return waiver


def _valid_candidate(**overrides: object) -> dict[str, object]:
    candidate: dict[str, object] = {
        "target_claim": "The model preserves calibration under the locked external cohort.",
        "expected_evidence_gain": "Closes the transportability gap for the active claim.",
        "statistical_risk": "Limited precision in one prespecified subgroup.",
        "clinical_interpretability": "Maps directly to an actionable triage threshold.",
        "decision": "exploit",
        "decision_reason": "The candidate addresses the highest-risk evidence gap inside the bounded scope.",
        "primary_evidence_basis": "calibration slope, confidence interval, and decision-curve net benefit",
    }
    candidate.update(overrides)
    return candidate


def _valid_statistical_reviewer_audit(**section_overrides: object) -> dict[str, object]:
    sections = {
        section_key: {
            "status": "pass",
            "assessment": f"{section_key} is prespecified and aligned with the active claim boundary.",
            "evidence_refs": [f"paper/{section_key}.json"],
            "manuscript_action": "Keep the manuscript text aligned with the audited statistical evidence.",
        }
        for section_key in REQUIRED_STATISTICAL_REVIEWER_AUDIT_SECTIONS
    }
    sections["causal_language_boundary"]["forbidden_language"] = [
        "causal effect",
        "treatment effect",
    ]
    for section_key, override in section_overrides.items():
        if isinstance(override, dict) and override:
            sections[section_key].update(override)
        else:
            sections[section_key] = override
    return {
        "status": "resolved",
        "reviewer_role": "statistical_reviewer",
        "sections": sections,
    }


@pytest.mark.parametrize("study_archetype", SUPPORTED_STUDY_ARCHETYPES)
def test_build_statistical_discipline_contract_for_each_supported_archetype(study_archetype: str) -> None:
    contract = build_statistical_discipline_contract(study_archetype=study_archetype)

    assert contract["status"] == "resolved"
    assert contract["study_archetype"] == study_archetype
    for field in REQUIRED_STATISTICAL_DISCIPLINE_FIELDS:
        assert contract[field]

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "present", "reason_code": ""}


def test_statistical_discipline_contract_blocks_when_external_validation_plan_missing() -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract["external_validation_plan"]

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": "missing_external_validation_plan"}


@pytest.mark.parametrize(
    "field",
    [
        "missingness_plan",
        "subgroup_plan",
        "multiplicity_guardrail",
        "sensitivity_plan",
    ],
)
def test_statistical_discipline_contract_allows_machine_checkable_waiver_for_operation_fields(field: str) -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract[field]
    contract["waivers"] = [_machine_checkable_waiver(field)]

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "present", "reason_code": ""}


@pytest.mark.parametrize(
    "field",
    [
        "sample_size_precision_plan",
        "external_validation_plan",
        "clinical_utility_plan",
        "endpoint_time_window",
    ],
)
def test_statistical_discipline_contract_blocks_guideline_fail_closed_waiver_fields(field: str) -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract[field]
    contract[f"{field}_waiver_reason"] = "The active claim is explicitly bounded away from this evidence domain."

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": f"missing_{field}"}


@pytest.mark.parametrize("field", FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS)
def test_statistical_discipline_contract_blocks_fail_closed_waiver_fields(field: str) -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract[field]
    contract[f"{field}_waiver_reason"] = "The active claim is explicitly bounded away from this evidence domain."

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": f"missing_{field}"}


def test_statistical_discipline_contract_blocks_nominal_p_value_primary_evidence() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    contract["sensitivity_plan"] = "Primary evidence will be the nominal p-value from the main comparison."

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": "nominal_p_value_primary_evidence"}


def test_statistical_discipline_contract_requires_machine_checkable_operation_waiver() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    del contract["missingness_plan"]
    contract["waivers"] = [
        _machine_checkable_waiver("missingness_plan", evidence_refs=[]),
    ]

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": "incomplete_missingness_plan_waiver"}


@pytest.mark.parametrize(
    ("primary_evidence_basis", "reason_code"),
    [
        ("AUC-only performance is the primary evidence for the clinical claim.", "auc_only_primary_evidence"),
        (
            "Cluster separation-only is the primary evidence for durable subtype naming.",
            "cluster_separation_only_primary_evidence",
        ),
    ],
)
def test_metric_only_primary_evidence_blocks_contract_audit_and_candidate_board(
    primary_evidence_basis: str,
    reason_code: str,
) -> None:
    contract = build_statistical_discipline_contract(study_archetype="subtype_reconstruction")
    contract["primary_evidence_basis"] = primary_evidence_basis

    contract_validation = validate_statistical_discipline_contract(contract)

    assert contract_validation == {"status": "blocked", "reason_code": reason_code}

    audit = _valid_statistical_reviewer_audit(
        model_or_test_selection={"primary_evidence_basis": primary_evidence_basis}
    )
    audit_validation = validate_statistical_reviewer_audit(audit)

    assert audit_validation == {
        "status": "blocked",
        "reason_code": f"model_or_test_selection_{reason_code}",
    }

    candidate_validation = validate_bounded_analysis_candidate_board(
        {"candidates": [_valid_candidate(primary_evidence_basis=primary_evidence_basis)]}
    )

    assert candidate_validation == {"status": "blocked", "reason_code": f"candidate_{reason_code}"}


@pytest.mark.parametrize(
    ("core_evidence_basis", "reason_code"),
    [
        ("AUC is the core evidence for the clinical claim.", "auc_only_primary_evidence"),
        (
            "Cluster separation is the core evidence for durable subtype naming.",
            "cluster_separation_only_primary_evidence",
        ),
    ],
)
def test_metric_only_core_evidence_blocks_contract_audit_and_candidate_board(
    core_evidence_basis: str,
    reason_code: str,
) -> None:
    contract = build_statistical_discipline_contract(study_archetype="subtype_reconstruction")
    contract["core_evidence_basis"] = core_evidence_basis

    assert validate_statistical_discipline_contract(contract) == {
        "status": "blocked",
        "reason_code": reason_code,
    }

    audit = _valid_statistical_reviewer_audit(
        model_or_test_selection={"core_evidence_basis": core_evidence_basis}
    )
    assert validate_statistical_reviewer_audit(audit) == {
        "status": "blocked",
        "reason_code": f"model_or_test_selection_{reason_code}",
    }

    candidate_validation = validate_bounded_analysis_candidate_board(
        {"candidates": [_valid_candidate(core_evidence_basis=core_evidence_basis)]}
    )

    assert candidate_validation == {"status": "blocked", "reason_code": f"candidate_{reason_code}"}


def test_statistical_discipline_contract_blocks_primary_secondary_exploratory_classification() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    contract["evidence_classification"] = "primary"

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": "forbidden_evidence_classification"}


def test_statistical_reviewer_discipline_library_projects_each_archetype_template() -> None:
    library = build_statistical_reviewer_discipline_library()

    assert library["surface"] == "statistical_reviewer_discipline_library"
    assert library["schema_version"] == 1
    assert library["status"] == "ready"
    assert library["supported_study_archetypes"] == list(SUPPORTED_STUDY_ARCHETYPES)
    assert library["primary_evidence_rule"] == (
        "Nominal p-value, AUC-only, and cluster separation-only cannot be used as primary evidence."
    )
    assert library["fail_closed_fields"] == list(FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS)
    assert library["quality_claim_authorized"] is False
    assert library["mechanical_projection_can_authorize_quality"] is False

    for study_archetype in SUPPORTED_STUDY_ARCHETYPES:
        archetype = library["archetypes"][study_archetype]
        assert archetype["study_archetype"] == study_archetype
        assert archetype["label"]
        templates = archetype["templates"]
        assert set(templates) == set(STATISTICAL_DISCIPLINE_OPERATION_FIELDS)
        for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS:
            template = templates[field]
            for required_field in REQUIRED_STATISTICAL_REVIEWER_TEMPLATE_FIELDS:
                assert template[required_field]
            assert template["target_blocker"] == f"missing_{field}"
            assert template["required_evidence_refs"]
            waiver_requirements = template["waiver_reason_requirements"]
            if field in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS:
                assert waiver_requirements["waiver_allowed"] is False
                assert waiver_requirements["fail_closed_reason"]
            else:
                assert waiver_requirements["waiver_allowed"] is True
                assert waiver_requirements["required_reason_components"]


def test_statistical_reviewer_discipline_library_exposes_guideline_linked_evidence_contracts() -> None:
    library = build_statistical_reviewer_discipline_library()
    expected_guidelines = {
        "prediction_model": [
            "TRIPOD",
            "TRIPOD-AI",
            "transparent_reporting_multivariable_prediction_external_validation",
        ],
        "external_validation": [
            "TRIPOD",
            "transparent_reporting_multivariable_prediction_external_validation",
        ],
        "observational_real_world": ["STROBE", "RECORD"],
        "subtype_reconstruction": ["STROBE", "subtype_triage_specific_reviewer_concerns"],
        "gray_zone_triage": ["TRIPOD", "subtype_triage_specific_reviewer_concerns"],
        "ai_clinical_task": ["TRIPOD-AI", "CONSORT-AI"],
    }

    for study_archetype, guideline_families in expected_guidelines.items():
        archetype = library["archetypes"][study_archetype]
        guideline_pack = archetype.get("guideline_pack")
        assert isinstance(guideline_pack, dict)
        assert guideline_pack["guideline_families"] == guideline_families
        assert guideline_pack["authority_contract"] == {
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }

        evidence_contract = archetype.get("evidence_contract")
        assert isinstance(evidence_contract, dict)
        assert set(evidence_contract) == set(STATISTICAL_DISCIPLINE_OPERATION_FIELDS)
        for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS:
            evidence_requirement = evidence_contract[field]
            assert evidence_requirement["blocker"] == f"missing_{field}"
            assert evidence_requirement["required_evidence_refs"]
            assert evidence_requirement["waiver_allowed"] is (
                field not in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS
            )
            waiver_requirements = evidence_requirement["waiver_reason_requirements"]
            assert waiver_requirements["waiver_allowed"] is evidence_requirement["waiver_allowed"]
            if waiver_requirements["waiver_allowed"]:
                assert waiver_requirements["machine_checkable_fields"] == list(
                    WAIVER_MACHINE_CHECKABLE_FIELDS
                )
            else:
                assert waiver_requirements["machine_checkable_fields"] == []


def test_statistical_discipline_contract_carries_guideline_pack_without_quality_authority() -> None:
    contract = build_statistical_discipline_contract(study_archetype="external_validation")

    assert contract["quality_claim_authorized"] is False
    assert contract["mechanical_projection_can_authorize_quality"] is False
    assert contract["guideline_pack"]["guideline_families"] == [
        "TRIPOD",
        "transparent_reporting_multivariable_prediction_external_validation",
    ]
    assert set(contract["evidence_contract"]) == set(STATISTICAL_DISCIPLINE_OPERATION_FIELDS)
    assert contract["evidence_contract"]["external_validation_plan"]["waiver_allowed"] is False


@pytest.mark.parametrize(
    "study_archetype",
    [
        "prediction_model",
        "external_validation",
    ],
)
def test_statistical_reviewer_discipline_library_binds_prediction_validation_evidence(
    study_archetype: str,
) -> None:
    library = build_statistical_reviewer_discipline_library()
    archetype = library["archetypes"][study_archetype]

    assert archetype["template_family"] == "prediction_external_validation"
    external_validation = archetype["templates"]["external_validation_plan"]

    assert external_validation["target_blocker"] == "missing_external_validation_plan"
    assert "analysis/locked_external_temporal_or_site_validation" in external_validation[
        "required_evidence_refs"
    ]
    assert "calibration" in external_validation["reviewer_concern"].lower()
    assert "locked external" in external_validation["manuscript_action"]


def test_statistical_reviewer_template_projection_blocks_nominal_primary_evidence_and_fail_closed_fields() -> None:
    contract = build_statistical_discipline_contract(study_archetype="ai_clinical_task")
    del contract["endpoint_time_window"]
    del contract["clinical_utility_plan"]
    contract["endpoint_time_window_waiver_reason"] = "Endpoint timing is out of scope."
    contract["clinical_utility_plan_waiver_reason"] = "Clinical utility is out of scope."
    contract["sample_size_precision_plan"] = "Primary evidence will be a nominal p-value below 0.05."
    contract["waivers"] = [_machine_checkable_waiver("subgroup_plan")]

    projection = build_statistical_reviewer_template_projection(contract)

    assert projection["surface"] == "statistical_reviewer_template_projection"
    assert projection["schema_version"] == 1
    assert projection["status"] == "blocked"
    assert projection["study_archetype"] == "ai_clinical_task"
    assert projection["template_family"] == "ai_clinical_task"
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    assert "nominal_p_value_primary_evidence" in projection["blockers"]
    assert "missing_endpoint_time_window" in projection["blockers"]
    assert "endpoint_time_window_waiver_not_allowed" in projection["blockers"]
    assert "missing_clinical_utility_plan" in projection["blockers"]
    assert "clinical_utility_plan_waiver_not_allowed" in projection["blockers"]

    concerns = {concern["field"]: concern for concern in projection["reviewer_concerns"]}
    assert concerns["sample_size_precision_plan"]["status"] == "blocked"
    assert concerns["subgroup_plan"]["status"] == "waived"
    assert concerns["subgroup_plan"]["waiver_reason"] == (
        "The active claim is explicitly bounded away from this evidence domain."
    )
    assert concerns["endpoint_time_window"]["status"] == "blocked"
    assert concerns["endpoint_time_window"]["waiver_reason"] == ""
    assert concerns["endpoint_time_window"]["waiver_reason_requirements"]["waiver_allowed"] is False
    assert concerns["clinical_utility_plan"]["status"] == "blocked"
    assert concerns["clinical_utility_plan"]["waiver_reason_requirements"]["waiver_allowed"] is False


def test_statistical_reviewer_template_projection_rejects_unsupported_archetype() -> None:
    projection = build_statistical_reviewer_template_projection({"study_archetype": "case_report"})

    assert projection["status"] == "blocked"
    assert projection["reason_code"] == "unsupported_study_archetype"
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False


def test_statistical_reviewer_audit_accepts_complete_truth_contract() -> None:
    validation = validate_statistical_reviewer_audit(_valid_statistical_reviewer_audit())

    assert validation == {"status": "present", "reason_code": ""}


def test_statistical_reviewer_audit_requires_each_review_domain() -> None:
    audit = _valid_statistical_reviewer_audit(statistical_plan={})

    validation = validate_statistical_reviewer_audit(audit)

    assert validation == {"status": "blocked", "reason_code": "missing_statistical_plan"}


def test_statistical_reviewer_audit_blocks_unresolved_missing_data_review() -> None:
    audit = _valid_statistical_reviewer_audit(
        missing_data={
            "status": "open",
            "assessment": "Missingness remains unresolved.",
            "evidence_refs": ["paper/methods_implementation_manifest.json"],
            "manuscript_action": "Route back to analysis.",
        }
    )

    validation = validate_statistical_reviewer_audit(audit)

    assert validation == {"status": "blocked", "reason_code": "missing_data_not_passed"}


def test_statistical_reviewer_audit_blocks_nominal_p_value_primary_evidence() -> None:
    audit = _valid_statistical_reviewer_audit(
        model_or_test_selection={
            "primary_evidence_basis": "Nominal p-value below 0.05 as primary evidence."
        }
    )

    validation = validate_statistical_reviewer_audit(audit)

    assert validation == {
        "status": "blocked",
        "reason_code": "model_or_test_selection_nominal_p_value_primary_evidence",
    }


def test_statistical_reviewer_audit_blocks_primary_secondary_exploratory_classification() -> None:
    audit = _valid_statistical_reviewer_audit(
        statistical_plan={
            "evidence_classification": "secondary",
        }
    )

    validation = validate_statistical_reviewer_audit(audit)

    assert validation == {
        "status": "blocked",
        "reason_code": "statistical_plan_forbidden_evidence_classification",
    }


def test_bounded_analysis_candidate_board_requires_target_claim() -> None:
    candidate = _valid_candidate(target_claim="")

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": "candidate_missing_target_claim"}


@pytest.mark.parametrize("field", REQUIRED_CANDIDATE_FIELDS)
def test_bounded_analysis_candidate_board_blocks_missing_required_candidate_fields(field: str) -> None:
    candidate = _valid_candidate(**{field: ""})

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": f"candidate_missing_{field}"}


def test_bounded_analysis_candidate_board_allows_stop_candidate_with_reason() -> None:
    candidate = _valid_candidate(
        decision="stop",
        decision_reason="Expected evidence gain is below the prespecified threshold and would widen the claim.",
    )

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "present", "reason_code": ""}


def test_bounded_analysis_candidate_board_blocks_stop_candidate_without_reason() -> None:
    candidate = _valid_candidate(decision="stop", decision_reason="")

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": "candidate_missing_decision_reason"}


def test_bounded_analysis_candidate_board_blocks_nominal_p_value_primary_evidence() -> None:
    candidate = _valid_candidate(primary_evidence_basis="Nominal p-value below 0.05 as primary evidence.")

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": "candidate_nominal_p_value_primary_evidence"}


def test_bounded_analysis_candidate_board_blocks_primary_secondary_exploratory_classification() -> None:
    candidate = _valid_candidate(evidence_classification="exploratory")

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": "candidate_forbidden_evidence_classification"}


@pytest.mark.parametrize(
    "field",
    [
        "target_claim",
        "expected_evidence_gain",
        "statistical_risk",
        "clinical_interpretability",
        "decision_reason",
    ],
)
def test_bounded_analysis_candidate_board_blocks_placeholder_required_bindings(field: str) -> None:
    candidate = _valid_candidate(**{field: "TBD"})

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": f"candidate_placeholder_{field}"}


def test_bounded_analysis_candidate_board_blocks_unknown_decision() -> None:
    candidate = _valid_candidate(decision="continue")

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": "candidate_unsupported_decision"}


def test_statistical_discipline_operations_projection_blocks_missing_and_nominal_primary_evidence() -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract["external_validation_plan"]
    contract["sample_size_precision_plan"] = "Primary evidence will be a nominal p-value below 0.05."
    contract["waivers"] = [_machine_checkable_waiver("subgroup_plan")]

    projection = build_statistical_discipline_operations_projection(contract)

    assert projection["surface"] == "statistical_discipline_operations"
    assert projection["schema_version"] == 1
    assert projection["status"] == "blocked"
    assert projection["quality_claim_authorized"] is False
    assert projection["mechanical_projection_can_authorize_quality"] is False
    cards = {card["field"]: card for card in projection["action_cards"]}
    assert set(cards) == {
        "missingness_plan",
        "sample_size_precision_plan",
        "external_validation_plan",
        "subgroup_plan",
        "multiplicity_guardrail",
        "clinical_utility_plan",
        "endpoint_time_window",
        "sensitivity_plan",
    }
    assert cards["external_validation_plan"]["status"] == "blocked"
    assert cards["external_validation_plan"]["required_for_ready"] is True
    assert cards["external_validation_plan"]["waiver_allowed"] is False
    assert cards["sample_size_precision_plan"]["status"] == "blocked"
    assert cards["subgroup_plan"]["status"] == "waived"
    assert projection["waivers"] == [
        {
            "field": "subgroup_plan",
            "reason": "The active claim is explicitly bounded away from this evidence domain.",
            "claim_boundary": "The manuscript states that this domain is outside the target claim.",
            "evidence_refs": ["methods/subgroup_plan_claim_boundary.json"],
            "reviewer_visible_artifact": "paper/subgroup_plan_claim_boundary.md",
        }
    ]
    assert "missing_external_validation_plan" in projection["blockers"]
    assert "nominal_p_value_primary_evidence" in projection["blockers"]


def test_statistical_discipline_operations_projection_blocks_precision_and_external_validation_waivers() -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract["sample_size_precision_plan"]
    del contract["external_validation_plan"]
    contract["sample_size_precision_plan_waiver_reason"] = "Precision is out of scope."
    contract["external_validation_plan_waiver_reason"] = "External validation is out of scope."

    projection = build_statistical_discipline_operations_projection(contract)

    cards = {card["field"]: card for card in projection["action_cards"]}
    assert projection["status"] == "blocked"
    assert "missing_sample_size_precision_plan" in projection["blockers"]
    assert "sample_size_precision_plan_waiver_not_allowed" in projection["blockers"]
    assert "missing_external_validation_plan" in projection["blockers"]
    assert "external_validation_plan_waiver_not_allowed" in projection["blockers"]
    assert cards["sample_size_precision_plan"]["waiver_allowed"] is False
    assert cards["external_validation_plan"]["waiver_allowed"] is False


def test_statistical_discipline_operations_projection_blocks_incomplete_operation_waiver() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    del contract["sensitivity_plan"]
    contract["waivers"] = [_machine_checkable_waiver("sensitivity_plan", reviewer_visible_artifact="")]

    projection = build_statistical_discipline_operations_projection(contract)

    cards = {card["field"]: card for card in projection["action_cards"]}
    assert projection["status"] == "blocked"
    assert "incomplete_sensitivity_plan_waiver" in projection["blockers"]
    assert projection["waivers"] == []
    assert cards["sensitivity_plan"]["status"] == "blocked"


def test_statistical_discipline_operations_projection_blocks_weak_board_and_recommends_stop_switch() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    bounded_board = {
        "candidates": [
            _valid_candidate(
                target_claim="Primary route no longer supports the clinical claim.",
                expected_evidence_gain="Low after locked diagnostics.",
                statistical_risk="weak",
                decision="stop",
                decision_reason="External support and precision are both below the prespecified stop threshold.",
                board_status="weak",
            ),
            _valid_candidate(decision="continue"),
        ]
    }

    projection = build_statistical_discipline_operations_projection(contract, bounded_board=bounded_board)

    assert projection["status"] == "blocked"
    assert "candidate_0_weak_board" in projection["blockers"]
    assert "candidate_1_unsupported_decision" in projection["blockers"]
    stop_cards = [card for card in projection["action_cards"] if card["field"] == "bounded_board"]
    assert {
        "action_id": "candidate_0_stop_loss_switch_line",
        "label": "Stop-loss / switch-line decision",
        "summary": "Stop the current analysis line or switch line using the recorded decision reason.",
        "field": "bounded_board",
        "status": "blocked",
        "required_for_ready": True,
        "waiver_allowed": False,
    } in stop_cards


def test_statistical_discipline_operations_projection_blocks_top_level_weak_board_and_stop_without_reason() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    bounded_board = {
        "status": "weak",
        "candidates": [_valid_candidate(decision="stop", decision_reason="")],
    }

    projection = build_statistical_discipline_operations_projection(contract, bounded_board=bounded_board)

    assert projection["status"] == "blocked"
    assert "bounded_board_weak" in projection["blockers"]
    assert "candidate_0_missing_stop_reason" in projection["blockers"]


@pytest.mark.parametrize("field", REQUIRED_CANDIDATE_FIELDS)
def test_statistical_discipline_operations_projection_blocks_candidate_missing_required_binding(field: str) -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    bounded_board = {"candidates": [_valid_candidate(**{field: ""})]}

    projection = build_statistical_discipline_operations_projection(contract, bounded_board=bounded_board)

    assert projection["status"] == "blocked"
    assert f"candidate_0_missing_{field}" in projection["blockers"]
