from __future__ import annotations

from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import time
from typing import Any, Mapping

from med_autoscience.controllers import workspace_git_boundary


GIT_TEMP_GARBAGE_MIN_AGE_SECONDS = 6 * 3600
EMPTY_REPO_REINITIALIZE_OBJECT_THRESHOLD_BYTES = 128 * 1024 * 1024


def audit_git_storage(
    workspace_root: Path,
    *,
    older_than_seconds: int = GIT_TEMP_GARBAGE_MIN_AGE_SECONDS,
    apply: bool = False,
    reinitialize_empty_workspace_git: bool = False,
    retire_workspace_root_git: bool = False,
) -> dict[str, Any]:
    git_root = workspace_root / ".git"
    health_before = _git_health(workspace_root=workspace_root)
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
    empty_repo_reinitialize_result = None
    if apply and reinitialize_empty_workspace_git:
        empty_repo_reinitialize_result = _reinitialize_empty_workspace_git(
            workspace_root=workspace_root,
            eligibility=health_before["reinitialize_eligibility"],
        )
    workspace_root_git_retirement_result = None
    if apply and retire_workspace_root_git:
        workspace_root_git_retirement_result = _retire_workspace_root_git(
            workspace_root=workspace_root,
            health=health_before,
        )
    health_after = _git_health(workspace_root=workspace_root)
    health = health_after if empty_repo_reinitialize_result or workspace_root_git_retirement_result else health_before
    return {
        "category": "git",
        "path": str(git_root),
        "bytes": _directory_size_bytes(git_root),
        "risk": "git_object_store",
        "candidate_action": _git_candidate_action(health=health, stale_files=stale_files),
        "estimated_release_bytes": estimated_release_bytes,
        "older_than_seconds": max(1, int(older_than_seconds)),
        "health": health,
        "tmp_pack_files": tmp_pack_files,
        "tmp_obj_files": tmp_obj_files,
        "temp_garbage_files": temp_files,
        "blockers": sorted(set([*blockers, *health["reinitialize_eligibility"]["blockers"]])),
        "lock_paths": [str(path) for path in lock_paths],
        "restore_command": "delete stale .git/objects temp files after confirming no git lock is present",
        "apply_result": apply_result,
        "hardening_result": hardening_result,
        "empty_repo_reinitialize_result": empty_repo_reinitialize_result,
        "workspace_root_git_retirement_result": workspace_root_git_retirement_result,
    }


def _git_candidate_action(*, health: Mapping[str, Any], stale_files: list[Mapping[str, Any]]) -> str:
    recommended_action = str(health.get("recommended_action") or "").strip()
    if recommended_action == "reinitialize_empty_workspace_git":
        return recommended_action
    if stale_files:
        return "delete-stale-temp-git-garbage"
    return recommended_action or "audit-only"


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


def _utc_run_id() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _run_git_command(
    args: list[str],
    *,
    workspace_root: Path,
    check: bool = False,
) -> subprocess.CompletedProcess[str]:
    git_bin = shutil.which("git") or "git"
    try:
        result = subprocess.run(
            [git_bin, *args],
            cwd=workspace_root,
            check=False,
            text=True,
            capture_output=True,
        )
    except FileNotFoundError as exc:
        raise RuntimeError("git executable is required for MedAutoScience workspace Git maintenance.") from exc
    if check and result.returncode != 0:
        command = " ".join(["git", *args])
        message = result.stderr.strip() or result.stdout.strip() or f"{command} failed"
        raise RuntimeError(message)
    return result


def _git_output(args: list[str], *, workspace_root: Path) -> dict[str, Any]:
    result = _run_git_command(args, workspace_root=workspace_root)
    return {
        "args": ["git", *args],
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }


def _git_health(*, workspace_root: Path) -> dict[str, Any]:
    git_root = workspace_root / ".git"
    objects_root = git_root / "objects"
    pack_root = objects_root / "pack"
    object_store_bytes = _directory_size_bytes(objects_root)
    lock_paths = _git_lock_paths(git_root)
    git_exists = git_root.exists()
    has_commits = _git_has_commits(workspace_root=workspace_root) if git_exists else False
    remote_count = _git_count_lines(["remote"], workspace_root=workspace_root) if git_exists else 0
    stash_count = _git_count_lines(["stash", "list"], workspace_root=workspace_root) if git_exists else 0
    linked_worktree_count = _linked_worktree_count(workspace_root=workspace_root) if git_exists else 0
    untracked_count = _git_count_lines(["ls-files", "-o", "--exclude-standard"], workspace_root=workspace_root) if git_exists else 0
    ignored_candidate_count = (
        _git_count_lines(["ls-files", "-o", "-i", "--exclude-standard"], workspace_root=workspace_root) if git_exists else 0
    )
    loose_object_bytes = max(0, object_store_bytes - _directory_size_bytes(pack_root))
    pack_bytes = _directory_size_bytes(pack_root)
    eligibility = _empty_repo_reinitialize_eligibility(
        git_exists=git_exists,
        has_commits=has_commits,
        object_store_bytes=object_store_bytes,
        lock_paths=lock_paths,
        remote_count=remote_count,
        stash_count=stash_count,
        linked_worktree_count=linked_worktree_count,
    )
    return {
        "git_exists": git_exists,
        "has_commits": has_commits,
        "bytes": _directory_size_bytes(git_root),
        "object_store_bytes": object_store_bytes,
        "loose_object_bytes": loose_object_bytes,
        "pack_bytes": pack_bytes,
        "untracked_count": untracked_count,
        "ignored_candidate_count": ignored_candidate_count,
        "remote_count": remote_count,
        "stash_count": stash_count,
        "linked_worktree_count": linked_worktree_count,
        "lock_paths": [str(path) for path in lock_paths],
        "recommended_action": _recommended_git_action(
            git_exists=git_exists,
            has_commits=has_commits,
            object_store_bytes=object_store_bytes,
            eligibility=eligibility,
        ),
        "reinitialize_eligibility": eligibility,
        "workspace_root_git_retirement_eligibility": _workspace_root_git_retirement_eligibility(
            git_root=git_root,
            git_exists=git_exists,
            lock_paths=lock_paths,
            remote_count=remote_count,
            stash_count=stash_count,
            linked_worktree_count=linked_worktree_count,
        ),
    }


def _workspace_root_git_retirement_eligibility(
    *,
    git_root: Path,
    git_exists: bool,
    lock_paths: list[Path],
    remote_count: int,
    stash_count: int,
    linked_worktree_count: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    reasons: list[str] = []
    if not git_exists:
        reasons.append("workspace_root_git_already_absent")
    elif not git_root.is_dir():
        blockers.append("git_root_not_directory")
    else:
        reasons.append("workspace_root_git_present")
    if lock_paths:
        blockers.append("git_lock_present")
    if remote_count:
        blockers.append("has_remotes")
    if stash_count:
        reasons.append("has_stashes_archived")
    if linked_worktree_count:
        blockers.append("has_linked_worktrees")
    return {
        "eligible": git_exists and not blockers,
        "already_absent": not git_exists,
        "blockers": blockers,
        "reasons": reasons,
    }


def _git_has_commits(*, workspace_root: Path) -> bool:
    result = _run_git_command(["rev-parse", "--verify", "HEAD"], workspace_root=workspace_root)
    return result.returncode == 0


def _git_count_lines(args: list[str], *, workspace_root: Path) -> int:
    result = _run_git_command(args, workspace_root=workspace_root)
    if result.returncode != 0:
        return 0
    lines = [line for line in result.stdout.splitlines() if line.strip()]
    return len(lines)


def _linked_worktree_count(*, workspace_root: Path) -> int:
    result = _run_git_command(["worktree", "list", "--porcelain"], workspace_root=workspace_root)
    if result.returncode != 0:
        return 0
    paths = [line for line in result.stdout.splitlines() if line.startswith("worktree ")]
    return max(0, len(paths) - 1)


def _empty_repo_reinitialize_eligibility(
    *,
    git_exists: bool,
    has_commits: bool,
    object_store_bytes: int,
    lock_paths: list[Path],
    remote_count: int,
    stash_count: int,
    linked_worktree_count: int,
) -> dict[str, Any]:
    blockers: list[str] = []
    reasons: list[str] = []
    if not git_exists:
        blockers.append("missing_git_root")
    if has_commits:
        blockers.append("has_commits")
    if lock_paths:
        blockers.append("git_lock_present")
    if remote_count:
        blockers.append("has_remotes")
    if stash_count:
        blockers.append("has_stashes")
    if linked_worktree_count:
        blockers.append("has_linked_worktrees")
    if object_store_bytes <= 0:
        blockers.append("empty_object_store")
    elif object_store_bytes >= EMPTY_REPO_REINITIALIZE_OBJECT_THRESHOLD_BYTES:
        reasons.append("empty_repo_object_store_oversized")
    else:
        reasons.append("empty_repo_object_store_present")
    return {
        "eligible": not blockers,
        "blockers": blockers,
        "reasons": reasons,
        "object_threshold_bytes": EMPTY_REPO_REINITIALIZE_OBJECT_THRESHOLD_BYTES,
    }


def _recommended_git_action(
    *,
    git_exists: bool,
    has_commits: bool,
    object_store_bytes: int,
    eligibility: Mapping[str, Any],
) -> str:
    if bool(eligibility.get("eligible")):
        return "reinitialize_empty_workspace_git"
    if not git_exists:
        return "workspace_root_git_absent"
    if has_commits and object_store_bytes >= EMPTY_REPO_REINITIALIZE_OBJECT_THRESHOLD_BYTES:
        return "manual_git_gc_review"
    return "audit-only"


def _reinitialize_empty_workspace_git(
    *,
    workspace_root: Path,
    eligibility: Mapping[str, Any],
) -> dict[str, Any]:
    if not bool(eligibility.get("eligible")):
        return {
            "status": "blocked_not_eligible",
            "blockers": list(eligibility.get("blockers") or []),
            "reasons": list(eligibility.get("reasons") or []),
        }
    git_root = workspace_root / ".git"
    before_bytes = _directory_size_bytes(git_root)
    try:
        shutil.rmtree(git_root)
        workspace_git_boundary.ensure_workspace_git(workspace_root=workspace_root, initialize_git=True)
        _apply_workspace_git_boundary_hardening(workspace_root=workspace_root)
    except (OSError, RuntimeError) as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "blockers": ["reinitialize_failed"],
            "before_bytes": before_bytes,
            "after_bytes": _directory_size_bytes(git_root),
        }
    after_bytes = _directory_size_bytes(git_root)
    return {
        "status": "reinitialized",
        "before_bytes": before_bytes,
        "after_bytes": after_bytes,
        "released_bytes": max(0, before_bytes - after_bytes),
        "blockers": [],
    }


def _retire_workspace_root_git(
    *,
    workspace_root: Path,
    health: Mapping[str, Any],
) -> dict[str, Any]:
    git_root = workspace_root / ".git"
    eligibility = _mapping(health.get("workspace_root_git_retirement_eligibility"))
    if bool(eligibility.get("already_absent")):
        return {
            "status": "already_retired",
            "blockers": [],
            "git_dir": str(git_root),
        }
    if not bool(eligibility.get("eligible")):
        return {
            "status": "blocked_not_eligible",
            "blockers": list(eligibility.get("blockers") or []),
            "reasons": list(eligibility.get("reasons") or []),
            "git_dir": str(git_root),
        }

    run_id = _utc_run_id()
    archive_root = workspace_root / "artifacts" / "runtime" / "lifecycle_migration" / "workspace_root_git_retirement" / run_id
    archive_path = archive_root / "workspace_root_git.tar.gz"
    manifest_path = archive_root / "manifest.json"
    latest_path = archive_root.parent / "latest.json"
    before_bytes = _directory_size_bytes(git_root)
    before = {
        "health": dict(health),
        "git_status_short_branch": _git_output(["status", "--short", "--branch"], workspace_root=workspace_root),
        "git_rev_list_count_head": _git_output(["rev-list", "--count", "HEAD"], workspace_root=workspace_root),
        "git_log_oneline_decorate": _git_output(["log", "--oneline", "--decorate", "-20"], workspace_root=workspace_root),
        "git_remote_verbose": _git_output(["remote", "-v"], workspace_root=workspace_root),
        "git_stash_list": _git_output(["stash", "list"], workspace_root=workspace_root),
        "git_worktree_list_porcelain": _git_output(["worktree", "list", "--porcelain"], workspace_root=workspace_root),
    }
    archive_root.mkdir(parents=True, exist_ok=True)
    try:
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(git_root, arcname=".git")
        archive_sha256 = _sha256_file(archive_path)
        shutil.rmtree(git_root)
    except (OSError, tarfile.TarError) as exc:
        return {
            "status": "failed",
            "error": str(exc),
            "blockers": ["workspace_root_git_retirement_failed"],
            "git_dir": str(git_root),
            "archive_path": str(archive_path),
            "before_bytes": before_bytes,
            "after_bytes": _directory_size_bytes(git_root),
        }

    after_health = _git_health(workspace_root=workspace_root)
    manifest = {
        "surface_kind": "workspace_root_git_retirement_manifest",
        "schema_version": 1,
        "run_id": run_id,
        "recorded_at": datetime.now(UTC).replace(microsecond=0).isoformat(),
        "workspace_root": str(workspace_root),
        "git_dir": str(git_root),
        "status": "retired",
        "before": before,
        "after": {"health": after_health},
        "archive": {
            "path": str(archive_path),
            "sha256": archive_sha256,
            "bytes": _directory_size_bytes(archive_path),
        },
        "restore_command": (
            f"tar -xzf {archive_path} -C {workspace_root} "
            f"&& test -d {git_root}"
        ),
        "authority_note": (
            "Root Git is archived for restore only; OPL owns runtime lifecycle and provider attempts, "
            "while MAS keeps restore locators, provenance refs, and artifact authority receipts."
        ),
    }
    _write_json(manifest_path, manifest)
    latest_payload = {
        "surface_kind": "workspace_root_git_retirement_latest",
        "schema_version": 1,
        "run_id": run_id,
        "recorded_at": manifest["recorded_at"],
        "workspace_root": str(workspace_root),
        "status": "retired",
        "manifest_path": str(manifest_path),
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha256,
        "restore_command": manifest["restore_command"],
    }
    _write_json(latest_path, latest_payload)
    return {
        "status": "retired",
        "blockers": [],
        "run_id": run_id,
        "git_dir": str(git_root),
        "manifest_path": str(manifest_path),
        "latest_path": str(latest_path),
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha256,
        "restore_command": manifest["restore_command"],
        "before_bytes": before_bytes,
        "after_bytes": _directory_size_bytes(git_root),
        "released_bytes": before_bytes,
        "verified_git_absent": not git_root.exists(),
    }


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
