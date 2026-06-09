from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
import os
from pathlib import Path
import shutil
import tarfile
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    safe_artifact_id,
    write_json,
)


SURFACE_KIND = "historical_directory_retention"
SCHEMA_VERSION = 1
_TIMESTAMP_FORMAT = "%Y%m%dT%H%M%SZ"


def run_historical_directory_retention(
    *,
    root: Path,
    apply: bool,
    cold_store_root: Path,
    min_mb: int = 128,
    max_directories: int | None = None,
) -> dict[str, Any]:
    resolved_root = _absolute_no_resolve(Path(root))
    recorded_at = _utc_now()
    threshold_bytes = max(0, int(min_mb)) * 1024 * 1024
    cold_root = _cold_store_root(root=resolved_root, cold_store_root=cold_store_root)
    candidates: list[dict[str, Any]] = []
    blockers: list[dict[str, Any]] = []
    moved_count = 0
    actual_release_bytes = 0

    for directory in _candidate_directories(resolved_root):
        inspection = _inspect_directory(root=resolved_root, directory=directory, threshold_bytes=threshold_bytes)
        if inspection.get("status") == "blocked":
            blockers.append(inspection)
            continue
        if inspection.get("status") != "candidate":
            continue
        if max_directories is not None and len(candidates) >= max(0, int(max_directories)):
            break
        if apply:
            applied = _apply_directory_retention(
                root=resolved_root,
                directory=directory,
                inspection=inspection,
                cold_root=cold_root,
                recorded_at=recorded_at,
            )
            inspection.update(applied)
            actual_release_bytes += int(applied.get("online_release_bytes") or 0)
            if applied.get("status") == "directory_moved_to_cold_archive":
                moved_count += 1
            elif str(applied.get("status") or "").startswith("blocked"):
                blockers.append(inspection)
        candidates.append(inspection)

    status = (
        "applied"
        if apply and moved_count and not blockers
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
        "max_directories": max_directories,
        "cold_store_root": str(cold_root),
        "candidate_count": len(candidates),
        "moved_count": moved_count,
        "blocker_count": len(blockers),
        "actual_release_bytes": actual_release_bytes,
        "body_included": False,
        "mutation_policy": {
            "moves_complete_historical_directory_to_cold_archive": bool(apply),
            "replaces_online_directory_with_capsule_ref": bool(apply),
            "deletes_domain_truth": False,
            "deletes_data_assets": False,
            "keeps_restore_manifest_and_proof": True,
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
    if not root.exists() or root.is_file():
        return []
    direct = _historical_directory_kind(root)
    if direct is not None:
        return [root]
    candidates: list[Path] = []
    for directory in root.rglob("*"):
        if not directory.is_dir() or directory.is_symlink():
            continue
        if _historical_directory_kind(directory) is None:
            continue
        if any(parent in candidates for parent in directory.parents):
            continue
        candidates.append(directory)
    return sorted(candidates)


def _inspect_directory(*, root: Path, directory: Path, threshold_bytes: int) -> dict[str, Any]:
    kind = _historical_directory_kind(directory)
    if kind is None:
        return {"status": "not_historical_directory", "path": str(directory)}
    if _contains_data_asset(directory):
        return {
            "status": "blocked",
            "reason": "data_assets_not_allowed",
            "path": str(directory),
            "historical_surface_kind": kind,
        }
    stats = _directory_stats(directory)
    if stats["bytes"] < threshold_bytes:
        return {
            "status": "below_threshold",
            "path": str(directory),
            "workspace_relative_path": _relative_to_root(root=root, path=directory),
            "bytes": stats["bytes"],
            "file_count": stats["file_count"],
            "symlink_count": stats["symlink_count"],
            "historical_surface_kind": kind,
        }
    return {
        "status": "candidate",
        "path": str(directory),
        "workspace_relative_path": _relative_to_root(root=root, path=directory),
        "bytes": stats["bytes"],
        "file_count": stats["file_count"],
        "symlink_count": stats["symlink_count"],
        "historical_surface_kind": kind,
        "restore_command": f"tar -xzf <cold_archive_path> -C {directory.parent}",
    }


def _historical_directory_kind(directory: Path) -> str | None:
    if _already_retained_directory(directory):
        return None
    parts = _absolute_no_resolve(directory).parts
    if _path_has(parts, ("data", "datasets")):
        return None
    if _path_has(parts, ("runtime", "archives", "legacy_mds")) and directory.name == "med-deepscientist":
        return "legacy_mds_directory_capsule"
    if _path_has(parts, ("archive", "legacy_ops_surfaces")) and directory.name in {"medautoscience", "framework_refs"}:
        return "legacy_ops_directory_capsule"
    if _path_has(parts, ("archive", "legacy_ops_surfaces")) and directory.name == "_repo_compare":
        return "legacy_ops_repo_compare_directory_capsule"
    if _path_has(parts, ("archive", "legacy_root_surfaces")) and directory.name in {"logs", "storage_audit"}:
        return "legacy_root_directory_capsule"
    return None


def _apply_directory_retention(
    *,
    root: Path,
    directory: Path,
    inspection: Mapping[str, Any],
    cold_root: Path,
    recorded_at: str,
) -> dict[str, Any]:
    original_bytes = int(inspection.get("bytes") or 0)
    manifest = _source_manifest(root=root, directory=directory, inspection=inspection, recorded_at=recorded_at)
    manifest_sha = _payload_sha256(manifest)
    archive_path = _cold_archive_path(cold_root=cold_root, directory=directory, manifest_sha=manifest_sha)
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    if not archive_path.exists():
        _write_archive(archive_path=archive_path, directory=directory)
    archive_sha = _sha256(archive_path)
    restore_proof = _restore_proof(
        archive_path=archive_path,
        manifest=manifest,
        archive_sha256=archive_sha,
        verified_at=_utc_now(),
    )
    manifest_path = archive_path.with_suffix(archive_path.suffix + ".manifest.json")
    restore_proof_path = archive_path.with_suffix(archive_path.suffix + ".restore_proof.json")
    write_json(manifest_path, manifest)
    write_json(restore_proof_path, restore_proof)
    if restore_proof.get("status") != "verified":
        return {
            "status": "blocked_restore_proof_failed",
            "cold_archive_path": str(archive_path),
            "source_manifest_path": str(manifest_path),
            "restore_proof_path": str(restore_proof_path),
            "restore_proof_errors": restore_proof.get("errors") or [],
            "online_release_bytes": 0,
        }

    ref_payload = _ref_payload(
        root=root,
        directory=directory,
        inspection=inspection,
        archive_path=archive_path,
        archive_sha=archive_sha,
        archive_bytes=archive_path.stat().st_size,
        manifest_path=manifest_path,
        restore_proof_path=restore_proof_path,
        recorded_at=recorded_at,
    )
    tmp_ref_dir = directory.with_name(f"{directory.name}.retention-ref.tmp")
    final_ref_dir = directory
    if tmp_ref_dir.exists():
        raise FileExistsError(f"temporary retention ref directory already exists: {tmp_ref_dir}")
    tmp_ref_dir.mkdir(parents=True)
    write_json(tmp_ref_dir / "capsule.cold_ref.json", ref_payload)
    shutil.rmtree(directory)
    tmp_ref_dir.rename(final_ref_dir)
    online_after = _directory_stats(final_ref_dir)["bytes"]
    return {
        "status": "directory_moved_to_cold_archive",
        "cold_archive_path": str(archive_path),
        "cold_ref_path": str(final_ref_dir / "capsule.cold_ref.json"),
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "archive_sha256": archive_sha,
        "archive_bytes": archive_path.stat().st_size,
        "online_release_bytes": max(0, original_bytes - online_after),
    }


def _source_manifest(
    *,
    root: Path,
    directory: Path,
    inspection: Mapping[str, Any],
    recorded_at: str,
) -> dict[str, Any]:
    entries = [_manifest_entry(directory=directory, path=path) for path in _manifest_source_paths(directory)]
    return {
        "surface_kind": "historical_directory_source_manifest",
        "schema_version": SCHEMA_VERSION,
        "recorded_at": recorded_at,
        "root": str(root),
        "directory": str(directory),
        "workspace_relative_path": _relative_to_root(root=root, path=directory),
        "historical_surface_kind": inspection.get("historical_surface_kind"),
        "source_file_count": sum(1 for entry in entries if entry.get("entry_type") == "file"),
        "source_symlink_count": sum(1 for entry in entries if entry.get("entry_type") == "symlink"),
        "source_files": entries,
    }


def _manifest_source_paths(directory: Path) -> Iterable[Path]:
    for path in sorted(directory.rglob("*")):
        if path.is_symlink() or path.is_file():
            yield path


def _manifest_entry(*, directory: Path, path: Path) -> dict[str, Any]:
    relative = path.relative_to(directory.parent).as_posix()
    if path.is_symlink():
        return {
            "path": relative,
            "entry_type": "symlink",
            "size_bytes": path.lstat().st_size,
            "link_target": str(path.readlink()),
        }
    return {
        "path": relative,
        "entry_type": "file",
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _write_archive(*, archive_path: Path, directory: Path) -> None:
    with tarfile.open(archive_path, "w:gz") as tar:
        tar.add(directory, arcname=directory.name, recursive=True)


def _restore_proof(
    *,
    archive_path: Path,
    manifest: Mapping[str, Any],
    archive_sha256: str,
    verified_at: str,
) -> dict[str, Any]:
    expected = {str(item["path"]): dict(item) for item in manifest.get("source_files", []) if isinstance(item, Mapping)}
    observed: dict[str, dict[str, Any]] = {}
    errors: list[dict[str, Any]] = []
    if _sha256(archive_path) != archive_sha256:
        errors.append({"path": str(archive_path), "reason": "archive_sha256_changed"})
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            file_observations: dict[str, dict[str, Any]] = {}
            hardlink_refs: list[tuple[str, str, int]] = []
            for member in tar.getmembers():
                if member.isfile():
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        errors.append({"path": member.name, "reason": "member_not_readable"})
                        continue
                    observed[member.name] = {
                        "path": member.name,
                        "entry_type": "file",
                        "size_bytes": member.size,
                        "sha256": hashlib.sha256(extracted.read()).hexdigest(),
                    }
                    file_observations[member.name] = observed[member.name]
                elif member.issym():
                    observed[member.name] = {
                        "path": member.name,
                        "entry_type": "symlink",
                        "size_bytes": len(member.linkname),
                        "link_target": member.linkname,
                    }
                elif member.islnk():
                    hardlink_refs.append((member.name, member.linkname, member.size))
            for member_name, link_name, member_size in hardlink_refs:
                target = file_observations.get(link_name)
                if target is None:
                    errors.append({"path": member_name, "reason": "hardlink_target_missing", "target": link_name})
                    continue
                observed[member_name] = {
                    "path": member_name,
                    "entry_type": "file",
                    "size_bytes": member_size or int(target.get("size_bytes") or 0),
                    "sha256": target.get("sha256"),
                }
    except tarfile.TarError as exc:
        errors.append({"path": str(archive_path), "reason": "archive_not_readable", "error": str(exc)})
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    mismatch = [
        path
        for path in sorted(set(expected) & set(observed))
        if _restore_entry_mismatch(expected[path], observed[path])
    ]
    errors.extend({"path": path, "reason": "missing_from_archive"} for path in missing)
    errors.extend({"path": path, "reason": "unexpected_archive_member"} for path in extra)
    errors.extend({"path": path, "reason": "archive_member_hash_or_size_mismatch"} for path in mismatch)
    return {
        "surface_kind": "historical_directory_restore_proof",
        "schema_version": SCHEMA_VERSION,
        "status": "verified" if not errors else "failed",
        "verified_at": verified_at,
        "archive_path": str(archive_path),
        "archive_sha256": archive_sha256,
        "source_file_count": len(expected),
        "verified_file_count": len(observed),
        "verified_entries": [observed[path] for path in sorted(observed)],
        "errors": errors,
    }


def _restore_entry_mismatch(expected: Mapping[str, Any], observed: Mapping[str, Any]) -> bool:
    expected_type = str(expected.get("entry_type") or "file")
    observed_type = str(observed.get("entry_type") or "file")
    if expected_type != observed_type:
        return True
    if expected_type == "symlink":
        return str(expected.get("link_target") or "") != str(observed.get("link_target") or "")
    return int(expected.get("size_bytes") or 0) != int(observed.get("size_bytes") or 0) or str(
        expected.get("sha256") or ""
    ) != str(observed.get("sha256") or "")


def _ref_payload(
    *,
    root: Path,
    directory: Path,
    inspection: Mapping[str, Any],
    archive_path: Path,
    archive_sha: str,
    archive_bytes: int,
    manifest_path: Path,
    restore_proof_path: Path,
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "surface_kind": "historical_directory_retention_ref",
        "schema_version": SCHEMA_VERSION,
        "status": "directory_body_moved_to_cold_archive",
        "recorded_at": recorded_at,
        "root": str(root),
        "directory_path": str(directory),
        "workspace_relative_path": _relative_to_root(root=root, path=directory),
        "historical_surface_kind": inspection.get("historical_surface_kind"),
        "cold_archive_path": str(archive_path),
        "archive_sha256": archive_sha,
        "archive_bytes": archive_bytes,
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "original_bytes": inspection.get("bytes"),
        "original_file_count": inspection.get("file_count"),
        "restore_command": f"tar -xzf {archive_path} -C {directory.parent}",
        "body_included": False,
    }


def _directory_stats(directory: Path) -> dict[str, int]:
    total = 0
    file_count = 0
    symlink_count = 0
    for path in directory.rglob("*"):
        if path.is_symlink():
            total += path.lstat().st_size
            symlink_count += 1
        elif path.is_file():
            total += path.stat().st_size
            file_count += 1
    return {"bytes": total, "file_count": file_count, "symlink_count": symlink_count}


def _contains_data_asset(directory: Path) -> bool:
    return _path_has(_absolute_no_resolve(directory).parts, ("data", "datasets"))


def _already_retained_directory(directory: Path) -> bool:
    ref_path = directory / "capsule.cold_ref.json"
    if not ref_path.is_file():
        return False
    entries = [path for path in directory.iterdir()]
    if len(entries) != 1:
        return False
    try:
        payload = json.loads(ref_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return payload.get("surface_kind") == "historical_directory_retention_ref"


def _cold_store_root(*, root: Path, cold_store_root: Path) -> Path:
    workspace = _workspace_root(root)
    namespace = workspace.name if workspace is not None else root.name
    return Path(cold_store_root).expanduser().resolve() / safe_artifact_id(namespace) / "historical_directory_retention"


def _receipt_root(root: Path) -> Path:
    runtime_root = _workspace_runtime_root(root)
    return runtime_root / "artifacts" / "historical_directory_retention"


def _workspace_runtime_root(root: Path) -> Path:
    workspace = _workspace_root(root)
    if workspace is not None:
        return workspace / "runtime"
    if root.name == "runtime":
        return root
    return root / "runtime"


def _workspace_root(root: Path) -> Path | None:
    resolved = _absolute_no_resolve(root)
    search_anchor = resolved if resolved.is_dir() and not resolved.is_symlink() else resolved.parent
    for candidate in (search_anchor, *search_anchor.parents):
        if (candidate / "workspace.yaml").exists():
            return candidate
    return None


def _cold_archive_path(*, cold_root: Path, directory: Path, manifest_sha: str) -> Path:
    safe_name = safe_artifact_id(directory.name)
    return cold_root / "objects" / manifest_sha[:2] / f"{safe_name}-{manifest_sha[:16]}.tar.gz"


def _payload_sha256(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _path_has(parts: tuple[str, ...], needle: tuple[str, ...]) -> bool:
    if not needle:
        return True
    upper = len(parts) - len(needle) + 1
    return any(parts[index : index + len(needle)] == needle for index in range(max(0, upper)))


def _relative_to_root(*, root: Path, path: Path) -> str:
    workspace = _workspace_root(root)
    path_absolute = _absolute_no_resolve(path)
    if workspace is not None:
        try:
            return path_absolute.relative_to(workspace).as_posix()
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


__all__ = ["run_historical_directory_retention"]
