from __future__ import annotations

from pathlib import Path

from med_autoscience.display_pack_gallery_parts.asset_reuse import seed_package_only_assets
from med_autoscience.display_pack_gallery_parts.pdf import copy_pdf_if_content_changed


def test_package_only_asset_reuse_seeds_empty_output_from_docs_mirror(tmp_path: Path) -> None:
    source = tmp_path / "docs_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    (source / "roc_curve_binary.png").write_bytes(b"png")
    (source / "roc_curve_binary.layout.json").write_text("{}", encoding="utf-8")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "seeded_from_docs_mirror"
    assert result["copied_file_count"] == 2
    assert (target / "roc_curve_binary.png").read_bytes() == b"png"
    assert (target / "roc_curve_binary.layout.json").read_text(encoding="utf-8") == "{}"


def test_package_only_asset_reuse_ignores_existing_manifest_only(tmp_path: Path) -> None:
    source = tmp_path / "docs_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    target.mkdir()
    (source / "calibration_curve_binary.png").write_bytes(b"png")
    (target / "gallery_manifest.json").write_text("{}", encoding="utf-8")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "seeded_from_docs_mirror"
    assert result["copied_file_count"] == 1
    assert (target / "calibration_curve_binary.png").is_file()


def test_package_only_asset_reuse_does_not_overwrite_populated_output(tmp_path: Path) -> None:
    source = tmp_path / "docs_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    target.mkdir()
    (source / "roc_curve_binary.png").write_bytes(b"new")
    (target / "roc_curve_binary.png").write_bytes(b"existing")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "target_already_complete"
    assert result["copied_file_count"] == 0
    assert result["skipped_existing_count"] == 1
    assert (target / "roc_curve_binary.png").read_bytes() == b"existing"


def test_package_only_asset_reuse_fills_missing_files_without_overwriting(tmp_path: Path) -> None:
    source = tmp_path / "docs_assets"
    target = tmp_path / "output_assets"
    source.mkdir()
    target.mkdir()
    (source / "roc_curve_binary.png").write_bytes(b"new")
    (source / "roc_curve_binary.layout.json").write_text("{}", encoding="utf-8")
    (target / "roc_curve_binary.png").write_bytes(b"existing")

    result = seed_package_only_assets(source_asset_root=source, target_asset_root=target)

    assert result["status"] == "seeded_from_docs_mirror"
    assert result["copied_file_count"] == 1
    assert result["skipped_existing_count"] == 1
    assert (target / "roc_curve_binary.png").read_bytes() == b"existing"
    assert (target / "roc_curve_binary.layout.json").read_text(encoding="utf-8") == "{}"


def test_package_only_asset_reuse_reports_missing_or_empty_source(tmp_path: Path) -> None:
    target = tmp_path / "output_assets"

    missing = seed_package_only_assets(
        source_asset_root=tmp_path / "missing_docs_assets",
        target_asset_root=target,
    )
    assert missing["status"] == "source_missing"

    empty_source = tmp_path / "empty_docs_assets"
    empty_source.mkdir()
    empty = seed_package_only_assets(
        source_asset_root=empty_source,
        target_asset_root=target,
    )
    assert empty["status"] == "source_empty"


def test_docs_pdf_copy_ignores_chrome_timestamp_only_changes(tmp_path: Path) -> None:
    target = tmp_path / "gallery.pdf"
    source = tmp_path / "rebuilt.pdf"
    target.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<</CreationDate (D:20260623112930+00'00')/ModDate (D:20260623112930+00'00')>>\n"
        b"stream\nsame content\nendstream\n%%EOF\n"
    )
    original = target.read_bytes()
    source.write_bytes(
        b"%PDF-1.4\n"
        b"1 0 obj\n"
        b"<</CreationDate (D:20260623113441+00'00')/ModDate (D:20260623113441+00'00')>>\n"
        b"stream\nsame content\nendstream\n%%EOF\n"
    )

    copy_pdf_if_content_changed(source, target)

    assert target.read_bytes() == original
