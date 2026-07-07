from __future__ import annotations

from pathlib import Path

from med_autoscience.display_pack_gallery.asset_reuse import seed_package_only_assets


def test_package_only_asset_reuse_seeds_empty_output_from_source_assets(tmp_path: Path) -> None:
    source = tmp_path / "source_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    (source / "roc_curve_binary.png").write_bytes(b"png")
    (source / "roc_curve_binary.layout.json").write_text("{}", encoding="utf-8")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "synced_from_source_assets"
    assert result["copied_file_count"] == 2
    assert (target / "roc_curve_binary.png").read_bytes() == b"png"
    assert (target / "roc_curve_binary.layout.json").read_text(encoding="utf-8") == "{}"


def test_package_only_asset_reuse_ignores_existing_manifest_only(tmp_path: Path) -> None:
    source = tmp_path / "source_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    target.mkdir()
    (source / "calibration_curve_binary.png").write_bytes(b"png")
    (target / "gallery_manifest.json").write_text("{}", encoding="utf-8")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "synced_from_source_assets"
    assert result["copied_file_count"] == 1
    assert (target / "calibration_curve_binary.png").is_file()


def test_package_only_asset_reuse_updates_stale_populated_output(tmp_path: Path) -> None:
    source = tmp_path / "source_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    target.mkdir()
    (source / "roc_curve_binary.png").write_bytes(b"new")
    (target / "roc_curve_binary.png").write_bytes(b"existing")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "synced_from_source_assets"
    assert result["copied_file_count"] == 0
    assert result["updated_file_count"] == 1
    assert result["skipped_existing_count"] == 0
    assert (target / "roc_curve_binary.png").read_bytes() == b"new"


def test_package_only_asset_reuse_fills_missing_files_and_updates_stale_files(tmp_path: Path) -> None:
    source = tmp_path / "source_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    target.mkdir()
    (source / "roc_curve_binary.png").write_bytes(b"new")
    (source / "roc_curve_binary.layout.json").write_text("{}", encoding="utf-8")
    (target / "roc_curve_binary.png").write_bytes(b"existing")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "synced_from_source_assets"
    assert result["copied_file_count"] == 1
    assert result["updated_file_count"] == 1
    assert result["skipped_existing_count"] == 0
    assert (target / "roc_curve_binary.png").read_bytes() == b"new"
    assert (target / "roc_curve_binary.layout.json").read_text(encoding="utf-8") == "{}"


def test_package_only_asset_reuse_reports_missing_or_empty_source(tmp_path: Path) -> None:
    target = tmp_path / "output_assets"

    missing = seed_package_only_assets(
        source_asset_root=tmp_path / "missing_source_assets",
        target_asset_root=target,
    )
    assert missing["status"] == "source_missing"

    empty_source = tmp_path / "empty_source_assets"
    empty_source.mkdir()
    empty = seed_package_only_assets(
        source_asset_root=empty_source,
        target_asset_root=target,
    )
    assert empty["status"] == "source_empty"
