from __future__ import annotations

import json

from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
    _typed_blocker_work_unit,
)


def test_consumed_gate_owner_receipt_materializes_actionable_gate_followthrough_successor() -> None:
    receipt_ref = "/workspace/studies/003/artifacts/controller/gate_clearing_batch/latest.json"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260615T222436Z::sat_eb686259d7e6346195aba801"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "owner_receipt_recorded",
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "stage_id": "publication_supervision",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "required_output_contract": {
                    "owner_receipt_consumed": True,
                    "owner_receipt_ref": receipt_ref,
                    "provider_completion_is_domain_completion": False,
                    "domain_ready_authorized": False,
                },
                "acceptance_refs": [receipt_ref],
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "source": "paper_recovery_state.owner_receipt_recorded",
                    "owner_receipt_ref": receipt_ref,
                    "next_safe_action_kind": "consume_owner_receipt",
                    "provider_admission_pending": False,
                },
                "currentness_basis": {
                    "source_eval_id": source_eval_id,
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "ai_reviewer_medical_prose_quality_review",
                    "lane": "review",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": "ai_reviewer_medical_prose_quality_review",
                    "work_unit_fingerprint": (
                        "domain-transition::ai_reviewer_re_eval::"
                        "ai_reviewer_medical_prose_quality_review"
                    ),
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "latest_record_path": receipt_ref,
                "source_eval_id": source_eval_id,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
                    "explicit_work_unit_fingerprint": fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "consumed_owner_receipt_routeback_successor",
            "source_condition": "current_work_unit_owner_receipt_recorded",
        }
    ]
    assert state["current_authority"]["owner"] == "write"
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": receipt_ref,
    }


def test_owner_receipt_recorded_materializes_dm002_review_successor_from_domain_transition() -> None:
    receipt_ref = (
        "/workspace/studies/002-dm-china-us-mortality-attribution/artifacts/controller/"
        "gate_clearing_batch/latest.json"
    )
    fingerprint = "publication-blockers::497d1260db522f01"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "owner_receipt_recorded",
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "stage_id": "publication_supervision",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "required_output_contract": {
                    "owner_receipt_consumed": True,
                    "owner_receipt_ref": receipt_ref,
                    "provider_completion_is_domain_completion": False,
                    "domain_ready_authorized": False,
                },
                "acceptance_refs": [receipt_ref],
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "owner_receipt_ref": receipt_ref,
                    "next_safe_action_kind": "consume_owner_receipt",
                },
            },
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "lane": "review",
                    "summary": "Continue the current MAS controller-authorized domain route.",
                },
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "consumed_owner_receipt_domain_transition_successor",
            "source_condition": "current_work_unit_owner_receipt_recorded",
        }
    ]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "return_to_ai_reviewer_workflow",
        "owner": "ai_reviewer",
        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        "work_unit_fingerprint": (
            "domain-transition::ai_reviewer_re_eval::"
            "produce_ai_reviewer_publication_eval_record_against_current_inputs"
        ),
        "domain_transition_decision_type": "ai_reviewer_re_eval",
        "domain_transition_controller_action": "return_to_ai_reviewer_workflow",
        "source_surface": "domain_transition",
        "source_ref": receipt_ref,
    }


def test_owner_receipt_recorded_materializes_dm003_route_back_successor_from_domain_transition() -> None:
    receipt_ref = (
        "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/controller/"
        "repair_execution_receipts/latest.json"
    )
    fingerprint = "publication-blockers::0915410f804b3697"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "owner_receipt_recorded",
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "stage_id": "publication_supervision",
                "owner": "one-person-lab",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "required_output_contract": {
                    "owner_receipt_consumed": True,
                    "owner_receipt_ref": receipt_ref,
                    "provider_completion_is_domain_completion": False,
                    "domain_ready_authorized": False,
                },
                "acceptance_refs": [receipt_ref],
                "state": {
                    "state_kind": "owner_receipt_recorded",
                    "owner_receipt_ref": receipt_ref,
                    "next_safe_action_kind": "consume_owner_receipt",
                },
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                    "summary": "Continue the current MAS controller-authorized domain route.",
                },
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "consumed_owner_receipt_domain_transition_successor",
            "source_condition": "current_work_unit_owner_receipt_recorded",
        }
    ]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "request_opl_stage_attempt",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "domain-transition::route_back_same_line::medical_prose_write_repair",
        "domain_transition_decision_type": "route_back_same_line",
        "domain_transition_controller_action": "request_opl_stage_attempt",
        "source_surface": "domain_transition",
        "source_ref": receipt_ref,
    }


def test_terminal_anti_loop_typed_blocker_does_not_rerun_same_owner_callable() -> None:
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    current_work_unit = _typed_blocker_work_unit(
        study_id="002-dm-china-us-mortality-attribution",
        owner="one-person-lab",
        action_type="run_gate_clearing_batch",
        work_unit_id="ai_reviewer_record_gate_consumption",
        blocker_type="anti_loop_budget_exhausted",
    ) | {
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": "ai_reviewer_record_gate_consumption",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_attempt_id": "sat_67e10efde628859185249aa0",
        },
    }
    current_work_unit["state"]["owner_answer_binding"] = {
        "answer_kind": "typed_blocker_ref",
        "typed_blocker_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "work_unit_id": "ai_reviewer_record_gate_consumption",
        "work_unit_fingerprint": fingerprint,
        "stage_attempt_id": "sat_67e10efde628859185249aa0",
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": current_work_unit,
            "terminal_closeout_precedence_evidence": {
                "stage_attempt_id": "sat_67e10efde628859185249aa0",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_fingerprint": fingerprint,
                "source_path": (
                    "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                    "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json"
                ),
                "paper_stage_log": {
                    "progress_delta_classification": "typed_blocker",
                    "remaining_blockers": ["anti_loop_budget_exhausted"],
                    "next_forced_delta": {
                        "required_delta": (
                            "publishability_repair_sprint_or_single_typed_blocker_"
                            "or_human_or_operator_gate"
                        ),
                    },
                },
            },
            "study_truth_snapshot": {
                "allowed_controller_actions": [
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
            },
        }
    )

    assert state["phase"] == "domain_blocked"
    assert state["conditions"] == [
        {
            "condition": "current_work_unit_typed_blocker",
            "blocker_type": "anti_loop_budget_exhausted",
        }
    ]
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert "owner_callable" not in state["next_safe_action"]


def test_terminal_anti_loop_uses_safe_next_forced_delta_successor_after_paper_delta() -> None:
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
    )
    current_work_unit = _typed_blocker_work_unit(
        study_id=study_id,
        owner="one-person-lab",
        action_type="run_gate_clearing_batch",
        work_unit_id=work_unit_id,
        blocker_type="anti_loop_budget_exhausted",
    ) | {
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_attempt_id": "sat_67e10efde628859185249aa0",
        },
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
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
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "terminal_typed_blocker_successor_evidence",
            "blocker_type": "anti_loop_budget_exhausted",
        }
    ]
    assert state["current_authority"]["owner"] == "write"
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    successor = state["next_safe_action"]["successor_owner_action"]
    assert successor["owner"] == "write"
    assert successor["action_type"] == "run_gate_clearing_batch"
    assert successor["work_unit_id"] == work_unit_id
    assert successor["source_surface"] == "study_progress.next_forced_delta.owner_action"
    assert successor["work_unit_fingerprint"].startswith(f"route-currentness::{study_id}::")


def test_consumed_anti_loop_closeout_yields_repair_owner_receipt_before_domain_blocked() -> None:
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
    )
    current_work_unit = _typed_blocker_work_unit(
        study_id=study_id,
        owner="one-person-lab",
        action_type="run_gate_clearing_batch",
        work_unit_id=work_unit_id,
        blocker_type="anti_loop_budget_exhausted",
    ) | {
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_attempt_id": "sat_67e10efde628859185249aa0",
        },
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
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
                "work_unit_id": "dm002_same_line_publication_paper_repair",
                "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
                "action_fingerprint": "publication-blockers::497d1260db522f01",
                "source_eval_id": source_eval_id,
                "owner_receipt_ref": receipt_ref,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
            "opl_current_control_state_handoff": {
                "provider_admission_terminal_closeout_consumed": {
                    "surface_kind": "provider_admission_terminal_closeout_consumed",
                    "status": "blocked",
                    "stage_attempt_id": "sat_67e10efde628859185249aa0",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "blocker_type": "anti_loop_budget_exhausted",
                    "typed_blocker_ref": (
                        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
                        "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
                    ),
                    "typed_blocker": {
                        "blocker_type": "anti_loop_budget_exhausted",
                        "blocked_reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                    },
                }
            },
            "opl_paper_autonomy_supervisor_decision_readback": {
                "opl_supervisor_decision_engine_readback_consumed": True,
                "status": "consumed",
            },
        }
    )

    assert state["phase"] == "owner_receipt_recorded"
    assert state["conditions"] == [
        {
            "condition": "repair_progress_owner_receipt_supersedes_terminal_stop_loss",
            "action_type": "run_gate_clearing_batch",
        }
    ]
    assert state["next_safe_action"]["kind"] == "consume_owner_receipt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["owner_receipt_ref"] == receipt_ref
    assert state["evidence_refs"] == [receipt_ref]


def test_terminal_anti_loop_does_not_rematerialize_consumed_gate_replay_successor() -> None:
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "stage-attempt-sat_a9b2ffcc8f97a24837d729bf::2026-06-11T12:41:21+00:00"
    )
    current_work_unit = _typed_blocker_work_unit(
        study_id=study_id,
        owner="one-person-lab",
        action_type="run_gate_clearing_batch",
        work_unit_id=work_unit_id,
        blocker_type="anti_loop_budget_exhausted",
    ) | {
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_attempt_id": "sat_67e10efde628859185249aa0",
        },
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
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
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": "route-currentness::002::consumed",
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "claim_evidence_consistency_failed",
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        }
    )

    assert state["phase"] == "domain_blocked"
    assert state["conditions"] == [
        {
            "condition": "current_work_unit_typed_blocker",
            "blocker_type": "anti_loop_budget_exhausted",
        }
    ]
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_same_work_unit_repair_receipt_supersedes_no_selected_dispatch_owner_gate() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    current_work_unit = _typed_blocker_work_unit(
        study_id=study_id,
        owner="one-person-lab",
        action_type="run_quality_repair_batch",
        work_unit_id="medical_prose_write_repair",
        blocker_type="no_selected_dispatch_for_authorized_stage_packet",
    ) | {
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
        },
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "typed_blocker_ref": (
            "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
            "sat_08da46bea43329723d2fbbea.closeout.json"
        ),
        "stage_packet_ref": (
            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/supervision/"
            "consumer/owner_callable_adapters/immutable/run_quality_repair_batch/"
            "33abc53e0c18295f5fa03738.json"
        ),
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": current_work_unit,
            "study_intervention_events": [
                {
                    "surface": "study_intervention_event",
                    "intent": "owner_gate_decision",
                    "payload": {
                        "decision": "admit_identity_bound_stage_packet",
                        "current_owner_identity": {
                            "study_id": study_id,
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": fingerprint,
                            "blocker_type": "stage_packet_not_current_selected_dispatch",
                        },
                        "owner_gate_decision_ref": "owner-gate-decision:dm003-stage-packet",
                        "provider_admission_allowed": True,
                    },
                }
            ],
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "status": "progress_delta_observed",
                "paper_delta_observed": True,
                "progress_delta_candidate": True,
                "accepted_owner_receipt": True,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": "publication-eval::003::current",
                "owner_receipt_ref": receipt_ref,
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "gate_replay_refs": ["artifacts/controller/gate_clearing_batch/latest.json"],
            },
        }
    )

    assert state["phase"] == "owner_receipt_recorded"
    assert state["conditions"] == [
        {
            "condition": "same_work_unit_owner_receipt_recorded",
            "action_type": "run_quality_repair_batch",
        }
    ]
    assert state["next_safe_action"]["kind"] == "consume_owner_receipt"
    assert state["next_safe_action"]["owner_receipt_ref"] == receipt_ref
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [receipt_ref]
