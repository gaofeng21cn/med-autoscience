from __future__ import annotations

from . import shared_base as _shared_base
from . import helper_04 as _helper_prev

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_helper_prev)

def _make_atlas_spatial_trajectory_context_support_panel_display(display_id: str = "Figure33") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "atlas_spatial_trajectory_context_support_panel",
        "title": "Atlas, spatial, trajectory, composition, kinetics, and context support composite",
        "caption": (
            "Atlas occupancy, tissue topography, trajectory progression, region composition, kinetics, and "
            "state-by-context support remain bound inside one audited multi-view contract."
        ),
        "atlas_panel_title": "Atlas occupancy",
        "atlas_x_label": "UMAP 1",
        "atlas_y_label": "UMAP 2",
        "atlas_points": [
            {"x": -2.1, "y": 1.0, "state_label": "Stem-like"},
            {"x": -1.7, "y": 0.8, "state_label": "Stem-like"},
            {"x": -0.2, "y": -0.1, "state_label": "Cycling"},
            {"x": 1.1, "y": -0.6, "state_label": "Effector"},
        ],
        "spatial_panel_title": "Spatial state topography",
        "spatial_x_label": "Tissue x coordinate",
        "spatial_y_label": "Tissue y coordinate",
        "spatial_points": [
            {"x": 0.12, "y": 0.82, "state_label": "Stem-like", "region_label": "Tumor core"},
            {"x": 0.18, "y": 0.76, "state_label": "Stem-like", "region_label": "Tumor core"},
            {"x": 0.54, "y": 0.48, "state_label": "Cycling", "region_label": "Invasive margin"},
            {"x": 0.82, "y": 0.20, "state_label": "Effector", "region_label": "Invasive margin"},
        ],
        "trajectory_panel_title": "Trajectory progression",
        "trajectory_x_label": "Trajectory 1",
        "trajectory_y_label": "Trajectory 2",
        "trajectory_points": [
            {"x": -1.7, "y": 0.9, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
            {"x": -0.9, "y": 0.4, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.34},
            {"x": -0.2, "y": -0.2, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
            {"x": 1.5, "y": 0.8, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
            {"x": 1.1, "y": 0.2, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.52},
            {"x": 0.7, "y": -0.6, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
        ],
        "composition_panel_title": "Region-wise state composition",
        "composition_x_label": "State composition",
        "composition_y_label": "Region",
        "composition_groups": [
            {
                "group_label": "Tumor core",
                "group_order": 1,
                "state_proportions": [
                    {"state_label": "Stem-like", "proportion": 0.48},
                    {"state_label": "Cycling", "proportion": 0.32},
                    {"state_label": "Effector", "proportion": 0.20},
                ],
            },
            {
                "group_label": "Invasive margin",
                "group_order": 2,
                "state_proportions": [
                    {"state_label": "Stem-like", "proportion": 0.18},
                    {"state_label": "Cycling", "proportion": 0.34},
                    {"state_label": "Effector", "proportion": 0.48},
                ],
            },
        ],
        "heatmap_panel_title": "Program kinetics",
        "heatmap_x_label": "Pseudotime bin",
        "heatmap_y_label": "Marker / module",
        "score_method": "GSVA",
        "state_order": [
            {"label": "Stem-like"},
            {"label": "Cycling"},
            {"label": "Effector"},
        ],
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
                    {"branch_label": "Branch A", "proportion": 0.58},
                    {"branch_label": "Branch B", "proportion": 0.42},
                ],
            },
            {
                "bin_label": "Mid",
                "bin_order": 2,
                "pseudotime_start": 0.33,
                "pseudotime_end": 0.67,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.46},
                    {"branch_label": "Branch B", "proportion": 0.54},
                ],
            },
            {
                "bin_label": "Late",
                "bin_order": 3,
                "pseudotime_start": 0.67,
                "pseudotime_end": 1.0,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.39},
                    {"branch_label": "Branch B", "proportion": 0.61},
                ],
            },
        ],
        "row_order": [
            {"label": "IFN response"},
            {"label": "EMT module"},
        ],
        "column_order": [
            {"label": "Early"},
            {"label": "Mid"},
            {"label": "Late"},
        ],
        "cells": [
            {"x": "Early", "y": "IFN response", "value": 0.74},
            {"x": "Mid", "y": "IFN response", "value": 0.26},
            {"x": "Late", "y": "IFN response", "value": -0.14},
            {"x": "Early", "y": "EMT module", "value": -0.28},
            {"x": "Mid", "y": "EMT module", "value": 0.18},
            {"x": "Late", "y": "EMT module", "value": 0.72},
        ],
        "support_panel_title": "State-by-context support",
        "support_x_label": "Context",
        "support_y_label": "Cell state",
        "support_scale_label": "Coverage fraction",
        "context_order": [
            {"label": "Atlas density", "context_kind": "atlas_density"},
            {"label": "Spatial coverage", "context_kind": "spatial_coverage"},
            {"label": "Trajectory coverage", "context_kind": "trajectory_coverage"},
        ],
        "support_cells": [
            {"x": "Atlas density", "y": "Stem-like", "value": 0.84},
            {"x": "Spatial coverage", "y": "Stem-like", "value": 0.73},
            {"x": "Trajectory coverage", "y": "Stem-like", "value": 0.58},
            {"x": "Atlas density", "y": "Cycling", "value": 0.49},
            {"x": "Spatial coverage", "y": "Cycling", "value": 0.61},
            {"x": "Trajectory coverage", "y": "Cycling", "value": 0.66},
            {"x": "Atlas density", "y": "Effector", "value": 0.31},
            {"x": "Spatial coverage", "y": "Effector", "value": 0.54},
            {"x": "Trajectory coverage", "y": "Effector", "value": 0.81},
        ],
    }

def _make_atlas_spatial_trajectory_multimanifold_context_support_panel_display(
    display_id: str = "Figure51",
) -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "atlas_spatial_trajectory_multimanifold_context_support_panel",
        "title": "Atlas multimanifold, spatial, trajectory, composition, kinetics, and context support composite",
        "caption": (
            "Dual-manifold atlas geometry, tissue topography, trajectory progression, region composition, kinetics, "
            "and state-by-context support remain bound inside one audited multiview contract."
        ),
        "atlas_manifold_panels": [
            {
                "panel_id": "atlas_umap",
                "panel_label": "A",
                "panel_title": "Atlas occupancy (UMAP)",
                "manifold_method": "umap",
                "x_label": "UMAP 1",
                "y_label": "UMAP 2",
                "points": [
                    {"x": -2.1, "y": 1.0, "state_label": "Stem-like"},
                    {"x": -1.7, "y": 0.8, "state_label": "Stem-like"},
                    {"x": -0.2, "y": -0.1, "state_label": "Cycling"},
                    {"x": 1.1, "y": -0.6, "state_label": "Effector"},
                ],
            },
            {
                "panel_id": "atlas_phate",
                "panel_label": "B",
                "panel_title": "Atlas geometry (PHATE)",
                "manifold_method": "phate",
                "x_label": "PHATE 1",
                "y_label": "PHATE 2",
                "points": [
                    {"x": -1.8, "y": 0.7, "state_label": "Stem-like"},
                    {"x": -1.2, "y": 0.2, "state_label": "Stem-like"},
                    {"x": 0.0, "y": -0.2, "state_label": "Cycling"},
                    {"x": 1.4, "y": -0.8, "state_label": "Effector"},
                ],
            },
        ],
        "spatial_panel_title": "Spatial state topography",
        "spatial_x_label": "Tissue x coordinate",
        "spatial_y_label": "Tissue y coordinate",
        "spatial_points": [
            {"x": 0.12, "y": 0.82, "state_label": "Stem-like", "region_label": "Tumor core"},
            {"x": 0.18, "y": 0.76, "state_label": "Stem-like", "region_label": "Tumor core"},
            {"x": 0.54, "y": 0.48, "state_label": "Cycling", "region_label": "Invasive margin"},
            {"x": 0.82, "y": 0.20, "state_label": "Effector", "region_label": "Invasive margin"},
        ],
        "trajectory_panel_title": "Trajectory progression",
        "trajectory_x_label": "Trajectory 1",
        "trajectory_y_label": "Trajectory 2",
        "trajectory_points": [
            {"x": -1.7, "y": 0.9, "branch_label": "Branch A", "state_label": "Stem-like", "pseudotime": 0.08},
            {"x": -0.9, "y": 0.4, "branch_label": "Branch A", "state_label": "Cycling", "pseudotime": 0.34},
            {"x": -0.2, "y": -0.2, "branch_label": "Branch A", "state_label": "Effector", "pseudotime": 0.76},
            {"x": 1.5, "y": 0.8, "branch_label": "Branch B", "state_label": "Stem-like", "pseudotime": 0.12},
            {"x": 1.1, "y": 0.2, "branch_label": "Branch B", "state_label": "Cycling", "pseudotime": 0.52},
            {"x": 0.7, "y": -0.6, "branch_label": "Branch B", "state_label": "Effector", "pseudotime": 0.88},
        ],
        "composition_panel_title": "Region-wise state composition",
        "composition_x_label": "State composition",
        "composition_y_label": "Region",
        "composition_groups": [
            {
                "group_label": "Tumor core",
                "group_order": 1,
                "state_proportions": [
                    {"state_label": "Stem-like", "proportion": 0.48},
                    {"state_label": "Cycling", "proportion": 0.32},
                    {"state_label": "Effector", "proportion": 0.20},
                ],
            },
            {
                "group_label": "Invasive margin",
                "group_order": 2,
                "state_proportions": [
                    {"state_label": "Stem-like", "proportion": 0.18},
                    {"state_label": "Cycling", "proportion": 0.34},
                    {"state_label": "Effector", "proportion": 0.48},
                ],
            },
        ],
        "heatmap_panel_title": "Program kinetics",
        "heatmap_x_label": "Pseudotime bin",
        "heatmap_y_label": "Marker / module",
        "score_method": "GSVA",
        "state_order": [
            {"label": "Stem-like"},
            {"label": "Cycling"},
            {"label": "Effector"},
        ],
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
                    {"branch_label": "Branch A", "proportion": 0.58},
                    {"branch_label": "Branch B", "proportion": 0.42},
                ],
            },
            {
                "bin_label": "Mid",
                "bin_order": 2,
                "pseudotime_start": 0.33,
                "pseudotime_end": 0.67,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.46},
                    {"branch_label": "Branch B", "proportion": 0.54},
                ],
            },
            {
                "bin_label": "Late",
                "bin_order": 3,
                "pseudotime_start": 0.67,
                "pseudotime_end": 1.0,
                "branch_weights": [
                    {"branch_label": "Branch A", "proportion": 0.39},
                    {"branch_label": "Branch B", "proportion": 0.61},
                ],
            },
        ],
        "row_order": [
            {"label": "IFN response"},
            {"label": "EMT module"},
        ],
        "column_order": [
            {"label": "Early"},
            {"label": "Mid"},
            {"label": "Late"},
        ],
        "cells": [
            {"x": "Early", "y": "IFN response", "value": 0.74},
            {"x": "Mid", "y": "IFN response", "value": 0.26},
            {"x": "Late", "y": "IFN response", "value": -0.14},
            {"x": "Early", "y": "EMT module", "value": -0.28},
            {"x": "Mid", "y": "EMT module", "value": 0.18},
            {"x": "Late", "y": "EMT module", "value": 0.72},
        ],
        "support_panel_title": "State-by-context support",
        "support_x_label": "Context",
        "support_y_label": "Cell state",
        "support_scale_label": "Coverage fraction",
        "context_order": [
            {"label": "Atlas density", "context_kind": "atlas_density"},
            {"label": "Spatial coverage", "context_kind": "spatial_coverage"},
            {"label": "Trajectory coverage", "context_kind": "trajectory_coverage"},
        ],
        "support_cells": [
            {"x": "Atlas density", "y": "Stem-like", "value": 0.84},
            {"x": "Spatial coverage", "y": "Stem-like", "value": 0.73},
            {"x": "Trajectory coverage", "y": "Stem-like", "value": 0.58},
            {"x": "Atlas density", "y": "Cycling", "value": 0.49},
            {"x": "Spatial coverage", "y": "Cycling", "value": 0.61},
            {"x": "Trajectory coverage", "y": "Cycling", "value": 0.66},
            {"x": "Atlas density", "y": "Effector", "value": 0.31},
            {"x": "Spatial coverage", "y": "Effector", "value": 0.54},
            {"x": "Trajectory coverage", "y": "Effector", "value": 0.81},
        ],
    }

def _make_pathway_enrichment_dotplot_panel_display(display_id: str = "Figure34") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "pathway_enrichment_dotplot_panel",
        "title": "Pathway enrichment comparison across transcriptome and proteome",
        "caption": (
            "Shared pathway ordering, signed enrichment direction, and hit-count magnitude remain bound "
            "inside one audited enrichment dotplot contract."
        ),
        "x_label": "Normalized enrichment score",
        "y_label": "Pathway",
        "effect_scale_label": "Directionality score",
        "size_scale_label": "Gene count",
        "panel_order": [
            {"panel_id": "transcriptome", "panel_title": "Transcriptome"},
            {"panel_id": "proteome", "panel_title": "Proteome"},
        ],
        "pathway_order": [
            {"label": "IFN response"},
            {"label": "EMT signaling"},
            {"label": "Cell cycle"},
        ],
        "points": [
            {"panel_id": "transcriptome", "pathway_label": "IFN response", "x_value": 1.84, "effect_value": 0.91, "size_value": 34.0},
            {"panel_id": "transcriptome", "pathway_label": "EMT signaling", "x_value": 1.18, "effect_value": 0.42, "size_value": 22.0},
            {"panel_id": "transcriptome", "pathway_label": "Cell cycle", "x_value": 2.06, "effect_value": 0.76, "size_value": 29.0},
            {"panel_id": "proteome", "pathway_label": "IFN response", "x_value": 1.41, "effect_value": 0.64, "size_value": 26.0},
            {"panel_id": "proteome", "pathway_label": "EMT signaling", "x_value": 1.73, "effect_value": 0.88, "size_value": 31.0},
            {"panel_id": "proteome", "pathway_label": "Cell cycle", "x_value": 1.22, "effect_value": 0.37, "size_value": 19.0},
        ],
    }

def _make_celltype_marker_dotplot_panel_display(display_id: str = "Figure53") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "celltype_marker_dotplot_panel",
        "title": "Cell-type marker expression atlas across discovery and validation cohorts",
        "caption": (
            "Shared cell-type ordering, marker ordering, mean-expression chromatic scale, and detection-rate "
            "dot sizing remain bound inside one audited marker dotplot contract."
        ),
        "x_label": "Marker gene",
        "y_label": "Cell type",
        "effect_scale_label": "Mean expression",
        "size_scale_label": "Detection rate (%)",
        "panel_order": [
            {"panel_id": "discovery", "panel_title": "Discovery atlas"},
            {"panel_id": "validation", "panel_title": "Validation atlas"},
        ],
        "celltype_order": [
            {"label": "Basal"},
            {"label": "Immune"},
            {"label": "Stromal"},
        ],
        "marker_order": [
            {"label": "KRT14"},
            {"label": "CXCL13"},
            {"label": "COL1A1"},
        ],
        "points": [
            {"panel_id": "discovery", "celltype_label": "Basal", "marker_label": "KRT14", "effect_value": 1.42, "size_value": 84.0},
            {"panel_id": "discovery", "celltype_label": "Basal", "marker_label": "CXCL13", "effect_value": 0.18, "size_value": 12.0},
            {"panel_id": "discovery", "celltype_label": "Basal", "marker_label": "COL1A1", "effect_value": 0.10, "size_value": 8.0},
            {"panel_id": "discovery", "celltype_label": "Immune", "marker_label": "KRT14", "effect_value": 0.12, "size_value": 10.0},
            {"panel_id": "discovery", "celltype_label": "Immune", "marker_label": "CXCL13", "effect_value": 1.21, "size_value": 73.0},
            {"panel_id": "discovery", "celltype_label": "Immune", "marker_label": "COL1A1", "effect_value": 0.22, "size_value": 14.0},
            {"panel_id": "discovery", "celltype_label": "Stromal", "marker_label": "KRT14", "effect_value": 0.10, "size_value": 9.0},
            {"panel_id": "discovery", "celltype_label": "Stromal", "marker_label": "CXCL13", "effect_value": 0.24, "size_value": 18.0},
            {"panel_id": "discovery", "celltype_label": "Stromal", "marker_label": "COL1A1", "effect_value": 1.36, "size_value": 88.0},
            {"panel_id": "validation", "celltype_label": "Basal", "marker_label": "KRT14", "effect_value": 1.31, "size_value": 80.0},
            {"panel_id": "validation", "celltype_label": "Basal", "marker_label": "CXCL13", "effect_value": 0.21, "size_value": 15.0},
            {"panel_id": "validation", "celltype_label": "Basal", "marker_label": "COL1A1", "effect_value": 0.11, "size_value": 7.0},
            {"panel_id": "validation", "celltype_label": "Immune", "marker_label": "KRT14", "effect_value": 0.14, "size_value": 11.0},
            {"panel_id": "validation", "celltype_label": "Immune", "marker_label": "CXCL13", "effect_value": 1.16, "size_value": 70.0},
            {"panel_id": "validation", "celltype_label": "Immune", "marker_label": "COL1A1", "effect_value": 0.25, "size_value": 16.0},
            {"panel_id": "validation", "celltype_label": "Stromal", "marker_label": "KRT14", "effect_value": 0.11, "size_value": 10.0},
            {"panel_id": "validation", "celltype_label": "Stromal", "marker_label": "CXCL13", "effect_value": 0.27, "size_value": 19.0},
            {"panel_id": "validation", "celltype_label": "Stromal", "marker_label": "COL1A1", "effect_value": 1.29, "size_value": 86.0},
        ],
    }

def _make_omics_volcano_panel_display(display_id: str = "Figure35") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("omics_volcano_panel"),
        "title": "Differential omics volcano comparison across transcriptome and proteome",
        "caption": (
            "Fold-change thresholds, significance thresholds, and highlighted drivers remain bound "
            "inside one audited volcano-panel contract."
        ),
        "x_label": "log2 fold change",
        "y_label": "-log10 adjusted P",
        "legend_title": "Regulation",
        "effect_threshold": 1.0,
        "significance_threshold": 2.0,
        "panel_order": [
            {"panel_id": "transcriptome", "panel_title": "Transcriptome"},
            {"panel_id": "proteome", "panel_title": "Proteome"},
        ],
        "points": [
            {
                "panel_id": "transcriptome",
                "feature_label": "CXCL9",
                "effect_value": 1.72,
                "significance_value": 4.41,
                "regulation_class": "upregulated",
                "label_text": "CXCL9",
            },
            {
                "panel_id": "transcriptome",
                "feature_label": "MKI67",
                "effect_value": 1.19,
                "significance_value": 3.28,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "transcriptome",
                "feature_label": "COL1A1",
                "effect_value": -1.34,
                "significance_value": 3.92,
                "regulation_class": "downregulated",
                "label_text": "COL1A1",
            },
            {
                "panel_id": "transcriptome",
                "feature_label": "GAPDH",
                "effect_value": 0.14,
                "significance_value": 0.52,
                "regulation_class": "background",
            },
            {
                "panel_id": "proteome",
                "feature_label": "CXCL9",
                "effect_value": 1.26,
                "significance_value": 3.36,
                "regulation_class": "upregulated",
                "label_text": "CXCL9",
            },
            {
                "panel_id": "proteome",
                "feature_label": "STAT1",
                "effect_value": 1.08,
                "significance_value": 2.91,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "proteome",
                "feature_label": "COL1A1",
                "effect_value": -1.11,
                "significance_value": 3.07,
                "regulation_class": "downregulated",
                "label_text": "COL1A1",
            },
            {
                "panel_id": "proteome",
                "feature_label": "ACTB",
                "effect_value": 0.11,
                "significance_value": 0.61,
                "regulation_class": "background",
            },
        ],
    }

def _make_oncoplot_mutation_landscape_panel_display(display_id: str = "Figure36") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("oncoplot_mutation_landscape_panel"),
        "title": "Mutation landscape oncoplot across discovery and validation cohorts",
        "caption": (
            "Declared gene order, sample order, annotation-track coverage, top burden, and right-side "
            "altered-frequency governance remain bound inside one audited oncoplot contract."
        ),
        "y_label": "Altered gene",
        "burden_axis_label": "Altered genes",
        "frequency_axis_label": "Altered samples (%)",
        "mutation_legend_title": "Alteration",
        "gene_order": [
            {"label": "TP53"},
            {"label": "KRAS"},
            {"label": "EGFR"},
        ],
        "sample_order": [
            {"sample_id": "D1"},
            {"sample_id": "D2"},
            {"sample_id": "V1"},
            {"sample_id": "V2"},
        ],
        "annotation_tracks": [
            {
                "track_id": "cohort",
                "track_label": "Cohort",
                "values": [
                    {"sample_id": "D1", "category_label": "Discovery"},
                    {"sample_id": "D2", "category_label": "Discovery"},
                    {"sample_id": "V1", "category_label": "Validation"},
                    {"sample_id": "V2", "category_label": "Validation"},
                ],
            },
            {
                "track_id": "response",
                "track_label": "Response",
                "values": [
                    {"sample_id": "D1", "category_label": "Responder"},
                    {"sample_id": "D2", "category_label": "Non-responder"},
                    {"sample_id": "V1", "category_label": "Responder"},
                    {"sample_id": "V2", "category_label": "Non-responder"},
                ],
            },
        ],
        "mutation_records": [
            {"sample_id": "D1", "gene_label": "TP53", "alteration_class": "missense"},
            {"sample_id": "D2", "gene_label": "KRAS", "alteration_class": "amplification"},
            {"sample_id": "V1", "gene_label": "TP53", "alteration_class": "truncating"},
            {"sample_id": "V2", "gene_label": "EGFR", "alteration_class": "fusion"},
        ],
    }

def _make_cnv_recurrence_summary_panel_display(display_id: str = "Figure37") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("cnv_recurrence_summary_panel"),
        "title": "Recurrent copy-number landscape across discovery and validation cohorts",
        "caption": (
            "Declared region order, sample order, annotation-track coverage, top CNV burden, and right-side "
            "gain/loss frequency governance remain bound inside one audited CNV-summary contract."
        ),
        "y_label": "Genomic region",
        "burden_axis_label": "Altered regions",
        "frequency_axis_label": "Gain/Loss samples (%)",
        "cnv_legend_title": "CNV state",
        "region_order": [
            {"label": "TP53"},
            {"label": "MYC"},
            {"label": "EGFR"},
            {"label": "CDKN2A"},
        ],
        "sample_order": [
            {"sample_id": "D1"},
            {"sample_id": "D2"},
            {"sample_id": "V1"},
            {"sample_id": "V2"},
        ],
        "annotation_tracks": [
            {
                "track_id": "cohort",
                "track_label": "Cohort",
                "values": [
                    {"sample_id": "D1", "category_label": "Discovery"},
                    {"sample_id": "D2", "category_label": "Discovery"},
                    {"sample_id": "V1", "category_label": "Validation"},
                    {"sample_id": "V2", "category_label": "Validation"},
                ],
            },
            {
                "track_id": "response",
                "track_label": "Response",
                "values": [
                    {"sample_id": "D1", "category_label": "Responder"},
                    {"sample_id": "D2", "category_label": "Non-responder"},
                    {"sample_id": "V1", "category_label": "Responder"},
                    {"sample_id": "V2", "category_label": "Non-responder"},
                ],
            },
        ],
        "cnv_records": [
            {"sample_id": "D1", "region_label": "TP53", "cnv_state": "amplification"},
            {"sample_id": "D2", "region_label": "TP53", "cnv_state": "loss"},
            {"sample_id": "D1", "region_label": "MYC", "cnv_state": "gain"},
            {"sample_id": "V1", "region_label": "MYC", "cnv_state": "loss"},
            {"sample_id": "D2", "region_label": "EGFR", "cnv_state": "gain"},
            {"sample_id": "V2", "region_label": "EGFR", "cnv_state": "loss"},
            {"sample_id": "V1", "region_label": "CDKN2A", "cnv_state": "deep_loss"},
            {"sample_id": "V2", "region_label": "CDKN2A", "cnv_state": "gain"},
        ],
    }

def _make_genomic_alteration_landscape_panel_display(display_id: str = "Figure38") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("genomic_alteration_landscape_panel"),
        "title": "Gene-level genomic alteration landscape across discovery and validation cohorts",
        "caption": (
            "Declared gene order, shared sample order, annotation-track coverage, top burden, and right-side "
            "gene-level alteration-frequency governance remain bound inside one audited mutation-plus-CNV landscape contract."
        ),
        "y_label": "Altered gene",
        "burden_axis_label": "Altered genes",
        "frequency_axis_label": "Altered samples (%)",
        "alteration_legend_title": "Genomic alteration",
        "gene_order": [
            {"label": "TP53"},
            {"label": "KRAS"},
            {"label": "EGFR"},
            {"label": "PIK3CA"},
        ],
        "sample_order": [
            {"sample_id": "D1"},
            {"sample_id": "D2"},
            {"sample_id": "V1"},
            {"sample_id": "V2"},
        ],
        "annotation_tracks": [
            {
                "track_id": "cohort",
                "track_label": "Cohort",
                "values": [
                    {"sample_id": "D1", "category_label": "Discovery"},
                    {"sample_id": "D2", "category_label": "Discovery"},
                    {"sample_id": "V1", "category_label": "Validation"},
                    {"sample_id": "V2", "category_label": "Validation"},
                ],
            },
            {
                "track_id": "response",
                "track_label": "Response",
                "values": [
                    {"sample_id": "D1", "category_label": "Responder"},
                    {"sample_id": "D2", "category_label": "Non-responder"},
                    {"sample_id": "V1", "category_label": "Responder"},
                    {"sample_id": "V2", "category_label": "Non-responder"},
                ],
            },
        ],
        "alteration_records": [
            {"sample_id": "D1", "gene_label": "TP53", "mutation_class": "missense", "cnv_state": "loss"},
            {"sample_id": "D2", "gene_label": "KRAS", "cnv_state": "amplification"},
            {"sample_id": "V1", "gene_label": "TP53", "mutation_class": "truncating"},
            {"sample_id": "V1", "gene_label": "PIK3CA", "cnv_state": "gain"},
            {"sample_id": "V2", "gene_label": "EGFR", "mutation_class": "fusion", "cnv_state": "amplification"},
        ],
    }

def _make_genomic_alteration_consequence_panel_display(display_id: str = "Figure39") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": full_id("genomic_alteration_consequence_panel"),
        "title": "Driver-centric genomic alteration landscape with downstream consequence panels",
        "caption": (
            "Shared gene/sample governance, driver-gene linkage, and bounded consequence evidence remain "
            "inside one audited genomic-composite contract."
        ),
        "y_label": "Altered gene",
        "burden_axis_label": "Altered genes",
        "frequency_axis_label": "Altered samples (%)",
        "alteration_legend_title": "Genomic alteration",
        "gene_order": [
            {"label": "TP53"},
            {"label": "KRAS"},
            {"label": "EGFR"},
            {"label": "PIK3CA"},
        ],
        "sample_order": [
            {"sample_id": "D1"},
            {"sample_id": "D2"},
            {"sample_id": "V1"},
            {"sample_id": "V2"},
        ],
        "annotation_tracks": [
            {
                "track_id": "cohort",
                "track_label": "Cohort",
                "values": [
                    {"sample_id": "D1", "category_label": "Discovery"},
                    {"sample_id": "D2", "category_label": "Discovery"},
                    {"sample_id": "V1", "category_label": "Validation"},
                    {"sample_id": "V2", "category_label": "Validation"},
                ],
            },
            {
                "track_id": "response",
                "track_label": "Response",
                "values": [
                    {"sample_id": "D1", "category_label": "Responder"},
                    {"sample_id": "D2", "category_label": "Non-responder"},
                    {"sample_id": "V1", "category_label": "Responder"},
                    {"sample_id": "V2", "category_label": "Non-responder"},
                ],
            },
        ],
        "alteration_records": [
            {"sample_id": "D1", "gene_label": "TP53", "mutation_class": "missense", "cnv_state": "loss"},
            {"sample_id": "D2", "gene_label": "KRAS", "cnv_state": "amplification"},
            {"sample_id": "V1", "gene_label": "TP53", "mutation_class": "truncating"},
            {"sample_id": "V1", "gene_label": "PIK3CA", "cnv_state": "gain"},
            {"sample_id": "V2", "gene_label": "EGFR", "mutation_class": "fusion", "cnv_state": "amplification"},
        ],
        "consequence_x_label": "Effect size",
        "consequence_y_label": "-log10 adjusted P",
        "consequence_legend_title": "Consequence class",
        "effect_threshold": 1.0,
        "significance_threshold": 2.0,
        "driver_gene_order": [
            {"label": "TP53"},
            {"label": "EGFR"},
        ],
        "consequence_panel_order": [
            {"panel_id": "transcriptome", "panel_title": "Transcriptome consequence"},
            {"panel_id": "proteome", "panel_title": "Proteome consequence"},
        ],
        "consequence_points": [
            {
                "panel_id": "transcriptome",
                "gene_label": "TP53",
                "effect_value": 1.62,
                "significance_value": 4.15,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "transcriptome",
                "gene_label": "EGFR",
                "effect_value": -1.31,
                "significance_value": 3.42,
                "regulation_class": "downregulated",
            },
            {
                "panel_id": "proteome",
                "gene_label": "TP53",
                "effect_value": 1.18,
                "significance_value": 3.28,
                "regulation_class": "upregulated",
            },
            {
                "panel_id": "proteome",
                "gene_label": "EGFR",
                "effect_value": -1.07,
                "significance_value": 2.84,
                "regulation_class": "downregulated",
            },
        ],
    }
