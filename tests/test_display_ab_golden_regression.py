from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_time_to_event_landmark_performance_panel_preserves_ab_composite_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure27",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_landmark_performance_panel",
                    "catalog_id": "F27",
                    "shell_path": "paper/figures/Figure27.shell.json",
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
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure27",
                    "template_id": "time_to_event_landmark_performance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure27",
                    "template_id": "fenggaolab.org.medical-display-core::time_to_event_landmark_performance_panel",
                    "title": "Landmark survival performance summary across recurrence prediction windows",
                    "caption": "Composite regression lock for landmark discrimination, error, and calibration governance.",
                    "discrimination_panel_title": "Discrimination",
                    "discrimination_x_label": "Validation C-index",
                    "error_panel_title": "Prediction error",
                    "error_x_label": "Brier score",
                    "calibration_panel_title": "Calibration",
                    "calibration_x_label": "Calibration slope",
                    "landmark_summaries": [
                        {
                            "window_label": "3→12 months",
                            "analysis_window_label": "3-month landmark predicting 12-month recurrence",
                            "landmark_months": 3,
                            "prediction_months": 12,
                            "c_index": 0.78,
                            "brier_score": 0.18,
                            "calibration_slope": 1.06,
                        },
                        {
                            "window_label": "6→15 months",
                            "analysis_window_label": "6-month landmark predicting 15-month recurrence",
                            "landmark_months": 6,
                            "prediction_months": 15,
                            "c_index": 0.81,
                            "brier_score": 0.15,
                            "calibration_slope": 0.98,
                        },
                        {
                            "window_label": "9→18 months",
                            "analysis_window_label": "9-month landmark predicting 18-month recurrence",
                            "landmark_months": 9,
                            "prediction_months": 18,
                            "c_index": 0.84,
                            "brier_score": 0.12,
                            "calibration_slope": 0.93,
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"reference_line"}
    assert [item["metric_kind"] for item in layout_sidecar["metrics"]["metric_panels"]] == [
        "c_index",
        "brier_score",
        "calibration_slope",
    ]
    assert layout_sidecar["metrics"]["metric_panels"][2]["reference_value"] == 1.0

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_time_to_event_threshold_governance_panel_preserves_ab_threshold_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure29",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_threshold_governance_panel",
                    "catalog_id": "F29",
                    "shell_path": "paper/figures/Figure29.shell.json",
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
            },
            "palette": {
                "primary": "#245A6B",
                "secondary": "#B89A6D",
                "light": "#E7E1D8",
                "primary_soft": "#EAF2F5",
                "secondary_soft": "#F4EEE5",
            },
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.2},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure29",
                    "template_id": "time_to_event_threshold_governance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure29",
                    "template_id": "fenggaolab.org.medical-display-core::time_to_event_threshold_governance_panel",
                    "title": "Threshold governance for 5-year deployment-facing survival triage",
                    "caption": "Threshold cards and grouped calibration governance lock operating review to explicit audited inputs.",
                    "threshold_panel_title": "Operating thresholds",
                    "calibration_panel_title": "Grouped calibration at 5 years",
                    "calibration_x_label": "Predicted / observed 5-year risk",
                    "threshold_summaries": [
                        {
                            "threshold_label": "Rule-in",
                            "threshold": 0.10,
                            "sensitivity": 0.88,
                            "specificity": 0.52,
                            "net_benefit": 0.041,
                        },
                        {
                            "threshold_label": "Actionable",
                            "threshold": 0.15,
                            "sensitivity": 0.74,
                            "specificity": 0.67,
                            "net_benefit": 0.058,
                        },
                    ],
                    "risk_group_summaries": [
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
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([box for box in layout_sidecar["layout_boxes"] if box["box_type"] == "threshold_card"]) == 2
    assert any(box["box_type"] == "legend" for box in layout_sidecar["guide_boxes"])
    assert [item["threshold"] for item in layout_sidecar["metrics"]["threshold_summaries"]] == [0.10, 0.15]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["risk_group_summaries"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_time_to_event_multihorizon_calibration_panel_preserves_ab_horizon_calibration_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure30",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_multihorizon_calibration_panel",
                    "catalog_id": "F30",
                    "shell_path": "paper/figures/Figure30.shell.json",
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
            },
            "palette": {
                "primary": "#245A6B",
                "secondary": "#B89A6D",
                "light": "#E7E1D8",
                "primary_soft": "#EAF2F5",
                "secondary_soft": "#F4EEE5",
            },
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.2},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure30",
                    "template_id": "time_to_event_multihorizon_calibration_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure30",
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
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.layout.json").read_text(
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
