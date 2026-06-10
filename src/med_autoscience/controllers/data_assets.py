from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path
from typing import Any

import yaml

from med_autoscience.controllers.data_assets_parts import impact_assessment as _impact_assessment
from med_autoscience.controllers.data_assets_parts.layout import (
    ALLOWED_DATASET_LAYERS,
    DATA_ASSET_LAYOUT_CONTRACT_SCHEMA_VERSION,
    DATA_ASSET_MANIFEST_REFS_SCHEMA_VERSION,
    PUBLIC_DATASET_ALLOWED_ROLES,
    PUBLIC_DATASET_ALLOWED_STATUSES,
    PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES,
    PRIVATE_DIFF_REPORT_SCHEMA_VERSION,
    PRIVATE_REGISTRY_SCHEMA_VERSION,
    PUBLIC_REGISTRY_SCHEMA_VERSION,
    data_asset_layout_contract,
    data_assets_root_path,
    dataset_layout_validation,
    impact_report_path,
    impact_root,
    layer_validation,
    lineage_root,
    manifest_ref_errors,
    manifest_refs,
    manifest_refs_path,
    manifest_refs_payload,
    private_diff_report_path,
    private_diffs_root,
    private_registry_path,
    private_root,
    public_registry_path,
    public_root,
    workspace_ref,
)
from med_autoscience.controllers.data_assets_parts.public_registry import (
    load_public_registry,
    normalize_public_dataset_entry,
    normalize_public_registry_discovery,
    normalize_public_registry_payload,
    validate_public_registry,
)
from med_autoscience.controllers.data_assets_parts.release_inventory import (
    build_private_release,
    inventory_summary,
    list_release_files,
    scan_private_releases,
    standardization_status,
)
from med_autoscience.controllers.data_assets_parts.serialization import (
    load_json as _load_json,
    load_yaml_dict as _load_yaml_dict,
    normalize_dict as _normalize_dict,
    normalize_int as _normalize_int,
    normalize_string_list as _normalize_string_list,
    normalize_string_map as _normalize_string_map,
    write_json as _write_json,
)
from med_autoscience.workspace_paths import DATA_ASSET_LAYER_IDS, DATASETS_RELPATH, datasets_root


_data_assets_root = data_assets_root_path
_private_root = private_root
_public_root = public_root
_impact_root = impact_root
_lineage_root = lineage_root
_manifest_refs_path = manifest_refs_path
_private_registry_path = private_registry_path
_private_diffs_root = private_diffs_root
_public_registry_path = public_registry_path
_impact_report_path = impact_report_path
_private_diff_report_path = private_diff_report_path
_workspace_ref = workspace_ref
_data_asset_layout_contract = data_asset_layout_contract
_layer_validation = layer_validation
_dataset_layout_validation = dataset_layout_validation
_manifest_ref_errors = manifest_ref_errors
_manifest_refs = manifest_refs
_manifest_refs_payload = manifest_refs_payload
_standardization_status = standardization_status
_inventory_summary = inventory_summary
_list_release_files = list_release_files
_build_private_release = build_private_release
_scan_private_releases = scan_private_releases
_normalize_public_dataset_entry = normalize_public_dataset_entry
_normalize_public_registry_discovery = normalize_public_registry_discovery
_normalize_public_registry_payload = normalize_public_registry_payload
_load_public_registry = load_public_registry


def _private_diff_count(workspace_root: Path) -> int:
    diffs_root = private_diffs_root(workspace_root)
    if not diffs_root.exists():
        return 0
    return sum(1 for path in diffs_root.rglob("*.json") if path.is_file())


def _find_release_root(*, workspace_root: Path, family_id: str, version_id: str) -> Path:
    release_root = datasets_root(workspace_root) / family_id / version_id
    if not release_root.exists():
        raise FileNotFoundError(f"Private release not found: {family_id}/{version_id}")
    return release_root


def _release_snapshot_for_report(release: dict[str, object]) -> dict[str, object]:
    return {
        "family_id": release["family_id"],
        "version_id": release["version_id"],
        "layer_id": release.get("layer_id"),
        "dataset_id": release.get("dataset_id"),
        "raw_snapshot": release.get("raw_snapshot"),
        "generated_by": release.get("generated_by"),
        "main_outputs": release.get("main_outputs", {}),
        "notes": release.get("notes", []),
        "declared_release_contract": release.get("declared_release_contract", {}),
        "layout_validation": release.get("layout_validation", {}),
        "manifest_refs": release.get("manifest_refs", {}),
        "semantic_readiness": release.get("semantic_readiness", {}),
        "inventory_summary": release.get("inventory_summary", {}),
    }


def _release_inventory_map(version_root: Path) -> dict[str, dict[str, int]]:
    inventory: dict[str, dict[str, int]] = {}
    for path in list_release_files(version_root):
        inventory[str(path.relative_to(version_root))] = {"size_bytes": path.stat().st_size}
    return inventory


def _contract_changes(from_release: dict[str, object], to_release: dict[str, object]) -> list[dict[str, object]]:
    fields = [
        "generated_by",
        "raw_snapshot",
        "notes",
        "declared_release_contract",
        "dataset_id",
    ]
    changes: list[dict[str, object]] = []
    for field in fields:
        from_value = from_release.get(field)
        to_value = to_release.get(field)
        if from_value != to_value:
            changes.append({"field": field, "from": from_value, "to": to_value})
    return changes


def _main_output_changes(from_release: dict[str, object], to_release: dict[str, object]) -> list[dict[str, object]]:
    from_outputs = from_release.get("main_outputs", {})
    to_outputs = to_release.get("main_outputs", {})
    if not isinstance(from_outputs, dict) or not isinstance(to_outputs, dict):
        return []
    changes: list[dict[str, object]] = []
    for output_name in sorted(set(from_outputs) | set(to_outputs)):
        from_value = from_outputs.get(output_name)
        to_value = to_outputs.get(output_name)
        if from_value != to_value:
            changes.append({"output_name": output_name, "from": from_value, "to": to_value})
    return changes


def _studies_affected_by_release(*, workspace_root: Path, family_id: str, version_id: str) -> tuple[list[str], list[str]]:
    studies_root = workspace_root / "studies"
    releases = scan_private_releases(workspace_root)
    release_index = _release_index(releases)
    dataset_version_index = _release_index_by_dataset_version(releases)
    affected_studies: list[str] = []
    affected_dataset_ids: list[str] = []
    for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()) if studies_root.exists() else []:
        dataset_inputs_path = _study_dataset_inputs_path(study_root)
        if dataset_inputs_path is None:
            continue
        matched = False
        for item in _load_dataset_inputs(dataset_inputs_path):
            dataset_id, _, item_family_id, item_version_id, _ = _resolve_dataset_binding(
                item=item,
                release_index=release_index,
                dataset_version_index=dataset_version_index,
            )
            if item_family_id == family_id and item_version_id == version_id:
                matched = True
                if dataset_id and dataset_id not in affected_dataset_ids:
                    affected_dataset_ids.append(dataset_id)
        if matched:
            affected_studies.append(study_root.name)
    return affected_studies, affected_dataset_ids


def build_private_release_diff(*, workspace_root: Path, family_id: str, from_version: str, to_version: str) -> dict[str, object]:
    from_root = _find_release_root(workspace_root=workspace_root, family_id=family_id, version_id=from_version)
    to_root = _find_release_root(workspace_root=workspace_root, family_id=family_id, version_id=to_version)
    from_release = build_private_release(workspace_root=workspace_root, family_id=family_id, version_root=from_root)
    to_release = build_private_release(workspace_root=workspace_root, family_id=family_id, version_root=to_root)
    from_inventory = _release_inventory_map(from_root)
    to_inventory = _release_inventory_map(to_root)
    added_files = sorted(path for path in to_inventory if path not in from_inventory)
    removed_files = sorted(path for path in from_inventory if path not in to_inventory)
    resized_files = sorted(
        path
        for path in (set(from_inventory) & set(to_inventory))
        if from_inventory[path]["size_bytes"] != to_inventory[path]["size_bytes"]
    )
    affected_studies, affected_dataset_ids = _studies_affected_by_release(
        workspace_root=workspace_root,
        family_id=family_id,
        version_id=from_version,
    )
    report_path = private_diff_report_path(
        workspace_root=workspace_root,
        family_id=family_id,
        from_version=from_version,
        to_version=to_version,
    )
    report = {
        "schema_version": PRIVATE_DIFF_REPORT_SCHEMA_VERSION,
        "workspace_root": str(workspace_root),
        "family_id": family_id,
        "from_version": from_version,
        "to_version": to_version,
        "report_path": str(report_path),
        "from_release": _release_snapshot_for_report(from_release),
        "to_release": _release_snapshot_for_report(to_release),
        "summary": {
            "inventory": {
                "from_file_count": from_release["inventory_summary"]["file_count"],
                "to_file_count": to_release["inventory_summary"]["file_count"],
                "added_files": added_files,
                "removed_files": removed_files,
                "resized_files": resized_files,
            },
            "contract": {"changed_fields": _contract_changes(from_release, to_release)},
            "main_outputs": {"changed_outputs": _main_output_changes(from_release, to_release)},
            "study_impact": {
                "affected_studies": affected_studies,
                "affected_dataset_ids": affected_dataset_ids,
            },
        },
    }
    _write_json(report_path, report)
    return report


def init_data_assets(*, workspace_root: Path) -> dict[str, object]:
    private_root(workspace_root).mkdir(parents=True, exist_ok=True)
    public_root(workspace_root).mkdir(parents=True, exist_ok=True)
    impact_root(workspace_root).mkdir(parents=True, exist_ok=True)
    lineage_root(workspace_root).mkdir(parents=True, exist_ok=True)
    private_diffs_root(workspace_root).mkdir(parents=True, exist_ok=True)

    releases = scan_private_releases(workspace_root)
    layout_validation = dataset_layout_validation(workspace_root)
    refs_payload = manifest_refs_payload(workspace_root=workspace_root, releases=releases)
    private_payload = {
        "schema_version": PRIVATE_REGISTRY_SCHEMA_VERSION,
        "layout_contract": data_asset_layout_contract(workspace_root),
        "layout_validation": layout_validation,
        "manifest_refs_ref": workspace_ref(workspace_root=workspace_root, path=manifest_refs_path(workspace_root)),
        "releases": releases,
    }
    _write_json(private_registry_path(workspace_root), private_payload)
    _write_json(manifest_refs_path(workspace_root), refs_payload)

    public_path = public_registry_path(workspace_root)
    public_payload = load_public_registry(workspace_root)
    _write_json(public_path, public_payload)

    impact_path = impact_report_path(workspace_root)
    return {
        "workspace_root": str(workspace_root),
        "layout_contract": private_payload["layout_contract"],
        "layout_validation": layout_validation,
        "private": {
            "registry_path": str(private_registry_path(workspace_root)),
            "release_count": len(private_payload["releases"]),
            "diff_root": str(private_diffs_root(workspace_root)),
            "diff_count": _private_diff_count(workspace_root),
        },
        "public": {
            "registry_path": str(public_path),
            "discovery": public_payload["discovery"],
            "dataset_count": len(public_payload["datasets"]),
            "valid_dataset_count": sum(
                1 for item in public_payload["datasets"] if item.get("validation", {}).get("is_valid")
            ),
            "invalid_dataset_count": sum(
                1 for item in public_payload["datasets"] if not item.get("validation", {}).get("is_valid")
            ),
        },
        "impact": {
            "report_path": str(impact_path),
            "report_exists": impact_path.exists(),
        },
        "lineage": {
            "root": str(lineage_root(workspace_root)),
            "manifest_refs_path": str(manifest_refs_path(workspace_root)),
            "manifest_ref_count": len(refs_payload["entries"]),
            "refs_only": True,
            "contains_dataset_body": False,
            "rebuildable_projection": True,
            "validation": refs_payload["validation"],
        },
    }


def rebuild_manifest_refs(*, workspace_root: Path) -> dict[str, object]:
    releases = scan_private_releases(workspace_root)
    refs_payload = manifest_refs_payload(workspace_root=workspace_root, releases=releases)
    path = manifest_refs_path(workspace_root)
    _write_json(path, refs_payload)
    return {
        "workspace_root": str(workspace_root),
        "surface_kind": "mas_data_asset_manifest_refs_rebuild",
        "status": "rebuilt" if refs_payload["validation"]["is_valid"] else "rebuilt_with_invalid_entries",
        "manifest_refs_path": str(path),
        "manifest_ref_count": len(refs_payload["entries"]),
        "refs_only": True,
        "contains_dataset_body": False,
        "rebuildable_projection": True,
        "validation": refs_payload["validation"],
    }


def data_assets_status(*, workspace_root: Path) -> dict[str, object]:
    private_path = private_registry_path(workspace_root)
    public_path = public_registry_path(workspace_root)
    impact_path = impact_report_path(workspace_root)
    private_payload = _load_json(private_path, default={"schema_version": 1, "releases": []})
    public_payload = load_public_registry(workspace_root)
    layout_validation = dataset_layout_validation(workspace_root)
    layout_contract = data_asset_layout_contract(workspace_root)
    refs_path = manifest_refs_path(workspace_root)
    refs_payload = _load_json(
        refs_path,
        default=manifest_refs_payload(
            workspace_root=workspace_root,
            releases=[item for item in private_payload.get("releases", []) if isinstance(item, dict)],
        ),
    )
    return {
        "workspace_root": str(workspace_root),
        "layout_ready": private_path.exists() and public_path.exists(),
        "layout_contract": layout_contract,
        "layout_validation": layout_validation,
        "retention": {
            "dataset_body_plane_ref": DATASETS_RELPATH.as_posix(),
            "dataset_body_is_runtime_residue": False,
            "excluded_from_runtime_residue_cleanup": True,
        },
        "read_model": {
            "sqlite_role": "refs_only_rebuildable",
            "stores_artifact_or_dataset_body": False,
            "authority": "projection_only",
        },
        "study_binding": {
            "plane": "studies/<study-id>/study.yaml",
            "binding_policy": "asset_refs_only",
            "body_storage_allowed": False,
        },
        "private": {
            "registry_path": str(private_path),
            "registry_exists": private_path.exists(),
            "release_count": len(private_payload["releases"]),
            "schema_version": private_payload.get("schema_version"),
            "diff_root": str(private_diffs_root(workspace_root)),
            "diff_count": _private_diff_count(workspace_root),
        },
        "public": {
            "registry_path": str(public_path),
            "registry_exists": public_path.exists(),
            "dataset_count": len(public_payload["datasets"]),
            "schema_version": public_payload["schema_version"],
            "discovery": public_payload["discovery"],
            "valid_dataset_count": sum(
                1 for item in public_payload["datasets"] if item.get("validation", {}).get("is_valid")
            ),
            "invalid_dataset_count": sum(
                1 for item in public_payload["datasets"] if not item.get("validation", {}).get("is_valid")
            ),
        },
        "impact": {
            "report_path": str(impact_path),
            "report_exists": impact_path.exists(),
        },
        "lineage": {
            "root": str(lineage_root(workspace_root)),
            "manifest_refs_path": str(refs_path),
            "manifest_refs_exists": refs_path.exists(),
            "manifest_ref_count": len(refs_payload.get("entries", [])),
            "refs_only": True,
            "contains_dataset_body": False,
            "rebuildable_projection": True,
            "validation": refs_payload.get("validation", {}),
        },
    }


def _extract_family_version(path_text: str | None) -> tuple[str | None, str | None]:
    if not path_text:
        return None, None
    parts = Path(path_text).parts
    try:
        index = parts.index("datasets")
    except ValueError:
        return None, None
    if len(parts) <= index + 2:
        return None, None
    return parts[index + 1], parts[index + 2]


def _latest_versions_by_family(releases: list[dict[str, object]]) -> dict[str, str]:
    latest: dict[str, str] = {}
    superseded_by_family: dict[str, set[str]] = {}
    for release in releases:
        family_id = str(release["family_id"])
        superseded_by_family.setdefault(family_id, set()).update(_normalize_string_list(release.get("supersedes_versions")))
    for release in releases:
        family_id = str(release["family_id"])
        version_id = str(release["version_id"])
        if version_id in superseded_by_family.get(family_id, set()):
            continue
        if family_id not in latest or version_id > latest[family_id]:
            latest[family_id] = version_id
    fallback_latest: dict[str, str] = {}
    for release in releases:
        family_id = str(release["family_id"])
        version_id = str(release["version_id"])
        if family_id not in latest and (family_id not in fallback_latest or version_id > fallback_latest[family_id]):
            fallback_latest[family_id] = version_id
    latest.update(fallback_latest)
    return latest


def _release_index(releases: list[dict[str, object]]) -> dict[tuple[str, str], dict[str, object]]:
    index: dict[tuple[str, str], dict[str, object]] = {}
    for release in releases:
        family_id = release.get("family_id")
        version_id = release.get("version_id")
        if isinstance(family_id, str) and isinstance(version_id, str):
            index[(family_id, version_id)] = release
    return index


def _release_index_by_dataset_version(
    releases: list[dict[str, object]],
) -> dict[tuple[str, str], list[dict[str, object]]]:
    index: dict[tuple[str, str], list[dict[str, object]]] = {}
    for release in releases:
        dataset_id = release.get("dataset_id")
        version_id = release.get("version_id")
        if isinstance(dataset_id, str) and isinstance(version_id, str):
            index.setdefault((dataset_id, version_id), []).append(release)
    return index


def _resolve_dataset_binding(
    *,
    item: dict[str, object],
    release_index: dict[tuple[str, str], dict[str, object]],
    dataset_version_index: dict[tuple[str, str], list[dict[str, object]]],
) -> tuple[str, str, str | None, str | None, dict[str, object] | None]:
    dataset_id = str(item.get("dataset_id", ""))
    source_path = str(item.get("path", ""))
    family_id, version_id = _extract_family_version(source_path)
    manifest_version = item.get("version")
    if isinstance(manifest_version, str) and manifest_version:
        version_id = manifest_version
    if family_id is None and dataset_id and isinstance(version_id, str):
        matches = dataset_version_index.get((dataset_id, version_id), [])
        resolved_families = {
            str(release.get("family_id"))
            for release in matches
            if isinstance(release.get("family_id"), str) and str(release.get("family_id")).strip()
        }
        if len(resolved_families) == 1:
            family_id = next(iter(resolved_families))
    bound_release = (
        release_index.get((family_id, version_id))
        if isinstance(family_id, str) and isinstance(version_id, str)
        else None
    )
    return dataset_id, source_path, family_id, version_id, bound_release


def _load_dataset_inputs(path: Path) -> list[dict[str, object]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    dataset_inputs = payload.get("dataset_inputs")
    if dataset_inputs is None:
        dataset_inputs = payload.get("locked_inputs", [])
    if not isinstance(dataset_inputs, list):
        return []
    return [item for item in dataset_inputs if isinstance(item, dict)]


def _study_versions_by_family(
    resolved_inputs: list[tuple[dict[str, object], str, str, str | None, str | None, dict[str, object] | None]],
) -> dict[str, set[str]]:
    versions_by_family: dict[str, set[str]] = {}
    for _, _, _, family_id, version_id, _ in resolved_inputs:
        if isinstance(family_id, str) and isinstance(version_id, str):
            versions_by_family.setdefault(family_id, set()).add(version_id)
    return versions_by_family


def _is_historical_comparator_release(
    *,
    family_id: str | None,
    version_id: str | None,
    latest_version: str | None,
    study_versions_by_family: dict[str, set[str]],
) -> bool:
    if not isinstance(family_id, str) or not isinstance(version_id, str) or not isinstance(latest_version, str):
        return False
    return latest_version != version_id and latest_version in study_versions_by_family.get(family_id, set())


def _study_dataset_inputs_path(study_root: Path) -> Path | None:
    manifest_path = study_root / "data_input" / "dataset_manifest.yaml"
    if manifest_path.exists():
        return manifest_path
    study_yaml_path = study_root / "study.yaml"
    if study_yaml_path.exists():
        return study_yaml_path
    return None


def assess_data_asset_impact(*, workspace_root: Path) -> dict[str, object]:
    init_data_assets(workspace_root=workspace_root)
    private_payload = _load_json(private_registry_path(workspace_root), default={"schema_version": 1, "releases": []})
    public_payload = load_public_registry(workspace_root)
    latest_versions = _latest_versions_by_family(private_payload["releases"])
    release_index = _release_index(private_payload["releases"])
    dataset_version_index = _release_index_by_dataset_version(private_payload["releases"])
    diff_cache: dict[tuple[str, str, str], dict[str, object]] = {}

    studies_root = workspace_root / "studies"
    study_reports: list[dict[str, object]] = []
    for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()) if studies_root.exists() else []:
        dataset_inputs_path = _study_dataset_inputs_path(study_root)
        if dataset_inputs_path is None:
            continue
        resolved_inputs: list[
            tuple[dict[str, object], str, str, str | None, str | None, dict[str, object] | None]
        ] = []
        for item in _load_dataset_inputs(dataset_inputs_path):
            dataset_id, source_path, family_id, version_id, bound_release = _resolve_dataset_binding(
                item=item,
                release_index=release_index,
                dataset_version_index=dataset_version_index,
            )
            resolved_inputs.append((item, dataset_id, source_path, family_id, version_id, bound_release))
        study_versions_by_family = _study_versions_by_family(resolved_inputs)
        dataset_reports: list[dict[str, object]] = []
        overall_status = "clear"
        for item, dataset_id, source_path, family_id, version_id, bound_release in resolved_inputs:
            latest_version = latest_versions.get(family_id) if family_id is not None else None
            public_registry_backed = item.get("source") == "portfolio_public_registry"
            historical_comparator = _is_historical_comparator_release(
                family_id=family_id,
                version_id=version_id,
                latest_version=latest_version,
                study_versions_by_family=study_versions_by_family,
            )
            private_status = _impact_assessment.private_version_status(
                public_registry_backed=public_registry_backed,
                family_id=family_id,
                version_id=version_id,
                latest_version=latest_version,
                historical_comparator=historical_comparator,
            )
            private_contract_status = _impact_assessment.private_contract_status(
                public_registry_backed=public_registry_backed,
                family_id=family_id,
                version_id=version_id,
                bound_release=bound_release,
            )
            upgrade_diff_report_path, upgrade_diff_report_exists = _impact_assessment.upgrade_diff_summary(
                workspace_root=workspace_root,
                family_id=family_id,
                version_id=version_id,
                latest_version=latest_version,
                private_status=private_status,
                diff_cache=diff_cache,
                build_private_release_diff=build_private_release_diff,
            )
            public_matches = _impact_assessment.matching_public_datasets(
                public_payload=public_payload,
                dataset_id=dataset_id,
                family_id=family_id,
            )
            dataset_report, review_needed = _impact_assessment.dataset_asset_impact_report(
                dataset_id=dataset_id,
                source_path=source_path,
                family_id=family_id,
                version_id=version_id,
                bound_release=bound_release,
                latest_version=latest_version,
                private_status=private_status,
                private_contract_status=private_contract_status,
                upgrade_diff_report_path=upgrade_diff_report_path,
                upgrade_diff_report_exists=upgrade_diff_report_exists,
                public_matches=public_matches,
            )
            if review_needed:
                overall_status = "review_needed"
            dataset_reports.append(dataset_report)
        study_reports.append({"study_id": study_root.name, "status": overall_status, "dataset_inputs": dataset_reports})

    report = {"workspace_root": str(workspace_root), "study_count": len(study_reports), "studies": study_reports}
    _write_json(impact_report_path(workspace_root), report)
    return report


def _release_selector(*, workspace_root: Path, family_id: str, version_id: str) -> dict[str, object]:
    for release in scan_private_releases(workspace_root):
        if release.get("family_id") == family_id and release.get("version_id") == version_id:
            return release
    raise FileNotFoundError(f"Private release not found: {family_id}/{version_id}")


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _release_body_manifest(*, release_root: Path) -> dict[str, object]:
    entries: list[dict[str, object]] = []
    aggregate = hashlib.sha256()
    for path in list_release_files(release_root):
        relative = path.relative_to(release_root).as_posix()
        sha256 = _sha256_file(path)
        size = path.stat().st_size
        entries.append({"path": relative, "bytes": size, "sha256": sha256})
        aggregate.update(relative.encode("utf-8"))
        aggregate.update(str(size).encode("utf-8"))
        aggregate.update(sha256.encode("utf-8"))
    return {
        "file_count": len(entries),
        "total_size_bytes": sum(int(item["bytes"]) for item in entries),
        "aggregate_sha256": aggregate.hexdigest(),
        "entries": entries,
    }


def data_asset_retention_plan(
    *,
    workspace_root: Path,
    family_id: str,
    version_id: str,
    owner_authorization_ref: str | None = None,
    cold_ref: str | None = None,
    restore_proof_ref: str | None = None,
    apply: bool = False,
) -> dict[str, object]:
    release = _release_selector(workspace_root=workspace_root, family_id=family_id, version_id=version_id)
    release_root = Path(str(release["data_root"]))
    manifest_path = release_root / "dataset_manifest.yaml"
    body_manifest = _release_body_manifest(release_root=release_root)
    affected_studies, affected_dataset_ids = _studies_affected_by_release(
        workspace_root=workspace_root,
        family_id=family_id,
        version_id=version_id,
    )
    blockers: list[str] = []
    if not manifest_path.exists():
        blockers.append("missing_dataset_manifest")
    if not owner_authorization_ref:
        blockers.append("missing_owner_authorization_ref")
    if not cold_ref:
        blockers.append("missing_cold_ref")
    if not restore_proof_ref:
        blockers.append("missing_restore_proof_ref")
    status = "ready_to_record_retention_receipt" if not blockers else "blocked"
    receipt_path = (
        data_assets_root_path(workspace_root)
        / "retention"
        / family_id
        / version_id
        / "latest.json"
    )
    payload = {
        "schema_version": 1,
        "surface_kind": "mas_data_asset_retention_plan",
        "workspace_root": str(workspace_root),
        "family_id": family_id,
        "version_id": version_id,
        "dataset_id": release.get("dataset_id"),
        "status": status,
        "apply": bool(apply),
        "receipt_path": str(receipt_path),
        "body_plane": {
            "release_root_ref": release.get("data_root_ref"),
            "dataset_body_is_runtime_residue": False,
            "generic_runtime_cleanup_allowed": False,
            "physical_delete_allowed": False,
        },
        "contract": {
            "manifest_ref": release.get("manifest_ref"),
            "manifest_sha256": _sha256_file(manifest_path) if manifest_path.exists() else None,
            "body_manifest": body_manifest,
        },
        "cold_store": {
            "cold_ref": cold_ref,
            "restore_proof_ref": restore_proof_ref,
            "byte_for_byte_restore_required_for_body_retirement": True,
        },
        "study_impact": {
            "affected_studies": affected_studies,
            "affected_dataset_ids": affected_dataset_ids,
            "study_impact_review_required": bool(affected_studies),
        },
        "owner_authorization_ref": owner_authorization_ref,
        "blockers": blockers,
    }
    if apply and blockers:
        payload["status"] = "blocked_receipt_not_recorded"
    elif apply:
        payload["status"] = "retention_receipt_recorded_no_body_delete"
        _write_json(receipt_path, payload)
    return payload


def _sqlite_integrity_check(db_path: Path) -> dict[str, object]:
    try:
        with sqlite3.connect(f"file:{db_path.as_posix()}?mode=ro", uri=True) as conn:
            value = conn.execute("PRAGMA integrity_check").fetchone()[0]
    except sqlite3.Error as exc:
        return {"status": "error", "error": str(exc)}
    return {"status": "ok" if value == "ok" else "failed", "result": value}


def data_asset_sqlite_compact_plan(*, workspace_root: Path, db_path: Path) -> dict[str, object]:
    resolved_workspace = workspace_root.expanduser().resolve()
    resolved_db = db_path.expanduser().resolve()
    datasets = datasets_root(resolved_workspace).resolve()
    try:
        relative_db = resolved_db.relative_to(resolved_workspace).as_posix()
    except ValueError:
        relative_db = resolved_db.as_posix()
    under_dataset_body = False
    try:
        resolved_db.relative_to(datasets)
        under_dataset_body = True
    except ValueError:
        under_dataset_body = False
    if not resolved_db.exists():
        return {
            "surface_kind": "mas_data_asset_sqlite_compact_plan",
            "status": "blocked_missing_db",
            "workspace_root": str(workspace_root),
            "db_path": str(db_path),
            "db_ref": relative_db,
        }
    integrity = _sqlite_integrity_check(resolved_db)
    blockers: list[str] = []
    if integrity.get("status") != "ok":
        blockers.append("sqlite_integrity_check_failed")
    if under_dataset_body:
        blockers.append("dataset_body_sqlite_requires_dataset_manifest_retention_policy")
    return {
        "surface_kind": "mas_data_asset_sqlite_compact_plan",
        "status": "blocked" if blockers else "eligible_for_runtime_sqlite_compact_surface",
        "workspace_root": str(workspace_root),
        "db_path": str(db_path),
        "db_ref": relative_db,
        "under_dataset_body": under_dataset_body,
        "integrity_check": integrity,
        "blockers": blockers,
        "dataset_body_compact_boundary": {
            "generic_sqlite_compact_allowed": not under_dataset_body,
            "dataset_release_sqlite_is_body_or_release_sidecar": under_dataset_body,
            "required_owner_surface": "dataset_manifest_retention_policy" if under_dataset_body else None,
        },
        "recommended_command": (
            None
            if under_dataset_body or blockers
            else f"medautosci runtime-lifecycle-payload-retention --db {resolved_db} --compact --apply"
        ),
    }


__all__ = [
    "DATA_ASSET_LAYOUT_CONTRACT_SCHEMA_VERSION",
    "DATA_ASSET_MANIFEST_REFS_SCHEMA_VERSION",
    "ALLOWED_DATASET_LAYERS",
    "DATA_ASSET_LAYER_IDS",
    "PRIVATE_REGISTRY_SCHEMA_VERSION",
    "PUBLIC_DATASET_ALLOWED_ROLES",
    "PUBLIC_DATASET_ALLOWED_STATUSES",
    "PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES",
    "PUBLIC_REGISTRY_SCHEMA_VERSION",
    "assess_data_asset_impact",
    "build_private_release_diff",
    "data_asset_retention_plan",
    "data_asset_sqlite_compact_plan",
    "data_assets_status",
    "init_data_assets",
    "rebuild_manifest_refs",
    "validate_public_registry",
]
