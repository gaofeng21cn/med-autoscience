"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

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
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)

from .constants import (
    REVIEWER_RESPONSE_ROLE_BY_REF_FIELD,
    SELECTED_BUILD_ROLE_BY_REF_FIELD,
)
from .records import (
    _manifest_artifact_ref,
)

def _normalize_no_authority_boundary(value: Any, field: str) -> dict[str, bool]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"authorizes_publication", "authorizes_submission"},
        field,
    )
    if payload.get("authorizes_publication") is not False:
        raise RequestShapeError(f"{field}.authorizes_publication must be false")
    if payload.get("authorizes_submission") is not False:
        raise RequestShapeError(f"{field}.authorizes_submission must be false")
    return {"authorizes_publication": False, "authorizes_submission": False}


def _normalize_clinical_analysis_identity_admission(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "status",
            "clinical_analysis_input_identity_ref",
            "reason_codes",
            "unresolved_items",
            "next_owner",
            "human_gate_refs",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_clinical_analysis_identity_admission":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    status = enum_text(
        payload.get("status"),
        f"{field}.status",
        {"adjudicator_required", "open_human_gate", "route_back"},
    )
    reason_codes = text_list(payload.get("reason_codes"), f"{field}.reason_codes")
    unresolved_items = text_list(
        payload.get("unresolved_items"), f"{field}.unresolved_items"
    )
    next_owner = optional_text(payload.get("next_owner"), f"{field}.next_owner")
    human_gate_refs = _typed_ref_list(
        payload.get("human_gate_refs"),
        f"{field}.human_gate_refs",
        "mas_human_gate",
    )
    if status == "adjudicator_required" and (
        unresolved_items or next_owner is not None or human_gate_refs
    ):
        raise RequestShapeError(
            f"{field} adjudicator_required cannot carry unresolved or gate state"
        )
    if status == "open_human_gate" and (
        not reason_codes
        or not unresolved_items
        or next_owner is None
        or not human_gate_refs
    ):
        raise RequestShapeError(
            f"{field} open_human_gate requires reasons, unresolved items, owner, and refs"
        )
    if status == "route_back" and (
        not reason_codes
        or not unresolved_items
        or next_owner != "baseline_and_evidence_setup"
        or human_gate_refs
    ):
        raise RequestShapeError(
            f"{field} route_back requires baseline owner and no human-gate refs"
        )
    return {
        "surface_kind": "mas_clinical_analysis_identity_admission",
        "schema_version": 1,
        "status": status,
        "clinical_analysis_input_identity_ref": _manifest_artifact_ref(
            payload.get("clinical_analysis_input_identity_ref"),
            f"{field}.clinical_analysis_input_identity_ref",
            artifacts=artifacts,
            expected_role="clinical_analysis_input_identity",
        ),
        "reason_codes": reason_codes,
        "unresolved_items": unresolved_items,
        "next_owner": next_owner,
        "human_gate_refs": human_gate_refs,
        "authority_boundary": _normalize_no_authority_boundary(
            payload.get("authority_boundary"), f"{field}.authority_boundary"
        ),
    }


def _normalize_selected_build_binding(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "selected_archive_label",
            *SELECTED_BUILD_ROLE_BY_REF_FIELD,
            "dependency_currentness",
            "dependency_currentness_receipt_ref",
            "dependency_currentness_receipt",
            "root_matches_selected_bytes",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_selected_build_binding":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    refs = {
        ref_field: _manifest_artifact_ref(
            payload.get(ref_field),
            f"{field}.{ref_field}",
            artifacts=artifacts,
            expected_role=role,
        )
        for ref_field, role in SELECTED_BUILD_ROLE_BY_REF_FIELD.items()
    }
    root_matches_selected_bytes = payload.get("root_matches_selected_bytes")
    if not isinstance(root_matches_selected_bytes, bool):
        raise RequestShapeError(
            f"{field}.root_matches_selected_bytes must be boolean"
        )
    exact_bytes_match = (
        refs["root_reader_output_ref"]["size_bytes"]
        == refs["selected_reader_output_ref"]["size_bytes"]
        and refs["root_reader_output_ref"]["sha256"]
        == refs["selected_reader_output_ref"]["sha256"]
    )
    if root_matches_selected_bytes != exact_bytes_match:
        raise RequestShapeError(
            f"{field}.root_matches_selected_bytes does not match exact reader bytes"
        )
    return {
        "surface_kind": "mas_selected_build_binding",
        "schema_version": 1,
        "selected_archive_label": text(
            payload.get("selected_archive_label"),
            f"{field}.selected_archive_label",
        ),
        **refs,
        "dependency_currentness": enum_text(
            payload.get("dependency_currentness"),
            f"{field}.dependency_currentness",
            {"current", "stale", "open"},
        ),
        "dependency_currentness_receipt_ref": _exact_ref(
            payload.get("dependency_currentness_receipt_ref"),
            f"{field}.dependency_currentness_receipt_ref",
            "mas_build_dependency_currentness_receipt",
        ),
        "dependency_currentness_receipt": _normalize_dependency_currentness_receipt(
            payload.get("dependency_currentness_receipt"),
            f"{field}.dependency_currentness_receipt",
            dependency_manifest_ref=refs["dependency_manifest_ref"],
            dependency_currentness=enum_text(
                payload.get("dependency_currentness"),
                f"{field}.dependency_currentness",
                {"current", "stale", "open"},
            ),
            receipt_ref=payload.get("dependency_currentness_receipt_ref"),
        ),
        "root_matches_selected_bytes": root_matches_selected_bytes,
        "authority_boundary": _normalize_no_authority_boundary(
            payload.get("authority_boundary"), f"{field}.authority_boundary"
        ),
    }


def _normalize_dependency_currentness_receipt(
    value: Any,
    field: str,
    *,
    dependency_manifest_ref: Mapping[str, Any],
    dependency_currentness: str,
    receipt_ref: Any,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_ref",
            "dependency_manifest_ref",
            "dependency_currentness",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_build_dependency_currentness_receipt":
        raise RequestShapeError(f"{field}.receipt_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "build_dependency_currentness_owner":
        raise RequestShapeError(f"{field}.authority_role is invalid")
    authority_ref = _exact_ref(
        payload.get("authority_ref"),
        f"{field}.authority_ref",
        "mas_build_dependency_currentness_authority",
    )
    normalized_dependency_ref = _exact_ref(
        payload.get("dependency_manifest_ref"),
        f"{field}.dependency_manifest_ref",
        "mas_artifact",
    )
    if normalized_dependency_ref != dict(dependency_manifest_ref):
        raise RequestShapeError(
            f"{field}.dependency_manifest_ref does not match selected build binding"
        )
    normalized_status = enum_text(
        payload.get("dependency_currentness"),
        f"{field}.dependency_currentness",
        {"current", "stale", "open"},
    )
    if normalized_status != dependency_currentness:
        raise RequestShapeError(
            f"{field}.dependency_currentness does not match selected build binding"
        )
    core = {
        "receipt_kind": "mas_build_dependency_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "build_dependency_currentness_owner",
        "authority_ref": authority_ref,
        "dependency_manifest_ref": normalized_dependency_ref,
        "dependency_currentness": normalized_status,
    }
    expected_fingerprint = fingerprint(core)
    supplied_fingerprint = sha256(
        payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint"
    )
    if supplied_fingerprint != expected_fingerprint:
        raise RequestShapeError(f"{field}.receipt_fingerprint is invalid")
    expected_size = len(canonical_json_bytes(core))
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(f"{field}.receipt_size_bytes is invalid")
    receipt_id = text(payload.get("receipt_id"), f"{field}.receipt_id")
    normalized_ref = _exact_ref(
        receipt_ref,
        f"{field}.receipt_ref",
        "mas_build_dependency_currentness_receipt",
    )
    if normalized_ref != {
        "kind": "mas_build_dependency_currentness_receipt",
        "ref": receipt_id,
        "size_bytes": expected_size,
        "sha256": expected_fingerprint,
    }:
        raise RequestShapeError(f"{field}.receipt_ref does not match sealed receipt")
    return {
        **core,
        "receipt_id": receipt_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_affected_artifact_binding(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"member_id", "ref", "size_bytes", "sha256"}, field)
    normalized = {
        "member_id": text(payload.get("member_id"), f"{field}.member_id"),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    if sum(
        all(item[key] == normalized[key] for key in normalized)
        for item in artifacts
    ) != 1:
        raise RequestShapeError(
            f"{field} must match exactly one current manifest artifact member"
        )
    return normalized


def _normalize_reviewer_response_sync(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "response_ref",
            "action_matrix_ref",
            "action_matrix_item_ids",
            "artifact_inventory_ref",
            "candidate_state",
            "sync_status",
            "items",
            "external_synthesis_ref",
            "new_revision_ref",
            "post_freeze_disposition",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_reviewer_response_sync":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    refs = {
        ref_field: _manifest_artifact_ref(
            payload.get(ref_field),
            f"{field}.{ref_field}",
            artifacts=artifacts,
            expected_role=REVIEWER_RESPONSE_ROLE_BY_REF_FIELD[ref_field],
        )
        for ref_field in ("response_ref", "action_matrix_ref", "artifact_inventory_ref")
    }
    action_matrix_item_ids = text_list(
        payload.get("action_matrix_item_ids"),
        f"{field}.action_matrix_item_ids",
    )
    if not action_matrix_item_ids:
        raise RequestShapeError(f"{field}.action_matrix_item_ids must not be empty")
    optional_refs: dict[str, dict[str, Any] | None] = {}
    for ref_field in ("external_synthesis_ref", "new_revision_ref"):
        raw_ref = payload.get(ref_field)
        optional_refs[ref_field] = (
            None
            if raw_ref is None
            else _manifest_artifact_ref(
                raw_ref,
                f"{field}.{ref_field}",
                artifacts=artifacts,
                expected_role=REVIEWER_RESPONSE_ROLE_BY_REF_FIELD[ref_field],
            )
        )
    items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(sequence(payload.get("items"), f"{field}.items")):
        item_field = f"{field}.items[{index}]"
        item_payload = mapping(raw_item, item_field)
        exact_keys(
            item_payload,
            {
                "comment_id",
                "status",
                "affected_artifact_bindings",
                "evidence_refs",
                "remaining_gap_or_not_applicable_reason",
            },
            item_field,
        )
        status = enum_text(
            item_payload.get("status"),
            f"{item_field}.status",
            {
                "planned",
                "implemented_candidate",
                "independently_reviewed_candidate",
                "not_applicable_with_reason",
            },
        )
        affected = [
            _normalize_affected_artifact_binding(
                binding,
                f"{item_field}.affected_artifact_bindings[{binding_index}]",
                artifacts=artifacts,
            )
            for binding_index, binding in enumerate(
                sequence(
                    item_payload.get("affected_artifact_bindings"),
                    f"{item_field}.affected_artifact_bindings",
                )
            )
        ]
        affected.sort(key=lambda item: item["member_id"])
        if len({item["member_id"] for item in affected}) != len(affected):
            raise RequestShapeError(
                f"{item_field}.affected_artifact_bindings contains duplicate members"
            )
        reason = optional_text(
            item_payload.get("remaining_gap_or_not_applicable_reason"),
            f"{item_field}.remaining_gap_or_not_applicable_reason",
        )
        evidence_refs = _normalize_reviewer_response_evidence_refs(
            item_payload.get("evidence_refs"),
            f"{item_field}.evidence_refs",
        )
        if status in {
            "implemented_candidate",
            "independently_reviewed_candidate",
        } and not affected:
            raise RequestShapeError(
                f"{item_field}.{status} requires affected artifact bindings"
            )
        if status in {
            "implemented_candidate",
            "independently_reviewed_candidate",
        } and not evidence_refs:
            raise RequestShapeError(
                f"{item_field}.{status} requires exact evidence refs"
            )
        if status == "not_applicable_with_reason" and reason is None:
            raise RequestShapeError(
                f"{item_field}.not_applicable_with_reason requires a reason"
            )
        items.append(
            {
                "comment_id": text(
                    item_payload.get("comment_id"), f"{item_field}.comment_id"
                ),
                "status": status,
                "affected_artifact_bindings": affected,
                "evidence_refs": evidence_refs,
                "remaining_gap_or_not_applicable_reason": reason,
            }
        )
    if not items or len({item["comment_id"] for item in items}) != len(items):
        raise RequestShapeError(f"{field}.items must be non-empty with unique comment_id")
    comment_ids = {item["comment_id"] for item in items}
    if comment_ids != set(action_matrix_item_ids):
        raise RequestShapeError(
            f"{field}.items must exactly cover action_matrix_item_ids"
        )
    candidate_state = enum_text(
        payload.get("candidate_state"),
        f"{field}.candidate_state",
        {"pre_freeze", "frozen"},
    )
    post_freeze_disposition = enum_text(
        payload.get("post_freeze_disposition"),
        f"{field}.post_freeze_disposition",
        {
            "not_started",
            "external_synthesis_bound",
            "scientific_change_requires_new_revision",
        },
    )
    if candidate_state == "pre_freeze" and (
        post_freeze_disposition != "not_started"
        or any(optional_refs.values())
    ):
        raise RequestShapeError(
            f"{field} pre_freeze sync cannot carry post-freeze refs or disposition"
        )
    if post_freeze_disposition == "external_synthesis_bound" and (
        optional_refs["external_synthesis_ref"] is None
        or optional_refs["new_revision_ref"] is not None
    ):
        raise RequestShapeError(
            f"{field} external synthesis disposition requires only external_synthesis_ref"
        )
    if post_freeze_disposition == "scientific_change_requires_new_revision" and (
        optional_refs["new_revision_ref"] is None
    ):
        raise RequestShapeError(
            f"{field} scientific response change requires new_revision_ref"
        )
    if candidate_state == "frozen" and post_freeze_disposition == "not_started" and any(
        optional_refs.values()
    ):
        raise RequestShapeError(
            f"{field} frozen not_started disposition cannot carry post-freeze refs"
        )
    return {
        "surface_kind": "mas_reviewer_response_sync",
        "schema_version": 1,
        **refs,
        "action_matrix_item_ids": sorted(action_matrix_item_ids),
        "candidate_state": candidate_state,
        "sync_status": enum_text(
            payload.get("sync_status"),
            f"{field}.sync_status",
            {"synchronized", "route_back_required"},
        ),
        "items": sorted(items, key=lambda item: item["comment_id"]),
        **optional_refs,
        "post_freeze_disposition": post_freeze_disposition,
        "authority_boundary": _normalize_no_authority_boundary(
            payload.get("authority_boundary"), f"{field}.authority_boundary"
        ),
    }


def _normalize_reviewer_response_evidence_refs(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for index, raw_ref in enumerate(sequence(value, field)):
        ref_field = f"{field}[{index}]"
        payload = mapping(raw_ref, ref_field)
        kind = enum_text(
            payload.get("kind"),
            f"{ref_field}.kind",
            {"mas_evidence", "mas_reviewer_receipt"},
        )
        refs.append(_exact_ref(payload, ref_field, kind))
    identities = [
        (item["kind"], item["ref"], item["size_bytes"], item["sha256"])
        for item in refs
    ]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate exact refs")
    return refs


def _validate_reviewer_response_evidence_refs(
    response_sync: Mapping[str, Any],
    reviews: list[dict[str, Any]],
    field: str,
) -> None:
    current_review_refs = {
        (
            wrapper["receipt_ref"]["ref"],
            wrapper["receipt_ref"]["size_bytes"],
            wrapper["receipt_ref"]["sha256"],
        )
        for wrapper in reviews
    }
    for index, item in enumerate(response_sync["items"]):
        item_field = f"{field}.items[{index}]"
        evidence_refs = item["evidence_refs"]
        if item["status"] == "independently_reviewed_candidate":
            if any(ref["kind"] != "mas_reviewer_receipt" for ref in evidence_refs):
                raise RequestShapeError(
                    f"{item_field}.independently_reviewed_candidate requires "
                    "current independent reviewer receipt refs"
                )
            for ref in evidence_refs:
                identity = (ref["ref"], ref["size_bytes"], ref["sha256"])
                if identity not in current_review_refs:
                    raise RequestShapeError(
                        f"{item_field}.evidence_refs must bind a current manifest "
                        "independent reviewer receipt"
                    )
        elif any(ref["kind"] != "mas_evidence" for ref in evidence_refs):
            raise RequestShapeError(
                f"{item_field}.{item['status']} accepts only mas_evidence exact refs"
            )
