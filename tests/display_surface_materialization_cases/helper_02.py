from __future__ import annotations

from . import shared_base as _shared_base
from . import helper_01 as _helper_prev
from .registry_builders import _build_workspace_registry_displays, _workspace_template_bindings

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_helper_prev)

def build_display_surface_workspace(
    tmp_path: Path,
    *,
    include_evidence: bool = False,
    include_extended_evidence: bool = False,
) -> Path:
    paper_root = tmp_path / "paper"
    include_evidence = include_evidence or include_extended_evidence
    displays = _build_workspace_registry_displays(
        include_evidence=include_evidence,
        include_extended_evidence=include_extended_evidence,
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
        for figure_index, template_id in _workspace_template_bindings(include_extended_evidence):
            dump_json(
                paper_root / "figures" / f"Figure{figure_index}.shell.json",
                {
                    "schema_version": 1,
                    "display_id": f"Figure{figure_index}",
                    "display_kind": "figure",
                    "requirement_key": template_id,
                },
            )
    if include_extended_evidence:
        for table_index, requirement_key in (
            (2, "table2_time_to_event_performance_summary"),
            (3, "table3_clinical_interpretation_summary"),
        ):
            dump_json(
                paper_root / "tables" / f"Table{table_index}.shell.json",
                {
                    "schema_version": 1,
                    "display_id": f"Table{table_index}",
                    "display_kind": "table",
                    "requirement_key": requirement_key,
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
                    {
                        "display_id": "Figure18",
                        "template_id": "time_dependent_roc_horizon",
                        "title": "Time-dependent ROC at 24 months",
                        "caption": "Horizon-specific discrimination of the locked survival model at 24 months.",
                        "time_horizon_months": 24,
                        "x_label": "1 - Specificity",
                        "y_label": "Sensitivity",
                        "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0], "label": "Chance"},
                        "series": [
                            {
                                "label": "24-month horizon",
                                "x": [0.0, 0.12, 0.28, 1.0],
                                "y": [0.0, 0.69, 0.84, 1.0],
                                "annotation": "AUC = 0.81",
                            }
                        ],
                    },
                    {
                        "display_id": "Figure22",
                        "template_id": "clinical_impact_curve_binary",
                        "title": "Clinical impact curve for the primary model",
                        "caption": "Estimated numbers of high-risk and event-positive patients across decision thresholds.",
                        "x_label": "Threshold probability",
                        "y_label": "Patients per 100",
                        "reference_line": {"x": [0.05, 0.40], "y": [18.0, 18.0], "label": "Observed events"},
                        "series": [
                            {
                                "label": "High risk",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40],
                                "y": [54.0, 43.0, 28.0, 16.0, 9.0],
                                "annotation": "Predicted high risk",
                            },
                            {
                                "label": "Event positive",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40],
                                "y": [18.0, 17.0, 14.0, 10.0, 7.0],
                                "annotation": "Observed events",
                            },
                        ],
                    },
                ],
            },
        )
        time_to_event_grouped_displays = [
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
            },
            {
                "display_id": "Figure7",
                "template_id": "cumulative_incidence_grouped",
                "title": "Cumulative incidence by risk group",
                "caption": "Event accumulation across prespecified risk strata.",
                "x_label": "Months from surgery",
                "y_label": "Cumulative incidence",
                "groups": [
                    {
                        "label": "Low risk",
                        "times": [0, 6, 12, 18, 24],
                        "values": [0.00, 0.04, 0.07, 0.09, 0.12],
                    },
                    {
                        "label": "High risk",
                        "times": [0, 6, 12, 18, 24],
                        "values": [0.00, 0.12, 0.23, 0.31, 0.38],
                    },
                ],
                "annotation": "Gray test P = .002",
            },
        ]
        if include_extended_evidence:
            time_to_event_grouped_displays.append(
                {
                    "display_id": "Figure15",
                    "template_id": "time_to_event_risk_group_summary",
                    "title": "Risk-group summary across follow-up horizons",
                    "caption": "Grouped event trajectories and retained cohort size across follow-up horizons.",
                    "panel_a_title": "Predicted and observed risk by tertile",
                    "panel_b_title": "Observed events by tertile",
                    "x_label": "Risk tertile",
                    "y_label": "5-year risk (%)",
                    "event_count_y_label": "Observed 5-year events",
                    "risk_group_summaries": [
                        {
                            "label": "Low risk",
                            "sample_size": 72,
                            "events_5y": 4,
                            "mean_predicted_risk_5y": 0.08,
                            "observed_km_risk_5y": 0.06,
                        },
                        {
                            "label": "Intermediate risk",
                            "sample_size": 65,
                            "events_5y": 11,
                            "mean_predicted_risk_5y": 0.17,
                            "observed_km_risk_5y": 0.18,
                        },
                        {
                            "label": "High risk",
                            "sample_size": 48,
                            "events_5y": 19,
                            "mean_predicted_risk_5y": 0.31,
                            "observed_km_risk_5y": 0.35,
                        },
                    ],
                }
            )
        dump_json(
            paper_root / "time_to_event_grouped_inputs.json",
            {
                "schema_version": 1,
                "input_schema_id": "time_to_event_grouped_inputs_v1",
                "displays": time_to_event_grouped_displays,
            },
        )
        if include_extended_evidence:
            dump_json(
                paper_root / "embedding_grouped_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "embedding_grouped_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure8",
                            "template_id": "umap_scatter_grouped",
                            "title": "UMAP embedding by subtype",
                            "caption": "Two-dimensional manifold embedding with subtype labels.",
                            "x_label": "UMAP 1",
                            "y_label": "UMAP 2",
                            "points": [
                                {"x": -2.1, "y": 1.2, "group": "Subtype A"},
                                {"x": -1.7, "y": 1.0, "group": "Subtype A"},
                                {"x": 1.4, "y": -0.8, "group": "Subtype B"},
                                {"x": 1.8, "y": -1.1, "group": "Subtype B"},
                            ],
                        },
                        {
                            "display_id": "Figure9",
                            "template_id": "pca_scatter_grouped",
                            "title": "PCA embedding by subtype",
                            "caption": "Principal component separation across latent subgroups.",
                            "x_label": "PC1",
                            "y_label": "PC2",
                            "points": [
                                {"x": -1.2, "y": 0.6, "group": "Subtype A"},
                                {"x": -0.9, "y": 0.4, "group": "Subtype A"},
                                {"x": 0.8, "y": -0.5, "group": "Subtype B"},
                                {"x": 1.1, "y": -0.7, "group": "Subtype B"},
                            ],
                        },
                        {
                            "display_id": "Figure19",
                            "template_id": "tsne_scatter_grouped",
                            "title": "t-SNE embedding by subtype",
                            "caption": "Local neighborhood preservation across latent subgroups.",
                            "x_label": "t-SNE 1",
                            "y_label": "t-SNE 2",
                            "points": [
                                {"x": -14.2, "y": 9.1, "group": "Subtype A"},
                                {"x": -12.8, "y": 8.5, "group": "Subtype A"},
                                {"x": 11.3, "y": -7.6, "group": "Subtype B"},
                                {"x": 12.7, "y": -8.9, "group": "Subtype B"},
                            ],
                        },
                        {
                            "display_id": "Figure24",
                            "template_id": "phate_scatter_grouped",
                            "title": "PHATE embedding by subtype",
                            "caption": "Diffusion-based manifold projection across latent subgroups.",
                            "x_label": "PHATE 1",
                            "y_label": "PHATE 2",
                            "points": [
                                {"x": -4.6, "y": 3.8, "group": "Subtype A"},
                                {"x": -4.1, "y": 3.4, "group": "Subtype A"},
                                {"x": 4.4, "y": -3.3, "group": "Subtype B"},
                                {"x": 4.9, "y": -3.8, "group": "Subtype B"},
                            ],
                        },
                        {
                            "display_id": "Figure25",
                            "template_id": "diffusion_map_scatter_grouped",
                            "title": "Diffusion map embedding by subtype",
                            "caption": "Diffusion map separates subtype manifolds along smooth latent trajectories.",
                            "x_label": "Diffusion component 1",
                            "y_label": "Diffusion component 2",
                            "points": [
                                {"x": -0.42, "y": 0.31, "group": "Subtype A"},
                                {"x": -0.35, "y": 0.28, "group": "Subtype A"},
                                {"x": 0.33, "y": -0.24, "group": "Subtype B"},
                                {"x": 0.4, "y": -0.29, "group": "Subtype B"},
                            ],
                        },
                    ],
                },
            )
            dump_json(
                paper_root / "heatmap_group_comparison_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "heatmap_group_comparison_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure10",
                            "template_id": "heatmap_group_comparison",
                            "title": "Group comparison heatmap",
                            "caption": "Standardized feature contrast across prespecified groups.",
                            "x_label": "Group",
                            "y_label": "Feature",
                            "cells": [
                                {"x": "Low risk", "y": "Age", "value": -0.6},
                                {"x": "High risk", "y": "Age", "value": 0.7},
                                {"x": "Low risk", "y": "Tumor size", "value": -0.4},
                                {"x": "High risk", "y": "Tumor size", "value": 0.8},
                            ],
                        }
                    ],
                },
            )
            dump_json(
                paper_root / "correlation_heatmap_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "correlation_heatmap_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure11",
                            "template_id": "correlation_heatmap",
                            "title": "Correlation heatmap",
                            "caption": "Pairwise correlation structure across core predictors.",
                            "x_label": "Variable",
                            "y_label": "Variable",
                            "cells": [
                                {"x": "Age", "y": "Age", "value": 1.0},
                                {"x": "Age", "y": "Tumor size", "value": 0.34},
                                {"x": "Tumor size", "y": "Age", "value": 0.34},
                                {"x": "Tumor size", "y": "Tumor size", "value": 1.0},
                            ],
                        }
                    ],
                },
            )
            dump_json(
                paper_root / "clustered_heatmap_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "clustered_heatmap_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure21",
                            "template_id": "clustered_heatmap",
                            "title": "Clustered heatmap",
                            "caption": "Heatmap rendered from an externally fixed row and column clustering order.",
                            "x_label": "Patient subgroup",
                            "y_label": "Feature",
                            "row_order": [
                                {"label": "Ki-67"},
                                {"label": "Tumor size"},
                                {"label": "Age"},
                            ],
                            "column_order": [
                                {"label": "Cluster A"},
                                {"label": "Cluster B"},
                            ],
                            "cells": [
                                {"x": "Cluster A", "y": "Ki-67", "value": 0.82},
                                {"x": "Cluster B", "y": "Ki-67", "value": -0.14},
                                {"x": "Cluster A", "y": "Tumor size", "value": 0.56},
                                {"x": "Cluster B", "y": "Tumor size", "value": 0.08},
                                {"x": "Cluster A", "y": "Age", "value": -0.22},
                                {"x": "Cluster B", "y": "Age", "value": 0.63},
                            ],
                        }
                    ],
                },
            )
            dump_json(
                paper_root / "forest_effect_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "forest_effect_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure12",
                            "template_id": "forest_effect_main",
                            "title": "Main-effect forest plot",
                            "caption": "Adjusted effect estimates for prespecified predictors.",
                            "x_label": "Odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age > 60 years", "estimate": 1.42, "lower": 1.11, "upper": 1.83},
                                {"label": "Tumor size > 30 mm", "estimate": 1.89, "lower": 1.35, "upper": 2.62},
                            ],
                        },
                        {
                            "display_id": "Figure20",
                            "template_id": "subgroup_forest",
                            "title": "Subgroup forest plot",
                            "caption": "Effect heterogeneity across clinically prespecified subgroups.",
                            "x_label": "Hazard ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Female", "estimate": 0.88, "lower": 0.71, "upper": 1.08},
                                {"label": "Age > 60 years", "estimate": 1.21, "lower": 0.98, "upper": 1.49},
                                {"label": "Macroadenoma", "estimate": 1.36, "lower": 1.08, "upper": 1.72},
                            ],
                        },
                        {
                            "display_id": "Figure23",
                            "template_id": "multivariable_forest",
                            "title": "Multivariable model forest plot",
                            "caption": "Adjusted odds ratios from the locked multivariable model.",
                            "x_label": "Adjusted odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age > 60 years", "estimate": 1.48, "lower": 1.16, "upper": 1.89},
                                {"label": "HbA1c > 8%", "estimate": 1.72, "lower": 1.29, "upper": 2.29},
                                {"label": "Albuminuria", "estimate": 1.63, "lower": 1.21, "upper": 2.18},
                            ],
                        },
                    ],
                },
            )
            dump_json(
                paper_root / "shap_summary_inputs.json",
                {
                    "schema_version": 1,
                    "input_schema_id": "shap_summary_inputs_v1",
                    "displays": [
                        {
                            "display_id": "Figure13",
                            "template_id": "shap_summary_beeswarm",
                            "title": "SHAP summary beeswarm",
                            "caption": "Feature-level SHAP distribution ranked by mean absolute contribution.",
                            "x_label": "SHAP value",
                            "rows": [
                                {
                                    "feature": "Tumor size",
                                    "points": [
                                        {"shap_value": -0.42, "feature_value": 0.15},
                                        {"shap_value": 0.31, "feature_value": 0.83},
                                    ],
                                },
                                {
                                    "feature": "Age",
                                    "points": [
                                        {"shap_value": -0.18, "feature_value": 0.28},
                                        {"shap_value": 0.22, "feature_value": 0.74},
                                    ],
                                },
                            ],
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
                            "display_id": "Figure14",
                            "template_id": "time_to_event_discrimination_calibration_panel",
                            "title": "Time-to-event discrimination and grouped calibration",
                            "caption": "Validation discrimination and grouped 5-year calibration for the locked survival model.",
                            "panel_a_title": "Validation discrimination",
                            "panel_b_title": "Grouped 5-year calibration",
                            "discrimination_x_label": "Validation C-index",
                            "calibration_x_label": "Risk decile",
                            "calibration_y_label": "5-year risk (%)",
                            "discrimination_points": [
                                {
                                    "label": "Ridge Cox",
                                    "c_index": 0.83,
                                    "annotation": "0.830",
                                },
                                {
                                    "label": "Lasso Cox",
                                    "c_index": 0.79,
                                    "annotation": "0.790",
                                },
                            ],
                            "calibration_summary": [
                                {
                                    "group_label": "Decile 1",
                                    "group_order": 1,
                                    "n": 60,
                                    "events_5y": 1,
                                    "predicted_risk_5y": 0.012,
                                    "observed_risk_5y": 0.010,
                                },
                                {
                                    "group_label": "Decile 5",
                                    "group_order": 5,
                                    "n": 60,
                                    "events_5y": 3,
                                    "predicted_risk_5y": 0.026,
                                    "observed_risk_5y": 0.032,
                                },
                                {
                                    "group_label": "Decile 10",
                                    "group_order": 10,
                                    "n": 60,
                                    "events_5y": 8,
                                    "predicted_risk_5y": 0.051,
                                    "observed_risk_5y": 0.074,
                                },
                            ],
                            "calibration_callout": {
                                "group_label": "Decile 10",
                                "predicted_risk_5y": 0.051,
                                "observed_risk_5y": 0.074,
                                "events_5y": 8,
                                "n": 60,
                            },
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
                            "display_id": "Figure16",
                            "template_id": "time_to_event_decision_curve",
                            "title": "Time-to-event decision curve at 24 months",
                            "caption": "Net benefit for the survival model at the 24-month clinical decision horizon.",
                            "time_horizon_months": 24,
                            "panel_a_title": "Decision-curve net benefit",
                            "panel_b_title": "Model-treated fraction",
                            "x_label": "Threshold probability",
                            "y_label": "Net benefit",
                            "treated_fraction_y_label": "Patients classified above threshold (%)",
                            "reference_line": {
                                "x": [0.05, 0.45],
                                "y": [0.0, 0.0],
                                "label": "Treat none",
                            },
                            "series": [
                                {
                                    "label": "Locked survival model",
                                    "x": [0.05, 0.10, 0.20, 0.30, 0.40, 0.45],
                                    "y": [0.18, 0.17, 0.15, 0.12, 0.08, 0.05],
                                    "annotation": "24-month horizon",
                                },
                                {
                                    "label": "Treat all",
                                    "x": [0.05, 0.10, 0.20, 0.30, 0.40, 0.45],
                                    "y": [0.15, 0.12, 0.08, 0.03, -0.01, -0.04],
                                    "annotation": "Treat all",
                                },
                            ],
                            "treated_fraction_series": {
                                "label": "Locked survival model",
                                "x": [0.05, 0.10, 0.20, 0.30, 0.40, 0.45],
                                "y": [62.0, 49.0, 31.0, 18.0, 9.0, 6.0],
                            },
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
                            "display_id": "Figure17",
                            "template_id": "multicenter_generalizability_overview",
                            "title": "Multicenter generalizability overview",
                            "caption": "Center-level event support with coverage context under the frozen split.",
                            "overview_mode": "center_support_counts",
                            "center_event_y_label": "5-year CVD events",
                            "coverage_y_label": "Patient count",
                            "center_event_counts": [
                                {
                                    "center_label": "Center A",
                                    "split_bucket": "train",
                                    "event_count": 7,
                                },
                                {
                                    "center_label": "Center B",
                                    "split_bucket": "validation",
                                    "event_count": 5,
                                },
                                {
                                    "center_label": "Center C",
                                    "split_bucket": "train",
                                    "event_count": 3,
                                },
                            ],
                            "coverage_panels": [
                                {
                                    "panel_id": "region",
                                    "title": "Region coverage (n=198)",
                                    "layout_role": "wide_left",
                                    "bars": [
                                        {"label": "Central", "count": 72},
                                        {"label": "East", "count": 54},
                                        {"label": "South", "count": 43},
                                        {"label": "North", "count": 29},
                                    ],
                                },
                                {
                                    "panel_id": "north_south",
                                    "title": "North vs South coverage",
                                    "layout_role": "top_right",
                                    "bars": [
                                        {"label": "North", "count": 84},
                                        {"label": "South", "count": 114},
                                    ],
                                },
                                {
                                    "panel_id": "urban_rural",
                                    "title": "Urban/rural coverage",
                                    "layout_role": "bottom_right",
                                    "bars": [
                                        {"label": "Urban", "count": 101},
                                        {"label": "Rural", "count": 63},
                                        {"label": "Missing", "count": 34},
                                    ],
                                },
                            ],
                            "footnote": "Train and validation centers remain balanced, but sparse center-level events limit transportability claims.",
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
    if include_extended_evidence:
        dump_json(
            paper_root / "time_to_event_performance_summary.json",
            {
                "schema_version": 1,
                "table_shell_id": "table2_time_to_event_performance_summary",
                "display_id": "Table2",
                "title": "Time-to-event model performance summary",
                "columns": [
                    {"column_id": "development", "label": "Development"},
                    {"column_id": "external", "label": "External validation"},
                ],
                "rows": [
                    {"row_id": "c_index", "label": "Harrell C-index", "values": ["0.81", "0.77"]},
                    {"row_id": "ibs", "label": "Integrated Brier score", "values": ["0.112", "0.128"]},
                ],
            },
        )
        dump_json(
            paper_root / "clinical_interpretation_summary.json",
            {
                "schema_version": 1,
                "table_shell_id": "table3_clinical_interpretation_summary",
                "display_id": "Table3",
                "title": "Clinical interpretation summary",
                "columns": [
                    {"column_id": "signal", "label": "Observed signal"},
                    {"column_id": "interpretation", "label": "Clinical interpretation"},
                ],
                "rows": [
                    {
                        "row_id": "high_risk",
                        "label": "High-risk subgroup",
                        "values": [
                            "Higher 24-month event burden",
                            "Escalated imaging surveillance after surgery",
                        ],
                    },
                    {
                        "row_id": "low_risk",
                        "label": "Low-risk subgroup",
                        "values": [
                            "Stable event-free course",
                            "Suitable for standard follow-up cadence",
                        ],
                    },
                ],
            },
        )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    return paper_root
