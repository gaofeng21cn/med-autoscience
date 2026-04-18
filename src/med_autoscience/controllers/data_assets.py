from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

import yaml


PRIVATE_REGISTRY_BASENAME = "registry.json"
PUBLIC_REGISTRY_BASENAME = "registry.json"
IMPACT_REPORT_BASENAME = "latest_impact_report.json"
PRIVATE_DIFF_REPORT_SCHEMA_VERSION = 1
PUBLIC_REGISTRY_SCHEMA_VERSION = 2
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


def _data_assets_root(workspace_root: Path) -> Path:
    return workspace_root / "portfolio" / "data_assets"


def _private_root(workspace_root: Path) -> Path:
    return _data_assets_root(workspace_root) / "private"


def _public_root(workspace_root: Path) -> Path:
    return _data_assets_root(workspace_root) / "public"


def _impact_root(workspace_root: Path) -> Path:
    return _data_assets_root(workspace_root) / "impact"


def _private_registry_path(workspace_root: Path) -> Path:
    return _private_root(workspace_root) / PRIVATE_REGISTRY_BASENAME


def _private_diffs_root(workspace_root: Path) -> Path:
    return _private_root(workspace_root) / "diffs"


def _public_registry_path(workspace_root: Path) -> Path:
    return _public_root(workspace_root) / PUBLIC_REGISTRY_BASENAME


def _impact_report_path(workspace_root: Path) -> Path:
    return _impact_root(workspace_root) / IMPACT_REPORT_BASENAME


def _private_diff_report_path(*, workspace_root: Path, family_id: str, from_version: str, to_version: str) -> Path:
    return _private_diffs_root(workspace_root) / family_id / f"{from_version}__{to_version}.json"


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    temp_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as handle:
            temp_name = handle.name
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        Path(temp_name).replace(path)
    finally:
        if temp_name is not None:
            Path(temp_name).unlink(missing_ok=True)


def _load_json(path: Path, *, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _load_yaml_dict(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return payload if isinstance(payload, dict) else {}


def _normalize_string_map(value: object) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    normalized: dict[str, str] = {}
    for key, item in value.items():
        if isinstance(key, str) and isinstance(item, str):
            normalized[key] = item
    return normalized


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    normalized: list[str] = []
    for item in value:
        if isinstance(item, str):
            normalized.append(item)
    return normalized


def _normalize_dict(value: object) -> dict[str, object]:
    return value if isinstance(value, dict) else {}


def _normalize_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    return None


def _list_release_files(version_root: Path) -> list[Path]:
    return sorted(path for path in version_root.rglob("*") if path.is_file())


def _inventory_summary(*, version_root: Path, main_outputs: dict[str, str]) -> dict[str, object]:
    files = _list_release_files(version_root)
    declared_outputs_present = {output_name: (version_root / relative_path).exists() for output_name, relative_path in main_outputs.items()}
    return {
        "file_count": len(files),
        "total_size_bytes": sum(path.stat().st_size for path in files),
        "declared_outputs_present": declared_outputs_present,
    }


def _build_private_release(*, family_id: str, version_root: Path) -> dict[str, object]:
    manifest_path = version_root / "dataset_manifest.yaml"
    manifest = _load_yaml_dict(manifest_path)
    main_outputs = _normalize_string_map(manifest.get("main_outputs"))
    notes = _normalize_string_list(manifest.get("notes"))
    dataset_id = manifest.get("dataset_id") if isinstance(manifest.get("dataset_id"), str) else None
    raw_snapshot = manifest.get("raw_snapshot") if isinstance(manifest.get("raw_snapshot"), str) else None
    generated_by = manifest.get("generated_by") if isinstance(manifest.get("generated_by"), str) else None
    declared_release_contract = _normalize_dict(manifest.get("release_contract"))
    inventory_summary = _inventory_summary(version_root=version_root, main_outputs=main_outputs)
    return {
        "family_id": family_id,
        "version_id": version_root.name,
        "dataset_id": dataset_id,
        "data_root": str(version_root),
        "manifest_path": str(manifest_path) if manifest_path.exists() else None,
        "contract_status": "manifest_backed" if manifest_path.exists() else "directory_scan_only",
        "raw_snapshot": raw_snapshot,
        "generated_by": generated_by,
        "main_outputs": main_outputs,
        "notes": notes,
        "declared_release_contract": declared_release_contract,
        "inventory_summary": inventory_summary,
        "file_count": inventory_summary["file_count"],
    }


def _scan_private_releases(workspace_root: Path) -> list[dict[str, object]]:
    datasets_root = workspace_root / "datasets"
    if not datasets_root.exists():
        return []

    releases: list[dict[str, object]] = []
    for family_root in sorted(path for path in datasets_root.iterdir() if path.is_dir()):
        for version_root in sorted(path for path in family_root.iterdir() if path.is_dir() and path.name.startswith("v")):
            releases.append(_build_private_release(family_id=family_root.name, version_root=version_root))
    return releases


def _normalize_public_dataset_entry(item: object) -> dict[str, object]:
    payload = _normalize_dict(item)
    roles = [role for role in _normalize_string_list(payload.get("roles")) if role in PUBLIC_DATASET_ALLOWED_ROLES]
    status = payload.get("status") if isinstance(payload.get("status"), str) else "candidate"
    normalized = {
        "dataset_id": payload.get("dataset_id") if isinstance(payload.get("dataset_id"), str) else None,
        "source_type": payload.get("source_type") if isinstance(payload.get("source_type"), str) else None,
        "accession": payload.get("accession") if isinstance(payload.get("accession"), str) else None,
        "disease": payload.get("disease") if isinstance(payload.get("disease"), str) else None,
        "modality": _normalize_string_list(payload.get("modality")),
        "endpoints": _normalize_string_list(payload.get("endpoints")),
        "roles": roles,
        "target_families": _normalize_string_list(payload.get("target_families")),
        "target_dataset_ids": _normalize_string_list(payload.get("target_dataset_ids")),
        "target_study_archetypes": _normalize_string_list(payload.get("target_study_archetypes")),
        "cohort_size": _normalize_int(payload.get("cohort_size")),
        "license": payload.get("license") if isinstance(payload.get("license"), str) else None,
        "access_url": payload.get("access_url") if isinstance(payload.get("access_url"), str) else None,
        "status": status if status in PUBLIC_DATASET_ALLOWED_STATUSES else "candidate",
        "rationale": payload.get("rationale") if isinstance(payload.get("rationale"), str) else None,
        "notes": _normalize_string_list(payload.get("notes")),
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


def _normalize_public_registry_discovery(value: object) -> dict[str, object]:
    payload = _normalize_dict(value)
    status = payload.get("status") if isinstance(payload.get("status"), str) else "not_started"
    last_scouted_on = payload.get("last_scouted_on") if isinstance(payload.get("last_scouted_on"), str) else None
    scope = payload.get("scope") if isinstance(payload.get("scope"), str) and payload.get("scope").strip() else "route_selection"
    return {
        "status": status if status in PUBLIC_DATASET_DISCOVERY_ALLOWED_STATUSES else "not_started",
        "last_scouted_on": last_scouted_on,
        "scope": scope,
        "notes": _normalize_string_list(payload.get("notes")),
    }


def _normalize_public_registry_payload(payload: dict) -> dict[str, object]:
    datasets_value = payload.get("datasets")
    datasets: list[dict[str, object]] = []
    if isinstance(datasets_value, list):
        datasets = [_normalize_public_dataset_entry(item) for item in datasets_value]
    return {
        "schema_version": PUBLIC_REGISTRY_SCHEMA_VERSION,
        "discovery": _normalize_public_registry_discovery(payload.get("discovery")),
        "datasets": datasets,
    }


def _load_public_registry(workspace_root: Path) -> dict[str, object]:
    public_path = _public_registry_path(workspace_root)
    payload = _load_json(
        public_path,
        default={
            "schema_version": PUBLIC_REGISTRY_SCHEMA_VERSION,
            "discovery": _normalize_public_registry_discovery({}),
            "datasets": [],
        },
    )
    normalized = _normalize_public_registry_payload(payload)
    if payload != normalized:
        _write_json(public_path, normalized)
    return normalized


def validate_public_registry(*, workspace_root: Path) -> dict[str, object]:
    payload = _load_public_registry(workspace_root)
    datasets = payload["datasets"]
    assert isinstance(datasets, list)
    valid_dataset_count = sum(1 for item in datasets if isinstance(item, dict) and item.get("validation", {}).get("is_valid"))
    invalid_dataset_count = len(datasets) - valid_dataset_count
    return {
        "schema_version": PUBLIC_REGISTRY_SCHEMA_VERSION,
        "workspace_root": str(workspace_root),
        "registry_path": str(_public_registry_path(workspace_root)),
        "discovery": payload["discovery"],
        "dataset_count": len(datasets),
        "valid_dataset_count": valid_dataset_count,
        "invalid_dataset_count": invalid_dataset_count,
        "datasets": datasets,
    }


def _private_diff_count(workspace_root: Path) -> int:
    diffs_root = _private_diffs_root(workspace_root)
    if not diffs_root.exists():
        return 0
    return sum(1 for path in diffs_root.rglob("*.json") if path.is_file())


def _find_release_root(*, workspace_root: Path, family_id: str, version_id: str) -> Path:
    release_root = workspace_root / "datasets" / family_id / version_id
    if not release_root.exists():
        raise FileNotFoundError(f"Private release not found: {family_id}/{version_id}")
    return release_root


def _release_snapshot_for_report(release: dict[str, object]) -> dict[str, object]:
    return {
        "family_id": release["family_id"],
        "version_id": release["version_id"],
        "dataset_id": release.get("dataset_id"),
        "raw_snapshot": release.get("raw_snapshot"),
        "generated_by": release.get("generated_by"),
        "main_outputs": release.get("main_outputs", {}),
        "notes": release.get("notes", []),
        "declared_release_contract": release.get("declared_release_contract", {}),
        "inventory_summary": release.get("inventory_summary", {}),
    }


def _release_inventory_map(version_root: Path) -> dict[str, dict[str, int]]:
    inventory: dict[str, dict[str, int]] = {}
    for path in _list_release_files(version_root):
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
    releases = _scan_private_releases(workspace_root)
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
    from_release = _build_private_release(family_id=family_id, version_root=from_root)
    to_release = _build_private_release(family_id=family_id, version_root=to_root)
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
    report_path = _private_diff_report_path(
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
            "contract": {
                "changed_fields": _contract_changes(from_release, to_release),
            },
            "main_outputs": {
                "changed_outputs": _main_output_changes(from_release, to_release),
            },
            "study_impact": {
                "affected_studies": affected_studies,
                "affected_dataset_ids": affected_dataset_ids,
            },
        },
    }
    _write_json(report_path, report)
    return report


def init_data_assets(*, workspace_root: Path) -> dict[str, object]:
    private_root = _private_root(workspace_root)
    public_root = _public_root(workspace_root)
    impact_root = _impact_root(workspace_root)
    private_diffs_root = _private_diffs_root(workspace_root)
    private_root.mkdir(parents=True, exist_ok=True)
    public_root.mkdir(parents=True, exist_ok=True)
    impact_root.mkdir(parents=True, exist_ok=True)
    private_diffs_root.mkdir(parents=True, exist_ok=True)

    private_payload = {
        "schema_version": 2,
        "releases": _scan_private_releases(workspace_root),
    }
    _write_json(_private_registry_path(workspace_root), private_payload)

    public_path = _public_registry_path(workspace_root)
    public_payload = _load_public_registry(workspace_root)
    _write_json(public_path, public_payload)

    impact_path = _impact_report_path(workspace_root)
    return {
        "workspace_root": str(workspace_root),
        "private": {
            "registry_path": str(_private_registry_path(workspace_root)),
            "release_count": len(private_payload["releases"]),
            "diff_root": str(private_diffs_root),
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
    }


def data_assets_status(*, workspace_root: Path) -> dict[str, object]:
    private_path = _private_registry_path(workspace_root)
    public_path = _public_registry_path(workspace_root)
    impact_path = _impact_report_path(workspace_root)
    private_payload = _load_json(private_path, default={"schema_version": 1, "releases": []})
    public_payload = _load_public_registry(workspace_root)
    return {
        "workspace_root": str(workspace_root),
        "layout_ready": private_path.exists() and public_path.exists(),
        "private": {
            "registry_path": str(private_path),
            "registry_exists": private_path.exists(),
            "release_count": len(private_payload["releases"]),
            "diff_root": str(_private_diffs_root(workspace_root)),
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
    for release in releases:
        family_id = str(release["family_id"])
        version_id = str(release["version_id"])
        if family_id not in latest or version_id > latest[family_id]:
            latest[family_id] = version_id
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
    normalized: list[dict[str, object]] = []
    for item in dataset_inputs:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


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
    private_payload = _load_json(_private_registry_path(workspace_root), default={"schema_version": 1, "releases": []})
    public_payload = _load_public_registry(workspace_root)
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
            public_registry_backed = item.get("source") == "portfolio_public_registry"
            latest_version = latest_versions.get(family_id) if family_id is not None else None
            if public_registry_backed:
                private_status = "public_registry_backed"
            elif family_id is None or version_id is None:
                private_status = "unversioned_path"
            elif latest_version is None:
                private_status = "family_not_registered"
            elif latest_version == version_id:
                private_status = "up_to_date"
            elif _is_historical_comparator_release(
                family_id=family_id,
                version_id=version_id,
                latest_version=latest_version,
                study_versions_by_family=study_versions_by_family,
            ):
                private_status = "historical_comparator"
            else:
                private_status = "older_than_latest"
                overall_status = "review_needed"
            if public_registry_backed:
                private_contract_status = "public_registry_backed"
            elif family_id is None or version_id is None:
                private_contract_status = None
            elif bound_release is None:
                private_contract_status = "release_not_registered"
                overall_status = "review_needed"
            else:
                private_contract_status = str(bound_release.get("contract_status") or "directory_scan_only")
                if private_contract_status != "manifest_backed":
                    overall_status = "review_needed"
            upgrade_diff_report_path: str | None = None
            upgrade_diff_report_exists = False
            if (
                family_id is not None
                and version_id is not None
                and latest_version is not None
                and latest_version != version_id
                and private_status == "older_than_latest"
            ):
                cache_key = (family_id, version_id, latest_version)
                diff_report = diff_cache.get(cache_key)
                if diff_report is None:
                    diff_report = build_private_release_diff(
                        workspace_root=workspace_root,
                        family_id=family_id,
                        from_version=version_id,
                        to_version=latest_version,
                    )
                    diff_cache[cache_key] = diff_report
                upgrade_diff_report_path = str(diff_report["report_path"])
                upgrade_diff_report_exists = Path(upgrade_diff_report_path).exists()

            public_matches = [
                dataset
                for dataset in public_payload.get("datasets", [])
                if dataset.get("validation", {}).get("is_valid")
                if dataset.get("status") != "rejected"
                if dataset_id in dataset.get("target_dataset_ids", []) or family_id in dataset.get("target_families", [])
            ]
            if public_matches:
                overall_status = "review_needed"

            dataset_reports.append(
                {
                    "dataset_id": dataset_id,
                    "source_path": source_path,
                    "family_id": family_id,
                    "version_id": version_id,
                    "latest_private_version": latest_version,
                    "private_version_status": private_status,
                    "private_contract_status": private_contract_status,
                    "upgrade_diff_report_path": upgrade_diff_report_path,
                    "upgrade_diff_report_exists": upgrade_diff_report_exists,
                    "public_support_count": len(public_matches),
                    "public_support_dataset_ids": [item.get("dataset_id") for item in public_matches],
                    "public_support_roles": sorted(
                        {
                            role
                            for item in public_matches
                            for role in (item.get("roles") or [])
                            if isinstance(role, str)
                        }
                    ),
                }
            )
        study_reports.append(
            {
                "study_id": study_root.name,
                "status": overall_status,
                "dataset_inputs": dataset_reports,
            }
        )

    report = {
        "workspace_root": str(workspace_root),
        "study_count": len(study_reports),
        "studies": study_reports,
    }
    _write_json(_impact_report_path(workspace_root), report)
    return report
