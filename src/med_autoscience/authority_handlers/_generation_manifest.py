"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._record_validation import (
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
    typed_ref_list as _typed_ref_list,
)


ANALYSIS_GENERATION_ROLES = frozenset(
    {
        "source_input_digest",
        "data_release",
        "denominator_definitions",
        "analysis_script",
        "analysis_output",
    }
)
MANUSCRIPT_GENERATION_ROLES = ANALYSIS_GENERATION_ROLES | frozenset(
    {
        "candidate_admission_receipt",
        "canonical_manuscript",
        "claim_evidence_map",
        "citation_ledger",
        "numeric_trace",
        "reference_library",
        "table_catalog",
        "table_file",
        "figure_catalog",
        "figure_file",
        "render_environment_and_font_manifest",
    }
)
PUBLICATION_GENERATION_ROLES = MANUSCRIPT_GENERATION_ROLES | frozenset(
    {
        "docx",
        "pdf",
        "supplementary_output",
        "final_zip_allowlist",
        "final_zip_member",
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    }
)
PUBLICATION_SINGLETON_ROLES = frozenset(
    {
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    }
)
OPTIONAL_GENERATION_ROLES = frozenset({"candidate_artifact", "evidence_record"})
REQUIRED_ROLES_BY_SCOPE = {
    "analysis_generation": ANALYSIS_GENERATION_ROLES,
    "manuscript_generation": MANUSCRIPT_GENERATION_ROLES,
    "publication_generation": PUBLICATION_GENERATION_ROLES,
}
ALLOWED_ROLES_BY_SCOPE = {
    scope: roles | OPTIONAL_GENERATION_ROLES
    for scope, roles in REQUIRED_ROLES_BY_SCOPE.items()
}
REVIEW_LANES_BY_SCOPE = {
    "analysis_generation": frozenset({"statistical"}),
    "manuscript_generation": frozenset(
        {"medical", "statistical", "reference", "display"}
    ),
    "publication_generation": frozenset(
        {
            "medical",
            "statistical",
            "reference",
            "display",
            "publication",
            "exact_byte_package",
        }
    ),
}
REVIEW_AUTHORITY_ROLE_BY_LANE = {
    "medical": "mas_independent_medical_reviewer",
    "statistical": "mas_independent_statistical_reviewer",
    "reference": "mas_independent_reference_reviewer",
    "display": "mas_independent_display_reviewer",
    "publication": "mas_independent_publication_reviewer",
    "exact_byte_package": "mas_independent_exact_byte_package_reviewer",
}
REVIEW_LANE_ORDER = (
    "medical",
    "statistical",
    "reference",
    "display",
    "publication",
    "exact_byte_package",
)
REVIEW_SCOPE_POLICY_ID = "mas_review_scope_dependency_map"
REVIEW_SCOPE_POLICY_VERSION = 1
# MAS owns this map. Hosts may materialize these inventories, but they may not
# choose or narrow review members.
REVIEW_SCOPE_ROLES_BY_LANE = {
    "medical": frozenset(
        {
            "denominator_definitions",
            "analysis_output",
            "candidate_artifact",
            "evidence_record",
            "canonical_manuscript",
            "claim_evidence_map",
            "numeric_trace",
        }
    ),
    "statistical": (ANALYSIS_GENERATION_ROLES - {"source_input_digest"})
    | frozenset(
        {
            "candidate_artifact",
            "evidence_record",
            "canonical_manuscript",
            "claim_evidence_map",
            "numeric_trace",
            "table_catalog",
            "table_file",
        }
    ),
    "reference": frozenset(
        {
            "canonical_manuscript",
            "claim_evidence_map",
            "citation_ledger",
            "reference_library",
            "evidence_record",
        }
    ),
    "display": frozenset(
        {
            "table_catalog",
            "table_file",
            "figure_catalog",
            "figure_file",
            "docx",
            "pdf",
            "supplementary_output",
        }
    ),
    "publication": frozenset(
        {
            "canonical_manuscript",
            "claim_evidence_map",
            "citation_ledger",
            "reference_library",
            "table_catalog",
            "table_file",
            "figure_catalog",
            "figure_file",
            "docx",
            "pdf",
            "supplementary_output",
            "submission_status",
            "publication_evaluation",
            "next_action_envelope",
            "submission_projection_manifest",
        }
    ),
}
STAGE_MINIMUM_SCOPE = {
    "direction_and_route_selection": "analysis_generation",
    "baseline_and_evidence_setup": "analysis_generation",
    "bounded_analysis_campaign": "analysis_generation",
    "manuscript_authoring": "manuscript_generation",
    "review_and_quality_gate": "manuscript_generation",
    "finalize_and_publication_handoff": "publication_generation",
}
_SCOPE_RANK = {
    "analysis_generation": 0,
    "manuscript_generation": 1,
    "publication_generation": 2,
}
def normalize_generation_manifest(
    value: Any,
    field: str = "generation_manifest",
) -> dict[str, Any]:
    """Normalize a manifest and recompute every executable identity."""

    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    keys = {
        "surface_kind",
        "schema_version",
        "generation_id",
        "manifest_scope",
        "generation_manifest_sha256",
        "artifacts",
        "independent_review_receipts",
    }
    if schema_version == 2:
        keys.add("review_scopes")
        if "professional_skill_invocations" in payload:
            keys.add("professional_skill_invocations")
    exact_keys(payload, keys, field)
    if payload.get("surface_kind") != "mas_evidence_generation_manifest":
        raise RequestShapeError(
            f"{field}.surface_kind must be mas_evidence_generation_manifest"
        )
    generation_id = text(payload.get("generation_id"), f"{field}.generation_id")
    scope = enum_text(
        payload.get("manifest_scope"),
        f"{field}.manifest_scope",
        set(REQUIRED_ROLES_BY_SCOPE),
    )
    artifacts = _normalize_generation_artifact_inventory(
        payload.get("artifacts"),
        f"{field}.artifacts",
        manifest_scope=scope,
        schema_version=schema_version,
    )

    manifest_core: dict[str, Any] = {
        "surface_kind": "mas_evidence_generation_manifest",
        "schema_version": schema_version,
        "generation_id": generation_id,
        "manifest_scope": scope,
        "artifacts": artifacts,
    }
    review_scopes: list[dict[str, Any]] = []
    if schema_version == 2:
        supplied_scopes = [
            _normalize_review_scope(
                item,
                f"{field}.review_scopes[{index}]",
                artifacts=artifacts,
            )
            for index, item in enumerate(
                sequence(payload.get("review_scopes"), f"{field}.review_scopes")
            )
        ]
        scope_lanes = [item["review_lane"] for item in supplied_scopes]
        if len(scope_lanes) != len(set(scope_lanes)):
            raise RequestShapeError(f"{field}.review_scopes contains duplicate lanes")
        required_lanes = REVIEW_LANES_BY_SCOPE[scope]
        if set(scope_lanes) != required_lanes:
            raise RequestShapeError(
                f"{field}.review_scopes must equal required lanes: "
                + ", ".join(sorted(required_lanes))
            )
        review_scopes = sorted(supplied_scopes, key=lambda item: item["review_lane"])
        manifest_core["review_scopes"] = review_scopes
        if "professional_skill_invocations" in payload:
            manifest_core["professional_skill_invocations"] = (
                _normalize_professional_skill_invocations(
                    payload.get("professional_skill_invocations"),
                    f"{field}.professional_skill_invocations",
                    artifacts=artifacts,
                )
            )
    expected_fingerprint = fingerprint(manifest_core)
    supplied_fingerprint = sha256(
        payload.get("generation_manifest_sha256"),
        f"{field}.generation_manifest_sha256",
    )
    if supplied_fingerprint != expected_fingerprint:
        raise RequestShapeError(
            f"{field}.generation_manifest_sha256 does not match canonical members"
        )

    reviews = [
        _normalize_review_receipt(
            item,
            f"{field}.independent_review_receipts[{index}]",
            generation_id=generation_id,
            manifest_sha256=expected_fingerprint,
            artifacts=artifacts,
            manifest_version=schema_version,
            review_scopes=review_scopes,
        )
        for index, item in enumerate(
            sequence(
                payload.get("independent_review_receipts"),
                f"{field}.independent_review_receipts",
            )
        )
    ]
    lanes = [item["receipt"]["review_lane"] for item in reviews]
    if len(lanes) != len(set(lanes)):
        raise RequestShapeError(
            f"{field}.independent_review_receipts contains duplicate lanes"
        )
    reviews.sort(key=lambda item: item["receipt"]["review_lane"])
    normalized = {
        **manifest_core,
        "generation_manifest_sha256": expected_fingerprint,
        "generation_manifest_size_bytes": len(canonical_json_bytes(manifest_core)),
        "independent_review_receipts": reviews,
    }
    return normalized


def _normalize_generation_artifact_inventory(
    value: Any,
    field: str,
    *,
    manifest_scope: str,
    schema_version: int,
) -> list[dict[str, Any]]:
    artifacts = [
        _normalize_artifact(
            item,
            f"{field}[{index}]",
            allowed_roles=ALLOWED_ROLES_BY_SCOPE[manifest_scope],
            schema_version=schema_version,
        )
        for index, item in enumerate(
            sequence(value, field)
        )
    ]
    identities = [(item["role"], item["ref"]) for item in artifacts]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate role refs")
    if schema_version == 2:
        _require_unique_member_ids(artifacts, field)
    roles = {item["role"] for item in artifacts}
    missing_roles = sorted(REQUIRED_ROLES_BY_SCOPE[manifest_scope] - roles)
    if missing_roles:
        raise RequestShapeError(
            f"{field} missing required roles: " + ", ".join(missing_roles)
        )
    if sum(item["role"] == "source_input_digest" for item in artifacts) != 1:
        raise RequestShapeError(
            f"{field} requires exactly one source_input_digest"
        )
    for role in sorted(PUBLICATION_SINGLETON_ROLES & roles):
        if sum(item["role"] == role for item in artifacts) != 1:
            raise RequestShapeError(
                f"{field} requires exactly one {role}"
            )
    artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    return artifacts


def build_generation_manifest_v2(
    *,
    artifacts: list[dict[str, Any]],
    generation_id: str,
    manifest_scope: str,
    professional_skill_invocations: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Build a canonical receipt-free v2 manifest from exact artifact records."""

    normalized_scope = enum_text(
        manifest_scope,
        "generation_manifest.manifest_scope",
        set(REQUIRED_ROLES_BY_SCOPE),
    )
    normalized_artifacts = _normalize_generation_artifact_inventory(
        artifacts,
        "generation_manifest.artifacts",
        manifest_scope=normalized_scope,
        schema_version=2,
    )
    core = {
        "surface_kind": "mas_evidence_generation_manifest",
        "schema_version": 2,
        "generation_id": text(generation_id, "generation_manifest.generation_id"),
        "manifest_scope": normalized_scope,
        "artifacts": normalized_artifacts,
        "review_scopes": build_review_scopes(
            normalized_artifacts,
            normalized_scope,
        ),
    }
    if professional_skill_invocations is not None:
        core["professional_skill_invocations"] = (
            _normalize_professional_skill_invocations(
                professional_skill_invocations,
                "generation_manifest.professional_skill_invocations",
                artifacts=normalized_artifacts,
            )
        )
    manifest = {
        **core,
        "generation_manifest_sha256": fingerprint(core),
        "independent_review_receipts": [],
    }
    normalize_generation_manifest(manifest)
    return manifest


def _normalize_professional_skill_invocations(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_by_member_id = {
        item["member_id"]: item for item in artifacts if "member_id" in item
    }
    invocations = [
        _normalize_professional_skill_invocation(
            item,
            f"{field}[{index}]",
            artifact_by_member_id=artifact_by_member_id,
        )
        for index, item in enumerate(sequence(value, field))
    ]
    identities = [(item["figure_id"], item["skill_id"]) for item in invocations]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate figure/skill receipts")
    member_owner: dict[str, str] = {}
    for invocation in invocations:
        for binding in invocation["output_artifact_bindings"]:
            member_id = binding["member_id"]
            prior_figure = member_owner.setdefault(member_id, invocation["figure_id"])
            if prior_figure != invocation["figure_id"]:
                raise RequestShapeError(
                    f"{field} binds figure artifact {member_id} to multiple figures"
                )
    invocations.sort(key=lambda item: (item["figure_id"], item["skill_id"]))
    return invocations


def _normalize_professional_skill_invocation(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    skill_id = enum_text(
        payload.get("skill_id"),
        f"{field}.skill_id",
        {
            "medical-figure-design",
            "medical-figure-style",
            "medical-figure-composer",
        },
    )
    keys = {
        "surface_kind",
        "schema_version",
        "receipt_id",
        "figure_id",
        "figure_kind",
        "composition_mode",
        "skill_id",
        "package_id",
        "package_version",
        "package_source_ref",
        "package_source_sha256",
        "skill_source_ref",
        "skill_source_sha256",
        "invocation_id",
        "input_contract_ref",
        "input_sha256",
        "consumed_rule_refs",
        "output_artifact_bindings",
        "status",
        "refs_only",
        "authority",
        "publication_ready",
    }
    if skill_id == "medical-figure-design":
        keys.update({"template_usage", "figure_text_policy"})
    exact_keys(payload, keys, field)
    if payload.get("surface_kind") != "mas_professional_figure_skill_invocation_candidate":
        raise RequestShapeError(
            f"{field}.surface_kind must be "
            "mas_professional_figure_skill_invocation_candidate"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("package_id") != "mas-scholar-skills":
        raise RequestShapeError(f"{field}.package_id must be mas-scholar-skills")
    if payload.get("status") != "completed":
        raise RequestShapeError(f"{field}.status must be completed")
    if payload.get("refs_only") is not True:
        raise RequestShapeError(f"{field}.refs_only must be true")
    for key in ("authority", "publication_ready"):
        if payload.get(key) is not False:
            raise RequestShapeError(f"{field}.{key} must be false")
    consumed_rule_refs = text_list(
        payload.get("consumed_rule_refs"), f"{field}.consumed_rule_refs"
    )
    if not consumed_rule_refs:
        raise RequestShapeError(f"{field}.consumed_rule_refs must not be empty")
    output_bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}.output_artifact_bindings[{index}]",
            artifact_by_member_id=artifact_by_member_id,
        )
        for index, item in enumerate(
            sequence(
                payload.get("output_artifact_bindings"),
                f"{field}.output_artifact_bindings",
            )
        )
    ]
    if not output_bindings:
        raise RequestShapeError(
            f"{field}.output_artifact_bindings must bind at least one final figure artifact"
        )
    member_ids = [item["member_id"] for item in output_bindings]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(
            f"{field}.output_artifact_bindings contains duplicate members"
        )
    normalized = {
        "surface_kind": "mas_professional_figure_skill_invocation_candidate",
        "schema_version": 1,
        "receipt_id": text(payload.get("receipt_id"), f"{field}.receipt_id"),
        "figure_id": text(payload.get("figure_id"), f"{field}.figure_id"),
        "figure_kind": enum_text(
            payload.get("figure_kind"),
            f"{field}.figure_kind",
            {"evidence_figure", "graphical_abstract"},
        ),
        "composition_mode": enum_text(
            payload.get("composition_mode"),
            f"{field}.composition_mode",
            {"single_canvas_direct", "assembled_panels"},
        ),
        "skill_id": skill_id,
        "package_id": "mas-scholar-skills",
        "package_version": text(
            payload.get("package_version"), f"{field}.package_version"
        ),
        "package_source_ref": text(
            payload.get("package_source_ref"), f"{field}.package_source_ref"
        ),
        "package_source_sha256": sha256(
            payload.get("package_source_sha256"),
            f"{field}.package_source_sha256",
        ),
        "skill_source_ref": text(
            payload.get("skill_source_ref"), f"{field}.skill_source_ref"
        ),
        "skill_source_sha256": sha256(
            payload.get("skill_source_sha256"), f"{field}.skill_source_sha256"
        ),
        "invocation_id": text(
            payload.get("invocation_id"), f"{field}.invocation_id"
        ),
        "input_contract_ref": text(
            payload.get("input_contract_ref"), f"{field}.input_contract_ref"
        ),
        "input_sha256": sha256(
            payload.get("input_sha256"), f"{field}.input_sha256"
        ),
        "consumed_rule_refs": consumed_rule_refs,
        "output_artifact_bindings": sorted(
            output_bindings, key=lambda item: item["member_id"]
        ),
        "status": "completed",
        "refs_only": True,
        "authority": False,
        "publication_ready": False,
    }
    if skill_id == "medical-figure-design":
        normalized["template_usage"] = _normalize_figure_template_usage(
            payload.get("template_usage"), f"{field}.template_usage"
        )
        normalized["figure_text_policy"] = _normalize_figure_text_policy(
            payload.get("figure_text_policy"),
            f"{field}.figure_text_policy",
            figure_kind=normalized["figure_kind"],
        )
    return normalized


def _normalize_professional_skill_artifact_binding(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"member_id", "role", "ref", "size_bytes", "sha256"}, field)
    member_id = text(payload.get("member_id"), f"{field}.member_id")
    normalized = {
        "member_id": member_id,
        "role": enum_text(payload.get("role"), f"{field}.role", {"figure_file"}),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    expected = artifact_by_member_id.get(member_id)
    if expected is None or expected.get("role") != "figure_file":
        raise RequestShapeError(
            f"{field} must name a generation figure_file artifact"
        )
    return normalized


def _normalize_figure_template_usage(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    if payload.get("used") is False:
        exact_keys(payload, {"used", "decision_reason"}, field)
        return {
            "used": False,
            "decision_reason": text(
                payload.get("decision_reason"), f"{field}.decision_reason"
            ),
        }
    if payload.get("used") is not True:
        raise RequestShapeError(f"{field}.used must be boolean")
    exact_keys(
        payload,
        {
            "used",
            "template_id",
            "template_ref",
            "adaptation_mode",
            "semantic_match_ref",
            "transform_delta_ref",
        },
        field,
    )
    return {
        "used": True,
        "template_id": text(payload.get("template_id"), f"{field}.template_id"),
        "template_ref": text(payload.get("template_ref"), f"{field}.template_ref"),
        "adaptation_mode": enum_text(
            payload.get("adaptation_mode"),
            f"{field}.adaptation_mode",
            {
                "declared_template",
                "schema_adapted_template",
                "reference_guided_new_render",
            },
        ),
        "semantic_match_ref": text(
            payload.get("semantic_match_ref"), f"{field}.semantic_match_ref"
        ),
        "transform_delta_ref": text(
            payload.get("transform_delta_ref"), f"{field}.transform_delta_ref"
        ),
    }


def _normalize_figure_text_policy(
    value: Any,
    field: str,
    *,
    figure_kind: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "embedded_title",
            "embedded_subtitle",
            "embedded_prose_footer",
            "allowed_text_roles",
        },
        field,
    )
    for key in ("embedded_title", "embedded_subtitle", "embedded_prose_footer"):
        if not isinstance(payload.get(key), bool):
            raise RequestShapeError(f"{field}.{key} must be boolean")
    allowed_text_roles = text_list(
        payload.get("allowed_text_roles"), f"{field}.allowed_text_roles"
    )
    evidence_roles = {
        "panel_label",
        "axis_label",
        "tick_label",
        "legend",
        "necessary_statistical_annotation",
    }
    allowed_roles = evidence_roles | {"graphical_abstract_copy"}
    if not set(allowed_text_roles).issubset(allowed_roles):
        raise RequestShapeError(f"{field}.allowed_text_roles contains unsupported roles")
    if figure_kind == "evidence_figure":
        for key in ("embedded_title", "embedded_subtitle", "embedded_prose_footer"):
            if payload.get(key) is not False:
                raise RequestShapeError(
                    f"{field}.{key} must be false for evidence figures"
                )
        if set(allowed_text_roles) != evidence_roles:
            raise RequestShapeError(
                f"{field}.allowed_text_roles must equal the evidence-figure text policy"
            )
    return {
        "embedded_title": payload["embedded_title"],
        "embedded_subtitle": payload["embedded_subtitle"],
        "embedded_prose_footer": payload["embedded_prose_footer"],
        "allowed_text_roles": allowed_text_roles,
    }


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
    return {
        name: artifact[name]
        for name in ("role", "ref", "size_bytes", "sha256")
    }


def review_scope_inventory(
    lane: str,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the canonical MAS-owned member inventory for one review lane."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    if lane == "exact_byte_package":
        members = list(artifacts)
    else:
        roles = REVIEW_SCOPE_ROLES_BY_LANE[lane]
        members = [item for item in artifacts if item["role"] in roles]
    members = [dict(item) for item in members]
    members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if not members:
        raise RequestShapeError(f"review scope {lane} has no canonical members")
    return members


def review_scope_sha256(lane: str, members: list[dict[str, Any]]) -> str:
    """Hash the owner identity/content projection appropriate to one review lane."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    _require_unique_member_ids(members, f"review scope {lane} members")
    if lane == "exact_byte_package":
        digest_members = [dict(item) for item in members]
        digest_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    else:
        digest_members = [
            {
                "member_id": item["member_id"],
                "role": item["role"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
            }
            for item in members
        ]
        digest_members.sort(
            key=lambda item: (
                item["member_id"],
                item["role"],
                item["sha256"],
                item["size_bytes"],
            )
        )

    return fingerprint(
        {
            "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
            "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
            "review_lane": lane,
            "reviewed_members": digest_members,
        }
    )


def review_scope_member_projection(
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project review members onto the path-independent snapshot identity."""

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


def _review_input_snapshot_authority_record(
    *,
    generation_ref: str,
    review_lane: str,
    review_scope_sha256_value: str,
    members: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_review_input_snapshot_authority",
        "schema_version": 1,
        "generation_ref": generation_ref,
        "review_lane": review_lane,
        "review_scope_sha256": review_scope_sha256_value,
        "members": [
            {
                "member_id": item["member_id"],
                "role": item["role"],
                "owner_ref": item["owner_ref"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
            }
            for item in members
        ],
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
) -> dict[str, Any]:
    """Project one canonical v2 review scope into the OPL transport request."""

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
        (
            item
            for item in manifest["review_scopes"]
            if item["review_lane"] == lane
        ),
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
    owner_refs_by_member_id = {
        item["member_id"]: item["ref"] for item in scope["reviewed_members"]
    }
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
            "role": item["role"],
            "owner_ref": owner_refs_by_member_id[item["member_id"]],
            "source_ref": normalized_source_refs[item["member_id"]],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in reviewed_members
    ]
    normalized_generation_ref = text(generation_ref, "generation_ref")
    authority_record = _review_input_snapshot_authority_record(
        generation_ref=normalized_generation_ref,
        review_lane=lane,
        review_scope_sha256_value=scope["review_scope_sha256"],
        members=members,
    )
    return {
        "surface_kind": "opl_reviewer_input_snapshot_materialization_request",
        "schema_version": 1,
        "generation_ref": normalized_generation_ref,
        "review_lane": lane,
        "review_scope_sha256": scope["review_scope_sha256"],
        "workspace_root": text(workspace_root, "workspace_root"),
        "members": members,
        "mas_authority_record_ref": _review_input_snapshot_authority_record_ref(
            authority_record
        ),
        "mas_authority_record": authority_record,
    }


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
            }
        )
    return scopes


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
    if sha256(payload.get("review_scope_sha256"), f"{field}.review_scope_sha256") != expected_sha256:
        raise RequestShapeError(
            f"{field}.review_scope_sha256 does not match canonical lane members"
        )
    return {
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_lane": lane,
        "review_scope_sha256": expected_sha256,
        "reviewed_members": expected_members,
    }


def _normalize_artifact(
    value: Any,
    field: str,
    *,
    allowed_roles: frozenset[str],
    schema_version: int = 1,
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {"role", "ref", "size_bytes", "sha256"}
    if schema_version == 2:
        keys.add("member_id")
    exact_keys(payload, keys, field)
    normalized = {
        "role": enum_text(payload.get("role"), f"{field}.role", set(allowed_roles)),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    if schema_version == 2:
        normalized["member_id"] = text(
            payload.get("member_id"), f"{field}.member_id"
        )
    return normalized


def _require_unique_member_ids(
    members: list[dict[str, Any]],
    field: str,
) -> None:
    member_ids = [
        text(item.get("member_id"), f"{field}[{index}].member_id")
        for index, item in enumerate(members)
    ]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(f"{field} contains duplicate member_id values")


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
        "accepted_candidate_receipt_refs",
        "defect_refs",
        "quality_debt_codes",
    }
    if "review_input_snapshot_binding" in payload:
        receipt_keys.add("review_input_snapshot_binding")
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
    allowed_receipt_roles = (
        frozenset().union(*ALLOWED_ROLES_BY_SCOPE.values())
        if lane == "exact_byte_package"
        else REVIEW_SCOPE_ROLES_BY_LANE[lane]
    )
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
    _require_unique_member_ids(
        reviewed_members, f"{receipt_field}.reviewed_members"
    )
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
    snapshot_binding = None
    if "review_input_snapshot_binding" in payload:
        snapshot_binding = _normalize_review_input_snapshot_binding(
            payload.get("review_input_snapshot_binding"),
            f"{receipt_field}.review_input_snapshot_binding",
        )
        if snapshot_binding["review_lane"] != lane:
            raise RequestShapeError(
                f"{receipt_field}.review_input_snapshot_binding.review_lane "
                "must match the receipt review lane"
            )
        if snapshot_binding["review_scope_sha256"] != supplied_scope_sha256:
            raise RequestShapeError(
                f"{receipt_field}.review_input_snapshot_binding.review_scope_sha256 "
                "must match the receipt review scope"
            )
        if snapshot_binding["members"] != review_scope_member_projection(
            reviewed_members
        ):
            raise RequestShapeError(
                f"{receipt_field}.review_input_snapshot_binding.members must equal "
                "the complete reviewed member inventory"
            )
        if "mas_authority_record_ref" in snapshot_binding:
            owner_refs_by_member_id = {
                item["member_id"]: item["ref"] for item in reviewed_members
            }
            authority_record = _review_input_snapshot_authority_record(
                generation_ref=snapshot_binding["generation_ref"],
                review_lane=lane,
                review_scope_sha256_value=supplied_scope_sha256,
                members=[
                    {
                        **item,
                        "owner_ref": owner_refs_by_member_id[item["member_id"]],
                    }
                    for item in snapshot_binding["members"]
                ],
            )
            if snapshot_binding[
                "mas_authority_record_ref"
            ] != _review_input_snapshot_authority_record_ref(authority_record):
                raise RequestShapeError(
                    f"{receipt_field}.review_input_snapshot_binding."
                    "mas_authority_record_ref must bind the complete MAS-owned scope"
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
    if snapshot_binding is not None:
        core["review_input_snapshot_binding"] = snapshot_binding
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
    binding_keys = {
        "surface_kind",
        "schema_version",
        "snapshot_manifest_ref",
        "review_lane",
        "review_scope_sha256",
        "members",
    }
    owner_keys = {"materialization_owner", "authority_boundary"}
    identity_keys = {"generation_ref", "mas_authority_record_ref"}
    if owner_keys & set(payload):
        binding_keys.update(owner_keys)
    if identity_keys & set(payload):
        binding_keys.update(identity_keys)
    exact_keys(
        payload,
        binding_keys,
        field,
    )
    if payload.get("surface_kind") != "mas_review_input_snapshot_binding":
        raise RequestShapeError(
            f"{field}.surface_kind must be mas_review_input_snapshot_binding"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    lane = enum_text(
        payload.get("review_lane"),
        f"{field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    allowed_roles = frozenset().union(*ALLOWED_ROLES_BY_SCOPE.values())
    members = []
    for index, item in enumerate(
        sequence(payload.get("members"), f"{field}.members")
    ):
        member_field = f"{field}.members[{index}]"
        member = mapping(item, member_field)
        exact_keys(
            member,
            {"member_id", "role", "sha256", "size_bytes"},
            member_field,
        )
        members.append(
            {
                "member_id": text(member.get("member_id"), f"{member_field}.member_id"),
                "role": enum_text(
                    member.get("role"), f"{member_field}.role", set(allowed_roles)
                ),
                "sha256": sha256(member.get("sha256"), f"{member_field}.sha256"),
                "size_bytes": integer(
                    member.get("size_bytes"), f"{member_field}.size_bytes"
                ),
            }
        )
    if not members:
        raise RequestShapeError(f"{field}.members must not be empty")
    member_ids = [item["member_id"] for item in members]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(f"{field}.members contains duplicate member_id values")
    members.sort(
        key=lambda item: (
            item["role"],
            item["member_id"],
            item["sha256"],
            item["size_bytes"],
        )
    )
    materialization_owner = None
    authority_boundary = None
    has_owner = "materialization_owner" in payload
    has_boundary = "authority_boundary" in payload
    if has_owner != has_boundary:
        raise RequestShapeError(
            f"{field}.materialization_owner and authority_boundary must appear together"
        )
    if has_owner:
        materialization_owner = text(
            payload.get("materialization_owner"), f"{field}.materialization_owner"
        )
        if materialization_owner != "one-person-lab":
            raise RequestShapeError(
                f"{field}.materialization_owner must be one-person-lab"
            )
        authority_field = f"{field}.authority_boundary"
        supplied_authority = mapping(payload.get("authority_boundary"), authority_field)
        expected_authority = {
            "storage_role": "immutable_reviewer_input_transport",
            "mas_selects_review_lane_scope_and_members": True,
            "framework_can_select_or_narrow_members": False,
            "framework_can_interpret_member_roles": False,
            "framework_can_write_domain_truth": False,
            "framework_can_sign_reviewer_receipt": False,
            "framework_can_sign_owner_receipt": False,
            "framework_can_create_typed_blocker": False,
            "framework_can_claim_quality_readiness": False,
            "framework_can_claim_publication_readiness": False,
            "framework_can_claim_artifact_authority": False,
        }
        exact_keys(supplied_authority, set(expected_authority), authority_field)
        if supplied_authority != expected_authority:
            raise RequestShapeError(
                f"{authority_field} must preserve the immutable transport-only boundary"
            )
        authority_boundary = dict(expected_authority)
    generation_ref = None
    mas_authority_record_ref = None
    has_generation_ref = "generation_ref" in payload
    has_authority_record_ref = "mas_authority_record_ref" in payload
    if has_generation_ref != has_authority_record_ref:
        raise RequestShapeError(
            f"{field}.generation_ref and mas_authority_record_ref must appear together"
        )
    if has_generation_ref:
        generation_ref = text(payload.get("generation_ref"), f"{field}.generation_ref")
        mas_authority_record_ref = _exact_ref(
            payload.get("mas_authority_record_ref"),
            f"{field}.mas_authority_record_ref",
            "mas_review_input_snapshot_authority",
        )
        expected_authority_ref = (
            "mas-review-input-snapshot-authority:"
            f"{mas_authority_record_ref['sha256'].removeprefix('sha256:')}"
        )
        if (
            mas_authority_record_ref["ref"] != expected_authority_ref
            or mas_authority_record_ref["size_bytes"] < 1
        ):
            raise RequestShapeError(
                f"{field}.mas_authority_record_ref must bind canonical MAS authority bytes"
            )
    normalized = {
        "surface_kind": "mas_review_input_snapshot_binding",
        "schema_version": 1,
        "snapshot_manifest_ref": _exact_ref(
            payload.get("snapshot_manifest_ref"),
            f"{field}.snapshot_manifest_ref",
            "opl_reviewer_input_snapshot_manifest",
        ),
        "review_lane": lane,
        "review_scope_sha256": sha256(
            payload.get("review_scope_sha256"), f"{field}.review_scope_sha256"
        ),
        "members": members,
    }
    if materialization_owner is not None:
        normalized["materialization_owner"] = materialization_owner
        normalized["authority_boundary"] = authority_boundary
    if generation_ref is not None:
        normalized["generation_ref"] = generation_ref
        normalized["mas_authority_record_ref"] = mas_authority_record_ref
    return normalized


__all__ = [
    "ALLOWED_ROLES_BY_SCOPE",
    "REQUIRED_ROLES_BY_SCOPE",
    "REVIEW_AUTHORITY_ROLE_BY_LANE",
    "REVIEW_LANE_ORDER",
    "REVIEW_LANES_BY_SCOPE",
    "REVIEW_SCOPE_ROLES_BY_LANE",
    "REVIEW_SCOPE_POLICY_ID",
    "REVIEW_SCOPE_POLICY_VERSION",
    "STAGE_MINIMUM_SCOPE",
    "build_generation_manifest_v2",
    "build_review_input_snapshot_materialization_request",
    "build_review_scopes",
    "normalize_generation_manifest",
    "require_stage_scope",
    "review_scope_inventory",
    "review_scope_member_projection",
    "review_scope_sha256",
    "source_input_digest",
]
