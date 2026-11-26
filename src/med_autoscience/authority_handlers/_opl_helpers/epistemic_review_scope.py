"""Generic `opl_epistemic_review_scope` DAG topology and closure builders."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from .exact_refs import fingerprint_v1


EPISTEMIC_REVIEW_SCOPE_SURFACE = "opl_epistemic_review_scope"
EPISTEMIC_REVIEW_SCOPE_VERSION = "opl-epistemic-review-scope.v1"


class EpistemicReviewScopeError(ValueError):
    """Raised when an epistemic review scope declaration has invalid members or roles."""


def _require_unique_member_ids(
    members: Sequence[Mapping[str, Any]],
    label: str,
) -> None:
    seen: set[str] = set()
    for item in members:
        member_id = item.get("member_id")
        if not isinstance(member_id, str) or not member_id.strip():
            raise EpistemicReviewScopeError(f"{label} contains an invalid member_id")
        if member_id in seen:
            raise EpistemicReviewScopeError(f"{label} contains duplicate member_id values")
        seen.add(member_id)


def build_epistemic_review_scope(
    *,
    scope_id: str,
    scope_kind: str,
    members: Sequence[Mapping[str, Any]],
    role_map: Mapping[str, tuple[str, str]],
    edge_rules: Sequence[tuple[Iterable[str], Iterable[str], str]],
    reviewed_roles: Iterable[str],
    evidence_profile: str,
    trust_model: str,
    authority_boundary: Mapping[str, Any],
    version: str = EPISTEMIC_REVIEW_SCOPE_VERSION,
    label: str = "epistemic review scope",
) -> dict[str, Any]:
    """Build a deterministic `opl_epistemic_review_scope` dependency DAG."""

    _require_unique_member_ids(members, f"{label} members")
    if any(item.get("role") not in role_map for item in members):
        raise EpistemicReviewScopeError(f"{label} contains undeclared artifact roles")

    nodes = [
        {
            "node_ref": item["member_id"],
            "node_kind": role_map[item["role"]][0],
            "role": role_map[item["role"]][1],
            "locator": {"ref": item["ref"], "sha256": item["sha256"]},
        }
        for item in members
    ]
    nodes.sort(key=lambda entry: entry["node_ref"])

    members_by_role: dict[str, list[Mapping[str, Any]]] = {}
    for item in members:
        members_by_role.setdefault(str(item["role"]), []).append(item)

    edges: list[dict[str, str]] = []
    for source_roles, dependent_roles, relation in edge_rules:
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
        key=lambda entry: (
            entry["source_ref"],
            entry["dependent_ref"],
            entry["relation"],
        )
    )

    reviewed_role_set = set(reviewed_roles)
    reviewed_node_refs = sorted(
        item["member_id"] for item in members if item.get("role") in reviewed_role_set
    )
    if not reviewed_node_refs:
        raise EpistemicReviewScopeError(f"{label} has no reviewed domain nodes")

    return {
        "surface_kind": EPISTEMIC_REVIEW_SCOPE_SURFACE,
        "version": version,
        "scope_id": scope_id,
        "scope_kind": scope_kind,
        "evidence_profile": evidence_profile,
        "trust_model": trust_model,
        "reviewed_node_refs": reviewed_node_refs,
        "nodes": nodes,
        "dependency_edges": edges,
        "authority_boundary": dict(authority_boundary),
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
    """Return the reverse BFS closure of all nodes depended on by reviewed nodes."""

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


def epistemic_review_scope_sha256(scope: Mapping[str, Any]) -> str:
    """Hash dependency topology as a stable locator without artifact content bytes."""

    return fingerprint_v1(epistemic_review_scope_identity(scope))


def project_review_scope_members(
    members: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Project reviewed members onto deterministic identity tuples."""

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


__all__ = [
    "EPISTEMIC_REVIEW_SCOPE_SURFACE",
    "EPISTEMIC_REVIEW_SCOPE_VERSION",
    "EpistemicReviewScopeError",
    "build_epistemic_review_scope",
    "epistemic_review_dependency_refs",
    "epistemic_review_scope_identity",
    "epistemic_review_scope_sha256",
    "project_review_scope_members",
]
