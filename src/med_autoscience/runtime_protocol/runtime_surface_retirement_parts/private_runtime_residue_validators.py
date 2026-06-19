from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def validate_domain_action_request_materializer_surface(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    if surface_id == "domain_action_request_materializer_owner_callable_adapter_projection":
        return _validate_materializer_owner_callable_adapter_projection(surface_id, surface)
    if surface_id == "domain_action_request_materializer_request_tasks_projection":
        return _validate_materializer_request_tasks_projection(surface_id, surface)
    if surface_id == "domain_action_request_materializer_canonical_transition_request_body_projection":
        return _validate_materializer_canonical_transition_request_body_projection(surface_id, surface)
    return []


def _validate_materializer_owner_callable_adapter_projection(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "direct_readback_migrated_legacy_diagnostic_projection_only":
        violations.append(_violation(surface_id, "materializer_owner_adapter_not_legacy_diagnostic_only"))
    if surface.get("retained_mas_role") != "migration_diagnostic_projection_only":
        violations.append(_violation(surface_id, "materializer_owner_adapter_retained_role_not_diagnostic_only"))
    if surface.get("canonical_surface") != "domain_progress_transition_requests":
        violations.append(_violation(surface_id, "materializer_owner_adapter_canonical_surface_not_transition_requests"))
    if surface.get("replacement_surface") != "domain_progress_transition_requests plus OPL DomainProgressTransitionRuntime readback":
        violations.append(_violation(surface_id, "materializer_owner_adapter_replacement_not_opl_runtime"))

    boundary = surface.get("legacy_projection_boundary")
    if not isinstance(boundary, Mapping):
        return [*violations, _violation(surface_id, "materializer_owner_adapter_missing_legacy_boundary")]
    expected_values: dict[str, Any] = {
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "legacy_diagnostic_ref_helper": "owner_callable_adapter_projection.legacy_owner_callable_adapter_refs",
        "legacy_public_body_reader_returns_active_carriers": False,
        "legacy_public_body_reader_status": "retired_returns_empty",
        "legacy_raw_body_reader_scope": "internal_projection_to_refs_only_diagnostics",
        "owner_callable_adapter_counts_authority": False,
        "owner_callable_adapter_item_can_create_success_outcome": False,
        "owner_callable_adapter_item_diagnostic_only": True,
        "owner_callable_adapter_item_readiness_authority": False,
        "owner_callable_adapter_list_can_create_success_outcome": False,
        "owner_callable_adapter_list_diagnostic_only": True,
        "owner_callable_adapter_readiness_authority": False,
        "refs_only_diagnostics_body_omitted": True,
    }
    for key, expected in expected_values.items():
        if boundary.get(key) != expected:
            violations.append(_violation(surface_id, f"materializer_owner_adapter_boundary_mismatch:{key}"))
    violations.extend(_validate_materializer_projection_tail_readback(surface_id, surface))
    return violations


def _validate_materializer_request_tasks_projection(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "top_level_alias_physically_retired_nested_diagnostics_refs_only":
        violations.append(_violation(surface_id, "materializer_request_tasks_alias_not_retired"))
    if surface.get("retained_mas_role") != "nested_identity_refs_only_diagnostic_projection_no_top_level_alias":
        violations.append(_violation(surface_id, "materializer_request_tasks_retained_role_not_refs_only"))
    if surface.get("canonical_surface") != "domain_progress_transition_requests":
        violations.append(_violation(surface_id, "materializer_request_tasks_canonical_surface_not_transition_requests"))

    boundary = surface.get("projection_boundary")
    if not isinstance(boundary, Mapping):
        return [*violations, _violation(surface_id, "materializer_request_tasks_missing_projection_boundary")]
    expected_values: dict[str, Any] = {
        "body_authority": False,
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "handoff_packet_body_omitted": True,
        "legacy_alias_field": "request_tasks",
        "legacy_alias_present": False,
        "legacy_alias_retired": True,
        "nested_diagnostic_surface": "legacy_request_task_diagnostics.legacy_request_task_refs",
        "owner_route_body_omitted": True,
        "payload_body_omitted": True,
        "request_packet_body_omitted": True,
        "source_action_body_omitted": True,
    }
    for key, expected in expected_values.items():
        if boundary.get(key) != expected:
            violations.append(_violation(surface_id, f"materializer_request_tasks_boundary_mismatch:{key}"))
    violations.extend(_validate_materializer_projection_tail_readback(surface_id, surface))
    return violations


def _validate_materializer_canonical_transition_request_body_projection(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "canonical_transition_request_projection_body_retired":
        violations.append(_violation(surface_id, "materializer_transition_request_body_not_retired"))
    if surface.get("retained_mas_role") != "identity_refs_and_contract_metadata_projection_only":
        violations.append(_violation(surface_id, "materializer_transition_request_retained_role_not_refs_only"))
    if surface.get("canonical_surface") != "domain_progress_transition_requests":
        violations.append(_violation(surface_id, "materializer_transition_request_canonical_surface_not_transition_requests"))
    if surface.get("replacement_surface") != (
        "OPL DomainProgressTransitionRuntime command/event/outbox/StageRun readback plus "
        "MAS refs-only policy request projection"
    ):
        violations.append(_violation(surface_id, "materializer_transition_request_replacement_not_opl_runtime"))

    boundary = surface.get("projection_boundary")
    if not isinstance(boundary, Mapping):
        return [*violations, _violation(surface_id, "materializer_transition_request_missing_projection_boundary")]
    expected_values: dict[str, Any] = {
        "body_authority": False,
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "payload_scope": "identity_refs_and_contract_metadata_only",
        "transition_request_projection_body_authority": False,
        "transition_request_projection_body_omitted": True,
    }
    for key, expected in expected_values.items():
        if boundary.get(key) != expected:
            violations.append(_violation(surface_id, f"materializer_transition_request_boundary_mismatch:{key}"))

    for key in (
        "source_action_body_omitted",
        "owner_route_body_omitted",
        "prompt_contract_body_omitted",
        "domain_intent_body_omitted",
        "stage_transition_authority_boundary_body_omitted",
        "progress_first_closeout_admission_body_omitted",
        "operator_payload_body_omitted",
        "payload_authoring_target_body_omitted",
        "record_production_satisfaction_body_omitted",
        "owner_route_attempt_envelope_body_omitted",
        "legacy_owner_callable_adapter_body_omitted",
    ):
        if boundary.get(key) is not True:
            violations.append(_violation(surface_id, f"materializer_transition_request_body_not_omitted:{key}"))

    allowed_ref_fields = boundary.get("allowed_ref_fields")
    required_ref_fields = {
        "domain_intent_ref",
        "owner_route_attempt_envelope_ref",
        "owner_route_ref",
        "progress_first_closeout_admission_ref",
        "prompt_contract_ref",
        "record_production_satisfaction_ref",
        "source_action_ref",
        "stage_transition_authority_boundary_ref",
    }
    if not isinstance(allowed_ref_fields, list) or required_ref_fields != {str(item) for item in allowed_ref_fields}:
        violations.append(_violation(surface_id, "materializer_transition_request_allowed_refs_mismatch"))

    omitted_body_fields = boundary.get("omitted_body_fields")
    required_omitted_fields = {
        "domain_intent",
        "operator_payload",
        "owner_route",
        "owner_route_attempt_envelope",
        "payload_authoring_target",
        "progress_first_closeout_admission",
        "prompt_contract",
        "record_production_satisfaction",
        "source_action",
        "stage_transition_authority_boundary",
    }
    if not isinstance(omitted_body_fields, list) or required_omitted_fields != {str(item) for item in omitted_body_fields}:
        violations.append(_violation(surface_id, "materializer_transition_request_omitted_bodies_mismatch"))
    violations.extend(_validate_materializer_projection_tail_readback(surface_id, surface))
    return violations


def _validate_materializer_projection_tail_readback(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    tail = surface.get("opl_materializer_projection_tail_readback")
    if not isinstance(tail, Mapping):
        return [*violations, _violation(surface_id, "materializer_projection_missing_tail_readback")]
    if tail.get("surface_kind") != "opl_materializer_projection_tail_readback_requirement":
        violations.append(_violation(surface_id, "materializer_projection_tail_kind_invalid"))
    if tail.get("runtime_owner") != "one-person-lab":
        violations.append(_violation(surface_id, "materializer_projection_tail_owner_not_opl"))
    if tail.get("runtime_kind") != "OPL DomainProgressTransitionRuntime/StageRun":
        violations.append(_violation(surface_id, "materializer_projection_tail_runtime_kind_invalid"))
    required_readbacks = {
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_stagerun_owner_callable_adapter_readback",
    }
    active_readbacks = tail.get("required_active_caller_readbacks")
    if not isinstance(active_readbacks, list) or not required_readbacks <= {
        str(item) for item in active_readbacks
    }:
        violations.append(_violation(surface_id, "materializer_projection_tail_active_readbacks_incomplete"))
    required_tail_refs = {
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_stagerun_owner_callable_adapter_readback",
        "no_active_materializer_projection_caller_scan",
        "no_forbidden_write_proof",
        "replacement_parity_ref",
        "tombstone_or_provenance_ref",
    }
    physical_tail_requires = tail.get("physical_delete_requires")
    if not isinstance(physical_tail_requires, list) or not required_tail_refs <= {
        str(item) for item in physical_tail_requires
    }:
        violations.append(_violation(surface_id, "materializer_projection_tail_physical_delete_refs_incomplete"))
    if tail.get("tail_readback_proven") is not False:
        violations.append(_violation(surface_id, "materializer_projection_tail_must_not_claim_readback_proven"))
    if tail.get("no_active_materializer_projection_caller_proven") is not False:
        violations.append(_violation(surface_id, "materializer_projection_tail_must_not_claim_no_active_caller"))
    if tail.get("physical_delete_allowed") is not False:
        violations.append(_violation(surface_id, "materializer_projection_tail_must_not_allow_physical_delete"))
    for key in (
        "projection_demoted_can_satisfy_live_readback",
        "legacy_alias_retired_can_satisfy_live_readback",
        "refs_only_projection_can_satisfy_live_readback",
        "focused_tests_can_satisfy_live_readback",
        "repo_no_authority_guard_can_satisfy_live_readback",
    ):
        if tail.get(key) is not False:
            violations.append(_violation(surface_id, f"materializer_projection_tail_forbidden:{key}"))
    forbidden_claims = tail.get("forbidden_completion_claims")
    required_false_claims = {
        "materializer_projection_demoted_as_opl_transition_readback",
        "request_tasks_alias_retired_as_no_active_caller",
        "refs_only_transition_projection_as_physical_delete",
        "repo_no_authority_guard_as_live_materializer_tail_readback",
        "focused_tests_green_as_materializer_physical_delete",
    }
    if not isinstance(forbidden_claims, list) or not required_false_claims <= {
        str(item) for item in forbidden_claims
    }:
        violations.append(_violation(surface_id, "materializer_projection_tail_missing_false_completion_guards"))

    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, "materializer_projection_missing_retirement_gate"))
    else:
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "materializer_projection_missing_no_active_caller_physical_delete_gate"))
        if gate.get("opl_materializer_projection_tail_readback_required") is not True:
            violations.append(_violation(surface_id, "materializer_projection_missing_tail_readback_gate"))
    return violations


def validate_progress_portal_study_workbench_overview_action_projection(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "read_only_workbench_projection":
        violations.append(_violation(surface_id, "workbench_projection_not_read_only_projection"))
    if surface.get("retained_mas_role") != "body_free_workbench_read_model_projection":
        violations.append(_violation(surface_id, "workbench_projection_retained_role_not_body_free"))
    if surface.get("replacement_surface") != (
        "OPL Workbench Shell owns operator action transport; MAS only publishes inert "
        "current_owner_delta and DomainProgressTransitionRuntime readback refs"
    ):
        violations.append(_violation(surface_id, "workbench_projection_replacement_not_opl_workbench_shell"))

    boundary = surface.get("projection_boundary")
    if not isinstance(boundary, Mapping):
        return [*violations, _violation(surface_id, "workbench_projection_missing_projection_boundary")]

    expected_values: dict[str, Any] = {
        "next_system_action_role": "read_only_owner_delta_summary",
        "projection_only": True,
        "operator_intent_refs_are_inert": True,
        "requires_opl_current_control_readback": True,
        "legacy_operator_focus_role": "diagnostic_legacy_projection_input",
        "legacy_next_system_action_role": "diagnostic_legacy_projection_input",
        "must_not_be_used_as_provider_admission": True,
        "must_not_be_used_as_next_action_authority": True,
        "must_not_be_used_as_publication_ready": True,
        "must_not_be_used_as_paper_progress": True,
    }
    for key, expected in expected_values.items():
        if boundary.get(key) != expected:
            violations.append(_violation(surface_id, f"workbench_projection_boundary_mismatch:{key}"))

    for key in (
        "can_generate_action",
        "can_execute",
        "can_emit_runtime_command",
        "can_authorize_provider_admission",
        "can_authorize_worker_attempt",
        "can_open_runtime_endpoint",
        "can_transport_operator_action",
    ):
        if boundary.get(key) is not False:
            violations.append(_violation(surface_id, f"workbench_projection_boundary_forbidden:{key}"))

    tail = surface.get("opl_workbench_shell_readback_tail")
    if not isinstance(tail, Mapping):
        violations.append(_violation(surface_id, "workbench_projection_missing_opl_workbench_tail"))
    else:
        if tail.get("surface_kind") != "opl_workbench_shell_readback_tail_requirement":
            violations.append(_violation(surface_id, "workbench_projection_tail_kind_invalid"))
        if tail.get("status") != "tail_open":
            violations.append(_violation(surface_id, "workbench_projection_tail_status_not_open"))
        if tail.get("runtime_owner") != "one-person-lab":
            violations.append(_violation(surface_id, "workbench_projection_tail_owner_not_opl"))
        if tail.get("runtime_kind") != (
            "OPL Workbench Shell/current-control/DomainProgressTransitionRuntime readback"
        ):
            violations.append(_violation(surface_id, "workbench_projection_tail_runtime_kind_invalid"))
        if tail.get("required_before_physical_delete") != (
            "progress_portal_study_workbench_overview_action_projection_"
            "opl_workbench_shell_readback_tail_ref"
        ):
            violations.append(
                _violation(
                    surface_id,
                    "workbench_projection_tail_required_before_physical_delete_invalid",
                )
            )
        required_readbacks = {
            "opl_workbench_shell_action_transport_readback",
            "opl_current_control_readback",
            "opl_domain_progress_transition_runtime_readback",
        }
        active_readbacks = tail.get("required_active_caller_readbacks")
        if not isinstance(active_readbacks, list) or not required_readbacks <= {
            str(item) for item in active_readbacks
        }:
            violations.append(_violation(surface_id, "workbench_projection_tail_active_readbacks_incomplete"))
        required_tail_refs = {
            "opl_workbench_shell_action_transport_readback",
            "opl_current_control_readback",
            "opl_domain_progress_transition_runtime_readback",
            "no_active_workbench_projection_action_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        }
        physical_tail_requires = tail.get("physical_delete_requires")
        if not isinstance(physical_tail_requires, list) or not required_tail_refs <= {
            str(item) for item in physical_tail_requires
        }:
            violations.append(_violation(surface_id, "workbench_projection_tail_physical_delete_refs_incomplete"))
        if tail.get("tail_readback_proven") is not False:
            violations.append(_violation(surface_id, "workbench_projection_tail_must_not_claim_readback_proven"))
        if tail.get("no_active_workbench_projection_action_caller_proven") is not False:
            violations.append(_violation(surface_id, "workbench_projection_tail_must_not_claim_no_active_caller"))
        if tail.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "workbench_projection_tail_must_not_allow_physical_delete"))
        for key in (
            "mas_portal_projection_can_satisfy_readback",
            "mas_next_system_action_summary_can_satisfy_readback",
            "operator_intent_refs_can_satisfy_action_transport",
            "repo_no_authority_guard_can_satisfy_readback",
            "focused_tests_can_satisfy_readback",
        ):
            if tail.get(key) is not False:
                violations.append(_violation(surface_id, f"workbench_projection_tail_forbidden:{key}"))
        forbidden_claims = tail.get("forbidden_completion_claims")
        required_false_claims = {
            "mas_portal_projection_as_opl_workbench_shell_readback",
            "mas_next_system_action_summary_as_action_transport_readback",
            "operator_intent_refs_as_workbench_action_transport",
            "current_owner_delta_summary_as_current_control_readback",
            "repo_no_authority_guard_as_workbench_tail_readback",
            "focused_tests_green_as_no_active_workbench_projection_caller",
        }
        if not isinstance(forbidden_claims, list) or not required_false_claims <= {
            str(item) for item in forbidden_claims
        }:
            violations.append(_violation(surface_id, "workbench_projection_tail_missing_false_completion_guards"))

    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, "workbench_projection_missing_retirement_gate"))
    else:
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "workbench_projection_missing_no_active_caller_gate"))
        if gate.get("no_forbidden_write_proof_required") is not True:
            violations.append(_violation(surface_id, "workbench_projection_missing_no_forbidden_write_proof"))
        if gate.get("opl_workbench_shell_readback_required") is not True:
            violations.append(_violation(surface_id, "workbench_projection_missing_opl_workbench_readback_gate"))
    return violations


def audit_workbench_projection_fields(surface: Mapping[str, Any]) -> dict[str, Any]:
    surface_id = surface.get("surface_id")
    boundary = surface.get("projection_boundary")
    if (
        surface_id != "progress_portal_study_workbench_overview_action_projection"
        or not isinstance(boundary, Mapping)
    ):
        return {
            "workbench_projection_only": None,
            "workbench_next_system_action_role": None,
            "workbench_operator_intent_refs_are_inert": None,
            "workbench_can_generate_action": None,
            "workbench_can_transport_operator_action": None,
            "workbench_tail_status": None,
            "workbench_tail_readback_proven": None,
            "workbench_no_active_caller_proven": None,
            "workbench_physical_delete_allowed": None,
            "workbench_required_active_caller_readback_count": None,
        }
    tail = surface.get("opl_workbench_shell_readback_tail")
    return {
        "workbench_projection_only": boundary.get("projection_only"),
        "workbench_next_system_action_role": boundary.get("next_system_action_role"),
        "workbench_operator_intent_refs_are_inert": boundary.get("operator_intent_refs_are_inert"),
        "workbench_can_generate_action": boundary.get("can_generate_action"),
        "workbench_can_transport_operator_action": boundary.get("can_transport_operator_action"),
        "workbench_tail_status": (
            tail.get("status") if isinstance(tail, Mapping) else None
        ),
        "workbench_tail_readback_proven": (
            tail.get("tail_readback_proven") if isinstance(tail, Mapping) else None
        ),
        "workbench_no_active_caller_proven": (
            tail.get("no_active_workbench_projection_action_caller_proven")
            if isinstance(tail, Mapping)
            else None
        ),
        "workbench_physical_delete_allowed": (
            tail.get("physical_delete_allowed") if isinstance(tail, Mapping) else None
        ),
        "workbench_required_active_caller_readback_count": (
            len(tail.get("required_active_caller_readbacks"))
            if isinstance(tail, Mapping)
            and isinstance(tail.get("required_active_caller_readbacks"), list)
            else None
        ),
    }


def validate_runtime_lifecycle_payload_retention(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "opl_authorized_maintenance_callable_adapter_live_takeover_tail_open":
        violations.append(_violation(surface_id, "lifecycle_retention_not_opl_authorized_adapter"))
    if surface.get("retained_mas_role") != "maintenance_callable_adapter_and_body_free_receipt_projection":
        violations.append(_violation(surface_id, "lifecycle_retention_retained_role_not_callable_adapter"))
    if surface.get("replacement_surface") != (
        "OPL runtime lifecycle cleanup / retention policy plus OPL maintenance authorization readback"
    ):
        violations.append(_violation(surface_id, "lifecycle_retention_replacement_not_opl_policy_readback"))

    _validate_maintenance_authority_boundary(
        surface_id,
        surface,
        violations,
        mutation_flag="mutates_derived_runtime_lifecycle_payload_only_when_opl_authorized",
        dry_run_projection_key=None,
        reason_prefix="lifecycle_retention",
    )

    apply_gate = surface.get("apply_gate")
    if not isinstance(apply_gate, Mapping):
        violations.append(_violation(surface_id, "lifecycle_retention_missing_apply_gate"))
    else:
        _validate_required_apply_gate_values(
            surface_id,
            apply_gate,
            violations,
            reason_prefix="lifecycle_retention",
            expected_values={
                "required_authorization_surface": "opl_runtime_lifecycle_maintenance_authorization",
                "proof_surface": "opl_runtime_lifecycle_maintenance_authorization_proof",
                "required_for_apply": True,
                "dry_run_requires_authorization": False,
                "missing_or_invalid_authorization_status": (
                    "blocked_opl_runtime_lifecycle_maintenance_authorization_required"
                ),
                "typed_blocker": "opl_runtime_lifecycle_maintenance_authorization_required",
            },
            required_bindings={
                "operation",
                "maintenance_surface",
                "db_path",
                "outcome",
                "authorization_ref",
            },
            required_operations={
                "payload_retention",
                "sqlite_sidecar_repair",
            },
            operations_key="applies_to_operations",
        )

    _validate_maintenance_tail_readback(
        surface_id,
        surface,
        violations,
        tail_key="opl_runtime_lifecycle_maintenance_tail_readback",
        reason_prefix="lifecycle_retention_tail",
        expected_kind="opl_runtime_lifecycle_maintenance_tail_readback_requirement",
        expected_runtime_kind="OPL RuntimeLifecycleCleanup/RetentionPolicy",
        required_readbacks={
            "opl_runtime_lifecycle_cleanup_policy_live_readback",
            "opl_runtime_retention_policy_live_readback",
        },
        required_physical_refs={
            "opl_runtime_lifecycle_cleanup_policy_live_readback",
            "opl_runtime_retention_policy_live_readback",
            "no_active_lifecycle_maintenance_adapter_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        },
        no_active_key="no_active_lifecycle_maintenance_adapter_caller_proven",
        forbidden_false_keys={
            "apply_authorization_can_satisfy_live_takeover",
            "dry_run_plan_can_satisfy_live_takeover",
            "maintenance_receipt_can_satisfy_live_takeover",
            "repo_tests_can_satisfy_live_takeover",
        },
        required_false_completion_claims={
            "opl_maintenance_authorization_as_live_cleanup_policy_takeover",
            "runtime_lifecycle_apply_gate_as_live_takeover",
            "runtime_lifecycle_dry_run_plan_as_live_takeover",
            "runtime_lifecycle_receipt_as_physical_delete",
            "repo_tests_green_as_runtime_lifecycle_physical_delete",
        },
    )
    _validate_forbidden_completion_claims(
        surface_id,
        surface,
        violations,
        reason_prefix="lifecycle_retention",
        required_claims={
            "mas_owned_generic_runtime_lifecycle_cleanup_policy",
            "mas_owned_generic_persistence_engine",
            "mas_owned_sqlite_sidecar_owner",
            "mas_owned_queue",
            "mas_owned_attempt_ledger",
            "runtime_storage_apply_as_runtime_ready",
            "runtime_storage_apply_as_paper_progress",
        },
    )
    _validate_maintenance_retirement_gate(
        surface_id,
        surface,
        violations,
        reason_prefix="lifecycle_retention",
        required_live_takeover_key="live_opl_cleanup_policy_takeover_required",
    )
    return violations


def validate_runtime_storage_maintenance(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != (
        "opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open"
    ):
        violations.append(_violation(surface_id, "storage_maintenance_not_opl_authorized_adapter"))
    if surface.get("retained_mas_role") != "maintenance_callable_adapter_and_body_free_diagnostic_projection":
        violations.append(_violation(surface_id, "storage_maintenance_retained_role_not_callable_adapter"))
    if surface.get("replacement_surface") != (
        "OPL runtime storage maintenance authorization / retention shell plus OPL StateIndex and restore/readback surfaces"
    ):
        violations.append(_violation(surface_id, "storage_maintenance_replacement_not_opl_policy_readback"))

    _validate_maintenance_authority_boundary(
        surface_id,
        surface,
        violations,
        mutation_flag="mutates_runtime_storage_payload_only_when_opl_authorized",
        dry_run_projection_key="dry_run_projection_only",
        reason_prefix="storage_maintenance",
    )

    apply_gate = surface.get("apply_gate")
    if not isinstance(apply_gate, Mapping):
        violations.append(_violation(surface_id, "storage_maintenance_missing_apply_gate"))
    else:
        _validate_required_apply_gate_values(
            surface_id,
            apply_gate,
            violations,
            reason_prefix="storage_maintenance",
            expected_values={
                "required_authorization_surface": "opl_runtime_storage_maintenance_authorization",
                "proof_surface": "opl_runtime_storage_maintenance_authorization_proof",
                "required_for_workspace_apply": True,
                "required_for_direct_quest_physical_apply": True,
                "dry_run_requires_authorization": False,
                "restore_proof_canary_requires_authorization": False,
                "refs_only_state_index_only_requires_authorization": False,
                "planned_retention_projection_requires_authorization": False,
                "missing_or_invalid_authorization_status": (
                    "blocked_opl_runtime_storage_maintenance_authorization_required"
                ),
                "typed_blocker": "opl_runtime_storage_maintenance_authorization_required",
            },
            required_bindings={
                "operation",
                "maintenance_surface",
                "workspace_root_or_quest_root",
                "outcome",
                "authorization_ref",
            },
            required_operations={
                "workspace_storage_apply",
                "quest_runtime_storage_backend_apply",
                "runtime_oversized_jsonl_slimming_apply",
                "restore_proof_compaction_apply",
                "archive_retention_apply",
                "report_retention_apply",
                "semantic_process_retention_apply",
                "git_temp_garbage_delete_apply",
                "workspace_root_git_reinitialize_apply",
                "workspace_root_git_retirement_apply",
                "delete_safe_cache_apply",
            },
            operations_key="applies_to_operations",
        )
        accepted_operations = apply_gate.get("accepted_operations")
        if not isinstance(accepted_operations, list) or not {
            "workspace_storage_apply",
            "quest_runtime_storage_apply",
        } <= {str(item) for item in accepted_operations}:
            violations.append(_violation(surface_id, "storage_maintenance_accepted_operations_incomplete"))
        accepted_surfaces = apply_gate.get("accepted_maintenance_surfaces")
        if not isinstance(accepted_surfaces, list) or not {
            "workspace_runtime_storage_maintenance",
            "quest_runtime_storage_maintenance",
        } <= {str(item) for item in accepted_surfaces}:
            violations.append(_violation(surface_id, "storage_maintenance_accepted_surfaces_incomplete"))

    allowed_without_authorization = surface.get("allowed_without_opl_authorization")
    required_allowed = {
        "workspace_storage_audit_dry_run",
        "restore_proof_canary_source_retained",
        "refs_only_state_index_only_projection",
        "archive_retention_plan",
        "report_retention_plan",
        "attempt_evidence_capsule_plan",
        "semantic_process_retention_plan",
    }
    if (
        not isinstance(allowed_without_authorization, list)
        or not required_allowed <= {str(item) for item in allowed_without_authorization}
    ):
        violations.append(_violation(surface_id, "storage_maintenance_allowed_without_auth_incomplete"))

    _validate_maintenance_tail_readback(
        surface_id,
        surface,
        violations,
        tail_key="opl_runtime_storage_maintenance_tail_readback",
        reason_prefix="storage_maintenance_tail",
        expected_kind="opl_runtime_storage_maintenance_tail_readback_requirement",
        expected_runtime_kind="OPL RuntimeStorageMaintenance/RestoreRetentionShell/StateIndex",
        required_readbacks={
            "opl_runtime_storage_policy_live_readback",
            "opl_restore_retention_shell_live_readback",
            "opl_state_index_storage_ref_readback",
        },
        required_physical_refs={
            "opl_runtime_storage_policy_live_readback",
            "opl_restore_retention_shell_live_readback",
            "opl_state_index_storage_ref_readback",
            "no_active_storage_maintenance_adapter_caller_scan",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        },
        no_active_key="no_active_storage_maintenance_adapter_caller_proven",
        forbidden_false_keys={
            "apply_authorization_can_satisfy_live_takeover",
            "dry_run_projection_can_satisfy_live_takeover",
            "restore_canary_can_satisfy_live_takeover",
            "refs_only_index_projection_can_satisfy_live_takeover",
            "repo_tests_can_satisfy_live_takeover",
        },
        required_false_completion_claims={
            "opl_storage_maintenance_authorization_as_live_storage_policy_takeover",
            "runtime_storage_apply_gate_as_live_takeover",
            "runtime_storage_dry_run_projection_as_live_takeover",
            "restore_proof_canary_as_live_takeover",
            "refs_only_state_index_projection_as_storage_takeover",
            "repo_tests_green_as_runtime_storage_physical_delete",
        },
    )
    _validate_forbidden_completion_claims(
        surface_id,
        surface,
        violations,
        reason_prefix="storage_maintenance",
        required_claims={
            "mas_owned_generic_runtime_storage_shell",
            "mas_owned_generic_runtime_lifecycle_cleanup_policy",
            "mas_owned_restore_retention_owner",
            "mas_owned_queue",
            "mas_owned_attempt_ledger",
            "runtime_storage_apply_as_runtime_ready",
            "runtime_storage_apply_as_paper_progress",
            "runtime_storage_apply_as_provider_admission",
            "runtime_storage_apply_as_publication_ready",
        },
    )
    _validate_maintenance_retirement_gate(
        surface_id,
        surface,
        violations,
        reason_prefix="storage_maintenance",
        required_live_takeover_key="live_opl_storage_policy_takeover_required",
    )
    return violations


def _validate_maintenance_authority_boundary(
    surface_id: str,
    surface: Mapping[str, Any],
    violations: list[dict[str, str]],
    *,
    mutation_flag: str,
    dry_run_projection_key: str | None,
    reason_prefix: str,
) -> None:
    authority = surface.get("authority_boundary")
    if not isinstance(authority, Mapping):
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_authority_boundary"))
        return
    for key in (
        "can_create_opl_command",
        "can_create_opl_event",
        "can_create_opl_outbox",
        "can_create_opl_stage_run",
        "can_claim_runtime_currentness",
        "can_claim_paper_progress",
        "can_authorize_generic_cleanup_policy",
        "can_authorize_artifact_mutation",
        "can_authorize_publication_ready",
        "can_write_domain_truth",
        "can_write_publication_eval",
        "can_write_controller_decision",
        "stores_body",
    ):
        if authority.get(key, False) is not False:
            violations.append(_violation(surface_id, f"{reason_prefix}_authority_forbidden:{key}"))
    if authority.get(mutation_flag) is not True:
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_opl_authorized_mutation_flag"))
    if dry_run_projection_key and authority.get(dry_run_projection_key) is not True:
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_dry_run_projection_boundary"))


def _validate_maintenance_tail_readback(
    surface_id: str,
    surface: Mapping[str, Any],
    violations: list[dict[str, str]],
    *,
    tail_key: str,
    reason_prefix: str,
    expected_kind: str,
    expected_runtime_kind: str,
    required_readbacks: set[str],
    required_physical_refs: set[str],
    no_active_key: str,
    forbidden_false_keys: set[str],
    required_false_completion_claims: set[str],
) -> None:
    tail = surface.get(tail_key)
    if not isinstance(tail, Mapping):
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_readback"))
        return
    if tail.get("surface_kind") != expected_kind:
        violations.append(_violation(surface_id, f"{reason_prefix}_kind_invalid"))
    if tail.get("runtime_owner") != "one-person-lab":
        violations.append(_violation(surface_id, f"{reason_prefix}_owner_not_opl"))
    if tail.get("runtime_kind") != expected_runtime_kind:
        violations.append(_violation(surface_id, f"{reason_prefix}_runtime_kind_invalid"))
    active_readbacks = tail.get("required_active_caller_readbacks")
    if not isinstance(active_readbacks, list) or not required_readbacks <= {
        str(item) for item in active_readbacks
    }:
        violations.append(_violation(surface_id, f"{reason_prefix}_active_readbacks_incomplete"))
    physical_delete_requires = tail.get("physical_delete_requires")
    if not isinstance(physical_delete_requires, list) or not required_physical_refs <= {
        str(item) for item in physical_delete_requires
    }:
        violations.append(_violation(surface_id, f"{reason_prefix}_physical_delete_refs_incomplete"))
    if tail.get("tail_readback_proven") is not False:
        violations.append(_violation(surface_id, f"{reason_prefix}_must_not_claim_readback_proven"))
    if tail.get(no_active_key) is not False:
        violations.append(_violation(surface_id, f"{reason_prefix}_must_not_claim_no_active_caller"))
    if tail.get("physical_delete_allowed") is not False:
        violations.append(_violation(surface_id, f"{reason_prefix}_must_not_allow_physical_delete"))
    for key in sorted(forbidden_false_keys):
        if tail.get(key) is not False:
            violations.append(_violation(surface_id, f"{reason_prefix}_forbidden:{key}"))
    forbidden_claims = tail.get("forbidden_completion_claims")
    if not isinstance(forbidden_claims, list) or not required_false_completion_claims <= {
        str(item) for item in forbidden_claims
    }:
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_false_completion_guards"))


def _validate_required_apply_gate_values(
    surface_id: str,
    apply_gate: Mapping[str, Any],
    violations: list[dict[str, str]],
    *,
    reason_prefix: str,
    expected_values: Mapping[str, Any],
    required_bindings: set[str],
    required_operations: set[str],
    operations_key: str,
) -> None:
    for key, expected in expected_values.items():
        if apply_gate.get(key) != expected:
            violations.append(_violation(surface_id, f"{reason_prefix}_apply_gate_mismatch:{key}"))
    must_bind = apply_gate.get("must_bind")
    if not isinstance(must_bind, list) or not required_bindings <= {str(item) for item in must_bind}:
        violations.append(_violation(surface_id, f"{reason_prefix}_apply_gate_bindings_incomplete"))
    operations = apply_gate.get(operations_key)
    if not isinstance(operations, list) or not required_operations <= {str(item) for item in operations}:
        violations.append(_violation(surface_id, f"{reason_prefix}_apply_gate_operations_incomplete"))


def _validate_forbidden_completion_claims(
    surface_id: str,
    surface: Mapping[str, Any],
    violations: list[dict[str, str]],
    *,
    reason_prefix: str,
    required_claims: set[str],
) -> None:
    forbidden_claims = surface.get("forbidden_claims")
    if not isinstance(forbidden_claims, list) or not required_claims <= {
        str(item) for item in forbidden_claims
    }:
        violations.append(_violation(surface_id, f"{reason_prefix}_forbidden_claims_incomplete"))


def _validate_maintenance_retirement_gate(
    surface_id: str,
    surface: Mapping[str, Any],
    violations: list[dict[str, str]],
    *,
    reason_prefix: str,
    required_live_takeover_key: str,
) -> None:
    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_retirement_gate"))
        return
    if gate.get(required_live_takeover_key) is not True:
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_live_opl_takeover_gate"))
    if gate.get("no_active_caller_required_before_physical_delete") is not True:
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_no_active_caller_gate"))
    if gate.get("completion_claim_requires_live_owner_or_opl_readback") is not True:
        violations.append(_violation(surface_id, f"{reason_prefix}_missing_live_readback_completion_gate"))


def validate_domain_owner_action_dispatch(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "opl_authorized_owner_callable_adapter":
        violations.append(_violation(surface_id, "owner_dispatch_not_opl_authorized_adapter"))
    if surface.get("retained_mas_role") != "owner_callable_adapter_policy_boundary_and_typed_blocker_projection":
        violations.append(_violation(surface_id, "owner_dispatch_retained_role_not_minimal_adapter"))

    execution_boundary = surface.get("execution_authorization_boundary")
    if not isinstance(execution_boundary, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_execution_authorization_boundary"))
    else:
        required_sources = {
            "trusted_opl_execution_authorization",
            "exact_provider_hosted_stage_attempt",
            "active_opl_provider_attempt_or_lease",
            "bound_opl_domain_progress_transition_runtime_readback",
        }
        sources = execution_boundary.get("execution_authorization_sources")
        if not isinstance(sources, list) or not required_sources <= {str(item) for item in sources}:
            violations.append(_violation(surface_id, "owner_dispatch_missing_opl_authorization_sources"))
        if execution_boundary.get("closeout_binding_authorizes_execution") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_closeout_binding_authorizes_execution"))
        if execution_boundary.get("repo_level_authorization_coverage_complete") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_repo_authorization_coverage_not_complete"))
        if execution_boundary.get("live_every_active_caller_soak_required") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_missing_live_every_active_caller_soak_gate"))
        if execution_boundary.get("missing_authorization_outcome") != "opl_execution_authorization_required_typed_blocker":
            violations.append(_violation(surface_id, "owner_dispatch_missing_authorization_outcome_not_typed_blocker"))
        if execution_boundary.get("provider_attempt_or_lease_required_when_blocked") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_provider_attempt_required_when_blocked"))
        selector = execution_boundary.get("running_provider_attempt_selector_boundary")
        if isinstance(selector, Mapping):
            if selector.get("running_provider_attempt_without_opl_proof_can_select_route") is not False:
                violations.append(_violation(surface_id, "owner_dispatch_running_attempt_selector_allows_no_proof"))
            accepted_proofs = selector.get("accepted_proofs")
            required_proofs = {
                "trusted_opl_execution_authorization",
                "exact_provider_hosted_stage_attempt",
                "bound_opl_domain_progress_transition_runtime_readback",
            }
            if not isinstance(accepted_proofs, list) or not required_proofs <= {
                str(item) for item in accepted_proofs
            }:
                violations.append(_violation(surface_id, "owner_dispatch_running_attempt_selector_missing_proofs"))
        else:
            violations.append(_violation(surface_id, "owner_dispatch_missing_running_attempt_selector_boundary"))

    coverage = surface.get("execution_authorization_coverage")
    if not isinstance(coverage, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_execution_authorization_coverage"))
    else:
        if coverage.get("coverage_status") != "repo_fail_closed_all_supported_actions_live_readback_tail_open":
            violations.append(_violation(surface_id, "owner_dispatch_coverage_status_not_fail_closed"))
        if coverage.get("request_projection_without_opl_proof_outcome") != "opl_execution_authorization_required":
            violations.append(_violation(surface_id, "owner_dispatch_request_without_proof_not_blocked"))
        if coverage.get("live_readback_required_before_retirement") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_missing_live_readback_retirement_gate"))
        if coverage.get("live_tail") != "live_every_active_caller_soak_or_no_active_caller_proof":
            violations.append(_violation(surface_id, "owner_dispatch_live_tail_not_explicit"))

    soak = surface.get("active_caller_soak_boundary")
    if not isinstance(soak, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_active_caller_soak_boundary"))
    else:
        active_caller_families = soak.get("active_caller_families")
        active_caller_family_list = (
            active_caller_families if isinstance(active_caller_families, list) else []
        )
        required_families = {
            "domain_owner_action_dispatch.execute_dispatch",
            "domain_owner_action_dispatch.stage_native_owner_action",
            "domain_owner_action_dispatch.provider_hosted_exact_stage_packet_selection",
            "domain_owner_action_dispatch.ai_reviewer_provider_hosted_authorization",
            "domain_owner_action_dispatch.gate_clearing_authorization",
            "current_execution_envelope.running_provider_attempt_priority",
            "study_progress.provider_admission_running_proof",
        }
        if soak.get("status") != "live_every_active_caller_soak_tail_open":
            violations.append(_violation(surface_id, "owner_dispatch_soak_status_not_tail_open"))
        if not required_families <= {str(item) for item in active_caller_family_list}:
            violations.append(_violation(surface_id, "owner_dispatch_soak_active_caller_families_incomplete"))
        if soak.get("live_every_active_caller_soak_proven") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_soak_must_not_claim_live_every_active_caller"))
        if soak.get("no_active_caller_proven") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_soak_must_not_claim_no_active_caller"))
        if soak.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "owner_dispatch_soak_must_not_allow_physical_delete"))
        if soak.get("allowed_effect") != "execute_only_with_trusted_opl_authorization_or_bound_readback":
            violations.append(_violation(surface_id, "owner_dispatch_soak_allowed_effect_not_opl_authorized"))
        if (
            soak.get("required_before_physical_delete")
            != "domain_owner_action_dispatch_live_every_active_caller_soak_or_no_active_caller_ref"
        ):
            violations.append(_violation(surface_id, "owner_dispatch_soak_missing_physical_delete_ref"))
        physical_delete_requires = soak.get("physical_delete_requires")
        required_physical_refs = {
            "domain_owner_action_dispatch_execute_dispatch_live_readback_ref",
            "domain_owner_action_dispatch_stage_native_owner_action_live_readback_ref",
            "domain_owner_action_dispatch_provider_hosted_stage_packet_live_readback_ref",
            "domain_owner_action_dispatch_ai_reviewer_authorization_live_readback_ref",
            "domain_owner_action_dispatch_gate_clearing_authorization_live_readback_ref",
            "domain_owner_action_dispatch_current_execution_running_proof_live_readback_ref",
            "domain_owner_action_dispatch_study_progress_running_proof_live_readback_ref",
            "domain_owner_action_dispatch_no_active_owner_callable_adapter_caller_scan_ref",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        }
        if not isinstance(physical_delete_requires, list) or not required_physical_refs <= {
            str(item) for item in physical_delete_requires
        }:
            violations.append(_violation(surface_id, "owner_dispatch_soak_physical_delete_refs_incomplete"))
        required_active_readbacks = {
            "execute_dispatch_live_readback",
            "stage_native_owner_action_live_readback",
            "provider_hosted_stage_packet_selection_live_readback",
            "ai_reviewer_provider_hosted_authorization_live_readback",
            "gate_clearing_authorization_live_readback",
            "current_execution_running_proof_live_readback",
            "study_progress_provider_admission_running_proof_live_readback",
        }
        active_readbacks = soak.get("required_active_caller_readbacks")
        if not isinstance(active_readbacks, list) or not required_active_readbacks <= {
            str(item) for item in active_readbacks
        }:
            violations.append(_violation(surface_id, "owner_dispatch_soak_active_readbacks_incomplete"))
        forbidden_claims = soak.get("forbidden_completion_claims")
        required_false_claims = {
            "repo_authorization_coverage_as_live_every_active_caller_soak",
            "active_caller_migrated_as_no_active_caller_proof",
            "focused_tests_green_as_physical_delete",
            "provider_completion_as_dispatch_retirement",
            "current_execution_running_proof_without_opl_readback_as_soak",
            "study_progress_running_proof_without_opl_readback_as_soak",
        }
        if not isinstance(forbidden_claims, list) or not required_false_claims <= {
            str(item) for item in forbidden_claims
        }:
            violations.append(_violation(surface_id, "owner_dispatch_soak_missing_false_completion_guards"))

    consumer = surface.get("consumer_input_boundary")
    if not isinstance(consumer, Mapping):
        violations.append(_violation(surface_id, "owner_dispatch_missing_consumer_input_boundary"))
    else:
        if consumer.get("canonical_current_surface") != "domain_progress_transition_requests":
            violations.append(_violation(surface_id, "owner_dispatch_canonical_surface_not_transition_requests"))
        for key in (
            "inline_default_executor_dispatch_request_candidate_allowed",
            "owner_callable_adapters_candidate_allowed",
            "can_authorize_provider_admission",
            "can_create_provider_attempt",
            "can_create_opl_event_outbox_or_stage_run",
        ):
            if consumer.get(key, False) is not False:
                violations.append(_violation(surface_id, f"owner_dispatch_consumer_boundary_forbidden:{key}"))
        if consumer.get("explicit_action_pending_request_outcome") != "opl_execution_authorization_required":
            violations.append(_violation(surface_id, "owner_dispatch_explicit_action_pending_not_blocked"))

    stage_native = surface.get("stage_native_next_action_selector_boundary")
    if isinstance(stage_native, Mapping):
        for key in (
            "candidate_without_opl_proof_can_score_current",
            "candidate_without_opl_proof_can_be_selected_by_default",
            "candidate_without_opl_proof_can_preempt_other_current_dispatch",
            "candidate_without_opl_proof_can_authorize_execution",
            "candidate_without_opl_proof_owner_route_basis_is_authority",
            "provider_admission_pending",
            "provider_attempt_or_lease_required",
            "mas_private_attempt_loop_forbidden",
        ):
            expected = True if key == "mas_private_attempt_loop_forbidden" else False
            if stage_native.get(key, False) is not expected:
                violations.append(_violation(surface_id, f"owner_dispatch_stage_native_boundary_invalid:{key}"))
        required_proofs = {
            "trusted_opl_execution_authorization",
            "exact_provider_hosted_stage_attempt",
            "bound_opl_domain_progress_transition_runtime_readback",
        }
        proofs = stage_native.get("required_execution_proofs")
        if not isinstance(proofs, list) or not required_proofs <= {str(item) for item in proofs}:
            violations.append(_violation(surface_id, "owner_dispatch_stage_native_missing_execution_proofs"))
    else:
        violations.append(_violation(surface_id, "owner_dispatch_missing_stage_native_selector_boundary"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("live_every_active_caller_soak_required") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_retirement_missing_live_soak"))
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_retirement_missing_no_active_caller_gate"))
        if gate.get("no_forbidden_write_proof_required") is not True:
            violations.append(_violation(surface_id, "owner_dispatch_retirement_missing_no_forbidden_write_proof"))
    return violations


def validate_domain_health_diagnostic_obligation_actuator(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    if surface.get("current_disposition") != "obligation_readback_projection_consumer":
        violations.append(_violation(surface_id, "obligation_actuator_not_readback_projection_consumer"))
    if surface.get("retained_mas_role") != "consume_only_obligation_outcome_projection_and_mas_typed_blocker_authority_result":
        violations.append(_violation(surface_id, "obligation_actuator_retained_role_not_consume_only"))
    if surface.get("validator_role") != "accepted_owner_answer_or_opl_readback_shape_validator":
        violations.append(_violation(surface_id, "obligation_actuator_validator_role_not_readback_shape_validator"))
    if surface.get("local_allowed_outcome_table_role") != "contract_bound_result_shape_validation_not_supervisor_decision_engine":
        violations.append(_violation(surface_id, "obligation_actuator_local_outcome_table_is_decision_engine"))
    for key in (
        "mas_can_choose_supervisor_decision",
        "mas_can_mutate_recovery_obligation_store",
        "mas_can_run_supervisor_decision_engine",
        "study_progress_supervisor_projection_can_build_decision",
        "paper_recovery_state_can_build_decision",
        "read_model_can_run_supervisor_decision_engine",
        "mas_can_create_opl_command_event_or_outbox",
        "can_write_fail_closed_typed_control_blocker",
        "actuator_can_write_private_blocker_surface",
    ):
        if surface.get(key, False) is not False:
            violations.append(_violation(surface_id, f"obligation_actuator_forbidden:{key}"))
    if surface.get("actuator_direct_filesystem_write_retired") is not True:
        violations.append(_violation(surface_id, "obligation_actuator_direct_filesystem_write_not_retired"))
    if surface.get("transition_request_pending_can_close_physical_tail") is not False:
        violations.append(_violation(surface_id, "obligation_actuator_transition_request_can_close_physical_tail"))

    active_boundary = surface.get("active_caller_boundary")
    if not isinstance(active_boundary, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_active_caller_boundary"))
    else:
        if active_boundary.get("active_caller_effect") != "consume_only_readback_projection_with_success_proof_gated_postcondition":
            violations.append(_violation(surface_id, "obligation_actuator_active_effect_not_consume_only"))
        if active_boundary.get("active_caller_retains_surface") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_active_surface_tail_not_explicit"))
        if active_boundary.get("active_caller_retains_runtime_authority") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_active_caller_retains_runtime_authority"))
        if active_boundary.get("request_projection_only_can_satisfy_success") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_request_projection_can_satisfy_success"))
        required_physical_delete = {
            "opl_recovery_obligation_store_active_caller",
            "opl_supervisor_decision_engine_active_caller",
            "no_active_caller_scan",
            "replacement_parity_ref",
            "owner_retirement_decision_ref",
            "tombstone_or_provenance_ref",
        }
        physical_delete_requires = active_boundary.get("physical_delete_requires")
        if not isinstance(physical_delete_requires, list) or not required_physical_delete <= set(physical_delete_requires):
            violations.append(_violation(surface_id, "obligation_actuator_physical_delete_gate_incomplete"))

    tail = surface.get("opl_obligation_actuator_tail_readback")
    if not isinstance(tail, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_opl_tail_readback_requirement"))
    else:
        if tail.get("surface_kind") != "opl_obligation_actuator_tail_readback_requirement":
            violations.append(_violation(surface_id, "obligation_actuator_tail_readback_kind_invalid"))
        if tail.get("runtime_owner") != "one-person-lab":
            violations.append(_violation(surface_id, "obligation_actuator_tail_runtime_owner_not_opl"))
        if tail.get("runtime_kind") != "RecoveryObligationStore/SupervisorDecisionEngine":
            violations.append(_violation(surface_id, "obligation_actuator_tail_runtime_kind_invalid"))
        required_readbacks = {
            "opl_recovery_obligation_store_active_caller_readback",
            "opl_supervisor_decision_engine_active_caller_readback",
        }
        active_readbacks = tail.get("required_active_caller_readbacks")
        if not isinstance(active_readbacks, list) or not required_readbacks <= {
            str(item) for item in active_readbacks
        }:
            violations.append(_violation(surface_id, "obligation_actuator_tail_active_readbacks_incomplete"))
        required_tail_refs = {
            "opl_recovery_obligation_store_active_caller_readback",
            "opl_supervisor_decision_engine_active_caller_readback",
            "no_active_mas_obligation_actuator_caller_scan",
            "no_forbidden_write_proof",
            "owner_retirement_decision",
            "tombstone_or_provenance",
        }
        physical_tail_requires = tail.get("physical_delete_requires")
        if not isinstance(physical_tail_requires, list) or not required_tail_refs <= {
            str(item) for item in physical_tail_requires
        }:
            violations.append(_violation(surface_id, "obligation_actuator_tail_physical_delete_refs_incomplete"))
        if tail.get("tail_readback_proven") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_tail_must_not_claim_readback_proven"))
        if tail.get("no_active_mas_obligation_actuator_caller_proven") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_tail_must_not_claim_no_active_caller"))
        if tail.get("physical_delete_allowed") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_tail_must_not_allow_physical_delete"))
        for key in (
            "mas_policy_projection_can_satisfy_readback",
            "mas_request_projection_can_satisfy_readback",
            "repo_no_authority_guard_can_satisfy_readback",
            "focused_tests_can_satisfy_readback",
        ):
            if tail.get(key) is not False:
                violations.append(_violation(surface_id, f"obligation_actuator_tail_forbidden:{key}"))
        forbidden_claims = tail.get("forbidden_completion_claims")
        required_false_claims = {
            "repo_no_authority_guard_as_obligation_actuator_tail_readback",
            "mas_policy_projection_as_opl_recovery_obligation_store_readback",
            "mas_transition_request_as_supervisor_decision_engine_readback",
            "focused_tests_green_as_no_active_obligation_actuator_caller",
            "typed_blocker_authority_result_as_opl_supervisor_decision_engine_readback",
        }
        if not isinstance(forbidden_claims, list) or not required_false_claims <= {
            str(item) for item in forbidden_claims
        }:
            violations.append(_violation(surface_id, "obligation_actuator_tail_missing_false_completion_guards"))

    readback = surface.get("obligation_readback_boundary")
    if not isinstance(readback, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_readback_boundary"))
    else:
        if readback.get("request_projection_is_success_outcome") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_request_projection_is_success"))
        if readback.get("success_proof_required_for_postcondition_ok") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_success_proof_gate"))
        if readback.get("success_proof_requires_consumed_readback_identity") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_consumed_identity_gate"))
        if readback.get("mas_domain_authority_readback_requires_authority_boundary") is not True:
            violations.append(
                _violation(surface_id, "obligation_actuator_missing_domain_authority_boundary_gate")
            )
        if readback.get("read_model_evidence_refs_can_satisfy_success") is not False:
            violations.append(
                _violation(surface_id, "obligation_actuator_read_model_refs_can_satisfy_success")
            )
        if readback.get("success_proof_forbidden_when_request_projection_only") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_request_projection_can_emit_success_proof"))
        if readback.get("supervisor_disallowed_outcome_is_success") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_disallowed_supervisor_outcome_is_success"))
        if readback.get("readback_result_validator_boundary_required") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_validator_boundary_requirement"))
        if readback.get("local_allowed_outcome_table_role") != "contract_bound_result_shape_validation_not_supervisor_decision_engine":
            violations.append(_violation(surface_id, "obligation_actuator_readback_table_is_decision_engine"))
        if readback.get("actuator_can_write_private_blocker_surface") is not False:
            violations.append(_violation(surface_id, "obligation_actuator_readback_can_write_private_blocker"))
        tail_requirement = readback.get("opl_obligation_actuator_tail_readback_requirement")
        if not isinstance(tail_requirement, Mapping):
            violations.append(_violation(surface_id, "obligation_actuator_readback_missing_tail_requirement"))
        else:
            if tail_requirement.get("runtime_owner") != "one-person-lab":
                violations.append(_violation(surface_id, "obligation_actuator_readback_tail_owner_not_opl"))
            if tail_requirement.get("runtime_kind") != "RecoveryObligationStore/SupervisorDecisionEngine":
                violations.append(_violation(surface_id, "obligation_actuator_readback_tail_kind_invalid"))
            for key in (
                "mas_policy_projection_can_satisfy_readback",
                "mas_request_projection_can_satisfy_readback",
                "focused_tests_can_satisfy_readback",
                "repo_no_authority_guard_can_satisfy_readback",
                "physical_delete_allowed_without_tail_proof",
            ):
                if tail_requirement.get(key) is not False:
                    violations.append(
                        _violation(surface_id, f"obligation_actuator_readback_tail_forbidden:{key}")
                    )
        source_families = readback.get("success_outcome_source_families")
        required_families = {
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        }
        if not isinstance(source_families, list) or not required_families <= {str(item) for item in source_families}:
            violations.append(_violation(surface_id, "obligation_actuator_missing_success_source_families"))

    typed_boundary = surface.get("typed_blocker_authority_result_adapter_boundary")
    if not isinstance(typed_boundary, Mapping):
        violations.append(_violation(surface_id, "obligation_actuator_missing_typed_blocker_adapter_boundary"))
    else:
        if typed_boundary.get("surface_kind") != "mas_domain_typed_blocker_authority_result_boundary":
            violations.append(_violation(surface_id, "obligation_actuator_typed_blocker_boundary_kind_invalid"))
        if typed_boundary.get("authority_owner") != "med-autoscience":
            violations.append(_violation(surface_id, "obligation_actuator_typed_blocker_owner_not_mas"))
        if typed_boundary.get("authority_result_surface") != "mas_domain_typed_blocker":
            violations.append(_violation(surface_id, "obligation_actuator_typed_blocker_surface_invalid"))
        for key in (
            "actuator_private_write_authority",
            "can_create_opl_command",
            "can_create_opl_event",
            "can_create_opl_outbox",
            "can_create_opl_stage_run",
            "can_store_recovery_obligation",
            "can_run_supervisor_decision_engine",
            "can_authorize_provider_admission",
            "can_claim_paper_progress",
            "can_write_publication_eval",
            "can_write_controller_decision",
        ):
            if typed_boundary.get(key, False) is not False:
                violations.append(_violation(surface_id, f"obligation_actuator_typed_blocker_boundary_forbidden:{key}"))

    gate = surface.get("retirement_gate")
    if isinstance(gate, Mapping):
        if gate.get("owner_retirement_decision_required") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_owner_retirement_decision_gate"))
        if gate.get("no_active_caller_required_before_physical_delete") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_no_active_caller_gate"))
        if gate.get("no_forbidden_write_proof_required") is not True:
            violations.append(_violation(surface_id, "obligation_actuator_missing_no_forbidden_write_proof"))
    return violations


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "audit_workbench_projection_fields",
    "validate_domain_action_request_materializer_surface",
    "validate_domain_health_diagnostic_obligation_actuator",
    "validate_domain_owner_action_dispatch",
    "validate_progress_portal_study_workbench_overview_action_projection",
    "validate_runtime_lifecycle_payload_retention",
    "validate_runtime_storage_maintenance",
]
