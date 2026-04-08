from __future__ import annotations

from pathlib import Path
import tomllib

from med_autoscience.display_pack_contract import (
    DisplayPackManifest,
    DisplayTemplateManifest,
    load_display_pack_manifest,
    load_display_template_manifest,
)


def _iter_enabled_local_pack_roots(repo_root: Path) -> list[tuple[str, Path]]:
    config_path = repo_root / "config" / "display_packs.toml"
    config_payload = tomllib.loads(config_path.read_text(encoding="utf-8"))

    enabled_pack_ids = set(config_payload["default_enabled_packs"])
    pack_roots: list[tuple[str, Path]] = []

    for source in config_payload["sources"]:
        if source["kind"] != "local_dir":
            continue

        pack_id = source["pack_id"]
        if pack_id not in enabled_pack_ids:
            continue
        pack_roots.append((pack_id, repo_root / source["path"]))

    return pack_roots


def load_enabled_local_display_packs(repo_root: Path) -> list[DisplayPackManifest]:
    manifests: list[DisplayPackManifest] = []
    for pack_id, pack_root in _iter_enabled_local_pack_roots(repo_root):
        manifest = load_display_pack_manifest(pack_root / "display_pack.toml")
        if manifest.pack_id != pack_id:
            raise ValueError(
                f"pack_id mismatch: source={pack_id!r}, manifest={manifest.pack_id!r}"
            )
        manifests.append(manifest)
    return manifests


def load_enabled_local_display_pack_templates(repo_root: Path) -> list[DisplayTemplateManifest]:
    manifests: list[DisplayTemplateManifest] = []
    for pack_id, pack_root in _iter_enabled_local_pack_roots(repo_root):
        pack_manifest = load_display_pack_manifest(pack_root / "display_pack.toml")
        if pack_manifest.pack_id != pack_id:
            raise ValueError(
                f"pack_id mismatch: source={pack_id!r}, manifest={pack_manifest.pack_id!r}"
            )
        template_paths = sorted((pack_root / "templates").glob("*/template.toml"))
        for template_path in template_paths:
            manifests.append(
                load_display_template_manifest(
                    template_path,
                    expected_pack_id=pack_manifest.pack_id,
                )
            )
    return manifests
