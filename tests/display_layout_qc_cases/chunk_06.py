from .shared import *

def test_run_display_layout_qc_passes_for_genomic_program_governance_summary_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_genomic_program_governance_summary_panel",
        layout_sidecar={
            "template_id": "genomic_program_governance_summary_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.88, x1=0.10, y1=0.91),
                make_box("panel_label_B", "panel_label", x0=0.64, y0=0.88, x1=0.66, y1=0.91),
                make_box("panel_title_A", "panel_title", x0=0.14, y0=0.88, x1=0.44, y1=0.91),
                make_box("panel_title_B", "panel_title", x0=0.70, y0=0.88, x1=0.92, y1=0.91),
                make_box("row_label_pi3k", "row_label", x0=0.06, y0=0.68, x1=0.17, y1=0.71),
                make_box("row_label_cycle", "row_label", x0=0.06, y0=0.53, x1=0.20, y1=0.56),
                make_box("row_label_immune", "row_label", x0=0.06, y0=0.38, x1=0.20, y1=0.41),
                make_box("evidence_pi3k_alteration", "evidence_cell", x0=0.19, y0=0.67, x1=0.22, y1=0.70),
                make_box("evidence_pi3k_proteome", "evidence_cell", x0=0.25, y0=0.67, x1=0.28, y1=0.70),
                make_box("evidence_pi3k_phosphoproteome", "evidence_cell", x0=0.31, y0=0.67, x1=0.34, y1=0.70),
                make_box("evidence_pi3k_glycoproteome", "evidence_cell", x0=0.37, y0=0.67, x1=0.40, y1=0.70),
                make_box("evidence_pi3k_pathway", "evidence_cell", x0=0.43, y0=0.67, x1=0.46, y1=0.70),
                make_box("evidence_cycle_alteration", "evidence_cell", x0=0.19, y0=0.52, x1=0.22, y1=0.55),
                make_box("evidence_cycle_proteome", "evidence_cell", x0=0.25, y0=0.52, x1=0.28, y1=0.55),
                make_box("evidence_cycle_phosphoproteome", "evidence_cell", x0=0.31, y0=0.52, x1=0.34, y1=0.55),
                make_box("evidence_cycle_glycoproteome", "evidence_cell", x0=0.37, y0=0.52, x1=0.40, y1=0.55),
                make_box("evidence_cycle_pathway", "evidence_cell", x0=0.43, y0=0.52, x1=0.46, y1=0.55),
                make_box("evidence_immune_alteration", "evidence_cell", x0=0.19, y0=0.37, x1=0.22, y1=0.40),
                make_box("evidence_immune_proteome", "evidence_cell", x0=0.25, y0=0.37, x1=0.28, y1=0.40),
                make_box("evidence_immune_phosphoproteome", "evidence_cell", x0=0.31, y0=0.37, x1=0.34, y1=0.40),
                make_box("evidence_immune_glycoproteome", "evidence_cell", x0=0.37, y0=0.37, x1=0.40, y1=0.40),
                make_box("evidence_immune_pathway", "evidence_cell", x0=0.43, y0=0.37, x1=0.46, y1=0.40),
                make_box("priority_pi3k", "priority_badge", x0=0.69, y0=0.67, x1=0.76, y1=0.70),
                make_box("verdict_pi3k", "verdict_value", x0=0.77, y0=0.67, x1=0.84, y1=0.70),
                make_box("support_pi3k", "row_support", x0=0.85, y0=0.67, x1=0.90, y1=0.70),
                make_box("action_pi3k", "row_action", x0=0.69, y0=0.63, x1=0.93, y1=0.66),
                make_box("priority_cycle", "priority_badge", x0=0.69, y0=0.52, x1=0.76, y1=0.55),
                make_box("verdict_cycle", "verdict_value", x0=0.77, y0=0.52, x1=0.84, y1=0.55),
                make_box("support_cycle", "row_support", x0=0.85, y0=0.52, x1=0.90, y1=0.55),
                make_box("action_cycle", "row_action", x0=0.69, y0=0.48, x1=0.93, y1=0.51),
                make_box("priority_immune", "priority_badge", x0=0.69, y0=0.37, x1=0.76, y1=0.40),
                make_box("verdict_immune", "verdict_value", x0=0.77, y0=0.37, x1=0.84, y1=0.40),
                make_box("support_immune", "row_support", x0=0.85, y0=0.37, x1=0.90, y1=0.40),
                make_box("action_immune", "row_action", x0=0.69, y0=0.33, x1=0.93, y1=0.36),
            ],
            "panel_boxes": [
                make_box("panel_evidence", "panel", x0=0.12, y0=0.28, x1=0.56, y1=0.86),
                make_box("panel_summary", "panel", x0=0.64, y0=0.28, x1=0.94, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend_support", "legend", x0=0.18, y0=0.18, x1=0.40, y1=0.24),
                make_box("colorbar_effect", "colorbar", x0=0.52, y0=0.28, x1=0.55, y1=0.78),
            ],
            "metrics": {
                "effect_scale_label": "Direction and magnitude",
                "support_scale_label": "Support fraction",
                "layer_labels": [
                    "Alteration",
                    "Proteome",
                    "Phosphoproteome",
                    "Glycoproteome",
                    "Pathway",
                ],
                "programs": [
                    {
                        "program_id": "pi3k_growth",
                        "program_label": "PI3K growth program",
                        "lead_driver_label": "EGFR",
                        "dominant_pathway_label": "PI3K-AKT signaling",
                        "pathway_hit_count": 8,
                        "priority_rank": 1,
                        "priority_band": "high_priority",
                        "verdict": "convergent",
                        "action": "Promote to manuscript main-text synthesis",
                        "row_label_box_id": "row_label_pi3k",
                        "priority_box_id": "priority_pi3k",
                        "verdict_box_id": "verdict_pi3k",
                        "support_box_id": "support_pi3k",
                        "action_box_id": "action_pi3k",
                        "layer_supports": [
                            {"layer_id": "alteration", "effect_value": 0.88, "support_fraction": 0.82, "cell_box_id": "evidence_pi3k_alteration"},
                            {"layer_id": "proteome", "effect_value": 1.21, "support_fraction": 0.74, "cell_box_id": "evidence_pi3k_proteome"},
                            {"layer_id": "phosphoproteome", "effect_value": 1.48, "support_fraction": 0.86, "cell_box_id": "evidence_pi3k_phosphoproteome"},
                            {"layer_id": "glycoproteome", "effect_value": 0.93, "support_fraction": 0.69, "cell_box_id": "evidence_pi3k_glycoproteome"},
                            {"layer_id": "pathway", "effect_value": 1.34, "support_fraction": 0.78, "cell_box_id": "evidence_pi3k_pathway"},
                        ],
                    },
                    {
                        "program_id": "cell_cycle_stress",
                        "program_label": "Cell-cycle stress program",
                        "lead_driver_label": "TP53",
                        "dominant_pathway_label": "Cell cycle",
                        "pathway_hit_count": 6,
                        "priority_rank": 2,
                        "priority_band": "monitor",
                        "verdict": "layer_specific",
                        "action": "Keep as support-domain evidence",
                        "row_label_box_id": "row_label_cycle",
                        "priority_box_id": "priority_cycle",
                        "verdict_box_id": "verdict_cycle",
                        "support_box_id": "support_cycle",
                        "action_box_id": "action_cycle",
                        "layer_supports": [
                            {"layer_id": "alteration", "effect_value": 0.76, "support_fraction": 0.67, "cell_box_id": "evidence_cycle_alteration"},
                            {"layer_id": "proteome", "effect_value": 1.02, "support_fraction": 0.72, "cell_box_id": "evidence_cycle_proteome"},
                            {"layer_id": "phosphoproteome", "effect_value": 1.16, "support_fraction": 0.75, "cell_box_id": "evidence_cycle_phosphoproteome"},
                            {"layer_id": "glycoproteome", "effect_value": 0.41, "support_fraction": 0.44, "cell_box_id": "evidence_cycle_glycoproteome"},
                            {"layer_id": "pathway", "effect_value": 1.08, "support_fraction": 0.71, "cell_box_id": "evidence_cycle_pathway"},
                        ],
                    },
                    {
                        "program_id": "immune_suppression",
                        "program_label": "Immune suppression program",
                        "lead_driver_label": "PIK3CA",
                        "dominant_pathway_label": "Immune signaling",
                        "pathway_hit_count": 4,
                        "priority_rank": 3,
                        "priority_band": "watchlist",
                        "verdict": "context_dependent",
                        "action": "Retain for supplementary context only",
                        "row_label_box_id": "row_label_immune",
                        "priority_box_id": "priority_immune",
                        "verdict_box_id": "verdict_immune",
                        "support_box_id": "support_immune",
                        "action_box_id": "action_immune",
                        "layer_supports": [
                            {"layer_id": "alteration", "effect_value": 0.22, "support_fraction": 0.36, "cell_box_id": "evidence_immune_alteration"},
                            {"layer_id": "proteome", "effect_value": 0.58, "support_fraction": 0.49, "cell_box_id": "evidence_immune_proteome"},
                            {"layer_id": "phosphoproteome", "effect_value": -0.34, "support_fraction": 0.41, "cell_box_id": "evidence_immune_phosphoproteome"},
                            {"layer_id": "glycoproteome", "effect_value": -0.27, "support_fraction": 0.38, "cell_box_id": "evidence_immune_glycoproteome"},
                            {"layer_id": "pathway", "effect_value": 0.43, "support_fraction": 0.47, "cell_box_id": "evidence_immune_pathway"},
                        ],
                    },
                ],
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_genomic_program_governance_summary_panel_drops_declared_layer_support() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_genomic_program_governance_summary_panel",
        layout_sidecar={
            "template_id": "genomic_program_governance_summary_panel",
            "device": make_device(),
            "layout_boxes": [],
            "panel_boxes": [],
            "guide_boxes": [],
            "metrics": {
                "effect_scale_label": "Direction and magnitude",
                "support_scale_label": "Support fraction",
                "layer_labels": [
                    "Alteration",
                    "Proteome",
                    "Phosphoproteome",
                    "Glycoproteome",
                    "Pathway",
                ],
                "programs": [
                    {
                        "program_id": "pi3k_growth",
                        "program_label": "PI3K growth program",
                        "lead_driver_label": "EGFR",
                        "dominant_pathway_label": "PI3K-AKT signaling",
                        "pathway_hit_count": 8,
                        "priority_rank": 1,
                        "priority_band": "high_priority",
                        "verdict": "convergent",
                        "action": "Promote to manuscript main-text synthesis",
                        "layer_supports": [
                            {"layer_id": "alteration", "effect_value": 0.88, "support_fraction": 0.82},
                            {"layer_id": "proteome", "effect_value": 1.21, "support_fraction": 0.74},
                            {"layer_id": "phosphoproteome", "effect_value": 1.48, "support_fraction": 0.86},
                            {"layer_id": "glycoproteome", "effect_value": 0.93, "support_fraction": 0.69},
                        ],
                    }
                ],
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "program_layer_support_coverage_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_oncoplot_annotation_track_is_incomplete() -> None:
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

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "annotation_track_coverage_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_fails_when_celltype_signature_panel_is_missing_colorbar() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_celltype_signature_panel",
        layout_sidecar={
            "template_id": "celltype_signature_heatmap",
            "device": make_device(),
            "layout_boxes": [
                make_box("embedding_panel_title", "panel_title", x0=0.12, y0=0.12, x1=0.32, y1=0.16),
                make_box("heatmap_panel_title", "panel_title", x0=0.52, y0=0.12, x1=0.82, y1=0.16),
                make_box("embedding_x_axis_title", "subplot_x_axis_title", x0=0.16, y0=0.92, x1=0.30, y1=0.96),
                make_box("embedding_y_axis_title", "subplot_y_axis_title", x0=0.04, y0=0.24, x1=0.07, y1=0.74),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.58, y0=0.92, x1=0.76, y1=0.96),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.46, y0=0.24, x1=0.49, y1=0.74),
                make_box("panel_label_A", "panel_label", x0=0.10, y0=0.82, x1=0.13, y1=0.86),
                make_box("panel_label_B", "panel_label", x0=0.50, y0=0.82, x1=0.53, y1=0.86),
            ],
            "panel_boxes": [
                make_box("panel_left", "panel", x0=0.10, y0=0.18, x1=0.42, y1=0.86),
                make_box("panel_right", "heatmap_tile_region", x0=0.50, y0=0.18, x1=0.82, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.14, y0=0.02, x1=0.34, y1=0.08),
            ],
            "metrics": {
                "points": [
                    {"x": 0.18, "y": 0.70, "group": "T cells"},
                    {"x": 0.34, "y": 0.30, "group": "Myeloid"},
                ],
                "group_labels": ["T cells", "Myeloid"],
                "matrix_cells": [
                    {"x": "T cells", "y": "IFN response", "value": 0.72},
                    {"x": "Myeloid", "y": "IFN response", "value": -0.18},
                    {"x": "T cells", "y": "TGF-beta", "value": -0.21},
                    {"x": "Myeloid", "y": "TGF-beta", "value": 0.64},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "missing_box" and issue["target"] == "colorbar" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_single_cell_atlas_overview_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_single_cell_atlas_overview_panel",
        layout_sidecar={
            "template_id": "single_cell_atlas_overview_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("embedding_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("embedding_x_axis_title", "subplot_x_axis_title", x0=0.10, y0=0.10, x1=0.22, y1=0.13),
                make_box("embedding_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_embedding", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "state_label": "T cells"},
                    {"x": 0.23, "y": 0.34, "state_label": "Myeloid"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["IFN response", "TGF-beta signaling"],
                "composition_groups": [
                    {
                        "group_label": "Tumor",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.62},
                            {"state_label": "Myeloid", "proportion": 0.38},
                        ],
                    },
                    {
                        "group_label": "Adjacent",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.41},
                            {"state_label": "Myeloid", "proportion": 0.59},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "IFN response", "value": 0.72},
                    {"x": "Myeloid", "y": "IFN response", "value": -0.14},
                    {"x": "T cells", "y": "TGF-beta signaling", "value": -0.21},
                    {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.67},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_single_cell_atlas_overview_composition_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_single_cell_atlas_overview_panel",
        layout_sidecar={
            "template_id": "single_cell_atlas_overview_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("embedding_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.24, y1=0.91),
                make_box("embedding_x_axis_title", "subplot_x_axis_title", x0=0.10, y0=0.10, x1=0.22, y1=0.13),
                make_box("embedding_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_embedding", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "state_label": "T cells"},
                    {"x": 0.23, "y": 0.34, "state_label": "Myeloid"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["IFN response", "TGF-beta signaling"],
                "composition_groups": [
                    {
                        "group_label": "Tumor",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.62},
                        ],
                    },
                    {
                        "group_label": "Adjacent",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.41},
                            {"state_label": "Myeloid", "proportion": 0.52},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "IFN response", "value": 0.72},
                    {"x": "Myeloid", "y": "IFN response", "value": -0.14},
                    {"x": "T cells", "y": "TGF-beta signaling", "value": -0.21},
                    {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.67},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "composition_group_state_set_mismatch" for issue in result["issues"])
    assert any(issue["rule_id"] == "composition_group_sum_invalid" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_atlas_spatial_bridge_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_bridge_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_bridge_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("atlas_panel_title", "panel_title", x0=0.20, y0=0.88, x1=0.30, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.22, y0=0.52, x1=0.28, y1=0.54),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.68, x1=0.05, y1=0.77),
                make_box("spatial_panel_title", "panel_title", x0=0.65, y0=0.88, x1=0.81, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.52, x1=0.79, y1=0.54),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.51, y0=0.62, x1=0.53, y1=0.83),
                make_box("composition_panel_title", "panel_title", x0=0.15, y0=0.47, x1=0.35, y1=0.50),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.18, y0=0.12, x1=0.32, y1=0.15),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.29, x1=0.05, y1=0.36),
                make_box("heatmap_panel_title", "panel_title", x0=0.63, y0=0.47, x1=0.80, y1=0.50),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.68, y0=0.11, x1=0.75, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.43, y0=0.23, x1=0.45, y1=0.42),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.83, x1=0.09, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.54, y0=0.83, x1=0.55, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.08, y0=0.40, x1=0.09, y1=0.42),
                make_box("panel_label_D", "panel_label", x0=0.54, y0=0.40, x1=0.55, y1=0.42),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.54, x1=0.44, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.53, y0=0.54, x1=0.88, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.07, y0=0.18, x1=0.44, y1=0.44),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.53, y0=0.18, x1=0.88, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.16, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.18, x1=0.94, y1=0.44),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.14, "y": 0.74, "state_label": "T cells"},
                    {"x": 0.29, "y": 0.62, "state_label": "Myeloid"},
                ],
                "spatial_points": [
                    {"x": 0.60, "y": 0.76, "state_label": "T cells"},
                    {"x": 0.78, "y": 0.62, "state_label": "Myeloid"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.64},
                            {"state_label": "Myeloid", "proportion": 0.36},
                        ],
                    },
                    {
                        "group_label": "Invasive margin",
                        "group_order": 2,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.42},
                            {"state_label": "Myeloid", "proportion": 0.58},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Myeloid", "y": "CXCL13 program", "value": -0.16},
                    {"x": "T cells", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Myeloid", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_atlas_spatial_bridge_spatial_states_drift() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_atlas_spatial_bridge_panel",
        layout_sidecar={
            "template_id": "atlas_spatial_bridge_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("atlas_panel_title", "panel_title", x0=0.20, y0=0.88, x1=0.30, y1=0.91),
                make_box("atlas_x_axis_title", "subplot_x_axis_title", x0=0.22, y0=0.52, x1=0.28, y1=0.54),
                make_box("atlas_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.68, x1=0.05, y1=0.77),
                make_box("spatial_panel_title", "panel_title", x0=0.65, y0=0.88, x1=0.81, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.67, y0=0.52, x1=0.79, y1=0.54),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.51, y0=0.62, x1=0.53, y1=0.83),
                make_box("composition_panel_title", "panel_title", x0=0.15, y0=0.47, x1=0.35, y1=0.50),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.18, y0=0.12, x1=0.32, y1=0.15),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.03, y0=0.29, x1=0.05, y1=0.36),
                make_box("heatmap_panel_title", "panel_title", x0=0.63, y0=0.47, x1=0.80, y1=0.50),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.68, y0=0.11, x1=0.75, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.43, y0=0.23, x1=0.45, y1=0.42),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.83, x1=0.09, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.54, y0=0.83, x1=0.55, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.08, y0=0.40, x1=0.09, y1=0.42),
                make_box("panel_label_D", "panel_label", x0=0.54, y0=0.40, x1=0.55, y1=0.42),
            ],
            "panel_boxes": [
                make_box("panel_atlas", "panel", x0=0.07, y0=0.54, x1=0.44, y1=0.86),
                make_box("panel_spatial", "panel", x0=0.53, y0=0.54, x1=0.88, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.07, y0=0.18, x1=0.44, y1=0.44),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.53, y0=0.18, x1=0.88, y1=0.44),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.16, y0=0.02, x1=0.42, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.18, x1=0.94, y1=0.44),
            ],
            "metrics": {
                "atlas_points": [
                    {"x": 0.14, "y": 0.74, "state_label": "T cells"},
                    {"x": 0.29, "y": 0.62, "state_label": "Myeloid"},
                ],
                "spatial_points": [
                    {"x": 0.60, "y": 0.76, "state_label": "T cells"},
                    {"x": 0.78, "y": 0.62, "state_label": "Fibroblast"},
                ],
                "state_labels": ["T cells", "Myeloid"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "state_proportions": [
                            {"state_label": "T cells", "proportion": 0.64},
                            {"state_label": "Myeloid", "proportion": 0.36},
                        ],
                    }
                ],
                "matrix_cells": [
                    {"x": "T cells", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Myeloid", "y": "CXCL13 program", "value": -0.16},
                    {"x": "T cells", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Myeloid", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "spatial_point_state_label_unknown" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_spatial_niche_map_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_spatial_niche_map_panel",
        layout_sidecar={
            "template_id": "spatial_niche_map_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("spatial_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.26, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.10, x1=0.23, y1=0.13),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_spatial", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "niche_label": "Immune niche"},
                    {"x": 0.23, "y": 0.34, "niche_label": "Stromal niche"},
                ],
                "niche_labels": ["Immune niche", "Stromal niche"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
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
                "matrix_cells": [
                    {"x": "Immune niche", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Stromal niche", "y": "CXCL13 program", "value": -0.16},
                    {"x": "Immune niche", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Stromal niche", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []

def test_run_display_layout_qc_fails_when_spatial_niche_map_composition_is_incomplete() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_spatial_niche_map_panel",
        layout_sidecar={
            "template_id": "spatial_niche_map_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("spatial_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.26, y1=0.91),
                make_box("spatial_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.10, x1=0.23, y1=0.13),
                make_box("spatial_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.30, x1=0.05, y1=0.74),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.58, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.43, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.28, x1=0.36, y1=0.76),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.86, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_spatial", "panel", x0=0.07, y0=0.18, x1=0.29, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.14, "y": 0.70, "niche_label": "Immune niche"},
                    {"x": 0.23, "y": 0.34, "niche_label": "Stromal niche"},
                ],
                "niche_labels": ["Immune niche", "Stromal niche"],
                "row_labels": ["CXCL13 program", "TGF-beta program"],
                "composition_groups": [
                    {
                        "group_label": "Tumor core",
                        "group_order": 1,
                        "niche_proportions": [
                            {"niche_label": "Immune niche", "proportion": 0.64},
                        ],
                    },
                ],
                "matrix_cells": [
                    {"x": "Immune niche", "y": "CXCL13 program", "value": 0.74},
                    {"x": "Stromal niche", "y": "CXCL13 program", "value": -0.16},
                    {"x": "Immune niche", "y": "TGF-beta program", "value": -0.19},
                    {"x": "Stromal niche", "y": "TGF-beta program", "value": 0.69},
                ],
                "score_method": "AUCell",
            },
        },
    )

    assert result["status"] == "fail"
    assert any(issue["rule_id"] == "composition_group_niche_set_mismatch" for issue in result["issues"])

def test_run_display_layout_qc_passes_for_trajectory_progression_panel() -> None:
    module = importlib.import_module("med_autoscience.display_layout_qc")

    result = module.run_display_layout_qc(
        qc_profile="publication_trajectory_progression_panel",
        layout_sidecar={
            "template_id": "trajectory_progression_panel",
            "device": make_device(),
            "layout_boxes": [
                make_box("trajectory_panel_title", "panel_title", x0=0.08, y0=0.88, x1=0.28, y1=0.91),
                make_box("trajectory_x_axis_title", "subplot_x_axis_title", x0=0.11, y0=0.10, x1=0.24, y1=0.13),
                make_box("trajectory_y_axis_title", "subplot_y_axis_title", x0=0.02, y0=0.28, x1=0.05, y1=0.76),
                make_box("composition_panel_title", "panel_title", x0=0.38, y0=0.88, x1=0.60, y1=0.91),
                make_box("composition_x_axis_title", "subplot_x_axis_title", x0=0.42, y0=0.10, x1=0.56, y1=0.13),
                make_box("composition_y_axis_title", "subplot_y_axis_title", x0=0.33, y0=0.26, x1=0.36, y1=0.78),
                make_box("heatmap_panel_title", "panel_title", x0=0.68, y0=0.88, x1=0.85, y1=0.91),
                make_box("heatmap_x_axis_title", "subplot_x_axis_title", x0=0.71, y0=0.10, x1=0.83, y1=0.13),
                make_box("heatmap_y_axis_title", "subplot_y_axis_title", x0=0.62, y0=0.28, x1=0.65, y1=0.76),
                make_box("panel_label_A", "panel_label", x0=0.08, y0=0.82, x1=0.10, y1=0.85),
                make_box("panel_label_B", "panel_label", x0=0.38, y0=0.82, x1=0.40, y1=0.85),
                make_box("panel_label_C", "panel_label", x0=0.68, y0=0.82, x1=0.70, y1=0.85),
            ],
            "panel_boxes": [
                make_box("panel_trajectory", "panel", x0=0.07, y0=0.18, x1=0.30, y1=0.86),
                make_box("panel_composition", "composition_panel", x0=0.37, y0=0.18, x1=0.60, y1=0.86),
                make_box("panel_heatmap", "heatmap_tile_region", x0=0.67, y0=0.18, x1=0.88, y1=0.86),
            ],
            "guide_boxes": [
                make_box("legend", "legend", x0=0.10, y0=0.02, x1=0.34, y1=0.08),
                make_box("colorbar", "colorbar", x0=0.90, y0=0.22, x1=0.94, y1=0.82),
            ],
            "metrics": {
                "points": [
                    {"x": 0.11, "y": 0.72, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
                    {"x": 0.17, "y": 0.60, "branch_label": "Branch A", "state_label": "Intermediate", "pseudotime": 0.36},
                    {"x": 0.25, "y": 0.34, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.74},
                    {"x": 0.28, "y": 0.76, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
                    {"x": 0.24, "y": 0.52, "branch_label": "Branch B", "state_label": "Intermediate", "pseudotime": 0.48},
                    {"x": 0.20, "y": 0.26, "branch_label": "Branch B", "state_label": "Terminal", "pseudotime": 0.86},
                ],
                "branch_labels": ["Branch A", "Branch B"],
                "bin_labels": ["Early", "Mid", "Late"],
                "row_labels": ["Interferon module", "EMT module"],
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
                "matrix_cells": [
                    {"x": "Early", "y": "Interferon module", "value": 0.72},
                    {"x": "Mid", "y": "Interferon module", "value": 0.28},
                    {"x": "Late", "y": "Interferon module", "value": -0.18},
                    {"x": "Early", "y": "EMT module", "value": -0.31},
                    {"x": "Mid", "y": "EMT module", "value": 0.22},
                    {"x": "Late", "y": "EMT module", "value": 0.68},
                ],
                "score_method": "GSVA",
            },
        },
    )

    assert result["status"] == "pass", result
    assert result["issues"] == []
