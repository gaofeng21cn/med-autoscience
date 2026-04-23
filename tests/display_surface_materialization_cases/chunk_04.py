from .shared import *

def test_materialize_display_surface_generates_risk_layering_monotonic_bars(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure22",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F22",
                    "shell_path": "paper/figures/Figure22.shell.json",
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
                    "display_id": "risk_layering",
                    "template_id": "risk_layering_monotonic_bars",
                    "layout_override": {
                        "show_figure_title": True,
                    },
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "risk_layering_monotonic_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "risk_layering_monotonic_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure22",
                    "template_id": "risk_layering_monotonic_bars",
                    "title": "Monotonic risk layering of the 3-month endocrine burden score",
                    "caption": "Observed risk rises monotonically across score bands and grouped follow-up strata.",
                    "y_label": "Risk of later persistent global hypopituitarism (%)",
                    "left_panel_title": "Score bands",
                    "left_x_label": "Simple score",
                    "left_bars": [
                        {"label": "0", "cases": 95, "events": 8, "risk": 0.0842},
                        {"label": "1", "cases": 98, "events": 18, "risk": 0.1837},
                        {"label": "2", "cases": 98, "events": 35, "risk": 0.3571},
                        {"label": "3", "cases": 54, "events": 29, "risk": 0.5370},
                        {"label": "4+", "cases": 12, "events": 8, "risk": 0.6667},
                    ],
                    "right_panel_title": "Grouped follow-up strata",
                    "right_x_label": "Grouped risk",
                    "right_bars": [
                        {"label": "Low", "cases": 95, "events": 8, "risk": 0.0842},
                        {"label": "Intermediate", "cases": 196, "events": 53, "risk": 0.2704},
                        {"label": "High", "cases": 66, "events": 37, "risk": 0.5606},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F22"]
    assert (paper_root / "figures" / "generated" / "F22_risk_layering_monotonic_bars.png").exists()
    assert (paper_root / "figures" / "generated" / "F22_risk_layering_monotonic_bars.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F22_risk_layering_monotonic_bars.layout.json"
    assert layout_sidecar_path.exists()

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F22"
    assert figure_entry["template_id"] == full_id("risk_layering_monotonic_bars")
    assert figure_entry["pack_id"] == "fenggaolab.org.medical-display-core"
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "risk_layering_monotonic_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_risk_layering_bars"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_gsva_ssgsea_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure23",
                    "display_kind": "figure",
                    "requirement_key": "gsva_ssgsea_heatmap",
                    "catalog_id": "F23",
                    "shell_path": "paper/figures/Figure23.shell.json",
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
                    "display_id": "Figure23",
                    "template_id": "gsva_ssgsea_heatmap",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "gsva_ssgsea_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "gsva_ssgsea_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure23",
                    "template_id": "gsva_ssgsea_heatmap",
                    "title": "GSVA heatmap for immune and stromal programs",
                    "caption": "Precomputed GSVA pathway scores across the analytic cohort highlight the dominant immune-stromal contrast.",
                    "x_label": "Samples",
                    "y_label": "Gene-set programs",
                    "score_method": "GSVA",
                    "row_order": [
                        {"label": "IFN-gamma response"},
                        {"label": "TGF-beta signaling"},
                    ],
                    "column_order": [
                        {"label": "Sample-01"},
                        {"label": "Sample-02"},
                    ],
                    "cells": [
                        {"x": "Sample-01", "y": "IFN-gamma response", "value": 0.72},
                        {"x": "Sample-02", "y": "IFN-gamma response", "value": -0.24},
                        {"x": "Sample-01", "y": "TGF-beta signaling", "value": -0.11},
                        {"x": "Sample-02", "y": "TGF-beta signaling", "value": 0.58},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F23"]
    assert (paper_root / "figures" / "generated" / "F23_gsva_ssgsea_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F23_gsva_ssgsea_heatmap.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F23_gsva_ssgsea_heatmap.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["score_method"] == "GSVA"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F23"
    assert figure_entry["template_id"] == full_id("gsva_ssgsea_heatmap")
    assert figure_entry["renderer_family"] == "r_ggplot2"
    assert figure_entry["input_schema_id"] == "gsva_ssgsea_heatmap_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_heatmap"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_performance_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure25",
                    "display_kind": "figure",
                    "requirement_key": "performance_heatmap",
                    "catalog_id": "F25",
                    "shell_path": "paper/figures/Figure25.shell.json",
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
                    "display_id": "Figure25",
                    "template_id": "performance_heatmap",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "performance_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "performance_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure25",
                    "template_id": "performance_heatmap",
                    "title": "AUC heatmap across APOE4 subgroups and predictor sets",
                    "caption": "Random-forest discrimination remains strongest for the integrated model across APOE4-stratified analyses.",
                    "x_label": "Analytic subgroup",
                    "y_label": "Predictor set",
                    "metric_name": "AUC",
                    "row_order": [
                        {"label": "Clinical baseline"},
                        {"label": "Integrated model"},
                    ],
                    "column_order": [
                        {"label": "All participants"},
                        {"label": "APOE4 carriers"},
                    ],
                    "cells": [
                        {"x": "All participants", "y": "Clinical baseline", "value": 0.71},
                        {"x": "APOE4 carriers", "y": "Clinical baseline", "value": 0.68},
                        {"x": "All participants", "y": "Integrated model", "value": 0.83},
                        {"x": "APOE4 carriers", "y": "Integrated model", "value": 0.79},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F25"]
    assert (paper_root / "figures" / "generated" / "F25_performance_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F25_performance_heatmap.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F25_performance_heatmap.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["metric_name"] == "AUC"
    assert layout_sidecar["metrics"]["matrix_cells"][0]["value"] == 0.71

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F25"
    assert figure_entry["template_id"] == full_id("performance_heatmap")
    assert figure_entry["renderer_family"] == "r_ggplot2"
    assert figure_entry["input_schema_id"] == "performance_heatmap_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_heatmap"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_binary_confusion_matrix_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure26",
                    "display_kind": "figure",
                    "requirement_key": "confusion_matrix_heatmap_binary",
                    "catalog_id": "F26",
                    "shell_path": "paper/figures/Figure26.shell.json",
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
                    "display_id": "Figure26",
                    "template_id": "confusion_matrix_heatmap_binary",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "confusion_matrix_heatmap_binary_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "confusion_matrix_heatmap_binary_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "confusion_matrix_heatmap_binary",
                    "title": "Binary confusion matrix on the held-out cohort",
                    "caption": "Row-normalized confusion matrix summarizing false-positive and false-negative error modes.",
                    "x_label": "Predicted class",
                    "y_label": "Observed class",
                    "metric_name": "Observed proportion",
                    "normalization": "row_fraction",
                    "row_order": [
                        {"label": "Observed negative"},
                        {"label": "Observed positive"},
                    ],
                    "column_order": [
                        {"label": "Predicted negative"},
                        {"label": "Predicted positive"},
                    ],
                    "cells": [
                        {"x": "Predicted negative", "y": "Observed negative", "value": 0.88},
                        {"x": "Predicted positive", "y": "Observed negative", "value": 0.12},
                        {"x": "Predicted negative", "y": "Observed positive", "value": 0.19},
                        {"x": "Predicted positive", "y": "Observed positive", "value": 0.81},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F26"]
    assert (paper_root / "figures" / "generated" / "F26_confusion_matrix_heatmap_binary.png").exists()
    assert (paper_root / "figures" / "generated" / "F26_confusion_matrix_heatmap_binary.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F26_confusion_matrix_heatmap_binary.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["metric_name"] == "Observed proportion"
    assert layout_sidecar["metrics"]["normalization"] == "row_fraction"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F26"
    assert figure_entry["template_id"] == full_id("confusion_matrix_heatmap_binary")
    assert figure_entry["renderer_family"] == "r_ggplot2"
    assert figure_entry["input_schema_id"] == "confusion_matrix_heatmap_binary_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_heatmap"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_celltype_signature_heatmap_baseline(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "celltype_signature_heatmap",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "celltype_signature_heatmap_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_signature_heatmap_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure26",
                    "template_id": "celltype_signature_heatmap",
                    "title": "Cell-type embedding and signature activity atlas",
                    "caption": "Cell-type clusters and pathway-signature activity remain aligned across the circulating immune atlas.",
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
                    "row_order": [
                        {"label": "IFN response"},
                        {"label": "TGF-beta signaling"},
                    ],
                    "column_order": [
                        {"label": "T cells"},
                        {"label": "Myeloid"},
                    ],
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
    assert result["figures_materialized"] == ["F26"]
    assert (paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.png").exists()
    assert (paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F26_celltype_signature_heatmap.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert layout_sidecar["metrics"]["score_method"] == "AUCell"
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "colorbar"}
    assert any(box["box_type"] == "heatmap_tile_region" for box in layout_sidecar["panel_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F26"
    assert figure_entry["template_id"] == full_id("celltype_signature_heatmap")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "celltype_signature_heatmap_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_celltype_signature_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_incomplete_composition_for_single_cell_atlas_overview(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_single_cell_atlas_overview_display()
    display_payload["composition_groups"][1]["state_proportions"] = [
        {"state_label": "T cells", "proportion": 0.37},
    ]
    dump_json(
        paper_root / "single_cell_atlas_overview_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "single_cell_atlas_overview_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("single_cell_atlas_overview_panel")

    with pytest.raises(ValueError, match="composition_groups.*must cover the declared state labels exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure27",
        )

def test_load_evidence_display_payload_rejects_incomplete_composition_for_spatial_niche_map(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_spatial_niche_map_display()
    display_payload["composition_groups"][1]["niche_proportions"] = [
        {"niche_label": "Immune niche", "proportion": 0.42},
    ]
    dump_json(
        paper_root / "spatial_niche_map_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "spatial_niche_map_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("spatial_niche_map_panel")

    with pytest.raises(ValueError, match="composition_groups.*must cover the declared niche labels exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure28",
        )

def test_load_evidence_display_payload_rejects_incomplete_panel_pathway_grid_for_enrichment_dotplot(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_pathway_enrichment_dotplot_panel_display()
    display_payload["points"] = list(display_payload["points"][:-1])
    dump_json(
        paper_root / "pathway_enrichment_dotplot_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "pathway_enrichment_dotplot_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("pathway_enrichment_dotplot_panel")

    with pytest.raises(ValueError, match="must cover every declared panel/pathway coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure34",
        )

def test_load_evidence_display_payload_rejects_incomplete_panel_celltype_marker_grid_for_dotplot(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_celltype_marker_dotplot_panel_display()
    display_payload["points"] = list(display_payload["points"][:-1])
    dump_json(
        paper_root / "celltype_marker_dotplot_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "celltype_marker_dotplot_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("celltype_marker_dotplot_panel")

    with pytest.raises(ValueError, match="must cover every declared panel/celltype/marker coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure53",
        )

def test_load_evidence_display_payload_rejects_incomplete_layer_support_grid_for_genomic_program_governance_summary_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_genomic_program_governance_summary_panel_display()
    display_payload["programs"][1]["layer_supports"] = list(display_payload["programs"][1]["layer_supports"][:-1])
    dump_json(
        paper_root / "genomic_program_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_program_governance_summary_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("genomic_program_governance_summary_panel")

    with pytest.raises(ValueError, match="layer_supports must cover the declared layer_order exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure51",
        )

def test_load_evidence_display_payload_rejects_unsupported_regulation_class_for_omics_volcano_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_omics_volcano_panel_display()
    display_payload["points"][0]["regulation_class"] = "mixed"
    dump_json(
        paper_root / "omics_volcano_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "omics_volcano_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("omics_volcano_panel")

    with pytest.raises(ValueError, match="regulation_class must be one of upregulated, downregulated, background"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure35",
        )

def test_load_evidence_display_payload_rejects_incomplete_driver_panel_grid_for_genomic_alteration_consequence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_genomic_alteration_consequence_panel_display()
    display_payload["consequence_points"] = list(display_payload["consequence_points"][:-1])
    dump_json(
        paper_root / "genomic_alteration_consequence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_consequence_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("genomic_alteration_consequence_panel")

    with pytest.raises(ValueError, match="must cover every declared consequence panel/driver gene coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure39",
        )

def test_load_evidence_display_payload_rejects_incomplete_multiomic_driver_panel_grid(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_genomic_alteration_multiomic_consequence_panel_display()
    display_payload["consequence_points"] = list(display_payload["consequence_points"][:-1])
    dump_json(
        paper_root / "genomic_alteration_multiomic_consequence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_multiomic_consequence_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("genomic_alteration_multiomic_consequence_panel")

    with pytest.raises(ValueError, match="must cover every declared consequence panel/driver gene coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure40",
        )

def test_load_evidence_display_payload_rejects_incomplete_pathway_grid_for_genomic_alteration_pathway_integrated_composite(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_genomic_alteration_pathway_integrated_composite_panel_display()
    display_payload["pathway_points"] = list(display_payload["pathway_points"][:-1])
    dump_json(
        paper_root / "genomic_alteration_pathway_integrated_composite_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_pathway_integrated_composite_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("genomic_alteration_pathway_integrated_composite_panel")

    with pytest.raises(ValueError, match="must cover every declared pathway panel/pathway coordinate exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure41",
        )

def test_load_evidence_display_payload_rejects_duplicate_sample_gene_coordinate_for_oncoplot(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_oncoplot_mutation_landscape_panel_display()
    display_payload["mutation_records"].append(
        {"sample_id": "D1", "gene_label": "TP53", "alteration_class": "multi_hit"}
    )
    dump_json(
        paper_root / "oncoplot_mutation_landscape_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "oncoplot_mutation_landscape_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("oncoplot_mutation_landscape_panel")

    with pytest.raises(ValueError, match="must keep sample/gene coordinates unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure36",
        )

def test_materialize_display_surface_generates_atlas_spatial_bridge_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    write_default_publication_display_contracts(paper_root)
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    dump_json(
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
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure30",
                    "template_id": full_id("atlas_spatial_bridge_panel"),
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "atlas_spatial_bridge_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_bridge_panel_inputs_v1",
            "displays": [_make_atlas_spatial_bridge_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_entry = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))["figures"][0]
    assert figure_entry["figure_id"] == "F30"
    assert figure_entry["template_id"] == full_id("atlas_spatial_bridge_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "atlas_spatial_bridge_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_atlas_spatial_bridge_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_atlas_spatial_bridge_when_spatial_states_drift(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_atlas_spatial_bridge_display()
    display_payload["spatial_points"][1]["state_label"] = "Fibroblast"
    dump_json(
        paper_root / "atlas_spatial_bridge_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_bridge_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("atlas_spatial_bridge_panel")

    with pytest.raises(ValueError, match="column_order labels must match spatial point state labels"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure30",
        )

def test_load_evidence_display_payload_rejects_incomplete_branch_weights_for_trajectory_progression(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_trajectory_progression_display()
    display_payload["progression_bins"][1]["branch_weights"] = [
        {"branch_label": "Branch A", "proportion": 0.49},
    ]
    dump_json(
        paper_root / "trajectory_progression_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "trajectory_progression_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("trajectory_progression_panel")

    with pytest.raises(ValueError, match="progression_bins.*must cover the declared branch labels exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure29",
        )
