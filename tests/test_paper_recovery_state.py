from __future__ import annotations

import importlib

from med_autoscience.controllers.paper_autonomy_supervisor import build_supervisor_decision
from tests.provider_admission_current_control_helpers import (
    opl_transition_readback,
)
from tests.test_paper_recovery_state_cases.shared import (
    _executable_work_unit,
    _module,
    _typed_blocker_work_unit,
)


def _opl_transition_request(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    transition_kind: str = "StartProviderAttempt",
) -> dict[str, object]:
    return {
        "surface_kind": "mas_domain_progress_transition_request",
        "target_runtime_kind": "DomainProgressTransitionRuntime",
        "target_runtime_owner": "one-person-lab",
        "request_owner": "med-autoscience",
        "authority_role": "domain_policy_request_only",
        "mas_can_create_opl_outbox_record": False,
        "runtime_kind": "DomainProgressTransitionRuntime",
        "recommended_transition_kind": transition_kind,
        "aggregate_identity": {
            "aggregate_kind": "study_work_unit",
            "aggregate_id": f"{study_id}::{work_unit_id}",
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
        },
        "idempotency_key": f"paper-policy-request::{study_id}::{work_unit_id}::{fingerprint}",
        "source_generation": fingerprint,
        "expected_version": fingerprint,
        "required_postcondition": {
            "kind": "provider_admission_enqueued_or_blocked",
            "outcome_owner": "one-person-lab",
            "domain_state_owner": "med-autoscience",
        },
    }


def _opl_transition_result(
    *,
    study_id: str = "003-dpcc-primary-care-phenotype-treatment-gap",
    work_unit_id: str = "medical_prose_write_repair",
    fingerprint: str = "publication-blockers::0915410f804b3697",
    stage_run_id: str = "stage-run-003-medical-prose",
) -> dict[str, object]:
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    return opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=f"paper-policy-request::{study_id}::{work_unit_id}::{fingerprint}",
        stage_run_id=stage_run_id,
    )


def _assert_readback_required_supervisor_projection(state: dict[str, object]) -> None:
    decision = state["supervisor_decision"]
    assert isinstance(decision, dict)
    assert decision["surface_kind"] == "paper_progress_policy_result_projection"
    assert decision["decision"] == "opl_supervisor_decision_readback_required"
    assert decision["decision_authority"] is False
    assert decision["read_model_can_build_supervisor_decision"] is False
    assert decision["requires_opl_supervisor_decision_engine_readback"] is True
    assert decision["mas_can_run_supervisor_decision_engine"] is False
    assert decision["mas_can_store_recovery_obligation"] is False
    assert decision["mas_can_authorize_provider_admission"] is False
    assert decision["provider_admission_pending"] is False
    assert decision["missing_evidence_refs"] == [
        "explicit_paper_autonomy_supervisor_decision_projection",
        "opl_supervisor_decision_engine_readback",
    ]
    assert "paper_autonomy_obligation" not in decision


def test_typed_blocker_owns_recovery_even_when_residual_action_exists() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_work_unit": _typed_blocker_work_unit(),
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "next_owner": "analysis-campaign",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "analysis_claim_evidence_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"action_type": "run_quality_repair_batch"}],
        }
    )

    assert state["surface_kind"] == "paper_recovery_state"
    _assert_readback_required_supervisor_projection(state)
    assert state["phase"] == "domain_blocked"
    assert state["recovery_obligation_id"] == (
        "paper-recovery::002-dm-cvd-mortality-risk::run_gate_clearing_batch::"
        "publication_gate_replay::stage_packet_not_current_selected_dispatch"
    )
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert "suppressed_surfaces" not in state


def test_paper_recovery_state_consumes_explicit_policy_projection_without_rebuilding() -> None:
    payload = {
        "study_id": "002-dm-cvd-mortality-risk",
        "current_work_unit": _typed_blocker_work_unit(),
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "next_owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
        },
    }
    policy_projection = build_supervisor_decision(payload)

    state = _module().build_paper_recovery_state(
        payload | {"paper_progress_policy_result_projection": policy_projection}
    )

    assert state["phase"] == "domain_blocked"
    assert state["supervisor_decision"] == policy_projection
    assert state["supervisor_decision"]["decision"] == "stop_with_stable_typed_blocker"
    assert state["supervisor_decision"]["decision_authority"] is False
    assert state["supervisor_decision"]["mas_can_run_supervisor_decision_engine"] is False


def test_current_ai_reviewer_gate_replay_action_supersedes_stale_ai_reviewer_blocker() -> None:
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    eval_id = (
        "publication-eval::002-dm-china-us-mortality-attribution::"
        "current-ai-reviewer-record::sha256-a05623df"
    )

    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "typed_blocker",
                "study_id": "002-dm-china-us-mortality-attribution",
                "quest_id": "002-dm-china-us-mortality-attribution",
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "ai_reviewer_record_stale_after_current_inputs",
                        "owner": "ai_reviewer",
                        "action_type": "return_to_ai_reviewer_workflow",
                        "work_unit_id": (
                            "produce_ai_reviewer_publication_eval_record_against_current_inputs"
                        ),
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                    },
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "finalize",
                "owner": "finalize",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_receipt_required": True,
                "required_delta_kind": "publication_eval_gate_replay_delta_or_typed_blocker",
                "publication_eval_id": eval_id,
                "owner_route_currentness_basis": {
                    "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                    "source_eval_id": eval_id,
                    "work_unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "target_surface": {
                    "ref_kind": "publication_eval_recommended_action",
                    "route_target": "finalize",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    "next_work_unit": {
                        "unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
                        "lane": "finalize",
                    },
                },
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
    assert state["next_safe_action"]["successor_owner_action"]["action_type"] == "run_gate_clearing_batch"
    assert state["current_authority"]["owner"] == "finalize"


def test_paper_recovery_state_consumes_opl_supervisor_decision_readback() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    obligation_id = (
        f"paper-recovery::{study_id}::run_quality_repair_batch::{work_unit_id}::{fingerprint}"
    )

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "current_work_unit": _executable_work_unit(
                study_id=study_id,
                owner="one-person-lab",
                fingerprint=fingerprint,
            ),
            "opl_paper_autonomy_supervisor_decision_readback": {
                "surface_kind": "opl_paper_autonomy_supervisor_decision_readback",
                "obligation_id": obligation_id,
                "decision_id": f"{obligation_id}|execute_current_owner_delta|stage-run-dm003",
                "decision_kind": "execute_current_owner_delta",
                "status": "decision_ready_for_identity_bound_transition",
                "domain_truth_owner": "med-autoscience",
                "substrate_owner": "one-person-lab",
                "current_identity": {
                    "stage_run_id": "stage-run-dm003",
                    "route_identity_key": "provider-admission::dm003::medical-prose",
                    "attempt_idempotency_key": "provider-admission::dm003::medical-prose",
                    "selected_dispatch_ref": "dispatch-ref:dm003",
                    "stage_packet_ref": "stage-packet:dm003",
                    "stage_packet_refs": ["stage-packet:dm003"],
                    "provider_attempt_ref": "provider-attempt:dm003",
                    "attempt_lease_ref": "lease:dm003",
                    "workflow_ref": "workflow:dm003",
                    "source_fingerprint": "source:dm003",
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                    "work_unit_fingerprint": fingerprint,
                },
                "transition_ref": "transition:dm003",
                "provider_admission_identity_ref": "provider-admission:dm003",
                "current_owner_delta_ref": "owner-delta:dm003",
                "evidence_refs": ["provider-admission:dm003", "stage-run-dm003"],
                "authority_boundary": {
                    "read_model_can_execute": False,
                    "observability_can_close_owner_answer": False,
                    "opl_can_write_mas_truth": False,
                    "opl_can_create_domain_owner_receipt": False,
                    "opl_can_create_domain_typed_blocker": False,
                    "provider_completion_is_domain_ready": False,
                },
            },
        }
    )

    decision = state["supervisor_decision"]
    assert decision["decision"] == "execute_current_owner_delta"
    assert decision["decision_authority"] is False
    assert decision["opl_supervisor_decision_engine_readback_consumed"] is True
    assert decision["requires_opl_supervisor_decision_engine_readback"] is False
    assert decision["mas_can_run_supervisor_decision_engine"] is False
    assert decision["mas_can_store_recovery_obligation"] is False
    assert state["phase"] == "owner_action_ready"
    assert state["next_safe_action"]["provider_admission_allowed"] is True


def test_terminal_selector_residue_yields_successor_over_stale_progress_first_owner_receipt() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="003-dpcc-primary-care-phenotype-treatment-gap",
                owner="one-person-lab",
                action_type="run_quality_repair_batch",
                work_unit_id="medical_prose_write_repair",
                blocker_type="no_selected_dispatch_for_authorized_stage_packet",
            )
            | {
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "state": {
                    "state_kind": "typed_blocker",
                    "source": "terminal_closeout_typed_blocker",
                    "typed_blocker": {
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "latest_owner_answer_kind": "typed_blocker",
                        "latest_owner_answer_ref": "studies/003/artifacts/supervision/consumer/owner_callable_adapter_receipt/sat.closeout.json",
                    },
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "owner_receipt_required": True,
                "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
                "paper_recovery_successor": {
                    "phase": "owner_action_ready",
                    "source_next_safe_action_kind": "materialize_successor_owner_action",
                },
            },
            "progress_first_monitoring_summary": {
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "action_fingerprint": "publication-blockers::0915410f804b3697",
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                        "owner_receipt_ref": "studies/003/artifacts/controller/repair_execution_receipts/latest.json",
                    },
                }
            },
            "gate_clearing_batch_followthrough": {
                "gate_replay_status": "blocked",
                "latest_record_path": "studies/003/artifacts/controller/gate_clearing_batch/latest.json",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": "medical_prose_write_repair",
                    "current_work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                },
                "current_publication_work_unit": {"unit_id": "medical_prose_write_repair", "lane": "write"},
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["conditions"] == [
        {
            "condition": "current_owner_action_supersedes_typed_blocker",
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        }
    ]
    assert state["next_safe_action"]["kind"] == "materialize_successor_owner_action"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert state["next_safe_action"]["successor_owner_action"] == {
        "action_type": "run_quality_repair_batch",
        "owner": "write",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
        "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
    }
    _assert_readback_required_supervisor_projection(state)


def test_opl_consumed_terminal_closeout_blocks_same_identity_successor_revival() -> None:
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    closeout_ref = (
        f"studies/{study_id}/artifacts/supervision/consumer/"
        "owner_callable_adapter_receipt/sat_08da46bea43329723d2fbbea.closeout.json"
    )

    state = _module().build_paper_recovery_state(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": _typed_blocker_work_unit(
                study_id=study_id,
                owner="one-person-lab",
                action_type="run_quality_repair_batch",
                work_unit_id=work_unit_id,
                blocker_type="no_selected_dispatch_for_authorized_stage_packet",
            )
            | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "source_surface": "gate_clearing_batch_followthrough.actionable_current_work_unit",
                "next_owner": "write",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_receipt_required": True,
                "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
                "paper_recovery_successor": {
                    "phase": "owner_action_ready",
                    "source_next_safe_action_kind": "materialize_successor_owner_action",
                },
            },
            "gate_clearing_batch_followthrough": {
                "gate_replay_status": "blocked",
                "latest_record_path": f"studies/{study_id}/artifacts/controller/gate_clearing_batch/latest.json",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "work_unit_currentness": {
                    "current_actionability_status": "actionable",
                    "lacks_specific_blocker_object": False,
                    "current_publication_work_unit_id": work_unit_id,
                    "current_work_unit_fingerprint": fingerprint,
                },
                "current_publication_work_unit": {"unit_id": work_unit_id, "lane": "write"},
            },
            "opl_current_control_state_handoff": {
                "provider_admission_terminal_closeout_consumed": {
                    "surface_kind": "provider_admission_terminal_closeout_consumed",
                    "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
                    "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "typed_blocker_ref": closeout_ref,
                    "typed_blocker": {
                        "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
                        "blocked_reason": "no_selected_dispatch_for_authorized_stage_packet",
                        "owner": "one-person-lab",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "latest_owner_answer_kind": "typed_blocker",
                        "latest_owner_answer_ref": f"{closeout_ref}#typed_blocker",
                    },
                    "latest_terminal_stage_log": {
                        "status": "blocked",
                        "stage_attempt_id": "sat_08da46bea43329723d2fbbea",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "typed_blocker_ref": closeout_ref,
                        "paper_stage_log": {
                            "outcome": "typed_blocker",
                            "progress_delta_classification": "typed_blocker",
                            "remaining_blockers": [
                                "no_selected_dispatch_for_authorized_stage_packet",
                            ],
                            "next_forced_delta": {
                                "required_delta_kind": "typed_blocker_consumption_or_owner_route_selector_reconcile",
                                "work_unit_id": work_unit_id,
                                "owner_action": {
                                    "next_owner": "one-person-lab",
                                    "action_type": "run_quality_repair_batch",
                                    "work_unit_id": work_unit_id,
                                },
                            },
                        },
                    },
                }
            },
        }
    )

    assert state["phase"] == "domain_blocked"
    assert state["conditions"] == [
        {
            "condition": "accepted_closeout_typed_blocker",
            "blocker_type": "no_selected_dispatch_for_authorized_stage_packet",
        }
    ]
    assert state["current_authority"]["owner"] == "one-person-lab"
    assert state["next_safe_action"]["kind"] == "resolve_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [closeout_ref]


def test_matching_owner_gate_event_supersedes_current_typed_blocker() -> None:
    fingerprint = "publication-blockers::497d1260db522f01"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-china-us-mortality-attribution",
            "current_work_unit": _typed_blocker_work_unit(
                study_id="002-dm-china-us-mortality-attribution",
                action_type="run_quality_repair_batch",
                work_unit_id="analysis_claim_evidence_repair",
                blocker_type="stage_packet_not_current_selected_dispatch",
            )
            | {
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "study_intervention_events": [
                {
                    "surface": "study_intervention_event",
                    "intent": "owner_gate_decision",
                    "event_id": "intervention-event-000001-13263a6ca77a1066",
                    "recorded_at": "2026-06-14T02:27:19+00:00",
                    "payload": {
                        "decision": "route_back_to_mas_packet_materialization_bug",
                        "current_owner_identity": {
                            "study_id": "002-dm-china-us-mortality-attribution",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "analysis_claim_evidence_repair",
                            "work_unit_fingerprint": fingerprint,
                            "blocker_type": "stage_packet_not_current_selected_dispatch",
                        },
                        "human_gate_ref": "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
                        "owner_gate_decision_ref": "owner-gate-decision:c7027de42ca336cfe0782428",
                        "route_back_evidence_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
                        "provider_admission_allowed": False,
                    },
                }
            ],
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"action_type": "run_quality_repair_batch"}],
        }
    )

    assert state["phase"] == "owner_action_ready"
    _assert_readback_required_supervisor_projection(state)
    assert state["conditions"] == [
        {
            "condition": "accepted_owner_gate_decision",
            "decision": "route_back_to_mas_packet_materialization_bug",
        }
    ]
    assert state["current_authority"]["owner"] == "MedAutoScience"
    assert state["next_safe_action"]["kind"] == "route_back_to_owner_or_repair_materialization"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["next_safe_action"]["accepted_owner_gate_decision"] == {
        "decision": "route_back_to_mas_packet_materialization_bug",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "analysis_claim_evidence_repair",
        "work_unit_fingerprint": fingerprint,
        "human_gate_ref": "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
        "owner_gate_decision_ref": "owner-gate-decision:c7027de42ca336cfe0782428",
        "route_back_evidence_ref": "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
    }
    assert state["evidence_refs"] == [
        "human_gate:owner-gate-decision:c7027de42ca336cfe0782428",
        "route_back:owner-gate-decision:c7027de42ca336cfe0782428",
        "owner-gate-decision:c7027de42ca336cfe0782428",
    ]


def test_successor_owner_gate_blocker_supersedes_prior_owner_receipt() -> None:
    successor_fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "progress_first_monitoring_summary": {
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": "studies/003/artifacts/controller/gate_clearing_batch/latest.json",
                    },
                }
            },
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "provider_admission_allowed": False,
                    "successor_owner_action": {
                        "action_type": "request_opl_stage_attempt",
                        "owner": "write",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": successor_fingerprint,
                    },
                },
            },
            "study_intervention_events": [
                {
                    "surface": "study_intervention_event",
                    "intent": "owner_gate_decision",
                    "event_id": "intervention-event-000002-cd6e1991896a2d4d",
                    "payload": {
                        "decision": "deny_and_stable_typed_blocker",
                        "provider_admission_allowed": False,
                        "human_gate_ref": "human_gate:owner-gate-decision:d6d895635654560a85573c04",
                        "owner_gate_decision_ref": "owner-gate-decision:d6d895635654560a85573c04",
                        "stable_typed_blocker_ref": (
                            "stable_typed_blocker:owner-gate-decision:"
                            "d6d895635654560a85573c04"
                        ),
                        "current_owner_identity": {
                            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                            "action_type": "request_opl_stage_attempt",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": successor_fingerprint,
                            "blocker_type": "runtime_recovery_retry_budget_exhausted",
                        },
                    },
                }
            ],
        }
    )

    assert state["phase"] == "domain_blocked"
    assert state["conditions"] == [
        {
            "condition": "accepted_owner_gate_decision",
            "decision": "deny_and_stable_typed_blocker",
        }
    ]
    assert state["next_safe_action"]["kind"] == "honor_stable_typed_blocker"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [
        "human_gate:owner-gate-decision:d6d895635654560a85573c04",
        "owner-gate-decision:d6d895635654560a85573c04",
        "stable_typed_blocker:owner-gate-decision:d6d895635654560a85573c04",
    ]



def test_paper_recovery_state_supersedes_stale_operator_parked_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "auto_runtime_parked": {
                "parked": False,
                "superseded_by_current_owner_action": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
            },
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "auto_runtime_parked",
            "current_blockers": [],
            "next_system_action": "Wait for explicit resume.",
            "paper_recovery_state": state,
            "auto_runtime_parked": {
                "surface_kind": "auto_runtime_parked",
                "parked": True,
                "parked_state": "explicit_resume_pending",
                "parked_owner": "user",
                "resource_release_expected": True,
                "awaiting_explicit_wakeup": True,
                "auto_execution_complete": False,
                "summary": "Waiting for explicit resume.",
            },
            "parked_state": "explicit_resume_pending",
            "parked_owner": "user",
            "resource_release_expected": True,
            "awaiting_explicit_wakeup": True,
            "auto_execution_complete": False,
            "needs_user_decision": True,
            "user_decision_summary": "Resume the parked runtime.",
            "intervention_lane": {
                "lane_id": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
                "awaiting_explicit_wakeup": True,
            },
            "operator_status_card": {
                "handling_state": "explicit_resume_pending",
                "current_focus": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
                "awaiting_explicit_wakeup": True,
            },
            "operator_verdict": {
                "decision_mode": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
            },
            "recovery_contract": {
                "action_mode": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
            },
            "autonomy_contract": {
                "autonomy_state": "auto_runtime_parked",
                "summary": "Waiting for explicit resume.",
                "parked_state": "explicit_resume_pending",
            },
            "user_visible_projection": {
                "next_step": "Wait for explicit resume.",
                "why_not_progressing": "explicit_resume_pending",
            },
        }
    )

    assert result["current_stage"] == "publication_supervision"
    assert result["current_blockers"] == ["projection_inconsistent"]
    assert result["auto_runtime_parked"]["parked"] is False
    assert result["auto_runtime_parked"]["superseded_by_paper_recovery_state"] is True
    assert result["parked_state"] is None
    assert result["parked_owner"] is None
    assert result["awaiting_explicit_wakeup"] is False
    assert result["needs_user_decision"] is False
    assert result["intervention_lane"]["lane_id"] == "paper_recovery_projection_inconsistent"
    assert "parked_state" not in result["intervention_lane"]
    assert result["operator_status_card"]["handling_state"] == (
        "paper_recovery_projection_inconsistent"
    )
    assert "parked_state" not in result["operator_status_card"]
    assert result["operator_verdict"]["decision_mode"] == "paper_recovery_state"
    assert result["recovery_contract"]["action_mode"] == "repair_projection_before_admission"
    assert result["autonomy_contract"]["autonomy_state"] == (
        "paper_recovery_projection_inconsistent"
    )
    assert result["user_visible_projection"]["why_not_progressing"] == "projection_inconsistent"


def test_paper_recovery_admission_blocked_suppresses_active_provider_admission_projection() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "opl_domain_progress_transition_request": _opl_transition_request(),
                }
            ],
            "runtime_health_snapshot": {
                "canonical_runtime_action": "external_supervisor_required",
                "retry_budget_remaining": 0,
            },
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "queued",
            "current_blockers": [],
            "next_system_action": "admit_provider_attempt",
            "paper_recovery_state": state,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [
                {
                    "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "opl_domain_progress_transition_request": _opl_transition_request(),
                }
            ],
            "owner_action_admission": {
                "admission_pending": True,
                "provider_attempt_start_requested": True,
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                    "pending_provider_admission_evidence": {
                        "provider_admission_pending_count": 1,
                    },
                    "opl_domain_progress_transition_request": _opl_transition_request(),
                },
            },
            "user_visible_projection": {
                "next_step": "admit_provider_attempt",
                "why_not_progressing": "admission_pending",
            },
        }
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["paper_recovery_provider_admission_blocked_count"] == 1
    assert len(result["blocked_provider_admission_candidates"]) == 1
    assert result["owner_action_admission"]["admission_pending"] is False
    assert result["owner_action_admission"]["provider_attempt_start_requested"] is False
    assert result["current_work_unit"]["state"]["provider_admission_pending"] is False
    assert "pending_provider_admission_evidence" not in result["current_work_unit"]["state"]
    assert result["user_visible_projection"]["why_not_progressing"] == "admission_blocked"


def test_paper_recovery_human_gate_keeps_user_decision_signal() -> None:
    visibility = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.paper_recovery_visibility"
    )
    state = _module().build_paper_recovery_state(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_work_unit": _typed_blocker_work_unit(
                owner="user",
                blocker_type="human_confirmation_required",
            ),
        }
    )

    result = visibility.apply_paper_recovery_state_user_visible_status(
        {
            "study_id": "002-dm-cvd-mortality-risk",
            "current_blockers": [],
            "paper_recovery_state": state,
            "needs_user_decision": False,
            "needs_physician_decision": False,
            "operator_status_card": {},
        }
    )

    assert result["current_blockers"] == []
    assert result["needs_user_decision"] is True
    assert result["needs_physician_decision"] is True
    assert result["user_decision_summary"] == (
        "Resolve the current typed blocker through its owner before starting another provider attempt."
    )
    assert result["intervention_lane"]["lane_id"] == "paper_recovery_human_gate"
    assert result["operator_verdict"]["needs_intervention"] is True


def test_terminal_closeout_matching_obligation_waits_for_owner_consumption() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "terminal_closeout_precedence_evidence": {
                "status": "completed",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "stage_attempt_id": "sat-complete",
                "closeout_ref": "artifacts/supervision/consumer/owner_callable_adapter_receipt/sat-complete.closeout.json",
            },
        }
    )

    assert state["phase"] == "terminal_closeout_ready"
    assert state["next_safe_action"]["kind"] == "consume_terminal_closeout"
    assert state["next_safe_action"]["provider_admission_allowed"] is False
    assert state["evidence_refs"] == [
        "artifacts/supervision/consumer/owner_callable_adapter_receipt/sat-complete.closeout.json"
    ]


def test_terminal_closeout_with_stale_fingerprint_does_not_match_current_obligation() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "terminal_closeout_precedence_evidence": {
                "status": "completed",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::old",
                "action_fingerprint": "publication-blockers::old",
                "stage_attempt_id": "sat-stale",
                "closeout_ref": "artifacts/supervision/consumer/owner_callable_adapter_receipt/sat-stale.closeout.json",
            },
        }
    )

    assert state["phase"] == "owner_action_ready"
    assert state["next_safe_action"]["kind"] == "materialize_mas_transition_request_or_owner_callable"
    assert state["next_safe_action"]["provider_admission_allowed"] is True
    assert not state.get("evidence_refs")


def test_foreground_file_delta_without_owner_receipt_is_unadopted() -> None:
    state = _module().build_paper_recovery_state(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": _executable_work_unit(),
            "manual_foreground_delta": {
                "changed": True,
                "paths": ["manuscript/main.tex"],
                "owner_receipt_ref": None,
            },
        }
    )

    assert state["phase"] == "manual_foreground_unadopted"
    assert state["next_safe_action"]["kind"] == "adopt_manual_delta_through_mas_owner_receipt"
    assert state["next_safe_action"]["provider_admission_allowed"] is False

from tests.test_paper_recovery_state_cases.provider_admission_transition_cases import *  # noqa: F401,F403

from tests.test_paper_recovery_state_cases.running_attempt_identity_cases import *  # noqa: F401,F403
