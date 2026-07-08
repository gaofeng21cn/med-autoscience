from __future__ import annotations

from . import shared_base as _shared_base
from . import layout_sidecar_fixtures as _layout_sidecar_fixtures

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared_base)
_module_reexport(_layout_sidecar_fixtures)


def _label_order(*labels: str) -> list[dict[str, str]]:
    return [{"label": label} for label in labels]


def _valued_cells(*rows: tuple[str, str, float]) -> list[dict[str, object]]:
    return [{"x": x, "y": y, "value": value} for x, y, value in rows]


def _composition_group(
    group_label: str,
    group_order: int,
    proportion_key: str,
    label_key: str,
    rows: tuple[tuple[str, float], ...],
) -> dict[str, object]:
    return {
        "group_label": group_label,
        "group_order": group_order,
        proportion_key: [{label_key: label, "proportion": value} for label, value in rows],
    }


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
            _composition_group("Tumor", 1, "state_proportions", "state_label", (("T cells", 0.58), ("Myeloid", 0.42))),
            _composition_group("Adjacent", 2, "state_proportions", "state_label", (("T cells", 0.37), ("Myeloid", 0.63))),
        ],
        "heatmap_panel_title": "Marker-program definition",
        "heatmap_x_label": "Cell state",
        "heatmap_y_label": "Marker / program",
        "score_method": "AUCell",
        "row_order": _label_order("IFN response", "TGF-beta signaling"),
        "column_order": _label_order("T cells", "Myeloid"),
        "cells": _valued_cells(
            ("T cells", "IFN response", 0.81),
            ("Myeloid", "IFN response", -0.22),
            ("T cells", "TGF-beta signaling", -0.18),
            ("Myeloid", "TGF-beta signaling", 0.64),
        ),
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
            _composition_group("Tumor core", 1, "state_proportions", "state_label", (("T cells", 0.64), ("Myeloid", 0.36))),
            _composition_group("Invasive margin", 2, "state_proportions", "state_label", (("T cells", 0.42), ("Myeloid", 0.58))),
        ],
        "heatmap_panel_title": "Marker-program definition",
        "heatmap_x_label": "Cell state",
        "heatmap_y_label": "Marker / program",
        "score_method": "AUCell",
        "row_order": _label_order("CXCL13 program", "TGF-beta program"),
        "column_order": _label_order("T cells", "Myeloid"),
        "cells": _valued_cells(
            ("T cells", "CXCL13 program", 0.78),
            ("Myeloid", "CXCL13 program", -0.14),
            ("T cells", "TGF-beta program", -0.21),
            ("Myeloid", "TGF-beta program", 0.66),
        ),
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
            _composition_group("Tumor core", 1, "niche_proportions", "niche_label", (("Immune niche", 0.64), ("Stromal niche", 0.36))),
            _composition_group("Invasive margin", 2, "niche_proportions", "niche_label", (("Immune niche", 0.42), ("Stromal niche", 0.58))),
        ],
        "heatmap_panel_title": "Marker-program definition",
        "heatmap_x_label": "Niche state",
        "heatmap_y_label": "Marker / program",
        "score_method": "AUCell",
        "row_order": _label_order("CXCL13 program", "TGF-beta program"),
        "column_order": _label_order("Immune niche", "Stromal niche"),
        "cells": _valued_cells(
            ("Immune niche", "CXCL13 program", 0.78),
            ("Stromal niche", "CXCL13 program", -0.14),
            ("Immune niche", "TGF-beta program", -0.21),
            ("Stromal niche", "TGF-beta program", 0.66),
        ),
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
        "branch_order": _label_order("Branch A", "Branch B"),
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
        "row_order": _label_order("Interferon module", "EMT module"),
        "column_order": _label_order("Early", "Mid", "Late"),
        "cells": _valued_cells(
            ("Early", "Interferon module", 0.72),
            ("Mid", "Interferon module", 0.28),
            ("Late", "Interferon module", -0.18),
            ("Early", "EMT module", -0.31),
            ("Mid", "EMT module", 0.22),
            ("Late", "EMT module", 0.68),
        ),
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
            _composition_group(
                "Tumor core",
                1,
                "state_proportions",
                "state_label",
                (("Stem-like", 0.48), ("Cycling", 0.32), ("Effector", 0.20)),
            ),
            _composition_group(
                "Invasive margin",
                2,
                "state_proportions",
                "state_label",
                (("Stem-like", 0.18), ("Cycling", 0.34), ("Effector", 0.48)),
            ),
        ],
        "heatmap_panel_title": "Program kinetics",
        "heatmap_x_label": "Pseudotime bin",
        "heatmap_y_label": "Marker / module",
        "score_method": "GSVA",
        "state_order": _label_order("Stem-like", "Cycling", "Effector"),
        "branch_order": _label_order("Branch A", "Branch B"),
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
        "row_order": _label_order("IFN response", "EMT module"),
        "column_order": _label_order("Early", "Mid", "Late"),
        "cells": _valued_cells(
            ("Early", "IFN response", 0.74),
            ("Mid", "IFN response", 0.26),
            ("Late", "IFN response", -0.14),
            ("Early", "EMT module", -0.28),
            ("Mid", "EMT module", 0.18),
            ("Late", "EMT module", 0.72),
        ),
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
        "state_order": _label_order("Stem-like", "Cycling", "Effector"),
        "context_order": [
            {"label": "Atlas density", "context_kind": "atlas_density"},
            {"label": "Spatial coverage", "context_kind": "spatial_coverage"},
            {"label": "Trajectory coverage", "context_kind": "trajectory_coverage"},
        ],
        "support_cells": _valued_cells(
            ("Atlas density", "Stem-like", 0.84),
            ("Spatial coverage", "Stem-like", 0.73),
            ("Trajectory coverage", "Stem-like", 0.58),
            ("Atlas density", "Cycling", 0.49),
            ("Spatial coverage", "Cycling", 0.61),
            ("Trajectory coverage", "Cycling", 0.66),
            ("Atlas density", "Effector", 0.31),
            ("Spatial coverage", "Effector", 0.54),
            ("Trajectory coverage", "Effector", 0.81),
        ),
    }
