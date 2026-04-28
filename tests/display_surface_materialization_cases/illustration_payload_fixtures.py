from __future__ import annotations

from . import shared_base as _shared_base
from . import layout_sidecar_fixtures as _layout_sidecar_fixtures

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_layout_sidecar_fixtures)

def _make_workflow_fact_sheet_panel_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "shell_id": "workflow_fact_sheet_panel",
        "display_id": "Figure2",
        "title": "Study workflow fact sheet",
        "caption": "Structured study-design and workflow summary for the audited manuscript-facing surface.",
        "sections": [
            {
                "section_id": "cohort",
                "panel_label": "A",
                "title": "Cohort and window",
                "layout_role": "top_left",
                "facts": [{"fact_id": "cohort_n", "label": "Cohort", "value": "n = 409", "detail": "Primary analysis cohort"}],
            },
            {
                "section_id": "endpoint",
                "panel_label": "B",
                "title": "Endpoint and target",
                "layout_role": "top_right",
                "facts": [{"fact_id": "target", "label": "Target", "value": "Early residual / non-GTR", "detail": "Formal audited endpoint"}],
            },
            {
                "section_id": "workflow",
                "panel_label": "C",
                "title": "Model workflow",
                "layout_role": "bottom_left",
                "facts": [{"fact_id": "family", "label": "Model family", "value": "Gradient boosting", "detail": "Structured preoperative model"}],
            },
            {
                "section_id": "validation",
                "panel_label": "D",
                "title": "Validation and boundary",
                "layout_role": "bottom_right",
                "facts": [{"fact_id": "validation_scheme", "label": "Validation", "value": "Repeated nested CV", "detail": "5 outer folds x 20 repeats"}],
            },
        ],
    }

def _make_design_evidence_composite_shell_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "shell_id": "design_evidence_composite_shell",
        "display_id": "Figure3",
        "title": "Study design evidence composite",
        "caption": "Bounded study-design overview with workflow ribbon and three manuscript-facing summary panels.",
        "workflow_stages": [
            {"stage_id": "cohort", "title": "Cohort assembly", "detail": "Primary screened and analyzed cohort"},
            {"stage_id": "modeling", "title": "Model development", "detail": "Feature engineering and internal validation"},
            {"stage_id": "validation", "title": "External validation", "detail": "Held-out center-level confirmation"},
        ],
        "summary_panels": [
            {
                "panel_id": "cohort_summary",
                "panel_label": "A",
                "title": "Cohort and splits",
                "layout_role": "left",
                "cards": [{"card_id": "train_n", "label": "Train", "value": "n = 812", "detail": "Derivation centers"}],
            },
            {
                "panel_id": "endpoint_summary",
                "panel_label": "B",
                "title": "Endpoint and design",
                "layout_role": "center",
                "cards": [{"card_id": "endpoint", "label": "Endpoint", "value": "Two-year relapse", "detail": "Audited manuscript endpoint"}],
            },
            {
                "panel_id": "evidence_summary",
                "panel_label": "C",
                "title": "Evidence and boundary",
                "layout_role": "right",
                "cards": [{"card_id": "auc", "label": "Primary AUC", "value": "0.83", "detail": "External validation cohort"}],
            },
        ],
    }

def _make_baseline_missingness_qc_panel_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "shell_id": "baseline_missingness_qc_panel",
        "display_id": "Figure4",
        "title": "Baseline balance, missingness, and QC overview",
        "caption": "Bounded cohort-quality overview combining baseline balance, missingness, and QC summary evidence.",
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
        "missingness_rows": [
            {"label": "Age"},
            {"label": "HbA1c"},
            {"label": "BMI"},
        ],
        "missingness_columns": [
            {"label": "Train"},
            {"label": "Validation"},
            {"label": "External"},
        ],
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
    }

def _make_center_coverage_batch_transportability_panel_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "shell_id": "center_coverage_batch_transportability_panel",
        "display_id": "Figure47",
        "title": "Center coverage, batch shift, and transportability overview",
        "caption": "Bounded center-coverage overview combining support counts, batch-shift governance, and transportability boundary evidence.",
        "coverage_panel_title": "Center coverage",
        "coverage_x_label": "Patients retained",
        "center_rows": [
            {
                "center_id": "train_a",
                "center_label": "Train A",
                "cohort_role": "Derivation",
                "support_count": 412,
                "event_count": 63,
            },
            {
                "center_id": "validation_c",
                "center_label": "Validation C",
                "cohort_role": "Internal validation",
                "support_count": 236,
                "event_count": 34,
            },
            {
                "center_id": "external_b",
                "center_label": "External B",
                "cohort_role": "External",
                "support_count": 188,
                "event_count": 29,
            },
        ],
        "batch_panel_title": "Batch shift map",
        "batch_x_label": "Shift domain",
        "batch_y_label": "Center",
        "batch_threshold": 0.20,
        "batch_rows": [{"label": "Train A"}, {"label": "Validation C"}, {"label": "External B"}],
        "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}, {"label": "Feature drift"}],
        "batch_cells": [
            {"x": "Specimen drift", "y": "Train A", "value": 0.08},
            {"x": "Scanner drift", "y": "Train A", "value": 0.11},
            {"x": "Feature drift", "y": "Train A", "value": 0.09},
            {"x": "Specimen drift", "y": "Validation C", "value": 0.12},
            {"x": "Scanner drift", "y": "Validation C", "value": 0.16},
            {"x": "Feature drift", "y": "Validation C", "value": 0.13},
            {"x": "Specimen drift", "y": "External B", "value": 0.14},
            {"x": "Scanner drift", "y": "External B", "value": 0.18},
            {"x": "Feature drift", "y": "External B", "value": 0.17},
        ],
        "transportability_panel_title": "Transportability boundary",
        "transportability_cards": [
            {"card_id": "covered_centers", "label": "Centers covered", "value": "3", "detail": "Derivation, internal, and external cohorts retained"},
            {"card_id": "largest_shift", "label": "Largest shift", "value": "0.18", "detail": "Scanner drift at External B remains below the pre-specified threshold"},
            {"card_id": "boundary", "label": "Boundary", "value": "No unseen center claim", "detail": "Transportability stays bounded to audited centers only"},
        ],
    }

def _make_transportability_recalibration_governance_panel_payload() -> dict[str, object]:
    return {
        "schema_version": 1,
        "shell_id": "transportability_recalibration_governance_panel",
        "display_id": "Figure48",
        "title": "Transportability recalibration governance overview",
        "caption": "Bounded center-coverage, batch-shift, and recalibration-governance evidence.",
        "coverage_panel_title": "Center coverage",
        "coverage_x_label": "Patients retained",
        "center_rows": [
            {
                "center_id": "train_a",
                "center_label": "Train A",
                "cohort_role": "Derivation",
                "support_count": 412,
                "event_count": 63,
            },
            {
                "center_id": "validation_c",
                "center_label": "Validation C",
                "cohort_role": "Internal validation",
                "support_count": 236,
                "event_count": 34,
            },
            {
                "center_id": "external_b",
                "center_label": "External B",
                "cohort_role": "External",
                "support_count": 188,
                "event_count": 29,
            },
        ],
        "batch_panel_title": "Batch shift map",
        "batch_x_label": "Shift domain",
        "batch_y_label": "Center",
        "batch_threshold": 0.20,
        "batch_rows": [{"label": "Train A"}, {"label": "Validation C"}, {"label": "External B"}],
        "batch_columns": [{"label": "Specimen drift"}, {"label": "Scanner drift"}, {"label": "Feature drift"}],
        "batch_cells": [
            {"x": "Specimen drift", "y": "Train A", "value": 0.08},
            {"x": "Scanner drift", "y": "Train A", "value": 0.11},
            {"x": "Feature drift", "y": "Train A", "value": 0.09},
            {"x": "Specimen drift", "y": "Validation C", "value": 0.12},
            {"x": "Scanner drift", "y": "Validation C", "value": 0.16},
            {"x": "Feature drift", "y": "Validation C", "value": 0.13},
            {"x": "Specimen drift", "y": "External B", "value": 0.14},
            {"x": "Scanner drift", "y": "External B", "value": 0.18},
            {"x": "Feature drift", "y": "External B", "value": 0.17},
        ],
        "recalibration_panel_title": "Recalibration governance",
        "slope_acceptance_lower": 0.90,
        "slope_acceptance_upper": 1.10,
        "oe_ratio_acceptance_lower": 0.90,
        "oe_ratio_acceptance_upper": 1.10,
        "recalibration_rows": [
            {
                "center_id": "train_a",
                "slope": 1.00,
                "oe_ratio": 1.00,
                "action": "Reference fit",
                "detail": "Derivation reference retained for calibration context.",
            },
            {
                "center_id": "validation_c",
                "slope": 0.96,
                "oe_ratio": 1.04,
                "action": "Monitor only",
                "detail": "Internal validation remains within the pre-specified acceptance band.",
            },
            {
                "center_id": "external_b",
                "slope": 0.84,
                "oe_ratio": 1.18,
                "action": "Recalibrate before deployment",
                "detail": "External B exceeds the pre-specified acceptance band.",
            },
        ],
    }

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

def _make_atlas_spatial_bridge_display(display_id: str = "Figure30") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "atlas_spatial_bridge_panel",
        "title": "Atlas occupancy, spatial state topography, region composition, and marker-program bridge",
        "caption": (
            "Atlas embedding, spatial state localization, region-wise state composition, and marker-program "
            "definition remain bound inside one audited bridge contract."
        ),
        "atlas_panel_title": "Atlas occupancy",
        "atlas_x_label": "UMAP 1",
        "atlas_y_label": "UMAP 2",
        "atlas_points": [
            {"x": -2.0, "y": 1.1, "state_label": "T cells", "group_label": "Tumor"},
            {"x": -1.7, "y": 0.8, "state_label": "T cells", "group_label": "Adjacent"},
            {"x": 1.4, "y": -0.5, "state_label": "Myeloid", "group_label": "Tumor"},
            {"x": 1.9, "y": -0.8, "state_label": "Myeloid", "group_label": "Adjacent"},
        ],
        "spatial_panel_title": "Spatial state topography",
        "spatial_x_label": "Tissue x coordinate",
        "spatial_y_label": "Tissue y coordinate",
        "spatial_points": [
            {"x": 0.10, "y": 0.78, "state_label": "T cells", "region_label": "Tumor core"},
            {"x": 0.18, "y": 0.70, "state_label": "T cells", "region_label": "Tumor core"},
            {"x": 0.74, "y": 0.26, "state_label": "Myeloid", "region_label": "Invasive margin"},
            {"x": 0.82, "y": 0.18, "state_label": "Myeloid", "region_label": "Invasive margin"},
        ],
        "composition_panel_title": "Region-wise state composition",
        "composition_x_label": "Cell-state composition",
        "composition_y_label": "Region",
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
        "heatmap_panel_title": "Marker-program definition",
        "heatmap_x_label": "Cell state",
        "heatmap_y_label": "Marker / program",
        "score_method": "AUCell",
        "row_order": [
            {"label": "CXCL13 program"},
            {"label": "TGF-beta program"},
        ],
        "column_order": [
            {"label": "T cells"},
            {"label": "Myeloid"},
        ],
        "cells": [
            {"x": "T cells", "y": "CXCL13 program", "value": 0.78},
            {"x": "Myeloid", "y": "CXCL13 program", "value": -0.14},
            {"x": "T cells", "y": "TGF-beta program", "value": -0.21},
            {"x": "Myeloid", "y": "TGF-beta program", "value": 0.66},
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

def _make_atlas_spatial_trajectory_storyboard_display(display_id: str = "Figure31") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "atlas_spatial_trajectory_storyboard_panel",
        "title": "Atlas, spatial niche, trajectory progression, composition, and kinetics storyboard",
        "caption": (
            "Atlas occupancy, tissue topography, trajectory progression, region composition, and kinetics heatmap "
            "remain bound inside one audited storyboard contract."
        ),
        "atlas_panel_title": "Atlas occupancy",
        "atlas_x_label": "UMAP 1",
        "atlas_y_label": "UMAP 2",
        "atlas_points": [
            {"x": -2.0, "y": 1.0, "state_label": "Stem-like"},
            {"x": -1.6, "y": 0.7, "state_label": "Stem-like"},
            {"x": -0.2, "y": -0.1, "state_label": "Cycling"},
            {"x": 1.2, "y": -0.7, "state_label": "Effector"},
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
    }

def _make_atlas_spatial_trajectory_density_coverage_panel_display(display_id: str = "Figure32") -> dict[str, object]:
    return {
        "display_id": display_id,
        "template_id": "atlas_spatial_trajectory_density_coverage_panel",
        "title": "Atlas, spatial, and trajectory density-coverage support panel",
        "caption": (
            "Atlas occupancy, tissue coverage, progression support, and state-by-context support remain bound inside "
            "one audited density-coverage contract."
        ),
        "atlas_panel_title": "Atlas density",
        "atlas_x_label": "UMAP 1",
        "atlas_y_label": "UMAP 2",
        "atlas_points": [
            {"x": -2.1, "y": 1.0, "state_label": "Stem-like"},
            {"x": -1.7, "y": 0.8, "state_label": "Stem-like"},
            {"x": -0.2, "y": -0.1, "state_label": "Cycling"},
            {"x": 1.1, "y": -0.6, "state_label": "Effector"},
        ],
        "spatial_panel_title": "Spatial coverage topography",
        "spatial_x_label": "Tissue x coordinate",
        "spatial_y_label": "Tissue y coordinate",
        "spatial_points": [
            {"x": 0.12, "y": 0.82, "state_label": "Stem-like", "region_label": "Tumor core"},
            {"x": 0.18, "y": 0.76, "state_label": "Stem-like", "region_label": "Tumor core"},
            {"x": 0.54, "y": 0.48, "state_label": "Cycling", "region_label": "Invasive margin"},
            {"x": 0.82, "y": 0.20, "state_label": "Effector", "region_label": "Invasive margin"},
        ],
        "trajectory_panel_title": "Trajectory coverage progression",
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
        "support_panel_title": "State-by-context support",
        "support_x_label": "Context",
        "support_y_label": "Cell state",
        "support_scale_label": "Coverage fraction",
        "state_order": [
            {"label": "Stem-like"},
            {"label": "Cycling"},
            {"label": "Effector"},
        ],
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
