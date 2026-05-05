from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def _content_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def path_fingerprint(path: Path | None) -> dict[str, Any] | None:
    if path is None:
        return None
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists():
        return {"path": str(resolved), "exists": False}
    stat = resolved.stat()
    if resolved.is_dir():
        return {
            "path": str(resolved),
            "exists": True,
            "is_dir": True,
            "mtime_ns": stat.st_mtime_ns,
        }
    return {
        "path": str(resolved),
        "exists": True,
        "size": stat.st_size,
        "content_sha256": _content_sha256(resolved),
        "mtime_ns": stat.st_mtime_ns,
    }


def globbed_path_fingerprints(root: Path, *patterns: str, limit: int = 64) -> list[dict[str, Any]]:
    if not root.exists():
        return []
    fingerprints: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file():
                continue
            resolved = path.expanduser().resolve()
            if resolved in seen:
                continue
            seen.add(resolved)
            fingerprint = path_fingerprint(resolved)
            if fingerprint is not None:
                fingerprints.append(fingerprint)
            if len(fingerprints) >= limit:
                return fingerprints
    return fingerprints


def path_fingerprints(*paths: Path | None, limit: int = 64) -> list[dict[str, Any]]:
    fingerprints: list[dict[str, Any]] = []
    seen: set[Path] = set()
    for path in paths:
        if path is None:
            continue
        resolved = path.expanduser().resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        fingerprint = path_fingerprint(resolved)
        if fingerprint is not None:
            fingerprints.append(fingerprint)
        if len(fingerprints) >= limit:
            break
    return fingerprints
