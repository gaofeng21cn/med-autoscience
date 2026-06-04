from __future__ import annotations

from collections.abc import Iterable, Mapping
import itertools
from pathlib import Path
from typing import Any


REPORT_SAMPLE_LIMIT = 5


def bucket_canary_sample(*, ds_root: Path, bucket: str, entry_limit: int) -> dict[str, Any]:
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
    if bucket_path.is_symlink() or bucket_path.is_file():
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


def restore_proof_summary(restore_proof: Mapping[str, Any]) -> dict[str, Any]:
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


def path_summary(paths: Iterable[Any]) -> dict[str, Any]:
    values = [str(path) for path in paths if isinstance(path, str) and path]
    return {
        "count": len(values),
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
        "samples": sample_values(values),
    }


def archive_ref_samples(archive_refs: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    samples: list[dict[str, Any]] = []
    for ref in sample_values([dict(ref) for ref in archive_refs]):
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


def shard_report_summary(shard: Mapping[str, Any]) -> dict[str, Any]:
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
        "pruned_path_samples": sample_values(pruned_paths),
        "blockers": shard.get("blockers") or [],
    }


def sample_values(values: Iterable[Any], *, limit: int = REPORT_SAMPLE_LIMIT) -> list[Any]:
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


def shard_paths(shards: Iterable[Mapping[str, Any]], key: str) -> Iterable[str]:
    for shard in shards:
        value = shard.get(key)
        if isinstance(value, str) and value:
            yield value


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


__all__ = [
    "archive_ref_samples",
    "bucket_canary_sample",
    "path_summary",
    "restore_proof_summary",
    "sample_values",
    "shard_paths",
    "shard_report_summary",
]
