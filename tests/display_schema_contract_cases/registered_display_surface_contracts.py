from .shared import *


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
