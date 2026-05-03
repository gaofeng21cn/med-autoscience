from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import data_assets
from med_autoscience.controllers.artifact_lifecycle_inventory import evaluate_archive_cleanup_readiness


def release_restore_handle(release: Mapping[str, Any]) -> str | None:
    source_release = release.get("source_release")
    source_payload = source_release if isinstance(source_release, Mapping) else {}
    release_contract = release.get("declared_release_contract")
    contract_payload = release_contract if isinstance(release_contract, Mapping) else {}
    for payload in (source_payload, contract_payload, release):
        for key in ("restore_handle", "restore_command", "archive_ref", "archive_uri", "external_archive_uri"):
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def release_checksum(release: Mapping[str, Any]) -> str | None:
    source_release = release.get("source_release")
    source_payload = source_release if isinstance(source_release, Mapping) else {}
    release_contract = release.get("declared_release_contract")
    contract_payload = release_contract if isinstance(release_contract, Mapping) else {}
    for payload in (source_payload, contract_payload, release):
        for key in ("sha256", "checksum", "manifest_sha256", "archive_sha256"):
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if isinstance(value, str) and value.strip():
                return value.strip()
    return None


def release_rehydrate_verification(release: Mapping[str, Any]) -> Mapping[str, Any] | str | None:
    source_release = release.get("source_release")
    source_payload = source_release if isinstance(source_release, Mapping) else {}
    release_contract = release.get("declared_release_contract")
    contract_payload = release_contract if isinstance(release_contract, Mapping) else {}
    for payload in (source_payload, contract_payload, release):
        for key in ("rehydrate_verification", "restore_verification", "rehydrate_verification_status"):
            value = payload.get(key) if isinstance(payload, Mapping) else None
            if isinstance(value, Mapping) or (isinstance(value, str) and value.strip()):
                return value
    return None


def audit_dataset_retention(workspace_root: Path) -> dict[str, Any]:
    releases = data_assets._scan_private_releases(workspace_root)
    superseded_by = superseded_release_index(releases)
    release_reports: list[dict[str, Any]] = []
    totals = {
        "total_bytes": 0,
        "keep_online_bytes": 0,
        "archive_offline_candidate_bytes": 0,
        "blocked_bytes": 0,
    }
    for release in releases:
        family_id = str(release.get("family_id") or "")
        version_id = str(release.get("version_id") or "")
        inventory = release.get("inventory_summary") if isinstance(release.get("inventory_summary"), Mapping) else {}
        release_bytes = int(inventory.get("total_size_bytes") or 0)
        totals["total_bytes"] += release_bytes
        superseding_versions = sorted(superseded_by.get((family_id, version_id), []))
        restore_handle = release_restore_handle(release)
        checksum = release_checksum(release)
        rehydrate_verification = release_rehydrate_verification(release)
        decision = dataset_release_decision(
            release=release,
            release_bytes=release_bytes,
            superseding_versions=superseding_versions,
            restore_handle=restore_handle,
            checksum=checksum,
            rehydrate_verification=rehydrate_verification,
        )
        totals[decision["total_bucket"]] += release_bytes
        release_reports.append(
            {
                "family_id": family_id,
                "dataset_id": release.get("dataset_id"),
                "version_id": version_id,
                "data_root": release.get("data_root"),
                "manifest_path": release.get("manifest_path"),
                "bytes": release_bytes,
                "superseded_by": superseding_versions,
                "source_release": release.get("source_release"),
                "restore_handle": restore_handle,
                "checksum": checksum,
                "rehydrate_verification": rehydrate_verification,
                "candidate_action": decision["candidate_action"],
                "risk": decision["risk"],
                "estimated_release_bytes": decision["estimated_release_bytes"],
                "blockers": decision["blockers"],
            }
        )
    return {
        "category": "dataset",
        "workspace_root": str(workspace_root),
        "release_count": len(release_reports),
        "total_bytes": totals["total_bytes"],
        "candidate_action": "lineage-aware-retention",
        "estimated_release_bytes": totals["archive_offline_candidate_bytes"],
        "actual_release_bytes": 0,
        "totals": totals,
        "releases": release_reports,
    }


def superseded_release_index(releases: list[Mapping[str, Any]]) -> dict[tuple[str, str], list[str]]:
    superseded_by: dict[tuple[str, str], list[str]] = {}
    for release in releases:
        family_id = str(release.get("family_id") or "")
        version_id = str(release.get("version_id") or "")
        for superseded_version in release.get("supersedes_versions") or []:
            if isinstance(superseded_version, str) and superseded_version:
                superseded_by.setdefault((family_id, superseded_version), []).append(version_id)
    return superseded_by


def dataset_release_decision(
    *,
    release: Mapping[str, Any],
    release_bytes: int,
    superseding_versions: list[str],
    restore_handle: str | None,
    checksum: str | None,
    rehydrate_verification: Mapping[str, Any] | str | None,
) -> dict[str, Any]:
    blockers = dataset_release_blockers(
        release=release,
        superseding_versions=superseding_versions,
        restore_handle=restore_handle,
        checksum=checksum,
        rehydrate_verification=rehydrate_verification,
    )
    if not superseding_versions:
        return {
            "candidate_action": "keep-online",
            "risk": "canonical_or_unsuperseded_release",
            "estimated_release_bytes": 0,
            "blockers": blockers,
            "total_bucket": "keep_online_bytes",
        }
    if blockers:
        return {
            "candidate_action": "blocked",
            "risk": "lineage_incomplete",
            "estimated_release_bytes": 0,
            "blockers": blockers,
            "total_bucket": "blocked_bytes",
        }
    return {
        "candidate_action": "archive-offline",
        "risk": "superseded_lineage_with_restore",
        "estimated_release_bytes": release_bytes,
        "blockers": blockers,
        "total_bucket": "archive_offline_candidate_bytes",
    }


def dataset_release_blockers(
    *,
    release: Mapping[str, Any],
    superseding_versions: list[str],
    restore_handle: str | None,
    checksum: str | None,
    rehydrate_verification: Mapping[str, Any] | str | None,
) -> list[str]:
    blockers: list[str] = []
    if release.get("contract_status") != "manifest_backed":
        blockers.append("missing_dataset_manifest")
    if superseding_versions:
        restore_metadata = {
            "restore_handle": restore_handle,
            "sha256": checksum,
            "rehydrate_verification": rehydrate_verification,
        }
        archive_path = Path(str(release.get("data_root") or release.get("manifest_path") or "."))
        for blocker in evaluate_archive_cleanup_readiness(
            archive_path=archive_path,
            restore_metadata=restore_metadata,
        )["blockers"]:
            if blocker not in blockers:
                blockers.append(blocker)
    return blockers
