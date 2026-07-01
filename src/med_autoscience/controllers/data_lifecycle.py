from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.workspace_paths import DATASETS_RELPATH


SCHEMA_VERSION = 1
INSPECTION_SURFACE_KIND = "mas_data_lifecycle_inspection"
CLOSEOUT_SURFACE_KIND = "mas_data_lifecycle_closeout_plan"
COMPACT_RUNTIME_SURFACE_KIND = "mas_data_lifecycle_runtime_compact_plan"
_CANDIDATE_LIMIT = 200
_DATASET_BODY_SKIP = DATASETS_RELPATH.as_posix()
_CACHE_DIR_NAMES = {".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}
_SMALL_FILE_BYTES = 16 * 1024
_SQLITE_TARGET_PATH = "runtime/index.sqlite"


def inspect_data_lifecycle(*, workspace_root: Path) -> dict[str, Any]:
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    cleanup_candidates = _cleanup_candidates(resolved_workspace)
    retention_faces = _retention_faces(resolved_workspace)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": INSPECTION_SURFACE_KIND,
        "workspace_root": str(resolved_workspace),
        "management_mode": _management_mode(resolved_workspace),
        "mutation_policy": _mutation_policy(),
        "retention_faces": retention_faces,
        "plane_summary": _plane_summary(resolved_workspace),
        "lifecycle_gaps": _lifecycle_gaps(resolved_workspace, retention_faces=retention_faces),
        "skipped_generic_cleanup_roots": [_DATASET_BODY_SKIP],
        "cleanup_candidate_count": len(cleanup_candidates),
        "cleanup_candidates": cleanup_candidates,
    }


def closeout_data_lifecycle(*, workspace_root: Path, dry_run: bool) -> dict[str, Any]:
    if not dry_run:
        raise ValueError("data-lifecycle closeout only supports --dry-run")
    inspection = inspect_data_lifecycle(workspace_root=workspace_root)
    operations = [_closeout_operation(candidate) for candidate in inspection["cleanup_candidates"]]
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": CLOSEOUT_SURFACE_KIND,
        "workspace_root": inspection["workspace_root"],
        "dry_run": True,
        "status": "dry_run",
        "mutation_policy": _mutation_policy(),
        "management_mode": inspection["management_mode"],
        "lifecycle_gaps": inspection["lifecycle_gaps"],
        "skipped_generic_cleanup_roots": inspection["skipped_generic_cleanup_roots"],
        "closeout_plan": {
            "mode": "dry_run",
            "cleanup_candidate_count": len(operations),
            "operations": operations,
        },
    }


def compact_runtime_lifecycle(*, workspace_root: Path, dry_run: bool, apply: bool = False) -> dict[str, Any]:
    if dry_run == apply:
        raise ValueError("data-lifecycle compact-runtime requires exactly one of --dry-run or --apply")
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    candidates = _small_runtime_candidates(resolved_workspace)
    candidate_file_count = sum(int(candidate["file_count"]) for candidate in candidates)
    candidate_bytes = sum(int(candidate["bytes"]) for candidate in candidates)
    if apply:
        apply_receipt = _apply_runtime_index(workspace_root=resolved_workspace, candidates=candidates)
        return {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": COMPACT_RUNTIME_SURFACE_KIND,
            "workspace_root": str(resolved_workspace),
            "dry_run": False,
            "status": "applied",
            "mutation_policy": _runtime_index_mutation_policy(apply=True),
            "target_index": _SQLITE_TARGET_PATH,
            "sqlite_target_path": _SQLITE_TARGET_PATH,
            "blob_policy": "small_runtime_payloads_indexed_by_sha256; large_payloads_remain_file_backed_by_sha256_ref",
            "forbidden_boundaries": _runtime_index_forbidden_boundaries(),
            "forbidden_boundary": _runtime_index_forbidden_boundary(),
            "candidate_count": len(candidates),
            "candidate_file_count": candidate_file_count,
            "candidate_bytes": candidate_bytes,
            "apply_receipt": apply_receipt,
            "candidates": candidates,
        }
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": COMPACT_RUNTIME_SURFACE_KIND,
        "workspace_root": str(resolved_workspace),
        "dry_run": True,
        "status": "dry_run",
        "mutation_policy": _runtime_index_mutation_policy(apply=False),
        "target_index": _SQLITE_TARGET_PATH,
        "sqlite_target_path": _SQLITE_TARGET_PATH,
        "blob_policy": "large_payloads_remain_file_backed_by_sha256_ref",
        "forbidden_boundaries": _runtime_index_forbidden_boundaries(),
        "forbidden_boundary": _runtime_index_forbidden_boundary(),
        "candidate_count": len(candidates),
        "candidate_file_count": candidate_file_count,
        "candidate_bytes": candidate_bytes,
        "estimated_benefit": {
            "candidate_count": len(candidates),
            "candidate_file_count": candidate_file_count,
            "candidate_small_file_count": candidate_file_count,
            "candidate_bytes": candidate_bytes,
            "estimated_metadata_entry_count": candidate_file_count,
        },
        "compact_plan": {
            "mode": "dry_run",
            "apply_command": "medautosci data-lifecycle compact-runtime --workspace-root <workspace> --apply --format json",
            "small_file_threshold_bytes": _SMALL_FILE_BYTES,
            "sqlite_target_path": _SQLITE_TARGET_PATH,
            "candidates": candidates,
        },
        "candidates": candidates,
    }


def _runtime_index_mutation_policy(*, apply: bool) -> dict[str, Any]:
    return {
        "read_only": not apply,
        "dry_run_only": False,
        "writes_workspace": apply,
        "writes_runtime": apply,
        "writes_runtime_index_only": apply,
        "physical_cleanup_performed": False,
        "physical_delete_performed": False,
        "source_files_preserved": True,
        "physical_cleanup_owner": "one-person-lab",
    }


def _runtime_index_forbidden_boundaries() -> list[str]:
    return [
        _DATASET_BODY_SKIP,
        "current_package.zip",
        "paper/submission_minimal.zip",
        "owner receipts by hand",
        "typed blockers by hand",
        "runtime queues/provider attempts",
    ]


def _runtime_index_forbidden_boundary() -> dict[str, Any]:
    return {
        "dataset_body_roots": [_DATASET_BODY_SKIP],
        "excluded_surfaces": ["dataset body", "current_package.zip", "owner receipts", "typed blockers"],
        "physical_payload_insert_performed": False,
        "source_file_delete_performed": False,
    }


def _mutation_policy() -> dict[str, Any]:
    return {
        "read_only": True,
        "dry_run_only": True,
        "writes_workspace": False,
        "writes_runtime": False,
        "physical_cleanup_performed": False,
        "physical_delete_performed": False,
        "physical_cleanup_owner": "one-person-lab",
    }


def _management_mode(workspace_root: Path) -> dict[str, Any]:
    return {
        "surface": "mas_data_lifecycle.v1",
        "mode": "read_only_inspection",
        "runtime_owner": "opl_provider_backed_stage_runtime",
        "physical_cleanup_owner": "one-person-lab",
        "data_datasets": {
            "root": _DATASET_BODY_SKIP,
            "role": "current_clinical_data_asset_authority",
            "generic_cleanup_allowed": False,
            "reason": "current_clinical_data_asset_authority",
        },
        "classified_categories": {
            "runtime": "runtime attempt and quest residue; MAS only projects retention candidates",
            "artifact": "workspace/study artifact projections requiring owner review before cleanup",
            "exchange": "human-facing package/export surfaces; never runtime residue",
            "archive": "cold or stopped runtime/archive material requiring restore proof before cleanup",
            "cache": "tool cache candidates; still no physical deletion from this command",
        },
        "workspace_refs": {
            "data_datasets": _workspace_ref(workspace_root, workspace_root / _DATASET_BODY_SKIP),
            "studies": _workspace_ref(workspace_root, workspace_root / "studies"),
            "runtime": _workspace_ref(workspace_root, workspace_root / "runtime"),
            "memory": _workspace_ref(workspace_root, workspace_root / "memory"),
        },
    }


def _retention_faces(workspace_root: Path) -> dict[str, Any]:
    roots = {
        "data": workspace_root / "data",
        "data_datasets": workspace_root / _DATASET_BODY_SKIP,
        "studies": workspace_root / "studies",
        "runtime": workspace_root / "runtime",
        "runtime_archives": workspace_root / "runtime" / "archives",
        "archive": workspace_root / "archive",
        "archives": workspace_root / "archives",
        "memory": workspace_root / "memory",
        "data_asset_registry": workspace_root / "memory" / "portfolio" / "data_assets",
        "artifact_runtime": workspace_root / "artifacts" / "runtime",
    }
    return {
        key: {
            "ref": _workspace_ref(workspace_root, path),
            "exists": path.exists(),
            "generic_cleanup_allowed": False if key == "data_datasets" else None,
        }
        for key, path in roots.items()
    }


def _lifecycle_gaps(workspace_root: Path, *, retention_faces: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if not retention_faces["memory"]["exists"]:
        gaps.append(_gap("missing_memory_root", "memory"))
    if not retention_faces["data_asset_registry"]["exists"]:
        gaps.append(_gap("missing_data_asset_registry_plane", "memory/portfolio/data_assets"))
    if retention_faces["runtime_archives"]["exists"] and not (workspace_root / "runtime" / "restore_index").exists():
        gaps.append(_gap("missing_runtime_restore_index_for_archives", "runtime/restore_index"))
    if retention_faces["studies"]["exists"] and not retention_faces["artifact_runtime"]["exists"]:
        gaps.append(_gap("missing_workspace_runtime_artifact_projection", "artifacts/runtime"))
    return gaps


def _plane_summary(workspace_root: Path) -> dict[str, Any]:
    planes = {
        "body": workspace_root / _DATASET_BODY_SKIP,
        "index": workspace_root / "memory" / "portfolio" / "data_assets",
        "study": workspace_root / "studies",
        "runtime": workspace_root / "runtime",
        "export": workspace_root / "manuscript",
        "retention": workspace_root / "memory" / "portfolio" / "data_assets" / "retention",
    }
    return {
        name: {
            **_path_stats(
                path,
                workspace_root=workspace_root,
                skip_cache=False,
                include_dataset_body=name == "body",
            ),
            "workspace_relative_path": _workspace_ref(workspace_root, path),
            "exists": path.exists(),
            "generic_cleanup_allowed": False if name == "body" else None,
        }
        for name, path in planes.items()
    }


def _gap(gap_type: str, ref: str) -> dict[str, str]:
    return {
        "gap_type": gap_type,
        "ref": ref,
        "severity": "info",
        "owner_surface": "mas_data_lifecycle_read_only_projection",
    }


def _cleanup_candidates(workspace_root: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for category, units in _candidate_units(workspace_root).items():
        for path in units:
            if not path.exists() or _is_under_dataset_body(path, workspace_root=workspace_root):
                continue
            candidate = _candidate(workspace_root=workspace_root, path=path, category=category)
            if candidate["file_count"] == 0 and candidate["bytes"] == 0:
                continue
            candidates.append(candidate)
            if len(candidates) >= _CANDIDATE_LIMIT:
                return candidates
    return candidates


def _candidate_units(workspace_root: Path) -> dict[str, tuple[Path, ...]]:
    return {
        "runtime": (
            *_direct_children(workspace_root / "runtime" / "quests"),
            *_direct_children(workspace_root / "runtime" / "runs"),
        ),
        "archive": (
            *_direct_children(workspace_root / "runtime" / "archives"),
            *_direct_children(workspace_root / "archive"),
            *_direct_children(workspace_root / "archives"),
        ),
        "artifact": (
            *_existing_paths(workspace_root / "artifacts" / "runtime"),
            *(workspace_root / "studies").glob("*/artifacts"),
        ),
        "exchange": _current_package_units(workspace_root),
        "cache": tuple(path for path in workspace_root.iterdir() if path.name in _CACHE_DIR_NAMES)
        if workspace_root.exists()
        else (),
    }


def _direct_children(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    if root.is_file():
        return (root,)
    return tuple(sorted(root.iterdir(), key=lambda path: path.name))


def _existing_paths(*paths: Path) -> tuple[Path, ...]:
    return tuple(path for path in paths if path.exists())


def _current_package_units(workspace_root: Path) -> tuple[Path, ...]:
    roots = [workspace_root / "manuscript"]
    studies_root = workspace_root / "studies"
    if studies_root.exists():
        roots.extend(study / "manuscript" for study in studies_root.iterdir() if study.is_dir())
    paths: list[Path] = []
    for root in roots:
        paths.extend(_existing_paths(root / "current_package", root / "current_package.zip"))
    return tuple(paths)


def _candidate(*, workspace_root: Path, path: Path, category: str) -> dict[str, Any]:
    action_by_category = {
        "runtime": "review_runtime_retention",
        "archive": "restore_proof_required_before_cleanup",
        "artifact": "owner_review_required_before_cleanup",
        "exchange": "retain_as_human_facing_exchange_surface",
        "cache": "delete_safe_cache_candidate",
    }
    stats = _path_stats(path, workspace_root=workspace_root)
    return {
        "workspace_relative_path": _workspace_ref(workspace_root, path),
        "category": category,
        "candidate_unit": "file" if path.is_file() else "directory",
        "bytes": stats["bytes"],
        "mib": round(stats["bytes"] / (1024**2), 1),
        "file_count": stats["file_count"],
        "candidate_action": action_by_category[category],
        "generic_cleanup_allowed": False,
        "physical_delete_allowed": False,
        "physical_delete_performed": False,
        "reason": "read_only_lifecycle_projection",
    }


def _path_stats(
    path: Path,
    *,
    workspace_root: Path,
    skip_cache: bool = True,
    include_dataset_body: bool = False,
) -> dict[str, int]:
    if path.is_file():
        try:
            size = path.stat().st_size
            return {"bytes": size, "file_count": 1, "small_file_count": int(size < _SMALL_FILE_BYTES)}
        except FileNotFoundError:
            return {"bytes": 0, "file_count": 0, "small_file_count": 0}
    total_bytes = 0
    file_count = 0
    small_file_count = 0
    if not path.exists():
        return {"bytes": 0, "file_count": 0, "small_file_count": 0}
    for current_root, dirnames, filenames in os.walk(path):
        current_path = Path(current_root)
        if not include_dataset_body and _is_under_dataset_body(current_path, workspace_root=workspace_root):
            dirnames[:] = []
            continue
        if skip_cache:
            dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in _CACHE_DIR_NAMES)
        else:
            dirnames[:] = sorted(dirnames)
        for filename in filenames:
            file_path = current_path / filename
            try:
                size = file_path.stat().st_size
            except FileNotFoundError:
                continue
            total_bytes += size
            file_count += 1
            if size < _SMALL_FILE_BYTES:
                small_file_count += 1
    return {"bytes": total_bytes, "file_count": file_count, "small_file_count": small_file_count}


def _small_runtime_candidates(workspace_root: Path) -> list[dict[str, Any]]:
    runtime_root = workspace_root / "runtime"
    if not runtime_root.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(runtime_root.rglob("*")):
        if len(candidates) >= _CANDIDATE_LIMIT:
            break
        if not path.is_file() or _is_under_dataset_body(path, workspace_root=workspace_root):
            continue
        if _workspace_ref(workspace_root, path) == _SQLITE_TARGET_PATH:
            continue
        if path.name in {"current_package.zip", "submission_minimal.zip"}:
            continue
        try:
            size = path.stat().st_size
        except FileNotFoundError:
            continue
        if size >= _SMALL_FILE_BYTES:
            continue
        candidates.append(
            {
                "workspace_relative_path": _workspace_ref(workspace_root, path),
                "file_count": 1,
                "bytes": size,
                "small_file_count": 1,
                "candidate_action": "index_small_runtime_record",
                "target_index": _SQLITE_TARGET_PATH,
                "dry_run": True,
                "writes_workspace": False,
            }
        )
    return candidates


def _apply_runtime_index(*, workspace_root: Path, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    indexed_at = datetime.now(timezone.utc).isoformat()
    index_path = workspace_root / _SQLITE_TARGET_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        _runtime_index_record(workspace_root=workspace_root, candidate=candidate, indexed_at=indexed_at)
        for candidate in candidates
    ]
    with sqlite3.connect(index_path) as connection:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS runtime_compact_manifest (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER NOT NULL,
                generated_at TEXT NOT NULL,
                workspace_root TEXT NOT NULL,
                small_file_threshold_bytes INTEGER NOT NULL,
                indexed_file_count INTEGER NOT NULL,
                indexed_bytes INTEGER NOT NULL,
                physical_delete_performed INTEGER NOT NULL,
                source_files_preserved INTEGER NOT NULL,
                forbidden_boundaries_json TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runtime_file_records (
                workspace_relative_path TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                bytes INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                indexed_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                source_file_preserved INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS runtime_file_payloads (
                sha256 TEXT PRIMARY KEY,
                bytes INTEGER NOT NULL,
                payload BLOB NOT NULL
            );
            """
        )
        connection.execute("DELETE FROM runtime_file_records")
        connection.execute(
            """
            INSERT OR REPLACE INTO runtime_compact_manifest (
                id,
                schema_version,
                generated_at,
                workspace_root,
                small_file_threshold_bytes,
                indexed_file_count,
                indexed_bytes,
                physical_delete_performed,
                source_files_preserved,
                forbidden_boundaries_json
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            """,
            (
                SCHEMA_VERSION,
                indexed_at,
                str(workspace_root),
                _SMALL_FILE_BYTES,
                len(records),
                sum(int(record["bytes"]) for record in records),
                json.dumps(_runtime_index_forbidden_boundaries()),
            ),
        )
        for record in records:
            connection.execute(
                """
                INSERT OR REPLACE INTO runtime_file_payloads (sha256, bytes, payload)
                VALUES (?, ?, ?)
                """,
                (record["sha256"], record["bytes"], record["payload"]),
            )
            connection.execute(
                """
                INSERT OR REPLACE INTO runtime_file_records (
                    workspace_relative_path,
                    sha256,
                    bytes,
                    mtime_ns,
                    indexed_at,
                    payload_sha256,
                    source_file_preserved
                )
                VALUES (?, ?, ?, ?, ?, ?, 1)
                """,
                (
                    record["workspace_relative_path"],
                    record["sha256"],
                    record["bytes"],
                    record["mtime_ns"],
                    indexed_at,
                    record["sha256"],
                ),
            )
    return {
        "sqlite_target_path": _SQLITE_TARGET_PATH,
        "indexed_file_count": len(records),
        "indexed_bytes": sum(int(record["bytes"]) for record in records),
        "indexed_payload_count": len({str(record["sha256"]) for record in records}),
        "physical_delete_performed": False,
        "source_files_preserved": True,
        "indexed_at": indexed_at,
    }


def _runtime_index_record(*, workspace_root: Path, candidate: dict[str, Any], indexed_at: str) -> dict[str, Any]:
    relative_path = str(candidate["workspace_relative_path"])
    file_path = workspace_root / relative_path
    payload = file_path.read_bytes()
    stat_result = file_path.stat()
    sha256 = hashlib.sha256(payload).hexdigest()
    return {
        "workspace_relative_path": relative_path,
        "sha256": sha256,
        "bytes": len(payload),
        "mtime_ns": stat_result.st_mtime_ns,
        "indexed_at": indexed_at,
        "payload": payload,
    }


def _closeout_operation(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        **candidate,
        "plan_action": "handoff_to_owner_for_review",
        "dry_run": True,
        "writes_workspace": False,
        "physical_delete_performed": False,
    }


def _is_under_dataset_body(path: Path, *, workspace_root: Path) -> bool:
    try:
        path.resolve().relative_to((workspace_root / _DATASET_BODY_SKIP).resolve())
        return True
    except ValueError:
        return False


def _workspace_ref(workspace_root: Path, path: Path) -> str:
    try:
        return path.expanduser().resolve().relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()


__all__ = ["closeout_data_lifecycle", "compact_runtime_lifecycle", "inspect_data_lifecycle"]
