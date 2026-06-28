from __future__ import annotations

from collections.abc import Mapping
from typing import Any


GENERIC_RUNTIME_OWNER = "one-person-lab"


def validate_legacy_latest_wire(
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
            "owner_callable_receipt_candidates_reads_legacy_wire_by_default",
            "owner_callable_adapter_receipt_consumption_reads_legacy_wire_by_default",
            "owner_callable_adapter_nonconsumable_closeout_reads_legacy_wire_by_default",
        ):
            if current_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"current_reader_legacy_fallback:{key}"))
    else:
        violations.append(_violation(surface_id, "missing_current_reader_boundary"))
    replay_boundary = surface.get("history_replay_boundary")
    if isinstance(replay_boundary, Mapping):
        for key in (
            "owner_callable_receipt_candidates_requires_allow_legacy_fallback",
            "owner_callable_adapter_receipt_consumption_requires_allow_legacy_fallback",
            "owner_callable_adapter_nonconsumable_closeout_requires_allow_legacy_fallback",
            "execution_latest_payload_requires_allow_legacy_fallback",
            "legacy_latest_payload_helper_requires_allow_legacy_fallback",
        ):
            if replay_boundary.get(key) is not True:
                violations.append(_violation(surface_id, f"history_replay_missing_explicit_opt_in:{key}"))
    else:
        violations.append(_violation(surface_id, "missing_history_replay_boundary"))
    return violations


def validate_legacy_stage_run_abi(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    boundary = surface.get("legacy_stage_run_abi_boundary")
    if not isinstance(boundary, Mapping):
        return [_violation(surface_id, "missing_legacy_stage_run_abi_boundary")]
    if boundary.get("abi_role") != "opl_stagerun_closeout_provenance_identity_recovery_only":
        violations.append(_violation(surface_id, "legacy_stage_run_abi_role_not_provenance_only"))
    if boundary.get("stage_id") != "stage_outcome/opl-handoff":
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
        violations.extend(validate_stage_run_abi_active_caller_scan(surface_id, boundary))
    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, "legacy_stage_run_abi_missing_retirement_gate"))
    else:
        if gate.get("active_caller_alone_retains_surface") is not False:
            violations.append(_violation(surface_id, "legacy_stage_run_abi_active_caller_alone_can_retain_surface"))
        if gate.get("completion_claim_requires_live_owner_or_opl_readback") is not True:
            violations.append(_violation(surface_id, "legacy_stage_run_abi_missing_live_completion_gate"))
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "legacy_stage_run_abi_missing_no_active_caller_gate"))
        if gate.get("no_active_stage_run_abi_caller_proven") is not False:
            violations.append(_violation(surface_id, "legacy_stage_run_abi_gate_must_not_claim_no_active_caller"))
        if gate.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "legacy_stage_run_abi_gate_must_not_allow_physical_delete"))
        if gate.get("repo_stage_run_abi_provenance_proven") is not True:
            violations.append(_violation(surface_id, "legacy_stage_run_abi_gate_missing_repo_provenance"))
    closeout_roots = boundary.get("closeout_packet_roots")
    if not isinstance(closeout_roots, list) or not closeout_roots:
        violations.append(_violation(surface_id, "stage_closeout_packet_roots_missing"))
    allowed = boundary.get("allowed_consumption")
    if not isinstance(allowed, list) or "terminal_closeout_consumption" not in allowed:
        violations.append(_violation(surface_id, "stage_closeout_allowed_consumption_missing_terminal_closeout"))
    return violations


def validate_stage_run_abi_active_caller_scan(
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
        != "legacy_owner_callable_adapter_carrier_no_active_stage_run_abi_caller_physical_delete_ref"
    ):
        violations.append(_violation(surface_id, "stage_closeout_active_scan_missing_physical_delete_ref"))
    return violations


def validate_legacy_owner_callable_adapter_carrier(
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
        if abi_boundary.get("task_kind_retained_for_opl_stage_run_abi") != "stage_outcome/opl-handoff":
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

    violations.extend(validate_owner_callable_adapter_carrier_tail_readback(surface_id, surface))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("repo_stage_run_abi_provenance_proven") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_repo_stage_run_abi_provenance_not_proven"))
        if gate.get("no_active_authority_caller_proven") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_no_active_authority_caller_not_proven"))
        if gate.get("opl_owner_callable_adapter_carrier_tail_readback_required") is not True:
            violations.append(_violation(surface_id, "legacy_carrier_missing_tail_readback_gate"))
        if gate.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "legacy_carrier_gate_must_not_allow_physical_delete"))
    else:
        violations.append(_violation(surface_id, "missing_legacy_carrier_retirement_gate"))
    return violations


def validate_owner_callable_adapter_carrier_tail_readback(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    tail = surface.get("opl_owner_callable_adapter_carrier_tail_readback")
    if not isinstance(tail, Mapping):
        return [_violation(surface_id, "missing_opl_owner_callable_adapter_carrier_tail_readback")]

    violations: list[dict[str, str]] = []
    if tail.get("surface_kind") != "opl_owner_callable_adapter_carrier_tail_readback_requirement":
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_surface_kind_mismatch"))
    if tail.get("status") != "tail_open":
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_status_not_open"))
    if tail.get("runtime_owner") != GENERIC_RUNTIME_OWNER:
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_runtime_owner_not_opl"))
    if tail.get("runtime_kind") != "DomainProgressTransitionRuntime/TransactionalOutbox/StageRun":
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_runtime_kind_mismatch"))

    required_readbacks = tail.get("required_active_caller_readbacks")
    required_readback_set = (
        {str(item) for item in required_readbacks}
        if isinstance(required_readbacks, list)
        else set()
    )
    expected_readbacks = {
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_command_event_outbox_live_readback",
        "opl_stagerun_owner_callable_adapter_live_readback",
    }
    if not expected_readbacks.issubset(required_readback_set):
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_missing_required_readbacks"))

    required_before_physical_delete = _text(tail.get("required_before_physical_delete"))
    if (
        required_before_physical_delete
        != "owner_callable_dispatch_request_opl_owner_callable_adapter_carrier_tail_readback_ref"
    ):
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_missing_physical_delete_ref"))

    physical_delete_requires = tail.get("physical_delete_requires")
    required_delete_set = (
        {str(item) for item in physical_delete_requires}
        if isinstance(physical_delete_requires, list)
        else set()
    )
    expected_delete_requirements = expected_readbacks | {
        "no_active_owner_callable_adapter_carrier_caller_scan",
        "no_forbidden_write_proof",
        "replacement_parity_ref",
        "owner_retirement_decision_ref",
        "tombstone_or_provenance_ref",
    }
    if not expected_delete_requirements.issubset(required_delete_set):
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_missing_physical_delete_requirements"))

    for key in (
        "tail_readback_proven",
        "no_active_owner_callable_adapter_carrier_caller_proven",
        "physical_delete_allowed",
        "legacy_carrier_provenance_can_satisfy_readback",
        "transition_request_pending_can_satisfy_readback",
        "repo_no_authority_guard_can_satisfy_readback",
        "focused_tests_can_satisfy_readback",
        "request_only_carrier_can_authorize_provider_admission",
        "request_only_carrier_can_claim_running_or_progress",
    ):
        if tail.get(key, False) is not False:
            violations.append(_violation(surface_id, f"owner_callable_adapter_carrier_tail_forbidden:{key}"))

    forbidden_claims = tail.get("forbidden_completion_claims")
    expected_forbidden_claims = {
        "legacy_carrier_provenance_as_owner_callable_adapter_carrier_tail_readback",
        "transition_request_pending_as_opl_live_readback",
        "repo_no_authority_guard_as_owner_callable_adapter_carrier_tail_readback",
        "focused_tests_green_as_no_active_owner_callable_adapter_carrier_caller",
        "request_only_carrier_as_provider_admission",
        "request_only_carrier_as_running_or_progress",
    }
    if not isinstance(forbidden_claims, list) or not expected_forbidden_claims.issubset(
        {str(item) for item in forbidden_claims}
    ):
        violations.append(_violation(surface_id, "owner_callable_adapter_carrier_tail_missing_false_completion_guards"))
    return violations


def _text(value: Any) -> str | None:
    if isinstance(value, str) and value.strip():
        return value
    return None


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}
