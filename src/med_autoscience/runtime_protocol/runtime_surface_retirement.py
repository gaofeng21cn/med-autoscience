from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


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
        "completion_claim_allowed": False,
        "physical_retirement_tail_open": True,
        "violations": violations,
        "forbidden_completion_interpretations": [
            "active_caller_exists_as_retention_reason",
            "active_caller_migrated_as_physical_retirement",
            "inventory_entry_updated_as_live_takeover",
            "focused_tests_green_as_runtime_ready",
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
        if surface_id == "default_executor_execution_latest_wire_projection":
            violations.extend(_validate_legacy_latest_wire(surface_id, surface))
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


def _audit_surface(surface: Mapping[str, Any]) -> dict[str, Any]:
    active_boundary = surface.get("active_caller_boundary")
    apply_gate = surface.get("apply_gate")
    retirement_gate = surface.get("retirement_gate")
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
    if isinstance(surface.get("apply_gate"), Mapping):
        return "mutate_only_when_bound_opl_maintenance_authorization_is_present"
    if surface.get("surface_id") == "runtime_health_kernel":
        return "read_only_diagnostic_projection"
    if surface.get("surface_id") == "progress_portal_study_workbench_overview_action_projection":
        return "read_only_owner_delta_summary"
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
