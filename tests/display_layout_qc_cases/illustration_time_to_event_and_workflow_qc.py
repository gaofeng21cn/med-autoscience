from .shared import (
    annotations,
    _shared_base,
    _layout_box_helpers,
    importlib,
    json,
    Path,
    pytest,
    make_box,
    make_device,
    _make_shap_grouped_local_support_domain_layout_sidecar,
    _make_shap_multigroup_decision_path_support_domain_layout_sidecar,
    _make_shap_signed_importance_local_support_domain_layout_sidecar,
)

def test_run_display_layout_qc_passes_for_valid_illustration_flow() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.125, x1=0.11, y1=0.155),
                make_box("panel_label_B", "panel_label", x0=0.52, y0=0.125, x1=0.55, y1=0.155),
                make_box("step_screened", "main_step", x0=0.08, y0=0.40, x1=0.28, y1=0.50),
                make_box("step_included", "main_step", x0=0.08, y0=0.24, x1=0.28, y1=0.34),
                make_box("exclusion_repeat", "exclusion_box", x0=0.32, y0=0.30, x1=0.46, y1=0.38),
            ],
            "panel_boxes": [
                make_box("subfigure_panel_A", "subfigure_panel", x0=0.06, y0=0.10, x1=0.48, y1=0.54),
                make_box("subfigure_panel_B", "subfigure_panel", x0=0.52, y0=0.10, x1=0.94, y1=0.54),
                make_box("flow_panel", "flow_panel", x0=0.08, y0=0.12, x1=0.46, y1=0.50),
                make_box("secondary_panel_validation", "secondary_panel", x0=0.54, y0=0.42, x1=0.92, y1=0.52),
                make_box("secondary_panel_core", "secondary_panel", x0=0.54, y0=0.28, x1=0.72, y1=0.38),
                make_box("secondary_panel_primary", "secondary_panel", x0=0.74, y0=0.28, x1=0.92, y1=0.38),
                make_box("secondary_panel_audit", "secondary_panel", x0=0.54, y0=0.14, x1=0.72, y1=0.24),
                make_box("secondary_panel_context", "secondary_panel", x0=0.74, y0=0.14, x1=0.92, y1=0.24),
            ],
            "guide_boxes": [
                make_box("flow_spine_screened_to_included", "flow_connector", x0=0.17, y0=0.34, x1=0.19, y1=0.40),
                make_box("flow_branch_repeat", "flow_branch_connector", x0=0.19, y0=0.33, x1=0.32, y1=0.35),
                make_box("hierarchy_root_trunk", "hierarchy_connector", x0=0.72, y0=0.38, x1=0.74, y1=0.42),
                make_box("hierarchy_root_branch", "hierarchy_connector", x0=0.63, y0=0.36, x1=0.83, y1=0.38),
                make_box("hierarchy_connector_left_middle_to_left_bottom", "hierarchy_connector", x0=0.63, y0=0.24, x1=0.65, y1=0.28),
                make_box("hierarchy_connector_right_middle_to_right_bottom", "hierarchy_connector", x0=0.83, y0=0.24, x1=0.85, y1=0.28),
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
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_illustration_subfigure_semantics_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("step_screened", "main_step", x0=0.08, y0=0.14, x1=0.46, y1=0.24),
            ],
            "panel_boxes": [
                make_box("flow_panel", "flow_panel", x0=0.08, y0=0.14, x1=0.46, y1=0.30),
                make_box("secondary_panel_validation", "secondary_panel", x0=0.54, y0=0.14, x1=0.92, y1=0.24),
            ],
            "guide_boxes": [],
            "metrics": {
                "steps": [
                    {"step_id": "screened"},
                    {"step_id": "included"},
                    {"step_id": "analysis"},
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
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_subfigure_panel" for issue in result["issues"])
    assert any(issue["rule_id"] == "missing_panel_label" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_structure_connectors_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
                "layout_boxes": [
                    make_box("panel_label_A", "panel_label", x0=0.08, y0=0.125, x1=0.11, y1=0.155),
                    make_box("panel_label_B", "panel_label", x0=0.52, y0=0.125, x1=0.55, y1=0.155),
                    make_box("step_screened", "main_step", x0=0.08, y0=0.40, x1=0.28, y1=0.50),
                    make_box("step_included", "main_step", x0=0.08, y0=0.24, x1=0.28, y1=0.34),
                    make_box("step_analysis", "main_step", x0=0.08, y0=0.08, x1=0.28, y1=0.18),
                    make_box("exclusion_repeat", "exclusion_box", x0=0.32, y0=0.30, x1=0.46, y1=0.38),
                ],
                "panel_boxes": [
                    make_box("subfigure_panel_A", "subfigure_panel", x0=0.06, y0=0.06, x1=0.48, y1=0.54),
                    make_box("subfigure_panel_B", "subfigure_panel", x0=0.52, y0=0.06, x1=0.94, y1=0.54),
                    make_box("flow_panel", "flow_panel", x0=0.08, y0=0.08, x1=0.46, y1=0.50),
                    make_box("secondary_panel_validation", "secondary_panel", x0=0.54, y0=0.42, x1=0.92, y1=0.52),
                    make_box("secondary_panel_core", "secondary_panel", x0=0.54, y0=0.28, x1=0.72, y1=0.38),
                    make_box("secondary_panel_primary", "secondary_panel", x0=0.74, y0=0.28, x1=0.92, y1=0.38),
                    make_box("secondary_panel_audit", "secondary_panel", x0=0.54, y0=0.14, x1=0.72, y1=0.24),
                    make_box("secondary_panel_context", "secondary_panel", x0=0.74, y0=0.14, x1=0.92, y1=0.24),
                ],
            "guide_boxes": [],
            "metrics": {
                "steps": [
                    {"step_id": "screened"},
                    {"step_id": "included"},
                    {"step_id": "analysis"},
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
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_flow_connector" for issue in result["issues"])
    assert any(issue["rule_id"] == "missing_hierarchy_connector" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_illustration_exclusion_overlaps_step() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("step_screened", "main_step", x0=0.08, y0=0.14, x1=0.46, y1=0.24),
                make_box("exclusion_repeat", "exclusion_box", x0=0.30, y0=0.16, x1=0.70, y1=0.24),
            ],
            "panel_boxes": [
                make_box("flow_panel", "flow_panel", x0=0.08, y0=0.14, x1=0.92, y1=0.30),
            ],
            "guide_boxes": [],
            "metrics": {
                "steps": [],
                "exclusions": [],
                "endpoint_inventory": [],
                "design_panels": [],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "exclusion_step_overlap" for issue in result["issues"])


def test_run_display_layout_qc_passes_for_participant_reporting_flow_without_ab_panels() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("participant_step_source", "main_step", x0=0.12, y0=0.66, x1=0.54, y1=0.78),
                make_box("participant_step_eligible", "main_step", x0=0.12, y0=0.48, x1=0.54, y1=0.60),
                make_box("participant_step_analysis", "main_step", x0=0.12, y0=0.30, x1=0.54, y1=0.42),
                make_box("participant_exclusion_missing", "exclusion_box", x0=0.64, y0=0.49, x1=0.90, y1=0.59),
                make_box("participant_summary_1", "summary_panel", x0=0.16, y0=0.08, x1=0.38, y1=0.18),
                make_box("participant_summary_2", "summary_panel", x0=0.42, y0=0.08, x1=0.64, y1=0.18),
            ],
            "panel_boxes": [
                make_box("participant_flow_main", "subfigure_panel", x0=0.10, y0=0.28, x1=0.92, y1=0.80),
            ],
            "guide_boxes": [
                make_box("flow_spine_source_to_eligible", "flow_connector", x0=0.32, y0=0.60, x1=0.34, y1=0.66),
                make_box("flow_spine_eligible_to_analysis", "flow_connector", x0=0.32, y0=0.42, x1=0.34, y1=0.48),
                make_box("flow_branch_missing", "flow_branch_connector", x0=0.54, y0=0.52, x1=0.64, y1=0.56),
            ],
            "metrics": {
                "layout_mode": "participant_flow",
                "steps": [
                    {"step_id": "source"},
                    {"step_id": "eligible"},
                    {"step_id": "analysis"},
                ],
                "exclusions": [
                    {"exclusion_id": "missing", "from_step_id": "eligible"},
                ],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_source",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 30,
                        "rendered_height_pt": 88.0,
                        "rendered_width_pt": 300.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_step_eligible",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 32,
                        "rendered_height_pt": 88.0,
                        "rendered_width_pt": 300.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_step_analysis",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 28,
                        "rendered_height_pt": 88.0,
                        "rendered_width_pt": 300.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_exclusion_missing",
                        "box_type": "exclusion_box",
                        "line_count": 2,
                        "max_line_chars": 24,
                        "rendered_height_pt": 62.0,
                        "rendered_width_pt": 190.0,
                        "padding_pt": 8.0,
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass"
    assert result["issues"] == []


def test_run_display_layout_qc_fails_for_left_compressed_participant_flow() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("participant_step_registry_records", "main_step", x0=0.10, y0=0.6855, x1=0.40, y1=0.835),
                make_box(
                    "participant_step_alliance_platform_records",
                    "main_step",
                    x0=0.10,
                    y0=0.4837,
                    x1=0.40,
                    y1=0.6332,
                ),
                make_box(
                    "participant_step_xiangya2_management_records",
                    "main_step",
                    x0=0.10,
                    y0=0.2818,
                    x1=0.40,
                    y1=0.4313,
                ),
                make_box(
                    "participant_step_xiangya2_precision_records",
                    "main_step",
                    x0=0.10,
                    y0=0.08,
                    x1=0.40,
                    y1=0.2295,
                ),
            ],
            "panel_boxes": [
                make_box("participant_flow_main", "subfigure_panel", x0=0.06, y0=0.06, x1=0.98, y1=0.855),
            ],
            "guide_boxes": [
                make_box(
                    "flow_spine_registry_records_to_alliance_platform_records",
                    "flow_connector",
                    x0=0.40,
                    y0=0.6332,
                    x1=0.42,
                    y1=0.6855,
                ),
                make_box(
                    "flow_spine_alliance_platform_records_to_xiangya2_management_records",
                    "flow_connector",
                    x0=0.40,
                    y0=0.4313,
                    x1=0.42,
                    y1=0.4837,
                ),
                make_box(
                    "flow_spine_xiangya2_management_records_to_xiangya2_precision_records",
                    "flow_connector",
                    x0=0.40,
                    y0=0.2295,
                    x1=0.42,
                    y1=0.2818,
                ),
            ],
            "metrics": {
                "layout_mode": "participant_flow",
                "steps": [
                    {"step_id": "registry_records"},
                    {"step_id": "alliance_platform_records"},
                    {"step_id": "xiangya2_management_records"},
                    {"step_id": "xiangya2_precision_records"},
                ],
                "exclusions": [],
                "endpoint_inventory": [],
                "design_panels": [],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_registry_records",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74.0,
                        "rendered_width_pt": 260.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_step_alliance_platform_records",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74.0,
                        "rendered_width_pt": 260.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_step_xiangya2_management_records",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74.0,
                        "rendered_width_pt": 260.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_step_xiangya2_precision_records",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 44,
                        "rendered_height_pt": 74.0,
                        "rendered_width_pt": 260.0,
                        "padding_pt": 10.0,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "participant_flow_content_horizontally_compressed" for issue in result["issues"])


def test_run_display_layout_qc_fails_participant_reporting_flow_when_connector_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_illustration_flow",
        layout_sidecar={
            "template_id": "cohort_flow_figure",
            "device": make_device(),
            "layout_boxes": [
                make_box("participant_step_source", "main_step", x0=0.12, y0=0.66, x1=0.54, y1=0.78),
                make_box("participant_step_eligible", "main_step", x0=0.12, y0=0.48, x1=0.54, y1=0.60),
            ],
            "panel_boxes": [
                make_box("participant_flow_main", "subfigure_panel", x0=0.10, y0=0.44, x1=0.58, y1=0.80),
            ],
            "guide_boxes": [],
            "metrics": {
                "layout_mode": "participant_flow",
                "steps": [{"step_id": "source"}, {"step_id": "eligible"}],
                "exclusions": [],
                "flow_nodes": [
                    {
                        "box_id": "participant_step_source",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 30,
                        "rendered_height_pt": 88.0,
                        "rendered_width_pt": 300.0,
                        "padding_pt": 10.0,
                    },
                    {
                        "box_id": "participant_step_eligible",
                        "box_type": "main_step",
                        "line_count": 2,
                        "max_line_chars": 32,
                        "rendered_height_pt": 88.0,
                        "rendered_width_pt": 300.0,
                        "padding_pt": 10.0,
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_flow_connector" for issue in result["issues"])
