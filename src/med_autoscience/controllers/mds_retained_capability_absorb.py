from __future__ import annotations

from typing import Any, Mapping


SCHEMA_VERSION = 1

RETAINED_OWNER_ORDER: tuple[str, ...] = ("Runtime OS", "Artifact OS", "Quality OS")
ALLOWED_MDS_FIXTURE_ROLES: tuple[str, ...] = (
    "legacy_oracle",
    "compat_oracle",
    "legacy_compat_oracle",
)
LEGACY_COMPAT_ORACLE_MARKERS: tuple[str, ...] = ("legacy", "compat", "oracle")

AUTHORITY_CONTRACT: dict[str, Any] = {
    "runtime_authority_owner": "Runtime OS",
    "artifact_authority_owner": "Artifact OS",
    "quality_authority_owner": "Quality OS",
    "mds_can_authorize_runtime": False,
    "mds_can_authorize_artifacts": False,
    "mds_can_authorize_quality_ready": False,
    "mds_can_authorize_publication_ready": False,
    "mechanical_oracle_can_authorize_quality_ready": False,
    "mechanical_oracle_can_authorize_publication_ready": False,
    "quality_ready_requires_ai_reviewer_provenance": True,
    "publication_ready_requires_publication_eval_and_controller_decisions": True,
}

RETAINED_CAPABILITY_GROUPS: tuple[dict[str, Any], ...] = (
    {
        "capability_id": "runtime_execution_recovery_replay",
        "owner": "Runtime OS",
        "consumption_contract": "execution/recovery replay consumer",
        "mds_oracle_fixture": "legacy_med_deepscientist_runtime_replay_oracle_fixture",
        "mds_fixture_role": "legacy_oracle",
        "mds_authority": "none",
        "mas_consumer_surfaces": ["study_runtime_status", "runtime_watch"],
        "can_authorize_quality_ready": False,
        "can_authorize_publication_ready": False,
    },
    {
        "capability_id": "artifact_inventory_package_locator",
        "owner": "Artifact OS",
        "consumption_contract": "inventory/package locator parity",
        "mds_oracle_fixture": "compat_med_deepscientist_artifact_locator_oracle_fixture",
        "mds_fixture_role": "compat_oracle",
        "mds_authority": "none",
        "mas_consumer_surfaces": [
            "artifact_inventory",
            "submission_minimal",
            "current_package locator",
        ],
        "can_authorize_quality_ready": False,
        "can_authorize_publication_ready": False,
    },
    {
        "capability_id": "quality_mechanical_oracle_input",
        "owner": "Quality OS",
        "consumption_contract": "mechanical oracle input",
        "mds_oracle_fixture": "legacy_compat_med_deepscientist_quality_preflight_oracle_fixture",
        "mds_fixture_role": "legacy_compat_oracle",
        "mds_authority": "none",
        "mas_consumer_surfaces": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "AI reviewer provenance",
        ],
        "requires_ai_reviewer_provenance": True,
        "mechanical_oracle_can_authorize_quality_ready": False,
        "mechanical_oracle_can_authorize_publication_ready": False,
        "can_authorize_quality_ready": False,
        "can_authorize_publication_ready": False,
    },
)


def build_mds_retained_capability_absorb_surface() -> dict[str, Any]:
    groups = [_copy_mapping(group) for group in RETAINED_CAPABILITY_GROUPS]
    return {
        "surface": "mds_retained_capability_absorb",
        "schema_version": SCHEMA_VERSION,
        "owner": "MedAutoScience",
        "mds_authority": "none",
        "retained_owner_order": list(RETAINED_OWNER_ORDER),
        "authority_contract": _copy_mapping(AUTHORITY_CONTRACT),
        "retained_capability_groups": groups,
        "summary": {
            "owner_count": len(RETAINED_OWNER_ORDER),
            "capability_group_count": len(groups),
            "mds_role": "legacy_compat_oracle_fixture_only",
            "quality_ready_authority": "blocked_for_mds_mechanical_oracle",
            "publication_ready_authority": "blocked_for_mds_mechanical_oracle",
        },
    }


def validate_mds_retained_capability_absorb_surface(surface: Mapping[str, Any]) -> dict[str, Any]:
    issues: list[dict[str, Any]] = []

    if _text(surface.get("surface")) != "mds_retained_capability_absorb":
        issues.append({"code": "wrong_surface"})
    if _text(surface.get("owner")) != "MedAutoScience":
        issues.append({"code": "owner_drift"})
    if _text(surface.get("mds_authority")) != "none":
        issues.append({"code": "authority_drift", "field": "mds_authority"})
    if _strings(surface.get("retained_owner_order")) != RETAINED_OWNER_ORDER:
        issues.append({"code": "retained_owner_order_drift"})

    _validate_authority_contract(surface.get("authority_contract"), issues)
    _validate_groups(surface.get("retained_capability_groups"), issues)
    _validate_deepscientist_markers(surface, issues)

    return {
        "surface": "mds_retained_capability_absorb_validation",
        "schema_version": SCHEMA_VERSION,
        "ok": not issues,
        "issue_count": len(issues),
        "issues": issues,
    }


def _validate_authority_contract(contract: object, issues: list[dict[str, Any]]) -> None:
    if not isinstance(contract, Mapping):
        issues.append({"code": "missing_authority_contract"})
        return
    for field in ("runtime_authority_owner", "artifact_authority_owner", "quality_authority_owner"):
        if _text(contract.get(field)) not in RETAINED_OWNER_ORDER:
            issues.append({"code": "authority_owner_drift", "field": field})
    for field in (
        "mds_can_authorize_runtime",
        "mds_can_authorize_artifacts",
        "mds_can_authorize_quality_ready",
        "mds_can_authorize_publication_ready",
    ):
        if contract.get(field) is not False:
            issues.append({"code": "authority_drift", "field": field})
    if contract.get("mechanical_oracle_can_authorize_quality_ready") is not False:
        issues.append({"code": "quality_ready_drift", "field": "mechanical_oracle_can_authorize_quality_ready"})
    if contract.get("mechanical_oracle_can_authorize_publication_ready") is not False:
        issues.append(
            {"code": "publication_ready_drift", "field": "mechanical_oracle_can_authorize_publication_ready"}
        )
    if contract.get("quality_ready_requires_ai_reviewer_provenance") is not True:
        issues.append({"code": "quality_ready_drift", "field": "quality_ready_requires_ai_reviewer_provenance"})
    if contract.get("publication_ready_requires_publication_eval_and_controller_decisions") is not True:
        issues.append(
            {
                "code": "publication_ready_drift",
                "field": "publication_ready_requires_publication_eval_and_controller_decisions",
            }
        )


def _validate_groups(groups: object, issues: list[dict[str, Any]]) -> None:
    group_list = _list(groups)
    if not group_list:
        issues.append({"code": "missing_retained_capability_groups"})
        return
    owners: list[str] = []
    for group in group_list:
        if not isinstance(group, Mapping):
            issues.append({"code": "invalid_retained_capability_group"})
            continue
        capability_id = _text(group.get("capability_id"))
        owner = _text(group.get("owner"))
        owners.append(owner)
        if owner not in RETAINED_OWNER_ORDER:
            issues.append({"code": "retained_group_owner_drift", "capability_id": capability_id})
        if _text(group.get("mds_authority")) != "none":
            issues.append({"code": "authority_drift", "capability_id": capability_id, "field": "mds_authority"})
        if _text(group.get("mds_fixture_role")) not in ALLOWED_MDS_FIXTURE_ROLES:
            issues.append({"code": "invalid_mds_fixture_role", "capability_id": capability_id})
        if not _text(group.get("mds_oracle_fixture")):
            issues.append({"code": "missing_mds_oracle_fixture", "capability_id": capability_id})
        if not _text(group.get("consumption_contract")):
            issues.append({"code": "missing_consumption_contract", "capability_id": capability_id})
        if not _list(group.get("mas_consumer_surfaces")):
            issues.append({"code": "missing_mas_consumer_surfaces", "capability_id": capability_id})
        if group.get("can_authorize_quality_ready") is not False:
            issues.append({"code": "quality_ready_drift", "capability_id": capability_id})
        if group.get("can_authorize_publication_ready") is not False:
            issues.append({"code": "publication_ready_drift", "capability_id": capability_id})
        if owner == "Quality OS":
            if group.get("requires_ai_reviewer_provenance") is not True:
                issues.append({"code": "quality_ready_drift", "capability_id": capability_id})
            if group.get("mechanical_oracle_can_authorize_quality_ready") is not False:
                issues.append({"code": "quality_ready_drift", "capability_id": capability_id})
            if group.get("mechanical_oracle_can_authorize_publication_ready") is not False:
                issues.append({"code": "publication_ready_drift", "capability_id": capability_id})
    if tuple(owners) != RETAINED_OWNER_ORDER:
        issues.append({"code": "retained_group_owner_order_drift"})


def _validate_deepscientist_markers(value: object, issues: list[dict[str, Any]], path: str = "$") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            _validate_deepscientist_markers(item, issues, f"{path}.{key}")
        return
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_deepscientist_markers(item, issues, f"{path}[{index}]")
        return
    if not isinstance(value, str):
        return
    normalized = value.lower().replace("-", "_")
    if "deepscientist" not in normalized:
        return
    if any(marker in normalized for marker in LEGACY_COMPAT_ORACLE_MARKERS):
        return
    issues.append(
        {
            "code": "deepscientist_reference_missing_legacy_compat_or_oracle_marker",
            "path": path,
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
