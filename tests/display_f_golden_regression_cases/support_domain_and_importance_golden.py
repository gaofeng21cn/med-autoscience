from .shared import *

def test_shap_multigroup_decision_path_support_domain_panel_preserves_f_explanation_scene_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure51",
                    "template_id": "shap_multigroup_decision_path_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_multigroup_decision_path_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multigroup_decision_path_support_domain_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure51",
                    "template_id": "fenggaolab.org.medical-display-core::shap_multigroup_decision_path_support_domain_panel",
                    "title": "Multigroup decision path with support-domain follow-on for manuscript-facing explanation scenes",
                    "caption": "Regression lock for a higher-order decision-path plus support-domain explanation scene.",
                    "decision_panel_title": "Phenotype-level SHAP decision paths",
                    "decision_x_label": "Predicted risk contribution",
                    "decision_y_label": "Ordered feature path",
                    "decision_legend_title": "Phenotype",
                    "support_y_label": "Predicted response probability",
                    "support_legend_title": "Support domain",
                    "baseline_value": 0.19,
                    "groups": [
                        {
                            "group_id": "immune_inflamed",
                            "group_label": "Phenotype 1",
                            "predicted_value": 0.34,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": 0.10},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.03},
                                {"rank": 3, "feature": "Tumor size", "shap_value": 0.08},
                            ],
                        },
                        {
                            "group_id": "stromal_low",
                            "group_label": "Phenotype 2",
                            "predicted_value": 0.08,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": -0.04},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.02},
                                {"rank": 3, "feature": "Tumor size", "shap_value": -0.05},
                            ],
                        },
                        {
                            "group_id": "immune_excluded",
                            "group_label": "Phenotype 3",
                            "predicted_value": 0.21,
                            "contributions": [
                                {"rank": 1, "feature": "Age", "shap_value": 0.02},
                                {"rank": 2, "feature": "Albumin", "shap_value": -0.01},
                                {"rank": 3, "feature": "Tumor size", "shap_value": 0.01},
                            ],
                        },
                    ],
                    "support_panels": [
                        {
                            "panel_id": "age_support",
                            "panel_label": "C",
                            "title": "Age response support",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "response_curve": {"x": [40.0, 50.0, 60.0, 70.0, 80.0], "y": [0.18, 0.22, 0.29, 0.35, 0.41]},
                            "support_segments": [
                                {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 40.0, "domain_end": 50.0},
                                {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 50.0, "domain_end": 62.0},
                                {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 62.0, "domain_end": 72.0},
                                {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 72.0, "domain_end": 80.0},
                            ],
                        },
                        {
                            "panel_id": "albumin_support",
                            "panel_label": "D",
                            "title": "Albumin response support",
                            "x_label": "Albumin (g/dL)",
                            "feature": "Albumin",
                            "reference_value": 3.8,
                            "reference_label": "Median albumin",
                            "response_curve": {
                                "x": [2.8, 3.2, 3.6, 4.0, 4.4, 4.6],
                                "y": [0.39, 0.33, 0.28, 0.23, 0.19, 0.17],
                            },
                            "support_segments": [
                                {"segment_id": "alb_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 2.8, "domain_end": 3.2},
                                {"segment_id": "alb_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 3.2, "domain_end": 3.8},
                                {"segment_id": "alb_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 3.8, "domain_end": 4.2},
                                {"segment_id": "alb_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 4.2, "domain_end": 4.6},
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
            / "F51_shap_multigroup_decision_path_support_domain_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert len(layout_sidecar["panel_boxes"]) == 3
    assert layout_sidecar["metrics"]["decision_panel"]["feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert layout_sidecar["metrics"]["decision_panel"]["groups"][0]["group_id"] == "immune_inflamed"
    assert layout_sidecar["metrics"]["support_legend_labels"] == [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["support_panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["support_panels"][1]["support_segments"][-1]["support_kind"] == "extrapolation_warning"
    assert any(box["box_id"] == "legend_box" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "support_legend_box" for box in layout_sidecar["layout_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_signed_importance_local_support_domain_panel_preserves_f_explanation_scene_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure52",
                    "template_id": "shap_signed_importance_local_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_signed_importance_local_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_local_support_domain_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure52",
                    "template_id": "fenggaolab.org.medical-display-core::shap_signed_importance_local_support_domain_panel",
                    "title": "Global signed importance with local waterfall and support-domain follow-on for manuscript-facing explanation scenes",
                    "caption": "Regression lock for a single-case explanation scene anchored by global polarity and matched support-domain evidence.",
                    "support_y_label": "Predicted response probability",
                    "support_legend_title": "Support domain",
                    "importance_panel": {
                        "panel_id": "global_signed_importance",
                        "panel_label": "A",
                        "title": "Directional global importance",
                        "x_label": "Mean signed SHAP value",
                        "negative_label": "Protective direction",
                        "positive_label": "Risk direction",
                        "bars": [
                            {"rank": 1, "feature": "Albumin", "signed_importance_value": -0.118},
                            {"rank": 2, "feature": "Age", "signed_importance_value": 0.104},
                            {"rank": 3, "feature": "Tumor size", "signed_importance_value": 0.081},
                            {"rank": 4, "feature": "Platelet count", "signed_importance_value": -0.064},
                        ],
                    },
                    "local_panel": {
                        "panel_id": "representative_case",
                        "panel_label": "B",
                        "title": "Representative high-risk case",
                        "case_label": "Case 1 · 1-year mortality",
                        "x_label": "Predicted 1-year mortality probability",
                        "baseline_value": 0.18,
                        "predicted_value": 0.39,
                        "contributions": [
                            {"feature": "Albumin", "feature_value_text": "3.1 g/dL", "shap_value": 0.08},
                            {"feature": "Age", "feature_value_text": "74 years", "shap_value": 0.12},
                            {"feature": "Tumor size", "feature_value_text": "9.4 cm", "shap_value": 0.04},
                            {"feature": "Platelet count", "feature_value_text": "210 ×10^9/L", "shap_value": -0.03},
                        ],
                    },
                    "support_panels": [
                        {
                            "panel_id": "albumin_support",
                            "panel_label": "C",
                            "title": "Albumin response support",
                            "x_label": "Albumin (g/dL)",
                            "feature": "Albumin",
                            "reference_value": 3.8,
                            "reference_label": "Median albumin",
                            "response_curve": {
                                "x": [2.8, 3.2, 3.6, 4.0, 4.4, 4.6],
                                "y": [0.39, 0.33, 0.28, 0.23, 0.19, 0.17],
                            },
                            "support_segments": [
                                {"segment_id": "alb_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 2.8, "domain_end": 3.2},
                                {"segment_id": "alb_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 3.2, "domain_end": 3.8},
                                {"segment_id": "alb_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 3.8, "domain_end": 4.2},
                                {"segment_id": "alb_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 4.2, "domain_end": 4.6},
                            ],
                        },
                        {
                            "panel_id": "age_support",
                            "panel_label": "D",
                            "title": "Age response support",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "response_curve": {"x": [40.0, 50.0, 60.0, 70.0, 80.0], "y": [0.18, 0.22, 0.29, 0.35, 0.41]},
                            "support_segments": [
                                {"segment_id": "age_observed", "segment_label": "Observed", "support_kind": "observed_support", "domain_start": 40.0, "domain_end": 50.0},
                                {"segment_id": "age_subgroup", "segment_label": "Subgroup", "support_kind": "subgroup_support", "domain_start": 50.0, "domain_end": 62.0},
                                {"segment_id": "age_bin", "segment_label": "Bin", "support_kind": "bin_support", "domain_start": 62.0, "domain_end": 72.0},
                                {"segment_id": "age_extrapolation", "segment_label": "Extrapolation", "support_kind": "extrapolation_warning", "domain_start": 72.0, "domain_end": 80.0},
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
            / "F52_shap_signed_importance_local_support_domain_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert len(layout_sidecar["panel_boxes"]) == 4
    assert layout_sidecar["metrics"]["global_feature_order"] == ["Albumin", "Age", "Tumor size", "Platelet count"]
    assert layout_sidecar["metrics"]["support_legend_labels"] == [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    assert [item["feature"] for item in layout_sidecar["metrics"]["support_panels"]] == ["Albumin", "Age"]
    assert layout_sidecar["metrics"]["local_panel"]["contributions"][-1]["end_value"] == 0.39
    assert layout_sidecar["metrics"]["support_panels"][0]["support_segments"][1]["support_kind"] == "subgroup_support"
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_D" for box in layout_sidecar["layout_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_bar_importance_preserves_f_global_importance_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
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
                    "requirement_key": "shap_bar_importance",
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
                    "template_id": "shap_bar_importance",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_bar_importance_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_bar_importance_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure37",
                    "template_id": "fenggaolab.org.medical-display-core::shap_bar_importance",
                    "title": "SHAP bar importance panel for audited global feature ranking",
                    "caption": "Regression lock for manuscript-facing global SHAP importance ranking.",
                    "x_label": "Mean absolute SHAP value",
                    "bars": [
                        {"rank": 1, "feature": "Age", "importance_value": 0.184},
                        {"rank": 2, "feature": "Albumin", "importance_value": 0.133},
                        {"rank": 3, "feature": "Tumor size", "importance_value": 0.096},
                        {"rank": 4, "feature": "Platelet count", "importance_value": 0.071},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F37_shap_bar_importance.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 1
    assert [item["feature"] for item in layout_sidecar["metrics"]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert [item["rank"] for item in layout_sidecar["metrics"]["bars"]] == [1, 2, 3, 4]
    assert layout_sidecar["metrics"]["bars"][0]["importance_value"] > layout_sidecar["metrics"]["bars"][1]["importance_value"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["template_id"] == "fenggaolab.org.medical-display-core::shap_bar_importance"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_signed_importance_panel_preserves_f_directional_global_importance_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
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
                    "requirement_key": "shap_signed_importance_panel",
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
                    "template_id": "shap_signed_importance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_signed_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_signed_importance_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure38",
                    "template_id": "fenggaolab.org.medical-display-core::shap_signed_importance_panel",
                    "title": "SHAP signed importance panel for audited directional feature influence",
                    "caption": "Regression lock for manuscript-facing signed SHAP global importance ranking.",
                    "x_label": "Mean signed SHAP value",
                    "negative_label": "Protective direction",
                    "positive_label": "Risk direction",
                    "bars": [
                        {"rank": 1, "feature": "Albumin", "signed_importance_value": -0.118},
                        {"rank": 2, "feature": "Age", "signed_importance_value": 0.104},
                        {"rank": 3, "feature": "Tumor size", "signed_importance_value": 0.081},
                        {"rank": 4, "feature": "Platelet count", "signed_importance_value": -0.064},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (paper_root / "figures" / "generated" / "F38_shap_signed_importance_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 1
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
    assert layout_sidecar["metrics"]["bars"][0]["signed_importance_value"] < 0.0
    assert layout_sidecar["metrics"]["bars"][1]["signed_importance_value"] > 0.0
    assert any(item["box_type"] == "zero_line" for item in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["template_id"] == "fenggaolab.org.medical-display-core::shap_signed_importance_panel"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"

def test_shap_multicohort_importance_panel_preserves_f_cross_cohort_global_importance_contract(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
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
                    "requirement_key": "shap_multicohort_importance_panel",
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
                    "template_id": "shap_multicohort_importance_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_multicohort_importance_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_multicohort_importance_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure39",
                    "template_id": "fenggaolab.org.medical-display-core::shap_multicohort_importance_panel",
                    "title": "SHAP multicohort importance panel for audited cross-cohort feature ranking",
                    "caption": "Regression lock for manuscript-facing cross-cohort SHAP global importance comparison.",
                    "x_label": "Mean absolute SHAP value",
                    "panels": [
                        {
                            "panel_id": "derivation",
                            "panel_label": "A",
                            "title": "Derivation cohort",
                            "cohort_label": "Derivation",
                            "bars": [
                                {"rank": 1, "feature": "Age", "importance_value": 0.184},
                                {"rank": 2, "feature": "Albumin", "importance_value": 0.133},
                                {"rank": 3, "feature": "Tumor size", "importance_value": 0.096},
                                {"rank": 4, "feature": "Platelet count", "importance_value": 0.071},
                            ],
                        },
                        {
                            "panel_id": "validation",
                            "panel_label": "B",
                            "title": "External validation cohort",
                            "cohort_label": "Validation",
                            "bars": [
                                {"rank": 1, "feature": "Age", "importance_value": 0.171},
                                {"rank": 2, "feature": "Albumin", "importance_value": 0.121},
                                {"rank": 3, "feature": "Tumor size", "importance_value": 0.089},
                                {"rank": 4, "feature": "Platelet count", "importance_value": 0.067},
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
        (paper_root / "figures" / "generated" / "F39_shap_multicohort_importance_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert [panel["panel_label"] for panel in layout_sidecar["metrics"]["panels"]] == ["A", "B"]
    assert [panel["cohort_label"] for panel in layout_sidecar["metrics"]["panels"]] == [
        "Derivation",
        "Validation",
    ]
    assert [bar["feature"] for bar in layout_sidecar["metrics"]["panels"][0]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert [bar["feature"] for bar in layout_sidecar["metrics"]["panels"][1]["bars"]] == [
        "Age",
        "Albumin",
        "Tumor size",
        "Platelet count",
    ]
    assert (
        layout_sidecar["metrics"]["panels"][0]["bars"][0]["importance_value"]
        > layout_sidecar["metrics"]["panels"][0]["bars"][1]["importance_value"]
    )
    assert (
        layout_sidecar["metrics"]["panels"][1]["bars"][0]["importance_value"]
        > layout_sidecar["metrics"]["panels"][1]["bars"][1]["importance_value"]
    )

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["template_id"] == "fenggaolab.org.medical-display-core::shap_multicohort_importance_panel"
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
