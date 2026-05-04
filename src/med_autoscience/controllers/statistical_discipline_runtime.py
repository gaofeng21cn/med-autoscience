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
    if value_present and not nominal_primary_evidence:
        status = "waived" if waiver_reason else "present"
    elif waiver_reason:
        status = "waived"
    else:
        status = "blocked"

    blockers = []
    if not value_present and not waiver_reason:
        blockers.append(f"missing_{field}")
    if nominal_primary_evidence:
        blockers.append("nominal_p_value_primary_evidence")
    waiver = {"field": field, "reason": waiver_reason} if waiver_reason else None
    return blockers, waiver, _operation_action_card(
        action_id=f"resolve_{field}",
        label=_OPERATION_FIELD_LABELS[field],
        summary=_OPERATION_FIELD_SUMMARIES[field],
        field=field,
        status=status,
        waiver_allowed=True,
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
    if _contains_nominal_p_value_primary_evidence(candidate):
        blockers.append(f"candidate_{index}_nominal_p_value_primary_evidence")

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
        "primary_evidence_rule": "Effect size, precision, calibration, validation, and clinical utility must anchor the claim; nominal p-value alone cannot be primary evidence.",
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
        if not _has_text(payload.get(field)) and not _waiver_reason(payload, field):
            return {"status": "blocked", "reason_code": f"missing_{field}"}
    if _contains_forbidden_evidence_classification(payload):
        return {"status": "blocked", "reason_code": "forbidden_evidence_classification"}
    if _contains_nominal_p_value_primary_evidence(payload):
        return {"status": "blocked", "reason_code": "nominal_p_value_primary_evidence"}
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
    if _contains_nominal_p_value_primary_evidence(section):
        return {"status": "blocked", "reason_code": f"{section_key}_nominal_p_value_primary_evidence"}
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
        if _contains_nominal_p_value_primary_evidence(candidate):
            return {"status": "blocked", "reason_code": "candidate_nominal_p_value_primary_evidence"}

    return {"status": "present", "reason_code": ""}
