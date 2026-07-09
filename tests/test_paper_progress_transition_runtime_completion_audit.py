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
    assert policy["domain_diagnostic_dry_run_can_claim_complete"] is False

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
        "domain diagnostic apply exactly-one live outcome when explicitly delegated",
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
            "legacy owner-callable carrier no-active StageRun ABI caller physical delete "
            "proof after OPL StageRun ABI/provenance boundary proof"
        ),
        (
            "legacy owner-callable carrier OPL DomainProgressTransitionRuntime / outbox / StageRun "
            "live readback or no-active-carrier-caller physical delete proof after OPL StageRun ABI/provenance boundary proof"
        ),
        (
            "domain_authority_refs_index live OPL StateIndexKernel takeover plus "
            "physical-delete/tombstone proof after no-active replay/local-inspection proof "
            "and active caller source-adapter migration"
        ),
        "domain_diagnostic_obligation_actuator physical retirement owner decision or no-active-caller proof",
        "stage_outcome_authority live every-active-caller soak or no-active-caller proof",
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
    assert repo_source["status"] == "done"
    assert repo_source["completion_percent"] == 100
    assert repo_source["all_repo_source_retirement_complete"] is True
    assert repo_source["completion_claim_allowed"] is True
    assert repo_source["live_runtime_evidence_required"] is False
    assert repo_source["item_completion_claim_allowed_when_criteria_satisfied"] is True
    assert repo_source["open_repo_source_gaps"] == []
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
        "missing domain diagnostic apply exactly-one live outcome",
        "missing provider running proof",
        "missing DM002/DM003 fresh paper-line outcome",
    } <= set(repo_source["non_blocking_live_runtime_tails"])
    assert {
        "runtime_surface_retirement audit reports repo_source_retirement_completion.status=complete",
        "runtime_surface_retirement audit reports open_surface_count=0 and open_surface_ids=[] for repo-source retirement",
        "runtime_surface_retirement validator reports violation_count=0",
    } <= set(repo_source["completed_repo_source_retirement_evidence"])
    assert "domain_diagnostic_dry_run_missing" in repo_source["false_repo_source_blockers"]

    assert live_runtime["scope"] == (
        "OPL live readback, domain diagnostic apply exactly-one, provider running proof, "
        "DM002/DM003 live paper-line outcome"
    )
    assert live_runtime["status"] == "partial"
    assert live_runtime["completion_claim_allowed"] is False
    assert live_runtime["blocks_repo_source_retirement"] is False
    assert live_runtime["blocks_final_runtime_paper_acceptance"] is True
    assert live_runtime["live_tail_work_order_refs"] == []
    assert live_runtime["live_tail_evidence_intake_refs"] == []
    assert live_runtime["open_live_runtime_work_order_surface_ids"] == []
    assert live_runtime["live_runtime_gap_work_order_refs"] == []
    assert live_runtime["live_runtime_gap_evidence_intake_refs"] == []
    assert live_runtime["open_live_runtime_gap_work_order_ids"] == []
    assert live_runtime["runtime_evidence_readback_redirect_refs"] == [
        "contracts/runtime/mas-live-runtime-evidence-rollup.json"
    ]
    assert live_runtime["opl_runtime_evidence_readback_ref"] == (
        "opl:runtime-evidence-readback"
    )
    assert live_runtime["mas_live_runtime_evidence_rollup_required_for_completion_claim"] is False
    assert live_runtime["opl_runtime_evidence_readback_required_for_completion_claim"] is True
    assert live_runtime["runtime_evidence_readback_claim_boundary"] == {
        "repo_source_retirement_blocked_by_missing_live_evidence": False,
        "mas_redirect_can_claim_live_runtime_readiness": False,
        "docs_tests_inventory_or_queue_empty_can_satisfy_readback": False,
    }
    assert {
        "same-transition OPL command/event/outbox/StageRun identity readback",
        "domain diagnostic apply exactly-one live outcome when explicitly delegated",
        "provider admission or running proof backed by same-identity OPL runtime readback",
        (
            "fresh DM002/DM003 owner receipt, stable typed blocker, human gate, "
            "route-back evidence, strict running proof, or paper/gate/artifact semantic delta"
        ),
        (
            "live evidence records for same-transition gaps must carry study_id, "
            "work_unit_id, work_unit_fingerprint, route_identity_key, and "
            "attempt_idempotency_key"
        ),
        (
            "live-tail readback evidence for active runtime surfaces must carry "
            "the same current transition identity unless it is no-active-caller/"
            "tombstone/replacement evidence"
        ),
    } <= set(live_runtime["required_evidence"])
    assert {
        "repo_source_retirement_complete",
        "accepted_ref_family_without_current_transition_identity",
        "concrete_evidence_ref_without_current_transition_identity",
        "cross_identity_live_readback_as_same_transition_evidence",
        "receipt_consumption_projection_as_live_acceptance",
        "legacy_next_action_tail_absorbed_as_live_acceptance",
        "repo_control_tail_refs_as_owner_receipt_or_human_gate",
    } <= set(live_runtime["false_live_completion_claims"])
    assert live_runtime["live_runtime_gap_evidence_transition_identity_required"] is True
    assert live_runtime["live_tail_readback_evidence_transition_identity_required"] is True
    assert live_runtime["live_evidence_transition_identity_fields"] == [
        "study_id",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
    ]

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
    assert physical_gate["repo_source_retirement_completion_percent"] == 100
    assert physical_gate["repo_source_retirement_completion_claim_allowed"] is True
    assert physical_gate["live_runtime_readiness_status"] == live_runtime["status"]
    assert physical_gate["live_runtime_evidence_blocks_repo_source_retirement"] is False
    assert physical_gate["repo_source_missing_evidence_tails"] == []
    assert physical_gate["live_runtime_work_order_refs"] == []
    assert physical_gate["live_runtime_gap_work_order_refs"] == []
    assert physical_gate["live_runtime_gap_evidence_intake_refs"] == []
    assert physical_gate["live_tail_evidence_intake_refs"] == []
    assert physical_gate["live_runtime_work_order_surface_ids"] == []
    assert physical_gate["runtime_evidence_readback_redirect_ref"] == (
        "contracts/runtime/mas-live-runtime-evidence-rollup.json"
    )
    assert physical_gate["opl_runtime_evidence_readback_ref"] == (
        "opl:runtime-evidence-readback"
    )
    assert set(physical_gate["missing_evidence_tails"]) == set(
        physical_gate["live_runtime_readiness_missing_evidence_tails"]
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
        "domain_diagnostic_dry_run",
        "domain_diagnostic_observe_only",
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
        "receipt_consumption_projection_as_live_acceptance",
        "legacy_next_action_tail_absorbed_as_live_acceptance",
        "repo_control_tail_refs_as_owner_receipt_or_human_gate",
    } <= set(audit["rejected_completion_claims"])

    non_claims = audit["non_claims"]
    assert non_claims["all_mas_private_surfaces_physically_retired"] is False
    assert non_claims["domain_progress_transition_runtime_live_complete"] is False
    assert non_claims["domain_diagnostic_apply_runtime_ready"] is False
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
        "domain_diagnostic_dry_run",
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

    expected_retained = {
        "stage_outcome_authority",
        "runtime_health_kernel",
        "progress_portal_study_workbench_overview_action_projection",
        "agent_tool_arsenal_scientific_capability_registry",
        "runtime_lifecycle_payload_retention",
        "runtime_storage_maintenance",
    }
    retained = {
        surface_id
        for surface_id, surface in surfaces.items()
        if surface["disposition"] != "physically_retired"
    }

    assert inventory["version"] == "mas-runtime-surface-retirement-inventory.v2"
    assert inventory["schema_ref"] == (
        "contracts/runtime/mas-runtime-surface-retirement.schema.json"
    )
    assert "domain_diagnostic_obligation_actuator" not in surfaces
    assert retained == expected_retained
    assert all(surface["mas_runtime_authority"] is False for surface in surfaces.values())
    assert all(
        surface["replacement_ref"].startswith("opl:")
        for surface in surfaces.values()
    )
    assert all(
        surface["tombstone_ref"]
        for surface in surfaces.values()
        if surface["disposition"] == "physically_retired"
    )
    assert surfaces["domain_authority_refs_index"] == {
        "surface_id": "domain_authority_refs_index",
        "disposition": "physically_retired",
        "replacement_ref": "opl:state-index-kernel",
        "tombstone_ref": (
            "human_doc:mas-private-surface-retirement#domain_authority_refs_index"
        ),
        "retained_mas_role": "none",
        "mas_runtime_authority": False,
    }

    assert physical_gate["repo_source_retirement_status"] == "done"
    assert physical_gate["repo_source_retirement_completion_percent"] == 100
    assert physical_gate["repo_source_missing_evidence_tails"] == []
    assert set(physical_gate["missing_evidence_tails"]) == set(
        physical_gate["live_runtime_readiness_missing_evidence_tails"]
    )
    assert "inventory_entry_updated" in physical_gate["false_completion_boundary"]
    assert "active_caller_exists_as_retention_reason" in physical_gate[
        "false_completion_boundary"
    ]
    assert "read_only_projection_as_execution_authority" in physical_gate[
        "false_completion_boundary"
    ]


def test_transition_runtime_completion_audit_records_provider_admission_repo_consumption_without_live_claim() -> None:
    audit = _audit()
    gates = {gate["gate_id"]: gate for gate in audit["gate_evidence_status"]}
    lane = gates["lane_3_opl_substrate_hardening_live_consumption"]
    required = {item["gate_id"]: item for item in audit["required_before_goal_complete"]}

    assert lane["status"] == "evidence_required"
    assert {
        (
            "src/med_autoscience/controllers/provider_admission/"
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
        (
            "repo:med-autoscience@10d17340d4d374d7eae56b302c09a8ad2ee12b78#"
            "study_progress_receipt_consumption_projection"
        ),
        "repo_control_readback_tail_not_live_acceptance_evidence",
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
        "domain diagnostic apply exactly-one live outcome when explicitly delegated",
        "DM002/DM003 fresh live paper-line outcome per allowed exactly-one family",
    } <= set(lane["missing_evidence_tails"])
    assert "contracts/paper_progress_replay_live_evidence_status.json#/replay_to_live_separation_gate" in (
        lane["observed_refs"]
    )
    assert {
        "provider_admission_same_identity_replay_as_fresh_opl_readback",
        "provider_admission_same_identity_replay_as_live_paper_progress",
        "same_identity_readback_consumes_transition_request_as_paper_line_outcome",
        "receipt_consumption_projection_as_opl_stagerun_live_readback",
        "receipt_consumption_projection_as_owner_receipt_or_human_gate",
    } <= set(lane["false_completion_boundary"])
    provider_gate = required["provider_admission_event_consumption"]
    assert provider_gate["status"] == "open"
    assert "live DM002/DM003" in provider_gate["repo_side_evidence"]
    assert audit["completion_claim_allowed"] is False


def test_transition_runtime_completion_audit_records_fresh_opl_repo_evidence_without_live_claim() -> None:
    audit = _audit()
    gates = {gate["gate_id"]: gate for gate in audit["gate_evidence_status"]}
    opl_gate = gates["lane_2_opl_runtime_repo_readback_shape"]
    opl_ref = "external_repo:one-person-lab@33d2fef294ac9e5d7749cf0918f2e4e56b8accb0"

    assert audit["source_of_truth"]["fresh_opl_repo_ref"] == opl_ref
    assert opl_gate["status"] == "satisfied_with_opl_repo_evidence"
    assert {
        f"{opl_ref}#src/family-runtime-domain-progress-transition-runtime.ts",
        f"{opl_ref}#src/family-runtime-domain-progress-transition-runtime-parts/live-readback.ts",
    } <= set(opl_gate["observed_refs"])
    assert {
        "MAS_same_transition_request_consumes_opl_runtime_live_readback_ref",
        "provider_hosted_stage_attempt_live_readback_for_DM002_DM003_ref",
        "terminal_closeout_side_effect_consumed_by_MAS_owner_answer_ref",
    } <= set(opl_gate["missing_evidence_tails"])
    assert "OPL_repo_tests_as_MAS_live_acceptance" in opl_gate["false_completion_boundary"]
    assert audit["completion_claim_allowed"] is False


def test_blueprint_l0_l7_functional_acceptance_matrix_splits_repo_and_live_scope() -> None:
    audit = _audit()
    matrix = audit["blueprint_l0_l7_functional_acceptance"]
    rows = {row["level"]: row for row in matrix["rows"]}

    assert matrix["surface_kind"] == (
        "mas_opl_progress_runtime_blueprint_l0_l7_functional_acceptance"
    )
    assert matrix["blueprint_ref"] == (
        "docs/runtime/designs/mas_opl_progress_runtime_ideal_blueprint.md"
    )
    assert matrix["goal_slice"] == "repo_source_control_plane_only"
    assert matrix["repo_source_control_plane_completion_status"] == "done"
    assert matrix["repo_source_control_plane_completion_percent"] == 100
    assert matrix["overall_blueprint_completion_status"] == "partial"
    assert matrix["overall_blueprint_completion_claim_allowed"] is False
    assert matrix["live_acceptance_executed"] is False
    assert matrix["live_only_completion_status"] == "deferred_not_run"
    assert matrix["fresh_repo_evidence"]["mas_repo_ref"] == (
        "repo:med-autoscience@37be1f4a88b271fddb78dcd3e43c65535fdaa1ea"
    )
    assert audit["source_of_truth"]["fresh_mas_repo_ref"] == (
        "repo:med-autoscience@37be1f4a88b271fddb78dcd3e43c65535fdaa1ea"
    )
    assert audit["source_of_truth"]["receipt_consumption_main_ref"] == (
        "repo:med-autoscience@10d17340d4d374d7eae56b302c09a8ad2ee12b78"
    )
    assert audit["source_of_truth"]["legacy_next_action_tail_absorption_ref"] == (
        "repo:med-autoscience@37be1f4a88b271fddb78dcd3e43c65535fdaa1ea"
    )
    assert matrix["fresh_repo_evidence"]["receipt_consumption_main_ref"] == (
        "repo:med-autoscience@10d17340d4d374d7eae56b302c09a8ad2ee12b78"
    )
    assert matrix["fresh_repo_evidence"]["legacy_next_action_tail_absorption_ref"] == (
        "repo:med-autoscience@37be1f4a88b271fddb78dcd3e43c65535fdaa1ea"
    )
    assert matrix["fresh_repo_evidence"]["opl_repo_ref"] == (
        "external_repo:one-person-lab@33d2fef294ac9e5d7749cf0918f2e4e56b8accb0"
    )
    assert "current_action_selection/current_work_unit_action producer-retirement worktree" in (
        matrix["fresh_repo_evidence"]["related_worktree_closeout_scope"]
    )

    assert set(rows) == {"L0", "L1", "L2", "L3", "L4", "L5", "L6", "L7"}
    for level, row in rows.items():
        required = row["repo_source_control_plane_required"]
        assert required["status"] == "done", level
        assert required["completion_percent"] == 100, level
        assert required["required"], level
        assert required["evidence_refs"], level
        assert required["remaining_repo_source_gaps"] == [], level
        assert row["live_only_deferred"]["status"] == "deferred_not_run", level
        assert row["live_only_deferred"]["required_evidence"], level
        assert row["live_only_deferred"][
            "blocks_repo_source_control_plane_completion"
        ] is False

    assert matrix["claim_boundary"] == {
        "repo_source_control_plane_complete_can_be_claimed": True,
        "overall_blueprint_complete_can_be_claimed": False,
        "runtime_ready_can_be_claimed": False,
        "paper_line_ready_can_be_claimed": False,
        "live_only_deferred_blocks_repo_source_control_plane": False,
        "tests_or_contracts_can_claim_live_acceptance": False,
        "repo_tail_refs_can_claim_live_acceptance": False,
        "receipt_consumption_or_legacy_tail_can_claim_owner_receipt_or_human_gate": False,
    }
    assert {
        "domain diagnostic apply",
        "provider start",
        "hydrate",
        "tick",
        "redrive",
        "owner-route reconcile",
    } == set(matrix["verification_scope"]["forbidden_live_commands_not_run"])
    assert {
        "Yang runtime/study/paper artifacts",
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
    } == set(matrix["verification_scope"]["forbidden_artifact_writes_not_done"])

    assert "live_only_deferred" in rows["L7"]["classification"]
    assert rows["L7"]["functional_surface"] == (
        "live_paper_line_acceptance_preflight_harness_only"
    )
    assert {
        "fresh DM002 study_progress and accepted outcome evidence",
        "fresh DM003 study_progress and accepted outcome evidence",
        "domain diagnostic apply exactly-one live outcome when explicitly delegated",
    } <= set(rows["L7"]["live_only_deferred"]["required_evidence"])
    assert {
        "OPL outbox and StageRun identity live readback for the same transition request",
        "domain diagnostic apply exactly-one live outcome when explicitly delegated",
        "fresh DM002/DM003 paper-line accepted outcome after provider-admission readback consumption",
    } <= set(matrix["remaining_live_only_deferred"])
    assert audit["completion_claim_allowed"] is False
    assert audit["non_claims"]["domain_progress_transition_runtime_live_complete"] is False
    assert audit["non_claims"]["dm002_dm003_live_paper_progress"] is False
