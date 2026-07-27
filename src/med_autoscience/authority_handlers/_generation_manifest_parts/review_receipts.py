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

def _normalize_review_scope(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "scope_policy_id",
            "scope_policy_version",
            "review_lane",
            "review_scope_sha256",
            "reviewed_members",
            "epistemic_scope",
        },
        field,
    )
    if payload.get("scope_policy_id") != REVIEW_SCOPE_POLICY_ID:
        raise RequestShapeError(
            f"{field}.scope_policy_id must be {REVIEW_SCOPE_POLICY_ID}"
        )
    if payload.get("scope_policy_version") != REVIEW_SCOPE_POLICY_VERSION or isinstance(
        payload.get("scope_policy_version"), bool
    ):
        raise RequestShapeError(
            f"{field}.scope_policy_version must be integer {REVIEW_SCOPE_POLICY_VERSION}"
        )
    lane = enum_text(
        payload.get("review_lane"),
        f"{field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    expected_members = review_scope_inventory(lane, artifacts)
    supplied_members = [
        _normalize_artifact(
            item,
            f"{field}.reviewed_members[{index}]",
            allowed_roles=frozenset(artifact["role"] for artifact in artifacts),
            schema_version=2,
        )
        for index, item in enumerate(
            sequence(payload.get("reviewed_members"), f"{field}.reviewed_members")
        )
    ]
    _require_unique_member_ids(supplied_members, f"{field}.reviewed_members")
    supplied_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if supplied_members != expected_members:
        raise RequestShapeError(
            f"{field}.reviewed_members must equal the MAS-owned lane inventory"
        )
    expected_sha256 = review_scope_sha256(lane, expected_members)
    if (
        sha256(payload.get("review_scope_sha256"), f"{field}.review_scope_sha256")
        != expected_sha256
    ):
        raise RequestShapeError(
            f"{field}.review_scope_sha256 does not match the dependency declaration"
        )
    expected_epistemic_scope = build_epistemic_review_scope(lane, expected_members)
    if payload.get("epistemic_scope") != expected_epistemic_scope:
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
    wrapper = mapping(value, field)
    exact_keys(wrapper, {"receipt_ref", "receipt"}, field)
    receipt_ref = _exact_ref(
        wrapper.get("receipt_ref"),
        f"{field}.receipt_ref",
        "mas_reviewer_receipt",
    )
    receipt_field = f"{field}.receipt"
    payload = mapping(wrapper.get("receipt"), receipt_field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "issuer",
            "authority_role",
            "authority_epoch",
            "review_lane",
            "verdict",
            "review_request_ref",
            "producer_output_ref",
            "reviewer_attempt_ref",
            "rubric_ref",
            "generation_id",
            "generation_manifest_sha256",
            "reviewed_members",
            "accepted_candidate_receipt_refs",
            "defect_refs",
            "quality_debt_codes",
        },
        receipt_field,
    )
    if payload.get("receipt_kind") != "mas_independent_review_receipt":
        raise RequestShapeError(
            f"{receipt_field}.receipt_kind must be mas_independent_review_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{receipt_field}.schema_version must be integer 1")
    if payload.get("issuer") != "MedAutoScience":
        raise RequestShapeError(f"{receipt_field}.issuer must be MedAutoScience")
    lane = enum_text(
        payload.get("review_lane"),
        f"{receipt_field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    expected_role = REVIEW_AUTHORITY_ROLE_BY_LANE[lane]
    if payload.get("authority_role") != expected_role:
        raise RequestShapeError(
            f"{receipt_field}.authority_role must be {expected_role}"
        )
    receipt_generation = text(
        payload.get("generation_id"), f"{receipt_field}.generation_id"
    )
    if receipt_generation != generation_id:
        raise RequestShapeError(
            f"{receipt_field}.generation_id does not match generation_manifest"
        )
    receipt_manifest = sha256(
        payload.get("generation_manifest_sha256"),
        f"{receipt_field}.generation_manifest_sha256",
    )
    if receipt_manifest != manifest_sha256:
        raise RequestShapeError(f"{receipt_field}.generation_manifest_sha256 is stale")
    reviewed_members = [
        _normalize_artifact(
            item,
            f"{receipt_field}.reviewed_members[{index}]",
            allowed_roles=frozenset(item["role"] for item in artifacts),
        )
        for index, item in enumerate(
            sequence(
                payload.get("reviewed_members"),
                f"{receipt_field}.reviewed_members",
            )
        )
    ]
    reviewed_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if reviewed_members != artifacts:
        raise RequestShapeError(
            f"{receipt_field}.reviewed_members must equal the canonical manifest inventory"
        )

    candidate_receipt_refs = _exact_ref_list(
        payload.get("accepted_candidate_receipt_refs"),
        f"{receipt_field}.accepted_candidate_receipt_refs",
        "mas_candidate_admission_receipt",
    )
    manifest_candidate_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in artifacts
        if item["role"] == "candidate_admission_receipt"
    }
    supplied_candidate_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in candidate_receipt_refs
    }
    if supplied_candidate_receipts != manifest_candidate_receipts:
        raise RequestShapeError(
            f"{receipt_field}.accepted_candidate_receipt_refs must equal the manifest receipt inventory"
        )

    core = {
        "receipt_kind": "mas_independent_review_receipt",
        "schema_version": 1,
        "issuer": "MedAutoScience",
        "authority_role": expected_role,
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{receipt_field}.authority_epoch"
        ),
        "review_lane": lane,
        "verdict": enum_text(
            payload.get("verdict"),
            f"{receipt_field}.verdict",
            {"passed", "revision_required", "rejected"},
        ),
        "review_request_ref": _exact_ref(
            payload.get("review_request_ref"),
            f"{receipt_field}.review_request_ref",
            "opl_action_output",
        ),
        "producer_output_ref": _exact_ref(
            payload.get("producer_output_ref"),
            f"{receipt_field}.producer_output_ref",
            "opl_action_output",
        ),
        "reviewer_attempt_ref": _typed_ref(
            payload.get("reviewer_attempt_ref"),
            f"{receipt_field}.reviewer_attempt_ref",
            "opl_stage_attempt",
        ),
        "rubric_ref": _typed_ref(
            payload.get("rubric_ref"),
            f"{receipt_field}.rubric_ref",
            "mas_quality_rubric",
        ),
        "generation_id": generation_id,
        "generation_manifest_sha256": manifest_sha256,
        "reviewed_members": reviewed_members,
        "accepted_candidate_receipt_refs": candidate_receipt_refs,
        "defect_refs": _typed_ref_list(
            payload.get("defect_refs"),
            f"{receipt_field}.defect_refs",
            "mas_review_defect",
        ),
        "quality_debt_codes": text_list(
            payload.get("quality_debt_codes"),
            f"{receipt_field}.quality_debt_codes",
        ),
    }
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
    return {"receipt_ref": receipt_ref, "receipt": core}


def _normalize_review_receipt_v2(
    value: Any,
    field: str,
    *,
    review_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = mapping(value, field)
    exact_keys(wrapper, {"receipt_ref", "receipt"}, field)
    receipt_ref = _exact_ref(
        wrapper.get("receipt_ref"),
        f"{field}.receipt_ref",
        "mas_reviewer_receipt",
    )
    receipt_field = f"{field}.receipt"
    payload = mapping(wrapper.get("receipt"), receipt_field)
    receipt_keys = {
        "receipt_kind",
        "schema_version",
        "issuer",
        "authority_role",
        "authority_epoch",
        "review_lane",
        "verdict",
        "review_request_ref",
        "producer_output_ref",
        "reviewer_attempt_ref",
        "rubric_ref",
        "issued_generation_id",
        "issued_generation_manifest_sha256",
        "scope_policy_id",
        "scope_policy_version",
        "review_scope_sha256",
        "reviewed_members",
        "review_input_snapshot_binding",
        "accepted_candidate_receipt_refs",
        "defect_refs",
        "quality_debt_codes",
    }
    exact_keys(payload, receipt_keys, receipt_field)
    if payload.get("receipt_kind") != "mas_independent_review_receipt":
        raise RequestShapeError(
            f"{receipt_field}.receipt_kind must be mas_independent_review_receipt"
        )
    if payload.get("schema_version") != 2 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{receipt_field}.schema_version must be integer 2")
    if payload.get("issuer") != "MedAutoScience":
        raise RequestShapeError(f"{receipt_field}.issuer must be MedAutoScience")
    if payload.get("scope_policy_id") != REVIEW_SCOPE_POLICY_ID:
        raise RequestShapeError(
            f"{receipt_field}.scope_policy_id must be {REVIEW_SCOPE_POLICY_ID}"
        )
    if payload.get("scope_policy_version") != REVIEW_SCOPE_POLICY_VERSION or isinstance(
        payload.get("scope_policy_version"), bool
    ):
        raise RequestShapeError(
            f"{receipt_field}.scope_policy_version must be integer {REVIEW_SCOPE_POLICY_VERSION}"
        )
    lane = enum_text(
        payload.get("review_lane"),
        f"{receipt_field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    expected_role = REVIEW_AUTHORITY_ROLE_BY_LANE[lane]
    if payload.get("authority_role") != expected_role:
        raise RequestShapeError(
            f"{receipt_field}.authority_role must be {expected_role}"
        )
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
            sequence(
                payload.get("reviewed_members"),
                f"{receipt_field}.reviewed_members",
            )
        )
    ]
    _require_unique_member_ids(reviewed_members, f"{receipt_field}.reviewed_members")
    reviewed_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    expected_scope_sha256 = review_scope_sha256(lane, reviewed_members)
    supplied_scope_sha256 = sha256(
        payload.get("review_scope_sha256"),
        f"{receipt_field}.review_scope_sha256",
    )
    if supplied_scope_sha256 != expected_scope_sha256:
        raise RequestShapeError(
            f"{receipt_field}.review_scope_sha256 does not match reviewed members"
        )
    candidate_receipt_refs = _exact_ref_list(
        payload.get("accepted_candidate_receipt_refs"),
        f"{receipt_field}.accepted_candidate_receipt_refs",
        "mas_candidate_admission_receipt",
    )
    snapshot_binding = _normalize_review_input_snapshot_binding(
        payload.get("review_input_snapshot_binding"),
        f"{receipt_field}.review_input_snapshot_binding",
    )
    core = {
        "receipt_kind": "mas_independent_review_receipt",
        "schema_version": 2,
        "issuer": "MedAutoScience",
        "authority_role": expected_role,
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{receipt_field}.authority_epoch"
        ),
        "review_lane": lane,
        "verdict": enum_text(
            payload.get("verdict"),
            f"{receipt_field}.verdict",
            {"passed", "revision_required", "rejected"},
        ),
        "review_request_ref": _exact_ref(
            payload.get("review_request_ref"),
            f"{receipt_field}.review_request_ref",
            "opl_action_output",
        ),
        "producer_output_ref": _exact_ref(
            payload.get("producer_output_ref"),
            f"{receipt_field}.producer_output_ref",
            "opl_action_output",
        ),
        "reviewer_attempt_ref": _typed_ref(
            payload.get("reviewer_attempt_ref"),
            f"{receipt_field}.reviewer_attempt_ref",
            "opl_stage_attempt",
        ),
        "rubric_ref": _typed_ref(
            payload.get("rubric_ref"),
            f"{receipt_field}.rubric_ref",
            "mas_quality_rubric",
        ),
        "issued_generation_id": text(
            payload.get("issued_generation_id"),
            f"{receipt_field}.issued_generation_id",
        ),
        "issued_generation_manifest_sha256": sha256(
            payload.get("issued_generation_manifest_sha256"),
            f"{receipt_field}.issued_generation_manifest_sha256",
        ),
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_scope_sha256": supplied_scope_sha256,
        "reviewed_members": reviewed_members,
        "review_input_snapshot_binding": snapshot_binding,
        "accepted_candidate_receipt_refs": candidate_receipt_refs,
        "defect_refs": _typed_ref_list(
            payload.get("defect_refs"),
            f"{receipt_field}.defect_refs",
            "mas_review_defect",
        ),
        "quality_debt_codes": text_list(
            payload.get("quality_debt_codes"),
            f"{receipt_field}.quality_debt_codes",
        ),
    }
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
    return {"receipt_ref": receipt_ref, "receipt": core}


def _normalize_review_input_snapshot_binding(
    value: Any,
    field: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "snapshot_manifest_ref",
            "owner_authority_ref",
            "producer_attempt_ref",
            "execution_content_binding_sha256",
        },
        field,
    )
    if payload.get("surface_kind") != "opl_reviewer_input_snapshot_binding":
        raise RequestShapeError(
            f"{field}.surface_kind must be opl_reviewer_input_snapshot_binding"
        )
    if payload.get("schema_version") != 3 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 3")
    producer_attempt_ref = text(
        payload.get("producer_attempt_ref"), f"{field}.producer_attempt_ref"
    )
    if not producer_attempt_ref.startswith("opl://stage_attempts/"):
        raise RequestShapeError(
            f"{field}.producer_attempt_ref must reference one OPL Stage Attempt"
        )
    owner_authority_ref = _exact_ref(
        payload.get("owner_authority_ref"),
        f"{field}.owner_authority_ref",
        "mas_review_input_snapshot_authority",
    )
    expected_authority_ref = (
        "mas-review-input-snapshot-authority:"
        f"{owner_authority_ref['sha256'].removeprefix('sha256:')}"
    )
    if (
        owner_authority_ref["ref"] != expected_authority_ref
        or owner_authority_ref["size_bytes"] < 1
    ):
        raise RequestShapeError(
            f"{field}.owner_authority_ref must bind canonical MAS authority bytes"
        )
    normalized = {
        "surface_kind": "opl_reviewer_input_snapshot_binding",
        "schema_version": 3,
        "snapshot_manifest_ref": _exact_ref(
            payload.get("snapshot_manifest_ref"),
            f"{field}.snapshot_manifest_ref",
            "opl_reviewer_input_snapshot_manifest",
        ),
        "owner_authority_ref": owner_authority_ref,
        "producer_attempt_ref": producer_attempt_ref,
        "execution_content_binding_sha256": sha256(
            payload.get("execution_content_binding_sha256"),
            f"{field}.execution_content_binding_sha256",
        ),
    }
    return normalized
