from __future__ import annotations

from med_autoscience.controllers import control_identity

from tests.test_current_work_unit_cases.shared import _assert_contract_shape, _module


def test_current_work_unit_supersedes_terminal_anti_loop_with_safe_next_forced_delta() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    blocker_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
    )
    route_fingerprint = control_identity.stable_route_currentness_fingerprint(
        study_id=study_id,
        source="study_progress.next_forced_delta.owner_action",
        work_unit_id=work_unit_id,
        action_type="run_gate_clearing_batch",
        next_owner="write",
        source_eval_id=source_eval_id,
        target_surface_ref="artifacts/controller/gate_clearing_batch/latest.json",
        required_delta_kind="review_current_paper_delta",
    )

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "paper_progress_delta": {"count": 1},
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "status": "progress_delta_observed",
                "paper_delta_observed": True,
                "progress_delta_candidate": True,
                "accepted_owner_receipt": True,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "action_fingerprint": "publication-blockers::497d1260db522f01",
                "source_eval_id": source_eval_id,
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": work_unit_id,
                "eval_id": source_eval_id,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "write",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "owner_action": {
                    "next_owner": "write",
                    "work_unit_id": work_unit_id,
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
        },
        current_executable_owner_action={
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": "write",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": route_fingerprint,
            "action_fingerprint": route_fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": "run_gate_clearing_batch",
            "allowed_actions": ["run_gate_clearing_batch"],
            "owner_receipt_required": True,
            "required_delta_kind": "review_current_paper_delta",
            "target_surface": {
                "ref_kind": "route_obligation",
                "route_target": "write",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_kind": "anti_loop_budget_exhausted",
            "blocker_id": "anti_loop_budget_exhausted",
            "blocker_type": "anti_loop_budget_exhausted",
            "reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "required_next_owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": blocker_fingerprint,
            "action_fingerprint": blocker_fingerprint,
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat.closeout.json#typed_blocker"
            ),
            "latest_owner_answer_ref": (
                "artifacts/supervision/consumer/default_executor_execution/"
                "sat.closeout.json#typed_blocker"
            ),
            "latest_owner_answer_kind": "typed_blocker",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "write"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["source"] == "study_progress.next_forced_delta.owner_action"
    assert "typed_blocker" not in work_unit["state"]
    assert work_unit["currentness_basis"]["work_unit_id"] == work_unit_id
    assert work_unit["work_unit_fingerprint"] == route_fingerprint
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == route_fingerprint
    assert work_unit["required_output_contract"]["owner_receipt_required"] is True
    assert work_unit["state"]["provider_admission_pending"] is False
    assert work_unit["authority_boundary"]["can_write_paper_or_package"] is False
    assert work_unit["authority_boundary"]["can_write_runtime_owned_surfaces"] is False
