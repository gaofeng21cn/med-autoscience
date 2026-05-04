from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


SUPPORTED_STUDY_ARCHETYPES = (
    "observational_real_world",
    "prediction_model",
    "external_validation",
    "subtype_reconstruction",
    "gray_zone_triage",
    "ai_clinical_task",
)

REQUIRED_STATISTICAL_DISCIPLINE_FIELDS = (
    "reporting_guideline",
    "missingness_plan",
    "sample_size_precision_plan",
    "external_validation_plan",
    "subgroup_plan",
    "multiplicity_guardrail",
    "clinical_utility_plan",
    "endpoint_time_window",
    "sensitivity_plan",
    "failure_conditions",
)

STATISTICAL_DISCIPLINE_OPERATION_FIELDS = (
    "missingness_plan",
    "sample_size_precision_plan",
    "external_validation_plan",
    "subgroup_plan",
    "multiplicity_guardrail",
    "clinical_utility_plan",
    "endpoint_time_window",
    "sensitivity_plan",
)

FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS = (
    "sample_size_precision_plan",
    "external_validation_plan",
    "clinical_utility_plan",
    "endpoint_time_window",
)

REQUIRED_STATISTICAL_REVIEWER_TEMPLATE_FIELDS = (
    "reviewer_concern",
    "target_blocker",
    "required_evidence_refs",
    "waiver_reason_requirements",
    "manuscript_action",
)

REQUIRED_STATISTICAL_REVIEWER_AUDIT_SECTIONS = (
    "statistical_plan",
    "model_or_test_selection",
    "sample_size_or_precision",
    "missing_data",
    "sensitivity_analyses",
    "subgroup_and_interaction",
    "multiplicity",
    "causal_language_boundary",
)

REQUIRED_STATISTICAL_REVIEWER_SECTION_FIELDS = (
    "assessment",
    "evidence_refs",
    "manuscript_action",
)

SUPPORTED_STATISTICAL_REVIEWER_SECTION_STATUSES = (
    "pass",
    "acceptable_with_boundary",
)

SUPPORTED_CANDIDATE_DECISIONS = (
    "explore",
    "exploit",
    "fusion",
    "debug",
    "stop",
)

REQUIRED_CANDIDATE_FIELDS = (
    "target_claim",
    "expected_evidence_gain",
    "statistical_risk",
    "clinical_interpretability",
    "decision",
    "decision_reason",
)

_NOMINAL_P_VALUE_TERMS = (
    "nominal p-value",
    "nominal p value",
    "nominal pvalue",
    "unadjusted p-value as primary",
    "unadjusted p value as primary",
    "p < 0.05 as primary",
    "p<0.05 as primary",
)

_METRIC_ONLY_PRIMARY_EVIDENCE_TERMS = {
    "auc_only_primary_evidence": (
        "auc-only",
        "auc only",
        "auc alone",
        "auc as primary",
        "auc is the primary evidence",
    ),
    "cluster_separation_only_primary_evidence": (
        "cluster separation-only",
        "cluster separation only",
        "cluster separation alone",
        "cluster separation as primary",
        "cluster separation is the primary evidence",
    ),
}

_PRIMARY_EVIDENCE_KEYS = (
    "primary_evidence",
    "primary_evidence_basis",
    "primary_statistical_evidence",
    "evidence_basis",
    "decision_reason",
    "sensitivity_plan",
)

_FORBIDDEN_EVIDENCE_CLASSIFICATIONS = (
    "primary",
    "secondary",
    "exploratory",
)

_EVIDENCE_CLASSIFICATION_KEYS = (
    "evidence_classification",
    "evidence_class",
    "evidence_tier",
    "claim_classification",
    "analysis_classification",
    "analysis_role",
)

_OPERATION_FIELD_LABELS = {
    "missingness_plan": "Missing-data discipline",
    "sample_size_precision_plan": "Precision and event-count discipline",
    "external_validation_plan": "External-validation discipline",
    "subgroup_plan": "Subgroup discipline",
    "multiplicity_guardrail": "Multiplicity guardrail",
    "clinical_utility_plan": "Clinical-utility discipline",
    "endpoint_time_window": "Endpoint and time-window discipline",
    "sensitivity_plan": "Sensitivity-analysis discipline",
}

_OPERATION_FIELD_SUMMARIES = {
    "missingness_plan": "Specify missingness measurement, handling, and sensitivity checks before promotion.",
    "sample_size_precision_plan": "Anchor the claim in sample size, event counts, and precision rather than nominal significance.",
    "external_validation_plan": "State external, temporal, or held-out validation requirements for the target claim.",
    "subgroup_plan": "Prespecify subgroup support thresholds and interpretation limits.",
    "multiplicity_guardrail": "Separate primary evidence from exploratory comparisons and control repeated contrasts.",
    "clinical_utility_plan": "Tie statistical evidence to an actionable clinical threshold, workflow, or care-pathway consequence.",
    "endpoint_time_window": "Lock endpoint definitions, index date, lookback, outcome window, and follow-up closure.",
    "sensitivity_plan": "Prespecify robustness checks that can falsify or qualify the target claim.",
}

_REVIEWER_TEMPLATE_FAMILIES = {
    "observational_real_world": "observational_real_world",
    "prediction_model": "prediction_external_validation",
    "external_validation": "prediction_external_validation",
    "subtype_reconstruction": "subtype_triage",
    "gray_zone_triage": "subtype_triage",
    "ai_clinical_task": "ai_clinical_task",
}

_REVIEWER_FAMILY_LABELS = {
    "observational_real_world": "Observational real-world statistical reviewer",
    "prediction_external_validation": "Prediction / external-validation statistical reviewer",
    "subtype_triage": "Subtype / triage statistical reviewer",
    "ai_clinical_task": "AI clinical-task statistical reviewer",
}

_GUIDELINE_FAMILIES = {
    "prediction_model": (
        "TRIPOD",
        "TRIPOD-AI",
        "transparent_reporting_multivariable_prediction_external_validation",
    ),
    "external_validation": (
        "TRIPOD",
        "transparent_reporting_multivariable_prediction_external_validation",
    ),
    "observational_real_world": (
        "STROBE",
        "RECORD",
    ),
    "subtype_reconstruction": (
        "STROBE",
        "subtype_triage_specific_reviewer_concerns",
    ),
    "gray_zone_triage": (
        "TRIPOD",
        "subtype_triage_specific_reviewer_concerns",
    ),
    "ai_clinical_task": (
        "TRIPOD-AI",
        "CONSORT-AI",
    ),
}

_REVIEWER_TEMPLATE_EVIDENCE_REFS = {
    "observational_real_world": {
        "missingness_plan": (
            "analysis/missingness_by_cohort_endpoint_exposure_site",
            "methods/missing_data_handling_plan",
            "sensitivity/missingness_robustness_checks",
        ),
        "sample_size_precision_plan": (
            "analysis/cohort_denominator_event_counts",
            "analysis/effect_size_confidence_intervals_or_detectable_range",
            "analysis/subgroup_support_table",
        ),
        "external_validation_plan": (
            "analysis/temporal_or_site_holdout_transportability_check",
            "methods/internal_only_claim_boundary_when_no_external_support",
        ),
        "subgroup_plan": (
            "analysis/prespecified_clinical_strata_support",
            "analysis/subgroup_estimates_with_uncertainty",
        ),
        "multiplicity_guardrail": (
            "analysis/primary_endpoint_family_manifest",
            "methods/multiplicity_or_estimation_guardrail",
        ),
        "clinical_utility_plan": (
            "analysis/absolute_risk_or_effect_size_interpretability",
            "clinical/guideline_or_care_pathway_action_threshold",
        ),
        "endpoint_time_window": (
            "methods/index_date_exposure_lookback_outcome_window",
            "analysis/follow_up_closure_and_censoring_manifest",
        ),
        "sensitivity_plan": (
            "sensitivity/confounding_coding_drift_time_window_checks",
            "sensitivity/site_support_and_missingness_checks",
        ),
    },
    "prediction_external_validation": {
        "missingness_plan": (
            "analysis/predictor_missingness_train_validation_deployment",
            "methods/imputation_unavailable_feature_routing",
            "sensitivity/missing_predictor_behavior",
        ),
        "sample_size_precision_plan": (
            "analysis/effective_sample_size_and_event_count",
            "analysis/calibration_discrimination_precision",
            "analysis/optimism_or_validation_uncertainty",
        ),
        "external_validation_plan": (
            "analysis/locked_external_temporal_or_site_validation",
            "analysis/calibration_transportability_and_case_mix_shift",
            "methods/recalibration_policy",
        ),
        "subgroup_plan": (
            "analysis/subgroup_discrimination_calibration_threshold_performance",
            "analysis/minimum_support_for_clinical_slices",
        ),
        "multiplicity_guardrail": (
            "methods/locked_primary_model_metric_manifest",
            "analysis/threshold_scan_and_subgroup_family_boundary",
        ),
        "clinical_utility_plan": (
            "analysis/net_benefit_decision_curve_or_threshold_impact",
            "clinical/intended_use_and_actionability_manifest",
        ),
        "endpoint_time_window": (
            "methods/prediction_origin_feature_lookback_horizon",
            "methods/outcome_window_and_censoring_policy",
        ),
        "sensitivity_plan": (
            "sensitivity/calibration_drift_threshold_outcome_definition",
            "sensitivity/missing_predictor_and_recalibration_checks",
        ),
    },
    "subtype_triage": {
        "missingness_plan": (
            "analysis/subtype_variable_or_gray_zone_marker_missingness",
            "methods/inclusion_imputation_reference_standard_gap_policy",
            "sensitivity/missing_marker_or_variable_retention_checks",
        ),
        "sample_size_precision_plan": (
            "analysis/subtype_cluster_or_gray_zone_support",
            "analysis/threshold_precision_or_cluster_stability_uncertainty",
            "analysis/minimum_interpretable_slice_size",
        ),
        "external_validation_plan": (
            "analysis/site_holdout_temporal_or_bootstrap_stability",
            "analysis/external_threshold_or_subtype_transportability",
        ),
        "subgroup_plan": (
            "analysis/clinically_interpretable_subtype_or_threshold_slices",
            "analysis/treatment_outcome_or_reference_standard_gradients",
        ),
        "multiplicity_guardrail": (
            "methods/discovery_vs_confirmatory_characterization_boundary",
            "analysis/repeated_threshold_or_characterization_contrast_control",
        ),
        "clinical_utility_plan": (
            "clinical/subtype_naming_or_triage_actionability_manifest",
            "analysis/downstream_tradeoff_or_care_pathway_consequence",
        ),
        "endpoint_time_window": (
            "methods/phenotype_measurement_or_index_assessment_window",
            "methods/reference_standard_decision_and_outcome_timing",
        ),
        "sensitivity_plan": (
            "sensitivity/algorithm_feature_scaling_threshold_perturbation",
            "sensitivity/site_holdout_reference_standard_missingness_checks",
        ),
    },
    "ai_clinical_task": {
        "missingness_plan": (
            "analysis/input_modality_annotation_prompt_context_missingness",
            "methods/deployment_time_abstention_or_unavailable_input_policy",
            "sensitivity/missing_modality_or_context_checks",
        ),
        "sample_size_precision_plan": (
            "analysis/task_instance_patient_level_independence_counts",
            "analysis/annotation_support_and_uncertainty",
            "analysis/clinically_meaningful_performance_precision",
        ),
        "external_validation_plan": (
            "analysis/locked_external_temporal_site_or_reader_environment_validation",
            "analysis/site_shift_and_model_version_traceability",
        ),
        "subgroup_plan": (
            "analysis/fairness_site_device_demographic_severity_slices",
            "analysis/minimum_support_and_error_severity_by_slice",
        ),
        "multiplicity_guardrail": (
            "methods/locked_model_prompt_evaluation_boundary",
            "analysis/repeated_task_subgroup_or_prompt_comparison_control",
        ),
        "clinical_utility_plan": (
            "analysis/workflow_effect_error_severity_human_ai_interaction",
            "clinical/actionability_beyond_aggregate_accuracy",
        ),
        "endpoint_time_window": (
            "methods/task_input_time_clinical_decision_point",
            "methods/reference_label_timing_and_follow_up_window",
        ),
        "sensitivity_plan": (
            "sensitivity/model_version_prompt_context_annotation_disagreement",
            "sensitivity/site_shift_subgroup_performance_abstention_checks",
        ),
    },
}

_REVIEWER_TEMPLATE_CONCERNS = {
    "observational_real_world": {
        "missingness_plan": "Missing data could distort denominators, exposure ascertainment, endpoint capture, or site comparability.",
        "sample_size_precision_plan": "The real-world estimate needs denominator, event-count, and interval precision support before reviewer-facing interpretation.",
        "external_validation_plan": "A transportability claim needs temporal, site-held-out, or registry-held-out evidence; otherwise the manuscript must state an internal claim boundary.",
        "subgroup_plan": "Subgroup language must be prespecified, clinically meaningful, and supported by interpretable uncertainty.",
        "multiplicity_guardrail": "Repeated endpoints, exposures, and subgroup contrasts need a declared primary family and multiplicity interpretation rule.",
        "clinical_utility_plan": "The estimate must map to absolute risk, guideline relevance, a decision threshold, or a care-pathway consequence.",
        "endpoint_time_window": "Endpoint semantics require locked index date, lookback, ascertainment window, and follow-up closure before reviewer clearance.",
        "sensitivity_plan": "Robustness to confounding, coding drift, missingness, time-window variation, and site support must be auditable.",
    },
    "prediction_external_validation": {
        "missingness_plan": "Predictor missingness, unavailable features, and deployment-time missingness behavior must be reviewer-visible.",
        "sample_size_precision_plan": "Performance claims need effective sample size, events, calibration precision, and uncertainty rather than nominal significance.",
        "external_validation_plan": "Generalizable prediction or validation claims require locked external, temporal, or site-held-out validation and calibration evidence.",
        "subgroup_plan": "Clinically important strata need discrimination, calibration, and threshold-performance support with uncertainty.",
        "multiplicity_guardrail": "Model metrics, threshold scans, subgroup checks, and recalibration attempts must be separated from the locked primary claim.",
        "clinical_utility_plan": "Performance metrics need intended-use, threshold, calibration, and net-benefit or decision-impact evidence.",
        "endpoint_time_window": "Prediction origin, lookback, prediction horizon, outcome window, and censoring must match the target-use claim.",
        "sensitivity_plan": "Optimism, calibration drift, threshold sensitivity, missing predictors, and outcome-definition robustness must be tested.",
    },
    "subtype_triage": {
        "missingness_plan": "Subtype-defining variables, gray-zone markers, reference-standard gaps, and indeterminate outcomes need explicit handling.",
        "sample_size_precision_plan": "Subtype or gray-zone claims need support, stability, threshold precision, and minimum interpretable slice size.",
        "external_validation_plan": "Durable subtype labels or triage thresholds need held-out, temporal, bootstrap, or external stability evidence.",
        "subgroup_plan": "Subtype and triage interpretations must map to prespecified clinical strata and avoid unsupported post-hoc naming.",
        "multiplicity_guardrail": "Discovery, characterization, threshold searching, and confirmatory contrasts need separate reviewer-visible boundaries.",
        "clinical_utility_plan": "Subtype names or triage rules must change diagnostic, prognostic, treatment-pattern, or workflow interpretation.",
        "endpoint_time_window": "Phenotype measurement, index assessment, reference-standard timing, decision window, and outcome follow-up must be locked.",
        "sensitivity_plan": "Algorithm, feature set, scaling, threshold perturbation, reference-standard uncertainty, and site support must be stress-tested.",
    },
    "ai_clinical_task": {
        "missingness_plan": "Missing modalities, annotation gaps, prompt/context absence, and abstention behavior must be explicit.",
        "sample_size_precision_plan": "AI task performance needs task-instance counts, patient-level independence, annotation support, and uncertainty.",
        "external_validation_plan": "Broad AI clinical task claims need locked external, temporal, site, or reader-environment validation.",
        "subgroup_plan": "Fairness, device, site, demographic, and severity slices need support and clinically interpretable error profiles.",
        "multiplicity_guardrail": "Prompt/model iteration must be separated from locked evaluation and repeated task or subgroup comparisons.",
        "clinical_utility_plan": "Aggregate accuracy must be tied to workflow impact, error severity, human-AI interaction, and clinical actionability.",
        "endpoint_time_window": "Task input time, clinical decision point, reference label timing, and follow-up outcome window must be locked.",
        "sensitivity_plan": "Model version, prompt/context variation, annotation disagreement, site shift, subgroup performance, and abstention rules must be checked.",
    },
}

_ARCHETYPE_DISCIPLINE: dict[str, dict[str, str]] = {
    "observational_real_world": {
        "reporting_guideline": "STROBE with RECORD overlay when electronic health records or registry linkage are used.",
        "missingness_plan": "Quantify missingness by cohort, endpoint, exposure, and site; prespecify complete-case, imputation, and missing-indicator sensitivity checks.",
        "sample_size_precision_plan": "State available cohort size, event counts, subgroup support, and precision targets using confidence intervals or detectable effect ranges.",
        "external_validation_plan": "Use temporally separated, site-held-out, or registry-held-out checks when a transportability claim is made; otherwise declare the claim as internal only.",
        "subgroup_plan": "Prespecify clinically meaningful strata and minimum support thresholds before subgroup interpretation.",
        "multiplicity_guardrail": "Separate primary endpoints from exploratory contrasts and apply family-wise, false-discovery, or estimation-focused interpretation rules.",
        "clinical_utility_plan": "Tie effect estimates to absolute risk, decision threshold, care pathway, or guideline-relevant clinical action.",
        "endpoint_time_window": "Define index date, exposure lookback, outcome ascertainment window, and censoring or follow-up closure.",
        "sensitivity_plan": "Run prespecified robustness checks for confounding, coding drift, missingness, time-window variation, and site support.",
        "failure_conditions": "Block promotion when endpoint semantics, denominator support, missingness, confounding control, or external support cannot sustain the target claim.",
    },
    "prediction_model": {
        "reporting_guideline": "TRIPOD with TRIPOD+AI extension when model development uses AI or machine-learning components.",
        "missingness_plan": "Describe missing predictor handling, imputation, unavailable-feature routing, and deployment-time missingness behavior.",
        "sample_size_precision_plan": "Report events per parameter or effective sample size, calibration precision, confidence intervals, and optimism-correction assumptions.",
        "external_validation_plan": "Require external, temporal, or site-held-out validation before any generalizable performance or clinical deployment claim.",
        "subgroup_plan": "Prespecify subgroup discrimination, calibration, and threshold-performance checks for clinically important strata.",
        "multiplicity_guardrail": "Freeze primary model metrics and subgroup families before analysis; label feature fishing and threshold scans as exploratory.",
        "clinical_utility_plan": "Pair performance metrics with calibration, net benefit, decision thresholds, and intended-use consequences.",
        "endpoint_time_window": "Define prediction origin, feature lookback, prediction horizon, outcome window, and censoring treatment.",
        "sensitivity_plan": "Check optimism, calibration drift, threshold sensitivity, missing predictors, and alternative outcome definitions.",
        "failure_conditions": "Block promotion when validation, calibration, endpoint horizon, subgroup support, or intended-use utility is unresolved.",
    },
    "external_validation": {
        "reporting_guideline": "TRIPOD external validation reporting with transportability and calibration update details.",
        "missingness_plan": "Compare missingness between derivation and validation settings and state how validation-time absent variables are handled.",
        "sample_size_precision_plan": "Report validation sample size, event count, calibration precision, and uncertainty around discrimination and net-benefit estimates.",
        "external_validation_plan": "Treat validation cohort independence, case-mix shift, and recalibration policy as mandatory primary evidence surfaces.",
        "subgroup_plan": "Prespecify subgroup validation slices only where validation support is sufficient for interpretable uncertainty.",
        "multiplicity_guardrail": "Keep recalibration, threshold tuning, and subgroup scans separate from the primary validation claim.",
        "clinical_utility_plan": "Assess whether validation performance preserves the intended clinical action and threshold behavior.",
        "endpoint_time_window": "Lock validation index, prediction horizon, outcome ascertainment, and follow-up closure to match the target-use claim.",
        "sensitivity_plan": "Test calibration drift, case-mix shift, threshold transportability, and recalibration alternatives.",
        "failure_conditions": "Block promotion when independence, transportability, calibration, or validation precision is insufficient.",
    },
    "subtype_reconstruction": {
        "reporting_guideline": "STROBE with transparent unsupervised-learning and phenotype-definition reporting.",
        "missingness_plan": "Profile missingness for subtype-defining variables and specify inclusion, imputation, and variable-retention rules.",
        "sample_size_precision_plan": "State subtype support, cluster stability precision, site balance, and minimum interpretable subgroup size.",
        "external_validation_plan": "Require site-held-out, bootstrap, temporal, or external-cohort stability evidence before naming durable clinical subtypes.",
        "subgroup_plan": "Map subtypes to clinically interpretable strata, treatment patterns, and outcome gradients without post-hoc overclaiming.",
        "multiplicity_guardrail": "Separate subtype discovery from confirmatory characterization and control repeated characterization contrasts.",
        "clinical_utility_plan": "Tie subtype labels to diagnostic, prognostic, treatment-pattern, or care-pathway interpretability.",
        "endpoint_time_window": "Define phenotype measurement window, temporal ordering, and outcome follow-up windows used for subtype characterization.",
        "sensitivity_plan": "Check algorithm choice, feature set, scaling, missingness, site holdout, and subtype assignment stability.",
        "failure_conditions": "Block promotion when subtype stability, clinical naming, site support, or characterization evidence is weak.",
    },
    "gray_zone_triage": {
        "reporting_guideline": "STARD or TRIPOD as appropriate for diagnostic, prognostic, or triage-threshold framing.",
        "missingness_plan": "State how unavailable gray-zone markers, reference-standard gaps, and indeterminate outcomes are handled.",
        "sample_size_precision_plan": "Report gray-zone support, event or reference-standard counts, and threshold precision around decision boundaries.",
        "external_validation_plan": "Require temporally or clinically distinct validation before changing triage thresholds or claiming transportable gray-zone rules.",
        "subgroup_plan": "Prespecify clinically relevant threshold-performance slices and prohibit unsupported threshold claims in small strata.",
        "multiplicity_guardrail": "Lock candidate thresholds and gray-zone definitions before exploitation; mark threshold searches as exploratory.",
        "clinical_utility_plan": "Quantify downstream triage consequences, false positive/negative tradeoffs, and decision-curve or net-benefit evidence.",
        "endpoint_time_window": "Define index assessment, triage decision window, reference-standard timing, and outcome ascertainment interval.",
        "sensitivity_plan": "Check threshold perturbation, reference-standard uncertainty, missing markers, and subgroup threshold robustness.",
        "failure_conditions": "Block promotion when threshold stability, clinical tradeoff, validation, or reference-standard quality is unresolved.",
    },
    "ai_clinical_task": {
        "reporting_guideline": "TRIPOD+AI, CONSORT-AI, SPIRIT-AI, or DECIDE-AI according to task maturity and evaluation design.",
        "missingness_plan": "Document missing input modalities, annotation gaps, prompt/context absence, and deployment-time abstention or fallback behavior.",
        "sample_size_precision_plan": "Report task instances, patient-level independence, annotation support, uncertainty, and clinically meaningful performance precision.",
        "external_validation_plan": "Require locked external, temporal, site, or reader-environment validation before broad AI clinical task claims.",
        "subgroup_plan": "Prespecify fairness, site, device, demographic, and clinical-severity slices with minimum support and interpretability thresholds.",
        "multiplicity_guardrail": "Separate prompt/model iteration from locked evaluation and adjust or label repeated task and subgroup comparisons.",
        "clinical_utility_plan": "Evaluate effect on clinical workflow, error severity, human-AI interaction, and actionability beyond aggregate accuracy.",
        "endpoint_time_window": "Define task input time, clinical decision point, reference label timing, and follow-up outcome window.",
        "sensitivity_plan": "Check model version, prompt/context variation, annotation disagreement, site shift, subgroup performance, and abstention rules.",
        "failure_conditions": "Block promotion when locked evaluation, external validation, subgroup safety, clinical utility, or model-version traceability is missing.",
    },
}


def _text(value: object) -> str:
    return str(value or "").strip()


def _has_text(value: object) -> bool:
    return bool(_text(value))


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _contains_nominal_p_value_primary_evidence(payload: Mapping[str, Any]) -> bool:
    for key in _PRIMARY_EVIDENCE_KEYS:
        text = _text(payload.get(key)).lower()
        if text and any(term in text for term in _NOMINAL_P_VALUE_TERMS):
            return True
    return False


def _metric_only_primary_evidence_reason(payload: Mapping[str, Any]) -> str:
    for key in _PRIMARY_EVIDENCE_KEYS:
        text = _text(payload.get(key)).lower()
        if not text:
            continue
        for reason_code, terms in _METRIC_ONLY_PRIMARY_EVIDENCE_TERMS.items():
            if any(term in text for term in terms):
                return reason_code
    return ""


def _primary_evidence_violation_reason(payload: Mapping[str, Any]) -> str:
    if _contains_nominal_p_value_primary_evidence(payload):
        return "nominal_p_value_primary_evidence"
    return _metric_only_primary_evidence_reason(payload)


def _contains_nominal_p_value(text: object) -> bool:
    normalized = _text(text).lower()
    return bool(normalized and any(term in normalized for term in _NOMINAL_P_VALUE_TERMS))


def _contains_forbidden_evidence_classification(payload: Mapping[str, Any]) -> bool:
    for key in _EVIDENCE_CLASSIFICATION_KEYS:
        value = _text(payload.get(key)).lower()
        if value in _FORBIDDEN_EVIDENCE_CLASSIFICATIONS:
            return True
    return False


def _waiver_reason(payload: Mapping[str, Any], field: str) -> str:
    for key in (f"{field}_waiver_reason", f"waiver_reason_{field}"):
        reason = _text(payload.get(key))
        if reason:
            return reason
    waivers = payload.get("waivers")
    if isinstance(waivers, Mapping):
        return _text(waivers.get(field))
    for waiver in _sequence(waivers):
        if isinstance(waiver, Mapping) and _text(waiver.get("field")) == field:
            return _text(waiver.get("reason"))
    return ""


def _operation_action_card(
    *,
    action_id: str,
    label: str,
    summary: str,
    field: str,
    status: str,
    waiver_allowed: bool,
) -> dict[str, object]:
    return {
        "action_id": action_id,
        "label": label,
        "summary": summary,
        "field": field,
        "status": status,
        "required_for_ready": status == "blocked",
        "waiver_allowed": waiver_allowed,
    }


def _bounded_board_candidates(payload: Mapping[str, Any] | None) -> list[Mapping[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    return [candidate for candidate in _sequence(payload.get("candidates")) if isinstance(candidate, Mapping)]


def _weak_or_blocked_status(payload: Mapping[str, Any]) -> str:
    for key in ("status", "board_status", "evidence_state", "strength", "signal_status"):
        value = _text(payload.get(key)).lower()
        if value in {"weak", "blocked"}:
            return value
    return ""


def _operation_field_projection(
    *,
    contract: Mapping[str, Any],
    field: str,
) -> tuple[list[str], dict[str, str] | None, dict[str, object]]:
    waiver_reason = _waiver_reason(contract, field)
    value_present = _has_text(contract.get(field))
    nominal_primary_evidence = _contains_nominal_p_value(contract.get(field))
    waiver_allowed = field not in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS
    if value_present and not nominal_primary_evidence:
        status = "waived" if waiver_reason and waiver_allowed else "present"
    elif waiver_reason and waiver_allowed:
        status = "waived"
    else:
        status = "blocked"

    blockers = []
    if not value_present and (not waiver_reason or not waiver_allowed):
        blockers.append(f"missing_{field}")
    if nominal_primary_evidence:
        blockers.append("nominal_p_value_primary_evidence")
    if waiver_reason and not waiver_allowed:
        blockers.append(f"{field}_waiver_not_allowed")
    waiver = {"field": field, "reason": waiver_reason} if waiver_reason and waiver_allowed else None
    return blockers, waiver, _operation_action_card(
        action_id=f"resolve_{field}",
        label=_OPERATION_FIELD_LABELS[field],
        summary=_OPERATION_FIELD_SUMMARIES[field],
        field=field,
        status=status,
        waiver_allowed=waiver_allowed,
    )


def _bounded_board_action_card(*, action_id: str, label: str, summary: str) -> dict[str, object]:
    return _operation_action_card(
        action_id=action_id,
        label=label,
        summary=summary,
        field="bounded_board",
        status="blocked",
        waiver_allowed=False,
    )


def _bounded_board_top_level_projection(
    bounded_board: Mapping[str, Any] | None,
) -> tuple[list[str], list[dict[str, object]]]:
    if not isinstance(bounded_board, Mapping):
        return [], []
    board_status = _weak_or_blocked_status(bounded_board)
    if not board_status:
        return [], []
    return [f"bounded_board_{board_status}"], [
        _bounded_board_action_card(
            action_id="repair_bounded_board",
            label="Bounded-board evidence repair",
            summary="Repair weak or blocked bounded-board evidence before using board decisions.",
        )
    ]


def _bounded_board_candidate_projection(
    *,
    index: int,
    candidate: Mapping[str, Any],
) -> tuple[list[str], list[dict[str, object]]]:
    blockers: list[str] = []
    action_cards: list[dict[str, object]] = []
    board_status = _weak_or_blocked_status(candidate)
    if board_status:
        blockers.append(f"candidate_{index}_{board_status}_board")
        action_cards.append(
            _bounded_board_action_card(
                action_id=f"candidate_{index}_repair_bounded_board",
                label="Bounded-board evidence repair",
                summary="Repair weak or blocked bounded-board evidence before using this candidate.",
            )
        )

    missing_required_fields = [
        field for field in REQUIRED_CANDIDATE_FIELDS if not _has_text(candidate.get(field))
    ]
    blockers.extend(f"candidate_{index}_missing_{field}" for field in missing_required_fields)
    if missing_required_fields:
        action_cards.append(
            _bounded_board_action_card(
                action_id=f"candidate_{index}_complete_required_bindings",
                label="Bounded-board candidate binding",
                summary="Bind the candidate to target claim, evidence gain, risk, interpretability, decision, and decision reason.",
            )
        )

    if _contains_forbidden_evidence_classification(candidate):
        blockers.append(f"candidate_{index}_forbidden_evidence_classification")
    primary_evidence_violation = _primary_evidence_violation_reason(candidate)
    if primary_evidence_violation:
        blockers.append(f"candidate_{index}_{primary_evidence_violation}")

    decision = _text(candidate.get("decision"))
    if decision not in SUPPORTED_CANDIDATE_DECISIONS:
        blockers.append(f"candidate_{index}_unsupported_decision")
        action_cards.append(
            _bounded_board_action_card(
                action_id=f"candidate_{index}_select_supported_decision",
                label="Supported board decision",
                summary="Set decision to explore, exploit, fusion, debug, or stop.",
            )
        )
        return blockers, action_cards

    if decision == "stop":
        if not _has_text(candidate.get("decision_reason")):
            blockers.append(f"candidate_{index}_missing_stop_reason")
        action_cards.append(
            _bounded_board_action_card(
                action_id=f"candidate_{index}_stop_loss_switch_line",
                label="Stop-loss / switch-line decision",
                summary="Stop the current analysis line or switch line using the recorded decision reason.",
            )
        )
    return blockers, action_cards


def _reviewer_template_family(study_archetype: str) -> str:
    return _REVIEWER_TEMPLATE_FAMILIES[study_archetype]


def _reviewer_waiver_requirements(field: str) -> dict[str, object]:
    if field in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS:
        return {
            "waiver_allowed": False,
            "required_reason_components": [],
            "fail_closed_reason": (
                "Precision, external validation, endpoint/time-window, and clinical-utility concerns "
                "cannot be waived because they define the claim support, semantics, transportability, "
                "and intended-use consequence."
            ),
        }
    return {
        "waiver_allowed": True,
        "required_reason_components": [
            "why this evidence domain is outside the active claim",
            "which manuscript claim boundary prevents overstatement",
            "which reviewer-visible artifact records the boundary",
        ],
    }


def _reviewer_manuscript_action(*, family: str, field: str) -> str:
    if field == "external_validation_plan" and family == "prediction_external_validation":
        return (
            "Add or preserve a reviewer-visible validation paragraph/table that binds the claim "
            "to locked external, temporal, or site-held-out evidence; downgrade to internal-only "
            "language when that evidence is absent."
        )
    if field == "clinical_utility_plan":
        return (
            "Bind Results and Discussion language to the clinical action, threshold, workflow, "
            "or intended-use consequence supported by the evidence."
        )
    if field == "endpoint_time_window":
        return (
            "State the endpoint definition, index point, lookback/input window, outcome or label "
            "timing, and follow-up closure in Methods before any reviewer-facing claim."
        )
    return (
        f"Update Methods, Results, and limitations so {_OPERATION_FIELD_LABELS[field].lower()} "
        "is visible as evidence, boundary, or waiver text."
    )


def _reviewer_template(
    *,
    family: str,
    field: str,
) -> dict[str, object]:
    return {
        "field": field,
        "reviewer_concern": _REVIEWER_TEMPLATE_CONCERNS[family][field],
        "target_blocker": f"missing_{field}",
        "required_evidence_refs": list(_REVIEWER_TEMPLATE_EVIDENCE_REFS[family][field]),
        "waiver_reason_requirements": _reviewer_waiver_requirements(field),
        "manuscript_action": _reviewer_manuscript_action(family=family, field=field),
    }


def _authority_contract() -> dict[str, bool]:
    return {
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def _guideline_pack(study_archetype: str) -> dict[str, object]:
    return {
        "guideline_families": list(_GUIDELINE_FAMILIES[study_archetype]),
        "authority_contract": _authority_contract(),
    }


def _evidence_contract(*, family: str) -> dict[str, dict[str, object]]:
    return {
        field: {
            "blocker": f"missing_{field}",
            "required_evidence_refs": list(_REVIEWER_TEMPLATE_EVIDENCE_REFS[family][field]),
            "waiver_allowed": field not in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS,
        }
        for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS
    }


def build_statistical_reviewer_discipline_library() -> dict[str, Any]:
    archetypes: dict[str, dict[str, object]] = {}
    for study_archetype in SUPPORTED_STUDY_ARCHETYPES:
        family = _reviewer_template_family(study_archetype)
        templates = {
            field: _reviewer_template(family=family, field=field)
            for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS
        }
        archetypes[study_archetype] = {
            "study_archetype": study_archetype,
            "template_family": family,
            "label": _REVIEWER_FAMILY_LABELS[family],
            "guideline_pack": _guideline_pack(study_archetype),
            "evidence_contract": _evidence_contract(family=family),
            "templates": templates,
        }

    return {
        "surface": "statistical_reviewer_discipline_library",
        "schema_version": 1,
        "status": "ready",
        "supported_study_archetypes": list(SUPPORTED_STUDY_ARCHETYPES),
        "primary_evidence_rule": (
            "Nominal p-value, AUC-only, and cluster separation-only cannot be used as primary evidence."
        ),
        "fail_closed_fields": list(FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "archetypes": archetypes,
    }


def build_statistical_reviewer_template_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    study_archetype = _text(contract.get("study_archetype"))
    if study_archetype not in SUPPORTED_STUDY_ARCHETYPES:
        return {
            "surface": "statistical_reviewer_template_projection",
            "schema_version": 1,
            "status": "blocked",
            "reason_code": "unsupported_study_archetype",
            "study_archetype": study_archetype or None,
            "supported_inputs": {"study_archetypes": list(SUPPORTED_STUDY_ARCHETYPES)},
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }

    library = build_statistical_reviewer_discipline_library()
    archetype_library = _mapping(_mapping(library["archetypes"]).get(study_archetype))
    templates = _mapping(archetype_library.get("templates"))
    blockers: list[str] = []
    concern_cards: list[dict[str, object]] = []

    for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS:
        template = dict(_mapping(templates.get(field)))
        waiver_reason = _waiver_reason(contract, field)
        waiver_requirements = _mapping(template.get("waiver_reason_requirements"))
        waiver_allowed = waiver_requirements.get("waiver_allowed") is True
        value_present = _has_text(contract.get(field))
        nominal_primary_evidence = _contains_nominal_p_value(contract.get(field))
        status = "present"
        field_blockers: list[str] = []

        if nominal_primary_evidence:
            field_blockers.append("nominal_p_value_primary_evidence")
        if value_present and waiver_reason and waiver_allowed:
            status = "waived"
        elif not value_present:
            if waiver_reason and waiver_allowed:
                status = "waived"
            else:
                status = "blocked"
                field_blockers.append(f"missing_{field}")
        if waiver_reason and not waiver_allowed:
            status = "blocked"
            field_blockers.append(f"{field}_waiver_not_allowed")
        if nominal_primary_evidence:
            status = "blocked"

        blockers.extend(field_blockers)
        template["status"] = status
        template["required_for_ready"] = status == "blocked"
        template["blockers"] = field_blockers
        template["waiver_reason"] = waiver_reason if waiver_reason and waiver_allowed else ""
        concern_cards.append(template)

    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "surface": "statistical_reviewer_template_projection",
        "schema_version": 1,
        "status": "blocked" if unique_blockers else "ready",
        "study_archetype": study_archetype,
        "template_family": archetype_library["template_family"],
        "primary_evidence_rule": library["primary_evidence_rule"],
        "fail_closed_fields": list(FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS),
        "blockers": unique_blockers,
        "reviewer_concerns": concern_cards,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def build_statistical_discipline_contract(*, study_archetype: str) -> dict[str, Any]:
    archetype = _text(study_archetype)
    if archetype not in SUPPORTED_STUDY_ARCHETYPES:
        return {
            "status": "blocked",
            "reason_code": "unsupported_study_archetype",
            "study_archetype": archetype or None,
            "supported_inputs": {"study_archetypes": list(SUPPORTED_STUDY_ARCHETYPES)},
        }

    return {
        "status": "resolved",
        "study_archetype": archetype,
        "primary_evidence_rule": (
            "Effect size, precision, calibration, validation, and clinical utility must anchor the claim; "
            "nominal p-value, AUC-only, or cluster separation-only evidence cannot be primary evidence."
        ),
        "guideline_pack": _guideline_pack(archetype),
        "evidence_contract": _evidence_contract(family=_reviewer_template_family(archetype)),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        **_ARCHETYPE_DISCIPLINE[archetype],
    }


def build_statistical_discipline_operations_projection(
    contract: Mapping[str, Any],
    bounded_board: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    blockers: list[str] = []
    waivers: list[dict[str, str]] = []
    action_cards: list[dict[str, object]] = []

    for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS:
        field_blockers, waiver, action_card = _operation_field_projection(contract=contract, field=field)
        blockers.extend(field_blockers)
        if waiver:
            waivers.append(waiver)
        action_cards.append(action_card)

    board_blockers, board_action_cards = _bounded_board_top_level_projection(bounded_board)
    blockers.extend(board_blockers)
    action_cards.extend(board_action_cards)

    for index, candidate in enumerate(_bounded_board_candidates(bounded_board)):
        candidate_blockers, candidate_action_cards = _bounded_board_candidate_projection(
            index=index,
            candidate=candidate,
        )
        blockers.extend(candidate_blockers)
        action_cards.extend(candidate_action_cards)

    unique_blockers = list(dict.fromkeys(blockers))
    return {
        "surface": "statistical_discipline_operations",
        "schema_version": 1,
        "status": "blocked" if unique_blockers else "partial" if waivers else "ready",
        "blockers": unique_blockers,
        "waivers": waivers,
        "action_cards": action_cards,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


def validate_statistical_discipline_contract(payload: Mapping[str, Any]) -> dict[str, str]:
    if _text(payload.get("status")) != "resolved":
        return {"status": "blocked", "reason_code": _text(payload.get("reason_code")) or "contract_not_resolved"}
    if _text(payload.get("study_archetype")) not in SUPPORTED_STUDY_ARCHETYPES:
        return {"status": "blocked", "reason_code": "unsupported_study_archetype"}
    for field in REQUIRED_STATISTICAL_DISCIPLINE_FIELDS:
        if field in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS and not _has_text(payload.get(field)):
            return {"status": "blocked", "reason_code": f"missing_{field}"}
        if field in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS and _waiver_reason(payload, field):
            return {"status": "blocked", "reason_code": f"{field}_waiver_not_allowed"}
        if not _has_text(payload.get(field)) and not _waiver_reason(payload, field):
            return {"status": "blocked", "reason_code": f"missing_{field}"}
    if _contains_forbidden_evidence_classification(payload):
        return {"status": "blocked", "reason_code": "forbidden_evidence_classification"}
    primary_evidence_violation = _primary_evidence_violation_reason(payload)
    if primary_evidence_violation:
        return {"status": "blocked", "reason_code": primary_evidence_violation}
    return {"status": "present", "reason_code": ""}


def _mapping(value: object) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _validate_statistical_reviewer_section(
    *,
    section_key: str,
    section: Mapping[str, Any],
) -> dict[str, str]:
    status = _text(section.get("status"))
    if status not in SUPPORTED_STATISTICAL_REVIEWER_SECTION_STATUSES:
        return {"status": "blocked", "reason_code": f"{section_key}_not_passed"}
    for field in REQUIRED_STATISTICAL_REVIEWER_SECTION_FIELDS:
        value = section.get(field)
        if field == "evidence_refs":
            if not _sequence(value):
                return {"status": "blocked", "reason_code": f"{section_key}_missing_{field}"}
        elif not _has_text(value):
            return {"status": "blocked", "reason_code": f"{section_key}_missing_{field}"}
    if _contains_forbidden_evidence_classification(section):
        return {"status": "blocked", "reason_code": f"{section_key}_forbidden_evidence_classification"}
    primary_evidence_violation = _primary_evidence_violation_reason(section)
    if primary_evidence_violation:
        return {"status": "blocked", "reason_code": f"{section_key}_{primary_evidence_violation}"}
    return {"status": "present", "reason_code": ""}


def _validate_causal_language_boundary(sections: Mapping[str, Any]) -> dict[str, str]:
    causal_boundary = _mapping(sections.get("causal_language_boundary"))
    forbidden_language = _sequence(causal_boundary.get("forbidden_language"))
    if not forbidden_language:
        return {"status": "blocked", "reason_code": "causal_language_boundary_missing_forbidden_language"}
    return {"status": "present", "reason_code": ""}


def validate_statistical_reviewer_audit(payload: Mapping[str, Any]) -> dict[str, str]:
    if _text(payload.get("status")) != "resolved":
        return {"status": "blocked", "reason_code": _text(payload.get("reason_code")) or "audit_not_resolved"}
    if _text(payload.get("reviewer_role")) != "statistical_reviewer":
        return {"status": "blocked", "reason_code": "missing_statistical_reviewer_role"}

    sections = _mapping(payload.get("sections"))
    if not sections:
        return {"status": "blocked", "reason_code": "missing_sections"}
    for section_key in REQUIRED_STATISTICAL_REVIEWER_AUDIT_SECTIONS:
        section = _mapping(sections.get(section_key))
        if not section:
            return {"status": "blocked", "reason_code": f"missing_{section_key}"}
        section_result = _validate_statistical_reviewer_section(section_key=section_key, section=section)
        if section_result["status"] != "present":
            return section_result

    return _validate_causal_language_boundary(sections)


def validate_bounded_analysis_candidate_board(payload: Mapping[str, Any]) -> dict[str, str]:
    candidates = [candidate for candidate in _sequence(payload.get("candidates")) if isinstance(candidate, Mapping)]
    if not candidates:
        return {"status": "blocked", "reason_code": "missing_candidates"}

    for candidate in candidates:
        for field in REQUIRED_CANDIDATE_FIELDS:
            if not _has_text(candidate.get(field)):
                return {"status": "blocked", "reason_code": f"candidate_missing_{field}"}
        if _text(candidate.get("decision")) not in SUPPORTED_CANDIDATE_DECISIONS:
            return {"status": "blocked", "reason_code": "candidate_unsupported_decision"}
        if _contains_forbidden_evidence_classification(candidate):
            return {"status": "blocked", "reason_code": "candidate_forbidden_evidence_classification"}
        primary_evidence_violation = _primary_evidence_violation_reason(candidate)
        if primary_evidence_violation:
            return {"status": "blocked", "reason_code": f"candidate_{primary_evidence_violation}"}

    return {"status": "present", "reason_code": ""}
