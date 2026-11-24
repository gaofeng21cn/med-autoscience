"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from typing import Any

from .._record_validation import (
    NonEmptyStr,
    RequestShapeError,
    Sha256Text,
    StrictRecordModel,
    canonical_json_bytes,
    enum_field,
    enum_text,
    exact_int_field,
    exact_str_field,
    fingerprint,
    integer,
    mapping,
    sequence,
    text,
    validate_record_model,
)
from .constants import (
    ALLOWED_ROLES_BY_SCOPE,
    PUBLICATION_SINGLETON_ROLES,
    REQUIRED_ROLES_BY_SCOPE,
    REVIEW_LANES_BY_SCOPE,
)
from .currentness import (
    _normalize_clinical_analysis_identity_admission,
    _normalize_reviewer_response_sync,
    _normalize_selected_build_binding,
    _validate_reviewer_response_evidence_refs,
)
from .first_draft import (
    _normalize_first_draft_quality_application,
    _validate_scholar_v2_semantic_policy_invocations,
)
from .professional_manuscript import (
    _normalize_professional_skill_invocations,
)
from .records import (
    _normalize_artifact,
    _require_unique_member_ids,
)
from .review_receipts import (
    _normalize_review_receipt,
    _normalize_review_scope,
)
from .review_scope import (
    build_review_scopes,
)


class _GenerationManifestV1Model(StrictRecordModel):
    surface_kind: exact_str_field("mas_evidence_generation_manifest")
    schema_version: exact_int_field(1)
    generation_id: NonEmptyStr
    manifest_scope: enum_field(REQUIRED_ROLES_BY_SCOPE)
    generation_manifest_sha256: Sha256Text
    artifacts: Any
    independent_review_receipts: Any


class _GenerationManifestV2Model(StrictRecordModel):
    surface_kind: exact_str_field("mas_evidence_generation_manifest")
    schema_version: exact_int_field(2)
    generation_id: NonEmptyStr
    manifest_scope: enum_field(REQUIRED_ROLES_BY_SCOPE)
    generation_manifest_sha256: Sha256Text
    artifacts: Any
    review_scopes: Any
    independent_review_receipts: Any
    professional_skill_invocations: Any = None
    first_draft_quality_application: Any = None
    clinical_analysis_identity_admission: Any = None
    selected_build_binding: Any = None
    reviewer_response_sync: Any = None


def normalize_generation_manifest(
    value: Any,
    field: str = "generation_manifest",
) -> dict[str, Any]:
    """Normalize a manifest and recompute every executable identity."""

    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")

    model_cls = (
        _GenerationManifestV2Model if schema_version == 2 else _GenerationManifestV1Model
    )
    envelope = validate_record_model(model_cls, payload, field)
    present_fields = envelope.model_fields_set
    generation_id = envelope.generation_id
    scope = envelope.manifest_scope
    artifacts = _normalize_generation_artifact_inventory(
        envelope.artifacts,
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
        assert isinstance(envelope, _GenerationManifestV2Model)
        supplied_scopes = [
            _normalize_review_scope(
                item,
                f"{field}.review_scopes[{index}]",
                artifacts=artifacts,
            )
            for index, item in enumerate(
                sequence(envelope.review_scopes, f"{field}.review_scopes")
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
        if "professional_skill_invocations" in present_fields:
            manifest_core["professional_skill_invocations"] = (
                _normalize_professional_skill_invocations(
                    envelope.professional_skill_invocations,
                    f"{field}.professional_skill_invocations",
                    artifacts=artifacts,
                )
            )
        if "first_draft_quality_application" in present_fields:
            if scope == "analysis_generation":
                raise RequestShapeError(
                    f"{field}.first_draft_quality_application is not allowed for "
                    "analysis_generation"
                )
            manifest_core["first_draft_quality_application"] = (
                _normalize_first_draft_quality_application(
                    envelope.first_draft_quality_application,
                    f"{field}.first_draft_quality_application",
                    artifacts=artifacts,
                    require_scholar_v2_semantics=(
                        "selected_build_binding" in present_fields
                    ),
                )
            )
        if "clinical_analysis_identity_admission" in present_fields:
            if scope != "analysis_generation":
                raise RequestShapeError(
                    f"{field}.clinical_analysis_identity_admission is allowed only "
                    "for analysis_generation"
                )
            manifest_core["clinical_analysis_identity_admission"] = (
                _normalize_clinical_analysis_identity_admission(
                    envelope.clinical_analysis_identity_admission,
                    f"{field}.clinical_analysis_identity_admission",
                    artifacts=artifacts,
                )
            )
        if "selected_build_binding" in present_fields:
            if scope == "analysis_generation":
                raise RequestShapeError(
                    f"{field}.selected_build_binding is not allowed for "
                    "analysis_generation"
                )
            manifest_core["selected_build_binding"] = _normalize_selected_build_binding(
                envelope.selected_build_binding,
                f"{field}.selected_build_binding",
                artifacts=artifacts,
            )
        if "reviewer_response_sync" in present_fields:
            if scope == "analysis_generation":
                raise RequestShapeError(
                    f"{field}.reviewer_response_sync is not allowed for "
                    "analysis_generation"
                )
            manifest_core["reviewer_response_sync"] = _normalize_reviewer_response_sync(
                envelope.reviewer_response_sync,
                f"{field}.reviewer_response_sync",
                artifacts=artifacts,
            )
        if "selected_build_binding" in manifest_core:
            _validate_scholar_v2_semantic_policy_invocations(
                manifest_core,
                f"{field}.first_draft_quality_application",
            )

    expected_fingerprint = fingerprint(manifest_core)
    if envelope.generation_manifest_sha256 != expected_fingerprint:
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
                envelope.independent_review_receipts,
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
    if "reviewer_response_sync" in manifest_core:
        _validate_reviewer_response_evidence_refs(
            manifest_core["reviewer_response_sync"],
            reviews,
            f"{field}.reviewer_response_sync",
        )
    return {
        **manifest_core,
        "generation_manifest_sha256": expected_fingerprint,
        "generation_manifest_size_bytes": len(canonical_json_bytes(manifest_core)),
        "independent_review_receipts": reviews,
    }


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
        for index, item in enumerate(sequence(value, field))
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
        raise RequestShapeError(f"{field} requires exactly one source_input_digest")
    for role in sorted(PUBLICATION_SINGLETON_ROLES & roles):
        if sum(item["role"] == role for item in artifacts) != 1:
            raise RequestShapeError(f"{field} requires exactly one {role}")
    artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    return artifacts


def build_generation_manifest_v2(
    *,
    artifacts: list[dict[str, Any]],
    generation_id: str,
    manifest_scope: str,
    professional_skill_invocations: list[dict[str, Any]] | None = None,
    first_draft_quality_application: dict[str, Any] | None = None,
    clinical_analysis_identity_admission: dict[str, Any] | None = None,
    selected_build_binding: dict[str, Any] | None = None,
    reviewer_response_sync: dict[str, Any] | None = None,
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
    core: dict[str, Any] = {
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
    if first_draft_quality_application is not None:
        if normalized_scope == "analysis_generation":
            raise RequestShapeError(
                "first_draft_quality_application is not allowed for analysis_generation"
            )
        core["first_draft_quality_application"] = (
            _normalize_first_draft_quality_application(
                first_draft_quality_application,
                "generation_manifest.first_draft_quality_application",
                artifacts=normalized_artifacts,
                require_scholar_v2_semantics=selected_build_binding is not None,
            )
        )
    if clinical_analysis_identity_admission is not None:
        if normalized_scope != "analysis_generation":
            raise RequestShapeError(
                "clinical_analysis_identity_admission is allowed only for "
                "analysis_generation"
            )
        core["clinical_analysis_identity_admission"] = (
            _normalize_clinical_analysis_identity_admission(
                clinical_analysis_identity_admission,
                "generation_manifest.clinical_analysis_identity_admission",
                artifacts=normalized_artifacts,
            )
        )
    if selected_build_binding is not None:
        if normalized_scope == "analysis_generation":
            raise RequestShapeError(
                "selected_build_binding is not allowed for analysis_generation"
            )
        core["selected_build_binding"] = _normalize_selected_build_binding(
            selected_build_binding,
            "generation_manifest.selected_build_binding",
            artifacts=normalized_artifacts,
        )
    if reviewer_response_sync is not None:
        if normalized_scope == "analysis_generation":
            raise RequestShapeError(
                "reviewer_response_sync is not allowed for analysis_generation"
            )
        core["reviewer_response_sync"] = _normalize_reviewer_response_sync(
            reviewer_response_sync,
            "generation_manifest.reviewer_response_sync",
            artifacts=normalized_artifacts,
        )
    manifest = {
        **core,
        "generation_manifest_sha256": fingerprint(core),
        "independent_review_receipts": [],
    }
    normalize_generation_manifest(manifest)
    return manifest
