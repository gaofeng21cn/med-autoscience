from __future__ import annotations
from tests.test_current_control_executable_handoff_cases.provider_readback_cases import *  # noqa: F403,F401
from tests.test_current_control_executable_handoff_cases.terminal_provider_precedence_cases import *  # noqa: F403,F401

import importlib
import json
import os

from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_transition_request_candidate_projects_current_executable_action() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_control_executable_handoff"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "quest_status": "transition_request_pending",
        "running_provider_attempt": False,
        "blocked_reason": "anti_loop_budget_exhausted",
        "next_owner": "one-person-lab",
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "ai_reviewer",
            "next_work_unit": work_unit_id,
            "typed_blocker": None,
        },
        "action_queue": [
            {
                "action_type": "return_to_ai_reviewer_workflow",
                "status": "transition_request_pending",
                "owner": "ai_reviewer",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            }
        ],
        "transition_request_pending_count": 1,
        "transition_request_candidates": [
            {
                "status": "transition_request_pending",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "route_identity_key": route_key,
                "attempt_idempotency_key": route_key,
                "idempotency_key": "paper-policy-request:dm002-ai-reviewer",
                "next_executable_owner": "ai_reviewer",
                "mas_owner_action_source": (
                    "paper_recovery_state.next_safe_action.successor_owner_action"
                ),
                "provider_admission_pending": False,
                "provider_attempt_or_lease_required": False,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_runtime_required": True,
                "required_output_surface": "artifacts/publication_eval/latest.json",
                "currentness_basis": {
                    "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
                    "runtime_health_epoch": "runtime-health-event-007038-937370e3bbb8ab22",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
            }
        ],
    }

    action = module.current_control_executable_owner_action(handoff)

    assert action is not None
    assert action["source"] == "paper_recovery_state.next_safe_action.successor_owner_action"
    assert action["next_owner"] == "ai_reviewer"
    assert action["action_type"] == "return_to_ai_reviewer_workflow"
    assert action["work_unit_id"] == work_unit_id
    assert action["work_unit_fingerprint"] == fingerprint
    assert action["provider_admission_pending"] is False
    assert action["transition_request_pending"] is True
    assert action["provider_admission_requires_opl_runtime_result"] is True

    currentness = module.current_control_executable_currentness_handoff(
        handoff,
        current_control_executable_action=action,
    )
    assert currentness["blocked_reason"] is None
    assert currentness["typed_blocker"] is None
    assert currentness["next_owner"] == "ai_reviewer"
    assert currentness["current_work_unit"]["status"] == "executable_owner_action"
    assert currentness["current_work_unit"]["owner"] == "ai_reviewer"
    assert currentness["current_work_unit"]["action_type"] == "return_to_ai_reviewer_workflow"
    assert currentness["current_work_unit"]["work_unit_id"] == work_unit_id
    assert currentness["current_work_unit"]["state"]["provider_admission_pending"] is False
    assert currentness["current_work_unit"]["state"]["transition_request_pending"] is True


def test_consumed_provider_terminal_closeout_does_not_project_next_forced_delta_handoff() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    consumed_work_unit_id = "medical_prose_write_repair"
    consumed_fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    next_work_unit_id = "ai_reviewer_recheck_after_medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    payload = {
        "study_id": study_id,
        "quest_id": study_id,
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "action_type": "request_opl_stage_attempt",
            "allowed_actions": ["request_opl_stage_attempt"],
            "work_unit_id": consumed_work_unit_id,
            "work_unit_fingerprint": consumed_fingerprint,
            "action_fingerprint": consumed_fingerprint,
            "provider_admission_pending": False,
            "transition_request_pending": True,
            "provider_admission_requires_opl_runtime_result": True,
            "opl_transition_runtime_required": True,
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "write",
            "action_type": "request_opl_stage_attempt",
            "work_unit_id": consumed_work_unit_id,
            "work_unit_fingerprint": consumed_fingerprint,
            "action_fingerprint": consumed_fingerprint,
        },
        "provider_admission_pending_count": 0,
        "transition_request_pending_count": 0,
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "quest_status": "provider_admission_pending",
        "running_provider_attempt": False,
        "runtime_health": {
            "health_status": "terminal",
            "runtime_liveness_status": "terminal",
        },
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "write",
            "next_work_unit": consumed_work_unit_id,
            "typed_blocker": None,
        },
        "latest_terminal_stage_log": {
            "surface_kind": "mas_latest_terminal_stage_log_projection",
            "study_id": study_id,
            "stage_attempt_id": "sat_efdab57a49cb6d58f2a17eeb",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": consumed_work_unit_id,
            "work_unit_fingerprint": consumed_fingerprint,
            "status": "closed_with_domain_owner_refs",
            "owner_receipt_refs": [
                f"studies/{study_id}/artifacts/controller/repair_execution_receipts/latest.json"
            ],
            "source_path": (
                f"studies/{study_id}/artifacts/supervision/consumer/"
                "stage_attempt_closeouts/sat_efdab57a49cb6d58f2a17eeb.json"
            ),
            "paper_stage_log": {
                "stage_name": consumed_work_unit_id,
                "outcome": "closed_with_domain_owner_refs",
                "progress_delta_classification": "deliverable_progress",
                "changed_paper_surfaces": [
                    f"studies/{study_id}/artifacts/stage_outputs/current_body/paper/draft.md"
                ],
                "next_forced_delta": {
                    "owner_action": {
                        "action_type": "return_to_ai_reviewer_workflow",
                        "next_owner": "ai_reviewer",
                        "work_unit_id": next_work_unit_id,
                    },
                    "reason": "story_surface_delta_recorded_requires_ai_reviewer_recheck",
                    "required_delta_kind": "ai_reviewer_recheck_or_publication_gate_replay",
                    "target_surface": {
                        "surface_ref": "artifacts/publication_eval/latest.json",
                    },
                    "work_unit_id": next_work_unit_id,
                },
            },
        },
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
            "stage_attempt_id": "sat_efdab57a49cb6d58f2a17eeb",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": consumed_work_unit_id,
            "work_unit_fingerprint": consumed_fingerprint,
            "action_fingerprint": consumed_fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
        },
    }

    result = module.refresh_current_execution_surfaces(
        payload=payload,
        status={},
        handoff=handoff,
        runtime_health_snapshot={},
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["transition_request_pending_count"] == 0
    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"] == {}
    assert result["current_execution_envelope"].get("state_kind") != "executable_owner_action"


def test_retired_current_work_unit_does_not_promote_current_control_transition_request() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "opl_current_control_state.transition_request_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "next_owner": "ai_reviewer",
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": f"provider-admission::{study_id}::{fingerprint}",
        "attempt_idempotency_key": f"provider-admission::{study_id}::{fingerprint}",
        "provider_admission_pending": False,
        "transition_request_pending": True,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
        "currentness_basis": {
            "truth_epoch": "truth-event-000040-1a4d1f9cfed66d87",
            "runtime_health_epoch": "runtime-health-event-007038-937370e3bbb8ab22",
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": action,
        },
        current_executable_owner_action=action,
        provider_admission={
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "transition_request_pending_count": 1,
            "transition_request_candidates": [dict(action, status="transition_request_pending")],
            "current_executable_owner_action": action,
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_id": "anti_loop_budget_exhausted",
            "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
            "blocked_reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "ai_reviewer_record_gate_consumption",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
            "action_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
            "anti_loop_budget": {"status": "exhausted"},
        },
        blocked_reason="anti_loop_budget_exhausted",
        next_owner="one-person-lab",
    )

    assert work_unit == {}


def test_retired_current_work_unit_does_not_promote_transition_request_candidate() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "opl_current_control_state.transition_request_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "next_owner": "ai_reviewer",
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "provider_admission_pending": False,
        "transition_request_pending": True,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": action,
            "progress_first_monitoring_summary": {
                "dispatch_consumption": {
                    "consumption_status": "consumed",
                    "receipt_ref": "artifacts/publication_eval/latest.json",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "canonical_work_unit_identity": {
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "source_eval_id": "publication-eval::002::prior-ai-reviewer",
                    },
                }
            },
        },
        actions=[action],
        current_executable_owner_action=action,
        provider_admission={
            "transition_request_pending_count": 1,
            "transition_request_candidates": [
                {
                    **action,
                    "status": "transition_request_pending",
                    "next_executable_owner": "ai_reviewer",
                }
            ],
            "current_executable_owner_action": action,
        },
        typed_blocker={
            "surface_kind": "mas_domain_typed_blocker",
            "blocker_id": "anti_loop_budget_exhausted",
            "blocker_type": "repeat_suppressed_after_opl_execution_authorization_required",
            "blocked_reason": "anti_loop_budget_exhausted",
            "owner": "one-person-lab",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "ai_reviewer_record_gate_consumption",
            "work_unit_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
            "action_fingerprint": (
                "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
            ),
        },
        blocked_reason="anti_loop_budget_exhausted",
        next_owner="one-person-lab",
    )

    assert work_unit == {}


def test_retired_current_work_unit_does_not_preserve_paper_recovery_successor_flags() -> None:
    module = importlib.import_module("med_autoscience.controllers.current_work_unit")
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": study_id,
            "quest_id": study_id,
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "schema_version": 1,
                "study_id": study_id,
                "quest_id": study_id,
                "phase": "owner_action_ready",
                "next_safe_action": {
                    "kind": "materialize_successor_owner_action",
                    "owner": "write",
                    "successor_owner_action": {
                        "owner": "write",
                        "action_type": "request_opl_stage_attempt",
                        "work_unit_id": work_unit_id,
                        "work_unit_fingerprint": fingerprint,
                        "domain_transition_decision_type": "route_back_same_line",
                        "domain_transition_controller_action": "request_opl_stage_attempt",
                        "source_surface": "domain_transition",
                        "source_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                    },
                },
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                "source_surface": "domain_transition",
                "next_owner": "write",
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "allowed_actions": ["request_opl_stage_attempt"],
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "provider_admission_pending": False,
                "transition_request_pending": True,
                "provider_attempt_or_lease_required": False,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_runtime_required": True,
            },
        },
        provider_admission={
            "transition_request_pending_count": 1,
            "transition_request_candidates": [
                {
                    "status": "transition_request_pending",
                    "study_id": study_id,
                    "action_type": "request_opl_stage_attempt",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "next_executable_owner": "write",
                }
            ],
        },
        typed_blocker={},
        blocked_reason=None,
        next_owner="write",
    )

    assert work_unit == {}


def test_terminal_probe_does_not_consume_different_identity_transition_request(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    work_unit_id = "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    route_key = f"provider-admission::{study_id}::{fingerprint}"
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "opl_current_control_state.transition_request_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "next_owner": "ai_reviewer",
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": "paper-policy-request:dm002-ai-reviewer",
        "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
        "provider_admission_pending": False,
        "transition_request_pending": True,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
    }
    candidate = {
        **action,
        "status": "transition_request_pending",
        "next_executable_owner": "ai_reviewer",
        "mas_owner_action_source": "paper_recovery_state.next_safe_action.successor_owner_action",
    }
    original_handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "running_provider_attempt": False,
        "transition_request_pending_count": 1,
        "transition_request_candidates": [candidate],
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
        "current_executable_owner_action": action,
    }
    stale_consumed = {
        "surface_kind": "provider_admission_terminal_closeout_consumed",
        "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
        "stage_attempt_id": "sat-stale-gate-closeout",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": "ai_reviewer_record_gate_consumption",
        "work_unit_fingerprint": (
            "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
        ),
        "action_fingerprint": (
            "domain-transition::route_back_same_line::ai_reviewer_record_gate_consumption"
        ),
    }

    def fake_refresh(**kwargs):
        assert kwargs["candidates"][0]["work_unit_id"] == work_unit_id
        return {
            **original_handoff,
            "active_stage_attempt_id": "sat-stale-gate-closeout",
            "active_run_id": "opl-stage-attempt://sat-stale-gate-closeout",
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "latest_terminal_stage_log": {
                "stage_attempt_id": "sat-stale-gate-closeout",
                "status": "completed",
            },
            "provider_admission_terminal_closeout_consumed": stale_consumed,
        }

    monkeypatch.setattr(module, "refresh_handoff_with_terminal_closeout_candidates", fake_refresh)

    result = module._apply_provider_admission_fields_with_terminal_probe(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": action,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
            },
            "transition_request_pending_count": 1,
            "transition_request_candidates": [candidate],
        },
        handoff=original_handoff,
        study_root=tmp_path,
        profile=object(),
        study_id=study_id,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["transition_request_pending_count"] == 1
    assert result["transition_request_candidates"][0]["action_type"] == "return_to_ai_reviewer_workflow"
    assert result["transition_request_candidates"][0]["work_unit_id"] == work_unit_id
    assert "provider_admission_terminal_closeout_consumed" not in result
    handoff = result["opl_current_control_state_handoff"]
    assert "provider_admission_terminal_closeout_consumed" not in handoff
    assert "latest_terminal_stage_log" not in handoff
    assert handoff["transition_request_candidates"][0]["work_unit_id"] == work_unit_id


def test_terminal_consumed_provider_candidate_is_not_active_provider_control() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_currentness"
    )
    fingerprint = "publication-blockers::f11710a114497b27"
    route_key = "paper-policy-request:60cf5242a09d91458cb21e22"
    readback = opl_transition_readback(
        "002-dm-china-us-mortality-attribution",
        action_fingerprint=fingerprint,
        work_unit_id="analysis_claim_evidence_repair",
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )
    handoff = {
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "action_type": "run_quality_repair_batch",
                "owner": "analysis-campaign",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "route_identity_key": route_key,
                "attempt_idempotency_key": route_key,
                "opl_domain_progress_transition_live_readback": readback,
            }
        ],
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "analysis_claim_evidence_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "route_identity_key": route_key,
            "attempt_idempotency_key": route_key,
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/sat.closeout.json"
            ),
        },
    }

    assert module.active_provider_control(handoff) is False
    assert module.current_control_provider_admission_action(handoff) is None


def test_terminal_closeout_typed_blocker_suppresses_stale_provider_admission_candidate() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_currentness"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    stale_fingerprint = "publication-blockers::f11710a114497b27"
    stale_route_key = "paper-policy-request:60cf5242a09d91458cb21e22"
    terminal_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    terminal_route_key = "paper-policy-request:3e1395abcbe28c3d60094f32"
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=stale_fingerprint,
        work_unit_id="analysis_claim_evidence_repair",
        route_identity_key=stale_route_key,
        attempt_idempotency_key=stale_route_key,
        request_idempotency_key=stale_route_key,
    )
    handoff = {
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [
            {
                "action_type": "run_quality_repair_batch",
                "owner": "analysis-campaign",
                "work_unit_id": "analysis_claim_evidence_repair",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
                "route_identity_key": stale_route_key,
                "attempt_idempotency_key": stale_route_key,
                "opl_domain_progress_transition_live_readback": readback,
            }
        ],
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
            "stage_attempt_id": "sat_006cf0ce68e11a4661912a37",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
            "work_unit_fingerprint": terminal_fingerprint,
            "action_fingerprint": terminal_fingerprint,
            "route_identity_key": terminal_route_key,
            "attempt_idempotency_key": terminal_route_key,
            "typed_blocker_ref": (
                "artifacts/supervision/consumer/owner_callable_adapter_receipt/"
                "sat_006cf0ce68e11a4661912a37.closeout.json#typed_blocker"
            ),
            "typed_blocker": {
                "blocker_type": "owner_receipt_missing_for_gate_clearing_batch",
                "blocked_reason": "owner_receipt_missing_for_gate_clearing_batch",
                "owner": "med-autoscience",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "consume_current_ai_reviewer_publication_eval_record_and_replay_gate",
                "work_unit_fingerprint": terminal_fingerprint,
                "action_fingerprint": terminal_fingerprint,
            },
        },
    }

    assert module.active_provider_control(handoff) is False
    assert module.current_control_provider_admission_action(handoff) is None


def test_terminal_closeout_typed_blocker_outranks_stale_provider_admission_projection() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.current_execution_surfaces"
    )
    study_id = "002-dm-china-us-mortality-attribution"
    stale_work_unit_id = "analysis_claim_evidence_repair"
    stale_fingerprint = "publication-blockers::f11710a114497b27"
    stale_route_key = "paper-policy-request:60cf5242a09d91458cb21e22"
    terminal_work_unit_id = "consume_current_ai_reviewer_publication_eval_record_and_replay_gate"
    terminal_fingerprint = (
        "domain-transition::ai_reviewer_re_eval::"
        "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    )
    terminal_route_key = "paper-policy-request:3e1395abcbe28c3d60094f32"
    closeout_ref = (
        "studies/002-dm-china-us-mortality-attribution/artifacts/supervision/"
        "consumer/owner_callable_adapter_receipt/sat_006cf0ce68e11a4661912a37.closeout.json"
    )
    stale_readback = opl_transition_readback(
        study_id,
        action_fingerprint=stale_fingerprint,
        work_unit_id=stale_work_unit_id,
        route_identity_key=stale_route_key,
        attempt_idempotency_key=stale_route_key,
        request_idempotency_key=stale_route_key,
    )
    stale_provider_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "opl_current_control_state.provider_admission_candidates",
        "source_surface": "opl_current_control_state.provider_admission_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "next_owner": "analysis-campaign",
        "owner": "analysis-campaign",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": stale_work_unit_id,
        "work_unit_fingerprint": stale_fingerprint,
        "action_fingerprint": stale_fingerprint,
        "route_identity_key": stale_route_key,
        "attempt_idempotency_key": stale_route_key,
        "provider_admission_pending": True,
        "transition_request_pending": False,
    }
    provider_candidate = {
        **stale_provider_action,
        "status": "provider_admission_pending",
        "next_executable_owner": "analysis-campaign",
        "opl_domain_progress_transition_live_readback": stale_readback,
    }
    handoff = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "study_id": study_id,
        "quest_id": study_id,
        "quest_status": "provider_admission_pending",
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
        "provider_admission_candidates": [provider_candidate],
        "transition_request_pending_count": 0,
        "transition_request_candidates": [],
        "current_executable_owner_action": stale_provider_action,
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "study_id": study_id,
            "quest_id": study_id,
            "owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": stale_work_unit_id,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "opl_current_control_state.provider_admission_candidates",
                "provider_admission_pending": True,
            },
        },
        "current_execution_envelope": {
            "state_kind": "executable_owner_action",
            "owner": "analysis-campaign",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": stale_work_unit_id,
            "work_unit_fingerprint": stale_fingerprint,
            "action_fingerprint": stale_fingerprint,
        },
        "provider_admission_terminal_closeout_consumed": {
            "surface_kind": "provider_admission_terminal_closeout_consumed",
            "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
            "stage_attempt_id": "sat_006cf0ce68e11a4661912a37",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": terminal_work_unit_id,
            "work_unit_fingerprint": terminal_fingerprint,
            "action_fingerprint": terminal_fingerprint,
            "route_identity_key": terminal_route_key,
            "attempt_idempotency_key": terminal_route_key,
            "typed_blocker_ref": f"{closeout_ref}#typed_blocker",
            "closeout_refs": [closeout_ref],
            "typed_blocker": {
                "blocker_type": "owner_receipt_missing_for_gate_clearing_batch",
                "blocked_reason": "owner_receipt_missing_for_gate_clearing_batch",
                "owner": "med-autoscience",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": terminal_work_unit_id,
                "work_unit_fingerprint": terminal_fingerprint,
                "action_fingerprint": terminal_fingerprint,
                "typed_blocker_ref": f"{closeout_ref}#typed_blocker",
            },
        },
    }

    result = module.refresh_current_execution_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": stale_provider_action,
            "current_work_unit": handoff["current_work_unit"],
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [provider_candidate],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
        },
        status={"study_id": study_id, "quest_id": study_id},
        handoff=handoff,
        runtime_health_snapshot={},
    )

    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"] == {}
    assert result["current_execution_envelope"] == {}
    evidence_handoff = result["current_execution_evidence"]["opl_current_control_state_handoff"]
    typed_blocker = evidence_handoff["provider_admission_terminal_closeout_consumed"]["typed_blocker"]
    assert typed_blocker["owner"] == "med-autoscience"
    assert typed_blocker["action_type"] == "run_gate_clearing_batch"
    assert typed_blocker["work_unit_id"] == terminal_work_unit_id
    assert typed_blocker["work_unit_fingerprint"] == terminal_fingerprint
    assert typed_blocker["blocked_reason"] == "owner_receipt_missing_for_gate_clearing_batch"
