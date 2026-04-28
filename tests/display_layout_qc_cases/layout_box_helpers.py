from __future__ import annotations

from . import shared_base as _shared_base

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)

def make_box(
    box_id: str,
    box_type: str,
    *,
    x0: float,
    y0: float,
    x1: float,
    y1: float,
) -> dict[str, object]:
    return {
        "box_id": box_id,
        "box_type": box_type,
        "x0": x0,
        "y0": y0,
        "x1": x1,
        "y1": y1,
    }

def make_device() -> dict[str, float]:
    return {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0}

def _make_shap_grouped_local_support_domain_layout_sidecar() -> dict[str, object]:
    return {
        "template_id": "shap_grouped_local_support_domain_panel",
        "device": make_device(),
        "render_context": {"layout_override": {"show_figure_title": False}},
        "layout_boxes": [
            make_box("panel_title_A", "panel_title", x0=0.12, y0=0.89, x1=0.29, y1=0.92),
            make_box("panel_title_B", "panel_title", x0=0.51, y0=0.89, x1=0.71, y1=0.92),
            make_box("panel_label_A", "panel_label", x0=0.11, y0=0.82, x1=0.13, y1=0.85),
            make_box("panel_label_B", "panel_label", x0=0.50, y0=0.82, x1=0.52, y1=0.85),
            make_box("group_label_A", "group_label", x0=0.16, y0=0.83, x1=0.31, y1=0.86),
            make_box("group_label_B", "group_label", x0=0.55, y0=0.83, x1=0.71, y1=0.86),
            make_box("baseline_label_A", "baseline_label", x0=0.16, y0=0.77, x1=0.23, y1=0.80),
            make_box("baseline_label_B", "baseline_label", x0=0.55, y0=0.77, x1=0.62, y1=0.80),
            make_box("prediction_label_A", "prediction_label", x0=0.25, y0=0.77, x1=0.32, y1=0.80),
            make_box("prediction_label_B", "prediction_label", x0=0.63, y0=0.77, x1=0.71, y1=0.80),
            make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.50, x1=0.35, y1=0.53),
            make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.57, y0=0.50, x1=0.74, y1=0.53),
            make_box("feature_label_A_1", "feature_label", x0=0.02, y0=0.72, x1=0.09, y1=0.77),
            make_box("feature_label_A_2", "feature_label", x0=0.01, y0=0.63, x1=0.09, y1=0.68),
            make_box("feature_label_A_3", "feature_label", x0=0.00, y0=0.58, x1=0.09, y1=0.63),
            make_box("feature_label_B_1", "feature_label", x0=0.40, y0=0.72, x1=0.47, y1=0.77),
            make_box("feature_label_B_2", "feature_label", x0=0.39, y0=0.63, x1=0.47, y1=0.68),
            make_box("feature_label_B_3", "feature_label", x0=0.38, y0=0.58, x1=0.47, y1=0.63),
            make_box("contribution_bar_A_1", "contribution_bar", x0=0.22, y0=0.72, x1=0.34, y1=0.77),
            make_box("contribution_bar_A_2", "contribution_bar", x0=0.12, y0=0.63, x1=0.22, y1=0.68),
            make_box("contribution_bar_A_3", "contribution_bar", x0=0.22, y0=0.58, x1=0.25, y1=0.63),
            make_box("contribution_bar_B_1", "contribution_bar", x0=0.45, y0=0.72, x1=0.54, y1=0.77),
            make_box("contribution_bar_B_2", "contribution_bar", x0=0.54, y0=0.63, x1=0.57, y1=0.68),
            make_box("contribution_bar_B_3", "contribution_bar", x0=0.53, y0=0.58, x1=0.54, y1=0.63),
            make_box("value_label_A_1", "value_label", x0=0.35, y0=0.72, x1=0.40, y1=0.77),
            make_box("value_label_A_2", "value_label", x0=0.07, y0=0.63, x1=0.11, y1=0.68),
            make_box("value_label_A_3", "value_label", x0=0.26, y0=0.58, x1=0.31, y1=0.63),
            make_box("value_label_B_1", "value_label", x0=0.40, y0=0.72, x1=0.44, y1=0.77),
            make_box("value_label_B_2", "value_label", x0=0.58, y0=0.63, x1=0.62, y1=0.68),
            make_box("value_label_B_3", "value_label", x0=0.47, y0=0.58, x1=0.52, y1=0.63),
            make_box("panel_title_C", "panel_title", x0=0.12, y0=0.45, x1=0.30, y1=0.48),
            make_box("panel_title_D", "panel_title", x0=0.49, y0=0.45, x1=0.69, y1=0.48),
            make_box("panel_label_C", "panel_label", x0=0.12, y0=0.34, x1=0.14, y1=0.37),
            make_box("panel_label_D", "panel_label", x0=0.49, y0=0.34, x1=0.51, y1=0.37),
            make_box("x_axis_title_C", "subplot_x_axis_title", x0=0.16, y0=0.02, x1=0.29, y1=0.05),
            make_box("x_axis_title_D", "subplot_x_axis_title", x0=0.54, y0=0.02, x1=0.69, y1=0.05),
            make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.15, x1=0.07, y1=0.35),
            make_box("reference_label_C", "support_domain_reference_label", x0=0.20, y0=0.35, x1=0.28, y1=0.38),
            make_box("reference_label_D", "support_domain_reference_label", x0=0.58, y0=0.35, x1=0.68, y1=0.38),
            make_box("support_label_C_1", "support_label", x0=0.12, y0=0.10, x1=0.18, y1=0.13),
            make_box("support_label_C_2", "support_label", x0=0.18, y0=0.10, x1=0.24, y1=0.13),
            make_box("support_label_C_3", "support_label", x0=0.24, y0=0.10, x1=0.28, y1=0.13),
            make_box("support_label_C_4", "support_label", x0=0.28, y0=0.10, x1=0.33, y1=0.13),
            make_box("support_label_D_1", "support_label", x0=0.49, y0=0.10, x1=0.56, y1=0.13),
            make_box("support_label_D_2", "support_label", x0=0.56, y0=0.10, x1=0.61, y1=0.13),
            make_box("support_label_D_3", "support_label", x0=0.61, y0=0.10, x1=0.65, y1=0.13),
            make_box("support_label_D_4", "support_label", x0=0.65, y0=0.10, x1=0.72, y1=0.13),
            make_box("support_legend_title", "legend_title", x0=0.32, y0=0.01, x1=0.46, y1=0.04),
            make_box("support_legend_box", "legend_box", x0=0.23, y0=0.00, x1=0.77, y1=0.08),
        ],
        "panel_boxes": [
            make_box("panel_A", "panel", x0=0.12, y0=0.56, x1=0.40, y1=0.82),
            make_box("panel_B", "panel", x0=0.51, y0=0.56, x1=0.78, y1=0.82),
            make_box("panel_C", "panel", x0=0.11, y0=0.08, x1=0.34, y1=0.38),
            make_box("panel_D", "panel", x0=0.48, y0=0.08, x1=0.73, y1=0.38),
        ],
        "guide_boxes": [
            make_box("zero_line_A", "zero_line", x0=0.22, y0=0.56, x1=0.221, y1=0.82),
            make_box("zero_line_B", "zero_line", x0=0.54, y0=0.56, x1=0.541, y1=0.82),
            make_box("reference_line_C", "support_domain_reference_line", x0=0.22, y0=0.08, x1=0.221, y1=0.38),
            make_box("reference_line_D", "support_domain_reference_line", x0=0.60, y0=0.08, x1=0.601, y1=0.38),
            make_box("support_segment_C_1", "support_domain_segment", x0=0.12, y0=0.08, x1=0.18, y1=0.15),
            make_box("support_segment_C_2", "support_domain_segment", x0=0.18, y0=0.08, x1=0.24, y1=0.15),
            make_box("support_segment_C_3", "support_domain_segment", x0=0.24, y0=0.08, x1=0.29, y1=0.15),
            make_box("support_segment_C_4", "support_domain_segment", x0=0.29, y0=0.08, x1=0.33, y1=0.15),
            make_box("support_segment_D_1", "support_domain_segment", x0=0.49, y0=0.08, x1=0.56, y1=0.15),
            make_box("support_segment_D_2", "support_domain_segment", x0=0.56, y0=0.08, x1=0.61, y1=0.15),
            make_box("support_segment_D_3", "support_domain_segment", x0=0.61, y0=0.08, x1=0.66, y1=0.15),
            make_box("support_segment_D_4", "support_domain_segment", x0=0.66, y0=0.08, x1=0.72, y1=0.15),
        ],
        "metrics": {
            "local_shared_feature_order": ["Age", "Albumin", "Tumor size"],
            "support_y_label": "Predicted response probability",
            "support_legend_title": "Support domain",
            "support_legend_labels": [
                "Response curve",
                "Observed support",
                "Subgroup support",
                "Bin support",
                "Extrapolation reminder",
            ],
            "local_panels": [
                {
                    "panel_id": "high_risk",
                    "panel_label": "A",
                    "title": "High-risk phenotype",
                    "group_label": "Phenotype 1",
                    "baseline_value": 0.22,
                    "predicted_value": 0.34,
                    "panel_box_id": "panel_A",
                    "zero_line_box_id": "zero_line_A",
                    "contributions": [
                        {
                            "rank": 1,
                            "feature": "Age",
                            "shap_value": 0.14,
                            "bar_box_id": "contribution_bar_A_1",
                            "feature_label_box_id": "feature_label_A_1",
                            "value_label_box_id": "value_label_A_1",
                        },
                        {
                            "rank": 2,
                            "feature": "Albumin",
                            "shap_value": -0.05,
                            "bar_box_id": "contribution_bar_A_2",
                            "feature_label_box_id": "feature_label_A_2",
                            "value_label_box_id": "value_label_A_2",
                        },
                        {
                            "rank": 3,
                            "feature": "Tumor size",
                            "shap_value": 0.03,
                            "bar_box_id": "contribution_bar_A_3",
                            "feature_label_box_id": "feature_label_A_3",
                            "value_label_box_id": "value_label_A_3",
                        },
                    ],
                },
                {
                    "panel_id": "low_risk",
                    "panel_label": "B",
                    "title": "Lower-risk phenotype",
                    "group_label": "Phenotype 2",
                    "baseline_value": 0.18,
                    "predicted_value": 0.12,
                    "panel_box_id": "panel_B",
                    "zero_line_box_id": "zero_line_B",
                    "contributions": [
                        {
                            "rank": 1,
                            "feature": "Age",
                            "shap_value": -0.07,
                            "bar_box_id": "contribution_bar_B_1",
                            "feature_label_box_id": "feature_label_B_1",
                            "value_label_box_id": "value_label_B_1",
                        },
                        {
                            "rank": 2,
                            "feature": "Albumin",
                            "shap_value": 0.02,
                            "bar_box_id": "contribution_bar_B_2",
                            "feature_label_box_id": "feature_label_B_2",
                            "value_label_box_id": "value_label_B_2",
                        },
                        {
                            "rank": 3,
                            "feature": "Tumor size",
                            "shap_value": -0.01,
                            "bar_box_id": "contribution_bar_B_3",
                            "feature_label_box_id": "feature_label_B_3",
                            "value_label_box_id": "value_label_B_3",
                        },
                    ],
                },
            ],
            "support_panels": [
                {
                    "panel_id": "age_support",
                    "panel_label": "C",
                    "title": "Age support",
                    "x_label": "Age (years)",
                    "feature": "Age",
                    "reference_value": 60.0,
                    "reference_label": "Median age",
                    "panel_box_id": "panel_C",
                    "reference_line_box_id": "reference_line_C",
                    "reference_label_box_id": "reference_label_C",
                    "response_points": [{"x": 0.13, "y": 0.25}, {"x": 0.22, "y": 0.31}, {"x": 0.31, "y": 0.36}],
                    "support_segments": [
                        {
                            "segment_id": "age_observed",
                            "segment_label": "Observed",
                            "support_kind": "observed_support",
                            "segment_box_id": "support_segment_C_1",
                            "label_box_id": "support_label_C_1",
                        },
                        {
                            "segment_id": "age_subgroup",
                            "segment_label": "Subgroup",
                            "support_kind": "subgroup_support",
                            "segment_box_id": "support_segment_C_2",
                            "label_box_id": "support_label_C_2",
                        },
                        {
                            "segment_id": "age_bin",
                            "segment_label": "Bin",
                            "support_kind": "bin_support",
                            "segment_box_id": "support_segment_C_3",
                            "label_box_id": "support_label_C_3",
                        },
                        {
                            "segment_id": "age_extrapolation",
                            "segment_label": "Extrapolation",
                            "support_kind": "extrapolation_warning",
                            "segment_box_id": "support_segment_C_4",
                            "label_box_id": "support_label_C_4",
                        },
                    ],
                },
                {
                    "panel_id": "albumin_support",
                    "panel_label": "D",
                    "title": "Albumin support",
                    "x_label": "Albumin (g/dL)",
                    "feature": "Albumin",
                    "reference_value": 3.8,
                    "reference_label": "Median albumin",
                    "panel_box_id": "panel_D",
                    "reference_line_box_id": "reference_line_D",
                    "reference_label_box_id": "reference_label_D",
                    "response_points": [{"x": 0.50, "y": 0.35}, {"x": 0.60, "y": 0.27}, {"x": 0.71, "y": 0.18}],
                    "support_segments": [
                        {
                            "segment_id": "alb_observed",
                            "segment_label": "Observed",
                            "support_kind": "observed_support",
                            "segment_box_id": "support_segment_D_1",
                            "label_box_id": "support_label_D_1",
                        },
                        {
                            "segment_id": "alb_subgroup",
                            "segment_label": "Subgroup",
                            "support_kind": "subgroup_support",
                            "segment_box_id": "support_segment_D_2",
                            "label_box_id": "support_label_D_2",
                        },
                        {
                            "segment_id": "alb_bin",
                            "segment_label": "Bin",
                            "support_kind": "bin_support",
                            "segment_box_id": "support_segment_D_3",
                            "label_box_id": "support_label_D_3",
                        },
                        {
                            "segment_id": "alb_extrapolation",
                            "segment_label": "Extrapolation",
                            "support_kind": "extrapolation_warning",
                            "segment_box_id": "support_segment_D_4",
                            "label_box_id": "support_label_D_4",
                        },
                    ],
                },
            ],
        },
    }

def _make_shap_multigroup_decision_path_support_domain_layout_sidecar() -> dict[str, object]:
    return {
        "template_id": "shap_multigroup_decision_path_support_domain_panel",
        "device": make_device(),
        "render_context": {"layout_override": {"show_figure_title": False}},
        "layout_boxes": [
            make_box("panel_title", "panel_title", x0=0.18, y0=0.91, x1=0.63, y1=0.94),
            make_box("x_axis_title", "subplot_x_axis_title", x0=0.27, y0=0.46, x1=0.58, y1=0.49),
            make_box("y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.63, x1=0.08, y1=0.87),
            make_box("legend_title", "legend_title", x0=0.73, y0=0.73, x1=0.85, y1=0.76),
            make_box("legend_box", "legend_box", x0=0.70, y0=0.60, x1=0.91, y1=0.78),
            make_box("feature_label_1", "feature_label", x0=0.05, y0=0.83, x1=0.13, y1=0.87),
            make_box("feature_label_2", "feature_label", x0=0.04, y0=0.74, x1=0.14, y1=0.78),
            make_box("feature_label_3", "feature_label", x0=0.03, y0=0.65, x1=0.15, y1=0.69),
            make_box("decision_path_line_immune_inflamed", "decision_path_line", x0=0.29, y0=0.61, x1=0.63, y1=0.86),
            make_box("decision_path_line_stromal_low", "decision_path_line", x0=0.24, y0=0.61, x1=0.53, y1=0.86),
            make_box("decision_path_line_immune_excluded", "decision_path_line", x0=0.27, y0=0.61, x1=0.58, y1=0.86),
            make_box("prediction_label_immune_inflamed", "prediction_label", x0=0.59, y0=0.58, x1=0.72, y1=0.61),
            make_box("prediction_label_stromal_low", "prediction_label", x0=0.33, y0=0.58, x1=0.47, y1=0.61),
            make_box("prediction_label_immune_excluded", "prediction_label", x0=0.50, y0=0.58, x1=0.65, y1=0.61),
            make_box("panel_title_C", "panel_title", x0=0.14, y0=0.45, x1=0.32, y1=0.48),
            make_box("panel_title_D", "panel_title", x0=0.51, y0=0.45, x1=0.72, y1=0.48),
            make_box("panel_label_C", "panel_label", x0=0.13, y0=0.37, x1=0.15, y1=0.40),
            make_box("panel_label_D", "panel_label", x0=0.50, y0=0.37, x1=0.52, y1=0.40),
            make_box("x_axis_title_C", "subplot_x_axis_title", x0=0.17, y0=0.04, x1=0.30, y1=0.07),
            make_box("x_axis_title_D", "subplot_x_axis_title", x0=0.55, y0=0.04, x1=0.70, y1=0.07),
            make_box("support_y_axis_title", "subplot_y_axis_title", x0=0.05, y0=0.18, x1=0.07, y1=0.34),
            make_box("reference_label_C", "support_domain_reference_label", x0=0.20, y0=0.37, x1=0.29, y1=0.40),
            make_box("reference_label_D", "support_domain_reference_label", x0=0.58, y0=0.37, x1=0.69, y1=0.40),
            make_box("support_label_C_1", "support_label", x0=0.13, y0=0.15, x1=0.19, y1=0.18),
            make_box("support_label_C_2", "support_label", x0=0.19, y0=0.12, x1=0.25, y1=0.15),
            make_box("support_label_C_3", "support_label", x0=0.25, y0=0.15, x1=0.29, y1=0.18),
            make_box("support_label_C_4", "support_label", x0=0.29, y0=0.12, x1=0.35, y1=0.15),
            make_box("support_label_D_1", "support_label", x0=0.50, y0=0.15, x1=0.57, y1=0.18),
            make_box("support_label_D_2", "support_label", x0=0.57, y0=0.12, x1=0.62, y1=0.15),
            make_box("support_label_D_3", "support_label", x0=0.62, y0=0.15, x1=0.67, y1=0.18),
            make_box("support_label_D_4", "support_label", x0=0.67, y0=0.12, x1=0.74, y1=0.15),
            make_box("support_legend_title", "legend_title", x0=0.31, y0=0.01, x1=0.46, y1=0.04),
            make_box("support_legend_box", "legend_box", x0=0.22, y0=0.00, x1=0.79, y1=0.08),
        ],
        "panel_boxes": [
            make_box("panel_decision_path", "panel", x0=0.18, y0=0.58, x1=0.67, y1=0.88),
            make_box("panel_C", "panel", x0=0.12, y0=0.12, x1=0.35, y1=0.40),
            make_box("panel_D", "panel", x0=0.49, y0=0.12, x1=0.74, y1=0.40),
        ],
        "guide_boxes": [
            make_box("baseline_reference_line", "baseline_reference_line", x0=0.32, y0=0.58, x1=0.321, y1=0.88),
            make_box("prediction_marker_immune_inflamed", "prediction_marker", x0=0.60, y0=0.59, x1=0.608, y1=0.61),
            make_box("prediction_marker_stromal_low", "prediction_marker", x0=0.40, y0=0.59, x1=0.408, y1=0.61),
            make_box("prediction_marker_immune_excluded", "prediction_marker", x0=0.54, y0=0.59, x1=0.548, y1=0.61),
            make_box("reference_line_C", "support_domain_reference_line", x0=0.22, y0=0.12, x1=0.221, y1=0.40),
            make_box("reference_line_D", "support_domain_reference_line", x0=0.60, y0=0.12, x1=0.601, y1=0.40),
            make_box("support_segment_C_1", "support_domain_segment", x0=0.13, y0=0.12, x1=0.19, y1=0.19),
            make_box("support_segment_C_2", "support_domain_segment", x0=0.19, y0=0.12, x1=0.25, y1=0.19),
            make_box("support_segment_C_3", "support_domain_segment", x0=0.25, y0=0.12, x1=0.30, y1=0.19),
            make_box("support_segment_C_4", "support_domain_segment", x0=0.30, y0=0.12, x1=0.34, y1=0.19),
            make_box("support_segment_D_1", "support_domain_segment", x0=0.50, y0=0.12, x1=0.57, y1=0.19),
            make_box("support_segment_D_2", "support_domain_segment", x0=0.57, y0=0.12, x1=0.62, y1=0.19),
            make_box("support_segment_D_3", "support_domain_segment", x0=0.62, y0=0.12, x1=0.67, y1=0.19),
            make_box("support_segment_D_4", "support_domain_segment", x0=0.67, y0=0.12, x1=0.73, y1=0.19),
        ],
        "metrics": {
            "decision_panel": {
                "panel_box_id": "panel_decision_path",
                "baseline_line_box_id": "baseline_reference_line",
                "baseline_value": 0.19,
                "legend_title": "Phenotype",
                "feature_order": ["Age", "Albumin", "Tumor size"],
                "feature_label_box_ids": ["feature_label_1", "feature_label_2", "feature_label_3"],
                "groups": [
                    {
                        "group_id": "immune_inflamed",
                        "group_label": "Phenotype 1",
                        "predicted_value": 0.34,
                        "line_box_id": "decision_path_line_immune_inflamed",
                        "prediction_marker_box_id": "prediction_marker_immune_inflamed",
                        "prediction_label_box_id": "prediction_label_immune_inflamed",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": 0.10, "start_value": 0.19, "end_value": 0.29},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.03, "start_value": 0.29, "end_value": 0.26},
                            {"rank": 3, "feature": "Tumor size", "shap_value": 0.08, "start_value": 0.26, "end_value": 0.34},
                        ],
                    },
                    {
                        "group_id": "stromal_low",
                        "group_label": "Phenotype 2",
                        "predicted_value": 0.08,
                        "line_box_id": "decision_path_line_stromal_low",
                        "prediction_marker_box_id": "prediction_marker_stromal_low",
                        "prediction_label_box_id": "prediction_label_stromal_low",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": -0.04, "start_value": 0.19, "end_value": 0.15},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.02, "start_value": 0.15, "end_value": 0.13},
                            {"rank": 3, "feature": "Tumor size", "shap_value": -0.05, "start_value": 0.13, "end_value": 0.08},
                        ],
                    },
                    {
                        "group_id": "immune_excluded",
                        "group_label": "Phenotype 3",
                        "predicted_value": 0.21,
                        "line_box_id": "decision_path_line_immune_excluded",
                        "prediction_marker_box_id": "prediction_marker_immune_excluded",
                        "prediction_label_box_id": "prediction_label_immune_excluded",
                        "contributions": [
                            {"rank": 1, "feature": "Age", "shap_value": 0.02, "start_value": 0.19, "end_value": 0.21},
                            {"rank": 2, "feature": "Albumin", "shap_value": -0.01, "start_value": 0.21, "end_value": 0.20},
                            {"rank": 3, "feature": "Tumor size", "shap_value": 0.01, "start_value": 0.20, "end_value": 0.21},
                        ],
                    },
                ],
            },
            "support_y_label": "Predicted response probability",
            "support_legend_title": "Support domain",
            "support_legend_labels": [
                "Response curve",
                "Observed support",
                "Subgroup support",
                "Bin support",
                "Extrapolation reminder",
            ],
            "support_y_axis_title_box_id": "support_y_axis_title",
            "support_legend_title_box_id": "support_legend_title",
            "support_panels": [
                {
                    "panel_id": "age_support",
                    "panel_label": "C",
                    "title": "Age support domain",
                    "x_label": "Age (years)",
                    "feature": "Age",
                    "reference_value": 60.0,
                    "reference_label": "Median age",
                    "panel_box_id": "panel_C",
                    "reference_line_box_id": "reference_line_C",
                    "reference_label_box_id": "reference_label_C",
                    "response_points": [
                        {"x": 0.13, "y": 0.27},
                        {"x": 0.19, "y": 0.31},
                        {"x": 0.24, "y": 0.35},
                        {"x": 0.29, "y": 0.37},
                        {"x": 0.33, "y": 0.39},
                    ],
                    "support_segments": [
                        {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "segment_box_id": "support_segment_C_1", "label_box_id": "support_label_C_1"},
                        {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "segment_box_id": "support_segment_C_2", "label_box_id": "support_label_C_2"},
                        {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "segment_box_id": "support_segment_C_3", "label_box_id": "support_label_C_3"},
                        {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "segment_box_id": "support_segment_C_4", "label_box_id": "support_label_C_4"},
                    ],
                },
                {
                    "panel_id": "albumin_support",
                    "panel_label": "D",
                    "title": "Albumin support domain",
                    "x_label": "Albumin (g/dL)",
                    "feature": "Albumin",
                    "reference_value": 3.8,
                    "reference_label": "Median albumin",
                    "panel_box_id": "panel_D",
                    "reference_line_box_id": "reference_line_D",
                    "reference_label_box_id": "reference_label_D",
                    "response_points": [
                        {"x": 0.50, "y": 0.38},
                        {"x": 0.56, "y": 0.33},
                        {"x": 0.61, "y": 0.28},
                        {"x": 0.67, "y": 0.23},
                        {"x": 0.72, "y": 0.18},
                    ],
                    "support_segments": [
                        {"segment_id": "alb_observed", "segment_label": "Observed", "support_kind": "observed_support", "segment_box_id": "support_segment_D_1", "label_box_id": "support_label_D_1"},
                        {"segment_id": "alb_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "segment_box_id": "support_segment_D_2", "label_box_id": "support_label_D_2"},
                        {"segment_id": "alb_bin", "segment_label": "Bin", "support_kind": "bin_support", "segment_box_id": "support_segment_D_3", "label_box_id": "support_label_D_3"},
                        {"segment_id": "alb_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "segment_box_id": "support_segment_D_4", "label_box_id": "support_label_D_4"},
                    ],
                },
            ],
        },
    }

def _make_shap_signed_importance_local_support_domain_layout_sidecar(tmp_path: Path) -> dict[str, object]:
    surface_tests = importlib.import_module("tests.test_display_surface_materialization")
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    surface_tests.dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure52",
                    "display_kind": "figure",
                    "requirement_key": "shap_signed_importance_local_support_domain_panel",
                    "catalog_id": "F52",
                    "shell_path": "paper/figures/Figure52.shell.json",
                }
            ],
        },
    )
    surface_tests.dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    surface_tests.dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    surface_tests.write_default_publication_display_contracts(paper_root)
    surface_tests.dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure52",
                    "template_id": "shap_signed_importance_local_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    surface_tests.dump_json(
        paper_root / "shap_signed_importance_local_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_local_support_domain_panel_inputs_v1",
            "displays": [surface_tests._make_shap_signed_importance_local_support_domain_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F52_shap_signed_importance_local_support_domain_panel.layout.json"
    )
    return json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
