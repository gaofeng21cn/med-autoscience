from tests.display_surface_materialization_cases.shared import (
    annotations,
    _shared_base,
    _registry_id_helpers,
    _workspace_surface_fixtures,
    _layout_sidecar_fixtures,
    _illustration_payload_fixtures,
    _current_evidence_payload_fixtures,
    importlib,
    json,
    Path,
    re,
    sys,
    Any,
    plt,
    pytest,
    display_registry,
    get_template_short_id,
    full_id,
    dump_json,
    extract_svg_font_size,
    write_default_publication_display_contracts,
    restrict_display_registry_to_display_ids,
    build_display_surface_workspace,
    minimal_current_layout_sidecar,
    minimal_tail_layout_sidecar,
    _center_transportability_governance_display,
    _current_evidence_input_envelopes,
    _make_generalizability_subgroup_composite_panel_display,
)

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
path = "paper-external/display-packs/medical-display-core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    pack_root = paper_root / "paper-external" / "display-packs" / "medical-display-core"
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
    assert entry["source_path"] == "paper-external/display-packs/medical-display-core"

def test_materialize_display_surface_uses_catalog_ids_for_semantic_shell_display_ids(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _write_prepared_dependency_environment(paper_root)
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
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.png").exists()
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.pdf").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert table_catalog["tables"][0]["table_id"] == "T1"
