"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._opl_helpers.epistemic_review_scope import (
    EpistemicReviewScopeError,
)
from .._opl_helpers.epistemic_review_scope import (
    build_epistemic_review_scope as _build_epistemic_review_scope,
)
from .._opl_helpers.epistemic_review_scope import (
    epistemic_review_dependency_refs as _epistemic_review_dependency_refs,
)
from .._opl_helpers.epistemic_review_scope import (
    epistemic_review_scope_identity as _epistemic_review_scope_identity,
)
from .._opl_helpers.epistemic_review_scope import (
    epistemic_review_scope_sha256 as _epistemic_review_scope_sha256,
)
from .._opl_helpers.epistemic_review_scope import (
    project_review_scope_members as _project_review_scope_members,
)

from .._record_validation import RequestShapeError
from .constants import (
    _SCOPE_RANK,
    EPISTEMIC_AUTHORITY_BOUNDARY,
    EPISTEMIC_EDGE_RULES_BY_LANE,
    EPISTEMIC_EVIDENCE_PROFILE,
    EPISTEMIC_NODE_ROLE_BY_LANE,
    EPISTEMIC_REVIEW_SCOPE_VERSION,
    EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE,
    EPISTEMIC_SCOPE_KIND_BY_LANE,
    EPISTEMIC_TRUST_MODEL,
    REVIEW_AUTHORITY_ROLE_BY_LANE,
    REVIEW_LANES_BY_SCOPE,
    REVIEW_SCOPE_POLICY_ID,
    REVIEW_SCOPE_POLICY_VERSION,
    REVIEW_SCOPE_ROLES_BY_LANE,
    STAGE_MINIMUM_SCOPE,
)
from .records import _require_unique_member_ids


def require_stage_scope(stage_id: str, manifest_scope: str) -> None:
    minimum = STAGE_MINIMUM_SCOPE.get(stage_id)
    if minimum is None:
        raise RequestShapeError(f"mission.stage_id is unsupported: {stage_id}")
    if _SCOPE_RANK[manifest_scope] < _SCOPE_RANK[minimum]:
        raise RequestShapeError(
            f"mission.stage_id {stage_id} requires at least {minimum}"
        )


def source_input_digest(manifest: dict[str, Any]) -> dict[str, Any]:
    artifact = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["role"] == "source_input_digest"
    )
    # Candidate admission's established exact-ref contract predates v2 member_id.
    return {name: artifact[name] for name in ("role", "ref", "size_bytes", "sha256")}


def review_scope_inventory(
    lane: str,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the canonical MAS-owned member inventory for one review lane."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    roles = REVIEW_SCOPE_ROLES_BY_LANE[lane]
    members = [item for item in artifacts if item["role"] in roles]
    members = [dict(item) for item in members]
    members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if not members:
        raise RequestShapeError(f"review scope {lane} has no canonical members")
    return members


def build_epistemic_review_scope(
    lane: str,
    members: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the MAS-owned dependency declaration consumed by OPL currentness."""

    if lane not in EPISTEMIC_SCOPE_KIND_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    try:
        return _build_epistemic_review_scope(
            scope_id=f"mas:{lane}",
            scope_kind=EPISTEMIC_SCOPE_KIND_BY_LANE[lane],
            members=members,
            role_map=EPISTEMIC_NODE_ROLE_BY_LANE[lane],
            edge_rules=EPISTEMIC_EDGE_RULES_BY_LANE[lane],
            reviewed_roles=EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE[lane],
            evidence_profile=EPISTEMIC_EVIDENCE_PROFILE,
            trust_model=EPISTEMIC_TRUST_MODEL,
            authority_boundary=EPISTEMIC_AUTHORITY_BOUNDARY,
            version=EPISTEMIC_REVIEW_SCOPE_VERSION,
            label=f"epistemic review scope {lane}",
        )
    except EpistemicReviewScopeError as error:
        raise RequestShapeError(str(error)) from error


def epistemic_review_scope_identity(scope: Mapping[str, Any]) -> dict[str, Any]:
    """Project scope topology without promoting locator hashes to content truth."""

    return _epistemic_review_scope_identity(scope)


def epistemic_review_dependency_refs(scope: Mapping[str, Any]) -> list[str]:
    """Return the declared dependency closure for Framework-evaluation binding."""

    return _epistemic_review_dependency_refs(scope)


def review_scope_sha256(lane: str, members: list[dict[str, Any]]) -> str:
    """Hash dependency topology as a locator; artifact bytes are not authority."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    scope = build_epistemic_review_scope(lane, members)
    return _epistemic_review_scope_sha256(scope)


def review_scope_member_projection(
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project MAS review members onto the domain currentness identity."""

    return _project_review_scope_members(members)


def build_review_scopes(
    artifacts: list[dict[str, Any]],
    manifest_scope: str,
) -> list[dict[str, Any]]:
    """Build every required deterministic lane scope for one manifest scope."""

    if manifest_scope not in REVIEW_LANES_BY_SCOPE:
        raise RequestShapeError(f"unsupported manifest scope: {manifest_scope}")
    _require_unique_member_ids(artifacts, "artifacts")
    scopes = []
    for lane in sorted(REVIEW_LANES_BY_SCOPE[manifest_scope]):
        members = review_scope_inventory(lane, artifacts)
        scopes.append(
            {
                "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
                "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
                "review_lane": lane,
                "review_scope_sha256": review_scope_sha256(lane, members),
                "reviewed_members": members,
                "epistemic_scope": build_epistemic_review_scope(lane, members),
            }
        )
    return scopes
