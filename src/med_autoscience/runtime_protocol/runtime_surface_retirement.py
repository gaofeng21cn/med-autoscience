from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.private_runtime_residue_validators import (
    audit_workbench_projection_fields as _audit_workbench_projection_fields,
    validate_domain_health_diagnostic_obligation_actuator as _validate_domain_health_diagnostic_obligation_actuator,
    validate_domain_action_request_materializer_surface as _validate_domain_action_request_materializer_surface,
    validate_domain_owner_action_dispatch as _validate_domain_owner_action_dispatch,
    validate_progress_portal_study_workbench_overview_action_projection as _validate_progress_portal_study_workbench_overview_action_projection,
    validate_runtime_lifecycle_payload_retention as _validate_runtime_lifecycle_payload_retention,
    validate_runtime_storage_maintenance as _validate_runtime_storage_maintenance,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.completion_evidence_layers import (
    completion_evidence_layers as _completion_evidence_layers,
)


SURFACE_KIND = "mas_runtime_surface_retirement_no_authority_audit"
SCHEMA_VERSION = 1

GENERIC_RUNTIME_OWNER = "one-person-lab"
FORBIDDEN_TRUE_AUTHORITY_FLAGS = frozenset(
    {
        "can_create_opl_command",
        "can_create_opl_event",
        "can_create_opl_outbox",
        "can_create_opl_stage_run",
        "can_generate_next_action_authority",
        "can_authorize_provider_admission",
        "can_authorize_quality_verdict",
        "can_authorize_publication_ready",
        "can_authorize_generic_cleanup_policy",
        "can_authorize_artifact_mutation",
        "can_claim_runtime_currentness",
        "can_claim_paper_progress",
        "can_write_domain_truth",
        "can_write_publication_eval",
        "can_write_controller_decision",
        "started_worker",
        "outbox_record",
        "stores_body",
        "stores_domain_truth",
        "mas_can_authorize_provider_admission",
        "mas_can_create_opl_outbox_event_or_stage_run",
        "mas_can_create_opl_command_event_or_outbox",
        "mas_can_choose_supervisor_decision",
        "mas_can_mutate_recovery_obligation_store",
        "mas_can_run_supervisor_decision_engine",
        "paper_recovery_state_can_build_decision",
        "read_model_can_run_supervisor_decision_engine",
        "study_progress_supervisor_projection_can_build_decision",
        "actuator_can_write_private_blocker_surface",
        "active_caller_retains_authority",
        "active_caller_retains_runtime_authority",
        "can_write_fail_closed_typed_control_blocker",
        "closeout_binding_authorizes_execution",
        "actuator_private_write_authority",
        "stage_closeout_packets_can_authorize_provider_admission",
        "stage_closeout_packets_can_authorize_execution",
        "stage_closeout_packets_can_create_provider_attempt",
        "stage_closeout_packets_can_create_opl_event_outbox_or_stage_run",
        "stage_closeout_packets_can_claim_running_or_progress",
        "stage_closeout_packets_can_satisfy_current_receipt_without_owner_result",
        "dispatch_ref_stage_packet_identity_recovery_is_authority",
        "latest_wire_surface_is_stage_run_abi",
        "mas_selector_authority",
        "mas_tool_invocation_runtime_authority",
        "polluted_source_payload_can_authorize_provider_admission",
        "polluted_source_payload_can_create_opl_event_outbox_or_stage_run",
        "polluted_source_payload_can_satisfy_opl_readback",
        "wildcard_action_triggers_auto_select",
        "wildcard_action_triggers_can_select_without_explicit_capability_request",
        "missing_explicit_capability_request_can_auto_select_wildcard_sidecar",
        "wildcard_sidecar_can_block_current_owner_action",
    }
)


def audit_runtime_surface_retirement_inventory(
    inventory: Mapping[str, Any],
) -> dict[str, Any]:
    surfaces = _surfaces(inventory)
    open_surfaces = [
        surface
        for surface in surfaces
        if surface.get("current_disposition") != "physically_retired"
    ]
    surface_audits = [_audit_surface(surface) for surface in open_surfaces]
    violations = validate_runtime_surface_retirement_inventory(inventory)
    evidence_layers = _completion_evidence_layers(
        open_surfaces,
        surface_audits=surface_audits,
        violations=violations,
    )
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": (
            "repo_no_authority_guard_landed_live_physical_retirement_tail_open"
            if not violations
            else "authority_boundary_violation"
        ),
        "generic_runtime_owner": GENERIC_RUNTIME_OWNER,
        "open_surface_count": len(open_surfaces),
        "open_surface_ids": [surface["surface_id"] for surface in open_surfaces],
        "open_surfaces": surface_audits,
        "no_active_authority_caller_proven": not violations,
        "repo_no_authority_guard_satisfied": evidence_layers["repo_no_authority_guard"][
            "status"
        ]
        == "satisfied_with_repo_evidence",
        "live_soak_or_no_active_caller_proven": evidence_layers[
            "live_soak_or_no_active_caller"
        ]["proven"],
        "physical_delete_allowed": evidence_layers["physical_retirement"]["allowed"],
        "completion_evidence_layers": evidence_layers,
        "completion_claim_allowed": False,
        "physical_retirement_tail_open": True,
        "violations": violations,
        "forbidden_completion_interpretations": [
            "active_caller_exists_as_retention_reason",
            "active_caller_migrated_as_physical_retirement",
            "inventory_entry_updated_as_live_takeover",
            "focused_tests_green_as_runtime_ready",
            "repo_no_authority_guard_satisfied_without_live_soak",
            "maintenance_apply_gate_as_paper_progress",
            "read_only_projection_as_execution_authority",
        ],
    }


def validate_runtime_surface_retirement_inventory(
    inventory: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    for surface in _surfaces(inventory):
        surface_id = _text(surface.get("surface_id")) or "<missing>"
        if surface.get("generic_runtime_owner") != GENERIC_RUNTIME_OWNER:
            violations.append(_violation(surface_id, "generic_runtime_owner_not_opl"))
        if surface.get("mas_owner_claim_allowed") is not False:
            violations.append(_violation(surface_id, "mas_owner_claim_allowed_not_false"))
        if surface.get("compatibility_alias_allowed") is not False:
            violations.append(_violation(surface_id, "compatibility_alias_allowed_not_false"))
        forbidden_claims = surface.get("forbidden_claims")
        if not isinstance(forbidden_claims, list) or "mas_owned_generic_runtime" not in forbidden_claims:
            violations.append(_violation(surface_id, "missing_mas_owned_generic_runtime_forbidden_claim"))
        if isinstance(forbidden_claims, list) and "provider_completion_as_domain_ready" not in forbidden_claims:
            violations.append(_violation(surface_id, "missing_provider_completion_forbidden_claim"))
        for flag_path in _truthy_authority_flags(surface):
            violations.append(_violation(surface_id, f"truthy_authority_flag:{flag_path}"))
        if surface_id == "default_executor_dispatch_request":
            violations.extend(_validate_legacy_default_executor_carrier(surface_id, surface))
        if surface_id == "default_executor_execution_latest_wire_projection":
            violations.extend(_validate_legacy_latest_wire(surface_id, surface))
            violations.extend(_validate_legacy_stage_run_abi(surface_id, surface))
        if surface_id == "domain_authority_refs_index":
            violations.extend(_validate_domain_authority_refs_index(surface_id, surface))
        if surface_id.startswith("domain_action_request_materializer_"):
            violations.extend(_validate_domain_action_request_materializer_surface(surface_id, surface))
        if surface_id == "domain_owner_action_dispatch":
            violations.extend(_validate_domain_owner_action_dispatch(surface_id, surface))
        if surface_id == "domain_health_diagnostic_obligation_actuator":
            violations.extend(_validate_domain_health_diagnostic_obligation_actuator(surface_id, surface))
        if surface_id == "runtime_health_kernel":
            violations.extend(_validate_runtime_health_kernel(surface_id, surface))
        if surface_id == "agent_tool_arsenal_scientific_capability_registry":
            violations.extend(_validate_agent_tool_arsenal_scientific_capability_registry(surface_id, surface))
        if surface_id == "progress_portal_study_workbench_overview_action_projection":
            violations.extend(_validate_progress_portal_study_workbench_overview_action_projection(surface_id, surface))
        if surface_id == "runtime_lifecycle_payload_retention":
            violations.extend(_validate_runtime_lifecycle_payload_retention(surface_id, surface))
        if surface_id == "runtime_storage_maintenance":
            violations.extend(_validate_runtime_storage_maintenance(surface_id, surface))
        if surface.get("current_disposition") != "physically_retired":
            violations.extend(_validate_open_surface(surface_id, surface))
    return violations


def _validate_open_surface(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("active_caller_alone_retains_surface") is not False:
            violations.append(_violation(surface_id, "active_caller_alone_can_retain_surface"))
        if gate.get("completion_claim_requires_live_owner_or_opl_readback") is not True:
            violations.append(_violation(surface_id, "missing_live_owner_or_opl_readback_completion_gate"))
        if gate.get("replacement_parity_required") is not True:
            violations.append(_violation(surface_id, "missing_replacement_parity_gate"))
        if gate.get("tombstone_or_provenance_required") is not True:
            violations.append(_violation(surface_id, "missing_tombstone_or_provenance_gate"))
    active_boundary = surface.get("active_caller_boundary")
    if isinstance(active_boundary, Mapping):
        if active_boundary.get("active_caller_retains_authority", False) is not False:
            violations.append(_violation(surface_id, "active_caller_retains_authority"))
        if active_boundary.get("active_caller_retains_runtime_authority", False) is not False:
            violations.append(_violation(surface_id, "active_caller_retains_runtime_authority"))
        if active_boundary.get("completion_claim_requires_live_owner_or_opl_readback") is not True:
            violations.append(_violation(surface_id, "active_boundary_missing_live_completion_gate"))
        if active_boundary.get("request_projection_only_can_satisfy_success", False) is not False:
            violations.append(_violation(surface_id, "request_projection_can_satisfy_success"))
        if active_boundary.get("default_sqlite_persistence", False) is not False:
            violations.append(_violation(surface_id, "default_sqlite_persistence_enabled"))
    apply_gate = surface.get("apply_gate")
    if isinstance(apply_gate, Mapping):
        if not _text(apply_gate.get("proof_surface")):
            violations.append(_violation(surface_id, "apply_gate_missing_proof_surface"))
        if not _text(apply_gate.get("typed_blocker")):
            violations.append(_violation(surface_id, "apply_gate_missing_typed_blocker"))
    if "legacy_caller_exists" in str(surface.get("retention_reason", "")):
        violations.append(_violation(surface_id, "legacy_caller_used_as_retention_reason"))
    return violations


def _validate_legacy_latest_wire(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("legacy_wire_default_reader_fallback_allowed") is not False:
        violations.append(_violation(surface_id, "legacy_default_reader_fallback_allowed"))
    if surface.get("legacy_wire_current_reader_fallback_allowed") is not False:
        violations.append(_violation(surface_id, "legacy_current_reader_fallback_allowed"))
    if surface.get("legacy_wire_history_replay_fallback_requires_explicit_opt_in") is not True:
        violations.append(_violation(surface_id, "legacy_history_replay_not_explicit_opt_in"))
    if surface.get("legacy_wire_history_merge_requires_explicit_opt_in") is not True:
        violations.append(_violation(surface_id, "legacy_history_merge_not_explicit_opt_in"))
    current_boundary = surface.get("current_reader_boundary")
    if isinstance(current_boundary, Mapping):
        for key in (
            "current_provider_admission_reads_legacy_wire",
            "current_provider_handoff_export_reads_legacy_wire",
            "current_recovery_action_reads_legacy_wire",
            "default_execution_latest_payload_reads_legacy_wire_by_default",
            "default_executor_execution_candidates_reads_legacy_wire_by_default",
            "default_executor_receipt_consumption_reads_legacy_wire_by_default",
            "default_executor_nonconsumable_closeout_reads_legacy_wire_by_default",
        ):
            if current_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"current_reader_legacy_fallback:{key}"))
    else:
        violations.append(_violation(surface_id, "missing_current_reader_boundary"))
    replay_boundary = surface.get("history_replay_boundary")
    if isinstance(replay_boundary, Mapping):
        for key in (
            "default_executor_execution_candidates_requires_allow_legacy_fallback",
            "default_executor_receipt_consumption_requires_allow_legacy_fallback",
            "default_executor_nonconsumable_closeout_requires_allow_legacy_fallback",
            "execution_latest_payload_requires_allow_legacy_fallback",
            "legacy_latest_payload_helper_requires_allow_legacy_fallback",
        ):
            if replay_boundary.get(key) is not True:
                violations.append(_violation(surface_id, f"history_replay_missing_explicit_opt_in:{key}"))
    else:
        violations.append(_violation(surface_id, "missing_history_replay_boundary"))
    return violations


def _validate_legacy_stage_run_abi(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    boundary = surface.get("legacy_stage_run_abi_boundary")
    if not isinstance(boundary, Mapping):
        return [_violation(surface_id, "missing_legacy_stage_run_abi_boundary")]
    if boundary.get("abi_role") != "opl_stagerun_closeout_provenance_identity_recovery_only":
        violations.append(_violation(surface_id, "legacy_stage_run_abi_role_not_provenance_only"))
    if boundary.get("stage_id") != "domain_owner/default-executor-dispatch":
        violations.append(_violation(surface_id, "legacy_stage_run_abi_stage_id_not_bound"))
    if boundary.get("latest_wire_surface_is_stage_run_abi") is not False:
        violations.append(_violation(surface_id, "legacy_latest_wire_misclassified_as_stage_run_abi"))
    if boundary.get("stage_closeout_packets_are_latest_wire_fallback") is not False:
        violations.append(_violation(surface_id, "stage_closeout_packets_are_latest_wire_fallback"))
    for key in (
        "stage_closeout_packets_can_authorize_provider_admission",
        "stage_closeout_packets_can_authorize_execution",
        "stage_closeout_packets_can_create_provider_attempt",
        "stage_closeout_packets_can_create_opl_event_outbox_or_stage_run",
        "stage_closeout_packets_can_claim_running_or_progress",
        "stage_closeout_packets_can_satisfy_current_receipt_without_owner_result",
        "dispatch_ref_stage_packet_identity_recovery_is_authority",
    ):
        if boundary.get(key, False) is not False:
            violations.append(_violation(surface_id, f"legacy_stage_run_abi_authority:{key}"))
    if boundary.get("terminal_closeout_consumption_requires_owner_result_or_typed_blocker") is not True:
        violations.append(_violation(surface_id, "stage_closeout_terminal_consumption_not_owner_result_bound"))
    physical_delete_requires_scan = (
        boundary.get("physical_delete_requires_no_active_stage_run_abi_caller_scan") is True
    )
    if not physical_delete_requires_scan:
        violations.append(_violation(surface_id, "stage_closeout_physical_delete_missing_no_active_caller_scan"))
    else:
        violations.extend(_validate_stage_run_abi_active_caller_scan(surface_id, boundary))
    closeout_roots = boundary.get("closeout_packet_roots")
    if not isinstance(closeout_roots, list) or not closeout_roots:
        violations.append(_violation(surface_id, "stage_closeout_packet_roots_missing"))
    allowed = boundary.get("allowed_consumption")
    if not isinstance(allowed, list) or "terminal_closeout_consumption" not in allowed:
        violations.append(_violation(surface_id, "stage_closeout_allowed_consumption_missing_terminal_closeout"))
    return violations


def _validate_stage_run_abi_active_caller_scan(
    surface_id: str,
    boundary: Mapping[str, Any],
) -> list[dict[str, str]]:
    scan = boundary.get("active_stage_run_abi_caller_scan")
    if not isinstance(scan, Mapping):
        return [_violation(surface_id, "stage_closeout_active_caller_scan_missing")]

    violations: list[dict[str, str]] = []
    active_callers = scan.get("active_callers")
    active_caller_list = active_callers if isinstance(active_callers, list) else []
    no_active_proven = scan.get("no_active_stage_run_abi_caller_proven")
    physical_delete_allowed = scan.get("physical_delete_allowed")
    status = _text(scan.get("status"))
    if status == "active_callers_present_tail_open":
        if not active_caller_list:
            violations.append(_violation(surface_id, "stage_closeout_active_caller_scan_empty"))
        if no_active_proven is not False:
            violations.append(_violation(surface_id, "stage_closeout_active_tail_must_not_claim_no_active_callers"))
        if physical_delete_allowed is not False:
            violations.append(_violation(surface_id, "stage_closeout_active_callers_block_physical_delete"))
    if active_caller_list and no_active_proven is True:
        violations.append(_violation(surface_id, "stage_closeout_no_active_claim_contradicts_active_callers"))
    if active_caller_list and physical_delete_allowed is not False:
        violations.append(_violation(surface_id, "stage_closeout_active_callers_block_physical_delete"))
    allowed_consumption = scan.get("allowed_consumption")
    if not isinstance(allowed_consumption, list) or "terminal_closeout_consumption" not in allowed_consumption:
        violations.append(_violation(surface_id, "stage_closeout_active_scan_missing_allowed_consumption"))
    forbidden_claims = scan.get("forbidden_completion_claims")
    if not isinstance(forbidden_claims, list) or "stage_closeout_provenance_only_as_physical_delete" not in forbidden_claims:
        violations.append(_violation(surface_id, "stage_closeout_active_scan_missing_false_completion_guard"))
    if (
        _text(scan.get("required_before_physical_delete"))
        != "legacy_default_executor_carrier_no_active_stage_run_abi_caller_physical_delete_ref"
    ):
        violations.append(_violation(surface_id, "stage_closeout_active_scan_missing_physical_delete_ref"))
    return violations


def _validate_legacy_default_executor_carrier(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    active_boundary = surface.get("active_caller_boundary")
    if isinstance(active_boundary, Mapping):
        if active_boundary.get("active_caller_effect") != "opl_domain_progress_transition_runtime_intake_only":
            violations.append(_violation(surface_id, "legacy_carrier_active_effect_not_opl_intake_only"))
        for key in (
            "active_caller_retains_authority",
            "active_caller_retains_runtime_authority",
            "active_caller_retains_surface",
            "provider_admission_pending",
            "provider_attempt_or_lease_required",
        ):
            if active_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"legacy_carrier_active_boundary_forbidden:{key}"))
        if active_boundary.get("transition_request_pending_only") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_not_transition_request_pending_only"))
        if active_boundary.get("completion_claim_requires_live_owner_or_opl_readback") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_missing_live_readback_completion_gate"))
    else:
        violations.append(_violation(surface_id, "missing_legacy_carrier_active_caller_boundary"))

    abi_boundary = surface.get("legacy_stage_run_abi_provenance_boundary")
    if isinstance(abi_boundary, Mapping):
        if abi_boundary.get("carrier_kind") != "opl_domain_progress_transition_request_carrier":
            violations.append(_violation(surface_id, "legacy_carrier_kind_not_opl_transition_request"))
        if abi_boundary.get("task_kind_retained_for_opl_stage_run_abi") != "domain_owner/default-executor-dispatch":
            violations.append(_violation(surface_id, "legacy_carrier_missing_stage_run_abi_task_kind"))
        for key in (
            "mas_can_create_stage_run",
            "mas_can_mark_provider_admission",
            "mas_can_mark_provider_running",
            "provider_admission_pending",
        ):
            if abi_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"legacy_stage_run_abi_forbidden:{key}"))
        if abi_boundary.get("requires_opl_domain_progress_transition_runtime_intake") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_missing_opl_runtime_intake_requirement"))
        if abi_boundary.get("provenance_only_until_opl_readback") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_not_provenance_only_until_readback"))
        if abi_boundary.get("transition_request_pending_only") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_abi_not_transition_request_pending_only"))
    else:
        violations.append(_violation(surface_id, "missing_legacy_stage_run_abi_provenance_boundary"))

    contamination_boundary = surface.get("legacy_source_contamination_boundary")
    if isinstance(contamination_boundary, Mapping):
        if contamination_boundary.get("source_dispatch_claims_are_diagnostic_only") is not True:
            violations.append(_violation(surface_id, "legacy_source_claims_not_diagnostic_only"))
        expected_claim_fields = {
            "source_dispatch_claimed_mas_authority_field": "source_dispatch_claimed_mas_authority",
            "source_dispatch_claimed_opl_write_field": "source_dispatch_claimed_opl_write",
            "source_dispatch_claimed_provider_admission_pending_field": (
                "source_dispatch_claimed_provider_admission_pending"
            ),
        }
        for key, expected in expected_claim_fields.items():
            if contamination_boundary.get(key) != expected:
                violations.append(_violation(surface_id, f"legacy_source_claim_field_mismatch:{key}"))
        for key in (
            "receipt_projection_must_force_authority_flags_false",
            "receipt_projection_must_force_provider_admission_pending_false",
            "owner_callable_adapter_boundary_must_force_authority_false",
        ):
            if contamination_boundary.get(key) is not True:
                violations.append(_violation(surface_id, f"legacy_source_boundary_missing_force_false:{key}"))
        for key in (
            "polluted_source_payload_can_authorize_provider_admission",
            "polluted_source_payload_can_create_opl_event_outbox_or_stage_run",
            "polluted_source_payload_can_satisfy_opl_readback",
        ):
            if contamination_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"legacy_source_boundary_forbidden:{key}"))
        forbidden_source_claims = contamination_boundary.get("forbidden_source_claims")
        required_source_claims = {
            "mas_dispatch_authority",
            "mas_creates_opl_outbox",
            "mas_creates_opl_event",
            "mas_creates_opl_stage_run",
            "provider_admission_pending",
        }
        if not isinstance(forbidden_source_claims, list) or not required_source_claims.issubset(
            {str(item) for item in forbidden_source_claims}
        ):
            violations.append(_violation(surface_id, "legacy_source_boundary_missing_forbidden_source_claims"))
    else:
        violations.append(_violation(surface_id, "missing_legacy_source_contamination_boundary"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("repo_stage_run_abi_provenance_proven") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_repo_stage_run_abi_provenance_not_proven"))
        if gate.get("no_active_authority_caller_proven") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_no_active_authority_caller_not_proven"))
    else:
        violations.append(_violation(surface_id, "missing_legacy_carrier_retirement_gate"))
    return violations


def _validate_domain_authority_refs_index(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    bridge = surface.get("opl_state_index_takeover_bridge")
    if not isinstance(bridge, Mapping):
        return [_violation(surface_id, "missing_opl_state_index_takeover_bridge")]
    scan = bridge.get("legacy_helper_active_caller_scan")
    if not isinstance(scan, Mapping):
        return [_violation(surface_id, "domain_authority_refs_legacy_helper_scan_missing")]
    runtime_scan = bridge.get("runtime_active_private_state_index_caller_scan")
    if not isinstance(runtime_scan, Mapping):
        violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_scan_missing"))
    else:
        runtime_status = _text(runtime_scan.get("status"))
        runtime_callers = runtime_scan.get("active_runtime_callers")
        runtime_caller_list = runtime_callers if isinstance(runtime_callers, list) else []
        if runtime_status != "no_runtime_active_private_state_index_callers":
            violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_scan_not_clear"))
        if runtime_scan.get("no_runtime_active_private_state_index_caller_proven") is not True:
            violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_no_private_caller_not_proven"))
        if runtime_scan.get("runtime_active_caller_count") != 0:
            violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_caller_count_not_zero"))
        if runtime_caller_list:
            violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_private_callers_present"))
        if runtime_scan.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_scan_must_not_allow_physical_delete"))
        runtime_forbidden_claims = runtime_scan.get("forbidden_completion_claims")
        if (
            not isinstance(runtime_forbidden_claims, list)
            or "runtime_active_no_private_caller_as_physical_delete"
            not in runtime_forbidden_claims
        ):
            violations.append(_violation(surface_id, "domain_authority_refs_runtime_active_scan_missing_false_completion_guard"))

    active_callers = scan.get("active_callers")
    active_caller_list = active_callers if isinstance(active_callers, list) else []
    no_active_proven = scan.get("no_active_replay_or_local_inspection_caller_proven")
    physical_delete_allowed = scan.get("physical_delete_allowed")
    status = _text(scan.get("status"))
    if status == "active_replay_or_local_inspection_callers_present_tail_open":
        if not active_caller_list:
            violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_scan_empty"))
        if no_active_proven is not False:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_active_tail_must_not_claim_no_active_replay_local_inspection_callers",
                )
            )
        if physical_delete_allowed is not False:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_active_replay_local_inspection_callers_block_physical_delete",
                )
            )
    if active_caller_list and no_active_proven is True:
        violations.append(
            _violation(
                surface_id,
                "domain_authority_refs_no_active_claim_contradicts_active_replay_local_inspection_callers",
            )
        )
    if active_caller_list and physical_delete_allowed is not False:
        violations.append(
            _violation(
                surface_id,
                "domain_authority_refs_active_replay_local_inspection_callers_block_physical_delete",
            )
        )
    forbidden_current_callers = {
        "opl_domain_pack.family_adoption.build_opl_family_adoption_surface::inspect_authority_refs_index",
        "opl_domain_pack.family_adoption.build_product_entry_adoption_projection::sqlite_refs_index_ref",
        "opl_domain_pack.adoption_ref_payload.payload_from_authority_refs::legacy_sqlite_payload_projection",
    }
    if forbidden_current_callers & {str(caller) for caller in active_caller_list}:
        violations.append(
            _violation(
                surface_id,
                "domain_authority_refs_family_adoption_legacy_sqlite_current_caller",
            )
        )
    allowed_consumption = scan.get("allowed_consumption")
    if not isinstance(allowed_consumption, list) or "explicit_history_replay" not in allowed_consumption:
        violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_scan_missing_allowed_consumption"))
    if isinstance(allowed_consumption, list) and "opl_family_adoption_projection" in allowed_consumption:
        violations.append(
            _violation(
                surface_id,
                "domain_authority_refs_legacy_sqlite_allowed_for_current_adoption",
            )
        )
    forbidden_claims = scan.get("forbidden_completion_claims")
    if (
        not isinstance(forbidden_claims, list)
        or "legacy_helper_active_scan_as_physical_delete" not in forbidden_claims
    ):
        violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_scan_missing_false_completion_guard"))
    if (
        not isinstance(forbidden_claims, list)
        or "opl_family_adoption_sqlite_inspection_as_current_projection" not in forbidden_claims
    ):
        violations.append(
            _violation(
                surface_id,
                "domain_authority_refs_legacy_helper_scan_missing_family_adoption_guard",
            )
        )
    if (
        _text(scan.get("required_before_physical_delete"))
        != "domain_authority_refs_index_live_state_index_takeover_or_no_active_replay_local_inspection_caller_physical_delete_ref"
    ):
        violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_scan_missing_physical_delete_ref"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("no_active_replay_or_local_inspection_caller_proven") is not False:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_retirement_gate_must_not_claim_no_active_replay_local_inspection_callers",
                )
            )
        if gate.get("physical_delete_allowed") is not False:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_retirement_gate_must_not_allow_physical_delete",
                )
            )
    else:
        violations.append(_violation(surface_id, "missing_domain_authority_refs_retirement_gate"))
    return violations


def _validate_runtime_health_kernel(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "read_only_diagnostic_publisher":
        violations.append(_violation(surface_id, "runtime_health_not_read_only_diagnostic_publisher"))
    if surface.get("retained_mas_role") != "body_free_runtime_health_diagnostic_projection":
        violations.append(_violation(surface_id, "runtime_health_retained_role_not_body_free_diagnostic_projection"))
    if surface.get("local_event_log_append_from_status_payload") is not False:
        violations.append(_violation(surface_id, "runtime_health_status_payload_can_append_event_log"))
    if surface.get("mas_local_event_append_api_retired") is not True:
        violations.append(_violation(surface_id, "runtime_health_local_event_append_api_not_retired"))
    if surface.get("historical_event_log_role") != "legacy_fixture_and_explicit_archive_import_provenance_input_only":
        violations.append(_violation(surface_id, "runtime_health_history_event_log_not_fixture_only"))
    if surface.get("read_only_actions") != ["read_runtime_status", "open_monitoring_entry"]:
        violations.append(_violation(surface_id, "runtime_health_read_only_actions_not_minimal"))

    boundary = surface.get("active_caller_boundary")
    if not isinstance(boundary, Mapping):
        violations.append(_violation(surface_id, "runtime_health_missing_active_caller_boundary"))
    else:
        if boundary.get("active_caller_effect") != "body_free_runtime_health_diagnostic_projection":
            violations.append(_violation(surface_id, "runtime_health_active_effect_not_diagnostic_projection"))
        for key in (
            "active_caller_retains_authority",
            "active_caller_retains_runtime_authority",
            "active_caller_retains_surface",
            "local_event_log_append_allowed",
            "runtime_health_epoch_is_currentness_authority",
            "canonical_runtime_action_is_next_action_authority",
        ):
            if boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"runtime_health_active_boundary_forbidden:{key}"))
        for owner_key in (
            "attempt_liveness_owner",
            "retry_dead_letter_owner",
            "worker_residency_owner",
            "provider_liveness_owner",
        ):
            if boundary.get(owner_key) != GENERIC_RUNTIME_OWNER:
                violations.append(_violation(surface_id, f"runtime_health_{owner_key}_not_opl"))
        if boundary.get("completion_claim_requires_live_owner_or_opl_readback") is not True:
            violations.append(_violation(surface_id, "runtime_health_missing_live_readback_completion_gate"))
        if boundary.get("read_only_actions") != ["read_runtime_status", "open_monitoring_entry"]:
            violations.append(_violation(surface_id, "runtime_health_active_boundary_read_only_actions_not_minimal"))
        physical_delete_requires = boundary.get("physical_delete_requires")
        if not isinstance(physical_delete_requires, list) or not {
            "opl_observability_live_readback",
            "opl_route_reconciler_live_readback",
            "no_active_diagnostic_projection_caller_scan",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        } <= set(physical_delete_requires):
            violations.append(_violation(surface_id, "runtime_health_physical_delete_gate_incomplete"))

    projection = surface.get("diagnostic_projection_boundary")
    if not isinstance(projection, Mapping):
        violations.append(_violation(surface_id, "runtime_health_missing_diagnostic_projection_boundary"))
    else:
        if projection.get("projection_role") != "mas_runtime_health_diagnostic_publisher":
            violations.append(_violation(surface_id, "runtime_health_projection_role_not_diagnostic_publisher"))
        for key in (
            "authority",
            "stores_body",
            "stores_domain_truth",
            "started_worker",
            "outbox_record",
            "can_claim_runtime_currentness",
            "can_generate_next_action_authority",
            "can_authorize_provider_admission",
            "can_claim_paper_progress",
            "can_create_opl_command",
            "can_create_opl_event",
            "can_create_opl_outbox",
            "can_create_opl_stage_run",
        ):
            if projection.get(key, False) is not False:
                violations.append(_violation(surface_id, f"runtime_health_projection_forbidden:{key}"))
        required_metadata = projection.get("projection_metadata_required")
        if not isinstance(required_metadata, list) or not set(surface.get("canonical_projection_metadata_fields", [])) <= set(required_metadata):
            violations.append(_violation(surface_id, "runtime_health_projection_metadata_fields_incomplete"))
        for key in (
            "allowed_actions_are_diagnostic_hints",
            "canonical_runtime_action_is_diagnostic_hint",
            "retry_budget_is_diagnostic_hint",
            "attempt_state_is_diagnostic_hint",
            "provider_readiness_is_diagnostic_hint",
        ):
            if projection.get(key) is not True:
                violations.append(_violation(surface_id, f"runtime_health_missing_diagnostic_hint_boundary:{key}"))

    consumer_gate = surface.get("diagnostic_consumer_gate_boundary")
    if not isinstance(consumer_gate, Mapping):
        violations.append(_violation(surface_id, "runtime_health_missing_diagnostic_consumer_gate_boundary"))
    else:
        if consumer_gate.get("consumer_gate") != "runtime_health_decision_gate":
            violations.append(_violation(surface_id, "runtime_health_consumer_gate_not_runtime_health_decision_gate"))
        if consumer_gate.get("decision_authority_owner") != GENERIC_RUNTIME_OWNER:
            violations.append(_violation(surface_id, "runtime_health_consumer_gate_owner_not_opl"))
        if consumer_gate.get("mas_role") != "read_only_diagnostic_consumer":
            violations.append(_violation(surface_id, "runtime_health_consumer_gate_mas_role_not_read_only"))
        for key in (
            "identity_bound_opl_readback_required",
        ):
            if consumer_gate.get(key) is not True:
                violations.append(_violation(surface_id, f"runtime_health_consumer_gate_missing:{key}"))
        for key in (
            "unbound_opl_ref_can_authorize_decision",
            "runtime_health_snapshot_authority_can_authorize_decision",
            "canonical_runtime_action_hint_can_authorize_recovery",
            "worker_liveness_hint_can_authorize_recovery",
        ):
            if consumer_gate.get(key, False) is not False:
                violations.append(_violation(surface_id, f"runtime_health_consumer_gate_forbidden:{key}"))
        if consumer_gate.get("allowed_decision_source") != "opl_runtime_readback":
            violations.append(_violation(surface_id, "runtime_health_consumer_gate_wrong_decision_source"))
        if consumer_gate.get("missing_or_cross_identity_readback_outcome") != (
            "opl_runtime_readback_required_for_runtime_health_decision"
        ):
            violations.append(_violation(surface_id, "runtime_health_consumer_gate_wrong_missing_readback_outcome"))

    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, "runtime_health_missing_retirement_gate"))
    else:
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "runtime_health_missing_no_active_caller_physical_delete_gate"))
        if gate.get("runtime_health_live_opl_observability_readback_required") is not True:
            violations.append(_violation(surface_id, "runtime_health_missing_live_opl_observability_gate"))
    return violations


def _validate_agent_tool_arsenal_scientific_capability_registry(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "opl_capability_runtime_projection":
        violations.append(_violation(surface_id, "capability_registry_not_opl_projection"))
    if surface.get("retained_mas_role") != "capability_planning_projection_and_owner_consumption_evidence_shape":
        violations.append(_violation(surface_id, "capability_registry_retained_role_not_projection"))
    if surface.get("replacement_surface") != "OPL Capability Runtime / Tool Arsenal selector and invocation runtime":
        violations.append(_violation(surface_id, "capability_registry_replacement_not_opl_runtime"))

    authority = surface.get("authority_boundary")
    if not isinstance(authority, Mapping):
        violations.append(_violation(surface_id, "capability_registry_missing_authority_boundary"))
    else:
        for key in (
            "mas_selector_authority",
            "mas_tool_invocation_runtime_authority",
            "can_create_default_selector",
            "can_start_always_on_sidecar",
            "can_authorize_provider_admission",
            "can_authorize_worker_attempt",
            "can_claim_paper_progress",
            "can_write_domain_truth",
            "can_write_publication_eval",
            "can_write_controller_decision",
            "missing_refs_trigger_mutating_invocation",
        ):
            if authority.get(key, False) is not False:
                violations.append(_violation(surface_id, f"capability_registry_authority_forbidden:{key}"))
        if authority.get("selection_runtime_owner") != GENERIC_RUNTIME_OWNER:
            violations.append(_violation(surface_id, "capability_registry_selection_owner_not_opl"))
        if authority.get("capability_runtime_owner") != GENERIC_RUNTIME_OWNER:
            violations.append(_violation(surface_id, "capability_registry_runtime_owner_not_opl"))
        if authority.get("capability_runtime_kind") != "OPL Capability Runtime":
            violations.append(_violation(surface_id, "capability_registry_runtime_kind_not_opl"))
        if authority.get("hosted_opl_capability_runtime_required") is not True:
            violations.append(_violation(surface_id, "capability_registry_missing_hosted_opl_runtime_gate"))

    wildcard = surface.get("wildcard_action_trigger_boundary")
    if not isinstance(wildcard, Mapping):
        violations.append(_violation(surface_id, "capability_registry_missing_wildcard_boundary"))
    else:
        if wildcard.get("wildcard_action_triggers_auto_select") is not False:
            violations.append(_violation(surface_id, "capability_registry_wildcard_auto_select_enabled"))
        if wildcard.get("requires_explicit_capability_request") is not True:
            violations.append(_violation(surface_id, "capability_registry_wildcard_missing_explicit_request_gate"))
        if wildcard.get("wildcard_action_triggers_can_select_without_explicit_capability_request") is not False:
            violations.append(
                _violation(surface_id, "capability_registry_wildcard_can_select_without_explicit_request")
            )
        if wildcard.get("missing_explicit_capability_request_can_auto_select_wildcard_sidecar") is not False:
            violations.append(
                _violation(surface_id, "capability_registry_wildcard_missing_request_can_auto_select")
            )
        if wildcard.get("wildcard_sidecar_can_block_current_owner_action") is not False:
            violations.append(_violation(surface_id, "capability_registry_wildcard_sidecar_can_block_owner_action"))
        explicit_fields = wildcard.get("explicit_request_fields")
        if not isinstance(explicit_fields, list) or not {
            "capability_families",
            "capability_family",
            "route_required_ref_families",
            "route_required_ref_family",
        } <= {str(item) for item in explicit_fields}:
            violations.append(_violation(surface_id, "capability_registry_wildcard_explicit_fields_incomplete"))
        wildcard_capabilities = wildcard.get("wildcard_capabilities")
        if not isinstance(wildcard_capabilities, list) or not {
            "evo_scientist_progress_sidecar",
            "light_external_skill_content_advisory",
        } <= {str(item) for item in wildcard_capabilities}:
            violations.append(_violation(surface_id, "capability_registry_wildcard_capabilities_incomplete"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("live_owner_consumption_soak_required") is not True:
            violations.append(_violation(surface_id, "capability_registry_missing_live_owner_soak_gate"))
        if gate.get("direct_hosted_parity_required") is not True:
            violations.append(_violation(surface_id, "capability_registry_missing_direct_hosted_parity_gate"))
        if gate.get("no_forbidden_write_proof_required") is not True:
            violations.append(_violation(surface_id, "capability_registry_missing_no_forbidden_write_gate"))

    live_soak = surface.get("live_owner_consumption_soak_boundary")
    if not isinstance(live_soak, Mapping):
        violations.append(_violation(surface_id, "capability_registry_missing_live_owner_soak_boundary"))
    else:
        if live_soak.get("status") != "live_owner_consumption_soak_and_direct_hosted_parity_tail_open":
            violations.append(_violation(surface_id, "capability_registry_live_soak_boundary_wrong_status"))
        for key in (
            "live_owner_consumption_soak_proven",
            "direct_hosted_parity_proven",
            "no_active_caller_proven",
            "physical_delete_allowed",
        ):
            if live_soak.get(key, False) is not False:
                violations.append(_violation(surface_id, f"capability_registry_live_soak_claimed:{key}"))
        if (
            live_soak.get("required_before_physical_delete")
            != "agent_tool_arsenal_live_owner_consumption_soak_and_direct_hosted_parity_ref"
        ):
            violations.append(_violation(surface_id, "capability_registry_live_soak_missing_physical_delete_ref"))
        allowed_consumption = live_soak.get("allowed_consumption")
        if not isinstance(allowed_consumption, list) or not {
            "current_owner_delta_bound_capability_projection",
            "explicit_capability_request_resolution_evidence",
        } <= {str(item) for item in allowed_consumption}:
            violations.append(_violation(surface_id, "capability_registry_live_soak_allowed_consumption_incomplete"))
        forbidden_claims = live_soak.get("forbidden_completion_claims")
        if not isinstance(forbidden_claims, list) or not {
            "capability_registry_contract_as_live_owner_consumption_soak",
            "hosted_opl_runtime_requirement_as_direct_hosted_parity",
            "repo_tests_green_as_physical_delete",
        } <= {str(item) for item in forbidden_claims}:
            violations.append(_violation(surface_id, "capability_registry_live_soak_missing_false_completion_guard"))
    return violations


def _audit_surface(surface: Mapping[str, Any]) -> dict[str, Any]:
    active_boundary = surface.get("active_caller_boundary")
    apply_gate = surface.get("apply_gate")
    retirement_gate = surface.get("retirement_gate")
    state_index_bridge = surface.get("opl_state_index_takeover_bridge")
    state_index_scan = (
        state_index_bridge.get("legacy_helper_active_caller_scan")
        if isinstance(state_index_bridge, Mapping)
        else None
    )
    state_index_runtime_scan = (
        state_index_bridge.get("runtime_active_private_state_index_caller_scan")
        if isinstance(state_index_bridge, Mapping)
        else None
    )
    legacy_stage_run_boundary = surface.get("legacy_stage_run_abi_boundary")
    legacy_stage_run_scan = (
        legacy_stage_run_boundary.get("active_stage_run_abi_caller_scan")
        if isinstance(legacy_stage_run_boundary, Mapping)
        else None
    )
    active_caller_soak = surface.get("active_caller_soak_boundary")
    live_owner_consumption_soak = surface.get("live_owner_consumption_soak_boundary")
    return {
        "surface_id": surface["surface_id"],
        "current_disposition": surface["current_disposition"],
        "active_caller_migrated": surface["active_caller_migrated"],
        "retained_mas_role": surface["retained_mas_role"],
        "authority_status": _authority_status(surface),
        "allowed_effect": _allowed_effect(surface),
        "active_caller_retains_authority": (
            active_boundary.get("active_caller_retains_authority", False)
            if isinstance(active_boundary, Mapping)
            else False
        ),
        "active_caller_retains_runtime_authority": (
            active_boundary.get("active_caller_retains_runtime_authority", False)
            if isinstance(active_boundary, Mapping)
            else False
        ),
        "requires_opl_or_owner_readback_for_completion": _requires_readback(surface),
        "physical_delete_gate_open": _physical_delete_gate_open(surface),
        "apply_authorization_surface": (
            apply_gate.get("required_authorization_surface")
            if isinstance(apply_gate, Mapping)
            else None
        ),
        "legacy_stage_run_abi_role": (
            legacy_stage_run_boundary.get("abi_role")
            if isinstance(legacy_stage_run_boundary, Mapping)
            else None
        ),
        "legacy_stage_run_provider_admission_authority": (
            legacy_stage_run_boundary.get("stage_closeout_packets_can_authorize_provider_admission")
            if isinstance(legacy_stage_run_boundary, Mapping)
            else None
        ),
        "legacy_stage_run_execution_authority": (
            legacy_stage_run_boundary.get("stage_closeout_packets_can_authorize_execution")
            if isinstance(legacy_stage_run_boundary, Mapping)
            else None
        ),
        "legacy_stage_run_no_active_caller_proven": (
            legacy_stage_run_scan.get("no_active_stage_run_abi_caller_proven")
            if isinstance(legacy_stage_run_scan, Mapping)
            else None
        ),
        "legacy_stage_run_physical_delete_allowed": (
            legacy_stage_run_scan.get("physical_delete_allowed")
            if isinstance(legacy_stage_run_scan, Mapping)
            else None
        ),
        "legacy_stage_run_active_caller_count": (
            len(legacy_stage_run_scan.get("active_callers"))
            if isinstance(legacy_stage_run_scan, Mapping)
            and isinstance(legacy_stage_run_scan.get("active_callers"), list)
            else None
        ),
        "domain_owner_action_dispatch_live_soak_status": (
            active_caller_soak.get("status") if isinstance(active_caller_soak, Mapping) else None
        ),
        "domain_owner_action_dispatch_live_every_active_caller_soak_proven": (
            active_caller_soak.get("live_every_active_caller_soak_proven")
            if isinstance(active_caller_soak, Mapping)
            else None
        ),
        "domain_owner_action_dispatch_no_active_caller_proven": (
            active_caller_soak.get("no_active_caller_proven")
            if isinstance(active_caller_soak, Mapping)
            else None
        ),
        "domain_owner_action_dispatch_physical_delete_allowed": (
            active_caller_soak.get("physical_delete_allowed")
            if isinstance(active_caller_soak, Mapping)
            else None
        ),
        "domain_owner_action_dispatch_active_caller_family_count": (
            len(active_caller_soak.get("active_caller_families"))
            if isinstance(active_caller_soak, Mapping)
            and isinstance(active_caller_soak.get("active_caller_families"), list)
            else None
        ),
        "agent_tool_arsenal_live_owner_consumption_soak_status": (
            live_owner_consumption_soak.get("status")
            if isinstance(live_owner_consumption_soak, Mapping)
            else None
        ),
        "agent_tool_arsenal_live_owner_consumption_soak_proven": (
            live_owner_consumption_soak.get("live_owner_consumption_soak_proven")
            if isinstance(live_owner_consumption_soak, Mapping)
            else None
        ),
        "agent_tool_arsenal_direct_hosted_parity_proven": (
            live_owner_consumption_soak.get("direct_hosted_parity_proven")
            if isinstance(live_owner_consumption_soak, Mapping)
            else None
        ),
        "agent_tool_arsenal_no_active_caller_proven": (
            live_owner_consumption_soak.get("no_active_caller_proven")
            if isinstance(live_owner_consumption_soak, Mapping)
            else None
        ),
        "agent_tool_arsenal_physical_delete_allowed": (
            live_owner_consumption_soak.get("physical_delete_allowed")
            if isinstance(live_owner_consumption_soak, Mapping)
            else None
        ),
        **_audit_workbench_projection_fields(surface),
        "domain_authority_refs_no_active_replay_local_inspection_caller_proven": (
            state_index_scan.get("no_active_replay_or_local_inspection_caller_proven")
            if isinstance(state_index_scan, Mapping)
            else None
        ),
        "domain_authority_refs_no_runtime_active_private_state_index_caller_proven": (
            state_index_runtime_scan.get(
                "no_runtime_active_private_state_index_caller_proven"
            )
            if isinstance(state_index_runtime_scan, Mapping)
            else None
        ),
        "domain_authority_refs_runtime_active_private_state_index_caller_count": (
            state_index_runtime_scan.get("runtime_active_caller_count")
            if isinstance(state_index_runtime_scan, Mapping)
            else None
        ),
        "domain_authority_refs_physical_delete_allowed": (
            state_index_scan.get("physical_delete_allowed")
            if isinstance(state_index_scan, Mapping)
            else None
        ),
        "domain_authority_refs_legacy_helper_active_caller_count": (
            len(state_index_scan.get("active_callers"))
            if isinstance(state_index_scan, Mapping)
            and isinstance(state_index_scan.get("active_callers"), list)
            else None
        ),
        "retirement_gate": dict(retirement_gate) if isinstance(retirement_gate, Mapping) else None,
    }


def _authority_status(surface: Mapping[str, Any]) -> str:
    surface_id = surface.get("surface_id")
    disposition = _text(surface.get("current_disposition")) or ""
    if surface_id == "domain_owner_action_dispatch":
        return "opl_authorized_owner_callable_adapter_live_tail_open"
    if surface_id in {"runtime_lifecycle_payload_retention", "runtime_storage_maintenance"}:
        return "opl_authorized_maintenance_callable_adapter_live_tail_open"
    if surface_id == "domain_health_diagnostic_obligation_actuator":
        return "consume_only_readback_projection_live_tail_open"
    if surface_id == "domain_authority_refs_index":
        return "active_callers_migrated_opl_state_index_source_adapter_live_tail_open"
    if surface_id == "agent_tool_arsenal_scientific_capability_registry":
        return "opl_capability_runtime_projection_live_owner_soak_tail_open"
    if surface_id == "default_executor_execution_latest_wire_projection":
        return "legacy_latest_history_only_stage_run_abi_provenance_tail_open"
    if surface_id == "default_executor_dispatch_request":
        return "legacy_default_executor_carrier_opl_stage_run_abi_provenance_only"
    if disposition.startswith("read_only"):
        return "read_only_projection_no_authority"
    if "projection" in disposition or "refs_only" in disposition:
        return "refs_only_projection_no_authority"
    if "handoff_contract" in disposition:
        return "transition_request_carrier_no_authority"
    return "open_surface_no_authority_guarded"


def _allowed_effect(surface: Mapping[str, Any]) -> str:
    boundary = surface.get("active_caller_boundary")
    if isinstance(boundary, Mapping) and _text(boundary.get("active_caller_effect")):
        return str(boundary["active_caller_effect"])
    if surface.get("surface_id") == "domain_owner_action_dispatch":
        return "execute_only_with_trusted_opl_authorization_or_bound_readback"
    if surface.get("surface_id") == "default_executor_execution_latest_wire_projection":
        return "canonical_owner_receipt_or_legacy_stage_run_closeout_provenance_only"
    if isinstance(surface.get("apply_gate"), Mapping):
        return "mutate_only_when_bound_opl_maintenance_authorization_is_present"
    if surface.get("surface_id") == "runtime_health_kernel":
        return "read_only_diagnostic_projection"
    if surface.get("surface_id") == "progress_portal_study_workbench_overview_action_projection":
        return "read_only_owner_delta_summary"
    if surface.get("surface_id") == "agent_tool_arsenal_scientific_capability_registry":
        return "current_owner_delta_bound_capability_projection_explicit_request_only"
    return "refs_only_or_diagnostic_projection"


def _requires_readback(surface: Mapping[str, Any]) -> bool:
    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        return gate.get("completion_claim_requires_live_owner_or_opl_readback") is True
    boundary = surface.get("active_caller_boundary")
    if isinstance(boundary, Mapping):
        return boundary.get("completion_claim_requires_live_owner_or_opl_readback") is True
    return True


def _physical_delete_gate_open(surface: Mapping[str, Any]) -> bool:
    if surface.get("current_disposition") == "physically_retired":
        return False
    legacy_stage_run_boundary = surface.get("legacy_stage_run_abi_boundary")
    if (
        isinstance(legacy_stage_run_boundary, Mapping)
        and legacy_stage_run_boundary.get("physical_delete_requires_no_active_stage_run_abi_caller_scan")
        is True
    ):
        scan = legacy_stage_run_boundary.get("active_stage_run_abi_caller_scan")
        return not (
            isinstance(scan, Mapping)
            and scan.get("no_active_stage_run_abi_caller_proven") is True
            and scan.get("physical_delete_allowed") is True
        )
    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        return False
    return bool(
        gate.get("no_active_caller_required_before_physical_delete")
        or gate.get("live_opl_cleanup_policy_takeover_required")
        or gate.get("live_opl_storage_policy_takeover_required")
        or gate.get("owner_retirement_decision_required")
    )


def _truthy_authority_flags(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    matches: list[str] = []
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            nested_path = (*path, key_text)
            if key_text in FORBIDDEN_TRUE_AUTHORITY_FLAGS and nested_value is True:
                matches.append(".".join(nested_path))
            matches.extend(_truthy_authority_flags(nested_value, nested_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested_value in enumerate(value):
            matches.extend(_truthy_authority_flags(nested_value, (*path, str(index))))
    return matches


def _surfaces(inventory: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    surfaces = inventory.get("surfaces")
    if not isinstance(surfaces, list):
        raise ValueError("runtime surface retirement inventory must contain a surfaces list")
    return [surface for surface in surfaces if isinstance(surface, Mapping)]


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "SURFACE_KIND",
    "audit_runtime_surface_retirement_inventory",
    "validate_runtime_surface_retirement_inventory",
]
