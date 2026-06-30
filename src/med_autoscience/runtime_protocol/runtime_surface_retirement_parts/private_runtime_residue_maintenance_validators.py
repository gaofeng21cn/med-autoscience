from __future__ import annotations

from collections.abc import Mapping
from typing import Any


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
        expected_required_before_physical_delete=(
            "runtime_lifecycle_payload_retention_opl_runtime_lifecycle_maintenance_"
            "tail_readback_ref"
        ),
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
            "cold_payload_externalization_receipt_can_satisfy_live_takeover",
            "dry_run_plan_can_satisfy_live_takeover",
            "maintenance_receipt_can_satisfy_live_takeover",
            "repo_tests_can_satisfy_live_takeover",
            "sqlite_sidecar_repair_receipt_can_satisfy_live_takeover",
        },
        required_false_completion_claims={
            "cold_payload_externalization_receipt_as_physical_delete",
            "opl_maintenance_authorization_as_live_cleanup_policy_takeover",
            "payload_retention_plan_as_live_takeover",
            "runtime_lifecycle_apply_gate_as_live_takeover",
            "runtime_lifecycle_dry_run_plan_as_live_takeover",
            "runtime_lifecycle_receipt_as_physical_delete",
            "repo_tests_green_as_runtime_lifecycle_physical_delete",
            "sqlite_sidecar_repair_receipt_as_live_takeover",
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
        expected_required_before_physical_delete=(
            "runtime_storage_maintenance_opl_runtime_storage_maintenance_tail_readback_ref"
        ),
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
            "archive_report_retention_plan_can_satisfy_live_takeover",
            "apply_authorization_can_satisfy_live_takeover",
            "attempt_evidence_capsule_can_satisfy_live_takeover",
            "dry_run_projection_can_satisfy_live_takeover",
            "planned_retention_projection_can_satisfy_live_takeover",
            "restore_canary_can_satisfy_live_takeover",
            "refs_only_index_projection_can_satisfy_live_takeover",
            "repo_tests_can_satisfy_live_takeover",
            "workspace_root_git_retirement_receipt_can_satisfy_live_takeover",
        },
        required_false_completion_claims={
            "archive_retention_plan_as_live_takeover",
            "attempt_evidence_capsule_plan_as_storage_takeover",
            "opl_storage_maintenance_authorization_as_live_storage_policy_takeover",
            "report_retention_plan_as_live_takeover",
            "runtime_storage_apply_gate_as_live_takeover",
            "runtime_storage_dry_run_projection_as_live_takeover",
            "restore_proof_canary_as_live_takeover",
            "refs_only_state_index_projection_as_storage_takeover",
            "repo_tests_green_as_runtime_storage_physical_delete",
            "semantic_process_retention_plan_as_live_takeover",
            "storage_maintenance_receipt_as_physical_delete",
            "workspace_root_git_retirement_receipt_as_physical_delete",
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
    expected_required_before_physical_delete: str,
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
    if tail.get("status") != "tail_open":
        violations.append(_violation(surface_id, f"{reason_prefix}_status_not_open"))
    if tail.get("runtime_owner") != "one-person-lab":
        violations.append(_violation(surface_id, f"{reason_prefix}_owner_not_opl"))
    if tail.get("runtime_kind") != expected_runtime_kind:
        violations.append(_violation(surface_id, f"{reason_prefix}_runtime_kind_invalid"))
    if tail.get("required_before_physical_delete") != expected_required_before_physical_delete:
        violations.append(
            _violation(surface_id, f"{reason_prefix}_required_before_physical_delete_invalid")
        )
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


def _violation(surface_id: str, reason: str) -> dict[str, str]:
    return {"surface_id": surface_id, "reason": reason}


__all__ = [
    "validate_runtime_lifecycle_payload_retention",
    "validate_runtime_storage_maintenance",
]
