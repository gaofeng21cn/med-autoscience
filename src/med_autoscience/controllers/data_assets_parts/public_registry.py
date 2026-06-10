from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.data_assets_parts.layout import (
    PUBLIC_DATASET_ALLOWED_ROLES,
    PUBLIC_DATASET_ALLOWED_STATUSES,
    PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES,
    PUBLIC_REGISTRY_SCHEMA_VERSION,
    public_registry_path,
)
from med_autoscience.controllers.data_assets_parts.serialization import (
    load_json,
    normalize_int,
    normalize_string_list,
    write_json,
)


def normalize_public_dataset_entry(item: object) -> dict[str, object]:
    payload = item if isinstance(item, dict) else {}
    roles = [role for role in normalize_string_list(payload.get("roles")) if role in PUBLIC_DATASET_ALLOWED_ROLES]
    status = payload.get("status") if isinstance(payload.get("status"), str) else "candidate"
    normalized = {
        "dataset_id": payload.get("dataset_id") if isinstance(payload.get("dataset_id"), str) else None,
        "source_type": payload.get("source_type") if isinstance(payload.get("source_type"), str) else None,
        "accession": payload.get("accession") if isinstance(payload.get("accession"), str) else None,
        "disease": payload.get("disease") if isinstance(payload.get("disease"), str) else None,
        "modality": normalize_string_list(payload.get("modality")),
        "endpoints": normalize_string_list(payload.get("endpoints")),
        "roles": roles,
        "target_families": normalize_string_list(payload.get("target_families")),
        "target_dataset_ids": normalize_string_list(payload.get("target_dataset_ids")),
        "target_study_archetypes": normalize_string_list(payload.get("target_study_archetypes")),
        "cohort_size": normalize_int(payload.get("cohort_size")),
        "license": payload.get("license") if isinstance(payload.get("license"), str) else None,
        "access_url": payload.get("access_url") if isinstance(payload.get("access_url"), str) else None,
        "status": status if status in PUBLIC_DATASET_ALLOWED_STATUSES else "candidate",
        "rationale": payload.get("rationale") if isinstance(payload.get("rationale"), str) else None,
        "notes": normalize_string_list(payload.get("notes")),
    }
    errors: list[str] = []
    if not normalized["dataset_id"]:
        errors.append("missing_dataset_id")
    if not normalized["source_type"]:
        errors.append("missing_source_type")
    if not normalized["roles"]:
        errors.append("missing_roles")
    if not (
        normalized["target_families"]
        or normalized["target_dataset_ids"]
        or normalized["target_study_archetypes"]
    ):
        errors.append("missing_target_scope")
    normalized["validation"] = {
        "is_valid": not errors,
        "errors": errors,
    }
    return normalized


def normalize_public_registry_discovery(value: object) -> dict[str, object]:
    payload = value if isinstance(value, dict) else {}
    status = payload.get("status") if isinstance(payload.get("status"), str) else "not_started"
    last_scouted_on = payload.get("last_scouted_on") if isinstance(payload.get("last_scouted_on"), str) else None
    scope = payload.get("scope") if isinstance(payload.get("scope"), str) and payload.get("scope").strip() else "route_selection"
    return {
        "status": status if status in PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES else "not_started",
        "last_scouted_on": last_scouted_on,
        "scope": scope,
        "notes": normalize_string_list(payload.get("notes")),
    }


def normalize_public_registry_payload(payload: dict) -> dict[str, object]:
    datasets_value = payload.get("datasets")
    datasets: list[dict[str, object]] = []
    if isinstance(datasets_value, list):
        datasets = [normalize_public_dataset_entry(item) for item in datasets_value]
    return {
        "schema_version": PUBLIC_REGISTRY_SCHEMA_VERSION,
        "discovery": normalize_public_registry_discovery(payload.get("discovery")),
        "datasets": datasets,
    }


def load_public_registry(workspace_root: Path) -> dict[str, object]:
    path = public_registry_path(workspace_root)
    payload = load_json(
        path,
        default={
            "schema_version": PUBLIC_REGISTRY_SCHEMA_VERSION,
            "discovery": normalize_public_registry_discovery({}),
            "datasets": [],
        },
    )
    normalized = normalize_public_registry_payload(payload)
    if payload != normalized:
        write_json(path, normalized)
    return normalized


def validate_public_registry(*, workspace_root: Path) -> dict[str, object]:
    payload = load_public_registry(workspace_root)
    datasets = payload["datasets"]
    assert isinstance(datasets, list)
    valid_dataset_count = sum(
        1 for item in datasets if isinstance(item, dict) and item.get("validation", {}).get("is_valid")
    )
    invalid_dataset_count = len(datasets) - valid_dataset_count
    return {
        "schema_version": PUBLIC_REGISTRY_SCHEMA_VERSION,
        "workspace_root": str(workspace_root),
        "registry_path": str(public_registry_path(workspace_root)),
        "discovery": payload["discovery"],
        "dataset_count": len(datasets),
        "valid_dataset_count": valid_dataset_count,
        "invalid_dataset_count": invalid_dataset_count,
        "datasets": datasets,
    }


__all__ = [
    "load_public_registry",
    "normalize_public_dataset_entry",
    "normalize_public_registry_discovery",
    "normalize_public_registry_payload",
    "validate_public_registry",
]
