from __future__ import annotations

import importlib
import json
from pathlib import Path
import runpy


def dump_json(path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_display_surface_workspace(tmp_path):
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
                    "shell_path": "paper/figures/Figure1.shell.json",
                },
                {
                    "display_id": "Table1",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "shell_path": "paper/tables/Table1.shell.json",
                },
            ],
        },
    )
    dump_json(
        paper_root / "figures" / "Figure1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Figure1",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
        },
    )
    dump_json(
        paper_root / "tables" / "Table1.shell.json",
        {
            "schema_version": 1,
            "display_id": "Table1",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort flow",
            "steps": [
                {"step_id": "screened", "label": "Patients screened", "n": 186, "detail": "Consecutive cases"},
                {"step_id": "included", "label": "Included in analysis", "n": 128, "detail": "Primary cohort"},
            ],
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "Table1",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "overall", "label": "Overall (n=128)"},
                {"group_id": "high_risk", "label": "High risk (n=55)"},
            ],
            "variables": [
                {
                    "variable_id": "age",
                    "label": "Age, median (IQR)",
                    "values": ["52 (44-61)", "58 (50-66)"],
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    return paper_root


def test_cli_materialize_display_surface_emits_result_json(tmp_path, capsys) -> None:
    module = importlib.import_module("med_autoscience.cli")
    paper_root = build_display_surface_workspace(tmp_path)

    exit_code = module.main(["materialize-display-surface", "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["status"] == "materialized"
    assert payload["figures_materialized"] == ["F1"]
    assert payload["tables_materialized"] == ["T1"]


def test_cli_materialize_display_surface_includes_registered_evidence_figures(tmp_path, monkeypatch, capsys) -> None:
    cli_module = importlib.import_module("med_autoscience.cli")
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    test_helpers = runpy.run_path(str(Path(__file__).with_name("test_display_surface_materialization.py")))
    paper_root = test_helpers["build_display_surface_workspace"](tmp_path, include_evidence=True)

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path,
        output_pdf_path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}:{display_payload['display_id']}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")

    monkeypatch.setattr(
        controller_module,
        "_render_r_evidence_figure",
        fake_render_r_evidence_figure,
        raising=False,
    )

    exit_code = cli_module.main(["materialize-display-surface", "--paper-root", str(paper_root)])

    captured = capsys.readouterr()
    payload = json.loads(captured.out)
    assert exit_code == 0
    assert payload["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "F6"]
    assert payload["tables_materialized"] == ["T1"]
