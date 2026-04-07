from __future__ import annotations

import json
from pathlib import Path
import tomllib
from typing import Any

from med_autoscience.display_pack_contract import load_display_pack_manifest


def _expect_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{key} must be non-empty")
    return normalized


def _expect_str_list(payload: dict[str, Any], key: str) -> list[str]:
    value = payload.get(key)
    if not isinstance(value, list) or not value:
        raise ValueError(f"{key} must be a non-empty list")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str) or not item.strip():
            raise ValueError(f"{key}[{index}] must be a non-empty string")
        result.append(item.strip())
    return result


def collect_enabled_pack_provenance(*, repo_root: Path) -> list[dict[str, str]]:
    config_path = Path(repo_root) / "config" / "display_packs.toml"
    config_payload = tomllib.loads(config_path.read_text(encoding="utf-8"))
    enabled_pack_ids = _expect_str_list(config_payload, "default_enabled_packs")
    sources = config_payload.get("sources")
    if not isinstance(sources, list):
        raise ValueError("sources must be a list")

    source_by_pack_id: dict[str, dict[str, Any]] = {}
    for index, source in enumerate(sources):
        if not isinstance(source, dict):
            raise ValueError(f"sources[{index}] must be an object")
        pack_id = _expect_str(source, "pack_id")
        if pack_id in source_by_pack_id:
            raise ValueError(f"duplicate source for pack_id `{pack_id}`")
        source_by_pack_id[pack_id] = source

    provenance_entries: list[dict[str, str]] = []
    for pack_id in enabled_pack_ids:
        source = source_by_pack_id.get(pack_id)
        if source is None:
            raise ValueError(f"enabled pack `{pack_id}` is missing from sources")
        source_kind = _expect_str(source, "kind")
        if source_kind != "local_dir":
            raise ValueError(f"unsupported enabled pack source kind `{source_kind}` for `{pack_id}`")
        source_path = _expect_str(source, "path")
        manifest_relative_path = (Path(source_path) / "display_pack.toml").as_posix()
        manifest_path = Path(repo_root) / manifest_relative_path
        manifest = load_display_pack_manifest(manifest_path)
        if manifest.pack_id != pack_id:
            raise ValueError(f"pack_id mismatch: enabled={pack_id!r}, manifest={manifest.pack_id!r}")
        provenance_entries.append(
            {
                "pack_id": manifest.pack_id,
                "version": manifest.version,
                "display_api_version": manifest.display_api_version,
                "default_execution_mode": manifest.default_execution_mode,
                "source_kind": source_kind,
                "source_path": source_path,
                "manifest_path": manifest_relative_path,
            }
        )

    return provenance_entries


def build_display_pack_lock_payload(*, repo_root: Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "enabled_packs": collect_enabled_pack_provenance(repo_root=repo_root),
    }


def write_display_pack_lock(*, paper_root: Path, repo_root: Path) -> Path:
    output_path = Path(paper_root) / "build" / "display_pack_lock.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    payload = build_display_pack_lock_payload(repo_root=repo_root)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return output_path
