from .shared import *

def test_load_evidence_display_payload_rejects_partial_comparator_metrics_for_generalizability_subgroup_composite_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_generalizability_subgroup_composite_panel_display()
    del display_payload["overview_rows"][1]["comparator_metric_value"]
    dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("generalizability_subgroup_composite_panel")

    with pytest.raises(
        ValueError,
        match="comparator_metric_value must be provided for every overview row when comparator_label is declared",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure34",
        )

def test_load_evidence_display_payload_rejects_row_order_mismatch_for_compact_effect_estimate_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_compact_effect_estimate_panel_display()
    display_payload["panels"][1]["rows"][0]["row_id"] = "female"
    display_payload["panels"][1]["rows"][0]["row_label"] = "Female"
    display_payload["panels"][1]["rows"][1]["row_id"] = "age_ge_65"
    display_payload["panels"][1]["rows"][1]["row_label"] = "Age ≥65 years"
    dump_json(
        paper_root / "compact_effect_estimate_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "compact_effect_estimate_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("compact_effect_estimate_panel")

    with pytest.raises(
        ValueError,
        match="rows must appear in the same row_id and row_label order across panels",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure46",
        )

def test_load_evidence_display_payload_rejects_missing_step_coverage_for_coefficient_path_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_coefficient_path_panel_display()
    display_payload["coefficient_rows"][1]["points"].pop()
    dump_json(
        paper_root / "coefficient_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "coefficient_path_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("coefficient_path_panel")

    with pytest.raises(
        ValueError,
        match="points must cover every declared step_id exactly once within each coefficient row",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure48",
        )

def test_load_evidence_display_payload_rejects_invalid_interaction_p_value_for_interaction_effect_summary_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_interaction_effect_summary_panel_display()
    display_payload["modifiers"][1]["interaction_p_value"] = 1.4
    dump_json(
        paper_root / "interaction_effect_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "interaction_effect_summary_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("interaction_effect_summary_panel")

    with pytest.raises(
        ValueError,
        match="interaction_p_value must be between 0.0 and 1.0",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure51",
        )

def test_materialize_display_surface_generates_shap_waterfall_local_explanation_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_waterfall_local_explanation_panel",
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
                    "template_id": "shap_waterfall_local_explanation_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [_make_shap_waterfall_local_explanation_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F33"]
    assert (paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "baseline_marker"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "prediction_marker"]) == 2
    assert [item["case_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Case 1 · 1-year mortality",
        "Case 2 · 1-year mortality",
    ]
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["feature"] == "Age"
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["feature_value_text"] == "74 years"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F33"
    assert figure_entry["template_id"] == full_id("shap_waterfall_local_explanation_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_waterfall_local_explanation_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_waterfall_local_explanation_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_shap_force_like_summary_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_force_like_summary_panel",
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
                    "template_id": "shap_force_like_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_force_like_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_force_like_summary_panel_inputs_v1",
            "displays": [_make_shap_force_like_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F35"]
    assert (paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "baseline_marker"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "prediction_marker"]) == 2
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["direction"] == "positive"
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][1]["direction"] == "negative"
    assert layout_sidecar["metrics"]["panels"][1]["contributions"][0]["feature"] == "Tumor stage"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F35"
    assert figure_entry["template_id"] == full_id("shap_force_like_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_force_like_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_force_like_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_shap_grouped_local_explanation_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_grouped_local_explanation_panel",
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
                    "template_id": "shap_grouped_local_explanation_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_grouped_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_local_explanation_panel_inputs_v1",
            "displays": [_make_shap_grouped_local_explanation_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F40"]
    assert (paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "zero_line"]) == 2
    assert [item["group_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Phenotype 1 · immune-inflamed",
        "Phenotype 2 · stromal-low",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][0]["contributions"]] == [
        "Age",
        "Albumin",
        "Tumor size",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][1]["contributions"]] == [
        "Age",
        "Albumin",
        "Tumor size",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F40"
    assert figure_entry["template_id"] == full_id("shap_grouped_local_explanation_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_grouped_local_explanation_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_grouped_local_explanation_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_shap_grouped_decision_path_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure42",
                    "display_kind": "figure",
                    "requirement_key": "shap_grouped_decision_path_panel",
                    "catalog_id": "F42",
                    "shell_path": "paper/figures/Figure42.shell.json",
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
                    "display_id": "Figure42",
                    "template_id": "shap_grouped_decision_path_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_grouped_decision_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_decision_path_panel_inputs_v1",
            "displays": [_make_shap_grouped_decision_path_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F42"]
    assert (paper_root / "figures" / "generated" / "F42_shap_grouped_decision_path_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F42_shap_grouped_decision_path_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F42_shap_grouped_decision_path_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert not any(item["box_type"] == "title" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "baseline_reference_line"]) == 1
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "prediction_marker"]) == 2
    assert layout_sidecar["metrics"]["baseline_value"] == 0.19
    assert layout_sidecar["metrics"]["feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["groups"]] == [
        "Phenotype 1 · immune-inflamed",
        "Phenotype 2 · stromal-low",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F42"
    assert figure_entry["template_id"] == full_id("shap_grouped_decision_path_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_grouped_decision_path_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_grouped_decision_path_panel"

def test_materialize_display_surface_generates_shap_multigroup_decision_path_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure49",
                    "display_kind": "figure",
                    "requirement_key": "shap_multigroup_decision_path_panel",
                    "catalog_id": "F49",
                    "shell_path": "paper/figures/Figure49.shell.json",
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
                    "display_id": "Figure49",
                    "template_id": "shap_multigroup_decision_path_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_multigroup_decision_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multigroup_decision_path_panel_inputs_v1",
            "displays": [_make_shap_multigroup_decision_path_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert (paper_root / "figures" / "generated" / "F49_shap_multigroup_decision_path_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F49_shap_multigroup_decision_path_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F49_shap_multigroup_decision_path_panel.layout.json"
    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(box["box_type"] == "legend_box" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "prediction_marker"]) == 3
    assert layout_sidecar["metrics"]["feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["groups"]] == [
        "Phenotype 1 · immune-inflamed",
        "Phenotype 2 · stromal-low",
        "Phenotype 3 · immune-excluded",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["template_id"] == full_id("shap_multigroup_decision_path_panel")
    assert figure_entry["input_schema_id"] == "shap_multigroup_decision_path_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_multigroup_decision_path_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_partial_dependence_ice_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "partial_dependence_ice_panel",
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
                    "template_id": "partial_dependence_ice_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "partial_dependence_ice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_ice_panel_inputs_v1",
            "displays": [_make_partial_dependence_ice_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F36"]
    assert (paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_type"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "pdp_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == ["ICE curves", "PDP mean"]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["panels"][0]["reference_label"] == "Median age"
    assert len(layout_sidecar["metrics"]["panels"][0]["ice_curves"]) == 3

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F36"
    assert figure_entry["template_id"] == full_id("partial_dependence_ice_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "partial_dependence_ice_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_partial_dependence_ice_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_partial_dependence_interaction_contour_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "partial_dependence_interaction_contour_panel",
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
                    "template_id": "partial_dependence_interaction_contour_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "partial_dependence_interaction_contour_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_interaction_contour_panel_inputs_v1",
            "displays": [_make_partial_dependence_interaction_contour_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F41"]
    assert (paper_root / "figures" / "generated" / "F41_partial_dependence_interaction_contour_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F41_partial_dependence_interaction_contour_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F41_partial_dependence_interaction_contour_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_type"] == "colorbar" for item in layout_sidecar["guide_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "interaction_reference_vertical"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "interaction_reference_horizontal"]) == 2
    assert layout_sidecar["metrics"]["colorbar_label"] == "Predicted response probability"
    assert [item["x_feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Tumor size"]
    assert layout_sidecar["metrics"]["panels"][0]["observed_points"][0]["point_id"] == "case_1"
    assert layout_sidecar["metrics"]["panels"][1]["response_grid"][3][3] == 0.52

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F41"
    assert figure_entry["template_id"] == full_id("partial_dependence_interaction_contour_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "partial_dependence_interaction_contour_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_partial_dependence_interaction_contour_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_partial_dependence_interaction_slice_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure43",
                    "display_kind": "figure",
                    "requirement_key": "partial_dependence_interaction_slice_panel",
                    "catalog_id": "F43",
                    "shell_path": "paper/figures/Figure43.shell.json",
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
                    "display_id": "Figure43",
                    "template_id": "partial_dependence_interaction_slice_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "partial_dependence_interaction_slice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_interaction_slice_panel_inputs_v1",
            "displays": [_make_partial_dependence_interaction_slice_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F43"]
    assert (paper_root / "figures" / "generated" / "F43_partial_dependence_interaction_slice_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F43_partial_dependence_interaction_slice_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F43_partial_dependence_interaction_slice_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_type"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "legend_title" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "slice_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_title"] == "Conditioning profile"
    assert layout_sidecar["metrics"]["legend_labels"] == ["Low conditioning", "High conditioning"]
    assert [item["slice_feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Albumin", "Platelet count"]
    assert layout_sidecar["metrics"]["panels"][0]["slice_curves"][0]["slice_id"] == "albumin_low"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F43"
    assert figure_entry["template_id"] == full_id("partial_dependence_interaction_slice_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "partial_dependence_interaction_slice_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_partial_dependence_interaction_slice_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_partial_dependence_subgroup_comparison_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure44",
                    "display_kind": "figure",
                    "requirement_key": "partial_dependence_subgroup_comparison_panel",
                    "catalog_id": "F44",
                    "shell_path": "paper/figures/Figure44.shell.json",
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
                    "display_id": "Figure44",
                    "template_id": "partial_dependence_subgroup_comparison_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "partial_dependence_subgroup_comparison_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_subgroup_comparison_panel_inputs_v1",
            "displays": [_make_partial_dependence_subgroup_comparison_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F44"]
    assert (paper_root / "figures" / "generated" / "F44_partial_dependence_subgroup_comparison_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F44_partial_dependence_subgroup_comparison_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F44_partial_dependence_subgroup_comparison_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len([item for item in layout_sidecar["panel_boxes"] if item["box_type"] == "panel"]) == 2
    assert len([item for item in layout_sidecar["panel_boxes"] if item["box_type"] == "subgroup_panel"]) == 1
    assert any(item["box_id"] == "panel_label_C" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "subgroup_ci_segment"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "subgroup_estimate_marker"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == ["ICE curves", "PDP mean", "Subgroup interval"]
    assert layout_sidecar["metrics"]["subgroup_panel"]["panel_label"] == "C"
    assert layout_sidecar["metrics"]["subgroup_panel"]["rows"][0]["panel_id"] == "immune_high"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F44"
    assert figure_entry["template_id"] == full_id("partial_dependence_subgroup_comparison_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "partial_dependence_subgroup_comparison_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_partial_dependence_subgroup_comparison_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_accumulated_local_effects_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure45",
                    "display_kind": "figure",
                    "requirement_key": "accumulated_local_effects_panel",
                    "catalog_id": "F45",
                    "shell_path": "paper/figures/Figure45.shell.json",
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
                    "display_id": "Figure45",
                    "template_id": "accumulated_local_effects_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "accumulated_local_effects_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "accumulated_local_effects_panel_inputs_v1",
            "displays": [_make_accumulated_local_effects_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F45"]
    assert (paper_root / "figures" / "generated" / "F45_accumulated_local_effects_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F45_accumulated_local_effects_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F45_accumulated_local_effects_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_type"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "ale_reference_line"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "local_effect_bin"]) == 8
    assert layout_sidecar["metrics"]["legend_labels"] == ["Accumulated local effect", "Local effect per bin"]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["panels"][0]["local_effect_bins"][1]["bin_id"] == "age_bin_2"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F45"
    assert figure_entry["template_id"] == full_id("accumulated_local_effects_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "accumulated_local_effects_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_accumulated_local_effects_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_support_domain_gap_for_feature_response_support_domain_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_feature_response_support_domain_panel_display()
    display_payload["panels"][0]["support_segments"][1]["domain_start"] = 51.0
    dump_json(
        paper_root / "feature_response_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "feature_response_support_domain_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("feature_response_support_domain_panel")

    with pytest.raises(ValueError, match="support_segments must cover the full response_curve.x range without gaps"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure47",
        )
