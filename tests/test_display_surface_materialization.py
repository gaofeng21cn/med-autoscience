from __future__ import annotations

import importlib
import json
from pathlib import Path
import re
from typing import Any

import matplotlib.pyplot as plt
import pytest

from med_autoscience import display_registry
from med_autoscience.display_pack_resolver import get_template_short_id


def _canonicalize_registry_id(value: str) -> str:
    normalized = str(value or "").strip()
    if not normalized:
        return normalized
    if display_registry.is_evidence_figure_template(normalized):
        return display_registry.get_evidence_figure_spec(normalized).template_id
    if display_registry.is_illustration_shell(normalized):
        return display_registry.get_illustration_shell_spec(normalized).shell_id
    if display_registry.is_table_shell(normalized):
        return display_registry.get_table_shell_spec(normalized).shell_id
    return normalized


def full_id(value: str) -> str:
    return _canonicalize_registry_id(value)


def _normalize_namespaced_ids(payload: Any) -> Any:
    if isinstance(payload, dict):
        normalized: dict[str, Any] = {}
        for key, value in payload.items():
            normalized_value = _normalize_namespaced_ids(value)
            if key in {"requirement_key", "template_id", "shell_id", "table_shell_id"} and isinstance(
                normalized_value, str
            ):
                normalized_value = _canonicalize_registry_id(normalized_value)
            normalized[key] = normalized_value
        return normalized
    if isinstance(payload, list):
        return [_normalize_namespaced_ids(item) for item in payload]
    return payload


def dump_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    normalized_payload = _normalize_namespaced_ids(payload)
    path.write_text(json.dumps(normalized_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ensure_output_parents(*paths: Path | None) -> None:
    for path in paths:
        if path is None:
            continue
        path.parent.mkdir(parents=True, exist_ok=True)


def extract_svg_font_size(svg_text: str, marker: str) -> float:
    match = re.search(rf"font-size: ([0-9.]+)px;[^>]*>{re.escape(marker)}<", svg_text)
    assert match is not None, f"missing svg text marker: {marker}"
    return float(match.group(1))


def write_default_publication_display_contracts(paper_root: Path) -> None:
    dump_json(
        paper_root / "publication_style_profile.json",
        {
            "schema_version": 1,
            "style_profile_id": "paper_neutral_clinical_v1",
            "palette": {
                "primary": "#245A6B",
                "secondary": "#B89A6D",
                "contrast": "#8B3A3A",
                "neutral": "#6B7280",
                "light": "#E7E1D8",
                "primary_soft": "#EAF2F5",
                "secondary_soft": "#F4EEE5",
                "contrast_soft": "#F7EBEB",
                "audit": "#9E5151",
                "audit_soft": "#FAEFED",
            },
            "semantic_roles": {
                "model_curve": "primary",
                "comparator_curve": "secondary",
                "reference_line": "neutral",
                "highlight_band": "light",
                "flow_main_fill": "light",
                "flow_main_edge": "neutral",
                "flow_exclusion_fill": "audit_soft",
                "flow_exclusion_edge": "audit",
                "flow_primary_fill": "primary_soft",
                "flow_primary_edge": "primary",
                "flow_secondary_fill": "light",
                "flow_secondary_edge": "neutral",
                "flow_context_fill": "contrast_soft",
                "flow_context_edge": "contrast",
                "flow_audit_fill": "audit_soft",
                "flow_audit_edge": "audit",
                "flow_title_text": "neutral",
                "flow_body_text": "neutral",
                "flow_panel_label": "neutral",
                "flow_connector": "neutral",
            },
            "typography": {
                "title_size": 12.5,
                "axis_title_size": 11.0,
                "tick_size": 10.0,
                "panel_label_size": 11.0,
            },
            "stroke": {
                "primary_linewidth": 2.4,
                "secondary_linewidth": 1.9,
                "reference_linewidth": 1.0,
                "marker_size": 4.2,
            },
        },
    )
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [],
        },
    )


def build_display_surface_workspace(
    tmp_path: Path,
    *,
    include_evidence: bool = False,
    include_extended_evidence: bool = False,
) -> Path:
    paper_root = tmp_path / "paper"
    include_evidence = include_evidence or include_extended_evidence
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
    if include_extended_evidence:
        displays.extend(
            [
                {
                    "display_id": "Figure7",
                    "display_kind": "figure",
                    "requirement_key": "cumulative_incidence_grouped",
                    "shell_path": "paper/figures/Figure7.shell.json",
                },
                {
                    "display_id": "Figure8",
                    "display_kind": "figure",
                    "requirement_key": "umap_scatter_grouped",
                    "shell_path": "paper/figures/Figure8.shell.json",
                },
                {
                    "display_id": "Figure9",
                    "display_kind": "figure",
                    "requirement_key": "pca_scatter_grouped",
                    "shell_path": "paper/figures/Figure9.shell.json",
                },
                {
                    "display_id": "Figure10",
                    "display_kind": "figure",
                    "requirement_key": "heatmap_group_comparison",
                    "shell_path": "paper/figures/Figure10.shell.json",
                },
                {
                    "display_id": "Figure11",
                    "display_kind": "figure",
                    "requirement_key": "correlation_heatmap",
                    "shell_path": "paper/figures/Figure11.shell.json",
                },
                {
                    "display_id": "Figure12",
                    "display_kind": "figure",
                    "requirement_key": "forest_effect_main",
                    "shell_path": "paper/figures/Figure12.shell.json",
                },
                {
                    "display_id": "Figure13",
                    "display_kind": "figure",
                    "requirement_key": "shap_summary_beeswarm",
                    "shell_path": "paper/figures/Figure13.shell.json",
                },
                {
                    "display_id": "Figure14",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_discrimination_calibration_panel",
                    "shell_path": "paper/figures/Figure14.shell.json",
                },
                {
                    "display_id": "Figure15",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_risk_group_summary",
                    "shell_path": "paper/figures/Figure15.shell.json",
                },
                {
                    "display_id": "Figure16",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_decision_curve",
                    "shell_path": "paper/figures/Figure16.shell.json",
                },
                {
                    "display_id": "Figure17",
                    "display_kind": "figure",
                    "requirement_key": "multicenter_generalizability_overview",
                    "shell_path": "paper/figures/Figure17.shell.json",
                },
                {
                    "display_id": "Figure18",
                    "display_kind": "figure",
                    "requirement_key": "time_dependent_roc_horizon",
                    "shell_path": "paper/figures/Figure18.shell.json",
                },
                {
                    "display_id": "Figure19",
                    "display_kind": "figure",
                    "requirement_key": "tsne_scatter_grouped",
                    "shell_path": "paper/figures/Figure19.shell.json",
                },
                {
                    "display_id": "Figure20",
                    "display_kind": "figure",
                    "requirement_key": "subgroup_forest",
                    "shell_path": "paper/figures/Figure20.shell.json",
                },
                {
                    "display_id": "Figure21",
                    "display_kind": "figure",
                    "requirement_key": "clustered_heatmap",
                    "shell_path": "paper/figures/Figure21.shell.json",
                },
                {
                    "display_id": "Table2",
                    "display_kind": "table",
                    "requirement_key": "table2_time_to_event_performance_summary",
                    "shell_path": "paper/tables/Table2.shell.json",
                },
                {
                    "display_id": "Table3",
                    "display_kind": "table",
                    "requirement_key": "table3_clinical_interpretation_summary",
                    "shell_path": "paper/tables/Table3.shell.json",
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
        template_bindings = [
            (2, "roc_curve_binary"),
            (3, "pr_curve_binary"),
            (4, "calibration_curve_binary"),
            (5, "decision_curve_binary"),
            (6, "kaplan_meier_grouped"),
        ]
        if include_extended_evidence:
            template_bindings.extend(
                [
                    (7, "cumulative_incidence_grouped"),
                    (8, "umap_scatter_grouped"),
                    (9, "pca_scatter_grouped"),
                    (10, "heatmap_group_comparison"),
                    (11, "correlation_heatmap"),
                    (12, "forest_effect_main"),
                    (13, "shap_summary_beeswarm"),
                    (14, "time_to_event_discrimination_calibration_panel"),
                    (15, "time_to_event_risk_group_summary"),
                    (16, "time_to_event_decision_curve"),
                    (17, "multicenter_generalizability_overview"),
                    (18, "time_dependent_roc_horizon"),
                    (19, "tsne_scatter_grouped"),
                    (20, "subgroup_forest"),
                    (21, "clustered_heatmap"),
                ]
            )
        for figure_index, template_id in template_bindings:
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
                        }
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


def _minimal_layout_sidecar_for_template(template_id: str) -> dict[str, object]:
    template_short_id = get_template_short_id(template_id) if "::" in template_id else template_id
    if template_short_id == "cohort_flow_figure":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.08, "y0": 0.125, "x1": 0.11, "y1": 0.155},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.52, "y0": 0.125, "x1": 0.55, "y1": 0.155},
                {"box_id": "step_screened", "box_type": "main_step", "x0": 0.08, "y0": 0.40, "x1": 0.28, "y1": 0.50},
                {"box_id": "step_included", "box_type": "main_step", "x0": 0.08, "y0": 0.24, "x1": 0.28, "y1": 0.34},
                {"box_id": "exclusion_repeat", "box_type": "exclusion_box", "x0": 0.32, "y0": 0.30, "x1": 0.46, "y1": 0.38},
            ],
            "panel_boxes": [
                {"box_id": "subfigure_panel_A", "box_type": "subfigure_panel", "x0": 0.06, "y0": 0.10, "x1": 0.48, "y1": 0.54},
                {"box_id": "subfigure_panel_B", "box_type": "subfigure_panel", "x0": 0.52, "y0": 0.10, "x1": 0.94, "y1": 0.54},
                {"box_id": "flow_panel", "box_type": "flow_panel", "x0": 0.08, "y0": 0.12, "x1": 0.46, "y1": 0.50},
                {"box_id": "secondary_panel_validation", "box_type": "secondary_panel", "x0": 0.54, "y0": 0.42, "x1": 0.92, "y1": 0.52},
                {"box_id": "secondary_panel_core", "box_type": "secondary_panel", "x0": 0.54, "y0": 0.28, "x1": 0.72, "y1": 0.38},
                {"box_id": "secondary_panel_primary", "box_type": "secondary_panel", "x0": 0.74, "y0": 0.28, "x1": 0.92, "y1": 0.38},
                {"box_id": "secondary_panel_audit", "box_type": "secondary_panel", "x0": 0.54, "y0": 0.14, "x1": 0.72, "y1": 0.24},
                {"box_id": "secondary_panel_context", "box_type": "secondary_panel", "x0": 0.74, "y0": 0.14, "x1": 0.92, "y1": 0.24},
            ],
            "guide_boxes": [
                {"box_id": "flow_spine_screened_to_included", "box_type": "flow_connector", "x0": 0.17, "y0": 0.34, "x1": 0.19, "y1": 0.40},
                {"box_id": "flow_branch_repeat", "box_type": "flow_branch_connector", "x0": 0.19, "y0": 0.33, "x1": 0.32, "y1": 0.35},
                {"box_id": "hierarchy_root_trunk", "box_type": "hierarchy_connector", "x0": 0.72, "y0": 0.38, "x1": 0.74, "y1": 0.42},
                {"box_id": "hierarchy_root_branch", "box_type": "hierarchy_connector", "x0": 0.63, "y0": 0.36, "x1": 0.83, "y1": 0.38},
                {"box_id": "hierarchy_connector_left_middle_to_left_bottom", "box_type": "hierarchy_connector", "x0": 0.63, "y0": 0.24, "x1": 0.65, "y1": 0.28},
                {"box_id": "hierarchy_connector_right_middle_to_right_bottom", "box_type": "hierarchy_connector", "x0": 0.83, "y0": 0.24, "x1": 0.85, "y1": 0.28},
            ],
            "metrics": {
                "steps": [
                    {"step_id": "screened"},
                    {"step_id": "included"},
                ],
                "exclusions": [
                    {"exclusion_id": "repeat", "from_step_id": "screened"},
                ],
                "endpoint_inventory": [],
                "design_panels": [
                    {"panel_id": "validation", "layout_role": "wide_top"},
                    {"panel_id": "core", "layout_role": "left_middle"},
                    {"panel_id": "primary", "layout_role": "right_middle"},
                    {"panel_id": "audit", "layout_role": "left_bottom"},
                    {"panel_id": "context", "layout_role": "right_bottom"},
                ],
                "flow_nodes": [
                    {
                        "box_id": "step_screened",
                        "box_type": "main_step",
                        "line_count": 3,
                        "max_line_chars": 24,
                        "rendered_height_pt": 92.0,
                        "rendered_width_pt": 218.0,
                        "padding_pt": 9.0,
                    },
                    {
                        "box_id": "step_included",
                        "box_type": "main_step",
                        "line_count": 3,
                        "max_line_chars": 26,
                        "rendered_height_pt": 92.0,
                        "rendered_width_pt": 218.0,
                        "padding_pt": 9.0,
                    },
                    {
                        "box_id": "exclusion_repeat",
                        "box_type": "exclusion_box",
                        "line_count": 2,
                        "max_line_chars": 20,
                        "rendered_height_pt": 62.0,
                        "rendered_width_pt": 176.0,
                        "padding_pt": 8.0,
                    },
                ],
            },
        }
    if template_short_id == "submission_graphical_abstract":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.70, "y1": 0.08},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.05, "y0": 0.18, "x1": 0.08, "y1": 0.22},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.38, "y0": 0.18, "x1": 0.41, "y1": 0.22},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.71, "y0": 0.18, "x1": 0.74, "y1": 0.22},
                {"box_id": "panel_a_title", "box_type": "panel_title", "x0": 0.09, "y0": 0.12, "x1": 0.26, "y1": 0.16},
                {"box_id": "panel_a_subtitle", "box_type": "panel_subtitle", "x0": 0.09, "y0": 0.16, "x1": 0.27, "y1": 0.18},
                {"box_id": "panel_b_title", "box_type": "panel_title", "x0": 0.42, "y0": 0.12, "x1": 0.58, "y1": 0.16},
                {"box_id": "panel_b_subtitle", "box_type": "panel_subtitle", "x0": 0.42, "y0": 0.16, "x1": 0.58, "y1": 0.18},
                {"box_id": "panel_c_title", "box_type": "panel_title", "x0": 0.75, "y0": 0.12, "x1": 0.90, "y1": 0.16},
                {"box_id": "panel_c_subtitle", "box_type": "panel_subtitle", "x0": 0.75, "y0": 0.16, "x1": 0.92, "y1": 0.18},
                {"box_id": "panel_a_card_1", "box_type": "card_box", "x0": 0.08, "y0": 0.24, "x1": 0.28, "y1": 0.40},
                {"box_id": "panel_a_card_2", "box_type": "card_box", "x0": 0.08, "y0": 0.44, "x1": 0.18, "y1": 0.58},
                {"box_id": "panel_a_card_3", "box_type": "card_box", "x0": 0.19, "y0": 0.44, "x1": 0.28, "y1": 0.58},
                {"box_id": "panel_b_card_1", "box_type": "card_box", "x0": 0.41, "y0": 0.24, "x1": 0.61, "y1": 0.40},
                {"box_id": "panel_b_card_2", "box_type": "card_box", "x0": 0.41, "y0": 0.44, "x1": 0.61, "y1": 0.58},
                {"box_id": "panel_c_card_1", "box_type": "card_box", "x0": 0.74, "y0": 0.24, "x1": 0.94, "y1": 0.40},
                {"box_id": "panel_c_card_2", "box_type": "card_box", "x0": 0.74, "y0": 0.44, "x1": 0.83, "y1": 0.58},
                {"box_id": "panel_c_card_3", "box_type": "card_box", "x0": 0.85, "y0": 0.44, "x1": 0.94, "y1": 0.58},
                {"box_id": "panel_a_card_1_title", "box_type": "card_title", "x0": 0.10, "y0": 0.25, "x1": 0.22, "y1": 0.28},
                {"box_id": "panel_a_card_1_value", "box_type": "card_value", "x0": 0.10, "y0": 0.30, "x1": 0.20, "y1": 0.36},
                {"box_id": "panel_a_card_1_detail", "box_type": "card_detail", "x0": 0.10, "y0": 0.36, "x1": 0.24, "y1": 0.39},
                {"box_id": "panel_b_card_1_title", "box_type": "card_title", "x0": 0.43, "y0": 0.25, "x1": 0.55, "y1": 0.28},
                {"box_id": "panel_b_card_1_value", "box_type": "card_value", "x0": 0.43, "y0": 0.30, "x1": 0.52, "y1": 0.36},
                {"box_id": "panel_b_card_1_detail", "box_type": "card_detail", "x0": 0.43, "y0": 0.36, "x1": 0.59, "y1": 0.39},
                {"box_id": "panel_c_card_1_title", "box_type": "card_title", "x0": 0.76, "y0": 0.25, "x1": 0.90, "y1": 0.28},
                {"box_id": "panel_c_card_1_value", "box_type": "card_value", "x0": 0.76, "y0": 0.30, "x1": 0.86, "y1": 0.36},
                {"box_id": "panel_c_card_1_detail", "box_type": "card_detail", "x0": 0.76, "y0": 0.36, "x1": 0.92, "y1": 0.39},
                {"box_id": "pill_a", "box_type": "footer_pill", "x0": 0.11, "y0": 0.84, "x1": 0.25, "y1": 0.89},
                {"box_id": "pill_b", "box_type": "footer_pill", "x0": 0.44, "y0": 0.84, "x1": 0.58, "y1": 0.89},
                {"box_id": "pill_c", "box_type": "footer_pill", "x0": 0.77, "y0": 0.84, "x1": 0.92, "y1": 0.89},
            ],
            "panel_boxes": [
                {"box_id": "panel_cohort", "box_type": "panel", "x0": 0.04, "y0": 0.10, "x1": 0.30, "y1": 0.80},
                {"box_id": "panel_primary", "box_type": "panel", "x0": 0.37, "y0": 0.10, "x1": 0.63, "y1": 0.80},
                {"box_id": "panel_supportive", "box_type": "panel", "x0": 0.70, "y0": 0.10, "x1": 0.96, "y1": 0.80},
            ],
            "guide_boxes": [
                {"box_id": "arrow_1", "box_type": "arrow_connector", "x0": 0.31, "y0": 0.46, "x1": 0.36, "y1": 0.54},
                {"box_id": "arrow_2", "box_type": "arrow_connector", "x0": 0.64, "y0": 0.46, "x1": 0.69, "y1": 0.54},
            ],
            "metrics": {
                "panels": [
                    {"panel_id": "cohort_split"},
                    {"panel_id": "primary_endpoint"},
                    {"panel_id": "supportive_context"},
                ],
                "footer_pills": [
                    {"pill_id": "p1"},
                    {"pill_id": "p2"},
                    {"pill_id": "p3"},
                ],
            },
        }
    if template_short_id in {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "time_dependent_roc_horizon",
    }:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44},
            ],
            "metrics": {
                "series": [{"label": "Model", "x": [0.0, 0.5, 1.0], "y": [0.0, 0.7, 1.0]}],
                "reference_line": {"x": [0.0, 1.0], "y": [0.0, 1.0]},
            },
        }
    if template_short_id in {"kaplan_meier_grouped", "cumulative_incidence_grouped"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44},
            ],
            "metrics": {
                "groups": [{"label": "Low risk", "times": [0.0, 12.0], "values": [1.0, 0.78]}],
            },
        }
    if template_short_id == "time_to_event_risk_group_summary":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.18, "y0": 0.92, "x1": 0.34, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.20, "x1": 0.06, "y1": 0.72},
                {"box_id": "panel_right_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.60, "y0": 0.92, "x1": 0.76, "y1": 0.97},
                {"box_id": "panel_right_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.50, "y0": 0.20, "x1": 0.54, "y1": 0.72},
                {"box_id": "panel_left_title", "box_type": "panel_title", "x0": 0.16, "y0": 0.11, "x1": 0.34, "y1": 0.15},
                {"box_id": "panel_right_title", "box_type": "panel_title", "x0": 0.58, "y0": 0.11, "x1": 0.80, "y1": 0.15},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.11, "y0": 0.80, "x1": 0.14, "y1": 0.85},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.55, "y0": 0.80, "x1": 0.58, "y1": 0.85},
            ],
            "panel_boxes": [
                {"box_id": "panel_left", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.44, "y1": 0.86},
                {"box_id": "panel_right", "box_type": "panel", "x0": 0.54, "y0": 0.16, "x1": 0.88, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.16, "y0": 0.02, "x1": 0.34, "y1": 0.08},
            ],
            "metrics": {
                "risk_group_summaries": [
                    {
                        "label": "Low risk",
                        "sample_size": 72,
                        "events_5y": 4,
                        "mean_predicted_risk_5y": 0.08,
                        "observed_km_risk_5y": 0.06,
                    },
                    {
                        "label": "High risk",
                        "sample_size": 48,
                        "events_5y": 19,
                        "mean_predicted_risk_5y": 0.31,
                        "observed_km_risk_5y": 0.35,
                    },
                ],
            },
        }
    if template_short_id == "time_to_event_discrimination_calibration_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.12, "y0": 0.02, "x1": 0.62, "y1": 0.08},
                {"box_id": "panel_left_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.16, "y0": 0.90, "x1": 0.32, "y1": 0.95},
                {"box_id": "panel_left_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
                {"box_id": "panel_left_title", "box_type": "panel_title", "x0": 0.12, "y0": 0.10, "x1": 0.40, "y1": 0.15},
                {"box_id": "calibration_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.62, "y0": 0.90, "x1": 0.78, "y1": 0.95},
                {"box_id": "calibration_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.52, "y0": 0.24, "x1": 0.56, "y1": 0.74},
                {"box_id": "panel_right_title", "box_type": "panel_title", "x0": 0.58, "y0": 0.10, "x1": 0.88, "y1": 0.15},
                {"box_id": "annotation_callout", "box_type": "annotation_block", "x0": 0.66, "y0": 0.02, "x1": 0.94, "y1": 0.08},
                {"box_id": "discrimination_marker_1", "box_type": "metric_marker", "x0": 0.24, "y0": 0.34, "x1": 0.26, "y1": 0.38},
                {"box_id": "discrimination_marker_2", "box_type": "metric_marker", "x0": 0.28, "y0": 0.56, "x1": 0.30, "y1": 0.60},
                {"box_id": "predicted_marker_1", "box_type": "metric_marker", "x0": 0.62, "y0": 0.46, "x1": 0.64, "y1": 0.50},
                {"box_id": "observed_marker_1", "box_type": "metric_marker", "x0": 0.62, "y0": 0.44, "x1": 0.64, "y1": 0.48},
                {"box_id": "predicted_marker_2", "box_type": "metric_marker", "x0": 0.70, "y0": 0.52, "x1": 0.72, "y1": 0.56},
                {"box_id": "observed_marker_2", "box_type": "metric_marker", "x0": 0.70, "y0": 0.55, "x1": 0.72, "y1": 0.59},
            ],
            "panel_boxes": [
                {"box_id": "panel_left", "box_type": "panel", "x0": 0.10, "y0": 0.18, "x1": 0.44, "y1": 0.84},
                {"box_id": "panel_right", "box_type": "panel", "x0": 0.54, "y0": 0.18, "x1": 0.88, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.34, "y0": 0.02, "x1": 0.62, "y1": 0.08},
            ],
            "metrics": {
                "discrimination_points": [
                    {"label": "Ridge Cox", "c_index": 0.83},
                    {"label": "Lasso Cox", "c_index": 0.79},
                ],
                "calibration_summary": [
                    {"group_label": "Decile 1", "group_order": 1, "n": 60, "events_5y": 1, "predicted_risk_5y": 0.012, "observed_risk_5y": 0.010},
                    {"group_label": "Decile 10", "group_order": 10, "n": 60, "events_5y": 8, "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
                ],
                "calibration_callout": {"group_label": "Decile 10", "predicted_risk_5y": 0.051, "observed_risk_5y": 0.074},
            },
        }
    if template_short_id == "time_to_event_decision_curve":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.60, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.16, "y0": 0.92, "x1": 0.34, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.20, "x1": 0.06, "y1": 0.72},
                {"box_id": "panel_right_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.62, "y0": 0.92, "x1": 0.80, "y1": 0.97},
                {"box_id": "panel_right_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.54, "y0": 0.20, "x1": 0.58, "y1": 0.72},
                {"box_id": "panel_left_title", "box_type": "panel_title", "x0": 0.18, "y0": 0.11, "x1": 0.34, "y1": 0.15},
                {"box_id": "panel_right_title", "box_type": "panel_title", "x0": 0.62, "y0": 0.11, "x1": 0.80, "y1": 0.15},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.11, "y0": 0.80, "x1": 0.14, "y1": 0.85},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.57, "y0": 0.80, "x1": 0.60, "y1": 0.85},
            ],
            "panel_boxes": [
                {"box_id": "panel_left", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.44, "y1": 0.86},
                {"box_id": "panel_right", "box_type": "panel", "x0": 0.56, "y0": 0.16, "x1": 0.90, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.34, "y0": 0.02, "x1": 0.66, "y1": 0.08},
            ],
            "metrics": {
                "series": [{"label": "Model", "x": [0.5, 1.0, 2.0], "y": [0.03, 0.02, 0.01]}],
                "reference_line": {"x": [0.5, 2.0], "y": [0.0, 0.0]},
                "treated_fraction_series": {"label": "Model", "x": [0.5, 1.0, 2.0], "y": [40.0, 20.0, 5.0]},
            },
        }
    if template_short_id in {"umap_scatter_grouped", "pca_scatter_grouped", "tsne_scatter_grouped"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.10, "y0": 0.16, "x1": 0.74, "y1": 0.86},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.80, "y0": 0.30, "x1": 0.96, "y1": 0.44},
            ],
            "metrics": {
                "points": [
                    {"x": 0.22, "y": 0.32, "group": "A"},
                    {"x": 0.44, "y": 0.54, "group": "B"},
                ]
            },
        }
    if template_short_id in {"heatmap_group_comparison", "performance_heatmap", "clustered_heatmap", "gsva_ssgsea_heatmap"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.28, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "heatmap_tile_region", "x0": 0.12, "y0": 0.16, "x1": 0.72, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "colorbar", "box_type": "colorbar", "x0": 0.80, "y0": 0.22, "x1": 0.90, "y1": 0.80},
            ],
            "metrics": (
                {"metric_name": "AUC", "matrix_cells": [{"x": "All participants", "y": "Integrated model", "value": 0.83}]}
                if template_short_id == "performance_heatmap"
                else {"score_method": "GSVA"} if template_short_id == "gsva_ssgsea_heatmap" else {}
            ),
        }
    if template_short_id == "correlation_heatmap":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.28, "y0": 0.92, "x1": 0.60, "y1": 0.97},
                {"box_id": "y_axis_title", "box_type": "y_axis_title", "x0": 0.02, "y0": 0.24, "x1": 0.06, "y1": 0.74},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "heatmap_tile_region", "x0": 0.12, "y0": 0.16, "x1": 0.72, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "colorbar", "box_type": "colorbar", "x0": 0.80, "y0": 0.22, "x1": 0.90, "y1": 0.80},
            ],
            "metrics": {
                "matrix_cells": [
                    {"x": "A", "y": "A", "value": 1.0},
                    {"x": "A", "y": "B", "value": 0.42},
                    {"x": "B", "y": "A", "value": 0.42},
                    {"x": "B", "y": "B", "value": 1.0},
                ]
            },
        }
    if template_short_id in {"forest_effect_main", "subgroup_forest"}:
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "reference_line", "box_type": "reference_line", "x0": 0.52, "y0": 0.18, "x1": 0.52, "y1": 0.86},
                {"box_id": "row_label_1", "box_type": "row_label", "x0": 0.02, "y0": 0.24, "x1": 0.20, "y1": 0.30},
                {"box_id": "estimate_marker_1", "box_type": "estimate_marker", "x0": 0.62, "y0": 0.25, "x1": 0.64, "y1": 0.29},
                {"box_id": "ci_segment_1", "box_type": "ci_segment", "x0": 0.56, "y0": 0.27, "x1": 0.74, "y1": 0.27},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.28, "y0": 0.16, "x1": 0.80, "y1": 0.88},
            ],
            "guide_boxes": [],
            "metrics": {
                "rows": [{"row_id": "1", "label": "Age >= 60", "lower": 0.90, "estimate": 1.05, "upper": 1.20}],
            },
        }
    if template_short_id == "multicenter_generalizability_overview":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.62, "y1": 0.08},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.09, "y0": 0.47, "x1": 0.12, "y1": 0.51},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.09, "y0": 0.89, "x1": 0.12, "y1": 0.93},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.57, "y0": 0.89, "x1": 0.60, "y1": 0.93},
                {"box_id": "center_event_y_axis_title", "box_type": "y_axis_title", "x0": 0.01, "y0": 0.12, "x1": 0.05, "y1": 0.52},
                {"box_id": "coverage_y_axis_title", "box_type": "y_axis_title", "x0": 0.01, "y0": 0.58, "x1": 0.05, "y1": 0.94},
                {"box_id": "center_event_bar_1", "box_type": "center_event_bar", "x0": 0.08, "y0": 0.14, "x1": 0.20, "y1": 0.52},
                {"box_id": "center_event_bar_2", "box_type": "center_event_bar", "x0": 0.22, "y0": 0.14, "x1": 0.34, "y1": 0.52},
                {"box_id": "coverage_bar_region_1", "box_type": "coverage_bar", "x0": 0.08, "y0": 0.64, "x1": 0.16, "y1": 0.92},
                {"box_id": "coverage_bar_region_2", "box_type": "coverage_bar", "x0": 0.19, "y0": 0.70, "x1": 0.27, "y1": 0.92},
                {"box_id": "coverage_bar_ns_1", "box_type": "coverage_bar", "x0": 0.60, "y0": 0.64, "x1": 0.70, "y1": 0.78},
                {"box_id": "coverage_bar_ns_2", "box_type": "coverage_bar", "x0": 0.74, "y0": 0.58, "x1": 0.84, "y1": 0.78},
                {"box_id": "coverage_bar_ur_1", "box_type": "coverage_bar", "x0": 0.60, "y0": 0.82, "x1": 0.70, "y1": 0.94},
                {"box_id": "coverage_bar_ur_2", "box_type": "coverage_bar", "x0": 0.74, "y0": 0.88, "x1": 0.84, "y1": 0.94},
            ],
            "panel_boxes": [
                {"box_id": "center_event_panel", "box_type": "center_event_panel", "x0": 0.08, "y0": 0.14, "x1": 0.92, "y1": 0.52},
                {"box_id": "coverage_panel_wide_left", "box_type": "coverage_panel", "x0": 0.08, "y0": 0.64, "x1": 0.44, "y1": 0.94},
                {"box_id": "coverage_panel_top_right", "box_type": "coverage_panel", "x0": 0.56, "y0": 0.58, "x1": 0.92, "y1": 0.78},
                {"box_id": "coverage_panel_bottom_right", "box_type": "coverage_panel", "x0": 0.56, "y0": 0.82, "x1": 0.92, "y1": 0.94},
                {"box_id": "coverage_panel_right_stack", "box_type": "coverage_panel", "x0": 0.56, "y0": 0.58, "x1": 0.92, "y1": 0.94},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.40, "y0": 0.02, "x1": 0.60, "y1": 0.08},
            ],
            "metrics": {
                "center_event_counts": [
                    {"center_label": "Center A", "split_bucket": "train", "event_count": 7},
                    {"center_label": "Center B", "split_bucket": "validation", "event_count": 5},
                ],
                "coverage_panels": [
                    {
                        "panel_id": "region",
                        "title": "Region coverage (n=198)",
                        "layout_role": "wide_left",
                        "bars": [{"label": "Central", "count": 72}, {"label": "East", "count": 54}],
                    },
                    {
                        "panel_id": "north_south",
                        "title": "North vs South coverage",
                        "layout_role": "top_right",
                        "bars": [{"label": "North", "count": 84}, {"label": "South", "count": 114}],
                    },
                    {
                        "panel_id": "urban_rural",
                        "title": "Urban/rural coverage",
                        "layout_role": "bottom_right",
                        "bars": [{"label": "Urban", "count": 101}, {"label": "Missing", "count": 34}],
                    },
                ],
                "legend_title": "Split",
                "legend_labels": ["Train", "Validation"],
            },
        }
    if template_short_id == "cohort_flow_figure":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.92, "x1": 0.42, "y1": 0.98},
                {"box_id": "step_screened", "box_type": "main_step", "x0": 0.24, "y0": 0.66, "x1": 0.48, "y1": 0.80},
                {"box_id": "step_included", "box_type": "main_step", "x0": 0.24, "y0": 0.42, "x1": 0.48, "y1": 0.56},
                {"box_id": "endpoint_primary", "box_type": "endpoint_panel", "x0": 0.56, "y0": 0.42, "x1": 0.86, "y1": 0.56},
            ],
            "panel_boxes": [
                {"box_id": "flow_panel", "box_type": "panel", "x0": 0.18, "y0": 0.20, "x1": 0.52, "y1": 0.84},
                {"box_id": "endpoint_panel", "box_type": "panel", "x0": 0.56, "y0": 0.20, "x1": 0.90, "y1": 0.66},
            ],
            "guide_boxes": [
                {"box_id": "connector_1", "box_type": "connector", "x0": 0.36, "y0": 0.56, "x1": 0.36, "y1": 0.66},
                {"box_id": "connector_2", "box_type": "connector", "x0": 0.48, "y0": 0.49, "x1": 0.56, "y1": 0.49},
            ],
            "metrics": {
                "steps": [
                    {"step_id": "screened", "label": "Screened", "n": 10},
                    {"step_id": "included", "label": "Included", "n": 8},
                ],
                "exclusions": [{"label": "Excluded", "n": 2}],
                "endpoint_inventory": [{"endpoint_id": "primary", "label": "Primary endpoint"}],
                "design_panels": [{"panel_id": "primary", "layout_role": "wide_top", "label": "Primary endpoint"}],
            },
        }
    if template_short_id == "submission_graphical_abstract":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.08, "y0": 0.93, "x1": 0.40, "y1": 0.98},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.08, "y0": 0.74, "x1": 0.11, "y1": 0.78},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.39, "y0": 0.74, "x1": 0.42, "y1": 0.78},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.70, "y0": 0.74, "x1": 0.73, "y1": 0.78},
                {"box_id": "panel_A_card_1", "box_type": "card_box", "x0": 0.10, "y0": 0.40, "x1": 0.26, "y1": 0.66},
                {"box_id": "panel_B_card_1", "box_type": "card_box", "x0": 0.41, "y0": 0.40, "x1": 0.57, "y1": 0.66},
                {"box_id": "panel_C_card_1", "box_type": "card_box", "x0": 0.72, "y0": 0.40, "x1": 0.88, "y1": 0.66},
                {"box_id": "footer_pill_train", "box_type": "footer_pill", "x0": 0.12, "y0": 0.08, "x1": 0.24, "y1": 0.14},
                {"box_id": "footer_pill_validation", "box_type": "footer_pill", "x0": 0.43, "y0": 0.08, "x1": 0.60, "y1": 0.14},
            ],
            "panel_boxes": [
                {"box_id": "panel_A", "box_type": "panel", "x0": 0.08, "y0": 0.18, "x1": 0.30, "y1": 0.82},
                {"box_id": "panel_B", "box_type": "panel", "x0": 0.39, "y0": 0.18, "x1": 0.61, "y1": 0.82},
                {"box_id": "panel_C", "box_type": "panel", "x0": 0.70, "y0": 0.18, "x1": 0.92, "y1": 0.82},
            ],
            "guide_boxes": [
                {"box_id": "panel_arrow_1", "box_type": "arrow_connector", "x0": 0.30, "y0": 0.50, "x1": 0.39, "y1": 0.54},
                {"box_id": "panel_arrow_2", "box_type": "arrow_connector", "x0": 0.61, "y0": 0.50, "x1": 0.70, "y1": 0.54},
            ],
            "metrics": {
                "panels": [
                    {"panel_id": "A", "panel_label": "A", "title": "Discovery", "subtitle": "Cohort definition"},
                    {"panel_id": "B", "panel_label": "B", "title": "Modeling", "subtitle": "Risk estimation"},
                    {"panel_id": "C", "panel_label": "C", "title": "Clinical use", "subtitle": "Deployment view"},
                ],
                "footer_pills": [
                    {"pill_id": "train", "panel_id": "A", "label": "Train"},
                    {"pill_id": "validation", "panel_id": "B", "label": "Validation"},
                ],
            },
        }
    if template_short_id == "shap_summary_beeswarm":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.56, "y1": 0.08},
                {"box_id": "x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.92, "x1": 0.62, "y1": 0.97},
                {"box_id": "feature_label_Age", "box_type": "feature_label", "x0": 0.03, "y0": 0.25, "x1": 0.12, "y1": 0.31},
                {"box_id": "feature_label_Ki-67", "box_type": "feature_label", "x0": 0.03, "y0": 0.43, "x1": 0.12, "y1": 0.49},
                {"box_id": "feature_row_Age", "box_type": "feature_row", "x0": 0.14, "y0": 0.24, "x1": 0.76, "y1": 0.36},
                {"box_id": "feature_row_Ki-67", "box_type": "feature_row", "x0": 0.14, "y0": 0.40, "x1": 0.76, "y1": 0.52},
            ],
            "panel_boxes": [
                {"box_id": "panel", "box_type": "panel", "x0": 0.14, "y0": 0.18, "x1": 0.76, "y1": 0.84},
            ],
            "guide_boxes": [
                {"box_id": "zero_line", "box_type": "zero_line", "x0": 0.48, "y0": 0.18, "x1": 0.48, "y1": 0.84},
                {"box_id": "colorbar", "box_type": "colorbar", "x0": 0.82, "y0": 0.22, "x1": 0.90, "y1": 0.80},
            ],
            "metrics": {
                "figure_height_inches": 4.8,
                "figure_width_inches": 7.2,
                "points": [
                    {"row_box_id": "feature_row_Age", "x": 0.42, "y": 0.28},
                    {"row_box_id": "feature_row_Ki-67", "x": 0.58, "y": 0.46},
                ],
                "feature_labels": [
                    {"feature": "Age", "row_box_id": "feature_row_Age", "label_box_id": "feature_label_Age"},
                    {"feature": "Ki-67", "row_box_id": "feature_row_Ki-67", "label_box_id": "feature_label_Ki-67"},
                ],
            },
        }
    raise ValueError(f"unsupported template_id `{template_id}` in test layout sidecar helper")


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
    assert figure_catalog["figures"][0]["template_id"] == full_id("cohort_flow_figure")
    assert figure_catalog["figures"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figure_catalog["figures"][0]["renderer_family"] == "python"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert table_catalog["tables"][0]["table_id"] == "T1"
    assert table_catalog["tables"][0]["table_shell_id"] == full_id("table1_baseline_characteristics")
    assert table_catalog["tables"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert table_catalog["tables"][0]["qc_result"]["status"] == "pass"


def test_materialize_display_surface_uses_pack_runtime_for_cohort_flow_shell(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("cohort_flow_figure"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_cohort_flow_figure",
        lambda **_: (_ for _ in ()).throw(AssertionError("host cohort-flow renderer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("cohort_flow_figure")]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()


def test_materialize_display_surface_uses_pack_runtime_for_r_evidence_template(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "roc_curve",
                    "display_kind": "figure",
                    "requirement_key": "roc_curve_binary",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/Figure2.shell.json",
                }
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
                    "display_id": "roc_curve",
                    "template_id": "roc_curve_binary",
                    "title": "ROC curve",
                    "caption": "Receiver operating characteristic curve.",
                    "x_label": "1 - Specificity",
                    "y_label": "Sensitivity",
                    "series": [
                        {
                            "label": "Model",
                            "x": [0.0, 0.2, 1.0],
                            "y": [0.0, 0.8, 1.0],
                        }
                    ],
                }
            ],
        },
    )
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_evidence_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("roc_curve_binary"):
            return fake_evidence_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_r_evidence_figure",
        lambda **_: (_ for _ in ()).throw(AssertionError("host R evidence renderer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("roc_curve_binary")]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()


def test_materialize_display_surface_writes_display_pack_lock(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)

    module.materialize_display_surface(paper_root=paper_root)

    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    assert lock_payload["schema_version"] == 2
    assert lock_payload["paper_config_present"] is False
    assert lock_payload["enabled_pack_ids"] == ["fenggaolab.org.medical-display-core"]
    assert lock_payload["enabled_packs"][0]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert lock_payload["enabled_packs"][0]["requested_version"] == "0.1.0"
    assert lock_payload["enabled_packs"][0]["declared_in"] == "repo"


def test_materialize_display_surface_uses_paper_pack_override_and_writes_versioned_lock(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "shell_path": "paper/tables/baseline_characteristics.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "tables" / "baseline_characteristics.shell.json",
        {
            "schema_version": 1,
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "all", "label": "All patients"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, y", "values": ["61 (54-68)"]},
            ],
        },
    )

    (paper_root / "display_packs.toml").write_text(
        """
inherit_repo_defaults = true
enabled_packs = ["fenggaolab.org.medical-display-core"]

[[sources]]
kind = "local_dir"
pack_id = "fenggaolab.org.medical-display-core"
path = "paper-display-packs/fenggaolab.org.medical-display-core"
version = "0.2.0"
""".strip()
        + "\n",
        encoding="utf-8",
    )

    pack_root = paper_root / "paper-display-packs" / "fenggaolab.org.medical-display-core"
    (pack_root / "templates" / "table1_baseline_characteristics").mkdir(parents=True)
    (pack_root / "src" / "paper_override_display_core").mkdir(parents=True)
    (pack_root / "display_pack.toml").write_text(
        "\n".join(
            (
                'pack_id = "fenggaolab.org.medical-display-core"',
                'version = "0.2.0"',
                'display_api_version = "1"',
                'default_execution_mode = "python_plugin"',
                'summary = "Paper-local override pack"',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "templates" / "table1_baseline_characteristics" / "template.toml").write_text(
        "\n".join(
            (
                'template_id = "table1_baseline_characteristics"',
                'full_template_id = "fenggaolab.org.medical-display-core::table1_baseline_characteristics"',
                'kind = "table_shell"',
                'display_name = "Baseline characteristics"',
                'paper_family_ids = ["H"]',
                'audit_family = "Publication Shells and Tables"',
                'renderer_family = "n/a"',
                'input_schema_ref = "table1_baseline_characteristics_inputs_v1"',
                'qc_profile_ref = "publication_table_shell"',
                'required_exports = ["md", "csv"]',
                'allowed_paper_roles = ["main_text", "supplementary"]',
                'execution_mode = "python_plugin"',
                'entrypoint = "paper_override_display_core.table_shells:render_table_shell"',
                "paper_proven = true",
            )
        )
        + "\n",
        encoding="utf-8",
    )
    (pack_root / "src" / "paper_override_display_core" / "__init__.py").write_text("", encoding="utf-8")
    (pack_root / "src" / "paper_override_display_core" / "table_shells.py").write_text(
        "\n".join(
            (
                "from __future__ import annotations",
                "",
                "from pathlib import Path",
                "",
                "def render_table_shell(*, template_id: str, payload_path: Path, payload: dict[str, object], output_md_path: Path, output_csv_path: Path | None = None) -> dict[str, str]:",
                "    output_md_path.parent.mkdir(parents=True, exist_ok=True)",
                '    output_md_path.write_text("# Paper override baseline characteristics\\n\\n| Characteristic | Overall |\\n| --- | --- |\\n| Age | 60 |\\n", encoding="utf-8")',
                "    if output_csv_path is not None:",
                '        output_csv_path.write_text("Characteristic,Overall\\nAge,60\\n", encoding="utf-8")',
                '    return {"title": "Paper override baseline characteristics", "caption": "Paper-local override version."}',
            )
        )
        + "\n",
        encoding="utf-8",
    )
    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "Paper override baseline characteristics" in (
        paper_root / "tables" / "generated" / "T1_baseline_characteristics.md"
    ).read_text(encoding="utf-8")

    lock_payload = json.loads((paper_root / "build" / "display_pack_lock.json").read_text(encoding="utf-8"))
    entry = lock_payload["enabled_packs"][0]
    assert lock_payload["paper_config_present"] is True
    assert entry["declared_in"] == "paper"
    assert entry["requested_version"] == "0.2.0"
    assert entry["version"] == "0.2.0"
    assert entry["source_path"] == "paper-display-packs/fenggaolab.org.medical-display-core"


def test_materialize_display_surface_uses_catalog_ids_for_semantic_shell_display_ids(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "cohort_flow",
                    "display_kind": "figure",
                    "requirement_key": "cohort_flow_figure",
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/cohort_flow.shell.json",
                },
                {
                    "display_id": "baseline_characteristics",
                    "display_kind": "table",
                    "requirement_key": "table1_baseline_characteristics",
                    "catalog_id": "T1",
                    "shell_path": "paper/tables/baseline_characteristics.shell.json",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "figures" / "cohort_flow.shell.json",
        {
            "schema_version": 1,
            "display_id": "cohort_flow",
            "display_kind": "figure",
            "requirement_key": "cohort_flow_figure",
            "catalog_id": "F1",
        },
    )
    dump_json(
        paper_root / "tables" / "baseline_characteristics.shell.json",
        {
            "schema_version": 1,
            "display_id": "baseline_characteristics",
            "display_kind": "table",
            "requirement_key": "table1_baseline_characteristics",
            "catalog_id": "T1",
        },
    )
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "cohort_flow",
            "title": "Study cohort flow",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Patients screened",
                    "n": 186,
                }
            ],
        },
    )
    dump_json(
        paper_root / "baseline_characteristics_schema.json",
        {
            "schema_version": 1,
            "table_shell_id": "table1_baseline_characteristics",
            "display_id": "baseline_characteristics",
            "title": "Baseline characteristics",
            "groups": [
                {"group_id": "all", "label": "All patients"},
            ],
            "variables": [
                {"variable_id": "age", "label": "Age, y", "values": ["61 (54-68)"]},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    assert result["tables_materialized"] == ["T1"]
    assert (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").exists()
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["figure_id"] == "F1"
    assert table_catalog["tables"][0]["table_id"] == "T1"


def test_materialize_display_surface_renders_cohort_flow_with_exclusions_and_design_panels(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
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
                    "catalog_id": "F1",
                    "shell_path": "paper/figures/Figure1.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"tables": []})
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Unified study cohort and design shell",
            "steps": [
                {"step_id": "source", "label": "Source records", "n": 409, "detail": "Institutional cohort"},
                {"step_id": "first_surgery", "label": "First-surgery cases", "n": 357},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 357, "detail": "Observed endpoint available"},
            ],
            "exclusions": [
                {
                    "exclusion_id": "repeat_or_salvage",
                    "from_step_id": "source",
                    "label": "Repeat or salvage surgery excluded",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery cohort",
                }
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "main_endpoint",
                    "label": "Early residual / non-GTR",
                    "event_n": 57,
                    "detail": "57 non-GTR vs 300 GTR",
                }
            ],
            "design_panels": [
                {
                    "panel_id": "validation_framework",
                    "title": "Validation framework",
                    "layout_role": "top_right",
                    "lines": [
                        {"label": "Repeated nested validation", "detail": "5 outer folds x 20 repeats; 4-fold inner tuning"}
                    ],
                },
                {
                    "panel_id": "model_hierarchy",
                    "title": "Model hierarchy",
                    "layout_role": "wide_left",
                    "lines": [
                        {"label": "Core preoperative model", "detail": "Confirmed comparator"},
                        {"label": "Clinical utility model", "detail": "Knowledge-guided primary model"},
                    ],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar_path = paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json"
    assert layout_sidecar_path.exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["engine_id"] == "display_layout_qc_v1"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")


def test_materialize_display_surface_renders_exclusion_aware_cohort_flow_shell(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation, exclusions, and study design",
            "caption": "Cohort derivation with explicit exclusion accounting.",
            "steps": [
                {"step_id": "source_total", "label": "Source study records", "n": 409, "detail": "Institutional cleaned cohort"},
                {"step_id": "first_surgery", "label": "First-surgery NF-PitNET cases", "n": 357, "detail": "Primary cohort"},
                {"step_id": "analysis", "label": "Analyzed cohort", "n": 357, "detail": "Observed resection status"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source_total",
                    "label": "Repeat or salvage surgery",
                    "n": 52,
                    "detail": "Excluded before first-surgery cohort lock",
                }
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "non_gtr",
                    "label": "Early residual / non-GTR",
                    "n": 57,
                    "detail": "Primary endpoint",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation_frame",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [
                        {"label": "Repeated nested validation", "detail": "5-fold outer x 20 repeats; 4-fold inner tuning"}
                    ],
                },
                {
                    "block_id": "primary_model",
                    "block_type": "left_bottom",
                    "title": "Primary model",
                    "items": [{"label": "Clinically informed preoperative model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "comparator_model",
                    "block_type": "right_bottom",
                    "title": "Comparator",
                    "items": [{"label": "Preoperative core model", "detail": "Confirmed comparator"}],
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    svg_text = (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").read_text(encoding="utf-8")
    assert "Cohort derivation, exclusions, and study design" not in svg_text
    assert "Repeat or" in svg_text
    assert "salvage" in svg_text
    assert "Endpoint inventory" in svg_text
    assert "Validation framework" in svg_text
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"
    assert qc_result["qc_profile"] == "publication_illustration_flow"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")


def test_materialize_display_surface_accepts_legacy_full_right_sidecar_role(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation and split schema",
            "steps": [
                {"step_id": "source_total", "label": "Source study records", "n": 409, "detail": "Institutional cleaned cohort"},
                {"step_id": "analysis", "label": "Analyzed cohort", "n": 357, "detail": "Observed resection status"},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "non_gtr",
                    "label": "Early residual / non-GTR",
                    "n": 57,
                    "detail": "Primary endpoint",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "split_schema",
                    "block_type": "full_right",
                    "title": "Center-based split schema",
                    "items": [
                        {"label": "Derivation centers", "detail": "n=200"},
                        {"label": "Validation centers", "detail": "n=157"},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8")
    )
    panel_roles = {item["layout_role"] for item in layout_sidecar["metrics"]["design_panels"]}
    assert "wide_top" in panel_roles
    assert "full_right" not in panel_roles


def test_materialize_display_surface_renders_cohort_flow_with_two_subfigure_panels_and_role_aware_grid(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly and analytic design",
            "caption": "Study flow with explicit analytic design hierarchy.",
            "steps": [
                {"step_id": "screened", "label": "Screened records", "n": 409, "detail": "Source population"},
                {"step_id": "included", "label": "Included cohort", "n": 357, "detail": "Primary surgery cases"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Removed before first-surgery cohort lock",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "5-fold outer repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Comparator", "detail": "Confirmed preoperative baseline"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical utility", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology audit", "detail": "Bounded postoperative audit"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Benchmark ceilings", "detail": "Context only"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
    guide_boxes = {item["box_id"]: item for item in layout["guide_boxes"]}

    assert "subfigure_panel_A" in panel_boxes
    assert "subfigure_panel_B" in panel_boxes
    assert "title" not in layout_boxes
    assert "panel_label_A" in layout_boxes
    assert "panel_label_B" in layout_boxes
    assert panel_boxes["secondary_panel_validation"]["x0"] <= panel_boxes["secondary_panel_core"]["x0"]
    assert panel_boxes["secondary_panel_validation"]["x1"] >= panel_boxes["secondary_panel_primary"]["x1"]
    assert panel_boxes["secondary_panel_core"]["x1"] < panel_boxes["secondary_panel_primary"]["x0"]
    assert panel_boxes["secondary_panel_audit"]["x1"] < panel_boxes["secondary_panel_context"]["x0"]
    assert panel_boxes["secondary_panel_core"]["y0"] > panel_boxes["secondary_panel_audit"]["y1"]
    assert "hierarchy_root_trunk" in guide_boxes
    assert "hierarchy_root_branch" in guide_boxes
    assert "hierarchy_connector_left_middle_to_left_bottom" in guide_boxes
    assert "hierarchy_connector_right_middle_to_right_bottom" in guide_boxes


def test_materialize_display_surface_centers_rooted_hierarchy_branch_connectors_on_target_panels(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly and analytic design",
            "caption": "Study flow with explicit analytic design hierarchy.",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Screened institutional NF-PitNET records",
                    "n": 409,
                    "detail": "Source population before first-surgery eligibility filtering",
                },
                {
                    "step_id": "included",
                    "label": "Included: first-surgery NF-PitNET cohort",
                    "n": 357,
                    "detail": "Eligible primary surgery cases",
                },
                {
                    "step_id": "analysis",
                    "label": "Included in final analysis cohort",
                    "n": 357,
                    "detail": "Observed early postoperative MRI-based resection status",
                },
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery analysis cohort",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Repeated nested validation",
                    "items": [{"label": "5-fold outer x 20 repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Preoperative Core Model", "detail": "Confirmed comparator"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical Utility Model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology-Augmented Model", "detail": "Secondary postoperative comparison"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Elastic-Net / Random-Forest", "detail": "Contextual comparison models"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    boxes = {item["box_id"]: item for item in layout["layout_boxes"] + layout["panel_boxes"] + layout["guide_boxes"]}

    def center_x(box: dict[str, float]) -> float:
        return (float(box["x0"]) + float(box["x1"])) / 2.0

    assert abs(center_x(boxes["hierarchy_connector_branch_to_left"]) - center_x(boxes["secondary_panel_core"])) < 0.01
    assert abs(center_x(boxes["hierarchy_connector_branch_to_right"]) - center_x(boxes["secondary_panel_primary"])) < 0.01


def test_materialize_display_surface_uses_readable_card_typography_for_cohort_flow(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly and analytic design",
            "caption": "Study flow with explicit analytic design hierarchy.",
            "steps": [
                {
                    "step_id": "screened",
                    "label": "Screened institutional NF-PitNET records",
                    "n": 409,
                    "detail": "Source population before first-surgery eligibility filtering",
                },
                {
                    "step_id": "included",
                    "label": "Included: first-surgery NF-PitNET cohort",
                    "n": 357,
                    "detail": "Eligible primary surgery cases",
                },
                {
                    "step_id": "analysis",
                    "label": "Included in final analysis cohort",
                    "n": 357,
                    "detail": "Observed early postoperative MRI-based resection status",
                },
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Not eligible for the first-surgery analysis cohort",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Repeated nested validation",
                    "items": [{"label": "5-fold outer x 20 repeats", "detail": "4-fold inner tuning"}],
                },
                {
                    "block_id": "core",
                    "block_type": "left_middle",
                    "title": "Core model",
                    "items": [{"label": "Preoperative Core Model", "detail": "Confirmed comparator"}],
                },
                {
                    "block_id": "primary",
                    "block_type": "right_middle",
                    "title": "Primary model",
                    "items": [{"label": "Clinical Utility Model", "detail": "Knowledge-guided primary model"}],
                },
                {
                    "block_id": "audit",
                    "block_type": "left_bottom",
                    "title": "Secondary model",
                    "items": [{"label": "Pathology-Augmented Model", "detail": "Secondary postoperative comparison"}],
                },
                {
                    "block_id": "context",
                    "block_type": "right_bottom",
                    "title": "Contextual models",
                    "items": [{"label": "Elastic-Net / Random-Forest", "detail": "Contextual comparison models"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    svg_text = (paper_root / "figures" / "generated" / "F1_cohort_flow.svg").read_text(encoding="utf-8")
    assert extract_svg_font_size(svg_text, "Screened institutional NF-PitNET") >= 10.9
    assert extract_svg_font_size(svg_text, "Repeated nested validation") >= 10.5
    assert extract_svg_font_size(svg_text, "Preoperative Core Model") >= 9.3
    assert extract_svg_font_size(svg_text, "5-fold outer x 20 repeats") >= 9.0


def test_materialize_display_surface_anchors_exclusion_branch_to_split_stage(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly with stage-anchored exclusions",
            "steps": [
                {"step_id": "screened", "label": "Screened records", "n": 409, "detail": "Source population"},
                {"step_id": "included", "label": "Included cohort", "n": 357, "detail": "Primary surgery cases"},
                {"step_id": "analysis", "label": "Analysis cohort", "n": 357, "detail": "Observed endpoint"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat",
                    "from_step_id": "screened",
                    "label": "Excluded: repeat/salvage surgery",
                    "n": 52,
                    "detail": "Removed before first-surgery cohort lock",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "5-fold outer repeats", "detail": "4-fold inner tuning"}],
                }
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    layout_boxes = {item["box_id"]: item for item in layout["layout_boxes"]}
    guide_boxes = {item["box_id"]: item for item in layout["guide_boxes"]}
    screened = layout_boxes["step_screened"]
    included = layout_boxes["step_included"]
    analysis = layout_boxes["step_analysis"]
    exclusion = layout_boxes["exclusion_repeat"]
    branch = guide_boxes["flow_branch_repeat"]

    def center_x(box: dict[str, float]) -> float:
        return (float(box["x0"]) + float(box["x1"])) / 2.0

    exclusion_center_y = (float(exclusion["y0"]) + float(exclusion["y1"])) / 2.0
    assert abs(center_x(screened) - center_x(included)) < 0.02
    assert abs(center_x(included) - center_x(analysis)) < 0.02
    assert float(exclusion["x0"]) > float(screened["x1"])
    assert float(included["y1"]) <= exclusion_center_y <= float(screened["y0"])
    assert float(branch["y0"]) >= float(included["y1"])
    assert float(branch["y1"]) <= float(screened["y0"])


def test_materialize_display_surface_renders_sparse_modern_cohort_flow_without_panel_b_overlap(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Sparse modern cohort flow",
            "caption": "Panel B stays hierarchical without overlapping sparse-role cards.",
            "steps": [
                {"step_id": "locked", "label": "Source study records", "n": 409},
                {"step_id": "first_surgery", "label": "First-surgery NF-PitNET cases", "n": 357},
                {"step_id": "analysis", "label": "Analyzed first-surgery cohort", "n": 357},
            ],
            "endpoint_inventory": [
                {
                    "endpoint_id": "early_residual",
                    "label": "Early residual / non-GTR",
                    "detail": "Primary manuscript endpoint",
                    "event_n": 57,
                }
            ],
            "design_panels": [
                {
                    "panel_id": "validation_contract",
                    "layout_role": "wide_top",
                    "style_role": "secondary",
                    "title": "Validation design",
                    "lines": [
                        {
                            "label": "Repeated nested validation",
                            "detail": "20 repeats x 5 outer folds; 4-fold inner tuning",
                        }
                    ],
                },
                {
                    "panel_id": "model_hierarchy",
                    "layout_role": "right_bottom",
                    "style_role": "secondary",
                    "title": "Model comparison frame",
                    "lines": [
                        {"label": "Core preoperative model", "detail": "Confirmed comparator"},
                        {"label": "Clinically informed preoperative model", "detail": "Primary knowledge-guided model"},
                    ],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = figure_catalog["figures"][0]["qc_result"]
    assert qc_result["status"] == "pass"

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    validation_box = panel_boxes["secondary_panel_validation_contract"]
    model_box = panel_boxes["secondary_panel_model_hierarchy"]
    footer_box = panel_boxes["secondary_panel_endpoint_inventory"]

    assert validation_box["y0"] > model_box["y1"]
    assert model_box["y0"] > footer_box["y1"]
    assert validation_box["x0"] < model_box["x1"]
    assert validation_box["x1"] > model_box["x0"]


def test_materialize_display_surface_supports_sparse_wide_bottom_panel_role(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Cohort derivation and score construction",
            "caption": "Sparse modern hierarchy supports a wide-bottom contract block.",
            "steps": [
                {"step_id": "source", "label": "Source cohort", "n": 409, "detail": "Study population"},
                {"step_id": "analysis", "label": "Final analysis cohort", "n": 357, "detail": "Eligible cases"},
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source",
                    "label": "Excluded: repeat or salvage surgery",
                    "n": 52,
                    "detail": "Removed before first-surgery cohort lock",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "Repeated nested validation", "detail": "5-fold outer x 20 repeats; 4-fold inner tuning"}],
                },
                {
                    "block_id": "score_rule",
                    "block_type": "wide_bottom",
                    "title": "Grouped rule",
                    "items": [{"label": "Low / intermediate / high risk", "detail": "Study-defined grouped contract"}],
                },
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    panel_boxes = {item["box_id"]: item for item in layout["panel_boxes"]}
    validation_box = panel_boxes["secondary_panel_validation"]
    bottom_box = panel_boxes["secondary_panel_score_rule"]

    assert validation_box["y0"] > bottom_box["y1"]
    assert validation_box["x0"] < bottom_box["x1"]
    assert validation_box["x1"] > bottom_box["x0"]


def test_materialize_display_surface_records_render_context_for_cohort_flow(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly",
            "steps": [{"step_id": "screened", "label": "Screened", "n": 409, "detail": "Source population"}],
            "sidecar_blocks": [
                {
                    "block_id": "validation",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [{"label": "5-fold outer repeats", "detail": "4-fold inner tuning"}],
                }
            ],
        },
    )

    module.materialize_display_surface(paper_root=paper_root)

    layout = json.loads((paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8"))
    assert layout["render_context"]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert "style_roles" in layout["render_context"]
    assert "palette" in layout["render_context"]


def test_materialize_display_surface_expands_exclusion_box_for_wrapped_copy(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    dump_json(
        paper_root / "cohort_flow.json",
        {
            "schema_version": 1,
            "shell_id": "cohort_flow_figure",
            "display_id": "Figure1",
            "title": "Study cohort assembly with exclusion accounting",
            "caption": "Source-to-analysis cohort derivation with explicit inclusion and exclusion accounting.",
            "steps": [
                {
                    "step_id": "source_total",
                    "label": "Screened institutional NF-PitNET records",
                    "n": 409,
                    "detail": "Source population before first-surgery eligibility filtering",
                },
                {
                    "step_id": "first_surgery",
                    "label": "Included: first-surgery NF-PitNET cohort",
                    "n": 357,
                    "detail": "Eligible primary surgery cases",
                },
                {
                    "step_id": "analysis",
                    "label": "Included in final analysis cohort",
                    "n": 357,
                    "detail": "Observed early postoperative MRI-based resection status",
                },
            ],
            "exclusion_branches": [
                {
                    "branch_id": "repeat_salvage",
                    "from_step_id": "source_total",
                    "label": "Excluded: repeat or salvage surgery",
                    "n": 52,
                    "detail": "Removed before locking the first-surgery analysis cohort",
                }
            ],
            "sidecar_blocks": [
                {
                    "block_id": "validation_frame",
                    "block_type": "wide_top",
                    "title": "Validation framework",
                    "items": [
                        {"label": "Repeated nested validation", "detail": "5-fold outer x 20 repeats; 4-fold inner tuning"}
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["figures_materialized"] == ["F1"]
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F1_cohort_flow.layout.json").read_text(encoding="utf-8")
    )
    exclusion_box = next(
        item for item in layout_sidecar["layout_boxes"] if item["box_id"] == "exclusion_repeat_salvage"
    )
    assert exclusion_box["y1"] - exclusion_box["y0"] >= 0.10
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_registered_evidence_figures(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_evidence=True)
    render_calls: list[dict[str, str]] = []
    original_loader = module.display_pack_runtime.load_python_plugin_callable

    def fake_render_r_evidence_figure(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.parent.mkdir(parents=True, exist_ok=True)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(
            {
                "template_id": template_id,
                "display_id": str(display_payload.get("display_id") or ""),
            }
        )

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if display_registry.is_evidence_figure_template(template_id):
            return fake_render_r_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F1", "F2", "F3", "F4", "F5", "F6"]
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.png").exists()
    assert (paper_root / "figures" / "generated" / "F2_roc_curve_binary.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F6_kaplan_meier_grouped.pdf").exists()
    assert {item["template_id"] for item in render_calls} == {
        full_id("roc_curve_binary"),
        full_id("pr_curve_binary"),
        full_id("calibration_curve_binary"),
        full_id("decision_curve_binary"),
        full_id("kaplan_meier_grouped"),
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F2"]["template_id"] == full_id("roc_curve_binary")
    assert figures_by_id["F2"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["F2"]["renderer_family"] == "r_ggplot2"
    assert figures_by_id["F2"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F5"]["qc_profile"] == "publication_evidence_curve"
    assert figures_by_id["F6"]["template_id"] == full_id("kaplan_meier_grouped")
    assert figures_by_id["F6"]["input_schema_id"] == "time_to_event_grouped_inputs_v1"


def test_materialize_display_surface_generates_full_registered_template_set(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    render_calls: list[tuple[str, str]] = []
    original_loader = module.display_pack_runtime.load_python_plugin_callable

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
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append((template_id, str(display_payload.get("display_id") or "")))

    def fake_render_python_evidence_figure(
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
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append((template_id, str(display_payload.get("display_id") or "")))

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if display_registry.is_evidence_figure_template(template_id):
            spec = display_registry.get_evidence_figure_spec(template_id)
            if spec.renderer_family == "r_ggplot2":
                return fake_render_r_evidence_figure
            return fake_render_python_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == [
        "F1",
        "F2",
        "F3",
        "F4",
        "F5",
        "F6",
        "F7",
        "F8",
        "F9",
        "F10",
        "F11",
        "F12",
        "F13",
        "F14",
        "F15",
        "F16",
        "F17",
        "F18",
        "F19",
        "F20",
        "F21",
    ]
    assert result["tables_materialized"] == ["T1", "T2", "T3"]
    assert (paper_root / "figures" / "generated" / "F7_cumulative_incidence_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F8_umap_scatter_grouped.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F10_heatmap_group_comparison.png").exists()
    assert (paper_root / "figures" / "generated" / "F12_forest_effect_main.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F13_shap_summary_beeswarm.png").exists()
    assert (paper_root / "figures" / "generated" / "F14_time_to_event_discrimination_calibration_panel.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F15_time_to_event_risk_group_summary.png").exists()
    assert (paper_root / "figures" / "generated" / "F16_time_to_event_decision_curve.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F17_multicenter_generalizability_overview.png").exists()
    assert (paper_root / "figures" / "generated" / "F18_time_dependent_roc_horizon.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F19_tsne_scatter_grouped.png").exists()
    assert (paper_root / "figures" / "generated" / "F20_subgroup_forest.pdf").exists()
    assert (paper_root / "figures" / "generated" / "F21_clustered_heatmap.png").exists()
    assert (paper_root / "tables" / "generated" / "T2_time_to_event_performance_summary.md").exists()
    assert (paper_root / "tables" / "generated" / "T3_clinical_interpretation_summary.md").exists()
    assert {template_id for template_id, _ in render_calls} == {
        full_id("roc_curve_binary"),
        full_id("pr_curve_binary"),
        full_id("calibration_curve_binary"),
        full_id("decision_curve_binary"),
        full_id("time_dependent_roc_horizon"),
        full_id("kaplan_meier_grouped"),
        full_id("cumulative_incidence_grouped"),
        full_id("umap_scatter_grouped"),
        full_id("pca_scatter_grouped"),
        full_id("tsne_scatter_grouped"),
        full_id("heatmap_group_comparison"),
        full_id("correlation_heatmap"),
        full_id("clustered_heatmap"),
        full_id("forest_effect_main"),
        full_id("subgroup_forest"),
        full_id("shap_summary_beeswarm"),
        full_id("time_to_event_discrimination_calibration_panel"),
        full_id("time_to_event_risk_group_summary"),
        full_id("time_to_event_decision_curve"),
        full_id("multicenter_generalizability_overview"),
    }

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["F7"]["template_id"] == full_id("cumulative_incidence_grouped")
    assert figures_by_id["F8"]["input_schema_id"] == "embedding_grouped_inputs_v1"
    assert figures_by_id["F10"]["qc_profile"] == "publication_heatmap"
    assert figures_by_id["F12"]["qc_profile"] == "publication_forest_plot"
    assert figures_by_id["F13"]["renderer_family"] == "python"
    assert figures_by_id["F13"]["input_schema_id"] == "shap_summary_inputs_v1"
    assert figures_by_id["F14"]["input_schema_id"] == "time_to_event_discrimination_calibration_inputs_v1"
    assert figures_by_id["F15"]["qc_profile"] == "publication_survival_curve"
    assert figures_by_id["F16"]["qc_profile"] == "publication_decision_curve"
    assert figures_by_id["F17"]["qc_profile"] == "publication_multicenter_overview"
    assert figures_by_id["F18"]["template_id"] == full_id("time_dependent_roc_horizon")
    assert figures_by_id["F18"]["input_schema_id"] == "binary_prediction_curve_inputs_v1"
    assert figures_by_id["F19"]["template_id"] == full_id("tsne_scatter_grouped")
    assert figures_by_id["F19"]["qc_profile"] == "publication_embedding_scatter"
    assert figures_by_id["F20"]["template_id"] == full_id("subgroup_forest")
    assert figures_by_id["F20"]["qc_profile"] == "publication_forest_plot"
    assert figures_by_id["F21"]["template_id"] == full_id("clustered_heatmap")
    assert figures_by_id["F21"]["input_schema_id"] == "clustered_heatmap_inputs_v1"
    assert figures_by_id["F21"]["qc_profile"] == "publication_heatmap"

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {item["table_id"]: item for item in table_catalog["tables"]}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("table2_time_to_event_performance_summary")
    assert tables_by_id["T2"]["qc_profile"] == "publication_table_performance"
    assert tables_by_id["T3"]["table_shell_id"] == full_id("table3_clinical_interpretation_summary")
    assert tables_by_id["T3"]["qc_profile"] == "publication_table_interpretation"


def test_render_python_evidence_figure_prefers_pack_entrypoint_for_migrated_python_template(
    tmp_path: Path,
    monkeypatch,
) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    output_png_path = tmp_path / "output.png"
    output_pdf_path = tmp_path / "output.pdf"
    layout_sidecar_path = tmp_path / "output.layout.json"
    template_id = full_id("time_to_event_risk_group_summary")
    render_calls: list[str] = []

    def fake_external_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(str(display_payload["display_id"]))

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "resolve_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )

    controller_module._render_python_evidence_figure(
        template_id=template_id,
        display_payload={
            "display_id": "F3",
            "risk_group_summaries": [
                {
                    "label": "Low risk",
                    "sample_size": 72,
                    "events_5y": 4,
                    "mean_predicted_risk_5y": 0.08,
                    "observed_km_risk_5y": 0.06,
                }
            ],
        },
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert render_calls == ["F3"]
    assert output_png_path.read_text(encoding="utf-8") == "PNG"
    assert output_pdf_path.read_text(encoding="utf-8") == "%PDF"
    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["template_id"] == template_id


def test_materialize_display_surface_materializes_optional_submission_graphical_abstract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
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
                    "rows": [{"cards": [{"card_id": "boundary", "title": "Transportability boundary", "value": "No external validation", "detail": "Internal cohort only", "accent_role": "audit"}]}],
                },
            ],
            "footer_pills": [
                {"pill_id": "p1", "panel_id": "cohort_split", "label": "Internal validation only", "style_role": "neutral"},
                {"pill_id": "p2", "panel_id": "primary_endpoint", "label": "Supportive endpoint retained", "style_role": "secondary"},
                {"pill_id": "p3", "panel_id": "supportive_context", "label": "No external validation", "style_role": "audit"},
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert "GA1" in result["figures_materialized"]
    assert (paper_root / "figures" / "generated" / "GA1_graphical_abstract.svg").exists()
    assert (paper_root / "figures" / "generated" / "GA1_graphical_abstract.png").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["GA1"]["template_id"] == full_id("submission_graphical_abstract")
    assert figures_by_id["GA1"]["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figures_by_id["GA1"]["qc_profile"] == "submission_graphical_abstract"
    assert figures_by_id["GA1"]["qc_result"]["status"] == "pass"


def test_materialize_display_surface_uses_pack_runtime_for_submission_graphical_abstract(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
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
                    "rows": [{"cards": [{"card_id": "analytic", "title": "Analytic cohort", "value": "15,787"}]}],
                }
            ],
            "footer_pills": [],
        },
    )
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_shell_renderer(
        *,
        template_id: str,
        shell_payload: dict[str, object],
        payload_path: Path | None = None,
        render_context: dict[str, object],
        output_svg_path: Path,
        output_png_path: Path,
        output_layout_path: Path,
    ) -> None:
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("submission_graphical_abstract"):
            return fake_shell_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_render_submission_graphical_abstract",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("host submission graphical abstract renderer should not be used")
        ),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("submission_graphical_abstract")]
    assert (paper_root / "figures" / "generated" / "GA1_graphical_abstract.svg").exists()


def test_choose_submission_graphical_abstract_arrow_lane_prefers_shared_blank_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")

    lane_center_y = module._choose_submission_graphical_abstract_arrow_lane(
        left_panel_box={"x0": 10.0, "y0": 100.0, "x1": 210.0, "y1": 480.0},
        right_panel_box={"x0": 250.0, "y0": 100.0, "x1": 450.0, "y1": 480.0},
        left_occupied_boxes=(
            {"x0": 24.0, "y0": 120.0, "x1": 196.0, "y1": 190.0},
            {"x0": 24.0, "y0": 392.0, "x1": 196.0, "y1": 450.0},
        ),
        right_occupied_boxes=(
            {"x0": 264.0, "y0": 130.0, "x1": 436.0, "y1": 200.0},
            {"x0": 264.0, "y0": 382.0, "x1": 436.0, "y1": 440.0},
        ),
        clearance_pt=12.0,
        arrow_half_height_pt=18.0,
    )

    assert 240.0 <= lane_center_y <= 320.0


def test_choose_submission_graphical_abstract_arrow_lane_prefers_shared_midline_over_larger_top_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")

    lane_center_y = module._choose_submission_graphical_abstract_arrow_lane(
        left_panel_box={"x0": 10.0, "y0": 100.0, "x1": 210.0, "y1": 500.0},
        right_panel_box={"x0": 250.0, "y0": 100.0, "x1": 450.0, "y1": 500.0},
        left_occupied_boxes=(
            {"x0": 24.0, "y0": 240.0, "x1": 196.0, "y1": 280.0},
            {"x0": 24.0, "y0": 350.0, "x1": 196.0, "y1": 380.0},
        ),
        right_occupied_boxes=(
            {"x0": 264.0, "y0": 240.0, "x1": 436.0, "y1": 280.0},
            {"x0": 264.0, "y0": 350.0, "x1": 436.0, "y1": 380.0},
        ),
        clearance_pt=12.0,
        arrow_half_height_pt=18.0,
    )

    assert 300.0 <= lane_center_y <= 330.0


def test_materialize_display_surface_wraps_or_stacks_long_graphical_abstract_boundary_cards(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
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

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figures_by_id = {item["figure_id"]: item for item in figure_catalog["figures"]}
    assert figures_by_id["GA1"]["qc_result"]["status"] == "pass"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "GA1_graphical_abstract.layout.json").read_text(encoding="utf-8")
    )
    value_boxes = {
        item["box_id"]: item
        for item in layout_sidecar["layout_boxes"]
        if item["box_type"] == "card_value"
    }
    arrow_boxes = [
        item
        for item in layout_sidecar["guide_boxes"]
        if item["box_type"] == "arrow_connector"
    ]
    arrow_mid_ys = [((item["y0"] + item["y1"]) / 2.0) for item in arrow_boxes]
    assert value_boxes["supportive_context_internal_boundary_value"]["x1"] <= 1.0
    assert value_boxes["supportive_context_transportability_boundary_value"]["x1"] <= 1.0
    assert len(arrow_boxes) == 2
    assert max(arrow_mid_ys) - min(arrow_mid_ys) <= 0.03


def test_materialize_display_surface_supports_generic_anchor_table_shells(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    (paper_root / "figures").mkdir(parents=True)
    (paper_root / "tables").mkdir(parents=True)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "performance_summary",
                    "display_kind": "table",
                    "requirement_key": "performance_summary_table_generic",
                    "catalog_id": "T2",
                },
                {
                    "display_id": "grouped_risk_event_summary",
                    "display_kind": "table",
                    "requirement_key": "grouped_risk_event_summary_table",
                    "catalog_id": "T3",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "performance_summary_table_generic.json",
        {
            "schema_version": 1,
            "table_shell_id": "performance_summary_table_generic",
            "display_id": "performance_summary",
            "catalog_id": "T2",
            "title": "Unified repeated nested validation results across candidate packages",
            "caption": "Pooled out-of-fold discrimination, error, and calibration summaries across candidate packages.",
            "row_header_label": "Model",
            "columns": [
                {"column_id": "auroc", "label": "AUROC"},
                {"column_id": "auprc", "label": "AUPRC"},
            ],
            "rows": [
                {"row_id": "simple", "label": "Simple 3-month score", "values": ["0.7081", "0.4740"]},
                {"row_id": "core", "label": "Core logistic confirmation", "values": ["0.6987", "0.4556"]},
            ],
        },
    )
    dump_json(
        paper_root / "grouped_risk_event_summary_table.json",
        {
            "schema_version": 1,
            "table_shell_id": "grouped_risk_event_summary_table",
            "display_id": "grouped_risk_event_summary",
            "catalog_id": "T3",
            "title": "Event rates across score bands and grouped-risk strata",
            "caption": "Observed event counts and risks across score-band and grouped-risk strata.",
            "surface_column_label": "Surface",
            "stratum_column_label": "Stratum",
            "cases_column_label": "Cases",
            "events_column_label": "Events",
            "risk_column_label": "Risk",
            "rows": [
                {
                    "row_id": "score_band_0",
                    "surface": "Score band",
                    "stratum": "0",
                    "cases": 95,
                    "events": 8,
                    "risk_display": "8.4%",
                },
                {
                    "row_id": "grouped_risk_high",
                    "surface": "Grouped risk",
                    "stratum": "High",
                    "cases": 66,
                    "events": 37,
                    "risk_display": "56.1%",
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["tables_materialized"] == ["T2", "T3"]
    assert (paper_root / "tables" / "generated" / "T2_performance_summary_table_generic.csv").exists()
    assert (paper_root / "tables" / "generated" / "T2_performance_summary_table_generic.md").exists()
    assert (paper_root / "tables" / "generated" / "T3_grouped_risk_event_summary_table.csv").exists()
    assert (paper_root / "tables" / "generated" / "T3_grouped_risk_event_summary_table.md").exists()

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {item["table_id"]: item for item in table_catalog["tables"]}
    assert tables_by_id["T2"]["table_shell_id"] == full_id("performance_summary_table_generic")
    assert tables_by_id["T2"]["input_schema_id"] == "performance_summary_table_generic_v1"
    assert tables_by_id["T2"]["asset_paths"] == [
        "paper/tables/generated/T2_performance_summary_table_generic.csv",
        "paper/tables/generated/T2_performance_summary_table_generic.md",
    ]
    assert tables_by_id["T3"]["table_shell_id"] == full_id("grouped_risk_event_summary_table")
    assert tables_by_id["T3"]["input_schema_id"] == "grouped_risk_event_summary_table_v1"
    assert tables_by_id["T3"]["asset_paths"] == [
        "paper/tables/generated/T3_grouped_risk_event_summary_table.csv",
        "paper/tables/generated/T3_grouped_risk_event_summary_table.md",
    ]


def test_materialize_display_surface_accepts_appendix_table_alias_a1_for_grouped_risk_table(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    (paper_root / "figures").mkdir(parents=True)
    (paper_root / "tables").mkdir(parents=True)
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "appendix_table_a1_public_anchors",
                    "display_kind": "table",
                    "requirement_key": "grouped_risk_event_summary_table",
                    "catalog_id": "A1",
                },
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
        paper_root / "grouped_risk_event_summary_table.json",
        {
            "schema_version": 1,
            "table_shell_id": "grouped_risk_event_summary_table",
            "display_id": "appendix_table_a1_public_anchors",
            "catalog_id": "A1",
            "title": "Retained public anchor summary",
            "caption": "Observed anchor counts across retained public anatomy and biology sources.",
            "surface_column_label": "Anchor surface",
            "stratum_column_label": "Retained subset",
            "cases_column_label": "Cases",
            "events_column_label": "Events",
            "risk_column_label": "Share",
            "rows": [
                {
                    "row_id": "mapping_pituitary_nfpa",
                    "surface": "Mapping pituitary",
                    "stratum": "NFPA",
                    "cases": 85,
                    "events": 27,
                    "risk_display": "31.8%",
                },
                {
                    "row_id": "gse169498_invasive",
                    "surface": "GSE169498",
                    "stratum": "Invasive",
                    "cases": 73,
                    "events": 49,
                    "risk_display": "67.1%",
                },
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["tables_materialized"] == ["TA1"]
    assert (paper_root / "tables" / "generated" / "TA1_grouped_risk_event_summary_table.csv").exists()
    assert (paper_root / "tables" / "generated" / "TA1_grouped_risk_event_summary_table.md").exists()

    table_catalog = json.loads((paper_root / "tables" / "table_catalog.json").read_text(encoding="utf-8"))
    tables_by_id = {item["table_id"]: item for item in table_catalog["tables"]}
    assert tables_by_id["TA1"]["table_shell_id"] == full_id("grouped_risk_event_summary_table")
    assert tables_by_id["TA1"]["input_schema_id"] == "grouped_risk_event_summary_table_v1"
    assert tables_by_id["TA1"]["asset_paths"] == [
        "paper/tables/generated/TA1_grouped_risk_event_summary_table.csv",
        "paper/tables/generated/TA1_grouped_risk_event_summary_table.md",
    ]


def test_materialize_display_surface_uses_pack_runtime_for_baseline_table_shell(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    original_loader = module.display_pack_runtime.load_python_plugin_callable
    render_calls: list[str] = []

    def fake_table_renderer(
        *,
        template_id: str,
        payload_path: Path,
        payload: dict[str, object],
        output_md_path: Path,
        output_csv_path: Path | None,
    ) -> dict[str, str]:
        _ensure_output_parents(output_md_path, output_csv_path)
        output_md_path.write_text("| Characteristic | Overall |\n| --- | --- |\n| Age | 61 |\n", encoding="utf-8")
        assert output_csv_path is not None
        output_csv_path.write_text("Characteristic,Overall\nAge,61\n", encoding="utf-8")
        render_calls.append(template_id)
        return {
            "title": "Baseline characteristics",
            "caption": "Baseline characteristics across prespecified groups.",
        }

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("table1_baseline_characteristics"):
            return fake_table_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_write_table_outputs",
        lambda **_: (_ for _ in ()).throw(AssertionError("host table writer should not be used")),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("table1_baseline_characteristics")]
    assert (paper_root / "tables" / "generated" / "T1_baseline_characteristics.md").exists()


def test_materialize_display_surface_writes_layout_sidecar_and_real_qc_result(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    original_loader = module.display_pack_runtime.load_python_plugin_callable

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
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    def fake_render_python_evidence_figure(
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
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if display_registry.is_evidence_figure_template(template_id):
            spec = display_registry.get_evidence_figure_spec(template_id)
            if spec.renderer_family == "r_ggplot2":
                return fake_render_r_evidence_figure
            return fake_render_python_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    module.materialize_display_surface(paper_root=paper_root)

    layout_sidecar_path = paper_root / "figures" / "generated" / "F17_multicenter_generalizability_overview.layout.json"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    qc_result = {item["figure_id"]: item["qc_result"] for item in figure_catalog["figures"]}["F17"]

    assert layout_sidecar_path.exists()
    assert qc_result["status"] == "pass", qc_result
    assert qc_result["engine_id"] == "display_layout_qc_v1"
    assert qc_result["qc_profile"] == "publication_multicenter_overview"
    assert qc_result["layout_sidecar_path"].endswith(".layout.json")
    assert qc_result["issues"] == []
    assert qc_result["audit_classes"] == []
    assert qc_result["failure_reason"] == ""
    assert qc_result["readability_findings"] == []
    assert qc_result["revision_note"] == ""


def test_materialize_display_surface_generates_risk_layering_monotonic_bars(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure22",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F22",
                    "shell_path": "paper/figures/Figure22.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "risk_layering",
                    "template_id": "risk_layering_monotonic_bars",
                    "layout_override": {
                        "show_figure_title": True,
                    },
                    "readability_override": {},
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
                    "display_id": "Figure22",
                    "template_id": "risk_layering_monotonic_bars",
                    "title": "Monotonic risk layering of the 3-month endocrine burden score",
                    "caption": "Observed risk rises monotonically across score bands and grouped follow-up strata.",
                    "y_label": "Risk of later persistent global hypopituitarism (%)",
                    "left_panel_title": "Score bands",
                    "left_x_label": "Simple score",
                    "left_bars": [
                        {"label": "0", "cases": 95, "events": 8, "risk": 0.0842},
                        {"label": "1", "cases": 98, "events": 18, "risk": 0.1837},
                        {"label": "2", "cases": 98, "events": 35, "risk": 0.3571},
                        {"label": "3", "cases": 54, "events": 29, "risk": 0.5370},
                        {"label": "4+", "cases": 12, "events": 8, "risk": 0.6667},
                    ],
                    "right_panel_title": "Grouped follow-up strata",
                    "right_x_label": "Grouped risk",
                    "right_bars": [
                        {"label": "Low", "cases": 95, "events": 8, "risk": 0.0842},
                        {"label": "Intermediate", "cases": 196, "events": 53, "risk": 0.2704},
                        {"label": "High", "cases": 66, "events": 37, "risk": 0.5606},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F22"]
    assert (paper_root / "figures" / "generated" / "F22_risk_layering_monotonic_bars.png").exists()
    assert (paper_root / "figures" / "generated" / "F22_risk_layering_monotonic_bars.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F22_risk_layering_monotonic_bars.layout.json"
    assert layout_sidecar_path.exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F22"
    assert figure_entry["template_id"] == full_id("risk_layering_monotonic_bars")
    assert figure_entry["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "risk_layering_monotonic_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_risk_layering_bars"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_gsva_ssgsea_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure23",
                    "display_kind": "figure",
                    "requirement_key": "gsva_ssgsea_heatmap",
                    "catalog_id": "F23",
                    "shell_path": "paper/figures/Figure23.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure23",
                    "template_id": "gsva_ssgsea_heatmap",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "gsva_ssgsea_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "gsva_ssgsea_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure23",
                    "template_id": "gsva_ssgsea_heatmap",
                    "title": "GSVA heatmap for immune and stromal programs",
                    "caption": "Precomputed GSVA pathway scores across the analytic cohort highlight the dominant immune-stromal contrast.",
                    "x_label": "Samples",
                    "y_label": "Gene-set programs",
                    "score_method": "GSVA",
                    "row_order": [
                        {"label": "IFN-gamma response"},
                        {"label": "TGF-beta signaling"},
                    ],
                    "column_order": [
                        {"label": "Sample-01"},
                        {"label": "Sample-02"},
                    ],
                    "cells": [
                        {"x": "Sample-01", "y": "IFN-gamma response", "value": 0.72},
                        {"x": "Sample-02", "y": "IFN-gamma response", "value": -0.24},
                        {"x": "Sample-01", "y": "TGF-beta signaling", "value": -0.11},
                        {"x": "Sample-02", "y": "TGF-beta signaling", "value": 0.58},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F23"]
    assert (paper_root / "figures" / "generated" / "F23_gsva_ssgsea_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F23_gsva_ssgsea_heatmap.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F23_gsva_ssgsea_heatmap.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F23"
    assert figure_entry["template_id"] == full_id("gsva_ssgsea_heatmap")
    assert figure_entry["renderer_family"] == "r_ggplot2"
    assert figure_entry["input_schema_id"] == "gsva_ssgsea_heatmap_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_heatmap"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_performance_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure25",
                    "display_kind": "figure",
                    "requirement_key": "performance_heatmap",
                    "catalog_id": "F25",
                    "shell_path": "paper/figures/Figure25.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure25",
                    "template_id": "performance_heatmap",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "performance_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "performance_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure25",
                    "template_id": "performance_heatmap",
                    "title": "AUC heatmap across APOE4 subgroups and predictor sets",
                    "caption": "Random-forest discrimination remains strongest for the integrated model across APOE4-stratified analyses.",
                    "x_label": "Analytic subgroup",
                    "y_label": "Predictor set",
                    "metric_name": "AUC",
                    "row_order": [
                        {"label": "Clinical baseline"},
                        {"label": "Integrated model"},
                    ],
                    "column_order": [
                        {"label": "All participants"},
                        {"label": "APOE4 carriers"},
                    ],
                    "cells": [
                        {"x": "All participants", "y": "Clinical baseline", "value": 0.71},
                        {"x": "APOE4 carriers", "y": "Clinical baseline", "value": 0.68},
                        {"x": "All participants", "y": "Integrated model", "value": 0.83},
                        {"x": "APOE4 carriers", "y": "Integrated model", "value": 0.79},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F25"]
    assert (paper_root / "figures" / "generated" / "F25_performance_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F25_performance_heatmap.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F25_performance_heatmap.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["metric_name"] == "AUC"
    assert layout_sidecar["metrics"]["matrix_cells"][0]["value"] == 0.71

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F25"
    assert figure_entry["template_id"] == full_id("performance_heatmap")
    assert figure_entry["renderer_family"] == "r_ggplot2"
    assert figure_entry["input_schema_id"] == "performance_heatmap_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_heatmap"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_celltype_signature_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure26",
                    "display_kind": "figure",
                    "requirement_key": "celltype_signature_heatmap",
                    "catalog_id": "F26",
                    "shell_path": "paper/figures/Figure26.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "celltype_signature_heatmap",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "celltype_signature_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_signature_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "celltype_signature_heatmap",
                    "title": "Cell-type embedding and signature activity atlas",
                    "caption": "Cell-type clusters and pathway-signature activity remain aligned across the circulating immune atlas.",
                    "embedding_panel_title": "Embedding by cell type",
                    "embedding_x_label": "UMAP 1",
                    "embedding_y_label": "UMAP 2",
                    "embedding_points": [
                        {"x": -2.1, "y": 1.0, "group": "T cells"},
                        {"x": -1.8, "y": 0.8, "group": "T cells"},
                        {"x": 1.4, "y": -0.6, "group": "Myeloid"},
                        {"x": 1.8, "y": -0.9, "group": "Myeloid"},
                    ],
                    "heatmap_panel_title": "Signature activity",
                    "heatmap_x_label": "Cell type",
                    "heatmap_y_label": "Program",
                    "score_method": "AUCell",
                    "row_order": [
                        {"label": "IFN response"},
                        {"label": "TGF-beta signaling"},
                    ],
                    "column_order": [
                        {"label": "T cells"},
                        {"label": "Myeloid"},
                    ],
                    "cells": [
                        {"x": "T cells", "y": "IFN response", "value": 0.78},
                        {"x": "Myeloid", "y": "IFN response", "value": -0.22},
                        {"x": "T cells", "y": "TGF-beta signaling", "value": -0.18},
                        {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.61},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F26"]
    assert (paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert any(box["box_type"] == "heatmap_tile_region" for box in layout_sidecar["panel_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F26"
    assert figure_entry["template_id"] == full_id("celltype_signature_heatmap")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "celltype_signature_heatmap_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_celltype_signature_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def _make_single_cell_atlas_overview_display(display_id: str = "Figure27") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "single_cell_atlas_overview_panel",
        "title": "Single-cell atlas occupancy, composition, and marker program overview",
        "caption": (
            "Embedding occupancy, group-wise state composition, and marker-program definition remain bound "
            "inside one audited atlas overview contract."
        ),
        "embedding_panel_title": "Atlas occupancy",
        "embedding_x_label": "UMAP 1",
        "embedding_y_label": "UMAP 2",
        "embedding_points": [
            {"x": -2.0, "y": 1.1, "state_label": "T cells", "group_label": "Tumor"},
            {"x": -1.7, "y": 0.8, "state_label": "T cells", "group_label": "Adjacent"},
            {"x": 1.4, "y": -0.5, "state_label": "Myeloid", "group_label": "Tumor"},
            {"x": 1.9, "y": -0.8, "state_label": "Myeloid", "group_label": "Adjacent"},
        ],
        "composition_panel_title": "Group-wise composition",
        "composition_x_label": "Cell-state composition",
        "composition_y_label": "Group",
        "composition_groups": [
            {
                "group_label": "Tumor",
                "group_order": 1,
                "state_proportions": [
                    {"state_label": "T cells", "proportion": 0.58},
                    {"state_label": "Myeloid", "proportion": 0.42},
                ],
            },
            {
                "group_label": "Adjacent",
                "group_order": 2,
                "state_proportions": [
                    {"state_label": "T cells", "proportion": 0.37},
                    {"state_label": "Myeloid", "proportion": 0.63},
                ],
            },
        ],
        "heatmap_panel_title": "Marker-program definition",
        "heatmap_x_label": "Cell state",
        "heatmap_y_label": "Marker / program",
        "score_method": "AUCell",
        "row_order": [
            {"label": "IFN response"},
            {"label": "TGF-beta signaling"},
        ],
        "column_order": [
            {"label": "T cells"},
            {"label": "Myeloid"},
        ],
        "cells": [
            {"x": "T cells", "y": "IFN response", "value": 0.81},
            {"x": "Myeloid", "y": "IFN response", "value": -0.22},
            {"x": "T cells", "y": "TGF-beta signaling", "value": -0.18},
            {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.64},
        ],
    }


def _make_spatial_niche_map_display(display_id: str = "Figure28") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "spatial_niche_map_panel",
        "title": "Spatial niche topography, abundance, and marker-program definition",
        "caption": (
            "Tissue-coordinate niche localization, region-level niche composition, and marker-program definition "
            "remain bound inside one audited spatial niche contract."
        ),
        "spatial_panel_title": "Spatial niche topography",
        "spatial_x_label": "Tissue x coordinate",
        "spatial_y_label": "Tissue y coordinate",
        "spatial_points": [
            {"x": 0.10, "y": 0.78, "niche_label": "Immune niche", "region_label": "Tumor core"},
            {"x": 0.18, "y": 0.70, "niche_label": "Immune niche", "region_label": "Tumor core"},
            {"x": 0.74, "y": 0.26, "niche_label": "Stromal niche", "region_label": "Invasive margin"},
            {"x": 0.82, "y": 0.18, "niche_label": "Stromal niche", "region_label": "Invasive margin"},
        ],
        "composition_panel_title": "Region-wise niche composition",
        "composition_x_label": "Niche composition",
        "composition_y_label": "Region",
        "composition_groups": [
            {
                "group_label": "Tumor core",
                "group_order": 1,
                "niche_proportions": [
                    {"niche_label": "Immune niche", "proportion": 0.64},
                    {"niche_label": "Stromal niche", "proportion": 0.36},
                ],
            },
            {
                "group_label": "Invasive margin",
                "group_order": 2,
                "niche_proportions": [
                    {"niche_label": "Immune niche", "proportion": 0.42},
                    {"niche_label": "Stromal niche", "proportion": 0.58},
                ],
            },
        ],
        "heatmap_panel_title": "Marker-program definition",
        "heatmap_x_label": "Niche state",
        "heatmap_y_label": "Marker / program",
        "score_method": "AUCell",
        "row_order": [
            {"label": "CXCL13 program"},
            {"label": "TGF-beta program"},
        ],
        "column_order": [
            {"label": "Immune niche"},
            {"label": "Stromal niche"},
        ],
        "cells": [
            {"x": "Immune niche", "y": "CXCL13 program", "value": 0.78},
            {"x": "Stromal niche", "y": "CXCL13 program", "value": -0.14},
            {"x": "Immune niche", "y": "TGF-beta program", "value": -0.21},
            {"x": "Stromal niche", "y": "TGF-beta program", "value": 0.66},
        ],
    }


def _make_trajectory_progression_display(display_id: str = "Figure29") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "trajectory_progression_panel",
        "title": "Trajectory progression, branch composition, and marker kinetics",
        "caption": (
            "Trajectory embedding, pseudotime-bin branch composition, and marker kinetics remain bound "
            "inside one audited trajectory progression contract."
        ),
        "trajectory_panel_title": "Trajectory progression",
        "trajectory_x_label": "Embedding 1",
        "trajectory_y_label": "Embedding 2",
        "trajectory_points": [
            {"x": -1.8, "y": 0.9, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
            {"x": -1.1, "y": 0.5, "branch_label": "Branch A", "state_label": "Intermediate", "pseudotime": 0.36},
            {"x": -0.3, "y": -0.1, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.74},
            {"x": 1.5, "y": 0.8, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
            {"x": 1.0, "y": 0.1, "branch_label": "Branch B", "state_label": "Intermediate", "pseudotime": 0.48},
            {"x": 0.6, "y": -0.7, "branch_label": "Branch B", "state_label": "Terminal", "pseudotime": 0.86},
        ],
        "composition_panel_title": "Pseudotime-bin branch composition",
        "composition_x_label": "Branch composition",
        "composition_y_label": "Pseudotime bin",
        "branch_order": [
            {"label": "Branch A"},
            {"label": "Branch B"},
        ],
        "progression_bins": [
            {
                "bin_label": "Early",
                "bin_order": 1,
                "pseudotime_start": 0.0,
                "pseudotime_end": 0.33,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.56},
                    {"branch_label": "Branch B", "proportion": 0.44},
                ],
            },
            {
                "bin_label": "Mid",
                "bin_order": 2,
                "pseudotime_start": 0.33,
                "pseudotime_end": 0.67,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.49},
                    {"branch_label": "Branch B", "proportion": 0.51},
                ],
            },
            {
                "bin_label": "Late",
                "bin_order": 3,
                "pseudotime_start": 0.67,
                "pseudotime_end": 1.0,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.38},
                    {"branch_label": "Branch B", "proportion": 0.62},
                ],
            },
        ],
        "heatmap_panel_title": "Marker kinetics",
        "heatmap_x_label": "Pseudotime bin",
        "heatmap_y_label": "Marker / module",
        "score_method": "GSVA",
        "row_order": [
            {"label": "Interferon module"},
            {"label": "EMT module"},
        ],
        "column_order": [
            {"label": "Early"},
            {"label": "Mid"},
            {"label": "Late"},
        ],
        "cells": [
            {"x": "Early", "y": "Interferon module", "value": 0.72},
            {"x": "Mid", "y": "Interferon module", "value": 0.28},
            {"x": "Late", "y": "Interferon module", "value": -0.18},
            {"x": "Early", "y": "EMT module", "value": -0.31},
            {"x": "Mid", "y": "EMT module", "value": 0.22},
            {"x": "Late", "y": "EMT module", "value": 0.68},
        ],
    }


def test_load_evidence_display_payload_rejects_incomplete_composition_for_single_cell_atlas_overview(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_single_cell_atlas_overview_display()
    display_payload["composition_groups"][1]["state_proportions"] = [
        {"state_label": "T cells", "proportion": 0.37},
    ]
    dump_json(
        paper_root / "single_cell_atlas_overview_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "single_cell_atlas_overview_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("single_cell_atlas_overview_panel")

    with pytest.raises(ValueError, match="composition_groups.*must cover the declared state labels exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure27",
        )


def test_load_evidence_display_payload_rejects_incomplete_composition_for_spatial_niche_map(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_spatial_niche_map_display()
    display_payload["composition_groups"][1]["niche_proportions"] = [
        {"niche_label": "Immune niche", "proportion": 0.42},
    ]
    dump_json(
        paper_root / "spatial_niche_map_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "spatial_niche_map_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("spatial_niche_map_panel")

    with pytest.raises(ValueError, match="composition_groups.*must cover the declared niche labels exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure28",
        )


def test_load_evidence_display_payload_rejects_incomplete_branch_weights_for_trajectory_progression(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_trajectory_progression_display()
    display_payload["progression_bins"][1]["branch_weights"] = [
        {"branch_label": "Branch A", "proportion": 0.49},
    ]
    dump_json(
        paper_root / "trajectory_progression_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "trajectory_progression_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("trajectory_progression_panel")

    with pytest.raises(ValueError, match="progression_bins.*must cover the declared branch labels exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure29",
        )


def test_materialize_display_surface_generates_single_cell_atlas_overview_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure27",
                    "display_kind": "figure",
                    "requirement_key": "single_cell_atlas_overview_panel",
                    "catalog_id": "F27",
                    "shell_path": "paper/figures/Figure27.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure27",
                    "template_id": "single_cell_atlas_overview_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "single_cell_atlas_overview_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "single_cell_atlas_overview_inputs_v1",
            "displays": [_make_single_cell_atlas_overview_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F27"]
    assert (paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_embedding",
        "panel_composition",
        "panel_heatmap",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["state_labels"]) == ["Myeloid", "T cells"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F27"
    assert figure_entry["template_id"] == full_id("single_cell_atlas_overview_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "single_cell_atlas_overview_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_single_cell_atlas_overview_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_spatial_niche_map_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure28",
                    "display_kind": "figure",
                    "requirement_key": "spatial_niche_map_panel",
                    "catalog_id": "F28",
                    "shell_path": "paper/figures/Figure28.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure28",
                    "template_id": "spatial_niche_map_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "spatial_niche_map_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "spatial_niche_map_inputs_v1",
            "displays": [_make_spatial_niche_map_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F28"]
    assert (paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_spatial",
        "panel_composition",
        "panel_heatmap",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["niche_labels"]) == ["Immune niche", "Stromal niche"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F28"
    assert figure_entry["template_id"] == full_id("spatial_niche_map_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "spatial_niche_map_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_spatial_niche_map_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_trajectory_progression_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure29",
                    "display_kind": "figure",
                    "requirement_key": "trajectory_progression_panel",
                    "catalog_id": "F29",
                    "shell_path": "paper/figures/Figure29.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure29",
                    "template_id": "trajectory_progression_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "trajectory_progression_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "trajectory_progression_inputs_v1",
            "displays": [_make_trajectory_progression_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F29"]
    assert (paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_trajectory",
        "panel_composition",
        "panel_heatmap",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["bin_labels"] == ["Early", "Mid", "Late"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F29"
    assert figure_entry["template_id"] == full_id("trajectory_progression_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "trajectory_progression_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_trajectory_progression_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_wraps_long_risk_layering_title_within_device(tmp_path: Path) -> None:
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
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "risk_layering",
                    "template_id": "risk_layering_monotonic_bars",
                    "layout_override": {
                        "show_figure_title": True,
                    },
                    "readability_override": {},
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
                    "template_id": "risk_layering_monotonic_bars",
                    "title": (
                        "Clinical utility of the clinically informed preoperative model compared "
                        "with the core preoperative comparator"
                    ),
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
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["qc_result"]["status"] == "pass"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F2_risk_layering_monotonic_bars.layout.json").read_text(
            encoding="utf-8"
        )
    )
    title_box = next(item for item in layout_sidecar["layout_boxes"] if item["box_id"] == "title")
    assert 0.0 <= title_box["x0"] <= 1.0
    assert 0.0 <= title_box["x1"] <= 1.0


def test_materialize_display_surface_generates_binary_calibration_decision_curve_panel(tmp_path: Path) -> None:
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
                    "calibration_axis_window": {"xmin": 0.0, "xmax": 0.5, "ymin": 0.0, "ymax": 0.35},
                    "calibration_reference_line": {"label": "Ideal", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    "calibration_series": [
                        {"label": "Core preoperative model", "x": [0.15, 0.25, 0.35, 0.45], "y": [0.04, 0.08, 0.16, 0.32]},
                        {
                            "label": "Clinically informed preoperative model",
                            "x": [0.05, 0.10, 0.18, 0.30],
                            "y": [0.03, 0.05, 0.14, 0.31],
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
    assert result["figures_materialized"] == ["F3"]
    assert (paper_root / "figures" / "generated" / "F3_binary_calibration_decision_curve_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F3_binary_calibration_decision_curve_panel.pdf").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["template_id"] == full_id("binary_calibration_decision_curve_panel")
    assert figure_entry["qc_result"]["status"] == "pass"


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


def test_materialize_display_surface_keeps_model_complexity_audit_audit_labels_clear_of_metric_column(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
                    "caption": "Discrimination, overall error, calibration, and bounded complexity audit across the candidate packages.",
                    "metric_panels": [
                        {
                            "panel_id": "auroc_panel",
                            "panel_label": "A",
                            "title": "Discrimination",
                            "x_label": "AUROC",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.8022},
                                {"label": "Clinically informed preoperative model", "value": 0.8004},
                                {"label": "Pathology-augmented model", "value": 0.7999},
                                {"label": "Elastic-net comparison model", "value": 0.8006},
                                {"label": "Random forest comparison model", "value": 0.8359},
                            ],
                        },
                        {
                            "panel_id": "brier_panel",
                            "panel_label": "B",
                            "title": "Overall error",
                            "x_label": "Brier score",
                            "rows": [
                                {"label": "Core preoperative model", "value": 0.1433},
                                {"label": "Clinically informed preoperative model", "value": 0.1099},
                                {"label": "Pathology-augmented model", "value": 0.1090},
                                {"label": "Elastic-net comparison model", "value": 0.1086},
                                {"label": "Random forest comparison model", "value": 0.1011},
                            ],
                        },
                        {
                            "panel_id": "slope_panel",
                            "panel_label": "C",
                            "title": "Calibration",
                            "x_label": "Calibration slope",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Core preoperative model", "value": 2.4065},
                                {"label": "Clinically informed preoperative model", "value": 1.0442},
                                {"label": "Pathology-augmented model", "value": 1.0395},
                                {"label": "Elastic-net comparison model", "value": 1.1096},
                                {"label": "Random forest comparison model", "value": 0.8017},
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
                                {"label": "Age", "value": 0.9117898553832784},
                                {"label": "Female sex", "value": 1.0309311059934487},
                                {"label": "Blurred Vision", "value": 1.183703663712767},
                                {"label": "Defect Field Vision", "value": 1.067175358232608},
                                {"label": "Preoperative hypopituitarism", "value": 1.121955952267307},
                                {"label": "Knosp grade", "value": 1.1321181751012195},
                                {"label": "Invasiveness", "value": 1.0176339267412329},
                                {"label": "Tumor diameter", "value": 1.443952677790654},
                                {"label": "Log Diameter", "value": 1.3878032746085207},
                                {"label": "Knosp Ge 3", "value": 1.0176339267412329},
                                {"label": "Knosp Ge 4", "value": 1.3314915096706699},
                                {"label": "Invasiveness Log Diameter", "value": 1.0860598862755477},
                            ],
                        },
                        {
                            "panel_id": "domain_panel",
                            "panel_label": "E",
                            "title": "Domain stability",
                            "x_label": "Mean absolute coefficient",
                            "rows": [
                                {"label": "Demographics", "value": 0.07697647508285217},
                                {"label": "Endocrine impairment", "value": 0.11428074753919776},
                                {"label": "Invasion burden", "value": 0.10914169938817306},
                                {"label": "Tumor burden", "value": 0.3444167074572295},
                                {"label": "Visual compromise", "value": 0.11849667910968223},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    captured_figures: list[Any] = []
    original_close = plt.close

    def _capture_close(fig: Any | None = None) -> None:
        if fig is not None:
            captured_figures.append(fig)

    monkeypatch.setattr(plt, "close", _capture_close)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert captured_figures

    figure = captured_figures[-1]
    figure.canvas.draw()
    renderer = figure.canvas.get_renderer()
    metric_axes = figure.axes[:3]
    audit_axes = figure.axes[3:]
    metric_column_right_edge = max(axes.get_window_extent(renderer=renderer).x1 for axes in metric_axes)
    audit_label_left_edge = min(
        label.get_window_extent(renderer=renderer).x0
        for axes in audit_axes
        for label in axes.get_yticklabels()
        if label.get_text().strip()
    )

    assert audit_label_left_edge - metric_column_right_edge >= 12.0

    original_close(figure)


def test_materialize_display_surface_omits_figure_title_for_model_complexity_audit_panel_by_default(
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
                    "title": "Threshold-based operating characteristics and risk-group profiles for the clinically informed preoperative model",
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
                    ],
                    "audit_panels": [
                        {
                            "panel_id": "coefficient_panel",
                            "panel_label": "C",
                            "title": "Coefficient stability",
                            "x_label": "Mean odds ratio",
                            "reference_value": 1.0,
                            "rows": [
                                {"label": "Age", "value": 0.91},
                                {"label": "Tumor diameter", "value": 1.44},
                                {"label": "Knosp grade", "value": 1.13},
                            ],
                        }
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
        (paper_root / "figures" / "generated" / "F4_model_complexity_audit_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert sum(1 for item in layout_sidecar["layout_boxes"] if item["box_type"] == "subplot_title") == 3

@pytest.mark.parametrize(
    ("template_id", "display_id"),
    [
        ("shap_summary_beeswarm", "Figure13"),
        ("time_to_event_discrimination_calibration_panel", "Figure14"),
        ("time_to_event_risk_group_summary", "Figure15"),
        ("time_to_event_decision_curve", "Figure16"),
        ("multicenter_generalizability_overview", "Figure17"),
    ],
)
def test_render_python_evidence_figure_emits_qc_passable_layout_sidecar(
    tmp_path: Path,
    template_id: str,
    display_id: str,
) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    qc_module = importlib.import_module("med_autoscience.display_layout_qc")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    spec = controller_module.display_registry.get_evidence_figure_spec(template_id)
    _, display_payload = controller_module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id=display_id,
    )
    if template_id in {
        "time_to_event_discrimination_calibration_panel",
        "time_to_event_risk_group_summary",
        "time_to_event_decision_curve",
        "multicenter_generalizability_overview",
    }:
        style_roles = {
            "model_curve": "#245A6B",
            "comparator_curve": "#B89A6D",
            "reference_line": "#6B7280",
        }
        if template_id == "time_to_event_decision_curve":
            style_roles["highlight_band"] = "#E7E1D8"
        display_payload = {
            **display_payload,
            "render_context": {
                "style_profile_id": "paper_neutral_clinical_v1",
                "style_roles": style_roles,
                "layout_override": {},
                "readability_override": {},
            },
        }
    output_png_path = tmp_path / f"{display_id}_{template_id}.png"
    output_pdf_path = tmp_path / f"{display_id}_{template_id}.pdf"
    layout_sidecar_path = tmp_path / f"{display_id}_{template_id}.layout.json"

    controller_module._render_python_evidence_figure(
        template_id=spec.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    qc_result = qc_module.run_display_layout_qc(
        qc_profile=spec.layout_qc_profile,
        layout_sidecar=layout_sidecar,
    )

    assert qc_result["status"] == "pass", qc_result
    assert qc_result["issues"] == []
    if template_id == "shap_summary_beeswarm":
        assert layout_sidecar["metrics"]["figure_height_inches"] > 0
        assert layout_sidecar["metrics"]["figure_width_inches"] > 0
        assert len(layout_sidecar["metrics"]["feature_labels"]) == 2
        feature_label_boxes = [box for box in layout_sidecar["layout_boxes"] if box["box_type"] == "feature_label"]
        feature_row_boxes = [box for box in layout_sidecar["layout_boxes"] if box["box_type"] == "feature_row"]
        assert len(feature_label_boxes) == 2
        assert len(feature_row_boxes) == 2
        assert all(box["x1"] <= layout_sidecar["panel_boxes"][0]["x0"] for box in feature_label_boxes)
        zero_line_box = next(box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "zero_line")
        panel_box = layout_sidecar["panel_boxes"][0]
        assert panel_box["y0"] <= zero_line_box["y0"] <= panel_box["y1"]
        assert panel_box["y0"] <= zero_line_box["y1"] <= panel_box["y1"]
        assert all(panel_box["y0"] <= box["y0"] <= panel_box["y1"] for box in feature_row_boxes)
        assert all(panel_box["y0"] <= box["y1"] <= panel_box["y1"] for box in feature_row_boxes)


def test_render_python_evidence_figure_uses_pack_entrypoint_for_time_to_event_risk_group_summary(
    tmp_path: Path,
    monkeypatch,
) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    spec = controller_module.display_registry.get_evidence_figure_spec("time_to_event_risk_group_summary")
    _, display_payload = controller_module._load_evidence_display_payload(
        paper_root=paper_root,
        spec=spec,
        display_id="Figure15",
    )
    display_payload = {
        **display_payload,
        "render_context": {
            "style_profile_id": "paper_neutral_clinical_v1",
            "style_roles": {
                "model_curve": "#245A6B",
                "comparator_curve": "#B89A6D",
                "reference_line": "#6B7280",
            },
            "layout_override": {},
            "readability_override": {},
        },
    }

    output_png_path = tmp_path / "Figure15_pack_entrypoint.png"
    output_pdf_path = tmp_path / "Figure15_pack_entrypoint.pdf"
    layout_sidecar_path = tmp_path / "Figure15_pack_entrypoint.layout.json"

    controller_module._render_python_evidence_figure(
        template_id=spec.template_id,
        display_payload=display_payload,
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert output_png_path.exists()
    assert output_pdf_path.exists()
    assert layout_sidecar_path.exists()


def test_render_r_evidence_figure_uses_pack_entrypoint_for_r_template(tmp_path: Path, monkeypatch) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    render_calls: list[str] = []

    def fake_external_renderer(
        *,
        template_id: str,
        display_payload: dict[str, object],
        output_png_path: Path,
        output_pdf_path: Path,
        layout_sidecar_path: Path,
    ) -> None:
        _ensure_output_parents(output_png_path, output_pdf_path, layout_sidecar_path)
        output_png_path.write_text("PNG", encoding="utf-8")
        output_pdf_path.write_text("%PDF", encoding="utf-8")
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append(template_id)

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "load_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )

    output_png_path = tmp_path / "Figure2_pack_entrypoint.png"
    output_pdf_path = tmp_path / "Figure2_pack_entrypoint.pdf"
    layout_sidecar_path = tmp_path / "Figure2_pack_entrypoint.layout.json"

    controller_module._render_r_evidence_figure(
        template_id=full_id("roc_curve_binary"),
        display_payload={"display_id": "Figure2"},
        output_png_path=output_png_path,
        output_pdf_path=output_pdf_path,
        layout_sidecar_path=layout_sidecar_path,
    )

    assert render_calls == [full_id("roc_curve_binary")]
    assert output_png_path.exists()
    assert output_pdf_path.exists()
    assert layout_sidecar_path.exists()


def test_render_cohort_flow_figure_uses_pack_entrypoint(tmp_path: Path, monkeypatch) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    render_calls: list[str] = []

    def fake_external_renderer(**kwargs: object) -> None:
        output_svg_path = kwargs["output_svg_path"]
        output_png_path = kwargs["output_png_path"]
        output_layout_path = kwargs["output_layout_path"]
        assert isinstance(output_svg_path, Path)
        assert isinstance(output_png_path, Path)
        assert isinstance(output_layout_path, Path)
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(json.dumps(_minimal_layout_sidecar_for_template(full_id("cohort_flow_figure"))), encoding="utf-8")
        render_calls.append("cohort_flow_figure")

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "load_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )
    monkeypatch.setattr(
        controller_module,
        "_run_graphviz_layout",
        lambda **_: (_ for _ in ()).throw(AssertionError("legacy cohort flow renderer should not run once pack entrypoint is active")),
    )

    controller_module._render_cohort_flow_figure(
        output_svg_path=tmp_path / "flow.svg",
        output_png_path=tmp_path / "flow.png",
        output_layout_path=tmp_path / "flow.layout.json",
        title="Cohort flow",
        steps=[{"step_id": "screened", "label": "Screened", "n": 10}],
        exclusions=[],
        endpoint_inventory=[],
        design_panels=[],
        render_context={},
    )

    assert render_calls == ["cohort_flow_figure"]


def test_render_submission_graphical_abstract_uses_pack_entrypoint(tmp_path: Path, monkeypatch) -> None:
    controller_module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    render_calls: list[str] = []

    def fake_external_renderer(**kwargs: object) -> None:
        output_svg_path = kwargs["output_svg_path"]
        output_png_path = kwargs["output_png_path"]
        output_layout_path = kwargs["output_layout_path"]
        assert isinstance(output_svg_path, Path)
        assert isinstance(output_png_path, Path)
        assert isinstance(output_layout_path, Path)
        _ensure_output_parents(output_svg_path, output_png_path, output_layout_path)
        output_svg_path.write_text("<svg />", encoding="utf-8")
        output_png_path.write_text("PNG", encoding="utf-8")
        output_layout_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(full_id("submission_graphical_abstract")), ensure_ascii=False),
            encoding="utf-8",
        )
        render_calls.append("submission_graphical_abstract")

    monkeypatch.setattr(
        controller_module.display_pack_runtime,
        "load_python_plugin_callable",
        lambda *, repo_root, template_id, paper_root=None: fake_external_renderer,
    )
    monkeypatch.setattr(
        controller_module,
        "_choose_shared_submission_graphical_abstract_arrow_lane",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("legacy graphical abstract renderer should not run once pack entrypoint is active")
        ),
    )

    controller_module._render_submission_graphical_abstract(
        output_svg_path=tmp_path / "ga.svg",
        output_png_path=tmp_path / "ga.png",
        output_layout_path=tmp_path / "ga.layout.json",
        shell_payload={"title": "GA", "panels": [], "footer_pills": []},
        render_context={},
    )

    assert render_calls == ["submission_graphical_abstract"]


def test_materialize_display_surface_uses_pack_entrypoint_for_table_shell(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path)
    render_calls: list[str] = []

    def fake_table_renderer(
        *,
        template_id: str,
        payload_path: Path,
        payload: dict[str, object],
        output_md_path: Path,
        output_csv_path: Path | None = None,
    ) -> dict[str, str]:
        _ensure_output_parents(output_md_path, output_csv_path)
        output_md_path.write_text(
            "# Baseline characteristics\n\n| Characteristic | Overall |\n| --- | --- |\n| Age | 61 |\n",
            encoding="utf-8",
        )
        if output_csv_path is not None:
            output_csv_path.write_text("Characteristic,Overall\nAge,61\n", encoding="utf-8")
        render_calls.append(template_id)
        assert payload_path.name == "baseline_characteristics_schema.json"
        assert payload["title"] == "Baseline characteristics"
        return {
            "title": "Baseline characteristics",
            "caption": "Baseline characteristics across prespecified groups.",
        }

    original_loader = module.display_pack_runtime.load_python_plugin_callable

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("table1_baseline_characteristics"):
            return fake_table_renderer
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)
    monkeypatch.setattr(
        module,
        "_write_table_outputs",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("legacy host table writer should not run once pack entrypoint is active")
        ),
        raising=False,
    )
    monkeypatch.setattr(
        module,
        "_write_rectangular_table_outputs",
        lambda **_: (_ for _ in ()).throw(
            AssertionError("legacy host table writer should not run once pack entrypoint is active")
        ),
        raising=False,
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert render_calls == [full_id("table1_baseline_characteristics")]


def test_materialize_display_surface_applies_publication_style_and_display_override(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "decision_curve",
                    "template_id": "time_to_event_decision_curve",
                    "layout_override": {
                        "highlight_band": {"xmin": 0.5, "xmax": 3.0, "unit": "percent"},
                        "legend_position": "lower_center",
                    },
                    "readability_override": {
                        "focus_window": {"panel_id": "A", "y_min": -0.002, "y_max": 0.006},
                    },
                }
            ],
        },
    )
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

    render_contexts: list[dict[str, object]] = []
    original_loader = module.display_pack_runtime.load_python_plugin_callable

    def fake_render_python_evidence_figure(
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
        layout_sidecar_path.write_text(
            json.dumps(_minimal_layout_sidecar_for_template(template_id), ensure_ascii=False),
            encoding="utf-8",
        )
        render_contexts.append(dict(display_payload.get("render_context") or {}))

    def fake_loader(*, repo_root: Path, template_id: str, paper_root: Path | None = None):
        if template_id == full_id("time_to_event_decision_curve"):
            return fake_render_python_evidence_figure
        return original_loader(repo_root=repo_root, template_id=template_id, paper_root=paper_root)

    monkeypatch.setattr(module.display_pack_runtime, "load_python_plugin_callable", fake_loader)

    report = module.materialize_display_surface(paper_root=paper_root)
    catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    f4 = next(item for item in catalog["figures"] if item["figure_id"] == "F4")
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F4_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )

    assert report["status"] == "materialized"
    assert len(render_contexts) == 1
    assert render_contexts[0]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert render_contexts[0]["style_roles"]["model_curve"] == "#245A6B"
    assert render_contexts[0]["layout_override"]["highlight_band"]["xmax"] == 3.0
    assert f4["render_context"]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert f4["render_context"]["style_roles"]["model_curve"] == "#245A6B"
    assert f4["render_context"]["layout_override"]["highlight_band"]["xmax"] == 3.0
    assert layout_sidecar["render_context"]["style_profile_id"] == "paper_neutral_clinical_v1"
    assert layout_sidecar["render_context"]["style_roles"]["model_curve"] == "#245A6B"
    assert layout_sidecar["render_context"]["layout_override"]["highlight_band"]["xmax"] == 3.0
    assert layout_sidecar["render_context"]["readability_override"]["focus_window"]["panel_id"] == "A"


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


def test_load_evidence_display_payload_rejects_incomplete_clustered_heatmap_grid(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    clustered_payload_path = paper_root / "clustered_heatmap_inputs.json"
    clustered_payload = json.loads(clustered_payload_path.read_text(encoding="utf-8"))
    clustered_payload["displays"][0]["cells"].pop()
    dump_json(clustered_payload_path, clustered_payload)

    spec = module.display_registry.get_evidence_figure_spec("clustered_heatmap")

    with pytest.raises(ValueError, match="must cover every declared row/column coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure21",
        )


def test_load_evidence_display_payload_rejects_gsva_heatmap_without_score_method(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "gsva_ssgsea_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "gsva_ssgsea_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure23",
                    "template_id": "gsva_ssgsea_heatmap",
                    "title": "GSVA heatmap for stromal programs",
                    "caption": "Pathway activity overview.",
                    "x_label": "Samples",
                    "y_label": "Gene-set programs",
                    "row_order": [{"label": "TGF-beta signaling"}],
                    "column_order": [{"label": "Sample-01"}],
                    "cells": [{"x": "Sample-01", "y": "TGF-beta signaling", "value": 0.58}],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("gsva_ssgsea_heatmap")

    with pytest.raises(ValueError, match="score_method"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure23",
        )


def test_load_evidence_display_payload_rejects_performance_heatmap_value_outside_unit_interval(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "performance_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "performance_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure25",
                    "template_id": "performance_heatmap",
                    "title": "AUC heatmap across APOE4 subgroups and predictor sets",
                    "caption": "Random-forest discrimination remains strongest for the integrated model across APOE4-stratified analyses.",
                    "x_label": "Analytic subgroup",
                    "y_label": "Predictor set",
                    "metric_name": "AUC",
                    "row_order": [
                        {"label": "Clinical baseline"},
                        {"label": "Integrated model"},
                    ],
                    "column_order": [
                        {"label": "All participants"},
                        {"label": "APOE4 carriers"},
                    ],
                    "cells": [
                        {"x": "All participants", "y": "Clinical baseline", "value": 0.71},
                        {"x": "APOE4 carriers", "y": "Clinical baseline", "value": 1.07},
                        {"x": "All participants", "y": "Integrated model", "value": 0.83},
                        {"x": "APOE4 carriers", "y": "Integrated model", "value": 0.79},
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("performance_heatmap")

    with pytest.raises(ValueError, match="must stay within \\[0, 1\\]"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure25",
        )


def test_load_evidence_display_payload_rejects_celltype_signature_heatmap_when_embedding_groups_and_columns_diverge(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "celltype_signature_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_signature_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "celltype_signature_heatmap",
                    "title": "Cell-type embedding and signature activity atlas",
                    "caption": "Embedding groups must stay aligned with declared heatmap columns.",
                    "embedding_panel_title": "Embedding by cell type",
                    "embedding_x_label": "UMAP 1",
                    "embedding_y_label": "UMAP 2",
                    "embedding_points": [
                        {"x": -2.1, "y": 1.0, "group": "T cells"},
                        {"x": 1.4, "y": -0.6, "group": "Myeloid"},
                    ],
                    "heatmap_panel_title": "Signature activity",
                    "heatmap_x_label": "Cell type",
                    "heatmap_y_label": "Program",
                    "score_method": "AUCell",
                    "row_order": [{"label": "IFN response"}],
                    "column_order": [{"label": "T cells"}, {"label": "B cells"}],
                    "cells": [
                        {"x": "T cells", "y": "IFN response", "value": 0.78},
                        {"x": "B cells", "y": "IFN response", "value": -0.22},
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("celltype_signature_heatmap")

    with pytest.raises(ValueError, match="column_order labels must match embedding point groups"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure26",
        )


def test_load_evidence_display_payload_rejects_grouped_risk_summary_when_events_exceed_sample_size(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    payload_path = paper_root / "time_to_event_grouped_inputs.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    display = next(item for item in payload["displays"] if item["display_id"] == "Figure15")
    display["risk_group_summaries"][1]["events_5y"] = display["risk_group_summaries"][1]["sample_size"] + 1
    dump_json(payload_path, payload)

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_risk_group_summary")

    with pytest.raises(ValueError, match="events_5y must not exceed \\.sample_size"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure15",
        )


def test_load_evidence_display_payload_rejects_time_to_event_calibration_when_events_exceed_group_size(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    payload_path = paper_root / "time_to_event_discrimination_calibration_inputs.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    display = next(item for item in payload["displays"] if item["display_id"] == "Figure14")
    display["calibration_summary"][0]["events_5y"] = display["calibration_summary"][0]["n"] + 1
    dump_json(payload_path, payload)

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")

    with pytest.raises(ValueError, match="events_5y must not exceed \\.n"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure14",
        )


def test_load_evidence_display_payload_rejects_time_to_event_calibration_when_callout_drifts_from_group_summary(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    payload_path = paper_root / "time_to_event_discrimination_calibration_inputs.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    display = next(item for item in payload["displays"] if item["display_id"] == "Figure14")
    display["calibration_callout"]["predicted_risk_5y"] = 0.999
    dump_json(payload_path, payload)

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")

    with pytest.raises(ValueError, match="calibration_callout must match the referenced calibration_summary row"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure14",
        )


def test_materialize_display_surface_preserves_structured_time_horizon_metrics_for_b_templates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)

    grouped_payload = json.loads((paper_root / "time_to_event_decision_curve_inputs.json").read_text(encoding="utf-8"))
    decision_display = next(item for item in grouped_payload["displays"] if item["display_id"] == "Figure16")
    decision_display["time_horizon_months"] = 24
    dump_json(paper_root / "time_to_event_decision_curve_inputs.json", grouped_payload)

    curve_payload = json.loads((paper_root / "binary_prediction_curve_inputs.json").read_text(encoding="utf-8"))
    roc_display = next(item for item in curve_payload["displays"] if item["display_id"] == "Figure18")
    roc_display["time_horizon_months"] = 24
    dump_json(paper_root / "binary_prediction_curve_inputs.json", curve_payload)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    f16_layout = json.loads(
        (paper_root / "figures" / "generated" / "F16_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )
    f18_layout = json.loads(
        (paper_root / "figures" / "generated" / "F18_time_dependent_roc_horizon.layout.json").read_text(
            encoding="utf-8"
        )
    )

    assert f16_layout["metrics"]["time_horizon_months"] == 24
    assert f18_layout["metrics"]["time_horizon_months"] == 24


def _make_stratified_cumulative_incidence_display(display_id: str = "Figure24") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_stratified_cumulative_incidence_panel",
        "title": "HTN-AI cumulative incidence of all-cause mortality across risk strata",
        "caption": (
            "Cumulative incidence curves stratified by baseline hypertension status, age band, and HTN-AI quintile."
        ),
        "x_label": "Years from index ECG",
        "y_label": "Cumulative incidence of all-cause mortality",
        "panels": [
            {
                "panel_id": "baseline_htn",
                "panel_label": "A",
                "title": "Baseline hypertension status",
                "annotation": "Gray test P < .001",
                "groups": [
                    {
                        "label": "HTN-AI+",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.04, 0.08, 0.13, 0.18],
                    },
                    {
                        "label": "HTN-AI−",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.02, 0.04, 0.06, 0.09],
                    },
                ],
            },
            {
                "panel_id": "age_band",
                "panel_label": "B",
                "title": "Age band",
                "annotation": "Gray test P < .001",
                "groups": [
                    {
                        "label": "Older",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.05, 0.10, 0.16, 0.22],
                    },
                    {
                        "label": "Younger",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.01, 0.03, 0.05, 0.07],
                    },
                ],
            },
            {
                "panel_id": "htn_ai_quintile",
                "panel_label": "C",
                "title": "HTN-AI quintile",
                "annotation": "Gray test P < .001",
                "groups": [
                    {
                        "label": "Q1",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.01, 0.02, 0.03, 0.05],
                    },
                    {
                        "label": "Q2",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.015, 0.03, 0.045, 0.06],
                    },
                    {
                        "label": "Q3",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.02, 0.04, 0.06, 0.09],
                    },
                    {
                        "label": "Q4",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.03, 0.06, 0.10, 0.14],
                    },
                    {
                        "label": "Q5",
                        "times": [0.0, 1.0, 2.0, 3.0, 4.0],
                        "values": [0.00, 0.05, 0.10, 0.16, 0.23],
                    },
                ],
            },
        ],
    }


def _make_time_dependent_roc_comparison_panel_display(display_id: str = "Figure25") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_dependent_roc_comparison_panel",
        "title": "Time-dependent ROC analyses for dementia risk across follow-up windows",
        "caption": (
            "Panelized time-dependent ROC analyses comparing overall follow-up with the first 15 years of follow-up."
        ),
        "x_label": "False-positive rate",
        "y_label": "True-positive rate",
        "panels": [
            {
                "panel_id": "overall_followup",
                "panel_label": "A",
                "title": "Overall follow-up",
                "analysis_window_label": "Overall follow-up",
                "annotation": "AUC = 0.84",
                "series": [
                    {
                        "label": "Locked dementia-risk model",
                        "x": [0.0, 0.08, 0.18, 0.33, 1.0],
                        "y": [0.0, 0.56, 0.72, 0.86, 1.0],
                    },
                    {
                        "label": "Clinical baseline",
                        "x": [0.0, 0.10, 0.24, 0.40, 1.0],
                        "y": [0.0, 0.48, 0.65, 0.79, 1.0],
                    },
                ],
                "reference_line": {
                    "label": "Chance",
                    "x": [0.0, 1.0],
                    "y": [0.0, 1.0],
                },
            },
            {
                "panel_id": "first_15_years",
                "panel_label": "B",
                "title": "First 15 years of follow-up",
                "analysis_window_label": "First 15 years of follow-up",
                "time_horizon_months": 180,
                "annotation": "AUC = 0.88",
                "series": [
                    {
                        "label": "Locked dementia-risk model",
                        "x": [0.0, 0.05, 0.14, 0.30, 1.0],
                        "y": [0.0, 0.60, 0.79, 0.90, 1.0],
                    },
                    {
                        "label": "Clinical baseline",
                        "x": [0.0, 0.09, 0.22, 0.39, 1.0],
                        "y": [0.0, 0.50, 0.68, 0.80, 1.0],
                    },
                ],
                "reference_line": {
                    "label": "Chance",
                    "x": [0.0, 1.0],
                    "y": [0.0, 1.0],
                },
            },
        ],
    }


def _make_time_to_event_landmark_performance_panel_display(display_id: str = "Figure27") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_landmark_performance_panel",
        "title": "Landmark survival performance summary across recurrence prediction windows",
        "caption": (
            "Discrimination, prediction error, and calibration slope were locked across forward landmark windows "
            "for dynamic recurrence-risk evaluation."
        ),
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
                "annotation": "Baseline postoperative window",
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


def test_load_evidence_display_payload_rejects_non_monotonic_stratified_cumulative_incidence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_stratified_cumulative_incidence_display()
    display_payload["panels"][2]["groups"][4]["values"][3] = 0.08
    dump_json(
        paper_root / "time_to_event_stratified_cumulative_incidence_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_stratified_cumulative_incidence_panel")

    with pytest.raises(ValueError, match="values must be monotonic non-decreasing"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure24",
        )


def test_load_evidence_display_payload_rejects_duplicate_panel_labels_for_stratified_cumulative_incidence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_stratified_cumulative_incidence_display()
    display_payload["panels"][1]["panel_label"] = "A"
    dump_json(
        paper_root / "time_to_event_stratified_cumulative_incidence_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_stratified_cumulative_incidence_panel")

    with pytest.raises(ValueError, match="panel_label must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure24",
        )


def test_materialize_display_surface_generates_stratified_cumulative_incidence_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure24",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_stratified_cumulative_incidence_panel",
                    "catalog_id": "F24",
                    "shell_path": "paper/figures/Figure24.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure24",
                    "template_id": "time_to_event_stratified_cumulative_incidence_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_stratified_cumulative_incidence_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "displays": [_make_stratified_cumulative_incidence_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F24"]
    assert (paper_root / "figures" / "generated" / "F24_time_to_event_stratified_cumulative_incidence_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F24_time_to_event_stratified_cumulative_incidence_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F24_time_to_event_stratified_cumulative_incidence_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["panel_label"] for item in layout_sidecar["metrics"]["panels"]] == ["A", "B", "C"]
    assert layout_sidecar["metrics"]["panels"][2]["groups"][-1]["label"] == "Q5"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F24"
    assert figure_entry["template_id"] == full_id("time_to_event_stratified_cumulative_incidence_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_stratified_cumulative_incidence_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_survival_curve"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_load_evidence_display_payload_rejects_non_positive_panel_horizon_for_time_dependent_roc_comparison_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_dependent_roc_comparison_panel_display()
    display_payload["panels"][1]["time_horizon_months"] = 0
    dump_json(
        paper_root / "time_dependent_roc_comparison_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_dependent_roc_comparison_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_dependent_roc_comparison_panel")

    with pytest.raises(ValueError, match="time_horizon_months must be >= 1"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure25",
        )


def test_load_evidence_display_payload_rejects_mismatched_panel_series_labels_for_time_dependent_roc_comparison_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_dependent_roc_comparison_panel_display()
    display_payload["panels"][1]["series"][1]["label"] = "Alternative baseline"
    dump_json(
        paper_root / "time_dependent_roc_comparison_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_dependent_roc_comparison_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_dependent_roc_comparison_panel")

    with pytest.raises(ValueError, match="series labels must match the first panel"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure25",
        )


def test_materialize_display_surface_generates_time_dependent_roc_comparison_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure25",
                    "display_kind": "figure",
                    "requirement_key": "time_dependent_roc_comparison_panel",
                    "catalog_id": "F25",
                    "shell_path": "paper/figures/Figure25.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure25",
                    "template_id": "time_dependent_roc_comparison_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_dependent_roc_comparison_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_dependent_roc_comparison_inputs_v1",
            "displays": [_make_time_dependent_roc_comparison_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F25"]
    assert (paper_root / "figures" / "generated" / "F25_time_dependent_roc_comparison_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F25_time_dependent_roc_comparison_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F25_time_dependent_roc_comparison_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert [item["panel_label"] for item in layout_sidecar["metrics"]["panels"]] == ["A", "B"]
    assert layout_sidecar["metrics"]["panels"][1]["time_horizon_months"] == 180
    assert layout_sidecar["metrics"]["panels"][1]["analysis_window_label"] == "First 15 years of follow-up"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F25"
    assert figure_entry["template_id"] == full_id("time_dependent_roc_comparison_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_dependent_roc_comparison_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_evidence_curve"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_load_evidence_display_payload_rejects_non_forward_prediction_window_for_landmark_performance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_landmark_performance_panel_display()
    display_payload["landmark_summaries"][1]["prediction_months"] = 6
    dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_landmark_performance_panel")

    with pytest.raises(ValueError, match="prediction_months must exceed landmark_months"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure27",
        )


def test_load_evidence_display_payload_rejects_brier_out_of_range_for_landmark_performance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_landmark_performance_panel_display()
    display_payload["landmark_summaries"][0]["brier_score"] = 1.2
    dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_landmark_performance_panel")

    with pytest.raises(ValueError, match="brier_score must stay within \\[0, 1\\]"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure27",
        )


def test_materialize_display_surface_generates_time_to_event_landmark_performance_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure27",
                    "template_id": "time_to_event_landmark_performance_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [_make_time_to_event_landmark_performance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F27"]
    assert (paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["metric_kind"] for item in layout_sidecar["metrics"]["metric_panels"]] == [
        "c_index",
        "brier_score",
        "calibration_slope",
    ]
    assert layout_sidecar["metrics"]["metric_panels"][1]["rows"][0]["value"] == 0.18
    assert layout_sidecar["metrics"]["metric_panels"][2]["reference_value"] == 1.0

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F27"
    assert figure_entry["template_id"] == full_id("time_to_event_landmark_performance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_landmark_performance_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_landmark_performance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def _make_shap_dependence_panel_display(display_id: str = "Figure28") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_dependence_panel",
        "title": "SHAP dependence panel for representative nonlinear feature effects",
        "caption": (
            "Feature-level SHAP dependence plots highlight nonlinear contribution structure and interaction patterns "
            "across the audited explanation surface."
        ),
        "y_label": "SHAP value",
        "colorbar_label": "Interaction feature value",
        "panels": [
            {
                "panel_id": "age_panel",
                "panel_label": "A",
                "title": "Age",
                "x_label": "Age (years)",
                "feature": "Age",
                "interaction_feature": "Albumin",
                "points": [
                    {"feature_value": 38.0, "shap_value": -0.22, "interaction_value": 3.1},
                    {"feature_value": 55.0, "shap_value": 0.04, "interaction_value": 4.2},
                    {"feature_value": 71.0, "shap_value": 0.31, "interaction_value": 4.8},
                ],
            },
            {
                "panel_id": "platelet_panel",
                "panel_label": "B",
                "title": "Platelet count",
                "x_label": "Platelets (10^9/L)",
                "feature": "Platelet count",
                "interaction_feature": "Age",
                "points": [
                    {"feature_value": 85.0, "shap_value": 0.28, "interaction_value": 72.0},
                    {"feature_value": 142.0, "shap_value": 0.02, "interaction_value": 59.0},
                    {"feature_value": 210.0, "shap_value": -0.19, "interaction_value": 44.0},
                ],
            },
        ],
    }


def test_load_evidence_display_payload_rejects_duplicate_panel_feature_for_shap_dependence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_dependence_panel_display()
    display_payload["panels"][1]["feature"] = "Age"
    dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_dependence_panel")

    with pytest.raises(ValueError, match="feature must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure28",
        )


def test_load_evidence_display_payload_rejects_non_finite_point_value_for_shap_dependence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_dependence_panel_display()
    display_payload["panels"][0]["points"][1]["interaction_value"] = float("nan")
    dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_dependence_panel")

    with pytest.raises(ValueError, match="point values must be finite"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure28",
        )


def test_materialize_display_surface_generates_shap_dependence_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure28",
                    "display_kind": "figure",
                    "requirement_key": "shap_dependence_panel",
                    "catalog_id": "F28",
                    "shell_path": "paper/figures/Figure28.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure28",
                    "template_id": "shap_dependence_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [_make_shap_dependence_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F28"]
    assert (paper_root / "figures" / "generated" / "F28_shap_dependence_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F28_shap_dependence_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F28_shap_dependence_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "zero_line"]) == 2
    assert any(item["box_type"] == "colorbar" for item in layout_sidecar["guide_boxes"])
    assert layout_sidecar["metrics"]["colorbar_label"] == "Interaction feature value"
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Platelet count"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F28"
    assert figure_entry["template_id"] == full_id("shap_dependence_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_dependence_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_dependence_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def _make_shap_waterfall_local_explanation_panel_display(display_id: str = "Figure33") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_waterfall_local_explanation_panel",
        "title": "SHAP waterfall local explanation panel for representative patient-level risk calls",
        "caption": (
            "Ordered case-level SHAP contributions show how the audited model output moves from baseline "
            "expectation to the final patient-level prediction."
        ),
        "x_label": "Predicted 1-year mortality probability",
        "panels": [
            {
                "panel_id": "case_a",
                "panel_label": "A",
                "title": "Representative high-risk case",
                "case_label": "Case 1 · 1-year mortality",
                "baseline_value": 0.18,
                "predicted_value": 0.39,
                "contributions": [
                    {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.12},
                    {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": 0.08},
                    {"feature": "Platelets", "feature_value_text": "210 ×10^9/L", "shap_value": -0.03},
                    {"feature": "Tumor size", "feature_value_text": "9.4 cm", "shap_value": 0.04},
                ],
            },
            {
                "panel_id": "case_b",
                "panel_label": "B",
                "title": "Representative lower-risk case",
                "case_label": "Case 2 · 1-year mortality",
                "baseline_value": 0.42,
                "predicted_value": 0.28,
                "contributions": [
                    {"feature": "Age", "feature_value_text": "49 years", "shap_value": -0.11},
                    {"feature": "Albumin", "feature_value_text": "4.5 g/dL", "shap_value": -0.07},
                    {"feature": "Tumor stage", "feature_value_text": "Stage II", "shap_value": 0.04},
                ],
            },
        ],
    }


def _make_shap_force_like_summary_panel_display(display_id: str = "Figure35") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_force_like_summary_panel",
        "title": "SHAP force-like summary panel for representative response phenotypes",
        "caption": (
            "Force-like local explanation lanes summarize which features push each representative case toward "
            "higher or lower predicted response probability."
        ),
        "x_label": "Predicted response probability",
        "panels": [
            {
                "panel_id": "case_a",
                "panel_label": "A",
                "title": "Representative responder",
                "case_label": "Case 1 · durable response",
                "baseline_value": 0.22,
                "predicted_value": 0.31,
                "contributions": [
                    {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.13},
                    {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": -0.04},
                ],
            },
            {
                "panel_id": "case_b",
                "panel_label": "B",
                "title": "Representative non-responder",
                "case_label": "Case 2 · early progression",
                "baseline_value": 0.57,
                "predicted_value": 0.48,
                "contributions": [
                    {"feature": "Tumor stage", "feature_value_text": "Stage III", "shap_value": -0.18},
                    {"feature": "Albumin", "feature_value_text": "4.6 g/dL", "shap_value": 0.09},
                ],
            },
        ],
    }


def _make_shap_grouped_local_explanation_panel_display(display_id: str = "Figure40") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_grouped_local_explanation_panel",
        "title": "SHAP grouped local explanation panel for representative phenotype comparison",
        "caption": (
            "Bounded grouped local explanation panels compare signed local feature contributions across "
            "representative phenotypes while preserving shared feature-order governance."
        ),
        "x_label": "Local SHAP contribution to predicted risk",
        "panels": [
            {
                "panel_id": "high_risk",
                "panel_label": "A",
                "title": "High-risk phenotype",
                "group_label": "Phenotype 1 · immune-inflamed",
                "baseline_value": 0.22,
                "predicted_value": 0.34,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": 0.14},
                    {"rank": 2, "feature": "Albumin", "shap_value": -0.05},
                    {"rank": 3, "feature": "Tumor size", "shap_value": 0.03},
                ],
            },
            {
                "panel_id": "low_risk",
                "panel_label": "B",
                "title": "Lower-risk phenotype",
                "group_label": "Phenotype 2 · stromal-low",
                "baseline_value": 0.18,
                "predicted_value": 0.12,
                "contributions": [
                    {"rank": 1, "feature": "Age", "shap_value": -0.07},
                    {"rank": 2, "feature": "Albumin", "shap_value": 0.02},
                    {"rank": 3, "feature": "Tumor size", "shap_value": -0.01},
                ],
            },
        ],
    }


def _make_partial_dependence_ice_panel_display(display_id: str = "Figure36") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "partial_dependence_ice_panel",
        "title": "Partial dependence and ICE panel for representative feature-response trajectories",
        "caption": (
            "Bounded PDP and ICE overlays summarize how key features move the audited model prediction "
            "across representative feature ranges."
        ),
        "y_label": "Predicted response probability",
        "panels": [
            {
                "panel_id": "age_panel",
                "panel_label": "A",
                "title": "Age",
                "x_label": "Age (years)",
                "feature": "Age",
                "reference_value": 60.0,
                "reference_label": "Median age",
                "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.16, 0.21, 0.27, 0.34]},
                "ice_curves": [
                    {"curve_id": "age_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.14, 0.19, 0.25, 0.33]},
                    {"curve_id": "age_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.17, 0.22, 0.29, 0.36]},
                    {"curve_id": "age_case_3", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.18, 0.23, 0.28, 0.35]},
                ],
            },
            {
                "panel_id": "albumin_panel",
                "panel_label": "B",
                "title": "Albumin",
                "x_label": "Albumin (g/dL)",
                "feature": "Albumin",
                "reference_value": 3.8,
                "reference_label": "Median albumin",
                "pdp_curve": {"x": [2.8, 3.4, 4.0, 4.6], "y": [0.39, 0.31, 0.25, 0.20]},
                "ice_curves": [
                    {"curve_id": "alb_case_1", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.41, 0.33, 0.26, 0.21]},
                    {"curve_id": "alb_case_2", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.37, 0.30, 0.24, 0.18]},
                    {"curve_id": "alb_case_3", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.40, 0.32, 0.27, 0.22]},
                ],
            },
        ],
    }


def _make_shap_bar_importance_display(display_id: str = "Figure37") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_bar_importance",
        "title": "SHAP bar importance panel for audited global feature ranking",
        "caption": (
            "Bounded SHAP importance bars summarize the top global drivers of the audited model prediction "
            "surface using a stable ranked-importance contract."
        ),
        "x_label": "Mean absolute SHAP value",
        "bars": [
            {"rank": 1, "feature": "Age", "importance_value": 0.184},
            {"rank": 2, "feature": "Albumin", "importance_value": 0.133},
            {"rank": 3, "feature": "Tumor size", "importance_value": 0.096},
            {"rank": 4, "feature": "Platelet count", "importance_value": 0.071},
        ],
    }


def _make_shap_signed_importance_panel_display(display_id: str = "Figure38") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_signed_importance_panel",
        "title": "SHAP signed importance panel for audited directional feature influence",
        "caption": (
            "Bounded signed-importance bars summarize the net directional contribution of the top global drivers "
            "while keeping zero-centered geometry and polarity semantics manuscript-facing and auditable."
        ),
        "x_label": "Mean signed SHAP value",
        "negative_label": "Protective direction",
        "positive_label": "Risk direction",
        "bars": [
            {"rank": 1, "feature": "Albumin", "signed_importance_value": -0.118},
            {"rank": 2, "feature": "Age", "signed_importance_value": 0.104},
            {"rank": 3, "feature": "Tumor size", "signed_importance_value": 0.081},
            {"rank": 4, "feature": "Platelet count", "signed_importance_value": -0.064},
        ],
    }


def _make_shap_multicohort_importance_panel_display(display_id: str = "Figure39") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "shap_multicohort_importance_panel",
        "title": "SHAP multicohort importance panel for audited cross-cohort feature ranking",
        "caption": (
            "Bounded multi-panel SHAP importance views compare stable ranked feature drivers across audited cohorts "
            "without giving up deterministic panel contracts or manuscript-facing readability."
        ),
        "x_label": "Mean absolute SHAP value",
        "panels": [
            {
                "panel_id": "derivation",
                "panel_label": "A",
                "title": "Derivation cohort",
                "cohort_label": "Derivation",
                "bars": [
                    {"rank": 1, "feature": "Age", "importance_value": 0.184},
                    {"rank": 2, "feature": "Albumin", "importance_value": 0.133},
                    {"rank": 3, "feature": "Tumor size", "importance_value": 0.096},
                    {"rank": 4, "feature": "Platelet count", "importance_value": 0.071},
                ],
            },
            {
                "panel_id": "validation",
                "panel_label": "B",
                "title": "External validation cohort",
                "cohort_label": "Validation",
                "bars": [
                    {"rank": 1, "feature": "Age", "importance_value": 0.171},
                    {"rank": 2, "feature": "Albumin", "importance_value": 0.121},
                    {"rank": 3, "feature": "Tumor size", "importance_value": 0.089},
                    {"rank": 4, "feature": "Platelet count", "importance_value": 0.067},
                ],
            },
        ],
    }


def _make_generalizability_subgroup_composite_panel_display(display_id: str = "Figure34") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "generalizability_subgroup_composite_panel",
        "title": "Generalizability and subgroup discrimination composite for external validation",
        "caption": (
            "Bounded composite lock for overall external generalizability and prespecified subgroup discrimination "
            "stability."
        ),
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
            {
                "cohort_id": "temporal",
                "cohort_label": "Temporal",
                "support_count": 142,
                "event_count": 18,
                "metric_value": 0.80,
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
            {
                "subgroup_id": "high_risk",
                "subgroup_label": "High-risk surgery",
                "group_n": 96,
                "estimate": 0.84,
                "lower": 0.79,
                "upper": 0.89,
            },
        ],
    }


def test_load_evidence_display_payload_rejects_additive_mismatch_for_shap_waterfall_local_explanation_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_waterfall_local_explanation_panel_display()
    display_payload["panels"][0]["predicted_value"] = 0.5
    dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_waterfall_local_explanation_panel")

    with pytest.raises(ValueError, match="predicted_value must equal baseline_value plus contribution sum"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure33",
        )


def test_load_evidence_display_payload_rejects_zero_contribution_for_shap_waterfall_local_explanation_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_waterfall_local_explanation_panel_display()
    display_payload["panels"][1]["contributions"][1]["shap_value"] = 0.0
    dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_waterfall_local_explanation_panel")

    with pytest.raises(ValueError, match="contributions\\[1\\]\\.shap_value must be finite and non-zero"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure33",
        )


def test_load_evidence_display_payload_rejects_unsorted_force_like_contributions(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_force_like_summary_panel_display()
    display_payload["panels"][0]["contributions"] = [
        {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": -0.04},
        {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.13},
    ]
    dump_json(
        paper_root / "shap_force_like_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_force_like_summary_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_force_like_summary_panel")

    with pytest.raises(
        ValueError,
        match="contributions must be sorted by descending absolute shap_value within each panel",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure35",
        )


def test_load_evidence_display_payload_rejects_feature_order_mismatch_for_shap_grouped_local_explanation_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_grouped_local_explanation_panel_display()
    display_payload["panels"][1]["contributions"][0]["feature"] = "Albumin"
    display_payload["panels"][1]["contributions"][1]["feature"] = "Age"
    dump_json(
        paper_root / "shap_grouped_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_local_explanation_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_grouped_local_explanation_panel")

    with pytest.raises(ValueError, match="contribution feature order must match across panels"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure40",
        )


def test_load_evidence_display_payload_rejects_ice_curve_grid_mismatch_for_partial_dependence_ice_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_partial_dependence_ice_panel_display()
    display_payload["panels"][0]["ice_curves"][1]["x"] = [40.0, 52.0, 60.0, 70.0]
    dump_json(
        paper_root / "partial_dependence_ice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_ice_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("partial_dependence_ice_panel")

    with pytest.raises(
        ValueError,
        match="ice_curves\\[1\\]\\.x must match pdp_curve.x within each panel",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure36",
        )


def test_load_evidence_display_payload_rejects_partial_comparator_metrics_for_generalizability_subgroup_composite_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_generalizability_subgroup_composite_panel_display()
    del display_payload["overview_rows"][1]["comparator_metric_value"]
    dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("generalizability_subgroup_composite_panel")

    with pytest.raises(
        ValueError,
        match="comparator_metric_value must be provided for every overview row when comparator_label is declared",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure34",
        )


def test_materialize_display_surface_generates_shap_waterfall_local_explanation_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure33",
                    "display_kind": "figure",
                    "requirement_key": "shap_waterfall_local_explanation_panel",
                    "catalog_id": "F33",
                    "shell_path": "paper/figures/Figure33.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure33",
                    "template_id": "shap_waterfall_local_explanation_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [_make_shap_waterfall_local_explanation_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F33"]
    assert (paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "baseline_marker"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "prediction_marker"]) == 2
    assert [item["case_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Case 1 · 1-year mortality",
        "Case 2 · 1-year mortality",
    ]
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["feature"] == "Age"
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["feature_value_text"] == "74 years"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F33"
    assert figure_entry["template_id"] == full_id("shap_waterfall_local_explanation_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_waterfall_local_explanation_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_waterfall_local_explanation_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_shap_force_like_summary_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure35",
                    "display_kind": "figure",
                    "requirement_key": "shap_force_like_summary_panel",
                    "catalog_id": "F35",
                    "shell_path": "paper/figures/Figure35.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure35",
                    "template_id": "shap_force_like_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_force_like_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_force_like_summary_panel_inputs_v1",
            "displays": [_make_shap_force_like_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F35"]
    assert (paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "baseline_marker"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "prediction_marker"]) == 2
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["direction"] == "positive"
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][1]["direction"] == "negative"
    assert layout_sidecar["metrics"]["panels"][1]["contributions"][0]["feature"] == "Tumor stage"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F35"
    assert figure_entry["template_id"] == full_id("shap_force_like_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_force_like_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_force_like_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_shap_grouped_local_explanation_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure40",
                    "display_kind": "figure",
                    "requirement_key": "shap_grouped_local_explanation_panel",
                    "catalog_id": "F40",
                    "shell_path": "paper/figures/Figure40.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure40",
                    "template_id": "shap_grouped_local_explanation_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_grouped_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_local_explanation_panel_inputs_v1",
            "displays": [_make_shap_grouped_local_explanation_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F40"]
    assert (paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "zero_line"]) == 2
    assert [item["group_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Phenotype 1 · immune-inflamed",
        "Phenotype 2 · stromal-low",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][0]["contributions"]] == [
        "Age",
        "Albumin",
        "Tumor size",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][1]["contributions"]] == [
        "Age",
        "Albumin",
        "Tumor size",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F40"
    assert figure_entry["template_id"] == full_id("shap_grouped_local_explanation_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_grouped_local_explanation_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_grouped_local_explanation_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_partial_dependence_ice_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure36",
                    "display_kind": "figure",
                    "requirement_key": "partial_dependence_ice_panel",
                    "catalog_id": "F36",
                    "shell_path": "paper/figures/Figure36.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure36",
                    "template_id": "partial_dependence_ice_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "partial_dependence_ice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_ice_panel_inputs_v1",
            "displays": [_make_partial_dependence_ice_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F36"]
    assert (paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_type"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "pdp_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == ["ICE curves", "PDP mean"]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["panels"][0]["reference_label"] == "Median age"
    assert len(layout_sidecar["metrics"]["panels"][0]["ice_curves"]) == 3

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F36"
    assert figure_entry["template_id"] == full_id("partial_dependence_ice_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "partial_dependence_ice_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_partial_dependence_ice_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_load_evidence_display_payload_rejects_duplicate_feature_for_shap_bar_importance(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_bar_importance_display()
    display_payload["bars"][2]["feature"] = "Albumin"
    dump_json(
        paper_root / "shap_bar_importance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_bar_importance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_bar_importance")

    with pytest.raises(ValueError, match="feature must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure37",
        )


def test_load_evidence_display_payload_rejects_zero_signed_importance_for_shap_signed_importance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_signed_importance_panel_display()
    display_payload["bars"][2]["signed_importance_value"] = 0.0
    dump_json(
        paper_root / "shap_signed_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_signed_importance_panel")

    with pytest.raises(ValueError, match="signed_importance_value must be finite and non-zero"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure38",
        )


def test_load_evidence_display_payload_rejects_feature_order_mismatch_for_shap_multicohort_importance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_multicohort_importance_panel_display()
    display_payload["panels"][1]["bars"][1]["feature"] = "Platelet count"
    display_payload["panels"][1]["bars"][3]["feature"] = "Albumin"
    dump_json(
        paper_root / "shap_multicohort_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multicohort_importance_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_multicohort_importance_panel")

    with pytest.raises(ValueError, match="bars feature order must match across panels"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure39",
        )


def test_materialize_display_surface_generates_shap_bar_importance(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure37",
                    "display_kind": "figure",
                    "requirement_key": "shap_bar_importance",
                    "catalog_id": "F37",
                    "shell_path": "paper/figures/Figure37.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure37",
                    "template_id": "shap_bar_importance",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_bar_importance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_bar_importance_inputs_v1",
            "displays": [_make_shap_bar_importance_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F37"]
    assert (paper_root / "figures" / "generated" / "F37_shap_bar_importance.png").exists()
    assert (paper_root / "figures" / "generated" / "F37_shap_bar_importance.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F37_shap_bar_importance.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(item["box_type"] == "importance_bar" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "feature_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "value_label" for item in layout_sidecar["layout_boxes"])
    assert [item["feature"] for item in layout_sidecar["metrics"]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert layout_sidecar["metrics"]["bars"][0]["importance_value"] == 0.184

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F37"
    assert figure_entry["template_id"] == full_id("shap_bar_importance")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_bar_importance_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_bar_importance"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_shap_signed_importance_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure38",
                    "display_kind": "figure",
                    "requirement_key": "shap_signed_importance_panel",
                    "catalog_id": "F38",
                    "shell_path": "paper/figures/Figure38.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure38",
                    "template_id": "shap_signed_importance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_signed_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_panel_inputs_v1",
            "displays": [_make_shap_signed_importance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F38"]
    assert (paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(item["box_type"] == "importance_bar" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "negative_direction_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "positive_direction_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "zero_line" for item in layout_sidecar["guide_boxes"])
    assert [item["feature"] for item in layout_sidecar["metrics"]["bars"]] == [
        "Albumin",
        "Age",
        "Tumor size",
        "Platelet count",
    ]
    assert [item["direction"] for item in layout_sidecar["metrics"]["bars"]] == [
        "negative",
        "positive",
        "positive",
        "negative",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F38"
    assert figure_entry["template_id"] == full_id("shap_signed_importance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_signed_importance_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_signed_importance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_shap_multicohort_importance_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure39",
                    "display_kind": "figure",
                    "requirement_key": "shap_multicohort_importance_panel",
                    "catalog_id": "F39",
                    "shell_path": "paper/figures/Figure39.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure39",
                    "template_id": "shap_multicohort_importance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_multicohort_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multicohort_importance_panel_inputs_v1",
            "displays": [_make_shap_multicohort_importance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F39"]
    assert (paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert [item["cohort_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Derivation",
        "Validation",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][0]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][1]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F39"
    assert figure_entry["template_id"] == full_id("shap_multicohort_importance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_multicohort_importance_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_multicohort_importance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_materialize_display_surface_generates_generalizability_subgroup_composite_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
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
    dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [_make_generalizability_subgroup_composite_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F34"]
    assert (paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
    assert layout_sidecar["metrics"]["metric_family"] == "discrimination"
    assert layout_sidecar["metrics"]["primary_label"] == "Locked model"
    assert layout_sidecar["metrics"]["comparator_label"] == "Derivation cohort"
    assert [item["cohort_label"] for item in layout_sidecar["metrics"]["overview_rows"]] == [
        "External A",
        "External B",
        "Temporal",
    ]
    assert layout_sidecar["metrics"]["subgroup_reference_value"] == 0.80
    assert layout_sidecar["metrics"]["subgroup_rows"][0]["subgroup_label"] == "Age ≥65 years"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F34"
    assert figure_entry["template_id"] == full_id("generalizability_subgroup_composite_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "generalizability_subgroup_composite_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_generalizability_subgroup_composite_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def _make_time_to_event_threshold_governance_panel_display(display_id: str = "Figure29") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_threshold_governance_panel",
        "title": "Time-to-event threshold governance panel for deployment-facing operating review",
        "caption": (
            "Structured threshold summary and grouped calibration governance lock the manuscript-facing operating "
            "threshold discussion to explicit audited inputs."
        ),
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


def _make_time_to_event_multihorizon_calibration_panel_display(display_id: str = "Figure30") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "time_to_event_multihorizon_calibration_panel",
        "title": "Multi-horizon grouped survival calibration governance",
        "caption": (
            "Prespecified grouped calibration at 36 and 60 months is locked to explicit audited panel contracts "
            "instead of manuscript-local freehand composition."
        ),
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


def test_load_evidence_display_payload_rejects_duplicate_threshold_label_for_threshold_governance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_threshold_governance_panel_display()
    display_payload["threshold_summaries"][1]["threshold_label"] = "Rule-in"
    dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_threshold_governance_panel")

    with pytest.raises(ValueError, match="threshold_label must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure29",
        )


def test_load_evidence_display_payload_rejects_invalid_risk_probability_for_threshold_governance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_threshold_governance_panel_display()
    display_payload["risk_group_summaries"][1]["observed_risk"] = 1.4
    dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_threshold_governance_panel")

    with pytest.raises(ValueError, match="observed_risk"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure29",
        )


def test_materialize_display_surface_generates_time_to_event_threshold_governance_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
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
    dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [_make_time_to_event_threshold_governance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F29"]
    assert (paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([item for item in layout_sidecar["layout_boxes"] if item["box_type"] == "threshold_card"]) == 2
    assert any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
    assert [item["threshold"] for item in layout_sidecar["metrics"]["threshold_summaries"]] == [0.10, 0.15]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["risk_group_summaries"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F29"
    assert figure_entry["template_id"] == full_id("time_to_event_threshold_governance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_threshold_governance_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_time_to_event_threshold_governance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"


def test_load_evidence_display_payload_rejects_non_positive_panel_horizon_for_multihorizon_calibration_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_multihorizon_calibration_panel_display()
    display_payload["panels"][0]["time_horizon_months"] = 0
    dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_multihorizon_calibration_panel")

    with pytest.raises(ValueError, match="time_horizon_months"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure30",
        )


def test_load_evidence_display_payload_rejects_non_increasing_group_order_for_multihorizon_calibration_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_multihorizon_calibration_panel_display()
    display_payload["panels"][0]["calibration_summary"][1]["group_order"] = 1
    dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_multihorizon_calibration_panel")

    with pytest.raises(ValueError, match="group_order must be strictly increasing"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure30",
        )


def test_materialize_display_surface_generates_time_to_event_multihorizon_calibration_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
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
    dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [_make_time_to_event_multihorizon_calibration_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F30"]
    assert (paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert all(item["box_type"] == "calibration_panel" for item in layout_sidecar["panel_boxes"])
    assert any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
    assert [item["time_horizon_months"] for item in layout_sidecar["metrics"]["panels"]] == [36, 60]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["panels"][1]["calibration_summary"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F30"
    assert figure_entry["template_id"] == full_id("time_to_event_multihorizon_calibration_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_multihorizon_calibration_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_time_to_event_multihorizon_calibration_panel"
    assert figure_entry["qc_result"]["status"] == "pass"
