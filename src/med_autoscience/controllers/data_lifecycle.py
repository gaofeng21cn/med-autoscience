from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Iterable

from med_autoscience.workspace_paths import DATASETS_RELPATH


SCHEMA_VERSION = 1
INSPECTION_SURFACE_KIND = "mas_data_lifecycle_inspection"
CLOSEOUT_SURFACE_KIND = "mas_data_lifecycle_closeout_plan"
_CANDIDATE_LIMIT = 200
_DATASET_BODY_SKIP = DATASETS_RELPATH.as_posix()
_CACHE_DIR_NAMES = {".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}


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


def _candidate(*, workspace_root: Path, path: Path, category: str) -> dict[str, Any]:
    action_by_category = {
        "runtime": "review_runtime_retention",
        "archive": "restore_proof_required_before_cleanup",
        "artifact": "owner_review_required_before_cleanup",
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


def _path_stats(path: Path, *, workspace_root: Path) -> dict[str, int]:
    if path.is_file():
        try:
            return {"bytes": path.stat().st_size, "file_count": 1}
        except FileNotFoundError:
            return {"bytes": 0, "file_count": 0}
    total_bytes = 0
    file_count = 0
    for current_root, dirnames, filenames in os.walk(path):
        current_path = Path(current_root)
        if _is_under_dataset_body(current_path, workspace_root=workspace_root):
            dirnames[:] = []
            continue
        dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in _CACHE_DIR_NAMES)
        for filename in filenames:
            file_path = current_path / filename
            try:
                total_bytes += file_path.stat().st_size
            except FileNotFoundError:
                continue
            file_count += 1
    return {"bytes": total_bytes, "file_count": file_count}


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


__all__ = ["closeout_data_lifecycle", "inspect_data_lifecycle"]
