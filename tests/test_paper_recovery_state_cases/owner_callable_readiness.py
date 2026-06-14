from __future__ import annotations

from tests.test_paper_recovery_state_cases.shared import _executable_work_unit, _module


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
