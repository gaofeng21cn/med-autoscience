from __future__ import annotations

import importlib
import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_private_runtime_residue_active_callers_are_no_authority_refs_or_consume_only() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    surfaces = {surface["surface_id"]: surface for surface in inventory["surfaces"]}

    refs_surface = surfaces["domain_authority_refs_index"]
    legacy_helper_scan = {
        "status": "active_replay_or_local_inspection_callers_present_tail_open",
        "no_active_replay_or_local_inspection_caller_proven": False,
        "physical_delete_allowed": False,
        "required_before_physical_delete": (
            "domain_authority_refs_index_live_state_index_takeover_or_"
            "no_active_replay_local_inspection_caller_physical_delete_ref"
        ),
        "active_callers": [
            (
                "paper_progress_transition_refs.record_paper_progress_transition_ref::"
                "persist_authority_refs_index_explicit_opt_in"
            ),
            "opl_domain_pack.family_adoption.build_opl_family_adoption_surface::inspect_authority_refs_index",
            "opl_domain_pack.family_adoption.build_product_entry_adoption_projection::sqlite_refs_index_ref",
            "opl_domain_pack.adoption_ref_payload.payload_from_authority_refs::legacy_sqlite_payload_projection",
        ],
        "allowed_consumption": [
            "explicit_history_replay",
            "explicit_local_refs_inspection",
            "opl_family_adoption_projection",
            "tombstone_provenance",
        ],
        "forbidden_completion_claims": [
            "legacy_helper_active_scan_as_physical_delete",
            "legacy_helper_active_callers_as_no_active_caller",
            "legacy_sqlite_payload_projection_as_state_index_kernel_takeover",
            "explicit_replay_opt_in_as_live_opl_readback",
        ],
    }
    assert refs_surface["active_caller_migrated"] is True
    assert refs_surface["current_disposition"] == (
        "active_callers_migrated_to_opl_state_index_source_adapter_live_takeover_tail_open"
    )
    assert refs_surface["active_caller_boundary"] == {
        "active_caller_effect": "opl_state_index_source_adapter_emitted_no_sqlite_persistence",
        "active_caller_retains_authority": False,
        "active_caller_retains_runtime_authority": False,
        "active_caller_retains_surface": False,
        "active_caller_db_path_does_not_imply_persistence": True,
        "active_callers": [
            "stage_artifact_materializer.opl_state_index_source_adapter.emit_stage_artifact_delta_source",
            "owner_route_reconcile.scan_output.opl_state_index_source_adapter.emit_owner_route_receipt_source",
            "domain_owner_action_dispatch.opl_state_index_source_adapter.emit_dispatch_receipt_source",
            "paper_progress_transition_refs.opl_state_index_source_adapter.emit_paper_progress_transition_source",
            "runtime_storage_maintenance.opl_state_index_source_adapter.emit_archive_ref_source",
        ],
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "default_sqlite_persistence": False,
        "physical_delete_requires": [
            "opl_state_index_kernel_takeover",
            "no_active_replay_or_local_inspection_caller_scan",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
        "legacy_domain_authority_refs_index_role": "explicit_history_replay_or_local_refs_inspection_only",
        "sqlite_persistence_requires_explicit_opt_in": True,
    }
    assert refs_surface["authority_boundary"] == {
        "stores_body": False,
        "stores_domain_truth": False,
        "rebuildable": True,
        "started_worker": False,
        "outbox_record": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_generate_next_action_authority": False,
        "can_authorize_provider_admission": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }
    assert refs_surface["retirement_gate"] == {
        "active_caller_alone_retains_surface": False,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "no_active_caller_required_before_physical_delete": True,
        "no_active_authority_caller_proven": True,
        "no_active_replay_or_local_inspection_caller_proven": False,
        "physical_delete_allowed": False,
        "repo_replacement_parity_proven": True,
        "replacement_parity_required": True,
        "tombstone_or_provenance_required": True,
    }
    assert refs_surface["opl_state_index_takeover_bridge"] == {
        "active_caller_db_path_does_not_imply_persistence": True,
        "active_caller_effect": "opl_state_index_source_adapter_emitted_no_sqlite_persistence",
        "active_caller_status": "repo_active_callers_migrated_to_opl_state_index_source_adapter",
        "active_caller_retains_authority": False,
        "active_caller_retains_surface": False,
        "bridge_status": "repo_replacement_parity_proven_live_takeover_tail_open",
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
        "default_sqlite_persistence": False,
        "live_takeover_required_before_physical_delete": True,
        "mas_projection_cannot_replace": [
            "opl_state_index_kernel_readback",
            "opl_lifecycle_index",
            "opl_operator_read_model",
            "opl_artifact_index",
            "opl_queue_index",
        ],
        "replacement_owner_surface": "one-person-lab StateIndexKernel",
        "required_opl_readback_ref": (
            "src/med_autoscience/runtime_protocol/refs_only_state_index_pilot.py#"
            "opl_state_index_kernel_readback_requirement"
        ),
        "sqlite_persistence_requires_explicit_opt_in": True,
        "legacy_domain_authority_refs_index_role": "explicit_history_replay_or_local_refs_inspection_only",
        "legacy_helper_active_caller_scan": legacy_helper_scan,
    }
    assert "mas_owned_state_index_kernel" in refs_surface["forbidden_claims"]

    refs_contract = importlib.import_module(
        "med_autoscience.runtime_protocol.domain_authority_refs_index"
    ).domain_authority_refs_index_contract()
    adapter_contract = importlib.import_module(
        "med_autoscience.runtime_protocol.opl_state_index_source_adapter"
    ).source_adapter_contract()
    assert refs_contract["role"] == "refs_only_domain_authority_receipt_index"
    policy = refs_contract["authority_policy"]
    assert policy["stores_body"] is False
    assert policy["stores_domain_truth"] is False
    assert policy["started_worker"] is False
    assert policy["outbox_record"] is False
    assert policy["can_generate_next_action_authority"] is False
    assert policy["can_authorize_provider_admission"] is False
    assert policy["can_authorize_quality_verdict"] is False
    assert policy["can_authorize_publication_ready"] is False
    assert refs_contract["generic_persistence_engine_claim_allowed"] is False
    assert refs_contract["generic_scheduler_queue_attempt_claim_allowed"] is False
    assert refs_contract["default_record_behavior"] == (
        "source_adapter_emitted_no_default_sqlite_persistence"
    )
    assert refs_contract["sqlite_persistence_policy"] == {
        "default_persist_sqlite": False,
        "requires_explicit_opt_in": True,
        "opt_in_parameter": "persist_sqlite",
        "allowed_use": "historical_replay_or_explicit_local_refs_inspection",
        "active_caller_db_path_does_not_imply_persistence": True,
    }
    bridge = refs_contract["opl_state_index_kernel_takeover_bridge"]
    inventory_bridge = refs_surface["opl_state_index_takeover_bridge"]
    assert bridge["active_caller_status"] == inventory_bridge["active_caller_status"]
    assert bridge["active_caller_effect"] == inventory_bridge["active_caller_effect"]
    assert (
        bridge["active_caller_retains_surface"]
        is inventory_bridge["active_caller_retains_surface"]
        is False
    )
    assert (
        bridge["active_caller_retains_authority"]
        is inventory_bridge["active_caller_retains_authority"]
        is False
    )
    assert (
        bridge["default_sqlite_persistence"]
        is inventory_bridge["default_sqlite_persistence"]
        is False
    )
    assert (
        bridge["sqlite_persistence_requires_explicit_opt_in"]
        is inventory_bridge["sqlite_persistence_requires_explicit_opt_in"]
        is True
    )
    assert (
        bridge["active_caller_db_path_does_not_imply_persistence"]
        is inventory_bridge["active_caller_db_path_does_not_imply_persistence"]
        is True
    )
    assert (
        bridge["completion_claim_requires_live_opl_readback_or_no_active_caller"]
        is inventory_bridge["completion_claim_requires_live_opl_readback_or_no_active_caller"]
        is True
    )
    assert (
        bridge["live_takeover_required_before_physical_delete"]
        is inventory_bridge["live_takeover_required_before_physical_delete"]
        is True
    )
    assert bridge["replacement_owner_surface"] == inventory_bridge["replacement_owner_surface"]
    assert bridge["required_opl_readback_ref"] == inventory_bridge["required_opl_readback_ref"]
    assert bridge["mas_projection_cannot_replace"] == inventory_bridge["mas_projection_cannot_replace"]
    assert bridge["legacy_helper_active_caller_scan"] == legacy_helper_scan
    assert (
        bridge["legacy_domain_authority_refs_index_role"]
        == refs_surface["active_caller_boundary"]["legacy_domain_authority_refs_index_role"]
        == inventory_bridge["legacy_domain_authority_refs_index_role"]
        == "explicit_history_replay_or_local_refs_inspection_only"
    )
    assert adapter_contract["active_caller_status"] == inventory_bridge["active_caller_status"]
    assert adapter_contract["active_caller_effect"] == inventory_bridge["active_caller_effect"]
    assert adapter_contract["active_caller_retains_surface"] is False
    assert adapter_contract["active_caller_retains_authority"] is False
    assert adapter_contract["active_caller_retains_runtime_authority"] is False
    assert adapter_contract["sqlite_persistence_allowed"] is False
    assert adapter_contract["sqlite_persistence_parameter_exposed"] is False
    assert (
        adapter_contract["completion_claim_requires_live_opl_readback_or_no_active_caller"]
        is True
    )
    assert adapter_contract["live_takeover_required_before_physical_delete"] is True
    assert (
        adapter_contract["legacy_domain_authority_refs_index_role"]
        == "explicit_history_replay_or_local_refs_inspection_only"
    )

    actuator = surfaces["domain_health_diagnostic_obligation_actuator"]
    assert actuator["active_caller_migrated"] is False
    assert actuator["validator_role"] == "accepted_owner_answer_or_opl_readback_shape_validator"
    assert actuator["local_allowed_outcome_table_role"] == (
        "contract_bound_result_shape_validation_not_supervisor_decision_engine"
    )
    assert actuator["mas_can_choose_supervisor_decision"] is False
    assert actuator["mas_can_mutate_recovery_obligation_store"] is False
    assert actuator["mas_can_run_supervisor_decision_engine"] is False
    assert actuator["mas_can_create_opl_command_event_or_outbox"] is False
    assert actuator["active_caller_boundary"] == {
        "active_caller_effect": (
            "consume_only_readback_projection_with_success_proof_gated_postcondition"
        ),
        "active_caller_retains_runtime_authority": False,
        "active_caller_retains_surface": True,
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "physical_delete_requires": [
            "opl_recovery_obligation_store_active_caller",
            "opl_supervisor_decision_engine_active_caller",
            "no_active_caller_scan",
            "replacement_parity_ref",
            "owner_retirement_decision_ref",
            "tombstone_or_provenance_ref",
        ],
        "request_projection_only_can_satisfy_success": False,
    }
    assert actuator["obligation_readback_boundary"] == {
        "request_projection_is_success_outcome": False,
        "success_proof_required_for_postcondition_ok": True,
        "success_proof_surface_kind": "dhd_apply_success_proof",
        "success_proof_requires_consumed_readback_identity": True,
        "consumed_readback_identity_surface_kind": "consumed_obligation_readback_identity",
        "success_proof_forbidden_when_request_projection_only": True,
        "success_outcome_source_families": [
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        ],
        "supervisor_disallowed_outcome_is_success": False,
        "readback_result_validator_boundary_required": True,
        "validator_role": "accepted_owner_answer_or_opl_readback_shape_validator",
        "local_allowed_outcome_table_role": (
            "contract_bound_result_shape_validation_not_supervisor_decision_engine"
        ),
        "fail_closed_typed_blocker_surface": "mas_domain_typed_blocker",
        "actuator_can_write_private_blocker_surface": False,
    }
    assert actuator["mas_typed_blocker_authority_result_adapter"] == (
        "med_autoscience.controllers.domain_health_diagnostic_parts."
        "obligation_actuator_parts.mas_domain_typed_blocker_authority_result"
    )
    assert actuator["typed_blocker_authority_result_adapter_surface"] == (
        "mas_domain_typed_blocker_authority_result_adapter"
    )
    assert actuator["typed_blocker_authority_result_adapter_boundary"] == {
        "actuator_private_write_authority": False,
        "adapter_role": "persist_mas_domain_typed_blocker_authority_result",
        "authority_owner": "med-autoscience",
        "authority_result_surface": "mas_domain_typed_blocker",
        "can_authorize_provider_admission": False,
        "can_claim_paper_progress": False,
        "can_create_opl_command": False,
        "can_create_opl_event": False,
        "can_create_opl_outbox": False,
        "can_create_opl_stage_run": False,
        "can_run_supervisor_decision_engine": False,
        "can_store_recovery_obligation": False,
        "can_write_controller_decision": False,
        "can_write_publication_eval": False,
        "surface_kind": "mas_domain_typed_blocker_authority_result_boundary",
    }
    assert actuator["can_write_fail_closed_typed_control_blocker"] is False
    assert actuator["fail_closed_typed_blocker_surface"] == "mas_domain_typed_blocker"
    assert actuator["actuator_direct_filesystem_write_retired"] is True
    assert actuator["actuator_can_write_private_blocker_surface"] is False
    assert actuator["transition_request_pending_can_close_physical_tail"] is False
    assert actuator["retirement_gate"]["owner_retirement_decision_required"] is True
    assert "mas_owned_recovery_obligation_store" in actuator["forbidden_claims"]
    assert "mas_owned_supervisor_decision_engine" in actuator["forbidden_claims"]


def test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)

    assert audit["surface_kind"] == "mas_runtime_surface_retirement_no_authority_audit"
    assert audit["status"] == "repo_no_authority_guard_landed_live_physical_retirement_tail_open"
    assert audit["generic_runtime_owner"] == "one-person-lab"
    assert audit["completion_claim_allowed"] is False
    assert audit["physical_retirement_tail_open"] is True
    assert audit["no_active_authority_caller_proven"] is True
    assert audit["violations"] == []
    assert "active_caller_exists_as_retention_reason" in audit["forbidden_completion_interpretations"]
    assert "maintenance_apply_gate_as_paper_progress" in audit["forbidden_completion_interpretations"]

    inventory_surfaces = {surface["surface_id"]: surface for surface in inventory["surfaces"]}
    legacy_helper_scan = inventory_surfaces["domain_authority_refs_index"][
        "opl_state_index_takeover_bridge"
    ]["legacy_helper_active_caller_scan"]
    open_surfaces = {surface["surface_id"]: surface for surface in audit["open_surfaces"]}
    assert open_surfaces["domain_authority_refs_index"]["authority_status"] == (
        "active_callers_migrated_opl_state_index_source_adapter_live_tail_open"
    )
    assert open_surfaces["domain_authority_refs_index"]["allowed_effect"] == (
        "opl_state_index_source_adapter_emitted_no_sqlite_persistence"
    )
    assert (
        open_surfaces["domain_authority_refs_index"][
            "domain_authority_refs_no_active_replay_local_inspection_caller_proven"
        ]
        is False
    )
    assert (
        open_surfaces["domain_authority_refs_index"][
            "domain_authority_refs_physical_delete_allowed"
        ]
        is False
    )
    assert (
        open_surfaces["domain_authority_refs_index"][
            "domain_authority_refs_legacy_helper_active_caller_count"
        ]
        == len(legacy_helper_scan["active_callers"])
    )
    assert open_surfaces["default_executor_dispatch_request"]["authority_status"] == (
        "legacy_default_executor_carrier_opl_stage_run_abi_provenance_only"
    )
    assert open_surfaces["default_executor_dispatch_request"]["allowed_effect"] == (
        "opl_domain_progress_transition_runtime_intake_only"
    )
    legacy_carrier_inventory = inventory_surfaces["default_executor_dispatch_request"]
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
    assert open_surfaces["domain_owner_action_dispatch"]["authority_status"] == (
        "opl_authorized_owner_callable_adapter_live_tail_open"
    )
    assert open_surfaces["default_executor_execution_latest_wire_projection"]["authority_status"] == (
        "legacy_latest_history_only_stage_run_abi_provenance_tail_open"
    )
    assert open_surfaces["default_executor_execution_latest_wire_projection"]["allowed_effect"] == (
        "canonical_owner_receipt_or_legacy_stage_run_closeout_provenance_only"
    )
    assert open_surfaces["default_executor_execution_latest_wire_projection"][
        "legacy_stage_run_abi_role"
    ] == "opl_stagerun_closeout_provenance_identity_recovery_only"
    assert open_surfaces["default_executor_execution_latest_wire_projection"][
        "legacy_stage_run_provider_admission_authority"
    ] is False
    assert open_surfaces["default_executor_execution_latest_wire_projection"][
        "legacy_stage_run_execution_authority"
    ] is False
    assert open_surfaces["runtime_storage_maintenance"]["apply_authorization_surface"] == (
        "opl_runtime_storage_maintenance_authorization"
    )
    assert all(surface["active_caller_retains_authority"] is False for surface in open_surfaces.values())
    assert all(
        surface["active_caller_retains_runtime_authority"] is False
        for surface in open_surfaces.values()
    )

    bad_inventory = json.loads(json.dumps(inventory))
    refs_surface = next(
        surface
        for surface in bad_inventory["surfaces"]
        if surface["surface_id"] == "domain_authority_refs_index"
    )
    refs_surface["active_caller_boundary"]["active_caller_retains_authority"] = True
    refs_surface["retirement_gate"]["active_caller_alone_retains_surface"] = True
    refs_surface["authority_boundary"]["can_authorize_provider_admission"] = True
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "no_active_replay_or_local_inspection_caller_proven"
    ] = True
    refs_surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"][
        "physical_delete_allowed"
    ] = True
    refs_surface["retirement_gate"][
        "no_active_replay_or_local_inspection_caller_proven"
    ] = True
    refs_surface["retirement_gate"]["physical_delete_allowed"] = True

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        ("domain_authority_refs_index", "truthy_authority_flag:active_caller_boundary.active_caller_retains_authority"),
        ("domain_authority_refs_index", "truthy_authority_flag:authority_boundary.can_authorize_provider_admission"),
        ("domain_authority_refs_index", "active_caller_retains_authority"),
        ("domain_authority_refs_index", "active_caller_alone_can_retain_surface"),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_active_tail_must_not_claim_no_active_replay_local_inspection_callers",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_active_replay_local_inspection_callers_block_physical_delete",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_no_active_claim_contradicts_active_replay_local_inspection_callers",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_retirement_gate_must_not_claim_no_active_replay_local_inspection_callers",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_retirement_gate_must_not_allow_physical_delete",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}

    legacy_bad_inventory = json.loads(json.dumps(inventory))
    legacy_latest = next(
        surface
        for surface in legacy_bad_inventory["surfaces"]
        if surface["surface_id"] == "default_executor_execution_latest_wire_projection"
    )
    legacy_latest["legacy_wire_default_reader_fallback_allowed"] = True
    legacy_latest["current_reader_boundary"][
        "default_executor_execution_candidates_reads_legacy_wire_by_default"
    ] = True
    legacy_latest["history_replay_boundary"].pop(
        "default_executor_receipt_consumption_requires_allow_legacy_fallback"
    )

    legacy_violations = retirement.validate_runtime_surface_retirement_inventory(legacy_bad_inventory)

    assert {
        ("default_executor_execution_latest_wire_projection", "legacy_default_reader_fallback_allowed"),
        (
            "default_executor_execution_latest_wire_projection",
            (
                "current_reader_legacy_fallback:"
                "default_executor_execution_candidates_reads_legacy_wire_by_default"
            ),
        ),
        (
            "default_executor_execution_latest_wire_projection",
            (
                "history_replay_missing_explicit_opt_in:"
                "default_executor_receipt_consumption_requires_allow_legacy_fallback"
            ),
        ),
    } <= {(item["surface_id"], item["reason"]) for item in legacy_violations}

    legacy_stage_run_bad_inventory = json.loads(json.dumps(inventory))
    legacy_stage_run = next(
        surface
        for surface in legacy_stage_run_bad_inventory["surfaces"]
        if surface["surface_id"] == "default_executor_execution_latest_wire_projection"
    )
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "stage_closeout_packets_can_authorize_provider_admission"
    ] = True
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "stage_closeout_packets_can_authorize_execution"
    ] = True
    legacy_stage_run["legacy_stage_run_abi_boundary"][
        "terminal_closeout_consumption_requires_owner_result_or_typed_blocker"
    ] = False
    legacy_stage_run_scan = legacy_stage_run["legacy_stage_run_abi_boundary"][
        "active_stage_run_abi_caller_scan"
    ]
    legacy_stage_run_scan["no_active_stage_run_abi_caller_proven"] = True
    legacy_stage_run_scan["physical_delete_allowed"] = True

    legacy_stage_run_violations = retirement.validate_runtime_surface_retirement_inventory(
        legacy_stage_run_bad_inventory
    )

    assert {
        (
            "default_executor_execution_latest_wire_projection",
            (
                "truthy_authority_flag:legacy_stage_run_abi_boundary."
                "stage_closeout_packets_can_authorize_provider_admission"
            ),
        ),
        (
            "default_executor_execution_latest_wire_projection",
            (
                "truthy_authority_flag:legacy_stage_run_abi_boundary."
                "stage_closeout_packets_can_authorize_execution"
            ),
        ),
        (
            "default_executor_execution_latest_wire_projection",
            (
                "legacy_stage_run_abi_authority:"
                "stage_closeout_packets_can_authorize_provider_admission"
            ),
        ),
        (
            "default_executor_execution_latest_wire_projection",
            "legacy_stage_run_abi_authority:stage_closeout_packets_can_authorize_execution",
        ),
        (
            "default_executor_execution_latest_wire_projection",
            "stage_closeout_terminal_consumption_not_owner_result_bound",
        ),
        (
            "default_executor_execution_latest_wire_projection",
            "stage_closeout_active_tail_must_not_claim_no_active_callers",
        ),
        (
            "default_executor_execution_latest_wire_projection",
            "stage_closeout_active_callers_block_physical_delete",
        ),
        (
            "default_executor_execution_latest_wire_projection",
            "stage_closeout_no_active_claim_contradicts_active_callers",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in legacy_stage_run_violations}

    carrier_bad_inventory = json.loads(json.dumps(inventory))
    legacy_carrier = next(
        surface
        for surface in carrier_bad_inventory["surfaces"]
        if surface["surface_id"] == "default_executor_dispatch_request"
    )
    legacy_carrier["active_caller_boundary"]["provider_admission_pending"] = True
    legacy_carrier["legacy_stage_run_abi_provenance_boundary"]["mas_can_create_stage_run"] = True
    legacy_carrier["legacy_stage_run_abi_provenance_boundary"][
        "requires_opl_domain_progress_transition_runtime_intake"
    ] = False
    legacy_carrier["legacy_source_contamination_boundary"][
        "source_dispatch_claims_are_diagnostic_only"
    ] = False
    legacy_carrier["legacy_source_contamination_boundary"][
        "polluted_source_payload_can_authorize_provider_admission"
    ] = True
    legacy_carrier["legacy_source_contamination_boundary"]["forbidden_source_claims"].remove(
        "provider_admission_pending"
    )

    carrier_violations = retirement.validate_runtime_surface_retirement_inventory(
        carrier_bad_inventory
    )

    assert {
        (
            "default_executor_dispatch_request",
            "legacy_carrier_active_boundary_forbidden:provider_admission_pending",
        ),
        (
            "default_executor_dispatch_request",
            "legacy_stage_run_abi_forbidden:mas_can_create_stage_run",
        ),
        (
            "default_executor_dispatch_request",
            "legacy_carrier_missing_opl_runtime_intake_requirement",
        ),
        (
            "default_executor_dispatch_request",
            "legacy_source_claims_not_diagnostic_only",
        ),
        (
            "default_executor_dispatch_request",
            "truthy_authority_flag:legacy_source_contamination_boundary."
            "polluted_source_payload_can_authorize_provider_admission",
        ),
        (
            "default_executor_dispatch_request",
            "legacy_source_boundary_forbidden:"
            "polluted_source_payload_can_authorize_provider_admission",
        ),
        (
            "default_executor_dispatch_request",
            "legacy_source_boundary_missing_forbidden_source_claims",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in carrier_violations}

    runtime_health_bad_inventory = json.loads(json.dumps(inventory))
    runtime_health = next(
        surface
        for surface in runtime_health_bad_inventory["surfaces"]
        if surface["surface_id"] == "runtime_health_kernel"
    )
    runtime_health["local_event_log_append_from_status_payload"] = True
    runtime_health["active_caller_boundary"]["active_caller_retains_runtime_authority"] = True
    runtime_health["active_caller_boundary"][
        "runtime_health_epoch_is_currentness_authority"
    ] = True
    runtime_health["active_caller_boundary"][
        "canonical_runtime_action_is_next_action_authority"
    ] = True
    runtime_health["active_caller_boundary"]["attempt_liveness_owner"] = "med-autoscience"
    runtime_health["diagnostic_projection_boundary"]["can_authorize_provider_admission"] = True
    runtime_health["diagnostic_projection_boundary"]["can_claim_paper_progress"] = True
    runtime_health["diagnostic_projection_boundary"][
        "canonical_runtime_action_is_diagnostic_hint"
    ] = False
    runtime_health["retirement_gate"][
        "runtime_health_live_opl_observability_readback_required"
    ] = False

    runtime_health_violations = retirement.validate_runtime_surface_retirement_inventory(
        runtime_health_bad_inventory
    )

    assert {
        (
            "runtime_health_kernel",
            "runtime_health_status_payload_can_append_event_log",
        ),
        (
            "runtime_health_kernel",
            (
                "truthy_authority_flag:active_caller_boundary."
                "active_caller_retains_runtime_authority"
            ),
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:active_caller_retains_runtime_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:runtime_health_epoch_is_currentness_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_active_boundary_forbidden:canonical_runtime_action_is_next_action_authority",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_attempt_liveness_owner_not_opl",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_projection_forbidden:can_authorize_provider_admission",
        ),
        (
            "runtime_health_kernel",
            "runtime_health_projection_forbidden:can_claim_paper_progress",
        ),
        (
            "runtime_health_kernel",
            (
                "runtime_health_missing_diagnostic_hint_boundary:"
                "canonical_runtime_action_is_diagnostic_hint"
            ),
        ),
        (
            "runtime_health_kernel",
            "runtime_health_missing_live_opl_observability_gate",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in runtime_health_violations}


def test_domain_authority_refs_index_legacy_helper_scan_keeps_physical_delete_tail_open() -> None:
    inventory = json.loads(
        (REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json").read_text(
            encoding="utf-8"
        )
    )
    retirement = importlib.import_module(
        "med_autoscience.runtime_protocol.runtime_surface_retirement"
    )
    surface = {
        item["surface_id"]: item for item in inventory["surfaces"]
    }["domain_authority_refs_index"]
    scan = surface["opl_state_index_takeover_bridge"]["legacy_helper_active_caller_scan"]

    assert scan["status"] == "active_replay_or_local_inspection_callers_present_tail_open"
    assert scan["no_active_replay_or_local_inspection_caller_proven"] is False
    assert scan["physical_delete_allowed"] is False
    assert (
        scan["required_before_physical_delete"]
        == (
            "domain_authority_refs_index_live_state_index_takeover_or_"
            "no_active_replay_local_inspection_caller_physical_delete_ref"
        )
    )
    assert {
        (
            "paper_progress_transition_refs.record_paper_progress_transition_ref::"
            "persist_authority_refs_index_explicit_opt_in"
        ),
        "opl_domain_pack.family_adoption.build_opl_family_adoption_surface::inspect_authority_refs_index",
        "opl_domain_pack.family_adoption.build_product_entry_adoption_projection::sqlite_refs_index_ref",
        "opl_domain_pack.adoption_ref_payload.payload_from_authority_refs::legacy_sqlite_payload_projection",
    } <= set(scan["active_callers"])
    assert "explicit_history_replay" in scan["allowed_consumption"]
    assert "explicit_local_refs_inspection" in scan["allowed_consumption"]
    assert "legacy_helper_active_scan_as_physical_delete" in scan[
        "forbidden_completion_claims"
    ]

    audit = retirement.audit_runtime_surface_retirement_inventory(inventory)
    audited_surface = {
        item["surface_id"]: item for item in audit["open_surfaces"]
    }["domain_authority_refs_index"]

    assert (
        audited_surface[
            "domain_authority_refs_no_active_replay_local_inspection_caller_proven"
        ]
        is False
    )
    assert audited_surface["domain_authority_refs_physical_delete_allowed"] is False
    assert audited_surface["domain_authority_refs_legacy_helper_active_caller_count"] == len(
        scan["active_callers"]
    )
    assert audited_surface["physical_delete_gate_open"] is True
    assert audit["completion_claim_allowed"] is False

    bad_inventory = json.loads(json.dumps(inventory))
    bad_surface = {
        item["surface_id"]: item for item in bad_inventory["surfaces"]
    }["domain_authority_refs_index"]
    bad_scan = bad_surface["opl_state_index_takeover_bridge"][
        "legacy_helper_active_caller_scan"
    ]
    bad_scan["no_active_replay_or_local_inspection_caller_proven"] = True
    bad_scan["physical_delete_allowed"] = True
    bad_surface["retirement_gate"][
        "no_active_replay_or_local_inspection_caller_proven"
    ] = True
    bad_surface["retirement_gate"]["physical_delete_allowed"] = True

    violations = retirement.validate_runtime_surface_retirement_inventory(bad_inventory)

    assert {
        (
            "domain_authority_refs_index",
            "domain_authority_refs_active_tail_must_not_claim_no_active_replay_local_inspection_callers",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_active_replay_local_inspection_callers_block_physical_delete",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_no_active_claim_contradicts_active_replay_local_inspection_callers",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_retirement_gate_must_not_claim_no_active_replay_local_inspection_callers",
        ),
        (
            "domain_authority_refs_index",
            "domain_authority_refs_retirement_gate_must_not_allow_physical_delete",
        ),
    } <= {(item["surface_id"], item["reason"]) for item in violations}
