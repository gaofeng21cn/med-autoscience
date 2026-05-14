from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.mds_capability_parity import (
    ALLOWED_CAPABILITY_CLASSIFICATIONS,
    build_mds_remaining_surface_inventory,
    validate_mds_remaining_surface_inventory,
)


SCHEMA_VERSION = 1

REQUIRED_SOURCE_PROVENANCE_FIELDS: tuple[str, ...] = (
    "upstream_repo",
    "upstream_ref",
    "snapshot_sha256",
    "license_refs",
    "capability_classification",
)
FORBIDDEN_SOURCE_PROVENANCE_PLACEHOLDERS: tuple[str, ...] = (
    "placeholder",
    "required_per_snapshot",
    "snapshot-ref-recorded",
    "upstream license file",
    "third-party notice inventory",
)
FORBIDDEN_MDS_ORACLE_AUTHORITY_SURFACES: tuple[str, ...] = (
    "publication_authority",
    "quality_authority",
    "study_authority",
    "submission_authority",
    "user_visible_next_action_authority",
)
RETAINED_CAPABILITY_IDS: tuple[str, ...] = (
    "runtime_execution",
    "artifact_inventory",
    "paper_contract_health",
    "manuscript_coverage",
    "prompt_stage_discipline",
    "memory_and_lesson_store",
)
DOC_REFERENCE_GUARDED_FAMILIES: tuple[str, ...] = (
    "README",
    "docs/README",
    "docs/status",
    "docs/policies",
    "docs/active",
    "docs/runtime",
    "docs/references",
)
DOC_REFERENCE_ALLOWED_MDS_ROLES: tuple[str, ...] = (
    "frozen_source_archive",
    "historical_fixture",
    "explicit_archive_import_ref",
    "provenance_reference",
    "parity_oracle",
    "upstream_intake_source",
)
DOC_REFERENCE_FORBIDDEN_MDS_CLAIMS: tuple[str, ...] = (
    "default_runtime_dependency",
    "default_diagnostic_dependency",
    "default_webui_progress_owner",
    "default_runner",
    "product_owner",
    "study_truth_authority",
    "quality_authority",
    "publication_authority",
    "runtime_authority",
    "artifact_authority",
    "contributor_history_import",
)
DOC_REFERENCE_MAS_PACKAGING_SURFACES: tuple[str, ...] = (
    "artifacts/runtime/progress_portal/latest.json",
    "ops/mas/progress/index.html",
    "ops/mas/bin/start-web",
    "medautosci workspace progress-portal --serve",
    "optional_local_read_only_progress_service",
)
DOC_REFERENCE_FORBIDDEN_AUTHORITY_WRITES: tuple[str, ...] = (
    "study_runtime_status",
    "runtime_watch",
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "study_macro_state/latest.json",
    "owner_route",
    "evidence_ledger",
    "review_ledger",
    "current_package",
    "runtime_lifecycle.sqlite",
)
DOC_REFERENCE_HUB_ROLES: tuple[dict[str, Any], ...] = (
    {
        "surface_id": "product_entry",
        "hub_role": "read_model",
        "authority_claims": [],
        "authority_source_refs": [
            "study_macro_state/latest.json",
            "study_runtime_status",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
        ],
        "materializes_only": [],
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_write_study_truth": False,
    },
    {
        "surface_id": "study_progress",
        "hub_role": "read_model",
        "authority_claims": [],
        "authority_source_refs": [
            "study_macro_state/latest.json",
            "study_runtime_status",
            "runtime_watch",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
        ],
        "materializes_only": [],
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_write_study_truth": False,
    },
    {
        "surface_id": "mcp",
        "hub_role": "adapter",
        "authority_claims": [],
        "authority_source_refs": [
            "MAS CLI/controller payloads",
            "durable workspace surfaces",
        ],
        "materializes_only": [],
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_write_study_truth": False,
    },
    {
        "surface_id": "progress_portal",
        "hub_role": "materializer",
        "authority_claims": [],
        "authority_source_refs": [
            "study_progress.user_visible_projection",
            "workspace-cockpit",
            "study_runtime_status",
            "runtime_watch",
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
        ],
        "materializes_only": [
            "artifacts/runtime/progress_portal/latest.json",
            "ops/mas/progress/index.html",
        ],
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_write_study_truth": False,
    },
    {
        "surface_id": "display_quality_entrances",
        "hub_role": "adapter",
        "authority_claims": [],
        "authority_source_refs": [
            "display registry",
            "quality/publication owner surfaces",
            "artifact rebuild proof",
        ],
        "materializes_only": [],
        "may_control_runtime": False,
        "may_authorize_publication": False,
        "may_write_study_truth": False,
    },
)

HISTORY_POLICY: dict[str, Any] = {
    "import_mode": "no_history_snapshot_only",
    "merge_unrelated_histories_allowed": False,
    "subtree_history_import_allowed": False,
    "filter_repo_history_import_allowed": False,
    "co_authored_by_upstream_authors_allowed": False,
    "unwanted_upstream_author_identity_allowed": False,
}

SOURCE_PROVENANCE: dict[str, Any] = {
    "upstream_repo": "med-deepscientist",
    "upstream_ref": "med-deepscientist@35976b7d6e3b99b15b57ec44ff5f5d959b342ecc",
    "snapshot_sha256": "f8dc31822dc52ecc6e073f54c8b5c95cd46646e299a67cd1c1f6f7f3764e0d5b",
    "snapshot_archive_format": "git archive --format=tar HEAD",
    "snapshot_file_count": 1843,
    "license_refs": [
        "LICENSE (Apache-2.0; Copyright 2026 ResearAI)",
        "MEDICAL_FORK_MANIFEST.json (controlled fork; upstream base a7853fda3432d37f6dee91fa6e66330f564bd8be)",
        "docs/references/med-deepscientist/med_deepscientist_upstream_source_provenance.md",
    ],
    "capability_classification": "external_source_archive_only",
}

AUTHOR_AUDIT: dict[str, Any] = {
    "import_commit_author_policy": "mas_maintainer_only",
    "coauthor_trailers_allowed": False,
    "unwanted_upstream_author_identity_allowed": False,
    "default_branch_contributor_check_required": True,
}

CAPABILITY_CLASSIFICATION_GUARD: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "mas_owned_surface",
        "classification": "mas_owned",
        "mds_role": "source_material_already_absorbed_or_superseded",
        "authority_claims": [],
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
    {
        "capability_id": "rewrite_in_mas_surface",
        "classification": "rewrite_in_mas",
        "mds_role": "source_archive_reference_only",
        "authority_claims": [],
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
    {
        "capability_id": "fixture_only_surface",
        "classification": "fixture_only",
        "mds_role": "fixture_or_historical_oracle_only",
        "authority_claims": [],
        "forbidden_authority_surfaces": list(FORBIDDEN_MDS_ORACLE_AUTHORITY_SURFACES),
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
    {
        "capability_id": "mds_retired_surface",
        "classification": "retire",
        "mds_role": "retired_source",
        "authority_claims": [],
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
    {
        "capability_id": "external_source_archive",
        "classification": "external_source_archive_only",
        "mds_role": "external_source_archive_only",
        "authority_claims": [],
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
)

NO_HISTORY_SNAPSHOT_CAPABILITIES: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "runtime_execution",
        "classification": "mas_owned",
        "mds_role": "oracle_fixture_source",
        "mas_owner": "Runtime OS",
        "authority_claims": [],
    },
    {
        "capability_id": "artifact_inventory",
        "classification": "fixture_only",
        "mds_role": "backend_oracle_only",
        "mas_owner": "Artifact OS",
        "authority_claims": [],
    },
    {
        "capability_id": "paper_contract_health",
        "classification": "fixture_only",
        "mds_role": "mechanical_oracle_only",
        "mas_owner": "Quality OS",
        "authority_claims": [],
    },
    {
        "capability_id": "manuscript_coverage",
        "classification": "fixture_only",
        "mds_role": "mechanical_compat_fixture",
        "mas_owner": "Quality OS",
        "authority_claims": [],
    },
    {
        "capability_id": "prompt_stage_discipline",
        "classification": "mas_owned",
        "mds_role": "source_material_only",
        "mas_owner": "Quality OS",
        "authority_claims": [],
    },
    {
        "capability_id": "memory_and_lesson_store",
        "classification": "retire",
        "mds_role": "intake_reference_only",
        "mas_owner": "Evaluation OS",
        "authority_claims": [],
    },
)


def build_mas_mds_absorb_governance_contract() -> dict[str, Any]:
    return {
        "surface": "mas_mds_absorb_governance_contract",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "upstream_role": "MedDeepScientist optional oracle/intake/backend-audit source",
        "history_policy": dict(HISTORY_POLICY),
        "required_source_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
        "source_provenance": _copy_mapping(SOURCE_PROVENANCE),
        "allowed_capability_classifications": list(ALLOWED_CAPABILITY_CLASSIFICATIONS),
        "capability_classification_guard": [_copy_mapping(item) for item in CAPABILITY_CLASSIFICATION_GUARD],
        "doc_reference_semantic_guard": build_mas_mds_doc_reference_semantic_guard(),
    }


def validate_mas_mds_absorb_governance_contract(contract: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    if _text(contract.get("surface")) != "mas_mds_absorb_governance_contract":
        issues.append({"code": "wrong_surface"})
    if _text(contract.get("owner")) != "MedAutoScience":
        issues.append({"code": "owner_drift"})

    _validate_history_policy(contract.get("history_policy"), issues)
    _validate_source_provenance(contract.get("source_provenance"), issues)
    _validate_classification_guard(contract.get("capability_classification_guard"), issues)
    _validate_doc_reference_semantic_guard(contract.get("doc_reference_semantic_guard"), issues)

    return {
        "surface": "mas_mds_absorb_governance_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def build_mas_mds_doc_reference_semantic_guard() -> dict[str, Any]:
    return {
        "surface": "mas_mds_doc_reference_semantic_guard",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "purpose": "keep README/status/policy/reference wording aligned to MAS-owned monolith semantics",
        "guarded_doc_families": list(DOC_REFERENCE_GUARDED_FAMILIES),
        "machine_contract_anchor": (
            "med_autoscience.controllers.mas_mds_absorb_governance."
            "build_mas_mds_doc_reference_semantic_guard"
        ),
        "doc_prose_wording_tests_allowed": False,
        "markdown_as_machine_truth_allowed": False,
        "readme_status_policy_may_create_owner_truth": False,
        "allowed_mds_roles": list(DOC_REFERENCE_ALLOWED_MDS_ROLES),
        "forbidden_mds_claims": list(DOC_REFERENCE_FORBIDDEN_MDS_CLAIMS),
        "default_operation_requires_external_mds": False,
        "default_diagnostic_requires_external_mds": False,
        "mds_webui_default_allowed": False,
        "hosted_runtime_packaging_owner": "MedAutoScience",
        "mas_owned_packaging_surfaces": list(DOC_REFERENCE_MAS_PACKAGING_SURFACES),
        "hub_reference_roles": [_copy_mapping(item) for item in DOC_REFERENCE_HUB_ROLES],
    }


def validate_mas_mds_doc_reference_semantic_guard(guard: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []
    _validate_doc_reference_semantic_guard(guard, issues)
    return {
        "surface": "mas_mds_doc_reference_semantic_guard_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def build_mds_no_history_snapshot_manifest() -> dict[str, Any]:
    return {
        "surface": "mds_no_history_snapshot_manifest",
        "schema_version": SCHEMA_VERSION,
        "import_mode": "no_history_snapshot_only",
        "default_operation_requires_external_mds": False,
        "source_provenance": _copy_mapping(SOURCE_PROVENANCE),
        "author_audit": _copy_mapping(AUTHOR_AUDIT),
        "capabilities": [_copy_mapping(item) for item in NO_HISTORY_SNAPSHOT_CAPABILITIES],
        "remaining_surface_inventory": build_mds_remaining_surface_inventory(),
        "retained_capability_ids": list(RETAINED_CAPABILITY_IDS),
    }


def validate_mds_no_history_snapshot_manifest(manifest: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    if _text(manifest.get("surface")) != "mds_no_history_snapshot_manifest":
        issues.append({"code": "wrong_surface"})
    if _text(manifest.get("import_mode")) != "no_history_snapshot_only":
        issues.append({"code": "history_import_mode_drift"})
    if manifest.get("default_operation_requires_external_mds") is not False:
        issues.append({"code": "external_mds_required_for_default_operation"})

    _validate_source_provenance(manifest.get("source_provenance"), issues)
    _validate_author_audit(manifest.get("author_audit"), issues)
    _validate_no_history_snapshot_capabilities(manifest.get("capabilities"), issues)
    _validate_remaining_surface_inventory(manifest.get("remaining_surface_inventory"), issues)

    retained_ids = [str(item).strip() for item in _list(manifest.get("retained_capability_ids")) if str(item).strip()]
    if retained_ids != list(RETAINED_CAPABILITY_IDS):
        issues.append({"code": "retained_capability_ids_drift"})

    return {
        "surface": "mds_no_history_snapshot_manifest_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_history_policy(policy: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(policy, Mapping):
        issues.append({"code": "missing_history_policy"})
        return
    if _text(policy.get("import_mode")) != "no_history_snapshot_only":
        issues.append({"code": "history_import_mode_drift"})
    if policy.get("merge_unrelated_histories_allowed") is not False:
        issues.append({"code": "merge_unrelated_histories_unblocked"})
    if policy.get("subtree_history_import_allowed") is not False:
        issues.append({"code": "subtree_history_import_unblocked"})
    if policy.get("filter_repo_history_import_allowed") is not False:
        issues.append({"code": "filter_repo_history_import_unblocked"})
    if policy.get("co_authored_by_upstream_authors_allowed") is not False:
        issues.append({"code": "upstream_coauthor_footprint_unblocked"})
    if policy.get("unwanted_upstream_author_identity_allowed") is not False:
        issues.append({"code": "upstream_author_identity_unblocked"})


def _validate_source_provenance(provenance: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(provenance, Mapping):
        issues.append({"code": "missing_source_provenance"})
        return
    for field in REQUIRED_SOURCE_PROVENANCE_FIELDS:
        value = provenance.get(field)
        if field == "license_refs":
            license_refs = _strings(value)
            if not license_refs:
                issues.append({"code": "missing_source_provenance_field", "field": field})
            elif _contains_placeholder(" ".join(license_refs)):
                issues.append({"code": "placeholder_source_provenance_field", "field": field})
            continue

        text = _text(value)
        if not text:
            issues.append({"code": "missing_source_provenance_field", "field": field})
            continue
        if _contains_placeholder(text):
            issues.append({"code": "placeholder_source_provenance_field", "field": field})
        if field == "snapshot_sha256" and not _is_sha256(text):
            issues.append({"code": "invalid_snapshot_sha256", "field": field})
    classification = _text(provenance.get("capability_classification"))
    if classification and classification not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
        issues.append(
            {
                "code": "invalid_source_provenance_capability_classification",
                "classification": classification,
            }
        )


def _validate_author_audit(author_audit: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(author_audit, Mapping):
        issues.append({"code": "missing_author_audit"})
        return
    if _text(author_audit.get("import_commit_author_policy")) != "mas_maintainer_only":
        issues.append({"code": "import_commit_author_policy_drift"})
    if author_audit.get("coauthor_trailers_allowed") is not False:
        issues.append({"code": "upstream_coauthor_footprint_unblocked"})
    if author_audit.get("unwanted_upstream_author_identity_allowed") is not False:
        issues.append({"code": "upstream_author_identity_unblocked"})
    if author_audit.get("default_branch_contributor_check_required") is not True:
        issues.append({"code": "default_branch_contributor_check_missing"})


def _validate_no_history_snapshot_capabilities(capabilities: object, issues: list[dict[str, Any]]) -> None:
    for item in _list(capabilities):
        if not isinstance(item, Mapping):
            issues.append({"code": "invalid_capability"})
            continue
        capability_id = _text(item.get("capability_id"))
        classification = _text(item.get("classification"))
        if classification not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
            issues.append(
                {
                    "code": "invalid_capability_classification",
                    "capability_id": capability_id,
                    "classification": classification,
                }
            )
        authority_claims = set(_strings(item.get("authority_claims")))
        forbidden_claims = sorted(authority_claims & set(FORBIDDEN_MDS_ORACLE_AUTHORITY_SURFACES))
        if forbidden_claims:
            issues.append(
                {
                    "code": "retained_capability_claims_mas_authority",
                    "capability_id": capability_id,
                    "authority_claims": forbidden_claims,
                }
            )


def _validate_classification_guard(guard: object, issues: list[dict[str, Any]]) -> None:
    for item in _list(guard):
        if not isinstance(item, Mapping):
            issues.append({"code": "invalid_capability_classification_guard"})
            continue
        capability_id = _text(item.get("capability_id"))
        classification = _text(item.get("classification"))
        if classification not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
            issues.append(
                {
                    "code": "invalid_capability_classification",
                    "capability_id": capability_id,
                    "classification": classification,
                }
            )
        authority_claims = set(_strings(item.get("authority_claims")))
        if classification == "fixture_only":
            forbidden_claims = sorted(authority_claims & set(FORBIDDEN_MDS_ORACLE_AUTHORITY_SURFACES))
            if forbidden_claims:
                issues.append(
                    {
                        "code": "mds_fixture_claims_mas_authority",
                        "capability_id": capability_id,
                        "authority_claims": forbidden_claims,
                    }
                )


def _validate_doc_reference_semantic_guard(guard: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(guard, Mapping):
        issues.append({"code": "missing_doc_reference_semantic_guard"})
        return
    if _text(guard.get("surface")) != "mas_mds_doc_reference_semantic_guard":
        issues.append({"code": "wrong_doc_reference_guard_surface"})
    if _text(guard.get("owner")) != "MedAutoScience":
        issues.append({"code": "doc_reference_owner_drift"})

    guarded_families = set(_strings(guard.get("guarded_doc_families")))
    for family in DOC_REFERENCE_GUARDED_FAMILIES:
        if family not in guarded_families:
            issues.append({"code": "missing_guarded_doc_family", "family": family})

    if guard.get("doc_prose_wording_tests_allowed") is not False:
        issues.append({"code": "doc_prose_wording_tests_unblocked"})
    if guard.get("markdown_as_machine_truth_allowed") is not False:
        issues.append({"code": "markdown_machine_truth_unblocked"})
    if guard.get("readme_status_policy_may_create_owner_truth") is not False:
        issues.append({"code": "readme_status_policy_owner_truth_unblocked"})
    if guard.get("default_operation_requires_external_mds") is not False:
        issues.append({"code": "doc_guard_external_mds_required_for_default_operation"})
    if guard.get("default_diagnostic_requires_external_mds") is not False:
        issues.append({"code": "doc_guard_external_mds_required_for_default_diagnostic"})
    if guard.get("mds_webui_default_allowed") is not False:
        issues.append({"code": "mds_webui_default_unblocked"})
    if _text(guard.get("hosted_runtime_packaging_owner")) != "MedAutoScience":
        issues.append({"code": "hosted_runtime_packaging_owner_drift"})

    allowed_roles = set(_strings(guard.get("allowed_mds_roles")))
    if allowed_roles != set(DOC_REFERENCE_ALLOWED_MDS_ROLES):
        issues.append({"code": "allowed_mds_roles_drift", "roles": sorted(allowed_roles)})

    forbidden_claims = set(_strings(guard.get("forbidden_mds_claims")))
    for claim in DOC_REFERENCE_FORBIDDEN_MDS_CLAIMS:
        if claim not in forbidden_claims:
            issues.append({"code": "missing_forbidden_mds_doc_claim", "claim": claim})

    packaging_surfaces = set(_strings(guard.get("mas_owned_packaging_surfaces")))
    for surface in DOC_REFERENCE_MAS_PACKAGING_SURFACES:
        if surface not in packaging_surfaces:
            issues.append({"code": "missing_mas_owned_packaging_surface", "surface": surface})
    for surface in packaging_surfaces:
        lowered = surface.lower()
        if "mds" in lowered or "deepscientist" in lowered or "webui" in lowered:
            issues.append({"code": "mas_packaging_surface_points_to_mds", "surface": surface})

    _validate_doc_reference_hub_roles(guard.get("hub_reference_roles"), issues)


def _validate_doc_reference_hub_roles(hubs: object, issues: list[dict[str, Any]]) -> None:
    hub_mappings = [_mapping(item) for item in _list(hubs)]
    by_surface = {_text(hub.get("surface_id")): hub for hub in hub_mappings if _text(hub.get("surface_id"))}
    for expected in [item["surface_id"] for item in DOC_REFERENCE_HUB_ROLES]:
        if expected not in by_surface:
            issues.append({"code": "missing_doc_reference_hub_role", "surface_id": expected})

    for hub in hub_mappings:
        surface_id = _text(hub.get("surface_id"))
        hub_role = _text(hub.get("hub_role"))
        authority_claims = set(_strings(hub.get("authority_claims")))
        materializes_only = set(_strings(hub.get("materializes_only")))

        if not surface_id:
            issues.append({"code": "doc_reference_hub_missing_surface_id"})
        if hub_role not in {"authority", "read_model", "adapter", "materializer"}:
            issues.append({"code": "doc_reference_hub_role_unknown", "surface_id": surface_id, "hub_role": hub_role})

        if hub_role != "authority":
            if authority_claims:
                issues.append(
                    {
                        "code": "doc_reference_non_authority_hub_claims_authority",
                        "surface_id": surface_id,
                        "authority_claims": sorted(authority_claims),
                    }
                )
            if hub.get("may_control_runtime") is not False or hub.get("may_authorize_publication") is not False:
                issues.append({"code": "doc_reference_non_authority_hub_controls_runtime_or_publication", "surface_id": surface_id})
            if hub.get("may_write_study_truth") is not False:
                issues.append({"code": "doc_reference_non_authority_hub_writes_study_truth", "surface_id": surface_id})

        if hub_role == "materializer" and not materializes_only:
            issues.append({"code": "doc_reference_materializer_missing_output_scope", "surface_id": surface_id})

        forbidden_outputs = sorted(materializes_only & set(DOC_REFERENCE_FORBIDDEN_AUTHORITY_WRITES))
        if forbidden_outputs:
            issues.append(
                {
                    "code": "doc_reference_hub_materializes_authority_surface",
                    "surface_id": surface_id,
                    "surfaces": forbidden_outputs,
                }
            )


def _validate_remaining_surface_inventory(inventory: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(inventory, Mapping):
        issues.append({"code": "missing_remaining_surface_inventory"})
        return
    validation = validate_mds_remaining_surface_inventory(inventory)
    for issue in _list(validation.get("issues")):
        if isinstance(issue, Mapping):
            issues.append(dict(issue))
        else:
            issues.append({"code": "invalid_remaining_surface_inventory_issue"})


def _copy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        result[key] = _copy_value(item)
    return result


def _copy_value(value: Any) -> Any:
    if isinstance(value, Mapping):
        return _copy_mapping(value)
    if isinstance(value, list):
        return [_copy_value(item) for item in value]
    if isinstance(value, tuple):
        return [_copy_value(item) for item in value]
    return value


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in _list(value) if str(item).strip())


def _text(value: object) -> str:
    return str(value or "").strip()


def _contains_placeholder(value: str) -> bool:
    lowered = value.lower()
    return any(token in lowered for token in FORBIDDEN_SOURCE_PROVENANCE_PLACEHOLDERS)


def _is_sha256(value: str) -> bool:
    return len(value) == 64 and all(char in "0123456789abcdefABCDEF" for char in value)
