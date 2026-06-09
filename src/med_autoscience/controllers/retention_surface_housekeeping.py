from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
from pathlib import Path
import shutil
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    write_json,
)


SURFACE_KIND = "retention_surface_housekeeping"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_MISPLACED_SUFFIXES = (
    ("archive", "runtime", "artifacts", "historical_body_retention"),
    ("runtime", "archives", "runtime", "artifacts", "historical_body_retention"),
)
_ALLOWED_MISPLACED_SURFACE_KINDS = frozenset({"historical_body_retention"})


def run_retention_surface_housekeeping(
    *,
    root: Path,
    apply: bool,
    max_directories: int | None = None,
) -> dict[str, Any]:
    resolved_root = Path(root).expanduser().resolve()
    recorded_at = _utc_now()
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    removed_count = 0
    removed_bytes = 0

    for directory in _candidate_directories(resolved_root):
        inspection = _inspect_directory(resolved_root=resolved_root, directory=directory)
        if inspection.get("status") == "blocked":
            blockers.append(inspection)
            continue
        if inspection.get("status") != "candidate":
            continue
        if max_directories is not None and len(candidates) >= max(0, int(max_directories)):
            break
        if apply:
            applied = _apply_cleanup(directory=directory, inspection=inspection)
            inspection.update(applied)
            if applied.get("status") == "removed":
                removed_count += 1
                removed_bytes += int(applied.get("removed_bytes") or 0)
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(inspection)
        candidates.append(inspection)

    status = (
        "applied"
        if apply and removed_count and not blockers
        else "blocked"
        if blockers
        else "planned"
        if candidates
        else "nothing_to_cleanup"
    )
    receipt = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "root": str(resolved_root),
        "apply": bool(apply),
        "max_directories": max_directories,
        "candidate_count": len(candidates),
        "removed_count": removed_count,
        "blocker_count": len(blockers),
        "removed_bytes": removed_bytes,
        "body_included": False,
        "mutation_policy": {
            "removes_misplaced_retention_receipts": bool(apply),
            "deletes_cold_objects": False,
            "deletes_domain_truth": False,
            "accepted_misplaced_suffixes": ["/".join(suffix) for suffix in _MISPLACED_SUFFIXES],
            "accepted_surface_kinds": sorted(_ALLOWED_MISPLACED_SURFACE_KINDS),
        },
        "candidate_samples": _sample_entries(candidates),
        "blocker_samples": _sample_entries(blockers),
    }
    receipt_root = _receipt_root(resolved_root)
    receipt_path = receipt_root / f"{_artifact_slug(recorded_at)}.json"
    latest_path = receipt_root / "latest.json"
    write_json(receipt_path, receipt)
    write_json(latest_path, receipt)
    receipt["receipt_path"] = str(receipt_path)
    receipt["latest_receipt_path"] = str(latest_path)
    return receipt


def _candidate_directories(root: Path) -> list[Path]:
    if not root.exists():
        return []
    candidates: list[Path] = []
    for directory in root.rglob("historical_body_retention"):
        if not directory.is_dir() or directory.is_symlink():
            continue
        parts = directory.parts
        if any(_endswith(parts, suffix) for suffix in _MISPLACED_SUFFIXES):
            candidates.append(directory)
    return sorted(candidates)


def _inspect_directory(*, resolved_root: Path, directory: Path) -> dict[str, Any]:
    workspace_root = _workspace_root(directory)
    if workspace_root is None:
        return {
            "status": "blocked",
            "reason": "workspace_root_not_found",
            "path": str(directory),
        }
    files = sorted(path for path in directory.rglob("*") if path.is_file() and not path.is_symlink())
    unknown: list[dict[str, Any]] = []
    entries: list[dict[str, Any]] = []
    for path in files:
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            unknown.append({"path": str(path), "reason": "not_valid_json", "error": str(exc)})
            continue
        surface_kind = str(payload.get("surface_kind") or "")
        if surface_kind not in _ALLOWED_MISPLACED_SURFACE_KINDS:
            unknown.append({"path": str(path), "reason": "unexpected_surface_kind", "surface_kind": surface_kind})
            continue
        entries.append(
            {
                "path": str(path),
                "workspace_relative_path": _relative_to_workspace(workspace_root=workspace_root, path=path),
                "bytes": path.stat().st_size,
                "sha256": _sha256(path),
                "surface_kind": surface_kind,
            }
        )
    if unknown:
        return {
            "status": "blocked",
            "reason": "unexpected_files_in_misplaced_retention_surface",
            "path": str(directory),
            "workspace_root": str(workspace_root),
            "unknown_files": unknown,
        }
    if not entries:
        return {
            "status": "blocked",
            "reason": "empty_misplaced_retention_surface",
            "path": str(directory),
            "workspace_root": str(workspace_root),
        }
    return {
        "status": "candidate",
        "path": str(directory),
        "workspace_root": str(workspace_root),
        "workspace_relative_path": _relative_to_workspace(workspace_root=workspace_root, path=directory),
        "file_count": len(entries),
        "bytes": sum(int(entry["bytes"]) for entry in entries),
        "files": entries,
        "cleanup_reason": "self_created_misplaced_historical_body_retention_receipt",
    }


def _apply_cleanup(*, directory: Path, inspection: Mapping[str, Any]) -> dict[str, Any]:
    expected_entries = inspection.get("files")
    if not isinstance(expected_entries, list) or not expected_entries:
        return {"status": "blocked_missing_manifest_entries", "removed_bytes": 0}
    for entry in expected_entries:
        if not isinstance(entry, Mapping):
            return {"status": "blocked_invalid_manifest_entry", "removed_bytes": 0}
        path = Path(str(entry.get("path") or ""))
        if not path.is_file() or path.is_symlink():
            return {"status": "blocked_file_missing_or_symlink", "path": str(path), "removed_bytes": 0}
        if _sha256(path) != str(entry.get("sha256") or ""):
            return {"status": "blocked_file_sha256_changed", "path": str(path), "removed_bytes": 0}
    removed_bytes = int(inspection.get("bytes") or 0)
    shutil.rmtree(directory)
    return {"status": "removed", "removed_bytes": removed_bytes}


def _workspace_root(path: Path) -> Path | None:
    resolved = path.expanduser().resolve()
    for candidate in (resolved, *resolved.parents):
        if (candidate / "workspace.yaml").exists() and (candidate / "runtime").is_dir():
            return candidate
    return None


def _receipt_root(root: Path) -> Path:
    workspace_root = _workspace_root(root)
    if workspace_root is not None:
        return workspace_root / "runtime" / "artifacts" / "retention_surface_housekeeping"
    return root / "runtime" / "artifacts" / "retention_surface_housekeeping"


def _relative_to_workspace(*, workspace_root: Path, path: Path) -> str:
    try:
        return path.resolve().relative_to(workspace_root.resolve()).as_posix()
    except ValueError:
        return str(path)


def _endswith(parts: tuple[str, ...], suffix: tuple[str, ...]) -> bool:
    if len(parts) < len(suffix):
        return False
    return parts[-len(suffix) :] == suffix


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


__all__ = ["run_retention_surface_housekeeping"]
