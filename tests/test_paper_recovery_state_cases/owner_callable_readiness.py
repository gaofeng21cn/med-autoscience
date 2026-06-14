from __future__ import annotations

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
            "blocker_type": "publication_gate_replay_blocked",
        }
    ]
    assert state["current_authority"]["owner"] == "publication_gate"
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert "owner_callable" not in state["next_safe_action"]


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
