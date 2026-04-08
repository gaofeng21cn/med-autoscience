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
version = "0.1.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_paper_display_pack_config(paper_root: Path) -> None:
    (paper_root / "display_packs.toml").write_text(
        """
inherit_repo_defaults = true
enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "paper-display-packs/fenggaolab.org.medical-display-core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )


def _write_python_package_display_pack_config(repo_root: Path, *, package_name: str, version: str) -> None:
    config_dir = repo_root / "config"
    config_dir.mkdir(parents=True, exist_ok=True)
    (config_dir / "display_packs.toml").write_text(
        "\n".join(
            (
                'default_enabled_packs = ["fenggaolab.org.medical-display-core"]',
                "",
                "[[sources]]",
                'kind = "python_package"',
                'pack_id = "fenggaolab.org.medical-display-core"',
                f'package = "{package_name}"',
                f'version = "{version}"',
            )
        )
        + "\n",
        encoding="utf-8",
    )


def _write_demo_pack(
    root: Path,
    *,
    pack_dir: str,
    module_name: str,
    version: str,
    return_prefix: str,
) -> Path:
    pack_root = root / pack_dir
    (pack_root / "templates" / "time_to_event_risk_group_summary").mkdir(parents=True)
    (pack_root / "src" / module_name).mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                f'version = "{version}"',
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
                f'entrypoint = "{module_name}.renderers:render_template"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "src" / module_name / "__init__.py").write_text("", encoding="utf-8")
    (pack_root / "src" / module_name / "renderers.py").write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "def render_template(*, template_id: str, display_payload: dict[str, object], output_png_path: Path, output_pdf_path: Path, layout_sidecar_path: Path) -> str:",
                f'    return "{return_prefix}:" + template_id',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return pack_root


def _write_demo_python_package_pack(
    site_root: Path,
    *,
    package_name: str,
    version: str,
    return_prefix: str,
) -> Path:
    package_root = site_root / package_name
    (package_root / "templates" / "time_to_event_risk_group_summary").mkdir(parents=True)
    (package_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                f'version = "{version}"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "templates" / "time_to_event_risk_group_summary" / "template.toml").write_text(
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
                f'entrypoint = "{package_name}.renderers:render_template"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (package_root / "__init__.py").write_text("", encoding="utf-8")
    (package_root / "renderers.py").write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "def render_template(*, template_id: str, display_payload: dict[str, object], output_png_path: Path, output_pdf_path: Path, layout_sidecar_path: Path) -> str:",
                f'    return "{return_prefix}:" + template_id',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    return package_root


def test_resolve_display_template_runtime_keeps_pack_root_and_manifest(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    pack_root = _write_demo_pack(
        repo_root,
        pack_dir="display-packs/fenggaolab.org.medical-display-core",
        module_name="demo_display_core_repo",
        version="0.1.0",
        return_prefix="repo",
    )

    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )

    assert runtime.pack_root == pack_root
    assert runtime.template_manifest.entrypoint == "demo_display_core_repo.renderers:render_template"


def test_load_python_plugin_callable_imports_pack_local_src(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    _write_demo_pack(
        repo_root,
        pack_dir="display-packs/fenggaolab.org.medical-display-core",
        module_name="demo_display_core_repo",
        version="0.1.0",
        return_prefix="repo",
    )

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
        == "repo:fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
    )


def test_paper_root_override_changes_runtime_resolution(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    _write_display_pack_config(repo_root)
    repo_pack_root = _write_demo_pack(
        repo_root,
        pack_dir="display-packs/fenggaolab.org.medical-display-core",
        module_name="demo_display_core_repo",
        version="0.1.0",
        return_prefix="repo",
    )

    paper_root = tmp_path / "paper"
    paper_root.mkdir()
    _write_paper_display_pack_config(paper_root)
    paper_pack_root = _write_demo_pack(
        paper_root,
        pack_dir="paper-display-packs/fenggaolab.org.medical-display-core",
        module_name="demo_display_core_paper",
        version="0.2.0",
        return_prefix="paper",
    )

    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )
    target = load_python_plugin_callable(
        repo_root=repo_root,
        paper_root=paper_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )

    assert runtime.pack_root == paper_pack_root
    assert runtime.pack_root != repo_pack_root
    assert runtime.pack_manifest.version == "0.2.0"
    assert (
        target(
            template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
            display_payload={},
            output_png_path=Path("output.png"),
            output_pdf_path=Path("output.pdf"),
            layout_sidecar_path=Path("output.layout.json"),
        )
        == "paper:fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
    )


def test_load_python_plugin_callable_imports_python_package_source(
    tmp_path: Path,
    monkeypatch,
) -> None:
    repo_root = tmp_path / "repo"
    repo_root.mkdir()
    site_root = tmp_path / "site-packages"
    site_root.mkdir()
    package_name = "demo_display_core_pkg"
    _write_python_package_display_pack_config(repo_root, package_name=package_name, version="0.3.0")
    package_root = _write_demo_python_package_pack(
        site_root,
        package_name=package_name,
        version="0.3.0",
        return_prefix="pkg",
    )
    monkeypatch.syspath_prepend(str(site_root))

    runtime = resolve_display_template_runtime(
        repo_root=repo_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )
    target = load_python_plugin_callable(
        repo_root=repo_root,
        template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
    )

    assert runtime.pack_root == package_root
    assert runtime.pack_manifest.version == "0.3.0"
    assert (
        target(
            template_id="fenggaolab.org.medical-display-core::time_to_event_risk_group_summary",
            display_payload={},
            output_png_path=Path("output.png"),
            output_pdf_path=Path("output.pdf"),
            layout_sidecar_path=Path("output.layout.json"),
        )
        == "pkg:fenggaolab.org.medical-display-core::time_to_event_risk_group_summary"
    )
