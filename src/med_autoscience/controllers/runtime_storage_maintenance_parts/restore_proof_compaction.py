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
OPERATOR_CONFIRMED_PARKED_ACTIVE_STATUSES = frozenset({"active", "waiting_for_user"})


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
    source_groups = _source_groups(ds_root=ds_root, selected_buckets=selected_buckets)
    if not source_groups:
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
    slug = _artifact_slug(recorded_at)
    shards: list[dict[str, Any]] = []
    for index, source_group in enumerate(source_groups, start=1):
        shard = _compact_source_group(
            quest_root=resolved_quest_root,
            ds_root=ds_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            slug=slug,
            group_index=index,
            group_count=len(source_groups),
            group_id=source_group["group_id"],
            source_paths=source_group["source_paths"],
        )
        if shard["status"] != "compacted":
            return {
                "surface_kind": SURFACE_KIND,
                "schema_version": SCHEMA_VERSION,
                "status": shard["status"],
                "quest_id": quest_id,
                "quest_root": str(resolved_quest_root),
                "source_buckets": list(selected_buckets),
                "actual_release_bytes": 0,
                "archive_ref": None,
                "archive_refs": [entry["archive_ref"] for entry in shards if isinstance(entry.get("archive_ref"), Mapping)],
                "source_manifest_path": shard.get("source_manifest_path"),
                "source_manifest_paths": [*list(_shard_paths(shards, "source_manifest_path")), shard.get("source_manifest_path")],
                "restore_proof": shard.get("restore_proof"),
                "restore_proof_path": shard.get("restore_proof_path"),
                "restore_proof_paths": [*list(_shard_paths(shards, "restore_proof_path")), shard.get("restore_proof_path")],
                "pruned_paths": [path for entry in shards for path in list(entry.get("pruned_paths") or [])],
                "blockers": shard.get("blockers") or [{"reason": "restore_proof_failed"}],
                "shards": shards,
                "failed_shard": shard,
            }
        shards.append(shard)

    archive_refs = [entry["archive_ref"] for entry in shards if isinstance(entry.get("archive_ref"), Mapping)]
    source_manifest_paths = list(_shard_paths(shards, "source_manifest_path"))
    restore_proof_paths = list(_shard_paths(shards, "restore_proof_path"))
    bytes_before = sum(int(entry.get("bytes_before") or 0) for entry in shards)
    files_before = sum(int(entry.get("files_before") or 0) for entry in shards)
    actual_release_bytes = sum(int(entry.get("actual_release_bytes") or 0) for entry in shards)
    pruned_paths = [path for entry in shards for path in list(entry.get("pruned_paths") or [])]
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "compacted",
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "source_buckets": list(selected_buckets),
        "source_manifest_path": source_manifest_paths[0] if len(source_manifest_paths) == 1 else None,
        "source_manifest_paths": source_manifest_paths,
        "restore_proof_path": restore_proof_paths[0] if len(restore_proof_paths) == 1 else None,
        "restore_proof_paths": restore_proof_paths,
        "archive_ref": archive_refs[0] if len(archive_refs) == 1 else None,
        "archive_refs": archive_refs,
        "archive_ref_count": len(archive_refs),
        "restore_proof": shards[0].get("restore_proof") if len(shards) == 1 else None,
        "restore_proofs": [entry.get("restore_proof") for entry in shards if isinstance(entry.get("restore_proof"), Mapping)],
        "bytes_before": bytes_before,
        "files_before": files_before,
        "actual_release_bytes": actual_release_bytes,
        "pruned_paths": pruned_paths,
        "blockers": [],
        "shards": shards,
    }


def restore_proof_compaction_blockers(
    snapshot: Mapping[str, Any],
    *,
    include_parked_controller_stop: bool = False,
    include_operator_confirmed_parked_active: bool = False,
) -> list[str]:
    status = str(snapshot.get("status") or "").strip().lower()
    allowed_statuses = set(COLD_RUNTIME_STATUSES)
    if include_parked_controller_stop:
        allowed_statuses.update(PARKED_CONTROLLER_STOP_STATUSES)
    if include_operator_confirmed_parked_active:
        allowed_statuses.update(OPERATOR_CONFIRMED_PARKED_ACTIVE_STATUSES)
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
    include_operator_confirmed_parked_active: bool = False,
) -> dict[str, Any]:
    result = dict(candidate)
    blockers = restore_proof_compaction_blockers(
        snapshot,
        include_parked_controller_stop=include_parked_controller_stop,
        include_operator_confirmed_parked_active=include_operator_confirmed_parked_active,
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


def _source_groups(*, ds_root: Path, selected_buckets: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    regular_sources: list[Path] = []
    for bucket in selected_buckets:
        bucket_path = ds_root / bucket
        if not bucket_path.exists():
            continue
        if bucket == "codex_homes" and bucket_path.is_dir():
            children = [path for path in sorted(bucket_path.iterdir()) if _has_any_payload(path)]
            groups.extend(
                {
                    "group_id": f"{bucket}__{_safe_artifact_id(child.name)}",
                    "source_paths": [child],
                }
                for child in children
            )
        elif _directory_size_bytes(bucket_path) > 0:
            regular_sources.append(bucket_path)
    if regular_sources:
        groups.insert(
            0,
            {
                "group_id": regular_sources[0].name if len(regular_sources) == 1 else "runtime_buckets",
                "source_paths": regular_sources,
            },
        )
    return groups


def _compact_source_group(
    *,
    quest_root: Path,
    ds_root: Path,
    quest_id: str,
    recorded_at: str,
    slug: str,
    group_index: int,
    group_count: int,
    group_id: str,
    source_paths: list[Path],
) -> dict[str, Any]:
    archive_root = _archive_root(quest_root)
    archive_root.mkdir(parents=True, exist_ok=True)
    safe_quest_id = _safe_artifact_id(quest_id)
    safe_group_id = _safe_artifact_id(group_id)
    archive_path = archive_root / f"{safe_quest_id}-{slug}-{group_index:04d}-of-{group_count:04d}-{safe_group_id}.tar.gz"
    manifest_path = archive_root / f"{safe_quest_id}-{slug}-{group_index:04d}-of-{group_count:04d}-{safe_group_id}.manifest.json"
    restore_proof_path = archive_root / f"{safe_quest_id}-{slug}-{group_index:04d}-of-{group_count:04d}-{safe_group_id}.restore_proof.json"
    if archive_path.exists() or manifest_path.exists() or restore_proof_path.exists():
        raise FileExistsError(f"restore-proof compaction target already exists for {quest_id}: {slug}:{group_id}")

    manifest = _source_manifest(
        quest_root=quest_root,
        ds_root=ds_root,
        quest_id=quest_id,
        recorded_at=recorded_at,
        source_paths=source_paths,
        selected_buckets=tuple(path.name for path in source_paths),
        shard={
            "group_id": group_id,
            "group_index": group_index,
            "group_count": group_count,
        },
    )
    _write_json(manifest_path, manifest)
    bytes_before = sum(int(item["size_bytes"]) for item in manifest["source_files"])
    files_before = len(manifest["source_files"])
    with tarfile.open(archive_path, "w:gz") as tar:
        for source_path in source_paths:
            tar.add(source_path, arcname=source_path.relative_to(ds_root).as_posix(), recursive=True)

    archive_sha256 = _file_sha256(archive_path)
    restore_proof = _restore_proof(
        archive_path=archive_path,
        manifest=manifest,
        archive_sha256=archive_sha256,
        verified_at=_utc_now(),
    )
    _write_json(restore_proof_path, restore_proof)
    report_restore_proof = restore_proof if group_count == 1 else _restore_proof_summary(restore_proof)
    if restore_proof["status"] != "verified":
        return {
            "surface_kind": "runtime_restore_proof_compaction_shard",
            "schema_version": SCHEMA_VERSION,
            "status": "blocked_restore_proof_failed",
            "quest_id": quest_id,
            "quest_root": str(quest_root),
            "group_id": group_id,
            "group_index": group_index,
            "group_count": group_count,
            "actual_release_bytes": 0,
            "archive_ref": None,
            "source_manifest_path": str(manifest_path),
            "restore_proof": report_restore_proof,
            "restore_proof_path": str(restore_proof_path),
            "pruned_paths": [],
            "blockers": restore_proof.get("errors") or [{"reason": "restore_proof_failed"}],
        }

    pruned_paths: list[str] = []
    for source_path in source_paths:
        if not source_path.exists():
            continue
        if source_path.is_dir():
            shutil.rmtree(source_path)
        else:
            source_path.unlink()
        pruned_paths.append(str(source_path))
    actual_release_bytes = max(0, bytes_before - archive_path.stat().st_size - manifest_path.stat().st_size - restore_proof_path.stat().st_size)
    archive_id = f"runtime-restore-proof-compaction::{quest_id}::{slug}::{group_index:04d}::{safe_group_id}"
    archive_ref = {
        "surface_kind": "runtime_archive_ref",
        "schema_version": SCHEMA_VERSION,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "archive_id": archive_id,
        "archived_at": recorded_at,
        "archive_path": str(archive_path),
        "archive_format": ARCHIVE_FORMAT,
        "sha256": archive_sha256,
        "bytes": archive_path.stat().st_size,
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "source_buckets": [path.relative_to(ds_root).as_posix() for path in source_paths],
        "source_file_count": files_before,
        "restore_command": f"tar -xzf {archive_path} -C {ds_root}",
    }
    return {
        "surface_kind": "runtime_restore_proof_compaction_shard",
        "schema_version": SCHEMA_VERSION,
        "status": "compacted",
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "group_id": group_id,
        "group_index": group_index,
        "group_count": group_count,
        "source_manifest_path": str(manifest_path),
        "restore_proof_path": str(restore_proof_path),
        "archive_ref": archive_ref,
        "restore_proof": report_restore_proof,
        "bytes_before": bytes_before,
        "files_before": files_before,
        "actual_release_bytes": actual_release_bytes,
        "pruned_paths": pruned_paths,
        "blockers": [],
    }


def _restore_proof_summary(restore_proof: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "surface_kind": restore_proof.get("surface_kind"),
        "schema_version": restore_proof.get("schema_version"),
        "status": restore_proof.get("status"),
        "verified_at": restore_proof.get("verified_at"),
        "archive_path": restore_proof.get("archive_path"),
        "archive_format": restore_proof.get("archive_format"),
        "archive_sha256": restore_proof.get("archive_sha256"),
        "source_file_count": restore_proof.get("source_file_count"),
        "verified_file_count": restore_proof.get("verified_file_count"),
        "verified_entries_inlined": False,
        "errors": restore_proof.get("errors") or [],
    }


def _shard_paths(shards: Iterable[Mapping[str, Any]], key: str) -> Iterable[str]:
    for shard in shards:
        value = shard.get(key)
        if isinstance(value, str) and value:
            yield value


def _source_manifest(
    *,
    quest_root: Path,
    ds_root: Path,
    quest_id: str,
    recorded_at: str,
    source_paths: list[Path],
    selected_buckets: tuple[str, ...],
    shard: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_files: list[dict[str, Any]] = []
    for source_path in source_paths:
        for path in sorted(source_path.rglob("*")):
            if path.is_symlink():
                source_files.append(
                    {
                        "path": path.relative_to(ds_root).as_posix(),
                        "entry_type": "symlink",
                        "size_bytes": path.lstat().st_size,
                        "link_target": str(path.readlink()),
                    }
                )
                continue
            if path.is_file():
                source_files.append(
                    {
                        "path": path.relative_to(ds_root).as_posix(),
                        "entry_type": "file",
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
        "shard": dict(shard or {}),
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
            file_observations: dict[str, dict[str, Any]] = {}
            hardlink_refs: list[tuple[str, str, int]] = []
            for member in tar.getmembers():
                if member.isfile():
                    extracted = tar.extractfile(member)
                    if extracted is None:
                        errors.append({"path": member.name, "reason": "member_not_readable"})
                        continue
                    digest = hashlib.sha256(extracted.read()).hexdigest()
                    payload = {
                        "path": member.name,
                        "entry_type": "file",
                        "size_bytes": member.size,
                        "sha256": digest,
                    }
                    observed[member.name] = payload
                    file_observations[member.name] = payload
                    continue
                if member.issym():
                    observed[member.name] = {
                        "path": member.name,
                        "entry_type": "symlink",
                        "link_target": member.linkname,
                    }
                    continue
                if member.islnk():
                    hardlink_refs.append((member.name, member.linkname, member.size))
                    continue
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
        "surface_kind": "runtime_restore_proof",
        "schema_version": SCHEMA_VERSION,
        "status": "verified" if not errors else "failed",
        "verified_at": verified_at,
        "archive_path": str(archive_path),
        "archive_format": ARCHIVE_FORMAT,
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


def _directory_size_bytes(path: Path) -> int:
    if path.is_symlink():
        return path.lstat().st_size
    if path.is_file():
        return path.stat().st_size
    total = 0
    for candidate in path.rglob("*"):
        if candidate.is_symlink():
            total += candidate.lstat().st_size
        elif candidate.is_file():
            total += candidate.stat().st_size
    return total


def _has_any_payload(path: Path) -> bool:
    if path.is_symlink() or path.is_file():
        return True
    if not path.is_dir():
        return False
    try:
        next(path.rglob("*"))
    except StopIteration:
        return False
    return True


def _archive_root(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / "restore_proof_archives" / "runtime_bucket_compaction"


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
