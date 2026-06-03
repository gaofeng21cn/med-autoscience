from __future__ import annotations

from collections import deque
from datetime import UTC, datetime
import gzip
import hashlib
import json
from pathlib import Path
from typing import Any


SURFACE_KIND = "runtime_oversized_jsonl_slimming"


def slim_oversized_jsonl_files(
    *,
    quest_root: Path,
    recorded_at: str,
    threshold_mb: int | None,
    head_lines: int,
    tail_lines: int,
) -> dict[str, Any]:
    threshold_bytes = _threshold_bytes(threshold_mb)
    if threshold_bytes is None:
        return {
            "surface_kind": SURFACE_KIND,
            "status": "disabled",
            "threshold_bytes": None,
            "slimmed_count": 0,
            "actual_release_bytes": 0,
            "files": [],
        }

    resolved_quest_root = Path(quest_root).expanduser().resolve()
    files: list[dict[str, Any]] = []
    actual_release_bytes = 0
    for path in _candidate_jsonl_paths(resolved_quest_root):
        try:
            size_before = path.stat().st_size
        except OSError:
            continue
        if size_before <= threshold_bytes:
            continue
        slim_result = _slim_jsonl_file(
            path=path,
            quest_root=resolved_quest_root,
            recorded_at=recorded_at,
            head_lines=max(1, head_lines),
            tail_lines=max(1, tail_lines),
        )
        files.append(slim_result)
        actual_release_bytes += int(slim_result.get("released_bytes") or 0)

    return {
        "surface_kind": SURFACE_KIND,
        "status": "slimmed" if files else "nothing_to_slim",
        "threshold_bytes": threshold_bytes,
        "slimmed_count": len(files),
        "actual_release_bytes": actual_release_bytes,
        "files": files,
    }


def _candidate_jsonl_paths(quest_root: Path) -> list[Path]:
    roots = (
        quest_root / "artifacts" / "runtime",
        quest_root / "artifacts" / "reports" / "runtime_events",
    )
    candidates: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*.jsonl")):
            if not path.is_file():
                continue
            resolved = path.resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            candidates.append(path)
    return candidates


def _slim_jsonl_file(
    *,
    path: Path,
    quest_root: Path,
    recorded_at: str,
    head_lines: int,
    tail_lines: int,
) -> dict[str, Any]:
    size_before = path.stat().st_size
    sha_before = _sha256(path)
    line_count, head, tail = _head_tail_lines(path, head_lines=head_lines, tail_lines=tail_lines)
    archive_path = _archive_path(
        quest_root=quest_root,
        path=path,
        recorded_at=recorded_at,
        sha256=sha_before,
    )
    archive_path.parent.mkdir(parents=True, exist_ok=True)
    _write_gzip_archive(source_path=path, archive_path=archive_path)
    archive_size = archive_path.stat().st_size

    slim_payload = _slim_payload(
        original_path=path,
        archive_path=archive_path,
        size_before=size_before,
        sha_before=sha_before,
        line_count=line_count,
        head=head,
        tail=tail,
        recorded_at=recorded_at,
    )
    path.unlink()
    path.write_text(json.dumps(slim_payload, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
    size_after = path.stat().st_size
    return {
        "status": "slimmed",
        "path": str(path),
        "archive_path": str(archive_path),
        "bytes_before": size_before,
        "bytes_after": size_after,
        "archive_bytes": archive_size,
        "released_bytes": max(0, size_before - archive_size - size_after),
        "line_count": line_count,
        "head_lines": len(head),
        "tail_lines": len(tail),
        "sha256_before": sha_before,
        "sha256_after": _sha256(path),
    }


def _head_tail_lines(path: Path, *, head_lines: int, tail_lines: int) -> tuple[int, list[str], list[str]]:
    head: list[str] = []
    tail: deque[str] = deque(maxlen=tail_lines)
    line_count = 0
    with path.open("r", encoding="utf-8", errors="replace") as handle:
        for line in handle:
            line_count += 1
            normalized = line.rstrip("\n")
            if len(head) < head_lines:
                head.append(normalized)
            tail.append(normalized)
    return line_count, head, list(tail)


def _slim_payload(
    *,
    original_path: Path,
    archive_path: Path,
    size_before: int,
    sha_before: str,
    line_count: int,
    head: list[str],
    tail: list[str],
    recorded_at: str,
) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "surface_kind": SURFACE_KIND,
        "status": "slimmed_ref",
        "recorded_at": recorded_at,
        "original_path": str(original_path),
        "archive_path": str(archive_path),
        "original_bytes": size_before,
        "original_sha256": sha_before,
        "line_count": line_count,
        "retained_head_lines": head,
        "retained_tail_lines": tail,
    }


def _archive_path(*, quest_root: Path, path: Path, recorded_at: str, sha256: str) -> Path:
    relative = path.resolve().relative_to(quest_root.resolve())
    safe_relative = "__".join(relative.parts)
    slug = _artifact_slug(recorded_at)
    return (
        quest_root
        / "artifacts"
        / "runtime"
        / "runtime_storage_maintenance"
        / "oversized_jsonl"
        / f"{slug}_{safe_relative}_{sha256[:12]}.jsonl.gz"
    )


def _threshold_bytes(threshold_mb: int | None) -> int | None:
    if threshold_mb is None:
        return None
    return max(1, int(threshold_mb)) * 1024 * 1024


def _artifact_slug(recorded_at: str) -> str:
    normalized = recorded_at.strip()
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    return datetime.fromisoformat(normalized).astimezone(UTC).strftime("%Y%m%dT%H%M%SZ")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_gzip_archive(*, source_path: Path, archive_path: Path) -> None:
    with source_path.open("rb") as source, gzip.open(archive_path, "wb", compresslevel=6) as target:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            target.write(chunk)
