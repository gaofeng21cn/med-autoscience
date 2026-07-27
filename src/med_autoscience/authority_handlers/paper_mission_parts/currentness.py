"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt

from .constants import (
    _BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY,
    _EPISTEMIC_CHANGE_CLASSES,
    _EPISTEMIC_IGNORED_REASONS,
    _HARD_GATE_KINDS,
)

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


def _normalize_epistemic_currentness(
    value: Any,
    field: str,
    *,
    lane: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "version",
            "scope_id",
            "scope_kind",
            "status",
            "invalidating_changes",
            "ignored_changes",
            "reviewed_dependency_refs",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "opl_epistemic_review_currentness_evaluation":
        raise RequestShapeError(
            f"{field}.surface_kind must be opl_epistemic_review_currentness_evaluation"
        )
    if payload.get("version") != "opl-epistemic-review-currentness-evaluation.v2":
        raise RequestShapeError(
            f"{field}.version must be opl-epistemic-review-currentness-evaluation.v2"
        )
    scope_id = text(payload.get("scope_id"), f"{field}.scope_id")
    if scope_id != f"mas:{lane}":
        raise RequestShapeError(f"{field}.scope_id must be mas:{lane}")
    status = enum_text(
        payload.get("status"), f"{field}.status", {"current", "stale"}
    )
    invalidating = [
        _normalize_epistemic_change(item, f"{field}.invalidating_changes[{index}]")
        for index, item in enumerate(
            sequence(payload.get("invalidating_changes"), f"{field}.invalidating_changes")
        )
    ]
    ignored = [
        _normalize_epistemic_change(
            item,
            f"{field}.ignored_changes[{index}]",
            ignored=True,
        )
        for index, item in enumerate(
            sequence(payload.get("ignored_changes"), f"{field}.ignored_changes")
        )
    ]
    if (status == "current" and invalidating) or (
        status == "stale" and not invalidating
    ):
        raise RequestShapeError(
            f"{field}.status must agree with invalidating_changes"
        )
    dependency_refs = text_list(
        payload.get("reviewed_dependency_refs"),
        f"{field}.reviewed_dependency_refs",
    )
    if not dependency_refs or dependency_refs != sorted(set(dependency_refs)):
        raise RequestShapeError(
            f"{field}.reviewed_dependency_refs must be sorted and unique"
        )
    authority = mapping(payload.get("authority_boundary"), f"{field}.authority_boundary")
    exact_keys(
        authority,
        set(EPISTEMIC_AUTHORITY_BOUNDARY),
        f"{field}.authority_boundary",
    )
    if authority != EPISTEMIC_AUTHORITY_BOUNDARY:
        raise RequestShapeError(
            f"{field}.authority_boundary must preserve the OPL/MAS authority split"
        )
    return {
        "surface_kind": "opl_epistemic_review_currentness_evaluation",
        "version": "opl-epistemic-review-currentness-evaluation.v2",
        "scope_id": scope_id,
        "scope_kind": enum_text(
            payload.get("scope_kind"),
            f"{field}.scope_kind",
            {"content", "reference", "display", "package"},
        ),
        "status": status,
        "invalidating_changes": invalidating,
        "ignored_changes": ignored,
        "reviewed_dependency_refs": dependency_refs,
        "authority_boundary": dict(EPISTEMIC_AUTHORITY_BOUNDARY),
    }


def _normalize_epistemic_change(
    value: Any,
    field: str,
    *,
    ignored: bool = False,
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {
        "node_ref",
        "change_class",
        "semantic_changed",
        "locator_sha256_before",
        "locator_sha256_after",
    }
    if ignored:
        keys.add("reason")
    exact_keys(payload, keys, field)
    if not isinstance(payload.get("semantic_changed"), bool):
        raise RequestShapeError(f"{field}.semantic_changed must be boolean")
    if not ignored and payload["semantic_changed"] is not True:
        raise RequestShapeError(
            f"{field}.semantic_changed must be true for an invalidating change"
        )
    normalized = {
        "node_ref": text(payload.get("node_ref"), f"{field}.node_ref"),
        "change_class": enum_text(
            payload.get("change_class"),
            f"{field}.change_class",
            _EPISTEMIC_CHANGE_CLASSES,
        ),
        "semantic_changed": payload["semantic_changed"],
        "locator_sha256_before": optional_sha256(
            payload.get("locator_sha256_before"),
            f"{field}.locator_sha256_before",
        ),
        "locator_sha256_after": optional_sha256(
            payload.get("locator_sha256_after"),
            f"{field}.locator_sha256_after",
        ),
    }
    if ignored:
        normalized["reason"] = enum_text(
            payload.get("reason"),
            f"{field}.reason",
            _EPISTEMIC_IGNORED_REASONS,
        )
    return normalized


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


def _normalize_repair(value: Any) -> dict[str, Any]:
    field = "repair_state"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "status",
            "attempts_used",
            "max_attempts",
            "repair_attempt_refs",
            "latest_repair_output_ref",
        },
        field,
    )
    attempts_used = integer(payload.get("attempts_used"), f"{field}.attempts_used")
    max_attempts = integer(payload.get("max_attempts"), f"{field}.max_attempts")
    if max_attempts != 3:
        raise RequestShapeError(
            "repair_state.max_attempts must equal the OPL scope budget of 3"
        )
    if attempts_used > max_attempts:
        raise RequestShapeError("repair_state.attempts_used cannot exceed max_attempts")
    attempt_refs = _typed_ref_list(
        payload.get("repair_attempt_refs"),
        f"{field}.repair_attempt_refs",
        "opl_stage_attempt",
    )
    if len(attempt_refs) != attempts_used:
        raise RequestShapeError("repair_attempt_refs must exactly match attempts_used")
    return {
        "status": enum_text(
            payload.get("status"),
            f"{field}.status",
            {"not_required", "pending", "completed", "exhausted", "failed"},
        ),
        "attempts_used": attempts_used,
        "max_attempts": max_attempts,
        "repair_attempt_refs": attempt_refs,
        "latest_repair_output_ref": _optional_typed_ref(
            payload.get("latest_repair_output_ref"),
            f"{field}.latest_repair_output_ref",
            "opl_action_output",
        ),
    }


def _normalize_hard_gate(value: Any) -> dict[str, Any]:
    field = "hard_gate"
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"kind", "reason_code", "evidence_refs", "next_owner", "resume_condition"},
        field,
    )
    kind = enum_text(
        payload.get("kind"),
        f"{field}.kind",
        {"none", "human_decision", *_HARD_GATE_KINDS},
    )
    normalized = {
        "kind": kind,
        "reason_code": optional_text(
            payload.get("reason_code"), f"{field}.reason_code"
        ),
        "evidence_refs": _typed_ref_list(
            payload.get("evidence_refs"),
            f"{field}.evidence_refs",
            "mas_gate_evidence",
        ),
        "next_owner": optional_text(payload.get("next_owner"), f"{field}.next_owner"),
        "resume_condition": optional_text(
            payload.get("resume_condition"), f"{field}.resume_condition"
        ),
    }
    if kind == "none":
        if any(
            (
                normalized["reason_code"] is not None,
                bool(normalized["evidence_refs"]),
                normalized["next_owner"] is not None,
                normalized["resume_condition"] is not None,
            )
        ):
            raise RequestShapeError("hard_gate.kind none requires an empty gate record")
        return normalized
    missing = [
        name
        for name in ("reason_code", "next_owner", "resume_condition")
        if normalized[name] is None
    ]
    if not normalized["evidence_refs"]:
        missing.append("evidence_refs")
    if missing:
        raise RequestShapeError("hard gate missing: " + ", ".join(missing))
    return normalized
