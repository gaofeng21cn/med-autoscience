from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.data_assets_parts.layout import (
    COHORT_ACCOUNTING_COMPONENT,
    DATA_DOCUMENTATION_COMPONENTS,
    DATASETS_RELPATH,
    RELEASE_READINESS_READY_STATUSES,
    layer_validation,
    manifest_refs,
    workspace_ref,
)
from med_autoscience.controllers.data_assets_parts.serialization import (
    load_yaml_dict,
    normalize_dict,
    normalize_int,
    normalize_string_list,
    normalize_string_map,
)
from med_autoscience.workspace_paths import datasets_root


def standardization_status(release_contract: dict[str, object]) -> dict[str, object]:
    access_tier = release_contract.get("access_tier") if isinstance(release_contract.get("access_tier"), str) else None
    contracts = normalize_dict(release_contract.get("standardization_contracts"))
    has_medication = bool(contracts.get("medication_standardization"))
    has_numeric = bool(contracts.get("numeric_unit_and_plausibility"))
    is_standardized = access_tier in {"analysis_ready_standardized", "publication_ready_standardized"}
    return {
        "is_standardized": is_standardized,
        "access_tier": access_tier,
        "has_medication_standardization": has_medication,
        "has_numeric_unit_and_plausibility": has_numeric,
        "contracts": contracts,
    }


def release_contract_field(
    *,
    manifest: dict[str, object],
    release_contract: dict[str, object],
    key: str,
) -> dict[str, object]:
    value = manifest.get(key)
    if value is None:
        value = release_contract.get(key)
    return normalize_dict(value)


def component_path_exists(*, version_root: Path, contract: dict[str, object]) -> bool:
    relative_path = contract.get("path")
    if not isinstance(relative_path, str) or not relative_path:
        return False
    return (version_root / relative_path).is_file()


def document_component_readiness(*, version_root: Path, contract: dict[str, object]) -> dict[str, object]:
    status = contract.get("status") if isinstance(contract.get("status"), str) else None
    path_exists = component_path_exists(version_root=version_root, contract=contract)
    errors: list[str] = []
    if not contract:
        errors.append("missing_contract")
    if status not in RELEASE_READINESS_READY_STATUSES:
        errors.append("status_not_ready")
    if not path_exists:
        errors.append("missing_declared_path")
    return {
        "status": status,
        "path": contract.get("path") if isinstance(contract.get("path"), str) else None,
        "path_exists": path_exists,
        "ready": not errors,
        "errors": errors,
        "contract": contract,
    }


def cohort_accounting_readiness(*, version_root: Path, contract: dict[str, object]) -> dict[str, object]:
    status = contract.get("status") if isinstance(contract.get("status"), str) else None
    source_n = normalize_int(contract.get("source_n"))
    analysis_n = normalize_int(contract.get("analysis_n"))
    exclusions = contract.get("exclusions") if isinstance(contract.get("exclusions"), list) else []
    cohort_flow_path = contract.get("cohort_flow_path") if isinstance(contract.get("cohort_flow_path"), str) else None
    cohort_flow_exists = (version_root / cohort_flow_path).is_file() if cohort_flow_path else False
    errors: list[str] = []
    if not contract:
        errors.append("missing_contract")
    if status not in RELEASE_READINESS_READY_STATUSES:
        errors.append("status_not_ready")
    if source_n is None:
        errors.append("missing_source_n")
    if analysis_n is None:
        errors.append("missing_analysis_n")
    if source_n is not None and analysis_n is not None and analysis_n > source_n:
        errors.append("analysis_n_exceeds_source_n")
    if not cohort_flow_exists:
        errors.append("missing_cohort_flow")
    return {
        "status": status,
        "source_n": source_n,
        "analysis_n": analysis_n,
        "exclusions": exclusions,
        "cohort_flow_path": cohort_flow_path,
        "cohort_flow_exists": cohort_flow_exists,
        "ready": not errors,
        "errors": errors,
        "contract": contract,
    }


def release_semantic_readiness(
    *,
    version_root: Path,
    manifest: dict[str, object],
    release_contract: dict[str, object],
) -> dict[str, object]:
    component_contracts = {
        key: release_contract_field(manifest=manifest, release_contract=release_contract, key=key)
        for key in DATA_DOCUMENTATION_COMPONENTS
    }
    component_contracts[COHORT_ACCOUNTING_COMPONENT] = release_contract_field(
        manifest=manifest,
        release_contract=release_contract,
        key=COHORT_ACCOUNTING_COMPONENT,
    )
    required = bool(
        manifest.get("semantic_readiness_required")
        or release_contract.get("semantic_readiness_required")
        or any(component_contracts.values())
    )
    components: dict[str, dict[str, object]] = {}
    errors: list[str] = []
    for key in DATA_DOCUMENTATION_COMPONENTS:
        readiness = document_component_readiness(
            version_root=version_root,
            contract=component_contracts[key],
        )
        components[key] = readiness
        if required:
            errors.extend(f"{key}:{error}" for error in readiness["errors"])
    cohort_readiness = cohort_accounting_readiness(
        version_root=version_root,
        contract=component_contracts[COHORT_ACCOUNTING_COMPONENT],
    )
    components[COHORT_ACCOUNTING_COMPONENT] = cohort_readiness
    if required:
        errors.extend(f"{COHORT_ACCOUNTING_COMPONENT}:{error}" for error in cohort_readiness["errors"])
    return {
        "required": required,
        "ready": not errors,
        "errors": errors,
        "components": components,
    }


def list_release_files(version_root: Path) -> list[Path]:
    return sorted(path for path in version_root.rglob("*") if path.is_file())


def inventory_summary(*, version_root: Path, main_outputs: dict[str, str]) -> dict[str, object]:
    files = list_release_files(version_root)
    declared_outputs_present = {
        output_name: (version_root / relative_path).exists() for output_name, relative_path in main_outputs.items()
    }
    return {
        "file_count": len(files),
        "total_size_bytes": sum(path.stat().st_size for path in files),
        "declared_outputs_present": declared_outputs_present,
    }


def build_private_release(*, workspace_root: Path, family_id: str, version_root: Path) -> dict[str, object]:
    manifest_path = version_root / "dataset_manifest.yaml"
    manifest = load_yaml_dict(manifest_path)
    main_outputs = normalize_string_map(manifest.get("main_outputs"))
    notes = normalize_string_list(manifest.get("notes"))
    dataset_id = manifest.get("dataset_id") if isinstance(manifest.get("dataset_id"), str) else None
    raw_snapshot = manifest.get("raw_snapshot") if isinstance(manifest.get("raw_snapshot"), str) else None
    generated_by = manifest.get("generated_by") if isinstance(manifest.get("generated_by"), str) else None
    source_release = normalize_dict(manifest.get("source_release"))
    declared_release_contract = normalize_dict(manifest.get("release_contract"))
    supersedes_versions = normalize_string_list(manifest.get("supersedes_versions"))
    if not supersedes_versions:
        supersedes_versions = normalize_string_list(declared_release_contract.get("supersedes_versions"))
    release_inventory_summary = inventory_summary(version_root=version_root, main_outputs=main_outputs)
    semantic_readiness = release_semantic_readiness(
        version_root=version_root,
        manifest=manifest,
        release_contract=declared_release_contract,
    )
    layout_validation = layer_validation(family_id)
    release_manifest_refs = manifest_refs(manifest)
    return {
        "family_id": family_id,
        "version_id": version_root.name,
        "layer_id": family_id,
        "dataset_id": dataset_id,
        "data_root": str(version_root),
        "data_root_ref": workspace_ref(workspace_root=workspace_root, path=version_root),
        "manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "manifest_ref": workspace_ref(workspace_root=workspace_root, path=manifest_path) if manifest_path.exists() else None,
        "contract_status": "manifest_backed" if manifest_path.exists() else "directory_scan_only",
        "layout_validation": layout_validation,
        "manifest_refs": release_manifest_refs,
        "body_plane": {
            "role": "dataset_body",
            "root_ref": DATASETS_RELPATH.as_posix(),
            "layout": "data/datasets/<layer>/<version>/",
            "runtime_residue": False,
            "retention_excluded": True,
        },
        "registry_plane": {
            "role": "refs_only_registry_projection",
            "contains_dataset_body": False,
        },
        "raw_snapshot": raw_snapshot,
        "generated_by": generated_by,
        "source_release": source_release,
        "main_outputs": main_outputs,
        "notes": notes,
        "supersedes_versions": supersedes_versions,
        "declared_release_contract": declared_release_contract,
        "standardization_status": standardization_status(declared_release_contract),
        "semantic_readiness": semantic_readiness,
        "data_dictionary": semantic_readiness["components"]["data_dictionary"],
        "codebook": semantic_readiness["components"]["codebook"],
        "derived_variables": semantic_readiness["components"]["derived_variables"],
        "cohort_accounting": semantic_readiness["components"]["cohort_accounting"],
        "inventory_summary": release_inventory_summary,
        "file_count": release_inventory_summary["file_count"],
    }


def private_release_roots(workspace_root: Path) -> list[Path]:
    current_root = datasets_root(workspace_root)
    roots: list[Path] = []
    seen: set[Path] = set()
    for root in (current_root,):
        resolved = root.resolve()
        if resolved in seen or not root.exists():
            continue
        seen.add(resolved)
        roots.append(root)
    return roots


def scan_private_releases(workspace_root: Path) -> list[dict[str, object]]:
    releases: list[dict[str, object]] = []
    seen: set[tuple[str, str]] = set()
    for releases_root in private_release_roots(workspace_root):
        for family_root in sorted(path for path in releases_root.iterdir() if path.is_dir()):
            for version_root in sorted(
                path for path in family_root.iterdir() if path.is_dir() and path.name.startswith("v")
            ):
                key = (family_root.name, version_root.name)
                if key in seen:
                    continue
                seen.add(key)
                releases.append(
                    build_private_release(
                        workspace_root=workspace_root,
                        family_id=family_root.name,
                        version_root=version_root,
                    )
                )
    return releases


__all__ = [
    "build_private_release",
    "cohort_accounting_readiness",
    "component_path_exists",
    "document_component_readiness",
    "inventory_summary",
    "list_release_files",
    "private_release_roots",
    "release_contract_field",
    "release_semantic_readiness",
    "scan_private_releases",
    "standardization_status",
]
