from __future__ import annotations

import importlib
import importlib.util
import json
from pathlib import Path


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
                    "display_id": "binary_calibration_decision",
                    "display_kind": "figure",
                    "requirement_key": "binary_calibration_decision_curve_panel",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/binary_calibration_decision.shell.json",
                },
                {
                    "display_id": "discrimination_calibration",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/discrimination_calibration.shell.json",
                },
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/km_risk_stratification.shell.json",
                },
                {
                    "display_id": "decision_curve",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/decision_curve.shell.json",
                },
                {
                    "display_id": "multicenter_generalizability",
                    "display_kind": "figure",
                    "requirement_key": "multicenter_generalizability_overview",
                    "catalog_id": "F5",
                    "shell_path": "paper/figures/multicenter_generalizability.shell.json",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)

    dump_json(
        paper_root / "binary_calibration_decision_curve_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "binary_calibration_decision_curve_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "binary_calibration_decision",
                    "template_id": "binary_calibration_decision_curve_panel",
                    "title": "Clinical coherence and coefficient stability of the clinically informed preoperative model",
                    "caption": "Calibration and decision-curve evidence across candidate packages.",
                    "calibration_x_label": "Mean predicted probability",
                    "calibration_y_label": "Observed probability",
                    "decision_x_label": "Threshold probability",
                    "decision_y_label": "Net benefit",
                    "calibration_axis_window": {"xmin": 0.0, "xmax": 0.65, "ymin": 0.0, "ymax": 0.65},
                    "calibration_reference_line": {"label": "Ideal", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    "calibration_series": [
                        {
                            "label": "Core preoperative model",
                            "x": [0.02, 0.10, 0.22, 0.41, 0.55],
                            "y": [0.01, 0.06, 0.14, 0.31, 0.50],
                        },
                        {
                            "label": "Clinically informed preoperative model",
                            "x": [0.01, 0.08, 0.18, 0.39, 0.54],
                            "y": [0.03, 0.05, 0.20, 0.43, 0.53],
                        },
                    ],
                    "decision_series": [
                        {
                            "label": "Core preoperative model",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.01, 0.0, -0.01, -0.005, -0.002],
                        },
                        {
                            "label": "Clinically informed preoperative model",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.06, 0.05, 0.04, 0.03, 0.02],
                        },
                    ],
                    "decision_reference_lines": [
                        {"label": "Treat none", "x": [0.15, 0.20, 0.25, 0.30, 0.35], "y": [0.0, 0.0, 0.0, 0.0, 0.0]},
                        {"label": "Treat all", "x": [0.15, 0.20, 0.25, 0.30, 0.35], "y": [0.01, -0.03, -0.08, -0.14, -0.22]},
                    ],
                    "decision_focus_window": {"xmin": 0.15, "xmax": 0.35},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_discrimination_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_discrimination_calibration_inputs_v1",
            "displays": [
                {
                    "display_id": "discrimination_calibration",
                    "template_id": "time_to_event_discrimination_calibration_panel",
                    "title": "Validation discrimination and grouped calibration for 5-year cardiovascular mortality",
                    "caption": "Validation discrimination remained strong, and grouped calibration showed underprediction in the highest-risk decile.",
                    "panel_a_title": "Validation discrimination",
                    "panel_b_title": "Grouped 5-year calibration",
                    "discrimination_x_label": "Validation C-index",
                    "calibration_x_label": "Risk decile",
                    "calibration_y_label": "5-year risk (%)",
                    "discrimination_points": [
                        {"label": "CoxPH", "c_index": 0.857306, "annotation": "0.857"},
                        {"label": "LassoCox", "c_index": 0.849734, "annotation": "0.850"},
                    ],
                    "calibration_summary": [
                        {"group_label": "Decile 1", "group_order": 1, "n": 732, "events_5y": 0, "predicted_risk_5y": 0.0013, "observed_risk_5y": 0.0},
                        {"group_label": "Decile 10", "group_order": 10, "n": 731, "events_5y": 26, "predicted_risk_5y": 0.0159, "observed_risk_5y": 0.0356},
                    ],
                    "calibration_callout": {
                        "group_label": "Decile 10",
                        "predicted_risk_5y": 0.0159,
                        "observed_risk_5y": 0.0356,
                        "events_5y": 26,
                        "n": 731,
                    },
                }
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
                    "display_id": "km_risk_stratification",
                    "template_id": "time_to_event_risk_group_summary",
                    "title": "Tertile-based 5-year cardiovascular risk stratification",
                    "caption": "Predicted versus observed 5-year cardiovascular risk and observed event concentration across prespecified validation tertiles.",
                    "panel_a_title": "Predicted and observed risk by tertile",
                    "panel_b_title": "Event concentration across tertiles",
                    "x_label": "Risk tertile",
                    "y_label": "5-year risk (%)",
                    "event_count_y_label": "Observed 5-year events",
                    "risk_group_summaries": [
                        {"label": "Low risk", "sample_size": 2437, "events_5y": 0, "mean_predicted_risk_5y": 0.0022, "observed_km_risk_5y": 0.0},
                        {"label": "Intermediate risk", "sample_size": 2437, "events_5y": 4, "mean_predicted_risk_5y": 0.0047, "observed_km_risk_5y": 0.0016},
                        {"label": "High risk", "sample_size": 2437, "events_5y": 44, "mean_predicted_risk_5y": 0.0105, "observed_km_risk_5y": 0.0181},
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
                    "template_id": "time_to_event_decision_curve",
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
        paper_root / "multicenter_generalizability_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "multicenter_generalizability_inputs_v1",
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "template_id": "multicenter_generalizability_overview",
                    "catalog_id": "F5",
                    "paper_role": "main_text",
                    "title": "Internal multicenter heterogeneity summary",
                    "caption": "Center-level event support with coverage context under the frozen split.",
                    "overview_mode": "center_support_counts",
                    "center_event_y_label": "5-year CVD events",
                    "coverage_y_label": "Patient count",
                    "center_event_counts": [
                        {"center_label": "Center 01", "split_bucket": "validation", "event_count": 2},
                        {"center_label": "Center 02", "split_bucket": "validation", "event_count": 1},
                        {"center_label": "Center 25", "split_bucket": "train", "event_count": 3},
                    ],
                    "coverage_panels": [
                        {"panel_id": "region", "title": "Region coverage", "layout_role": "wide_left", "bars": [{"label": "Central", "count": 72}]},
                        {"panel_id": "north_south", "title": "North vs South", "layout_role": "top_right", "bars": [{"label": "North", "count": 84}]},
                        {"panel_id": "urban_rural", "title": "Urban/rural", "layout_role": "bottom_right", "bars": [{"label": "Urban", "count": 101}]},
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
                    "rows": [{"cards": [{"card_id": "analytic", "title": "Analytic cohort", "value": "15,787", "detail": "Formal modeling cohort"}]}],
                },
                {
                    "panel_id": "primary_endpoint",
                    "panel_label": "B",
                    "title": "Primary endpoint",
                    "subtitle": "Cardiovascular mortality",
                    "rows": [{"cards": [{"card_id": "ridge", "title": "Validation C-index", "value": "0.857", "detail": "Primary five-year endpoint", "accent_role": "primary"}]}],
                },
                {
                    "panel_id": "supportive_context",
                    "panel_label": "C",
                    "title": "Supportive context",
                    "subtitle": "Applicability boundary",
                    "rows": [
                        {
                            "cards": [
                                {
                                    "card_id": "internal_boundary",
                                    "title": "Applicability boundary",
                                    "value": "Internal validation only",
                                    "detail": "Multicenter support inside the current cohort",
                                    "accent_role": "contrast",
                                },
                                {
                                    "card_id": "transportability_boundary",
                                    "title": "Transportability boundary",
                                    "value": "No external validation",
                                    "detail": "Do not expand beyond the audited cohort",
                                    "accent_role": "audit",
                                },
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


def test_abh_golden_regression_tracked_docs_track_current_suite() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    text = "\n".join(
        (
            (repo_root / "docs" / "medical_display_template_catalog.md").read_text(encoding="utf-8"),
            (repo_root / "docs" / "medical_display_audit_guide.md").read_text(encoding="utf-8"),
        )
    )

    for token in (
        "binary_calibration_decision_curve_panel",
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
        "submission_graphical_abstract",
    ):
        assert token in text
    for token in (
        "title policy",
        "annotation placement",
        "panel-label/header-band anchoring",
        "graphical-abstract arrow lanes",
        "axis-window fit",
        "grouped-separation readability",
        "landmark/time-slice regression semantics",
    ):
        assert token in text


def test_materialize_display_surface_preserves_ab_golden_regression_invariants(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = _build_abh_paper_proven_workspace(tmp_path)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "GA1"]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}

    for figure_id in ("F1", "F2", "F3", "F4"):
        assert figures_by_id[figure_id]["qc_result"]["status"] == "pass"
        assert figures_by_id[figure_id]["qc_result"]["issues"] == []

    f1_layout = json.loads(
        (paper_root / "figures" / "generated" / "F1_binary_calibration_decision_curve_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert f1_layout["metrics"]["calibration_axis_window"] == {
        "xmin": 0.0,
        "xmax": 0.65,
        "ymin": 0.0,
        "ymax": 0.65,
    }
    assert not any(item["box_type"] == "title" for item in f1_layout["layout_boxes"])

    f2_layout = json.loads(
        (paper_root / "figures" / "generated" / "F2_time_to_event_discrimination_calibration_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    f2_layout_boxes = {item["box_id"]: item for item in f2_layout["layout_boxes"]}
    f2_panel_boxes = {item["box_id"]: item for item in f2_layout["panel_boxes"]}
    annotation_box = f2_layout_boxes["annotation_callout"]
    left_panel = f2_panel_boxes["panel_left"]
    right_panel = f2_panel_boxes["panel_right"]
    right_title = f2_layout_boxes["panel_right_title"]
    assert not any(item["box_type"] == "title" for item in f2_layout["layout_boxes"])
    assert annotation_box["x0"] >= left_panel["x1"] + 0.02
    assert annotation_box["x1"] <= right_panel["x0"] + (right_panel["x1"] - right_panel["x0"]) * 0.58
    assert annotation_box["y1"] <= right_panel["y1"] - 0.03
    assert annotation_box["y1"] >= right_panel["y0"] + (right_panel["y1"] - right_panel["y0"]) * 0.58
    assert (
        annotation_box["y1"] <= right_title["y0"] - 0.005
        or annotation_box["y0"] >= right_title["y1"] + 0.005
    )

    for figure_id, filename in (
        ("F3", "F3_time_to_event_risk_group_summary.layout.json"),
        ("F4", "F4_time_to_event_decision_curve.layout.json"),
    ):
        layout = json.loads((paper_root / "figures" / "generated" / filename).read_text(encoding="utf-8"))
        layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
        panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
        assert not any(item["box_type"] == "title" for item in layout["layout_boxes"])
        assert not any(item["box_type"] == "legend" for item in layout["guide_boxes"])
        assert {"panel_left_title", "panel_right_title", "panel_label_A", "panel_label_B"} <= set(layout_boxes)
        for label_box_id, panel_box_id in {
            "panel_label_A": "panel_left",
            "panel_label_B": "panel_right",
        }.items():
            label_box = layout_boxes[label_box_id]
            panel_box = panel_boxes[panel_box_id]
            panel_width = panel_box["x1"] - panel_box["x0"]
            panel_height = panel_box["y1"] - panel_box["y0"]
            assert panel_box["x0"] <= label_box["x0"] <= panel_box["x0"] + panel_width * 0.08
            assert panel_box["y1"] - panel_height * 0.10 <= label_box["y1"] <= panel_box["y1"]
            assert label_box["x1"] <= layout_boxes[f"{panel_box_id}_title"]["x0"]
        if figure_id == "F3":
            summaries = layout["metrics"]["risk_group_summaries"]
            predicted_risks = [item["mean_predicted_risk_5y"] for item in summaries]
            observed_risks = [item["observed_km_risk_5y"] for item in summaries]
            event_counts = [item["events_5y"] for item in summaries]
            assert predicted_risks == sorted(predicted_risks)
            assert observed_risks == sorted(observed_risks)
            assert event_counts == sorted(event_counts)
            assert event_counts[-1] - event_counts[0] >= 1


def test_materialize_display_surface_preserves_h_golden_regression_invariants(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = _build_abh_paper_proven_workspace(tmp_path)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F5"]["qc_result"]["status"] == "pass"
    assert figures_by_id["GA1"]["qc_result"]["status"] == "pass"

    f5_layout = json.loads(
        (paper_root / "figures" / "generated" / "F5_multicenter_generalizability_overview.layout.json").read_text(
            encoding="utf-8"
        )
    )
    f5_layout_boxes = {item["box_id"]: item for item in f5_layout["layout_boxes"]}
    f5_panel_boxes = {item["box_id"]: item for item in f5_layout["panel_boxes"]}
    f5_guide_boxes = {item["box_id"]: item for item in f5_layout["guide_boxes"]}
    assert {"panel_label_A", "panel_label_B", "panel_label_C"} <= set(f5_layout_boxes)
    assert "coverage_panel_right_stack" in f5_panel_boxes
    for label_box_id, panel_box_id in {
        "panel_label_A": "center_event_panel",
        "panel_label_B": "coverage_panel_wide_left",
        "panel_label_C": "coverage_panel_right_stack",
    }.items():
        label_box = f5_layout_boxes[label_box_id]
        panel_box = f5_panel_boxes[panel_box_id]
        panel_width = panel_box["x1"] - panel_box["x0"]
        panel_height = panel_box["y1"] - panel_box["y0"]
        assert label_box["x0"] <= panel_box["x0"] + panel_width * 0.08
        assert label_box["y1"] >= panel_box["y1"] - panel_height * 0.10
    assert f5_layout["metrics"]["center_label_mode"] == "shared_prefix_compacted"
    assert f5_layout["metrics"]["center_tick_labels"] == ["01", "02", "25"]
    assert f5_layout["metrics"]["center_axis_title"] == "Center ID"
    assert f5_layout["metrics"]["legend_title"] == "Split"
    assert f5_layout["metrics"]["legend_labels"] == ["Train", "Validation"]
    legend_box = f5_guide_boxes["legend"]
    assert legend_box["y1"] <= min(
        f5_panel_boxes["coverage_panel_wide_left"]["y0"],
        f5_panel_boxes["coverage_panel_right_stack"]["y0"],
    ) - 0.01
    assert abs(((legend_box["x0"] + legend_box["x1"]) / 2.0) - 0.5) <= 0.02
    assert not any(item["box_type"] == "title" for item in f5_layout["layout_boxes"])

    ga_layout = json.loads(
        (paper_root / "figures" / "generated" / "GA1_graphical_abstract.layout.json").read_text(encoding="utf-8")
    )
    arrow_boxes = [
        item
        for item in ga_layout["guide_boxes"]
        if item["box_type"] == "arrow_connector"
    ]
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
        if item["display_id"] in {"Figure6", "Figure7", "Figure18"}
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
        layout_boxes = [
            {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.62, "y1": 0.97},
            {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.01, "y0": 0.24, "x1": 0.05, "y1": 0.70},
        ]
        panel_boxes = [{"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86}]
        guide_boxes = [{"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44}]
        if template_id == "time_dependent_roc_horizon":
            metrics = {
                "series": list(display_payload["series"]),
                "reference_line": dict(display_payload["reference_line"]),
                "title": str(display_payload["title"]),
                "caption": str(display_payload["caption"]),
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
    assert result["figures_materialized"] == ["F6", "F7", "F18"]

    f6_layout = json.loads((paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.layout.json").read_text(encoding="utf-8"))
    f7_layout = json.loads((paper_root / "figures" / "generated" / "F7_cumulative_incidence_grouped.layout.json").read_text(encoding="utf-8"))
    f18_layout = json.loads((paper_root / "figures" / "generated" / "F18_time_dependent_roc_horizon.layout.json").read_text(encoding="utf-8"))

    f6_terminal_values = [group["values"][-1] for group in f6_layout["metrics"]["groups"]]
    f7_terminal_values = [group["values"][-1] for group in f7_layout["metrics"]["groups"]]
    assert max(f6_terminal_values) - min(f6_terminal_values) >= 0.01
    assert max(f7_terminal_values) - min(f7_terminal_values) >= 0.01
    assert f6_layout["metrics"]["annotation"] == "Log-rank P < .001"
    assert f7_layout["metrics"]["annotation"] == "Gray test P = .002"

    assert f18_layout["metrics"]["title"] == "Time-dependent ROC at 24 months"
    assert f18_layout["metrics"]["caption"] == (
        "Horizon-specific discrimination of the locked survival model at 24 months."
    )
    assert f18_layout["metrics"]["series"][0]["label"] == "24-month horizon"
    assert f18_layout["metrics"]["series"][0]["annotation"] == "AUC = 0.81"
    assert f18_layout["metrics"]["reference_line"]["label"] == "Chance"
