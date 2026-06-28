from __future__ import annotations

import json

from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
    _typed_blocker_work_unit,
)


def test_paper_progress_stall_terminal_uses_gate_followthrough_successor_action() -> None:
    fingerprint = "sha256:7ede1907479d87ea1a88c4468749d0e63017d93b7b2d518cdcd9be95d4ee0e96"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": fingerprint,
                "source_eval_id": "publication-eval::003::current-ai-reviewer",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": repair_fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="one-person-lab",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                blocker_type="paper_progress_stall_terminal",
            ) | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "terminal_typed_blocker_successor_evidence",
            "blocker_type": "paper_progress_stall_terminal",
        }
    ]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    successor = state["next_safe_action"]["successor_owner_action"]
    assert successor["owner"] == "write"
    assert successor["action_type"] == "run_quality_repair_batch"
    assert successor["work_unit_id"] == "medical_prose_write_repair"
    assert successor["work_unit_fingerprint"] == repair_fingerprint


def test_gate_followthrough_successor_action_is_not_closed_by_prior_repair_receipt() -> None:
    gate_fingerprint = "sha256:7ede1907479d87ea1a88c4468749d0e63017d93b7b2d518cdcd9be95d4ee0e96"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": "publication-eval::003::current-ai-reviewer",
                "repair_execution_evidence_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "owner_receipt_ref": receipt_ref,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": [
                    "artifacts/controller/gate_clearing_batch/latest.json",
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "gate_replay_status": "blocked",
                "latest_record_path": "artifacts/controller/gate_clearing_batch/latest.json",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": repair_fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
            },
            "current_work_unit": _executable_work_unit(
                owner="write",
                action_type="run_quality_repair_batch",
                work_unit_id="medical_prose_write_repair",
                fingerprint=repair_fingerprint,
            )
            | {
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                }
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "action_fingerprint": repair_fingerprint,
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [{"condition": "current_owner_action_ready"}]
    assert state["next_safe_action"]["kind"] == "materialize_mas_transition_request_or_owner_callable"
    assert state["current_authority"]["obligation"]["work_unit_fingerprint"] == repair_fingerprint
    assert receipt_ref not in state.get("evidence_refs", [])
    assert state["supervisor_decision"]["decision"] == "materialize_recovery_action"


def test_current_ai_reviewer_record_supersedes_stale_record_typed_blocker() -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    source_eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "current-ai-reviewer-record::20260621T002645Z"
    )
    record_ref = (
        "artifacts/publication_eval/ai_reviewer_responses/"
        "20260621T002645Z_publication_eval_record.json"
    )
    stale_blocker = _typed_blocker_work_unit(
        study_id=study_id,
        owner="ai_reviewer",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        blocker_type="ai_reviewer_record_stale_after_current_inputs",
    )
    stale_blocker["work_unit_fingerprint"] = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    stale_blocker["action_fingerprint"] = stale_blocker["work_unit_fingerprint"]
    stale_blocker["state"]["typed_blocker"] |= {
        "reason": "ai_reviewer_record_stale_after_current_inputs",
        "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
        "source_eval_id": "publication-eval::002::stale-record",
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": stale_blocker,
            "ai_reviewer_request_lifecycle": {
                "surface": "ai_reviewer_request_lifecycle",
                "state": "assessment_written",
                "assessment_written": True,
                "owner_output_consumption": {
                    "status": "consumed",
                    "record_ref": record_ref,
                    "eval_id": source_eval_id,
                },
            },
            "publication_eval": {
                "eval_id": source_eval_id,
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "recommended_actions": [
                    {
                        "action_type": "route_back_same_line",
                        "requires_controller_decision": True,
                        "work_unit_fingerprint": (
                            "domain-transition::route_back_same_line::"
                            "ai_reviewer_record_gate_consumption"
                        ),
                        "next_work_unit": {
                            "unit_id": work_unit_id,
                            "lane": "publication_gate",
                        },
                    }
                ],
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "terminal_typed_blocker_successor_evidence",
            "blocker_type": "ai_reviewer_record_stale_after_current_inputs",
        }
    ]
    successor = state["next_safe_action"]["successor_owner_action"]
    assert successor["action_type"] == "run_gate_clearing_batch"
    assert successor["owner"] == "gate_clearing_batch"
    assert successor["work_unit_id"] == work_unit_id
    assert successor["source_ref"] == record_ref
    assert successor["source_eval_id"] == source_eval_id
    assert successor["owner_route_currentness_basis"] == {
        "source": "ai_reviewer_request_lifecycle.owner_output_consumption",
        "source_eval_id": source_eval_id,
        "record_ref": record_ref,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
        ),
        "action_fingerprint": (
            "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
        ),
    }
    assert state["supervisor_decision"]["decision"] == "materialize_recovery_action"


def test_gate_followthrough_successor_supersedes_stale_ai_reviewer_blocker() -> None:
    study_id = "002-dm-china-us-mortality-attribution"
    source_eval_id = "publication-eval::002::current"
    work_unit_id = "medical_prose_quality_analysis_source_documentation_repair"
    fingerprint = "publication-blockers::5a4f2060d6d7d97e"
    stale_blocker = _typed_blocker_work_unit(
        study_id=study_id,
        owner="ai_reviewer",
        action_type="return_to_ai_reviewer_workflow",
        work_unit_id="produce_ai_reviewer_publication_eval_record_against_current_inputs",
        blocker_type="ai_reviewer_record_stale_after_current_inputs",
    )
    stale_blocker["work_unit_fingerprint"] = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    stale_blocker["action_fingerprint"] = stale_blocker["work_unit_fingerprint"]
    stale_blocker["state"]["typed_blocker"] |= {
        "reason": "ai_reviewer_record_stale_after_current_inputs",
        "blocked_reason": "ai_reviewer_record_stale_after_current_inputs",
        "source_eval_id": "publication-eval::002::stale-record",
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": stale_blocker,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "analysis-campaign",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
                "required_delta_kind": "publication_gate_actionable_repair_delta_or_typed_blocker",
                "target_surface": {
                    "ref_kind": "publication_work_unit",
                    "route_target": "analysis-campaign",
                    "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                },
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": source_eval_id,
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "work_unit_currentness": {
                    "explicit_publication_work_unit_id": "ai_reviewer_record_gate_consumption",
                    "current_publication_work_unit_id": work_unit_id,
                    "current_work_unit_fingerprint": fingerprint,
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": work_unit_id,
                    "lane": "analysis-campaign",
                },
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "claim_evidence_consistency_failed",
                    "submission_hardening_incomplete",
                ],
                "latest_record_path": (
                    f"/workspace/studies/{study_id}/artifacts/controller/"
                    "gate_clearing_batch/latest.json"
                ),
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "current_owner_action_supersedes_terminal_typed_blocker",
            "blocker_type": "ai_reviewer_record_stale_after_current_inputs",
        }
    ]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    successor = state["next_safe_action"]["successor_owner_action"]
    assert successor["action_type"] == "run_quality_repair_batch"
    assert successor["owner"] == "analysis-campaign"
    assert successor["work_unit_id"] == work_unit_id
    assert successor["work_unit_fingerprint"] == fingerprint
    assert successor["source_surface"] == "gate_clearing_batch_followthrough.actionable_current_work_unit"


def test_terminal_anti_loop_owner_gate_reads_closeout_ref_before_stale_progress_delta(tmp_path) -> None:
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    study_id = "002-dm-china-us-mortality-attribution"
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/owner_callable_adapter_receipt/sat_67e10efde628859185249aa0.closeout.json"
    )
    closeout_path = tmp_path / closeout_ref
    closeout_path.parent.mkdir(parents=True, exist_ok=True)
    closeout_path.write_text(
        json.dumps(
            {
                "stage_attempt_id": "sat_67e10efde628859185249aa0",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "ai_reviewer_record_gate_consumption",
                "paper_stage_log": {
                    "next_forced_delta": {
                        "required_delta_kind": (
                            "publishability_repair_sprint_or_single_typed_blocker_"
                            "or_human_or_operator_gate"
                        ),
                    },
                },
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    current_work_unit = _typed_blocker_work_unit(
        study_id=study_id,
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
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": f"{closeout_ref}#typed_blocker",
        "typed_blocker_ref": f"{closeout_ref}#typed_blocker",
        "source_ref": f"{closeout_ref}#typed_blocker",
        "closeout_refs": [closeout_ref],
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "study_root": str(tmp_path / "studies" / study_id),
            "workspace_root": str(tmp_path),
            "current_work_unit": current_work_unit,
            "next_forced_delta": {"required_delta_kind": "review_current_paper_delta"},
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
