from .shared import *

def test_normalize_figure_catalog_id_accepts_supplementary_short_form() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")

    assert module._normalize_figure_catalog_id("S1") == "S1"
    assert module._normalize_figure_catalog_id("FS1") == "S1"
    assert module._normalize_figure_catalog_id("SupplementaryFigureS1") == "S1"

def test_materialize_display_surface_generates_official_shell_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.csv").exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert figure_catalog["figures"][0]["template_id"] == full_id("cohort_flow_figure")
    assert figure_catalog["figures"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figure_catalog["figures"][0]["renderer_family"] == "python"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert table_catalog["tables"][0]["table_shell_id"] == full_id("table1_baseline_characteristics")
    assert table_catalog["tables"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert table_catalog["tables"][0]["qc_result"]["status"] == "pass"

def test_materialize_display_surface_replaces_legacy_catalog_entries_with_matching_catalog_id(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "catalog_id": "F1",
                    "display_id": "cohort_flow",
                    "title": "Legacy cohort flow entry",
                    "png_path": "paper/figures/F1_cohort_flow.png",
                    "json_path": "paper/cohort_flow.json",
                }
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "catalog_id": "T1",
                    "display_id": "baseline_characteristics",
                    "title": "Legacy baseline table entry",
                    "markdown_path": "paper/tables/T1_baseline_characteristics.md",
                    "json_path": "paper/baseline_characteristics_schema.json",
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert len(figure_catalog["figures"]) == 1
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert all("figure_id" in item for item in figure_catalog["figures"])
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert len(table_catalog["tables"]) == 1
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert all("table_id" in item for item in table_catalog["tables"])

def test_materialize_display_surface_materializes_catalog_only_cohort_flow_figure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    display_registry_payload = json.loads((paper_root / "display_registry.json").read_text(encoding="utf-8"))
    display_registry_payload["displays"] = [
        item
        for item in display_registry_payload["displays"]
        if item.get("display_id") != "Figure1" and item.get("requirement_key") != "cohort_flow_figure"
    ]
    dump_json(paper_root / "display_registry.json", display_registry_payload)

    cohort_flow_payload = json.loads((paper_root / "cohort_flow.json").read_text(encoding="utf-8"))
    cohort_flow_payload["display_id"] = "cohort_flow"
    dump_json(paper_root / "cohort_flow.json", cohort_flow_payload)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "S1",
                    "display_id": "cohort_flow",
                    "template_id": full_id("cohort_flow_figure"),
                    "renderer_family": "python",
                    "input_schema_id": "cohort_flow_shell_inputs_v1",
                    "title": "Legacy cohort flow entry",
                    "export_paths": [
                        "paper/figures/generated/F1_cohort_flow.svg",
                        "paper/figures/generated/F1_cohort_flow.png",
                    ],
                    "source_paths": ["paper/cohort_flow.json"],
                }
            ],
        },
    )

    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
        output_pdf_path: Path | None = None,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        if output_pdf_path is not None:
            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("cohort_flow_figure"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_cohort_flow_figure",
        lambda **_: (_ for _ in ()).throw(AssertionError("host cohort-flow renderer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["S1"]
    assert render_calls == [full_id("cohort_flow_figure")]
    assert (paper_root / "figures" / "generated" / "S1_cohort_flow.svg").exists()
    assert (paper_root / "figures" / "generated" / "S1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "S1_cohort_flow.pdf").exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert len(figure_catalog["figures"]) == 1
    assert figure_catalog["figures"][0]["figure_id"] == "S1"
    assert figure_catalog["figures"][0]["template_id"] == full_id("cohort_flow_figure")
    assert figure_catalog["figures"][0]["input_schema_id"] == "cohort_flow_shell_inputs_v1"
    assert figure_catalog["figures"][0]["export_paths"] == [
        "paper/figures/generated/S1_cohort_flow.svg",
        "paper/figures/generated/S1_cohort_flow.png",
        "paper/figures/generated/S1_cohort_flow.pdf",
    ]

def test_materialize_display_surface_uses_pack_runtime_for_cohort_flow_shell(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
        output_pdf_path: Path | None = None,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        if output_pdf_path is not None:
            output_pdf_path.parent.mkdir(parents=True, exist_ok=True)
            output_pdf_path.write_text("%PDF-1.4\n", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("cohort_flow_figure"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_cohort_flow_figure",
        lambda **_: (_ for _ in ()).throw(AssertionError("host cohort-flow renderer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("cohort_flow_figure")]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()

def test_materialize_display_surface_uses_pack_runtime_for_r_evidence_template(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "binary_prediction_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "binary_prediction_curve_inputs_v1",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "template_id": "roc_curve_binary",
                    "title": "ROC curve",
                    "caption": "Receiver operating characteristic curve.",
                    "x_label": "1 - Specificity",
                    "y_label": "Sensitivity",
                    "series": [
                        {
                            "label": "Model",
                            "x": [0.0, 0.2, 1.0],
                            "y": [0.0, 0.8, 1.0],
                        }
                    ],
                }
            ],
        },
    )
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_evidence_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("roc_curve_binary"):
            return fake_evidence_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_r_evidence_figure",
        lambda **_: (_ for _ in ()).throw(AssertionError("host R evidence renderer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("roc_curve_binary")]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()

def test_materialize_display_surface_writes_display_pack_lock(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    module.materialize_display_surface(paper_root=paper_root)

    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    assert lock_payload["schema_version"] == 2
    assert lock_payload["paper_config_present"] is False
    assert lock_payload["enabled_pack_ids"] == ["fenggaolab.org.medical-display-core"]
    assert lock_payload["enabled_packs"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert lock_payload["enabled_packs"][0]["requested_version"] == "0.1.0"
    assert lock_payload["enabled_packs"][0]["declared_in"] == "repo"

def test_materialize_display_surface_uses_paper_pack_override_and_writes_versioned_lock(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "shell_path": "paper/tables/baseline_characteristics.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "tables" / "baseline_characteristics.shell.json",
        {
            "schema_version": 1,
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "all", "label": "All patients"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, y", "values": ["61 (54-68)"]},
            ],
        },
    )

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

    pack_root = paper_root / "paper-display-packs" / "fenggaolab.org.medical-display-core"
    (pack_root / "templates" / "table1_baseline_characteristics").mkdir(parents=True)
    (pack_root / "src" / "paper_override_display_core").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.2.0"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "Paper-local override pack"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "templates" / "table1_baseline_characteristics" / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "table1_baseline_characteristics"',
                'full_template_id = "fenggaolab.org.medical-display-core::table1_baseline_characteristics"',
                'kind = "table_shell"',
                'display_name = "Baseline characteristics"',
                'paper_family_ids = ["H"]',
                'audit_family = "Publication Shells and Tables"',
                'renderer_family = "n/a"',
                'input_schema_ref = "table1_baseline_characteristics_inputs_v1"',
                'qc_profile_ref = "publication_table_shell"',
                'required_exports = ["md", "csv"]',
                'allowed_paper_roles = ["main_text", "supplementary"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "paper_override_display_core.table_shells:render_table_shell"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "src" / "paper_override_display_core" / "__init__.py").write_text("", encoding="utf-8")
    (pack_root / "src" / "paper_override_display_core" / "table_shells.py").write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "def render_table_shell(*, template_id: str, payload_path: Path, payload: dict[str, object], output_md_path: Path, output_csv_path: Path | None = None) -> dict[str, str]:",
                "    output_md_path.parent.mkdir(parents=True, exist_ok=True)",
                '    output_md_path.write_text("# Paper override baseline characteristics\\n\\n| Characteristic | Overall |\\n| --- | --- |\\n| Age | 60 |\\n", encoding="utf-8")',
                "    if output_csv_path is not None:",
                '        output_csv_path.write_text("Characteristic,Overall\\nAge,60\\n", encoding="utf-8")',
                '    return {"title": "Paper override baseline characteristics", "caption": "Paper-local override version."}',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "Paper override baseline characteristics" in (
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md"
    ).read_text(encoding="utf-8")

    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    entry = lock_payload["enabled_packs"][0]
    assert lock_payload["paper_config_present"] is True
    assert entry["declared_in"] == "paper"
    assert entry["requested_version"] == "0.2.0"
    assert entry["version"] == "0.2.0"
    assert entry["source_path"] == "paper-display-packs/fenggaolab.org.medical-display-core"

def test_materialize_display_surface_uses_catalog_ids_for_semantic_shell_display_ids(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                },
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "shell_path": "paper/tables/baseline_characteristics.shell.json",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
    )
    dump_json(
        paper_root / "tables" / "baseline_characteristics.shell.json",
        {
            "schema_version": 1,
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                }
            ],
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "all", "label": "All patients"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, y", "values": ["61 (54-68)"]},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    assert result["tables_materialized"] == ["T1"]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert table_catalog["tables"][0]["table_id"] == "T1"

def test_materialize_display_surface_defaults_study_setup_shells_to_supplementary(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "S1",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "S1",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["S1"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "S1"
    assert figure_catalog["figures"][0]["paper_role"] == "supplementary"

def test_materialize_display_surface_renders_cohort_flow_with_exclusions_and_design_panels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure1",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/Figure1.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Unified study cohort and design shell",
            "steps": [
                {"step_id": "source", "label": "Source records", "n": 409, "detail": "Institutional cohort"},
                {"step_id": "first_surgery", "label": "First-surgery cases", "n": 357},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 357, "detail": "Observed endpoint available"},
            ],
            "exclusions": [
                {
                    "exclusion_id": "repeat_or_salvage",
                    "from_step_id": "source",
                    "label": "Repeat or salvage surgery excluded",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery cohort",
                }
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "main_endpoint",
                    "label": "Early residual / non-GTR",
                    "event_n": 57,
                    "detail": "57 non-GTR vs 300 GTR",
                }
            ],
            "design_panels": [
                {
                    "panel_id": "validation_framework",
                    "title": "Validation framework",
                    "layout_role": "top_right",
                    "lines": [
                        {"label": "Repeated nested validation", "detail": "5 outer folds x 20 repeats; 4-fold inner tuning"}
                    ],
                },
                {
                    "panel_id": "model_hierarchy",
                    "title": "Model hierarchy",
                    "layout_role": "wide_left",
                    "lines": [
                        {"label": "Core preoperative model", "detail": "Confirmed comparator"},
                        {"label": "Clinical utility model", "detail": "Knowledge-guided primary model"},
                    ],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar_path = paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json"
    assert layout_sidecar_path.exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["engine_id"] == "display_layout_qc_v1"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")

def test_materialize_display_surface_renders_exclusion_aware_cohort_flow_shell(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation, exclusions, and study design",
            "caption": "Cohort derivation with explicit exclusion accounting.",
            "steps": [
                {"step_id": "source_total", "label": "Source study records", "n": 409, "detail": "Institutional cleaned cohort"},
                {"step_id": "first_surgery", "label": "First-surgery NF-PitNET cases", "n": 357, "detail": "Primary cohort"},
                {"step_id": "analysis", "label": "Analyzed cohort", "n": 357, "detail": "Observed resection status"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source_total",
                    "label": "Repeat or salvage surgery",
                    "n": 52,
                    "detail": "Excluded before first-surgery cohort lock",
                }
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "non_gtr",
                    "label": "Early residual / non-GTR",
                    "n": 57,
                    "detail": "Primary endpoint",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation_frame",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [
                        {"label": "Repeated nested validation", "detail": "5-fold outer x 20 repeats; 4-fold inner tuning"}
                    ],
                },
                {
                    "block_id": "primary_model",
                    "block_type": "left_bottom",
                    "title": "Primary model",
                    "items": [{"label": "Clinically informed preoperative model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "comparator_model",
                    "block_type": "right_bottom",
                    "title": "Comparator",
                    "items": [{"label": "Preoperative core model", "detail": "Confirmed comparator"}],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    svg_text = (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").read_text(encoding="utf-8")
    assert "Cohort derivation, exclusions, and study design" not in svg_text
    assert "Repeat or" in svg_text
    assert "salvage" in svg_text
    assert "Endpoint inventory" in svg_text
    assert "Validation framework" in svg_text
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["qc_profile"] == "publication_illustration_flow"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")

def test_materialize_display_surface_accepts_legacy_full_right_sidecar_role(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation and split schema",
            "steps": [
                {"step_id": "source_total", "label": "Source study records", "n": 409, "detail": "Institutional cleaned cohort"},
                {"step_id": "analysis", "label": "Analyzed cohort", "n": 357, "detail": "Observed resection status"},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "non_gtr",
                    "label": "Early residual / non-GTR",
                    "n": 57,
                    "detail": "Primary endpoint",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "split_schema",
                    "block_type": "full_right",
                    "title": "Center-based split schema",
                    "items": [
                        {"label": "Derivation centers", "detail": "n=200"},
                        {"label": "Validation centers", "detail": "n=157"},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8")
    )
    panel_roles = {item["layout_role"] for item in layout_sidecar["metrics"]["design_panels"]}
    assert "wide_top" in panel_roles
    assert "full_right" not in panel_roles

def test_materialize_display_surface_renders_cohort_flow_with_two_subfigure_panels_and_role_aware_grid(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly and analytic design",
            "caption": "Study flow with explicit analytic design hierarchy.",
            "steps": [
                {"step_id": "screened", "label": "Screened records", "n": 409, "detail": "Source population"},
                {"step_id": "included", "label": "Included cohort", "n": 357, "detail": "Primary surgery cases"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Removed before first-surgery cohort lock",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "5-fold outer repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Comparator", "detail": "Confirmed preoperative baseline"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical utility", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology audit", "detail": "Bounded postoperative audit"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Benchmark ceilings", "detail": "Context only"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
    guide_boxes = {item["box_id"]: item for item in layout["guide_boxes"]}

    assert "subfigure_panel_A" in panel_boxes
    assert "subfigure_panel_B" in panel_boxes
    assert "title" not in layout_boxes
    assert "panel_label_A" in layout_boxes
    assert "panel_label_B" in layout_boxes
    assert panel_boxes["secondary_panel_validation"]["x0"] <= panel_boxes["secondary_panel_core"]["x0"]
    assert panel_boxes["secondary_panel_validation"]["x1"] >= panel_boxes["secondary_panel_primary"]["x1"]
    assert panel_boxes["secondary_panel_core"]["x1"] < panel_boxes["secondary_panel_primary"]["x0"]
    assert panel_boxes["secondary_panel_audit"]["x1"] < panel_boxes["secondary_panel_context"]["x0"]
    assert panel_boxes["secondary_panel_core"]["y0"] > panel_boxes["secondary_panel_audit"]["y1"]
    assert "hierarchy_root_trunk" in guide_boxes
    assert "hierarchy_root_branch" in guide_boxes
    assert "hierarchy_connector_left_middle_to_left_bottom" in guide_boxes
    assert "hierarchy_connector_right_middle_to_right_bottom" in guide_boxes
