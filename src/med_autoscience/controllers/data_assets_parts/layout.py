from __future__ import annotations

from pathlib import Path

from med_autoscience.workspace_paths import (
    DATA_ASSET_LAYER_IDS,
    DATA_ASSETS_RELPATH,
    DATASETS_RELPATH,
    data_asset_lineage_root,
    data_assets_root,
    datasets_root,
)


PRIVATE_REGISTRY_BASENAME = "registry.json"
PUBLIC_REGISTRY_BASENAME = "registry.json"
IMPACT_REPORT_BASENAME = "latest_impact_report.json"
PRIVATE_DIFF_REPORT_SCHEMA_VERSION = 1
PUBLIC_REGISTRY_SCHEMA_VERSION = 2
PRIVATE_REGISTRY_SCHEMA_VERSION = 3
DATA_ASSET_LAYOUT_CONTRACT_SCHEMA_VERSION = 2
DATA_ASSET_MANIFEST_REFS_SCHEMA_VERSION = 1
PUBLIC_DATASET_ALLOWED_ROLES = {
    "external_validation",
    "cohort_extension",
    "mechanistic_extension",
    "benchmark_transfer",
}
PUBLIC_DATASET_ALLOWED_STATUSES = {
    "candidate",
    "screened",
    "accepted",
    "rejected",
}
PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES = {
    "not_started",
    "completed",
}
DATA_DOCUMENTATION_COMPONENTS = (
    "data_dictionary",
    "codebook",
    "derived_variables",
)
COHORT_ACCOUNTING_COMPONENT = "cohort_accounting"
RELEASE_READINESS_READY_STATUSES = {"ready", "complete", "locked"}
ALLOWED_DATASET_LAYERS = set(DATA_ASSET_LAYER_IDS)


def data_assets_root_path(workspace_root: Path) -> Path:
    return data_assets_root(workspace_root)


def private_root(workspace_root: Path) -> Path:
    return data_assets_root_path(workspace_root) / "private"


def public_root(workspace_root: Path) -> Path:
    return data_assets_root_path(workspace_root) / "public"


def impact_root(workspace_root: Path) -> Path:
    return data_assets_root_path(workspace_root) / "impact"


def lineage_root(workspace_root: Path) -> Path:
    return data_asset_lineage_root(workspace_root)


def manifest_refs_path(workspace_root: Path) -> Path:
    return lineage_root(workspace_root) / "manifest_refs.json"


def private_registry_path(workspace_root: Path) -> Path:
    return private_root(workspace_root) / PRIVATE_REGISTRY_BASENAME


def private_diffs_root(workspace_root: Path) -> Path:
    return private_root(workspace_root) / "diffs"


def public_registry_path(workspace_root: Path) -> Path:
    return public_root(workspace_root) / PUBLIC_REGISTRY_BASENAME


def impact_report_path(workspace_root: Path) -> Path:
    return impact_root(workspace_root) / IMPACT_REPORT_BASENAME


def private_diff_report_path(*, workspace_root: Path, family_id: str, from_version: str, to_version: str) -> Path:
    return private_diffs_root(workspace_root) / family_id / f"{from_version}__{to_version}.json"


def workspace_ref(*, workspace_root: Path, path: Path) -> str:
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    resolved_path = path.expanduser().resolve()
    try:
        return resolved_path.relative_to(resolved_workspace).as_posix()
    except ValueError:
        return resolved_path.as_posix()


def data_asset_layout_contract(workspace_root: Path) -> dict[str, object]:
    return {
        "schema_version": DATA_ASSET_LAYOUT_CONTRACT_SCHEMA_VERSION,
        "surface_kind": "mas_data_asset_operating_contract",
        "body_plane": {
            "root": DATASETS_RELPATH.as_posix(),
            "layout": "data/datasets/<layer>/<version>/",
            "allowed_layers": list(DATA_ASSET_LAYER_IDS),
            "dataset_body_is_runtime_residue": False,
            "retention_exclusion": {
                "excluded_from_runtime_residue_cleanup": True,
                "reason": "dataset_body_plane_is_domain_data_asset_authority",
            },
        },
        "contract_registry_lineage_plane": {
            "root": DATA_ASSETS_RELPATH.as_posix(),
            "private_registry_ref": "memory/portfolio/data_assets/private/registry.json",
            "public_registry_ref": "memory/portfolio/data_assets/public/registry.json",
            "impact_ref": "memory/portfolio/data_assets/impact/latest_impact_report.json",
            "startup_ref": "memory/portfolio/data_assets/startup/latest_startup_data_readiness.json",
            "mutations_ref": "memory/portfolio/data_assets/mutations/",
            "lineage_ref": "memory/portfolio/data_assets/lineage/",
            "manifest_refs_ref": "memory/portfolio/data_assets/lineage/manifest_refs.json",
            "contains_dataset_body": False,
            "manifest_refs_rebuildable_projection": True,
        },
        "study_binding_plane": {
            "root": "studies/<study-id>/study.yaml",
            "binding_policy": "asset_refs_only",
            "body_storage_allowed": False,
            "accepted_ref_fields": ["dataset_id", "version", "family_id", "source", "asset_ref"],
        },
        "sqlite_read_model_plane": {
            "role": "refs_only_rebuildable_read_model",
            "stores_artifact_or_dataset_body": False,
            "authority": "projection_only",
            "generic_compact_applies_to_dataset_body": False,
        },
        "authority_boundary": {
            "mas_owns": [
                "data_asset_contract",
                "registry",
                "lineage_refs",
                "study_binding_validation",
                "source_readiness",
                "access_tier",
                "clinical_semantic_mapping",
                "owner_receipt",
            ],
            "opl_owns": [
                "generic_runtime_lifecycle",
                "queue",
                "attempt_ledger",
                "generic_retention_cleanup_shell",
                "locator_index",
                "workbench_projection",
            ],
        },
        "workspace_refs": {
            "datasets_root": workspace_ref(workspace_root=workspace_root, path=datasets_root(workspace_root)),
            "data_assets_root": workspace_ref(workspace_root=workspace_root, path=data_assets_root_path(workspace_root)),
        },
    }


def layer_validation(layer_id: str) -> dict[str, object]:
    errors: list[str] = []
    if layer_id not in ALLOWED_DATASET_LAYERS:
        errors.append("unsupported_dataset_layer")
    return {
        "layer_id": layer_id,
        "is_valid": not errors,
        "errors": errors,
        "allowed_layers": list(DATA_ASSET_LAYER_IDS),
    }


def dataset_layout_validation(workspace_root: Path) -> dict[str, object]:
    root = datasets_root(workspace_root)
    layers: list[dict[str, object]] = []
    invalid_layers: list[str] = []
    if root.exists():
        for layer_root in sorted(path for path in root.iterdir() if path.is_dir()):
            validation = layer_validation(layer_root.name)
            versions = sorted(path.name for path in layer_root.iterdir() if path.is_dir() and path.name.startswith("v"))
            validation["version_count"] = len(versions)
            validation["versions"] = versions
            layers.append(validation)
            if not validation["is_valid"]:
                invalid_layers.append(layer_root.name)
    return {
        "is_valid": not invalid_layers,
        "root": workspace_ref(workspace_root=workspace_root, path=root),
        "allowed_layers": list(DATA_ASSET_LAYER_IDS),
        "layers": layers,
        "invalid_layers": invalid_layers,
        "errors": ["unsupported_dataset_layer"] if invalid_layers else [],
    }


def normalize_ref_list(value: object) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [item for item in value if isinstance(item, str)]
    if isinstance(value, dict):
        refs: list[str] = []
        for item in value.values():
            refs.extend(normalize_ref_list(item))
        return refs
    return []


def manifest_ref_errors(refs: list[str]) -> list[str]:
    errors: list[str] = []
    for ref in refs:
        if ref.startswith(DATASETS_RELPATH.as_posix() + "/") or ref.startswith("datasets/"):
            errors.append(f"manifest_ref_points_to_dataset_body:{ref}")
        if Path(ref).is_absolute():
            errors.append(f"manifest_ref_must_be_workspace_relative:{ref}")
    return errors


def manifest_refs(manifest: dict[str, object]) -> dict[str, object]:
    refs = {
        "lineage_refs": normalize_ref_list(manifest.get("lineage_refs")),
        "manifest_refs": normalize_ref_list(manifest.get("manifest_refs")),
    }
    all_refs = refs["lineage_refs"] + refs["manifest_refs"]
    errors = manifest_ref_errors(all_refs)
    return {
        **refs,
        "refs_only": True,
        "contains_dataset_body": False,
        "validation": {
            "is_valid": not errors,
            "errors": errors,
        },
    }


def manifest_refs_payload(*, workspace_root: Path, releases: list[dict[str, object]]) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    invalid_entries: list[dict[str, object]] = []
    for release in releases:
        release_manifest_refs = release.get("manifest_refs", {})
        entry = {
            "dataset_id": release.get("dataset_id"),
            "layer_id": release.get("layer_id"),
            "version_id": release.get("version_id"),
            "manifest_ref": release.get("manifest_ref"),
            "lineage_refs": release_manifest_refs.get("lineage_refs", [])
            if isinstance(release_manifest_refs, dict)
            else [],
            "manifest_refs": release_manifest_refs.get("manifest_refs", [])
            if isinstance(release_manifest_refs, dict)
            else [],
            "refs_only": True,
            "contains_dataset_body": False,
        }
        entries.append(entry)
        refs_validation = release_manifest_refs.get("validation", {}) if isinstance(release_manifest_refs, dict) else {}
        layout_validation_payload = release.get("layout_validation", {}) if isinstance(release.get("layout_validation"), dict) else {}
        errors = []
        if isinstance(refs_validation.get("errors"), list):
            errors.extend(refs_validation["errors"])
        if isinstance(layout_validation_payload.get("errors"), list):
            errors.extend(layout_validation_payload["errors"])
        if errors:
            invalid_entries.append(
                {
                    "dataset_id": release.get("dataset_id"),
                    "layer_id": release.get("layer_id"),
                    "version_id": release.get("version_id"),
                    "errors": errors,
                }
            )
    return {
        "schema_version": DATA_ASSET_MANIFEST_REFS_SCHEMA_VERSION,
        "surface_kind": "mas_data_asset_manifest_refs",
        "workspace_root": str(workspace_root),
        "refs_only": True,
        "contains_dataset_body": False,
        "rebuildable_projection": True,
        "entries": entries,
        "validation": {
            "is_valid": not invalid_entries,
            "invalid_entry_count": len(invalid_entries),
            "invalid_entries": invalid_entries,
        },
    }


__all__ = [
    "ALLOWED_DATASET_LAYERS",
    "COHORT_ACCOUNTING_COMPONENT",
    "DATA_ASSET_LAYOUT_CONTRACT_SCHEMA_VERSION",
    "DATA_ASSET_MANIFEST_REFS_SCHEMA_VERSION",
    "DATA_DOCUMENTATION_COMPONENTS",
    "IMPACT_REPORT_BASENAME",
    "PRIVATE_DIFF_REPORT_SCHEMA_VERSION",
    "PRIVATE_REGISTRY_SCHEMA_VERSION",
    "PUBLIC_DATASET_ALLOWED_ROLES",
    "PUBLIC_DATASET_ALLOWED_STATUSES",
    "PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES",
    "PUBLIC_REGISTRY_SCHEMA_VERSION",
    "RELEASE_READINESS_READY_STATUSES",
    "data_asset_layout_contract",
    "data_assets_root_path",
    "dataset_layout_validation",
    "impact_report_path",
    "impact_root",
    "layer_validation",
    "lineage_root",
    "manifest_ref_errors",
    "manifest_refs",
    "manifest_refs_path",
    "manifest_refs_payload",
    "private_diff_report_path",
    "private_diffs_root",
    "private_registry_path",
    "private_root",
    "public_registry_path",
    "public_root",
    "workspace_ref",
]
