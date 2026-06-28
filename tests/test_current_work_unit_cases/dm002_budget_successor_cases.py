from __future__ import annotations

from med_autoscience.controllers import control_identity
from med_autoscience.controllers.paper_recovery_state import build_paper_recovery_state

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
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "reason": "paper_progress_delta_observed",
                "work_unit_id": None,
                "eval_id": None,
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": None,
                    "surface_ref": "study_progress.next_forced_delta",
                },
                "owner_action": {
                    "next_owner": None,
                    "work_unit_id": None,
                    "allowed_actions": [],
                    "owner_receipt_required": True,
                },
            },
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
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                "sat.closeout.json#typed_blocker"
            ),
            "latest_owner_answer_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
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


def test_current_work_unit_derives_dm002_anti_loop_successor_from_repair_progress() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::ai-reviewer-current-inputs::"
        "2026-06-20T12:00:39+00:00"
    )
    blocker_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    progress = {
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
                "accepted_owner_receipt": False,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "work_unit_id": "dm002_same_line_publication_paper_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "action_fingerprint": "publication-blockers::497d1260db522f01",
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "gate_replay_refs": [
                    "runtime/quests/002-dm-china-us-mortality-attribution/"
                    "artifacts/reports/publishability_gate/2026-06-20T113829Z.json",
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "publication_supervision",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": blocker_fingerprint,
                "action_fingerprint": blocker_fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "typed_blocker",
                    "typed_blocker": {
                        "blocker_kind": "anti_loop_budget_exhausted",
                        "blocker_id": "anti_loop_budget_exhausted",
                        "blocker_type": (
                            "repeat_suppressed_after_opl_execution_authorization_required"
                        ),
                        "blocked_reason": (
                            "repeat_suppressed_after_opl_execution_authorization_required"
                        ),
                        "reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "required_next_owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": blocker_fingerprint,
                        "action_fingerprint": blocker_fingerprint,
                        "source_eval_id": source_eval_id,
                    },
                },
            },
        }
    recovery = build_paper_recovery_state(progress)
    assert recovery["phase"] == "owner_action_ready"
    assert recovery["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    successor = recovery["next_safe_action"]["successor_owner_action"]
    assert successor["work_unit_id"] == work_unit_id
    assert successor["source_surface"] == "repair_progress_projection.mas_owner_repair_execution_evidence"

    work_unit = module.build_current_work_unit(
        progress={**progress, "paper_recovery_state": recovery},
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "schema_version": 1,
            "blocker_kind": "anti_loop_budget_exhausted",
            "blocker_id": "anti_loop_budget_exhausted",
            "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
            "blocked_reason": "repeat_suppressed_after_opl_execution_authorization_required",
            "reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "required_next_owner": "one-person-lab",
            "required_owner_action": (
                "Consume this typed closeout, provide a fresh owner-authorized route such as "
                "publishability_repair_sprint, single_typed_blocker, or human_or_operator_gate, "
                "then retry only through a current OPL-bound stage attempt."
            ),
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": blocker_fingerprint,
            "action_fingerprint": blocker_fingerprint,
            "source_eval_id": source_eval_id,
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                "sat_67e10efde628859185249aa0.closeout.json"
            ),
            "latest_owner_answer_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                "sat_67e10efde628859185249aa0.closeout.json"
            ),
            "latest_owner_answer_kind": "typed_blocker",
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["action_type"] == "run_gate_clearing_batch"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is False
    assert work_unit["state"]["transition_request_pending"] is True
    assert "typed_blocker" not in work_unit["state"]
    assert work_unit["currentness_basis"]["work_unit_id"] == work_unit_id
    assert work_unit["currentness_basis"]["source_eval_id"] == source_eval_id
    assert work_unit["currentness_basis"]["source"] == (
        "repair_progress_projection.mas_owner_repair_execution_evidence"
    )
    assert work_unit["required_output_contract"]["owner_receipt_required"] is True
    assert work_unit["authority_boundary"]["can_write_paper_or_package"] is False
    assert work_unit["authority_boundary"]["can_write_runtime_owned_surfaces"] is False


def test_current_work_unit_consumes_repeat_suppressed_blocker_after_fresh_repair_receipt() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::ai-reviewer-current-inputs::"
        "2026-06-20T12:00:39+00:00"
    )
    blocker_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    progress = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_stage": "publication_supervision",
        "repair_progress_projection": {
            "surface_kind": "repair_progress_projection",
            "source": "mas_owner_repair_execution_evidence",
            "status": "progress_delta_observed",
            "paper_delta_observed": True,
            "progress_delta_candidate": True,
            "accepted_owner_receipt": True,
            "gate_replay_done": True,
            "ai_reviewer_recheck_done": True,
            "work_unit_id": "dm002_same_line_publication_paper_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "source_eval_id": source_eval_id,
            "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            "repair_execution_evidence_ref": (
                "artifacts/controller/repair_execution_evidence/latest.json"
            ),
            "gate_replay_refs": [
                "artifacts/controller/gate_clearing_batch/latest.json",
                "artifacts/controller/gate_replay_requests/latest.json",
            ],
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "typed_blocker",
            "study_id": study_id,
            "quest_id": study_id,
            "stage_id": "publication_supervision",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": blocker_fingerprint,
            "action_fingerprint": blocker_fingerprint,
            "state": {
                "typed_blocker": {
                    "blocker_kind": "anti_loop_budget_exhausted",
                    "blocker_id": "anti_loop_budget_exhausted",
                    "blocker_type": (
                        "repeat_suppressed_after_opl_execution_authorization_required"
                    ),
                    "blocked_reason": (
                        "repeat_suppressed_after_opl_execution_authorization_required"
                    ),
                    "reason": "anti_loop_budget_exhausted",
                    "owner": "one-person-lab",
                    "required_next_owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": blocker_fingerprint,
                    "action_fingerprint": blocker_fingerprint,
                    "source_eval_id": source_eval_id,
                    "stage_attempt_id": "sat_67e10efde628859185249aa0",
                    "source_ref": (
                        "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                        "sat_67e10efde628859185249aa0.closeout.json"
                    ),
                },
            },
        },
    }

    recovery = build_paper_recovery_state(progress)
    assert recovery["phase"] == "owner_receipt_recorded"
    assert recovery["next_safe_action"]["kind"] == "consume_owner_receipt"
    assert recovery["conditions"][0]["condition"] == (
        "repair_progress_owner_receipt_supersedes_terminal_stop_loss"
    )
    assert recovery["next_safe_action"]["owner_receipt_ref"] == (
        "artifacts/controller/repair_execution_receipts/latest.json"
    )

    work_unit = module.build_current_work_unit(
        progress={**progress, "paper_recovery_state": recovery},
        typed_blocker=progress["current_work_unit"]["state"]["typed_blocker"],
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "owner_receipt_recorded"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["source"] == "paper_recovery_state.owner_receipt_recorded"
    assert work_unit["state"]["owner_receipt_ref"] == (
        "artifacts/controller/repair_execution_receipts/latest.json"
    )
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_uses_gate_followthrough_repair_after_dm002_budget_stop_loss() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    blocked_work_unit_id = "ai_reviewer_record_gate_consumption"
    successor_work_unit_id = "medical_prose_quality_analysis_source_documentation_repair"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "002-dm-china-us-mortality-attribution::ai-reviewer-current-inputs::"
        "2026-06-20T12:00:39+00:00"
    )
    blocked_fingerprint = f"domain-transition::route_back_same_line::{blocked_work_unit_id}"
    successor_fingerprint = "publication-blockers::5a4f2060d6d7d97e"
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "analysis-campaign",
        "work_unit_id": successor_work_unit_id,
        "work_unit_fingerprint": successor_fingerprint,
        "action_fingerprint": successor_fingerprint,
        "source_eval_id": source_eval_id,
        "owner_route_currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": successor_work_unit_id,
            "work_unit_fingerprint": successor_fingerprint,
            "explicit_publication_work_unit_id": blocked_work_unit_id,
            "selected_publication_work_unit_id": blocked_work_unit_id,
        },
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
        "target_surface": {
            "ref_kind": "publication_work_unit",
            "route_target": "analysis-campaign",
            "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "gate_clearing_batch_ref": (
                "/workspace/studies/002-dm-china-us-mortality-attribution/"
                "artifacts/controller/gate_clearing_batch/latest.json"
            ),
            "current_publication_work_unit": {
                "unit_id": successor_work_unit_id,
                "lane": "analysis-campaign",
                "summary": "Materialize current analysis-source documentation repair.",
            },
            "next_work_unit": {
                "unit_id": successor_work_unit_id,
                "lane": "analysis-campaign",
                "summary": "Materialize current analysis-source documentation repair.",
            },
        },
        "acceptance_refs": [
            "/workspace/studies/002-dm-china-us-mortality-attribution/"
            "artifacts/controller/gate_clearing_batch/latest.json"
        ],
    }
    progress = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_stage": "publication_supervision",
        "progress_first_monitoring_summary": {
            "current_executable_owner_action": action,
        },
        "gate_clearing_batch_followthrough": {
            "surface_kind": "gate_clearing_batch_followthrough",
            "status": "executed",
            "gate_replay_status": "blocked",
            "source_eval_id": source_eval_id,
            "work_unit_id": blocked_work_unit_id,
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "latest_record_path": (
                "/workspace/studies/002-dm-china-us-mortality-attribution/"
                "artifacts/controller/gate_clearing_batch/latest.json"
            ),
            "work_unit_currentness": {
                "explicit_publication_work_unit_id": blocked_work_unit_id,
                "selected_publication_work_unit_id": blocked_work_unit_id,
                "current_publication_work_unit_id": "analysis_claim_evidence_repair",
                "current_work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "lacks_specific_blocker_object": False,
                "current_actionability_status": "actionable",
            },
            "current_publication_work_unit": {
                "unit_id": "analysis_claim_evidence_repair",
                "lane": "analysis-campaign",
            },
        },
    }
    typed_blocker = {
        "surface_kind": "mas_domain_typed_blocker",
        "schema_version": 1,
        "blocker_kind": "anti_loop_budget_exhausted",
        "blocker_id": "anti_loop_budget_exhausted",
        "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
        "blocked_reason": "repeat_suppressed_after_opl_execution_authorization_required",
        "reason": "anti_loop_budget_exhausted",
        "owner": "one-person-lab",
        "required_next_owner": "one-person-lab",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": blocked_work_unit_id,
        "work_unit_fingerprint": blocked_fingerprint,
        "action_fingerprint": blocked_fingerprint,
        "source_eval_id": source_eval_id,
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_eval_id": source_eval_id,
            "work_unit_id": blocked_work_unit_id,
            "work_unit_fingerprint": blocked_fingerprint,
        },
    }

    recovery = build_paper_recovery_state(
        {
            **progress,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "typed_blocker",
                "study_id": study_id,
                "quest_id": study_id,
                "stage_id": "publication_supervision",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": blocked_work_unit_id,
                "work_unit_fingerprint": blocked_fingerprint,
                "action_fingerprint": blocked_fingerprint,
                "state": {"typed_blocker": typed_blocker},
            },
        }
    )
    assert recovery["phase"] == "owner_action_ready"
    assert recovery["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert recovery["next_safe_action"]["owner"] == "analysis-campaign"

    work_unit = module.build_current_work_unit(
        progress={**progress, "paper_recovery_state": recovery},
        typed_blocker=typed_blocker,
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "analysis-campaign"
    assert work_unit["action_type"] == "run_quality_repair_batch"
    assert work_unit["work_unit_id"] == successor_work_unit_id
    assert work_unit["work_unit_fingerprint"] == successor_fingerprint
    assert work_unit["state"]["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is False
    assert "typed_blocker" not in work_unit["state"]
    assert work_unit["currentness_basis"]["source_eval_id"] == source_eval_id
    assert work_unit["currentness_basis"]["source"] == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    )


def test_current_work_unit_keeps_dm002_anti_loop_blocker_for_mismatched_repair_eval() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    blocker_eval_id = "publication-eval::dm002::current"
    repair_eval_id = "publication-eval::dm002::different"
    blocker_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    progress = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_stage": "publication_supervision",
        "repair_progress_projection": {
            "surface_kind": "repair_progress_projection",
            "source": "mas_owner_repair_execution_evidence",
            "status": "progress_delta_observed",
            "paper_delta_observed": True,
            "progress_delta_candidate": True,
            "accepted_owner_receipt": True,
            "gate_replay_done": True,
            "ai_reviewer_recheck_done": True,
            "work_unit_id": "dm002_same_line_publication_paper_repair",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "action_fingerprint": "publication-blockers::497d1260db522f01",
            "source_eval_id": repair_eval_id,
            "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
            "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
            "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "typed_blocker",
            "study_id": study_id,
            "quest_id": study_id,
            "stage_id": "publication_supervision",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": blocker_fingerprint,
            "action_fingerprint": blocker_fingerprint,
            "state": {
                "typed_blocker": {
                    "blocker_kind": "anti_loop_budget_exhausted",
                    "blocker_id": "anti_loop_budget_exhausted",
                    "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
                    "blocked_reason": "repeat_suppressed_after_opl_execution_authorization_required",
                    "reason": "anti_loop_budget_exhausted",
                    "owner": "one-person-lab",
                    "required_next_owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": blocker_fingerprint,
                    "action_fingerprint": blocker_fingerprint,
                    "source_eval_id": blocker_eval_id,
                },
            },
        },
    }

    recovery = build_paper_recovery_state(progress)
    assert recovery["phase"] == "domain_blocked"

    work_unit = module.build_current_work_unit(
        progress={**progress, "paper_recovery_state": recovery},
        typed_blocker=progress["current_work_unit"]["state"]["typed_blocker"],
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["work_unit_id"] == work_unit_id


def test_current_work_unit_keeps_dm002_anti_loop_blocker_without_repair_progress_evidence() -> None:
    module = _module()
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    blocker_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_stage": "publication_supervision",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": False,
                "gate_replay_done": True,
                "work_unit_id": "dm002_same_line_publication_paper_repair",
            },
        },
        typed_blocker={
            "blocker_id": "anti_loop_budget_exhausted",
            "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
            "reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": blocker_fingerprint,
            "action_fingerprint": blocker_fingerprint,
        },
        next_owner="one-person-lab",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "one-person-lab"
    assert work_unit["work_unit_id"] == work_unit_id
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == (
        "repeat_suppressed_after_opl_execution_authorization_required"
    )
