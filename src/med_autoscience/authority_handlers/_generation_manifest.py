"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

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
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "generation_id",
            "manifest_scope",
            "generation_manifest_sha256",
            "artifacts",
            "independent_review_receipts",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_evidence_generation_manifest":
        raise RequestShapeError(
            f"{field}.surface_kind must be mas_evidence_generation_manifest"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")

    generation_id = text(payload.get("generation_id"), f"{field}.generation_id")
    scope = enum_text(
        payload.get("manifest_scope"),
        f"{field}.manifest_scope",
        set(REQUIRED_ROLES_BY_SCOPE),
    )
    artifacts = [
        _normalize_artifact(
            item,
            f"{field}.artifacts[{index}]",
            allowed_roles=ALLOWED_ROLES_BY_SCOPE[scope],
        )
        for index, item in enumerate(
            sequence(payload.get("artifacts"), f"{field}.artifacts")
        )
    ]
    identities = [(item["role"], item["ref"]) for item in artifacts]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field}.artifacts contains duplicate role refs")
    roles = {item["role"] for item in artifacts}
    missing_roles = sorted(REQUIRED_ROLES_BY_SCOPE[scope] - roles)
    if missing_roles:
        raise RequestShapeError(
            f"{field}.artifacts missing required roles: " + ", ".join(missing_roles)
        )
    if sum(item["role"] == "source_input_digest" for item in artifacts) != 1:
        raise RequestShapeError(
            f"{field}.artifacts requires exactly one source_input_digest"
        )
    for role in sorted(PUBLICATION_SINGLETON_ROLES & roles):
        if sum(item["role"] == role for item in artifacts) != 1:
            raise RequestShapeError(
                f"{field}.artifacts requires exactly one {role}"
            )
    artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))

    manifest_core = {
        "surface_kind": "mas_evidence_generation_manifest",
        "schema_version": 1,
        "generation_id": generation_id,
        "manifest_scope": scope,
        "artifacts": artifacts,
    }
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
    return {
        **manifest_core,
        "generation_manifest_sha256": expected_fingerprint,
        "generation_manifest_size_bytes": len(canonical_json_bytes(manifest_core)),
        "independent_review_receipts": reviews,
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
    return next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["role"] == "source_input_digest"
    )


def _normalize_artifact(
    value: Any,
    field: str,
    *,
    allowed_roles: frozenset[str],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"role", "ref", "size_bytes", "sha256"}, field)
    return {
        "role": enum_text(payload.get("role"), f"{field}.role", set(allowed_roles)),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }


def _normalize_review_receipt(
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


__all__ = [
    "ALLOWED_ROLES_BY_SCOPE",
    "REQUIRED_ROLES_BY_SCOPE",
    "REVIEW_AUTHORITY_ROLE_BY_LANE",
    "REVIEW_LANES_BY_SCOPE",
    "STAGE_MINIMUM_SCOPE",
    "normalize_generation_manifest",
    "require_stage_scope",
    "source_input_digest",
]
