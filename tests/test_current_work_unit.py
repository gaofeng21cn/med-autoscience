from __future__ import annotations

import importlib
from collections.abc import Mapping
from typing import Any


REQUIRED_KEYS = {
    "surface_kind",
    "schema_version",
    "status",
    "study_id",
    "quest_id",
    "stage_id",
    "owner",
    "action_type",
    "work_unit_id",
    "work_unit_fingerprint",
    "action_fingerprint",
    "input_refs",
    "required_output_contract",
    "acceptance_refs",
    "state",
    "currentness_basis",
    "authority_boundary",
}


def _module():
    return importlib.import_module("med_autoscience.controllers.current_work_unit")


def _assert_contract_shape(work_unit: Mapping[str, Any]) -> None:
    assert set(work_unit) == REQUIRED_KEYS
    assert work_unit["surface_kind"] == "current_work_unit"
    assert work_unit["schema_version"] == 1
    assert work_unit["status"] in {
        "executable_owner_action",
        "running_provider_attempt",
        "typed_blocker",
        "blocked_current_work_unit",
    }
    assert work_unit["authority_boundary"]["top_level_truth"] == "status"
    assert work_unit["authority_boundary"]["mas_owner_authority_preserved"] is True
    assert work_unit["authority_boundary"]["stage_transition_authority"] == "OPL Stage Transition Authority"
    assert work_unit["authority_boundary"]["stage_authority_role"] == (
        "non_authoritative_observation_and_intent_producer"
    )
    assert work_unit["authority_boundary"]["can_write_stage_current_pointer"] is False
    assert work_unit["authority_boundary"]["can_write_current_owner_delta"] is False
    assert work_unit["authority_boundary"]["can_write_stage_terminal_state"] is False


def test_current_work_unit_projects_repair_progress_ai_reviewer_followup() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
            "paper_progress_delta": {"count": 1},
            "progress_first_sprint_state": {"paper_progress_delta_counted": True},
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                    "latest_owner_answer_kind": "typed_blocker",
                    "hard_gate": {"state": "domain_owner_answer_recorded"},
                }
            },
        },
        actions=[
            {
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "action_type": "return_to_ai_reviewer_workflow",
                "owner": "ai_reviewer",
                "next_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "work_unit_fingerprint": "study-progress-current-owner-ticket::002::ai-reviewer",
                "action_fingerprint": "study-progress-current-owner-ticket::002::ai-reviewer",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
                "acceptance_refs": ["artifacts/supervision/requests/ai_reviewer/latest.json"],
            }
        ],
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["action_type"] == "return_to_ai_reviewer_workflow"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["source"] == "repair_progress_projection.mas_owner_repair_execution_evidence"
    assert work_unit["currentness_basis"]["work_unit_fingerprint"] == (
        "study-progress-current-owner-ticket::002::ai-reviewer"
    )


def test_current_work_unit_preserves_readiness_typed_blocker_over_stale_handoff_action() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
            "stage_kernel_projection": {
                "current_owner_delta": {
                    "owner": "MedAutoScience",
                    "action": "complete_medical_paper_readiness_surface",
                    "reason": "medical_paper_readiness_missing",
                    "source_ref": "artifacts/stage_outputs/08/receipts/typed_blocker.json",
                    "source_kind": "typed_blocker",
                },
                "stage_run_kernel": {"status": "TypedBlocked"},
            },
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "complete_medical_paper_readiness_surface",
                "owner": "MedAutoScience",
                "next_work_unit": "complete_medical_paper_readiness_surface",
                "work_unit_id": "complete_medical_paper_readiness_surface",
                "allowed_actions": ["complete_medical_paper_readiness_surface"],
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="MedAutoScience",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "typed_blocker"
    assert work_unit["owner"] == "MedAutoScience"
    assert work_unit["state"]["source"] == "stage_owner_answer"
    assert work_unit["state"]["typed_blocker"]["blocker_type"] == "medical_paper_readiness_missing"
    assert work_unit["state"]["stale_queue_or_handoff_can_override"] is False


def test_current_work_unit_accepts_strict_running_provider_proof() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "source_surface": "action_queue",
                "action_type": "run_gate_clearing_batch",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            }
        ],
        blocked_reason="medical_paper_readiness_not_ready",
        next_owner="gate_clearing_batch",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live",
            "active_stage_attempt_id": "sat-live",
            "active_workflow_id": "wf-live",
            "work_unit_id": "publication_gate_replay",
            "action_type": "run_gate_clearing_batch",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "gate_clearing_batch"
    assert work_unit["work_unit_id"] == "publication_gate_replay"
    assert work_unit["state"]["strict_running_proof"] is True
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live"


def test_current_work_unit_running_attempt_supersedes_ai_reviewer_recheck_blocker() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-china-us-mortality-attribution",
            "quest_id": "002-dm-china-us-mortality-attribution",
            "current_stage": "publication_supervision",
        },
        blocked_reason="repair_progress_ai_reviewer_recheck_required",
        next_owner="ai_reviewer",
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-ai-review",
            "active_stage_attempt_id": "sat-live-ai-review",
            "active_workflow_id": "wf-live-ai-review",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["owner"] == "ai_reviewer"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert "typed_blocker" not in work_unit["state"]


def test_current_work_unit_ignores_terminal_log_without_matching_attempt_id() -> None:
    module = _module()

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_stage": "publication_supervision",
        },
        live_provider_attempt={
            "running_provider_attempt": True,
            "active_run_id": "opl-stage-attempt://sat-live-gate",
            "active_stage_attempt_id": "sat-live-gate",
            "active_workflow_id": "wf-live-gate",
            "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "action_type": "return_to_ai_reviewer_workflow",
            "runtime_health": {
                "health_status": "running",
                "runtime_liveness_status": "live",
            },
            "latest_terminal_stage_log": {
                "stage_attempt_id": None,
                "status": "blocked",
                "source_path": "studies/003/artifacts/supervision/consumer/default_executor_execution/latest.json",
            },
        },
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "running_provider_attempt"
    assert work_unit["work_unit_id"] == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
    assert work_unit["state"]["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-live-gate"


def test_current_work_unit_treats_handoff_ready_as_pending_evidence_not_running() -> None:
    module = _module()
    handoff = {
        "execution_status": "handoff_ready",
        "provider_attempt_or_lease_required": True,
        "running_provider_attempt": False,
        "provider_admission_pending_count": 1,
    }

    work_unit = module.build_current_work_unit(
        progress={
            "study_id": "002-dm-cvd-mortality-risk",
            "quest_id": "002-dm-cvd-mortality-risk",
            "current_stage": "publication_supervision",
        },
        actions=[
            {
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_owner": "write",
                "next_work_unit": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "work_unit_id": "dm002_current_publication_hardening_after_current_ai_reviewer_eval",
                "authority": "mas_provider_admission_identity",
                "action_id": "provider-admission::002-dm::run_quality_repair_batch",
                "work_unit_fingerprint": "study-progress-current-owner-ticket::002::repair",
                "action_fingerprint": "study-progress-current-owner-ticket::002::repair",
            }
        ],
        provider_admission=handoff,
        blocked_reason="provider_admission_current_control_state_required",
        next_owner="write",
    )

    _assert_contract_shape(work_unit)
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["provider_admission_pending"] is True
    assert work_unit["state"]["pending_provider_admission_evidence"]["execution_status"] == "handoff_ready"
    assert work_unit["status"] != "running_provider_attempt"
