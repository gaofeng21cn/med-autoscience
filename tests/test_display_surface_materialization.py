from __future__ import annotations

import importlib
import json
from pathlib import Path


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_display_surface_workspace(tmp_path: Path, *, include_evidence: bool = False) -> Path:
    paper_root = tmp_path / "paper"
    displays = [
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
    ]
    if include_evidence:
        displays.extend(
            [
                {
                    "display_id": "Figure2",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "shell_path": "paper/figures/Figure2.shell.json",
                },
                {
                    "display_id": "Figure3",
                    "display_kind": "figure",
                    "requirement_key": "pr_curve_binary",
                    "shell_path": "paper/figures/Figure3.shell.json",
                },
                {
                    "display_id": "Figure4",
                    "display_kind": "figure",
                    "requirement_key": "calibration_curve_binary",
                    "shell_path": "paper/figures/Figure4.shell.json",
                },
                {
                    "display_id": "Figure5",
                    "display_kind": "figure",
                    "requirement_key": "decision_curve_binary",
                    "shell_path": "paper/figures/Figure5.shell.json",
                },
                {
                    "display_id": "Figure6",
                    "display_kind": "figure",
                    "requirement_key": "kaplan_meier_grouped",
                    "shell_path": "paper/figures/Figure6.shell.json",
                },
            ]
        )
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": displays,
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
    if include_evidence:
        for figure_index, template_id in (
            (2, "roc_curve_binary"),
            (3, "pr_curve_binary"),
            (4, "calibration_curve_binary"),
            (5, "decision_curve_binary"),
            (6, "kaplan_meier_grouped"),
        ):
            dump_json(
                paper_root / "figures" / f"Figure{figure_index}.shell.json",
                {
                    "schema_version": 1,
                    "display_id": f"Figure{figure_index}",
                    "display_kind": "figure",
                    "requirement_key": template_id,
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
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                    "detail": "Consecutive surgical cases",
                },
                {
                    "step_id": "eligible",
                    "label": "Eligible after criteria review",
                    "n": 142,
                    "detail": "Complete preoperative variables",
                },
                {
                    "step_id": "included",
                    "label": "Included in analysis",
                    "n": 128,
                    "detail": "Primary cohort",
                },
            ],
        },
    )
    if include_evidence:
        dump_json(
            paper_root / "binary_prediction_curve_inputs.json",
            {
                "schema_version": 1,
                "input_schema_id": "binary_prediction_curve_inputs_v1",
                "displays": [
                    {
                        "display_id": "Figure2",
                        "template_id": "roc_curve_binary",
                        "title": "ROC curve for the primary model",
                        "caption": "Discrimination of the primary model across thresholds.",
                        "x_label": "1 - Specificity",
                        "y_label": "Sensitivity",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.0, 0.08, 0.24, 1.0],
                                "y": [0.0, 0.66, 0.87, 1.0],
                                "annotation": "AUC = 0.84",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure3",
                        "template_id": "pr_curve_binary",
                        "title": "Precision-recall curve for the primary model",
                        "caption": "Positive predictive yield across recall levels.",
                        "x_label": "Recall",
                        "y_label": "Precision",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.42, 0.42], "label": "Prevalence"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.0, 0.25, 0.55, 1.0],
                                "y": [1.0, 0.82, 0.69, 0.42],
                                "annotation": "AP = 0.73",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure4",
                        "template_id": "calibration_curve_binary",
                        "title": "Calibration curve for the primary model",
                        "caption": "Observed versus predicted risk across bins.",
                        "x_label": "Predicted probability",
                        "y_label": "Observed event rate",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Ideal"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.05, 0.20, 0.40, 0.70, 0.90],
                                "y": [0.08, 0.22, 0.36, 0.68, 0.88],
                                "annotation": "Slope = 0.97",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure5",
                        "template_id": "decision_curve_binary",
                        "title": "Decision curve for the primary model",
                        "caption": "Net benefit across clinically relevant thresholds.",
                        "x_label": "Threshold probability",
                        "y_label": "Net benefit",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 0.0], "label": "Treat none"},
                        "series": [
                            {
                                "label": "Primary model",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40],
                                "y": [0.18, 0.17, 0.14, 0.10, 0.07],
                                "annotation": "Model",
                            },
                            {
                                "label": "Treat all",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40],
                                "y": [0.16, 0.13, 0.08, 0.03, -0.02],
                                "annotation": "Treat all",
                            },
                        ],
                    },
                ],
            },
        )
        dump_json(
            paper_root / "time_to_event_grouped_inputs.json",
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "displays": [
                    {
                        "display_id": "Figure6",
                        "template_id": "kaplan_meier_grouped",
                        "title": "Kaplan-Meier risk stratification",
                        "caption": "Time-to-event separation across prespecified risk groups.",
                        "x_label": "Months from surgery",
                        "y_label": "Survival probability",
                        "groups": [
                            {
                                "label": "Low risk",
                                "times": [0, 6, 12, 18, 24],
                                "values": [1.0, 0.96, 0.93, 0.90, 0.88],
                            },
                            {
                                "label": "High risk",
                                "times": [0, 6, 12, 18, 24],
                                "values": [1.0, 0.88, 0.77, 0.69, 0.62],
                            },
                        ],
                        "annotation": "Log-rank P < .001",
                    }
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
                {"group_id": "low_risk", "label": "Low risk (n=73)"},
                {"group_id": "high_risk", "label": "High risk (n=55)"},
            ],
            "variables": [
                {
                    "variable_id": "age",
                    "label": "Age, median (IQR)",
                    "values": ["52 (44-61)", "49 (42-56)", "58 (50-66)"],
                },
                {
                    "variable_id": "female",
                    "label": "Female sex, n (%)",
                    "values": ["71 (55.5)", "45 (61.6)", "26 (47.3)"],
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    return paper_root


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
    assert figure_catalog["figures"][0]["template_id"] == "cohort_flow_figure"
    assert figure_catalog["figures"][0]["renderer_family"] == "python"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert table_catalog["tables"][0]["table_shell_id"] == "table1_baseline_characteristics"
    assert table_catalog["tables"][0]["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_registered_evidence_figures(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)
    render_calls: list[dict[str, str]] = []

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        render_calls.append(
            {
                "template_id": template_id,
                "display_id": str(display_payload.get("display_id") or ""),
            }
        )

    monkeypatch.setattr(module, "_render_r_evidence_figure", fake_render_r_evidence_figure, raising=False)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "F6"]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.pdf").exists()
    assert {item["template_id"] for item in render_calls} == {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "kaplan_meier_grouped",
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == "roc_curve_binary"
    assert figures_by_id["F2"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F2"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F5"]["qc_profile"] == "publication_evidence_curve"
    assert figures_by_id["F6"]["template_id"] == "kaplan_meier_grouped"
    assert figures_by_id["F6"]["input_schema_id"] == "time_to_event_grouped_inputs_v1"


def test_materialize_display_surface_rejects_incomplete_cohort_flow_input(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "steps": [],
        },
    )

    try:
        module.materialize_display_surface(paper_root=paper_root)
    except ValueError as exc:
        assert "cohort_flow.json" in str(exc)
    else:
        raise AssertionError("expected incomplete cohort flow input to fail")
