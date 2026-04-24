from .shared import *

def test_transportability_recalibration_governance_panel_preserves_h_bounded_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure48",
                    "display_kind": "figure",
                    "requirement_key": "transportability_recalibration_governance_panel",
                    "catalog_id": "F48",
                    "shell_path": "paper/figures/Figure48.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "transportability_recalibration_governance_panel.json",
        {
            "schema_version": 1,
            "shell_id": "fenggaolab.org.medical-display-core::transportability_recalibration_governance_panel",
            "display_id": "Figure48",
            "title": "Transportability recalibration governance overview",
            "caption": "Regression lock for bounded center-coverage, batch-shift, and recalibration-governance evidence.",
            "coverage_panel_title": "Center coverage",
            "coverage_x_label": "Patients retained",
            "center_rows": [
                {"center_id": "train_a", "center_label": "Train A", "cohort_role": "Derivation", "support_count": 412, "event_count": 63},
                {"center_id": "validation_c", "center_label": "Validation C", "cohort_role": "Internal validation", "support_count": 236, "event_count": 34},
                {"center_id": "external_b", "center_label": "External B", "cohort_role": "External", "support_count": 188, "event_count": 29},
            ],
            "batch_panel_title": "Batch shift map",
            "batch_x_label": "Shift domain",
            "batch_y_label": "Center",
            "batch_threshold": 0.20,
            "batch_rows": [{"label": "Train A"}, {"label": "Validation C"}, {"label": "External B"}],
            "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}, {"label": "Feature drift"}],
            "batch_cells": [
                {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                {"x": "Feature drift", "y": "Train A", "value": 0.09},
                {"x": "Specimen drift", "y": "Validation C", "value": 0.12},
                {"x": "Scanner drift", "y": "Validation C", "value": 0.16},
                {"x": "Feature drift", "y": "Validation C", "value": 0.13},
                {"x": "Specimen drift", "y": "External B", "value": 0.14},
                {"x": "Scanner drift", "y": "External B", "value": 0.18},
                {"x": "Feature drift", "y": "External B", "value": 0.17},
            ],
            "recalibration_panel_title": "Recalibration governance",
            "slope_acceptance_lower": 0.90,
            "slope_acceptance_upper": 1.10,
            "oe_ratio_acceptance_lower": 0.90,
            "oe_ratio_acceptance_upper": 1.10,
            "recalibration_rows": [
                {
                    "center_id": "train_a",
                    "slope": 1.00,
                    "oe_ratio": 1.00,
                    "action": "Reference fit",
                    "detail": "Derivation reference retained for calibration context.",
                },
                {
                    "center_id": "validation_c",
                    "slope": 0.96,
                    "oe_ratio": 1.04,
                    "action": "Monitor only",
                    "detail": "Internal validation remains within the pre-specified acceptance band.",
                },
                {
                    "center_id": "external_b",
                    "slope": 0.84,
                    "oe_ratio": 1.18,
                    "action": "Recalibrate before deployment",
                    "detail": "External B exceeds the pre-specified acceptance band.",
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F48_transportability_recalibration_governance_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["center_label"] for item in layout_sidecar["metrics"]["center_rows"]] == [
        "Train A",
        "Validation C",
        "External B",
    ]
    assert [item["label"] for item in layout_sidecar["metrics"]["batch_rows"]] == [
        "Train A",
        "Validation C",
        "External B",
    ]
    assert layout_sidecar["metrics"]["slope_acceptance_lower"] == 0.90
    assert layout_sidecar["metrics"]["slope_acceptance_upper"] == 1.10
    assert layout_sidecar["metrics"]["oe_ratio_acceptance_lower"] == 0.90
    assert layout_sidecar["metrics"]["oe_ratio_acceptance_upper"] == 1.10
    assert [item["center_id"] for item in layout_sidecar["metrics"]["recalibration_rows"]] == [
        "train_a",
        "validation_c",
        "external_b",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_center_transportability_governance_summary_panel_preserves_h_bounded_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure50",
                    "display_kind": "figure",
                    "requirement_key": "center_transportability_governance_summary_panel",
                    "catalog_id": "F50",
                    "shell_path": "paper/figures/Figure50.shell.json",
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
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff", "audit": "#7c3aed"},
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
                    "display_id": "Figure50",
                    "template_id": "center_transportability_governance_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "center_transportability_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "center_transportability_governance_summary_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure50",
                    "template_id": "fenggaolab.org.medical-display-core::center_transportability_governance_summary_panel",
                    "title": "Center transportability governance summary",
                    "caption": "Regression lock for bounded center-level transportability governance synthesis.",
                    "metric_family": "discrimination",
                    "metric_panel_title": "Center-level discrimination",
                    "metric_x_label": "AUROC",
                    "metric_reference_value": 0.80,
                    "batch_shift_threshold": 0.20,
                    "slope_acceptance_lower": 0.90,
                    "slope_acceptance_upper": 1.10,
                    "oe_ratio_acceptance_lower": 0.90,
                    "oe_ratio_acceptance_upper": 1.10,
                    "summary_panel_title": "Transportability governance summary",
                    "centers": [
                        {
                            "center_id": "train_a",
                            "center_label": "Train A",
                            "cohort_role": "Derivation",
                            "support_count": 412,
                            "event_count": 63,
                            "metric_estimate": 0.84,
                            "metric_lower": 0.80,
                            "metric_upper": 0.88,
                            "max_shift": 0.11,
                            "slope": 1.00,
                            "oe_ratio": 1.00,
                            "verdict": "stable",
                            "action": "Reference fit",
                            "detail": "Derivation center remains inside every declared governance band.",
                        },
                        {
                            "center_id": "validation_c",
                            "center_label": "Validation C",
                            "cohort_role": "Internal validation",
                            "support_count": 236,
                            "event_count": 34,
                            "metric_estimate": 0.82,
                            "metric_lower": 0.78,
                            "metric_upper": 0.86,
                            "max_shift": 0.16,
                            "slope": 0.96,
                            "oe_ratio": 1.04,
                            "verdict": "stable",
                            "action": "Monitor only",
                            "detail": "Internal validation remains within the acceptance band.",
                        },
                        {
                            "center_id": "external_b",
                            "center_label": "External B",
                            "cohort_role": "External",
                            "support_count": 188,
                            "event_count": 29,
                            "metric_estimate": 0.78,
                            "metric_lower": 0.73,
                            "metric_upper": 0.83,
                            "max_shift": 0.18,
                            "slope": 0.84,
                            "oe_ratio": 1.18,
                            "verdict": "context_dependent",
                            "action": "Recalibrate before deployment",
                            "detail": "External center needs recalibration before any manuscript-facing transportability claim.",
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root / "figures" / "generated" / "F50_center_transportability_governance_summary_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert layout_sidecar["metrics"]["metric_family"] == "discrimination"
    assert layout_sidecar["metrics"]["batch_shift_threshold"] == 0.20
    assert [item["center_label"] for item in layout_sidecar["metrics"]["centers"]] == [
        "Train A",
        "Validation C",
        "External B",
    ]
    assert [item["action"] for item in layout_sidecar["metrics"]["centers"]] == [
        "Reference fit",
        "Monitor only",
        "Recalibrate before deployment",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
