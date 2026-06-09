from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "historical_body_retention"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"
_TEXT_REF_SUFFIXES = {".json", ".jsonl", ".log", ".txt", ".md"}
_SYMLINK_BODY_SUFFIXES = {".tar.gz", ".zip", ".gz"}


def run_historical_body_retention(
    *,
    root: Path,
    apply: bool,
    cold_store_root: Path,
    min_mb: int = 16,
    max_files: int | None = None,
) -> dict[str, Any]:
    resolved_root = _absolute_no_resolve(Path(root))
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    cold_root = _cold_store_root(root=resolved_root, cold_store_root=cold_store_root)
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    moved_count = 0
    deduped_count = 0
    retained_count = 0
    actual_release_bytes = 0

    for path in _candidate_paths(resolved_root):
        inspection = _inspect_candidate(root=resolved_root, path=path, threshold_bytes=threshold_bytes)
        if inspection.get("status") == "blocked":
            blockers.append(inspection)
            continue
        if inspection.get("status") != "candidate":
            continue
        if max_files is not None and len(candidates) >= max(0, int(max_files)):
            break
        if apply:
            applied = _apply_body_retention(
                root=resolved_root,
                path=path,
                inspection=inspection,
                cold_root=cold_root,
                recorded_at=recorded_at,
            )
            inspection.update(applied)
            actual_release_bytes += int(applied.get("online_release_bytes") or 0)
            if applied.get("status") == "moved_to_cold_object":
                moved_count += 1
            elif applied.get("status") == "deduped_to_existing_cold_object":
                deduped_count += 1
            elif applied.get("status") == "already_retained_in_cold_object":
                retained_count += 1
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(inspection)
        candidates.append(inspection)

    status = (
        "applied"
        if apply and (moved_count or deduped_count or retained_count)
        else "blocked"
        if apply and blockers
        else "planned"
        if candidates
        else "nothing_to_retain"
        if not blockers
        else "blocked"
    )
    receipt = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "recorded_at": recorded_at,
        "root": str(resolved_root),
        "apply": bool(apply),
        "min_bytes": threshold_bytes,
        "max_files": max_files,
        "cold_store_root": str(cold_root),
        "candidate_count": len(candidates),
        "moved_count": moved_count,
        "deduped_count": deduped_count,
        "already_retained_count": retained_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "mutation_policy": {
            "moves_historical_body": bool(apply),
            "keeps_original_path_as_ref_or_symlink": bool(apply),
            "deletes_domain_truth": False,
            "deletes_data_assets": False,
            "keeps_latest_aliases": True,
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


def _candidate_paths(root: Path) -> list[Path]:
    if root.is_file():
        return [root]
    if not root.exists():
        return []
    return sorted(path for path in root.rglob("*") if path.is_file() and not path.is_symlink())


def _inspect_candidate(*, root: Path, path: Path, threshold_bytes: int) -> dict[str, Any]:
    surface_kind = _historical_surface_kind(root=root, path=path)
    if surface_kind is None:
        return {"status": "not_historical_body", "path": str(path)}
    try:
        size_bytes = path.stat().st_size
    except OSError as exc:
        return {"status": "blocked", "reason": "stat_failed", "path": str(path), "error": str(exc)}
    if size_bytes < threshold_bytes:
        return {
            "status": "below_threshold",
            "path": str(path),
            "workspace_relative_path": _relative_to_root(root=root, path=path),
            "bytes": size_bytes,
            "historical_surface_kind": surface_kind,
        }
    sha256 = _sha256(path)
    return {
        "status": "candidate",
        "path": str(path),
        "workspace_relative_path": _relative_to_root(root=root, path=path),
        "bytes": size_bytes,
        "sha256": sha256,
        "historical_surface_kind": surface_kind,
        "retention_mode": _retention_mode(path),
        "restore_command": f"cp <cold_object_path> {path}",
    }


def _historical_surface_kind(*, root: Path, path: Path) -> str | None:
    root_absolute = _absolute_no_resolve(root)
    path_absolute = _absolute_no_resolve(path)
    try:
        relative_parts = path_absolute.relative_to(root_absolute).parts
    except ValueError:
        relative_parts = ()
    absolute_parts = path_absolute.parts
    classification_parts = (*absolute_parts, *relative_parts)
    if ("data" in absolute_parts and "datasets" in absolute_parts) or ".git" in relative_parts:
        return None
    if path.name in {"latest.json", "latest.jsonl"}:
        return None
    if path.name.endswith((".cold_ref.json", ".detail_ref.json")):
        return None
    if _path_has(classification_parts, ("archive", "legacy_root_surfaces")):
        if "storage_audit" in classification_parts and path.suffix == ".json":
            return "legacy_root_storage_audit_json"
        if "inbox" in classification_parts and _full_suffix(path) == ".zip":
            return "legacy_root_inbox_raw_archive_body"
        if path.suffix in {".log", ".jsonl"} and "logs" in classification_parts:
            return "legacy_root_log"
    if _path_has(classification_parts, ("archive", "legacy_ops_surfaces")) and path.suffix in {".json", ".jsonl", ".log"}:
        return "legacy_ops_surface_history_body"
    if _path_has(classification_parts, ("runtime", "artifacts", "legacy_control_surface_migration", "history")):
        if path.suffix in {".log", ".jsonl", ".json"}:
            return "legacy_control_surface_history_body"
    if _path_has(classification_parts, ("runtime", "artifacts", "legacy_physical_cleanup", "history")):
        if path.suffix == ".json":
            return "legacy_physical_cleanup_history_body"
    if _path_has(classification_parts, ("runtime", "artifacts", "lifecycle_migration")) and "quest_git_archives" in classification_parts:
        if _full_suffix(path) in {".tar.gz", ".zip"}:
            return "quest_git_archive_body"
    if _path_has(classification_parts, ("runtime", "archives", "legacy_mds")):
        if _full_suffix(path) in {".tar.gz", ".zip", ".gz"} or path.suffix in {".json", ".jsonl", ".log"}:
            return "legacy_mds_archive_body"
    if _path_has(classification_parts, ("runtime", "runtime_storage_maintenance", "oversized_jsonl")):
        if _full_suffix(path) == ".gz" and path.name.endswith(".jsonl.gz"):
            return "oversized_runtime_jsonl_archive_body"
    return None


def _apply_body_retention(
    *,
    root: Path,
    path: Path,
    inspection: Mapping[str, Any],
    cold_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    expected_sha = str(inspection.get("sha256") or "")
    if not expected_sha:
        return {"status": "blocked_missing_sha256", "online_release_bytes": 0}
    observed_sha = _sha256(path)
    if observed_sha != expected_sha:
        return {
            "status": "blocked_source_sha256_changed",
            "expected_sha256": expected_sha,
            "observed_sha256": observed_sha,
            "online_release_bytes": 0,
        }
    original_bytes = path.stat().st_size
    object_path = _cold_object_path(cold_root=cold_root, path=path, sha256=observed_sha)
    object_path.parent.mkdir(parents=True, exist_ok=True)
    source_is_symlink = path.is_symlink()
    if source_is_symlink and object_path.exists():
        if _sha256(object_path) != observed_sha:
            return {
                "status": "blocked_cold_object_sha256_mismatch",
                "cold_object_path": str(object_path),
                "online_release_bytes": 0,
            }
        path.unlink()
        _write_relative_symlink(target=object_path, link_path=path)
        status = "already_retained_in_cold_object"
    elif source_is_symlink:
        return {
            "status": "blocked_symlink_source_without_canonical_cold_object",
            "cold_object_path": str(object_path),
            "online_release_bytes": 0,
        }
    elif object_path.exists():
        if _sha256(object_path) != observed_sha:
            return {
                "status": "blocked_cold_object_sha256_mismatch",
                "cold_object_path": str(object_path),
                "online_release_bytes": 0,
            }
        path.unlink()
        status = "deduped_to_existing_cold_object"
    else:
        shutil.move(str(path), str(object_path))
        status = "moved_to_cold_object"

    if str(inspection.get("retention_mode") or "") == "symlink":
        if not path.exists() and not path.is_symlink():
            _write_relative_symlink(target=object_path, link_path=path)
    else:
        _write_inline_ref(
            root=root,
            path=path,
            cold_object_path=object_path,
            inspection=inspection,
            recorded_at=recorded_at,
        )
    ref_path = path.with_name(path.name + ".cold_ref.json")
    cold_ref = _cold_ref_payload(
        root=root,
        path=path,
        cold_object_path=object_path,
        inspection=inspection,
        recorded_at=recorded_at,
    )
    write_json(ref_path, cold_ref)
    online_after = path.lstat().st_size + ref_path.stat().st_size
    release_bytes = 0 if source_is_symlink else max(0, original_bytes - online_after)
    return {
        "status": status,
        "cold_object_path": str(object_path),
        "cold_ref_path": str(ref_path),
        "online_release_bytes": release_bytes,
        "original_path_retained_as_symlink": path.is_symlink(),
    }


def _write_inline_ref(
    *,
    root: Path,
    path: Path,
    cold_object_path: Path,
    inspection: Mapping[str, Any],
    recorded_at: str,
) -> None:
    payload = {
        "surface_kind": "historical_body_retention_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "body_moved_to_cold_object",
        "recorded_at": recorded_at,
        "path": str(path),
        "workspace_relative_path": _relative_to_root(root=root, path=path),
        "historical_surface_kind": inspection.get("historical_surface_kind"),
        "cold_object_path": str(cold_object_path),
        "original_sha256": inspection.get("sha256"),
        "original_bytes": inspection.get("bytes"),
        "restore_command": f"cp {cold_object_path} {path}",
        "body_included": False,
    }
    content = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if path.suffix == ".jsonl":
        content = json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n"
    path.write_text(content, encoding="utf-8")


def _cold_ref_payload(
    *,
    root: Path,
    path: Path,
    cold_object_path: Path,
    inspection: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "historical_body_cold_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "online_path_retained_as_ref",
        "recorded_at": recorded_at,
        "path": str(path),
        "workspace_relative_path": _relative_to_root(root=root, path=path),
        "historical_surface_kind": inspection.get("historical_surface_kind"),
        "retention_mode": inspection.get("retention_mode"),
        "cold_object_path": str(cold_object_path),
        "original_sha256": inspection.get("sha256"),
        "original_bytes": inspection.get("bytes"),
        "restore_command": f"cp {cold_object_path} {path}",
        "body_included": False,
    }


def _retention_mode(path: Path) -> str:
    return "symlink" if _full_suffix(path) in _SYMLINK_BODY_SUFFIXES else "inline_ref"


def _cold_store_root(*, root: Path, cold_store_root: Path) -> Path:
    return (
        Path(cold_store_root).expanduser().resolve()
        / safe_artifact_id(_workspace_identity_root(root).name)
        / "historical_body_retention"
    )


def _receipt_root(root: Path) -> Path:
    runtime_root = _workspace_runtime_root(root)
    return runtime_root / "artifacts" / "historical_body_retention"


def _workspace_runtime_root(root: Path) -> Path:
    workspace_root = _workspace_identity_root(root)
    resolved = _absolute_no_resolve(root)
    if workspace_root != resolved:
        return workspace_root / "runtime"
    for candidate in (resolved, *resolved.parents):
        runtime_root = candidate / "runtime"
        if runtime_root.is_dir() and (candidate / "workspace.yaml").exists():
            return runtime_root
        if candidate.name == "runtime" and (candidate.parent / "workspace.yaml").exists():
            return candidate
    if resolved.name == "runtime":
        return resolved
    return resolved / "runtime"


def _workspace_identity_root(root: Path) -> Path:
    resolved = _absolute_no_resolve(root)
    search_anchor = resolved if resolved.is_dir() and not resolved.is_symlink() else resolved.parent
    search_roots = (search_anchor, *search_anchor.parents)
    for candidate in search_roots:
        if (candidate / "workspace.yaml").exists() and (candidate / "runtime").is_dir():
            return candidate
    return resolved


def _cold_object_path(*, cold_root: Path, path: Path, sha256: str) -> Path:
    return cold_root / "objects" / sha256[:2] / f"{sha256}{_object_suffix(path)}"


def _object_suffix(path: Path) -> str:
    full_suffix = _full_suffix(path)
    if full_suffix:
        return full_suffix
    return path.suffix or ".body"


def _full_suffix(path: Path) -> str:
    suffixes = path.suffixes
    if len(suffixes) >= 2 and suffixes[-2:] == [".tar", ".gz"]:
        return ".tar.gz"
    if suffixes:
        return suffixes[-1]
    return ""


def _path_has(parts: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    if not needle:
        return True
    upper = len(parts) - len(needle) + 1
    return any(parts[index : index + len(needle)] == needle for index in range(max(0, upper)))


def _write_relative_symlink(*, target: Path, link_path: Path) -> None:
    relative_target = os.path.relpath(target, start=link_path.parent)
    link_path.symlink_to(relative_target)


def _relative_to_root(*, root: Path, path: Path) -> str:
    workspace_root = _workspace_identity_root(root)
    path_absolute = _absolute_no_resolve(path)
    if workspace_root != _absolute_no_resolve(root):
        try:
            return path_absolute.relative_to(workspace_root).as_posix()
        except ValueError:
            pass
    try:
        return path_absolute.relative_to(_absolute_no_resolve(root)).as_posix()
    except ValueError:
        return str(path)


def _absolute_no_resolve(path: Path) -> Path:
    expanded = path.expanduser()
    if expanded.is_absolute():
        return expanded
    return expanded.absolute()


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


__all__ = ["run_historical_body_retention"]
