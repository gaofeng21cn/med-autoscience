"""Generation currentness receipt validation and stale request detection."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    exact_keys,
    mapping,
    text,
    text_list,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from .._record_validation import (
    exact_ref_list as _exact_ref_list,
)
from .receipt_integrity import _validate_embedded_receipt


def _normalize_currentness_receipt(value: Any) -> dict[str, Any]:
    field = "currentness_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_epoch",
            "current_generation_id",
            "authority_role",
            "current_generation_manifest_ref",
            "current_admission_request_ref",
            "current_adjudicator_receipt_ref",
            "superseded_generation_ids",
            "superseded_request_refs",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_generation_currentness_receipt":
        raise RequestShapeError(
            "currentness_receipt.receipt_kind must be mas_generation_currentness_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("currentness_receipt.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError("currentness_receipt.owner must be MedAutoScience")
    if payload.get("authority_role") != "generation_currentness_owner":
        raise RequestShapeError(
            "currentness_receipt.authority_role must be generation_currentness_owner"
        )
    generations = text_list(
        payload.get("superseded_generation_ids"),
        "currentness_receipt.superseded_generation_ids",
    )
    superseded_refs = _exact_ref_list(
        payload.get("superseded_request_refs"),
        "currentness_receipt.superseded_request_refs",
        "opl_action_output",
        dedupe_size=False,
    )
    core = {
        "receipt_kind": "mas_generation_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "generation_currentness_owner",
        "authority_epoch": text(
            payload.get("authority_epoch"), "currentness_receipt.authority_epoch"
        ),
        "current_generation_id": text(
            payload.get("current_generation_id"),
            "currentness_receipt.current_generation_id",
        ),
        "current_generation_manifest_ref": _exact_ref(
            payload.get("current_generation_manifest_ref"),
            "currentness_receipt.current_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "current_admission_request_ref": _exact_ref(
            payload.get("current_admission_request_ref"),
            "currentness_receipt.current_admission_request_ref",
            "opl_action_output",
        ),
        "current_adjudicator_receipt_ref": _exact_ref(
            payload.get("current_adjudicator_receipt_ref"),
            "currentness_receipt.current_adjudicator_receipt_ref",
            "mas_candidate_adjudicator_receipt",
        ),
        "superseded_generation_ids": generations,
        "superseded_request_refs": superseded_refs,
    }
    return _validate_embedded_receipt(
        payload,
        core,
        field=field,
        id_prefix="mas-generation-currentness",
    )


def _validate_currentness_receipt_ref(request: Mapping[str, Any]) -> None:
    receipt = request["currentness_receipt"]
    receipt_ref = request["adjudicator_context"]["currentness_receipt_ref"]
    if (
        receipt_ref["ref"] != receipt["receipt_id"]
        or receipt_ref["sha256"] != receipt["receipt_fingerprint"]
        or receipt_ref["size_bytes"] != receipt["receipt_size_bytes"]
    ):
        raise RequestShapeError(
            "currentness_receipt_ref size/hash does not match currentness_receipt"
        )
    if (
        receipt["current_adjudicator_receipt_ref"]
        != request["adjudicator_context"]["adjudicator_receipt_ref"]
    ):
        raise RequestShapeError(
            "currentness_receipt does not authorize the supplied adjudicator receipt"
        )


def _currentness_issue(request: Mapping[str, Any]) -> dict[str, Any] | None:
    context = request["adjudicator_context"]
    manifest = request["generation_manifest"]
    currentness = request["currentness_receipt"]
    request_identity = (
        context["admission_request_ref"]["ref"],
        context["admission_request_ref"]["size_bytes"],
        context["admission_request_ref"]["sha256"],
    )
    superseded_requests = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in currentness["superseded_request_refs"]
    }
    stale = any(
        (
            currentness["current_generation_id"] != manifest["generation_id"],
            currentness["current_generation_manifest_ref"]
            != request["generation_manifest_ref"],
            currentness["current_admission_request_ref"]
            != context["admission_request_ref"],
            manifest["generation_id"] in currentness["superseded_generation_ids"],
            request_identity in superseded_requests,
        )
    )
    if not stale:
        return None
    return {
        "gate_kind": "source_currentness",
        "reason_code": "superseded_candidate_admission_request",
        "evidence_refs": [
            {
                "kind": context["currentness_receipt_ref"]["kind"],
                "ref": context["currentness_receipt_ref"]["ref"],
                "sha256": context["currentness_receipt_ref"]["sha256"],
            }
        ],
        "next_owner": "mas_generation_currentness_owner",
        "resume_condition": (
            "supply the current generation, admission request, and fresh MAS adjudicator receipt"
        ),
        "authorizes_manuscript_consumption": False,
        "requires_host_exact_byte_persistence": True,
    }
