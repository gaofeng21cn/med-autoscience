from __future__ import annotations

import importlib


def test_structured_reporting_checklist_accepts_charter_nested_contract() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")

    checklist = policy.build_structured_reporting_checklist(
        {
            "structured_reporting_contract": {
                "paper_archetype": "phenotype_real_world",
                "clinical_actionability_required": True,
                "methods_completeness": {
                    "study_design": "complete",
                    "cohort": "complete",
                    "variables": "complete",
                    "model": "complete",
                    "validation": "complete",
                    "statistical_analysis": "complete",
                },
                "statistical_reporting": {
                    "summary_format": "complete",
                    "p_values": "complete",
                    "subgroup_tests": "complete",
                },
                "table_figure_claim_map": [
                    {"claim_id": "treatment-gap", "table_figure_refs": ["Table3", "Figure3"]}
                ],
                "clinical_actionability": {
                    "treatment_gap": "complete",
                    "follow_up_or_outcome_relevance": "complete",
                },
                "treatment_gap_reporting": {
                    "explicit_numerator_denominator_rules": "complete",
                    "overall_burden_and_group_rates": "complete",
                    "table_role_consistency": "complete",
                    "figure_legend_uniqueness": "complete",
                    "non_causal_claim_guardrail": "complete",
                    "numerator": "complete",
                    "denominator": "complete",
                    "eligibility": "complete",
                    "time_window": "complete",
                    "medication_data_source": "complete",
                    "interpretation_label_or_guardrail": "complete",
                },
                "phenotype_derivation_reporting": {
                    "assignment_method": "complete",
                    "clinical_domains_or_features": "complete",
                    "assignment_rules_or_algorithm": "complete",
                    "class_count_rationale": "complete",
                    "reproducibility_or_new_patient_assignment": "complete",
                    "analysis_plan_or_prespecification_status": "complete",
                },
                "baseline_characteristics_reporting": {
                    "population_total_n": "complete",
                    "group_columns": "complete",
                    "denominators": "complete",
                    "missingness": "complete",
                    "core_clinical_variables": "complete",
                    "units_or_scale": "complete",
                    "comparison_or_balance_statistic": "complete",
                },
                "data_quality_reporting": {
                    "source_record_checks": "complete",
                    "range_plausibility_checks": "complete",
                    "missingness_by_variable": "complete",
                    "semantic_field_checks": "complete",
                    "cohort_attrition_denominators": "complete",
                    "claim_impact_or_downgrade": "complete",
                },
                "manuscript_voice_reporting": {
                    "results_driven_results_section": "complete",
                    "internal_quality_control_language_absent": "complete",
                    "verified_output_language_absent": "complete",
                    "author_confirmation_notes_absent_from_body": "complete",
                    "defensive_boundary_language_not_repetitive": "complete",
                    "formal_figure_legend_language": "complete",
                    "no_submission_readiness_meta_language": "complete",
                },
            }
        }
    )

    assert checklist["status"] == "clear"
    assert checklist["blockers"] == []
    assert checklist["clinical_actionability"]["status"] == "clear"
    assert checklist["treatment_gap_reporting"]["status"] == "clear"
    assert checklist["phenotype_derivation_reporting"]["status"] == "clear"
    assert checklist["baseline_characteristics_reporting"]["status"] == "clear"
    assert checklist["data_quality_reporting"]["status"] == "clear"
    assert checklist["manuscript_voice_reporting"]["status"] == "clear"


def test_structured_reporting_checklist_blocks_phenotype_reporting_schema_gaps() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")

    checklist = policy.build_structured_reporting_checklist(
        {
            "paper_archetype": "phenotype_real_world",
            "clinical_actionability_required": True,
            "methods_completeness": {
                item: "complete" for item in policy.METHODS_COMPLETENESS_ITEMS
            },
            "statistical_reporting": {
                item: "complete" for item in policy.STATISTICAL_REPORTING_ITEMS
            },
            "table_figure_claim_map": [
                {"claim_id": "phenotype-gap", "table_figure_refs": ["Table1", "Figure2"]}
            ],
            "clinical_actionability": {
                "treatment_gap": "complete",
                "follow_up_or_outcome_relevance": "complete",
            },
            "treatment_gap_reporting": {
                "explicit_numerator_denominator_rules": "complete",
                "overall_burden_and_group_rates": "complete",
                "table_role_consistency": "complete",
                "figure_legend_uniqueness": "complete",
                "non_causal_claim_guardrail": "complete",
                "numerator": "complete",
                "denominator": "complete",
            },
            "phenotype_derivation_reporting": {
                "assignment_method": "complete",
                "clinical_domains_or_features": "complete",
            },
            "baseline_characteristics_reporting": {
                "population_total_n": "complete",
                "group_columns": "complete",
            },
            "data_quality_reporting": {
                "source_record_checks": "complete",
                "range_plausibility_checks": "complete",
            },
        }
    )

    assert checklist["status"] == "blocked"
    assert "phenotype_derivation_reporting_incomplete" in checklist["blockers"]
    assert "treatment_gap_reporting_incomplete" in checklist["blockers"]
    assert "baseline_characteristics_reporting_incomplete" in checklist["blockers"]
    assert "data_quality_reporting_incomplete" in checklist["blockers"]
    assert checklist["phenotype_derivation_reporting"]["missing_items"] == [
        "assignment_rules_or_algorithm",
        "class_count_rationale",
        "reproducibility_or_new_patient_assignment",
        "analysis_plan_or_prespecification_status",
    ]
    assert checklist["treatment_gap_reporting"]["missing_items"] == [
        "eligibility",
        "time_window",
        "medication_data_source",
        "interpretation_label_or_guardrail",
    ]
    assert checklist["baseline_characteristics_reporting"]["missing_items"] == [
        "denominators",
        "missingness",
        "core_clinical_variables",
        "units_or_scale",
        "comparison_or_balance_statistic",
    ]
    assert checklist["data_quality_reporting"]["missing_items"] == [
        "missingness_by_variable",
        "semantic_field_checks",
        "cohort_attrition_denominators",
        "claim_impact_or_downgrade",
    ]


def test_structured_reporting_checklist_keeps_non_phenotype_contract_not_required() -> None:
    policy = importlib.import_module("med_autoscience.policies.medical_reporting_checklist")

    checklist = policy.build_structured_reporting_checklist(
        {
            "paper_archetype": "clinical_observation",
            "manuscript_family": "clinical_observation",
        }
    )

    assert checklist["status"] == "not_required"
    assert checklist["phenotype_derivation_reporting"]["status"] == "not_required"
    assert checklist["treatment_gap_reporting"]["status"] == "not_required"
    assert checklist["baseline_characteristics_reporting"]["status"] == "not_required"
    assert checklist["data_quality_reporting"]["status"] == "not_required"
