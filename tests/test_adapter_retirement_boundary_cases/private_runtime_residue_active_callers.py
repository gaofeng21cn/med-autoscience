from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
OBLIGATION_ACTUATOR_TAIL_READBACK_REQUIREMENT = {
    "surface_kind": "opl_obligation_actuator_tail_readback_requirement",
    "runtime_owner": "one-person-lab",
    "runtime_kind": "RecoveryObligationStore/SupervisorDecisionEngine",
    "required_before_physical_delete": [
        "opl_recovery_obligation_store_active_caller_readback",
        "opl_supervisor_decision_engine_active_caller_readback",
        "no_active_mas_obligation_actuator_caller_scan",
        "no_forbidden_write_proof",
        "owner_retirement_decision",
        "tombstone_or_provenance",
    ],
    "required_active_caller_readbacks": [
        "opl_recovery_obligation_store_active_caller_readback",
        "opl_supervisor_decision_engine_active_caller_readback",
    ],
    "mas_policy_projection_can_satisfy_readback": False,
    "mas_request_projection_can_satisfy_readback": False,
    "focused_tests_can_satisfy_readback": False,
    "repo_no_authority_guard_can_satisfy_readback": False,
    "physical_delete_allowed_without_tail_proof": False,
}
OBLIGATION_ACTUATOR_TAIL_READBACK = {
    "surface_kind": "opl_obligation_actuator_tail_readback_requirement",
    "status": "tail_open",
    "runtime_owner": "one-person-lab",
    "runtime_kind": "RecoveryObligationStore/SupervisorDecisionEngine",
    "required_active_caller_readbacks": [
        "opl_recovery_obligation_store_active_caller_readback",
        "opl_supervisor_decision_engine_active_caller_readback",
    ],
    "required_before_physical_delete": (
        "domain_health_diagnostic_obligation_actuator_"
        "opl_obligation_actuator_tail_readback_ref"
    ),
    "physical_delete_requires": [
        "opl_recovery_obligation_store_active_caller_readback",
        "opl_supervisor_decision_engine_active_caller_readback",
        "no_active_mas_obligation_actuator_caller_scan",
        "no_forbidden_write_proof",
        "owner_retirement_decision",
        "tombstone_or_provenance",
    ],
    "tail_readback_proven": False,
    "no_active_mas_obligation_actuator_caller_proven": False,
    "physical_delete_allowed": False,
    "mas_policy_projection_can_satisfy_readback": False,
    "mas_request_projection_can_satisfy_readback": False,
    "repo_no_authority_guard_can_satisfy_readback": False,
    "focused_tests_can_satisfy_readback": False,
    "forbidden_completion_claims": [
        "repo_no_authority_guard_as_obligation_actuator_tail_readback",
        "mas_policy_projection_as_opl_recovery_obligation_store_readback",
        "mas_transition_request_as_supervisor_decision_engine_readback",
        "focused_tests_green_as_no_active_obligation_actuator_caller",
        "typed_blocker_authority_result_as_opl_supervisor_decision_engine_readback",
    ],
}
DOMAIN_AUTHORITY_REFS_NO_ACTIVE_LEGACY_HELPER_SCAN = {
    "status": "no_active_replay_or_local_inspection_callers",
    "no_active_replay_or_local_inspection_caller_proven": True,
    "physical_delete_allowed": False,
    "required_before_physical_delete": (
        "domain_authority_refs_index_live_state_index_takeover_or_"
        "no_active_replay_local_inspection_caller_physical_delete_ref"
    ),
    "active_callers": [],
    "retired_callers": [
        (
            "paper_progress_transition_refs.record_paper_progress_transition_ref::"
            "persist_authority_refs_index_explicit_opt_in"
        ),
    ],
    "allowed_consumption": [
        "explicit_history_replay",
        "explicit_local_refs_inspection",
        "tombstone_provenance",
    ],
    "forbidden_completion_claims": [
        "legacy_helper_no_active_scan_as_physical_delete",
        "opl_family_adoption_sqlite_inspection_as_current_projection",
        "legacy_sqlite_payload_projection_as_state_index_kernel_takeover",
        "explicit_replay_opt_in_as_live_opl_readback",
        "no_active_replay_local_inspection_scan_as_live_state_index_kernel_takeover",
    ],
}


def test_private_runtime_residue_active_callers_are_no_authority_refs_or_consume_only() -> None:
    inventory_path = REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    surfaces = {surface["surface_id"]: surface for surface in inventory["surfaces"]}

    refs_surface = surfaces["domain_authority_refs_index"]
    legacy_helper_scan = DOMAIN_AUTHORITY_REFS_NO_ACTIVE_LEGACY_HELPER_SCAN
    runtime_active_scan = {
        "status": "no_runtime_active_private_state_index_callers",
        "no_runtime_active_private_state_index_caller_proven": True,
        "runtime_active_caller_count": 0,
        "active_runtime_callers": [],
        "current_runtime_caller_route": (
            "med_autoscience.runtime_protocol.opl_state_index_source_adapter"
        ),
        "legacy_helper_status": "history_replay_or_local_inspection_only_tail_open",
        "physical_delete_allowed": False,
        "forbidden_completion_claims": [
            "runtime_active_no_private_caller_as_physical_delete",
            "history_replay_opt_in_as_runtime_active_caller",
            "source_adapter_manifest_as_live_opl_state_index_readback",
        ],
    }
    assert refs_surface["active_caller_migrated"] is True
    assert refs_surface["current_disposition"] == "physically_retired"
    assert refs_surface["retained_mas_role"] == "none_physically_retired_no_alias"
    assert refs_surface["tombstone_or_provenance_ref"] == (
        "docs/history/runtime/mas-private-surface-retirement.md#domain_authority_refs_index"
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
        "runtime_active_private_state_index_caller_scan": runtime_active_scan,
        "default_sqlite_persistence": False,
        "source_adapter_manifest_ref": (
            "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json"
        ),
        "family_adoption_reads_legacy_sqlite_helper": False,
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
        "live_runtime_readiness_required_for_repo_source_delete": False,
        "no_forbidden_write_proof_proven": True,
        "replacement_parity_proven": True,
        "repo_source_physical_retirement_authorized": True,
        "tombstone_or_provenance_proven": True,
    }
    assert refs_surface["opl_state_index_takeover_bridge"] == {
        "active_caller_db_path_does_not_imply_persistence": True,
        "active_caller_effect": "opl_state_index_source_adapter_emitted_no_sqlite_persistence",
        "active_caller_status": "repo_active_callers_migrated_to_opl_state_index_source_adapter",
        "active_caller_retains_authority": False,
        "active_caller_retains_surface": False,
        "bridge_status": "repo_replacement_parity_proven_live_takeover_tail_open",
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
        "runtime_active_private_state_index_caller_scan": runtime_active_scan,
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
        "source_adapter_manifest_ref": (
            "runtime/artifacts/opl_state_index_source_adapter/authority_refs_source.json"
        ),
        "family_adoption_current_projection": "opl_state_index_source_adapter_manifest",
        "family_adoption_reads_legacy_sqlite_helper": False,
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
    assert (
        bridge["runtime_active_private_state_index_caller_scan"]
        == inventory_bridge["runtime_active_private_state_index_caller_scan"]
        == runtime_active_scan
    )
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
    assert adapter_contract["runtime_active_private_state_index_caller_scan"] == runtime_active_scan
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
    assert actuator["opl_obligation_actuator_tail_readback"] == (
        OBLIGATION_ACTUATOR_TAIL_READBACK
    )
    assert actuator["obligation_readback_boundary"] == {
        "request_projection_is_success_outcome": False,
        "success_proof_required_for_postcondition_ok": True,
        "success_proof_surface_kind": "dhd_apply_success_proof",
        "success_proof_requires_consumed_readback_identity": True,
        "consumed_readback_identity_surface_kind": "consumed_obligation_readback_identity",
        "mas_domain_authority_readback_requires_authority_boundary": True,
        "read_model_evidence_refs_can_satisfy_success": False,
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
        "opl_obligation_actuator_tail_readback_requirement": (
            OBLIGATION_ACTUATOR_TAIL_READBACK_REQUIREMENT
        ),
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
