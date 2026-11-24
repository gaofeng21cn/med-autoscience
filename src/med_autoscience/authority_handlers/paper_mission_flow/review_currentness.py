"""Review receipt, lane currentness, and reuse provenance normalizers."""

from __future__ import annotations

from typing import Any

from .._generation_manifest import REVIEW_LANES_BY_SCOPE
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
)
from .epistemic_currentness import _normalize_epistemic_currentness

def _normalize_review_currentness_receipt(value: Any) -> dict[str, Any]:
    field = "review_authority.currentness_receipt"
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version == 1:
        return _normalize_review_currentness_receipt_v1(value)
    if schema_version == 2:
        return _normalize_review_currentness_receipt_v2(value)
    raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")


def _normalize_review_currentness_receipt_v1(value: Any) -> dict[str, Any]:
    field = "review_authority.currentness_receipt"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_epoch",
            "current_generation_id",
            "current_generation_manifest_ref",
            "current_review_request_ref",
            "current_candidate_admission_receipt_refs",
            "current_review_receipt_refs",
            "superseded_generation_ids",
            "superseded_review_request_refs",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_review_currentness_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_review_currentness_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "review_currentness_owner":
        raise RequestShapeError(
            f"{field}.authority_role must be review_currentness_owner"
        )
    core = {
        "receipt_kind": "mas_review_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "review_currentness_owner",
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "current_generation_id": text(
            payload.get("current_generation_id"),
            f"{field}.current_generation_id",
        ),
        "current_generation_manifest_ref": _exact_ref(
            payload.get("current_generation_manifest_ref"),
            f"{field}.current_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "current_review_request_ref": _exact_ref(
            payload.get("current_review_request_ref"),
            f"{field}.current_review_request_ref",
            "opl_action_output",
        ),
        "current_candidate_admission_receipt_refs": _exact_ref_list(
            payload.get("current_candidate_admission_receipt_refs"),
            f"{field}.current_candidate_admission_receipt_refs",
            "mas_candidate_admission_receipt",
        ),
        "current_review_receipt_refs": _exact_ref_list(
            payload.get("current_review_receipt_refs"),
            f"{field}.current_review_receipt_refs",
            "mas_reviewer_receipt",
        ),
        "superseded_generation_ids": text_list(
            payload.get("superseded_generation_ids"),
            f"{field}.superseded_generation_ids",
        ),
        "superseded_review_request_refs": _exact_ref_list(
            payload.get("superseded_review_request_refs"),
            f"{field}.superseded_review_request_refs",
            "opl_action_output",
        ),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        f"mas-review-currentness:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
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
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_review_currentness_receipt_v2(value: Any) -> dict[str, Any]:
    field = "review_authority.currentness_receipt"
    payload = mapping(value, field)
    keys = {
        "receipt_kind",
        "schema_version",
        "owner",
        "authority_role",
        "authority_epoch",
        "current_generation_id",
        "current_generation_manifest_ref",
        "current_review_request_ref",
        "current_candidate_admission_receipt_refs",
        "lane_currentness",
        "receipt_id",
        "receipt_size_bytes",
        "receipt_fingerprint",
    }
    if "current_build_dependency_authority_refs" in payload:
        keys.add("current_build_dependency_authority_refs")
    exact_keys(
        payload,
        keys,
        field,
    )
    if payload.get("receipt_kind") != "mas_review_currentness_receipt":
        raise RequestShapeError(
            f"{field}.receipt_kind must be mas_review_currentness_receipt"
        )
    if payload.get("schema_version") != 2 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 2")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "review_currentness_owner":
        raise RequestShapeError(
            f"{field}.authority_role must be review_currentness_owner"
        )
    lanes = [
        _normalize_lane_currentness(
            item,
            f"{field}.lane_currentness[{index}]",
        )
        for index, item in enumerate(
            sequence(payload.get("lane_currentness"), f"{field}.lane_currentness")
        )
    ]
    lane_ids = [item["review_lane"] for item in lanes]
    if len(lane_ids) != len(set(lane_ids)):
        raise RequestShapeError(f"{field}.lane_currentness contains duplicate lanes")
    lanes.sort(key=lambda item: item["review_lane"])
    core = {
        "receipt_kind": "mas_review_currentness_receipt",
        "schema_version": 2,
        "owner": "MedAutoScience",
        "authority_role": "review_currentness_owner",
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{field}.authority_epoch"
        ),
        "current_generation_id": text(
            payload.get("current_generation_id"),
            f"{field}.current_generation_id",
        ),
        "current_generation_manifest_ref": _exact_ref(
            payload.get("current_generation_manifest_ref"),
            f"{field}.current_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "current_review_request_ref": _exact_ref(
            payload.get("current_review_request_ref"),
            f"{field}.current_review_request_ref",
            "opl_action_output",
        ),
        "current_candidate_admission_receipt_refs": _exact_ref_list(
            payload.get("current_candidate_admission_receipt_refs"),
            f"{field}.current_candidate_admission_receipt_refs",
            "mas_candidate_admission_receipt",
        ),
        "lane_currentness": lanes,
    }
    if "current_build_dependency_authority_refs" in payload:
        core["current_build_dependency_authority_refs"] = _exact_ref_list(
            payload.get("current_build_dependency_authority_refs"),
            f"{field}.current_build_dependency_authority_refs",
            "mas_build_dependency_currentness_authority",
        )
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_id = (
        f"mas-review-currentness:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if text(payload.get("receipt_id"), f"{field}.receipt_id") != expected_id:
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
        "current_build_dependency_authority_refs": core.get(
            "current_build_dependency_authority_refs", []
        ),
        "receipt_id": expected_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_lane_currentness(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "review_lane",
            "review_authority_epoch",
            "currentness_status",
            "current_rubric_ref",
            "review_scope_sha256",
            "review_receipt_issued_generation_id",
            "review_receipt_issued_generation_manifest_sha256",
            "current_review_request_ref",
            "current_review_receipt_ref",
            "superseded_review_request_refs",
            "reuse_provenance",
            "epistemic_currentness",
        },
        field,
    )
    lane = enum_text(
        payload.get("review_lane"),
        f"{field}.review_lane",
        set().union(*REVIEW_LANES_BY_SCOPE.values()),
    )
    status = enum_text(
        payload.get("currentness_status"),
        f"{field}.currentness_status",
        {"fresh", "reused_unchanged_scope"},
    )
    reuse_value = payload.get("reuse_provenance")
    reuse = None
    if status == "fresh":
        if reuse_value is not None:
            raise RequestShapeError(
                f"{field}.reuse_provenance must be null for fresh review"
            )
    else:
        reuse = _normalize_reuse_provenance(reuse_value, f"{field}.reuse_provenance")
    return {
        "review_lane": lane,
        "review_authority_epoch": text(
            payload.get("review_authority_epoch"),
            f"{field}.review_authority_epoch",
        ),
        "currentness_status": status,
        "current_rubric_ref": _typed_ref(
            payload.get("current_rubric_ref"),
            f"{field}.current_rubric_ref",
            "mas_quality_rubric",
        ),
        "review_scope_sha256": sha256(
            payload.get("review_scope_sha256"),
            f"{field}.review_scope_sha256",
        ),
        "review_receipt_issued_generation_id": text(
            payload.get("review_receipt_issued_generation_id"),
            f"{field}.review_receipt_issued_generation_id",
        ),
        "review_receipt_issued_generation_manifest_sha256": sha256(
            payload.get("review_receipt_issued_generation_manifest_sha256"),
            f"{field}.review_receipt_issued_generation_manifest_sha256",
        ),
        "current_review_request_ref": _exact_ref(
            payload.get("current_review_request_ref"),
            f"{field}.current_review_request_ref",
            "opl_action_output",
        ),
        "current_review_receipt_ref": _exact_ref(
            payload.get("current_review_receipt_ref"),
            f"{field}.current_review_receipt_ref",
            "mas_reviewer_receipt",
        ),
        "superseded_review_request_refs": _exact_ref_list(
            payload.get("superseded_review_request_refs"),
            f"{field}.superseded_review_request_refs",
            "opl_action_output",
        ),
        "reuse_provenance": reuse,
        "epistemic_currentness": _normalize_epistemic_currentness(
            payload.get("epistemic_currentness"),
            f"{field}.epistemic_currentness",
            lane=lane,
        ),
    }


def _normalize_reuse_provenance(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "origin_generation_id",
            "origin_generation_manifest_ref",
            "origin_review_request_ref",
            "origin_review_receipt_ref",
            "origin_review_scope_sha256",
            "origin_candidate_admission_receipt_refs",
        },
        field,
    )
    return {
        "origin_generation_id": text(
            payload.get("origin_generation_id"), f"{field}.origin_generation_id"
        ),
        "origin_generation_manifest_ref": _exact_ref(
            payload.get("origin_generation_manifest_ref"),
            f"{field}.origin_generation_manifest_ref",
            "mas_generation_manifest",
        ),
        "origin_review_request_ref": _exact_ref(
            payload.get("origin_review_request_ref"),
            f"{field}.origin_review_request_ref",
            "opl_action_output",
        ),
        "origin_review_receipt_ref": _exact_ref(
            payload.get("origin_review_receipt_ref"),
            f"{field}.origin_review_receipt_ref",
            "mas_reviewer_receipt",
        ),
        "origin_review_scope_sha256": sha256(
            payload.get("origin_review_scope_sha256"),
            f"{field}.origin_review_scope_sha256",
        ),
        "origin_candidate_admission_receipt_refs": _exact_ref_list(
            payload.get("origin_candidate_admission_receipt_refs"),
            f"{field}.origin_candidate_admission_receipt_refs",
            "mas_candidate_admission_receipt",
        ),
    }
