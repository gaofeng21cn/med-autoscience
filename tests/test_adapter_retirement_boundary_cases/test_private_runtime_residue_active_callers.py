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
    assert refs_surface["active_caller_migrated"] is False
    assert refs_surface["current_disposition"] == (
        "repo_replacement_parity_proven_live_state_index_takeover_tail_open"
    )
    assert refs_surface["active_caller_boundary"] == {
        "active_caller_effect": "body_free_refs_only_locator_index",
        "active_caller_retains_authority": False,
        "active_caller_retains_runtime_authority": False,
        "active_caller_retains_surface": True,
        "active_callers": [
            "stage_artifact_materializer.record_stage_artifact_delta_ref",
            "owner_route_reconcile.scan_output.record_owner_route_receipt",
            "domain_owner_action_dispatch.record_dispatch_receipt",
            "paper_progress_transition_refs.record_paper_progress_transition_ref",
            "runtime_storage_maintenance.record_archive_ref",
        ],
        "completion_claim_requires_live_owner_or_opl_readback": True,
        "physical_delete_requires": [
            "opl_state_index_kernel_takeover",
            "no_active_caller_scan",
            "replacement_parity_ref",
            "tombstone_or_provenance_ref",
        ],
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
        "repo_replacement_parity_proven": True,
        "replacement_parity_required": True,
        "tombstone_or_provenance_required": True,
    }
    assert refs_surface["opl_state_index_takeover_bridge"] == {
        "active_caller_status": "repo_proven_no_active_authority_caller",
        "active_caller_retains_authority": False,
        "active_caller_retains_surface": True,
        "bridge_status": "repo_replacement_parity_proven_live_takeover_tail_open",
        "completion_claim_requires_live_opl_readback_or_no_active_caller": True,
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
    }
    assert "mas_owned_state_index_kernel" in refs_surface["forbidden_claims"]

    refs_contract = importlib.import_module(
        "med_autoscience.runtime_protocol.domain_authority_refs_index"
    ).domain_authority_refs_index_contract()
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
    assert refs_contract["opl_state_index_kernel_takeover_bridge"][
        "active_caller_status"
    ] == "repo_proven_no_active_authority_caller"
    assert refs_contract["opl_state_index_kernel_takeover_bridge"][
        "active_caller_retains_surface"
    ] is True
    assert refs_contract["opl_state_index_kernel_takeover_bridge"][
        "active_caller_retains_authority"
    ] is False

    actuator = surfaces["domain_health_diagnostic_obligation_actuator"]
    assert actuator["active_caller_migrated"] is False
    assert actuator["active_caller_boundary"] == {
        "active_caller_effect": "consume_only_readback_projection_and_fail_closed_postcondition",
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
        "success_outcome_source_families": [
            "opl_runtime_readback",
            "mas_owner_answer_readback",
            "mas_domain_authority_readback",
        ],
        "request_projection_is_success_outcome": False,
        "supervisor_disallowed_outcome_is_success": False,
    }
    assert actuator["transition_request_pending_can_close_physical_tail"] is False
    assert actuator["retirement_gate"]["owner_retirement_decision_required"] is True
    assert "mas_owned_recovery_obligation_store" in actuator["forbidden_claims"]
    assert "mas_owned_supervisor_decision_engine" in actuator["forbidden_claims"]
