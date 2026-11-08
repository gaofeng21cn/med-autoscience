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
    EPISTEMIC_AUTHORITY_BOUNDARY,
    EPISTEMIC_EDGE_RULES_BY_LANE,
    EPISTEMIC_EVIDENCE_PROFILE,
    EPISTEMIC_NODE_ROLE_BY_LANE,
    EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE,
    EPISTEMIC_REVIEW_SCOPE_VERSION,
    EPISTEMIC_SCOPE_KIND_BY_LANE,
    EPISTEMIC_TRUST_MODEL,
    REVIEW_AUTHORITY_ROLE_BY_LANE,
    REVIEW_LANES_BY_SCOPE,
    REVIEW_SCOPE_POLICY_ID,
    REVIEW_SCOPE_POLICY_VERSION,
    REVIEW_SCOPE_ROLES_BY_LANE,
    STAGE_MINIMUM_SCOPE,
    _SCOPE_RANK,
)
from .records import (
    _require_unique_member_ids,
)

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
    _require_unique_member_ids(members, f"epistemic review scope {lane} members")
    role_map = EPISTEMIC_NODE_ROLE_BY_LANE[lane]
    if any(item["role"] not in role_map for item in members):
        raise RequestShapeError(
            f"epistemic review scope {lane} contains undeclared artifact roles"
        )
    nodes = [
        {
            "node_ref": item["member_id"],
            "node_kind": role_map[item["role"]][0],
            "role": role_map[item["role"]][1],
            "locator": {"ref": item["ref"], "sha256": item["sha256"]},
        }
        for item in members
    ]
    nodes.sort(key=lambda item: item["node_ref"])
    members_by_role: dict[str, list[dict[str, Any]]] = {}
    for item in members:
        members_by_role.setdefault(item["role"], []).append(item)
    edges: list[dict[str, str]] = []
    for source_roles, dependent_roles, relation in EPISTEMIC_EDGE_RULES_BY_LANE[lane]:
        sources = [
            item
            for role in sorted(source_roles)
            for item in members_by_role.get(role, [])
        ]
        dependents = [
            item
            for role in sorted(dependent_roles)
            for item in members_by_role.get(role, [])
        ]
        edges.extend(
            {
                "source_ref": source["member_id"],
                "dependent_ref": dependent["member_id"],
                "relation": relation,
            }
            for source in sources
            for dependent in dependents
            if source["member_id"] != dependent["member_id"]
        )
    edges.sort(
        key=lambda item: (
            item["source_ref"],
            item["dependent_ref"],
            item["relation"],
        )
    )
    reviewed_roles = EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE[lane]
    reviewed_node_refs = sorted(
        item["member_id"] for item in members if item["role"] in reviewed_roles
    )
    if not reviewed_node_refs:
        raise RequestShapeError(
            f"epistemic review scope {lane} has no reviewed domain nodes"
        )
    return {
        "surface_kind": "opl_epistemic_review_scope",
        "version": EPISTEMIC_REVIEW_SCOPE_VERSION,
        "scope_id": f"mas:{lane}",
        "scope_kind": EPISTEMIC_SCOPE_KIND_BY_LANE[lane],
        "evidence_profile": EPISTEMIC_EVIDENCE_PROFILE,
        "trust_model": EPISTEMIC_TRUST_MODEL,
        "reviewed_node_refs": reviewed_node_refs,
        "nodes": nodes,
        "dependency_edges": edges,
        "authority_boundary": dict(EPISTEMIC_AUTHORITY_BOUNDARY),
    }


def epistemic_review_scope_identity(scope: Mapping[str, Any]) -> dict[str, Any]:
    """Project scope topology without promoting locator hashes to content truth."""

    return {
        "surface_kind": scope["surface_kind"],
        "version": scope["version"],
        "scope_id": scope["scope_id"],
        "scope_kind": scope["scope_kind"],
        "evidence_profile": scope["evidence_profile"],
        "trust_model": scope["trust_model"],
        "reviewed_node_refs": list(scope["reviewed_node_refs"]),
        "nodes": [
            {
                "node_ref": item["node_ref"],
                "node_kind": item["node_kind"],
                "role": item["role"],
            }
            for item in scope["nodes"]
        ],
        "dependency_edges": [dict(item) for item in scope["dependency_edges"]],
        "authority_boundary": dict(scope["authority_boundary"]),
    }


def epistemic_review_dependency_refs(scope: Mapping[str, Any]) -> list[str]:
    """Return the declared dependency closure for Framework-evaluation binding."""

    sources_by_dependent: dict[str, list[str]] = {}
    for edge in scope["dependency_edges"]:
        sources_by_dependent.setdefault(edge["dependent_ref"], []).append(
            edge["source_ref"]
        )
    closure = set(scope["reviewed_node_refs"])
    pending = list(scope["reviewed_node_refs"])
    while pending:
        dependent = pending.pop()
        for source in sources_by_dependent.get(dependent, []):
            if source not in closure:
                closure.add(source)
                pending.append(source)
    return sorted(closure)


def review_scope_sha256(lane: str, members: list[dict[str, Any]]) -> str:
    """Hash dependency topology as a locator; artifact bytes are not authority."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    scope = build_epistemic_review_scope(lane, members)
    return fingerprint(epistemic_review_scope_identity(scope))


def review_scope_member_projection(
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project MAS review members onto the domain currentness identity."""

    projected = [
        {
            "member_id": item["member_id"],
            "role": item["role"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in members
    ]
    projected.sort(
        key=lambda item: (
            item["role"],
            item["member_id"],
            item["sha256"],
            item["size_bytes"],
        )
    )
    return projected


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
