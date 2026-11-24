"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pydantic import StrictBool, model_validator

from .._record_validation import (
    NonEmptyStr,
    NonNegativeInt,
    OptionalNonEmptyStr,
    RequestShapeError,
    Sha256Text,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    canonical_json_bytes,
    enum_field,
    enum_text,
    exact_int_field,
    exact_ref_field,
    exact_str_field,
    fingerprint,
    mapping,
    sequence,
    typed_ref_list_field,
    validate_record_dict,
    validate_record_model,
)
from .._record_validation import (
    exact_ref as _exact_ref,
)
from .constants import (
    REVIEWER_RESPONSE_ROLE_BY_REF_FIELD,
    SELECTED_BUILD_ROLE_BY_REF_FIELD,
)
from .records import _manifest_artifact_ref


class _NoAuthorityBoundaryModel(StrictRecordModel):
    authorizes_publication: StrictBool
    authorizes_submission: StrictBool

    @model_validator(mode="after")
    def _require_false_flags(self) -> _NoAuthorityBoundaryModel:
        if self.authorizes_publication is not False:
            raise RequestShapeError("__FIELD__.authorizes_publication must be false")
        if self.authorizes_submission is not False:
            raise RequestShapeError("__FIELD__.authorizes_submission must be false")
        return self


class _ClinicalAnalysisIdentityAdmissionModel(StrictRecordModel):
    surface_kind: exact_str_field(
        "mas_clinical_analysis_identity_admission",
        message="__FIELD__ is invalid",
    )
    schema_version: exact_int_field(1)
    status: enum_field({"adjudicator_required", "open_human_gate", "route_back"})
    clinical_analysis_input_identity_ref: Any
    reason_codes: UniqueNonEmptyStrList
    unresolved_items: UniqueNonEmptyStrList
    next_owner: OptionalNonEmptyStr
    human_gate_refs: typed_ref_list_field("mas_human_gate")
    authority_boundary: _NoAuthorityBoundaryModel

    @model_validator(mode="after")
    def _validate_status_rules(self) -> _ClinicalAnalysisIdentityAdmissionModel:
        if self.status == "adjudicator_required" and (
            self.unresolved_items
            or self.next_owner is not None
            or self.human_gate_refs
        ):
            raise RequestShapeError(
                "__FIELD__ adjudicator_required cannot carry unresolved or gate state"
            )
        if self.status == "open_human_gate" and (
            not self.reason_codes
            or not self.unresolved_items
            or self.next_owner is None
            or not self.human_gate_refs
        ):
            raise RequestShapeError(
                "__FIELD__ open_human_gate requires reasons, unresolved items, owner, and refs"
            )
        if self.status == "route_back" and (
            not self.reason_codes
            or not self.unresolved_items
            or self.next_owner != "baseline_and_evidence_setup"
            or self.human_gate_refs
        ):
            raise RequestShapeError(
                "__FIELD__ route_back requires baseline owner and no human-gate refs"
            )
        return self


class _SelectedBuildBindingModel(StrictRecordModel):
    surface_kind: exact_str_field(
        "mas_selected_build_binding",
        message="__FIELD__ is invalid",
    )
    schema_version: exact_int_field(1)
    selected_archive_label: NonEmptyStr
    selected_archive_manifest_ref: Any
    selected_build_receipt_ref: Any
    dependency_manifest_ref: Any
    root_reader_output_ref: Any
    selected_reader_output_ref: Any
    dependency_currentness: enum_field({"current", "stale", "open"})
    dependency_currentness_receipt_ref: exact_ref_field(
        "mas_build_dependency_currentness_receipt"
    )
    dependency_currentness_receipt: Any
    root_matches_selected_bytes: StrictBool
    authority_boundary: _NoAuthorityBoundaryModel


class _DependencyCurrentnessReceiptModel(StrictRecordModel):
    receipt_kind: exact_str_field(
        "mas_build_dependency_currentness_receipt",
        message="__FIELD__ is invalid",
    )
    schema_version: exact_int_field(1)
    owner: exact_str_field("MedAutoScience")
    authority_role: exact_str_field(
        "build_dependency_currentness_owner",
        message="__FIELD__ is invalid",
    )
    authority_ref: exact_ref_field("mas_build_dependency_currentness_authority")
    dependency_manifest_ref: exact_ref_field("mas_artifact")
    dependency_currentness: enum_field({"current", "stale", "open"})
    receipt_id: NonEmptyStr
    receipt_size_bytes: NonNegativeInt
    receipt_fingerprint: Sha256Text


class _AffectedArtifactBindingModel(StrictRecordModel):
    member_id: NonEmptyStr
    ref: NonEmptyStr
    size_bytes: NonNegativeInt
    sha256: Sha256Text


class _ReviewerResponseItemModel(StrictRecordModel):
    comment_id: NonEmptyStr
    status: enum_field(
        {
            "planned",
            "implemented_candidate",
            "independently_reviewed_candidate",
            "not_applicable_with_reason",
        }
    )
    affected_artifact_bindings: Any
    evidence_refs: Any
    remaining_gap_or_not_applicable_reason: OptionalNonEmptyStr


class _ReviewerResponseSyncModel(StrictRecordModel):
    surface_kind: exact_str_field(
        "mas_reviewer_response_sync",
        message="__FIELD__ is invalid",
    )
    schema_version: exact_int_field(1)
    response_ref: Any
    action_matrix_ref: Any
    action_matrix_item_ids: UniqueNonEmptyStrList
    artifact_inventory_ref: Any
    candidate_state: enum_field({"pre_freeze", "frozen"})
    sync_status: enum_field({"synchronized", "route_back_required"})
    items: Any
    external_synthesis_ref: Any
    new_revision_ref: Any
    post_freeze_disposition: enum_field(
        {
            "not_started",
            "external_synthesis_bound",
            "scientific_change_requires_new_revision",
        }
    )
    authority_boundary: _NoAuthorityBoundaryModel


def _normalize_no_authority_boundary(value: Any, field: str) -> dict[str, bool]:
    return validate_record_dict(_NoAuthorityBoundaryModel, value, field)


def _normalize_clinical_analysis_identity_admission(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed = validate_record_model(
        _ClinicalAnalysisIdentityAdmissionModel, value, field
    )
    result = parsed.model_dump()
    result["clinical_analysis_input_identity_ref"] = _manifest_artifact_ref(
        parsed.clinical_analysis_input_identity_ref,
        f"{field}.clinical_analysis_input_identity_ref",
        artifacts=artifacts,
        expected_role="clinical_analysis_input_identity",
    )
    return result


def _normalize_selected_build_binding(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed = validate_record_model(_SelectedBuildBindingModel, value, field)
    refs = {
        ref_field: _manifest_artifact_ref(
            getattr(parsed, ref_field),
            f"{field}.{ref_field}",
            artifacts=artifacts,
            expected_role=role,
        )
        for ref_field, role in SELECTED_BUILD_ROLE_BY_REF_FIELD.items()
    }
    exact_bytes_match = (
        refs["root_reader_output_ref"]["size_bytes"]
        == refs["selected_reader_output_ref"]["size_bytes"]
        and refs["root_reader_output_ref"]["sha256"]
        == refs["selected_reader_output_ref"]["sha256"]
    )
    if parsed.root_matches_selected_bytes != exact_bytes_match:
        raise RequestShapeError(
            f"{field}.root_matches_selected_bytes does not match exact reader bytes"
        )
    return {
        "surface_kind": "mas_selected_build_binding",
        "schema_version": 1,
        "selected_archive_label": parsed.selected_archive_label,
        **refs,
        "dependency_currentness": parsed.dependency_currentness,
        "dependency_currentness_receipt_ref": parsed.dependency_currentness_receipt_ref,
        "dependency_currentness_receipt": _normalize_dependency_currentness_receipt(
            parsed.dependency_currentness_receipt,
            f"{field}.dependency_currentness_receipt",
            dependency_manifest_ref=refs["dependency_manifest_ref"],
            dependency_currentness=parsed.dependency_currentness,
            receipt_ref=parsed.dependency_currentness_receipt_ref,
        ),
        "root_matches_selected_bytes": parsed.root_matches_selected_bytes,
        "authority_boundary": parsed.authority_boundary.model_dump(),
    }


def _normalize_dependency_currentness_receipt(
    value: Any,
    field: str,
    *,
    dependency_manifest_ref: Mapping[str, Any],
    dependency_currentness: str,
    receipt_ref: Any,
) -> dict[str, Any]:
    parsed = validate_record_model(_DependencyCurrentnessReceiptModel, value, field)
    if parsed.dependency_manifest_ref != dict(dependency_manifest_ref):
        raise RequestShapeError(
            f"{field}.dependency_manifest_ref does not match selected build binding"
        )
    if parsed.dependency_currentness != dependency_currentness:
        raise RequestShapeError(
            f"{field}.dependency_currentness does not match selected build binding"
        )
    core = {
        "receipt_kind": "mas_build_dependency_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "build_dependency_currentness_owner",
        "authority_ref": parsed.authority_ref,
        "dependency_manifest_ref": parsed.dependency_manifest_ref,
        "dependency_currentness": parsed.dependency_currentness,
    }
    expected_fingerprint = fingerprint(core)
    if parsed.receipt_fingerprint != expected_fingerprint:
        raise RequestShapeError(f"{field}.receipt_fingerprint is invalid")
    expected_size = len(canonical_json_bytes(core))
    if parsed.receipt_size_bytes != expected_size:
        raise RequestShapeError(f"{field}.receipt_size_bytes is invalid")
    normalized_ref = _exact_ref(
        receipt_ref,
        f"{field}.receipt_ref",
        "mas_build_dependency_currentness_receipt",
    )
    if normalized_ref != {
        "kind": "mas_build_dependency_currentness_receipt",
        "ref": parsed.receipt_id,
        "size_bytes": expected_size,
        "sha256": expected_fingerprint,
    }:
        raise RequestShapeError(f"{field}.receipt_ref does not match sealed receipt")
    return {
        **core,
        "receipt_id": parsed.receipt_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_affected_artifact_binding(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    normalized = validate_record_dict(_AffectedArtifactBindingModel, value, field)
    if (
        sum(
            all(item[key] == normalized[key] for key in normalized)
            for item in artifacts
        )
        != 1
    ):
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
    parsed = validate_record_model(_ReviewerResponseSyncModel, value, field)
    refs = {
        ref_field: _manifest_artifact_ref(
            getattr(parsed, ref_field),
            f"{field}.{ref_field}",
            artifacts=artifacts,
            expected_role=REVIEWER_RESPONSE_ROLE_BY_REF_FIELD[ref_field],
        )
        for ref_field in ("response_ref", "action_matrix_ref", "artifact_inventory_ref")
    }
    action_matrix_item_ids = parsed.action_matrix_item_ids
    if not action_matrix_item_ids:
        raise RequestShapeError(f"{field}.action_matrix_item_ids must not be empty")
    optional_refs: dict[str, dict[str, Any] | None] = {}
    for ref_field in ("external_synthesis_ref", "new_revision_ref"):
        raw_ref = getattr(parsed, ref_field)
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
    for index, raw_item in enumerate(sequence(parsed.items, f"{field}.items")):
        item_field = f"{field}.items[{index}]"
        item_model = validate_record_model(
            _ReviewerResponseItemModel, raw_item, item_field
        )
        status = item_model.status
        affected = [
            _normalize_affected_artifact_binding(
                binding,
                f"{item_field}.affected_artifact_bindings[{binding_index}]",
                artifacts=artifacts,
            )
            for binding_index, binding in enumerate(
                sequence(
                    item_model.affected_artifact_bindings,
                    f"{item_field}.affected_artifact_bindings",
                )
            )
        ]
        affected.sort(key=lambda item: item["member_id"])
        if len({item["member_id"] for item in affected}) != len(affected):
            raise RequestShapeError(
                f"{item_field}.affected_artifact_bindings contains duplicate members"
            )
        reason = item_model.remaining_gap_or_not_applicable_reason
        evidence_refs = _normalize_reviewer_response_evidence_refs(
            item_model.evidence_refs,
            f"{item_field}.evidence_refs",
        )
        if (
            status in {"implemented_candidate", "independently_reviewed_candidate"}
            and not affected
        ):
            raise RequestShapeError(
                f"{item_field}.{status} requires affected artifact bindings"
            )
        if (
            status in {"implemented_candidate", "independently_reviewed_candidate"}
            and not evidence_refs
        ):
            raise RequestShapeError(
                f"{item_field}.{status} requires exact evidence refs"
            )
        if status == "not_applicable_with_reason" and reason is None:
            raise RequestShapeError(
                f"{item_field}.not_applicable_with_reason requires a reason"
            )
        items.append(
            {
                "comment_id": item_model.comment_id,
                "status": status,
                "affected_artifact_bindings": affected,
                "evidence_refs": evidence_refs,
                "remaining_gap_or_not_applicable_reason": reason,
            }
        )
    if not items or len({item["comment_id"] for item in items}) != len(items):
        raise RequestShapeError(
            f"{field}.items must be non-empty with unique comment_id"
        )
    comment_ids = {item["comment_id"] for item in items}
    if comment_ids != set(action_matrix_item_ids):
        raise RequestShapeError(
            f"{field}.items must exactly cover action_matrix_item_ids"
        )
    candidate_state = parsed.candidate_state
    post_freeze_disposition = parsed.post_freeze_disposition
    if candidate_state == "pre_freeze" and (
        post_freeze_disposition != "not_started" or any(optional_refs.values())
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
    if (
        post_freeze_disposition == "scientific_change_requires_new_revision"
        and optional_refs["new_revision_ref"] is None
    ):
        raise RequestShapeError(
            f"{field} scientific response change requires new_revision_ref"
        )
    if (
        candidate_state == "frozen"
        and post_freeze_disposition == "not_started"
        and any(optional_refs.values())
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
        "sync_status": parsed.sync_status,
        "items": sorted(items, key=lambda item: item["comment_id"]),
        **optional_refs,
        "post_freeze_disposition": post_freeze_disposition,
        "authority_boundary": parsed.authority_boundary.model_dump(),
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
