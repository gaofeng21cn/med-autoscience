from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers.submission_minimal_parts.package_builder import create_submission_minimal_package
from med_autoscience.controllers.submission_package_layout import resolve_submission_manifest_path
from tests.test_submission_minimal_display_surface import dump_json, full_id, make_workspace, write_png, write_text


def test_create_submission_minimal_package_preserves_second_stage_display_entries(tmp_path: Path) -> None:
    paper_root = make_workspace(tmp_path)
    workspace_root = paper_root.parent

    write_png(paper_root / "figures" / "F14_validation.png")
    write_text(paper_root / "figures" / "F14_validation.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F17_generalizability.png")
    write_text(paper_root / "figures" / "F17_generalizability.pdf", "%PDF-1.4\n")
    write_text(
        paper_root / "tables" / "T2_performance.md",
        "| Metric | Development | External |\n| --- | --- | --- |\n| C-index | 0.81 | 0.77 |\n",
    )
    write_text(
        paper_root / "tables" / "T3_interpretation.md",
        "| Clinical Item | Observed signal | Interpretation |\n| --- | --- | --- |\n| High risk | Higher burden | Intensify follow-up |\n",
    )

    figure_catalog_path = paper_root / "figures" / "figure_catalog.json"
    figure_catalog = json.loads(figure_catalog_path.read_text(encoding="utf-8"))
    figure_catalog["figures"].extend(
        [
            {
                "figure_id": "F14",
                "template_id": "time_to_event_discrimination_calibration_panel",
                "renderer_family": "r_ggplot2",
                "paper_role": "main_text",
                "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
                "qc_profile": "publication_evidence_curve",
                "qc_result": {
                    "status": "pass",
                    "checked_at": "2026-04-03T10:00:00+00:00",
                    "engine_id": "display_layout_qc_v1",
                    "qc_profile": "publication_evidence_curve",
                    "layout_sidecar_path": "paper/figures/generated/F14.layout.json",
                    "issues": [],
                },
                "title": "Validation discrimination and calibration",
                "export_paths": ["paper/figures/F14_validation.pdf", "paper/figures/F14_validation.png"],
            },
            {
                "figure_id": "F17",
                "template_id": "generalizability_subgroup_composite_panel",
                "renderer_family": "r_ggplot2",
                "paper_role": "supplementary",
                "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
                "qc_profile": "publication_generalizability_subgroup_composite_panel",
                "qc_result": {
                    "status": "pass",
                    "checked_at": "2026-04-03T10:00:00+00:00",
                    "engine_id": "display_layout_qc_v1",
                    "qc_profile": "publication_generalizability_subgroup_composite_panel",
                    "layout_sidecar_path": "paper/figures/generated/F17.layout.json",
                    "issues": [],
                },
                "title": "Multicenter generalizability",
                "export_paths": ["paper/figures/F17_generalizability.pdf", "paper/figures/F17_generalizability.png"],
            },
        ]
    )
    dump_json(figure_catalog_path, figure_catalog)

    table_catalog_path = paper_root / "tables" / "table_catalog.json"
    table_catalog = json.loads(table_catalog_path.read_text(encoding="utf-8"))
    table_catalog["tables"].extend(
        [
            {
                "table_id": "T2",
                "table_shell_id": "table2_time_to_event_performance_summary",
                "paper_role": "main_text",
                "input_schema_id": "time_to_event_performance_summary_v1",
                "qc_profile": "publication_table_performance",
                "qc_result": {"status": "pass", "issues": []},
                "title": "Time-to-event performance summary",
                "asset_paths": ["paper/tables/T2_performance.md"],
            },
            {
                "table_id": "T3",
                "table_shell_id": "table3_clinical_interpretation_summary",
                "paper_role": "supplementary",
                "input_schema_id": "clinical_interpretation_summary_v1",
                "qc_profile": "publication_table_interpretation",
                "qc_result": {"status": "pass", "issues": []},
                "title": "Clinical interpretation summary",
                "asset_paths": ["paper/tables/T3_interpretation.md"],
            },
        ]
    )
    dump_json(table_catalog_path, table_catalog)

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    figures_by_id = {item["figure_id"]: item for item in manifest["figures"]}
    tables_by_id = {item["table_id"]: item for item in manifest["tables"]}

    assert set(figures_by_id) == {"F1", "F14", "F17"}
    assert figures_by_id["F14"]["template_id"] == full_id("time_to_event_discrimination_calibration_panel")
    assert figures_by_id["F14"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F14"]["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert figures_by_id["F17"]["template_id"] == full_id("generalizability_subgroup_composite_panel")
    assert figures_by_id["F17"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F17"]["qc_profile"] == "publication_generalizability_subgroup_composite_panel"
    assert len(figures_by_id["F14"]["output_paths"]) == 2
    assert all((workspace_root / output_path).exists() for output_path in figures_by_id["F14"]["output_paths"])
    assert all((workspace_root / output_path).exists() for output_path in figures_by_id["F17"]["output_paths"])

    assert set(tables_by_id) == {"T1", "T2", "T3"}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_time_to_event_performance_summary")
    assert tables_by_id["T2"]["qc_profile"] == "publication_table_performance"
    assert tables_by_id["T3"]["table_shell_id"] == full_id("table3_clinical_interpretation_summary")
    assert tables_by_id["T3"]["qc_profile"] == "publication_table_interpretation"
    assert tables_by_id["T2"]["output_paths"][0].endswith(".md")
    assert tables_by_id["T3"]["output_paths"][0].endswith(".md")
    assert (workspace_root / tables_by_id["T2"]["output_paths"][0]).exists()
    assert (workspace_root / tables_by_id["T3"]["output_paths"][0]).exists()


def test_create_submission_minimal_package_preserves_001_direct_migration_display_entries(tmp_path: Path) -> None:
    paper_root = make_workspace(tmp_path)
    workspace_root = paper_root.parent

    write_png(paper_root / "figures" / "F1_cohort_flow.png")
    write_text(paper_root / "figures" / "F1_cohort_flow.svg", "<svg><text>flow</text></svg>\n")
    write_png(paper_root / "figures" / "F2_validation.png")
    write_text(paper_root / "figures" / "F2_validation.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F3_risk_group_summary.png")
    write_text(paper_root / "figures" / "F3_risk_group_summary.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F4_dca.png")
    write_text(paper_root / "figures" / "F4_dca.pdf", "%PDF-1.4\n")
    write_png(paper_root / "figures" / "F5_generalizability.png")
    write_text(paper_root / "figures" / "F5_generalizability.pdf", "%PDF-1.4\n")
    write_text(
        paper_root / "tables" / "T2_performance.md",
        "| Metric | Development | External |\n| --- | --- | --- |\n| C-index | 0.81 | 0.77 |\n",
    )

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "F1",
                    "template_id": "cohort_flow_figure",
                    "renderer_family": "python",
                    "paper_role": "main_text",
                    "input_schema_id": "cohort_flow_shell_inputs_v1",
                    "qc_profile": "publication_illustration_flow",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Cohort derivation and endpoint inventory",
                    "export_paths": ["paper/figures/F1_cohort_flow.png", "paper/figures/F1_cohort_flow.svg"],
                },
                {
                    "figure_id": "F2",
                    "template_id": "time_to_event_discrimination_calibration_panel",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
                    "qc_profile": "publication_evidence_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_evidence_curve",
                        "layout_sidecar_path": "paper/figures/generated/F2.layout.json",
                        "issues": [],
                    },
                    "title": "Discrimination and grouped calibration",
                    "export_paths": ["paper/figures/F2_validation.pdf", "paper/figures/F2_validation.png"],
                },
                {
                    "figure_id": "F3",
                    "template_id": "time_to_event_risk_group_summary",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_grouped_inputs_v1",
                    "qc_profile": "publication_survival_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_survival_curve",
                        "layout_sidecar_path": "paper/figures/generated/F3.layout.json",
                        "issues": [],
                    },
                    "title": "Primary risk-group summary",
                    "export_paths": ["paper/figures/F3_risk_group_summary.pdf", "paper/figures/F3_risk_group_summary.png"],
                },
                {
                    "figure_id": "F4",
                    "template_id": "time_to_event_decision_curve",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_decision_curve_inputs_v1",
                    "qc_profile": "publication_decision_curve",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_decision_curve",
                        "layout_sidecar_path": "paper/figures/generated/F4.layout.json",
                        "issues": [],
                    },
                    "title": "Time-to-event decision curve",
                    "export_paths": ["paper/figures/F4_dca.pdf", "paper/figures/F4_dca.png"],
                },
                {
                    "figure_id": "F5",
                    "template_id": "generalizability_subgroup_composite_panel",
                    "renderer_family": "r_ggplot2",
                    "paper_role": "main_text",
                    "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
                    "qc_profile": "publication_generalizability_subgroup_composite_panel",
                    "qc_result": {
                        "status": "pass",
                        "checked_at": "2026-04-03T10:00:00+00:00",
                        "engine_id": "display_layout_qc_v1",
                        "qc_profile": "publication_generalizability_subgroup_composite_panel",
                        "layout_sidecar_path": "paper/figures/generated/F5.layout.json",
                        "issues": [],
                    },
                    "title": "Internal multicenter generalizability",
                    "export_paths": ["paper/figures/F5_generalizability.pdf", "paper/figures/F5_generalizability.png"],
                },
            ],
        },
    )
    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "table_shell_id": "table1_baseline_characteristics",
                    "paper_role": "main_text",
                    "input_schema_id": "baseline_characteristics_schema_v1",
                    "qc_profile": "publication_table_baseline",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Summary table",
                    "asset_paths": ["paper/tables/T1_summary.csv", "paper/tables/T1_summary.md"],
                },
                {
                    "table_id": "T2",
                    "table_shell_id": "table2_time_to_event_performance_summary",
                    "paper_role": "main_text",
                    "input_schema_id": "time_to_event_performance_summary_v1",
                    "qc_profile": "publication_table_performance",
                    "qc_result": {"status": "pass", "issues": []},
                    "title": "Time-to-event performance summary",
                    "asset_paths": ["paper/tables/T2_performance.md"],
                },
            ],
        },
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    figures_by_id = {item["figure_id"]: item for item in manifest["figures"]}
    tables_by_id = {item["table_id"]: item for item in manifest["tables"]}
    manifest_path = resolve_submission_manifest_path(paper_root / "submission_minimal")
    manifest_payload = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert set(figures_by_id) == {"F1", "F2", "F3", "F4", "F5"}
    assert figures_by_id["F1"]["template_id"] == full_id("cohort_flow_figure")
    assert figures_by_id["F1"]["renderer_family"] == "python"
    assert figures_by_id["F5"]["template_id"] == full_id("generalizability_subgroup_composite_panel")
    assert figures_by_id["F5"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F5"]["qc_profile"] == "publication_generalizability_subgroup_composite_panel"
    assert manifest_payload["naming_map"]["figures"]["F5"] == "Figure5"
    assert all((workspace_root / output_path).exists() for output_path in figures_by_id["F5"]["output_paths"])

    assert set(tables_by_id) == {"T1", "T2"}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_time_to_event_performance_summary")
    assert tables_by_id["T2"]["qc_profile"] == "publication_table_performance"
    assert manifest_payload["naming_map"]["tables"]["T2"] == "Table2"
    assert (workspace_root / tables_by_id["T2"]["output_paths"][0]).exists()


def test_create_submission_minimal_package_accepts_table_catalog_csv_and_markdown_paths(tmp_path: Path) -> None:
    paper_root = make_workspace(tmp_path)

    dump_json(
        paper_root / "tables" / "table_catalog.json",
        {
            "schema_version": 1,
            "tables": [
                {
                    "table_id": "T1",
                    "title": "Summary table",
                    "paper_role": "main_text",
                    "csv_path": str((paper_root / "tables" / "T1_summary.csv").resolve()),
                    "markdown_path": str((paper_root / "tables" / "T1_summary.md").resolve()),
                }
            ],
        },
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["tables"][0]["table_id"] == "T1"
    assert manifest["naming_map"]["tables"]["T1"] == "Table1"
    assert (paper_root / "submission_minimal" / "tables" / "Table1.csv").exists()
    assert (paper_root / "submission_minimal" / "tables" / "Table1.md").exists()


def test_create_submission_minimal_package_accepts_prefixed_catalog_ids_and_direct_paths(tmp_path: Path) -> None:
    paper_root = make_workspace(tmp_path)

    dump_json(
        paper_root / "figures" / "figure_catalog.json",
        {
            "schema_version": 1,
            "figures": [
                {
                    "figure_id": "Figure1",
                    "title": "Main figure",
                    "pdf_path": str((paper_root / "figures" / "F1_main.pdf").resolve()),
                    "png_path": str((paper_root / "figures" / "F1_main.png").resolve()),
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
                    "table_id": "Table1",
                    "title": "Summary table",
                    "paper_role": "main_text",
                    "csv_path": str((paper_root / "tables" / "T1_summary.csv").resolve()),
                    "markdown_path": str((paper_root / "tables" / "T1_summary.md").resolve()),
                }
            ],
        },
    )

    manifest = create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert manifest["naming_map"]["figures"]["Figure1"] == "Figure1"
    assert manifest["naming_map"]["tables"]["Table1"] == "Table1"
    assert (paper_root / "submission_minimal" / "figures" / "Figure1.pdf").exists()
    assert (paper_root / "submission_minimal" / "figures" / "Figure1.png").exists()
    assert (paper_root / "submission_minimal" / "tables" / "Table1.csv").exists()
    assert (paper_root / "submission_minimal" / "tables" / "Table1.md").exists()


def test_create_submission_minimal_package_resets_stale_generated_assets(tmp_path: Path) -> None:
    paper_root = make_workspace(tmp_path)

    stale_path = paper_root / "submission_minimal" / "tables" / "stale.txt"
    write_text(stale_path, "stale")

    create_submission_minimal_package(
        paper_root=paper_root,
        publication_profile="general_medical_journal",
    )

    assert not stale_path.exists()
