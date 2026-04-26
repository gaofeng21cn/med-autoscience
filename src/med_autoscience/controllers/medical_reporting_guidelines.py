from __future__ import annotations

from typing import Any


_GUIDELINE_EXPECTATIONS: dict[str, dict[str, Any]] = {
    "STROBE": {
        "registry": "EQUATOR",
        "guideline_family": "STROBE",
        "base_guideline_family": "STROBE",
        "overlay_guideline": False,
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
        "base_guideline_family": "TRIPOD",
        "overlay_guideline": False,
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
    "TRIPOD+AI": {
        "registry": "EQUATOR",
        "guideline_family": "TRIPOD+AI",
        "base_guideline_family": "TRIPOD",
        "overlay_guideline": False,
        "applies_to": "ai_prediction_model_or_ai_validation_study",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "source_of_data_and_participants",
            "outcome_definition_and_follow_up",
            "candidate_predictors_and_missing_data",
            "ai_model_specification_preprocessing_and_training",
            "performance_calibration_fairness_and_clinical_utility",
            "human_ai_use_case_explainability_and_limitations",
        ],
    },
    "CONSORT": {
        "registry": "EQUATOR",
        "guideline_family": "CONSORT",
        "base_guideline_family": "CONSORT",
        "overlay_guideline": False,
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
    "CONSORT-AI": {
        "registry": "EQUATOR",
        "guideline_family": "CONSORT-AI",
        "base_guideline_family": "CONSORT",
        "overlay_guideline": False,
        "applies_to": "ai_intervention_randomized_trial",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "trial_design_registration_randomization_and_flow",
            "ai_intervention_versioning_and_integration",
            "human_ai_interaction_training_and_usability",
            "outcomes_harms_failure_modes_and_protocol_deviations",
            "deployment_context_limitations_and_generalizability",
        ],
    },
    "PRISMA": {
        "registry": "EQUATOR",
        "guideline_family": "PRISMA",
        "base_guideline_family": "PRISMA",
        "overlay_guideline": False,
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
    "RECORD": {
        "registry": "EQUATOR",
        "guideline_family": "RECORD",
        "base_guideline_family": "STROBE",
        "overlay_guideline": True,
        "applies_to": "real_world_data_or_routinely_collected_health_data_study",
        "checklist_surface_required": True,
        "quality_gate_timing": "before_first_full_draft_and_before_submission_gate",
        "required_domains": [
            "real_world_data_source_and_linkage",
            "coding_algorithms_and_validation",
            "data_cleaning_missingness_and_denominator_accounting",
            "population_flow_reproducibility_and_bias",
            "privacy_governance_and_reuse_limitations",
        ],
    },
}

SUPPORTED_REPORTING_GUIDELINE_EXPECTATION_FAMILIES = (
    "STROBE",
    "TRIPOD",
    "TRIPOD+AI",
    "CONSORT",
    "CONSORT-AI",
    "PRISMA",
    "RECORD",
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
    "TRIPOD+AI": (
        "tripod_ai_source_participants_and_outcomes",
        "tripod_ai_model_specification_and_training",
        "tripod_ai_performance_calibration_fairness_and_clinical_utility",
    ),
    "CONSORT": (
        "consort_trial_design_registration_and_flow",
        "consort_randomization_blinding_and_sample_size",
        "consort_outcomes_harms_and_protocol_deviations",
    ),
    "CONSORT-AI": (
        "consort_ai_trial_design_registration_and_flow",
        "consort_ai_intervention_versioning_and_integration",
        "consort_ai_human_ai_interaction_outcomes_and_harms",
    ),
    "PRISMA": (
        "prisma_protocol_and_registration",
        "prisma_search_selection_flow",
        "prisma_risk_of_bias_and_synthesis_methods",
    ),
    "RECORD": (
        "record_data_source_linkage_and_cleaning",
        "record_code_lists_algorithms_and_validation",
        "record_denominator_reproducibility_privacy_and_limitations",
    ),
}


def build_reporting_guideline_expectation(guideline_family: str) -> dict[str, Any]:
    normalized = str(guideline_family or "").strip().upper()
    expectation = _GUIDELINE_EXPECTATIONS.get(normalized)
    if expectation is None:
        return {
            "authority": "EQUATOR",
            "guideline_family": normalized or "UNKNOWN",
            "base_guideline_family": normalized or "UNKNOWN",
            "overlay_guideline": False,
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
        "base_guideline_family": expectation["base_guideline_family"],
        "overlay_guideline": bool(expectation["overlay_guideline"]),
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


def build_evidence_review_ledger_contract() -> dict[str, Any]:
    return {
        "evidence_ledger_surface": "paper/evidence_ledger.json",
        "review_ledger_surface": "paper/review_ledger.json",
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
        "required_evidence_status": "closed",
        "required_review_status": "closed",
        "blocks_accelerated_handoff_when_missing": True,
    }


def build_guideline_quality_gate_expectation(guideline_family: str) -> dict[str, Any]:
    expectation = build_reporting_guideline_expectation(guideline_family)
    gates = expectation["gates"]
    return {
        "authority": expectation["authority"],
        "guideline_family": expectation["guideline_family"],
        "base_guideline_family": expectation["base_guideline_family"],
        "overlay_guideline": bool(expectation["overlay_guideline"]),
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
        "evidence_review_ledger_contract": build_evidence_review_ledger_contract(),
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
