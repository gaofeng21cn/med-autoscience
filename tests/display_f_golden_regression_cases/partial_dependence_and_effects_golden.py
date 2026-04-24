from .shared import *

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

def test_shap_grouped_local_support_domain_panel_preserves_f_explanation_scene_contract(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.display_surface_materialization")
    paper_root = tmp_path / "paper"
    _dump_json(
        paper_root / "display_registry.json",
        {
            "schema_version": 1,
            "source_contract_path": "paper/medical_reporting_contract.json",
            "displays": [
                {
                    "display_id": "Figure50",
                    "display_kind": "figure",
                    "requirement_key": "shap_grouped_local_support_domain_panel",
                    "catalog_id": "F50",
                    "shell_path": "paper/figures/Figure50.shell.json",
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
                    "display_id": "Figure50",
                    "template_id": "shap_grouped_local_support_domain_panel",
                    "layout_override": {"show_figure_title": False},
                    "readability_override": {},
                }
            ],
        },
    )
    _dump_json(
        paper_root / "shap_grouped_local_support_domain_panel_inputs.json",
        {
            "schema_version": 1,
            "input_schema_id": "shap_grouped_local_support_domain_panel_inputs_v1",
            "displays": [
                {
                    "display_id": "Figure50",
                    "template_id": "fenggaolab.org.medical-display-core::shap_grouped_local_support_domain_panel",
                    "title": "Grouped local explanation with support-domain follow-on for manuscript-facing driver interpretation",
                    "caption": "Regression lock for grouped local explanation scenes with matched support-domain context.",
                    "grouped_local_x_label": "Local SHAP contribution to predicted risk",
                    "support_y_label": "Predicted response probability",
                    "support_legend_title": "Support domain",
                    "local_panels": [
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
        (paper_root / "figures" / "generated" / "F50_shap_grouped_local_support_domain_panel.layout.json").read_text(
            encoding="utf-8"
        )
    )
    assert len(layout_sidecar["panel_boxes"]) == 4
    assert layout_sidecar["metrics"]["support_legend_labels"] == [
        "Response curve",
        "Observed support",
        "Subgroup support",
        "Bin support",
        "Extrapolation reminder",
    ]
    assert layout_sidecar["metrics"]["local_shared_feature_order"] == ["Age", "Albumin", "Tumor size"]
    assert [item["feature"] for item in layout_sidecar["metrics"]["support_panels"]] == ["Age", "Albumin"]
    assert layout_sidecar["metrics"]["support_panels"][0]["support_segments"][1]["support_kind"] == "subgroup_support"
    assert any(box["box_type"] == "zero_line" for box in layout_sidecar["guide_boxes"])
    assert any(box["box_type"] == "support_domain_segment" for box in layout_sidecar["guide_boxes"])

    figure_catalog = json.loads((paper_root / "figures" / "figure_catalog.json").read_text(encoding="utf-8"))
    assert figure_catalog["figures"][0]["qc_result"]["status"] == "pass"
