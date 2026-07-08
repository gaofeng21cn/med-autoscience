from __future__ import annotations

import shutil
from pathlib import Path

from .delivery_io import create_staging_root, replace_directory_atomically, write_relative_symlink, write_text
from .delivery_rendering import build_user_delivery_entry_readme


def _sync_user_delivery_entry(
    *,
    study_root: Path,
    study_id: str,
    stage: str,
    source_relative_root: str,
    current_package_root: Path,
    current_package_zip: Path,
    journal_packages_root: Path | None = None,
    journal_package_mirrors_root: Path | None = None,
) -> Path:
    delivery_root = study_root / "delivery"
    staging_root = create_staging_root(target_root=delivery_root)
    try:
        write_text(
            staging_root / "README.md",
            build_user_delivery_entry_readme(
                study_id=study_id,
                stage=stage,
                source_relative_root=source_relative_root,
                has_journal_packages=bool(journal_packages_root and journal_packages_root.exists()),
                has_journal_package_mirrors=bool(
                    journal_package_mirrors_root and journal_package_mirrors_root.exists()
                ),
            ),
        )
        if current_package_root.exists():
            write_relative_symlink(
                link_path=staging_root / "current",
                target_path=current_package_root,
                target_is_directory=True,
            )
        if current_package_zip.exists():
            write_relative_symlink(
                link_path=staging_root / "current.zip",
                target_path=current_package_zip,
            )
        if journal_packages_root is not None and journal_packages_root.exists():
            write_relative_symlink(
                link_path=staging_root / "journal_packages",
                target_path=journal_packages_root,
                target_is_directory=True,
            )
        if journal_package_mirrors_root is not None and journal_package_mirrors_root.exists():
            write_relative_symlink(
                link_path=staging_root / "journal_package_mirrors",
                target_path=journal_package_mirrors_root,
                target_is_directory=True,
            )
        replace_directory_atomically(
            staging_root=staging_root,
            target_root=delivery_root,
        )
    except Exception:
        shutil.rmtree(staging_root, ignore_errors=True)
        raise
    return delivery_root


__all__ = ["_sync_user_delivery_entry"]
