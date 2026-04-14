from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_generalizability_subgroup_composite_panel_preserves_ch_bounded_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure34",
                    "display_kind": "figure",
                    "requirement_key": "generalizability_subgroup_composite_panel",
                    "catalog_id": "F34",
                    "shell_path": "paper/figures/Figure34.shell.json",
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
                    "display_id": "Figure34",
                    "template_id": "generalizability_subgroup_composite_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure34",
                    "template_id": "fenggaolab.org.medical-display-core::generalizability_subgroup_composite_panel",
                    "title": "Generalizability and subgroup discrimination composite for external validation",
                    "caption": "Regression lock for bounded generalizability plus subgroup robustness evidence.",
                    "metric_family": "discrimination",
                    "primary_label": "Locked model",
                    "comparator_label": "Derivation cohort",
                    "overview_panel_title": "External cohort discrimination overview",
                    "overview_x_label": "AUROC",
                    "overview_rows": [
                        {
                            "cohort_id": "external_a",
                            "cohort_label": "External A",
                            "support_count": 184,
                            "event_count": 29,
                            "metric_value": 0.82,
                            "comparator_metric_value": 0.79,
                        },
                        {
                            "cohort_id": "external_b",
                            "cohort_label": "External B",
                            "support_count": 163,
                            "event_count": 21,
                            "metric_value": 0.78,
                            "comparator_metric_value": 0.79,
                        },
                    ],
                    "subgroup_panel_title": "Prespecified subgroup discrimination stability",
                    "subgroup_x_label": "AUROC",
                    "subgroup_reference_value": 0.80,
                    "subgroup_rows": [
                        {
                            "subgroup_id": "age_ge_65",
                            "subgroup_label": "Age ≥65 years",
                            "group_n": 201,
                            "estimate": 0.82,
                            "lower": 0.78,
                            "upper": 0.86,
                        },
                        {
                            "subgroup_id": "female",
                            "subgroup_label": "Female",
                            "group_n": 173,
                            "estimate": 0.79,
                            "lower": 0.75,
                            "upper": 0.83,
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert [item["cohort_label"] for item in layout_sidecar["metrics"]["overview_rows"]] == ["External A", "External B"]
    assert [item["subgroup_label"] for item in layout_sidecar["metrics"]["subgroup_rows"]] == [
        "Age ≥65 years",
        "Female",
    ]
    assert layout_sidecar["metrics"]["subgroup_reference_value"] == 0.80
    assert layout_sidecar["metrics"]["legend_labels"] == ["Locked model", "Derivation cohort"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "legend" for box in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_compact_effect_estimate_panel_preserves_ch_bounded_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure46",
                    "display_kind": "figure",
                    "requirement_key": "compact_effect_estimate_panel",
                    "catalog_id": "F46",
                    "shell_path": "paper/figures/Figure46.shell.json",
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
                    "display_id": "Figure46",
                    "template_id": "compact_effect_estimate_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "compact_effect_estimate_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "compact_effect_estimate_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure46",
                    "template_id": "fenggaolab.org.medical-display-core::compact_effect_estimate_panel",
                    "title": "Compact effect estimate panel for prespecified heterogeneity review",
                    "caption": "Regression lock for bounded multi-panel effect-estimate evidence.",
                    "x_label": "Hazard ratio",
                    "reference_value": 1.0,
                    "panels": [
                        {
                            "panel_id": "overall",
                            "panel_label": "A",
                            "title": "Overall cohort",
                            "rows": [
                                {
                                    "row_id": "age_ge_65",
                                    "row_label": "Age ≥65 years",
                                    "support_n": 184,
                                    "estimate": 1.18,
                                    "lower": 1.04,
                                    "upper": 1.34,
                                },
                                {
                                    "row_id": "female",
                                    "row_label": "Female",
                                    "support_n": 201,
                                    "estimate": 1.26,
                                    "lower": 1.10,
                                    "upper": 1.44,
                                },
                            ],
                        },
                        {
                            "panel_id": "adjusted",
                            "panel_label": "B",
                            "title": "Covariate-adjusted model",
                            "rows": [
                                {
                                    "row_id": "age_ge_65",
                                    "row_label": "Age ≥65 years",
                                    "support_n": 184,
                                    "estimate": 1.11,
                                    "lower": 0.98,
                                    "upper": 1.28,
                                },
                                {
                                    "row_id": "female",
                                    "row_label": "Female",
                                    "support_n": 201,
                                    "estimate": 1.22,
                                    "lower": 1.05,
                                    "upper": 1.40,
                                },
                            ],
                        },
                        {
                            "panel_id": "sensitivity",
                            "panel_label": "C",
                            "title": "Sensitivity analysis",
                            "rows": [
                                {
                                    "row_id": "age_ge_65",
                                    "row_label": "Age ≥65 years",
                                    "support_n": 184,
                                    "estimate": 1.09,
                                    "lower": 0.95,
                                    "upper": 1.25,
                                },
                                {
                                    "row_id": "female",
                                    "row_label": "Female",
                                    "support_n": 201,
                                    "estimate": 1.18,
                                    "lower": 1.01,
                                    "upper": 1.37,
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
        (paper_root / "figures" / "generated" / "F46_compact_effect_estimate_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["panel_id"] for item in layout_sidecar["metrics"]["panels"]] == [
        "overall",
        "adjusted",
        "sensitivity",
    ]
    assert [item["row_id"] for item in layout_sidecar["metrics"]["panels"][0]["rows"]] == [
        "age_ge_65",
        "female",
    ]
    assert [item["row_id"] for item in layout_sidecar["metrics"]["panels"][1]["rows"]] == [
        "age_ge_65",
        "female",
    ]
    assert layout_sidecar["metrics"]["reference_value"] == 1.0
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "reference_line"]) == 3

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_baseline_missingness_qc_panel_preserves_h_bounded_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure44",
                    "display_kind": "figure",
                    "requirement_key": "baseline_missingness_qc_panel",
                    "catalog_id": "F44",
                    "shell_path": "paper/figures/Figure44.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "baseline_missingness_qc_panel.json",
        {
            "schema_version": 1,
            "shell_id": "fenggaolab.org.medical-display-core::baseline_missingness_qc_panel",
            "display_id": "Figure44",
            "title": "Baseline balance, missingness, and QC overview",
            "caption": "Regression lock for bounded cohort-quality evidence.",
            "balance_panel_title": "Baseline balance",
            "balance_x_label": "Absolute standardized mean difference",
            "balance_threshold": 0.10,
            "primary_balance_label": "Pre-adjustment SMD",
            "secondary_balance_label": "Post-adjustment SMD",
            "balance_variables": [
                {"variable_id": "age", "label": "Age", "primary_value": 0.24, "secondary_value": 0.08},
                {"variable_id": "sex", "label": "Female sex", "primary_value": 0.11, "secondary_value": 0.04},
                {"variable_id": "tumor_size", "label": "Tumor size", "primary_value": 0.19, "secondary_value": 0.07},
            ],
            "missingness_panel_title": "Missingness map",
            "missingness_x_label": "Dataset split",
            "missingness_y_label": "Variable",
            "missingness_rows": [{"label": "Age"}, {"label": "HbA1c"}, {"label": "BMI"}],
            "missingness_columns": [{"label": "Train"}, {"label": "Validation"}, {"label": "External"}],
            "missingness_cells": [
                {"x": "Train", "y": "Age", "value": 0.01},
                {"x": "Validation", "y": "Age", "value": 0.03},
                {"x": "External", "y": "Age", "value": 0.04},
                {"x": "Train", "y": "HbA1c", "value": 0.08},
                {"x": "Validation", "y": "HbA1c", "value": 0.10},
                {"x": "External", "y": "HbA1c", "value": 0.13},
                {"x": "Train", "y": "BMI", "value": 0.05},
                {"x": "Validation", "y": "BMI", "value": 0.06},
                {"x": "External", "y": "BMI", "value": 0.09},
            ],
            "qc_panel_title": "QC summary",
            "qc_cards": [
                {"card_id": "retained", "label": "Retained", "value": "92%", "detail": "1,284 / 1,396 records"},
                {"card_id": "max_missing", "label": "Max missing", "value": "13%", "detail": "HbA1c in external cohort"},
                {"card_id": "batch", "label": "QC batches", "value": "3", "detail": "No site failed pre-specified checks"},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F44_baseline_missingness_qc_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["label"] for item in layout_sidecar["metrics"]["missingness_rows"]] == ["Age", "HbA1c", "BMI"]
    assert [item["label"] for item in layout_sidecar["metrics"]["missingness_columns"]] == [
        "Train",
        "Validation",
        "External",
    ]
    assert layout_sidecar["metrics"]["balance_threshold"] == 0.10
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
