from __future__ import annotations

from collections.abc import Iterable, Mapping
import itertools
import json
import shutil
import tarfile
from pathlib import Path
from typing import Any

from med_autoscience.controllers.runtime_storage_maintenance_parts.restore_proof_compaction_helpers import (
    artifact_slug as _artifact_slug,
    file_sha256 as _file_sha256,
    restore_proof as _restore_proof,
    safe_artifact_id as _safe_artifact_id,
    utc_now as _utc_now,
    write_json as _write_json,
)


ARCHIVE_FORMAT = "tar.gz"
SURFACE_KIND = "runtime_restore_proof_compaction"
SCHEMA_VERSION = 1
COLD_RUNTIME_STATUSES = frozenset({"completed", "failed", "terminated"})
PARKED_CONTROLLER_STOP_STATUSES = frozenset({"paused", "stopped"})
OPERATOR_CONFIRMED_PARKED_ACTIVE_STATUSES = frozenset({"active", "waiting_for_user"})
REPORT_SAMPLE_LIMIT = 5


def plan_restore_proof_compaction_canary(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    buckets: Iterable[str],
    entry_limit: int = 20,
    blockers: Iterable[str] | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    ds_root = resolved_quest_root / ".ds"
    selected_buckets = tuple(dict.fromkeys(_bucket_name(bucket) for bucket in buckets))
    bounded_limit = max(1, int(entry_limit))
    slug = _artifact_slug(recorded_at)
    bucket_samples = [
        _bucket_canary_sample(
            ds_root=ds_root,
            bucket=bucket,
            entry_limit=bounded_limit,
        )
        for bucket in selected_buckets
    ]
    receipt_ref = f"mas-runtime-storage-restore-proof-canary:{quest_id}:{slug}"
    canary_root = _canary_root(resolved_quest_root)
    canary_root.mkdir(parents=True, exist_ok=True)
    plan_path = canary_root / f"{_safe_artifact_id(quest_id)}-{slug}.restore_proof_canary.json"
    receipt_path = canary_root / f"{_safe_artifact_id(quest_id)}-{slug}.restore_proof_canary_receipt.json"
    archive_path = canary_root / f"{_safe_artifact_id(quest_id)}-{slug}.restore_proof_canary.tar.gz"
    manifest_path = canary_root / f"{_safe_artifact_id(quest_id)}-{slug}.restore_proof_canary.manifest.json"
    restore_proof_path = canary_root / f"{_safe_artifact_id(quest_id)}-{slug}.restore_proof_canary.restore_proof.json"
    blocker_list = [str(blocker) for blocker in blockers or [] if str(blocker).strip()]
    source_paths = [
        ds_root / str(entry["path"])
        for sample in bucket_samples
        for entry in list(sample.get("entries") or [])
        if isinstance(entry, Mapping) and str(entry.get("path") or "").strip()
    ]
    manifest: dict[str, Any] | None = None
    restore_proof: dict[str, Any] | None = None
    archive_ref: dict[str, Any] | None = None
    archive_created = False
    archive_sha256: str | None = None
    if not blocker_list and source_paths:
        if archive_path.exists() or manifest_path.exists() or restore_proof_path.exists():
            raise FileExistsError(f"restore-proof canary target already exists for {quest_id}: {slug}")
        manifest = _source_manifest(
            quest_root=resolved_quest_root,
            ds_root=ds_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            source_paths=source_paths,
            selected_buckets=selected_buckets,
            shard={
                "group_id": "bounded_canary",
                "group_index": 1,
                "group_count": 1,
                "entry_limit_per_bucket": bounded_limit,
                "source_retained": True,
            },
        )
        _write_json(manifest_path, manifest)
        with tarfile.open(archive_path, "w:gz") as tar:
            for source_path in source_paths:
                tar.add(source_path, arcname=source_path.relative_to(ds_root).as_posix(), recursive=True)
        archive_created = True
        archive_sha256 = _file_sha256(archive_path)
        restore_proof = _restore_proof(
            archive_path=archive_path,
            manifest=manifest,
            archive_sha256=archive_sha256,
            verified_at=_utc_now(),
        )
        _write_json(restore_proof_path, restore_proof)
        archive_ref = {
            "surface_kind": "runtime_archive_ref",
            "schema_version": SCHEMA_VERSION,
            "quest_id": quest_id,
            "quest_root": str(resolved_quest_root),
            "archive_id": f"runtime-restore-proof-canary::{quest_id}::{slug}",
            "archived_at": recorded_at,
            "archive_path": str(archive_path),
            "archive_format": ARCHIVE_FORMAT,
            "sha256": archive_sha256,
            "bytes": archive_path.stat().st_size,
            "source_manifest_path": str(manifest_path),
            "restore_proof_path": str(restore_proof_path),
            "source_buckets": [path.relative_to(ds_root).as_posix() for path in source_paths],
            "source_file_count": len(manifest["source_files"]),
            "restore_command": f"tar -xzf {archive_path} -C {ds_root}",
            "source_retained": True,
        }
    status = (
        "blocked_not_stopped_cold"
        if blocker_list
        else "nothing_to_archive"
        if not source_paths
        else "verified"
        if restore_proof and restore_proof.get("status") == "verified"
        else "blocked_restore_proof_failed"
    )
    plan = {
        "surface_kind": "runtime_restore_proof_compaction_canary",
        "schema_version": SCHEMA_VERSION,
        "status": status,
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "recorded_at": recorded_at,
        "receipt_ref": receipt_ref,
        "source_buckets": list(selected_buckets),
        "entry_limit_per_bucket": bounded_limit,
        "bucket_samples": bucket_samples,
        "bucket_sample_count": len(bucket_samples),
        "blockers": blocker_list,
        "compaction_apply_eligible": not blocker_list,
        "actual_release_bytes": 0,
        "archive_ref": archive_ref,
        "archive_ref_count": 1 if archive_ref else 0,
        "archive_path": str(archive_path) if archive_created else None,
        "source_manifest_path": str(manifest_path) if manifest else None,
        "restore_proof": restore_proof,
        "restore_proof_path": str(restore_proof_path) if restore_proof else None,
        "pruned_paths": [],
        "source_retained": True,
        "body_included": False,
        "recursive_hash_scan_performed": bool(manifest),
        "bounded_source_path_count": len(source_paths),
        "archive_created": archive_created,
        "mutated_runtime_payload": False,
        "sqlite_record_counts_as_stage_complete": False,
        "authority_boundary": {
            "role": "bounded_restore_proof_canary_receipt",
            "stores_body": False,
            "stores_domain_truth": False,
            "writes_archive_body": archive_created,
            "prunes_runtime_payload": False,
            "owner_receipt_authority": "med-autoscience",
            "generic_state_index_owner": "one-person-lab",
        },
    }
    receipt = {
        "surface_kind": "runtime_restore_proof_compaction_canary_receipt",
        "schema_version": SCHEMA_VERSION,
        "receipt_ref": receipt_ref,
        "receipt_kind": "mas_refs_only_restore_proof_canary",
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "recorded_at": recorded_at,
        "plan_path": str(plan_path),
        "source_buckets": list(selected_buckets),
        "entry_limit_per_bucket": bounded_limit,
        "body_included": False,
        "archive_created": archive_created,
        "archive_ref": archive_ref,
        "restore_proof_status": restore_proof.get("status") if restore_proof else None,
        "source_retained": True,
        "mutated_runtime_payload": False,
        "pruned_paths": [],
        "blockers": blocker_list,
        "authority_boundary": plan["authority_boundary"],
    }
    _write_json(plan_path, plan)
    _write_json(receipt_path, receipt)
    result = dict(plan)
    result["plan_path"] = str(plan_path)
    result["receipt_path"] = str(receipt_path)
    return result


def compact_cold_runtime_buckets(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    buckets: Iterable[str],
    max_shards: int | None = None,
) -> dict[str, Any]:
    resolved_quest_root = Path(quest_root).expanduser().resolve()
    ds_root = resolved_quest_root / ".ds"
    selected_buckets = tuple(dict.fromkeys(_bucket_name(bucket) for bucket in buckets))
    source_groups = _source_groups(ds_root=ds_root, selected_buckets=selected_buckets)
    bounded_max_shards = _bounded_max_shards(max_shards)
    all_source_group_count = len(source_groups)
    selected_source_groups = source_groups[:bounded_max_shards] if bounded_max_shards else source_groups
    remaining_source_group_count = max(0, all_source_group_count - len(selected_source_groups))
    if not source_groups:
        empty_bucket_pruned_paths = _prune_empty_selected_bucket_dirs(
            ds_root=ds_root,
            selected_buckets=selected_buckets,
        )
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "nothing_to_archive",
            "quest_id": quest_id,
            "quest_root": str(resolved_quest_root),
            "source_buckets": list(selected_buckets),
            "actual_release_bytes": 0,
            "archive_ref": None,
            "archive_ref_count": 0,
            "restore_proof": None,
            "pruned_paths": [],
            "empty_bucket_pruned_paths": empty_bucket_pruned_paths,
            "blockers": [],
            "source_group_count": 0,
            "selected_source_group_count": 0,
            "remaining_source_group_count": 0,
            "max_shards": bounded_max_shards,
        }
    slug = _artifact_slug(recorded_at)
    shards: list[dict[str, Any]] = []
    for index, source_group in enumerate(selected_source_groups, start=1):
        shard = _compact_source_group(
            quest_root=resolved_quest_root,
            ds_root=ds_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            slug=slug,
            group_index=index,
            group_count=len(selected_source_groups),
            group_id=source_group["group_id"],
            source_paths=source_group["source_paths"],
        )
        if shard["status"] != "compacted":
            archive_refs = [entry["archive_ref"] for entry in shards if isinstance(entry.get("archive_ref"), Mapping)]
            source_manifest_paths = [*list(_shard_paths(shards, "source_manifest_path")), shard.get("source_manifest_path")]
            restore_proof_paths = [*list(_shard_paths(shards, "restore_proof_path")), shard.get("restore_proof_path")]
            pruned_paths = [path for entry in shards for path in list(entry.get("pruned_paths") or [])]
            archive_refs_path = _write_archive_refs_index(
                quest_root=resolved_quest_root,
                quest_id=quest_id,
                recorded_at=recorded_at,
                slug=slug,
                archive_refs=archive_refs,
            )
            return {
                "surface_kind": SURFACE_KIND,
                "schema_version": SCHEMA_VERSION,
                "status": shard["status"],
                "quest_id": quest_id,
                "quest_root": str(resolved_quest_root),
                "source_buckets": list(selected_buckets),
                "actual_release_bytes": 0,
                "archive_ref": None,
                "archive_ref_count": len(archive_refs),
                "archive_refs_path": str(archive_refs_path) if archive_refs_path is not None else None,
                "archive_refs_inlined": False,
                "archive_ref_samples": _archive_ref_samples(archive_refs),
                "source_manifest_path": shard.get("source_manifest_path"),
                "source_manifest_path_summary": _path_summary(source_manifest_paths),
                "restore_proof": shard.get("restore_proof"),
                "restore_proof_path": shard.get("restore_proof_path"),
                "restore_proof_path_summary": _path_summary(restore_proof_paths),
                "pruned_path_count": len(pruned_paths),
                "pruned_paths_inlined": False,
                "pruned_path_samples": _sample_values(pruned_paths),
                "blockers": shard.get("blockers") or [{"reason": "restore_proof_failed"}],
                "shard_count": len(shards),
                "shards_inlined": False,
                "shard_samples": _sample_values([_shard_report_summary(entry) for entry in shards]),
                "failed_shard": _shard_report_summary(shard),
                "source_group_count": all_source_group_count,
                "selected_source_group_count": len(selected_source_groups),
                "remaining_source_group_count": remaining_source_group_count,
                "max_shards": bounded_max_shards,
            }
        shards.append(shard)

    archive_refs = [entry["archive_ref"] for entry in shards if isinstance(entry.get("archive_ref"), Mapping)]
    source_manifest_paths = list(_shard_paths(shards, "source_manifest_path"))
    restore_proof_paths = list(_shard_paths(shards, "restore_proof_path"))
    bytes_before = sum(int(entry.get("bytes_before") or 0) for entry in shards)
    files_before = sum(int(entry.get("files_before") or 0) for entry in shards)
    actual_release_bytes = sum(int(entry.get("actual_release_bytes") or 0) for entry in shards)
    pruned_paths = [path for entry in shards for path in list(entry.get("pruned_paths") or [])]
    empty_bucket_pruned_paths = _prune_empty_selected_bucket_dirs(
        ds_root=ds_root,
        selected_buckets=selected_buckets,
    )
    if len(shards) > 1:
        archive_refs_path = _write_archive_refs_index(
            quest_root=resolved_quest_root,
            quest_id=quest_id,
            recorded_at=recorded_at,
            slug=slug,
            archive_refs=archive_refs,
        )
        return {
            "surface_kind": SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "status": "compacted",
            "quest_id": quest_id,
            "quest_root": str(resolved_quest_root),
            "source_buckets": list(selected_buckets),
            "archive_root": str(_archive_root(resolved_quest_root)),
            "source_manifest_path": None,
            "source_manifest_path_summary": _path_summary(source_manifest_paths),
            "restore_proof_path": None,
            "restore_proof_path_summary": _path_summary(restore_proof_paths),
            "archive_ref": None,
            "archive_ref_count": len(archive_refs),
            "archive_refs_path": str(archive_refs_path) if archive_refs_path is not None else None,
            "archive_refs_inlined": False,
            "archive_ref_samples": _archive_ref_samples(archive_refs),
            "restore_proof": None,
            "restore_proofs_inlined": False,
            "restore_proof_samples": _sample_values(
                [entry.get("restore_proof") for entry in shards if isinstance(entry.get("restore_proof"), Mapping)]
            ),
            "bytes_before": bytes_before,
            "files_before": files_before,
            "actual_release_bytes": actual_release_bytes,
            "pruned_path_count": len(pruned_paths),
            "pruned_paths_inlined": False,
            "pruned_path_samples": _sample_values(pruned_paths),
            "empty_bucket_pruned_paths": empty_bucket_pruned_paths,
            "blockers": [],
            "shard_count": len(shards),
            "shards_inlined": False,
            "shard_samples": _sample_values([_shard_report_summary(entry) for entry in shards]),
            "source_group_count": all_source_group_count,
            "selected_source_group_count": len(selected_source_groups),
            "remaining_source_group_count": remaining_source_group_count,
            "max_shards": bounded_max_shards,
        }
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": "compacted",
        "quest_id": quest_id,
        "quest_root": str(resolved_quest_root),
        "source_buckets": list(selected_buckets),
        "archive_root": str(_archive_root(resolved_quest_root)),
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
        "empty_bucket_pruned_paths": empty_bucket_pruned_paths,
        "blockers": [],
        "shards": shards,
        "source_group_count": all_source_group_count,
        "selected_source_group_count": len(selected_source_groups),
        "remaining_source_group_count": remaining_source_group_count,
        "max_shards": bounded_max_shards,
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


def archive_refs_from_compaction_result(compaction: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    archive_refs = compaction.get("archive_refs")
    if isinstance(archive_refs, list):
        return [archive_ref for archive_ref in archive_refs if isinstance(archive_ref, Mapping)]
    archive_refs_path = compaction.get("archive_refs_path")
    if isinstance(archive_refs_path, str) and archive_refs_path.strip():
        payload = json.loads(Path(archive_refs_path).expanduser().read_text(encoding="utf-8"))
        indexed_refs = payload.get("archive_refs") if isinstance(payload, Mapping) else None
        if isinstance(indexed_refs, list):
            return [archive_ref for archive_ref in indexed_refs if isinstance(archive_ref, Mapping)]
        return []
    archive_ref = compaction.get("archive_ref")
    return [archive_ref] if isinstance(archive_ref, Mapping) else []


def _bucket_canary_sample(*, ds_root: Path, bucket: str, entry_limit: int) -> dict[str, Any]:
    bucket_path = ds_root / bucket
    if not bucket_path.exists():
        return {
            "bucket": bucket,
            "path": str(bucket_path),
            "status": "missing",
            "sampled_entry_count": 0,
            "has_more_than_limit": False,
            "entries": [],
        }
    if bucket_path.is_symlink():
        return {
            "bucket": bucket,
            "path": str(bucket_path),
            "status": "sampled",
            "sampled_entry_count": 1,
            "has_more_than_limit": False,
            "entries": [_canary_entry(ds_root=ds_root, path=bucket_path)],
        }
    if bucket_path.is_file():
        return {
            "bucket": bucket,
            "path": str(bucket_path),
            "status": "sampled",
            "sampled_entry_count": 1,
            "has_more_than_limit": False,
            "entries": [_canary_entry(ds_root=ds_root, path=bucket_path)],
        }
    if not bucket_path.is_dir():
        return {
            "bucket": bucket,
            "path": str(bucket_path),
            "status": "unsupported_path_type",
            "sampled_entry_count": 0,
            "has_more_than_limit": False,
            "entries": [],
        }
    try:
        observed = list(
            itertools.islice(
                (path for path in bucket_path.rglob("*") if path.is_file() or path.is_symlink()),
                entry_limit + 1,
            )
        )
    except OSError as exc:
        return {
            "bucket": bucket,
            "path": str(bucket_path),
            "status": "blocked_unreadable_bucket",
            "sampled_entry_count": 0,
            "has_more_than_limit": False,
            "entries": [],
            "blockers": [{"reason": "bucket_not_readable", "error": str(exc)}],
        }
    sample = sorted(observed[:entry_limit], key=lambda path: path.name)
    return {
        "bucket": bucket,
        "path": str(bucket_path),
        "status": "sampled",
        "sampled_entry_count": len(sample),
        "has_more_than_limit": len(observed) > entry_limit,
        "sampling_kind": "bounded_recursive_file_or_symlink_sample",
        "entries": [_canary_entry(ds_root=ds_root, path=entry) for entry in sample],
    }


def _canary_entry(*, ds_root: Path, path: Path) -> dict[str, Any]:
    if path.is_symlink():
        entry_type = "symlink"
        size_bytes = path.lstat().st_size
    elif path.is_file():
        entry_type = "file"
        size_bytes = path.stat().st_size
    elif path.is_dir():
        entry_type = "directory"
        size_bytes = None
    else:
        entry_type = "other"
        size_bytes = None
    return {
        "path": path.relative_to(ds_root).as_posix(),
        "entry_type": entry_type,
        "size_bytes": size_bytes,
        "body_included": False,
        "content_hash": None,
    }


def _source_groups(*, ds_root: Path, selected_buckets: tuple[str, ...]) -> list[dict[str, Any]]:
    groups: list[dict[str, Any]] = []
    regular_sources: list[Path] = []
    for bucket in selected_buckets:
        bucket_path = ds_root / bucket
        if not bucket_path.exists():
            continue
        if bucket in {"codex_homes", "runs"} and bucket_path.is_dir():
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


def _bounded_max_shards(value: int | None) -> int | None:
    if value is None:
        return None
    return max(1, int(value))


def _prune_empty_selected_bucket_dirs(*, ds_root: Path, selected_buckets: tuple[str, ...]) -> list[str]:
    pruned_paths: list[str] = []
    for bucket in selected_buckets:
        bucket_path = ds_root / bucket
        if not bucket_path.exists() or not bucket_path.is_dir() or bucket_path.is_symlink():
            continue
        for child in sorted(bucket_path.iterdir(), reverse=True):
            if not child.is_dir() or child.is_symlink() or _has_any_payload(child):
                continue
            try:
                child.rmdir()
            except OSError:
                continue
            pruned_paths.append(str(child))
        try:
            bucket_path.rmdir()
        except OSError:
            continue
        pruned_paths.append(str(bucket_path))
    return pruned_paths


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


def _write_archive_refs_index(
    *,
    quest_root: Path,
    quest_id: str,
    recorded_at: str,
    slug: str,
    archive_refs: list[Mapping[str, Any]],
) -> Path | None:
    if not archive_refs:
        return None
    archive_root = _archive_root(quest_root)
    archive_root.mkdir(parents=True, exist_ok=True)
    path = archive_root / f"{_safe_artifact_id(quest_id)}-{slug}.archive_refs.json"
    payload = {
        "surface_kind": "runtime_restore_proof_archive_refs_index",
        "schema_version": SCHEMA_VERSION,
        "quest_id": quest_id,
        "quest_root": str(quest_root),
        "recorded_at": recorded_at,
        "archive_ref_count": len(archive_refs),
        "archive_refs": [dict(ref) for ref in archive_refs],
    }
    _write_json(path, payload)
    return path


def _path_summary(paths: Iterable[Any]) -> dict[str, Any]:
    values = [str(path) for path in paths if isinstance(path, str) and path]
    return {
        "count": len(values),
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
        "samples": _sample_values(values),
    }


def _archive_ref_samples(archive_refs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for ref in _sample_values([dict(ref) for ref in archive_refs]):
        samples.append(
            {
                "archive_id": ref.get("archive_id"),
                "archive_path": ref.get("archive_path"),
                "source_manifest_path": ref.get("source_manifest_path"),
                "restore_proof_path": ref.get("restore_proof_path"),
                "bytes": ref.get("bytes"),
                "source_file_count": ref.get("source_file_count"),
            }
        )
    return samples


def _shard_report_summary(shard: Mapping[str, Any]) -> dict[str, Any]:
    archive_ref = shard.get("archive_ref") if isinstance(shard.get("archive_ref"), Mapping) else {}
    restore_proof = shard.get("restore_proof") if isinstance(shard.get("restore_proof"), Mapping) else {}
    pruned_paths = [str(path) for path in list(shard.get("pruned_paths") or []) if isinstance(path, str)]
    return {
        "surface_kind": shard.get("surface_kind"),
        "schema_version": shard.get("schema_version"),
        "status": shard.get("status"),
        "quest_id": shard.get("quest_id"),
        "group_id": shard.get("group_id"),
        "group_index": shard.get("group_index"),
        "group_count": shard.get("group_count"),
        "source_manifest_path": shard.get("source_manifest_path"),
        "restore_proof_path": shard.get("restore_proof_path"),
        "archive_id": archive_ref.get("archive_id"),
        "archive_path": archive_ref.get("archive_path"),
        "restore_proof_status": restore_proof.get("status"),
        "bytes_before": shard.get("bytes_before"),
        "files_before": shard.get("files_before"),
        "actual_release_bytes": shard.get("actual_release_bytes"),
        "pruned_path_count": len(pruned_paths),
        "pruned_path_samples": _sample_values(pruned_paths),
        "blockers": shard.get("blockers") or [],
    }


def _sample_values(values: Iterable[Any], *, limit: int = REPORT_SAMPLE_LIMIT) -> list[Any]:
    items = list(values)
    if len(items) <= limit:
        return items
    head_count = max(1, limit // 2)
    tail_count = max(1, limit - head_count)
    sampled = [*items[:head_count], *items[-tail_count:]]
    deduped: list[Any] = []
    for item in sampled:
        if item not in deduped:
            deduped.append(item)
    return deduped


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
        for path in _manifest_source_paths(source_path):
            source_files.append(_source_manifest_entry(ds_root=ds_root, path=path))
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


def _manifest_source_paths(source_path: Path) -> Iterable[Path]:
    if source_path.is_symlink() or source_path.is_file():
        yield source_path
        return
    if source_path.is_dir():
        for path in sorted(source_path.rglob("*")):
            if path.is_symlink() or path.is_file():
                yield path


def _source_manifest_entry(*, ds_root: Path, path: Path) -> dict[str, Any]:
    if path.is_symlink():
        return {
            "path": path.relative_to(ds_root).as_posix(),
            "entry_type": "symlink",
            "size_bytes": path.lstat().st_size,
            "link_target": str(path.readlink()),
        }
    return {
        "path": path.relative_to(ds_root).as_posix(),
        "entry_type": "file",
        "size_bytes": path.stat().st_size,
        "sha256": _file_sha256(path),
    }


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


def _canary_root(quest_root: Path) -> Path:
    return quest_root / "artifacts" / "runtime" / "runtime_storage_maintenance" / "restore_proof_canary"


def _bucket_name(value: str) -> str:
    name = str(value or "").strip()
    if not name or name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError(f"invalid runtime bucket name: {value!r}")
    return name


__all__ = [
    "ARCHIVE_FORMAT",
    "COLD_RUNTIME_STATUSES",
    "PARKED_CONTROLLER_STOP_STATUSES",
    "SURFACE_KIND",
    "compact_cold_runtime_buckets",
    "plan_restore_proof_compaction_canary",
    "restore_proof_compaction_blockers",
    "restore_proof_compaction_candidate",
]
