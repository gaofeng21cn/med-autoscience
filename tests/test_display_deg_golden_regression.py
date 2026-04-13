from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_celltype_signature_heatmap_preserves_deg_composite_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure26",
                    "display_kind": "figure",
                    "requirement_key": "celltype_signature_heatmap",
                    "catalog_id": "F26",
                    "shell_path": "paper/figures/Figure26.shell.json",
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
                    "display_id": "Figure26",
                    "template_id": "fenggaolab.org.medical-display-core::celltype_signature_heatmap",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "celltype_signature_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_signature_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "fenggaolab.org.medical-display-core::celltype_signature_heatmap",
                    "title": "Cell-type embedding and signature activity atlas",
                    "caption": "Composite atlas regression lock for embedding-signature coupling.",
                    "embedding_panel_title": "Embedding by cell type",
                    "embedding_x_label": "UMAP 1",
                    "embedding_y_label": "UMAP 2",
                    "embedding_points": [
                        {"x": -2.1, "y": 1.0, "group": "T cells"},
                        {"x": -1.8, "y": 0.8, "group": "T cells"},
                        {"x": 1.4, "y": -0.6, "group": "Myeloid"},
                        {"x": 1.8, "y": -0.9, "group": "Myeloid"},
                    ],
                    "heatmap_panel_title": "Signature activity",
                    "heatmap_x_label": "Cell type",
                    "heatmap_y_label": "Program",
                    "score_method": "AUCell",
                    "row_order": [{"label": "IFN response"}, {"label": "TGF-beta signaling"}],
                    "column_order": [{"label": "T cells"}, {"label": "Myeloid"}],
                    "cells": [
                        {"x": "T cells", "y": "IFN response", "value": 0.78},
                        {"x": "Myeloid", "y": "IFN response", "value": -0.22},
                        {"x": "T cells", "y": "TGF-beta signaling", "value": -0.18},
                        {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.61},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == ["panel_left", "panel_right"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["group_labels"]) == ["Myeloid", "T cells"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_single_cell_atlas_overview_panel_preserves_deg_atlas_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure27",
                    "display_kind": "figure",
                    "requirement_key": "single_cell_atlas_overview_panel",
                    "catalog_id": "F27",
                    "shell_path": "paper/figures/Figure27.shell.json",
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
                    "display_id": "Figure27",
                    "template_id": "fenggaolab.org.medical-display-core::single_cell_atlas_overview_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "single_cell_atlas_overview_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "single_cell_atlas_overview_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure27",
                    "template_id": "fenggaolab.org.medical-display-core::single_cell_atlas_overview_panel",
                    "title": "Single-cell atlas occupancy, composition, and marker program overview",
                    "caption": "Composite atlas regression lock for occupancy-composition-program coupling.",
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
                    "row_order": [{"label": "IFN response"}, {"label": "TGF-beta signaling"}],
                    "column_order": [{"label": "T cells"}, {"label": "Myeloid"}],
                    "cells": [
                        {"x": "T cells", "y": "IFN response", "value": 0.81},
                        {"x": "Myeloid", "y": "IFN response", "value": -0.22},
                        {"x": "T cells", "y": "TGF-beta signaling", "value": -0.18},
                        {"x": "Myeloid", "y": "TGF-beta signaling", "value": 0.64},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_embedding",
        "panel_composition",
        "panel_heatmap",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["state_labels"]) == ["Myeloid", "T cells"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_spatial_niche_map_panel_preserves_deg_spatial_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure28",
                    "display_kind": "figure",
                    "requirement_key": "spatial_niche_map_panel",
                    "catalog_id": "F28",
                    "shell_path": "paper/figures/Figure28.shell.json",
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
                    "display_id": "Figure28",
                    "template_id": "fenggaolab.org.medical-display-core::spatial_niche_map_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "spatial_niche_map_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "spatial_niche_map_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure28",
                    "template_id": "fenggaolab.org.medical-display-core::spatial_niche_map_panel",
                    "title": "Spatial niche topography, abundance, and marker-program definition",
                    "caption": "Composite spatial regression lock for topography-composition-program coupling.",
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
                    "row_order": [{"label": "CXCL13 program"}, {"label": "TGF-beta program"}],
                    "column_order": [{"label": "Immune niche"}, {"label": "Stromal niche"}],
                    "cells": [
                        {"x": "Immune niche", "y": "CXCL13 program", "value": 0.78},
                        {"x": "Stromal niche", "y": "CXCL13 program", "value": -0.14},
                        {"x": "Immune niche", "y": "TGF-beta program", "value": -0.21},
                        {"x": "Stromal niche", "y": "TGF-beta program", "value": 0.66},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_spatial",
        "panel_composition",
        "panel_heatmap",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["niche_labels"]) == ["Immune niche", "Stromal niche"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_trajectory_progression_panel_preserves_deg_trajectory_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure29",
                    "display_kind": "figure",
                    "requirement_key": "trajectory_progression_panel",
                    "catalog_id": "F29",
                    "shell_path": "paper/figures/Figure29.shell.json",
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
                    "display_id": "Figure29",
                    "template_id": "fenggaolab.org.medical-display-core::trajectory_progression_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "trajectory_progression_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "trajectory_progression_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure29",
                    "template_id": "fenggaolab.org.medical-display-core::trajectory_progression_panel",
                    "title": "Trajectory progression, branch composition, and marker kinetics",
                    "caption": "Composite trajectory regression lock for branch-composition-kinetics coupling.",
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
                    "row_order": [{"label": "Interferon module"}, {"label": "EMT module"}],
                    "column_order": [{"label": "Early"}, {"label": "Mid"}, {"label": "Late"}],
                    "cells": [
                        {"x": "Early", "y": "Interferon module", "value": 0.72},
                        {"x": "Mid", "y": "Interferon module", "value": 0.28},
                        {"x": "Late", "y": "Interferon module", "value": -0.18},
                        {"x": "Early", "y": "EMT module", "value": -0.31},
                        {"x": "Mid", "y": "EMT module", "value": 0.22},
                        {"x": "Late", "y": "EMT module", "value": 0.68},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_trajectory",
        "panel_composition",
        "panel_heatmap",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["bin_labels"] == ["Early", "Mid", "Late"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_atlas_spatial_bridge_panel_preserves_deg_bridge_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure30",
                    "display_kind": "figure",
                    "requirement_key": "atlas_spatial_bridge_panel",
                    "catalog_id": "F30",
                    "shell_path": "paper/figures/Figure30.shell.json",
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
                    "display_id": "Figure30",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_bridge_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "atlas_spatial_bridge_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_bridge_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure30",
                    "template_id": "fenggaolab.org.medical-display-core::atlas_spatial_bridge_panel",
                    "title": "Atlas occupancy, spatial state topography, region composition, and marker-program bridge",
                    "caption": "Composite bridge regression lock for atlas-spatial-program coupling.",
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
                    "row_order": [{"label": "CXCL13 program"}, {"label": "TGF-beta program"}],
                    "column_order": [{"label": "T cells"}, {"label": "Myeloid"}],
                    "cells": [
                        {"x": "T cells", "y": "CXCL13 program", "value": 0.78},
                        {"x": "Myeloid", "y": "CXCL13 program", "value": -0.14},
                        {"x": "T cells", "y": "TGF-beta program", "value": -0.21},
                        {"x": "Myeloid", "y": "TGF-beta program", "value": 0.66},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F30_atlas_spatial_bridge_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_atlas",
        "panel_spatial",
        "panel_composition",
        "panel_heatmap",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_D" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["state_labels"]) == ["Myeloid", "T cells"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
