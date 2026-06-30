from __future__ import annotations

import importlib


def test_stage_closure_next_legal_action_prefers_submission_authority_owner_gate_readback() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary_parts.stage_closure_projection"
    )

    projection = module.top_level_stage_closure_projection(
        {
            "submission_authority_owner_gate_readback": {
                "next_legal_action": "await_submission_authority_or_human_gate_closeout",
            },
            "mas_receipt_consumption": {
                "next_legal_action": "record_typed_blocker",
            },
            "stage_closure_decision": {
                "outcome": {
                    "kind": "typed_blocker",
                    "next_action": "resolve_typed_blocker_or_route_redesign",
                },
            },
        }
    )

    assert projection["next_legal_action"] == (
        "await_submission_authority_or_human_gate_closeout"
    )
    assert projection["stage_closure"]["next_legal_action"] == (
        "resolve_typed_blocker_or_route_redesign"
    )
