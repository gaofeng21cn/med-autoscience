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


def test_stage_closure_next_legal_action_prefers_successor_action_after_owner_consumed_route_checkpoint() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.mission_summary_parts.stage_closure_projection"
    )

    projection = module.top_level_stage_closure_projection(
        {
            "mas_receipt_consumption": {
                "status": "owner_consumed_route_checkpoint",
                "next_legal_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
            },
            "next_action": {
                "surface_kind": "mas_next_action_envelope",
                "action_family": "paper.write.prose_repair",
                "action_type": "request_opl_stage_attempt",
            },
            "stage_closure_decision": {
                "outcome": {
                    "kind": "next_stage_transition",
                    "transition_kind": "route_back_candidate_checkpoint",
                    "next_action": "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
                },
            },
        }
    )

    assert projection["stage_closure"]["next_legal_action"] == (
        "consume_route_back_checkpoint_or_materialize_terminalizer_outcome"
    )
    assert projection["next_legal_action"] == "request_opl_stage_attempt"
