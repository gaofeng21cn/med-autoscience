from __future__ import annotations

from pathlib import Path

from med_autoscience.display_pack_runtime import (
    load_python_plugin_callable,
    resolve_display_template_runtime,
)


def _write_display_pack_config(repo_root: Path) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True)
    (config_dir / "display_packs.toml").write_text(
        """
default_enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "display-packs/fenggaolab.org.medical-display-core"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_demo_pack(repo_root: Path) -> Path:
    pack_root = repo_root / "display-packs" / "fenggaolab.org.medical-display-core"
    (pack_root / "templates" / "time_to_event_risk_group_summary").mkdir(parents=True)
    (pack_root / "src" / "demo_display_core").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.1.0"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "templates" / "time_to_event_risk_group_summary" / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "time_to_event_risk_group_summary"',
                'full_template_id = "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"',
                'kind = "evidence_figure"',
                'display_name = "Risk Group Summary"',
                'paper_family_ids = ["A", "B"]',
                'audit_family = "Clinical Utility"',
                'renderer_family = "python"',
                'input_schema_ref = "time_to_event_risk_group_summary_inputs_v1"',
                'qc_profile_ref = "publication_risk_group_summary"',
                'required_exports = ["png", "pdf"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "demo_display_core.renderers:render_template"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "src" / "demo_display_core" / "__init__.py").write_text("", encoding="utf-8")
    (pack_root / "src" / "demo_display_core" / "renderers.py").write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "def render_template(*, template_id: str, display_payload: dict[str, object], output_png_path: Path, output_pdf_path: Path, layout_sidecar_path: Path) -> str:",
                "    return template_id",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return pack_root


def test_resolve_display_template_runtime_keeps_pack_root_and_manifest(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    pack_root = _write_demo_pack(repo_root)

    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )

    assert runtime.pack_root == pack_root
    assert runtime.template_manifest.entrypoint == "demo_display_core.renderers:render_template"


def test_load_python_plugin_callable_imports_pack_local_src(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    _write_demo_pack(repo_root)

    target = load_python_plugin_callable(
        repo_root=repo_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )

    assert callable(target)
    assert (
        target(
            template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
            display_payload={},
            output_png_path=Path("output.png"),
            output_pdf_path=Path("output.pdf"),
            layout_sidecar_path=Path("output.layout.json"),
        )
        == "fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
    )
