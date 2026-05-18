from __future__ import annotations

import importlib


def test_structured_reporting_checklist_blocks_prediction_model_external_validation_quality_gaps() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")

    def complete_section(items: tuple[str, ...]) -> dict[str, str]:
        return {item: "complete" for item in items}

    checklist = policy.build_structured_reporting_checklist(
        {
            "manuscript_family": "prediction_model",
            "endpoint_type": "time_to_event",
            "external_validation_dataset": "NHANES",
            "methods_completeness": complete_section(policy.METHODS_COMPLETENESS_ITEMS),
            "statistical_reporting": complete_section(policy.STATISTICAL_REPORTING_ITEMS),
            "table_figure_claim_map": [
                {"claim_id": "external-validation", "table_figure_refs": ["T2", "F3"]}
            ],
            "prediction_methods": complete_section(policy.PREDICTION_MODEL_METHODS_ITEMS),
            "prediction_model_reproducibility": {
                "model_type_or_algorithm": "complete",
                "penalty_or_regularization_form": "complete",
            },
            "variable_harmonization": {
                "unit_system_per_predictor": "complete",
            },
            "time_to_event_prediction_reporting": complete_section(
                policy.TIME_TO_EVENT_PREDICTION_ITEMS
            ),
            "external_validation_reporting": {
                "external_validation_cohort_definition": "complete",
                "observed_event_rate_and_denominators": "complete",
            },
            "decision_curve_clinical_utility": complete_section(
                policy.DECISION_CURVE_CLINICAL_UTILITY_ITEMS
            ),
            "prediction_performance_reporting": complete_section(
                policy.PREDICTION_PERFORMANCE_REPORTING_ITEMS
            ),
            "validation_uncertainty_reporting": {
                "c_index_confidence_interval": "complete",
            },
            "prediction_display_reporting": {
                "baseline_characteristics_table": "complete",
            },
            "survey_design_reporting": {
                "unweighted_analysis_label": "complete",
            },
            "manuscript_voice_reporting": {
                "results_driven_results_section": "complete",
            },
            "baseline_balance_reporting": complete_section(policy.BASELINE_BALANCE_REPORTING_ITEMS),
        }
    )

    assert checklist["status"] == "blocked"
    assert "prediction_model_reproducibility_incomplete" in checklist["blockers"]
    assert "variable_harmonization_incomplete" in checklist["blockers"]
    assert "external_validation_reporting_incomplete" in checklist["blockers"]
    assert "validation_uncertainty_reporting_incomplete" in checklist["blockers"]
    assert "prediction_display_reporting_incomplete" in checklist["blockers"]
    assert "survey_design_reporting_incomplete" in checklist["blockers"]
    assert "manuscript_voice_reporting_incomplete" in checklist["blockers"]
    assert (
        "baseline_survival_or_absolute_risk_extraction"
        in checklist["prediction_model_reproducibility"]["missing_items"]
    )
    assert "cross_cohort_unit_conversion" in checklist["variable_harmonization"]["missing_items"]
    assert "case_mix_and_covariate_support" in checklist["external_validation_reporting"]["missing_items"]
    assert (
        "observed_expected_ratio_confidence_interval"
        in checklist["validation_uncertainty_reporting"]["missing_items"]
    )
    assert "calibration_curve_with_uncertainty" in checklist["prediction_display_reporting"]["missing_items"]
    assert "weighting_policy" in checklist["survey_design_reporting"]["missing_items"]
    assert "internal_quality_control_language_absent" in checklist["manuscript_voice_reporting"]["missing_items"]
