from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers.statistical_discipline_runtime_parts.reference_data import (
    FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS,
    METRIC_ONLY_PRIMARY_EVIDENCE_TERMS,
    NOMINAL_P_VALUE_TERMS,
    PRIMARY_EVIDENCE_KEYS,
    STATISTICAL_DISCIPLINE_OPERATION_FIELDS,
)


FIELD_QUESTION_SPECS: dict[str, dict[str, str]] = {
    "missingness_plan": {
        "question_key": "missingness",
        "question": "How are missing data measured, handled, and stress-tested for the active claim?",
        "claim_impact": (
            "Missing data can distort denominators, predictor availability, endpoint capture, and site "
            "comparability, so the claim may reflect ascertainment bias rather than the target population."
        ),
    },
    "sample_size_precision_plan": {
        "question_key": "precision_sample_size",
        "question": "Is the claim supported by sample size, event counts, and interval precision?",
        "claim_impact": (
            "A claim needs denominator support, effective sample size, event counts, and uncertainty; "
            "a nominal p-value alone cannot establish effect magnitude, calibration reliability, or "
            "clinical stability."
        ),
    },
    "external_validation_plan": {
        "question_key": "external_validation",
        "question": "What external, temporal, or site-held-out evidence supports transportability?",
        "claim_impact": (
            "Without independent validation evidence, a generalizable claim remains internal to the "
            "observed cohort, model version, site mix, or case-mix setting."
        ),
    },
    "subgroup_plan": {
        "question_key": "subgroup",
        "question": "Which prespecified clinical strata can support subgroup interpretation?",
        "claim_impact": (
            "Unsupported subgroup language can overstate heterogeneity, fairness, or clinical applicability "
            "when slice support and uncertainty do not sustain the claim."
        ),
    },
    "multiplicity_guardrail": {
        "question_key": "multiplicity",
        "question": "Which tests, endpoints, thresholds, and subgroup families are confirmatory?",
        "claim_impact": (
            "Repeated comparisons can turn exploratory signals into false-positive claim support unless "
            "primary families and interpretation boundaries are locked."
        ),
    },
    "clinical_utility_plan": {
        "question_key": "clinical_utility",
        "question": "How does the statistical result change a threshold, workflow, or care decision?",
        "claim_impact": (
            "A statistical signal does not sustain a clinical claim unless it maps to actionability, "
            "decision thresholds, workflow consequences, or care-pathway interpretation."
        ),
    },
    "endpoint_time_window": {
        "question_key": "endpoint_time_window",
        "question": "Are endpoint definitions, index time, lookback, horizon, and follow-up windows locked?",
        "claim_impact": (
            "Endpoint and time-window ambiguity changes who is at risk, what outcome is counted, and when "
            "follow-up closes, which can invalidate the claim semantics."
        ),
    },
    "sensitivity_plan": {
        "question_key": "sensitivity",
        "question": "Which robustness checks could falsify or qualify the active claim?",
        "claim_impact": (
            "Sensitivity analyses show whether the claim survives plausible changes in coding, missingness, "
            "thresholds, model assumptions, site support, or endpoint timing."
        ),
    },
}


def operation_field_status(
    *,
    value_present: bool,
    nominal_primary_evidence: bool,
    waiver_reason: str,
    waiver_allowed: bool,
    waiver_incomplete: bool,
) -> str:
    if waiver_incomplete:
        return "blocked"
    if value_present and not nominal_primary_evidence:
        return "waived" if waiver_reason and waiver_allowed else "present"
    if waiver_reason and waiver_allowed:
        return "waived"
    return "blocked"


def operation_field_blockers(
    *,
    field: str,
    value_present: bool,
    nominal_primary_evidence: bool,
    waiver_reason: str,
    waiver_allowed: bool,
    waiver_incomplete: bool,
) -> list[str]:
    blockers = []
    if not value_present and (not waiver_reason or not waiver_allowed):
        blockers.append(f"missing_{field}")
    if waiver_incomplete and waiver_allowed:
        blockers.append(f"incomplete_{field}_waiver")
    if nominal_primary_evidence:
        blockers.append("nominal_p_value_primary_evidence")
    if waiver_reason and not waiver_allowed:
        blockers.append(f"{field}_waiver_not_allowed")
    return blockers


def reviewer_template_field_projection(
    *,
    field: str,
    template: dict[str, Any],
    waiver_reason: str,
    waiver_incomplete: bool,
    waiver_allowed: bool,
    value_present: bool,
    nominal_primary_evidence: bool,
) -> tuple[list[str], dict[str, object]]:
    status = operation_field_status(
        value_present=value_present,
        nominal_primary_evidence=nominal_primary_evidence,
        waiver_reason=waiver_reason,
        waiver_allowed=waiver_allowed,
        waiver_incomplete=waiver_incomplete,
    )
    field_blockers = operation_field_blockers(
        field=field,
        value_present=value_present,
        nominal_primary_evidence=nominal_primary_evidence,
        waiver_reason=waiver_reason,
        waiver_allowed=waiver_allowed,
        waiver_incomplete=waiver_incomplete,
    )
    updated_template = dict(template)
    updated_template["status"] = status
    updated_template["required_for_ready"] = status == "blocked"
    updated_template["blockers"] = field_blockers
    updated_template["waiver_reason"] = waiver_reason if waiver_reason and waiver_allowed else ""
    return field_blockers, updated_template


def waiver_allowed_from_template(template: Mapping[str, Any]) -> bool:
    waiver_requirements = template.get("waiver_reason_requirements")
    return isinstance(waiver_requirements, Mapping) and waiver_requirements.get("waiver_allowed") is True


def _text(value: object) -> str:
    return str(value or "").strip()


def _has_text(value: object) -> bool:
    return bool(_text(value))


def _sequence(value: object) -> Sequence[object]:
    if isinstance(value, list | tuple):
        return value
    return ()


def _structured_waiver(payload: Mapping[str, Any], field: str) -> Mapping[str, Any]:
    waivers = payload.get("waivers")
    if isinstance(waivers, Mapping):
        waiver = waivers.get(field)
        return waiver if isinstance(waiver, Mapping) else {}
    for waiver in _sequence(waivers):
        if isinstance(waiver, Mapping) and _text(waiver.get("field")) == field:
            return waiver
    return {}


def _waiver_reason(payload: Mapping[str, Any], field: str) -> str:
    waiver = _structured_waiver(payload, field)
    if waiver:
        return _text(waiver.get("reason"))
    waivers = payload.get("waivers")
    if isinstance(waivers, Mapping):
        value = waivers.get(field)
        if isinstance(value, Mapping):
            return _text(value.get("reason"))
        return _text(value)
    for key in (f"{field}_waiver_reason", f"waiver_reason_{field}"):
        reason = _text(payload.get(key))
        if reason:
            return reason
    return ""


def _machine_checkable_waiver_payload(
    payload: Mapping[str, Any],
    field: str,
) -> dict[str, object] | None:
    waiver = _structured_waiver(payload, field)
    if waiver:
        return {
            "field": field,
            "reason": _text(waiver.get("reason")),
            "claim_boundary": _text(waiver.get("claim_boundary")),
            "evidence_refs": list(_sequence(waiver.get("evidence_refs"))),
            "reviewer_visible_artifact": _text(waiver.get("reviewer_visible_artifact")),
            "source": "statistical_discipline_contract",
        }
    reason = _waiver_reason(payload, field)
    if reason:
        return {
            "field": field,
            "reason": reason,
            "claim_boundary": "",
            "evidence_refs": [],
            "reviewer_visible_artifact": "",
            "source": "statistical_discipline_contract",
        }
    return None


def _waiver_payload_complete(waiver: Mapping[str, object]) -> bool:
    return all(
        (
            _has_text(waiver.get("reason")),
            _has_text(waiver.get("claim_boundary")),
            bool(_sequence(waiver.get("evidence_refs"))),
            _has_text(waiver.get("reviewer_visible_artifact")),
        )
    )


def _blocker_ref(*, reason_code: str, field: str) -> dict[str, str]:
    return {
        "reason_code": reason_code,
        "field": field,
        "source": "statistical_discipline_contract",
    }


def _contains_nominal_p_value(text: object) -> bool:
    normalized = _text(text).lower()
    return bool(normalized and any(term in normalized for term in NOMINAL_P_VALUE_TERMS))


def _metric_only_primary_evidence_reason(text: object) -> str:
    normalized = _text(text).lower()
    if not normalized:
        return ""
    for reason_code, terms in METRIC_ONLY_PRIMARY_EVIDENCE_TERMS.items():
        if any(term in normalized for term in terms):
            return reason_code
    return ""


def _primary_evidence_violation_reason(text: object) -> str:
    if _contains_nominal_p_value(text):
        return "nominal_p_value_primary_evidence"
    return _metric_only_primary_evidence_reason(text)


def _field_blocker_refs(contract: Mapping[str, Any], field: str) -> list[dict[str, str]]:
    blocker_refs: list[dict[str, str]] = []
    waiver_reason = _waiver_reason(contract, field)
    waiver_payload = _machine_checkable_waiver_payload(contract, field)
    waiver_complete = bool(waiver_payload and _waiver_payload_complete(waiver_payload))
    waiver_allowed = field not in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS
    if not _has_text(contract.get(field)) and (not waiver_reason or not waiver_allowed):
        blocker_refs.append(_blocker_ref(reason_code=f"missing_{field}", field=field))
    if waiver_payload and not waiver_complete and waiver_allowed:
        blocker_refs.append(_blocker_ref(reason_code=f"incomplete_{field}_waiver", field=field))
    if waiver_reason and not waiver_allowed:
        blocker_refs.append(_blocker_ref(reason_code=f"{field}_waiver_not_allowed", field=field))
    field_evidence_violation = _primary_evidence_violation_reason(contract.get(field))
    if field_evidence_violation:
        blocker_refs.append(_blocker_ref(reason_code=field_evidence_violation, field=field))
    return blocker_refs


def _field_status(
    *,
    blocker_refs: Sequence[Mapping[str, str]],
    waiver_payload: Mapping[str, object] | None,
    waiver_allowed: bool,
) -> str:
    if blocker_refs:
        return "blocked"
    if waiver_payload and waiver_allowed and _waiver_payload_complete(waiver_payload):
        return "waived"
    return "present"


def _field_question(contract: Mapping[str, Any], field: str) -> tuple[dict[str, object], dict[str, object] | None]:
    spec = FIELD_QUESTION_SPECS[field]
    blocker_refs = _field_blocker_refs(contract, field)
    waiver_payload = _machine_checkable_waiver_payload(contract, field)
    waiver_allowed = field not in FAIL_CLOSED_STATISTICAL_DISCIPLINE_FIELDS
    waiver_ref = (
        waiver_payload
        if waiver_payload and waiver_allowed and _waiver_payload_complete(waiver_payload)
        else None
    )
    question = {
        "field": field,
        "question_key": spec["question_key"],
        "question": spec["question"],
        "claim_impact": spec["claim_impact"],
        "status": _field_status(
            blocker_refs=blocker_refs,
            waiver_payload=waiver_payload,
            waiver_allowed=waiver_allowed,
        ),
        "blocker_refs": blocker_refs,
        "waiver_ref": waiver_ref,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    return question, waiver_ref


def _core_evidence_blocker_refs(contract: Mapping[str, Any]) -> list[dict[str, str]]:
    blocker_refs: list[dict[str, str]] = []
    for field in PRIMARY_EVIDENCE_KEYS:
        violation_reason = _primary_evidence_violation_reason(contract.get(field))
        if violation_reason:
            blocker_refs.append(_blocker_ref(reason_code=violation_reason, field=field))
    return blocker_refs


def _unique_refs(refs: Sequence[Mapping[str, str]]) -> list[dict[str, str]]:
    unique: dict[tuple[str, str, str], dict[str, str]] = {}
    for ref in refs:
        reason_code = _text(ref.get("reason_code"))
        field = _text(ref.get("field"))
        source = _text(ref.get("source"))
        key = (reason_code, field, source)
        if reason_code and field and source and key not in unique:
            unique[key] = {
                "reason_code": reason_code,
                "field": field,
                "source": source,
            }
    return list(unique.values())


def _unique_reason_codes(refs: Sequence[Mapping[str, str]]) -> list[str]:
    return list(dict.fromkeys(_text(ref.get("reason_code")) for ref in refs if _text(ref.get("reason_code"))))


def build_statistical_field_projection(contract: Mapping[str, Any]) -> dict[str, Any]:
    field_questions: list[dict[str, object]] = []
    waiver_refs: list[dict[str, object]] = []
    field_blocker_refs: list[dict[str, str]] = []
    for field in STATISTICAL_DISCIPLINE_OPERATION_FIELDS:
        question, waiver_ref = _field_question(contract, field)
        field_questions.append(question)
        field_blocker_refs.extend(question["blocker_refs"])
        if waiver_ref:
            waiver_refs.append(waiver_ref)

    core_evidence_blocker_refs = _unique_refs(_core_evidence_blocker_refs(contract))
    blocker_refs = _unique_refs([*field_blocker_refs, *core_evidence_blocker_refs])
    blockers = _unique_reason_codes(blocker_refs)
    return {
        "surface": "statistical_field_projection",
        "schema_version": 1,
        "status": "blocked" if blockers else "partial" if waiver_refs else "ready",
        "blockers": blockers,
        "blocker_refs": blocker_refs,
        "waiver_refs": waiver_refs,
        "field_questions": field_questions,
        "core_evidence_rule": (
            "AUC-only, nominal p-value, and cluster separation-only cannot be used as core evidence "
            "for the active scientific claim."
        ),
        "core_evidence_blocker_refs": core_evidence_blocker_refs,
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }


__all__ = [
    "FIELD_QUESTION_SPECS",
    "build_statistical_field_projection",
    "operation_field_blockers",
    "operation_field_status",
    "reviewer_template_field_projection",
    "waiver_allowed_from_template",
]
