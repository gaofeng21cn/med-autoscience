"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from typing import Any

from pydantic import ValidationInfo, model_validator

from .._record_validation import (
    NonEmptyStr,
    RequestShapeError,
    Sha256Text,
    StrictRecordModel,
    UniqueNonEmptyStrList,
    canonical_json_bytes,
    enum_field,
    exact_int_field,
    exact_ref_field,
    exact_ref_list_field,
    exact_str_field,
    fingerprint,
    integer,
    mapping,
    sequence,
    typed_ref_field,
    typed_ref_list_field,
    validate_record_dict,
    validate_record_model,
)
from .constants import (
    REVIEW_AUTHORITY_ROLE_BY_LANE,
    REVIEW_SCOPE_POLICY_ID,
    REVIEW_SCOPE_POLICY_VERSION,
    REVIEW_SCOPE_ROLES_BY_LANE,
)
from .records import (
    _normalize_artifact,
    _require_unique_member_ids,
)
from .review_scope import (
    build_epistemic_review_scope,
    review_scope_inventory,
    review_scope_sha256,
)


class _ReviewScopeModel(StrictRecordModel):
    scope_policy_id: exact_str_field(REVIEW_SCOPE_POLICY_ID)
    scope_policy_version: exact_int_field(REVIEW_SCOPE_POLICY_VERSION)
    review_lane: enum_field(REVIEW_AUTHORITY_ROLE_BY_LANE)
    review_scope_sha256: Sha256Text
    reviewed_members: Any
    epistemic_scope: Any


class _ReviewReceiptWrapperModel(StrictRecordModel):
    receipt_ref: exact_ref_field("mas_reviewer_receipt")
    receipt: Any


class _ReviewInputSnapshotBindingModel(StrictRecordModel):
    surface_kind: exact_str_field("opl_reviewer_input_snapshot_binding")
    schema_version: exact_int_field(3)
    snapshot_manifest_ref: exact_ref_field("opl_reviewer_input_snapshot_manifest")
    owner_authority_ref: exact_ref_field("mas_review_input_snapshot_authority")
    producer_attempt_ref: NonEmptyStr
    execution_content_binding_sha256: Sha256Text

    @model_validator(mode="after")
    def _validate_binding(self) -> _ReviewInputSnapshotBindingModel:
        if not self.producer_attempt_ref.startswith("opl://stage_attempts/"):
            raise RequestShapeError(
                "__FIELD__.producer_attempt_ref must reference one OPL Stage Attempt"
            )
        expected_authority_ref = (
            "mas-review-input-snapshot-authority:"
            f"{self.owner_authority_ref['sha256'].removeprefix('sha256:')}"
        )
        if (
            self.owner_authority_ref["ref"] != expected_authority_ref
            or self.owner_authority_ref["size_bytes"] < 1
        ):
            raise RequestShapeError(
                "__FIELD__.owner_authority_ref must bind canonical MAS authority bytes"
            )
        return self


class _ReviewReceiptV1Model(StrictRecordModel):
    receipt_kind: exact_str_field("mas_independent_review_receipt")
    schema_version: exact_int_field(1)
    issuer: exact_str_field("MedAutoScience")
    authority_role: NonEmptyStr
    authority_epoch: NonEmptyStr
    review_lane: enum_field(REVIEW_AUTHORITY_ROLE_BY_LANE)
    verdict: enum_field({"passed", "revision_required", "rejected"})
    review_request_ref: exact_ref_field("opl_action_output")
    producer_output_ref: exact_ref_field("opl_action_output")
    reviewer_attempt_ref: typed_ref_field("opl_stage_attempt")
    rubric_ref: typed_ref_field("mas_quality_rubric")
    generation_id: NonEmptyStr
    generation_manifest_sha256: Sha256Text
    reviewed_members: Any
    accepted_candidate_receipt_refs: exact_ref_list_field(
        "mas_candidate_admission_receipt"
    )
    defect_refs: typed_ref_list_field("mas_review_defect")
    quality_debt_codes: UniqueNonEmptyStrList

    @model_validator(mode="after")
    def _validate_authority_role(self, info: ValidationInfo) -> _ReviewReceiptV1Model:
        field = (info.context or {}).get("root_field", "receipt")
        expected_role = REVIEW_AUTHORITY_ROLE_BY_LANE[self.review_lane]
        if self.authority_role != expected_role:
            raise RequestShapeError(f"{field}.authority_role must be {expected_role}")
        return self


class _ReviewReceiptV2Model(StrictRecordModel):
    receipt_kind: exact_str_field("mas_independent_review_receipt")
    schema_version: exact_int_field(2)
    issuer: exact_str_field("MedAutoScience")
    authority_role: NonEmptyStr
    authority_epoch: NonEmptyStr
    review_lane: enum_field(REVIEW_AUTHORITY_ROLE_BY_LANE)
    verdict: enum_field({"passed", "revision_required", "rejected"})
    review_request_ref: exact_ref_field("opl_action_output")
    producer_output_ref: exact_ref_field("opl_action_output")
    reviewer_attempt_ref: typed_ref_field("opl_stage_attempt")
    rubric_ref: typed_ref_field("mas_quality_rubric")
    issued_generation_id: NonEmptyStr
    issued_generation_manifest_sha256: Sha256Text
    scope_policy_id: exact_str_field(REVIEW_SCOPE_POLICY_ID)
    scope_policy_version: exact_int_field(REVIEW_SCOPE_POLICY_VERSION)
    review_scope_sha256: Sha256Text
    reviewed_members: Any
    review_input_snapshot_binding: _ReviewInputSnapshotBindingModel
    accepted_candidate_receipt_refs: exact_ref_list_field(
        "mas_candidate_admission_receipt"
    )
    defect_refs: typed_ref_list_field("mas_review_defect")
    quality_debt_codes: UniqueNonEmptyStrList

    @model_validator(mode="after")
    def _validate_authority_role(self, info: ValidationInfo) -> _ReviewReceiptV2Model:
        field = (info.context or {}).get("root_field", "receipt")
        expected_role = REVIEW_AUTHORITY_ROLE_BY_LANE[self.review_lane]
        if self.authority_role != expected_role:
            raise RequestShapeError(f"{field}.authority_role must be {expected_role}")
        return self


def _verify_canonical_review_receipt_ref(
    *,
    field: str,
    lane: str,
    receipt_ref: dict[str, Any],
    core: dict[str, Any],
) -> None:
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_ref = (
        "mas-independent-review-receipt:"
        f"{lane}:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if (
        receipt_ref["ref"] != expected_ref
        or receipt_ref["sha256"] != expected_fingerprint
        or receipt_ref["size_bytes"] != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_ref identity/size/hash does not match canonical receipt bytes"
        )


def _normalize_review_scope(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    parsed = validate_record_model(_ReviewScopeModel, value, field)
    lane = parsed.review_lane
    expected_members = review_scope_inventory(lane, artifacts)
    supplied_members = [
        _normalize_artifact(
            item,
            f"{field}.reviewed_members[{index}]",
            allowed_roles=frozenset(artifact["role"] for artifact in artifacts),
            schema_version=2,
        )
        for index, item in enumerate(
            sequence(parsed.reviewed_members, f"{field}.reviewed_members")
        )
    ]
    _require_unique_member_ids(supplied_members, f"{field}.reviewed_members")
    supplied_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if supplied_members != expected_members:
        raise RequestShapeError(
            f"{field}.reviewed_members must equal the MAS-owned lane inventory"
        )
    expected_sha256 = review_scope_sha256(lane, expected_members)
    if parsed.review_scope_sha256 != expected_sha256:
        raise RequestShapeError(
            f"{field}.review_scope_sha256 does not match the dependency declaration"
        )
    expected_epistemic_scope = build_epistemic_review_scope(lane, expected_members)
    if parsed.epistemic_scope != expected_epistemic_scope:
        raise RequestShapeError(
            f"{field}.epistemic_scope must equal the MAS-owned dependency declaration"
        )
    return {
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_lane": lane,
        "review_scope_sha256": expected_sha256,
        "reviewed_members": expected_members,
        "epistemic_scope": expected_epistemic_scope,
    }


def _normalize_review_receipt(
    value: Any,
    field: str,
    *,
    generation_id: str,
    manifest_sha256: str,
    artifacts: list[dict[str, Any]],
    manifest_version: int,
    review_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = mapping(value, field)
    receipt = mapping(wrapper.get("receipt"), f"{field}.receipt")
    receipt_version = integer(
        receipt.get("schema_version"), f"{field}.receipt.schema_version"
    )
    if receipt_version != manifest_version:
        raise RequestShapeError(
            f"{field}.receipt.schema_version must match generation manifest"
        )
    if receipt_version == 1:
        return _normalize_review_receipt_v1(
            value,
            field,
            generation_id=generation_id,
            manifest_sha256=manifest_sha256,
            artifacts=artifacts,
        )
    if receipt_version == 2:
        return _normalize_review_receipt_v2(
            value,
            field,
            review_scopes=review_scopes,
        )
    raise RequestShapeError(f"{field}.receipt.schema_version must be integer 1 or 2")


def _normalize_review_receipt_v1(
    value: Any,
    field: str,
    *,
    generation_id: str,
    manifest_sha256: str,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = validate_record_model(_ReviewReceiptWrapperModel, value, field)
    receipt_field = f"{field}.receipt"
    parsed = validate_record_model(_ReviewReceiptV1Model, wrapper.receipt, receipt_field)
    if parsed.generation_id != generation_id:
        raise RequestShapeError(
            f"{receipt_field}.generation_id does not match generation_manifest"
        )
    if parsed.generation_manifest_sha256 != manifest_sha256:
        raise RequestShapeError(f"{receipt_field}.generation_manifest_sha256 is stale")

    reviewed_members = [
        _normalize_artifact(
            item,
            f"{receipt_field}.reviewed_members[{index}]",
            allowed_roles=frozenset(item["role"] for item in artifacts),
        )
        for index, item in enumerate(
            sequence(parsed.reviewed_members, f"{receipt_field}.reviewed_members")
        )
    ]
    reviewed_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if reviewed_members != artifacts:
        raise RequestShapeError(
            f"{receipt_field}.reviewed_members must equal the canonical manifest inventory"
        )

    manifest_candidate_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in artifacts
        if item["role"] == "candidate_admission_receipt"
    }
    supplied_candidate_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in parsed.accepted_candidate_receipt_refs
    }
    if supplied_candidate_receipts != manifest_candidate_receipts:
        raise RequestShapeError(
            f"{receipt_field}.accepted_candidate_receipt_refs must equal the manifest receipt inventory"
        )

    core = parsed.model_dump()
    core["reviewed_members"] = reviewed_members
    _verify_canonical_review_receipt_ref(
        field=field,
        lane=parsed.review_lane,
        receipt_ref=wrapper.receipt_ref,
        core=core,
    )
    return {"receipt_ref": wrapper.receipt_ref, "receipt": core}


def _normalize_review_receipt_v2(
    value: Any,
    field: str,
    *,
    review_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = validate_record_model(_ReviewReceiptWrapperModel, value, field)
    receipt_field = f"{field}.receipt"
    parsed = validate_record_model(_ReviewReceiptV2Model, wrapper.receipt, receipt_field)
    lane = parsed.review_lane
    scope = next(
        (item for item in review_scopes if item["review_lane"] == lane),
        None,
    )
    if scope is None:
        raise RequestShapeError(
            f"{receipt_field}.review_lane has no manifest review scope"
        )
    allowed_receipt_roles = REVIEW_SCOPE_ROLES_BY_LANE[lane]
    reviewed_members = [
        _normalize_artifact(
            item,
            f"{receipt_field}.reviewed_members[{index}]",
            allowed_roles=allowed_receipt_roles,
            schema_version=2,
        )
        for index, item in enumerate(
            sequence(parsed.reviewed_members, f"{receipt_field}.reviewed_members")
        )
    ]
    _require_unique_member_ids(reviewed_members, f"{receipt_field}.reviewed_members")
    reviewed_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    expected_scope_sha256 = review_scope_sha256(lane, reviewed_members)
    if parsed.review_scope_sha256 != expected_scope_sha256:
        raise RequestShapeError(
            f"{receipt_field}.review_scope_sha256 does not match reviewed members"
        )

    core = parsed.model_dump()
    core["reviewed_members"] = reviewed_members
    _verify_canonical_review_receipt_ref(
        field=field,
        lane=lane,
        receipt_ref=wrapper.receipt_ref,
        core=core,
    )
    return {"receipt_ref": wrapper.receipt_ref, "receipt": core}


def _normalize_review_input_snapshot_binding(
    value: Any,
    field: str,
) -> dict[str, Any]:
    return validate_record_dict(_ReviewInputSnapshotBindingModel, value, field)
