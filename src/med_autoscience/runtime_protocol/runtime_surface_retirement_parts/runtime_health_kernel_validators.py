from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement_validators import (
    GENERIC_RUNTIME_OWNER,
    _text,
    _violation,
)


def validate_runtime_health_kernel(
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

    tail = surface.get("opl_runtime_health_observability_tail_readback")
    if not isinstance(tail, Mapping):
        violations.append(_violation(surface_id, "runtime_health_missing_opl_observability_tail_readback"))
    else:
        if tail.get("surface_kind") != "opl_runtime_health_observability_tail_readback_requirement":
            violations.append(_violation(surface_id, "runtime_health_tail_readback_kind_invalid"))
        if tail.get("status") != "tail_open":
            violations.append(_violation(surface_id, "runtime_health_tail_status_not_open"))
        if tail.get("runtime_owner") != GENERIC_RUNTIME_OWNER:
            violations.append(_violation(surface_id, "runtime_health_tail_owner_not_opl"))
        if tail.get("runtime_kind") != "OPL Observability/StageRun/RouteReconciler":
            violations.append(_violation(surface_id, "runtime_health_tail_runtime_kind_invalid"))
        if (
            _text(tail.get("required_before_physical_delete"))
            != "runtime_health_kernel_opl_runtime_health_observability_tail_readback_ref"
        ):
            violations.append(
                _violation(surface_id, "runtime_health_tail_required_before_physical_delete_invalid")
            )
        required_readbacks = {
            "opl_observability_live_readback",
            "opl_route_reconciler_live_readback",
        }
        active_readbacks = tail.get("required_active_caller_readbacks")
        if not isinstance(active_readbacks, list) or not required_readbacks <= {
            str(item) for item in active_readbacks
        }:
            violations.append(_violation(surface_id, "runtime_health_tail_active_readbacks_incomplete"))
        if tail.get("required_tail_readback_families_must_match_same_runtime_identity") is not True:
            violations.append(_violation(surface_id, "runtime_health_tail_missing_same_identity_family_gate"))
        if tail.get("current_control_or_stage_run_readback_alone_can_satisfy_tail") is not False:
            violations.append(_violation(surface_id, "runtime_health_tail_allows_generic_readback_as_tail"))
        required_tail_refs = {
            "opl_observability_live_readback",
            "opl_route_reconciler_live_readback",
            "no_active_diagnostic_projection_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        }
        physical_tail_requires = tail.get("physical_delete_requires")
        if not isinstance(physical_tail_requires, list) or not required_tail_refs <= {
            str(item) for item in physical_tail_requires
        }:
            violations.append(_violation(surface_id, "runtime_health_tail_physical_delete_refs_incomplete"))
        if tail.get("tail_readback_proven") is not False:
            violations.append(_violation(surface_id, "runtime_health_tail_must_not_claim_readback_proven"))
        if tail.get("no_active_diagnostic_projection_caller_proven") is not False:
            violations.append(_violation(surface_id, "runtime_health_tail_must_not_claim_no_active_caller"))
        if tail.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "runtime_health_tail_must_not_allow_physical_delete"))
        for key in (
            "mas_diagnostic_projection_can_satisfy_readback",
            "mas_runtime_health_snapshot_can_satisfy_readback",
            "repo_no_authority_guard_can_satisfy_readback",
            "focused_tests_can_satisfy_readback",
        ):
            if tail.get(key) is not False:
                violations.append(_violation(surface_id, f"runtime_health_tail_forbidden:{key}"))
        forbidden_claims = tail.get("forbidden_completion_claims")
        required_false_claims = {
            "repo_no_authority_guard_as_runtime_health_tail_readback",
            "mas_runtime_health_snapshot_as_opl_observability_readback",
            "mas_diagnostic_projection_as_route_reconciler_readback",
            "focused_tests_green_as_no_active_runtime_health_caller",
            "runtime_health_decision_gate_as_opl_runtime_readback",
            "current_control_readback_alone_as_runtime_health_tail",
            "stage_run_readback_alone_as_runtime_health_tail",
        }
        if not isinstance(forbidden_claims, list) or not required_false_claims <= {
            str(item) for item in forbidden_claims
        }:
            violations.append(_violation(surface_id, "runtime_health_tail_missing_false_completion_guards"))
        violations.extend(_validate_runtime_health_active_diagnostic_projection_scan(surface_id, tail))

    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, "runtime_health_missing_retirement_gate"))
    else:
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "runtime_health_missing_no_active_caller_physical_delete_gate"))
        if gate.get("runtime_health_live_opl_observability_readback_required") is not True:
            violations.append(_violation(surface_id, "runtime_health_missing_live_opl_observability_gate"))
    return violations


def _validate_runtime_health_active_diagnostic_projection_scan(
    surface_id: str,
    tail: Mapping[str, Any],
) -> list[dict[str, str]]:
    scan = tail.get("active_diagnostic_projection_caller_scan")
    if not isinstance(scan, Mapping):
        return [_violation(surface_id, "runtime_health_active_diagnostic_projection_scan_missing")]

    violations: list[dict[str, str]] = []
    active_callers = scan.get("active_callers")
    active_caller_list = active_callers if isinstance(active_callers, list) else []
    status = _text(scan.get("status"))
    no_active_proven = scan.get("no_active_diagnostic_projection_caller_proven")
    physical_delete_allowed = scan.get("physical_delete_allowed")
    if status == "active_diagnostic_projection_callers_present_tail_open":
        if not active_caller_list:
            violations.append(_violation(surface_id, "runtime_health_active_diagnostic_scan_empty"))
        if no_active_proven is not False:
            violations.append(
                _violation(surface_id, "runtime_health_active_diagnostic_scan_must_not_claim_no_active")
            )
        if physical_delete_allowed is not False:
            violations.append(
                _violation(surface_id, "runtime_health_active_diagnostic_scan_blocks_physical_delete")
            )
    if active_caller_list and no_active_proven is True:
        violations.append(
            _violation(surface_id, "runtime_health_active_diagnostic_no_active_claim_contradicts_callers")
        )
    if active_caller_list and physical_delete_allowed is not False:
        violations.append(
            _violation(surface_id, "runtime_health_active_diagnostic_callers_block_physical_delete")
        )
    allowed_consumption = scan.get("allowed_consumption")
    if not isinstance(allowed_consumption, list) or not {
        "read_runtime_status",
        "open_monitoring_entry",
        "identity_bound_opl_readback_requirement_projection",
    } <= {str(item) for item in allowed_consumption}:
        violations.append(
            _violation(surface_id, "runtime_health_active_diagnostic_scan_allowed_consumption_incomplete")
        )
    forbidden_claims = scan.get("forbidden_completion_claims")
    if not isinstance(forbidden_claims, list) or not {
        "diagnostic_projection_active_callers_as_no_active_caller",
        "runtime_health_decision_gate_as_no_active_caller",
        "runtime_health_snapshot_reader_as_opl_observability_readback",
        "active_diagnostic_projection_scan_as_physical_delete",
    } <= {str(item) for item in forbidden_claims}:
        violations.append(
            _violation(surface_id, "runtime_health_active_diagnostic_scan_missing_false_completion_guard")
        )
    if (
        _text(scan.get("required_before_physical_delete"))
        != "runtime_health_kernel_no_active_diagnostic_projection_caller_physical_delete_ref"
    ):
        violations.append(
            _violation(surface_id, "runtime_health_active_diagnostic_scan_missing_physical_delete_ref")
        )
    return violations


__all__ = ["validate_runtime_health_kernel"]
