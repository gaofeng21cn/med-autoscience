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
    REVIEW_LANES_BY_SCOPE,
    REVIEW_SCOPE_POLICY_ID,
    REVIEW_SCOPE_POLICY_VERSION,
    STAGE_FIXED_REVIEW_LANE,
    STAGE_MINIMUM_SCOPE,
)
from .manifest import (
    build_generation_manifest_v2,
    normalize_generation_manifest,
)
from .review_scope import (
    review_scope_member_projection,
)

def _normalize_review_input_snapshot_authority_issuer(
    value: Any,
    field: str = "authority_issuer",
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {
        "agent_id",
        "domain_id",
        "package_id",
        "stage_attempt_ref",
        "execution_content_binding_sha256",
        "package_use_boundary_id",
        "root_package_content_digest",
    }
    exact_keys(payload, keys, field)
    if payload.get("agent_id") != "mas":
        raise RequestShapeError(f"{field}.agent_id must be mas")
    if payload.get("domain_id") != "medautoscience":
        raise RequestShapeError(f"{field}.domain_id must be medautoscience")
    if payload.get("package_id") != "mas":
        raise RequestShapeError(f"{field}.package_id must be mas")
    stage_attempt_ref = text(
        payload.get("stage_attempt_ref"),
        f"{field}.stage_attempt_ref",
    )
    if not stage_attempt_ref.startswith("opl://stage_attempts/"):
        raise RequestShapeError(
            f"{field}.stage_attempt_ref must reference one OPL Stage Attempt"
        )
    return {
        "agent_id": "mas",
        "domain_id": "medautoscience",
        "package_id": "mas",
        "stage_attempt_ref": stage_attempt_ref,
        "execution_content_binding_sha256": sha256(
            payload.get("execution_content_binding_sha256"),
            f"{field}.execution_content_binding_sha256",
        ),
        "package_use_boundary_id": text(
            payload.get("package_use_boundary_id"),
            f"{field}.package_use_boundary_id",
        ),
        "root_package_content_digest": sha256(
            payload.get("root_package_content_digest"),
            f"{field}.root_package_content_digest",
        ),
    }


def _review_input_snapshot_authority_record(
    *,
    generation_ref: str,
    review_lane: str,
    review_scope_sha256_value: str,
    members: list[dict[str, Any]],
    authority_issuer: Mapping[str, Any],
) -> dict[str, Any]:
    member_projection = [
        {
            "member_id": item["member_id"],
            "role": item["role"],
            "owner_ref": item["owner_ref"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in members
    ]
    return {
        "surface_kind": "mas_review_input_snapshot_authority",
        "schema_version": 2,
        "issuer": _normalize_review_input_snapshot_authority_issuer(
            authority_issuer
        ),
        "generation_ref": generation_ref,
        "review_lane": review_lane,
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_scope_sha256": review_scope_sha256_value,
        "members": member_projection,
    }


def _review_input_snapshot_authority_record_ref(
    authority_record: dict[str, Any],
) -> dict[str, Any]:
    authority_sha256 = fingerprint(authority_record)
    return {
        "kind": "mas_review_input_snapshot_authority",
        "ref": (
            "mas-review-input-snapshot-authority:"
            f"{authority_sha256.removeprefix('sha256:')}"
        ),
        "size_bytes": len(canonical_json_bytes(authority_record)),
        "sha256": authority_sha256,
    }


def build_review_input_snapshot_materialization_request(
    *,
    generation_manifest: dict[str, Any],
    review_lane: str,
    generation_ref: str,
    workspace_root: str,
    source_refs_by_member_id: Mapping[str, str],
    authority_issuer: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one MAS-owned review scope into the generic OPL transport request."""

    manifest = normalize_generation_manifest(generation_manifest)
    if manifest["schema_version"] != 2:
        raise RequestShapeError(
            "generation_manifest.schema_version must be integer 2 for snapshot materialization"
        )
    lane = enum_text(
        review_lane,
        "review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    scope = next(
        (item for item in manifest["review_scopes"] if item["review_lane"] == lane),
        None,
    )
    if scope is None:
        raise RequestShapeError(
            f"review_lane {lane} is not declared by generation_manifest.review_scopes"
        )

    supplied_source_refs = mapping(
        source_refs_by_member_id,
        "source_refs_by_member_id",
    )
    normalized_source_refs: dict[str, str] = {}
    for index, (member_id_value, source_ref_value) in enumerate(
        supplied_source_refs.items()
    ):
        member_id = text(
            member_id_value,
            f"source_refs_by_member_id key[{index}]",
        )
        if member_id in normalized_source_refs:
            raise RequestShapeError(
                "source_refs_by_member_id contains duplicate normalized member_id values"
            )
        normalized_source_refs[member_id] = text(
            source_ref_value,
            f"source_refs_by_member_id.{member_id}",
        )

    reviewed_members = review_scope_member_projection(scope["reviewed_members"])
    expected_member_ids = {item["member_id"] for item in reviewed_members}
    supplied_member_ids = set(normalized_source_refs)
    missing_member_ids = sorted(expected_member_ids - supplied_member_ids)
    extra_member_ids = sorted(supplied_member_ids - expected_member_ids)
    if missing_member_ids or extra_member_ids:
        mismatch_parts = []
        if missing_member_ids:
            mismatch_parts.append("missing: " + ", ".join(missing_member_ids))
        if extra_member_ids:
            mismatch_parts.append("extra: " + ", ".join(extra_member_ids))
        raise RequestShapeError(
            "source_refs_by_member_id must exactly match the MAS-owned review scope; "
            + "; ".join(mismatch_parts)
        )

    members = [
        {
            "member_id": item["member_id"],
            "source_ref": normalized_source_refs[item["member_id"]],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in reviewed_members
    ]
    normalized_generation_ref = text(generation_ref, "generation_ref")
    normalized_authority_issuer = _normalize_review_input_snapshot_authority_issuer(
        authority_issuer
    )
    authority_record = _review_input_snapshot_authority_record(
        generation_ref=normalized_generation_ref,
        review_lane=lane,
        review_scope_sha256_value=scope["review_scope_sha256"],
        members=[
            {
                "member_id": item["member_id"],
                "role": item["role"],
                "owner_ref": item["ref"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
            }
            for item in scope["reviewed_members"]
        ],
        authority_issuer=normalized_authority_issuer,
    )
    return {
        "surface_kind": "opl_reviewer_input_snapshot_materialization_request",
        "schema_version": 2,
        "review_lane": lane,
        "owner_authority_ref": _review_input_snapshot_authority_record_ref(
            authority_record
        ),
        "producer_attempt_ref": normalized_authority_issuer["stage_attempt_ref"],
        "execution_content_binding_sha256": normalized_authority_issuer[
            "execution_content_binding_sha256"
        ],
        "workspace_root": text(workspace_root, "workspace_root"),
        "members": members,
    }


def build_stage_review_input_snapshot_bundle(
    *,
    stage_id: str,
    artifacts: list[dict[str, Any]],
    generation_id: str,
    generation_ref: str,
    workspace_root: str,
    source_refs_by_member_id: Mapping[str, str],
    authority_issuer: Mapping[str, Any],
    review_lane: str | None = None,
    professional_skill_invocations: list[dict[str, Any]] | None = None,
    first_draft_quality_application: dict[str, Any] | None = None,
    clinical_analysis_identity_admission: dict[str, Any] | None = None,
    selected_build_binding: dict[str, Any] | None = None,
    reviewer_response_sync: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one stage-bound generation manifest and immutable review request."""

    normalized_stage_id = text(stage_id, "stage_id")
    manifest_scope = STAGE_MINIMUM_SCOPE.get(normalized_stage_id)
    if manifest_scope is None:
        raise RequestShapeError(f"stage_id is unsupported: {normalized_stage_id}")

    allowed_lanes = REVIEW_LANES_BY_SCOPE[manifest_scope]
    fixed_lane = STAGE_FIXED_REVIEW_LANE.get(normalized_stage_id)
    if fixed_lane is not None:
        if review_lane is not None:
            supplied_lane = enum_text(
                review_lane,
                "review_lane",
                set(REVIEW_AUTHORITY_ROLE_BY_LANE),
            )
            if supplied_lane != fixed_lane:
                raise RequestShapeError(
                    f"stage_id {normalized_stage_id} binds review_lane {fixed_lane}"
                )
        lane = fixed_lane
    else:
        if review_lane is None:
            raise RequestShapeError(
                f"stage_id {normalized_stage_id} requires an explicit controller-bound review_lane"
            )
        lane = enum_text(
            review_lane,
            "review_lane",
            set(REVIEW_AUTHORITY_ROLE_BY_LANE),
        )
    if lane not in allowed_lanes:
        raise RequestShapeError(
            f"review_lane {lane} is not allowed for stage_id {normalized_stage_id}"
        )

    generation_manifest = build_generation_manifest_v2(
        artifacts=artifacts,
        generation_id=generation_id,
        manifest_scope=manifest_scope,
        professional_skill_invocations=professional_skill_invocations,
        first_draft_quality_application=first_draft_quality_application,
        clinical_analysis_identity_admission=clinical_analysis_identity_admission,
        selected_build_binding=selected_build_binding,
        reviewer_response_sync=reviewer_response_sync,
    )
    request = build_review_input_snapshot_materialization_request(
        generation_manifest=generation_manifest,
        review_lane=lane,
        generation_ref=generation_ref,
        workspace_root=workspace_root,
        source_refs_by_member_id=source_refs_by_member_id,
        authority_issuer=authority_issuer,
    )
    return {
        "surface_kind": "mas_stage_review_input_snapshot_bundle",
        "schema_version": 1,
        "stage_id": normalized_stage_id,
        "manifest_scope": manifest_scope,
        "review_lane": lane,
        "generation_ref": text(generation_ref, "generation_ref"),
        "generation_manifest": generation_manifest,
        "review_input_snapshot_materialization_request": request,
        "required_closeout_ref_metadata": [dict(request["owner_authority_ref"])],
    }
