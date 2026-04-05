from __future__ import annotations

import importlib
from pathlib import Path


def test_schema_contract_exposes_phase2_top_level_display_classes() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    classes = module.list_display_schema_classes()

    assert {item.class_id for item in classes} == {
        "prediction_performance",
        "clinical_utility",
        "time_to_event",
        "data_geometry",
        "matrix_pattern",
        "effect_estimate",
        "model_explanation",
        "model_audit",
        "generalizability",
        "publication_shells_and_tables",
    }


def test_schema_contract_tracks_registered_templates_and_input_shapes() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    binary = module.get_input_schema_contract("binary_prediction_curve_inputs_v1")
    embedding = module.get_input_schema_contract("embedding_grouped_inputs_v1")
    clustered_heatmap = module.get_input_schema_contract("clustered_heatmap_inputs_v1")
    correlation = module.get_input_schema_contract("correlation_heatmap_inputs_v1")
    forest = module.get_input_schema_contract("forest_effect_inputs_v1")
    shap = module.get_input_schema_contract("shap_summary_inputs_v1")
    cohort_flow = module.get_input_schema_contract("cohort_flow_shell_inputs_v1")
    time_to_event_panel = module.get_input_schema_contract("time_to_event_discrimination_calibration_inputs_v1")
    time_to_event_decision = module.get_input_schema_contract("time_to_event_decision_curve_inputs_v1")
    generalizability = module.get_input_schema_contract("multicenter_generalizability_inputs_v1")
    risk_layering = module.get_input_schema_contract("risk_layering_monotonic_inputs_v1")
    binary_calibration_decision = module.get_input_schema_contract(
        "binary_calibration_decision_curve_panel_inputs_v1"
    )
    model_complexity_audit = module.get_input_schema_contract("model_complexity_audit_panel_inputs_v1")
    performance_table = module.get_input_schema_contract("time_to_event_performance_summary_v1")
    interpretation_table = module.get_input_schema_contract("clinical_interpretation_summary_v1")
    time_to_event_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "time_to_event"
    )
    clinical_utility_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "clinical_utility"
    )
    model_audit_class = next(item for item in module.list_display_schema_classes() if item.class_id == "model_audit")

    assert binary.template_ids == (
        "roc_curve_binary",
        "pr_curve_binary",
        "calibration_curve_binary",
        "decision_curve_binary",
        "time_dependent_roc_horizon",
    )
    assert embedding.template_ids == (
        "umap_scatter_grouped",
        "pca_scatter_grouped",
        "tsne_scatter_grouped",
    )
    assert clustered_heatmap.template_ids == ("clustered_heatmap",)
    assert clustered_heatmap.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "row_order",
        "column_order",
        "cells",
    )
    assert clustered_heatmap.collection_required_fields["row_order"] == ("label",)
    assert clustered_heatmap.collection_required_fields["column_order"] == ("label",)
    assert clustered_heatmap.additional_constraints == (
        "cells_must_be_non_empty",
        "cell_coordinates_must_be_non_empty",
        "cell_values_must_be_finite",
        "row_order_labels_must_be_unique",
        "column_order_labels_must_be_unique",
        "declared_row_labels_must_match_cell_rows",
        "declared_column_labels_must_match_cell_columns",
        "declared_heatmap_grid_must_be_complete_and_unique",
    )

    assert correlation.template_ids == ("correlation_heatmap",)
    assert correlation.required_top_level_fields == ("schema_version", "input_schema_id", "displays")
    assert correlation.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "x_label",
        "y_label",
        "cells",
    )
    assert correlation.collection_required_fields["cells"] == ("x", "y", "value")
    assert correlation.additional_constraints == (
        "matrix_must_be_square",
        "matrix_must_include_diagonal",
        "matrix_must_be_symmetric",
    )

    assert forest.template_ids == ("forest_effect_main", "subgroup_forest")
    assert forest.collection_required_fields["rows"] == ("label", "estimate", "lower", "upper")
    assert shap.template_ids == ("shap_summary_beeswarm",)
    assert shap.collection_required_fields["rows"] == ("feature", "points")
    assert shap.nested_collection_required_fields["rows.points"] == ("shap_value", "feature_value")
    assert cohort_flow.template_ids == ("cohort_flow_figure",)
    assert cohort_flow.required_top_level_fields == ("schema_version", "shell_id", "display_id", "title", "steps")
    assert cohort_flow.optional_top_level_fields == ("caption", "exclusions", "endpoint_inventory", "design_panels")
    assert cohort_flow.collection_required_fields["steps"] == ("step_id", "label", "n")
    assert cohort_flow.collection_required_fields["exclusions"] == ("exclusion_id", "from_step_id", "label", "n")
    assert cohort_flow.collection_required_fields["endpoint_inventory"] == ("endpoint_id", "label", "event_n")
    assert cohort_flow.collection_required_fields["design_panels"] == ("panel_id", "title", "layout_role", "lines")
    assert cohort_flow.nested_collection_required_fields["design_panels.lines"] == ("label",)
    assert "exclusion_ids_must_be_unique" in cohort_flow.additional_constraints
    assert "design_panel_lines_must_be_non_empty" in cohort_flow.additional_constraints

    assert "time_dependent_roc_horizon" in time_to_event_class.template_ids
    assert "binary_prediction_curve_inputs_v1" in time_to_event_class.input_schema_ids
    assert time_to_event_panel.template_ids == ("time_to_event_discrimination_calibration_panel",)
    assert time_to_event_panel.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "discrimination_x_label",
        "discrimination_y_label",
        "calibration_x_label",
        "calibration_y_label",
        "discrimination_series",
        "calibration_groups",
    )
    assert time_to_event_panel.collection_required_fields["discrimination_series"] == ("label", "x", "y")
    assert time_to_event_panel.collection_required_fields["calibration_groups"] == ("label", "times", "values")
    assert "binary_calibration_decision_curve_panel" in clinical_utility_class.template_ids
    assert "binary_calibration_decision_curve_panel_inputs_v1" in clinical_utility_class.input_schema_ids
    assert binary_calibration_decision.template_ids == ("binary_calibration_decision_curve_panel",)
    assert binary_calibration_decision.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "calibration_x_label",
        "calibration_y_label",
        "decision_x_label",
        "decision_y_label",
        "calibration_series",
        "decision_series",
        "decision_reference_lines",
        "decision_focus_window",
    )
    assert binary_calibration_decision.collection_required_fields["calibration_series"] == ("label", "x", "y")
    assert binary_calibration_decision.collection_required_fields["decision_series"] == ("label", "x", "y")
    assert binary_calibration_decision.collection_required_fields["decision_reference_lines"] == (
        "label",
        "x",
        "y",
    )
    assert "calibration_axis_window" in binary_calibration_decision.display_optional_fields
    assert binary_calibration_decision.nested_collection_required_fields["calibration_axis_window"] == (
        "xmin",
        "xmax",
        "ymin",
        "ymax",
    )
    assert binary_calibration_decision.nested_collection_required_fields["decision_focus_window"] == ("xmin", "xmax")
    assert "calibration_axis_window_must_be_strictly_increasing" in binary_calibration_decision.additional_constraints
    assert "decision_focus_window_must_be_strictly_increasing" in binary_calibration_decision.additional_constraints

    assert time_to_event_decision.template_ids == ("time_to_event_decision_curve",)
    assert time_to_event_decision.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "panel_a_title",
        "panel_b_title",
        "x_label",
        "y_label",
        "treated_fraction_y_label",
        "series",
        "treated_fraction_series",
    )
    assert time_to_event_decision.collection_required_fields["series"] == ("label", "x", "y")
    assert time_to_event_decision.collection_required_fields["treated_fraction_series"] == ("label", "x", "y")
    assert "publication_style_profile_required_at_materialization" in time_to_event_decision.additional_constraints
    assert "display_override_contract_may_adjust_layout_without_changing_data" in time_to_event_decision.additional_constraints
    assert "treated_fraction_series_x_y_lengths_must_match" in time_to_event_decision.additional_constraints
    assert generalizability.template_ids == ("multicenter_generalizability_overview",)
    assert generalizability.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "overview_mode",
        "center_event_y_label",
        "coverage_y_label",
        "center_event_counts",
        "coverage_panels",
    )
    assert generalizability.collection_required_fields["center_event_counts"] == (
        "center_label",
        "split_bucket",
        "event_count",
    )
    assert generalizability.collection_required_fields["coverage_panels"] == (
        "panel_id",
        "title",
        "layout_role",
        "bars",
    )
    assert generalizability.nested_collection_required_fields["coverage_panels.bars"] == ("label", "count")
    assert "overview_mode_must_be_center_support_counts" in generalizability.additional_constraints
    assert risk_layering.template_ids == ("risk_layering_monotonic_bars",)
    assert risk_layering.required_top_level_fields == ("schema_version", "input_schema_id", "displays")
    assert risk_layering.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "y_label",
        "left_panel_title",
        "left_x_label",
        "left_bars",
        "right_panel_title",
        "right_x_label",
        "right_bars",
    )
    assert risk_layering.collection_required_fields["left_bars"] == ("label", "cases", "events", "risk")
    assert risk_layering.collection_required_fields["right_bars"] == ("label", "cases", "events", "risk")
    assert "bar_events_must_not_exceed_cases" in risk_layering.additional_constraints
    assert "left_bars_risk_must_be_monotonic_non_decreasing" in risk_layering.additional_constraints
    assert "right_bars_risk_must_be_monotonic_non_decreasing" in risk_layering.additional_constraints
    assert model_audit_class.template_ids == ("model_complexity_audit_panel",)
    assert model_complexity_audit.display_required_fields == (
        "display_id",
        "template_id",
        "title",
        "caption",
        "metric_panels",
        "audit_panels",
    )
    assert model_complexity_audit.collection_required_fields["metric_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "rows",
    )
    assert model_complexity_audit.collection_required_fields["audit_panels"] == (
        "panel_id",
        "panel_label",
        "title",
        "x_label",
        "rows",
    )
    assert model_complexity_audit.nested_collection_required_fields["metric_panels.rows"] == ("label", "value")
    assert model_complexity_audit.nested_collection_required_fields["audit_panels.rows"] == ("label", "value")
    assert performance_table.template_ids == ("table2_time_to_event_performance_summary",)
    assert performance_table.collection_required_fields["rows"] == ("row_id", "label", "values")
    assert interpretation_table.template_ids == ("table3_clinical_interpretation_summary",)
    assert interpretation_table.collection_required_fields["rows"] == ("row_id", "label", "values")
    cohort_flow_shell = module.get_input_schema_contract("cohort_flow_shell_inputs_v1")
    assert cohort_flow_shell.required_top_level_fields == ("schema_version", "shell_id", "display_id", "title", "steps")
    assert cohort_flow_shell.optional_top_level_fields == (
        "caption",
        "exclusions",
        "endpoint_inventory",
        "design_panels",
    )
    assert cohort_flow_shell.collection_required_fields["steps"] == ("step_id", "label", "n")
    assert cohort_flow_shell.collection_required_fields["exclusions"] == ("exclusion_id", "from_step_id", "label", "n")
    assert cohort_flow_shell.collection_required_fields["endpoint_inventory"] == ("endpoint_id", "label", "event_n")
    assert cohort_flow_shell.collection_required_fields["design_panels"] == ("panel_id", "title", "layout_role", "lines")
    assert cohort_flow_shell.nested_collection_required_fields["design_panels.lines"] == ("label",)
    assert "exclusion_ids_must_be_unique" in cohort_flow_shell.additional_constraints
    assert "design_panel_lines_must_be_non_empty" in cohort_flow_shell.additional_constraints


def test_schema_contract_covers_all_registered_display_surface_items() -> None:
    schema_module = importlib.import_module("med_autoscience.display_schema_contract")
    registry_module = importlib.import_module("med_autoscience.display_registry")

    covered_templates = {
        template_id
        for schema in schema_module.list_input_schema_contracts()
        for template_id in schema.template_ids
    }
    covered_templates.update(
        template_id
        for display_class in schema_module.list_display_schema_classes()
        for template_id in display_class.template_ids
    )

    expected = {
        *(item.template_id for item in registry_module.list_evidence_figure_specs()),
        *(item.shell_id for item in registry_module.list_illustration_shell_specs()),
        *(item.shell_id for item in registry_module.list_table_shell_specs()),
    }

    assert covered_templates >= expected


def test_render_display_template_catalog_covers_all_registered_templates() -> None:
    module = importlib.import_module("med_autoscience.display_template_catalog")

    markdown = module.render_display_template_catalog_markdown()

    assert "roc_curve_binary" in markdown
    assert "shap_summary_inputs_v1" in markdown
    assert "cohort_flow_figure" in markdown
    assert "table1_baseline_characteristics" in markdown
    assert "time_dependent_roc_horizon" in markdown
    assert "tsne_scatter_grouped" in markdown
    assert "clustered_heatmap" in markdown
    assert "clustered_heatmap_inputs_v1" in markdown
    assert "subgroup_forest" in markdown
    assert "time_to_event_discrimination_calibration_panel" in markdown
    assert "time_to_event_decision_curve_inputs_v1" in markdown
    assert "multicenter_generalizability_overview" in markdown
    assert "risk_layering_monotonic_bars" in markdown
    assert "binary_calibration_decision_curve_panel" in markdown
    assert "model_complexity_audit_panel" in markdown
    assert "table2_time_to_event_performance_summary" in markdown


def test_checked_in_template_catalog_guide_matches_renderer_output() -> None:
    module = importlib.import_module("med_autoscience.display_template_catalog")
    guide_path = Path(__file__).resolve().parents[1] / "docs" / "medical_display_template_catalog.md"

    assert guide_path.read_text(encoding="utf-8") == module.render_display_template_catalog_markdown()


def test_checked_in_display_audit_guide_tracks_current_counts_and_class_map() -> None:
    schema_module = importlib.import_module("med_autoscience.display_schema_contract")
    registry_module = importlib.import_module("med_autoscience.display_registry")
    guide_path = Path(__file__).resolve().parents[1] / "docs" / "medical_display_audit_guide.md"

    guide_text = guide_path.read_text(encoding="utf-8")
    evidence_classes = [
        display_class
        for display_class in schema_module.list_display_schema_classes()
        if display_class.class_id != "publication_shells_and_tables"
    ]

    assert f"- Evidence figure classes: `{len(evidence_classes)}`" in guide_text
    assert f"- Implemented evidence figure templates: `{len(registry_module.list_evidence_figure_specs())}`" in guide_text
    assert f"- Illustration shells: `{len(registry_module.list_illustration_shell_specs())}`" in guide_text
    assert f"- Table shells: `{len(registry_module.list_table_shell_specs())}`" in guide_text
    total_templates = (
        len(registry_module.list_evidence_figure_specs())
        + len(registry_module.list_illustration_shell_specs())
        + len(registry_module.list_table_shell_specs())
    )
    assert f"- Total implemented display templates: `{total_templates}`" in guide_text

    for display_class in evidence_classes:
        assert display_class.display_name in guide_text
