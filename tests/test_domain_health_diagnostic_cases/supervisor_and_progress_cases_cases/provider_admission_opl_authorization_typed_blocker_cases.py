from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith("__")
})


def test_provider_admission_candidate_accepts_current_opl_authorization_typed_blocker() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "ai_reviewer_record_gate_consumption"
    action_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"
    dispatch_path = (
        f"/workspace/studies/{study_id}/artifacts/supervision/consumer/"
        "default_executor_dispatches/run_gate_clearing_batch.json"
    )

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "owner_route_basis": "terminal_closeout_owner_answer_dispatch",
                    "next_executable_owner": "gate_clearing_batch",
                    "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
                    "dispatch_path": dispatch_path,
                    "dispatch_authority": "consumer_default_executor_dispatch",
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                            "owner_route_currentness_basis": {
                                "work_unit_id": work_unit_id,
                                "work_unit_fingerprint": action_fingerprint,
                            },
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "input_refs": [
                    f"/workspace/studies/{study_id}/artifacts/controller_decisions/latest.json",
                    f"/workspace/studies/{study_id}/artifacts/publication_eval/latest.json",
                ],
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "blocked",
                        "blocker_id": "blocked",
                        "blocked_reason": "blocked",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                        "terminal_closeout_outcome": (
                            "blocked:{'blocker_id': 'opl_execution_authorization_required', "
                            "'owner': 'one-person-lab'}"
                        ),
                    },
                },
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "blocked",
                    "blocker_id": "blocked",
                    "blocked_reason": "blocked",
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                    "terminal_closeout_outcome": (
                        "blocked:{'blocker_id': 'opl_execution_authorization_required', "
                        "'owner': 'one-person-lab'}"
                    ),
                },
            },
        },
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["study_id"] == study_id
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint
    assert candidate["blocked_reason"] == "opl_execution_authorization_required"


def test_provider_admission_candidate_rejects_non_authorization_current_work_unit_typed_blocker() -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    action_fingerprint = f"domain-transition::route_back_same_line::{work_unit_id}"

    result = provider_admission.provider_admission_candidates_from_execution_payload(
        {
            "executions": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "execution_status": "blocked",
                    "blocked_reason": "opl_execution_authorization_required",
                    "typed_blocker": {"blocker_id": "opl_execution_authorization_required"},
                    "provider_attempt_or_lease_required": True,
                    "owner_route_current": True,
                    "next_executable_owner": "gate_clearing_batch",
                    "dispatch_path": "/workspace/current-gate-clearing.json",
                    "action_fingerprint": action_fingerprint,
                    "owner_route": {
                        "next_owner": "gate_clearing_batch",
                        "work_unit_fingerprint": action_fingerprint,
                        "source_refs": {
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                }
            ]
        },
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "status": "typed_blocker",
                "study_id": study_id,
                "owner": "one-person-lab",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "anti_loop_budget_exhausted",
                        "blocker_id": "anti_loop_budget_exhausted",
                        "blocked_reason": "anti_loop_budget_exhausted",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": work_unit_id,
                    },
                },
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-current",
                },
            },
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "one-person-lab",
                "typed_blocker": {
                    "blocker_type": "anti_loop_budget_exhausted",
                    "blocker_id": "anti_loop_budget_exhausted",
                    "blocked_reason": "anti_loop_budget_exhausted",
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": work_unit_id,
                },
            },
        },
    )

    assert result == []
