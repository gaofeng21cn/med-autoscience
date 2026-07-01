from __future__ import annotations

import importlib


def test_stage_closure_terminalizer_reterminalizes_waiting_opl_closeout_when_terminal_readback_arrives() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    existing_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "outcome": {
            "kind": "typed_blocker",
            "blocker_type": "route_back_checkpoint_without_semantic_delta",
        },
        "opl_closeout": {"status": "waiting_for_opl_runtime_live_readback"},
    }
    assert commands._stage_closure_decision_requires_reterminalize(
        existing_decision
    ) is True

    decision = commands._terminalize_stage_closure_from_readback(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "mission_id": "mission-002",
            "consume_candidate_status": "accepted_submission_milestone_candidate",
            "paper_mission_transaction": {
                "transaction_id": "txn-002",
                "stage_id": "submission_milestone_candidate::followthrough::followthrough-02",
            },
            "stage_terminal_decision": {
                "status": "accepted_submission_milestone_candidate",
            },
            "stage_closure_decision": existing_decision,
            "opl_runtime_carrier_readback": {
                "carrier_status": "opl_runtime_terminal_readback_observed",
                "terminal_closeout": {
                    "status": "completed",
                    "stage_attempt_id": "sat-002-terminal",
                },
            },
        }
    )

    assert decision["opl_closeout"]["status"] == (
        "opl_runtime_terminal_readback_observed"
    )
    assert decision["opl_closeout"]["stage_attempt_id"] == "sat-002-terminal"


def test_stage_closure_terminalizer_keeps_receipt_owner_consumed_typed_blocker() -> None:
    commands = importlib.import_module(
        "med_autoscience.cli_parts.paper_mission_commands"
    )

    receipt_owner_decision = {
        "surface_kind": "mas_stage_closure_decision",
        "authority_materialized": True,
        "counts_as_typed_blocker": True,
        "authority_boundary": {
            "surface_role": "paper_mission_receipt_owner_consumption",
        },
        "outcome": {
            "kind": "typed_blocker",
            "blocker_type": "paper_mission_stage_route_domain_gate_pending",
        },
    }

    assert (
        commands._stage_closure_decision_requires_reterminalize(
            receipt_owner_decision,
            current_package={
                "package_kind": "submission_ready_package",
                "can_submit": True,
                "quality_gate_status": "clear",
                "known_blockers": [],
                "generated_from_current_source": True,
                "root": "/tmp/current_package",
                "zip_exists": True,
                "freshness_status": "current",
            },
        )
        is False
    )
