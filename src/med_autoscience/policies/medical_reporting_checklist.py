from __future__ import annotations

from typing import Any

METHODS_COMPLETENESS_ITEMS = (
    "study_design",
    "cohort",
    "variables",
    "model",
    "validation",
    "statistical_analysis",
)
STATISTICAL_REPORTING_ITEMS = ("summary_format", "p_values", "subgroup_tests")
CLINICAL_ACTIONABILITY_ITEMS = ("treatment_gap", "follow_up_or_outcome_relevance")
PREDICTION_MODEL_METHODS_ITEMS = (
    "data_source_years",
    "inclusion_exclusion",
    "endpoint_ascertainment",
    "follow_up_start",
    "censoring_rules",
    "missing_data_handling",
    "variable_coding",
    "model_tuning",
    "center_effect_handling",
)
PREDICTION_MODEL_REPRODUCIBILITY_ITEMS = (
    "model_type_or_algorithm",
    "penalty_or_regularization_form",
    "tuning_parameter_selection",
    "baseline_survival_or_absolute_risk_extraction",
    "predictor_coding_and_reference_levels",
    "continuous_predictor_transformations",
    "software_and_source_code_environment",
)
VARIABLE_HARMONIZATION_ITEMS = (
    "unit_system_per_predictor",
    "cross_cohort_unit_conversion",
    "range_plausibility_by_cohort",
    "harmonization_anomaly_sensitivity",
    "unit_standardized_model_application_or_sensitivity",
)
TIME_TO_EVENT_PREDICTION_ITEMS = (
    "proportional_hazards_assessment",
    "nonlinearity_assessment",
    "competing_event_screen",
    "absolute_risk_estimator",
    "calibration_time_horizon",
)
EXTERNAL_VALIDATION_REPORTING_ITEMS = (
    "external_validation_cohort_definition",
    "transport_without_refit_or_recalibration",
    "case_mix_and_covariate_support",
    "risk_group_occupancy",
    "observed_event_rate_and_denominators",
    "calibration_update_policy",
)
DECISION_CURVE_CLINICAL_UTILITY_ITEMS = (
    "dca_threshold_range",
    "linked_clinical_action_scenario",
    "threshold_rationale",
    "implementation_boundary",
)
PREDICTION_PERFORMANCE_REPORTING_ITEMS = (
    "validation_n",
    "event_count",
    "c_index_with_ci",
    "calibration_metric",
    "high_risk_predicted_observed",
    "decision_curve_threshold_range",
)
VALIDATION_UNCERTAINTY_ITEMS = (
    "c_index_confidence_interval",
    "calibration_intercept_slope_confidence_interval",
    "observed_expected_ratio_confidence_interval",
    "brier_score_or_uncertainty_interval",
    "calibration_curve_or_grouped_calibration_interval",
    "bootstrap_or_resampling_method",
)
PREDICTION_DISPLAY_REPORTING_ITEMS = (
    "cohort_flow_diagram",
    "baseline_characteristics_table",
    "performance_metrics_table",
    "main_text_table_rendering_in_submission_package",
    "calibration_curve_with_uncertainty",
    "risk_distribution_or_support_overlap",
    "decision_curve_not_main_display_without_verified_net_benefit",
    "figure_legibility_and_non_overlap",
)
SURVEY_DESIGN_REPORTING_ITEMS = (
    "weighting_policy",
    "strata_cluster_handling",
    "unweighted_analysis_label",
    "population_inference_boundary",
)
MANUSCRIPT_VOICE_REPORTING_ITEMS = (
    "results_driven_results_section",
    "internal_quality_control_language_absent",
    "verified_output_language_absent",
    "author_confirmation_notes_absent_from_body",
    "invalid_analysis_history_absent_from_main_story",
    "defensive_boundary_language_not_repetitive",
    "formal_figure_legend_language",
    "no_submission_readiness_meta_language",
)
BASELINE_BALANCE_REPORTING_ITEMS = (
    "variable_level_missingness",
    "standardized_mean_differences",
    "denominator_rules",
    "variable_definition_anomalies",
)
COMPETING_RISK_REPORTING_ITEMS = (
    "target_event_definition",
    "competing_event_definition",
    "non_target_death_handling",
    "cumulative_incidence_or_aalen_johansen",
    "fine_gray_or_competing_risk_sensitivity",
    "absolute_risk_calibration_interpretation",
)
TREATMENT_GAP_REPORTING_ITEMS = (
    "explicit_numerator_denominator_rules",
    "overall_burden_and_group_rates",
    "table_role_consistency",
    "figure_legend_uniqueness",
    "non_causal_claim_guardrail",
    "numerator",
    "denominator",
    "eligibility",
    "time_window",
    "medication_data_source",
    "interpretation_label_or_guardrail",
)
PHENOTYPE_DERIVATION_REPORTING_ITEMS = (
    "assignment_method",
    "clinical_domains_or_features",
    "assignment_rules_or_algorithm",
    "class_count_rationale",
    "reproducibility_or_new_patient_assignment",
    "analysis_plan_or_prespecification_status",
)
BASELINE_CHARACTERISTICS_REPORTING_ITEMS = (
    "population_total_n",
    "group_columns",
    "denominators",
    "missingness",
    "core_clinical_variables",
    "units_or_scale",
    "comparison_or_balance_statistic",
)
DATA_QUALITY_REPORTING_ITEMS = (
    "source_record_checks",
    "range_plausibility_checks",
    "missingness_by_variable",
    "semantic_field_checks",
    "cohort_attrition_denominators",
    "claim_impact_or_downgrade",
)
PHENOTYPE_ARCHETYPE_TOKENS = (
    "phenotype",
    "subtype",
    "clinical_subtype",
    "cluster",
    "real_world",
    "treatment_gap",
    "treatment-gap",
    "treatment gap",
)

REPORTING_CHECKLIST_BLOCKER_KEYS = frozenset(
    {
        "methods_completeness_incomplete",
        "statistical_reporting_incomplete",
        "table_figure_claim_map_missing_or_incomplete",
        "clinical_actionability_incomplete",
        "prediction_model_methods_reporting_incomplete",
        "prediction_model_reproducibility_incomplete",
        "variable_harmonization_incomplete",
        "time_to_event_prediction_reporting_incomplete",
        "external_validation_reporting_incomplete",
        "decision_curve_clinical_utility_incomplete",
        "prediction_performance_reporting_incomplete",
        "validation_uncertainty_reporting_incomplete",
        "prediction_display_reporting_incomplete",
        "survey_design_reporting_incomplete",
        "manuscript_voice_reporting_incomplete",
        "baseline_balance_reporting_incomplete",
        "competing_risk_reporting_incomplete",
        "treatment_gap_reporting_incomplete",
        "phenotype_derivation_reporting_incomplete",
        "baseline_characteristics_reporting_incomplete",
        "data_quality_reporting_incomplete",
    }
)

STRUCTURED_REPORTING_SECTION_ITEMS: dict[str, tuple[str, ...]] = {
    "methods_completeness": METHODS_COMPLETENESS_ITEMS,
    "statistical_reporting": STATISTICAL_REPORTING_ITEMS,
    "clinical_actionability": CLINICAL_ACTIONABILITY_ITEMS,
    "prediction_methods": PREDICTION_MODEL_METHODS_ITEMS,
    "prediction_model_reproducibility": PREDICTION_MODEL_REPRODUCIBILITY_ITEMS,
    "variable_harmonization": VARIABLE_HARMONIZATION_ITEMS,
    "time_to_event_prediction_reporting": TIME_TO_EVENT_PREDICTION_ITEMS,
    "external_validation_reporting": EXTERNAL_VALIDATION_REPORTING_ITEMS,
    "decision_curve_clinical_utility": DECISION_CURVE_CLINICAL_UTILITY_ITEMS,
    "prediction_performance_reporting": PREDICTION_PERFORMANCE_REPORTING_ITEMS,
    "validation_uncertainty_reporting": VALIDATION_UNCERTAINTY_ITEMS,
    "prediction_display_reporting": PREDICTION_DISPLAY_REPORTING_ITEMS,
    "survey_design_reporting": SURVEY_DESIGN_REPORTING_ITEMS,
    "manuscript_voice_reporting": MANUSCRIPT_VOICE_REPORTING_ITEMS,
    "baseline_balance_reporting": BASELINE_BALANCE_REPORTING_ITEMS,
    "competing_risk_reporting": COMPETING_RISK_REPORTING_ITEMS,
    "treatment_gap_reporting": TREATMENT_GAP_REPORTING_ITEMS,
    "phenotype_derivation_reporting": PHENOTYPE_DERIVATION_REPORTING_ITEMS,
    "baseline_characteristics_reporting": BASELINE_CHARACTERISTICS_REPORTING_ITEMS,
    "data_quality_reporting": DATA_QUALITY_REPORTING_ITEMS,
}

_CLOSED_REPORTING_STATUSES = frozenset(
    {
        "closed",
        "complete",
        "clear",
        "present",
        "reported_as_limitation",
        "not_applicable_with_rationale",
    }
)

_REPORTING_GUIDELINE_DOMAIN_SECTION_ITEMS: dict[str, dict[str, tuple[str, ...] | None]] = {
    "source_of_data_and_participants": {
        "methods_completeness": ("study_design", "cohort"),
        "prediction_methods": ("data_source_years", "inclusion_exclusion"),
        "prediction_display_reporting": ("cohort_flow_diagram", "baseline_characteristics_table"),
        "baseline_balance_reporting": (
            "variable_level_missingness",
            "standardized_mean_differences",
            "denominator_rules",
        ),
        "survey_design_reporting": ("weighting_policy", "strata_cluster_handling"),
    },
    "outcome_definition_and_follow_up": {
        "methods_completeness": ("statistical_analysis",),
        "prediction_methods": ("endpoint_ascertainment", "follow_up_start", "censoring_rules"),
        "time_to_event_prediction_reporting": ("absolute_risk_estimator", "calibration_time_horizon"),
    },
    "candidate_predictors_and_missing_data": {
        "methods_completeness": ("variables",),
        "prediction_methods": ("missing_data_handling", "variable_coding"),
        "variable_harmonization": None,
        "baseline_balance_reporting": ("variable_definition_anomalies",),
    },
    "model_specification_or_validation": {
        "methods_completeness": ("model", "validation"),
        "prediction_methods": ("model_tuning", "center_effect_handling"),
        "prediction_model_reproducibility": None,
        "time_to_event_prediction_reporting": (
            "proportional_hazards_assessment",
            "nonlinearity_assessment",
            "competing_event_screen",
        ),
        "external_validation_reporting": (
            "external_validation_cohort_definition",
            "transport_without_refit_or_recalibration",
            "calibration_update_policy",
        ),
    },
    "performance_calibration_and_clinical_utility": {
        "statistical_reporting": None,
        "external_validation_reporting": (
            "case_mix_and_covariate_support",
            "risk_group_occupancy",
            "observed_event_rate_and_denominators",
        ),
        "decision_curve_clinical_utility": None,
        "prediction_performance_reporting": None,
        "validation_uncertainty_reporting": None,
        "prediction_display_reporting": (
            "performance_metrics_table",
            "main_text_table_rendering_in_submission_package",
            "calibration_curve_with_uncertainty",
            "risk_distribution_or_support_overlap",
            "decision_curve_not_main_display_without_verified_net_benefit",
            "figure_legibility_and_non_overlap",
        ),
    },
    "interpretation_limitations_and_use_case": {
        "survey_design_reporting": ("unweighted_analysis_label", "population_inference_boundary"),
        "manuscript_voice_reporting": None,
    },
}


def _required_status_map(items: tuple[str, ...], *, status: str = "required_before_first_full_draft") -> dict[str, dict[str, str]]:
    return {item: {"status": status} for item in items}


def build_default_structured_reporting_contract(
    *,
    study_archetype: str | None = None,
    paper_archetype: str | None = None,
    manuscript_family: str | None = None,
    endpoint_type: str | None = None,
    external_validation_dataset: str | None = None,
    cohort_name: str | None = None,
) -> dict[str, Any]:
    contract: dict[str, Any] = {
        "methods_completeness": _required_status_map(METHODS_COMPLETENESS_ITEMS),
        "statistical_reporting": _required_status_map(STATISTICAL_REPORTING_ITEMS),
        "table_figure_claim_map_required": True,
        "table_figure_claim_map": [],
    }
    for key, value in (
        ("study_archetype", study_archetype),
        ("paper_archetype", paper_archetype),
        ("manuscript_family", manuscript_family),
        ("endpoint_type", endpoint_type),
        ("external_validation_dataset", external_validation_dataset),
        ("cohort_name", cohort_name),
    ):
        if value:
            contract[key] = value
    if _prediction_model_required(contract):
        contract.update(
            {
                "prediction_model_reporting_required": True,
                "prediction_methods": _required_status_map(PREDICTION_MODEL_METHODS_ITEMS),
                "prediction_model_reproducibility": _required_status_map(
                    PREDICTION_MODEL_REPRODUCIBILITY_ITEMS
                ),
                "variable_harmonization": _required_status_map(VARIABLE_HARMONIZATION_ITEMS),
                "external_validation_reporting": _required_status_map(
                    EXTERNAL_VALIDATION_REPORTING_ITEMS
                ),
                "decision_curve_clinical_utility": _required_status_map(
                    DECISION_CURVE_CLINICAL_UTILITY_ITEMS
                ),
                "prediction_performance_reporting": _required_status_map(
                    PREDICTION_PERFORMANCE_REPORTING_ITEMS
                ),
                "validation_uncertainty_reporting": _required_status_map(
                    VALIDATION_UNCERTAINTY_ITEMS
                ),
                "prediction_display_reporting": _required_status_map(
                    PREDICTION_DISPLAY_REPORTING_ITEMS
                ),
                "manuscript_voice_reporting_required": True,
                "manuscript_voice_reporting": _required_status_map(
                    MANUSCRIPT_VOICE_REPORTING_ITEMS
                ),
                "baseline_balance_reporting": _required_status_map(BASELINE_BALANCE_REPORTING_ITEMS),
            }
        )
    if _survey_design_reporting_required(contract):
        contract["survey_design_reporting_required"] = True
        contract["survey_design_reporting"] = _required_status_map(SURVEY_DESIGN_REPORTING_ITEMS)
    if _time_to_event_prediction_required(contract):
        contract["time_to_event_prediction_reporting"] = _required_status_map(
            TIME_TO_EVENT_PREDICTION_ITEMS
        )
        contract["competing_risk_reporting_required"] = "when_non_target_deaths_present"
        contract["competing_risk_reporting"] = _required_status_map(
            COMPETING_RISK_REPORTING_ITEMS,
            status="required_when_non_target_deaths_present",
        )
    if _phenotype_actionability_required(contract):
        contract.update(
            {
                "clinical_actionability_required": True,
                "clinical_actionability": _required_status_map(CLINICAL_ACTIONABILITY_ITEMS),
                "treatment_gap_reporting": _required_status_map(TREATMENT_GAP_REPORTING_ITEMS),
                "phenotype_derivation_reporting": _required_status_map(
                    PHENOTYPE_DERIVATION_REPORTING_ITEMS
                ),
                "baseline_characteristics_reporting": _required_status_map(
                    BASELINE_CHARACTERISTICS_REPORTING_ITEMS
                ),
                "data_quality_reporting": _required_status_map(DATA_QUALITY_REPORTING_ITEMS),
            }
        )
    return contract


def _truthy_mapping_item(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if isinstance(value, dict):
        status = str(value.get("status") or "").strip().lower()
        return status in {"complete", "clear", "present", "closed"} or value.get("present") is True
    if isinstance(value, str):
        return value.strip().lower() in {"complete", "clear", "present", "closed", "yes", "true"}
    return value is True


def _closed_status(value: object) -> bool:
    if isinstance(value, dict):
        raw_status = value.get("status")
    else:
        raw_status = value
    return str(raw_status or "").strip().lower() in _CLOSED_REPORTING_STATUSES


def _closure_evidence_present(item: dict[str, Any]) -> bool:
    evidence = item.get("evidence") or item.get("evidence_refs") or item.get("source_paths")
    if isinstance(evidence, list):
        return any(str(ref or "").strip() for ref in evidence)
    return bool(str(evidence or "").strip())


def _closed_reporting_guideline_domains(reporting_closure: object) -> tuple[dict[str, Any], ...]:
    if not isinstance(reporting_closure, dict) or not _closed_status(reporting_closure):
        return ()
    domains = reporting_closure.get("domains")
    if not isinstance(domains, list):
        return ()
    closed_domains: list[dict[str, Any]] = []
    for item in domains:
        if not isinstance(item, dict):
            continue
        domain_id = str(item.get("domain_id") or item.get("id") or "").strip()
        if not domain_id or domain_id not in _REPORTING_GUIDELINE_DOMAIN_SECTION_ITEMS:
            continue
        if not _closed_status(item) or not _closure_evidence_present(item):
            continue
        closed_domains.append(item)
    return tuple(closed_domains)


def _set_closed_reporting_items(
    contract: dict[str, Any],
    section_key: str,
    item_keys: tuple[str, ...],
    *,
    evidence_refs: list[str],
) -> None:
    section = contract.get(section_key)
    if not isinstance(section, dict):
        section = {}
    updated_section = dict(section)
    for item_key in item_keys:
        updated_section[item_key] = {
            "status": "closed",
            "evidence_refs": list(evidence_refs),
            "closure_source": "reporting_guideline_checklist",
        }
    contract[section_key] = updated_section


def _apply_reporting_closure(contract: dict[str, Any], reporting_closure: object) -> tuple[dict[str, Any], dict[str, Any]]:
    merged = dict(contract)
    consumed_domains: list[str] = []
    for domain in _closed_reporting_guideline_domains(reporting_closure):
        domain_id = str(domain.get("domain_id") or domain.get("id") or "").strip()
        section_map = _REPORTING_GUIDELINE_DOMAIN_SECTION_ITEMS[domain_id]
        evidence_refs = [str(ref).strip() for ref in domain.get("evidence") or [] if str(ref).strip()]
        for section_key, item_keys in section_map.items():
            section_items = STRUCTURED_REPORTING_SECTION_ITEMS.get(section_key, ())
            if not section_items:
                continue
            _set_closed_reporting_items(
                merged,
                section_key,
                section_items if item_keys is None else item_keys,
                evidence_refs=evidence_refs,
            )
        consumed_domains.append(domain_id)
    return merged, {
        "status": "consumed" if consumed_domains else "not_consumed",
        "consumed_domain_ids": consumed_domains,
    }


def _standalone_claim_map_items(payload: object) -> list[dict[str, Any]] | None:
    raw_items: object
    if isinstance(payload, dict):
        raw_items = payload.get("items")
        if not isinstance(raw_items, list):
            raw_items = payload.get("claims")
    else:
        raw_items = payload
    if not isinstance(raw_items, list):
        return None
    return [dict(item) for item in raw_items if isinstance(item, dict)]


def _section_status(payload: object, required_items: tuple[str, ...]) -> dict[str, Any]:
    section = payload if isinstance(payload, dict) else {}
    missing_items = [item for item in required_items if not _truthy_mapping_item(section, item)]
    return {
        "status": "blocked" if missing_items else "clear",
        "required_items": list(required_items),
        "missing_items": missing_items,
    }


def _not_required_section(required_items: tuple[str, ...]) -> dict[str, Any]:
    return {
        "status": "not_required",
        "required_items": list(required_items),
        "missing_items": [],
    }


def _claim_map_status(payload: object) -> dict[str, Any]:
    items = payload if isinstance(payload, list) else []
    complete_items: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        claim = str(item.get("claim") or item.get("claim_id") or "").strip()
        displays = (
            item.get("displays")
            or item.get("tables_figures")
            or item.get("table_figure_refs")
            or item.get("display_bindings")
        )
        if claim and isinstance(displays, list) and displays:
            complete_items.append(item)
    return {
        "status": "clear" if complete_items else "blocked",
        "mapped_claim_count": len(complete_items),
        "missing_items": [] if complete_items else ["claim_to_table_or_figure_links"],
    }


def _phenotype_actionability_required(contract: dict[str, Any]) -> bool:
    explicit = contract.get("clinical_actionability_required")
    if explicit is not None:
        return explicit is True
    surfaces = (
        contract.get("paper_archetype"),
        contract.get("study_archetype"),
        contract.get("manuscript_family"),
        contract.get("endpoint_type"),
    )
    text = " ".join(str(item or "").strip().lower() for item in surfaces)
    return any(token in text for token in PHENOTYPE_ARCHETYPE_TOKENS)


def _prediction_model_required(contract: dict[str, Any]) -> bool:
    explicit = contract.get("prediction_model_reporting_required")
    if explicit is not None:
        return explicit is True or str(explicit).strip().lower() in {"true", "yes", "required"}
    surfaces = (
        contract.get("paper_archetype"),
        contract.get("study_archetype"),
        contract.get("manuscript_family"),
        contract.get("reporting_guideline_family"),
    )
    text = " ".join(str(item or "").strip().lower() for item in surfaces)
    return "prediction_model" in text or "prediction model" in text or "tripod" in text


def _survey_design_reporting_required(contract: dict[str, Any]) -> bool:
    explicit = contract.get("survey_design_reporting_required")
    if explicit is not None:
        return explicit is True or str(explicit).strip().lower() in {"true", "yes", "required"}
    surfaces = (
        contract.get("paper_archetype"),
        contract.get("study_archetype"),
        contract.get("manuscript_family"),
        contract.get("external_validation_dataset"),
        contract.get("cohort_name"),
    )
    text = " ".join(str(item or "").strip().lower() for item in surfaces)
    return "nhanes" in text or "survey" in text or "complex sample" in text


def _manuscript_voice_required(contract: dict[str, Any]) -> bool:
    explicit = contract.get("manuscript_voice_reporting_required")
    if explicit is not None:
        return explicit is True or str(explicit).strip().lower() in {"true", "yes", "required"}
    return _prediction_model_required(contract) or _phenotype_actionability_required(contract)


def _time_to_event_prediction_required(contract: dict[str, Any]) -> bool:
    if not _prediction_model_required(contract):
        return False
    explicit = contract.get("time_to_event_prediction_reporting_required")
    if explicit is not None:
        return explicit is True or str(explicit).strip().lower() in {"true", "yes", "required"}
    endpoint_type = str(contract.get("endpoint_type") or "").strip().lower()
    return endpoint_type in {"time_to_event", "survival", "time-to-event"}


def _competing_risk_reporting_required(contract: dict[str, Any]) -> bool:
    explicit = contract.get("competing_risk_reporting_required")
    if explicit is not None:
        return explicit is True or str(explicit).strip().lower() in {"true", "yes", "required", "always"}
    if _truthy_mapping_item(contract, "competing_risk_events_present"):
        return True
    competing_risk_reporting = contract.get("competing_risk_reporting")
    return isinstance(competing_risk_reporting, dict) and bool(competing_risk_reporting)


def _structured_contract_source(contract: dict[str, Any]) -> dict[str, Any]:
    nested = contract.get("structured_reporting_contract")
    if isinstance(nested, dict):
        merged = dict(contract)
        merged.update(nested)
        return merged
    return contract


def build_structured_reporting_checklist(
    contract: dict[str, Any],
    *,
    reporting_closure: object | None = None,
    table_figure_claim_map: object | None = None,
) -> dict[str, Any]:
    contract = _structured_contract_source(contract)
    reporting_closure_consumed = {"status": "not_provided", "consumed_domain_ids": []}
    if reporting_closure is not None:
        contract, reporting_closure_consumed = _apply_reporting_closure(contract, reporting_closure)
    table_figure_claim_map_consumed = {"status": "not_provided", "mapped_claim_count": 0}
    standalone_claim_items = _standalone_claim_map_items(table_figure_claim_map)
    if standalone_claim_items is not None:
        contract = dict(contract)
        contract["table_figure_claim_map"] = standalone_claim_items
        table_figure_claim_map_consumed = {
            "status": "consumed",
            "mapped_claim_count": _claim_map_status(standalone_claim_items)["mapped_claim_count"],
        }
    actionability_required = _phenotype_actionability_required(contract)
    prediction_required = _prediction_model_required(contract)
    time_to_event_prediction_required = _time_to_event_prediction_required(contract)
    competing_risk_required = _competing_risk_reporting_required(contract)
    survey_design_required = _survey_design_reporting_required(contract)
    manuscript_voice_required = _manuscript_voice_required(contract)
    explicit_structured_contract = any(
        key in contract
        for key in (
            "methods_completeness",
            "statistical_reporting",
            "table_figure_claim_map",
            "clinical_actionability",
            "treatment_gap_reporting",
            "prediction_methods",
            "prediction_model_reproducibility",
            "variable_harmonization",
            "time_to_event_prediction_reporting",
            "external_validation_reporting",
            "decision_curve_clinical_utility",
            "prediction_performance_reporting",
            "validation_uncertainty_reporting",
            "prediction_display_reporting",
            "survey_design_reporting",
            "manuscript_voice_reporting",
            "baseline_balance_reporting",
            "competing_risk_reporting",
            "phenotype_derivation_reporting",
            "baseline_characteristics_reporting",
            "data_quality_reporting",
        )
    )
    if not actionability_required and not prediction_required and not explicit_structured_contract:
        return {
            "status": "not_required",
            "blockers": [],
            "reporting_guideline_closure_consumed": reporting_closure_consumed,
            "table_figure_claim_map_consumed": table_figure_claim_map_consumed,
            "methods_completeness": _not_required_section(METHODS_COMPLETENESS_ITEMS),
            "statistical_reporting": _not_required_section(STATISTICAL_REPORTING_ITEMS),
            "table_figure_claim_map": {
                "status": "not_required",
                "mapped_claim_count": 0,
                "missing_items": [],
            },
            "clinical_actionability": _not_required_section(CLINICAL_ACTIONABILITY_ITEMS),
            "prediction_methods": _not_required_section(PREDICTION_MODEL_METHODS_ITEMS),
            "prediction_model_reproducibility": _not_required_section(
                PREDICTION_MODEL_REPRODUCIBILITY_ITEMS
            ),
            "variable_harmonization": _not_required_section(VARIABLE_HARMONIZATION_ITEMS),
            "time_to_event_prediction_reporting": _not_required_section(TIME_TO_EVENT_PREDICTION_ITEMS),
            "external_validation_reporting": _not_required_section(EXTERNAL_VALIDATION_REPORTING_ITEMS),
            "decision_curve_clinical_utility": _not_required_section(DECISION_CURVE_CLINICAL_UTILITY_ITEMS),
            "prediction_performance_reporting": _not_required_section(PREDICTION_PERFORMANCE_REPORTING_ITEMS),
            "validation_uncertainty_reporting": _not_required_section(VALIDATION_UNCERTAINTY_ITEMS),
            "prediction_display_reporting": _not_required_section(PREDICTION_DISPLAY_REPORTING_ITEMS),
            "survey_design_reporting": _not_required_section(SURVEY_DESIGN_REPORTING_ITEMS),
            "manuscript_voice_reporting": _not_required_section(MANUSCRIPT_VOICE_REPORTING_ITEMS),
            "baseline_balance_reporting": _not_required_section(BASELINE_BALANCE_REPORTING_ITEMS),
            "competing_risk_reporting": _not_required_section(COMPETING_RISK_REPORTING_ITEMS),
            "treatment_gap_reporting": _not_required_section(TREATMENT_GAP_REPORTING_ITEMS),
            "phenotype_derivation_reporting": _not_required_section(
                PHENOTYPE_DERIVATION_REPORTING_ITEMS
            ),
            "baseline_characteristics_reporting": _not_required_section(
                BASELINE_CHARACTERISTICS_REPORTING_ITEMS
            ),
            "data_quality_reporting": _not_required_section(DATA_QUALITY_REPORTING_ITEMS),
        }
    methods = _section_status(contract.get("methods_completeness"), METHODS_COMPLETENESS_ITEMS)
    statistics = _section_status(contract.get("statistical_reporting"), STATISTICAL_REPORTING_ITEMS)
    claim_map = _claim_map_status(contract.get("table_figure_claim_map"))
    actionability = (
        _section_status(contract.get("clinical_actionability"), CLINICAL_ACTIONABILITY_ITEMS)
        if actionability_required
        else {
            "status": "not_required",
            "required_items": list(CLINICAL_ACTIONABILITY_ITEMS),
            "missing_items": [],
        }
    )
    prediction_methods = (
        _section_status(contract.get("prediction_methods"), PREDICTION_MODEL_METHODS_ITEMS)
        if prediction_required
        else _not_required_section(PREDICTION_MODEL_METHODS_ITEMS)
    )
    prediction_model_reproducibility = (
        _section_status(
            contract.get("prediction_model_reproducibility"),
            PREDICTION_MODEL_REPRODUCIBILITY_ITEMS,
        )
        if prediction_required
        else _not_required_section(PREDICTION_MODEL_REPRODUCIBILITY_ITEMS)
    )
    variable_harmonization = (
        _section_status(contract.get("variable_harmonization"), VARIABLE_HARMONIZATION_ITEMS)
        if prediction_required
        else _not_required_section(VARIABLE_HARMONIZATION_ITEMS)
    )
    time_to_event_prediction = (
        _section_status(contract.get("time_to_event_prediction_reporting"), TIME_TO_EVENT_PREDICTION_ITEMS)
        if time_to_event_prediction_required
        else _not_required_section(TIME_TO_EVENT_PREDICTION_ITEMS)
    )
    external_validation = (
        _section_status(contract.get("external_validation_reporting"), EXTERNAL_VALIDATION_REPORTING_ITEMS)
        if prediction_required
        else _not_required_section(EXTERNAL_VALIDATION_REPORTING_ITEMS)
    )
    decision_curve_clinical_utility = (
        _section_status(contract.get("decision_curve_clinical_utility"), DECISION_CURVE_CLINICAL_UTILITY_ITEMS)
        if prediction_required
        else _not_required_section(DECISION_CURVE_CLINICAL_UTILITY_ITEMS)
    )
    prediction_performance = (
        _section_status(contract.get("prediction_performance_reporting"), PREDICTION_PERFORMANCE_REPORTING_ITEMS)
        if prediction_required
        else _not_required_section(PREDICTION_PERFORMANCE_REPORTING_ITEMS)
    )
    validation_uncertainty = (
        _section_status(contract.get("validation_uncertainty_reporting"), VALIDATION_UNCERTAINTY_ITEMS)
        if prediction_required
        else _not_required_section(VALIDATION_UNCERTAINTY_ITEMS)
    )
    prediction_display = (
        _section_status(contract.get("prediction_display_reporting"), PREDICTION_DISPLAY_REPORTING_ITEMS)
        if prediction_required
        else _not_required_section(PREDICTION_DISPLAY_REPORTING_ITEMS)
    )
    survey_design = (
        _section_status(contract.get("survey_design_reporting"), SURVEY_DESIGN_REPORTING_ITEMS)
        if survey_design_required
        else _not_required_section(SURVEY_DESIGN_REPORTING_ITEMS)
    )
    manuscript_voice = (
        _section_status(contract.get("manuscript_voice_reporting"), MANUSCRIPT_VOICE_REPORTING_ITEMS)
        if manuscript_voice_required
        else _not_required_section(MANUSCRIPT_VOICE_REPORTING_ITEMS)
    )
    baseline_balance = (
        _section_status(contract.get("baseline_balance_reporting"), BASELINE_BALANCE_REPORTING_ITEMS)
        if prediction_required
        else _not_required_section(BASELINE_BALANCE_REPORTING_ITEMS)
    )
    competing_risk = (
        _section_status(contract.get("competing_risk_reporting"), COMPETING_RISK_REPORTING_ITEMS)
        if competing_risk_required
        else _not_required_section(COMPETING_RISK_REPORTING_ITEMS)
    )
    treatment_gap_reporting = (
        _section_status(contract.get("treatment_gap_reporting"), TREATMENT_GAP_REPORTING_ITEMS)
        if actionability_required
        else {
            "status": "not_required",
            "required_items": list(TREATMENT_GAP_REPORTING_ITEMS),
            "missing_items": [],
        }
    )
    phenotype_derivation_reporting = (
        _section_status(
            contract.get("phenotype_derivation_reporting"),
            PHENOTYPE_DERIVATION_REPORTING_ITEMS,
        )
        if actionability_required
        else _not_required_section(PHENOTYPE_DERIVATION_REPORTING_ITEMS)
    )
    baseline_characteristics_reporting = (
        _section_status(
            contract.get("baseline_characteristics_reporting"),
            BASELINE_CHARACTERISTICS_REPORTING_ITEMS,
        )
        if actionability_required
        else _not_required_section(BASELINE_CHARACTERISTICS_REPORTING_ITEMS)
    )
    data_quality_reporting = (
        _section_status(contract.get("data_quality_reporting"), DATA_QUALITY_REPORTING_ITEMS)
        if actionability_required
        else _not_required_section(DATA_QUALITY_REPORTING_ITEMS)
    )
    blockers: list[str] = []
    if methods["status"] == "blocked":
        blockers.append("methods_completeness_incomplete")
    if statistics["status"] == "blocked":
        blockers.append("statistical_reporting_incomplete")
    if claim_map["status"] == "blocked":
        blockers.append("table_figure_claim_map_missing_or_incomplete")
    if actionability["status"] == "blocked":
        blockers.append("clinical_actionability_incomplete")
    if prediction_methods["status"] == "blocked":
        blockers.append("prediction_model_methods_reporting_incomplete")
    if prediction_model_reproducibility["status"] == "blocked":
        blockers.append("prediction_model_reproducibility_incomplete")
    if variable_harmonization["status"] == "blocked":
        blockers.append("variable_harmonization_incomplete")
    if time_to_event_prediction["status"] == "blocked":
        blockers.append("time_to_event_prediction_reporting_incomplete")
    if external_validation["status"] == "blocked":
        blockers.append("external_validation_reporting_incomplete")
    if decision_curve_clinical_utility["status"] == "blocked":
        blockers.append("decision_curve_clinical_utility_incomplete")
    if prediction_performance["status"] == "blocked":
        blockers.append("prediction_performance_reporting_incomplete")
    if validation_uncertainty["status"] == "blocked":
        blockers.append("validation_uncertainty_reporting_incomplete")
    if prediction_display["status"] == "blocked":
        blockers.append("prediction_display_reporting_incomplete")
    if survey_design["status"] == "blocked":
        blockers.append("survey_design_reporting_incomplete")
    if manuscript_voice["status"] == "blocked":
        blockers.append("manuscript_voice_reporting_incomplete")
    if baseline_balance["status"] == "blocked":
        blockers.append("baseline_balance_reporting_incomplete")
    if competing_risk["status"] == "blocked":
        blockers.append("competing_risk_reporting_incomplete")
    if treatment_gap_reporting["status"] == "blocked":
        blockers.append("treatment_gap_reporting_incomplete")
    if phenotype_derivation_reporting["status"] == "blocked":
        blockers.append("phenotype_derivation_reporting_incomplete")
    if baseline_characteristics_reporting["status"] == "blocked":
        blockers.append("baseline_characteristics_reporting_incomplete")
    if data_quality_reporting["status"] == "blocked":
        blockers.append("data_quality_reporting_incomplete")
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "reporting_guideline_closure_consumed": reporting_closure_consumed,
        "table_figure_claim_map_consumed": table_figure_claim_map_consumed,
        "methods_completeness": methods,
        "statistical_reporting": statistics,
        "table_figure_claim_map": claim_map,
        "clinical_actionability": actionability,
        "prediction_methods": prediction_methods,
        "prediction_model_reproducibility": prediction_model_reproducibility,
        "variable_harmonization": variable_harmonization,
        "time_to_event_prediction_reporting": time_to_event_prediction,
        "external_validation_reporting": external_validation,
        "decision_curve_clinical_utility": decision_curve_clinical_utility,
        "prediction_performance_reporting": prediction_performance,
        "validation_uncertainty_reporting": validation_uncertainty,
        "prediction_display_reporting": prediction_display,
        "survey_design_reporting": survey_design,
        "manuscript_voice_reporting": manuscript_voice,
        "baseline_balance_reporting": baseline_balance,
        "competing_risk_reporting": competing_risk,
        "treatment_gap_reporting": treatment_gap_reporting,
        "phenotype_derivation_reporting": phenotype_derivation_reporting,
        "baseline_characteristics_reporting": baseline_characteristics_reporting,
        "data_quality_reporting": data_quality_reporting,
    }


def normalize_structured_reporting_checklist(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("structured_reporting_checklist"), dict):
        return dict(payload["structured_reporting_checklist"])
    return None
