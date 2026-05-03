from __future__ import annotations

import pytest

from med_autoscience.controllers.statistical_discipline_runtime import (
    REQUIRED_CANDIDATE_FIELDS,
    REQUIRED_STATISTICAL_DISCIPLINE_FIELDS,
    SUPPORTED_STUDY_ARCHETYPES,
    build_statistical_discipline_operations_projection,
    build_statistical_discipline_contract,
    validate_bounded_analysis_candidate_board,
    validate_statistical_discipline_contract,
)


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


def test_statistical_discipline_contract_blocks_nominal_p_value_primary_evidence() -> None:
    contract = build_statistical_discipline_contract(study_archetype="observational_real_world")
    contract["sensitivity_plan"] = "Primary evidence will be the nominal p-value from the main comparison."

    validation = validate_statistical_discipline_contract(contract)

    assert validation == {"status": "blocked", "reason_code": "nominal_p_value_primary_evidence"}


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


def test_bounded_analysis_candidate_board_blocks_unknown_decision() -> None:
    candidate = _valid_candidate(decision="continue")

    validation = validate_bounded_analysis_candidate_board({"candidates": [candidate]})

    assert validation == {"status": "blocked", "reason_code": "candidate_unsupported_decision"}


def test_statistical_discipline_operations_projection_blocks_missing_and_nominal_primary_evidence() -> None:
    contract = build_statistical_discipline_contract(study_archetype="prediction_model")
    del contract["external_validation_plan"]
    contract["sample_size_precision_plan"] = "Primary evidence will be a nominal p-value below 0.05."
    contract["subgroup_plan_waiver_reason"] = "No clinically meaningful subgroup is defensible for this endpoint."

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
    assert cards["external_validation_plan"]["waiver_allowed"] is True
    assert cards["sample_size_precision_plan"]["status"] == "blocked"
    assert cards["subgroup_plan"]["status"] == "waived"
    assert projection["waivers"] == [
        {
            "field": "subgroup_plan",
            "reason": "No clinically meaningful subgroup is defensible for this endpoint.",
        }
    ]
    assert "missing_external_validation_plan" in projection["blockers"]
    assert "nominal_p_value_primary_evidence" in projection["blockers"]


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
