from __future__ import annotations

import importlib
from pathlib import Path

from med_autoscience.cli.paper_mission_commands import route_back_budget


def test_route_back_budget_counts_synonymous_followthrough_route_back(tmp_path: Path) -> None:
    commands = importlib.import_module(
        "med_autoscience.cli.paper_mission_commands"
    )

    def route_back_readback(*, followthrough: str = "") -> tuple[dict, dict]:
        mission_id = f"mission-001{followthrough}"
        transaction_id = (
            "paper-mission-transaction::study-001::paper-stage::gate::"
            f"mission-001{followthrough}"
        )
        decision = {
            "decision_kind": "route_back",
            "status": "route_back",
            "next_owner": "mission_executor",
            "target_stage_id": "paper-stage::gate",
            "route_back_evidence_ref": (
                "route-back:paper-mission-terminal-owner-gate:study-001:"
                f"sat-terminal{followthrough}"
            ),
        }
        readback = {
            "study_id": "study-001",
            "mission_id": mission_id,
            "candidate_ref": f"candidate{followthrough}.json",
            "paper_mission_transaction": {
                "transaction_id": transaction_id,
                "mission_id": mission_id,
                "study_id": "study-001",
                "stage_id": "paper-stage::gate",
                "stage_terminal_decision": decision,
            },
            "stage_terminal_decision": decision,
            "opl_route_command": {
                "command_kind": "route_back",
                "target": "paper-stage::gate",
                "paper_mission_transaction_ref": transaction_id,
            },
            "next_owner_or_human_decision": {"next_owner": "mission_executor"},
            "terminal_owner_gate": {
                "owner": "mas_authority_kernel",
                "gate_kind": "domain_gate",
                "blocked_reason": "paper_mission_stage_route_domain_gate_pending",
            },
            "terminal_owner_gate_owner_answer_readback": {
                "status": "route_back",
                "owner_answer_shape": "route_back_evidence_ref",
                "route_back_evidence_ref": decision["route_back_evidence_ref"],
                "stage_terminal_decision": decision,
            },
        }
        handoff = {
            "study_id": "study-001",
            "mission_id": mission_id,
            "paper_mission_transaction_ref": transaction_id,
            "candidate_ref": f"candidate{followthrough}.json",
            "next_owner": "mission_executor",
            "route_command_kind": "route_back",
            "route_target": "paper-stage::gate",
        }
        return readback, handoff

    ledger = route_back_budget._empty_paper_mission_route_back_budget_ledger(
        study_id="study-001"
    )
    first_readback, first_handoff = route_back_readback()
    first_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=first_readback,
        handoff=first_handoff,
        route_back_budget_ledger=ledger,
    )
    assert first_guard["route_back_budget"]["next_observed_count"] == 1
    assert first_guard["route_back_budget"]["budget_exhausted"] is False
    assert first_guard["signature_payload"]["semantic_delta_refs"] == {}

    ledger_ref = tmp_path / "route_back_budget_ledger.json"
    ledger = route_back_budget._record_paper_mission_route_back_budget_ledger(
        ledger=ledger,
        ledger_ref=ledger_ref,
        progress_guard=first_guard,
        consume_readback=first_readback,
        handoff=first_handoff,
        trigger="drive-initial",
        source="pytest",
    )

    second_readback, second_handoff = route_back_readback(
        followthrough="::followthrough-02"
    )
    second_guard = commands._paper_mission_semantic_progress_guard(
        consume_readback=second_readback,
        handoff=second_handoff,
        previous_guard=first_guard,
        route_back_budget_ledger=ledger,
    )

    assert second_guard["signature"] == first_guard["signature"]
    assert second_guard["status"] == "non_advancing_route_back"
    assert second_guard["route_back_budget"]["next_observed_count"] == 2
    assert second_guard["route_back_budget"]["budget_exhausted"] is True
    assert second_guard["route_back_budget"]["required_next_owner"] == (
        "mission_executor"
    )
    assert second_guard["route_back_budget"]["next_mode"] == (
        "mas_mission_executor_fallback"
    )
    assert second_guard["can_claim_submission_ready"] is False
    assert second_guard["can_claim_runtime_ready"] is False

    ledger = route_back_budget._record_paper_mission_route_back_budget_ledger(
        ledger=ledger,
        ledger_ref=ledger_ref,
        progress_guard=second_guard,
        consume_readback=second_readback,
        handoff=second_handoff,
        trigger="followthrough-02",
        source="pytest",
    )
    assert ledger_ref.exists()
    assert ledger["signatures"][second_guard["signature"]]["observed_count"] == 2
    assert ledger["latest_budget_status"]["budget_exhausted"] is True
    assert ledger["authority_boundary"]["ledger_is_authority"] is False
