from __future__ import annotations

import importlib


ALL_STAGES = (
    "literature_scout",
    "line_selection",
    "baseline",
    "primary_analysis",
    "bounded_analysis",
    "route_back",
    "stop_loss",
    "revision_reopen",
    "runtime_recovery",
    "finalize_rebuild",
    "final_pre_submission_audit",
)


def _module():
    return importlib.import_module("med_autoscience.controllers.multistudy_soak_proof")


def _ready_study(study_id: str, archetype: str) -> dict[str, object]:
    contracts = {
        "literature_contract": True,
        "statistical_contract": True,
    }
    if archetype == "prediction_model/external_validation":
        contracts["external_validation_fixture"] = True
    return {
        "study_id": study_id,
        "study_archetype": archetype,
        "stages": list(ALL_STAGES),
        "contracts": contracts,
        "result_strength": "adequate",
        "route_action": "continue",
    }


def test_complete_fixture_is_ready_across_required_archetypes_and_stages() -> None:
    projection = _module().build_multistudy_soak_matrix_projection(
        [
            _ready_study("001-risk-model", "prediction_model/external_validation"),
            _ready_study("002-real-world", "observational_real_world"),
            _ready_study("003-triage", "subtype_or_triage"),
        ],
    )

    assert projection["overall_status"] == "ready"
    assert projection["next_action"] == "continue_multistudy_soak"
    assert projection["missing_archetypes"] == []
    assert projection["coverage_manifest"] == {
        "required_archetypes": [
            "prediction_model/external_validation",
            "observational_real_world",
            "subtype_or_triage",
        ],
        "covered_archetypes": [
            "observational_real_world",
            "prediction_model/external_validation",
            "subtype_or_triage",
        ],
        "required_stages": list(ALL_STAGES),
        "covered_stage_matrix": {
            "001-risk-model": list(ALL_STAGES),
            "002-real-world": list(ALL_STAGES),
            "003-triage": list(ALL_STAGES),
        },
    }
    assert projection["authority_contract"]["can_authorize_quality"] is False
    assert projection["authority_contract"]["can_authorize_finalize"] is False
    assert projection["authority_contract"]["can_authorize_submission"] is False

    for study in projection["studies"]:
        assert study["status"] == "ready"
        assert study["missing_gaps"] == []
        assert study["required_stages"] == list(ALL_STAGES)
        assert study["authority_contract"]["can_authorize_quality"] is False


def test_missing_literature_statistics_or_external_validation_blocks_study() -> None:
    projection = _module().build_multistudy_soak_matrix_projection(
        [
            {
                **_ready_study("001-risk-model", "prediction_model/external_validation"),
                "contracts": {
                    "literature_contract": False,
                    "statistical_contract": False,
                    "external_validation_fixture": False,
                },
            },
            _ready_study("002-real-world", "observational_real_world"),
            _ready_study("003-triage", "subtype_or_triage"),
        ],
    )

    assert projection["overall_status"] == "blocked"
    assert projection["next_action"] == "materialize_literature_contract"
    blocked = projection["studies"][0]
    assert blocked["status"] == "blocked"
    assert blocked["missing_gaps"] == [
        "contract:literature_contract",
        "contract:statistical_contract",
        "contract:external_validation_fixture",
    ]
    assert blocked["blocking_gaps"] == blocked["missing_gaps"]


def test_missing_stage_reports_per_study_gap_without_blocking_contracts() -> None:
    incomplete = _ready_study("002-real-world", "observational_real_world")
    incomplete["stages"] = [stage for stage in ALL_STAGES if stage != "runtime_recovery"]
    projection = _module().build_multistudy_soak_matrix_projection(
        [
            _ready_study("001-risk-model", "prediction_model/external_validation"),
            incomplete,
            _ready_study("003-triage", "subtype_or_triage"),
        ],
    )

    assert projection["overall_status"] == "partial"
    study = projection["studies"][1]
    assert study["status"] == "partial"
    assert study["missing_gaps"] == ["stage:runtime_recovery"]
    assert study["blocking_gaps"] == []
    assert study["next_action"] == "complete_stage_runtime_recovery"


def test_weak_result_must_stop_loss_or_switch_line() -> None:
    unsafe = {
        **_ready_study("003-triage", "subtype_or_triage"),
        "result_strength": "weak",
        "route_action": "continue",
    }
    projection = _module().build_multistudy_soak_matrix_projection(
        [
            _ready_study("001-risk-model", "prediction_model/external_validation"),
            _ready_study("002-real-world", "observational_real_world"),
            unsafe,
        ],
    )

    assert projection["overall_status"] == "blocked"
    weak = projection["studies"][2]
    assert weak["status"] == "blocked"
    assert weak["missing_gaps"] == ["route:weak_result_requires_stop_loss_or_switch_line"]
    assert weak["next_action"] == "materialize_route_weak_result_requires_stop_loss_or_switch_line"

    safe = {
        **_ready_study("003-triage", "subtype_or_triage"),
        "result_strength": "weak",
        "route_action": "stop_loss",
    }
    projection = _module().build_multistudy_soak_matrix_projection(
        [
            _ready_study("001-risk-model", "prediction_model/external_validation"),
            _ready_study("002-real-world", "observational_real_world"),
            safe,
        ],
    )
    assert projection["overall_status"] == "ready"
    assert projection["studies"][2]["next_action"] == "stop_loss"
