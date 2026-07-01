from __future__ import annotations


def minimal_tail_layout_sidecar(template_short_id: str, template_id: str) -> dict[str, object] | None:
    if template_short_id == "generalizability_subgroup_composite_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "title", "box_type": "title", "x0": 0.10, "y0": 0.02, "x1": 0.62, "y1": 0.08},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.09, "y0": 0.12, "x1": 0.12, "y1": 0.16},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.09, "y0": 0.55, "x1": 0.12, "y1": 0.59},
                {"box_id": "overview_x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.47, "x1": 0.56, "y1": 0.51},
                {"box_id": "subgroup_x_axis_title", "box_type": "x_axis_title", "x0": 0.30, "y0": 0.91, "x1": 0.56, "y1": 0.95},
                {"box_id": "overview_row_1_label", "box_type": "row_label", "x0": 0.08, "y0": 0.22, "x1": 0.22, "y1": 0.27},
                {"box_id": "overview_primary_1", "box_type": "estimate_marker", "x0": 0.56, "y0": 0.22, "x1": 0.58, "y1": 0.27},
                {"box_id": "overview_comparator_1", "box_type": "estimate_marker", "x0": 0.51, "y0": 0.22, "x1": 0.53, "y1": 0.27},
                {"box_id": "subgroup_row_1_label", "box_type": "row_label", "x0": 0.08, "y0": 0.66, "x1": 0.24, "y1": 0.71},
                {"box_id": "subgroup_estimate_1", "box_type": "estimate_marker", "x0": 0.57, "y0": 0.66, "x1": 0.59, "y1": 0.71},
                {"box_id": "subgroup_ci_1", "box_type": "ci_segment", "x0": 0.51, "y0": 0.685, "x1": 0.64, "y1": 0.695},
            ],
            "panel_boxes": [
                {"box_id": "overview_panel", "box_type": "panel", "x0": 0.08, "y0": 0.14, "x1": 0.84, "y1": 0.46},
                {"box_id": "subgroup_panel", "box_type": "panel", "x0": 0.08, "y0": 0.57, "x1": 0.84, "y1": 0.90},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.70, "y0": 0.02, "x1": 0.92, "y1": 0.08},
                {"box_id": "subgroup_reference_line", "box_type": "reference_line", "x0": 0.54, "y0": 0.57, "x1": 0.54, "y1": 0.90},
            ],
            "metrics": {
                "metric_family": "discrimination",
                "primary_label": "Locked model",
                "comparator_label": "Derivation cohort",
                "overview_rows": [
                    {
                        "cohort_id": "external_a",
                        "cohort_label": "External A",
                        "support_count": 184,
                        "event_count": 29,
                        "metric_value": 0.82,
                        "comparator_metric_value": 0.79,
                    },
                ],
                "subgroup_reference_value": 0.80,
                "subgroup_rows": [
                    {
                        "subgroup_id": "age_ge_65",
                        "subgroup_label": "Age >=65 years",
                        "group_n": 201,
                        "estimate": 0.82,
                        "lower": 0.78,
                        "upper": 0.86,
                    },
                ],
                },
            }
    if template_short_id == "center_transportability_governance_summary_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.09, "y0": 0.12, "x1": 0.12, "y1": 0.16},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.56, "y0": 0.12, "x1": 0.59, "y1": 0.16},
                {"box_id": "metric_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.20, "y0": 0.86, "x1": 0.42, "y1": 0.90},
                {"box_id": "center_china_marker", "box_type": "metric_marker", "x0": 0.30, "y0": 0.32, "x1": 0.33, "y1": 0.36},
                {"box_id": "center_us_marker", "box_type": "metric_marker", "x0": 0.27, "y0": 0.52, "x1": 0.30, "y1": 0.56},
                {"box_id": "china_slope_marker", "box_type": "calibration_governance_metric", "x0": 0.65, "y0": 0.32, "x1": 0.68, "y1": 0.36},
                {"box_id": "china_oe_marker", "box_type": "calibration_governance_metric", "x0": 0.80, "y0": 0.32, "x1": 0.83, "y1": 0.36},
                {"box_id": "us_slope_marker", "box_type": "calibration_governance_metric", "x0": 0.62, "y0": 0.56, "x1": 0.65, "y1": 0.60},
                {"box_id": "us_oe_marker", "box_type": "calibration_governance_metric", "x0": 0.90, "y0": 0.56, "x1": 0.93, "y1": 0.60},
                {"box_id": "calibration_reference_line", "box_type": "calibration_reference_line", "x0": 0.74, "y0": 0.23, "x1": 0.745, "y1": 0.77},
                {"box_id": "calibration_acceptance_band", "box_type": "calibration_acceptance_band", "x0": 0.66, "y0": 0.23, "x1": 0.82, "y1": 0.77},
            ],
            "panel_boxes": [
                {"box_id": "panel_left", "box_type": "metric_panel", "x0": 0.08, "y0": 0.18, "x1": 0.48, "y1": 0.82},
                {"box_id": "panel_right", "box_type": "governance_decision_panel", "x0": 0.54, "y0": 0.18, "x1": 0.94, "y1": 0.82},
            ],
            "guide_boxes": [
                {"box_id": "legend", "box_type": "legend", "x0": 0.22, "y0": 0.06, "x1": 0.78, "y1": 0.12},
            ],
            "metrics": {
                "source_renderer": "MAS/Transportability::center_transportability_governance_summary_panel",
                "figure_purpose": "transportability_discrimination_plus_recalibration_governance_decision_matrix",
                "rendered_title_policy": "figure_title_metadata_only_not_drawn_inside_plot",
                "governance_visual_encoding_policy": "numeric_calibration_markers_with_reference_and_acceptance_band",
                "centers": [
                    {
                        "center_id": "china",
                        "center_label": "China validation",
                        "metric_estimate": 0.74,
                        "metric_lower": 0.72,
                        "metric_upper": 0.76,
                        "slope": 0.96,
                        "oe_ratio": 1.02,
                    },
                    {
                        "center_id": "us",
                        "center_label": "US transport",
                        "metric_estimate": 0.73,
                        "metric_lower": 0.71,
                        "metric_upper": 0.75,
                        "slope": 0.91,
                        "oe_ratio": 1.08,
                    },
                ],
                "metric_reference_value": 0.74,
                "batch_shift_threshold": 0.04,
                "slope_acceptance": {"lower": 0.85, "upper": 1.15},
                "oe_ratio_acceptance": {"lower": 0.85, "upper": 1.15},
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
                "layout_mode": "participant_flow",
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
    return None
