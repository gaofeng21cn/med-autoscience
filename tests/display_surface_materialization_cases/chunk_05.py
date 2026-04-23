from .shared import *

def test_materialize_display_surface_generates_single_cell_atlas_overview_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure27",
                    "template_id": "single_cell_atlas_overview_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "single_cell_atlas_overview_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "single_cell_atlas_overview_inputs_v1",
            "displays": [_make_single_cell_atlas_overview_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F27"]
    assert (paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F27_single_cell_atlas_overview_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_embedding",
        "panel_composition",
        "panel_heatmap",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["state_labels"]) == ["Myeloid", "T cells"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F27"
    assert figure_entry["template_id"] == full_id("single_cell_atlas_overview_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "single_cell_atlas_overview_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_single_cell_atlas_overview_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_spatial_niche_map_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure28",
                    "template_id": "spatial_niche_map_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "spatial_niche_map_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "spatial_niche_map_inputs_v1",
            "displays": [_make_spatial_niche_map_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F28"]
    assert (paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F28_spatial_niche_map_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_spatial",
        "panel_composition",
        "panel_heatmap",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert sorted(layout_sidecar["metrics"]["niche_labels"]) == ["Immune niche", "Stromal niche"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F28"
    assert figure_entry["template_id"] == full_id("spatial_niche_map_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "spatial_niche_map_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_spatial_niche_map_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_trajectory_progression_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure29",
                    "template_id": "trajectory_progression_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "trajectory_progression_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "trajectory_progression_inputs_v1",
            "displays": [_make_trajectory_progression_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F29"]
    assert (paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F29_trajectory_progression_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_trajectory",
        "panel_composition",
        "panel_heatmap",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"
    assert layout_sidecar["metrics"]["branch_labels"] == ["Branch A", "Branch B"]
    assert layout_sidecar["metrics"]["bin_labels"] == ["Early", "Mid", "Late"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F29"
    assert figure_entry["template_id"] == full_id("trajectory_progression_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "trajectory_progression_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_trajectory_progression_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_pathway_enrichment_dotplot_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure34",
                    "template_id": "pathway_enrichment_dotplot_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "pathway_enrichment_dotplot_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "pathway_enrichment_dotplot_panel_inputs_v1",
            "displays": [_make_pathway_enrichment_dotplot_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F34"]
    assert (paper_root / "figures" / "generated" / "F34_pathway_enrichment_dotplot_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F34_pathway_enrichment_dotplot_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F34_pathway_enrichment_dotplot_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == ["panel_A", "panel_B"]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}
    assert layout_sidecar["metrics"]["pathway_labels"] == ["IFN response", "EMT signaling", "Cell cycle"]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["panels"]] == ["transcriptome", "proteome"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F34"
    assert figure_entry["template_id"] == full_id("pathway_enrichment_dotplot_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "pathway_enrichment_dotplot_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_pathway_enrichment_dotplot_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_celltype_marker_dotplot_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure53",
                    "template_id": "celltype_marker_dotplot_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "celltype_marker_dotplot_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_marker_dotplot_panel_inputs_v1",
            "displays": [_make_celltype_marker_dotplot_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F53"]
    assert (paper_root / "figures" / "generated" / "F53_celltype_marker_dotplot_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F53_celltype_marker_dotplot_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F53_celltype_marker_dotplot_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
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
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F53"
    assert figure_entry["template_id"] == full_id("celltype_marker_dotplot_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "celltype_marker_dotplot_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_celltype_marker_dotplot_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_omics_volcano_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure35",
                    "template_id": "omics_volcano_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "omics_volcano_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "omics_volcano_panel_inputs_v1",
            "displays": [_make_omics_volcano_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F35"]
    assert (paper_root / "figures" / "generated" / "F35_omics_volcano_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F35_omics_volcano_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F35_omics_volcano_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
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
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F35"
    assert figure_entry["template_id"] == full_id("omics_volcano_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "omics_volcano_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_omics_volcano_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_oncoplot_mutation_landscape_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure36",
                    "template_id": "oncoplot_mutation_landscape_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "oncoplot_mutation_landscape_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "oncoplot_mutation_landscape_panel_inputs_v1",
            "displays": [_make_oncoplot_mutation_landscape_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F36"]
    assert (paper_root / "figures" / "generated" / "F36_oncoplot_mutation_landscape_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F36_oncoplot_mutation_landscape_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F36_oncoplot_mutation_landscape_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend"}
    assert layout_sidecar["metrics"]["mutation_legend_title"] == "Alteration"
    assert layout_sidecar["metrics"]["sample_ids"] == ["D1", "D2", "V1", "V2"]
    assert layout_sidecar["metrics"]["gene_labels"] == ["TP53", "KRAS", "EGFR"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F36"
    assert figure_entry["template_id"] == full_id("oncoplot_mutation_landscape_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "oncoplot_mutation_landscape_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_oncoplot_mutation_landscape_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_cnv_recurrence_summary_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure37",
                    "template_id": "cnv_recurrence_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "cnv_recurrence_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "cnv_recurrence_summary_panel_inputs_v1",
            "displays": [_make_cnv_recurrence_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F37"]
    assert (paper_root / "figures" / "generated" / "F37_cnv_recurrence_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F37_cnv_recurrence_summary_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F37_cnv_recurrence_summary_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend"}
    assert layout_sidecar["metrics"]["cnv_legend_title"] == "CNV state"
    assert layout_sidecar["metrics"]["sample_ids"] == ["D1", "D2", "V1", "V2"]
    assert layout_sidecar["metrics"]["region_labels"] == ["TP53", "MYC", "EGFR", "CDKN2A"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F37"
    assert figure_entry["template_id"] == full_id("cnv_recurrence_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "cnv_recurrence_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_cnv_recurrence_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_genomic_alteration_landscape_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure38",
                    "template_id": "genomic_alteration_landscape_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "genomic_alteration_landscape_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_landscape_panel_inputs_v1",
            "displays": [_make_genomic_alteration_landscape_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F38"]
    assert (paper_root / "figures" / "generated" / "F38_genomic_alteration_landscape_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F38_genomic_alteration_landscape_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F38_genomic_alteration_landscape_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend"}
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
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F38"
    assert figure_entry["template_id"] == full_id("genomic_alteration_landscape_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "genomic_alteration_landscape_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_genomic_alteration_landscape_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_genomic_alteration_consequence_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure39",
                    "template_id": "genomic_alteration_consequence_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "genomic_alteration_consequence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_consequence_panel_inputs_v1",
            "displays": [_make_genomic_alteration_consequence_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F39"]
    assert (paper_root / "figures" / "generated" / "F39_genomic_alteration_consequence_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F39_genomic_alteration_consequence_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F39_genomic_alteration_consequence_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
        "panel_consequence_A",
        "panel_consequence_B",
    ]
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_C" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "reference_line"}
    assert layout_sidecar["metrics"]["alteration_legend_title"] == "Genomic alteration"
    assert layout_sidecar["metrics"]["consequence_legend_title"] == "Consequence class"
    assert layout_sidecar["metrics"]["driver_gene_labels"] == ["TP53", "EGFR"]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["consequence_panels"]] == [
        "transcriptome",
        "proteome",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F39"
    assert figure_entry["template_id"] == full_id("genomic_alteration_consequence_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "genomic_alteration_consequence_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_genomic_alteration_consequence_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_genomic_alteration_multiomic_consequence_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure40",
                    "display_kind": "figure",
                    "requirement_key": "genomic_alteration_multiomic_consequence_panel",
                    "catalog_id": "F40",
                    "shell_path": "paper/figures/Figure40.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure40",
                    "template_id": "genomic_alteration_multiomic_consequence_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "genomic_alteration_multiomic_consequence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_multiomic_consequence_panel_inputs_v1",
            "displays": [_make_genomic_alteration_multiomic_consequence_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F40"]
    assert (paper_root / "figures" / "generated" / "F40_genomic_alteration_multiomic_consequence_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F40_genomic_alteration_multiomic_consequence_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F40_genomic_alteration_multiomic_consequence_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == [
        "panel_burden",
        "panel_annotations",
        "panel_matrix",
        "panel_frequency",
        "panel_consequence_A",
        "panel_consequence_B",
        "panel_consequence_C",
    ]
    assert any(box["box_id"] == "panel_label_D" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "reference_line"}
    assert layout_sidecar["metrics"]["driver_gene_labels"] == ["TP53", "EGFR"]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["consequence_panels"]] == [
        "proteome",
        "phosphoproteome",
        "glycoproteome",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F40"
    assert figure_entry["template_id"] == full_id("genomic_alteration_multiomic_consequence_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "genomic_alteration_multiomic_consequence_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_genomic_alteration_multiomic_consequence_panel"
    assert figure_entry["qc_result"]["status"] == "pass"
