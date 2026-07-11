from __future__ import annotations

import importlib
import importlib.util
import json
import shutil
from pathlib import Path

import pytest


def _load_materialization_test_support():
    support_path = Path(__file__).with_name("test_display_surface_materialization.py")
    spec = importlib.util.spec_from_file_location("_display_surface_materialization_test_support", support_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_SUPPORT = _load_materialization_test_support()
build_display_surface_workspace = _SUPPORT.build_display_surface_workspace
dump_json = _SUPPORT.dump_json
get_template_short_id = _SUPPORT.get_template_short_id
write_default_publication_display_contracts = _SUPPORT.write_default_publication_display_contracts


def _build_abh_paper_proven_workspace(tmp_path: Path) -> Path:
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "time_dependent_roc",
                    "display_kind": "figure",
                    "requirement_key": "time_dependent_roc_horizon",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/time_dependent_roc.shell.json",
                },
                {
                    "display_id": "risk_layering",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/risk_layering.shell.json",
                },
                {
                    "display_id": "decision_curve",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/decision_curve.shell.json",
                },
                {
                    "display_id": "multicenter_generalizability",
                    "display_kind": "figure",
                    "requirement_key": "generalizability_subgroup_composite_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/multicenter_generalizability.shell.json",
                },
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
                    "display_id": "time_dependent_roc",
                    "template_id": "fenggaolab.org.medical-display-core::time_dependent_roc_horizon",
                    "title": "Five-year cardiovascular mortality discrimination",
                    "caption": "Fixed-horizon ROC curves summarize discrimination for the primary Cox model and comparator.",
                    "x_label": "1 - Specificity",
                    "y_label": "Sensitivity",
                    "time_horizon_months": 60,
                    "series": [
                        {"label": "CoxPH AUC 0.857", "x": [0, 0.08, 0.24, 1], "y": [0, 0.68, 0.88, 1]},
                        {"label": "LassoCox AUC 0.768", "x": [0, 0.16, 0.38, 1], "y": [0, 0.55, 0.80, 1]},
                    ],
                    "reference_line": {"label": "Chance", "x": [0, 1], "y": [0, 1]},
                }
            ],
        },
    )
    dump_json(
        paper_root / "risk_layering_monotonic_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "risk_layering_monotonic_inputs_v1",
            "displays": [
                {
                    "display_id": "risk_layering",
                    "template_id": "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars",
                    "title": "Tertile-based 5-year cardiovascular risk stratification",
                    "caption": "Predicted and observed 5-year cardiovascular risk across prespecified validation tertiles.",
                    "y_label": "5-year risk (%)",
                    "left_panel_title": "Predicted risk by tertile",
                    "left_x_label": "Predicted risk tertile",
                    "left_bars": [
                        {"label": "Low risk", "cases": 2437, "events": 5, "risk": 0.0022},
                        {"label": "Intermediate risk", "cases": 2437, "events": 11, "risk": 0.0047},
                        {"label": "High risk", "cases": 2437, "events": 26, "risk": 0.0105},
                    ],
                    "right_panel_title": "Observed risk by tertile",
                    "right_x_label": "Observed risk tertile",
                    "right_bars": [
                        {"label": "Low risk", "cases": 2437, "events": 0, "risk": 0.0},
                        {"label": "Intermediate risk", "cases": 2437, "events": 4, "risk": 0.0016},
                        {"label": "High risk", "cases": 2437, "events": 44, "risk": 0.0181},
                    ],
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_decision_curve_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_decision_curve_inputs_v1",
            "displays": [
                {
                    "display_id": "decision_curve",
                    "template_id": "fenggaolab.org.medical-display-core::time_to_event_decision_curve",
                    "title": "Five-year decision curve",
                    "caption": "Net benefit for the locked survival model across the prespecified threshold range.",
                    "panel_a_title": "Decision-curve net benefit",
                    "panel_b_title": "Model-treated fraction",
                    "x_label": "Threshold risk (%)",
                    "y_label": "Net benefit",
                    "treated_fraction_y_label": "Patients classified above threshold (%)",
                    "reference_line": {"x": [0.5, 4.0], "y": [0.0, 0.0], "label": "Treat none"},
                    "series": [
                        {"label": "Model", "x": [0.5, 1.0, 2.0, 4.0], "y": [0.004, 0.003, 0.001, 0.0]},
                        {"label": "Treat all", "x": [0.5, 1.0, 2.0, 4.0], "y": [0.002, -0.003, -0.014, -0.035]},
                    ],
                    "treated_fraction_series": {"label": "Model", "x": [0.5, 1.0, 2.0, 4.0], "y": [45.0, 28.0, 12.0, 2.0]},
                }
            ],
        },
    )
    dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "template_id": "fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel",
                    "catalog_id": "F4",
                    "paper_role": "main_text",
                    "title": "Internal multicenter heterogeneity summary",
                    "caption": "Center-level event support with coverage context under the frozen split.",
                    "metric_family": "effect_estimate",
                    "primary_label": "Center event fraction",
                    "overview_panel_title": "Center-level event support",
                    "overview_x_label": "Observed event fraction",
                    "overview_rows": [
                        {"cohort_id": "center_25", "cohort_label": "Center 25", "support_count": 110, "event_count": 3, "metric_value": 0.0273},
                        {"cohort_id": "center_01", "cohort_label": "Center 01", "support_count": 100, "event_count": 2, "metric_value": 0.0200},
                        {"cohort_id": "center_02", "cohort_label": "Center 02", "support_count": 120, "event_count": 1, "metric_value": 0.0083},
                    ],
                    "subgroup_panel_title": "Geodemographic support distribution",
                    "subgroup_x_label": "Cohort fraction",
                    "subgroup_reference_value": 0.3333,
                    "subgroup_rows": [
                        {"subgroup_id": "region_central", "subgroup_label": "Region: Central", "group_n": 72, "estimate": 0.48, "lower": 0.40, "upper": 0.56},
                        {"subgroup_id": "region_north", "subgroup_label": "Region: North", "group_n": 84, "estimate": 0.56, "lower": 0.48, "upper": 0.64},
                        {"subgroup_id": "urban", "subgroup_label": "Urban", "group_n": 101, "estimate": 0.67, "lower": 0.60, "upper": 0.74},
                    ],
                }
            ],
        },
    )
    dump_json(
        paper_root / "submission_graphical_abstract.json",
        {
            "schema_version": 1,
            "shell_id": "submission_graphical_abstract",
            "display_id": "submission_graphical_abstract",
            "catalog_id": "GA1",
            "paper_role": "submission_companion",
            "title": "Submission companion overview",
            "caption": "A programmatic graphical abstract aligned to the audited paper-facing surface.",
            "panels": [
                {
                    "panel_id": "cohort_split",
                    "panel_label": "A",
                    "title": "Cohort and split",
                    "subtitle": "Locked analysis cohort",
                    "rows": [{"cards": [{"card_id": "analytic", "title": "Analytic cohort", "value": "15,787", "detail": "Formal modeling cohort", "evidence_ref": "analysis:cohort_flow"}]}],
                },
                {
                    "panel_id": "primary_endpoint",
                    "panel_label": "B",
                    "title": "Primary endpoint",
                    "subtitle": "Cardiovascular mortality",
                    "rows": [{"cards": [{"card_id": "ridge", "title": "Validation C-index", "value": "0.857", "detail": "Primary five-year endpoint", "accent_role": "primary", "evidence_ref": "analysis:primary_model_performance"}]}],
                },
                {
                    "panel_id": "supportive_context",
                    "panel_label": "C",
                    "title": "Supportive context",
                    "subtitle": "Applicability boundary",
                    "rows": [
                        {
                            "cards": [
                                {"card_id": "internal_boundary", "title": "Applicability boundary", "value": "Internal validation only", "detail": "Multicenter support inside the current cohort", "accent_role": "contrast"},
                                {"card_id": "transportability_boundary", "title": "Transportability boundary", "value": "No external validation", "detail": "Do not expand beyond the audited cohort", "accent_role": "audit"},
                            ]
                        }
                    ],
                },
            ],
            "footer_pills": [
                {"pill_id": "p1", "panel_id": "cohort_split", "label": "Internal validation only", "style_role": "neutral"},
                {"pill_id": "p2", "panel_id": "primary_endpoint", "label": "Supportive endpoint retained", "style_role": "secondary"},
                {"pill_id": "p3", "panel_id": "supportive_context", "label": "No external validation", "style_role": "audit"},
            ],
        },
    )
    return paper_root


@pytest.fixture(scope="module")
def materialized_abh_paper_proven_fixture(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, dict[str, object]]:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = _build_abh_paper_proven_workspace(tmp_path_factory.mktemp("abh_paper_proven"))
    result = module.materialize_display_surface(paper_root=paper_root)
    assert result["status"] == "materialized"
    return paper_root, result


def _copy_materialized_abh_paper_proven_fixture(
    tmp_path: Path,
    fixture: tuple[Path, dict[str, object]],
) -> tuple[Path, dict[str, object]]:
    cached_paper_root, result = fixture
    paper_root = tmp_path / "paper"
    shutil.copytree(cached_paper_root, paper_root)
    return paper_root, dict(result)


def test_materialize_display_surface_preserves_current_ab_golden_regression_invariants(
    tmp_path: Path,
    materialized_abh_paper_proven_fixture: tuple[Path, dict[str, object]],
) -> None:
    paper_root, result = _copy_materialized_abh_paper_proven_fixture(
        tmp_path,
        materialized_abh_paper_proven_fixture,
    )

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "GA1"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}

    for figure_id in ("F1", "F2", "F3", "F4"):
        assert figures_by_id[figure_id]["qc_result"]["status"] == "pass"
        assert figures_by_id[figure_id]["qc_result"]["issues"] == []

    f1_layout = json.loads(
        (paper_root / "figures" / "generated" / "F1_time_dependent_roc_horizon.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert f1_layout["metrics"]["time_horizon_months"] == 60
    assert [item["label"] for item in f1_layout["metrics"]["series"]] == [
        "CoxPH AUC 0.857",
        "LassoCox AUC 0.768",
    ]
    assert any(item["box_type"] == "legend" for item in f1_layout["guide_boxes"])

    f2_layout = json.loads(
        (paper_root / "figures" / "generated" / "F2_risk_layering_monotonic_bars.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(f2_layout["panel_boxes"]) == 2
    predicted_risks = [item["risk"] for item in f2_layout["metrics"]["left_bars"]]
    observed_risks = [item["risk"] for item in f2_layout["metrics"]["right_bars"]]
    assert predicted_risks == sorted(predicted_risks)
    assert observed_risks == sorted(observed_risks)
    assert f2_layout["metrics"]["right_bars"][-1]["events"] - f2_layout["metrics"]["right_bars"][0]["events"] >= 1

    f3_layout = json.loads(
        (paper_root / "figures" / "generated" / "F3_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(f3_layout["panel_boxes"]) == 2
    assert f3_layout["metrics"]["reference_line"]["label"] == "Treat none"
    assert f3_layout["metrics"]["treated_fraction_series"]["label"] == "Model"


def test_materialize_display_surface_preserves_current_h_golden_regression_invariants(
    tmp_path: Path,
    materialized_abh_paper_proven_fixture: tuple[Path, dict[str, object]],
) -> None:
    paper_root, result = _copy_materialized_abh_paper_proven_fixture(
        tmp_path,
        materialized_abh_paper_proven_fixture,
    )

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F4"]["qc_result"]["status"] == "pass"
    assert figures_by_id["GA1"]["qc_result"]["status"] == "pass"

    f4_layout = json.loads(
        (
            paper_root
            / "figures"
            / "generated"
            / "F4_generalizability_subgroup_composite_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    f4_layout_boxes = {item["box_id"]: item for item in f4_layout["layout_boxes"]}
    f4_panel_boxes = {item["box_id"]: item for item in f4_layout["panel_boxes"]}
    assert figures_by_id["F4"]["template_id"].endswith("::generalizability_subgroup_composite_panel")
    assert figures_by_id["F4"]["renderer_family"] == "r_ggplot2"
    assert {"panel_label_A", "panel_label_B"} <= set(f4_layout_boxes)
    assert {"overview_panel", "subgroup_panel"} <= set(f4_panel_boxes)
    assert [item["cohort_label"] for item in f4_layout["metrics"]["overview_rows"]] == [
        "Center 25",
        "Center 01",
        "Center 02",
    ]
    assert [item["event_count"] for item in f4_layout["metrics"]["overview_rows"]] == [3, 2, 1]
    assert not any(item["box_type"] == "title" for item in f4_layout["layout_boxes"])

    ga_layout = json.loads(
        (paper_root / "figures" / "generated" / "GA1_graphical_abstract.layout.json").read_text(encoding="utf-8")
    )
    arrow_boxes = [item for item in ga_layout["guide_boxes"] if item["box_type"] == "arrow_connector"]
    assert len(arrow_boxes) == 2
    arrow_mid_ys = [((item["y0"] + item["y1"]) / 2.0) for item in arrow_boxes]
    assert max(arrow_mid_ys) - min(arrow_mid_ys) <= 0.03


def test_materialize_display_surface_preserves_ab_adjacent_grouped_and_time_slice_regression(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    registry_path = paper_root / "display_registry.json"
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    registry["displays"] = [
        item
        for item in registry["displays"]
        if item["display_id"] in {"Figure6", "Figure7", "Figure8"}
    ]
    dump_json(registry_path, registry)

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text(f"PNG:{template_id}", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        template_short_id = get_template_short_id(template_id) if "::" in template_id else template_id
        layout_boxes = [
            {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.62, "y1": 0.97},
            {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.01, "y0": 0.24, "x1": 0.05, "y1": 0.70},
        ]
        panel_boxes = [{"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86}]
        guide_boxes = [{"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44}]
        if template_short_id in {
            "roc_curve_binary",
            "pr_curve_binary",
            "calibration_curve_binary",
            "decision_curve_binary",
            "time_dependent_roc_horizon",
        }:
            metrics = {
                "series": list(display_payload["series"]),
                "reference_line": dict(display_payload["reference_line"]),
                "title": str(display_payload.get("title") or ""),
                "caption": str(display_payload.get("caption") or ""),
            }
        else:
            metrics = {
                "groups": list(display_payload["groups"]),
                "annotation": str(display_payload.get("annotation") or ""),
            }
        layout_sidecar_path.write_text(
            json.dumps(
                {
                    "template_id": template_id,
                    "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
                    "layout_boxes": layout_boxes,
                    "panel_boxes": panel_boxes,
                    "guide_boxes": guide_boxes,
                    "metrics": metrics,
                    "render_context": dict(display_payload.get("render_context") or {}),
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(module, "_render_r_evidence_figure", fake_render_r_evidence_figure, raising=False)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F6", "F7", "F8"]

    f6_layout = json.loads((paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.layout.json").read_text(encoding="utf-8"))
    f7_layout = json.loads((paper_root / "figures" / "generated" / "F7_cumulative_incidence_grouped.layout.json").read_text(encoding="utf-8"))
    f8_layout = json.loads((paper_root / "figures" / "generated" / "F8_time_dependent_roc_horizon.layout.json").read_text(encoding="utf-8"))

    f6_terminal_values = [group["values"][-1] for group in f6_layout["metrics"]["groups"]]
    f7_terminal_values = [group["values"][-1] for group in f7_layout["metrics"]["groups"]]
    assert max(f6_terminal_values) - min(f6_terminal_values) >= 0.01
    assert max(f7_terminal_values) - min(f7_terminal_values) >= 0.01
    assert f6_layout["metrics"]["annotation"] == "Log-rank P < .001"
    assert f7_layout["metrics"]["annotation"] == "Gray test P = .002"

    assert f8_layout["metrics"]["title"] == "Time-dependent ROC at 24 months"
    assert f8_layout["metrics"]["caption"] == (
        "Horizon-specific discrimination of the locked survival model."
    )
    assert f8_layout["metrics"]["series"][0]["label"] == "24-month horizon"
    assert f8_layout["metrics"]["series"][0]["annotation"] == "AUC = 0.81"
    assert f8_layout["metrics"]["reference_line"]["label"] == "Chance"
