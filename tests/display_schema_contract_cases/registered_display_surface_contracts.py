from .shared import *


RETIRED_PYTHON_EVIDENCE_TEMPLATE_IDS = (
    "single_cell_atlas_overview_panel",
    "atlas_spatial_bridge_panel",
    "spatial_niche_map_panel",
    "trajectory_progression_panel",
    "atlas_spatial_trajectory_storyboard_panel",
    "atlas_spatial_trajectory_density_coverage_panel",
    "atlas_spatial_trajectory_context_support_panel",
    "atlas_spatial_trajectory_multimanifold_context_support_panel",
    "shap_signed_importance_panel",
    "shap_grouped_local_explanation_panel",
    "shap_grouped_decision_path_panel",
    "shap_multigroup_decision_path_panel",
    "partial_dependence_ice_panel",
    "partial_dependence_interaction_contour_panel",
    "partial_dependence_interaction_slice_panel",
    "partial_dependence_subgroup_comparison_panel",
    "accumulated_local_effects_panel",
    "feature_response_support_domain_panel",
    "shap_grouped_local_support_domain_panel",
    "shap_multigroup_decision_path_support_domain_panel",
    "shap_signed_importance_local_support_domain_panel",
    "multicenter_generalizability_overview",
    "center_transportability_governance_summary_panel",
)

RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS = (
    "single_cell_atlas_overview_inputs_v1",
    "atlas_spatial_bridge_panel_inputs_v1",
    "spatial_niche_map_inputs_v1",
    "trajectory_progression_inputs_v1",
    "atlas_spatial_trajectory_storyboard_inputs_v1",
    "atlas_spatial_trajectory_density_coverage_panel_inputs_v1",
    "atlas_spatial_trajectory_context_support_panel_inputs_v1",
    "atlas_spatial_trajectory_multimanifold_context_support_panel_inputs_v1",
    "shap_signed_importance_panel_inputs_v1",
    "shap_grouped_local_explanation_panel_inputs_v1",
    "shap_grouped_decision_path_panel_inputs_v1",
    "shap_multigroup_decision_path_panel_inputs_v1",
    "partial_dependence_ice_panel_inputs_v1",
    "partial_dependence_interaction_contour_panel_inputs_v1",
    "partial_dependence_interaction_slice_panel_inputs_v1",
    "partial_dependence_subgroup_comparison_panel_inputs_v1",
    "accumulated_local_effects_panel_inputs_v1",
    "feature_response_support_domain_panel_inputs_v1",
    "shap_grouped_local_support_domain_panel_inputs_v1",
    "shap_multigroup_decision_path_support_domain_panel_inputs_v1",
    "shap_signed_importance_local_support_domain_panel_inputs_v1",
    "multicenter_generalizability_inputs_v1",
    "center_transportability_governance_summary_panel_inputs_v1",
)


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


def test_current_schema_contract_has_no_python_evidence_or_empty_evidence_schema() -> None:
    schema_module = importlib.import_module("med_autoscience.display_schema_contract")
    registry_module = importlib.import_module("med_autoscience.display_registry")

    assert [
        item.template_id
        for item in registry_module.list_evidence_figure_specs()
        if item.renderer_family == "python"
    ] == []
    assert [
        item.input_schema_id
        for item in schema_module.list_input_schema_contracts()
        if item.display_kind == "evidence_figure" and not item.template_ids
    ] == []


def test_retired_python_evidence_templates_are_not_current_contract_or_catalog() -> None:
    schema_module = importlib.import_module("med_autoscience.display_schema_contract")
    catalog_module = importlib.import_module("med_autoscience.display_template_catalog")

    current_schema_ids = {item.input_schema_id for item in schema_module.list_input_schema_contracts()}
    current_class_schema_ids = {
        schema_id
        for display_class in schema_module.list_display_schema_classes()
        for schema_id in display_class.input_schema_ids
    }
    current_template_ids = {
        template_id
        for display_class in schema_module.list_display_schema_classes()
        for template_id in display_class.template_ids
    }
    markdown = catalog_module.render_display_template_catalog_markdown()

    assert not (set(RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS) & current_schema_ids)
    assert not (set(RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS) & current_class_schema_ids)
    assert not ({_full_id(item) for item in RETIRED_PYTHON_EVIDENCE_TEMPLATE_IDS} & current_template_ids)
    for template_id in RETIRED_PYTHON_EVIDENCE_TEMPLATE_IDS:
        assert _full_id(template_id) not in markdown
    for schema_id in RETIRED_PYTHON_EVIDENCE_SCHEMA_IDS:
        assert schema_id not in markdown


def test_current_key_schema_contracts_remain_registered() -> None:
    module = importlib.import_module("med_autoscience.display_schema_contract")

    threshold_governance = module.get_input_schema_contract("time_to_event_threshold_governance_inputs_v1")
    multihorizon = module.get_input_schema_contract("time_to_event_multihorizon_calibration_inputs_v1")
    shap_waterfall = module.get_input_schema_contract("shap_waterfall_local_explanation_panel_inputs_v1")
    generalizability = module.get_input_schema_contract("generalizability_subgroup_composite_inputs_v1")

    assert threshold_governance.template_ids == (_full_id("time_to_event_threshold_governance_panel"),)
    assert "threshold_values_must_be_strictly_increasing_probability" in threshold_governance.additional_constraints
    assert multihorizon.template_ids == (_full_id("time_to_event_multihorizon_calibration_panel"),)
    assert "panel_time_horizon_months_must_be_strictly_increasing" in multihorizon.additional_constraints
    assert shap_waterfall.template_ids == (_full_id("shap_waterfall_local_explanation_panel"),)
    assert "panel_prediction_value_must_equal_baseline_plus_contributions" in shap_waterfall.additional_constraints
    assert generalizability.template_ids == (_full_id("generalizability_subgroup_composite_panel"),)
    assert "subgroup_rows_must_satisfy_lower_le_estimate_le_upper" in generalizability.additional_constraints
