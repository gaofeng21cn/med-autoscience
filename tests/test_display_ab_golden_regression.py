from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _build_single_figure_workspace(
    *,
    paper_root: Path,
    display_id: str,
    requirement_key: str,
    catalog_id: str,
    input_filename: str,
    input_schema_id: str,
    display_payload: dict[str, object],
) -> None:
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": display_id,
                    "display_kind": "figure",
                    "requirement_key": requirement_key,
                    "catalog_id": catalog_id,
                    "shell_path": f"paper/figures/{display_id}.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#245A6B",
                "comparator_curve": "#B89A6D",
                "reference_line": "#6B7280",
                "heatmap_low": "#2166AC",
                "heatmap_high": "#B2182B",
            },
            "palette": {
                "primary": "#245A6B",
                "secondary": "#B89A6D",
                "light": "#E7E1D8",
                "primary_soft": "#EAF2F5",
                "secondary_soft": "#F4EEE5",
            },
            "typography": {
                "title_size": 12.5,
                "axis_title_size": 11.0,
                "tick_size": 10.0,
                "legend_size": 8.2,
                "panel_label_size": 11.0,
            },
            "stroke": {"marker_size": 4.2, "primary_linewidth": 2.2},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": display_id,
                    "template_id": requirement_key,
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / input_filename,
        {
            "schema_version": 1,
            "input_schema_id": input_schema_id,
            "displays": [display_payload],
        },
    )


def test_time_dependent_roc_horizon_preserves_current_curve_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _build_single_figure_workspace(
        paper_root=paper_root,
        display_id="Figure8",
        requirement_key="time_dependent_roc_horizon",
        catalog_id="F8",
        input_filename="binary_prediction_curve_inputs.json",
        input_schema_id="binary_prediction_curve_inputs_v1",
        display_payload={
            "display_id": "Figure8",
            "template_id": "fenggaolab.org.medical-display-core::time_dependent_roc_horizon",
            "title": "Time-dependent ROC at 60 months",
            "caption": "Horizon-specific discrimination of the locked survival model.",
            "time_horizon_months": 60,
            "x_label": "1 - Specificity",
            "y_label": "Sensitivity",
            "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
            "series": [
                {
                    "label": "Primary model",
                    "x": [0.0, 0.08, 0.21, 1.0],
                    "y": [0.0, 0.66, 0.86, 1.0],
                    "annotation": "AUC = 0.84",
                },
                {
                    "label": "Comparator",
                    "x": [0.0, 0.18, 0.36, 1.0],
                    "y": [0.0, 0.55, 0.74, 1.0],
                    "annotation": "AUC = 0.76",
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F8_time_dependent_roc_horizon.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(box["box_type"] == "legend" for box in layout_sidecar["guide_boxes"])
    assert [item["label"] for item in layout_sidecar["metrics"]["series"]] == ["Primary model", "Comparator"]
    assert layout_sidecar["metrics"]["reference_line"]["label"] == "Chance"
    assert layout_sidecar["metrics"]["time_horizon_months"] == 60

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_time_to_event_decision_curve_preserves_current_two_panel_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _build_single_figure_workspace(
        paper_root=paper_root,
        display_id="Figure10",
        requirement_key="time_to_event_decision_curve",
        catalog_id="F10",
        input_filename="time_to_event_decision_curve_inputs.json",
        input_schema_id="time_to_event_decision_curve_inputs_v1",
        display_payload={
            "display_id": "Figure10",
            "template_id": "fenggaolab.org.medical-display-core::time_to_event_decision_curve",
            "title": "Five-year decision curve",
            "caption": "Net benefit for the survival model across the prespecified threshold range.",
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
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F10_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert {"decision_curve_panel", "treated_fraction_panel"} == {
        box["box_type"] for box in layout_sidecar["panel_boxes"]
    }
    assert [item["label"] for item in layout_sidecar["metrics"]["series"]] == ["Model", "Treat all"]
    assert layout_sidecar["metrics"]["treated_fraction_series"]["label"] == "Model"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_risk_layering_monotonic_bars_preserves_current_monotonic_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _build_single_figure_workspace(
        paper_root=paper_root,
        display_id="Figure11",
        requirement_key="risk_layering_monotonic_bars",
        catalog_id="F11",
        input_filename="risk_layering_monotonic_inputs.json",
        input_schema_id="risk_layering_monotonic_inputs_v1",
        display_payload={
            "display_id": "Figure11",
            "template_id": "fenggaolab.org.medical-display-core::risk_layering_monotonic_bars",
            "title": "Risk layering by score band",
            "caption": "Predicted and observed event proportions remain monotonic across prespecified strata.",
            "y_label": "Outcome risk (%)",
            "left_panel_title": "Predicted risk by tertile",
            "left_x_label": "Predicted risk tertile",
            "left_bars": [
                {"label": "Low", "cases": 120, "events": 2, "risk": 2 / 120},
                {"label": "Intermediate", "cases": 120, "events": 4, "risk": 4 / 120},
                {"label": "High", "cases": 120, "events": 11, "risk": 11 / 120},
            ],
            "right_panel_title": "Observed risk by tertile",
            "right_x_label": "Observed risk tertile",
            "right_bars": [
                {"label": "Low", "cases": 120, "events": 2, "risk": 2 / 120},
                {"label": "Intermediate", "cases": 120, "events": 5, "risk": 5 / 120},
                {"label": "High", "cases": 120, "events": 14, "risk": 14 / 120},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F11_risk_layering_monotonic_bars.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert all(box["box_type"] == "panel" for box in layout_sidecar["panel_boxes"])
    assert any(box["box_type"] == "risk_bar" for box in layout_sidecar["layout_boxes"])
    predicted = [item["risk"] for item in layout_sidecar["metrics"]["left_bars"]]
    observed = [item["risk"] for item in layout_sidecar["metrics"]["right_bars"]]
    assert predicted == sorted(predicted)
    assert observed == sorted(observed)

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_time_to_event_multihorizon_calibration_panel_preserves_ab_horizon_calibration_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _build_single_figure_workspace(
        paper_root=paper_root,
        display_id="Figure9",
        requirement_key="time_to_event_multihorizon_calibration_panel",
        catalog_id="F9",
        input_filename="time_to_event_multihorizon_calibration_inputs.json",
        input_schema_id="time_to_event_multihorizon_calibration_inputs_v1",
        display_payload={
            "display_id": "Figure9",
            "template_id": "fenggaolab.org.medical-display-core::time_to_event_multihorizon_calibration_panel",
            "title": "Grouped survival calibration governance across 36 and 60 months",
            "caption": "Parallel grouped calibration panels lock multi-horizon survival calibration review to audited contracts.",
            "x_label": "Predicted / observed risk",
            "panels": [
                {
                    "panel_id": "h36",
                    "panel_label": "A",
                    "title": "36-month calibration",
                    "time_horizon_months": 36,
                    "calibration_summary": [
                        {
                            "group_label": "Low risk",
                            "group_order": 1,
                            "n": 182,
                            "events": 5,
                            "predicted_risk": 0.03,
                            "observed_risk": 0.04,
                        },
                        {
                            "group_label": "Intermediate risk",
                            "group_order": 2,
                            "n": 146,
                            "events": 13,
                            "predicted_risk": 0.11,
                            "observed_risk": 0.13,
                        },
                        {
                            "group_label": "High risk",
                            "group_order": 3,
                            "n": 88,
                            "events": 22,
                            "predicted_risk": 0.24,
                            "observed_risk": 0.27,
                        },
                    ],
                },
                {
                    "panel_id": "h60",
                    "panel_label": "B",
                    "title": "60-month calibration",
                    "time_horizon_months": 60,
                    "calibration_summary": [
                        {
                            "group_label": "Low risk",
                            "group_order": 1,
                            "n": 182,
                            "events": 8,
                            "predicted_risk": 0.04,
                            "observed_risk": 0.05,
                        },
                        {
                            "group_label": "Intermediate risk",
                            "group_order": 2,
                            "n": 146,
                            "events": 19,
                            "predicted_risk": 0.13,
                            "observed_risk": 0.15,
                        },
                        {
                            "group_label": "High risk",
                            "group_order": 3,
                            "n": 88,
                            "events": 27,
                            "predicted_risk": 0.31,
                            "observed_risk": 0.29,
                        },
                    ],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F9_time_to_event_multihorizon_calibration_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert all(box["box_type"] == "calibration_panel" for box in layout_sidecar["panel_boxes"])
    assert any(box["box_type"] == "legend" for box in layout_sidecar["guide_boxes"])
    assert [item["time_horizon_months"] for item in layout_sidecar["metrics"]["panels"]] == [36, 60]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["panels"][1]["calibration_summary"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
