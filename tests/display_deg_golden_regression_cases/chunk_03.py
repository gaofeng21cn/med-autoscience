from .shared import *

def test_atlas_spatial_trajectory_storyboard_panel_preserves_deg_storyboard_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure31",
                    "display_kind": "figure",
                    "requirement_key": "atlas_spatial_trajectory_storyboard_panel",
                    "catalog_id": "F31",
                    "shell_path": "paper/figures/Figure31.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure31",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_storyboard_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "atlas_spatial_trajectory_storyboard_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_storyboard_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure31",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_storyboard_panel",
                    "title": "Atlas, spatial niche, trajectory progression, composition, and kinetics storyboard",
                    "caption": "Composite storyboard regression lock for atlas-spatial-trajectory coupling.",
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
                    "row_order": [{"label": "IFN response"}, {"label": "EMT module"}],
                    "column_order": [{"label": "Early"}, {"label": "Mid"}, {"label": "Late"}],
                    "cells": [
                        {"x": "Early", "y": "IFN response", "value": 0.74},
                        {"x": "Mid", "y": "IFN response", "value": 0.26},
                        {"x": "Late", "y": "IFN response", "value": -0.14},
                        {"x": "Early", "y": "EMT module", "value": -0.28},
                        {"x": "Mid", "y": "EMT module", "value": 0.18},
                        {"x": "Late", "y": "EMT module", "value": 0.72},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root / "figures" / "generated" / "F31_atlas_spatial_trajectory_storyboard_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_atlas",
        "panel_spatial",
        "panel_trajectory",
        "panel_composition",
        "panel_heatmap",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_D" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_E" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"
    assert layout_sidecar["metrics"]["state_labels"] == ["Stem-like", "Cycling", "Effector"]
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["bin_labels"] == ["Early", "Mid", "Late"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_atlas_spatial_trajectory_density_coverage_panel_preserves_deg_density_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure32",
                    "display_kind": "figure",
                    "requirement_key": "atlas_spatial_trajectory_density_coverage_panel",
                    "catalog_id": "F32",
                    "shell_path": "paper/figures/Figure32.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure32",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_density_coverage_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "atlas_spatial_trajectory_density_coverage_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_density_coverage_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure32",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_density_coverage_panel",
                    "title": "Atlas, spatial, and trajectory density-coverage support panel",
                    "caption": "Composite density-coverage regression lock for atlas-spatial-trajectory support.",
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
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root / "figures" / "generated" / "F32_atlas_spatial_trajectory_density_coverage_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_atlas",
        "panel_spatial",
        "panel_trajectory",
        "panel_support",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_D" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["state_labels"] == ["Stem-like", "Cycling", "Effector"]
    assert layout_sidecar["metrics"]["context_labels"] == [
        "Atlas density",
        "Spatial coverage",
        "Trajectory coverage",
    ]
    assert layout_sidecar["metrics"]["region_labels"] == ["Tumor core", "Invasive margin"]
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["support_scale_label"] == "Coverage fraction"
    assert len(layout_sidecar["metrics"]["support_cells"]) == 9

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_atlas_spatial_trajectory_context_support_panel_preserves_deg_multiview_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure33",
                    "display_kind": "figure",
                    "requirement_key": "atlas_spatial_trajectory_context_support_panel",
                    "catalog_id": "F33",
                    "shell_path": "paper/figures/Figure33.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure33",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_context_support_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "atlas_spatial_trajectory_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_context_support_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure33",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_context_support_panel",
                    "title": "Atlas, spatial, trajectory, composition, kinetics, and context support composite",
                    "caption": "Composite multiview regression lock for atlas-spatial-trajectory support.",
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
                    "row_order": [{"label": "IFN response"}, {"label": "EMT module"}],
                    "column_order": [{"label": "Early"}, {"label": "Mid"}, {"label": "Late"}],
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
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root / "figures" / "generated" / "F33_atlas_spatial_trajectory_context_support_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_atlas",
        "panel_spatial",
        "panel_trajectory",
        "panel_composition",
        "panel_heatmap",
        "panel_support",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_F" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"
    assert layout_sidecar["metrics"]["state_labels"] == ["Stem-like", "Cycling", "Effector"]
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["context_labels"] == [
        "Atlas density",
        "Spatial coverage",
        "Trajectory coverage",
    ]
    assert layout_sidecar["metrics"]["support_scale_label"] == "Coverage fraction"
    assert len(layout_sidecar["metrics"]["support_cells"]) == 9
    composition_y_axis_box = next(
        box for box in layout_sidecar["layout_boxes"] if box["box_id"] == "composition_y_axis_title"
    )
    assert composition_y_axis_box["x0"] >= 0.0

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_atlas_spatial_trajectory_multimanifold_context_support_panel_preserves_deg_multimanifold_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    surface_module = importlib.import_module("tests.test_display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure51",
                    "display_kind": "figure",
                    "requirement_key": "atlas_spatial_trajectory_multimanifold_context_support_panel",
                    "catalog_id": "F51",
                    "shell_path": "paper/figures/Figure51.shell.json",
                }
            ],
        },
    )
    _dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    _dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    _dump_json(
        paper_root / "medical_reporting_contract.json",
        {
            "schema_version": 1,
            "style_roles": {
                "model_curve": "#1f77b4",
                "comparator_curve": "#d62728",
                "reference_line": "#334155",
            },
            "palette": {"primary": "#1f77b4", "secondary_soft": "#cbd5e1", "light": "#eff6ff"},
            "typography": {"title_size": 12.5, "axis_title_size": 11.0, "tick_size": 10.0, "panel_label_size": 11.0},
            "stroke": {"marker_size": 4.5},
        },
    )
    _dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure51",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_trajectory_multimanifold_context_support_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
            "displays": [
                surface_module._make_atlas_spatial_trajectory_multimanifold_context_support_panel_display(
                    display_id="Figure51"
                )
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root
            / "figures"
            / "generated"
            / "F51_atlas_spatial_trajectory_multimanifold_context_support_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_atlas_A",
        "panel_atlas_B",
        "panel_spatial",
        "panel_trajectory",
        "panel_composition",
        "panel_heatmap",
        "panel_support",
    ]
    assert [item["manifold_method"] for item in layout_sidecar["metrics"]["atlas_manifold_panels"]] == ["umap", "phate"]
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["context_labels"] == [
        "Atlas density",
        "Spatial coverage",
        "Trajectory coverage",
    ]
    assert layout_sidecar["metrics"]["support_scale_label"] == "Coverage fraction"
    assert len(layout_sidecar["metrics"]["support_cells"]) == 9

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
