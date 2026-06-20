from .shared import *


def test_current_shap_schema_contracts_are_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    shap_summary = module.get_input_schema_contract("shap_summary_inputs_v1")
    shap_dependence = module.get_input_schema_contract("shap_dependence_panel_inputs_v1")
    shap_waterfall = module.get_input_schema_contract("shap_waterfall_local_explanation_panel_inputs_v1")

    assert shap_summary.template_ids == (_full_id("shap_summary_beeswarm"),)
    assert shap_summary.collection_required_fields["rows"] == ("feature", "points")
    assert "shap_values_must_be_finite" in shap_summary.additional_constraints
    assert shap_dependence.template_ids == (_full_id("shap_dependence_panel"),)
    assert "panel_point_values_must_be_finite" in shap_dependence.additional_constraints
    assert shap_waterfall.template_ids == (_full_id("shap_waterfall_local_explanation_panel"),)
    assert "panel_prediction_value_must_equal_baseline_plus_contributions" in shap_waterfall.additional_constraints

    assert model_explanation_class.template_ids == (
        _full_id("shap_summary_beeswarm"),
        _full_id("shap_dependence_panel"),
        _full_id("shap_waterfall_local_explanation_panel"),
    )


def test_render_display_template_catalog_covers_current_registered_templates() -> None:
    registry_module = importlib.import_module("med_autoscience.display_registry")
    catalog_module = importlib.import_module("med_autoscience.display_template_catalog")

    markdown = catalog_module.render_display_template_catalog_markdown()

    assert "| Template ID | Kind | Paper Family | Display Name | Renderer Family | Input Schema | QC Profile | Required Exports |" in markdown
    assert "`A. Predictive Performance and Decision`" in markdown
    assert "`H. Cohort and Study Design Evidence`" in markdown
    for item in registry_module.list_evidence_figure_specs():
        assert item.template_id in markdown
        assert item.input_schema_id in markdown
        assert item.renderer_family == "r_ggplot2"
    for item in registry_module.list_illustration_shell_specs():
        assert item.shell_id in markdown
        assert item.input_schema_id in markdown
    for item in registry_module.list_table_shell_specs():
        assert item.shell_id in markdown
        assert item.input_schema_id in markdown
