"""Downstream candidate-admission receipt normalization."""

from __future__ import annotations

from typing import Any, cast

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    sha256,
    text,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from .._record_validation import (
    exact_ref_list as _exact_ref_list,
)
from .adjudicator import _normalize_adjudicator_refs
from .candidate import (
    _normalize_claim_scope,
    _normalize_manifest_member,
    _normalize_mission,
)
from .policy import _ACCEPT_CODES, _REJECT_CODES


def normalize_candidate_admission_receipt(
    value: Any,
    field: str = "candidate_admission_receipt",
) -> dict[str, Any]:
    """Validate an exact accepted/rejected receipt for downstream consumption."""

    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "mission_identity",
            "adjudicator_refs",
            "currentness_receipt_ref",
            "authority_epoch",
            "generation_id",
            "generation_manifest_ref",
            "source_input_digest",
            "candidate_id",
            "candidate_ref",
            "candidate_size_bytes",
            "evidence_refs",
            "claim_scope",
            "disposition",
            "decision_code",
            "authorizes_manuscript_consumption",
            "authorizes_publication_or_submission",
            "requires_host_exact_byte_persistence",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_candidate_admission_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_candidate_admission_receipt"
        )
    if payload.get("schema_version") != 2 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 2")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")

    disposition = enum_text(
        payload.get("disposition"), f"{field}.disposition", {"accepted", "rejected"}
    )
    decision_code = enum_text(
        payload.get("decision_code"),
        f"{field}.decision_code",
        _ACCEPT_CODES | _REJECT_CODES,
    )
    if disposition == "accepted" and decision_code not in _ACCEPT_CODES:
        raise RequestShapeError(f"{field}.decision_code is not an acceptance code")
    if disposition == "rejected" and decision_code not in _REJECT_CODES:
        raise RequestShapeError(f"{field}.decision_code is not a rejection code")
    expected_authorization = disposition == "accepted"
    if payload.get("authorizes_manuscript_consumption") is not expected_authorization:
        raise RequestShapeError(
            f"{field}.authorizes_manuscript_consumption does not match disposition"
        )
    if payload.get("authorizes_publication_or_submission") is not False:
        raise RequestShapeError(
            f"{field}.authorizes_publication_or_submission must be false"
        )
    if payload.get("requires_host_exact_byte_persistence") is not True:
        raise RequestShapeError(
            f"{field}.requires_host_exact_byte_persistence must be true"
        )

    core = {
        "receipt_kind": "mas_candidate_admission_receipt",
        "schema_version": 2,
        "owner": "MedAutoScience",
        "mission_identity": _normalize_mission(
            payload.get("mission_identity"), f"{field}.mission_identity"
        ),
        "adjudicator_refs": _normalize_adjudicator_refs(
            payload.get("adjudicator_refs"), f"{field}.adjudicator_refs"
        ),
        "currentness_receipt_ref": _exact_ref(
            payload.get("currentness_receipt_ref"),
            f"{field}.currentness_receipt_ref",
            "mas_generation_currentness_receipt",
        ),
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "generation_id": text(payload.get("generation_id"), f"{field}.generation_id"),
        "generation_manifest_ref": _exact_ref(
            payload.get("generation_manifest_ref"),
            f"{field}.generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "source_input_digest": _normalize_manifest_member(
            payload.get("source_input_digest"),
            f"{field}.source_input_digest",
            expected_kind="mas_artifact",
            expected_role="source_input_digest",
        ),
        "candidate_id": text(payload.get("candidate_id"), f"{field}.candidate_id"),
        "candidate_ref": _exact_ref(
            payload.get("candidate_ref"),
            f"{field}.candidate_ref",
            "mas_artifact",
        ),
        "candidate_size_bytes": integer(
            payload.get("candidate_size_bytes"), f"{field}.candidate_size_bytes"
        ),
        "evidence_refs": _exact_ref_list(
            payload.get("evidence_refs"),
            f"{field}.evidence_refs",
            "mas_evidence",
            dedupe_size=False,
        ),
        "claim_scope": _normalize_claim_scope(
            payload.get("claim_scope"), f"{field}.claim_scope"
        ),
        "disposition": disposition,
        "decision_code": decision_code,
        "authorizes_manuscript_consumption": expected_authorization,
        "authorizes_publication_or_submission": False,
        "requires_host_exact_byte_persistence": True,
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    candidate_ref = cast(dict[str, Any], core["candidate_ref"])
    if core["candidate_size_bytes"] != candidate_ref["size_bytes"]:
        raise RequestShapeError(
            f"{field}.candidate_size_bytes does not match candidate_ref"
        )
    receipt_id = text(payload.get("receipt_id"), f"{field}.receipt_id")
    if (
        receipt_id
        != f"mas-candidate-admission:{expected_fingerprint.removeprefix('sha256:')}"
    ):
        raise RequestShapeError(f"{field}.receipt_id does not match canonical receipt")
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_size_bytes does not match canonical receipt"
        )
    if (
        sha256(payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint")
        != expected_fingerprint
    ):
        raise RequestShapeError(
            f"{field}.receipt_fingerprint does not match canonical receipt"
        )
    return {
        **core,
        "receipt_id": receipt_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }
