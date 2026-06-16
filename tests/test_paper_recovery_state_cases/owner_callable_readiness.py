from __future__ import annotations

import json

from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
    _typed_blocker_work_unit,
)


def test_runtime_retry_exhausted_current_mas_owner_callable_stays_owner_action_ready() -> None:
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                owner="gate_clearing_batch",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                fingerprint=fingerprint,
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "study_truth_snapshot": {
                "allowed_controller_actions": [
                    "record_user_decision",
                    "direct_study_execution",
                    "direct_paper_line_write",
                ],
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                }
            ],
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "retry_budget_remaining": 0,
                "blocking_reasons": ["runtime_recovery_retry_budget_exhausted"],
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "current_mas_owner_callable_ready",
            "reason": "runtime_recovery_retry_budget_exhausted",
        }
    ]
    assert state["next_safe_action"]["kind"] == "run_mas_owner_callable"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["owner_callable"]["callable_surface"] == (
        "gate_clearing_batch.run_gate_clearing_batch"
    )


def test_current_readiness_typed_blocker_with_mas_owner_callable_is_owner_action_ready() -> None:
    fingerprint = "current-readiness-typed-blocker::002-dm-china-us-mortality-attribution::52c1080bfe75a671"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="002-dm-china-us-mortality-attribution",
                owner="MedAutoScience",
                action_type="complete_medical_paper_readiness_surface",
                work_unit_id="complete_medical_paper_readiness_surface",
                blocker_type="medical_paper_readiness_missing",
            )
            | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "complete_medical_paper_readiness_surface",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
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

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "current_mas_owner_callable_ready",
            "reason": "medical_paper_readiness_missing",
        }
    ]
    assert state["current_authority"]["owner"] == "MedAutoScience"
    assert state["next_safe_action"]["kind"] == "run_mas_owner_callable"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["owner_callable"]["callable_surface"] == (
        "medical_paper_readiness.complete_medical_paper_readiness_surface"
    )


def test_publication_gate_typed_blocker_with_registered_callable_is_owner_action_ready() -> None:
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="publication_gate",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                blocker_type="publication_gate_replay_blocked",
            )
            | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
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

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "current_mas_owner_callable_ready",
            "reason": "publication_gate_replay_blocked",
        }
    ]
    assert state["current_authority"]["owner"] == "publication_gate"
    assert state["next_safe_action"]["kind"] == "run_mas_owner_callable"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["owner_callable"]["callable_surface"] == (
        "gate_clearing_batch.run_gate_clearing_batch"
    )


def test_terminal_publication_gate_typed_blocker_does_not_rerun_same_owner_callable() -> None:
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    successor_fingerprint = "publication-blockers::0915410f804b3697"
    current_work_unit = _typed_blocker_work_unit(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        owner="publication_gate",
        action_type="run_gate_clearing_batch",
        work_unit_id="publication_gate_replay",
        blocker_type="publication_gate_replay_blocked",
    ) | {
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "currentness_basis": {
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "stage_attempt_id": "sat_d2b4c700b31294ab17c225d4",
        },
    }
    current_work_unit["state"]["owner_answer_binding"] = {
        "answer_kind": "typed_blocker_ref",
        "typed_blocker_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat_d2b4c700b31294ab17c225d4.closeout.json"
        ),
        "latest_owner_answer_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat_d2b4c700b31294ab17c225d4.closeout.json"
        ),
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": fingerprint,
        "stage_attempt_id": "sat_d2b4c700b31294ab17c225d4",
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": (
            "artifacts/supervision/consumer/default_executor_execution/"
            "sat_d2b4c700b31294ab17c225d4.closeout.json"
        ),
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "work_unit_fingerprint": fingerprint,
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "source_eval_id": "publication-eval::003::current",
                "gate_replay_status": "blocked",
                "gate_replay_blockers": [
                    "medical_publication_surface_blocked",
                    "reviewer_first_concerns_unresolved",
                    "submission_hardening_incomplete",
                ],
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": successor_fingerprint,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "selected_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
                },
                "latest_record_path": (
                    "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
                    "controller/gate_clearing_batch/latest.json"
                ),
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

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "terminal_typed_blocker_successor_evidence",
            "blocker_type": "publication_gate_replay_blocked",
        }
    ]
    assert state["current_authority"]["owner"] == "write"
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": successor_fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": (
            "studies/003-dpcc-primary-care-phenotype-treatment-gap/artifacts/"
            "controller/gate_clearing_batch/latest.json"
        ),
    }
    assert "owner_callable" not in state["next_safe_action"]


def test_successor_owner_action_precedes_stale_observe_only_provider_admission() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                owner="publication_gate",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                fingerprint="sha256:publication-gate-replay-current",
            )
            | {
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                }
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "publication_gate",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": "artifacts/controller/quality_repair_batch/latest.json",
                "gate_replay_done": True,
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/latest.json"],
            },
        },
        diagnostic_report={
            "action_class": "observe_only",
            "will_start_llm": False,
            "codex_dispatch_count": 0,
            "provider_admission_pending_count": 0,
        },
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [{"condition": "current_owner_action_successor_materialization"}]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
    }


def test_current_owner_route_missing_after_repair_progress_materializes_gate_replay_successor() -> None:
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    current_work_unit = _typed_blocker_work_unit(
        study_id="003-dpcc-primary-care-phenotype-treatment-gap",
        owner="one-person-lab",
        action_type="run_gate_clearing_batch",
        work_unit_id="publication_gate_replay",
        blocker_type="current_owner_route_missing",
    ) | {
        "work_unit_fingerprint": gate_fingerprint,
        "action_fingerprint": gate_fingerprint,
        "currentness_basis": {
            "source_eval_id": source_eval_id,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": gate_fingerprint,
            "action_fingerprint": gate_fingerprint,
        },
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "owner": "one-person-lab",
        "blocked_reason": "current_owner_route_missing",
        "work_unit_fingerprint": gate_fingerprint,
        "action_fingerprint": gate_fingerprint,
        "latest_owner_answer_ref": "artifacts/supervision/consumer/default_executor_execution/latest.json",
        "latest_owner_answer_kind": "typed_blocker",
        "owner_answer_shape": "typed_blocker_ref",
        "terminal_closeout_outcome": "blocked:current_owner_route_missing",
    }

    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": current_work_unit,
            "progress_first_monitoring_summary": {
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "source_eval_id": source_eval_id,
                    "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                }
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "source_fingerprint": gate_fingerprint,
                "source_eval_id": source_eval_id,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "owner_receipt_ref": "artifacts/controller/repair_execution_receipts/latest.json",
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
                "gate_replay_refs": ["artifacts/controller/gate_replay_requests/latest.json"],
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "terminal_typed_blocker_successor_evidence",
            "blocker_type": "current_owner_route_missing",
        }
    ]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_gate_clearing_batch",
        "owner": "gate_clearing_batch",
        "work_unit_id": "publication_gate_replay",
        "work_unit_fingerprint": gate_fingerprint,
        "source_surface": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "source_ref": "artifacts/controller/repair_execution_evidence/latest.json",
    }


def test_same_work_unit_quality_repair_owner_receipt_closes_current_callable() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                owner="write",
                action_type="run_quality_repair_batch",
                work_unit_id="medical_prose_write_repair",
                fingerprint=fingerprint,
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "next_work_unit": "medical_prose_write_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "source_eval_id": "publication-eval::003::current",
                "allowed_actions": ["run_quality_repair_batch"],
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": "publication-eval::003::current",
                "owner_receipt_ref": receipt_ref,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "gate_replay_done": True,
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

    assert state["phase"] == "owner_receipt_recorded"
    assert state["conditions"] == [
        {
            "condition": "same_work_unit_owner_receipt_recorded",
            "action_type": "run_quality_repair_batch",
        }
    ]
    assert state["next_safe_action"] == {
        "kind": "consume_owner_receipt",
        "owner": "write",
        "provider_admission_allowed": False,
        "owner_receipt_ref": receipt_ref,
    }
    assert state["evidence_refs"] == [receipt_ref]
    assert state["supervisor_decision"]["decision"] == "stop_with_owner_receipt"
    assert state["supervisor_decision"]["next_safe_action"] == {
        "kind": "consume_owner_receipt",
        "owner_receipt_ref": receipt_ref,
    }
    assert state["supervisor_decision"]["paper_progress_classification"] == (
        "mas_owner_receipt_credit"
    )


def test_routeback_successor_does_not_reclose_consumed_owner_receipt() -> None:
    fingerprint = "publication-blockers::0915410f804b3697"
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                owner="write",
                action_type="run_quality_repair_batch",
                work_unit_id="medical_prose_write_repair",
                fingerprint=fingerprint,
            )
            | {
                "required_output_contract": {
                    "target_surface": {
                        "ref_kind": "publication_work_unit",
                        "route_target": "write",
                        "current_publication_work_unit": {
                            "unit_id": "medical_prose_write_repair",
                            "lane": "write",
                        },
                    }
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "next_work_unit": "medical_prose_write_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "allowed_actions": ["run_quality_repair_batch"],
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "owner_receipt_ref": receipt_ref,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "gate_replay_done": True,
            },
            "gate_clearing_batch_followthrough": {
                "surface_kind": "gate_clearing_batch_followthrough",
                "status": "executed",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "source_eval_id": source_eval_id,
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": fingerprint,
                    "explicit_work_unit_fingerprint": fingerprint,
                    "lacks_specific_blocker_object": False,
                },
                "current_publication_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
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
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["current_authority"]["owner"] == "write"


def test_repair_progress_gate_replay_followup_with_existing_receipt_closes_as_owner_receipt() -> None:
    fingerprint = "publication-gate-replay::current"
    artifact_delta_fingerprint = "sha256:7ede1907479d87ea1a88c4468749d0e63017d93b7b2d518cdcd9be95d4ee0e96"
    repair_receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    gate_replay_ref = "artifacts/controller/gate_clearing_batch/latest.json"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(
                owner="gate_clearing_batch",
                action_type="run_gate_clearing_batch",
                work_unit_id="publication_gate_replay",
                fingerprint=fingerprint,
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_eval_id": "publication-eval::003::current",
                "allowed_actions": ["run_gate_clearing_batch"],
                "repair_progress_precedence": {
                    "paper_delta_observed": True,
                    "accepted_owner_receipt": True,
                    "source_work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "source_fingerprint": artifact_delta_fingerprint,
                },
            },
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "source": "mas_owner_repair_execution_evidence",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "source_fingerprint": artifact_delta_fingerprint,
                "source_eval_id": "publication-eval::003::current",
                "owner_receipt_ref": repair_receipt_ref,
                "repair_execution_evidence_ref": (
                    "artifacts/controller/repair_execution_evidence/latest.json"
                ),
                "gate_replay_refs": [
                    gate_replay_ref,
                    "artifacts/controller/gate_replay_requests/latest.json",
                ],
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
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

    assert state["phase"] == "owner_receipt_recorded"
    assert state["conditions"] == [
        {
            "condition": "repair_progress_followup_owner_receipt_recorded",
            "action_type": "run_gate_clearing_batch",
        }
    ]
    assert state["next_safe_action"] == {
        "kind": "consume_owner_receipt",
        "owner": "gate_clearing_batch",
        "provider_admission_allowed": False,
        "owner_receipt_ref": gate_replay_ref,
    }
    assert state["evidence_refs"] == [gate_replay_ref]
    assert state["supervisor_decision"]["decision"] == "stop_with_owner_receipt"


def test_current_work_unit_owner_receipt_recorded_closes_paper_recovery_state() -> None:
    receipt_ref = "artifacts/controller/gate_clearing_batch/latest.json"
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
                "work_unit_fingerprint": "sha256:gate-replay-current",
                "action_fingerprint": "sha256:gate-replay-current",
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
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "sha256:gate-replay-current",
                },
            },
        }
    )

    assert state["phase"] == "owner_receipt_recorded"
    assert state["conditions"] == [
        {
            "condition": "current_work_unit_owner_receipt_recorded",
            "action_type": "run_gate_clearing_batch",
        }
    ]
    assert state["next_safe_action"] == {
        "kind": "consume_owner_receipt",
        "owner": "gate_clearing_batch",
        "provider_admission_allowed": False,
        "owner_receipt_ref": receipt_ref,
    }
    assert state["evidence_refs"] == [receipt_ref]
    assert state["supervisor_decision"]["decision"] == "stop_with_owner_receipt"


def test_consumed_gate_owner_receipt_materializes_routeback_successor() -> None:
    receipt_ref = "artifacts/controller/gate_clearing_batch/latest.json"
    fingerprint = "publication-blockers::0915410f804b3697"
    source_eval_id = (
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260612T142918Z::sat_433e34b1795d4f3c3fbe1fbb"
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
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "owner": "write",
                "controller_action": "request_opl_stage_attempt",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": "write",
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
    assert state["next_safe_action"] == {
        "kind": "materialize_successor_owner_action",
        "owner": "write",
        "provider_admission_allowed": True,
        "successor_owner_action": {
            "action_type": "run_quality_repair_batch",
            "owner": "write",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "source_ref": receipt_ref,
        },
    }


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
            "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
        ),
        "work_unit_id": "ai_reviewer_record_gate_consumption",
        "work_unit_fingerprint": fingerprint,
        "stage_attempt_id": "sat_67e10efde628859185249aa0",
    }
    current_work_unit["state"]["typed_blocker"] |= {
        "latest_owner_answer_ref": (
            "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
            "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json#typed_blocker"
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
                    "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
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


def test_terminal_anti_loop_owner_gate_reads_closeout_ref_before_stale_progress_delta(tmp_path) -> None:
    fingerprint = "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
    study_id = "002-dm-china-us-mortality-attribution"
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/default_executor_execution/sat_67e10efde628859185249aa0.closeout.json"
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
