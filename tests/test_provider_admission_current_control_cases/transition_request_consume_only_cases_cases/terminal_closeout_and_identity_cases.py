from __future__ import annotations

import importlib

from tests.test_provider_admission_current_control_cases.transition_request_consume_only_cases import (
    _opl_transition_readback,
    _provider_candidate,
)

def test_provider_admission_current_control_consumes_terminal_closeout_currentness_for_same_request(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    idempotency_key = "paper-policy-request:1a379264039c75d0e9cfd8f5"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "status": "transition_request_pending",
        "source": "opl_current_control_state.study_current_executable_owner_action",
        "mas_owner_action_source": "paper_recovery_state.accepted_owner_gate_decision",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "idempotency_key": idempotency_key,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_attempt_or_lease_required": False,
        "opl_domain_progress_transition_request": {
            "surface_kind": "mas_domain_progress_transition_request",
            "idempotency_key": idempotency_key,
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
        },
    }
    scanned_study = {
        "study_id": study_id,
        "quest_id": study_id,
        "handoff_scan_status": "scanned",
        "quest_status": "active",
        "running_provider_attempt": False,
        "action_queue": [],
        "transition_request_pending_count": 0,
        "provider_admission_pending_count": 0,
        "transition_request_candidates": [],
        "provider_admission_candidates": [],
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
            "stage_attempt_id": "sat_91d23a554175ea9288d903ad",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "route_identity_key": idempotency_key,
            "attempt_idempotency_key": idempotency_key,
            "idempotency_key": idempotency_key,
        },
        "opl_current_control_state_handoff": {
            "surface": "opl_current_control_state_handoff",
            "transition_request_pending_count": 0,
            "provider_admission_pending_count": 0,
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
                "stage_attempt_id": "sat_91d23a554175ea9288d903ad",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "route_identity_key": idempotency_key,
                "attempt_idempotency_key": idempotency_key,
                "idempotency_key": idempotency_key,
            },
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "typed_blocker",
            "owner": "one-person-lab",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "action_fingerprint": action_fingerprint,
            "state": {
                "state_kind": "typed_blocker",
                "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                "source": "provider_admission_terminal_closeout_consumed",
            },
        },
        "current_execution_envelope": {
            "state_kind": "typed_blocker",
            "owner": "one-person-lab",
            "next_work_unit": None,
            "source": "provider_admission_terminal_closeout_consumed",
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-20T11:45:00+00:00",
        apply=False,
        scanned_studies=[scanned_study],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 0
    assert result["transition_request_candidates"] == []
    assert result["action_queue"] == []
    assert result["stage_route_arbiter"]["decision_counts"] == {}
    study = next(item for item in result["studies"] if item["study_id"] == study_id)
    assert study["provider_admission_pending_count"] == 0
    assert study["transition_request_pending_count"] == 0
    assert study["provider_admission_terminal_closeout_consumed"]["stage_attempt_id"] == (
        "sat_91d23a554175ea9288d903ad"
    )


def test_provider_admission_current_control_rejects_mismatched_opl_readback_identity(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    action_fingerprint = "paper-policy-request:current"
    stale_fingerprint = "paper-policy-request:stale"
    candidate = _provider_candidate(
        profile,
        study_id,
        action_fingerprint=action_fingerprint,
    )
    candidate["opl_domain_progress_transition_live_readback"] = _opl_transition_readback(
        study_id,
        action_fingerprint=stale_fingerprint,
        work_unit_id=work_unit_id,
    )

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-17T20:50:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "ai_reviewer",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert len(result["transition_request_candidates"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["evidence"]["blocked_reason"] == "opl_transition_readback_required"
    assert decision["evidence"]["candidate_has_opl_transition_readback"] is True
    assert decision["evidence"]["candidate_has_provider_bound_opl_transition_readback"] is False
    action = result["action_queue"][0]
    assert action["status"] == "transition_request_pending"
    assert action["provider_admission_pending"] is False
    assert action["provider_admission_requires_opl_runtime_result"] is True
    assert "opl_domain_progress_transition_live_readback" not in action


def test_provider_admission_current_control_keeps_same_tick_materialized_recovery_request_consume_only(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.provider_admission.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    action_fingerprint = "publication-blockers::0915410f804b3697"
    candidate = {
        **_provider_candidate(profile, study_id, action_fingerprint=action_fingerprint),
        "source": "same_tick_materialized_dispatch",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "next_executable_owner": "write",
        "required_output_surface": "artifacts/controller/repair_execution_evidence/latest.json",
        "same_tick_materialized_provider_admission": True,
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-16T00:25:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned",
                "quest_status": "active",
                "running_provider_attempt": False,
                "action_queue": [],
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                    "action_fingerprint": action_fingerprint,
                },
                "paper_recovery_state": {
                    "surface_kind": "paper_recovery_state",
                    "phase": "owner_action_ready",
                    "current_authority": {
                        "owner": "write",
                        "obligation": {
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "write",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": work_unit_id,
                            "work_unit_fingerprint": action_fingerprint,
                        },
                    },
                    "conditions": [
                        {
                            "condition": "current_mas_owner_callable_ready",
                            "reason": "runtime_recovery_retry_budget_exhausted",
                        }
                    ],
                    "next_safe_action": {
                        "kind": "run_mas_owner_callable",
                        "owner": "write",
                        "provider_admission_allowed": False,
                    },
                    "supervisor_decision": {
                        "surface_kind": "paper_autonomy_supervisor_decision",
                        "decision": "materialize_recovery_action",
                        "next_owner": "write",
                        "next_safe_action": {
                            "kind": "materialize_recovery_work_unit_or_receipt",
                            "recovery_kind": "mas_control_plane_repair",
                            "source_next_safe_action": {
                                "kind": "run_mas_owner_callable",
                                "owner": "write",
                                "provider_admission_allowed": False,
                            },
                        },
                        "forbidden_interpretations": [
                            "provider_admission_pending_count=0",
                            "observe_only",
                        ],
                    },
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert len(result["transition_request_candidates"]) == 1
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "opl_transition_readback_required": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "opl_transition_readback_required"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["evidence_status"] == "NonAdvancingApply"
    assert decision["no_progress_signal"] == "transition_request_waits_for_opl_runtime"
    assert decision["anti_loop_classification"] == "non_advancing_apply_required"
    assert result["action_queue"][0]["action_type"] == "run_quality_repair_batch"
    assert result["action_queue"][0]["work_unit_id"] == work_unit_id
    assert result["action_queue"][0]["provider_admission_pending"] is False
    assert result["action_queue"][0]["provider_attempt_or_lease_required"] is False
    assert result["action_queue"][0]["provider_admission_requires_opl_runtime_result"] is True
