from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import os
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    write_json,
)


SURFACE_KIND = "cold_store_dedupe"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def run_cold_store_dedupe(
    *,
    root: Path,
    apply: bool,
    min_mb: int = 16,
    max_groups: int | None = None,
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    blockers: list[dict[str, Any]] = []
    groups = _duplicate_groups(root=resolved_root, threshold_bytes=threshold_bytes)
    if max_groups is not None:
        groups = groups[: max(0, int(max_groups))]

    hardlinked_count = 0
    already_hardlinked_count = 0
    actual_release_bytes = 0
    for group in groups:
        if not apply:
            continue
        applied = _apply_group(group)
        group.update(applied)
        hardlinked_count += int(applied.get("hardlinked_count") or 0)
        already_hardlinked_count += int(applied.get("already_hardlinked_count") or 0)
        actual_release_bytes += int(applied.get("actual_logical_release_bytes") or 0)
        blockers.extend(applied.get("blockers") or [])

    if blockers and apply:
        status = "blocked"
    elif groups and apply:
        status = "applied" if hardlinked_count or already_hardlinked_count else "nothing_to_dedupe"
    elif groups:
        status = "planned"
    else:
        status = "nothing_to_dedupe"

    receipt = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "root": str(resolved_root),
        "apply": bool(apply),
        "min_bytes": threshold_bytes,
        "max_groups": max_groups,
        "duplicate_group_count": len(groups),
        "candidate_duplicate_file_count": sum(max(0, len(group["paths"]) - 1) for group in groups),
        "hardlinked_count": hardlinked_count,
        "already_hardlinked_count": already_hardlinked_count,
        "blocker_count": len(blockers),
        "actual_logical_release_bytes": actual_release_bytes,
        "body_included": False,
        "mutation_policy": {
            "hardlinks_duplicate_cold_objects": bool(apply),
            "rewrites_cold_refs_or_restore_commands": False,
            "deletes_online_workspace_files": False,
            "deletes_domain_truth": False,
            "deletes_data_assets": False,
        },
        "candidate_samples": _sample_entries(groups),
        "blocker_samples": _sample_entries(blockers),
    }
    receipt_root = resolved_root / ".retention" / SURFACE_KIND
    receipt_path = receipt_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = receipt_root / "latest.json"
    write_json(receipt_path, receipt)
    write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)
    return receipt


def _duplicate_groups(*, root: Path, threshold_bytes: int) -> list[dict[str, Any]]:
    if not root.is_dir():
        return []
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in _iter_cold_object_files(root):
        try:
            size_bytes = path.stat().st_size
        except OSError:
            continue
        if size_bytes >= threshold_bytes:
            by_size[size_bytes].append(path)

    groups: list[dict[str, Any]] = []
    for size_bytes, paths in sorted(by_size.items(), reverse=True):
        if len(paths) < 2:
            continue
        by_sha: dict[str, list[Path]] = defaultdict(list)
        for path in paths:
            by_sha[_sha256(path)].append(path)
        for sha256, duplicate_paths in by_sha.items():
            unique_inodes = {_inode_key(path) for path in duplicate_paths}
            if len(duplicate_paths) < 2 or len(unique_inodes) < 2:
                continue
            sorted_paths = sorted(duplicate_paths, key=lambda item: (len(str(item)), str(item)))
            groups.append(
                {
                    "status": "candidate",
                    "sha256": sha256,
                    "bytes": size_bytes,
                    "canonical_path": str(sorted_paths[0]),
                    "paths": [str(path) for path in sorted_paths],
                    "duplicate_path_count": len(sorted_paths) - 1,
                    "planned_logical_release_bytes": size_bytes * (len(sorted_paths) - 1),
                }
            )
    return groups


def _iter_cold_object_files(root: Path) -> Iterable[Path]:
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        parts = path.parts
        if len(parts) < 3 or parts[-3] != "objects":
            continue
        if path.name.endswith((".manifest.json", ".restore_proof.json", ".cold_ref.json", ".detail_ref.json")):
            continue
        yield path


def _apply_group(group: Mapping[str, Any]) -> dict[str, Any]:
    canonical = Path(str(group["canonical_path"]))
    expected_sha = str(group["sha256"])
    if not canonical.is_file():
        return {"status": "blocked", "blockers": [{"reason": "canonical_missing", "path": str(canonical)}]}
    if _sha256(canonical) != expected_sha:
        return {"status": "blocked", "blockers": [{"reason": "canonical_sha256_mismatch", "path": str(canonical)}]}

    hardlinked_count = 0
    already_hardlinked_count = 0
    release_bytes = 0
    blockers: list[dict[str, Any]] = []
    for raw_path in list(group.get("paths") or [])[1:]:
        path = Path(str(raw_path))
        if not path.is_file():
            blockers.append({"reason": "duplicate_missing", "path": str(path)})
            continue
        if _inode_key(path) == _inode_key(canonical):
            already_hardlinked_count += 1
            continue
        observed_sha = _sha256(path)
        if observed_sha != expected_sha:
            blockers.append(
                {
                    "reason": "duplicate_sha256_mismatch",
                    "path": str(path),
                    "expected_sha256": expected_sha,
                    "observed_sha256": observed_sha,
                }
            )
            continue
        tmp_path = path.with_name(f"{path.name}.dedupe-hardlink.tmp")
        if tmp_path.exists() or tmp_path.is_symlink():
            blockers.append({"reason": "temporary_path_exists", "path": str(tmp_path)})
            continue
        try:
            os.link(canonical, tmp_path)
            if _sha256(tmp_path) != expected_sha:
                blockers.append({"reason": "temporary_hardlink_sha256_mismatch", "path": str(tmp_path)})
                tmp_path.unlink(missing_ok=True)
                continue
            os.replace(tmp_path, path)
        except OSError as exc:
            tmp_path.unlink(missing_ok=True)
            blockers.append({"reason": "hardlink_replace_failed", "path": str(path), "error": str(exc)})
            continue
        hardlinked_count += 1
        release_bytes += int(group.get("bytes") or 0)

    return {
        "status": "applied" if hardlinked_count or already_hardlinked_count else "blocked" if blockers else "nothing_to_dedupe",
        "hardlinked_count": hardlinked_count,
        "already_hardlinked_count": already_hardlinked_count,
        "actual_logical_release_bytes": release_bytes,
        "blockers": blockers,
    }


def _inode_key(path: Path) -> tuple[int, int]:
    stat_result = path.stat()
    return (stat_result.st_dev, stat_result.st_ino)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _artifact_slug(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime(_TIMESTAMP_FORMAT)


def _sample_entries(entries: Iterable[Mapping[str, Any]], limit: int = 20) -> list[dict[str, Any]]:
    return [dict(entry) for entry in list(entries)[:limit]]


__all__ = ["run_cold_store_dedupe"]
