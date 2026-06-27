from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_EXECUTOR_CARRIER_TAIL_READBACK = {
    "surface_kind": "opl_default_executor_carrier_tail_readback_requirement",
    "status": "tail_open",
    "runtime_owner": "one-person-lab",
    "runtime_kind": "DomainProgressTransitionRuntime/TransactionalOutbox/StageRun",
    "required_active_caller_readbacks": [
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_command_event_outbox_live_readback",
        "opl_stagerun_owner_callable_adapter_live_readback",
    ],
    "required_before_physical_delete": (
        "default_executor_dispatch_request_opl_default_executor_carrier_tail_readback_ref"
    ),
    "physical_delete_requires": [
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_command_event_outbox_live_readback",
        "opl_stagerun_owner_callable_adapter_live_readback",
        "no_active_default_executor_carrier_caller_scan",
        "no_forbidden_write_proof",
        "replacement_parity_ref",
        "owner_retirement_decision_ref",
        "tombstone_or_provenance_ref",
    ],
    "tail_readback_proven": False,
    "no_active_default_executor_carrier_caller_proven": False,
    "physical_delete_allowed": False,
    "legacy_carrier_provenance_can_satisfy_readback": False,
    "transition_request_pending_can_satisfy_readback": False,
    "repo_no_authority_guard_can_satisfy_readback": False,
    "focused_tests_can_satisfy_readback": False,
    "request_only_carrier_can_authorize_provider_admission": False,
    "request_only_carrier_can_claim_running_or_progress": False,
    "forbidden_completion_claims": [
        "legacy_carrier_provenance_as_default_executor_carrier_tail_readback",
        "transition_request_pending_as_opl_live_readback",
        "repo_no_authority_guard_as_default_executor_carrier_tail_readback",
        "focused_tests_green_as_no_active_default_executor_carrier_caller",
        "request_only_carrier_as_provider_admission",
        "request_only_carrier_as_running_or_progress",
    ],
}

def test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)

    assert audit["surface_kind"] == "mas_runtime_surface_retirement_no_authority_audit"
    assert audit["status"] == "repo_source_physical_retirement_complete"
    assert audit["generic_runtime_owner"] == "one-person-lab"
    assert audit["completion_claim_allowed"] is True
    assert audit["physical_retirement_tail_open"] is False
    assert audit["repo_source_retirement_completion"] == {
        "status": "complete",
        "completion_claim_allowed": True,
        "open_surface_count": 0,
        "open_surface_ids": [],
        "evidence_basis": [
            "current_disposition=physically_retired",
            "no authority-boundary violations",
            "compatibility_alias_allowed=false",
            "mas_owner_claim_allowed=false",
        ],
    }
    assert audit["live_runtime_readiness_completion"]["status"] == "evidence_required"
    assert audit["live_runtime_readiness_completion"]["completion_claim_allowed"] is False
    assert audit["no_active_authority_caller_proven"] is True
    layers = audit["completion_evidence_layers"]
    assert layers["repo_no_authority_guard"]["status"] == "satisfied_with_repo_evidence"
    assert layers["repo_no_authority_guard"]["violations_count"] == 0
    assert layers["live_soak_or_no_active_caller"]["status"] == "evidence_required"
    assert layers["live_soak_or_no_active_caller"]["proven"] is False
    assert (
        "domain_owner_action_dispatch_live_every_active_caller_soak_or_no_active_caller_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_execute_dispatch_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_stage_native_owner_action_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_provider_hosted_stage_packet_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_ai_reviewer_authorization_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_gate_clearing_authorization_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_current_execution_running_proof_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_study_progress_running_proof_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_no_active_owner_callable_adapter_caller_scan_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "domain_health_diagnostic_obligation_actuator_owner_retirement_decision_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_scientific_capability_registry_live_owner_consumption_soak_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_live_owner_consumption_soak_current_owner_delta_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_explicit_capability_request_resolution_live_readback_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_direct_hosted_tool_invocation_runtime_parity_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_no_active_registry_projection_caller_scan_ref"
        in layers["live_soak_or_no_active_caller"]["required_ref_families"]
    )
    evidence_tails = {
        item["surface_id"]: item
        for item in layers["live_soak_or_no_active_caller"]["open_surface_tails"]
    }
    assert "default_executor_dispatch_request" not in evidence_tails
    assert "domain_authority_refs_index" not in evidence_tails
    assert "default_executor_execution_latest_wire_projection" not in evidence_tails
    actuator_tail = evidence_tails["domain_health_diagnostic_obligation_actuator"]
    assert (
        "domain_health_diagnostic_obligation_actuator_opl_obligation_actuator_tail_readback_ref"
        in actuator_tail["required_ref_families"]
    )
    assert (
        "domain_health_diagnostic_obligation_actuator_owner_retirement_decision_ref"
        in actuator_tail["required_ref_families"]
    )
    assert (
        "domain_health_diagnostic_obligation_actuator_no_active_caller_scan_ref"
        in actuator_tail["required_ref_families"]
    )
    assert (
        "mas_policy_projection_as_opl_recovery_obligation_store_readback"
        in actuator_tail["forbidden_completion_interpretations"]
    )
    owner_dispatch_tail = evidence_tails["domain_owner_action_dispatch"]
    assert (
        "domain_owner_action_dispatch_execute_dispatch_live_readback_ref"
        in owner_dispatch_tail["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_provider_hosted_stage_packet_live_readback_ref"
        in owner_dispatch_tail["required_ref_families"]
    )
    assert (
        "domain_owner_action_dispatch_no_active_owner_callable_adapter_caller_scan_ref"
        in owner_dispatch_tail["required_ref_families"]
    )
    assert (
        "repo_authorization_coverage_as_live_every_active_caller_soak"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    assert (
        "provider_completion_as_dispatch_retirement"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    assert (
        "current_execution_running_proof_without_opl_readback_as_soak"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    assert (
        "study_progress_running_proof_without_opl_readback_as_soak"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    assert (
        "owner_callable_adapter_receipt_projection_as_opl_stage_run_readback"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    assert (
        "opl_execution_authorization_required_blocker_as_live_soak"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    assert (
        "provider_handoff_or_completion_as_physical_delete"
        in owner_dispatch_tail["forbidden_completion_interpretations"]
    )
    runtime_health_tail = evidence_tails["runtime_health_kernel"]
    assert (
        "runtime_health_kernel_opl_runtime_health_observability_tail_readback_ref"
        in runtime_health_tail["required_ref_families"]
    )
    assert (
        "runtime_health_kernel_opl_observability_live_readback_ref"
        in runtime_health_tail["required_ref_families"]
    )
    assert (
        "runtime_health_kernel_opl_route_reconciler_live_readback_ref"
        in runtime_health_tail["required_ref_families"]
    )
    assert (
        "mas_runtime_health_snapshot_as_opl_observability_readback"
        in runtime_health_tail["forbidden_completion_interpretations"]
    )
    assert (
        "runtime_health_kernel_no_active_diagnostic_projection_caller_physical_delete_ref"
        in runtime_health_tail["required_ref_families"]
    )
    assert (
        "runtime_health_snapshot_reader_as_opl_observability_readback"
        in runtime_health_tail["forbidden_completion_interpretations"]
    )
    assert (
        "active_diagnostic_projection_scan_as_physical_delete"
        in runtime_health_tail["forbidden_completion_interpretations"]
    )
    workbench_tail = evidence_tails[
        "progress_portal_study_workbench_overview_action_projection"
    ]
    assert (
        "progress_portal_study_workbench_overview_action_projection_"
        "opl_workbench_shell_readback_tail_ref"
        in workbench_tail["required_ref_families"]
    )
    assert (
        "progress_portal_study_workbench_overview_action_projection_"
        "opl_workbench_shell_action_transport_readback_ref"
        in workbench_tail["required_ref_families"]
    )
    assert (
        "progress_portal_study_workbench_overview_action_projection_"
        "opl_current_control_readback_ref"
        in workbench_tail["required_ref_families"]
    )
    assert (
        "mas_next_system_action_summary_as_action_transport_readback"
        in workbench_tail["forbidden_completion_interpretations"]
    )
    assert (
        "operator_intent_refs_as_workbench_action_transport"
        in workbench_tail["forbidden_completion_interpretations"]
    )
    lifecycle_tail = evidence_tails["runtime_lifecycle_payload_retention"]
    assert (
        "runtime_lifecycle_payload_retention_opl_runtime_lifecycle_maintenance_tail_readback_ref"
        in lifecycle_tail["required_ref_families"]
    )
    assert (
        "runtime_lifecycle_payload_retention_opl_runtime_lifecycle_cleanup_policy_live_readback_ref"
        in lifecycle_tail["required_ref_families"]
    )
    assert (
        "opl_maintenance_authorization_as_live_cleanup_policy_takeover"
        in lifecycle_tail["forbidden_completion_interpretations"]
    )
    storage_tail = evidence_tails["runtime_storage_maintenance"]
    assert (
        "runtime_storage_maintenance_opl_runtime_storage_maintenance_tail_readback_ref"
        in storage_tail["required_ref_families"]
    )
    assert (
        "runtime_storage_maintenance_opl_runtime_storage_policy_live_readback_ref"
        in storage_tail["required_ref_families"]
    )
    assert (
        "runtime_storage_maintenance_opl_restore_retention_shell_live_readback_ref"
        in storage_tail["required_ref_families"]
    )
    assert (
        "runtime_storage_apply_gate_as_live_takeover"
        in storage_tail["forbidden_completion_interpretations"]
    )
    arsenal_tail = evidence_tails["agent_tool_arsenal_scientific_capability_registry"]
    assert (
        "agent_tool_arsenal_scientific_capability_registry_live_owner_consumption_soak_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_scientific_capability_registry_direct_hosted_parity_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_live_owner_consumption_soak_and_direct_hosted_parity_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_live_owner_consumption_soak_current_owner_delta_readback_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_explicit_capability_request_resolution_live_readback_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_direct_hosted_tool_invocation_runtime_parity_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "agent_tool_arsenal_no_active_registry_projection_caller_scan_ref"
        in arsenal_tail["required_ref_families"]
    )
    assert (
        "capability_registry_contract_as_live_owner_consumption_soak"
        in arsenal_tail["forbidden_completion_interpretations"]
    )
    assert (
        "hosted_opl_runtime_requirement_as_direct_hosted_parity"
        in arsenal_tail["forbidden_completion_interpretations"]
    )
    assert (
        "wildcard_guard_as_live_owner_consumption_soak"
        in arsenal_tail["forbidden_completion_interpretations"]
    )
    assert (
        "mcp_or_cli_mode_coverage_as_direct_hosted_parity"
        in arsenal_tail["forbidden_completion_interpretations"]
    )
    assert (
        "capability_request_projection_as_paper_progress"
        in arsenal_tail["forbidden_completion_interpretations"]
    )
    assert (
        "registry_projection_no_active_scan_as_physical_delete"
        in arsenal_tail["forbidden_completion_interpretations"]
    )
    assert layers["physical_retirement"]["status"] == "evidence_required"
    assert layers["physical_retirement"]["allowed"] is False
    assert "domain_owner_action_dispatch" in layers["physical_retirement"]["blocked_surface_ids"]
    assert {
        "domain_health_diagnostic_obligation_actuator",
        "runtime_health_kernel",
        "progress_portal_study_workbench_overview_action_projection",
        "agent_tool_arsenal_scientific_capability_registry",
        "runtime_lifecycle_payload_retention",
        "runtime_storage_maintenance",
    } <= {item["surface_id"] for item in layers["physical_retirement"]["open_surface_tails"]}
    assert audit["repo_no_authority_guard_satisfied"] is True
    assert audit["live_soak_or_no_active_caller_proven"] is False
    assert audit["physical_delete_allowed"] is False
    assert (
        "repo_source_retirement_as_live_runtime_ready"
        in audit["forbidden_completion_interpretations"]
    )
    assert (
        "live_runtime_tail_open_as_repo_source_delete_blocker"
        in audit["forbidden_completion_interpretations"]
    )
    assert audit["violations"] == []
    assert "active_caller_exists_as_retention_reason" in audit["forbidden_completion_interpretations"]
    assert "maintenance_apply_gate_as_paper_progress" in audit["forbidden_completion_interpretations"]

    inventory_surfaces = {surface["surface_id"]: surface for surface in inventory["surfaces"]}
    legacy_helper_scan = inventory_surfaces["domain_authority_refs_index"][
        "opl_state_index_takeover_bridge"
    ]["legacy_helper_active_caller_scan"]
    open_surfaces = {surface["surface_id"]: surface for surface in audit["open_surfaces"]}
    assert "domain_authority_refs_index" not in open_surfaces
    assert "default_executor_dispatch_request" not in open_surfaces
    assert "default_executor_execution_latest_wire_projection" not in open_surfaces
    refs_inventory = inventory_surfaces["domain_authority_refs_index"]
    assert refs_inventory["current_disposition"] == "physically_retired"
    assert refs_inventory["retirement_gate"]["repo_source_physical_retirement_authorized"] is True
    assert legacy_helper_scan["no_active_replay_or_local_inspection_caller_proven"] is True
    assert legacy_helper_scan["physical_delete_allowed"] is False
    assert (
        "legacy_helper_no_active_scan_as_physical_delete"
        in legacy_helper_scan["forbidden_completion_claims"]
    )
    legacy_carrier_inventory = inventory_surfaces["default_executor_dispatch_request"]
    assert legacy_carrier_inventory["current_disposition"] == "physically_retired"
    assert (
        legacy_carrier_inventory["retirement_gate"][
            "repo_source_physical_retirement_authorized"
        ]
        is True
    )
    assert (
        legacy_carrier_inventory["opl_default_executor_carrier_tail_readback"]
        == DEFAULT_EXECUTOR_CARRIER_TAIL_READBACK
    )
    assert legacy_carrier_inventory["legacy_source_contamination_boundary"] == {
        "source_dispatch_claims_are_diagnostic_only": True,
        "source_dispatch_claimed_mas_authority_field": "source_dispatch_claimed_mas_authority",
        "source_dispatch_claimed_opl_write_field": "source_dispatch_claimed_opl_write",
        "source_dispatch_claimed_provider_admission_pending_field": (
            "source_dispatch_claimed_provider_admission_pending"
        ),
        "receipt_projection_must_force_authority_flags_false": True,
        "receipt_projection_must_force_provider_admission_pending_false": True,
        "owner_callable_adapter_boundary_must_force_authority_false": True,
        "polluted_source_payload_can_authorize_provider_admission": False,
        "polluted_source_payload_can_create_opl_event_outbox_or_stage_run": False,
        "polluted_source_payload_can_satisfy_opl_readback": False,
        "forbidden_source_claims": [
            "mas_dispatch_authority",
            "mas_creates_opl_outbox",
            "mas_creates_opl_event",
            "mas_creates_opl_stage_run",
            "provider_admission_pending",
        ],
    }
    assert open_surfaces["domain_health_diagnostic_obligation_actuator"]["authority_status"] == (
        "consume_only_readback_projection_live_tail_open"
    )
    assert open_surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_actuator_tail_status"
    ] == "tail_open"
    assert open_surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_actuator_tail_readback_proven"
    ] is False
    assert open_surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_actuator_no_active_caller_proven"
    ] is False
    assert open_surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_actuator_physical_delete_allowed"
    ] is False
    assert open_surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_actuator_required_active_caller_readback_count"
    ] == 2
    assert open_surfaces["runtime_health_kernel"]["authority_status"] == (
        "read_only_projection_no_authority"
    )
    assert open_surfaces["runtime_health_kernel"]["runtime_health_tail_status"] == "tail_open"
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_tail_readback_proven"
    ] is False
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_no_active_caller_proven"
    ] is False
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_physical_delete_allowed"
    ] is False
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_required_active_caller_readback_count"
    ] == 2
    runtime_health_active_scan = inventory_surfaces["runtime_health_kernel"][
        "opl_runtime_health_observability_tail_readback"
    ]["active_diagnostic_projection_caller_scan"]
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_active_diagnostic_projection_caller_count"
    ] == len(runtime_health_active_scan["active_callers"])
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_active_diagnostic_projection_no_active_caller_proven"
    ] is False
    assert open_surfaces["runtime_health_kernel"][
        "runtime_health_active_diagnostic_projection_physical_delete_allowed"
    ] is False
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["authority_status"] == "read_only_workbench_projection_opl_shell_tail_open"
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["allowed_effect"] == "read_only_owner_delta_summary"
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["workbench_tail_status"] == "tail_open"
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["workbench_tail_readback_proven"] is False
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["workbench_no_active_caller_proven"] is False
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["workbench_physical_delete_allowed"] is False
    assert open_surfaces[
        "progress_portal_study_workbench_overview_action_projection"
    ]["workbench_required_active_caller_readback_count"] == 3
    assert open_surfaces["domain_owner_action_dispatch"]["authority_status"] == (
        "opl_authorized_owner_callable_adapter_live_tail_open"
    )
    assert open_surfaces["domain_owner_action_dispatch"][
        "domain_owner_action_dispatch_live_soak_status"
    ] == "live_every_active_caller_soak_tail_open"
    assert open_surfaces["domain_owner_action_dispatch"][
        "domain_owner_action_dispatch_live_every_active_caller_soak_proven"
    ] is False
    assert open_surfaces["domain_owner_action_dispatch"][
        "domain_owner_action_dispatch_no_active_caller_proven"
    ] is False
    assert open_surfaces["domain_owner_action_dispatch"][
        "domain_owner_action_dispatch_physical_delete_allowed"
    ] is False
    assert open_surfaces["domain_owner_action_dispatch"][
        "domain_owner_action_dispatch_active_caller_family_count"
    ] >= 7
    legacy_latest_inventory = inventory_surfaces[
        "default_executor_execution_latest_wire_projection"
    ]
    assert legacy_latest_inventory["current_disposition"] == "physically_retired"
    assert (
        legacy_latest_inventory["legacy_stage_run_abi_boundary"]["abi_role"]
        == "opl_stagerun_closeout_provenance_identity_recovery_only"
    )
    assert (
        legacy_latest_inventory["legacy_stage_run_abi_boundary"][
            "stage_closeout_packets_can_authorize_provider_admission"
        ]
        is False
    )
    assert (
        legacy_latest_inventory["legacy_stage_run_abi_boundary"][
            "stage_closeout_packets_can_authorize_execution"
        ]
        is False
    )
    assert open_surfaces["runtime_storage_maintenance"]["apply_authorization_surface"] == (
        "opl_runtime_storage_maintenance_authorization"
    )
    assert open_surfaces["runtime_lifecycle_payload_retention"]["authority_status"] == (
        "opl_authorized_maintenance_callable_adapter_live_tail_open"
    )
    assert open_surfaces["runtime_lifecycle_payload_retention"]["allowed_effect"] == (
        "mutate_only_when_bound_opl_maintenance_authorization_is_present"
    )
    assert open_surfaces["runtime_lifecycle_payload_retention"][
        "apply_authorization_surface"
    ] == "opl_runtime_lifecycle_maintenance_authorization"
    assert open_surfaces["runtime_lifecycle_payload_retention"][
        "runtime_lifecycle_maintenance_tail_status"
    ] == "tail_open"
    assert open_surfaces["runtime_lifecycle_payload_retention"][
        "runtime_lifecycle_maintenance_tail_readback_proven"
    ] is False
    assert open_surfaces["runtime_lifecycle_payload_retention"][
        "runtime_lifecycle_maintenance_no_active_caller_proven"
    ] is False
    assert open_surfaces["runtime_lifecycle_payload_retention"][
        "runtime_lifecycle_maintenance_physical_delete_allowed"
    ] is False
    assert open_surfaces["runtime_lifecycle_payload_retention"][
        "runtime_lifecycle_maintenance_required_active_caller_readback_count"
    ] == 2
    assert open_surfaces["runtime_storage_maintenance"]["authority_status"] == (
        "opl_authorized_maintenance_callable_adapter_live_tail_open"
    )
    assert open_surfaces["runtime_storage_maintenance"]["allowed_effect"] == (
        "mutate_only_when_bound_opl_maintenance_authorization_is_present"
    )
    assert open_surfaces["runtime_storage_maintenance"][
        "runtime_storage_maintenance_tail_status"
    ] == "tail_open"
    assert open_surfaces["runtime_storage_maintenance"][
        "runtime_storage_maintenance_tail_readback_proven"
    ] is False
    assert open_surfaces["runtime_storage_maintenance"][
        "runtime_storage_maintenance_no_active_caller_proven"
    ] is False
    assert open_surfaces["runtime_storage_maintenance"][
        "runtime_storage_maintenance_physical_delete_allowed"
    ] is False
    assert open_surfaces["runtime_storage_maintenance"][
        "runtime_storage_maintenance_required_active_caller_readback_count"
    ] == 3
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "authority_status"
    ] == "opl_capability_runtime_projection_live_owner_soak_tail_open"
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "allowed_effect"
    ] == "current_owner_delta_bound_capability_projection_explicit_request_only"
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "agent_tool_arsenal_live_owner_consumption_soak_status"
    ] == "live_owner_consumption_soak_and_direct_hosted_parity_tail_open"
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "agent_tool_arsenal_live_owner_consumption_soak_proven"
    ] is False
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "agent_tool_arsenal_direct_hosted_parity_proven"
    ] is False
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "agent_tool_arsenal_no_active_caller_proven"
    ] is False
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "agent_tool_arsenal_physical_delete_allowed"
    ] is False
    assert open_surfaces["agent_tool_arsenal_scientific_capability_registry"][
        "agent_tool_arsenal_required_active_caller_readback_count"
    ] == 3
    assert all(surface["active_caller_retains_authority"] is False for surface in open_surfaces.values())
    assert all(
        surface["active_caller_retains_runtime_authority"] is False
        for surface in open_surfaces.values()
    )
    assert open_surfaces["domain_owner_action_dispatch"][
        "domain_owner_action_dispatch_active_caller_family_count"
    ] == 7
