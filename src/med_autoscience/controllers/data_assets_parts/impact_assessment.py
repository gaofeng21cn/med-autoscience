from __future__ import annotations

from pathlib import Path

from med_autoscience.controllers.data_availability_projection import project_release_data_availability


def private_version_status(
    *,
    public_registry_backed: bool,
    family_id: str | None,
    version_id: str | None,
    latest_version: str | None,
    historical_comparator: bool,
) -> str:
    if public_registry_backed:
        return "public_registry_backed"
    if family_id is None or version_id is None:
        return "unversioned_path"
    if latest_version is None:
        return "family_not_registered"
    if latest_version == version_id:
        return "up_to_date"
    if historical_comparator:
        return "historical_comparator"
    return "older_than_latest"


def private_contract_status(
    *,
    public_registry_backed: bool,
    family_id: str | None,
    version_id: str | None,
    bound_release: dict[str, object] | None,
) -> str | None:
    if public_registry_backed:
        return "public_registry_backed"
    if family_id is None or version_id is None:
        return None
    if bound_release is None:
        return "release_not_registered"
    return str(bound_release.get("contract_status") or "directory_scan_only")


def matching_public_datasets(
    *,
    public_payload: dict[str, object],
    dataset_id: str,
    family_id: str | None,
) -> list[dict[str, object]]:
    return [
        dataset
        for dataset in public_payload.get("datasets", [])
        if isinstance(dataset, dict)
        if dataset.get("validation", {}).get("is_valid")
        if dataset.get("status") != "rejected"
        if dataset_id in dataset.get("target_dataset_ids", []) or family_id in dataset.get("target_families", [])
    ]


def upgrade_diff_summary(
    *,
    workspace_root: Path,
    family_id: str | None,
    version_id: str | None,
    latest_version: str | None,
    private_status: str,
    diff_cache: dict[tuple[str, str, str], dict[str, object]],
    build_private_release_diff,
) -> tuple[str | None, bool]:
    if not (
        family_id is not None
        and version_id is not None
        and latest_version is not None
        and latest_version != version_id
        and private_status == "older_than_latest"
    ):
        return None, False
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
    report_path = str(diff_report["report_path"])
    return report_path, Path(report_path).exists()


def dataset_asset_impact_report(
    *,
    dataset_id: str,
    source_path: str,
    family_id: str | None,
    version_id: str | None,
    bound_release: dict[str, object] | None,
    latest_version: str | None,
    private_status: str,
    private_contract_status: str | None,
    upgrade_diff_report_path: str | None,
    upgrade_diff_report_exists: bool,
    public_matches: list[dict[str, object]],
) -> tuple[dict[str, object], bool]:
    review_needed = (
        private_status == "older_than_latest"
        or private_contract_status in {"release_not_registered", "directory_scan_only"}
        or bool(public_matches)
    )
    return (
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
            "standardization_status": (
                bound_release.get("standardization_status")
                if isinstance(bound_release, dict)
                else None
            ),
            "semantic_readiness": (
                bound_release.get("semantic_readiness")
                if isinstance(bound_release, dict)
                else None
            ),
            "data_availability": project_release_data_availability(
                release=bound_release,
                dataset_id=dataset_id,
                family_id=family_id,
                version_id=version_id,
                source_path=source_path,
            ),
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
        },
        review_needed,
    )
