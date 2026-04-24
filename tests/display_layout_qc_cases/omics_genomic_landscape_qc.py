from .shared import *

def test_run_display_layout_qc_fails_when_pathway_enrichment_dotplot_scale_label_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_pathway_enrichment_dotplot_panel",
        layout_sidecar={
            "template_id": "pathway_enrichment_dotplot_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.28, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.80, x1=0.12, y1=0.83),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.14, y0=0.10, x1=0.30, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.88, y0=0.20, x1=0.92, y1=0.76),
            ],
            "metrics": {
                "effect_scale_label": "Directionality score",
                "size_scale_label": "",
                "pathway_labels": ["IFN response", "EMT signaling"],
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "points": [
                            {"pathway_label": "IFN response", "x": 0.28, "y": 0.62, "size_value": 34.0, "effect_value": 0.91},
                            {"pathway_label": "EMT signaling", "x": 0.22, "y": 0.38, "size_value": 22.0, "effect_value": 0.42},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "size_scale_label_missing" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_celltype_marker_dotplot_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_celltype_marker_dotplot_panel",
        layout_sidecar={
            "template_id": "celltype_marker_dotplot_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.52, y0=0.86, x1=0.70, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                make_box("panel_label_B", "panel_label", x0=0.52, y0=0.76, x1=0.54, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.12),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.58, y0=0.08, x1=0.74, y1=0.12),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.34, x1=0.06, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
                make_box("panel_B", "panel", x0=0.52, y0=0.18, x1=0.84, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.88, y0=0.20, x1=0.92, y1=0.76),
            ],
            "metrics": {
                "effect_scale_label": "Mean expression",
                "size_scale_label": "Detection rate (%)",
                "celltype_labels": ["Basal", "Immune", "Stromal"],
                "marker_labels": ["KRT14", "CXCL13", "COL1A1"],
                "panels": [
                    {
                        "panel_id": "discovery",
                        "panel_title": "Discovery atlas",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "points": [
                            {"celltype_label": "Basal", "marker_label": "KRT14", "x": 0.20, "y": 0.68, "size_value": 84.0, "effect_value": 1.42},
                            {"celltype_label": "Basal", "marker_label": "CXCL13", "x": 0.27, "y": 0.68, "size_value": 12.0, "effect_value": 0.18},
                            {"celltype_label": "Basal", "marker_label": "COL1A1", "x": 0.34, "y": 0.68, "size_value": 8.0, "effect_value": 0.10},
                            {"celltype_label": "Immune", "marker_label": "KRT14", "x": 0.20, "y": 0.50, "size_value": 10.0, "effect_value": 0.12},
                            {"celltype_label": "Immune", "marker_label": "CXCL13", "x": 0.27, "y": 0.50, "size_value": 73.0, "effect_value": 1.21},
                            {"celltype_label": "Immune", "marker_label": "COL1A1", "x": 0.34, "y": 0.50, "size_value": 14.0, "effect_value": 0.22},
                            {"celltype_label": "Stromal", "marker_label": "KRT14", "x": 0.20, "y": 0.32, "size_value": 9.0, "effect_value": 0.10},
                            {"celltype_label": "Stromal", "marker_label": "CXCL13", "x": 0.27, "y": 0.32, "size_value": 18.0, "effect_value": 0.24},
                            {"celltype_label": "Stromal", "marker_label": "COL1A1", "x": 0.34, "y": 0.32, "size_value": 88.0, "effect_value": 1.36},
                        ],
                    },
                    {
                        "panel_id": "validation",
                        "panel_title": "Validation atlas",
                        "panel_label": "B",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "points": [
                            {"celltype_label": "Basal", "marker_label": "KRT14", "x": 0.62, "y": 0.68, "size_value": 80.0, "effect_value": 1.31},
                            {"celltype_label": "Basal", "marker_label": "CXCL13", "x": 0.69, "y": 0.68, "size_value": 15.0, "effect_value": 0.21},
                            {"celltype_label": "Basal", "marker_label": "COL1A1", "x": 0.76, "y": 0.68, "size_value": 7.0, "effect_value": 0.11},
                            {"celltype_label": "Immune", "marker_label": "KRT14", "x": 0.62, "y": 0.50, "size_value": 11.0, "effect_value": 0.14},
                            {"celltype_label": "Immune", "marker_label": "CXCL13", "x": 0.69, "y": 0.50, "size_value": 70.0, "effect_value": 1.16},
                            {"celltype_label": "Immune", "marker_label": "COL1A1", "x": 0.76, "y": 0.50, "size_value": 16.0, "effect_value": 0.25},
                            {"celltype_label": "Stromal", "marker_label": "KRT14", "x": 0.62, "y": 0.32, "size_value": 10.0, "effect_value": 0.11},
                            {"celltype_label": "Stromal", "marker_label": "CXCL13", "x": 0.69, "y": 0.32, "size_value": 19.0, "effect_value": 0.27},
                            {"celltype_label": "Stromal", "marker_label": "COL1A1", "x": 0.76, "y": 0.32, "size_value": 86.0, "effect_value": 1.29},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_celltype_marker_dotplot_marker_labels_are_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_celltype_marker_dotplot_panel",
        layout_sidecar={
            "template_id": "celltype_marker_dotplot_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.16, y0=0.08, x1=0.32, y1=0.12),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.34, x1=0.06, y1=0.66),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.88, y0=0.20, x1=0.92, y1=0.76),
            ],
            "metrics": {
                "effect_scale_label": "Mean expression",
                "size_scale_label": "Detection rate (%)",
                "celltype_labels": ["Basal", "Immune"],
                "marker_labels": [],
                "panels": [
                    {
                        "panel_id": "discovery",
                        "panel_title": "Discovery atlas",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "points": [
                            {"celltype_label": "Basal", "marker_label": "KRT14", "x": 0.20, "y": 0.60, "size_value": 84.0, "effect_value": 1.42},
                            {"celltype_label": "Immune", "marker_label": "CXCL13", "x": 0.30, "y": 0.40, "size_value": 73.0, "effect_value": 1.21},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "marker_labels_missing" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_omics_volcano_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_omics_volcano_panel",
        layout_sidecar={
            "template_id": "omics_volcano_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_title_B", "panel_title", x0=0.52, y0=0.86, x1=0.70, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                make_box("panel_label_B", "panel_label", x0=0.52, y0=0.76, x1=0.54, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.10, x1=0.30, y1=0.13),
                make_box("x_axis_title_B", "subplot_x_axis_title", x0=0.60, y0=0.10, x1=0.72, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
                make_box("label_A_0", "annotation_label", x0=0.31, y0=0.63, x1=0.39, y1=0.67),
                make_box("label_B_0", "annotation_label", x0=0.73, y0=0.59, x1=0.81, y1=0.63),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
                make_box("panel_B", "panel", x0=0.52, y0=0.18, x1=0.84, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("panel_A_threshold_left", "reference_line", x0=0.17, y0=0.18, x1=0.171, y1=0.80),
                make_box("panel_A_threshold_right", "reference_line", x0=0.35, y0=0.18, x1=0.351, y1=0.80),
                make_box("panel_A_significance_threshold", "reference_line", x0=0.10, y0=0.50, x1=0.42, y1=0.501),
                make_box("panel_B_threshold_left", "reference_line", x0=0.59, y0=0.18, x1=0.591, y1=0.80),
                make_box("panel_B_threshold_right", "reference_line", x0=0.77, y0=0.18, x1=0.771, y1=0.80),
                make_box("panel_B_significance_threshold", "reference_line", x0=0.52, y0=0.50, x1=0.84, y1=0.501),
            ],
            "metrics": {
                "legend_title": "Regulation",
                "effect_threshold": 1.0,
                "significance_threshold": 2.0,
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "effect_threshold_left_box_id": "panel_A_threshold_left",
                        "effect_threshold_right_box_id": "panel_A_threshold_right",
                        "significance_threshold_box_id": "panel_A_significance_threshold",
                        "points": [
                            {
                                "feature_label": "CXCL9",
                                "x": 0.33,
                                "y": 0.65,
                                "effect_value": 1.72,
                                "significance_value": 4.41,
                                "regulation_class": "upregulated",
                                "label_text": "CXCL9",
                                "label_box_id": "label_A_0",
                            },
                            {
                                "feature_label": "MKI67",
                                "x": 0.31,
                                "y": 0.57,
                                "effect_value": 1.19,
                                "significance_value": 3.28,
                                "regulation_class": "upregulated",
                            },
                            {
                                "feature_label": "COL1A1",
                                "x": 0.21,
                                "y": 0.61,
                                "effect_value": -1.34,
                                "significance_value": 3.92,
                                "regulation_class": "downregulated",
                            },
                            {
                                "feature_label": "GAPDH",
                                "x": 0.27,
                                "y": 0.29,
                                "effect_value": 0.14,
                                "significance_value": 0.52,
                                "regulation_class": "background",
                            },
                        ],
                    },
                    {
                        "panel_id": "proteome",
                        "panel_title": "Proteome",
                        "panel_label": "B",
                        "panel_box_id": "panel_B",
                        "panel_label_box_id": "panel_label_B",
                        "panel_title_box_id": "panel_title_B",
                        "x_axis_title_box_id": "x_axis_title_B",
                        "effect_threshold_left_box_id": "panel_B_threshold_left",
                        "effect_threshold_right_box_id": "panel_B_threshold_right",
                        "significance_threshold_box_id": "panel_B_significance_threshold",
                        "points": [
                            {
                                "feature_label": "CXCL9",
                                "x": 0.75,
                                "y": 0.61,
                                "effect_value": 1.26,
                                "significance_value": 3.36,
                                "regulation_class": "upregulated",
                                "label_text": "CXCL9",
                                "label_box_id": "label_B_0",
                            },
                            {
                                "feature_label": "STAT1",
                                "x": 0.73,
                                "y": 0.56,
                                "effect_value": 1.08,
                                "significance_value": 2.91,
                                "regulation_class": "upregulated",
                            },
                            {
                                "feature_label": "COL1A1",
                                "x": 0.61,
                                "y": 0.57,
                                "effect_value": -1.11,
                                "significance_value": 3.07,
                                "regulation_class": "downregulated",
                            },
                            {
                                "feature_label": "ACTB",
                                "x": 0.68,
                                "y": 0.30,
                                "effect_value": 0.11,
                                "significance_value": 0.61,
                                "regulation_class": "background",
                            },
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_omics_volcano_threshold_box_is_missing() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_omics_volcano_panel",
        layout_sidecar={
            "template_id": "omics_volcano_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_title_A", "panel_title", x0=0.10, y0=0.86, x1=0.30, y1=0.89),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.76, x1=0.12, y1=0.79),
                make_box("x_axis_title_A", "subplot_x_axis_title", x0=0.18, y0=0.10, x1=0.30, y1=0.13),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.36, x1=0.06, y1=0.66),
                make_box("label_A_0", "annotation_label", x0=0.31, y0=0.63, x1=0.39, y1=0.67),
            ],
            "panel_boxes": [
                make_box("panel_A", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.80),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.26, y0=0.02, x1=0.56, y1=0.08),
                make_box("panel_A_threshold_left", "reference_line", x0=0.17, y0=0.18, x1=0.171, y1=0.80),
                make_box("panel_A_significance_threshold", "reference_line", x0=0.10, y0=0.50, x1=0.42, y1=0.501),
            ],
            "metrics": {
                "legend_title": "Regulation",
                "effect_threshold": 1.0,
                "significance_threshold": 2.0,
                "panels": [
                    {
                        "panel_id": "transcriptome",
                        "panel_title": "Transcriptome",
                        "panel_label": "A",
                        "panel_box_id": "panel_A",
                        "panel_label_box_id": "panel_label_A",
                        "panel_title_box_id": "panel_title_A",
                        "x_axis_title_box_id": "x_axis_title_A",
                        "effect_threshold_left_box_id": "panel_A_threshold_left",
                        "effect_threshold_right_box_id": "panel_A_threshold_right",
                        "significance_threshold_box_id": "panel_A_significance_threshold",
                        "points": [
                            {
                                "feature_label": "CXCL9",
                                "x": 0.33,
                                "y": 0.65,
                                "effect_value": 1.72,
                                "significance_value": 4.41,
                                "regulation_class": "upregulated",
                                "label_text": "CXCL9",
                                "label_box_id": "label_A_0",
                            },
                            {
                                "feature_label": "COL1A1",
                                "x": 0.21,
                                "y": 0.61,
                                "effect_value": -1.34,
                                "significance_value": 3.92,
                                "regulation_class": "downregulated",
                            },
                        ],
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "effect_threshold_box_missing" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_oncoplot_mutation_landscape_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_oncoplot_mutation_landscape_panel",
        layout_sidecar={
            "template_id": "oncoplot_mutation_landscape_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.91, x1=0.10, y1=0.94),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.26, x1=0.05, y1=0.60),
                make_box("annotation_track_label_cohort", "annotation_track_label", x0=0.08, y0=0.71, x1=0.18, y1=0.74),
                make_box("annotation_track_label_response", "annotation_track_label", x0=0.08, y0=0.65, x1=0.20, y1=0.68),
                make_box("burden_bar_D1", "bar", x0=0.18, y0=0.82, x1=0.22, y1=0.88),
                make_box("burden_bar_D2", "bar", x0=0.23, y0=0.82, x1=0.27, y1=0.86),
                make_box("burden_bar_V1", "bar", x0=0.28, y0=0.82, x1=0.32, y1=0.88),
                make_box("burden_bar_V2", "bar", x0=0.33, y0=0.82, x1=0.37, y1=0.86),
                make_box("freq_bar_TP53", "bar", x0=0.74, y0=0.47, x1=0.82, y1=0.53),
                make_box("freq_bar_KRAS", "bar", x0=0.74, y0=0.38, x1=0.78, y1=0.44),
                make_box("freq_bar_EGFR", "bar", x0=0.74, y0=0.29, x1=0.78, y1=0.35),
                make_box("annotation_cohort_D1", "annotation_cell", x0=0.18, y0=0.70, x1=0.22, y1=0.74),
                make_box("annotation_cohort_D2", "annotation_cell", x0=0.23, y0=0.70, x1=0.27, y1=0.74),
                make_box("annotation_cohort_V1", "annotation_cell", x0=0.28, y0=0.70, x1=0.32, y1=0.74),
                make_box("annotation_cohort_V2", "annotation_cell", x0=0.33, y0=0.70, x1=0.37, y1=0.74),
                make_box("annotation_response_D1", "annotation_cell", x0=0.18, y0=0.64, x1=0.22, y1=0.68),
                make_box("annotation_response_D2", "annotation_cell", x0=0.23, y0=0.64, x1=0.27, y1=0.68),
                make_box("annotation_response_V1", "annotation_cell", x0=0.28, y0=0.64, x1=0.32, y1=0.68),
                make_box("annotation_response_V2", "annotation_cell", x0=0.33, y0=0.64, x1=0.37, y1=0.68),
                make_box("mutation_TP53_D1", "mutation_cell", x0=0.18, y0=0.47, x1=0.22, y1=0.53),
                make_box("mutation_KRAS_D2", "mutation_cell", x0=0.23, y0=0.38, x1=0.27, y1=0.44),
                make_box("mutation_TP53_V1", "mutation_cell", x0=0.28, y0=0.47, x1=0.32, y1=0.53),
                make_box("mutation_EGFR_V2", "mutation_cell", x0=0.33, y0=0.29, x1=0.37, y1=0.35),
            ],
            "panel_boxes": [
                make_box("panel_burden", "panel", x0=0.18, y0=0.80, x1=0.37, y1=0.89),
                make_box("panel_annotations", "panel", x0=0.18, y0=0.62, x1=0.37, y1=0.75),
                make_box("panel_matrix", "panel", x0=0.18, y0=0.26, x1=0.37, y1=0.56),
                make_box("panel_frequency", "panel", x0=0.74, y0=0.26, x1=0.84, y1=0.56),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.44, y0=0.02, x1=0.82, y1=0.10),
            ],
            "metrics": {
                "mutation_legend_title": "Alteration",
                "sample_ids": ["D1", "D2", "V1", "V2"],
                "gene_labels": ["TP53", "KRAS", "EGFR"],
                "annotation_tracks": [
                    {
                        "track_id": "cohort",
                        "track_label": "Cohort",
                        "track_label_box_id": "annotation_track_label_cohort",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Discovery", "box_id": "annotation_cohort_D1"},
                            {"sample_id": "D2", "category_label": "Discovery", "box_id": "annotation_cohort_D2"},
                            {"sample_id": "V1", "category_label": "Validation", "box_id": "annotation_cohort_V1"},
                            {"sample_id": "V2", "category_label": "Validation", "box_id": "annotation_cohort_V2"},
                        ],
                    },
                    {
                        "track_id": "response",
                        "track_label": "Response",
                        "track_label_box_id": "annotation_track_label_response",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Responder", "box_id": "annotation_response_D1"},
                            {"sample_id": "D2", "category_label": "Non-responder", "box_id": "annotation_response_D2"},
                            {"sample_id": "V1", "category_label": "Responder", "box_id": "annotation_response_V1"},
                            {"sample_id": "V2", "category_label": "Non-responder", "box_id": "annotation_response_V2"},
                        ],
                    },
                ],
                "sample_burdens": [
                    {"sample_id": "D1", "altered_gene_count": 1, "bar_box_id": "burden_bar_D1"},
                    {"sample_id": "D2", "altered_gene_count": 1, "bar_box_id": "burden_bar_D2"},
                    {"sample_id": "V1", "altered_gene_count": 1, "bar_box_id": "burden_bar_V1"},
                    {"sample_id": "V2", "altered_gene_count": 1, "bar_box_id": "burden_bar_V2"},
                ],
                "gene_altered_frequencies": [
                    {"gene_label": "TP53", "altered_fraction": 0.5, "bar_box_id": "freq_bar_TP53"},
                    {"gene_label": "KRAS", "altered_fraction": 0.25, "bar_box_id": "freq_bar_KRAS"},
                    {"gene_label": "EGFR", "altered_fraction": 0.25, "bar_box_id": "freq_bar_EGFR"},
                ],
                "altered_cells": [
                    {"sample_id": "D1", "gene_label": "TP53", "alteration_class": "missense", "box_id": "mutation_TP53_D1"},
                    {"sample_id": "D2", "gene_label": "KRAS", "alteration_class": "amplification", "box_id": "mutation_KRAS_D2"},
                    {"sample_id": "V1", "gene_label": "TP53", "alteration_class": "truncating", "box_id": "mutation_TP53_V1"},
                    {"sample_id": "V2", "gene_label": "EGFR", "alteration_class": "fusion", "box_id": "mutation_EGFR_V2"},
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_passes_for_cnv_recurrence_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_cnv_recurrence_summary_panel",
        layout_sidecar={
            "template_id": "cnv_recurrence_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.91, x1=0.10, y1=0.94),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.26, x1=0.05, y1=0.60),
                make_box("annotation_track_label_cohort", "annotation_track_label", x0=0.08, y0=0.71, x1=0.18, y1=0.74),
                make_box("annotation_track_label_response", "annotation_track_label", x0=0.08, y0=0.65, x1=0.20, y1=0.68),
                make_box("burden_bar_D1", "bar", x0=0.18, y0=0.82, x1=0.22, y1=0.88),
                make_box("burden_bar_D2", "bar", x0=0.23, y0=0.82, x1=0.27, y1=0.88),
                make_box("burden_bar_V1", "bar", x0=0.28, y0=0.82, x1=0.32, y1=0.88),
                make_box("burden_bar_V2", "bar", x0=0.33, y0=0.82, x1=0.37, y1=0.88),
                make_box("freq_gain_TP53", "bar", x0=0.74, y0=0.50, x1=0.80, y1=0.55),
                make_box("freq_loss_TP53", "bar", x0=0.68, y0=0.50, x1=0.74, y1=0.55),
                make_box("freq_gain_MYC", "bar", x0=0.74, y0=0.42, x1=0.80, y1=0.47),
                make_box("freq_loss_MYC", "bar", x0=0.68, y0=0.42, x1=0.74, y1=0.47),
                make_box("freq_gain_EGFR", "bar", x0=0.74, y0=0.34, x1=0.80, y1=0.39),
                make_box("freq_loss_EGFR", "bar", x0=0.68, y0=0.34, x1=0.74, y1=0.39),
                make_box("freq_gain_CDKN2A", "bar", x0=0.74, y0=0.26, x1=0.80, y1=0.31),
                make_box("freq_loss_CDKN2A", "bar", x0=0.68, y0=0.26, x1=0.74, y1=0.31),
                make_box("annotation_cohort_D1", "annotation_cell", x0=0.18, y0=0.70, x1=0.22, y1=0.74),
                make_box("annotation_cohort_D2", "annotation_cell", x0=0.23, y0=0.70, x1=0.27, y1=0.74),
                make_box("annotation_cohort_V1", "annotation_cell", x0=0.28, y0=0.70, x1=0.32, y1=0.74),
                make_box("annotation_cohort_V2", "annotation_cell", x0=0.33, y0=0.70, x1=0.37, y1=0.74),
                make_box("annotation_response_D1", "annotation_cell", x0=0.18, y0=0.64, x1=0.22, y1=0.68),
                make_box("annotation_response_D2", "annotation_cell", x0=0.23, y0=0.64, x1=0.27, y1=0.68),
                make_box("annotation_response_V1", "annotation_cell", x0=0.28, y0=0.64, x1=0.32, y1=0.68),
                make_box("annotation_response_V2", "annotation_cell", x0=0.33, y0=0.64, x1=0.37, y1=0.68),
                make_box("cnv_TP53_D1", "cnv_cell", x0=0.18, y0=0.50, x1=0.22, y1=0.55),
                make_box("cnv_TP53_D2", "cnv_cell", x0=0.23, y0=0.50, x1=0.27, y1=0.55),
                make_box("cnv_MYC_D1", "cnv_cell", x0=0.18, y0=0.42, x1=0.22, y1=0.47),
                make_box("cnv_MYC_V1", "cnv_cell", x0=0.28, y0=0.42, x1=0.32, y1=0.47),
                make_box("cnv_EGFR_D2", "cnv_cell", x0=0.23, y0=0.34, x1=0.27, y1=0.39),
                make_box("cnv_EGFR_V2", "cnv_cell", x0=0.33, y0=0.34, x1=0.37, y1=0.39),
                make_box("cnv_CDKN2A_V1", "cnv_cell", x0=0.28, y0=0.26, x1=0.32, y1=0.31),
                make_box("cnv_CDKN2A_V2", "cnv_cell", x0=0.33, y0=0.26, x1=0.37, y1=0.31),
            ],
            "panel_boxes": [
                make_box("panel_burden", "panel", x0=0.18, y0=0.80, x1=0.37, y1=0.89),
                make_box("panel_annotations", "panel", x0=0.18, y0=0.62, x1=0.37, y1=0.75),
                make_box("panel_matrix", "panel", x0=0.18, y0=0.24, x1=0.37, y1=0.58),
                make_box("panel_frequency", "panel", x0=0.68, y0=0.24, x1=0.82, y1=0.58),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.42, y0=0.02, x1=0.86, y1=0.10),
            ],
            "metrics": {
                "cnv_legend_title": "CNV state",
                "sample_ids": ["D1", "D2", "V1", "V2"],
                "region_labels": ["TP53", "MYC", "EGFR", "CDKN2A"],
                "annotation_tracks": [
                    {
                        "track_id": "cohort",
                        "track_label": "Cohort",
                        "track_label_box_id": "annotation_track_label_cohort",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Discovery", "box_id": "annotation_cohort_D1"},
                            {"sample_id": "D2", "category_label": "Discovery", "box_id": "annotation_cohort_D2"},
                            {"sample_id": "V1", "category_label": "Validation", "box_id": "annotation_cohort_V1"},
                            {"sample_id": "V2", "category_label": "Validation", "box_id": "annotation_cohort_V2"},
                        ],
                    },
                    {
                        "track_id": "response",
                        "track_label": "Response",
                        "track_label_box_id": "annotation_track_label_response",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Responder", "box_id": "annotation_response_D1"},
                            {"sample_id": "D2", "category_label": "Non-responder", "box_id": "annotation_response_D2"},
                            {"sample_id": "V1", "category_label": "Responder", "box_id": "annotation_response_V1"},
                            {"sample_id": "V2", "category_label": "Non-responder", "box_id": "annotation_response_V2"},
                        ],
                    },
                ],
                "sample_burdens": [
                    {"sample_id": "D1", "altered_region_count": 2, "bar_box_id": "burden_bar_D1"},
                    {"sample_id": "D2", "altered_region_count": 2, "bar_box_id": "burden_bar_D2"},
                    {"sample_id": "V1", "altered_region_count": 2, "bar_box_id": "burden_bar_V1"},
                    {"sample_id": "V2", "altered_region_count": 2, "bar_box_id": "burden_bar_V2"},
                ],
                "region_gain_loss_frequencies": [
                    {
                        "region_label": "TP53",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_TP53",
                        "loss_bar_box_id": "freq_loss_TP53",
                    },
                    {
                        "region_label": "MYC",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_MYC",
                        "loss_bar_box_id": "freq_loss_MYC",
                    },
                    {
                        "region_label": "EGFR",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_EGFR",
                        "loss_bar_box_id": "freq_loss_EGFR",
                    },
                    {
                        "region_label": "CDKN2A",
                        "gain_fraction": 0.25,
                        "loss_fraction": 0.25,
                        "gain_bar_box_id": "freq_gain_CDKN2A",
                        "loss_bar_box_id": "freq_loss_CDKN2A",
                    },
                ],
                "cnv_cells": [
                    {"sample_id": "D1", "region_label": "TP53", "cnv_state": "amplification", "box_id": "cnv_TP53_D1"},
                    {"sample_id": "D2", "region_label": "TP53", "cnv_state": "loss", "box_id": "cnv_TP53_D2"},
                    {"sample_id": "D1", "region_label": "MYC", "cnv_state": "gain", "box_id": "cnv_MYC_D1"},
                    {"sample_id": "V1", "region_label": "MYC", "cnv_state": "loss", "box_id": "cnv_MYC_V1"},
                    {"sample_id": "D2", "region_label": "EGFR", "cnv_state": "gain", "box_id": "cnv_EGFR_D2"},
                    {"sample_id": "V2", "region_label": "EGFR", "cnv_state": "loss", "box_id": "cnv_EGFR_V2"},
                    {"sample_id": "V1", "region_label": "CDKN2A", "cnv_state": "deep_loss", "box_id": "cnv_CDKN2A_V1"},
                    {"sample_id": "V2", "region_label": "CDKN2A", "cnv_state": "gain", "box_id": "cnv_CDKN2A_V2"},
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_passes_for_genomic_alteration_landscape_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_genomic_alteration_landscape_panel",
        layout_sidecar={
            "template_id": "genomic_alteration_landscape_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.91, x1=0.10, y1=0.94),
                make_box("y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.26, x1=0.05, y1=0.60),
                make_box("annotation_track_label_cohort", "annotation_track_label", x0=0.08, y0=0.71, x1=0.18, y1=0.74),
                make_box("annotation_track_label_response", "annotation_track_label", x0=0.08, y0=0.65, x1=0.20, y1=0.68),
                make_box("burden_bar_D1", "bar", x0=0.18, y0=0.82, x1=0.22, y1=0.88),
                make_box("burden_bar_D2", "bar", x0=0.23, y0=0.82, x1=0.27, y1=0.86),
                make_box("burden_bar_V1", "bar", x0=0.28, y0=0.82, x1=0.32, y1=0.90),
                make_box("burden_bar_V2", "bar", x0=0.33, y0=0.82, x1=0.37, y1=0.88),
                make_box("freq_bar_TP53", "bar", x0=0.74, y0=0.50, x1=0.82, y1=0.56),
                make_box("freq_bar_KRAS", "bar", x0=0.74, y0=0.42, x1=0.78, y1=0.48),
                make_box("freq_bar_EGFR", "bar", x0=0.74, y0=0.34, x1=0.78, y1=0.40),
                make_box("freq_bar_PIK3CA", "bar", x0=0.74, y0=0.26, x1=0.78, y1=0.32),
                make_box("annotation_cohort_D1", "annotation_cell", x0=0.18, y0=0.70, x1=0.22, y1=0.74),
                make_box("annotation_cohort_D2", "annotation_cell", x0=0.23, y0=0.70, x1=0.27, y1=0.74),
                make_box("annotation_cohort_V1", "annotation_cell", x0=0.28, y0=0.70, x1=0.32, y1=0.74),
                make_box("annotation_cohort_V2", "annotation_cell", x0=0.33, y0=0.70, x1=0.37, y1=0.74),
                make_box("annotation_response_D1", "annotation_cell", x0=0.18, y0=0.64, x1=0.22, y1=0.68),
                make_box("annotation_response_D2", "annotation_cell", x0=0.23, y0=0.64, x1=0.27, y1=0.68),
                make_box("annotation_response_V1", "annotation_cell", x0=0.28, y0=0.64, x1=0.32, y1=0.68),
                make_box("annotation_response_V2", "annotation_cell", x0=0.33, y0=0.64, x1=0.37, y1=0.68),
                make_box("alteration_TP53_D1", "alteration_cell", x0=0.18, y0=0.50, x1=0.22, y1=0.56),
                make_box("overlay_TP53_D1", "alteration_overlay", x0=0.191, y0=0.514, x1=0.209, y1=0.546),
                make_box("alteration_KRAS_D2", "alteration_cell", x0=0.23, y0=0.42, x1=0.27, y1=0.48),
                make_box("alteration_TP53_V1", "alteration_cell", x0=0.28, y0=0.50, x1=0.32, y1=0.56),
                make_box("alteration_PIK3CA_V1", "alteration_cell", x0=0.28, y0=0.26, x1=0.32, y1=0.32),
                make_box("alteration_EGFR_V2", "alteration_cell", x0=0.33, y0=0.34, x1=0.37, y1=0.40),
                make_box("overlay_EGFR_V2", "alteration_overlay", x0=0.341, y0=0.354, x1=0.359, y1=0.386),
            ],
            "panel_boxes": [
                make_box("panel_burden", "panel", x0=0.18, y0=0.80, x1=0.37, y1=0.90),
                make_box("panel_annotations", "panel", x0=0.18, y0=0.62, x1=0.37, y1=0.75),
                make_box("panel_matrix", "panel", x0=0.18, y0=0.24, x1=0.37, y1=0.58),
                make_box("panel_frequency", "panel", x0=0.74, y0=0.24, x1=0.84, y1=0.58),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.42, y0=0.02, x1=0.86, y1=0.10),
            ],
            "metrics": {
                "alteration_legend_title": "Genomic alteration",
                "sample_ids": ["D1", "D2", "V1", "V2"],
                "gene_labels": ["TP53", "KRAS", "EGFR", "PIK3CA"],
                "annotation_tracks": [
                    {
                        "track_id": "cohort",
                        "track_label": "Cohort",
                        "track_label_box_id": "annotation_track_label_cohort",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Discovery", "box_id": "annotation_cohort_D1"},
                            {"sample_id": "D2", "category_label": "Discovery", "box_id": "annotation_cohort_D2"},
                            {"sample_id": "V1", "category_label": "Validation", "box_id": "annotation_cohort_V1"},
                            {"sample_id": "V2", "category_label": "Validation", "box_id": "annotation_cohort_V2"},
                        ],
                    },
                    {
                        "track_id": "response",
                        "track_label": "Response",
                        "track_label_box_id": "annotation_track_label_response",
                        "cells": [
                            {"sample_id": "D1", "category_label": "Responder", "box_id": "annotation_response_D1"},
                            {"sample_id": "D2", "category_label": "Non-responder", "box_id": "annotation_response_D2"},
                            {"sample_id": "V1", "category_label": "Responder", "box_id": "annotation_response_V1"},
                            {"sample_id": "V2", "category_label": "Non-responder", "box_id": "annotation_response_V2"},
                        ],
                    },
                ],
                "sample_burdens": [
                    {"sample_id": "D1", "altered_gene_count": 1, "bar_box_id": "burden_bar_D1"},
                    {"sample_id": "D2", "altered_gene_count": 1, "bar_box_id": "burden_bar_D2"},
                    {"sample_id": "V1", "altered_gene_count": 2, "bar_box_id": "burden_bar_V1"},
                    {"sample_id": "V2", "altered_gene_count": 1, "bar_box_id": "burden_bar_V2"},
                ],
                "gene_alteration_frequencies": [
                    {"gene_label": "TP53", "altered_fraction": 0.5, "bar_box_id": "freq_bar_TP53"},
                    {"gene_label": "KRAS", "altered_fraction": 0.25, "bar_box_id": "freq_bar_KRAS"},
                    {"gene_label": "EGFR", "altered_fraction": 0.25, "bar_box_id": "freq_bar_EGFR"},
                    {"gene_label": "PIK3CA", "altered_fraction": 0.25, "bar_box_id": "freq_bar_PIK3CA"},
                ],
                "alteration_cells": [
                    {
                        "sample_id": "D1",
                        "gene_label": "TP53",
                        "mutation_class": "missense",
                        "cnv_state": "loss",
                        "box_id": "alteration_TP53_D1",
                        "overlay_box_id": "overlay_TP53_D1",
                    },
                    {
                        "sample_id": "D2",
                        "gene_label": "KRAS",
                        "cnv_state": "amplification",
                        "box_id": "alteration_KRAS_D2",
                    },
                    {
                        "sample_id": "V1",
                        "gene_label": "TP53",
                        "mutation_class": "truncating",
                        "box_id": "alteration_TP53_V1",
                    },
                    {
                        "sample_id": "V1",
                        "gene_label": "PIK3CA",
                        "cnv_state": "gain",
                        "box_id": "alteration_PIK3CA_V1",
                    },
                    {
                        "sample_id": "V2",
                        "gene_label": "EGFR",
                        "mutation_class": "fusion",
                        "cnv_state": "amplification",
                        "box_id": "alteration_EGFR_V2",
                        "overlay_box_id": "overlay_EGFR_V2",
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []
