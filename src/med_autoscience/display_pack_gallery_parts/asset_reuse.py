from __future__ import annotations

from pathlib import Path
import shutil
from typing import Any

from med_autoscience.display_pack_gallery_parts import paths

_ASSET_SUFFIXES = {
    ".json",
    ".pdf",
    ".png",
    ".svg",
}


def seed_package_only_assets_from_docs_mirror() -> dict[str, Any]:
    docs_asset_root = paths.EXAMPLES_ROOT / paths.ASSET_ROOT.name
    return seed_package_only_assets(
        source_asset_root=docs_asset_root,
        target_asset_root=paths.ASSET_ROOT,
    )


def seed_package_only_assets(
    *,
    source_asset_root: Path,
    target_asset_root: Path,
) -> dict[str, Any]:
    if source_asset_root.resolve() == target_asset_root.resolve():
        return {
            "status": "same_asset_root",
            "source_asset_root": str(source_asset_root),
            "target_asset_root": str(target_asset_root),
            "copied_file_count": 0,
        }
    if not source_asset_root.is_dir():
        return {
            "status": "source_missing",
            "source_asset_root": str(source_asset_root),
            "target_asset_root": str(target_asset_root),
            "copied_file_count": 0,
            "missing_source_count": 0,
            "skipped_existing_count": 0,
        }
    target_asset_root.mkdir(parents=True, exist_ok=True)
    copied = 0
    missing_source = 0
    skipped_existing = 0
    extension_counts: dict[str, int] = {}
    source_files = [
        path
        for path in sorted(source_asset_root.iterdir())
        if path.is_file() and path.suffix in _ASSET_SUFFIXES
    ]
    if not source_files:
        return {
            "status": "source_empty",
            "source_asset_root": str(source_asset_root),
            "target_asset_root": str(target_asset_root),
            "copied_file_count": 0,
            "missing_source_count": 0,
            "skipped_existing_count": 0,
            "extension_counts": {},
        }
    for source_path in source_files:
        target_path = target_asset_root / source_path.name
        if target_path.is_file():
            skipped_existing += 1
            continue
        if not source_path.is_file():
            missing_source += 1
            continue
        shutil.copy2(source_path, target_path)
        copied += 1
        extension_counts[source_path.suffix] = extension_counts.get(source_path.suffix, 0) + 1
    return {
        "status": "seeded_from_docs_mirror" if copied else "target_already_complete",
        "source_asset_root": str(source_asset_root),
        "target_asset_root": str(target_asset_root),
        "copied_file_count": copied,
        "missing_source_count": missing_source,
        "skipped_existing_count": skipped_existing,
        "extension_counts": extension_counts,
    }
