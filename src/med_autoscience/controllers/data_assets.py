from __future__ import annotations

import json
from pathlib import Path

import yaml


PRIVATE_REGISTRY_BASENAME = "registry.json"
PUBLIC_REGISTRY_BASENAME = "registry.json"
IMPACT_REPORT_BASENAME = "latest_impact_report.json"


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


def _public_registry_path(workspace_root: Path) -> Path:
    return _public_root(workspace_root) / PUBLIC_REGISTRY_BASENAME


def _impact_report_path(workspace_root: Path) -> Path:
    return _impact_root(workspace_root) / IMPACT_REPORT_BASENAME


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _load_json(path: Path, *, default: dict) -> dict:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def _scan_private_releases(workspace_root: Path) -> list[dict[str, object]]:
    datasets_root = workspace_root / "datasets"
    if not datasets_root.exists():
        return []

    releases: list[dict[str, object]] = []
    for family_root in sorted(path for path in datasets_root.iterdir() if path.is_dir()):
        for version_root in sorted(path for path in family_root.iterdir() if path.is_dir() and path.name.startswith("v")):
            file_count = sum(1 for path in version_root.rglob("*") if path.is_file())
            releases.append(
                {
                    "family_id": family_root.name,
                    "version_id": version_root.name,
                    "data_root": str(version_root),
                    "file_count": file_count,
                }
            )
    return releases


def init_data_assets(*, workspace_root: Path) -> dict[str, object]:
    private_root = _private_root(workspace_root)
    public_root = _public_root(workspace_root)
    impact_root = _impact_root(workspace_root)
    private_root.mkdir(parents=True, exist_ok=True)
    public_root.mkdir(parents=True, exist_ok=True)
    impact_root.mkdir(parents=True, exist_ok=True)

    private_payload = {
        "schema_version": 1,
        "releases": _scan_private_releases(workspace_root),
    }
    _write_json(_private_registry_path(workspace_root), private_payload)

    public_path = _public_registry_path(workspace_root)
    public_payload = _load_json(public_path, default={"schema_version": 1, "datasets": []})
    _write_json(public_path, public_payload)

    impact_path = _impact_report_path(workspace_root)
    return {
        "workspace_root": str(workspace_root),
        "private": {
            "registry_path": str(_private_registry_path(workspace_root)),
            "release_count": len(private_payload["releases"]),
        },
        "public": {
            "registry_path": str(public_path),
            "dataset_count": len(public_payload["datasets"]),
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
    public_payload = _load_json(public_path, default={"schema_version": 1, "datasets": []})
    return {
        "workspace_root": str(workspace_root),
        "layout_ready": private_path.exists() and public_path.exists(),
        "private": {
            "registry_path": str(private_path),
            "registry_exists": private_path.exists(),
            "release_count": len(private_payload["releases"]),
        },
        "public": {
            "registry_path": str(public_path),
            "registry_exists": public_path.exists(),
            "dataset_count": len(public_payload["datasets"]),
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


def _load_dataset_inputs(path: Path) -> list[dict[str, object]]:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    dataset_inputs = payload.get("dataset_inputs", [])
    if not isinstance(dataset_inputs, list):
        return []
    normalized: list[dict[str, object]] = []
    for item in dataset_inputs:
        if isinstance(item, dict):
            normalized.append(item)
    return normalized


def assess_data_asset_impact(*, workspace_root: Path) -> dict[str, object]:
    init_data_assets(workspace_root=workspace_root)
    private_payload = _load_json(_private_registry_path(workspace_root), default={"schema_version": 1, "releases": []})
    public_payload = _load_json(_public_registry_path(workspace_root), default={"schema_version": 1, "datasets": []})
    latest_versions = _latest_versions_by_family(private_payload["releases"])

    studies_root = workspace_root / "studies"
    study_reports: list[dict[str, object]] = []
    for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()) if studies_root.exists() else []:
        manifest_path = study_root / "data_input" / "dataset_manifest.yaml"
        if not manifest_path.exists():
            continue
        dataset_reports: list[dict[str, object]] = []
        overall_status = "clear"
        for item in _load_dataset_inputs(manifest_path):
            dataset_id = str(item.get("dataset_id", ""))
            source_path = str(item.get("path", ""))
            family_id, version_id = _extract_family_version(source_path)
            latest_version = latest_versions.get(family_id) if family_id is not None else None
            if family_id is None or version_id is None:
                private_status = "unversioned_path"
            elif latest_version is None:
                private_status = "family_not_registered"
            elif latest_version == version_id:
                private_status = "up_to_date"
            else:
                private_status = "older_than_latest"
                overall_status = "review_needed"

            public_matches = [
                dataset
                for dataset in public_payload.get("datasets", [])
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
                    "public_support_count": len(public_matches),
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
