from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.controllers.data_lifecycle.inspection import (
    CANDIDATE_LIMIT as _CANDIDATE_LIMIT,
    DATASET_BODY_SKIP as _DATASET_BODY_SKIP,
    SMALL_FILE_BYTES as _SMALL_FILE_BYTES,
    cleanup_candidates as _cleanup_candidates,
    closeout_operation as _closeout_operation,
    is_under_dataset_body as _is_under_dataset_body,
    lifecycle_gaps as _lifecycle_gaps,
    management_mode as _management_mode,
    mutation_policy as _mutation_policy,
    path_stats as _path_stats,
    plane_summary as _plane_summary,
    retention_faces as _retention_faces,
    workspace_ref as _workspace_ref,
)


SCHEMA_VERSION = 1
INSPECTION_SURFACE_KIND = "mas_data_lifecycle_inspection"
CLOSEOUT_SURFACE_KIND = "mas_data_lifecycle_closeout_plan"
COMPACT_RUNTIME_SURFACE_KIND = "mas_data_lifecycle_runtime_compact_plan"
ASSET_INDEX_SURFACE_KIND = "mas_data_lifecycle_asset_index"
COMPACT_STUDY_SURFACE_KIND = "mas_data_lifecycle_study_compact_plan"
COMPLETED_PROJECT_CLOSEOUT_SURFACE_KIND = "mas_data_lifecycle_completed_project_closeout"
FINAL_GOVERNANCE_SURFACE_KIND = "mas_data_lifecycle_final_governance"
_SQLITE_TARGET_PATH = "runtime/index.sqlite"
_ASSET_INDEX_PATH = "memory/portfolio/data_assets/index.sqlite"
_STUDY_INDEX_PATH = "studies/index.sqlite"
_GOVERNANCE_ROOT = "memory/portfolio/data_assets/governance"


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


def index_data_assets(*, workspace_root: Path, dry_run: bool, apply: bool = False) -> dict[str, Any]:
    if dry_run == apply:
        raise ValueError("data-lifecycle index-assets requires exactly one of --dry-run or --apply")
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    releases = _dataset_release_records(resolved_workspace)
    file_records = _dataset_file_inventory_records(resolved_workspace)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": ASSET_INDEX_SURFACE_KIND,
        "workspace_root": str(resolved_workspace),
        "dry_run": dry_run,
        "status": "dry_run" if dry_run else "applied",
        "target_index": _ASSET_INDEX_PATH,
        "sqlite_target_path": _ASSET_INDEX_PATH,
        "mutation_policy": {
            "writes_workspace": apply,
            "writes_data_asset_index_only": apply,
            "stores_dataset_body": False,
            "physical_delete_performed": False,
        },
        "release_count": len(releases),
        "file_record_count": len(file_records),
        "index_plan": {
            "mode": "dry_run" if dry_run else "apply",
            "release_count": len(releases),
            "file_record_count": len(file_records),
        },
    }
    if apply:
        payload["apply_receipt"] = _apply_asset_index(
            workspace_root=resolved_workspace,
            releases=releases,
            file_records=file_records,
        )
    return payload


def compact_study_lifecycle(*, workspace_root: Path, dry_run: bool, apply: bool = False) -> dict[str, Any]:
    if dry_run == apply:
        raise ValueError("data-lifecycle compact-study requires exactly one of --dry-run or --apply")
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    candidates = _small_study_candidates(resolved_workspace)
    candidate_file_count = sum(int(candidate["file_count"]) for candidate in candidates)
    candidate_bytes = sum(int(candidate["bytes"]) for candidate in candidates)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": COMPACT_STUDY_SURFACE_KIND,
        "workspace_root": str(resolved_workspace),
        "dry_run": dry_run,
        "status": "dry_run" if dry_run else "applied",
        "target_index": _STUDY_INDEX_PATH,
        "sqlite_target_path": _STUDY_INDEX_PATH,
        "mutation_policy": {
            "writes_workspace": apply,
            "writes_study_index_only": apply,
            "physical_delete_performed": False,
            "source_files_preserved": True,
        },
        "candidate_count": len(candidates),
        "candidate_file_count": candidate_file_count,
        "candidate_bytes": candidate_bytes,
        "compact_plan": {
            "mode": "dry_run" if dry_run else "apply",
            "small_file_threshold_bytes": _SMALL_FILE_BYTES,
            "sqlite_target_path": _STUDY_INDEX_PATH,
            "candidates": candidates,
        },
        "candidates": candidates,
    }
    if apply:
        payload["apply_receipt"] = _apply_small_file_index(
            workspace_root=resolved_workspace,
            index_relpath=_STUDY_INDEX_PATH,
            manifest_table="study_compact_manifest",
            record_table="study_file_records",
            payload_table="study_file_payloads",
            candidates=candidates,
            plane="study",
        )
    return payload


def closeout_completed_project(*, workspace_root: Path, project_id: str, dry_run: bool, apply: bool = False) -> dict[str, Any]:
    if dry_run == apply:
        raise ValueError("data-lifecycle closeout-completed-project requires exactly one of --dry-run or --apply")
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    inspection = inspect_data_lifecycle(workspace_root=resolved_workspace)
    timestamp = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    capsule_relpath = (
        "memory/portfolio/data_assets/retention/semantic_reproducible_capsules/"
        f"{project_id}_semantic_capsule_latest.md"
    )
    capsule_json_relpath = capsule_relpath.removesuffix(".md") + ".json"
    capsule_path = resolved_workspace / capsule_relpath
    capsule_json_path = resolved_workspace / capsule_json_relpath
    capsule = _completed_project_capsule_markdown(
        project_id=project_id,
        timestamp=timestamp,
        inspection=inspection,
    )
    capsule_json = _completed_project_capsule_payload(
        project_id=project_id,
        timestamp=timestamp,
        inspection=inspection,
        capsule_ref=capsule_relpath,
    )
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": COMPLETED_PROJECT_CLOSEOUT_SURFACE_KIND,
        "workspace_root": str(resolved_workspace),
        "project_id": project_id,
        "dry_run": dry_run,
        "status": "dry_run" if dry_run else "applied",
        "capsule_ref": capsule_relpath,
        "capsule_json_ref": capsule_json_relpath,
        "mutation_policy": {
            "writes_workspace": apply,
            "writes_semantic_capsule_only": apply,
            "physical_delete_performed": False,
            "source_files_preserved": True,
        },
        "important_result_reproduction_ref": capsule_relpath,
        "data_body_boundary_ref": _DATASET_BODY_SKIP,
        "cleanup_candidate_count": inspection["cleanup_candidate_count"],
    }
    if apply:
        capsule_path.parent.mkdir(parents=True, exist_ok=True)
        capsule_path.write_text(capsule, encoding="utf-8")
        capsule_json_path.write_text(json.dumps(capsule_json, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        payload["apply_receipt"] = {
            "capsule_ref": capsule_relpath,
            "capsule_json_ref": capsule_json_relpath,
            "bytes": capsule_path.stat().st_size,
            "json_bytes": capsule_json_path.stat().st_size,
            "physical_delete_performed": False,
            "source_files_preserved": True,
        }
    return payload


def finalize_governance(*, workspace_root: Path, project_id: str, dry_run: bool, apply: bool = False) -> dict[str, Any]:
    if dry_run == apply:
        raise ValueError("data-lifecycle finalize-governance requires exactly one of --dry-run or --apply")
    resolved_workspace = Path(workspace_root).expanduser().resolve()
    generated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
    refs = _governance_refs(project_id)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": FINAL_GOVERNANCE_SURFACE_KIND,
        "workspace_root": str(resolved_workspace),
        "project_id": project_id,
        "dry_run": dry_run,
        "status": "dry_run" if dry_run else "applied",
        "mutation_policy": {
            "writes_workspace": apply,
            "writes_governance_refs_only": apply,
            "physical_delete_performed": False,
            "clinical_data_transformation_performed": False,
            "source_files_preserved": True,
        },
        "refs": refs,
        "governance": _governance_payload(
            workspace_root=resolved_workspace,
            project_id=project_id,
            generated_at=generated_at,
        ),
    }
    if apply:
        written = _write_governance_refs(
            workspace_root=resolved_workspace,
            refs=refs,
            governance=payload["governance"],
        )
        payload["apply_receipt"] = {
            "written_refs": written,
            "physical_delete_performed": False,
            "clinical_data_transformation_performed": False,
            "source_files_preserved": True,
        }
    return payload


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
    return _apply_small_file_index(
        workspace_root=workspace_root,
        index_relpath=_SQLITE_TARGET_PATH,
        manifest_table="runtime_compact_manifest",
        record_table="runtime_file_records",
        payload_table="runtime_file_payloads",
        candidates=candidates,
        plane="runtime",
        forbidden_boundaries=_runtime_index_forbidden_boundaries(),
    )


def _small_study_candidates(workspace_root: Path) -> list[dict[str, Any]]:
    studies_root = workspace_root / "studies"
    if not studies_root.exists():
        return []
    candidates: list[dict[str, Any]] = []
    for path in sorted(studies_root.rglob("*")):
        if len(candidates) >= _CANDIDATE_LIMIT:
            break
        if not path.is_file() or _is_under_dataset_body(path, workspace_root=workspace_root):
            continue
        if _workspace_ref(workspace_root, path) == _STUDY_INDEX_PATH:
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
                "candidate_action": "index_small_study_record",
                "target_index": _STUDY_INDEX_PATH,
                "dry_run": True,
                "writes_workspace": False,
            }
        )
    return candidates


def _apply_small_file_index(
    *,
    workspace_root: Path,
    index_relpath: str,
    manifest_table: str,
    record_table: str,
    payload_table: str,
    candidates: list[dict[str, Any]],
    plane: str,
    forbidden_boundaries: list[str] | None = None,
) -> dict[str, Any]:
    indexed_at = datetime.now(timezone.utc).isoformat()
    index_path = workspace_root / index_relpath
    index_path.parent.mkdir(parents=True, exist_ok=True)
    records = [
        _runtime_index_record(workspace_root=workspace_root, candidate=candidate, indexed_at=indexed_at)
        for candidate in candidates
    ]
    with sqlite3.connect(index_path) as connection:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {manifest_table} (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER NOT NULL,
                plane TEXT NOT NULL,
                generated_at TEXT NOT NULL,
                workspace_root TEXT NOT NULL,
                small_file_threshold_bytes INTEGER NOT NULL,
                indexed_file_count INTEGER NOT NULL,
                indexed_bytes INTEGER NOT NULL,
                physical_delete_performed INTEGER NOT NULL,
                source_files_preserved INTEGER NOT NULL,
                forbidden_boundaries_json TEXT NOT NULL
            )
            """
        )
        _ensure_text_column(
            connection,
            table_name=manifest_table,
            column_name="plane",
            default_value=plane,
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {record_table} (
                workspace_relative_path TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                bytes INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL,
                indexed_at TEXT NOT NULL,
                payload_sha256 TEXT NOT NULL,
                source_file_preserved INTEGER NOT NULL
            )
            """
        )
        connection.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {payload_table} (
                sha256 TEXT PRIMARY KEY,
                bytes INTEGER NOT NULL,
                payload BLOB NOT NULL
            )
            """
        )
        connection.execute(f"DELETE FROM {record_table}")
        connection.execute(
            f"""
            INSERT OR REPLACE INTO {manifest_table} (
                id,
                schema_version,
                plane,
                generated_at,
                workspace_root,
                small_file_threshold_bytes,
                indexed_file_count,
                indexed_bytes,
                physical_delete_performed,
                source_files_preserved,
                forbidden_boundaries_json
            )
            VALUES (1, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?)
            """,
            (
                SCHEMA_VERSION,
                plane,
                indexed_at,
                str(workspace_root),
                _SMALL_FILE_BYTES,
                len(records),
                sum(int(record["bytes"]) for record in records),
                json.dumps(forbidden_boundaries or []),
            ),
        )
        for record in records:
            connection.execute(
                f"""
                INSERT OR REPLACE INTO {payload_table} (sha256, bytes, payload)
                VALUES (?, ?, ?)
                """,
                (record["sha256"], record["bytes"], record["payload"]),
            )
            connection.execute(
                f"""
                INSERT OR REPLACE INTO {record_table} (
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
        "sqlite_target_path": index_relpath,
        "indexed_file_count": len(records),
        "indexed_bytes": sum(int(record["bytes"]) for record in records),
        "indexed_payload_count": len({str(record["sha256"]) for record in records}),
        "physical_delete_performed": False,
        "source_files_preserved": True,
        "indexed_at": indexed_at,
    }


def _ensure_text_column(
    connection: sqlite3.Connection,
    *,
    table_name: str,
    column_name: str,
    default_value: str,
) -> None:
    columns = {row[1] for row in connection.execute(f"PRAGMA table_info({table_name})")}
    if column_name in columns:
        return
    escaped_default = default_value.replace("'", "''")
    connection.execute(
        f"ALTER TABLE {table_name} ADD COLUMN {column_name} TEXT NOT NULL DEFAULT '{escaped_default}'"
    )


def _dataset_release_records(workspace_root: Path) -> list[dict[str, Any]]:
    datasets_root = workspace_root / _DATASET_BODY_SKIP
    releases: list[dict[str, Any]] = []
    if not datasets_root.exists():
        return releases
    for layer_root in sorted(path for path in datasets_root.iterdir() if path.is_dir()):
        for version_root in sorted(path for path in layer_root.iterdir() if path.is_dir()):
            stats = _path_stats(version_root, workspace_root=workspace_root, include_dataset_body=True)
            manifest = version_root / "dataset_manifest.yaml"
            releases.append(
                {
                    "layer": layer_root.name,
                    "version": version_root.name,
                    "workspace_relative_path": _workspace_ref(workspace_root, version_root),
                    "manifest_ref": _workspace_ref(workspace_root, manifest) if manifest.exists() else None,
                    "bytes": stats["bytes"],
                    "file_count": stats["file_count"],
                    "manifest_exists": manifest.exists(),
                }
            )
    return releases


def _dataset_file_inventory_records(workspace_root: Path) -> list[dict[str, Any]]:
    datasets_root = workspace_root / _DATASET_BODY_SKIP
    records: list[dict[str, Any]] = []
    if not datasets_root.exists():
        return records
    for path in sorted(item for item in datasets_root.rglob("*") if item.is_file()):
        try:
            stat_result = path.stat()
        except FileNotFoundError:
            continue
        records.append(
            {
                "workspace_relative_path": _workspace_ref(workspace_root, path),
                "bytes": stat_result.st_size,
                "mtime_ns": stat_result.st_mtime_ns,
                "sha256": _sha256_file(path),
            }
        )
    return records


def _apply_asset_index(
    *,
    workspace_root: Path,
    releases: list[dict[str, Any]],
    file_records: list[dict[str, Any]],
) -> dict[str, Any]:
    generated_at = datetime.now(timezone.utc).isoformat()
    index_path = workspace_root / _ASSET_INDEX_PATH
    index_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(index_path) as connection:
        connection.execute("PRAGMA journal_mode=DELETE")
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS asset_index_manifest (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                schema_version INTEGER NOT NULL,
                generated_at TEXT NOT NULL,
                workspace_root TEXT NOT NULL,
                release_count INTEGER NOT NULL,
                file_record_count INTEGER NOT NULL,
                stores_dataset_body INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS asset_releases (
                workspace_relative_path TEXT PRIMARY KEY,
                layer TEXT NOT NULL,
                version TEXT NOT NULL,
                manifest_ref TEXT,
                bytes INTEGER NOT NULL,
                file_count INTEGER NOT NULL,
                manifest_exists INTEGER NOT NULL
            );
            CREATE TABLE IF NOT EXISTS asset_file_inventory (
                workspace_relative_path TEXT PRIMARY KEY,
                sha256 TEXT NOT NULL,
                bytes INTEGER NOT NULL,
                mtime_ns INTEGER NOT NULL
            );
            """
        )
        connection.execute("DELETE FROM asset_releases")
        connection.execute("DELETE FROM asset_file_inventory")
        connection.execute(
            """
            INSERT OR REPLACE INTO asset_index_manifest (
                id, schema_version, generated_at, workspace_root, release_count, file_record_count, stores_dataset_body
            )
            VALUES (1, ?, ?, ?, ?, ?, 0)
            """,
            (SCHEMA_VERSION, generated_at, str(workspace_root), len(releases), len(file_records)),
        )
        for release in releases:
            connection.execute(
                """
                INSERT OR REPLACE INTO asset_releases (
                    workspace_relative_path, layer, version, manifest_ref, bytes, file_count, manifest_exists
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    release["workspace_relative_path"],
                    release["layer"],
                    release["version"],
                    release["manifest_ref"],
                    release["bytes"],
                    release["file_count"],
                    int(bool(release["manifest_exists"])),
                ),
            )
        for record in file_records:
            connection.execute(
                """
                INSERT OR REPLACE INTO asset_file_inventory (
                    workspace_relative_path, sha256, bytes, mtime_ns
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    record["workspace_relative_path"],
                    record["sha256"],
                    record["bytes"],
                    record["mtime_ns"],
                ),
            )
    return {
        "sqlite_target_path": _ASSET_INDEX_PATH,
        "release_count": len(releases),
        "file_record_count": len(file_records),
        "stores_dataset_body": False,
        "generated_at": generated_at,
    }


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _completed_project_capsule_markdown(*, project_id: str, timestamp: str, inspection: dict[str, Any]) -> str:
    planes = inspection.get("plane_summary", {})
    body = planes.get("body", {})
    runtime = planes.get("runtime", {})
    study = planes.get("study", {})
    return "\n".join(
        [
            f"# Semantic Reproducible Capsule: {project_id}",
            "",
            f"Generated at: {timestamp}",
            "",
            "## Scope",
            "",
            "This capsule preserves reproducibility information only. It does not delete files,",
            "store clinical row-level bodies, sign owner receipts, or create typed blockers.",
            "",
            "## Data Body Boundary",
            "",
            f"- Body root: `{_DATASET_BODY_SKIP}`",
            f"- Body bytes: {body.get('bytes', 0)}",
            f"- Body file count: {body.get('file_count', 0)}",
            "",
            "## Process Planes",
            "",
            f"- Runtime bytes: {runtime.get('bytes', 0)}",
            f"- Runtime file count: {runtime.get('file_count', 0)}",
            f"- Study bytes: {study.get('bytes', 0)}",
            f"- Study file count: {study.get('file_count', 0)}",
            "",
            "## Reproduction Contract",
            "",
            "1. Rebuild release and file inventory from `memory/portfolio/data_assets/index.sqlite`.",
            "2. Rebuild runtime small-record inventory from `runtime/index.sqlite`.",
            "3. Rebuild study small-record inventory from `studies/index.sqlite` when present.",
            "4. Keep manuscript exchange packages as exchange artifacts, not authority.",
            "5. Require owner decision before any non-cache physical deletion.",
            "",
        ]
    )


def _completed_project_capsule_payload(
    *,
    project_id: str,
    timestamp: str,
    inspection: dict[str, Any],
    capsule_ref: str,
) -> dict[str, Any]:
    planes = inspection.get("plane_summary", {})
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": "mas_data_lifecycle_semantic_reproducible_capsule",
        "project_id": project_id,
        "generated_at": timestamp,
        "capsule_ref": capsule_ref,
        "data_body_boundary_ref": _DATASET_BODY_SKIP,
        "plane_summary": {
            key: {
                "workspace_relative_path": value.get("workspace_relative_path"),
                "bytes": value.get("bytes", 0),
                "file_count": value.get("file_count", 0),
                "small_file_count": value.get("small_file_count", 0),
            }
            for key, value in planes.items()
            if isinstance(value, dict)
        },
        "reproduction_contract": [
            "Rebuild release and file inventory from memory/portfolio/data_assets/index.sqlite.",
            "Rebuild runtime small-record inventory from runtime/index.sqlite.",
            "Rebuild study small-record inventory from studies/index.sqlite when present.",
            "Treat manuscript packages as exchange artifacts, not authority.",
            "Require owner decision before non-cache physical deletion.",
        ],
        "mutation_policy": {
            "stores_dataset_body": False,
            "physical_delete_performed": False,
            "source_files_preserved": True,
        },
    }


def _governance_refs(project_id: str) -> dict[str, str]:
    prefix = f"{_GOVERNANCE_ROOT}/{project_id}"
    return {
        "study_ttl_pin_audit": f"{prefix}/study_ttl_pin_audit_latest.json",
        "owner_gated_deletion_receipt": f"{prefix}/owner_gated_deletion_receipt_latest.json",
        "omop_like_semantic_mapping": f"{prefix}/omop_like_semantic_mapping_latest.json",
        "sidecar_registry": f"{prefix}/sidecar_registry_latest.json",
        "ro_crate_metadata": f"{prefix}/ro_crate_metadata_latest.json",
    }


def _governance_payload(*, workspace_root: Path, project_id: str, generated_at: str) -> dict[str, Any]:
    studies = _study_ttl_pin_records(workspace_root)
    releases = _dataset_release_records(workspace_root)
    return {
        "generated_at": generated_at,
        "study_ttl_pin_audit": {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "mas_data_lifecycle_study_ttl_pin_audit",
            "project_id": project_id,
            "generated_at": generated_at,
            "study_count": len(studies),
            "studies": studies,
            "physical_delete_performed": False,
        },
        "owner_gated_deletion_receipt": {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "mas_data_lifecycle_owner_gated_deletion_receipt",
            "project_id": project_id,
            "generated_at": generated_at,
            "status": "not_authorized",
            "physical_delete_performed": False,
            "required_before_apply_delete": [
                "owner_decision_ref",
                "important_result_reproduction_ref",
                "study_impact_ref",
                "post_cleanup_readback_ref",
            ],
        },
        "omop_like_semantic_mapping": {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "mas_data_lifecycle_omop_like_semantic_mapping",
            "project_id": project_id,
            "generated_at": generated_at,
            "status": "mapping_manifest_only",
            "clinical_data_transformation_performed": False,
            "stable_keys": ["person_id", "event_date", "site_or_facility", "condition", "medication_exposure"],
            "recommended_dataset_ref": _DATASET_BODY_SKIP,
        },
        "sidecar_registry": {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "mas_data_lifecycle_sidecar_registry",
            "project_id": project_id,
            "generated_at": generated_at,
            "status": "registry_only",
            "clinical_data_transformation_performed": False,
            "allowed_sidecar_types": ["parquet", "duckdb"],
            "release_count": len(releases),
            "release_refs": [release["workspace_relative_path"] for release in releases],
        },
        "ro_crate_metadata": {
            "schema_version": SCHEMA_VERSION,
            "surface_kind": "mas_data_lifecycle_ro_crate_metadata",
            "project_id": project_id,
            "generated_at": generated_at,
            "status": "metadata_only",
            "conforms_to": "RO-Crate-like semantic metadata; not a full RO-Crate package",
            "dataset_root": _DATASET_BODY_SKIP,
            "has_part": [release["workspace_relative_path"] for release in releases],
        },
    }


def _study_ttl_pin_records(workspace_root: Path) -> list[dict[str, Any]]:
    studies_root = workspace_root / "studies"
    if not studies_root.exists():
        return []
    records: list[dict[str, Any]] = []
    for study_root in sorted(path for path in studies_root.iterdir() if path.is_dir()):
        package_refs = [
            _workspace_ref(workspace_root, path)
            for path in (study_root / "manuscript").glob("current_package*")
            if path.exists()
        ]
        records.append(
            {
                "study_id": study_root.name,
                "study_ref": _workspace_ref(workspace_root, study_root),
                "current_package_refs": package_refs,
                "ttl_required_for_non_current_outputs": True,
                "milestone_pin_required_for_retention": True,
                "physical_delete_performed": False,
            }
        )
    return records


def _write_governance_refs(
    *,
    workspace_root: Path,
    refs: dict[str, str],
    governance: dict[str, Any],
) -> list[str]:
    written: list[str] = []
    for key, ref in refs.items():
        path = workspace_root / ref
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(governance[key], ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        written.append(ref)
    return written


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


__all__ = [
    "closeout_completed_project",
    "closeout_data_lifecycle",
    "compact_runtime_lifecycle",
    "compact_study_lifecycle",
    "finalize_governance",
    "index_data_assets",
    "inspect_data_lifecycle",
]
