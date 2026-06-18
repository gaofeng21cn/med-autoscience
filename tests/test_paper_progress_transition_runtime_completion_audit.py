from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
AUDIT_PATH = REPO_ROOT / "contracts" / "paper_progress_transition_runtime_completion_audit.json"
REPLAY_STATUS_PATH = REPO_ROOT / "contracts" / "paper_progress_replay_live_evidence_status.json"
RETIREMENT_INVENTORY_PATH = (
    REPO_ROOT / "contracts" / "runtime" / "mas-runtime-surface-retirement-inventory.json"
)


def _audit() -> dict[str, object]:
    return json.loads(AUDIT_PATH.read_text(encoding="utf-8"))


def _replay_status() -> dict[str, object]:
    return json.loads(REPLAY_STATUS_PATH.read_text(encoding="utf-8"))


def _retirement_inventory() -> dict[str, object]:
    return json.loads(RETIREMENT_INVENTORY_PATH.read_text(encoding="utf-8"))


def test_transition_runtime_completion_audit_declares_non_completion_boundary() -> None:
    audit = _audit()

    assert audit["surface_kind"] == "paper_progress_transition_runtime_completion_audit"
    assert audit["version"] == "paper-progress-transition-runtime-completion-audit.v1"
    assert audit["state"] == "active_evidence_audit"
    assert audit["overall_status"] == "evidence_tail_open_not_complete"
    assert audit["completion_claim_allowed"] is False

    policy = audit["completion_claim_policy"]
    assert (
        policy["required_final_claim"]
        == "all_transition_runtime_gates_satisfied_with_current_repo_and_live_evidence"
    )
    assert policy["current_completion_status"] == "evidence_tail_open_not_complete"
    assert policy["docs_or_contract_can_claim_complete"] is False
    assert policy["focused_tests_can_claim_complete"] is False
    assert policy["opl_repo_slice_can_claim_mas_live_complete"] is False
    assert policy["projection_clean_can_claim_complete"] is False
    assert policy["queue_empty_can_claim_complete"] is False
    assert policy["dhd_dry_run_can_claim_complete"] is False

    assert audit["required_runtime_readback_sections"] == [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ]


def test_transition_runtime_completion_audit_covers_target_lanes_and_keeps_open_tails() -> None:
    audit = _audit()
    gates = {gate["gate_id"]: gate for gate in audit["gate_evidence_status"]}

    assert set(gates) == {
        "lane_0_contract_and_taxonomy",
        "lane_1_replay_fixtures",
        "lane_2_opl_runtime_repo_readback_shape",
        "lane_2_mas_policy_adapter_boundary",
        "lane_3_opl_substrate_hardening_live_consumption",
        "lane_4_projection_demotion_and_physical_retirement",
        "lane_5_live_paper_line_acceptance",
    }

    allowed_statuses = {
        "satisfied_with_repo_evidence",
        "satisfied_with_opl_repo_evidence",
        "evidence_required",
    }
    for gate in gates.values():
        assert gate["status"] in allowed_statuses, gate["gate_id"]
        assert gate["required_evidence_refs"], gate["gate_id"]
        assert gate["observed_refs"], gate["gate_id"]
        assert gate["false_completion_boundary"], gate["gate_id"]

    assert gates["lane_0_contract_and_taxonomy"]["missing_evidence_tails"] == []
    assert gates["lane_1_replay_fixtures"]["missing_evidence_tails"] == []
    assert gates["lane_2_mas_policy_adapter_boundary"]["missing_evidence_tails"] == []
    assert gates["lane_3_opl_substrate_hardening_live_consumption"]["status"] == "evidence_required"
    assert gates["lane_4_projection_demotion_and_physical_retirement"]["status"] == "evidence_required"
    assert gates["lane_5_live_paper_line_acceptance"]["status"] == "evidence_required"

    open_tails = set(audit["open_evidence_tails"])
    assert {
        "OPL outbox and StageRun identity live readback for the same transition request",
        "DHD apply exactly-one live outcome when explicitly delegated",
        "provider admission arbiter fully consuming OPL transition events",
        "DM002/DM003 fresh live paper-line outcome per allowed exactly-one family",
        "domain_authority_refs_index OPL StateIndexKernel takeover or no-active-caller proof",
        "domain_health_diagnostic_obligation_actuator physical retirement owner decision or no-active-caller proof",
    } <= open_tails


def test_transition_runtime_completion_audit_rejects_known_false_completion_claims() -> None:
    audit = _audit()

    assert {
        "contract_landed",
        "docs_updated",
        "focused_tests_passed",
        "make_test_meta_passed",
        "scripts_verify_passed",
        "OPL_repo_slice_landed",
        "DHD_dry_run",
        "DHD_observe_only",
        "queue_empty",
        "provider_completed",
        "provider_admission_pending_count=0",
        "transition_request_pending_count=0",
        "projection_clean",
        "read_model_refreshed",
        "refs_only_ledger",
        "command_event_log_present",
        "event_id_present_without_full_readback",
        "outbox_item_id_present_without_full_readback",
        "StageRun_identity_present_without_currentness_match",
    } <= set(audit["rejected_completion_claims"])

    non_claims = audit["non_claims"]
    assert non_claims["all_mas_private_surfaces_physically_retired"] is False
    assert non_claims["domain_progress_transition_runtime_live_complete"] is False
    assert non_claims["dhd_apply_runtime_ready"] is False
    assert non_claims["provider_admission_ready"] is False
    assert non_claims["dm002_dm003_live_paper_progress"] is False
    assert non_claims["paper_closure"] is False
    assert non_claims["publication_ready"] is False
    assert non_claims["production_ready"] is False


def test_transition_runtime_completion_audit_matches_replay_status_open_tails() -> None:
    audit = _audit()
    replay = _replay_status()

    assert replay["current_status"]["live_paper_progress_claim_allowed"] is False
    assert set(replay["remaining_evidence_tails"]) <= set(audit["open_evidence_tails"])
    assert {
        "queue_empty",
        "DHD_dry_run",
        "provider_admission_pending_count=0",
        "focused_tests_passed",
        "docs_updated",
        "contract_landed",
        "command_event_log_readback_extraction",
    } <= set(replay["forbidden_completion_interpretations"])
    assert set(replay["forbidden_completion_interpretations"]) & set(
        audit["rejected_completion_claims"]
    )


def test_transition_runtime_completion_audit_tracks_retirement_inventory_tails() -> None:
    audit = _audit()
    inventory = _retirement_inventory()
    surfaces = {surface["surface_id"]: surface for surface in inventory["surfaces"]}
    physical_gate = {
        gate["gate_id"]: gate for gate in audit["gate_evidence_status"]
    }["lane_4_projection_demotion_and_physical_retirement"]

    assert surfaces["runtime_health_kernel"]["current_disposition"] == "read_only_diagnostic_publisher"
    assert surfaces["runtime_health_kernel"]["mas_local_event_append_api_retired"] is True
    assert surfaces["domain_owner_action_dispatch"]["current_disposition"] == (
        "opl_authorized_owner_callable_adapter"
    )
    assert surfaces["domain_health_diagnostic_obligation_actuator"]["current_disposition"] == (
        "opl_recovery_obligation_readback_consumer"
    )
    assert surfaces["domain_authority_refs_index"]["active_caller_migrated"] is False

    assert {
        "domain_authority_refs_index_opl_state_index_kernel_takeover_or_no_active_caller_ref",
        "domain_health_diagnostic_obligation_actuator_no_active_caller_or_owner_retirement_decision_ref",
        "domain_owner_action_dispatch_live_opl_authorization_for_every_active_caller_ref",
        "legacy_default_executor_carrier_physical_delete_ref",
    } <= set(physical_gate["missing_evidence_tails"])
    assert "inventory_entry_updated" in physical_gate["false_completion_boundary"]


def test_transition_runtime_completion_audit_records_fresh_opl_repo_evidence_without_live_claim() -> None:
    audit = _audit()
    gates = {gate["gate_id"]: gate for gate in audit["gate_evidence_status"]}
    opl_gate = gates["lane_2_opl_runtime_repo_readback_shape"]

    assert opl_gate["status"] == "satisfied_with_opl_repo_evidence"
    assert {
        (
            "external_repo:one-person-lab@3aaf41766f7c454fb6938633b05f4e18c9d061b7#"
            "src/family-runtime-domain-progress-transition-runtime.ts"
        ),
        (
            "external_repo:one-person-lab@3aaf41766f7c454fb6938633b05f4e18c9d061b7#"
            "src/family-runtime-domain-progress-transition-runtime-parts/live-readback.ts"
        ),
    } <= set(opl_gate["observed_refs"])
    assert {
        "MAS_same_transition_request_consumes_opl_runtime_live_readback_ref",
        "provider_hosted_stage_attempt_live_readback_for_DM002_DM003_ref",
        "terminal_closeout_side_effect_consumed_by_MAS_owner_answer_ref",
    } <= set(opl_gate["missing_evidence_tails"])
    assert "OPL_repo_tests_as_MAS_live_acceptance" in opl_gate["false_completion_boundary"]
    assert audit["completion_claim_allowed"] is False
