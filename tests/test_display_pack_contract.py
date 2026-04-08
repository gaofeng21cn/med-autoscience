from __future__ import annotations

from pathlib import Path

import pytest

from med_autoscience.display_pack_contract import (
    load_display_pack_manifest,
    load_display_template_manifest,
)


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
    assert manifest.summary == "Minimal valid display pack fixture"
    assert manifest.maintainer == ""


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


def test_load_display_pack_manifest_rejects_non_semantic_version(tmp_path: Path) -> None:
    manifest_path = tmp_path / "display_pack.toml"
    manifest_path.write_text(
        (
            'pack_id = "fenggaolab.org.medical-display-core"\n'
            'version = "2026.04"\n'
            'display_api_version = "1"\n'
            'default_execution_mode = "python_plugin"\n'
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="version"):
        load_display_pack_manifest(manifest_path)


def test_load_display_template_manifest_parses_minimal_valid_template() -> None:
    template_path = (
        Path(__file__).parent
        / "fixtures"
        / "display_packs"
        / "minimal_valid_pack"
        / "templates"
        / "roc_curve_binary"
        / "template.toml"
    )

    manifest = load_display_template_manifest(
        template_path,
        expected_pack_id="fenggaolab.org.medical-display-core",
    )

    assert manifest.template_id == "roc_curve_binary"
    assert manifest.full_template_id == "fenggaolab.org.medical-display-core::roc_curve_binary"
    assert manifest.kind == "evidence_figure"
    assert manifest.display_class_id == "prediction_performance"
    assert manifest.audit_family == "Prediction Performance"
    assert manifest.paper_family_ids == ("A",)
    assert manifest.required_exports == ("png", "pdf")
    assert manifest.paper_proven is False


def test_load_display_template_manifest_rejects_unknown_audit_family(tmp_path: Path) -> None:
    template_path = tmp_path / "template.toml"
    template_path.write_text(
        "\n".join(
            (
                'template_id = "roc_curve_binary"',
                'full_template_id = "fenggaolab.org.medical-display-core::roc_curve_binary"',
                'kind = "evidence_figure"',
                'display_name = "ROC Curve (Binary Outcome)"',
                'paper_family_ids = ["A"]',
                'audit_family = "Unknown Family"',
                'renderer_family = "r_ggplot2"',
                'input_schema_ref = "binary_prediction_curve_inputs_v1"',
                'qc_profile_ref = "publication_evidence_curve"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "pkg.module:render"',
                "paper_proven = false",
            )
        )
        + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="audit_family"):
        load_display_template_manifest(
            template_path,
            expected_pack_id="fenggaolab.org.medical-display-core",
        )
