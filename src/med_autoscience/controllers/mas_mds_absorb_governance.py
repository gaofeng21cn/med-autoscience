from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1

ALLOWED_CAPABILITY_CLASSIFICATIONS: tuple[str, ...] = ("absorb", "oracle", "retire", "compat")
REQUIRED_SOURCE_PROVENANCE_FIELDS: tuple[str, ...] = (
    "upstream_repo",
    "upstream_ref",
    "snapshot_sha256",
    "license_refs",
    "capability_classification",
)
FORBIDDEN_MDS_ORACLE_AUTHORITY_SURFACES: tuple[str, ...] = (
    "publication_authority",
    "quality_authority",
    "study_authority",
    "submission_authority",
    "user_visible_next_action_authority",
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
    "upstream_ref": "snapshot-ref-recorded-at-intake",
    "snapshot_sha256": "required_per_snapshot_intake",
    "license_refs": ["upstream license file", "third-party notice inventory"],
    "capability_classification": "oracle",
}

CAPABILITY_CLASSIFICATION_GUARD: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "mas_owned_absorb_candidate",
        "classification": "absorb",
        "mds_role": "source_material_only",
        "authority_claims": [],
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
    {
        "capability_id": "mds_regression_oracle",
        "classification": "oracle",
        "mds_role": "backend_oracle_only",
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
        "capability_id": "mds_compat_fixture",
        "classification": "compat",
        "mds_role": "compat_fixture_only",
        "authority_claims": [],
        "required_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
    },
)


def build_mas_mds_absorb_governance_contract() -> dict[str, Any]:
    return {
        "surface": "mas_mds_absorb_governance_contract",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "upstream_role": "MedDeepScientist controlled backend/oracle/intake source",
        "history_policy": dict(HISTORY_POLICY),
        "required_source_provenance_fields": list(REQUIRED_SOURCE_PROVENANCE_FIELDS),
        "source_provenance": _copy_mapping(SOURCE_PROVENANCE),
        "allowed_capability_classifications": list(ALLOWED_CAPABILITY_CLASSIFICATIONS),
        "capability_classification_guard": [_copy_mapping(item) for item in CAPABILITY_CLASSIFICATION_GUARD],
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

    return {
        "surface": "mas_mds_absorb_governance_validation",
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
            if not _list(value):
                issues.append({"code": "missing_source_provenance_field", "field": field})
        elif not _text(value):
            issues.append({"code": "missing_source_provenance_field", "field": field})
    classification = _text(provenance.get("capability_classification"))
    if classification and classification not in ALLOWED_CAPABILITY_CLASSIFICATIONS:
        issues.append(
            {
                "code": "invalid_source_provenance_capability_classification",
                "classification": classification,
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
        if classification == "oracle":
            forbidden_claims = sorted(authority_claims & set(FORBIDDEN_MDS_ORACLE_AUTHORITY_SURFACES))
            if forbidden_claims:
                issues.append(
                    {
                        "code": "mds_oracle_claims_mas_authority",
                        "capability_id": capability_id,
                        "authority_claims": forbidden_claims,
                    }
                )


def _copy_mapping(value: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, item in value.items():
        if isinstance(item, list):
            result[key] = list(item)
        else:
            result[key] = item
    return result


def _list(value: object) -> list[object]:
    return value if isinstance(value, list) else []


def _strings(value: object) -> tuple[str, ...]:
    return tuple(str(item).strip() for item in _list(value) if str(item).strip())


def _text(value: object) -> str:
    return str(value or "").strip()
