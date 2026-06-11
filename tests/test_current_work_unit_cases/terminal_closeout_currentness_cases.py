from __future__ import annotations

from tests.test_current_work_unit import _assert_contract_shape, _module


def test_current_work_unit_suppresses_gate_replay_receipt_consumed_owner_action() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_3961f4c4b2e9335879a17891"
    )
    current_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "consumption_status": "receipt_consumed",
                    "receipt_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    "receipt_kind": "gate_clearing_batch",
                    "execution_status": "executed",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": (
                        "domain-transition::route_back_same_line::"
                        "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                    ),
                    "canonical_work_unit_identity": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
                        ),
                        "source_eval_id": source_eval_id,
                    },
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": current_fingerprint,
            "action_fingerprint": current_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "blocked_current_work_unit"
    assert work_unit["action_type"] is None
    assert work_unit["work_unit_id"] is None
    assert work_unit["state"]["blocker_type"] == "current_work_unit_unresolved"


def test_current_work_unit_treats_repeat_suppressed_gate_replay_terminal_stage_as_typed_blocker() -> None:
    module = _module()
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260611T003412Z::sat_3961f4c4b2e9335879a17891"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        f"{work_unit_id}::{source_eval_id}"
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_monitoring_summary": {
                "latest_terminal_stage": {
                    "stage_id": "domain_owner/default-executor-dispatch",
                    "action_type": "run_gate_clearing_batch",
                    "status": "repeat_suppressed",
                    "stage_name": work_unit_id,
                    "outcome": "repeat_suppressed",
                    "progress_delta_classification": "typed_blocker",
                    "source_path": (
                        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
                        "artifacts/supervision/consumer/default_executor_execution/latest.json"
                    ),
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["blocker_type"] == "anti_loop_budget_exhausted"
    assert work_unit["state"]["stale_queue_or_handoff_can_override"] is False

