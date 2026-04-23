from .shared import *

def test_materialize_display_surface_omits_figure_title_for_risk_layering_monotonic_bars_by_default(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "risk_layering",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/risk_layering.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "risk_layering_monotonic_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "risk_layering_monotonic_inputs_v1",
            "displays": [
                {
                    "display_id": "risk_layering",
                    "template_id": "risk_layering_monotonic_bars",
                    "title": "Clinical utility of the clinically informed preoperative model compared with the core preoperative comparator",
                    "caption": "Observed risk rises monotonically across score bands and grouped follow-up strata.",
                    "y_label": "Risk of later persistent global hypopituitarism (%)",
                    "left_panel_title": "Core preoperative comparator",
                    "left_x_label": "Predicted-risk tertile",
                    "left_bars": [
                        {"label": "Low", "cases": 118, "events": 5, "risk": 0.0423728813559322},
                        {"label": "Intermediate", "cases": 118, "events": 8, "risk": 0.06779661016949153},
                        {"label": "High", "cases": 118, "events": 44, "risk": 0.3728813559322034},
                    ],
                    "right_panel_title": "Clinically informed model",
                    "right_x_label": "Predicted-risk tertile",
                    "right_bars": [
                        {"label": "Low", "cases": 118, "events": 5, "risk": 0.0423728813559322},
                        {"label": "Intermediate", "cases": 118, "events": 10, "risk": 0.0847457627118644},
                        {"label": "High", "cases": 118, "events": 42, "risk": 0.3559322033898305},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F2_risk_layering_monotonic_bars.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])

def test_materialize_display_surface_honors_calibration_axis_window_for_binary_calibration_decision_curve_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "calibration_decision",
                    "display_kind": "figure",
                    "requirement_key": "binary_calibration_decision_curve_panel",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/calibration_decision.shell.json",
                }
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
                    "display_id": "calibration_decision",
                    "template_id": "binary_calibration_decision_curve_panel",
                    "title": "Clinical coherence and coefficient stability of the clinically informed preoperative model",
                    "caption": "Calibration and decision-curve evidence across candidate packages.",
                    "calibration_x_label": "Mean predicted probability",
                    "calibration_y_label": "Observed probability",
                    "decision_x_label": "Threshold probability",
                    "decision_y_label": "Net benefit",
                    "calibration_axis_window": {
                        "xmin": 0.0,
                        "xmax": 0.65,
                        "ymin": 0.0,
                        "ymax": 0.65,
                    },
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
                        {
                            "label": "Treat none",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.0, 0.0, 0.0, 0.0, 0.0],
                        },
                        {
                            "label": "Treat all",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.01, -0.03, -0.08, -0.14, -0.22],
                        },
                    ],
                    "decision_focus_window": {"xmin": 0.15, "xmax": 0.35},
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root / "figures" / "generated" / "F3_binary_calibration_decision_curve_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert layout_sidecar["metrics"]["calibration_axis_window"] == {
        "xmin": 0.0,
        "xmax": 0.65,
        "ymin": 0.0,
        "ymax": 0.65,
    }
    reference_line = layout_sidecar["metrics"]["calibration_reference_line"]
    assert max(reference_line["x"]) < 1.0
    assert max(reference_line["y"]) < 1.0
    assert all(0.0 <= value <= 1.0 for value in reference_line["x"])
    assert all(0.0 <= value <= 1.0 for value in reference_line["y"])
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert sum(1 for item in layout_sidecar["layout_boxes"] if item["box_type"] == "subplot_title") == 2

def test_materialize_display_surface_omits_figure_title_for_time_to_event_discrimination_calibration_panel_by_default(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "discrimination_calibration",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/discrimination_calibration.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
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

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F2_time_to_event_discrimination_calibration_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])

def test_materialize_display_surface_omits_figure_title_for_shap_summary_by_default(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    restrict_display_registry_to_display_ids(paper_root, "Figure13")

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F13_shap_summary_beeswarm.layout.json").read_text(encoding="utf-8")
    )
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = next(item for item in figure_catalog["figures"] if item["figure_id"] == "F13")

    assert figure_entry["title"] == "SHAP summary beeswarm"
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert layout_sidecar["render_context"]["layout_override"].get("show_figure_title") is not True

def test_materialize_display_surface_places_time_to_event_callout_in_right_upper_blank_zone(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "discrimination_calibration",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/discrimination_calibration.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
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

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F2_time_to_event_discrimination_calibration_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    layout_boxes = {item["box_id"]: item for item in layout_sidecar["layout_boxes"]}
    panel_boxes = {item["box_id"]: item for item in layout_sidecar["panel_boxes"]}
    annotation_box = layout_boxes["annotation_callout"]
    left_panel = panel_boxes["panel_left"]
    right_panel = panel_boxes["panel_right"]
    right_title = layout_boxes["panel_right_title"]

    assert annotation_box["x0"] >= left_panel["x1"] + 0.02
    assert right_panel["x0"] <= annotation_box["x0"] <= right_panel["x0"] + (right_panel["x1"] - right_panel["x0"]) * 0.14
    assert annotation_box["x1"] <= right_panel["x0"] + (right_panel["x1"] - right_panel["x0"]) * 0.58
    assert annotation_box["y0"] >= right_panel["y0"] + 0.01
    assert annotation_box["y1"] <= right_panel["y1"] - 0.03
    assert (
        annotation_box["y1"] <= right_title["y0"] - 0.005
        or annotation_box["y0"] >= right_title["y1"] + 0.005
    )
    assert annotation_box["y1"] >= right_panel["y0"] + (right_panel["y1"] - right_panel["y0"]) * 0.58

def test_materialize_display_surface_omits_figure_title_and_legend_for_time_to_event_risk_group_summary_by_default(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "km_risk_stratification",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/km_risk_stratification.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
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

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F3_time_to_event_risk_group_summary.layout.json").read_text(
            encoding="utf-8"
        )
    )
    layout_boxes = {item["box_id"]: item for item in layout_sidecar["layout_boxes"]}
    panel_boxes = {item["box_id"]: item for item in layout_sidecar["panel_boxes"]}
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert not any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
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

def test_materialize_display_surface_omits_figure_title_and_legend_for_time_to_event_decision_curve_by_default(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "decision_curve",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/decision_curve.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
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
                    "treated_fraction_series": {
                        "label": "Model",
                        "x": [0.5, 1.0, 2.0, 4.0],
                        "y": [45.0, 28.0, 12.0, 2.0],
                    },
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F4_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )
    layout_boxes = {item["box_id"]: item for item in layout_sidecar["layout_boxes"]}
    panel_boxes = {item["box_id"]: item for item in layout_sidecar["panel_boxes"]}
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert not any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
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

def test_materialize_display_surface_multicenter_overview_adds_panel_labels_and_compacts_center_tick_labels(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "multicenter_generalizability",
                    "display_kind": "figure",
                    "requirement_key": "multicenter_generalizability_overview",
                    "catalog_id": "F5",
                    "shell_path": "paper/figures/multicenter_generalizability.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
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
                        {
                            "panel_id": "region",
                            "title": "Region coverage",
                            "layout_role": "wide_left",
                            "bars": [{"label": "Central", "count": 72}],
                        },
                        {
                            "panel_id": "north_south",
                            "title": "North vs South",
                            "layout_role": "top_right",
                            "bars": [{"label": "North", "count": 84}],
                        },
                        {
                            "panel_id": "urban_rural",
                            "title": "Urban/rural",
                            "layout_role": "bottom_right",
                            "bars": [{"label": "Urban", "count": 101}],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F5_multicenter_generalizability_overview.layout.json").read_text(
            encoding="utf-8"
        )
    )
    layout_box_ids = {item["box_id"] for item in layout_sidecar["layout_boxes"]}
    panel_box_ids = {item["box_id"] for item in layout_sidecar["panel_boxes"]}
    assert {"panel_label_A", "panel_label_B", "panel_label_C"} <= layout_box_ids
    assert "coverage_panel_right_stack" in panel_box_ids
    layout_boxes = {item["box_id"]: item for item in layout_sidecar["layout_boxes"]}
    panel_boxes = {item["box_id"]: item for item in layout_sidecar["panel_boxes"]}
    guide_boxes = {item["box_id"]: item for item in layout_sidecar["guide_boxes"]}
    for label_box_id, panel_box_id in {
        "panel_label_A": "center_event_panel",
        "panel_label_B": "coverage_panel_wide_left",
        "panel_label_C": "coverage_panel_right_stack",
    }.items():
        label_box = layout_boxes[label_box_id]
        panel_box = panel_boxes[panel_box_id]
        panel_width = panel_box["x1"] - panel_box["x0"]
        panel_height = panel_box["y1"] - panel_box["y0"]
        assert label_box["x0"] <= panel_box["x0"] + panel_width * 0.08
        assert label_box["y1"] >= panel_box["y1"] - panel_height * 0.10
        assert (label_box["y1"] - label_box["y0"]) >= 0.014
    assert layout_sidecar["metrics"]["center_label_mode"] == "shared_prefix_compacted"
    assert layout_sidecar["metrics"]["center_tick_labels"] == ["01", "02", "25"]
    assert layout_sidecar["metrics"]["center_axis_title"] == "Center ID"
    assert layout_sidecar["metrics"]["legend_title"] == "Split"
    assert layout_sidecar["metrics"]["legend_labels"] == ["Train", "Validation"]
    legend_box = guide_boxes["legend"]
    assert legend_box["y1"] <= min(panel["y0"] for panel in panel_boxes.values()) - 0.01
    assert abs(((legend_box["x0"] + legend_box["x1"]) / 2.0) - 0.5) <= 0.08
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert "manuscript-facing authority surface" in (paper_root / "README.md").read_text(encoding="utf-8")
    assert "figure_catalog.json" in (paper_root / "figures" / "README.md").read_text(encoding="utf-8")
    generated_readme = (paper_root / "figures" / "generated" / "README.md").read_text(encoding="utf-8")
    assert "use the catalog rather than guessing by filename age" in generated_readme
    assert "F5" in generated_readme
    assert "table_catalog.json" in (paper_root / "tables" / "README.md").read_text(encoding="utf-8")
    assert "paper/tables/generated/" in (paper_root / "tables" / "generated" / "README.md").read_text(encoding="utf-8")

def test_materialize_display_surface_prunes_unreferenced_generated_outputs(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    restrict_display_registry_to_display_ids(paper_root, "Figure15")

    stale_paths = [
        paper_root / "figures" / "generated" / "F15_kaplan_meier_grouped.png",
        paper_root / "figures" / "generated" / "F15_kaplan_meier_grouped.pdf",
        paper_root / "figures" / "generated" / "F15_kaplan_meier_grouped.layout.json",
        paper_root / "tables" / "generated" / "T2_old_summary.md",
    ]
    for stale_path in stale_paths:
        stale_path.parent.mkdir(parents=True, exist_ok=True)
        if stale_path.suffix == ".png":
            stale_path.write_bytes(
                bytes.fromhex(
                    "89504e470d0a1a0a"
                    "0000000d49484452000000010000000108060000001f15c489"
                    "0000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082"
                )
            )
        else:
            stale_path.write_text("stale\n", encoding="utf-8")

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["pruned_generated_paths"] == [
        "paper/figures/generated/F15_kaplan_meier_grouped.layout.json",
        "paper/figures/generated/F15_kaplan_meier_grouped.pdf",
        "paper/figures/generated/F15_kaplan_meier_grouped.png",
        "paper/tables/generated/T2_old_summary.md",
    ]
    for stale_path in stale_paths:
        assert not stale_path.exists()
    assert (paper_root / "figures" / "generated" / "F15_time_to_event_risk_group_summary.png").exists()

def test_materialize_display_surface_generates_model_complexity_audit_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "model_audit",
                    "display_kind": "figure",
                    "requirement_key": "model_complexity_audit_panel",
                    "catalog_id": "F4",
                    "shell_path": "paper/figures/model_audit.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "model_complexity_audit_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "model_complexity_audit_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "model_audit",
                    "template_id": "model_complexity_audit_panel",
                    "title": (
                        "Threshold-based operating characteristics and risk-group profiles "
                        "for the clinically informed preoperative model"
                    ),
                    "caption": "Discrimination, calibration, and bounded complexity audit across candidate packages.",
                    "metric_panels": [
                        {
                            "panel_id": "auroc_panel",
                            "panel_label": "A",
                            "title": "Discrimination",
                            "x_label": "AUROC",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.80},
                                {"label": "Clinically informed preoperative model", "value": 0.81},
                                {"label": "Random forest comparison model", "value": 0.84},
                            ],
                        },
                        {
                            "panel_id": "brier_panel",
                            "panel_label": "B",
                            "title": "Overall error",
                            "x_label": "Brier score",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.14},
                                {"label": "Clinically informed preoperative model", "value": 0.11},
                                {"label": "Random forest comparison model", "value": 0.10},
                            ],
                        },
                        {
                            "panel_id": "slope_panel",
                            "panel_label": "C",
                            "title": "Calibration",
                            "x_label": "Calibration slope",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Core preoperative model", "value": 2.4},
                                {"label": "Clinically informed preoperative model", "value": 1.04},
                                {"label": "Random forest comparison model", "value": 0.80},
                            ],
                        },
                    ],
                    "audit_panels": [
                        {
                            "panel_id": "coefficient_panel",
                            "panel_label": "D",
                            "title": "Coefficient stability",
                            "x_label": "Mean odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age", "value": 0.91},
                                {"label": "Tumor diameter", "value": 1.44},
                                {"label": "Knosp grade", "value": 1.13},
                            ],
                        },
                        {
                            "panel_id": "domain_panel",
                            "panel_label": "E",
                            "title": "Domain stability",
                            "x_label": "Mean absolute coefficient",
                            "rows": [
                                {"label": "Tumor burden", "value": 0.34},
                                {"label": "Endocrine impairment", "value": 0.11},
                                {"label": "Visual compromise", "value": 0.12},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F4"]
    assert (paper_root / "figures" / "generated" / "F4_model_complexity_audit_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F4_model_complexity_audit_panel.pdf").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["template_id"] == full_id("model_complexity_audit_panel")
    assert figure_entry["qc_result"]["status"] == "pass"
