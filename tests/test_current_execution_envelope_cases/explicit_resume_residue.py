from __future__ import annotations

import importlib


def test_current_work_unit_supersedes_non_human_explicit_resume_residue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "explicit_resume_pending",
                "parked_owner": "user",
                "awaiting_explicit_wakeup": True,
                "runtime_failure_classification": {"requires_human_gate": False},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "await_explicit_resume",
            },
        },
        progress={
            "parked_state": "explicit_resume_pending",
            "parked_owner": "user",
        },
        current_work_unit_payload={
            "status": "executable_owner_action",
            "owner": "ai_reviewer",
            "action_type": "return_to_ai_reviewer_workflow",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
    )

    assert envelope["state_kind"] == "executable_owner_action"
    assert envelope["owner"] == "ai_reviewer"
    assert envelope["next_work_unit"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert envelope["parked_state"] is None
    assert "runtime_health:await_explicit_resume" in envelope["conflict_suppression_refs"]


def test_current_work_unit_typed_blocker_supersedes_explicit_resume_residue() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_execution_envelope")

    envelope = module.build_current_execution_envelope(
        status={
            "auto_runtime_parked": {
                "parked": True,
                "parked_state": "explicit_resume_pending",
                "parked_owner": "user",
                "awaiting_explicit_wakeup": True,
                "runtime_failure_classification": {"requires_human_gate": False},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "await_explicit_resume",
            },
        },
        progress={
            "parked_state": "explicit_resume_pending",
            "parked_owner": "user",
        },
        current_work_unit_payload={
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "state": {
                "state_kind": "typed_blocker",
                "source": "terminal_closeout_typed_blocker",
                "typed_blocker": {
                    "blocker_type": "opl_execution_authorization_required",
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "source_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
                    "typed_blocker_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
                },
            },
        },
    )

    assert envelope["state_kind"] == "typed_blocker"
    assert envelope["owner"] == "one-person-lab"
    assert envelope["parked_state"] is None
    assert envelope["typed_blocker"]["blocker_type"] == "opl_execution_authorization_required"
