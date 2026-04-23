from .shared import *

def test_materialize_display_surface_generates_genomic_alteration_pathway_integrated_composite_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure41",
                    "display_kind": "figure",
                    "requirement_key": "genomic_alteration_pathway_integrated_composite_panel",
                    "catalog_id": "F41",
                    "shell_path": "paper/figures/Figure41.shell.json",
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
                    "display_id": "Figure41",
                    "template_id": "genomic_alteration_pathway_integrated_composite_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "genomic_alteration_pathway_integrated_composite_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_alteration_pathway_integrated_composite_panel_inputs_v1",
            "displays": [_make_genomic_alteration_pathway_integrated_composite_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F41"]
    assert (
        paper_root / "figures" / "generated" / "F41_genomic_alteration_pathway_integrated_composite_panel.png"
    ).exists()
    assert (
        paper_root / "figures" / "generated" / "F41_genomic_alteration_pathway_integrated_composite_panel.pdf"
    ).exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F41_genomic_alteration_pathway_integrated_composite_panel.layout.json"
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
        "panel_pathway_A",
        "panel_pathway_B",
        "panel_pathway_C",
    ]
    assert any(box["box_id"] == "panel_label_G" for box in layout_sidecar["layout_boxes"])
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} >= {"legend", "reference_line", "colorbar"}
    assert layout_sidecar["metrics"]["driver_gene_labels"] == ["TP53", "EGFR"]
    assert layout_sidecar["metrics"]["pathway_labels"] == [
        "PI3K-AKT signaling",
        "Cell cycle",
        "DNA damage response",
        "Immune signaling",
    ]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["consequence_panels"]] == [
        "proteome",
        "phosphoproteome",
        "glycoproteome",
    ]
    assert [panel["panel_id"] for panel in layout_sidecar["metrics"]["pathway_panels"]] == [
        "proteome",
        "phosphoproteome",
        "glycoproteome",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F41"
    assert figure_entry["template_id"] == full_id("genomic_alteration_pathway_integrated_composite_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "genomic_alteration_pathway_integrated_composite_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_genomic_alteration_pathway_integrated_composite_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_genomic_program_governance_summary_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure51",
                    "display_kind": "figure",
                    "requirement_key": "genomic_program_governance_summary_panel",
                    "catalog_id": "F51",
                    "shell_path": "paper/figures/Figure51.shell.json",
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
                    "display_id": "Figure51",
                    "template_id": "genomic_program_governance_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "genomic_program_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "genomic_program_governance_summary_panel_inputs_v1",
            "displays": [_make_genomic_program_governance_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F51"]
    assert (paper_root / "figures" / "generated" / "F51_genomic_program_governance_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F51_genomic_program_governance_summary_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F51_genomic_program_governance_summary_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert [box["box_id"] for box in layout_sidecar["panel_boxes"]] == ["panel_evidence", "panel_summary"]
    assert layout_sidecar["metrics"]["layer_labels"] == [
        "Alteration",
        "Proteome",
        "Phosphoproteome",
        "Glycoproteome",
        "Pathway",
    ]
    assert [item["program_id"] for item in layout_sidecar["metrics"]["programs"]] == [
        "pi3k_growth",
        "cell_cycle_stress",
        "immune_suppression",
    ]
    assert {box["box_type"] for box in layout_sidecar["guide_boxes"]} == {"legend", "colorbar"}

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F51"
    assert figure_entry["template_id"] == full_id("genomic_program_governance_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "genomic_program_governance_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_genomic_program_governance_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_atlas_spatial_trajectory_storyboard_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure31",
                    "template_id": "atlas_spatial_trajectory_storyboard_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "atlas_spatial_trajectory_storyboard_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_storyboard_inputs_v1",
            "displays": [_make_atlas_spatial_trajectory_storyboard_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F31"]
    assert (paper_root / "figures" / "generated" / "F31_atlas_spatial_trajectory_storyboard_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F31_atlas_spatial_trajectory_storyboard_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F31_atlas_spatial_trajectory_storyboard_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
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
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F31"
    assert figure_entry["template_id"] == full_id("atlas_spatial_trajectory_storyboard_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "atlas_spatial_trajectory_storyboard_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_atlas_spatial_trajectory_storyboard_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_storyboard_when_trajectory_states_drift(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_atlas_spatial_trajectory_storyboard_display()
    display_payload["trajectory_points"][1]["state_label"] = "Terminal"
    dump_json(
        paper_root / "atlas_spatial_trajectory_storyboard_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_storyboard_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("atlas_spatial_trajectory_storyboard_panel")

    with pytest.raises(ValueError, match="state_order labels must match trajectory point state labels"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure31",
        )

def test_materialize_display_surface_generates_atlas_spatial_trajectory_density_coverage_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure32",
                    "template_id": "atlas_spatial_trajectory_density_coverage_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "atlas_spatial_trajectory_density_coverage_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_density_coverage_panel_inputs_v1",
            "displays": [_make_atlas_spatial_trajectory_density_coverage_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F32"]
    assert (paper_root / "figures" / "generated" / "F32_atlas_spatial_trajectory_density_coverage_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F32_atlas_spatial_trajectory_density_coverage_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F32_atlas_spatial_trajectory_density_coverage_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
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
    assert layout_sidecar["metrics"]["support_scale_label"] == "Coverage fraction"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F32"
    assert figure_entry["template_id"] == full_id("atlas_spatial_trajectory_density_coverage_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "atlas_spatial_trajectory_density_coverage_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_atlas_spatial_trajectory_density_coverage_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_density_coverage_when_support_grid_drifts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_atlas_spatial_trajectory_density_coverage_panel_display()
    display_payload["support_cells"] = [
        item
        for item in display_payload["support_cells"]
        if not (item["x"] == "Trajectory coverage" and item["y"] == "Effector")
    ]
    dump_json(
        paper_root / "atlas_spatial_trajectory_density_coverage_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_density_coverage_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("atlas_spatial_trajectory_density_coverage_panel")

    with pytest.raises(ValueError, match="support_cells must cover the declared state-context grid exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure32",
        )

def test_materialize_display_surface_generates_atlas_spatial_trajectory_context_support_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure33",
                    "template_id": "atlas_spatial_trajectory_context_support_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "atlas_spatial_trajectory_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_context_support_panel_inputs_v1",
            "displays": [_make_atlas_spatial_trajectory_context_support_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F33"]
    assert (paper_root / "figures" / "generated" / "F33_atlas_spatial_trajectory_context_support_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F33_atlas_spatial_trajectory_context_support_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F33_atlas_spatial_trajectory_context_support_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
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
    assert layout_sidecar["metrics"]["context_labels"] == [
        "Atlas density",
        "Spatial coverage",
        "Trajectory coverage",
    ]
    assert layout_sidecar["metrics"]["support_scale_label"] == "Coverage fraction"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F33"
    assert figure_entry["template_id"] == full_id("atlas_spatial_trajectory_context_support_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "atlas_spatial_trajectory_context_support_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_atlas_spatial_trajectory_context_support_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_context_support_when_support_grid_drifts(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_atlas_spatial_trajectory_context_support_panel_display()
    display_payload["support_cells"] = [
        item
        for item in display_payload["support_cells"]
        if not (item["x"] == "Trajectory coverage" and item["y"] == "Effector")
    ]
    dump_json(
        paper_root / "atlas_spatial_trajectory_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_context_support_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("atlas_spatial_trajectory_context_support_panel")

    with pytest.raises(ValueError, match="support_cells must cover the declared state-context grid exactly once"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure33",
        )

def test_materialize_display_surface_generates_atlas_spatial_trajectory_multimanifold_context_support_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure51",
                    "template_id": full_id("atlas_spatial_trajectory_multimanifold_context_support_panel"),
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
            "displays": [_make_atlas_spatial_trajectory_multimanifold_context_support_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F51"]
    assert (
        paper_root / "figures" / "generated" / "F51_atlas_spatial_trajectory_multimanifold_context_support_panel.png"
    ).exists()
    assert (
        paper_root / "figures" / "generated" / "F51_atlas_spatial_trajectory_multimanifold_context_support_panel.pdf"
    ).exists()
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
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_G" for box in layout_sidecar["layout_boxes"])
    composition_y_axis_box = next(
        box for box in layout_sidecar["layout_boxes"] if box["box_id"] == "composition_y_axis_title"
    )
    assert composition_y_axis_box["x0"] >= 0.0
    assert [item["manifold_method"] for item in layout_sidecar["metrics"]["atlas_manifold_panels"]] == ["umap", "phate"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F51"
    assert figure_entry["template_id"] == full_id("atlas_spatial_trajectory_multimanifold_context_support_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_atlas_spatial_trajectory_multimanifold_context_support_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_preserves_semantic_multimanifold_panel_labels(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
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
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "display_overrides.json",
        {
            "schema_version": 1,
            "displays": [
                {
                    "display_id": "Figure51",
                    "template_id": full_id("atlas_spatial_trajectory_multimanifold_context_support_panel"),
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    display_payload = _make_atlas_spatial_trajectory_multimanifold_context_support_panel_display()
    display_payload["atlas_manifold_panels"] = [
        {
            **dict(panel),
            "panel_label": semantic_label,
        }
        for panel, semantic_label in zip(
            list(display_payload["atlas_manifold_panels"]),
            ("UMAP", "PHATE"),
            strict=True,
        )
    ]
    dump_json(
        paper_root / "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
            "displays": [display_payload],
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
    assert [item["panel_label"] for item in layout_sidecar["metrics"]["atlas_manifold_panels"]] == [
        "UMAP",
        "PHATE",
    ]
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_multimanifold_context_support_when_manifold_methods_repeat(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_atlas_spatial_trajectory_multimanifold_context_support_panel_display()
    atlas_manifold_panels = list(display_payload["atlas_manifold_panels"])
    atlas_manifold_panels[1] = {**atlas_manifold_panels[1], "manifold_method": "umap"}
    display_payload["atlas_manifold_panels"] = atlas_manifold_panels
    dump_json(
        paper_root / "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec(
        "atlas_spatial_trajectory_multimanifold_context_support_panel"
    )

    with pytest.raises(ValueError, match="atlas_manifold_panels\\[1\\]\\.manifold_method must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure51",
        )

def test_materialize_display_surface_wraps_long_risk_layering_title_within_device(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "risk_layering",
                    "display_kind": "figure",
                    "requirement_key": "risk_layering_monotonic_bars",
                    "catalog_id": "F2",
                    "shell_path": "paper/figures/risk_layering.shell.json",
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
                    "display_id": "risk_layering",
                    "template_id": "risk_layering_monotonic_bars",
                    "title": (
                        "Clinical utility of the clinically informed preoperative model compared "
                        "with the core preoperative comparator"
                    ),
                    "caption": "Observed risk rises monotonically across score bands and grouped follow-up strata.",
                    "y_label": "Risk of later persistent global hypopituitarism (%)",
                    "left_panel_title": "Core preoperative comparator",
                    "left_x_label": "Predicted-risk tertile",
                    "left_bars": [
                        {"label": "Low", "cases": 118, "events": 5, "risk": 0.0423728813559322},
                        {"label": "Intermediate", "cases": 118, "events": 8, "risk": 0.06779661016949153},
                        {"label": "High", "cases": 118, "events": 44, "risk": 0.3728813559322034},
                    ],
                    "right_panel_title": "Clinically informed model",
                    "right_x_label": "Predicted-risk tertile",
                    "right_bars": [
                        {"label": "Low", "cases": 118, "events": 5, "risk": 0.0423728813559322},
                        {"label": "Intermediate", "cases": 118, "events": 10, "risk": 0.0847457627118644},
                        {"label": "High", "cases": 118, "events": 42, "risk": 0.3559322033898305},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["qc_result"]["status"] == "pass"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F2_risk_layering_monotonic_bars.layout.json").read_text(
            encoding="utf-8"
        )
    )
    title_box = next(item for item in layout_sidecar["layout_boxes"] if item["box_id"] == "title")
    assert 0.0 <= title_box["x0"] <= 1.0
    assert 0.0 <= title_box["x1"] <= 1.0

def test_materialize_display_surface_generates_binary_calibration_decision_curve_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "calibration_decision",
                    "display_kind": "figure",
                    "requirement_key": "binary_calibration_decision_curve_panel",
                    "catalog_id": "F3",
                    "shell_path": "paper/figures/calibration_decision.shell.json",
                }
            ],
        },
    )
    dump_json(paper_root / "figures" / "figure_catalog.json", {"schema_version": 1, "figures": []})
    dump_json(paper_root / "tables" / "table_catalog.json", {"schema_version": 1, "tables": []})
    write_default_publication_display_contracts(paper_root)
    dump_json(
        paper_root / "binary_calibration_decision_curve_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "binary_calibration_decision_curve_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "calibration_decision",
                    "template_id": "binary_calibration_decision_curve_panel",
                    "title": "Clinical coherence and coefficient stability of the clinically informed preoperative model",
                    "caption": "Calibration and decision-curve evidence across candidate packages.",
                    "calibration_x_label": "Mean predicted probability",
                    "calibration_y_label": "Observed probability",
                    "decision_x_label": "Threshold probability",
                    "decision_y_label": "Net benefit",
                    "calibration_axis_window": {"xmin": 0.0, "xmax": 0.5, "ymin": 0.0, "ymax": 0.35},
                    "calibration_reference_line": {"label": "Ideal", "x": [0.0, 1.0], "y": [0.0, 1.0]},
                    "calibration_series": [
                        {"label": "Core preoperative model", "x": [0.15, 0.25, 0.35, 0.45], "y": [0.04, 0.08, 0.16, 0.32]},
                        {
                            "label": "Clinically informed preoperative model",
                            "x": [0.05, 0.10, 0.18, 0.30],
                            "y": [0.03, 0.05, 0.14, 0.31],
                        },
                    ],
                    "decision_series": [
                        {
                            "label": "Core preoperative model",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.01, 0.0, -0.01, -0.005, -0.002],
                        },
                        {
                            "label": "Clinically informed preoperative model",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.06, 0.05, 0.04, 0.03, 0.02],
                        },
                    ],
                    "decision_reference_lines": [
                        {
                            "label": "Treat none",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.0, 0.0, 0.0, 0.0, 0.0],
                        },
                        {
                            "label": "Treat all",
                            "x": [0.15, 0.20, 0.25, 0.30, 0.35],
                            "y": [0.01, -0.03, -0.08, -0.14, -0.22],
                        },
                    ],
                    "decision_focus_window": {"xmin": 0.15, "xmax": 0.35},
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F3"]
    assert (paper_root / "figures" / "generated" / "F3_binary_calibration_decision_curve_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F3_binary_calibration_decision_curve_panel.pdf").exists()
    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["template_id"] == full_id("binary_calibration_decision_curve_panel")
    assert figure_entry["qc_result"]["status"] == "pass"
