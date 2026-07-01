from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.authority_flags import (
    FORBIDDEN_TRUE_AUTHORITY_FLAGS as _FORBIDDEN_TRUE_AUTHORITY_FLAGS,
    truthy_authority_flags as _truthy_authority_flags,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.private_runtime_residue_validators import (
    audit_workbench_projection_fields as _audit_workbench_projection_fields,
    validate_domain_diagnostic_obligation_actuator as _validate_domain_diagnostic_obligation_actuator,
    validate_domain_action_request_materializer_surface as _validate_domain_action_request_materializer_surface,
    validate_stage_outcome_authority as _validate_stage_outcome_authority,
    validate_progress_portal_study_workbench_overview_action_projection as _validate_progress_portal_study_workbench_overview_action_projection,
    validate_runtime_lifecycle_payload_retention as _validate_runtime_lifecycle_payload_retention,
    validate_runtime_storage_maintenance as _validate_runtime_storage_maintenance,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.completion_evidence_layers import (
    completion_evidence_layers as _completion_evidence_layers,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.runtime_health_kernel_validators import (
    validate_runtime_health_kernel as _validate_runtime_health_kernel,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_parts.surface_helpers import (
    SCHEMA_VERSION,
    SURFACE_KIND,
    allowed_effect as _allowed_effect,
    authority_status as _authority_status,
    physical_delete_gate_open as _physical_delete_gate_open,
    repo_source_retired as _repo_source_retired,
    requires_readback as _requires_readback,
    surfaces as _surfaces,
)
from med_autoscience.runtime_protocol.runtime_surface_retirement_validators import (
    GENERIC_RUNTIME_OWNER,
    _text,
    _violation,
    validate_legacy_owner_callable_adapter_carrier as _validate_legacy_owner_callable_adapter_carrier,
    validate_legacy_latest_wire as _validate_legacy_latest_wire,
    validate_legacy_stage_run_abi as _validate_legacy_stage_run_abi,
)


FORBIDDEN_TRUE_AUTHORITY_FLAGS = _FORBIDDEN_TRUE_AUTHORITY_FLAGS


def audit_runtime_surface_retirement_inventory(
    inventory: Mapping[str, Any],
) -> dict[str, Any]:
    surfaces = _surfaces(inventory)
    repo_source_open_surfaces = [
        surface for surface in surfaces if not _repo_source_retired(surface)
    ]
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
    repo_source_completion_allowed = not violations and not repo_source_open_surfaces
    live_runtime_readiness = evidence_layers["live_soak_or_no_active_caller"]
    return {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "status": (
            "repo_source_physical_retirement_complete"
            if repo_source_completion_allowed
            else "repo_no_authority_guard_landed_live_runtime_readiness_tail_open"
            if not violations
            else "authority_boundary_violation"
        ),
        "generic_runtime_owner": GENERIC_RUNTIME_OWNER,
        "repo_source_retirement_completion": {
            "status": "complete" if repo_source_completion_allowed else "incomplete",
            "completion_claim_allowed": repo_source_completion_allowed,
            "open_surface_count": len(repo_source_open_surfaces),
            "open_surface_ids": [
                str(surface.get("surface_id"))
                for surface in repo_source_open_surfaces
            ],
            "evidence_basis": [
                "current_disposition=physically_retired",
                "no authority-boundary violations",
                "compatibility_alias_allowed=false",
                "mas_owner_claim_allowed=false",
            ],
        },
        "live_runtime_readiness_completion": {
            "status": (
                "complete"
                if live_runtime_readiness["proven"]
                else "evidence_required"
            ),
            "completion_claim_allowed": bool(live_runtime_readiness["proven"]),
            "required_ref_families": live_runtime_readiness["required_ref_families"],
            "open_surface_tails": live_runtime_readiness["open_surface_tails"],
        },
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
        "completion_claim_allowed": repo_source_completion_allowed,
        "physical_retirement_tail_open": not repo_source_completion_allowed,
        "violations": violations,
        "forbidden_completion_interpretations": [
            "active_caller_exists_as_retention_reason",
            "focused_tests_green_as_runtime_ready",
            "maintenance_apply_gate_as_paper_progress",
            "read_only_projection_as_execution_authority",
            "repo_source_retirement_as_live_runtime_ready",
            "live_runtime_tail_open_as_repo_source_delete_blocker",
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
        if surface.get("current_disposition") == "physically_retired":
            if not _text(surface.get("tombstone_or_provenance_ref")):
                violations.append(_violation(surface_id, "physically_retired_missing_tombstone_or_provenance_ref"))
            continue
        if surface_id == "owner_callable_dispatch_request":
            violations.extend(_validate_legacy_owner_callable_adapter_carrier(surface_id, surface))
        if surface_id == "owner_callable_adapter_receipt_latest_wire_projection":
            violations.extend(_validate_legacy_latest_wire(surface_id, surface))
            violations.extend(_validate_legacy_stage_run_abi(surface_id, surface))
        if surface_id == "domain_authority_refs_index":
            violations.extend(_validate_domain_authority_refs_index(surface_id, surface))
        if surface_id.startswith("domain_action_request_materializer_"):
            violations.extend(_validate_domain_action_request_materializer_surface(surface_id, surface))
        if surface_id == "stage_outcome_authority":
            violations.extend(_validate_stage_outcome_authority(surface_id, surface))
        if surface_id == "domain_diagnostic_obligation_actuator":
            violations.extend(_validate_domain_diagnostic_obligation_actuator(surface_id, surface))
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
        violations.extend(_validate_open_surface(surface_id, surface))
    return violations


def _validate_open_surface(
    surface_id: str,
    surface: Mapping[str, Any],
) -> list[dict[str, str]]:
    violations: list[dict[str, str]] = []
    gate = surface.get("retirement_gate")
    if not isinstance(gate, Mapping):
        violations.append(_violation(surface_id, "missing_open_surface_retirement_gate"))
    else:
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
    retired_callers = scan.get("retired_callers")
    retired_caller_list = retired_callers if isinstance(retired_callers, list) else []
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
    elif status == "no_active_replay_or_local_inspection_callers":
        if active_caller_list:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_no_active_scan_must_not_list_active_callers",
                )
            )
        if no_active_proven is not True:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_no_active_scan_must_claim_no_active_replay_local_inspection_callers",
                )
            )
        if physical_delete_allowed is not False:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_no_active_scan_must_not_allow_physical_delete",
                )
            )
        if (
            "paper_progress_transition_refs.record_paper_progress_transition_ref::persist_authority_refs_index_explicit_opt_in"
            not in {str(caller) for caller in retired_caller_list}
        ):
            violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_retired_caller_missing"))
    else:
        violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_scan_status_invalid"))
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
        or not {
            "opl_family_adoption_sqlite_inspection_as_current_projection",
            "legacy_sqlite_payload_projection_as_state_index_kernel_takeover",
            "explicit_replay_opt_in_as_live_opl_readback",
        }.issubset({str(item) for item in forbidden_claims})
    ):
        violations.append(_violation(surface_id, "domain_authority_refs_legacy_helper_scan_missing_false_completion_guard"))
    if status == "active_replay_or_local_inspection_callers_present_tail_open":
        if (
            not isinstance(forbidden_claims, list)
            or "legacy_helper_active_scan_as_physical_delete" not in forbidden_claims
            or "legacy_helper_active_callers_as_no_active_caller" not in forbidden_claims
        ):
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_active_scan_missing_false_completion_guard",
                )
            )
    if status == "no_active_replay_or_local_inspection_callers":
        if (
            not isinstance(forbidden_claims, list)
            or "legacy_helper_no_active_scan_as_physical_delete" not in forbidden_claims
            or "no_active_replay_local_inspection_scan_as_live_state_index_kernel_takeover"
            not in forbidden_claims
        ):
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_no_active_scan_missing_false_completion_guard",
                )
            )
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
        if gate.get("no_active_replay_or_local_inspection_caller_proven") is not True:
            violations.append(
                _violation(
                    surface_id,
                    "domain_authority_refs_retirement_gate_must_claim_no_active_replay_local_inspection_callers",
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
        physical_delete_requires = live_soak.get("physical_delete_requires")
        if not isinstance(physical_delete_requires, list) or not {
            "agent_tool_arsenal_live_owner_consumption_soak_current_owner_delta_readback_ref",
            "agent_tool_arsenal_explicit_capability_request_resolution_live_readback_ref",
            "agent_tool_arsenal_direct_hosted_tool_invocation_runtime_parity_ref",
            "agent_tool_arsenal_no_active_registry_projection_caller_scan_ref",
            "no_forbidden_write_proof",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        } <= {str(item) for item in physical_delete_requires}:
            violations.append(_violation(surface_id, "capability_registry_live_soak_physical_delete_requires_incomplete"))
        required_readbacks = live_soak.get("required_active_caller_readbacks")
        if not isinstance(required_readbacks, list) or not {
            "current_owner_delta_bound_capability_consumption_live_readback",
            "explicit_capability_request_resolution_live_readback",
            "direct_hosted_tool_invocation_runtime_parity_readback",
        } <= {str(item) for item in required_readbacks}:
            violations.append(_violation(surface_id, "capability_registry_live_soak_required_readbacks_incomplete"))
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
            "mcp_or_cli_mode_coverage_as_direct_hosted_parity",
            "wildcard_guard_as_live_owner_consumption_soak",
            "capability_request_projection_as_paper_progress",
            "registry_projection_no_active_scan_as_physical_delete",
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
    obligation_tail = surface.get("opl_obligation_actuator_tail_readback")
    runtime_health_tail = surface.get("opl_runtime_health_observability_tail_readback")
    runtime_health_active_scan = (
        runtime_health_tail.get("active_diagnostic_projection_caller_scan")
        if isinstance(runtime_health_tail, Mapping)
        else None
    )
    materializer_tail = surface.get("opl_materializer_projection_tail_readback")
    workbench_tail = surface.get("opl_workbench_shell_readback_tail")
    owner_callable_adapter_carrier_tail = surface.get("opl_owner_callable_adapter_carrier_tail_readback")
    lifecycle_maintenance_tail = surface.get("opl_runtime_lifecycle_maintenance_tail_readback")
    storage_maintenance_tail = surface.get("opl_runtime_storage_maintenance_tail_readback")
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
        "stage_outcome_authority_live_soak_status": (
            active_caller_soak.get("status") if isinstance(active_caller_soak, Mapping) else None
        ),
        "stage_outcome_authority_live_every_active_caller_soak_proven": (
            active_caller_soak.get("live_every_active_caller_soak_proven")
            if isinstance(active_caller_soak, Mapping)
            else None
        ),
        "stage_outcome_authority_no_active_caller_proven": (
            active_caller_soak.get("no_active_caller_proven")
            if isinstance(active_caller_soak, Mapping)
            else None
        ),
        "stage_outcome_authority_physical_delete_allowed": (
            active_caller_soak.get("physical_delete_allowed")
            if isinstance(active_caller_soak, Mapping)
            else None
        ),
        "stage_outcome_authority_active_caller_family_count": (
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
        "agent_tool_arsenal_required_active_caller_readback_count": (
            len(live_owner_consumption_soak.get("required_active_caller_readbacks"))
            if isinstance(live_owner_consumption_soak, Mapping)
            and isinstance(live_owner_consumption_soak.get("required_active_caller_readbacks"), list)
            else None
        ),
        "obligation_actuator_tail_status": (
            obligation_tail.get("status") if isinstance(obligation_tail, Mapping) else None
        ),
        "obligation_actuator_tail_readback_proven": (
            obligation_tail.get("tail_readback_proven")
            if isinstance(obligation_tail, Mapping)
            else None
        ),
        "obligation_actuator_no_active_caller_proven": (
            obligation_tail.get("no_active_mas_obligation_actuator_caller_proven")
            if isinstance(obligation_tail, Mapping)
            else None
        ),
        "obligation_actuator_physical_delete_allowed": (
            obligation_tail.get("physical_delete_allowed")
            if isinstance(obligation_tail, Mapping)
            else None
        ),
        "obligation_actuator_required_active_caller_readback_count": (
            len(obligation_tail.get("required_active_caller_readbacks"))
            if isinstance(obligation_tail, Mapping)
            and isinstance(obligation_tail.get("required_active_caller_readbacks"), list)
            else None
        ),
        "runtime_health_tail_status": (
            runtime_health_tail.get("status")
            if isinstance(runtime_health_tail, Mapping)
            else None
        ),
        "runtime_health_tail_readback_proven": (
            runtime_health_tail.get("tail_readback_proven")
            if isinstance(runtime_health_tail, Mapping)
            else None
        ),
        "runtime_health_no_active_caller_proven": (
            runtime_health_tail.get("no_active_diagnostic_projection_caller_proven")
            if isinstance(runtime_health_tail, Mapping)
            else None
        ),
        "runtime_health_physical_delete_allowed": (
            runtime_health_tail.get("physical_delete_allowed")
            if isinstance(runtime_health_tail, Mapping)
            else None
        ),
        "runtime_health_required_active_caller_readback_count": (
            len(runtime_health_tail.get("required_active_caller_readbacks"))
            if isinstance(runtime_health_tail, Mapping)
            and isinstance(runtime_health_tail.get("required_active_caller_readbacks"), list)
            else None
        ),
        "runtime_health_active_diagnostic_projection_caller_count": (
            len(runtime_health_active_scan.get("active_callers"))
            if isinstance(runtime_health_active_scan, Mapping)
            and isinstance(runtime_health_active_scan.get("active_callers"), list)
            else None
        ),
        "runtime_health_active_diagnostic_projection_no_active_caller_proven": (
            runtime_health_active_scan.get("no_active_diagnostic_projection_caller_proven")
            if isinstance(runtime_health_active_scan, Mapping)
            else None
        ),
        "runtime_health_active_diagnostic_projection_physical_delete_allowed": (
            runtime_health_active_scan.get("physical_delete_allowed")
            if isinstance(runtime_health_active_scan, Mapping)
            else None
        ),
        "materializer_projection_tail_status": (
            materializer_tail.get("status")
            if isinstance(materializer_tail, Mapping)
            else None
        ),
        "materializer_projection_tail_readback_proven": (
            materializer_tail.get("tail_readback_proven")
            if isinstance(materializer_tail, Mapping)
            else None
        ),
        "materializer_projection_no_active_caller_proven": (
            materializer_tail.get("no_active_materializer_projection_caller_proven")
            if isinstance(materializer_tail, Mapping)
            else None
        ),
        "materializer_projection_physical_delete_allowed": (
            materializer_tail.get("physical_delete_allowed")
            if isinstance(materializer_tail, Mapping)
            else None
        ),
        "materializer_projection_required_active_caller_readback_count": (
            len(materializer_tail.get("required_active_caller_readbacks"))
            if isinstance(materializer_tail, Mapping)
            and isinstance(materializer_tail.get("required_active_caller_readbacks"), list)
            else None
        ),
        "workbench_tail_status": (
            workbench_tail.get("status")
            if isinstance(workbench_tail, Mapping)
            else None
        ),
        "workbench_tail_readback_proven": (
            workbench_tail.get("tail_readback_proven")
            if isinstance(workbench_tail, Mapping)
            else None
        ),
        "workbench_no_active_caller_proven": (
            workbench_tail.get("no_active_workbench_projection_action_caller_proven")
            if isinstance(workbench_tail, Mapping)
            else None
        ),
        "workbench_physical_delete_allowed": (
            workbench_tail.get("physical_delete_allowed")
            if isinstance(workbench_tail, Mapping)
            else None
        ),
        "workbench_required_active_caller_readback_count": (
            len(workbench_tail.get("required_active_caller_readbacks"))
            if isinstance(workbench_tail, Mapping)
            and isinstance(workbench_tail.get("required_active_caller_readbacks"), list)
            else None
        ),
        "owner_callable_adapter_carrier_tail_status": (
            owner_callable_adapter_carrier_tail.get("status")
            if isinstance(owner_callable_adapter_carrier_tail, Mapping)
            else None
        ),
        "owner_callable_adapter_carrier_tail_readback_proven": (
            owner_callable_adapter_carrier_tail.get("tail_readback_proven")
            if isinstance(owner_callable_adapter_carrier_tail, Mapping)
            else None
        ),
        "owner_callable_adapter_carrier_no_active_caller_proven": (
            owner_callable_adapter_carrier_tail.get(
                "no_active_owner_callable_adapter_carrier_caller_proven"
            )
            if isinstance(owner_callable_adapter_carrier_tail, Mapping)
            else None
        ),
        "owner_callable_adapter_carrier_physical_delete_allowed": (
            owner_callable_adapter_carrier_tail.get("physical_delete_allowed")
            if isinstance(owner_callable_adapter_carrier_tail, Mapping)
            else None
        ),
        "owner_callable_adapter_carrier_required_active_caller_readback_count": (
            len(owner_callable_adapter_carrier_tail.get("required_active_caller_readbacks"))
            if isinstance(owner_callable_adapter_carrier_tail, Mapping)
            and isinstance(
                owner_callable_adapter_carrier_tail.get("required_active_caller_readbacks"),
                list,
            )
            else None
        ),
        "runtime_lifecycle_maintenance_tail_status": (
            lifecycle_maintenance_tail.get("status")
            if isinstance(lifecycle_maintenance_tail, Mapping)
            else None
        ),
        "runtime_lifecycle_maintenance_tail_readback_proven": (
            lifecycle_maintenance_tail.get("tail_readback_proven")
            if isinstance(lifecycle_maintenance_tail, Mapping)
            else None
        ),
        "runtime_lifecycle_maintenance_no_active_caller_proven": (
            lifecycle_maintenance_tail.get(
                "no_active_lifecycle_maintenance_adapter_caller_proven"
            )
            if isinstance(lifecycle_maintenance_tail, Mapping)
            else None
        ),
        "runtime_lifecycle_maintenance_physical_delete_allowed": (
            lifecycle_maintenance_tail.get("physical_delete_allowed")
            if isinstance(lifecycle_maintenance_tail, Mapping)
            else None
        ),
        "runtime_lifecycle_maintenance_required_active_caller_readback_count": (
            len(lifecycle_maintenance_tail.get("required_active_caller_readbacks"))
            if isinstance(lifecycle_maintenance_tail, Mapping)
            and isinstance(
                lifecycle_maintenance_tail.get("required_active_caller_readbacks"),
                list,
            )
            else None
        ),
        "runtime_storage_maintenance_tail_status": (
            storage_maintenance_tail.get("status")
            if isinstance(storage_maintenance_tail, Mapping)
            else None
        ),
        "runtime_storage_maintenance_tail_readback_proven": (
            storage_maintenance_tail.get("tail_readback_proven")
            if isinstance(storage_maintenance_tail, Mapping)
            else None
        ),
        "runtime_storage_maintenance_no_active_caller_proven": (
            storage_maintenance_tail.get(
                "no_active_storage_maintenance_adapter_caller_proven"
            )
            if isinstance(storage_maintenance_tail, Mapping)
            else None
        ),
        "runtime_storage_maintenance_physical_delete_allowed": (
            storage_maintenance_tail.get("physical_delete_allowed")
            if isinstance(storage_maintenance_tail, Mapping)
            else None
        ),
        "runtime_storage_maintenance_required_active_caller_readback_count": (
            len(storage_maintenance_tail.get("required_active_caller_readbacks"))
            if isinstance(storage_maintenance_tail, Mapping)
            and isinstance(
                storage_maintenance_tail.get("required_active_caller_readbacks"),
                list,
            )
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


__all__ = [
    "SURFACE_KIND",
    "audit_runtime_surface_retirement_inventory",
    "validate_runtime_surface_retirement_inventory",
]
