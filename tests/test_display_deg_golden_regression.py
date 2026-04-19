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


def test_pathway_enrichment_dotplot_panel_preserves_eg_omics_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure34",
                    "display_kind": "figure",
                    "requirement_key": "pathway_enrichment_dotplot_panel",
                    "catalog_id": "F34",
                    "shell_path": "paper/figures/Figure34.shell.json",
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
                    "display_id": "Figure34",
                    "template_id": "fenggaolab.org.medical-display-core::pathway_enrichment_dotplot_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "pathway_enrichment_dotplot_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "pathway_enrichment_dotplot_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure34",
                    "template_id": "fenggaolab.org.medical-display-core::pathway_enrichment_dotplot_panel",
                    "title": "Pathway enrichment comparison across transcriptome and proteome",
                    "caption": "Shared pathway ordering and effect-size semantics remain stable across both omics panels.",
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
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F34_pathway_enrichment_dotplot_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == ["panel_A", "panel_B"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["effect_scale_label"] == "Directionality score"
    assert layout_sidecar["metrics"]["size_scale_label"] == "Gene count"
    assert layout_sidecar["metrics"]["pathway_labels"] == ["IFN response", "EMT signaling", "Cell cycle"]

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

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
