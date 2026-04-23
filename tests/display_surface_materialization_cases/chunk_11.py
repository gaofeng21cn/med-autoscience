from .shared import *

def test_materialize_display_surface_generates_feature_response_support_domain_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure47",
                    "display_kind": "figure",
                    "requirement_key": "feature_response_support_domain_panel",
                    "catalog_id": "F47",
                    "shell_path": "paper/figures/Figure47.shell.json",
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
                    "display_id": "Figure47",
                    "template_id": "feature_response_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "feature_response_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "feature_response_support_domain_panel_inputs_v1",
            "displays": [_make_feature_response_support_domain_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F47"]
    assert (paper_root / "figures" / "generated" / "F47_feature_response_support_domain_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F47_feature_response_support_domain_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F47_feature_response_support_domain_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_type"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "support_domain_segment"]) == 8
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "support_domain_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["panels"][0]["support_segments"][-1]["support_kind"] == "extrapolation_warning"
    assert layout_sidecar["metrics"]["panels"][1]["support_segments"][2]["segment_label"] == "Bin"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F47"
    assert figure_entry["template_id"] == full_id("feature_response_support_domain_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "feature_response_support_domain_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_feature_response_support_domain_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_support_feature_order_drift_for_shap_multigroup_decision_path_support_domain_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_multigroup_decision_path_support_domain_panel_display()
    display_payload["support_panels"] = [
        display_payload["support_panels"][1],
        display_payload["support_panels"][0],
    ]
    dump_json(
        paper_root / "shap_multigroup_decision_path_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multigroup_decision_path_support_domain_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_multigroup_decision_path_support_domain_panel")

    with pytest.raises(ValueError, match="support_panels.feature order must follow the shared group feature order"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure51",
        )

def test_materialize_display_surface_generates_shap_multigroup_decision_path_support_domain_panel(
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
                    "requirement_key": "shap_multigroup_decision_path_support_domain_panel",
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
                    "template_id": "shap_multigroup_decision_path_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_multigroup_decision_path_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multigroup_decision_path_support_domain_panel_inputs_v1",
            "displays": [_make_shap_multigroup_decision_path_support_domain_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F51"]
    assert (
        paper_root / "figures" / "generated" / "F51_shap_multigroup_decision_path_support_domain_panel.png"
    ).exists()
    assert (
        paper_root / "figures" / "generated" / "F51_shap_multigroup_decision_path_support_domain_panel.pdf"
    ).exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F51_shap_multigroup_decision_path_support_domain_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert any(item["box_id"] == "legend_box" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "support_legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "prediction_marker"]) == 3
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "support_domain_segment"]) == 8
    assert layout_sidecar["metrics"]["decision_panel"]["legend_title"] == "Phenotype"
    assert layout_sidecar["metrics"]["decision_panel"]["feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert layout_sidecar["metrics"]["support_legend_labels"] == [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["support_panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["support_panels"][0]["support_segments"][2]["support_kind"] == "bin_support"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F51"
    assert figure_entry["template_id"] == full_id("shap_multigroup_decision_path_support_domain_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_multigroup_decision_path_support_domain_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_multigroup_decision_path_support_domain_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_local_feature_order_drift_for_shap_signed_importance_local_support_domain_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_signed_importance_local_support_domain_panel_display()
    display_payload["local_panel"]["contributions"] = [
        display_payload["local_panel"]["contributions"][1],
        display_payload["local_panel"]["contributions"][0],
        *display_payload["local_panel"]["contributions"][2:],
    ]
    dump_json(
        paper_root / "shap_signed_importance_local_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_local_support_domain_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_signed_importance_local_support_domain_panel")

    with pytest.raises(
        ValueError,
        match="local_panel.contributions.feature order must follow the global signed-importance feature order",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure52",
        )

def test_materialize_display_surface_generates_shap_signed_importance_local_support_domain_panel(
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
                    "display_id": "Figure52",
                    "display_kind": "figure",
                    "requirement_key": "shap_signed_importance_local_support_domain_panel",
                    "catalog_id": "F52",
                    "shell_path": "paper/figures/Figure52.shell.json",
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
                    "display_id": "Figure52",
                    "template_id": "shap_signed_importance_local_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_signed_importance_local_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_local_support_domain_panel_inputs_v1",
            "displays": [_make_shap_signed_importance_local_support_domain_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F52"]
    assert (
        paper_root / "figures" / "generated" / "F52_shap_signed_importance_local_support_domain_panel.png"
    ).exists()
    assert (
        paper_root / "figures" / "generated" / "F52_shap_signed_importance_local_support_domain_panel.pdf"
    ).exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F52_shap_signed_importance_local_support_domain_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 4
    assert any(item["box_id"] == "negative_direction_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "support_legend_box" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "support_domain_segment"]) == 8
    assert layout_sidecar["metrics"]["global_feature_order"] == ["Albumin", "Age", "Tumor size", "Platelet count"]
    assert layout_sidecar["metrics"]["local_feature_order"] == ["Albumin", "Age", "Tumor size", "Platelet count"]
    assert layout_sidecar["metrics"]["importance_panel"]["bars"][0]["direction"] == "negative"
    assert layout_sidecar["metrics"]["local_panel"]["contributions"][-1]["end_value"] == 0.39
    assert [item["feature"] for item in layout_sidecar["metrics"]["support_panels"]] == ["Albumin", "Age"]
    assert layout_sidecar["metrics"]["support_panels"][1]["support_segments"][2]["support_kind"] == "bin_support"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F52"
    assert figure_entry["template_id"] == full_id("shap_signed_importance_local_support_domain_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_signed_importance_local_support_domain_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_signed_importance_local_support_domain_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_duplicate_feature_for_shap_bar_importance(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_bar_importance_display()
    display_payload["bars"][2]["feature"] = "Albumin"
    dump_json(
        paper_root / "shap_bar_importance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_bar_importance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_bar_importance")

    with pytest.raises(ValueError, match="feature must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure37",
        )

def test_load_evidence_display_payload_rejects_zero_signed_importance_for_shap_signed_importance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_signed_importance_panel_display()
    display_payload["bars"][2]["signed_importance_value"] = 0.0
    dump_json(
        paper_root / "shap_signed_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_signed_importance_panel")

    with pytest.raises(ValueError, match="signed_importance_value must be finite and non-zero"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure38",
        )

def test_load_evidence_display_payload_rejects_feature_order_mismatch_for_shap_multicohort_importance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_multicohort_importance_panel_display()
    display_payload["panels"][1]["bars"][1]["feature"] = "Platelet count"
    display_payload["panels"][1]["bars"][3]["feature"] = "Albumin"
    dump_json(
        paper_root / "shap_multicohort_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multicohort_importance_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_multicohort_importance_panel")

    with pytest.raises(ValueError, match="bars feature order must match across panels"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure39",
        )

def test_materialize_display_surface_generates_shap_bar_importance(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_bar_importance",
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
                    "template_id": "shap_bar_importance",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_bar_importance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_bar_importance_inputs_v1",
            "displays": [_make_shap_bar_importance_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F37"]
    assert (paper_root / "figures" / "generated" / "F37_shap_bar_importance.png").exists()
    assert (paper_root / "figures" / "generated" / "F37_shap_bar_importance.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F37_shap_bar_importance.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(item["box_type"] == "importance_bar" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "feature_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "value_label" for item in layout_sidecar["layout_boxes"])
    assert [item["feature"] for item in layout_sidecar["metrics"]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert layout_sidecar["metrics"]["bars"][0]["importance_value"] == 0.184

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F37"
    assert figure_entry["template_id"] == full_id("shap_bar_importance")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_bar_importance_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_bar_importance"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_shap_signed_importance_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_signed_importance_panel",
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
                    "template_id": "shap_signed_importance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_signed_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_panel_inputs_v1",
            "displays": [_make_shap_signed_importance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F38"]
    assert (paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(item["box_type"] == "importance_bar" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "negative_direction_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "positive_direction_label" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "zero_line" for item in layout_sidecar["guide_boxes"])
    assert [item["feature"] for item in layout_sidecar["metrics"]["bars"]] == [
        "Albumin",
        "Age",
        "Tumor size",
        "Platelet count",
    ]
    assert [item["direction"] for item in layout_sidecar["metrics"]["bars"]] == [
        "negative",
        "positive",
        "positive",
        "negative",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F38"
    assert figure_entry["template_id"] == full_id("shap_signed_importance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_signed_importance_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_signed_importance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_shap_multicohort_importance_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_multicohort_importance_panel",
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
                    "template_id": "shap_multicohort_importance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_multicohort_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multicohort_importance_panel_inputs_v1",
            "displays": [_make_shap_multicohort_importance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F39"]
    assert (paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert [item["cohort_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Derivation",
        "Validation",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][0]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"][1]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F39"
    assert figure_entry["template_id"] == full_id("shap_multicohort_importance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_multicohort_importance_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_multicohort_importance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_generalizability_subgroup_composite_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "generalizability_subgroup_composite_panel",
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
                    "template_id": "generalizability_subgroup_composite_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "generalizability_subgroup_composite_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "generalizability_subgroup_composite_inputs_v1",
            "displays": [_make_generalizability_subgroup_composite_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F34"]
    assert (paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F34_generalizability_subgroup_composite_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
    assert layout_sidecar["metrics"]["metric_family"] == "discrimination"
    assert layout_sidecar["metrics"]["primary_label"] == "Locked model"
    assert layout_sidecar["metrics"]["comparator_label"] == "Derivation cohort"
    assert [item["cohort_label"] for item in layout_sidecar["metrics"]["overview_rows"]] == [
        "External A",
        "External B",
        "Temporal",
    ]
    assert layout_sidecar["metrics"]["subgroup_reference_value"] == 0.80
    assert layout_sidecar["metrics"]["subgroup_rows"][0]["subgroup_label"] == "Age ≥65 years"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F34"
    assert figure_entry["template_id"] == full_id("generalizability_subgroup_composite_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "generalizability_subgroup_composite_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_generalizability_subgroup_composite_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_compact_effect_estimate_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure46",
                    "display_kind": "figure",
                    "requirement_key": "compact_effect_estimate_panel",
                    "catalog_id": "F46",
                    "shell_path": "paper/figures/Figure46.shell.json",
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
                    "display_id": "Figure46",
                    "template_id": "compact_effect_estimate_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "compact_effect_estimate_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "compact_effect_estimate_panel_inputs_v1",
            "displays": [_make_compact_effect_estimate_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F46"]
    assert (paper_root / "figures" / "generated" / "F46_compact_effect_estimate_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F46_compact_effect_estimate_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F46_compact_effect_estimate_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_C" for item in layout_sidecar["layout_boxes"])
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "reference_line"]) == 3
    assert layout_sidecar["metrics"]["reference_value"] == 1.0
    assert [item["panel_id"] for item in layout_sidecar["metrics"]["panels"]] == [
        "overall",
        "adjusted",
        "sensitivity",
    ]
    assert [item["row_id"] for item in layout_sidecar["metrics"]["panels"][0]["rows"]] == [
        "age_ge_65",
        "female",
        "high_risk",
    ]
    assert [item["row_id"] for item in layout_sidecar["metrics"]["panels"][1]["rows"]] == [
        "age_ge_65",
        "female",
        "high_risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F46"
    assert figure_entry["template_id"] == full_id("compact_effect_estimate_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "compact_effect_estimate_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_compact_effect_estimate_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_coefficient_path_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure48",
                    "display_kind": "figure",
                    "requirement_key": "coefficient_path_panel",
                    "catalog_id": "F48",
                    "shell_path": "paper/figures/Figure48.shell.json",
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
                    "display_id": "Figure48",
                    "template_id": "coefficient_path_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "coefficient_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "coefficient_path_panel_inputs_v1",
            "displays": [_make_coefficient_path_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F48"]
    assert (paper_root / "figures" / "generated" / "F48_coefficient_path_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F48_coefficient_path_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F48_coefficient_path_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "reference_line" for item in layout_sidecar["guide_boxes"])
    assert layout_sidecar["metrics"]["reference_value"] == 0.0
    assert [item["step_label"] for item in layout_sidecar["metrics"]["steps"]] == [
        "Unadjusted",
        "Adjusted",
        "Sensitivity",
    ]
    assert [item["row_id"] for item in layout_sidecar["metrics"]["coefficient_rows"]] == [
        "age_ge_65",
        "female",
        "high_risk",
    ]
    assert [item["card_id"] for item in layout_sidecar["metrics"]["summary_cards"]] == [
        "age",
        "female",
        "high_risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F48"
    assert figure_entry["template_id"] == full_id("coefficient_path_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "coefficient_path_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_coefficient_path_panel"
    assert figure_entry["qc_result"]["status"] == "pass"
