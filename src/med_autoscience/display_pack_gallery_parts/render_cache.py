from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable
import hashlib
import json

from med_autoscience.display_pack_gallery_parts import paths
from med_autoscience.display_pack_gallery_parts.assets import write_json

RENDER_CACHE_SCHEMA_VERSION = 1


def stable_payload_digest(payload: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _repo_relative(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(paths.REPO_ROOT))
    except ValueError:
        return str(path.resolve())


def render_cache_key(
    *,
    renderer: str,
    payload: dict[str, Any],
    request: dict[str, Any],
    source_paths: Iterable[Path],
) -> str:
    source_fingerprints: list[dict[str, str]] = []
    for source_path in sorted({path.resolve() for path in source_paths}, key=str):
        if source_path.is_file():
            source_fingerprints.append(
                {
                    "path": _repo_relative(source_path),
                    "sha256": _file_digest(source_path),
                }
            )
        else:
            source_fingerprints.append(
                {
                    "path": _repo_relative(source_path),
                    "sha256": "missing",
                }
            )
    key_payload = {
        "schema_version": RENDER_CACHE_SCHEMA_VERSION,
        "renderer": renderer,
        "payload_sha256": stable_payload_digest(payload),
        "request_sha256": stable_payload_digest(request),
        "source_fingerprints": source_fingerprints,
    }
    return f"sha256:{stable_payload_digest(key_payload)}"


def cache_hit(
    *,
    cache_path: Path,
    cache_key: str,
    required_outputs: Iterable[Path],
) -> bool:
    if not all(path.is_file() for path in required_outputs):
        return False
    if not cache_path.is_file():
        return False
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return False
    return (
        isinstance(payload, dict)
        and payload.get("schema_version") == RENDER_CACHE_SCHEMA_VERSION
        and payload.get("render_cache_key") == cache_key
    )


def write_render_cache(
    *,
    cache_path: Path,
    cache_key: str,
    renderer: str,
) -> None:
    write_json(
        cache_path,
        {
            "schema_version": RENDER_CACHE_SCHEMA_VERSION,
            "renderer": renderer,
            "render_cache_key": cache_key,
        },
    )
