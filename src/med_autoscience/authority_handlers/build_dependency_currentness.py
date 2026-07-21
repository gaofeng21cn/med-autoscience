"""Issue one managed-attempt MAS build-dependency currentness authority record."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref,
    exact_keys,
    fingerprint,
    mapping,
    text,
    typed_ref,
)


REQUEST_KIND = "mas_build_dependency_currentness_authority_request"
RESULT_KIND = "mas_build_dependency_currentness_authority_result"
AUTHORITY_BOUNDARY = {
    "authorizes_publication": False,
    "authorizes_submission": False,
}


def evaluate_build_dependency_currentness_authority(
    request: Mapping[str, Any],
) -> dict[str, Any]:
    """Return a byte-bound owner result or a deterministic invalid-input result."""

    try:
        normalized = _normalize_request(request)
    except (RequestShapeError, TypeError, ValueError) as exc:
        return {
            "surface_kind": RESULT_KIND,
            "schema_version": 1,
            "status": "invalid_host_input",
            "authority_ref": None,
            "authority_record": None,
            "opl_injection_provenance": None,
            "error": {"code": "invalid_host_input", "detail": str(exc)},
        }

    context = normalized["authority_context"]
    authority_record = {
        "surface_kind": "mas_build_dependency_currentness_authority",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "build_dependency_currentness_owner",
        "authority_epoch": context["authority_epoch"],
        "issuer_attempt_ref": context["managed_authority_attempt_ref"],
        "managed_authority_attempt_receipt_ref": context[
            "managed_authority_attempt_receipt_ref"
        ],
        "owner_ledger_ref": context["owner_ledger_ref"],
        "reviewer_response_currentness": normalized[
            "reviewer_response_currentness"
        ],
        "dependency_manifest_ref": normalized["dependency_manifest_ref"],
        "dependency_currentness": normalized["dependency_currentness"],
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    authority_sha256 = fingerprint(authority_record)
    authority_ref = {
        "kind": "mas_build_dependency_currentness_authority",
        "ref": (
            "mas-build-dependency-currentness-authority:"
            f"{authority_sha256.removeprefix('sha256:')}"
        ),
        "size_bytes": len(canonical_json_bytes(authority_record)),
        "sha256": authority_sha256,
    }
    return {
        "surface_kind": RESULT_KIND,
        "schema_version": 1,
        "status": "owner_authority",
        "authority_ref": authority_ref,
        "authority_record": authority_record,
        "opl_injection_provenance": {
            "managed_authority_attempt_ref": context[
                "managed_authority_attempt_ref"
            ],
            "managed_authority_attempt_receipt_ref": context[
                "managed_authority_attempt_receipt_ref"
            ],
            "owner_ledger_ref": context["owner_ledger_ref"],
            "owner_ledger_history_ref": normalized[
                "reviewer_response_currentness"
            ]["owner_ledger_history_ref"],
            "host_context_authority_ref_field": (
                "build_dependency_currentness_authority_ref"
            ),
            "host_context_issuer_attempt_ref_field": (
                "build_dependency_currentness_authority_issuer_attempt_ref"
            ),
            "requires_host_exact_byte_persistence": True,
        },
        "error": None,
    }


def _normalize_request(request: Mapping[str, Any]) -> dict[str, Any]:
    payload = mapping(request, "request")
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "authority_context",
            "dependency_manifest_ref",
            "dependency_currentness",
            "reviewer_response_currentness",
        },
        "request",
    )
    if payload.get("surface_kind") != REQUEST_KIND:
        raise RequestShapeError(f"surface_kind must be {REQUEST_KIND}")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError("schema_version must be integer 1")
    context = _normalize_authority_context(payload.get("authority_context"))
    managed_attempt = context["managed_authority_attempt_ref"]
    producer_attempt = context["generation_producer_attempt_ref"]
    if (
        managed_attempt["ref"] == producer_attempt["ref"]
        or managed_attempt["sha256"] == producer_attempt["sha256"]
    ):
        raise RequestShapeError(
            "managed authority attempt must differ from generation producer attempt"
        )
    response_currentness = _normalize_reviewer_response_currentness(
        payload.get("reviewer_response_currentness")
    )
    if response_currentness["owner_ledger_history_ref"] != context["owner_ledger_ref"]:
        raise RequestShapeError(
            "reviewer_response_currentness.owner_ledger_history_ref must reuse the "
            "managed build-currentness owner ledger provenance"
        )
    return {
        "surface_kind": REQUEST_KIND,
        "schema_version": 1,
        "authority_context": context,
        "dependency_manifest_ref": exact_ref(
            payload.get("dependency_manifest_ref"),
            "dependency_manifest_ref",
            "mas_artifact",
        ),
        "dependency_currentness": enum_text(
            payload.get("dependency_currentness"),
            "dependency_currentness",
            {"current", "stale", "open"},
        ),
        "reviewer_response_currentness": response_currentness,
    }


def _normalize_reviewer_response_currentness(value: Any) -> dict[str, Any]:
    field = "reviewer_response_currentness"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "generation_id",
            "candidate_state",
            "response_ref",
            "prior_frozen_response_ref",
            "post_freeze_disposition",
            "external_synthesis_ref",
            "new_revision_ref",
            "owner_ledger_history_ref",
        },
        field,
    )
    candidate_state = enum_text(
        payload.get("candidate_state"),
        f"{field}.candidate_state",
        {"pre_freeze", "frozen"},
    )
    disposition = enum_text(
        payload.get("post_freeze_disposition"),
        f"{field}.post_freeze_disposition",
        {
            "not_started",
            "external_synthesis_bound",
            "scientific_change_requires_new_revision",
        },
    )

    def optional_artifact_ref(name: str) -> dict[str, Any] | None:
        raw = payload.get(name)
        return None if raw is None else exact_ref(raw, f"{field}.{name}", "mas_artifact")

    response_ref = exact_ref(
        payload.get("response_ref"), f"{field}.response_ref", "mas_artifact"
    )
    prior_ref = optional_artifact_ref("prior_frozen_response_ref")
    external_ref = optional_artifact_ref("external_synthesis_ref")
    new_revision_ref = optional_artifact_ref("new_revision_ref")
    if candidate_state == "pre_freeze":
        if prior_ref is not None or disposition != "not_started" or any(
            (external_ref, new_revision_ref)
        ):
            raise RequestShapeError(
                f"{field} pre-freeze state cannot carry frozen history or post-freeze refs"
            )
    else:
        if prior_ref is None:
            raise RequestShapeError(
                f"{field} frozen state requires prior_frozen_response_ref from owner ledger"
            )
        if response_ref != prior_ref and new_revision_ref is None:
            raise RequestShapeError(
                f"{field} same frozen generation cannot replace reviewer response bytes"
            )
        if disposition == "external_synthesis_bound" and (
            response_ref != prior_ref
            or external_ref is None
            or new_revision_ref is not None
        ):
            raise RequestShapeError(
                f"{field} external synthesis must bind the original frozen response bytes"
            )
        if disposition == "scientific_change_requires_new_revision" and (
            new_revision_ref is None
        ):
            raise RequestShapeError(
                f"{field} scientific response change requires new_revision_ref"
            )
        if disposition == "not_started" and any((external_ref, new_revision_ref)):
            raise RequestShapeError(
                f"{field} frozen not_started state cannot carry post-freeze refs"
            )
    return {
        "generation_id": text(payload.get("generation_id"), f"{field}.generation_id"),
        "candidate_state": candidate_state,
        "response_ref": response_ref,
        "prior_frozen_response_ref": prior_ref,
        "post_freeze_disposition": disposition,
        "external_synthesis_ref": external_ref,
        "new_revision_ref": new_revision_ref,
        "owner_ledger_history_ref": exact_ref(
            payload.get("owner_ledger_history_ref"),
            f"{field}.owner_ledger_history_ref",
            "opl_action_output",
        ),
    }


def _normalize_authority_context(value: Any) -> dict[str, Any]:
    field = "authority_context"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "action_id",
            "authority_epoch",
            "managed_authority_attempt_ref",
            "generation_producer_attempt_ref",
            "managed_authority_attempt_receipt_ref",
            "owner_ledger_ref",
        },
        field,
    )
    if payload.get("action_id") != "build_dependency_currentness_authority_evaluate":
        raise RequestShapeError(f"{field}.action_id is invalid")
    return {
        "action_id": "build_dependency_currentness_authority_evaluate",
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "managed_authority_attempt_ref": typed_ref(
            payload.get("managed_authority_attempt_ref"),
            f"{field}.managed_authority_attempt_ref",
            "opl_stage_attempt",
        ),
        "generation_producer_attempt_ref": typed_ref(
            payload.get("generation_producer_attempt_ref"),
            f"{field}.generation_producer_attempt_ref",
            "opl_stage_attempt",
        ),
        "managed_authority_attempt_receipt_ref": exact_ref(
            payload.get("managed_authority_attempt_receipt_ref"),
            f"{field}.managed_authority_attempt_receipt_ref",
            "opl_action_output",
        ),
        "owner_ledger_ref": exact_ref(
            payload.get("owner_ledger_ref"),
            f"{field}.owner_ledger_ref",
            "opl_action_output",
        ),
    }


__all__ = ["evaluate_build_dependency_currentness_authority"]
