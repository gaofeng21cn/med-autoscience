from __future__ import annotations

from tests.test_paper_recovery_state_cases.shared import _executable_work_unit, _module


def test_running_attempt_accepts_current_work_unit_provider_attempt_proof() -> None:
    fingerprint = "sha256:c69e0d2890655ebc1e7a774e9a83dfe333cbc855bf85c3b2cdaf021289e8fc32"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "running_provider_attempt",
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                },
                "state": {
                    "state_kind": "running_provider_attempt",
                    "provider_attempt_proof": {
                        "running_provider_attempt": True,
                        "active_run_id": "opl-stage-attempt://sat-current",
                        "active_stage_attempt_id": "sat-current",
                        "active_workflow_id": "wf-current",
                        "runtime_health": {
                            "health_status": "running",
                            "runtime_liveness_status": "live",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                        },
                    },
                    "strict_running_proof": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "one-person-lab",
                "next_work_unit": "publication_gate_replay",
            },
        }
    )

    assert state["phase"] == "attempt_running"
    assert state["conditions"] == [{"condition": "running_attempt_identity_bound"}]
    assert state["next_safe_action"]["kind"] == "watch_running_attempt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_running_attempt_requires_strong_identity_binding() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-unbound",
                "active_stage_attempt_id": "sat-unbound",
                "active_workflow_id": "wf-unbound",
            },
        }
    )

    assert state["phase"] == "projection_inconsistent"
    assert state["conditions"][0]["condition"] == "running_attempt_missing_obligation_identity"
    assert state["next_safe_action"]["provider_admission_allowed"] is False


def test_running_attempt_accepts_matching_recovery_obligation_identity() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "active_run_id": "opl-stage-attempt://sat-current",
                "active_stage_attempt_id": "sat-current",
                "active_workflow_id": "wf-current",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "recovery_obligation_id": (
                    "paper-recovery::003-dpcc-primary-care-phenotype-treatment-gap::"
                    "run_quality_repair_batch::medical_prose_write_repair::"
                    "publication-blockers::0915410f804b3697"
                ),
            },
        }
    )

    assert state["phase"] == "attempt_running"
    assert state["next_safe_action"]["kind"] == "watch_running_attempt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
