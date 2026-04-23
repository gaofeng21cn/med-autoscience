from .shared import *

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

def test_celltype_marker_dotplot_panel_preserves_deg_marker_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure53",
                    "display_kind": "figure",
                    "requirement_key": "celltype_marker_dotplot_panel",
                    "catalog_id": "F53",
                    "shell_path": "paper/figures/Figure53.shell.json",
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
                    "display_id": "Figure53",
                    "template_id": "fenggaolab.org.medical-display-core::celltype_marker_dotplot_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "celltype_marker_dotplot_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_marker_dotplot_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure53",
                    "template_id": "fenggaolab.org.medical-display-core::celltype_marker_dotplot_panel",
                    "title": "Cell-type marker expression atlas across discovery and validation cohorts",
                    "caption": "Marker-expression atlas regression lock for celltype-marker grid completeness and size/effect semantics.",
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
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F53_celltype_marker_dotplot_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == ["panel_A", "panel_B"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["effect_scale_label"] == "Mean expression"
    assert layout_sidecar["metrics"]["size_scale_label"] == "Detection rate (%)"
    assert layout_sidecar["metrics"]["celltype_labels"] == ["Basal", "Immune", "Stromal"]
    assert layout_sidecar["metrics"]["marker_labels"] == ["KRT14", "CXCL13", "COL1A1"]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["panels"]] == ["discovery", "validation"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_omics_volcano_panel_preserves_g_omics_contract(tmp_path: Path) -> None:
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
                    "display_id": "Figure35",
                    "display_kind": "figure",
                    "requirement_key": "omics_volcano_panel",
                    "catalog_id": "F35",
                    "shell_path": "paper/figures/Figure35.shell.json",
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
                    "display_id": "Figure35",
                    "template_id": "fenggaolab.org.medical-display-core::omics_volcano_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "omics_volcano_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "omics_volcano_panel_inputs_v1",
            "displays": [surface_module._make_omics_volcano_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F35_omics_volcano_panel.layout.json").read_text(encoding="utf-8")
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == ["panel_A", "panel_B"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "label_A_0" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "label_B_0" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "reference_line"}
    assert layout_sidecar["metrics"]["legend_title"] == "Regulation"
    assert layout_sidecar["metrics"]["effect_threshold"] == 1.0
    assert layout_sidecar["metrics"]["significance_threshold"] == 2.0
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["panels"]] == ["transcriptome", "proteome"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_oncoplot_mutation_landscape_panel_preserves_g_omics_contract(tmp_path: Path) -> None:
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
                    "display_id": "Figure36",
                    "display_kind": "figure",
                    "requirement_key": "oncoplot_mutation_landscape_panel",
                    "catalog_id": "F36",
                    "shell_path": "paper/figures/Figure36.shell.json",
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
                    "display_id": "Figure36",
                    "template_id": "fenggaolab.org.medical-display-core::oncoplot_mutation_landscape_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "oncoplot_mutation_landscape_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "oncoplot_mutation_landscape_panel_inputs_v1",
            "displays": [surface_module._make_oncoplot_mutation_landscape_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F36_oncoplot_mutation_landscape_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
    ]
    assert layout_sidecar["metrics"]["sample_ids"] == ["D1", "D2", "V1", "V2"]
    assert layout_sidecar["metrics"]["gene_labels"] == ["TP53", "KRAS", "EGFR"]

def test_cnv_recurrence_summary_panel_preserves_g_omics_contract(tmp_path: Path) -> None:
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
                    "display_id": "Figure37",
                    "display_kind": "figure",
                    "requirement_key": "cnv_recurrence_summary_panel",
                    "catalog_id": "F37",
                    "shell_path": "paper/figures/Figure37.shell.json",
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
                    "display_id": "Figure37",
                    "template_id": "fenggaolab.org.medical-display-core::cnv_recurrence_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "cnv_recurrence_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "cnv_recurrence_summary_panel_inputs_v1",
            "displays": [surface_module._make_cnv_recurrence_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F37_cnv_recurrence_summary_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
    ]
    assert layout_sidecar["metrics"]["cnv_legend_title"] == "CNV state"
    assert layout_sidecar["metrics"]["sample_ids"] == ["D1", "D2", "V1", "V2"]
    assert layout_sidecar["metrics"]["region_labels"] == ["TP53", "MYC", "EGFR", "CDKN2A"]
    assert [track["track_id"] for track in layout_sidecar["metrics"]["annotation_tracks"]] == ["cohort", "response"]
    assert sorted({cell["cnv_state"] for cell in layout_sidecar["metrics"]["cnv_cells"]}) == [
        "amplification",
        "deep_loss",
        "gain",
        "loss",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_genomic_alteration_landscape_panel_preserves_g_omics_contract(tmp_path: Path) -> None:
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
                    "display_id": "Figure38",
                    "display_kind": "figure",
                    "requirement_key": "genomic_alteration_landscape_panel",
                    "catalog_id": "F38",
                    "shell_path": "paper/figures/Figure38.shell.json",
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
                    "display_id": "Figure38",
                    "template_id": "fenggaolab.org.medical-display-core::genomic_alteration_landscape_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "genomic_alteration_landscape_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_landscape_panel_inputs_v1",
            "displays": [surface_module._make_genomic_alteration_landscape_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F38_genomic_alteration_landscape_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
    ]
    assert layout_sidecar["metrics"]["alteration_legend_title"] == "Genomic alteration"
    assert layout_sidecar["metrics"]["sample_ids"] == ["D1", "D2", "V1", "V2"]
    assert layout_sidecar["metrics"]["gene_labels"] == ["TP53", "KRAS", "EGFR", "PIK3CA"]
    assert any(
        cell["sample_id"] == "D1"
        and cell["gene_label"] == "TP53"
        and cell["mutation_class"] == "missense"
        and cell["cnv_state"] == "loss"
        for cell in layout_sidecar["metrics"]["alteration_cells"]
    )

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_genomic_alteration_consequence_panel_preserves_g_omics_contract(tmp_path: Path) -> None:
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
                    "display_id": "Figure39",
                    "display_kind": "figure",
                    "requirement_key": "genomic_alteration_consequence_panel",
                    "catalog_id": "F39",
                    "shell_path": "paper/figures/Figure39.shell.json",
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
                    "display_id": "Figure39",
                    "template_id": "fenggaolab.org.medical-display-core::genomic_alteration_consequence_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "genomic_alteration_consequence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_consequence_panel_inputs_v1",
            "displays": [surface_module._make_genomic_alteration_consequence_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F39_genomic_alteration_consequence_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
        "panel_consequence_A",
        "panel_consequence_B",
    ]
    assert layout_sidecar["metrics"]["alteration_legend_title"] == "Genomic alteration"
    assert layout_sidecar["metrics"]["consequence_legend_title"] == "Consequence class"
    assert layout_sidecar["metrics"]["driver_gene_labels"] == ["TP53", "EGFR"]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["consequence_panels"]] == [
        "transcriptome",
        "proteome",
    ]
    assert all(
        sorted(point["gene_label"] for point in panel["points"]) == ["EGFR", "TP53"]
        for panel in layout_sidecar["metrics"]["consequence_panels"]
    )

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
