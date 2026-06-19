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
        "partial",
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
    assert gates["lane_4_projection_demotion_and_physical_retirement"]["status"] == "partial"
    assert gates["lane_5_live_paper_line_acceptance"]["status"] == "evidence_required"
    assert {
        (
            "contracts/paper_progress_replay_live_evidence_status.json#/replay_coverage/"
            "provider_admission_same_identity_live_readback_consumes_transition_request"
        ),
        (
            "contracts/paper_progress_replay_live_evidence_status.json#/replay_coverage/"
            "provider_admission_cross_identity_readback_remains_request_pending"
        ),
        (
            "contracts/paper_progress_replay_live_evidence_status.json#/replay_coverage/"
            "provider_admission_bare_transaction_fragments_rejected"
        ),
    } <= set(gates["lane_1_replay_fixtures"]["observed_refs"])

    open_tails = set(audit["open_evidence_tails"])
    assert {
        "OPL outbox and StageRun identity live readback for the same transition request",
        "DHD apply exactly-one live outcome when explicitly delegated",
        (
            "fresh live OPL event/outbox/StageRun consumption readback reaches provider "
            "admission arbiter for current DM002/DM003 transition identity"
        ),
        (
            "fresh DM002/DM003 same-identity OPL provider-admission live readback "
            "instead of replay fixture readback"
        ),
        "fresh DM002/DM003 paper-line accepted outcome after provider-admission readback consumption",
        "DM002/DM003 fresh live paper-line outcome per allowed exactly-one family",
        (
            "legacy default-executor carrier no-active StageRun ABI caller physical delete "
            "proof after OPL StageRun ABI/provenance boundary proof"
        ),
        (
            "legacy default-executor carrier OPL DomainProgressTransitionRuntime / outbox / StageRun "
            "live readback or no-active-carrier-caller physical delete proof after OPL StageRun ABI/provenance boundary proof"
        ),
        (
            "domain_authority_refs_index live OPL StateIndexKernel takeover plus "
            "physical-delete/tombstone proof after no-active replay/local-inspection proof "
            "and active caller source-adapter migration"
        ),
        "domain_health_diagnostic_obligation_actuator physical retirement owner decision or no-active-caller proof",
        "domain_owner_action_dispatch live every-active-caller soak or no-active-caller proof",
    } <= open_tails


def test_transition_runtime_completion_audit_splits_repo_source_and_live_runtime_columns() -> None:
    audit = _audit()
    columns = audit["completion_columns"]
    repo_source = columns["repo_source_retirement_completion"]
    live_runtime = columns["live_runtime_readiness_completion"]
    physical_gate = {
        gate["gate_id"]: gate for gate in audit["gate_evidence_status"]
    }["lane_4_projection_demotion_and_physical_retirement"]

    assert repo_source["scope"] == "code_contract_test_docs_physical_retirement_only"
    assert repo_source["status"] == "partial"
    assert repo_source["live_runtime_evidence_required"] is False
    assert repo_source["item_completion_claim_allowed_when_criteria_satisfied"] is True
    assert {
        "active callsites migrated to OPL primitives or MAS minimal PaperProgressPolicyAdapter / authority adapter",
        (
            "old module, alias, wrapper, compat shim, private scheduler/log/outbox/"
            "projection authority physically deleted or tombstoned"
        ),
        (
            "paths without live proof fail closed with a typed blocker instead of "
            "restoring MAS private runtime authority"
        ),
        "focused, meta, and default verification pass for the deletion/tombstone slice",
        "docs, contracts, and runtime retirement inventory record the source disposition",
    } <= set(repo_source["completion_criteria"])
    assert {
        "missing OPL outbox / StageRun live readback",
        "missing DHD apply exactly-one live outcome",
        "missing provider running proof",
        "missing DM002/DM003 fresh paper-line outcome",
    } <= set(repo_source["non_blocking_live_runtime_tails"])
    assert "DHD_dry_run_missing" in repo_source["false_repo_source_blockers"]

    assert live_runtime["scope"] == (
        "OPL live readback, DHD apply exactly-one, provider running proof, "
        "DM002/DM003 live paper-line outcome"
    )
    assert live_runtime["blocks_repo_source_retirement"] is False
    assert live_runtime["blocks_final_runtime_paper_acceptance"] is True
    assert {
        "same-transition OPL command/event/outbox/StageRun identity readback",
        "DHD apply exactly-one live outcome when explicitly delegated",
        "provider admission or running proof backed by same-identity OPL runtime readback",
        (
            "fresh DM002/DM003 owner receipt, stable typed blocker, human gate, "
            "route-back evidence, strict running proof, or paper/gate/artifact semantic delta"
        ),
    } <= set(live_runtime["required_evidence"])
    assert "repo_source_retirement_complete" in live_runtime["false_live_completion_claims"]

    policy = audit["completion_claim_policy"]
    assert policy["repo_source_retirement_can_complete_without_live_runtime_evidence"] is True
    assert policy["live_runtime_readiness_can_claim_from_repo_source_retirement"] is False
    assert policy["final_runtime_or_paper_acceptance_still_requires_live_evidence"] is True
    assert audit["completion_claim_allowed"] is False
    assert audit["non_claims"]["repo_source_retirement_implies_live_runtime_ready"] is False
    assert audit["non_claims"]["repo_source_retirement_implies_paper_progress"] is False
    assert {
        "repo_source_retirement_complete_as_live_runtime_ready",
        "repo_source_retirement_complete_as_paper_progress",
        "live_runtime_evidence_missing_as_repo_source_retirement_blocker",
    } <= set(audit["rejected_completion_claims"])

    assert physical_gate["repo_source_retirement_status"] == repo_source["status"]
    assert physical_gate["live_runtime_readiness_status"] == live_runtime["status"]
    assert physical_gate["live_runtime_evidence_blocks_repo_source_retirement"] is False
    assert set(physical_gate["missing_evidence_tails"]) == set(
        physical_gate["repo_source_missing_evidence_tails"]
    )
    assert set(live_runtime["open_live_runtime_gaps"]) <= set(
        physical_gate["live_runtime_readiness_missing_evidence_tails"]
    )


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
    helper = __import__(
        "med_autoscience.controllers.opl_domain_progress_transition_contract",
        fromlist=["live_readback_evidence_source_contract"],
    )

    assert replay["current_status"]["live_paper_progress_claim_allowed"] is False
    assert replay["replay_to_live_separation_gate"]["readback_evidence_source_gate"] == (
        helper.live_readback_evidence_source_contract()
    )
    assert audit["completion_evidence_rules"]["live_readback_evidence_source_gate"] == (
        helper.live_readback_evidence_source_contract()
    )
    assert set(replay["remaining_evidence_tails"]) <= set(audit["open_evidence_tails"])
    separation_gate = replay["replay_to_live_separation_gate"]
    assert separation_gate["status"] == "evidence_tail_open"
    assert set(separation_gate["live_tails_that_remain_open"]) <= set(
        replay["remaining_evidence_tails"]
    )
    assert {
        "provider_admission_same_identity_live_readback_consumes_transition_request",
        "provider_admission_cross_identity_readback_remains_request_pending",
        "provider_admission_bare_transaction_fragments_rejected",
    } <= {item["trace_id"] for item in replay["replay_coverage"]}
    assert {
        "fresh DM002/DM003 same-identity OPL provider-admission live readback instead of replay fixture readback",
        "fresh DM002/DM003 paper-line accepted outcome after provider-admission readback consumption",
    } <= set(replay["remaining_evidence_tails"])
    assert {
        "queue_empty",
        "DHD_dry_run",
        "provider_admission_pending_count=0",
        "focused_tests_passed",
        "docs_updated",
        "contract_landed",
        "command_event_log_readback_extraction",
        "provider_admission_same_identity_replay_as_fresh_opl_readback",
        "provider_admission_same_identity_replay_as_live_paper_progress",
        "same_identity_readback_consumes_transition_request_as_paper_line_outcome",
        "valid_opl_readback_shape_without_claimable_evidence_source",
    } <= set(replay["forbidden_completion_interpretations"])
    assert set(replay["forbidden_completion_interpretations"]) & set(
        audit["rejected_completion_claims"]
    )
    assert {
        "provider_admission_same_identity_replay_as_fresh_opl_readback",
        "provider_admission_same_identity_replay_as_live_paper_progress",
        "same_identity_readback_consumes_transition_request_as_paper_line_outcome",
        "valid_opl_readback_shape_without_claimable_evidence_source",
    } <= set(audit["rejected_completion_claims"])


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
        "obligation_readback_projection_consumer"
    )
    assert surfaces["domain_health_diagnostic_obligation_actuator"][
        "fail_closed_typed_blocker_surface"
    ] == "mas_domain_typed_blocker"
    assert surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_readback_boundary"
    ]["mas_domain_authority_readback_requires_authority_boundary"] is True
    assert surfaces["domain_health_diagnostic_obligation_actuator"][
        "obligation_readback_boundary"
    ]["read_model_evidence_refs_can_satisfy_success"] is False
    assert surfaces["domain_authority_refs_index"]["current_disposition"] == "physically_retired"
    assert surfaces["domain_authority_refs_index"]["retained_mas_role"] == (
        "none_physically_retired_no_alias"
    )
    assert surfaces["domain_authority_refs_index"]["active_caller_boundary"][
        "active_caller_effect"
    ] == "opl_state_index_source_adapter_emitted_no_sqlite_persistence"
    assert surfaces["domain_authority_refs_index"]["active_caller_boundary"][
        "active_caller_retains_surface"
    ] is False
    assert surfaces["domain_authority_refs_index"]["active_caller_boundary"][
        "default_sqlite_persistence"
    ] is False
    assert surfaces["domain_authority_refs_index"]["active_caller_boundary"][
        "sqlite_persistence_requires_explicit_opt_in"
    ] is True
    assert surfaces["domain_authority_refs_index"]["active_caller_migrated"] is True
    assert surfaces["domain_authority_refs_index"]["retirement_gate"][
        "replacement_parity_proven"
    ] is True
    assert surfaces["domain_authority_refs_index"]["retirement_gate"][
        "repo_source_physical_retirement_authorized"
    ] is True
    assert surfaces["domain_authority_refs_index"]["retirement_gate"][
        "live_runtime_readiness_required_for_repo_source_delete"
    ] is False
    assert surfaces["domain_authority_refs_index"]["physical_delete_completion_basis"][
        "live_runtime_evidence_blocks_repo_source_delete"
    ] is False
    assert surfaces["default_executor_dispatch_request"]["active_caller_boundary"][
        "active_caller_effect"
    ] == "opl_domain_progress_transition_runtime_intake_only"
    assert surfaces["default_executor_dispatch_request"]["current_disposition"] == (
        "physically_retired"
    )
    assert surfaces["default_executor_dispatch_request"]["retained_mas_role"] == (
        "none_physically_retired_no_alias"
    )
    assert surfaces["default_executor_dispatch_request"]["active_caller_boundary"][
        "provider_admission_pending"
    ] is False
    assert surfaces["default_executor_dispatch_request"]["active_caller_boundary"][
        "active_caller_retains_surface"
    ] is False
    assert surfaces["default_executor_dispatch_request"][
        "legacy_stage_run_abi_provenance_boundary"
    ]["mas_can_create_stage_run"] is False
    assert surfaces["default_executor_dispatch_request"][
        "legacy_stage_run_abi_provenance_boundary"
    ]["requires_opl_domain_progress_transition_runtime_intake"] is True
    assert surfaces["default_executor_dispatch_request"][
        "opl_default_executor_carrier_tail_readback"
    ]["tail_readback_proven"] is False
    assert surfaces["default_executor_dispatch_request"][
        "opl_default_executor_carrier_tail_readback"
    ]["transition_request_pending_can_satisfy_readback"] is False
    assert surfaces["default_executor_dispatch_request"][
        "opl_default_executor_carrier_tail_readback"
    ]["request_only_carrier_can_authorize_provider_admission"] is False
    assert surfaces["default_executor_dispatch_request"]["retirement_gate"][
        "repo_source_physical_retirement_authorized"
    ] is True
    assert surfaces["default_executor_dispatch_request"]["retirement_gate"][
        "live_runtime_readiness_required_for_repo_source_delete"
    ] is False
    assert surfaces["default_executor_dispatch_request"]["physical_delete_completion_basis"][
        "live_runtime_evidence_blocks_repo_source_delete"
    ] is False
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "current_disposition"
    ] == "physically_retired"
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "retained_mas_role"
    ] == "none_physically_retired_no_alias"
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "legacy_stage_run_abi_boundary"
    ]["abi_role"] == "opl_stagerun_closeout_provenance_identity_recovery_only"
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "legacy_stage_run_abi_boundary"
    ]["stage_closeout_packets_can_authorize_provider_admission"] is False
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "legacy_stage_run_abi_boundary"
    ]["stage_closeout_packets_can_authorize_execution"] is False
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "retirement_gate"
    ]["repo_source_physical_retirement_authorized"] is True
    assert surfaces["default_executor_execution_latest_wire_projection"][
        "physical_delete_completion_basis"
    ]["live_runtime_evidence_blocks_repo_source_delete"] is False
    assert surfaces["runtime_lifecycle_payload_retention"]["current_disposition"] == (
        "opl_authorized_maintenance_callable_adapter_live_takeover_tail_open"
    )
    assert surfaces["runtime_lifecycle_payload_retention"]["apply_gate"][
        "required_authorization_surface"
    ] == "opl_runtime_lifecycle_maintenance_authorization"
    assert surfaces["runtime_storage_maintenance"]["current_disposition"] == (
        "opl_authorized_storage_maintenance_callable_adapter_live_takeover_tail_open"
    )
    assert surfaces["runtime_storage_maintenance"]["apply_gate"][
        "required_authorization_surface"
    ] == "opl_runtime_storage_maintenance_authorization"

    assert {
        "remaining old MAS runtime-like entries must be individually deleted, tombstoned, or explicitly reclassified as retained minimal MAS authority / OPL-authorized adapter surfaces",
        (
            "runtime inventory gates still need source-level reclassification where they encode "
            "live OPL readback as a physical-delete prerequisite rather than a live-runtime readiness tail"
        ),
        (
            "default-executor carrier and latest-wire history surfaces still need final physical "
            "delete/tombstone or explicit history-only provenance closeout once active callsites are migrated"
        ),
    } <= set(physical_gate["repo_source_missing_evidence_tails"])
    assert set(physical_gate["missing_evidence_tails"]) == set(
        physical_gate["repo_source_missing_evidence_tails"]
    )
    assert {
        "OPL outbox and StageRun identity live readback for the same transition request",
        "DHD apply exactly-one live outcome when explicitly delegated",
        (
            "fresh live OPL event/outbox/StageRun consumption readback reaches provider "
            "admission arbiter for current DM002/DM003 transition identity"
        ),
    } <= set(physical_gate["live_runtime_readiness_missing_evidence_tails"])
    assert {
        "domain_authority_refs_index_live_state_index_takeover_or_no_active_replay_local_inspection_caller_physical_delete_ref",
        "domain_health_diagnostic_obligation_actuator_no_active_caller_or_owner_retirement_decision_ref",
        "domain_owner_action_dispatch_live_every_active_caller_soak_or_no_active_caller_ref",
        "default_executor_dispatch_request_opl_default_executor_carrier_tail_readback_ref",
        "legacy_default_executor_carrier_no_active_stage_run_abi_caller_physical_delete_ref",
    }.isdisjoint(set(physical_gate["missing_evidence_tails"]))
    assert (
        "legacy_default_executor_carrier_opl_stagerun_abi_or_no_active_caller_physical_delete_ref"
        not in physical_gate["missing_evidence_tails"]
    )
    assert (
        "tests/test_adapter_retirement_boundary.py::"
        "test_default_executor_stage_closeout_candidates_are_opl_stagerun_abi_provenance_only"
    ) in physical_gate["observed_refs"]
    assert (
        "contracts/runtime/mas-runtime-surface-retirement-inventory.json#/surfaces/"
        "default_executor_execution_latest_wire_projection#"
        "legacy_stage_run_abi_boundary.active_stage_run_abi_caller_scan"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_adapter_retirement_boundary.py::"
        "test_legacy_stage_run_abi_active_caller_scan_keeps_physical_delete_tail_open"
    ) in physical_gate["observed_refs"]
    assert (
        "legacy_stage_run_abi_provenance_without_no_active_caller_physical_delete"
        in physical_gate["false_completion_boundary"]
    )
    assert (
        "active_stage_run_abi_caller_scan_as_physical_delete"
        in physical_gate["false_completion_boundary"]
    )
    assert (
        "runtime_lifecycle_payload_retention_live_opl_cleanup_policy_takeover_or_no_active_caller_physical_delete_ref"
        not in physical_gate["missing_evidence_tails"]
    )
    assert (
        "runtime_storage_maintenance_live_opl_storage_policy_takeover_or_no_active_caller_physical_delete_ref"
        not in physical_gate["missing_evidence_tails"]
    )
    assert (
        "tests/test_domain_owner_action_dispatch_contract.py::"
        "test_transition_request_projection_requires_opl_execution_authorization_for_every_supported_action"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_domain_owner_action_dispatch_cases/opl_authorization_boundary.py::"
        "test_owner_dispatch_accepts_bound_domain_progress_transition_readback_only"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_runtime_storage_maintenance_cases/runtime_refs_only_state_index_pilot.py::"
        "test_refs_only_state_index_pilot_indexes_small_runtime_refs_without_bodies"
    ) in physical_gate["observed_refs"]
    assert (
        "src/med_autoscience/runtime_protocol/runtime_surface_retirement.py::"
        "audit_runtime_surface_retirement_inventory"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_adapter_retirement_boundary_cases/test_private_runtime_residue_active_callers.py::"
        "test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "test_obligation_actuator_postcondition.py::_assert_exactly_one_dhd_apply_outcome#"
        "consumed_obligation_readback_identity"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "test_obligation_actuator_outcomes.py::"
        "test_domain_health_diagnostic_apply_accepts_opl_provider_admission_result_as_closed_outcome#"
        "consumed_obligation_readback_identity"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "test_obligation_actuator_outcomes.py::"
        "test_domain_health_diagnostic_apply_rejects_read_model_human_gate_and_route_back_refs"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
        "test_obligation_actuator_outcomes.py::"
        "test_domain_health_diagnostic_apply_accepts_owner_gate_authority_payload_refs"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_paper_recovery_state_cases/owner_gate_projection_cases.py::"
        "test_runtime_report_preserves_human_gate_authority_payload"
    ) in physical_gate["observed_refs"]
    assert (
        "contracts/runtime/mas-runtime-surface-retirement-inventory.json#/surfaces/"
        "default_executor_dispatch_request#legacy_stage_run_abi_provenance_boundary"
    ) in physical_gate["observed_refs"]
    assert (
        "contracts/runtime/mas-runtime-surface-retirement-inventory.json#/surfaces/"
        "default_executor_dispatch_request#opl_default_executor_carrier_tail_readback"
    ) in physical_gate["observed_refs"]
    assert (
        "contracts/runtime/mas-runtime-surface-retirement-inventory.json#/surfaces/"
        "default_executor_execution_latest_wire_projection#legacy_stage_run_abi_boundary"
    ) in physical_gate["observed_refs"]
    assert (
        "src/med_autoscience/controllers/study_transition_receipt_consumption_parts/"
        "default_executor_candidates.py::_execution_from_stage_closeout#"
        "legacy_stage_run_abi_provenance_only"
    ) in physical_gate["observed_refs"]
    assert (
        "src/med_autoscience/runtime_protocol/runtime_surface_retirement.py::"
        "_validate_legacy_default_executor_carrier"
    ) in physical_gate["observed_refs"]
    assert (
        "src/med_autoscience/runtime_protocol/runtime_surface_retirement.py::"
        "_validate_default_executor_carrier_tail_readback"
    ) in physical_gate["observed_refs"]
    assert (
        "src/med_autoscience/runtime_protocol/runtime_surface_retirement.py::"
        "_validate_legacy_stage_run_abi"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_adapter_retirement_boundary.py::"
        "test_runtime_like_surfaces_have_machine_readable_opl_migration_inventory#"
        "legacy_default_executor_carrier_stage_run_abi_boundary"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_adapter_retirement_boundary.py::"
        "test_runtime_like_surfaces_have_machine_readable_opl_migration_inventory#"
        "default_executor_carrier_tail_readback"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_adapter_retirement_boundary_cases/test_private_runtime_residue_active_callers.py::"
        "test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression#"
        "legacy_default_executor_carrier_authority_regression"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_adapter_retirement_boundary_cases/test_private_runtime_residue_active_callers.py::"
        "test_runtime_surface_retirement_no_authority_audit_blocks_active_caller_regression#"
        "default_executor_carrier_tail_false_completion_guard"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_runtime_lifecycle_payload_retention.py::"
        "test_runtime_lifecycle_payload_retention_apply_requires_opl_authorization"
    ) in physical_gate["observed_refs"]
    assert (
        "tests/test_runtime_storage_maintenance_cases/runtime_storage_maintenance_basics.py::"
        "test_workspace_storage_apply_without_opl_authorization_blocks_before_physical_cleanup"
    ) in physical_gate["observed_refs"]
    assert "inventory_entry_updated" in physical_gate["false_completion_boundary"]
    assert "active_caller_exists_as_retention_reason" in physical_gate["false_completion_boundary"]
    assert "read_only_projection_as_execution_authority" in physical_gate["false_completion_boundary"]
    assert (
        "legacy_carrier_provenance_as_default_executor_carrier_tail_readback"
        in physical_gate["false_completion_boundary"]
    )
    assert (
        "transition_request_pending_as_opl_live_readback"
        in physical_gate["false_completion_boundary"]
    )
    assert (
        "request_only_carrier_as_provider_admission"
        in physical_gate["false_completion_boundary"]
    )
    assert "storage_authorization_gate_as_live_opl_takeover" in physical_gate["false_completion_boundary"]


def test_transition_runtime_completion_audit_records_provider_admission_repo_consumption_without_live_claim() -> None:
    audit = _audit()
    gates = {gate["gate_id"]: gate for gate in audit["gate_evidence_status"]}
    lane = gates["lane_3_opl_substrate_hardening_live_consumption"]
    required = {item["gate_id"]: item for item in audit["required_before_goal_complete"]}

    assert lane["status"] == "evidence_required"
    assert {
        (
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/"
            "provider_admission_current_control_arbiter.py::"
            "_provider_admission_readback_consumption_evidence"
        ),
        (
            "tests/test_provider_admission_current_control_arbiter.py::"
            "test_provider_admission_current_control_records_retained_pending_arbiter_decision"
            "#opl_transition_event_consumption"
        ),
        (
            "tests/test_provider_admission_current_control_cases/"
            "transition_request_consume_only_cases.py::"
            "test_provider_admission_current_control_treats_mas_request_without_opl_readback_as_non_advancing"
            "#bare_event_outbox_stage_run_fragment_rejected"
        ),
    } <= set(lane["observed_refs"])
    assert (
        "provider admission arbiter fully consuming OPL transition events"
        not in lane["missing_evidence_tails"]
    )
    assert {
        (
            "fresh live OPL event/outbox/StageRun consumption readback reaches provider "
            "admission arbiter for current DM002/DM003 transition identity"
        ),
        (
            "fresh DM002/DM003 same-identity OPL provider-admission live readback "
            "instead of replay fixture readback"
        ),
        "fresh DM002/DM003 paper-line accepted outcome after provider-admission readback consumption",
        "DHD apply exactly-one live outcome when explicitly delegated",
        "DM002/DM003 fresh live paper-line outcome per allowed exactly-one family",
    } <= set(lane["missing_evidence_tails"])
    assert "contracts/paper_progress_replay_live_evidence_status.json#/replay_to_live_separation_gate" in (
        lane["observed_refs"]
    )
    assert {
        "provider_admission_same_identity_replay_as_fresh_opl_readback",
        "provider_admission_same_identity_replay_as_live_paper_progress",
        "same_identity_readback_consumes_transition_request_as_paper_line_outcome",
    } <= set(lane["false_completion_boundary"])
    provider_gate = required["provider_admission_event_consumption"]
    assert provider_gate["status"] == "open"
    assert "live DM002/DM003" in provider_gate["repo_side_evidence"]
    assert audit["completion_claim_allowed"] is False


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
