from .shared import *

def test_materialize_display_surface_generates_broader_heterogeneity_summary_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "broader_heterogeneity_summary_panel",
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
                    "template_id": "broader_heterogeneity_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "broader_heterogeneity_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "broader_heterogeneity_summary_panel_inputs_v1",
            "displays": [_make_broader_heterogeneity_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F49"]
    assert (paper_root / "figures" / "generated" / "F49_broader_heterogeneity_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F49_broader_heterogeneity_summary_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F49_broader_heterogeneity_summary_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert layout_sidecar["metrics"]["reference_value"] == 1.0
    assert [item["slice_label"] for item in layout_sidecar["metrics"]["slices"]] == [
        "Overall cohort",
        "Prespecified subgroup",
        "Adjusted model",
    ]
    assert [item["row_id"] for item in layout_sidecar["metrics"]["effect_rows"]] == [
        "age_ge_65",
        "female",
        "high_risk",
    ]
    assert [item["verdict"] for item in layout_sidecar["metrics"]["effect_rows"]] == [
        "stable",
        "attenuated",
        "context_dependent",
    ]
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "reference_line" for item in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F49"
    assert figure_entry["template_id"] == full_id("broader_heterogeneity_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "broader_heterogeneity_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_broader_heterogeneity_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_interaction_effect_summary_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "interaction_effect_summary_panel",
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
                    "template_id": "interaction_effect_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "interaction_effect_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "interaction_effect_summary_panel_inputs_v1",
            "displays": [_make_interaction_effect_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F51"]
    assert (paper_root / "figures" / "generated" / "F51_interaction_effect_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F51_interaction_effect_summary_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F51_interaction_effect_summary_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert layout_sidecar["metrics"]["reference_value"] == 0.0
    assert [item["modifier_id"] for item in layout_sidecar["metrics"]["modifiers"]] == [
        "age_ge_65",
        "female",
        "high_risk",
    ]
    assert [item["verdict"] for item in layout_sidecar["metrics"]["modifiers"]] == [
        "credible",
        "suggestive",
        "credible",
    ]
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "reference_line" for item in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F51"
    assert figure_entry["template_id"] == full_id("interaction_effect_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "interaction_effect_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_interaction_effect_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_materialize_display_surface_generates_center_transportability_governance_summary_panel(
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
                    "display_id": "Figure50",
                    "display_kind": "figure",
                    "requirement_key": "center_transportability_governance_summary_panel",
                    "catalog_id": "F50",
                    "shell_path": "paper/figures/Figure50.shell.json",
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
                    "display_id": "Figure50",
                    "template_id": "center_transportability_governance_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "center_transportability_governance_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "center_transportability_governance_summary_panel_inputs_v1",
            "displays": [_make_center_transportability_governance_summary_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F50"]
    assert (paper_root / "figures" / "generated" / "F50_center_transportability_governance_summary_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F50_center_transportability_governance_summary_panel.pdf").exists()
    layout_sidecar_path = (
        paper_root / "figures" / "generated" / "F50_center_transportability_governance_summary_panel.layout.json"
    )
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert layout_sidecar["metrics"]["metric_family"] == "discrimination"
    assert layout_sidecar["metrics"]["metric_reference_value"] == 0.80
    assert layout_sidecar["metrics"]["batch_shift_threshold"] == 0.20
    assert [item["center_id"] for item in layout_sidecar["metrics"]["centers"]] == [
        "train_a",
        "validation_c",
        "external_b",
    ]
    assert [item["verdict"] for item in layout_sidecar["metrics"]["centers"]] == [
        "stable",
        "stable",
        "context_dependent",
    ]
    assert any(item["box_id"] == "panel_label_A" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_id"] == "panel_label_B" for item in layout_sidecar["layout_boxes"])
    assert any(item["box_type"] == "reference_line" for item in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F50"
    assert figure_entry["template_id"] == full_id("center_transportability_governance_summary_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "center_transportability_governance_summary_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_center_transportability_governance_summary_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_duplicate_threshold_label_for_threshold_governance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_threshold_governance_panel_display()
    display_payload["threshold_summaries"][1]["threshold_label"] = "Rule-in"
    dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_threshold_governance_panel")

    with pytest.raises(ValueError, match="threshold_label must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure29",
        )

def test_load_evidence_display_payload_rejects_invalid_risk_probability_for_threshold_governance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_threshold_governance_panel_display()
    display_payload["risk_group_summaries"][1]["observed_risk"] = 1.4
    dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_threshold_governance_panel")

    with pytest.raises(ValueError, match="observed_risk"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure29",
        )

def test_materialize_display_surface_generates_time_to_event_threshold_governance_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "time_to_event_threshold_governance_panel",
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
                    "template_id": "time_to_event_threshold_governance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_threshold_governance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_threshold_governance_inputs_v1",
            "displays": [_make_time_to_event_threshold_governance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F29"]
    assert (paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F29_time_to_event_threshold_governance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([item for item in layout_sidecar["layout_boxes"] if item["box_type"] == "threshold_card"]) == 2
    assert any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
    assert [item["threshold"] for item in layout_sidecar["metrics"]["threshold_summaries"]] == [0.10, 0.15]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["risk_group_summaries"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F29"
    assert figure_entry["template_id"] == full_id("time_to_event_threshold_governance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_threshold_governance_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_time_to_event_threshold_governance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_non_positive_panel_horizon_for_multihorizon_calibration_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_multihorizon_calibration_panel_display()
    display_payload["panels"][0]["time_horizon_months"] = 0
    dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_multihorizon_calibration_panel")

    with pytest.raises(ValueError, match="time_horizon_months"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure30",
        )

def test_load_evidence_display_payload_rejects_non_increasing_group_order_for_multihorizon_calibration_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_multihorizon_calibration_panel_display()
    display_payload["panels"][0]["calibration_summary"][1]["group_order"] = 1
    dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_multihorizon_calibration_panel")

    with pytest.raises(ValueError, match="group_order must be strictly increasing"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure30",
        )

def test_materialize_display_surface_generates_time_to_event_multihorizon_calibration_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure30",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_multihorizon_calibration_panel",
                    "catalog_id": "F30",
                    "shell_path": "paper/figures/Figure30.shell.json",
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
                    "display_id": "Figure30",
                    "template_id": "time_to_event_multihorizon_calibration_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_multihorizon_calibration_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_multihorizon_calibration_inputs_v1",
            "displays": [_make_time_to_event_multihorizon_calibration_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F30"]
    assert (paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F30_time_to_event_multihorizon_calibration_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert all(item["box_type"] == "calibration_panel" for item in layout_sidecar["panel_boxes"])
    assert any(item["box_type"] == "legend" for item in layout_sidecar["guide_boxes"])
    assert [item["time_horizon_months"] for item in layout_sidecar["metrics"]["panels"]] == [36, 60]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["panels"][1]["calibration_summary"]] == [
        "Low risk",
        "Intermediate risk",
        "High risk",
    ]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F30"
    assert figure_entry["template_id"] == full_id("time_to_event_multihorizon_calibration_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_multihorizon_calibration_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_time_to_event_multihorizon_calibration_panel"
    assert figure_entry["qc_result"]["status"] == "pass"
