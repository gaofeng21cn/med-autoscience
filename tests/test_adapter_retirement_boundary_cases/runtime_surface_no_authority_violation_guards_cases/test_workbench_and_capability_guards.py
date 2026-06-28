from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[3]


def test_workbench_and_capability_violation_guards() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    workbench_bad_inventory = json.loads(json.dumps(inventory))
    workbench = next(
        surface
        for surface in workbench_bad_inventory["surfaces"]
        if surface["surface_id"]
        == "progress_portal_study_workbench_overview_action_projection"
    )
    workbench["projection_boundary"]["can_transport_operator_action"] = True
    workbench["projection_boundary"]["can_generate_action"] = True
    workbench["projection_boundary"][
        "operator_intent_refs_are_inert"
    ] = False
    workbench["opl_workbench_shell_readback_tail"]["tail_readback_proven"] = True
    workbench["opl_workbench_shell_readback_tail"][
        "no_active_workbench_projection_action_caller_proven"
    ] = True
    workbench["opl_workbench_shell_readback_tail"]["physical_delete_allowed"] = True
    workbench["opl_workbench_shell_readback_tail"][
        "mas_portal_projection_can_satisfy_readback"
    ] = True
    workbench["opl_workbench_shell_readback_tail"][
        "current_owner_delta_projection_can_satisfy_workbench_shell_readback"
    ] = True
    workbench["opl_workbench_shell_readback_tail"][
        "domain_progress_transition_runtime_readback_can_satisfy_action_transport"
    ] = True
    workbench["opl_workbench_shell_readback_tail"][
        "operator_intent_refs_can_satisfy_action_transport"
    ] = True
    workbench["opl_workbench_shell_readback_tail"]["forbidden_completion_claims"] = []
    workbench["retirement_gate"]["opl_workbench_shell_readback_required"] = False

    workbench_violations = retirement.validate_runtime_surface_retirement_inventory(
        workbench_bad_inventory
    )

    assert {
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_boundary_forbidden:can_generate_action",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_boundary_forbidden:can_transport_operator_action",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_boundary_mismatch:operator_intent_refs_are_inert",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_must_not_claim_readback_proven",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_must_not_claim_no_active_caller",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_must_not_allow_physical_delete",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_forbidden:mas_portal_projection_can_satisfy_readback",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            (
                "workbench_projection_tail_forbidden:"
                "current_owner_delta_projection_can_satisfy_workbench_shell_readback"
            ),
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            (
                "workbench_projection_tail_forbidden:"
                "domain_progress_transition_runtime_readback_can_satisfy_action_transport"
            ),
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_forbidden:operator_intent_refs_can_satisfy_action_transport",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_tail_missing_false_completion_guards",
        ),
        (
            "progress_portal_study_workbench_overview_action_projection",
            "workbench_projection_missing_opl_workbench_readback_gate",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in workbench_violations}

    capability_bad_inventory = json.loads(json.dumps(inventory))
    capability = next(
        surface
        for surface in capability_bad_inventory["surfaces"]
        if surface["surface_id"] == "agent_tool_arsenal_scientific_capability_registry"
    )
    capability["authority_boundary"]["mas_selector_authority"] = True
    capability["authority_boundary"]["selection_runtime_owner"] = "med-autoscience"
    capability["wildcard_action_trigger_boundary"]["wildcard_action_triggers_auto_select"] = True
    capability["wildcard_action_trigger_boundary"][
        "requires_explicit_capability_request"
    ] = False
    capability["wildcard_action_trigger_boundary"][
        "wildcard_action_triggers_can_select_without_explicit_capability_request"
    ] = True
    capability["wildcard_action_trigger_boundary"][
        "missing_explicit_capability_request_can_auto_select_wildcard_sidecar"
    ] = True
    capability["wildcard_action_trigger_boundary"][
        "wildcard_sidecar_can_block_current_owner_action"
    ] = True
    capability["retirement_gate"]["live_owner_consumption_soak_required"] = False
    capability["live_owner_consumption_soak_boundary"][
        "live_owner_consumption_soak_proven"
    ] = True
    capability["live_owner_consumption_soak_boundary"][
        "direct_hosted_parity_proven"
    ] = True
    capability["live_owner_consumption_soak_boundary"]["physical_delete_allowed"] = True
    capability["live_owner_consumption_soak_boundary"][
        "required_before_physical_delete"
    ] = "repo_tests_green_ref"
    capability["live_owner_consumption_soak_boundary"]["physical_delete_requires"] = [
        "repo_tests_green_ref"
    ]
    capability["live_owner_consumption_soak_boundary"][
        "required_active_caller_readbacks"
    ] = ["mcp_or_cli_mode_coverage"]
    capability["live_owner_consumption_soak_boundary"][
        "forbidden_completion_claims"
    ] = ["repo_tests_green_as_physical_delete"]

    capability_violations = retirement.validate_runtime_surface_retirement_inventory(
        capability_bad_inventory
    )

    assert {
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "truthy_authority_flag:authority_boundary.mas_selector_authority",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            (
                "truthy_authority_flag:wildcard_action_trigger_boundary."
                "wildcard_action_triggers_auto_select"
            ),
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_authority_forbidden:mas_selector_authority",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_selection_owner_not_opl",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_auto_select_enabled",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_missing_explicit_request_gate",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_can_select_without_explicit_request",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_missing_request_can_auto_select",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_wildcard_sidecar_can_block_owner_action",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_missing_live_owner_soak_gate",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_claimed:live_owner_consumption_soak_proven",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_claimed:direct_hosted_parity_proven",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_claimed:physical_delete_allowed",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_missing_physical_delete_ref",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_physical_delete_requires_incomplete",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_required_readbacks_incomplete",
        ),
        (
            "agent_tool_arsenal_scientific_capability_registry",
            "capability_registry_live_soak_missing_false_completion_guard",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in capability_violations}
