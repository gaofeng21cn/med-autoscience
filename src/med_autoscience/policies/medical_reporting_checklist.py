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
TIME_TO_EVENT_PREDICTION_ITEMS = (
    "proportional_hazards_assessment",
    "nonlinearity_assessment",
    "competing_event_screen",
    "absolute_risk_estimator",
    "calibration_time_horizon",
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
)
PHENOTYPE_ARCHETYPE_TOKENS = ("phenotype", "subtype", "cluster", "real_world")

REPORTING_CHECKLIST_BLOCKER_KEYS = frozenset(
    {
        "methods_completeness_incomplete",
        "statistical_reporting_incomplete",
        "table_figure_claim_map_missing_or_incomplete",
        "clinical_actionability_incomplete",
        "prediction_model_methods_reporting_incomplete",
        "time_to_event_prediction_reporting_incomplete",
        "decision_curve_clinical_utility_incomplete",
        "prediction_performance_reporting_incomplete",
        "baseline_balance_reporting_incomplete",
        "competing_risk_reporting_incomplete",
        "treatment_gap_reporting_incomplete",
    }
)


def _required_status_map(items: tuple[str, ...], *, status: str = "required_before_first_full_draft") -> dict[str, dict[str, str]]:
    return {item: {"status": status} for item in items}


def build_default_structured_reporting_contract(
    *,
    study_archetype: str | None = None,
    paper_archetype: str | None = None,
    manuscript_family: str | None = None,
    endpoint_type: str | None = None,
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
    ):
        if value:
            contract[key] = value
    if _prediction_model_required(contract):
        contract.update(
            {
                "prediction_model_reporting_required": True,
                "prediction_methods": _required_status_map(PREDICTION_MODEL_METHODS_ITEMS),
                "decision_curve_clinical_utility": _required_status_map(
                    DECISION_CURVE_CLINICAL_UTILITY_ITEMS
                ),
                "prediction_performance_reporting": _required_status_map(
                    PREDICTION_PERFORMANCE_REPORTING_ITEMS
                ),
                "baseline_balance_reporting": _required_status_map(BASELINE_BALANCE_REPORTING_ITEMS),
            }
        )
    if _time_to_event_prediction_required(contract):
        contract["time_to_event_prediction_reporting"] = _required_status_map(
            TIME_TO_EVENT_PREDICTION_ITEMS
        )
        contract["competing_risk_reporting_required"] = "when_non_target_deaths_present"
        contract["competing_risk_reporting"] = _required_status_map(
            COMPETING_RISK_REPORTING_ITEMS,
            status="required_when_non_target_deaths_present",
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
        displays = item.get("displays") or item.get("tables_figures") or item.get("table_figure_refs")
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


def build_structured_reporting_checklist(contract: dict[str, Any]) -> dict[str, Any]:
    contract = _structured_contract_source(contract)
    actionability_required = _phenotype_actionability_required(contract)
    prediction_required = _prediction_model_required(contract)
    time_to_event_prediction_required = _time_to_event_prediction_required(contract)
    competing_risk_required = _competing_risk_reporting_required(contract)
    explicit_structured_contract = any(
        key in contract
        for key in (
            "methods_completeness",
            "statistical_reporting",
            "table_figure_claim_map",
            "clinical_actionability",
            "treatment_gap_reporting",
            "prediction_methods",
            "time_to_event_prediction_reporting",
            "decision_curve_clinical_utility",
            "prediction_performance_reporting",
            "baseline_balance_reporting",
            "competing_risk_reporting",
        )
    )
    if not actionability_required and not prediction_required and not explicit_structured_contract:
        return {
            "status": "not_required",
            "blockers": [],
            "methods_completeness": _not_required_section(METHODS_COMPLETENESS_ITEMS),
            "statistical_reporting": _not_required_section(STATISTICAL_REPORTING_ITEMS),
            "table_figure_claim_map": {
                "status": "not_required",
                "mapped_claim_count": 0,
                "missing_items": [],
            },
            "clinical_actionability": _not_required_section(CLINICAL_ACTIONABILITY_ITEMS),
            "prediction_methods": _not_required_section(PREDICTION_MODEL_METHODS_ITEMS),
            "time_to_event_prediction_reporting": _not_required_section(TIME_TO_EVENT_PREDICTION_ITEMS),
            "decision_curve_clinical_utility": _not_required_section(DECISION_CURVE_CLINICAL_UTILITY_ITEMS),
            "prediction_performance_reporting": _not_required_section(PREDICTION_PERFORMANCE_REPORTING_ITEMS),
            "baseline_balance_reporting": _not_required_section(BASELINE_BALANCE_REPORTING_ITEMS),
            "competing_risk_reporting": _not_required_section(COMPETING_RISK_REPORTING_ITEMS),
            "treatment_gap_reporting": _not_required_section(TREATMENT_GAP_REPORTING_ITEMS),
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
    time_to_event_prediction = (
        _section_status(contract.get("time_to_event_prediction_reporting"), TIME_TO_EVENT_PREDICTION_ITEMS)
        if time_to_event_prediction_required
        else _not_required_section(TIME_TO_EVENT_PREDICTION_ITEMS)
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
    if time_to_event_prediction["status"] == "blocked":
        blockers.append("time_to_event_prediction_reporting_incomplete")
    if decision_curve_clinical_utility["status"] == "blocked":
        blockers.append("decision_curve_clinical_utility_incomplete")
    if prediction_performance["status"] == "blocked":
        blockers.append("prediction_performance_reporting_incomplete")
    if baseline_balance["status"] == "blocked":
        blockers.append("baseline_balance_reporting_incomplete")
    if competing_risk["status"] == "blocked":
        blockers.append("competing_risk_reporting_incomplete")
    if treatment_gap_reporting["status"] == "blocked":
        blockers.append("treatment_gap_reporting_incomplete")
    return {
        "status": "blocked" if blockers else "clear",
        "blockers": blockers,
        "methods_completeness": methods,
        "statistical_reporting": statistics,
        "table_figure_claim_map": claim_map,
        "clinical_actionability": actionability,
        "prediction_methods": prediction_methods,
        "time_to_event_prediction_reporting": time_to_event_prediction,
        "decision_curve_clinical_utility": decision_curve_clinical_utility,
        "prediction_performance_reporting": prediction_performance,
        "baseline_balance_reporting": baseline_balance,
        "competing_risk_reporting": competing_risk,
        "treatment_gap_reporting": treatment_gap_reporting,
    }


def normalize_structured_reporting_checklist(payload: object) -> dict[str, Any] | None:
    if not isinstance(payload, dict):
        return None
    if isinstance(payload.get("structured_reporting_checklist"), dict):
        return dict(payload["structured_reporting_checklist"])
    return None
