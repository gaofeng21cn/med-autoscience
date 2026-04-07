from __future__ import annotations

from pathlib import Path
import tomllib

from med_autoscience.display_pack_contract import (
    DisplayPackManifest,
    load_display_pack_manifest,
)


def load_enabled_local_display_packs(repo_root: Path) -> list[DisplayPackManifest]:
    config_path = repo_root / "config" / "display_packs.toml"
    config_payload = tomllib.loads(config_path.read_text(encoding="utf-8"))

    enabled_pack_ids = set(config_payload["default_enabled_packs"])
    manifests: list[DisplayPackManifest] = []

    for source in config_payload["sources"]:
        if source["kind"] != "local_dir":
            continue

        pack_id = source["pack_id"]
        if pack_id not in enabled_pack_ids:
            continue

        pack_root = repo_root / source["path"]
        manifests.append(load_display_pack_manifest(pack_root / "display_pack.toml"))

    return manifests
