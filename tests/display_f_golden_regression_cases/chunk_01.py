from .shared import *

def test_shap_dependence_panel_preserves_f_local_explanation_contract(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_dependence_panel",
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
                    "template_id": "shap_dependence_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_dependence_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_dependence_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure28",
                    "template_id": "fenggaolab.org.medical-display-core::shap_dependence_panel",
                    "title": "SHAP dependence panel for representative nonlinear feature effects",
                    "caption": "Composite regression lock for manuscript-facing local dependence explanations.",
                    "y_label": "SHAP value",
                    "colorbar_label": "Interaction feature value",
                    "panels": [
                        {
                            "panel_id": "age_panel",
                            "panel_label": "A",
                            "title": "Age",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "interaction_feature": "Albumin",
                            "points": [
                                {"feature_value": 38.0, "shap_value": -0.22, "interaction_value": 3.1},
                                {"feature_value": 55.0, "shap_value": 0.04, "interaction_value": 4.2},
                                {"feature_value": 71.0, "shap_value": 0.31, "interaction_value": 4.8},
                            ],
                        },
                        {
                            "panel_id": "platelet_panel",
                            "panel_label": "B",
                            "title": "Platelet count",
                            "x_label": "Platelets (10^9/L)",
                            "feature": "Platelet count",
                            "interaction_feature": "Age",
                            "points": [
                                {"feature_value": 85.0, "shap_value": 0.28, "interaction_value": 72.0},
                                {"feature_value": 142.0, "shap_value": 0.02, "interaction_value": 59.0},
                                {"feature_value": 210.0, "shap_value": -0.19, "interaction_value": 44.0},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F28_shap_dependence_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "zero_line"]) == 2
    assert any(box["box_type"] == "colorbar" for box in layout_sidecar["guide_boxes"])
    assert layout_sidecar["metrics"]["colorbar_label"] == "Interaction feature value"
    assert [item["interaction_feature"] for item in layout_sidecar["metrics"]["panels"]] == ["Albumin", "Age"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_waterfall_local_explanation_panel_preserves_f_patient_level_contract(tmp_path: Path) -> None:
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
                    "requirement_key": "shap_waterfall_local_explanation_panel",
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
                    "template_id": "shap_waterfall_local_explanation_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_waterfall_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_waterfall_local_explanation_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure33",
                    "template_id": "fenggaolab.org.medical-display-core::shap_waterfall_local_explanation_panel",
                    "title": "SHAP waterfall panel for representative patient-level risk calls",
                    "caption": "Regression lock for ordered patient-level additive explanation paths.",
                    "x_label": "Predicted 1-year mortality probability",
                    "panels": [
                        {
                            "panel_id": "case_a",
                            "panel_label": "A",
                            "title": "Representative high-risk case",
                            "case_label": "Case 1 · 1-year mortality",
                            "baseline_value": 0.18,
                            "predicted_value": 0.39,
                            "contributions": [
                                {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.12},
                                {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": 0.08},
                                {"feature": "Platelets", "feature_value_text": "210 ×10^9/L", "shap_value": -0.03},
                                {"feature": "Tumor size", "feature_value_text": "9.4 cm", "shap_value": 0.04},
                            ],
                        },
                        {
                            "panel_id": "case_b",
                            "panel_label": "B",
                            "title": "Representative lower-risk case",
                            "case_label": "Case 2 · 1-year mortality",
                            "baseline_value": 0.42,
                            "predicted_value": 0.28,
                            "contributions": [
                                {"feature": "Age", "feature_value_text": "49 years", "shap_value": -0.11},
                                {"feature": "Albumin", "feature_value_text": "4.5 g/dL", "shap_value": -0.07},
                                {"feature": "Tumor stage", "feature_value_text": "Stage II", "shap_value": 0.04},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F33_shap_waterfall_local_explanation_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert not any(box["box_type"] == "title" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "baseline_marker"]) == 2
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "prediction_marker"]) == 2
    assert [item["case_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Case 1 · 1-year mortality",
        "Case 2 · 1-year mortality",
    ]
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["start_value"] == 0.18
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][-1]["end_value"] == 0.39
    assert layout_sidecar["metrics"]["panels"][1]["contributions"][0]["shap_value"] == -0.11

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_force_like_summary_panel_preserves_f_force_like_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
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
                    "requirement_key": "shap_force_like_summary_panel",
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
                    "template_id": "shap_force_like_summary_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_force_like_summary_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_force_like_summary_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure35",
                    "template_id": "fenggaolab.org.medical-display-core::shap_force_like_summary_panel",
                    "title": "SHAP force-like summary panel for representative response phenotypes",
                    "caption": "Regression lock for manuscript-facing force-like local explanation lanes.",
                    "x_label": "Predicted response probability",
                    "panels": [
                        {
                            "panel_id": "case_a",
                            "panel_label": "A",
                            "title": "Representative responder",
                            "case_label": "Case 1 · durable response",
                            "baseline_value": 0.22,
                            "predicted_value": 0.31,
                            "contributions": [
                                {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.13},
                                {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": -0.04},
                            ],
                        },
                        {
                            "panel_id": "case_b",
                            "panel_label": "B",
                            "title": "Representative non-responder",
                            "case_label": "Case 2 · early progression",
                            "baseline_value": 0.57,
                            "predicted_value": 0.48,
                            "contributions": [
                                {"feature": "Tumor stage", "feature_value_text": "Stage III", "shap_value": -0.18},
                                {"feature": "Albumin", "feature_value_text": "4.6 g/dL", "shap_value": 0.09},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F35_shap_force_like_summary_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert not any(box["box_type"] == "title" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "baseline_marker"]) == 2
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "prediction_marker"]) == 2
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][0]["direction"] == "positive"
    assert layout_sidecar["metrics"]["panels"][0]["contributions"][1]["direction"] == "negative"
    assert layout_sidecar["metrics"]["panels"][1]["contributions"][0]["direction"] == "negative"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_grouped_local_explanation_panel_preserves_f_grouped_local_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure40",
                    "template_id": "shap_grouped_local_explanation_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_grouped_local_explanation_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_local_explanation_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure40",
                    "template_id": "fenggaolab.org.medical-display-core::shap_grouped_local_explanation_panel",
                    "title": "SHAP grouped local explanation panel for phenotype-level comparison",
                    "caption": "Regression lock for grouped manuscript-facing local explanation comparison.",
                    "x_label": "Local SHAP contribution to predicted risk",
                    "panels": [
                        {
                            "panel_id": "high_risk",
                            "panel_label": "A",
                            "title": "High-risk phenotype",
                            "group_label": "Phenotype 1 · immune-inflamed",
                            "baseline_value": 0.22,
                            "predicted_value": 0.34,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": 0.14},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.05},
                                {"rank": 3, "feature": "Tumor size", "shap_value": 0.03},
                            ],
                        },
                        {
                            "panel_id": "low_risk",
                            "panel_label": "B",
                            "title": "Lower-risk phenotype",
                            "group_label": "Phenotype 2 · stromal-low",
                            "baseline_value": 0.18,
                            "predicted_value": 0.12,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": -0.07},
                                {"rank": 2, "feature": "Albumin", "shap_value": 0.02},
                                {"rank": 3, "feature": "Tumor size", "shap_value": -0.01},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F40_shap_grouped_local_explanation_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "zero_line"]) == 2
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
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_grouped_decision_path_panel_preserves_f_grouped_decision_path_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure42",
                    "template_id": "shap_grouped_decision_path_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_grouped_decision_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_decision_path_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure42",
                    "template_id": "fenggaolab.org.medical-display-core::shap_grouped_decision_path_panel",
                    "title": "SHAP grouped decision path panel for phenotype-level local explanation contrast",
                    "caption": "Regression lock for grouped manuscript-facing decision-path explanations.",
                    "panel_title": "Decision-path comparison across representative phenotypes",
                    "x_label": "Cumulative model output",
                    "y_label": "Ordered feature contributions",
                    "legend_title": "Phenotype",
                    "baseline_value": 0.19,
                    "groups": [
                        {
                            "group_id": "immune_inflamed",
                            "group_label": "Phenotype 1 · immune-inflamed",
                            "predicted_value": 0.34,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": 0.10},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.03},
                                {"rank": 3, "feature": "Tumor size", "shap_value": 0.08},
                            ],
                        },
                        {
                            "group_id": "stromal_low",
                            "group_label": "Phenotype 2 · stromal-low",
                            "predicted_value": 0.08,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": -0.04},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.02},
                                {"rank": 3, "feature": "Tumor size", "shap_value": -0.05},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F42_shap_grouped_decision_path_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(box["box_type"] == "legend_box" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "legend_title" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "baseline_reference_line"]) == 1
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "prediction_marker"]) == 2
    assert layout_sidecar["metrics"]["feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["groups"]] == [
        "Phenotype 1 · immune-inflamed",
        "Phenotype 2 · stromal-low",
    ]
    assert layout_sidecar["metrics"]["groups"][0]["contributions"][0]["start_value"] == 0.19
    assert layout_sidecar["metrics"]["groups"][0]["contributions"][-1]["end_value"] == 0.34
    assert layout_sidecar["metrics"]["groups"][1]["contributions"][-1]["end_value"] == 0.08

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_multigroup_decision_path_panel_preserves_f_multigroup_decision_path_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
        },
    )
    _dump_json(
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
    _dump_json(
        paper_root / "shap_multigroup_decision_path_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multigroup_decision_path_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure49",
                    "template_id": "fenggaolab.org.medical-display-core::shap_multigroup_decision_path_panel",
                    "title": "SHAP multigroup decision path panel for phenotype-level local explanation contrast",
                    "caption": "Regression lock for multigroup manuscript-facing decision-path explanations.",
                    "panel_title": "Decision-path comparison across representative phenotypes",
                    "x_label": "Cumulative model output",
                    "y_label": "Ordered feature contributions",
                    "legend_title": "Phenotype",
                    "baseline_value": 0.19,
                    "groups": [
                        {
                            "group_id": "immune_inflamed",
                            "group_label": "Phenotype 1 · immune-inflamed",
                            "predicted_value": 0.34,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": 0.10},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.03},
                                {"rank": 3, "feature": "Tumor size", "shap_value": 0.08},
                            ],
                        },
                        {
                            "group_id": "stromal_low",
                            "group_label": "Phenotype 2 · stromal-low",
                            "predicted_value": 0.08,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": -0.04},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.02},
                                {"rank": 3, "feature": "Tumor size", "shap_value": -0.05},
                            ],
                        },
                        {
                            "group_id": "immune_excluded",
                            "group_label": "Phenotype 3 · immune-excluded",
                            "predicted_value": 0.21,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": 0.02},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.01},
                                {"rank": 3, "feature": "Tumor size", "shap_value": 0.01},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F49_shap_multigroup_decision_path_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert any(box["box_type"] == "legend_box" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "legend_title" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "baseline_reference_line"]) == 1
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "prediction_marker"]) == 3
    assert layout_sidecar["metrics"]["feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert [item["group_label"] for item in layout_sidecar["metrics"]["groups"]] == [
        "Phenotype 1 · immune-inflamed",
        "Phenotype 2 · stromal-low",
        "Phenotype 3 · immune-excluded",
    ]
    assert layout_sidecar["metrics"]["groups"][0]["contributions"][0]["start_value"] == 0.19
    assert layout_sidecar["metrics"]["groups"][0]["contributions"][-1]["end_value"] == 0.34
    assert layout_sidecar["metrics"]["groups"][1]["contributions"][-1]["end_value"] == 0.08
    assert layout_sidecar["metrics"]["groups"][2]["contributions"][-1]["end_value"] == 0.21

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_partial_dependence_interaction_contour_panel_preserves_f_pairwise_interaction_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure41",
                    "template_id": "partial_dependence_interaction_contour_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "partial_dependence_interaction_contour_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_interaction_contour_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure41",
                    "template_id": "fenggaolab.org.medical-display-core::partial_dependence_interaction_contour_panel",
                    "title": "Partial dependence interaction contour panel for joint feature-response surfaces",
                    "caption": "Regression lock for manuscript-facing bounded pairwise partial dependence interactions.",
                    "colorbar_label": "Predicted response probability",
                    "panels": [
                        {
                            "panel_id": "age_albumin",
                            "panel_label": "A",
                            "title": "Age x Albumin",
                            "x_label": "Age (years)",
                            "y_label": "Albumin (g/dL)",
                            "x_feature": "Age",
                            "y_feature": "Albumin",
                            "reference_x_value": 60.0,
                            "reference_y_value": 3.8,
                            "reference_label": "Median profile",
                            "x_grid": [40.0, 50.0, 60.0, 70.0],
                            "y_grid": [2.8, 3.4, 4.0, 4.6],
                            "response_grid": [
                                [0.44, 0.37, 0.31, 0.27],
                                [0.35, 0.29, 0.24, 0.20],
                                [0.28, 0.23, 0.19, 0.16],
                                [0.24, 0.20, 0.17, 0.14],
                            ],
                            "observed_points": [
                                {"point_id": "case_1", "x": 43.0, "y": 3.0},
                                {"point_id": "case_2", "x": 51.0, "y": 3.5},
                                {"point_id": "case_3", "x": 60.0, "y": 3.8},
                                {"point_id": "case_4", "x": 67.0, "y": 4.2},
                            ],
                        },
                        {
                            "panel_id": "tumor_platelet",
                            "panel_label": "B",
                            "title": "Tumor size x Platelets",
                            "x_label": "Tumor size (cm)",
                            "y_label": "Platelets (10^9/L)",
                            "x_feature": "Tumor size",
                            "y_feature": "Platelet count",
                            "reference_x_value": 6.0,
                            "reference_y_value": 160.0,
                            "reference_label": "Reference profile",
                            "x_grid": [2.0, 4.0, 6.0, 8.0],
                            "y_grid": [80.0, 120.0, 160.0, 200.0],
                            "response_grid": [
                                [0.18, 0.21, 0.25, 0.29],
                                [0.22, 0.27, 0.31, 0.36],
                                [0.27, 0.33, 0.39, 0.45],
                                [0.31, 0.38, 0.45, 0.52],
                            ],
                            "observed_points": [
                                {"point_id": "case_5", "x": 2.6, "y": 92.0},
                                {"point_id": "case_6", "x": 4.8, "y": 138.0},
                                {"point_id": "case_7", "x": 6.1, "y": 164.0},
                                {"point_id": "case_8", "x": 7.5, "y": 188.0},
                            ],
                        },
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root
            / "figures"
            / "generated"
            / "F41_partial_dependence_interaction_contour_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "colorbar" for box in layout_sidecar["guide_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "interaction_reference_vertical"]) == 2
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "interaction_reference_horizontal"]) == 2
    assert layout_sidecar["metrics"]["colorbar_label"] == "Predicted response probability"
    assert [item["reference_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Median profile",
        "Reference profile",
    ]
    assert layout_sidecar["metrics"]["panels"][0]["response_grid"][0][0] == 0.44
    assert layout_sidecar["metrics"]["panels"][1]["observed_points"][-1]["point_id"] == "case_8"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
