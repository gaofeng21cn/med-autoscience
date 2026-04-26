from __future__ import annotations

from typing import Any


_GUIDELINE_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "STROBE": {
        "registry": "EQUATOR",
        "guideline_family": "STROBE",
        "applies_to": "observational_medical_study",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "study_design_and_setting",
            "participant_flow_and_eligibility",
            "variables_and_data_sources",
            "bias_and_missing_data",
            "statistical_methods_and_subgroups",
            "limitations_and_generalizability",
        ],
    },
    "TRIPOD": {
        "registry": "EQUATOR",
        "guideline_family": "TRIPOD",
        "applies_to": "prediction_model_or_validation_study",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "source_of_data_and_participants",
            "outcome_definition_and_follow_up",
            "candidate_predictors_and_missing_data",
            "model_specification_or_validation",
            "performance_calibration_and_clinical_utility",
            "interpretation_limitations_and_use_case",
        ],
    },
    "CONSORT": {
        "registry": "EQUATOR",
        "guideline_family": "CONSORT",
        "applies_to": "randomized_trial",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "trial_design_and_registration",
            "participants_interventions_and_outcomes",
            "sample_size_randomization_and_blinding",
            "participant_flow_recruitment_and_follow_up",
            "harms_protocol_deviations_and_limitations",
        ],
    },
    "PRISMA": {
        "registry": "EQUATOR",
        "guideline_family": "PRISMA",
        "applies_to": "systematic_review_or_meta_analysis",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "protocol_and_registration",
            "eligibility_search_and_selection",
            "data_collection_and_risk_of_bias",
            "synthesis_methods_and_certainty",
            "results_limitations_and_implications",
        ],
    },
}

SUPPORTED_REPORTING_GUIDELINE_EXPECTATION_FAMILIES = (
    "STROBE",
    "TRIPOD",
    "CONSORT",
    "PRISMA",
)


_BEFORE_REVIEW_ITEMS: dict[str, tuple[str, ...]] = {
    "STROBE": (
        "strobe_participant_flow",
        "strobe_variables_bias_and_missing_data",
        "strobe_statistical_methods_and_subgroups",
    ),
    "TRIPOD": (
        "tripod_source_participants_and_outcomes",
        "tripod_predictor_model_specification",
        "tripod_model_performance_validation_calibration",
    ),
    "CONSORT": (
        "consort_trial_design_registration_and_flow",
        "consort_randomization_blinding_and_sample_size",
        "consort_outcomes_harms_and_protocol_deviations",
    ),
    "PRISMA": (
        "prisma_protocol_and_registration",
        "prisma_search_selection_flow",
        "prisma_risk_of_bias_and_synthesis_methods",
    ),
}


def build_reporting_guideline_expectation(guideline_family: str) -> dict[str, Any]:
    normalized = str(guideline_family or "").strip().upper()
    expectation = _GUIDELINE_EXPECTATIONS.get(normalized)
    if expectation is None:
        return {
            "authority": "EQUATOR",
            "guideline_family": normalized or "UNKNOWN",
            "applies_to": "unsupported_or_unspecified",
            "checklist_surface": "reporting_guideline_checklist.json",
            "required_domains": [],
            "gates": {
                "before_first_full_draft": {
                    "required_status": "closed",
                    "required_items": [],
                },
                "before_review_handoff": {
                    "required_status": "closed",
                    "required_items": [],
                },
            },
        }
    return {
        "authority": expectation["registry"],
        "guideline_family": expectation["guideline_family"],
        "applies_to": expectation["applies_to"],
        "checklist_surface": "reporting_guideline_checklist.json",
        "required_domains": list(expectation["required_domains"]),
        "gates": {
            "before_first_full_draft": {
                "required_status": "closed",
                "required_items": [
                    "reporting_guideline_family_declared",
                    "guideline_checklist_surface_present",
                    "methods_and_population_accounting_closed",
                ],
            },
            "before_review_handoff": {
                "required_status": "closed",
                "required_items": list(_BEFORE_REVIEW_ITEMS.get(normalized, ())),
            },
        },
    }


def build_guideline_quality_gate_expectation(guideline_family: str) -> dict[str, Any]:
    expectation = build_reporting_guideline_expectation(guideline_family)
    gates = expectation["gates"]
    return {
        "authority": expectation["authority"],
        "guideline_family": expectation["guideline_family"],
        "applies_to": expectation["applies_to"],
        "checklist_surface": expectation["checklist_surface"],
        "required_domains": list(expectation["required_domains"]),
        "gate_relaxation_allowed": False,
        "required_before_accelerated_handoff": True,
        "quality_non_degradation_constraint": {
            "can_parallelize_quality_work": True,
            "can_skip_pre_draft_gate": False,
            "can_skip_review_handoff_gate": False,
            "can_downgrade_blockers_to_advisories": False,
        },
        "gates": {
            "before_first_full_draft": {
                "required_status": gates["before_first_full_draft"]["required_status"],
                "required_items": list(gates["before_first_full_draft"]["required_items"]),
                "blocks": "first_full_draft",
                "owner_surface": "study_charter.paper_quality_contract.structured_reporting_contract",
            },
            "before_review_handoff": {
                "required_status": gates["before_review_handoff"]["required_status"],
                "required_items": list(gates["before_review_handoff"]["required_items"]),
                "blocks": "review_handoff_or_submission_package",
                "owner_surface": "study_charter.paper_quality_contract.structured_reporting_contract",
            },
        },
    }


def guideline_expectations(guideline_family: str) -> dict[str, Any]:
    expectation = build_reporting_guideline_expectation(guideline_family)
    return {
        "registry": expectation["authority"],
        "guideline_family": expectation["guideline_family"],
        "applies_to": expectation["applies_to"],
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": list(expectation["required_domains"]),
    }
