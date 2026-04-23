from .shared import *

def test_load_evidence_display_payload_rejects_celltype_signature_heatmap_when_embedding_groups_and_columns_diverge(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
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
                    "caption": "Embedding groups must stay aligned with declared heatmap columns.",
                    "embedding_panel_title": "Embedding by cell type",
                    "embedding_x_label": "UMAP 1",
                    "embedding_y_label": "UMAP 2",
                    "embedding_points": [
                        {"x": -2.1, "y": 1.0, "group": "T cells"},
                        {"x": 1.4, "y": -0.6, "group": "Myeloid"},
                    ],
                    "heatmap_panel_title": "Signature activity",
                    "heatmap_x_label": "Cell type",
                    "heatmap_y_label": "Program",
                    "score_method": "AUCell",
                    "row_order": [{"label": "IFN response"}],
                    "column_order": [{"label": "T cells"}, {"label": "B cells"}],
                    "cells": [
                        {"x": "T cells", "y": "IFN response", "value": 0.78},
                        {"x": "B cells", "y": "IFN response", "value": -0.22},
                    ],
                }
            ],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("celltype_signature_heatmap")

    with pytest.raises(ValueError, match="column_order labels must match embedding point groups"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure26",
        )

def test_load_evidence_display_payload_rejects_grouped_risk_summary_when_events_exceed_sample_size(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    payload_path = paper_root / "time_to_event_grouped_inputs.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    display = next(item for item in payload["displays"] if item["display_id"] == "Figure15")
    display["risk_group_summaries"][1]["events_5y"] = display["risk_group_summaries"][1]["sample_size"] + 1
    dump_json(payload_path, payload)

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_risk_group_summary")

    with pytest.raises(ValueError, match="events_5y must not exceed \\.sample_size"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure15",
        )

def test_load_evidence_display_payload_rejects_time_to_event_calibration_when_events_exceed_group_size(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    payload_path = paper_root / "time_to_event_discrimination_calibration_inputs.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    display = next(item for item in payload["displays"] if item["display_id"] == "Figure14")
    display["calibration_summary"][0]["events_5y"] = display["calibration_summary"][0]["n"] + 1
    dump_json(payload_path, payload)

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")

    with pytest.raises(ValueError, match="events_5y must not exceed \\.n"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure14",
        )

def test_load_evidence_display_payload_rejects_time_to_event_calibration_when_callout_drifts_from_group_summary(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    payload_path = paper_root / "time_to_event_discrimination_calibration_inputs.json"
    payload = json.loads(payload_path.read_text(encoding="utf-8"))
    display = next(item for item in payload["displays"] if item["display_id"] == "Figure14")
    display["calibration_callout"]["predicted_risk_5y"] = 0.999
    dump_json(payload_path, payload)

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_discrimination_calibration_panel")

    with pytest.raises(ValueError, match="calibration_callout must match the referenced calibration_summary row"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure14",
        )

def test_materialize_display_surface_preserves_structured_time_horizon_metrics_for_b_templates(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = build_display_surface_workspace(tmp_path, include_extended_evidence=True)
    restrict_display_registry_to_display_ids(paper_root, "Figure16", "Figure18")

    grouped_payload = json.loads((paper_root / "time_to_event_decision_curve_inputs.json").read_text(encoding="utf-8"))
    decision_display = next(item for item in grouped_payload["displays"] if item["display_id"] == "Figure16")
    decision_display["time_horizon_months"] = 24
    dump_json(paper_root / "time_to_event_decision_curve_inputs.json", grouped_payload)

    curve_payload = json.loads((paper_root / "binary_prediction_curve_inputs.json").read_text(encoding="utf-8"))
    roc_display = next(item for item in curve_payload["displays"] if item["display_id"] == "Figure18")
    roc_display["time_horizon_months"] = 24
    dump_json(paper_root / "binary_prediction_curve_inputs.json", curve_payload)

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    f16_layout = json.loads(
        (paper_root / "figures" / "generated" / "F16_time_to_event_decision_curve.layout.json").read_text(
            encoding="utf-8"
        )
    )
    f18_layout = json.loads(
        (paper_root / "figures" / "generated" / "F18_time_dependent_roc_horizon.layout.json").read_text(
            encoding="utf-8"
        )
    )

    assert f16_layout["metrics"]["time_horizon_months"] == 24
    assert f18_layout["metrics"]["time_horizon_months"] == 24

def test_load_evidence_display_payload_rejects_non_monotonic_stratified_cumulative_incidence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_stratified_cumulative_incidence_display()
    display_payload["panels"][2]["groups"][4]["values"][3] = 0.08
    dump_json(
        paper_root / "time_to_event_stratified_cumulative_incidence_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_stratified_cumulative_incidence_panel")

    with pytest.raises(ValueError, match="values must be monotonic non-decreasing"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure24",
        )

def test_load_evidence_display_payload_rejects_duplicate_panel_labels_for_stratified_cumulative_incidence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_stratified_cumulative_incidence_display()
    display_payload["panels"][1]["panel_label"] = "A"
    dump_json(
        paper_root / "time_to_event_stratified_cumulative_incidence_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_stratified_cumulative_incidence_panel")

    with pytest.raises(ValueError, match="panel_label must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure24",
        )

def test_materialize_display_surface_generates_stratified_cumulative_incidence_panel(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure24",
                    "display_kind": "figure",
                    "requirement_key": "time_to_event_stratified_cumulative_incidence_panel",
                    "catalog_id": "F24",
                    "shell_path": "paper/figures/Figure24.shell.json",
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
                    "display_id": "Figure24",
                    "template_id": "time_to_event_stratified_cumulative_incidence_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_stratified_cumulative_incidence_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_stratified_cumulative_incidence_inputs_v1",
            "displays": [_make_stratified_cumulative_incidence_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F24"]
    assert (paper_root / "figures" / "generated" / "F24_time_to_event_stratified_cumulative_incidence_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F24_time_to_event_stratified_cumulative_incidence_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F24_time_to_event_stratified_cumulative_incidence_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["panel_label"] for item in layout_sidecar["metrics"]["panels"]] == ["A", "B", "C"]
    assert layout_sidecar["metrics"]["panels"][2]["groups"][-1]["label"] == "Q5"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F24"
    assert figure_entry["template_id"] == full_id("time_to_event_stratified_cumulative_incidence_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_stratified_cumulative_incidence_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_survival_curve"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_non_positive_panel_horizon_for_time_dependent_roc_comparison_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_dependent_roc_comparison_panel_display()
    display_payload["panels"][1]["time_horizon_months"] = 0
    dump_json(
        paper_root / "time_dependent_roc_comparison_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_dependent_roc_comparison_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_dependent_roc_comparison_panel")

    with pytest.raises(ValueError, match="time_horizon_months must be >= 1"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure25",
        )

def test_load_evidence_display_payload_rejects_mismatched_panel_series_labels_for_time_dependent_roc_comparison_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_dependent_roc_comparison_panel_display()
    display_payload["panels"][1]["series"][1]["label"] = "Alternative baseline"
    dump_json(
        paper_root / "time_dependent_roc_comparison_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_dependent_roc_comparison_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_dependent_roc_comparison_panel")

    with pytest.raises(ValueError, match="series labels must match the first panel"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure25",
        )

def test_materialize_display_surface_generates_time_dependent_roc_comparison_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "time_dependent_roc_comparison_panel",
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
                    "template_id": "time_dependent_roc_comparison_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_dependent_roc_comparison_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_dependent_roc_comparison_inputs_v1",
            "displays": [_make_time_dependent_roc_comparison_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F25"]
    assert (paper_root / "figures" / "generated" / "F25_time_dependent_roc_comparison_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F25_time_dependent_roc_comparison_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F25_time_dependent_roc_comparison_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert [item["panel_label"] for item in layout_sidecar["metrics"]["panels"]] == ["A", "B"]
    assert layout_sidecar["metrics"]["panels"][1]["time_horizon_months"] == 180
    assert layout_sidecar["metrics"]["panels"][1]["analysis_window_label"] == "First 15 years of follow-up"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F25"
    assert figure_entry["template_id"] == full_id("time_dependent_roc_comparison_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_dependent_roc_comparison_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_evidence_curve"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_non_forward_prediction_window_for_landmark_performance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_landmark_performance_panel_display()
    display_payload["landmark_summaries"][1]["prediction_months"] = 6
    dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_landmark_performance_panel")

    with pytest.raises(ValueError, match="prediction_months must exceed landmark_months"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure27",
        )

def test_load_evidence_display_payload_rejects_brier_out_of_range_for_landmark_performance_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_time_to_event_landmark_performance_panel_display()
    display_payload["landmark_summaries"][0]["brier_score"] = 1.2
    dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("time_to_event_landmark_performance_panel")

    with pytest.raises(ValueError, match="brier_score must stay within \\[0, 1\\]"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure27",
        )

def test_materialize_display_surface_generates_time_to_event_landmark_performance_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "time_to_event_landmark_performance_panel",
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
                    "template_id": "time_to_event_landmark_performance_panel",
                    "layout_override": {"show_figure_title": True},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "time_to_event_landmark_performance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "time_to_event_landmark_performance_inputs_v1",
            "displays": [_make_time_to_event_landmark_performance_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F27"]
    assert (paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F27_time_to_event_landmark_performance_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert [item["metric_kind"] for item in layout_sidecar["metrics"]["metric_panels"]] == [
        "c_index",
        "brier_score",
        "calibration_slope",
    ]
    assert layout_sidecar["metrics"]["metric_panels"][1]["rows"][0]["value"] == 0.18
    assert layout_sidecar["metrics"]["metric_panels"][2]["reference_value"] == 1.0

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F27"
    assert figure_entry["template_id"] == full_id("time_to_event_landmark_performance_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "time_to_event_landmark_performance_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_landmark_performance_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_duplicate_panel_feature_for_shap_dependence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_dependence_panel_display()
    display_payload["panels"][1]["feature"] = "Age"
    dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_dependence_panel")

    with pytest.raises(ValueError, match="feature must be unique"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure28",
        )

def test_load_evidence_display_payload_rejects_non_finite_point_value_for_shap_dependence_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_dependence_panel_display()
    display_payload["panels"][0]["points"][1]["interaction_value"] = float("nan")
    dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_dependence_panel")

    with pytest.raises(ValueError, match="point values must be finite"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure28",
        )

def test_materialize_display_surface_generates_shap_dependence_panel(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_dependence_panel",
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
                    "template_id": "shap_dependence_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [_make_shap_dependence_panel_display()],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    assert result["figures_materialized"] == ["F28"]
    assert (paper_root / "figures" / "generated" / "F28_shap_dependence_panel.png").exists()
    assert (paper_root / "figures" / "generated" / "F28_shap_dependence_panel.pdf").exists()
    layout_sidecar_path = paper_root / "figures" / "generated" / "F28_shap_dependence_panel.layout.json"
    assert layout_sidecar_path.exists()

    layout_sidecar = json.loads(layout_sidecar_path.read_text(encoding="utf-8"))
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([item for item in layout_sidecar["guide_boxes"] if item["box_type"] == "zero_line"]) == 2
    assert any(item["box_type"] == "colorbar" for item in layout_sidecar["guide_boxes"])
    assert layout_sidecar["metrics"]["colorbar_label"] == "Interaction feature value"
    assert [item["feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Age", "Platelet count"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    figure_entry = figure_catalog["figures"][0]
    assert figure_entry["figure_id"] == "F28"
    assert figure_entry["template_id"] == full_id("shap_dependence_panel")
    assert figure_entry["renderer_family"] == "python"
    assert figure_entry["input_schema_id"] == "shap_dependence_panel_inputs_v1"
    assert figure_entry["qc_profile"] == "publication_shap_dependence_panel"
    assert figure_entry["qc_result"]["status"] == "pass"

def test_load_evidence_display_payload_rejects_additive_mismatch_for_shap_waterfall_local_explanation_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_waterfall_local_explanation_panel_display()
    display_payload["panels"][0]["predicted_value"] = 0.5
    dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_waterfall_local_explanation_panel")

    with pytest.raises(ValueError, match="predicted_value must equal baseline_value plus contribution sum"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure33",
        )

def test_load_evidence_display_payload_rejects_zero_contribution_for_shap_waterfall_local_explanation_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_waterfall_local_explanation_panel_display()
    display_payload["panels"][1]["contributions"][1]["shap_value"] = 0.0
    dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_waterfall_local_explanation_panel")

    with pytest.raises(ValueError, match="contributions\\[1\\]\\.shap_value must be finite and non-zero"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure33",
        )

def test_load_evidence_display_payload_rejects_unsorted_force_like_contributions(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_force_like_summary_panel_display()
    display_payload["panels"][0]["contributions"] = [
        {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": -0.04},
        {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.13},
    ]
    dump_json(
        paper_root / "shap_force_like_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_force_like_summary_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_force_like_summary_panel")

    with pytest.raises(
        ValueError,
        match="contributions must be sorted by descending absolute shap_value within each panel",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure35",
        )

def test_load_evidence_display_payload_rejects_feature_order_mismatch_for_shap_grouped_local_explanation_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_grouped_local_explanation_panel_display()
    display_payload["panels"][1]["contributions"][0]["feature"] = "Albumin"
    display_payload["panels"][1]["contributions"][1]["feature"] = "Age"
    dump_json(
        paper_root / "shap_grouped_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_local_explanation_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_grouped_local_explanation_panel")

    with pytest.raises(ValueError, match="contribution feature order must match across panels"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure40",
        )

def test_load_evidence_display_payload_rejects_group_count_for_shap_grouped_decision_path_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_grouped_decision_path_panel_display()
    display_payload["groups"].append(
        {
            "group_id": "immune_excluded",
            "group_label": "Phenotype 3 · immune-excluded",
            "predicted_value": 0.27,
            "contributions": [
                {"rank": 1, "feature": "Age", "shap_value": 0.03},
                {"rank": 2, "feature": "Albumin", "shap_value": 0.01},
                {"rank": 3, "feature": "Tumor size", "shap_value": 0.04},
            ],
        }
    )
    dump_json(
        paper_root / "shap_grouped_decision_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_decision_path_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_grouped_decision_path_panel")

    with pytest.raises(ValueError, match="groups must contain exactly two entries"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure42",
        )

def test_load_evidence_display_payload_rejects_group_count_for_shap_multigroup_decision_path_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_shap_multigroup_decision_path_panel_display()
    display_payload["groups"].pop()
    dump_json(
        paper_root / "shap_multigroup_decision_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multigroup_decision_path_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("shap_multigroup_decision_path_panel")

    with pytest.raises(ValueError, match="groups must contain exactly three entries"):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure49",
        )

def test_load_evidence_display_payload_rejects_ice_curve_grid_mismatch_for_partial_dependence_ice_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_partial_dependence_ice_panel_display()
    display_payload["panels"][0]["ice_curves"][1]["x"] = [40.0, 52.0, 60.0, 70.0]
    dump_json(
        paper_root / "partial_dependence_ice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_ice_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("partial_dependence_ice_panel")

    with pytest.raises(
        ValueError,
        match="ice_curves\\[1\\]\\.x must match pdp_curve.x within each panel",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure36",
        )

def test_load_evidence_display_payload_rejects_slice_curve_grid_mismatch_for_partial_dependence_interaction_slice_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_partial_dependence_interaction_slice_panel_display()
    display_payload["panels"][0]["slice_curves"][1]["x"] = [40.0, 51.0, 60.0, 70.0]
    dump_json(
        paper_root / "partial_dependence_interaction_slice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_interaction_slice_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("partial_dependence_interaction_slice_panel")

    with pytest.raises(
        ValueError,
        match="slice_curves\\[1\\]\\.x must match the first slice x grid within each panel",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure43",
        )

def test_load_evidence_display_payload_rejects_invalid_interval_for_partial_dependence_subgroup_comparison_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_partial_dependence_subgroup_comparison_panel_display()
    display_payload["subgroup_rows"][1]["estimate"] = 0.35
    display_payload["subgroup_rows"][1]["upper"] = 0.28
    dump_json(
        paper_root / "partial_dependence_subgroup_comparison_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_subgroup_comparison_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("partial_dependence_subgroup_comparison_panel")

    with pytest.raises(
        ValueError,
        match="subgroup_rows\\[1\\] must satisfy lower <= estimate <= upper",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure44",
        )

def test_load_evidence_display_payload_rejects_non_cumulative_ale_for_accumulated_local_effects_panel(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    display_payload = _make_accumulated_local_effects_panel_display()
    display_payload["panels"][0]["ale_curve"]["y"][2] = 0.13
    dump_json(
        paper_root / "accumulated_local_effects_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "accumulated_local_effects_panel_inputs_v1",
            "displays": [display_payload],
        },
    )

    spec = module.display_registry.get_evidence_figure_spec("accumulated_local_effects_panel")

    with pytest.raises(
        ValueError,
        match="ale_curve.y must equal the cumulative sum of local_effect_bins within each panel",
    ):
        module._load_evidence_display_payload(
            paper_root=paper_root,
            spec=spec,
            display_id="Figure45",
        )
