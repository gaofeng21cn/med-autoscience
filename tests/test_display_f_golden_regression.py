from __future__ import annotations

import importlib
import json
from pathlib import Path


def _dump_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


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


def test_partial_dependence_ice_panel_preserves_f_pdp_ice_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
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
                    "requirement_key": "partial_dependence_ice_panel",
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
                    "template_id": "partial_dependence_ice_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "partial_dependence_ice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_ice_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure36",
                    "template_id": "fenggaolab.org.medical-display-core::partial_dependence_ice_panel",
                    "title": "Partial dependence and ICE panel for representative feature-response trajectories",
                    "caption": "Regression lock for manuscript-facing bounded PDP and ICE explanation overlays.",
                    "y_label": "Predicted response probability",
                    "panels": [
                        {
                            "panel_id": "age_panel",
                            "panel_label": "A",
                            "title": "Age",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.16, 0.21, 0.27, 0.34]},
                            "ice_curves": [
                                {"curve_id": "age_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.14, 0.19, 0.25, 0.33]},
                                {"curve_id": "age_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.17, 0.22, 0.29, 0.36]},
                                {"curve_id": "age_case_3", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.18, 0.23, 0.28, 0.35]},
                            ],
                        },
                        {
                            "panel_id": "albumin_panel",
                            "panel_label": "B",
                            "title": "Albumin",
                            "x_label": "Albumin (g/dL)",
                            "feature": "Albumin",
                            "reference_value": 3.8,
                            "reference_label": "Median albumin",
                            "pdp_curve": {"x": [2.8, 3.4, 4.0, 4.6], "y": [0.39, 0.31, 0.25, 0.20]},
                            "ice_curves": [
                                {"curve_id": "alb_case_1", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.41, 0.33, 0.26, 0.21]},
                                {"curve_id": "alb_case_2", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.37, 0.30, 0.24, 0.18]},
                                {"curve_id": "alb_case_3", "x": [2.8, 3.4, 4.0, 4.6], "y": [0.40, 0.32, 0.27, 0.22]},
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
        (paper_root / "figures" / "generated" / "F36_partial_dependence_ice_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_id"] == "panel_label_A" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_id"] == "panel_label_B" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "legend_box" for box in layout_sidecar["layout_boxes"])
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "pdp_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == ["ICE curves", "PDP mean"]
    assert [item["reference_label"] for item in layout_sidecar["metrics"]["panels"]] == [
        "Median age",
        "Median albumin",
    ]
    assert layout_sidecar["metrics"]["panels"][0]["pdp_points"][0]["feature_value"] == 40.0
    assert layout_sidecar["metrics"]["panels"][1]["ice_curves"][0]["curve_id"] == "alb_case_1"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_partial_dependence_interaction_slice_panel_preserves_f_slice_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure43",
                    "template_id": "partial_dependence_interaction_slice_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "partial_dependence_interaction_slice_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_interaction_slice_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure43",
                    "template_id": "fenggaolab.org.medical-display-core::partial_dependence_interaction_slice_panel",
                    "title": "Partial dependence interaction slice panel for clinically bounded conditioning profiles",
                    "caption": "Regression lock for manuscript-facing interaction slices over fixed conditioning profiles.",
                    "y_label": "Predicted response probability",
                    "legend_title": "Conditioning profile",
                    "panels": [
                        {
                            "panel_id": "age_by_albumin",
                            "panel_label": "A",
                            "title": "Age conditioned on albumin",
                            "x_label": "Age (years)",
                            "x_feature": "Age",
                            "slice_feature": "Albumin",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "slice_curves": [
                                {"slice_id": "albumin_low", "slice_label": "Low conditioning", "conditioning_value": 3.2, "x": [40.0, 50.0, 60.0, 70.0], "y": [0.24, 0.28, 0.33, 0.39]},
                                {"slice_id": "albumin_high", "slice_label": "High conditioning", "conditioning_value": 4.4, "x": [40.0, 50.0, 60.0, 70.0], "y": [0.15, 0.19, 0.24, 0.30]},
                            ],
                        },
                        {
                            "panel_id": "tumor_by_platelet",
                            "panel_label": "B",
                            "title": "Tumor size conditioned on platelets",
                            "x_label": "Tumor size (cm)",
                            "x_feature": "Tumor size",
                            "slice_feature": "Platelet count",
                            "reference_value": 6.0,
                            "reference_label": "Reference tumor size",
                            "slice_curves": [
                                {"slice_id": "platelet_low", "slice_label": "Low conditioning", "conditioning_value": 110.0, "x": [2.0, 4.0, 6.0, 8.0], "y": [0.20, 0.27, 0.36, 0.47]},
                                {"slice_id": "platelet_high", "slice_label": "High conditioning", "conditioning_value": 210.0, "x": [2.0, 4.0, 6.0, 8.0], "y": [0.13, 0.19, 0.27, 0.35]},
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
            paper_root / "figures" / "generated" / "F43_partial_dependence_interaction_slice_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert any(box["box_type"] == "legend_box" for box in layout_sidecar["layout_boxes"])
    assert any(box["box_type"] == "legend_title" for box in layout_sidecar["layout_boxes"])
    assert layout_sidecar["metrics"]["legend_title"] == "Conditioning profile"
    assert layout_sidecar["metrics"]["legend_labels"] == ["Low conditioning", "High conditioning"]
    assert layout_sidecar["metrics"]["panels"][0]["slice_curves"][0]["slice_id"] == "albumin_low"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_partial_dependence_subgroup_comparison_panel_preserves_f_subgroup_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure44",
                    "template_id": "partial_dependence_subgroup_comparison_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "partial_dependence_subgroup_comparison_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "partial_dependence_subgroup_comparison_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure44",
                    "template_id": "fenggaolab.org.medical-display-core::partial_dependence_subgroup_comparison_panel",
                    "title": "Partial dependence subgroup comparison panel for audited sensitivity heterogeneity",
                    "caption": "Regression lock for bounded subgroup-specific PDP/ICE plus interval summary.",
                    "y_label": "Predicted response probability",
                    "subgroup_panel_label": "C",
                    "subgroup_panel_title": "Subgroup-level absolute risk contrast",
                    "subgroup_x_label": "Mean predicted risk difference",
                    "panels": [
                        {
                            "panel_id": "immune_high",
                            "panel_label": "A",
                            "subgroup_label": "Immune-high",
                            "title": "Immune-high subgroup",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.18, 0.24, 0.31, 0.39]},
                            "ice_curves": [
                                {"curve_id": "immune_high_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.16, 0.22, 0.30, 0.40]},
                                {"curve_id": "immune_high_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.19, 0.25, 0.33, 0.41]},
                            ],
                        },
                        {
                            "panel_id": "immune_low",
                            "panel_label": "B",
                            "subgroup_label": "Immune-low",
                            "title": "Immune-low subgroup",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "pdp_curve": {"x": [40.0, 50.0, 60.0, 70.0], "y": [0.13, 0.17, 0.22, 0.28]},
                            "ice_curves": [
                                {"curve_id": "immune_low_case_1", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.12, 0.16, 0.21, 0.27]},
                                {"curve_id": "immune_low_case_2", "x": [40.0, 50.0, 60.0, 70.0], "y": [0.14, 0.18, 0.23, 0.29]},
                            ],
                        },
                    ],
                    "subgroup_rows": [
                        {"row_id": "immune_high_row", "panel_id": "immune_high", "row_label": "Immune-high", "estimate": 0.31, "lower": 0.24, "upper": 0.38, "support_n": 142},
                        {"row_id": "immune_low_row", "panel_id": "immune_low", "row_label": "Immune-low", "estimate": 0.22, "lower": 0.16, "upper": 0.28, "support_n": 151},
                    ],
                }
            ],
        },
    )

    result = module.materialize_display_surface(paper_root=paper_root)

    assert result["status"] == "materialized"
    layout_sidecar = json.loads(
        (
            paper_root / "figures" / "generated" / "F44_partial_dependence_subgroup_comparison_panel.layout.json"
        ).read_text(encoding="utf-8")
    )
    assert len([box for box in layout_sidecar["panel_boxes"] if box["box_type"] == "panel"]) == 2
    assert len([box for box in layout_sidecar["panel_boxes"] if box["box_type"] == "subgroup_panel"]) == 1
    assert layout_sidecar["metrics"]["legend_labels"] == ["ICE curves", "PDP mean", "Subgroup interval"]
    assert layout_sidecar["metrics"]["subgroup_panel"]["panel_label"] == "C"
    assert layout_sidecar["metrics"]["subgroup_panel"]["rows"][1]["panel_id"] == "immune_low"

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_accumulated_local_effects_panel_preserves_f_ale_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure45",
                    "template_id": "accumulated_local_effects_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "accumulated_local_effects_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "accumulated_local_effects_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure45",
                    "template_id": "fenggaolab.org.medical-display-core::accumulated_local_effects_panel",
                    "title": "Accumulated local effects panel for bounded feature-response accumulation",
                    "caption": "Regression lock for manuscript-facing accumulated local-effect explanation panels.",
                    "y_label": "Accumulated local effect",
                    "panels": [
                        {
                            "panel_id": "age_ale",
                            "panel_label": "A",
                            "title": "Age",
                            "x_label": "Age (years)",
                            "feature": "Age",
                            "reference_value": 60.0,
                            "reference_label": "Median age",
                            "ale_curve": {"x": [45.0, 55.0, 65.0, 75.0], "y": [0.02, 0.07, 0.11, 0.16]},
                            "local_effect_bins": [
                                {"bin_id": "age_bin_1", "bin_left": 40.0, "bin_right": 50.0, "bin_center": 45.0, "local_effect": 0.02, "support_count": 84},
                                {"bin_id": "age_bin_2", "bin_left": 50.0, "bin_right": 60.0, "bin_center": 55.0, "local_effect": 0.05, "support_count": 91},
                                {"bin_id": "age_bin_3", "bin_left": 60.0, "bin_right": 70.0, "bin_center": 65.0, "local_effect": 0.04, "support_count": 88},
                                {"bin_id": "age_bin_4", "bin_left": 70.0, "bin_right": 80.0, "bin_center": 75.0, "local_effect": 0.05, "support_count": 73},
                            ],
                        },
                        {
                            "panel_id": "albumin_ale",
                            "panel_label": "B",
                            "title": "Albumin",
                            "x_label": "Albumin (g/dL)",
                            "feature": "Albumin",
                            "reference_value": 3.8,
                            "reference_label": "Median albumin",
                            "ale_curve": {"x": [3.0, 3.4, 3.8, 4.2], "y": [-0.03, -0.07, -0.10, -0.12]},
                            "local_effect_bins": [
                                {"bin_id": "alb_bin_1", "bin_left": 2.8, "bin_right": 3.2, "bin_center": 3.0, "local_effect": -0.03, "support_count": 81},
                                {"bin_id": "alb_bin_2", "bin_left": 3.2, "bin_right": 3.6, "bin_center": 3.4, "local_effect": -0.04, "support_count": 87},
                                {"bin_id": "alb_bin_3", "bin_left": 3.6, "bin_right": 4.0, "bin_center": 3.8, "local_effect": -0.03, "support_count": 96},
                                {"bin_id": "alb_bin_4", "bin_left": 4.0, "bin_right": 4.4, "bin_center": 4.2, "local_effect": -0.02, "support_count": 78},
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
        (paper_root / "figures" / "generated" / "F45_accumulated_local_effects_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "local_effect_bin"]) == 8
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "ale_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == ["Accumulated local effect", "Local effect per bin"]
    assert layout_sidecar["metrics"]["panels"][0]["local_effect_bins"][0]["bin_id"] == "age_bin_1"
    assert layout_sidecar["metrics"]["panels"][1]["ale_points"][-1]["y"] < layout_sidecar["metrics"]["panels"][1]["ale_points"][0]["y"]

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"


def test_feature_response_support_domain_panel_preserves_f_support_domain_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
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
                    "display_id": "Figure47",
                    "template_id": "feature_response_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "feature_response_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "feature_response_support_domain_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure47",
                    "template_id": "fenggaolab.org.medical-display-core::feature_response_support_domain_panel",
                    "title": "Feature response support domain panel for audited support-aware explanation bounds",
                    "caption": "Regression lock for manuscript-facing support-domain explanation panels.",
                    "y_label": "Predicted response probability",
                    "panels": [
                        {
                            "panel_id": "age_support",
                            "panel_label": "A",
                            "title": "Age support domain",
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
                            "panel_label": "B",
                            "title": "Albumin support domain",
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
        (paper_root / "figures" / "generated" / "F47_feature_response_support_domain_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 2
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "support_domain_segment"]) == 8
    assert len([box for box in layout_sidecar["guide_boxes"] if box["box_type"] == "support_domain_reference_line"]) == 2
    assert layout_sidecar["metrics"]["legend_labels"] == [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    assert layout_sidecar["metrics"]["panels"][0]["support_segments"][1]["support_kind"] == "subgroup_support"
    assert layout_sidecar["metrics"]["panels"][0]["support_segments"][-1]["segment_label"] == "Extrapolation"
    assert layout_sidecar["metrics"]["panels"][1]["response_points"][-1]["y"] < layout_sidecar["metrics"]["panels"][1]["response_points"][0]["y"]

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
