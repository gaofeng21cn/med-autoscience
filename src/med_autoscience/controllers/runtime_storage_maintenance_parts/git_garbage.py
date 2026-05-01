from __future__ import annotations

from datetime import UTC, datetime
import os
from pathlib import Path
import time
from typing import Any, Mapping

from med_autoscience.controllers import workspace_git_boundary


GIT_TEMP_GARBAGE_MIN_AGE_SECONDS = 6 * 3600


def audit_git_storage(
    workspace_root: Path,
    *,
    older_than_seconds: int = GIT_TEMP_GARBAGE_MIN_AGE_SECONDS,
    apply: bool = False,
) -> dict[str, Any]:
    git_root = workspace_root / ".git"
    now_timestamp = time.time()
    temp_files = _git_temp_garbage_files(
        git_root=git_root,
        now_timestamp=now_timestamp,
        older_than_seconds=older_than_seconds,
    )
    tmp_pack_files = [item for item in temp_files if Path(str(item["path"])).name.startswith("tmp_pack_")]
    tmp_obj_files = [item for item in temp_files if Path(str(item["path"])).name.startswith("tmp_obj_")]
    stale_files = [item for item in temp_files if bool(item.get("stale"))]
    estimated_release_bytes = sum(int(item.get("bytes") or 0) for item in stale_files)
    lock_paths = _git_lock_paths(git_root)
    blockers = ["git_lock_present"] if lock_paths else []
    apply_result: dict[str, Any] | None = None
    hardening_result: dict[str, Any] | None = None
    if apply:
        apply_result = _apply_git_temp_garbage_cleanup(stale_files=stale_files, lock_paths=lock_paths)
        hardening_result = _apply_workspace_git_boundary_hardening(workspace_root=workspace_root)
    return {
        "category": "git",
        "path": str(git_root),
        "bytes": _directory_size_bytes(git_root),
        "risk": "git_object_store",
        "candidate_action": "delete-stale-temp-git-garbage" if stale_files else "audit-only",
        "estimated_release_bytes": estimated_release_bytes,
        "older_than_seconds": max(1, int(older_than_seconds)),
        "tmp_pack_files": tmp_pack_files,
        "tmp_obj_files": tmp_obj_files,
        "temp_garbage_files": temp_files,
        "blockers": blockers,
        "lock_paths": [str(path) for path in lock_paths],
        "restore_command": "delete stale .git/objects temp files after confirming no git lock is present",
        "apply_result": apply_result,
        "hardening_result": hardening_result,
    }


def _directory_size_bytes(path: Path) -> int:
    if not path.exists():
        return 0
    if path.is_file():
        try:
            return path.stat().st_size
        except OSError:
            return 0
    total = 0
    for current_root, _, filenames in os.walk(path):
        current_path = Path(current_root)
        for filename in filenames:
            candidate = current_path / filename
            try:
                total += candidate.stat().st_size
            except OSError:
                continue
    return total


def _git_temp_garbage_files(
    *,
    git_root: Path,
    now_timestamp: float,
    older_than_seconds: int,
) -> list[dict[str, Any]]:
    objects_root = git_root / "objects"
    if not objects_root.exists():
        return []
    older_than = max(1, int(older_than_seconds))
    candidates = list(objects_root.glob("pack/tmp_pack_*"))
    candidates.extend(
        path
        for path in objects_root.glob("*/tmp_obj_*")
        if path.parent.name != "pack"
    )
    reports: list[dict[str, Any]] = []
    for path in sorted(candidates):
        if not path.is_file():
            continue
        try:
            stat_result = path.stat()
        except OSError:
            continue
        age_seconds = max(0, int(now_timestamp - stat_result.st_mtime))
        stale = age_seconds >= older_than
        reports.append(
            {
                "path": str(path),
                "bytes": stat_result.st_size,
                "mtime": datetime.fromtimestamp(stat_result.st_mtime, UTC).replace(microsecond=0).isoformat(),
                "age_seconds": age_seconds,
                "stale": stale,
                "candidate_action": "delete-safe" if stale else "audit-only",
                "blockers": [] if stale else ["too_fresh"],
            }
        )
    return reports


def _git_lock_paths(git_root: Path) -> list[Path]:
    lock_paths = [
        git_root / "index.lock",
        git_root / "gc.pid",
    ]
    pack_root = git_root / "objects" / "pack"
    if pack_root.exists():
        lock_paths.extend(sorted(path for path in pack_root.glob("*.lock") if path.exists()))
    return [path for path in lock_paths if path.exists()]


def _apply_git_temp_garbage_cleanup(
    *,
    stale_files: list[Mapping[str, Any]],
    lock_paths: list[Path],
) -> dict[str, Any]:
    if lock_paths:
        return {
            "status": "blocked_git_lock",
            "deleted_count": 0,
            "deleted_bytes": 0,
            "deleted_files": [],
            "blockers": ["git_lock_present"],
            "lock_paths": [str(path) for path in lock_paths],
        }
    if not stale_files:
        return {
            "status": "nothing_to_delete",
            "deleted_count": 0,
            "deleted_bytes": 0,
            "deleted_files": [],
            "blockers": [],
        }
    deleted_files: list[str] = []
    delete_errors: list[dict[str, str]] = []
    deleted_bytes = 0
    for item in stale_files:
        path = Path(str(item.get("path") or ""))
        if not path.is_file():
            continue
        item_bytes = int(item.get("bytes") or _directory_size_bytes(path))
        try:
            path.unlink()
        except OSError as exc:
            delete_errors.append({"path": str(path), "error": str(exc)})
            continue
        deleted_files.append(str(path))
        deleted_bytes += item_bytes
    status = "deleted" if deleted_files and not delete_errors else "delete_failed"
    if deleted_files and delete_errors:
        status = "partially_deleted"
    return {
        "status": status,
        "deleted_count": len(deleted_files),
        "deleted_bytes": deleted_bytes,
        "deleted_files": deleted_files,
        "delete_errors": delete_errors,
        "blockers": ["delete_error"] if delete_errors else [],
    }


def _apply_workspace_git_boundary_hardening(*, workspace_root: Path) -> dict[str, Any]:
    config_status = "skipped_no_git"
    config_error = None
    if (workspace_root / ".git").exists():
        try:
            configured = workspace_git_boundary.configure_existing_workspace_git(workspace_root=workspace_root)
        except RuntimeError as exc:
            configured = False
            config_status = "config_failed"
            config_error = str(exc)
        else:
            config_status = "configured" if configured else "skipped_no_git"

    gitignore_path = workspace_root / ".gitignore"
    try:
        existing_content = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
        merged_content = (
            workspace_git_boundary.merge_workspace_gitignore_content(existing_content)
            if existing_content
            else workspace_git_boundary.render_workspace_gitignore()
        )
        gitignore_updated = merged_content != existing_content
        if gitignore_updated:
            gitignore_path.write_text(merged_content, encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return {
            "status": "partial" if config_status == "configured" else "failed",
            "git_config_status": config_status,
            "git_config_error": config_error,
            "gitignore_status": "failed",
            "gitignore_error": str(exc),
            "gitignore_path": str(gitignore_path),
        }

    if config_status == "config_failed":
        status = "partial" if gitignore_updated else "failed"
    else:
        status = "hardened" if config_status == "configured" or gitignore_updated else "unchanged"
    return {
        "status": status,
        "git_config_status": config_status,
        "git_config_error": config_error,
        "gitignore_status": "updated" if gitignore_updated else "unchanged",
        "gitignore_path": str(gitignore_path),
    }
