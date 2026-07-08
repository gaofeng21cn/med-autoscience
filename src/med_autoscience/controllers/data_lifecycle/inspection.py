from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from med_autoscience.workspace_paths import DATASETS_RELPATH


DATASET_BODY_SKIP = DATASETS_RELPATH.as_posix()
CANDIDATE_LIMIT = 200
CACHE_DIR_NAMES = {".pytest_cache", ".mypy_cache", ".ruff_cache", "__pycache__"}
SMALL_FILE_BYTES = 16 * 1024


def mutation_policy() -> dict[str, Any]:
    return {
        "read_only": True,
        "dry_run_only": True,
        "writes_workspace": False,
        "writes_runtime": False,
        "physical_cleanup_performed": False,
        "physical_delete_performed": False,
        "physical_cleanup_owner": "one-person-lab",
    }


def management_mode(workspace_root: Path) -> dict[str, Any]:
    return {
        "surface": "mas_data_lifecycle.v1",
        "mode": "read_only_inspection",
        "runtime_owner": "opl_provider_backed_stage_runtime",
        "physical_cleanup_owner": "one-person-lab",
        "data_datasets": {
            "root": DATASET_BODY_SKIP,
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
            "data_datasets": workspace_ref(workspace_root, workspace_root / DATASET_BODY_SKIP),
            "studies": workspace_ref(workspace_root, workspace_root / "studies"),
            "runtime": workspace_ref(workspace_root, workspace_root / "runtime"),
            "memory": workspace_ref(workspace_root, workspace_root / "memory"),
        },
    }


def retention_faces(workspace_root: Path) -> dict[str, Any]:
    roots = {
        "data": workspace_root / "data",
        "data_datasets": workspace_root / DATASET_BODY_SKIP,
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
            "ref": workspace_ref(workspace_root, path),
            "exists": path.exists(),
            "generic_cleanup_allowed": False if key == "data_datasets" else None,
        }
        for key, path in roots.items()
    }


def lifecycle_gaps(workspace_root: Path, *, retention_faces: dict[str, Any]) -> list[dict[str, Any]]:
    gaps: list[dict[str, Any]] = []
    if not retention_faces["memory"]["exists"]:
        gaps.append(gap("missing_memory_root", "memory"))
    if not retention_faces["data_asset_registry"]["exists"]:
        gaps.append(gap("missing_data_asset_registry_plane", "memory/portfolio/data_assets"))
    if retention_faces["runtime_archives"]["exists"] and not (workspace_root / "runtime" / "restore_index").exists():
        gaps.append(gap("missing_runtime_restore_index_for_archives", "runtime/restore_index"))
    if retention_faces["studies"]["exists"] and not retention_faces["artifact_runtime"]["exists"]:
        gaps.append(gap("missing_workspace_runtime_artifact_projection", "artifacts/runtime"))
    return gaps


def plane_summary(workspace_root: Path) -> dict[str, Any]:
    planes = {
        "body": workspace_root / DATASET_BODY_SKIP,
        "index": workspace_root / "memory" / "portfolio" / "data_assets",
        "study": workspace_root / "studies",
        "runtime": workspace_root / "runtime",
        "export": workspace_root / "manuscript",
        "retention": workspace_root / "memory" / "portfolio" / "data_assets" / "retention",
    }
    return {
        name: {
            **path_stats(
                path,
                workspace_root=workspace_root,
                skip_cache=False,
                include_dataset_body=name == "body",
            ),
            "workspace_relative_path": workspace_ref(workspace_root, path),
            "exists": path.exists(),
            "generic_cleanup_allowed": False if name == "body" else None,
        }
        for name, path in planes.items()
    }


def gap(gap_type: str, ref: str) -> dict[str, str]:
    return {
        "gap_type": gap_type,
        "ref": ref,
        "severity": "info",
        "owner_surface": "mas_data_lifecycle_read_only_projection",
    }


def cleanup_candidates(workspace_root: Path) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    for category, units in candidate_units(workspace_root).items():
        for path in units:
            if not path.exists() or is_under_dataset_body(path, workspace_root=workspace_root):
                continue
            candidate = candidate_payload(workspace_root=workspace_root, path=path, category=category)
            if candidate["file_count"] == 0 and candidate["bytes"] == 0:
                continue
            candidates.append(candidate)
            if len(candidates) >= CANDIDATE_LIMIT:
                return candidates
    return candidates


def candidate_units(workspace_root: Path) -> dict[str, tuple[Path, ...]]:
    return {
        "runtime": (
            *direct_children(workspace_root / "runtime" / "quests"),
            *direct_children(workspace_root / "runtime" / "runs"),
        ),
        "archive": (
            *direct_children(workspace_root / "runtime" / "archives"),
            *direct_children(workspace_root / "archive"),
            *direct_children(workspace_root / "archives"),
        ),
        "artifact": (
            *existing_paths(workspace_root / "artifacts" / "runtime"),
            *(workspace_root / "studies").glob("*/artifacts"),
        ),
        "exchange": current_package_units(workspace_root),
        "cache": tuple(path for path in workspace_root.iterdir() if path.name in CACHE_DIR_NAMES)
        if workspace_root.exists()
        else (),
    }


def direct_children(root: Path) -> tuple[Path, ...]:
    if not root.exists():
        return ()
    if root.is_file():
        return (root,)
    return tuple(sorted(root.iterdir(), key=lambda path: path.name))


def existing_paths(*paths: Path) -> tuple[Path, ...]:
    return tuple(path for path in paths if path.exists())


def current_package_units(workspace_root: Path) -> tuple[Path, ...]:
    roots = [workspace_root / "manuscript"]
    studies_root = workspace_root / "studies"
    if studies_root.exists():
        roots.extend(study / "manuscript" for study in studies_root.iterdir() if study.is_dir())
    paths: list[Path] = []
    for root in roots:
        paths.extend(existing_paths(root / "current_package", root / "current_package.zip"))
    return tuple(paths)


def candidate_payload(*, workspace_root: Path, path: Path, category: str) -> dict[str, Any]:
    action_by_category = {
        "runtime": "review_runtime_retention",
        "archive": "restore_proof_required_before_cleanup",
        "artifact": "owner_review_required_before_cleanup",
        "exchange": "retain_as_human_facing_exchange_surface",
        "cache": "delete_safe_cache_candidate",
    }
    stats = path_stats(path, workspace_root=workspace_root)
    return {
        "workspace_relative_path": workspace_ref(workspace_root, path),
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


def path_stats(
    path: Path,
    *,
    workspace_root: Path,
    skip_cache: bool = True,
    include_dataset_body: bool = False,
) -> dict[str, int]:
    if path.is_file():
        try:
            size = path.stat().st_size
            return {"bytes": size, "file_count": 1, "small_file_count": int(size < SMALL_FILE_BYTES)}
        except FileNotFoundError:
            return {"bytes": 0, "file_count": 0, "small_file_count": 0}
    total_bytes = 0
    file_count = 0
    small_file_count = 0
    if not path.exists():
        return {"bytes": 0, "file_count": 0, "small_file_count": 0}
    for current_root, dirnames, filenames in os.walk(path):
        current_path = Path(current_root)
        if not include_dataset_body and is_under_dataset_body(current_path, workspace_root=workspace_root):
            dirnames[:] = []
            continue
        if skip_cache:
            dirnames[:] = sorted(dirname for dirname in dirnames if dirname not in CACHE_DIR_NAMES)
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
            if size < SMALL_FILE_BYTES:
                small_file_count += 1
    return {"bytes": total_bytes, "file_count": file_count, "small_file_count": small_file_count}


def closeout_operation(candidate: dict[str, Any]) -> dict[str, Any]:
    return {
        **candidate,
        "plan_action": "handoff_to_owner_for_review",
        "dry_run": True,
        "writes_workspace": False,
        "physical_delete_performed": False,
    }


def is_under_dataset_body(path: Path, *, workspace_root: Path) -> bool:
    try:
        path.resolve().relative_to((workspace_root / DATASET_BODY_SKIP).resolve())
        return True
    except ValueError:
        return False


def workspace_ref(workspace_root: Path, path: Path) -> str:
    try:
        return path.expanduser().resolve().relative_to(workspace_root).as_posix()
    except ValueError:
        return path.as_posix()
