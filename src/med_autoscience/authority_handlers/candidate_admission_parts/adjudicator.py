"""Independent adjudicator receipt and waiver normalization."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    enum_text,
    exact_keys,
    fingerprint,
    mapping,
    optional_text,
    sha256,
    text,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from .._record_validation import (
    exact_ref_list as _exact_ref_list,
)
from .._record_validation import (
    typed_ref as _typed_ref,
)
from .._record_validation import (
    typed_ref_list as _typed_ref_list,
)
from .candidate import (
    _candidate_exact_ref,
    _normalize_claim_scope,
)
from .policy import (
    _ACCEPT_CODES,
    _ALL_DECISION_CODES,
    _REJECT_CODES,
    _ROUTE_CODES,
    _WAIVER_CODES,
)
from .receipt_integrity import _validate_embedded_receipt


def _normalize_adjudicator_context(value: Any) -> dict[str, Any]:
    field = "adjudicator_context"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "producer_attempt_ref",
            "adjudicator_attempt_ref",
            "candidate_packet_ref",
            "admission_request_ref",
            "adjudicator_receipt_ref",
            "currentness_receipt_ref",
        },
        field,
    )
    normalized = {
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            f"{field}.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "adjudicator_attempt_ref": _typed_ref(
            payload.get("adjudicator_attempt_ref"),
            f"{field}.adjudicator_attempt_ref",
            "opl_stage_attempt",
        ),
        "candidate_packet_ref": _exact_ref(
            payload.get("candidate_packet_ref"),
            f"{field}.candidate_packet_ref",
            "opl_action_output",
        ),
        "admission_request_ref": _exact_ref(
            payload.get("admission_request_ref"),
            f"{field}.admission_request_ref",
            "opl_action_output",
        ),
        "adjudicator_receipt_ref": _exact_ref(
            payload.get("adjudicator_receipt_ref"),
            f"{field}.adjudicator_receipt_ref",
            "mas_candidate_adjudicator_receipt",
        ),
        "currentness_receipt_ref": _exact_ref(
            payload.get("currentness_receipt_ref"),
            f"{field}.currentness_receipt_ref",
            "mas_generation_currentness_receipt",
        ),
    }
    if (
        normalized["producer_attempt_ref"]["ref"]
        == normalized["adjudicator_attempt_ref"]["ref"]
        or normalized["producer_attempt_ref"]["sha256"]
        == normalized["adjudicator_attempt_ref"]["sha256"]
    ):
        raise RequestShapeError(
            "adjudicator attempt must be independent from the candidate producer attempt"
        )
    return normalized


def _normalize_adjudicator_receipt(value: Any) -> dict[str, Any]:
    field = "adjudicator_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_epoch",
            "producer_attempt_ref",
            "adjudicator_attempt_ref",
            "candidate_packet_ref",
            "admission_request_ref",
            "generation_id",
            "generation_manifest_ref",
            "candidate_id",
            "candidate_ref",
            "evidence_refs",
            "claim_scope",
            "candidate_record_sha256",
            "verdict",
            "decision_code",
            "next_owner",
            "resume_condition",
            "waiver",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_candidate_adjudicator_receipt":
        raise RequestShapeError(
            "adjudicator_receipt.receipt_kind must be mas_candidate_adjudicator_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("adjudicator_receipt.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError("adjudicator_receipt.owner must be MedAutoScience")
    if payload.get("authority_role") != "independent_medical_adjudicator":
        raise RequestShapeError(
            "adjudicator_receipt.authority_role must be independent_medical_adjudicator"
        )
    verdict = enum_text(
        payload.get("verdict"),
        "adjudicator_receipt.verdict",
        {"accepted", "rejected", "route_back", "waived"},
    )
    decision_code = enum_text(
        payload.get("decision_code"),
        "adjudicator_receipt.decision_code",
        _ALL_DECISION_CODES,
    )
    next_owner = optional_text(
        payload.get("next_owner"), "adjudicator_receipt.next_owner"
    )
    resume_condition = optional_text(
        payload.get("resume_condition"), "adjudicator_receipt.resume_condition"
    )
    waiver = _normalize_waiver(payload.get("waiver"), "adjudicator_receipt.waiver")
    if verdict == "accepted" and decision_code not in _ACCEPT_CODES:
        raise RequestShapeError(
            "accepted adjudicator receipt requires an acceptance code"
        )
    if verdict == "rejected" and decision_code not in _REJECT_CODES:
        raise RequestShapeError(
            "rejected adjudicator receipt requires a rejection code"
        )
    if verdict == "route_back" and decision_code not in _ROUTE_CODES:
        raise RequestShapeError(
            "route-back adjudicator receipt requires a typed route code"
        )
    if verdict == "waived" and decision_code != "waived_with_typed_scope":
        raise RequestShapeError(
            "waived adjudicator receipt requires waived_with_typed_scope"
        )
    if verdict == "route_back":
        if next_owner is None or resume_condition is None or waiver is not None:
            raise RequestShapeError(
                "route-back adjudicator receipt requires next_owner/resume_condition and no waiver"
            )
    elif verdict == "waived":
        if waiver is None or next_owner is not None or resume_condition is not None:
            raise RequestShapeError(
                "waived adjudicator receipt requires one typed waiver and no route fields"
            )
    elif any(
        (next_owner is not None, resume_condition is not None, waiver is not None)
    ):
        raise RequestShapeError(
            "accepted/rejected adjudicator receipt cannot carry route or waiver fields"
        )
    core = {
        "receipt_kind": "mas_candidate_adjudicator_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "independent_medical_adjudicator",
        "authority_epoch": text(
            payload.get("authority_epoch"), "adjudicator_receipt.authority_epoch"
        ),
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            "adjudicator_receipt.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "adjudicator_attempt_ref": _typed_ref(
            payload.get("adjudicator_attempt_ref"),
            "adjudicator_receipt.adjudicator_attempt_ref",
            "opl_stage_attempt",
        ),
        "candidate_packet_ref": _exact_ref(
            payload.get("candidate_packet_ref"),
            "adjudicator_receipt.candidate_packet_ref",
            "opl_action_output",
        ),
        "admission_request_ref": _exact_ref(
            payload.get("admission_request_ref"),
            "adjudicator_receipt.admission_request_ref",
            "opl_action_output",
        ),
        "generation_id": text(
            payload.get("generation_id"), "adjudicator_receipt.generation_id"
        ),
        "generation_manifest_ref": _exact_ref(
            payload.get("generation_manifest_ref"),
            "adjudicator_receipt.generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "candidate_id": text(
            payload.get("candidate_id"), "adjudicator_receipt.candidate_id"
        ),
        "candidate_ref": _exact_ref(
            payload.get("candidate_ref"),
            "adjudicator_receipt.candidate_ref",
            "mas_artifact",
        ),
        "evidence_refs": _exact_ref_list(
            payload.get("evidence_refs"),
            "adjudicator_receipt.evidence_refs",
            "mas_evidence",
            dedupe_size=False,
        ),
        "claim_scope": _normalize_claim_scope(
            payload.get("claim_scope"), "adjudicator_receipt.claim_scope"
        ),
        "candidate_record_sha256": sha256(
            payload.get("candidate_record_sha256"),
            "adjudicator_receipt.candidate_record_sha256",
        ),
        "verdict": verdict,
        "decision_code": decision_code,
        "next_owner": next_owner,
        "resume_condition": resume_condition,
        "waiver": waiver,
    }
    return _validate_embedded_receipt(
        payload,
        core,
        field=field,
        id_prefix="mas-candidate-adjudicator",
    )


def _normalize_waiver(value: Any, field: str) -> dict[str, Any] | None:
    if value is None:
        return None
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "waiver_kind",
            "waiver_code",
            "scope",
            "evidence_refs",
            "expires_on_generation_change",
            "authorizes_manuscript_consumption",
        },
        field,
    )
    if payload.get("waiver_kind") != "mas_candidate_admission_waiver":
        raise RequestShapeError(
            f"{field}.waiver_kind must be mas_candidate_admission_waiver"
        )
    if payload.get("expires_on_generation_change") is not True:
        raise RequestShapeError(f"{field}.expires_on_generation_change must be true")
    if payload.get("authorizes_manuscript_consumption") is not False:
        raise RequestShapeError(
            f"{field}.authorizes_manuscript_consumption must be false"
        )
    refs = _typed_ref_list(
        payload.get("evidence_refs"), f"{field}.evidence_refs", "mas_evidence"
    )
    if not refs:
        raise RequestShapeError(f"{field}.evidence_refs must not be empty")
    return {
        "waiver_kind": "mas_candidate_admission_waiver",
        "waiver_code": enum_text(
            payload.get("waiver_code"), f"{field}.waiver_code", _WAIVER_CODES
        ),
        "scope": enum_text(
            payload.get("scope"),
            f"{field}.scope",
            {"candidate_record_only", "provenance_only", "quality_debt_only"},
        ),
        "evidence_refs": refs,
        "expires_on_generation_change": True,
        "authorizes_manuscript_consumption": False,
    }


def _validate_adjudicator_receipt(request: Mapping[str, Any]) -> None:
    context = request["adjudicator_context"]
    manifest = request["generation_manifest"]
    currentness = request["currentness_receipt"]
    candidate = request["candidate"]
    receipt = request["adjudicator_receipt"]
    receipt_ref = context["adjudicator_receipt_ref"]
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
    ):
        raise RequestShapeError(
            "adjudicator_receipt_ref size/hash does not match adjudicator_receipt"
        )
    comparisons = {
        "authority_epoch": (
            receipt["authority_epoch"],
            currentness["authority_epoch"],
        ),
        "adjudicator_attempt_ref": (
            receipt["adjudicator_attempt_ref"],
            context["adjudicator_attempt_ref"],
        ),
        "producer_attempt_ref": (
            receipt["producer_attempt_ref"],
            context["producer_attempt_ref"],
        ),
        "candidate_packet_ref": (
            receipt["candidate_packet_ref"],
            context["candidate_packet_ref"],
        ),
        "admission_request_ref": (
            receipt["admission_request_ref"],
            context["admission_request_ref"],
        ),
        "generation_id": (receipt["generation_id"], manifest["generation_id"]),
        "generation_manifest_ref": (
            receipt["generation_manifest_ref"],
            request["generation_manifest_ref"],
        ),
        "candidate_id": (
            receipt["candidate_id"],
            candidate["candidate_id"],
        ),
        "candidate_ref": (
            receipt["candidate_ref"],
            _candidate_exact_ref(candidate),
        ),
        "evidence_refs": (
            receipt["evidence_refs"],
            [
                {
                    "kind": item["kind"],
                    "ref": item["ref"],
                    "size_bytes": item["size_bytes"],
                    "sha256": item["sha256"],
                }
                for item in candidate["evidence_members"]
            ],
        ),
        "claim_scope": (
            receipt["claim_scope"],
            candidate["claim_scope"],
        ),
        "candidate_record_sha256": (
            receipt["candidate_record_sha256"],
            fingerprint(candidate),
        ),
    }
    mismatches = [name for name, (left, right) in comparisons.items() if left != right]
    if mismatches:
        raise RequestShapeError(
            "adjudicator_receipt is not bound to current exact records: "
            + ", ".join(mismatches)
        )
    if receipt["verdict"] == "accepted":
        scope = candidate["claim_scope"]
        if not scope["claim_ids"] or not scope["permitted_sections"]:
            raise RequestShapeError(
                "accepted adjudicator receipt requires claim_ids and permitted_sections"
            )
        if (
            receipt["decision_code"] == "accepted_for_bounded_sensitivity_use"
            and not scope["sensitivity_only"]
        ):
            raise RequestShapeError(
                "bounded-sensitivity acceptance requires sensitivity_only claim scope"
            )
        if scope["sensitivity_only"] and scope["abstract_headline_allowed"]:
            raise RequestShapeError(
                "sensitivity-only claim scope cannot allow an abstract headline"
            )


def _adjudicator_refs(request: Mapping[str, Any]) -> dict[str, Any]:
    context = request["adjudicator_context"]
    return {
        "producer_attempt_ref": dict(context["producer_attempt_ref"]),
        "adjudicator_attempt_ref": dict(context["adjudicator_attempt_ref"]),
        "candidate_packet_ref": dict(context["candidate_packet_ref"]),
        "admission_request_ref": dict(context["admission_request_ref"]),
        "adjudicator_receipt_ref": dict(context["adjudicator_receipt_ref"]),
    }


def _normalize_adjudicator_refs(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "producer_attempt_ref",
            "adjudicator_attempt_ref",
            "candidate_packet_ref",
            "admission_request_ref",
            "adjudicator_receipt_ref",
        },
        field,
    )
    return {
        "producer_attempt_ref": _typed_ref(
            payload.get("producer_attempt_ref"),
            f"{field}.producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "adjudicator_attempt_ref": _typed_ref(
            payload.get("adjudicator_attempt_ref"),
            f"{field}.adjudicator_attempt_ref",
            "opl_stage_attempt",
        ),
        "candidate_packet_ref": _exact_ref(
            payload.get("candidate_packet_ref"),
            f"{field}.candidate_packet_ref",
            "opl_action_output",
        ),
        "admission_request_ref": _exact_ref(
            payload.get("admission_request_ref"),
            f"{field}.admission_request_ref",
            "opl_action_output",
        ),
        "adjudicator_receipt_ref": _exact_ref(
            payload.get("adjudicator_receipt_ref"),
            f"{field}.adjudicator_receipt_ref",
            "mas_candidate_adjudicator_receipt",
        ),
    }
