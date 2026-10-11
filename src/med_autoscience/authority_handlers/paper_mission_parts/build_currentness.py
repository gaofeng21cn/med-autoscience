"""Selected-build and reviewer-response currentness authority normalizers."""

from __future__ import annotations

from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_keys,
    fingerprint,
    mapping,
    text,
    typed_ref as _typed_ref,
    exact_ref as _exact_ref,
)
from .constants import _BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY

def _normalize_selected_build_currentness_authority(
    value: Any,
) -> dict[str, Any]:
    field = "selected_build_currentness_authority"
    payload = mapping(value, field)
    exact_keys(payload, {"authority_ref", "authority_record"}, field)
    authority_ref = _exact_ref(
        payload.get("authority_ref"),
        f"{field}.authority_ref",
        "mas_build_dependency_currentness_authority",
    )
    record_field = f"{field}.authority_record"
    record = mapping(payload.get("authority_record"), record_field)
    exact_keys(
        record,
        {
            "surface_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_epoch",
            "issuer_attempt_ref",
            "managed_authority_attempt_receipt_ref",
            "owner_ledger_ref",
            "reviewer_response_currentness",
            "dependency_manifest_ref",
            "dependency_currentness",
            "authority_boundary",
        },
        record_field,
    )
    if record.get("surface_kind") != "mas_build_dependency_currentness_authority":
        raise RequestShapeError(f"{record_field}.surface_kind is invalid")
    if record.get("schema_version") != 1 or isinstance(
        record.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{record_field}.schema_version must be integer 1")
    if record.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{record_field}.owner must be MedAutoScience")
    if record.get("authority_role") != "build_dependency_currentness_owner":
        raise RequestShapeError(f"{record_field}.authority_role is invalid")
    boundary = mapping(
        record.get("authority_boundary"), f"{record_field}.authority_boundary"
    )
    exact_keys(
        boundary,
        set(_BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY),
        f"{record_field}.authority_boundary",
    )
    if boundary != _BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY:
        raise RequestShapeError(
            f"{record_field}.authority_boundary must preserve no publication or "
            "submission authority"
        )
    core = {
        "surface_kind": "mas_build_dependency_currentness_authority",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "build_dependency_currentness_owner",
        "authority_epoch": text(
            record.get("authority_epoch"), f"{record_field}.authority_epoch"
        ),
        "issuer_attempt_ref": _typed_ref(
            record.get("issuer_attempt_ref"),
            f"{record_field}.issuer_attempt_ref",
            "opl_stage_attempt",
        ),
        "managed_authority_attempt_receipt_ref": _exact_ref(
            record.get("managed_authority_attempt_receipt_ref"),
            f"{record_field}.managed_authority_attempt_receipt_ref",
            "opl_action_output",
        ),
        "owner_ledger_ref": _exact_ref(
            record.get("owner_ledger_ref"),
            f"{record_field}.owner_ledger_ref",
            "opl_action_output",
        ),
        "reviewer_response_currentness": (
            _normalize_reviewer_response_authority_currentness(
                record.get("reviewer_response_currentness"),
                f"{record_field}.reviewer_response_currentness",
            )
        ),
        "dependency_manifest_ref": _exact_ref(
            record.get("dependency_manifest_ref"),
            f"{record_field}.dependency_manifest_ref",
            "mas_artifact",
        ),
        "dependency_currentness": enum_text(
            record.get("dependency_currentness"),
            f"{record_field}.dependency_currentness",
            {"current", "stale", "open"},
        ),
        "authority_boundary": dict(
            _BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY
        ),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        "mas-build-dependency-currentness-authority:"
        f"{expected_fingerprint.removeprefix('sha256:')}"
    )
    if authority_ref != {
        "kind": "mas_build_dependency_currentness_authority",
        "ref": expected_id,
        "size_bytes": expected_size,
        "sha256": expected_fingerprint,
    }:
        raise RequestShapeError(
            f"{field}.authority_ref does not match canonical authority record bytes"
        )
    return {"authority_ref": authority_ref, "authority_record": core}


def _normalize_reviewer_response_authority_currentness(
    value: Any,
    field: str,
) -> dict[str, Any]:
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

    def optional_artifact_ref(name: str) -> dict[str, Any] | None:
        raw = payload.get(name)
        return (
            None
            if raw is None
            else _exact_ref(raw, f"{field}.{name}", "mas_artifact")
        )

    normalized = {
        "generation_id": text(payload.get("generation_id"), f"{field}.generation_id"),
        "candidate_state": enum_text(
            payload.get("candidate_state"),
            f"{field}.candidate_state",
            {"pre_freeze", "frozen"},
        ),
        "response_ref": _exact_ref(
            payload.get("response_ref"), f"{field}.response_ref", "mas_artifact"
        ),
        "prior_frozen_response_ref": optional_artifact_ref(
            "prior_frozen_response_ref"
        ),
        "post_freeze_disposition": enum_text(
            payload.get("post_freeze_disposition"),
            f"{field}.post_freeze_disposition",
            {
                "not_started",
                "external_synthesis_bound",
                "scientific_change_requires_new_revision",
            },
        ),
        "external_synthesis_ref": optional_artifact_ref("external_synthesis_ref"),
        "new_revision_ref": optional_artifact_ref("new_revision_ref"),
        "owner_ledger_history_ref": _exact_ref(
            payload.get("owner_ledger_history_ref"),
            f"{field}.owner_ledger_history_ref",
            "opl_action_output",
        ),
    }
    state = normalized["candidate_state"]
    prior_ref = normalized["prior_frozen_response_ref"]
    disposition = normalized["post_freeze_disposition"]
    if state == "pre_freeze" and (
        prior_ref is not None
        or disposition != "not_started"
        or normalized["external_synthesis_ref"] is not None
        or normalized["new_revision_ref"] is not None
    ):
        raise RequestShapeError(
            f"{field} pre-freeze state cannot carry frozen history or post-freeze refs"
        )
    if state == "frozen":
        if prior_ref is None:
            raise RequestShapeError(
                f"{field} frozen state requires prior_frozen_response_ref"
            )
        if (
            normalized["response_ref"] != prior_ref
            and normalized["new_revision_ref"] is None
        ):
            raise RequestShapeError(
                f"{field} same frozen generation cannot replace reviewer response bytes"
            )
        if disposition == "external_synthesis_bound" and (
            normalized["response_ref"] != prior_ref
            or normalized["external_synthesis_ref"] is None
            or normalized["new_revision_ref"] is not None
        ):
            raise RequestShapeError(
                f"{field} external synthesis must bind original frozen response bytes"
            )
    return normalized

