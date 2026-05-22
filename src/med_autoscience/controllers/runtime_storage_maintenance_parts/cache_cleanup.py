from __future__ import annotations

import os
from pathlib import Path
import shutil
from typing import Any, Mapping


_DELETE_SAFE_DIR_NAMES = {
    ".cache",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "cache",
    "tmp",
}
_DELETE_SAFE_FILE_SUFFIXES = (".tmp", ".pyc", ".pyo")


def delete_safe_candidates(
    workspace_root: Path,
    *,
    apply: bool = False,
    scan_roots: list[Path] | None = None,
) -> dict[str, Any]:
    candidates: list[dict[str, Any]] = []
    if not workspace_root.exists():
        return {
            "category": "cache",
            "workspace_root": str(workspace_root),
            "candidate_action": "delete-safe",
            "bytes": 0,
            "estimated_release_bytes": 0,
            "actual_release_bytes": 0,
            "candidates": [],
            "apply_result": empty_cache_apply_result("workspace_missing") if apply else None,
            "deleted_count": 0,
            "deleted_bytes": 0,
            "skipped": [],
            "errors": [],
        }
    roots_to_scan = cache_scan_roots(workspace_root=workspace_root, scan_roots=scan_roots)
    for root in roots_to_scan:
        if not root.exists():
            continue
        for current_root, dirnames, filenames in os.walk(root):
            current = Path(current_root)
            dirnames[:] = [name for name in dirnames if name not in {".git", "storage_audit"}]
            for dirname in list(dirnames):
                if dirname not in _DELETE_SAFE_DIR_NAMES:
                    continue
                candidate = current / dirname
                candidate_bytes = _directory_size_bytes(candidate)
                candidates.append(
                    {
                        "path": str(candidate),
                        "bytes": candidate_bytes,
                        "candidate_action": "delete-safe",
                        "risk": "rebuildable_process_cache",
                    }
                )
                dirnames.remove(dirname)
            for filename in filenames:
                if filename == ".DS_Store" or filename.endswith(_DELETE_SAFE_FILE_SUFFIXES):
                    candidate = current / filename
                    candidates.append(
                        {
                            "path": str(candidate),
                            "bytes": _directory_size_bytes(candidate),
                            "candidate_action": "delete-safe",
                            "risk": "rebuildable_process_cache",
                        }
                    )
    total_bytes = sum(int(item["bytes"]) for item in candidates)
    apply_result = apply_delete_safe_candidates(workspace_root=workspace_root, candidates=candidates) if apply else None
    deleted_bytes = int((apply_result or {}).get("deleted_bytes") or 0)
    deleted_count = int((apply_result or {}).get("deleted_count") or 0)
    skipped = list((apply_result or {}).get("skipped") or [])
    errors = list((apply_result or {}).get("errors") or [])
    return {
        "category": "cache",
        "workspace_root": str(workspace_root),
        "candidate_action": "delete-safe",
        "bytes": total_bytes,
        "estimated_release_bytes": total_bytes,
        "actual_release_bytes": deleted_bytes,
        "candidates": candidates,
        "apply_result": apply_result,
        "deleted_count": deleted_count,
        "deleted_bytes": deleted_bytes,
        "skipped": skipped,
        "errors": errors,
    }


def cache_scan_roots(*, workspace_root: Path, scan_roots: list[Path] | None) -> list[Path]:
    if scan_roots is None:
        return [workspace_root]
    resolved_roots: list[Path] = []
    seen: set[Path] = set()
    for root in scan_roots:
        resolved_root = root.expanduser().resolve()
        if not path_is_inside_workspace(resolved_root, workspace_root):
            continue
        if resolved_root in seen:
            continue
        seen.add(resolved_root)
        resolved_roots.append(resolved_root)
    return resolved_roots


def empty_cache_apply_result(status: str) -> dict[str, Any]:
    return {
        "status": status,
        "deleted_count": 0,
        "deleted_bytes": 0,
        "deleted_paths": [],
        "skipped": [],
        "errors": [],
    }


def apply_delete_safe_candidates(
    *,
    workspace_root: Path,
    candidates: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if not candidates:
        return empty_cache_apply_result("nothing_to_delete")
    deleted_paths: list[str] = []
    skipped: list[dict[str, str]] = []
    errors: list[dict[str, str]] = []
    deleted_bytes = 0
    for item in candidates:
        candidate = Path(str(item.get("path") or ""))
        if not path_is_inside_workspace(candidate, workspace_root):
            errors.append({"path": str(candidate), "error": "outside_workspace"})
            continue
        if not candidate.exists() and not candidate.is_symlink():
            skipped.append({"path": str(candidate), "reason": "missing"})
            continue
        item_bytes = int(item.get("bytes") or _directory_size_bytes(candidate))
        try:
            if candidate.is_symlink() or candidate.is_file():
                candidate.unlink()
            elif candidate.is_dir():
                shutil.rmtree(candidate)
            else:
                skipped.append({"path": str(candidate), "reason": "unsupported_file_type"})
                continue
        except OSError as exc:
            errors.append({"path": str(candidate), "error": str(exc)})
            continue
        deleted_paths.append(str(candidate))
        deleted_bytes += item_bytes
    if errors and deleted_paths:
        status = "partially_deleted"
    elif errors:
        status = "delete_failed"
    elif skipped and deleted_paths:
        status = "partially_deleted"
    elif deleted_paths:
        status = "deleted"
    elif skipped:
        status = "nothing_deleted"
    else:
        status = "nothing_to_delete"
    return {
        "status": status,
        "deleted_count": len(deleted_paths),
        "deleted_bytes": deleted_bytes,
        "deleted_paths": deleted_paths,
        "skipped": skipped,
        "errors": errors,
    }


def path_is_inside_workspace(path: Path, workspace_root: Path) -> bool:
    try:
        path.absolute().relative_to(workspace_root.absolute())
    except ValueError:
        return False
    return True


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
