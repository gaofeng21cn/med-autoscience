from __future__ import annotations

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_projects_gate_action_over_matching_currentness_blocker_from_live_handoff() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::stage-attempt-sat_current::2026-06-11T11:30:58+00:00"
    )
    fingerprint = (
        "current-ai-reviewer-gate-replay::002-dm-china-us-mortality-attribution::"
        f"{work_unit_id}::{source_eval_id}"
    )
    current_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "study_progress.next_forced_delta.owner_action",
        "next_owner": "write",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "source_eval_id": source_eval_id,
        "action_type": "run_gate_clearing_batch",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "review_current_paper_delta",
    }
    blocker = {
        "blocker_id": "gate_clearing_batch_source_eval_currentness_mismatch",
        "blocker_type": "gate_clearing_batch_source_eval_currentness_mismatch",
        "owner": "gate_clearing_batch",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "currentness_basis": {
            "source": "study_progress.next_forced_delta.owner_action",
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        actions=[
            {
                "action_type": "run_gate_clearing_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": work_unit_id,
                "work_unit_id": work_unit_id,
                "allowed_actions": ["run_gate_clearing_batch"],
                "source_surface": "study_progress.next_forced_delta.owner_action",
            }
        ],
        current_executable_owner_action=current_action,
        live_provider_attempt={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat_live_without_identity",
            "active_stage_attempt_id": "sat_live_without_identity",
            "active_workflow_id": "wf_live_without_identity",
            "blocked_reason": "gate_clearing_batch_source_eval_currentness_mismatch",
            "next_owner": "gate_clearing_batch",
            "typed_blocker": blocker,
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
        typed_blocker=blocker,
        blocked_reason="gate_clearing_batch_source_eval_currentness_mismatch",
        next_owner="gate_clearing_batch",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == fingerprint
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]
