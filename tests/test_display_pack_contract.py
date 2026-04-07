from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.display_pack_contract import load_display_pack_manifest


def test_load_display_pack_manifest_parses_minimal_valid_pack() -> None:
    pack_root = (
        Path(__file__).parent
        / "fixtures"
        / "display_packs"
        / "minimal_valid_pack"
    )
    manifest = load_display_pack_manifest(pack_root / "display_pack.toml")

    assert manifest.pack_id == "fenggaolab.org.medical-display-core"
    assert manifest.version == "0.1.0"
    assert manifest.display_api_version == "1"
    assert manifest.default_execution_mode == "python_plugin"


def test_load_display_pack_manifest_rejects_non_namespaced_pack_id(tmp_path: Path) -> None:
    manifest_path = tmp_path / "display_pack.toml"
    manifest_path.write_text(
        'pack_id = "medical-display-core"\nversion = "0.1.0"\ndisplay_api_version = "1"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="pack_id"):
        load_display_pack_manifest(manifest_path)


def test_load_display_pack_manifest_rejects_non_string_type(tmp_path: Path) -> None:
    manifest_path = tmp_path / "display_pack.toml"
    manifest_path.write_text(
        'pack_id = 123\nversion = "0.1.0"\ndisplay_api_version = "1"\ndefault_execution_mode = "python_plugin"\n',
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="pack_id"):
        load_display_pack_manifest(manifest_path)
