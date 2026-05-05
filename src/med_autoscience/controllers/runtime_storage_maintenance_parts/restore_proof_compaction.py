from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
import hashlib
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any


ARCHIVE_FORMAT = "tar.gz"
SURFACE_KIND = "runtime_restore_proof_compaction"
SCHEMA_VERSION = 1
COLD_RUNTIME_STATUSES = frozenset({"completed", "failed", "terminated"})
PARKED_CONTROLLER_STOP_STATUSES = frozenset({"paused", "stopped"})


def compact_cold_runtime_buckets(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    buckets: Iterable[str],
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    ds_root = resolved_quest_root / ".ds"
    selected_buckets = tuple(dict.fromkeys(_bucket_name(bucket) for bucket in buckets))
    existing_sources = [
        ds_root / bucket for bucket in selected_buckets if (ds_root / bucket).exists() and _directory_size_bytes(ds_root / bucket) > 0
    ]
    if not existing_sources:
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "nothing_to_archive",
            "quest_id": quest_id,
            "quest_root": str(resolved_quest_root),
            "source_buckets": list(selected_buckets),
            "actual_release_bytes": 0,
            "archive_ref": None,
            "restore_proof": None,
            "pruned_paths": [],
            "blockers": [],
        }
    symlink = _first_symlink(existing_sources)
    if symlink is not None:
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "blocked_symlink_in_source_bucket",
            "quest_id": quest_id,
            "quest_root": str(resolved_quest_root),
            "source_buckets": list(selected_buckets),
            "actual_release_bytes": 0,
            "archive_ref": None,
            "restore_proof": None,
            "pruned_paths": [],
            "blockers": [{"reason": "symlink_in_source_bucket", "path": str(symlink)}],
        }

    archive_root = ds_root / "cold_archive" / "restore_proof_compaction"
    archive_root.mkdir(parents=True, exist_ok=True)
    slug = _artifact_slug(recorded_at)
    safe_quest_id = _safe_artifact_id(quest_id)
    archive_path = archive_root / f"{safe_quest_id}-{slug}.tar.gz"
    manifest_path = archive_root / f"{safe_quest_id}-{slug}.manifest.json"
    restore_proof_path = archive_root / f"{safe_quest_id}-{slug}.restore_proof.json"
    if archive_path.exists() or manifest_path.exists() or restore_proof_path.exists():
        raise FileExistsError(f"restore-proof compaction target already exists for {quest_id}: {slug}")

    manifest = _source_manifest(
        quest_root=resolved_quest_root,
        ds_root=ds_root,
        quest_id=quest_id,
        recorded_at=recorded_at,
        source_paths=existing_sources,
        selected_buckets=selected_buckets,
    )
    _write_json(manifest_path, manifest)
    bytes_before = sum(int(item["size_bytes"]) for item in manifest["source_files"])
    files_before = len(manifest["source_files"])
    with tarfile.open(archive_path, "w:gz") as tar:
        for source_path in existing_sources:
            tar.add(source_path, arcname=source_path.relative_to(ds_root).as_posix(), recursive=True)

    archive_sha256 = _file_sha256(archive_path)
    restore_proof = _restore_proof(
        archive_path=archive_path,
        manifest=manifest,
        archive_sha256=archive_sha256,
        verified_at=_utc_now(),
    )
    _write_json(restore_proof_path, restore_proof)
    if restore_proof["status"] != "verified":
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "blocked_restore_proof_failed",
            "quest_id": quest_id,
            "quest_root": str(resolved_quest_root),
            "source_buckets": list(selected_buckets),
            "actual_release_bytes": 0,
            "archive_ref": None,
            "source_manifest_path": str(manifest_path),
            "restore_proof": restore_proof,
            "restore_proof_path": str(restore_proof_path),
            "pruned_paths": [],
            "blockers": restore_proof.get("errors") or [{"reason": "restore_proof_failed"}],
        }

    pruned_paths: list[str] = []
    for source_path in existing_sources:
        if not source_path.exists():
            continue
        shutil.rmtree(source_path)
        pruned_paths.append(str(source_path))
    actual_release_bytes = max(0, bytes_before - archive_path.stat().st_size - manifest_path.stat().st_size - restore_proof_path.stat().st_size)
    archive_id = f"runtime-restore-proof-compaction::{quest_id}::{slug}"
    archive_ref = {
        "surface_kind": "runtime_archive_ref",
        "schema_version": SCHEMA_VERSION,
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "archive_id": archive_id,
        "archived_at": recorded_at,
        "archive_path": str(archive_path),
        "archive_format": ARCHIVE_FORMAT,
        "sha256": archive_sha256,
        "bytes": archive_path.stat().st_size,
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "source_buckets": [path.name for path in existing_sources],
        "source_file_count": files_before,
        "restore_command": f"tar -xzf {archive_path} -C {ds_root}",
    }
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "compacted",
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "source_buckets": list(selected_buckets),
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "archive_ref": archive_ref,
        "restore_proof": restore_proof,
        "bytes_before": bytes_before,
        "files_before": files_before,
        "actual_release_bytes": actual_release_bytes,
        "pruned_paths": pruned_paths,
        "blockers": [],
    }


def restore_proof_compaction_blockers(
    snapshot: Mapping[str, Any],
    *,
    include_parked_controller_stop: bool = False,
) -> list[str]:
    status = str(snapshot.get("status") or "").strip().lower()
    allowed_statuses = set(COLD_RUNTIME_STATUSES)
    if include_parked_controller_stop:
        allowed_statuses.update(PARKED_CONTROLLER_STOP_STATUSES)
    blockers: list[str] = []
    if not bool(snapshot.get("quest_exists")):
        blockers.append("missing_quest_root")
    if snapshot.get("runtime_state_error"):
        blockers.append("runtime_state_unreadable")
    if snapshot.get("active_run_id"):
        blockers.append("active_run_id_present")
    if status not in allowed_statuses:
        blockers.append(f"not_stopped_cold:{status or 'missing'}")
    return blockers


def restore_proof_compaction_candidate(
    *,
    candidate: Mapping[str, Any],
    snapshot: Mapping[str, Any],
    include_parked_controller_stop: bool = False,
) -> dict[str, Any]:
    result = dict(candidate)
    blockers = restore_proof_compaction_blockers(
        snapshot,
        include_parked_controller_stop=include_parked_controller_stop,
    )
    result["restore_proof_compaction"] = {
        "enabled": True,
        "eligible": not blockers,
        "blockers": blockers,
    }
    if blockers:
        result["candidate_action"] = "audit-only"
        result["risk"] = "not_stopped_cold"
        result["estimated_release_bytes"] = 0
        result["blockers"] = list(dict.fromkeys([*list(result.get("blockers") or []), *blockers]))
    else:
        result["candidate_action"] = "restore-proof-compaction"
    return result


def _source_manifest(
    *,
    quest_root: Path,
    ds_root: Path,
    quest_id: str,
    recorded_at: str,
    source_paths: list[Path],
    selected_buckets: tuple[str, ...],
) -> dict[str, Any]:
    source_files: list[dict[str, Any]] = []
    for source_path in source_paths:
        for path in sorted(candidate for candidate in source_path.rglob("*") if candidate.is_file()):
            source_files.append(
                {
                    "path": path.relative_to(ds_root).as_posix(),
                    "size_bytes": path.stat().st_size,
                    "sha256": _file_sha256(path),
                }
            )
    return {
        "surface_kind": "runtime_restore_source_manifest",
        "schema_version": SCHEMA_VERSION,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "recorded_at": recorded_at,
        "source_buckets": list(selected_buckets),
        "source_files": source_files,
    }


def _restore_proof(
    *,
    archive_path: Path,
    manifest: Mapping[str, Any],
    archive_sha256: str,
    verified_at: str,
) -> dict[str, Any]:
    expected = {str(item["path"]): dict(item) for item in manifest.get("source_files", []) if isinstance(item, Mapping)}
    errors: list[dict[str, Any]] = []
    observed: dict[str, dict[str, Any]] = {}
    try:
        with tarfile.open(archive_path, "r:gz") as tar:
            for member in tar.getmembers():
                if not member.isfile():
                    continue
                extracted = tar.extractfile(member)
                if extracted is None:
                    errors.append({"path": member.name, "reason": "member_not_readable"})
                    continue
                digest = hashlib.sha256(extracted.read()).hexdigest()
                observed[member.name] = {"path": member.name, "size_bytes": member.size, "sha256": digest}
    except tarfile.TarError as exc:
        errors.append({"path": str(archive_path), "reason": "archive_not_readable", "error": str(exc)})
    missing = sorted(set(expected) - set(observed))
    extra = sorted(set(observed) - set(expected))
    mismatch = [
        path
        for path in sorted(set(expected) & set(observed))
        if int(expected[path].get("size_bytes") or 0) != int(observed[path].get("size_bytes") or 0)
        or str(expected[path].get("sha256") or "") != str(observed[path].get("sha256") or "")
    ]
    errors.extend({"path": path, "reason": "missing_from_archive"} for path in missing)
    errors.extend({"path": path, "reason": "unexpected_archive_member"} for path in extra)
    errors.extend({"path": path, "reason": "archive_member_hash_or_size_mismatch"} for path in mismatch)
    return {
        "surface_kind": "runtime_restore_proof",
        "schema_version": SCHEMA_VERSION,
        "status": "verified" if not errors else "failed",
        "verified_at": verified_at,
        "archive_path": str(archive_path),
        "archive_format": ARCHIVE_FORMAT,
        "archive_sha256": archive_sha256,
        "source_file_count": len(expected),
        "verified_file_count": len(observed),
        "errors": errors,
    }


def _first_symlink(paths: list[Path]) -> Path | None:
    for source_path in paths:
        if source_path.is_symlink():
            return source_path
        for path in source_path.rglob("*"):
            if path.is_symlink():
                return path
    return None


def _directory_size_bytes(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    total = 0
    for candidate in path.rglob("*"):
        if candidate.is_file():
            total += candidate.stat().st_size
    return total


def _bucket_name(value: str) -> str:
    name = str(value or "").strip()
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"invalid runtime bucket name: {value!r}")
    return name


def _artifact_slug(value: str) -> str:
    normalized = value.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _safe_artifact_id(value: str) -> str:
    safe = "".join(char if char.isalnum() or char in {"-", "_", "."} else "-" for char in str(value).strip())
    return safe.strip("-._") or "quest"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(dict(payload), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


__all__ = [
    "ARCHIVE_FORMAT",
    "COLD_RUNTIME_STATUSES",
    "PARKED_CONTROLLER_STOP_STATUSES",
    "SURFACE_KIND",
    "compact_cold_runtime_buckets",
    "restore_proof_compaction_blockers",
    "restore_proof_compaction_candidate",
]
