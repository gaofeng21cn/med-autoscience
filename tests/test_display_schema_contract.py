from __future__ import annotations

import importlib


def test_schema_contract_exposes_eight_top_level_display_classes() -> None:
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
        "publication_shells_and_tables",
    }


def test_schema_contract_tracks_registered_templates_and_input_shapes() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    correlation = module.get_input_schema_contract("correlation_heatmap_inputs_v1")
    shap = module.get_input_schema_contract("shap_summary_inputs_v1")

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

    assert shap.template_ids == ("shap_summary_beeswarm",)
    assert shap.collection_required_fields["rows"] == ("feature", "points")
    assert shap.nested_collection_required_fields["rows.points"] == ("shap_value", "feature_value")


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
