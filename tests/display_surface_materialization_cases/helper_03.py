from __future__ import annotations

from . import shared_base as _shared_base
from . import helper_02 as _helper_prev

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_helper_prev)

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
    if template_short_id == "workflow_fact_sheet_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.07, "y0": 0.10, "x1": 0.10, "y1": 0.14},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.55, "y0": 0.10, "x1": 0.58, "y1": 0.14},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.07, "y0": 0.54, "x1": 0.10, "y1": 0.58},
                {"box_id": "panel_label_D", "box_type": "panel_label", "x0": 0.55, "y0": 0.54, "x1": 0.58, "y1": 0.58},
                {"box_id": "section_title_A", "box_type": "section_title", "x0": 0.11, "y0": 0.10, "x1": 0.34, "y1": 0.14},
                {"box_id": "section_title_B", "box_type": "section_title", "x0": 0.59, "y0": 0.10, "x1": 0.82, "y1": 0.14},
                {"box_id": "section_title_C", "box_type": "section_title", "x0": 0.11, "y0": 0.54, "x1": 0.34, "y1": 0.58},
                {"box_id": "section_title_D", "box_type": "section_title", "x0": 0.59, "y0": 0.54, "x1": 0.82, "y1": 0.58},
                {"box_id": "fact_label_A_1", "box_type": "fact_label", "x0": 0.11, "y0": 0.18, "x1": 0.24, "y1": 0.22},
                {"box_id": "fact_value_A_1", "box_type": "fact_value", "x0": 0.26, "y0": 0.18, "x1": 0.42, "y1": 0.22},
                {"box_id": "fact_label_B_1", "box_type": "fact_label", "x0": 0.59, "y0": 0.18, "x1": 0.72, "y1": 0.22},
                {"box_id": "fact_value_B_1", "box_type": "fact_value", "x0": 0.74, "y0": 0.18, "x1": 0.90, "y1": 0.22},
                {"box_id": "fact_label_C_1", "box_type": "fact_label", "x0": 0.11, "y0": 0.62, "x1": 0.24, "y1": 0.66},
                {"box_id": "fact_value_C_1", "box_type": "fact_value", "x0": 0.26, "y0": 0.62, "x1": 0.42, "y1": 0.66},
                {"box_id": "fact_label_D_1", "box_type": "fact_label", "x0": 0.59, "y0": 0.62, "x1": 0.72, "y1": 0.66},
                {"box_id": "fact_value_D_1", "box_type": "fact_value", "x0": 0.74, "y0": 0.62, "x1": 0.90, "y1": 0.66},
            ],
            "panel_boxes": [
                {"box_id": "panel_A", "box_type": "panel", "x0": 0.06, "y0": 0.08, "x1": 0.46, "y1": 0.46},
                {"box_id": "panel_B", "box_type": "panel", "x0": 0.54, "y0": 0.08, "x1": 0.94, "y1": 0.46},
                {"box_id": "panel_C", "box_type": "panel", "x0": 0.06, "y0": 0.52, "x1": 0.46, "y1": 0.90},
                {"box_id": "panel_D", "box_type": "panel", "x0": 0.54, "y0": 0.52, "x1": 0.94, "y1": 0.90},
            ],
            "guide_boxes": [],
            "metrics": {
                "sections": [
                    {
                        "section_id": "cohort",
                        "panel_label": "A",
                        "layout_role": "top_left",
                        "panel_box_id": "panel_A",
                        "title_box_id": "section_title_A",
                        "panel_label_box_id": "panel_label_A",
                        "facts": [{"fact_id": "cohort_n", "label_box_id": "fact_label_A_1", "value_box_id": "fact_value_A_1"}],
                    },
                    {
                        "section_id": "endpoint",
                        "panel_label": "B",
                        "layout_role": "top_right",
                        "panel_box_id": "panel_B",
                        "title_box_id": "section_title_B",
                        "panel_label_box_id": "panel_label_B",
                        "facts": [{"fact_id": "endpoint", "label_box_id": "fact_label_B_1", "value_box_id": "fact_value_B_1"}],
                    },
                    {
                        "section_id": "workflow",
                        "panel_label": "C",
                        "layout_role": "bottom_left",
                        "panel_box_id": "panel_C",
                        "title_box_id": "section_title_C",
                        "panel_label_box_id": "panel_label_C",
                        "facts": [{"fact_id": "model_family", "label_box_id": "fact_label_C_1", "value_box_id": "fact_value_C_1"}],
                    },
                    {
                        "section_id": "validation",
                        "panel_label": "D",
                        "layout_role": "bottom_right",
                        "panel_box_id": "panel_D",
                        "title_box_id": "section_title_D",
                        "panel_label_box_id": "panel_label_D",
                        "facts": [{"fact_id": "validation_scheme", "label_box_id": "fact_label_D_1", "value_box_id": "fact_value_D_1"}],
                    },
                ],
            },
        }
    if template_short_id == "baseline_missingness_qc_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.06, "y0": 0.08, "x1": 0.09, "y1": 0.12},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.58, "y0": 0.08, "x1": 0.61, "y1": 0.12},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.58, "y0": 0.58, "x1": 0.61, "y1": 0.62},
                {"box_id": "balance_panel_title", "box_type": "panel_title", "x0": 0.10, "y0": 0.08, "x1": 0.34, "y1": 0.12},
                {"box_id": "balance_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.14, "y0": 0.84, "x1": 0.40, "y1": 0.88},
                {"box_id": "missingness_panel_title", "box_type": "panel_title", "x0": 0.63, "y0": 0.08, "x1": 0.88, "y1": 0.12},
                {"box_id": "missingness_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.66, "y0": 0.45, "x1": 0.89, "y1": 0.49},
                {"box_id": "missingness_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.56, "y0": 0.18, "x1": 0.60, "y1": 0.38},
                {"box_id": "qc_panel_title", "box_type": "panel_title", "x0": 0.63, "y0": 0.58, "x1": 0.84, "y1": 0.62},
                {"box_id": "qc_card_label_retained", "box_type": "card_label", "x0": 0.63, "y0": 0.68, "x1": 0.74, "y1": 0.71},
                {"box_id": "qc_card_value_retained", "box_type": "card_value", "x0": 0.63, "y0": 0.72, "x1": 0.74, "y1": 0.77},
                {"box_id": "qc_card_label_missing", "box_type": "card_label", "x0": 0.77, "y0": 0.68, "x1": 0.89, "y1": 0.71},
                {"box_id": "qc_card_value_missing", "box_type": "card_value", "x0": 0.77, "y0": 0.72, "x1": 0.89, "y1": 0.77},
            ],
            "panel_boxes": [
                {"box_id": "panel_balance", "box_type": "panel", "x0": 0.04, "y0": 0.06, "x1": 0.48, "y1": 0.90},
                {"box_id": "panel_missingness", "box_type": "panel", "x0": 0.56, "y0": 0.06, "x1": 0.94, "y1": 0.50},
                {"box_id": "panel_qc", "box_type": "panel", "x0": 0.56, "y0": 0.56, "x1": 0.94, "y1": 0.90},
            ],
            "guide_boxes": [
                {"box_id": "balance_threshold", "box_type": "reference_line", "x0": 0.24, "y0": 0.16, "x1": 0.25, "y1": 0.82},
                {"box_id": "missingness_colorbar", "box_type": "colorbar", "x0": 0.90, "y0": 0.14, "x1": 0.92, "y1": 0.42},
            ],
            "metrics": {
                "primary_balance_label": "Pre-adjustment SMD",
                "secondary_balance_label": "Post-adjustment SMD",
                "balance_threshold": 0.10,
                "balance_variables": [
                    {"variable_id": "age", "label": "Age", "primary_value": 0.24, "secondary_value": 0.08},
                    {"variable_id": "sex", "label": "Female sex", "primary_value": 0.11, "secondary_value": 0.04},
                ],
                "missingness_rows": [{"label": "Age"}, {"label": "HbA1c"}],
                "missingness_columns": [{"label": "Train"}, {"label": "Validation"}],
                "missingness_cells": [
                    {"x": "Train", "y": "Age", "value": 0.01},
                    {"x": "Validation", "y": "Age", "value": 0.03},
                    {"x": "Train", "y": "HbA1c", "value": 0.08},
                    {"x": "Validation", "y": "HbA1c", "value": 0.11},
                ],
                "qc_cards": [
                    {"card_id": "retained", "label_box_id": "qc_card_label_retained", "value_box_id": "qc_card_value_retained"},
                    {"card_id": "max_missing", "label_box_id": "qc_card_label_missing", "value_box_id": "qc_card_value_missing"},
                ],
            },
        }
    if template_short_id == "center_coverage_batch_transportability_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.06, "y0": 0.08, "x1": 0.09, "y1": 0.12},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.58, "y0": 0.08, "x1": 0.61, "y1": 0.12},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.58, "y0": 0.58, "x1": 0.61, "y1": 0.62},
                {"box_id": "coverage_panel_title", "box_type": "panel_title", "x0": 0.10, "y0": 0.08, "x1": 0.34, "y1": 0.12},
                {"box_id": "coverage_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.15, "y0": 0.84, "x1": 0.40, "y1": 0.88},
                {"box_id": "batch_panel_title", "box_type": "panel_title", "x0": 0.63, "y0": 0.08, "x1": 0.86, "y1": 0.12},
                {"box_id": "batch_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.66, "y0": 0.45, "x1": 0.89, "y1": 0.49},
                {"box_id": "batch_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.56, "y0": 0.18, "x1": 0.60, "y1": 0.38},
                {"box_id": "transportability_panel_title", "box_type": "panel_title", "x0": 0.63, "y0": 0.58, "x1": 0.87, "y1": 0.62},
                {"box_id": "transport_card_label_centers", "box_type": "card_label", "x0": 0.63, "y0": 0.68, "x1": 0.77, "y1": 0.71},
                {"box_id": "transport_card_value_centers", "box_type": "card_value", "x0": 0.63, "y0": 0.72, "x1": 0.77, "y1": 0.77},
                {"box_id": "transport_card_label_shift", "box_type": "card_label", "x0": 0.63, "y0": 0.79, "x1": 0.77, "y1": 0.82},
                {"box_id": "transport_card_value_shift", "box_type": "card_value", "x0": 0.63, "y0": 0.83, "x1": 0.77, "y1": 0.88},
            ],
            "panel_boxes": [
                {"box_id": "panel_coverage", "box_type": "panel", "x0": 0.04, "y0": 0.06, "x1": 0.48, "y1": 0.90},
                {"box_id": "panel_batch", "box_type": "panel", "x0": 0.56, "y0": 0.06, "x1": 0.94, "y1": 0.50},
                {"box_id": "panel_transportability", "box_type": "panel", "x0": 0.56, "y0": 0.56, "x1": 0.94, "y1": 0.90},
            ],
            "guide_boxes": [
                {"box_id": "batch_threshold", "box_type": "reference_line", "x0": 0.88, "y0": 0.14, "x1": 0.89, "y1": 0.42},
                {"box_id": "batch_colorbar", "box_type": "colorbar", "x0": 0.90, "y0": 0.14, "x1": 0.92, "y1": 0.42},
            ],
            "metrics": {
                "batch_threshold": 0.20,
                "center_rows": [
                    {"center_id": "train_a", "center_label": "Train A", "cohort_role": "Derivation", "support_count": 412, "event_count": 63},
                    {"center_id": "external_b", "center_label": "External B", "cohort_role": "External", "support_count": 188, "event_count": 29},
                ],
                "batch_rows": [{"label": "Train A"}, {"label": "External B"}],
                "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}],
                "batch_cells": [
                    {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                    {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                    {"x": "Specimen drift", "y": "External B", "value": 0.14},
                    {"x": "Scanner drift", "y": "External B", "value": 0.18},
                ],
                "transportability_cards": [
                    {"card_id": "covered_centers", "label_box_id": "transport_card_label_centers", "value_box_id": "transport_card_value_centers"},
                    {"card_id": "largest_shift", "label_box_id": "transport_card_label_shift", "value_box_id": "transport_card_value_shift"},
                ],
            },
        }
    if template_short_id == "transportability_recalibration_governance_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.06, "y0": 0.08, "x1": 0.09, "y1": 0.12},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.58, "y0": 0.08, "x1": 0.61, "y1": 0.12},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.58, "y0": 0.58, "x1": 0.61, "y1": 0.62},
                {"box_id": "coverage_panel_title", "box_type": "panel_title", "x0": 0.10, "y0": 0.08, "x1": 0.34, "y1": 0.12},
                {"box_id": "coverage_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.15, "y0": 0.84, "x1": 0.40, "y1": 0.88},
                {"box_id": "batch_panel_title", "box_type": "panel_title", "x0": 0.63, "y0": 0.08, "x1": 0.86, "y1": 0.12},
                {"box_id": "batch_x_axis_title", "box_type": "subplot_x_axis_title", "x0": 0.66, "y0": 0.45, "x1": 0.89, "y1": 0.49},
                {"box_id": "batch_y_axis_title", "box_type": "subplot_y_axis_title", "x0": 0.56, "y0": 0.18, "x1": 0.60, "y1": 0.38},
                {"box_id": "recalibration_panel_title", "box_type": "panel_title", "x0": 0.63, "y0": 0.58, "x1": 0.89, "y1": 0.62},
                {"box_id": "recalibration_row_label_train_a", "box_type": "row_label", "x0": 0.62, "y0": 0.68, "x1": 0.72, "y1": 0.72},
                {"box_id": "recalibration_row_slope_train_a", "box_type": "row_metric", "x0": 0.62, "y0": 0.73, "x1": 0.71, "y1": 0.77},
                {"box_id": "recalibration_row_oe_train_a", "box_type": "row_metric", "x0": 0.73, "y0": 0.73, "x1": 0.82, "y1": 0.77},
                {"box_id": "recalibration_row_action_train_a", "box_type": "row_action", "x0": 0.83, "y0": 0.71, "x1": 0.92, "y1": 0.77},
                {"box_id": "recalibration_row_label_external_b", "box_type": "row_label", "x0": 0.62, "y0": 0.80, "x1": 0.75, "y1": 0.84},
                {"box_id": "recalibration_row_slope_external_b", "box_type": "row_metric", "x0": 0.62, "y0": 0.85, "x1": 0.71, "y1": 0.89},
                {"box_id": "recalibration_row_oe_external_b", "box_type": "row_metric", "x0": 0.73, "y0": 0.85, "x1": 0.82, "y1": 0.89},
                {"box_id": "recalibration_row_action_external_b", "box_type": "row_action", "x0": 0.83, "y0": 0.83, "x1": 0.92, "y1": 0.89},
            ],
            "panel_boxes": [
                {"box_id": "panel_coverage", "box_type": "panel", "x0": 0.04, "y0": 0.06, "x1": 0.48, "y1": 0.90},
                {"box_id": "panel_batch", "box_type": "panel", "x0": 0.56, "y0": 0.06, "x1": 0.94, "y1": 0.50},
                {"box_id": "panel_recalibration", "box_type": "panel", "x0": 0.56, "y0": 0.56, "x1": 0.94, "y1": 0.90},
            ],
            "guide_boxes": [
                {"box_id": "batch_threshold", "box_type": "reference_line", "x0": 0.88, "y0": 0.14, "x1": 0.89, "y1": 0.42},
                {"box_id": "batch_colorbar", "box_type": "colorbar", "x0": 0.90, "y0": 0.14, "x1": 0.92, "y1": 0.42},
            ],
            "metrics": {
                "batch_threshold": 0.20,
                "slope_acceptance_lower": 0.90,
                "slope_acceptance_upper": 1.10,
                "oe_ratio_acceptance_lower": 0.90,
                "oe_ratio_acceptance_upper": 1.10,
                "center_rows": [
                    {"center_id": "train_a", "center_label": "Train A", "cohort_role": "Derivation", "support_count": 412, "event_count": 63},
                    {"center_id": "external_b", "center_label": "External B", "cohort_role": "External", "support_count": 188, "event_count": 29},
                ],
                "batch_rows": [{"label": "Train A"}, {"label": "External B"}],
                "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}],
                "batch_cells": [
                    {"x": "Specimen drift", "y": "Train A", "value": 0.08},
                    {"x": "Scanner drift", "y": "Train A", "value": 0.11},
                    {"x": "Specimen drift", "y": "External B", "value": 0.14},
                    {"x": "Scanner drift", "y": "External B", "value": 0.18},
                ],
                "recalibration_rows": [
                    {"center_id": "train_a", "label_box_id": "recalibration_row_label_train_a", "slope_box_id": "recalibration_row_slope_train_a", "oe_ratio_box_id": "recalibration_row_oe_train_a", "action_box_id": "recalibration_row_action_train_a", "slope": 1.00, "oe_ratio": 1.00},
                    {"center_id": "external_b", "label_box_id": "recalibration_row_label_external_b", "slope_box_id": "recalibration_row_slope_external_b", "oe_ratio_box_id": "recalibration_row_oe_external_b", "action_box_id": "recalibration_row_action_external_b", "slope": 0.84, "oe_ratio": 1.18},
                ],
            },
        }
    if template_short_id == "design_evidence_composite_shell":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "stage_title_1", "box_type": "stage_title", "x0": 0.08, "y0": 0.08, "x1": 0.24, "y1": 0.12},
                {"box_id": "stage_detail_1", "box_type": "stage_detail", "x0": 0.08, "y0": 0.13, "x1": 0.24, "y1": 0.18},
                {"box_id": "stage_title_2", "box_type": "stage_title", "x0": 0.39, "y0": 0.08, "x1": 0.55, "y1": 0.12},
                {"box_id": "stage_detail_2", "box_type": "stage_detail", "x0": 0.39, "y0": 0.13, "x1": 0.55, "y1": 0.18},
                {"box_id": "stage_title_3", "box_type": "stage_title", "x0": 0.70, "y0": 0.08, "x1": 0.86, "y1": 0.12},
                {"box_id": "stage_detail_3", "box_type": "stage_detail", "x0": 0.70, "y0": 0.13, "x1": 0.86, "y1": 0.18},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.07, "y0": 0.38, "x1": 0.10, "y1": 0.42},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.38, "y0": 0.38, "x1": 0.41, "y1": 0.42},
                {"box_id": "panel_label_C", "box_type": "panel_label", "x0": 0.69, "y0": 0.38, "x1": 0.72, "y1": 0.42},
                {"box_id": "summary_title_A", "box_type": "summary_title", "x0": 0.11, "y0": 0.38, "x1": 0.28, "y1": 0.42},
                {"box_id": "summary_title_B", "box_type": "summary_title", "x0": 0.42, "y0": 0.38, "x1": 0.59, "y1": 0.42},
                {"box_id": "summary_title_C", "box_type": "summary_title", "x0": 0.73, "y0": 0.38, "x1": 0.90, "y1": 0.42},
                {"box_id": "card_label_A_1", "box_type": "card_label", "x0": 0.09, "y0": 0.48, "x1": 0.18, "y1": 0.51},
                {"box_id": "card_value_A_1", "box_type": "card_value", "x0": 0.09, "y0": 0.52, "x1": 0.20, "y1": 0.57},
                {"box_id": "card_label_B_1", "box_type": "card_label", "x0": 0.40, "y0": 0.48, "x1": 0.49, "y1": 0.51},
                {"box_id": "card_value_B_1", "box_type": "card_value", "x0": 0.40, "y0": 0.52, "x1": 0.51, "y1": 0.57},
                {"box_id": "card_label_C_1", "box_type": "card_label", "x0": 0.71, "y0": 0.48, "x1": 0.80, "y1": 0.51},
                {"box_id": "card_value_C_1", "box_type": "card_value", "x0": 0.71, "y0": 0.52, "x1": 0.82, "y1": 0.57},
            ],
            "panel_boxes": [
                {"box_id": "workflow_stage_1", "box_type": "workflow_stage", "x0": 0.05, "y0": 0.05, "x1": 0.28, "y1": 0.21},
                {"box_id": "workflow_stage_2", "box_type": "workflow_stage", "x0": 0.36, "y0": 0.05, "x1": 0.59, "y1": 0.21},
                {"box_id": "workflow_stage_3", "box_type": "workflow_stage", "x0": 0.67, "y0": 0.05, "x1": 0.90, "y1": 0.21},
                {"box_id": "summary_panel_A", "box_type": "panel", "x0": 0.05, "y0": 0.34, "x1": 0.30, "y1": 0.88},
                {"box_id": "summary_panel_B", "box_type": "panel", "x0": 0.36, "y0": 0.34, "x1": 0.61, "y1": 0.88},
                {"box_id": "summary_panel_C", "box_type": "panel", "x0": 0.67, "y0": 0.34, "x1": 0.92, "y1": 0.88},
            ],
            "guide_boxes": [
                {"box_id": "stage_arrow_1", "box_type": "arrow_connector", "x0": 0.29, "y0": 0.11, "x1": 0.35, "y1": 0.15},
                {"box_id": "stage_arrow_2", "box_type": "arrow_connector", "x0": 0.60, "y0": 0.11, "x1": 0.66, "y1": 0.15},
            ],
            "metrics": {
                "workflow_stages": [
                    {"stage_id": "cohort", "stage_box_id": "workflow_stage_1", "title_box_id": "stage_title_1", "detail_box_id": "stage_detail_1"},
                    {"stage_id": "modeling", "stage_box_id": "workflow_stage_2", "title_box_id": "stage_title_2", "detail_box_id": "stage_detail_2"},
                    {"stage_id": "validation", "stage_box_id": "workflow_stage_3", "title_box_id": "stage_title_3", "detail_box_id": "stage_detail_3"},
                ],
                "summary_panels": [
                    {
                        "panel_id": "cohort_summary",
                        "panel_label": "A",
                        "layout_role": "left",
                        "panel_box_id": "summary_panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "title_box_id": "summary_title_A",
                        "cards": [{"card_id": "train_n", "label_box_id": "card_label_A_1", "value_box_id": "card_value_A_1"}],
                    },
                    {
                        "panel_id": "endpoint_summary",
                        "panel_label": "B",
                        "layout_role": "center",
                        "panel_box_id": "summary_panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "title_box_id": "summary_title_B",
                        "cards": [{"card_id": "endpoint", "label_box_id": "card_label_B_1", "value_box_id": "card_value_B_1"}],
                    },
                    {
                        "panel_id": "evidence_summary",
                        "panel_label": "C",
                        "layout_role": "right",
                        "panel_box_id": "summary_panel_C",
                        "panel_label_box_id": "panel_label_C",
                        "title_box_id": "summary_title_C",
                        "cards": [{"card_id": "auc", "label_box_id": "card_label_C_1", "value_box_id": "card_value_C_1"}],
                    },
                ],
            },
        }
    if template_short_id in {
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "clinical_impact_curve_binary",
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
    if template_short_id in {
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "phate_scatter_grouped",
        "tsne_scatter_grouped",
        "diffusion_map_scatter_grouped",
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
    if template_short_id in {"forest_effect_main", "subgroup_forest", "multivariable_forest"}:
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
    if template_short_id == "compact_effect_estimate_panel":
        return {
            "template_id": template_id,
            "device": {"x0": 0.0, "y0": 0.0, "x1": 1.0, "y1": 1.0},
            "layout_boxes": [
                {"box_id": "panel_title_A", "box_type": "panel_title", "x0": 0.13, "y0": 0.86, "x1": 0.32, "y1": 0.89},
                {"box_id": "panel_title_B", "box_type": "panel_title", "x0": 0.58, "y0": 0.86, "x1": 0.77, "y1": 0.89},
                {"box_id": "panel_label_A", "box_type": "panel_label", "x0": 0.13, "y0": 0.82, "x1": 0.15, "y1": 0.85},
                {"box_id": "panel_label_B", "box_type": "panel_label", "x0": 0.58, "y0": 0.82, "x1": 0.60, "y1": 0.85},
                {"box_id": "x_axis_title_A", "box_type": "subplot_x_axis_title", "x0": 0.18, "y0": 0.10, "x1": 0.33, "y1": 0.13},
                {"box_id": "x_axis_title_B", "box_type": "subplot_x_axis_title", "x0": 0.63, "y0": 0.10, "x1": 0.78, "y1": 0.13},
                {"box_id": "row_label_A_1", "box_type": "row_label", "x0": 0.03, "y0": 0.61, "x1": 0.12, "y1": 0.65},
                {"box_id": "row_label_A_2", "box_type": "row_label", "x0": 0.03, "y0": 0.46, "x1": 0.12, "y1": 0.50},
                {"box_id": "estimate_A_1", "box_type": "estimate_marker", "x0": 0.23, "y0": 0.61, "x1": 0.24, "y1": 0.65},
                {"box_id": "estimate_A_2", "box_type": "estimate_marker", "x0": 0.26, "y0": 0.46, "x1": 0.27, "y1": 0.50},
                {"box_id": "ci_A_1", "box_type": "ci_segment", "x0": 0.19, "y0": 0.625, "x1": 0.29, "y1": 0.635},
                {"box_id": "ci_A_2", "box_type": "ci_segment", "x0": 0.21, "y0": 0.475, "x1": 0.33, "y1": 0.485},
                {"box_id": "row_label_B_1", "box_type": "row_label", "x0": 0.48, "y0": 0.61, "x1": 0.57, "y1": 0.65},
                {"box_id": "row_label_B_2", "box_type": "row_label", "x0": 0.48, "y0": 0.46, "x1": 0.57, "y1": 0.50},
                {"box_id": "estimate_B_1", "box_type": "estimate_marker", "x0": 0.68, "y0": 0.61, "x1": 0.69, "y1": 0.65},
                {"box_id": "estimate_B_2", "box_type": "estimate_marker", "x0": 0.71, "y0": 0.46, "x1": 0.72, "y1": 0.50},
                {"box_id": "ci_B_1", "box_type": "ci_segment", "x0": 0.64, "y0": 0.625, "x1": 0.74, "y1": 0.635},
                {"box_id": "ci_B_2", "box_type": "ci_segment", "x0": 0.66, "y0": 0.475, "x1": 0.78, "y1": 0.485},
            ],
            "panel_boxes": [
                {"box_id": "panel_A", "box_type": "panel", "x0": 0.13, "y0": 0.18, "x1": 0.40, "y1": 0.80},
                {"box_id": "panel_B", "box_type": "panel", "x0": 0.58, "y0": 0.18, "x1": 0.85, "y1": 0.80},
            ],
            "guide_boxes": [
                {"box_id": "reference_line_A", "box_type": "reference_line", "x0": 0.28, "y0": 0.18, "x1": 0.29, "y1": 0.80},
                {"box_id": "reference_line_B", "box_type": "reference_line", "x0": 0.73, "y0": 0.18, "x1": 0.74, "y1": 0.80},
            ],
            "metrics": {
                "reference_value": 1.0,
                "panels": [
                    {
                        "panel_id": "overall",
                        "panel_label": "A",
                        "title": "Overall cohort",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "reference_line_box_id": "reference_line_A",
                        "rows": [
                            {
                                "row_id": "age_ge_65",
                                "row_label": "Age ≥65 years",
                                "estimate": 1.18,
                                "lower": 1.04,
                                "upper": 1.34,
                                "label_box_id": "row_label_A_1",
                                "estimate_box_id": "estimate_A_1",
                                "ci_box_id": "ci_A_1",
                            },
                            {
                                "row_id": "female",
                                "row_label": "Female",
                                "estimate": 1.26,
                                "lower": 1.10,
                                "upper": 1.44,
                                "label_box_id": "row_label_A_2",
                                "estimate_box_id": "estimate_A_2",
                                "ci_box_id": "ci_A_2",
                            },
                        ],
                    },
                    {
                        "panel_id": "sensitivity",
                        "panel_label": "B",
                        "title": "Sensitivity analysis",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "reference_line_box_id": "reference_line_B",
                        "rows": [
                            {
                                "row_id": "age_ge_65",
                                "row_label": "Age ≥65 years",
                                "estimate": 1.11,
                                "lower": 0.98,
                                "upper": 1.28,
                                "label_box_id": "row_label_B_1",
                                "estimate_box_id": "estimate_B_1",
                                "ci_box_id": "ci_B_1",
                            },
                            {
                                "row_id": "female",
                                "row_label": "Female",
                                "estimate": 1.22,
                                "lower": 1.05,
                                "upper": 1.40,
                                "label_box_id": "row_label_B_2",
                                "estimate_box_id": "estimate_B_2",
                                "ci_box_id": "ci_B_2",
                            },
                        ],
                    },
                ],
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
