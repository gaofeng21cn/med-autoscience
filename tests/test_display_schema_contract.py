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
    time_to_event_panel = module.get_input_schema_contract("time_to_event_discrimination_calibration_inputs_v1")
    time_to_event_decision = module.get_input_schema_contract("time_to_event_decision_curve_inputs_v1")
    generalizability = module.get_input_schema_contract("multicenter_generalizability_inputs_v1")
    performance_table = module.get_input_schema_contract("time_to_event_performance_summary_v1")
    interpretation_table = module.get_input_schema_contract("clinical_interpretation_summary_v1")
    time_to_event_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "time_to_event"
    )

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

    assert time_to_event_decision.template_ids == ("time_to_event_decision_curve",)
    assert time_to_event_decision.collection_required_fields["series"] == ("label", "x", "y")
    assert "publication_style_profile_required_at_materialization" in time_to_event_decision.additional_constraints
    assert "display_override_contract_may_adjust_layout_without_changing_data" in time_to_event_decision.additional_constraints
    assert generalizability.template_ids == ("multicenter_generalizability_overview",)
    assert generalizability.collection_required_fields["centers"] == (
        "center_label",
        "sample_size",
        "estimate",
        "lower",
        "upper",
    )
    assert performance_table.template_ids == ("table2_time_to_event_performance_summary",)
    assert performance_table.collection_required_fields["rows"] == ("row_id", "label", "values")
    assert interpretation_table.template_ids == ("table3_clinical_interpretation_summary",)
    assert interpretation_table.collection_required_fields["rows"] == ("row_id", "label", "values")


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
