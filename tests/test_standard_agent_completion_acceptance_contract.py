from __future__ import annotations

import json
import re
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = REPO_ROOT / "contracts" / "standard_agent_completion_acceptance.json"
LEDGER_PATH = REPO_ROOT / "contracts" / "standard_agent_completion_evidence_status.json"
PINNED_HUMAN_DOC_PATH_PATTERN = re.compile(
    r"\b(?:README(?:\.zh-CN)?\.md|AGENTS\.md|docs/[A-Za-z0-9_./-]+\.md(?:#[A-Za-z0-9_-]+)?|contracts/[A-Za-z0-9_./-]+\.md)\b"
)
MACHINE_TRUTH_HUMAN_DOC_PATH_PATTERN = re.compile(
    r"\b(?:README(?:\.zh-CN)?\.md|AGENTS\.md|docs/[A-Za-z0-9_./-]+\.md(?:#[A-Za-z0-9_-]+)?)\b"
)
ABSOLUTE_LOCAL_PATH_PATTERN = re.compile(r"(?<!workspace:)/Users/[^ \"]+")


def _contract() -> dict[str, object]:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


def _ledger() -> dict[str, object]:
    return json.loads(LEDGER_PATH.read_text(encoding="utf-8"))


def test_standard_agent_completion_acceptance_declares_non_completion_boundary() -> None:
    contract = _contract()

    assert contract["surface_kind"] == "mas_standard_opl_agent_completion_acceptance"
    assert contract["version"] == "standard-opl-agent-completion-acceptance.v1"
    assert contract["state"] == "active_contract"
    assert contract["machine_boundary"].startswith("This contract defines acceptance gates")

    policy = contract["completion_claim_policy"]
    assert policy["definition_landed_status"] == "acceptance_definition_landed"
    assert policy["current_completion_status"] == "evidence_tail_open_not_complete"
    assert policy["definition_landed_can_claim_complete"] is False
    assert policy["classification_zero_can_claim_complete"] is False
    assert policy["docs_updated_can_claim_complete"] is False
    assert policy["contract_tests_green_can_claim_complete"] is False
    assert policy["required_final_claim"] == "all_acceptance_gates_satisfied_with_current_evidence"


def test_standard_agent_completion_acceptance_does_not_pin_human_docs_paths() -> None:
    raw_contract = CONTRACT_PATH.read_text(encoding="utf-8")

    assert PINNED_HUMAN_DOC_PATH_PATTERN.findall(raw_contract) == []
    assert "human_doc:mas_ideal_state_gap_plan" in raw_contract
    assert "human_doc:mas_status" in raw_contract
    assert "human_doc:mas_decisions" in raw_contract


def test_standard_agent_completion_acceptance_covers_both_user_objectives() -> None:
    contract = _contract()
    scope = contract["scope"]

    assert scope["objective_1"]["id"] == "mas_legacy_baggage_eliminated"
    assert "standard OPL Agent" in scope["objective_1"]["goal"]
    assert scope["objective_2"]["id"] == "standard_agent_failure_mode_not_repeated"
    assert "future OPL-standard-agent" in scope["objective_2"]["goal"]
    assert "MAS-specific paper recovery phases" in scope["objective_2"]["non_goal"]


def test_standard_agent_completion_acceptance_gates_require_sources_and_negative_claims() -> None:
    contract = _contract()
    gates = {gate["gate_id"]: gate for gate in contract["acceptance_gates"]}

    assert set(gates) == {
        "single_default_recovery_and_progress_root",
        "physical_source_morphology_standardized",
        "active_caller_migration_and_no_resurrection",
        "stage_route_and_stop_loss_have_single_arbiter",
        "negative_false_completion_tests",
        "live_owner_evidence_for_representative_paper_lines",
        "family_standard_agent_feedback_loop",
    }

    for gate in gates.values():
        assert gate["source_of_truth"], gate["gate_id"]
        assert gate["requires"], gate["gate_id"]
        assert gate["cannot_be_satisfied_by"], gate["gate_id"]

    morphology = gates["physical_source_morphology_standardized"]
    assert "functional_structure_gap_count=0 alone" in morphology["cannot_be_satisfied_by"]
    assert "descriptor ready alone" in morphology["cannot_be_satisfied_by"]
    assert "generated interface ready alone" in morphology["cannot_be_satisfied_by"]

    live = gates["live_owner_evidence_for_representative_paper_lines"]
    assert live["required_status"] == "evidence_required"
    assert "repo tests alone" in live["cannot_be_satisfied_by"]
    assert "contract landed" in live["cannot_be_satisfied_by"]

    family = gates["family_standard_agent_feedback_loop"]
    assert family["required_status"] == "evidence_required"
    assert "copying MAS paper_recovery_state into OPL" in family["cannot_be_satisfied_by"]


def test_standard_agent_completion_acceptance_false_completion_claims_are_explicit() -> None:
    contract = _contract()

    assert {
        "contract_landed",
        "docs_updated",
        "classification_gap_count_zero",
        "functional_structure_gap_count_zero",
        "generated_interface_ready",
        "descriptor_ready",
        "OPL_conformance_passed",
        "queue_empty",
        "provider_completed",
        "workflow_terminal",
        "active_run_id_present",
        "active_run_id_null",
        "DHD_observe_only",
        "verified_refs_only_ledger",
        "App_projection_ready",
        "manual_foreground_edit_without_adoption_refs",
    } <= set(contract["false_completion_claims"])

    assert {
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "stable_typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
        "canonical_changed_surface_adopted_ref",
        "strict_current_identity_provider_running_proof",
        "OPL_generated_surface_production_consumption_ref",
        "no_active_caller_scan_ref",
        "physical_retirement_owner_decision_ref",
        "no_forbidden_write_proof_ref",
        "cross_agent_standard_conformance_negative_test_ref",
    } <= set(contract["allowed_completion_evidence"])

    assert {
        "representative DM002/DM003 governed recovery evidence",
        "OPL/OMA family-level standard-agent generation negative conformance",
    } <= set(contract["current_open_evidence_tails"])


def test_standard_agent_completion_evidence_ledger_covers_every_acceptance_gate() -> None:
    contract = _contract()
    ledger = _ledger()

    assert ledger["surface_kind"] == "mas_standard_agent_completion_evidence_status"
    assert ledger["contract_ref"] == "contracts/standard_agent_completion_acceptance.json"
    assert ledger["state"] == "active_evidence_ledger"
    assert ledger["overall_status"] == "evidence_tail_open_not_complete"
    assert ledger["completion_claim_allowed"] is False

    contract_gate_ids = {gate["gate_id"] for gate in contract["acceptance_gates"]}
    ledger_gate_ids = {gate["gate_id"] for gate in ledger["gate_evidence_status"]}
    assert ledger_gate_ids == contract_gate_ids

    allowed_statuses = {
        "satisfied_with_repo_evidence",
        "evidence_required",
        "blocked_by_live_owner_evidence",
    }
    for gate in ledger["gate_evidence_status"]:
        assert gate["status"] in allowed_statuses, gate["gate_id"]
        assert gate["required_evidence_refs"], gate["gate_id"]
        assert "observed_refs" in gate, gate["gate_id"]
        assert "missing_evidence_tails" in gate, gate["gate_id"]
        assert gate["false_completion_boundary"], gate["gate_id"]


def test_standard_agent_completion_evidence_ledger_keeps_live_tails_open() -> None:
    ledger = _ledger()
    gates = {gate["gate_id"]: gate for gate in ledger["gate_evidence_status"]}

    live = gates["live_owner_evidence_for_representative_paper_lines"]
    assert live["status"] == "blocked_by_live_owner_evidence"
    assert live["observed_refs"] == []
    assert {
        "fresh_DM002_DM003_owner_receipt_or_stable_typed_blocker_ref",
        "fresh_human_gate_or_route_back_evidence_ref",
        "provider_long_soak_same_current_identity_proof_ref",
    } <= set(live["missing_evidence_tails"])
    assert {
        "repo_tests",
        "contract_landed",
        "docs_updated",
        "provider_completed_without_mas_closeout_consumption",
    } <= set(live["false_completion_boundary"])

    family = gates["family_standard_agent_feedback_loop"]
    assert family["status"] == "evidence_required"
    assert "OPL_OMA_family_negative_conformance_receipt_ref" in family[
        "missing_evidence_tails"
    ]
    assert "cross_agent_standard_conformance_negative_test_ref" in family[
        "required_evidence_refs"
    ]

    observations = {
        observation["study_id"]: observation
        for observation in ledger["latest_read_only_gap_observations"]
    }
    assert observations["002-dm-china-us-mortality-attribution"][
        "progress_first_outcome"
    ] == "blocked_with_typed_owner"
    assert observations["003-dpcc-primary-care-phenotype-treatment-gap"][
        "progress_first_outcome"
    ] == "ready_for_owner_action"
    for observation in observations.values():
        assert observation["completion_evidence"] is False
        assert observation["can_close_live_owner_gate"] is False


def test_standard_agent_completion_evidence_ledger_rejects_docs_as_machine_truth_refs() -> None:
    ledger = _ledger()

    for gate in ledger["gate_evidence_status"]:
        machine_refs = gate["required_evidence_refs"] + gate["observed_refs"]
        for ref in machine_refs:
            assert not MACHINE_TRUTH_HUMAN_DOC_PATH_PATTERN.search(ref), (
                gate["gate_id"],
                ref,
            )
            assert not ABSOLUTE_LOCAL_PATH_PATTERN.search(ref), (
                gate["gate_id"],
                ref,
            )


def test_standard_agent_completion_evidence_ledger_keeps_false_claims_rejected() -> None:
    contract = _contract()
    ledger = _ledger()

    assert set(contract["false_completion_claims"]) <= set(
        ledger["rejected_completion_claims"]
    )
    assert ledger["completion_claim_policy"]["required_final_claim"] == (
        "all_acceptance_gates_satisfied_with_current_evidence"
    )
    assert ledger["completion_claim_policy"]["current_completion_status"] == (
        "evidence_tail_open_not_complete"
    )
    assert ledger["completion_claim_policy"]["completion_requires_all_gate_statuses"] == [
        "satisfied",
        "retired_with_owner_decision",
        "not_applicable_with_owner_decision",
    ]
