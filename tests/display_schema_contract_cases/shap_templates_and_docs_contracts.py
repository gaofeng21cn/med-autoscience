from .shared import *


def test_current_shap_schema_contracts_are_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")
    model_explanation_class = next(
        item for item in module.list_display_schema_classes() if item.class_id == "model_explanation"
    )

    shap_bar = module.get_input_schema_contract("shap_bar_importance_inputs_v1")
    shap_multicohort = module.get_input_schema_contract("shap_multicohort_importance_panel_inputs_v1")
    shap_dependence = module.get_input_schema_contract("shap_dependence_panel_inputs_v1")
    shap_force = module.get_input_schema_contract("shap_force_like_summary_panel_inputs_v1")

    assert shap_bar.template_ids == (_full_id("shap_bar_importance"),)
    assert shap_bar.collection_required_fields["bars"] == ("rank", "feature", "importance_value")
    assert "bar_importance_values_must_be_sorted_descending_by_rank" in shap_bar.additional_constraints
    assert shap_multicohort.template_ids == (_full_id("shap_multicohort_importance_panel"),)
    assert shap_multicohort.nested_collection_required_fields["panels.bars"] == (
        "rank",
        "feature",
        "importance_value",
    )
    assert "panel_feature_orders_must_match_across_panels" in shap_multicohort.additional_constraints
    assert shap_dependence.template_ids == (_full_id("shap_dependence_panel"),)
    assert "panel_point_values_must_be_finite" in shap_dependence.additional_constraints
    assert shap_force.template_ids == (_full_id("shap_force_like_summary_panel"),)
    assert "panel_contributions_must_be_sorted_by_absolute_magnitude_descending" in shap_force.additional_constraints

    assert model_explanation_class.template_ids == (
        _full_id("shap_summary_beeswarm"),
        _full_id("shap_bar_importance"),
        _full_id("shap_multicohort_importance_panel"),
        _full_id("shap_dependence_panel"),
        _full_id("shap_waterfall_local_explanation_panel"),
        _full_id("shap_force_like_summary_panel"),
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
