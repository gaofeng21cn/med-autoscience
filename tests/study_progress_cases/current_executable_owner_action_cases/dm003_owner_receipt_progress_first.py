from __future__ import annotations

import importlib

from .dm003_owner_receipt_running_handoff import (
    AI_REVIEWER_FINGERPRINT,
    AI_REVIEWER_WORK_UNIT,
    STUDY_ID,
    WRITE_FINGERPRINT,
    WRITE_WORK_UNIT,
    _dm003_post_write_repair_payload,
    _opl_transition_live_readback,
)


def test_current_execution_refresh_consumes_terminal_closeout_over_stale_successor_ready() -> None:
    surfaces = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts."
        "current_execution_surfaces"
    )
    receipt_ref = "artifacts/controller/repair_execution_receipts/latest.json"
    handoff_work_unit = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "owner_receipt_recorded",
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "stage_id": "publication_supervision",
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": WRITE_WORK_UNIT,
        "work_unit_fingerprint": WRITE_FINGERPRINT,
        "action_fingerprint": WRITE_FINGERPRINT,
        "required_output_contract": {
            "owner_receipt_consumed": True,
            "owner_receipt_ref": receipt_ref,
            "provider_completion_is_domain_completion": False,
            "domain_ready_authorized": False,
        },
        "acceptance_refs": [receipt_ref],
        "state": {
            "state_kind": "owner_receipt_recorded",
            "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            "owner_receipt_ref": receipt_ref,
            "next_safe_action_kind": "consume_owner_receipt",
            "provider_admission_pending": False,
        },
        "currentness_basis": {
            "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "truth_epoch": "truth-event-000035-39f0b8e96689a623",
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7",
        },
    }
    payload = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "current_stage": "publication_supervision",
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "next_owner": "write",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "action_fingerprint": WRITE_FINGERPRINT,
            "action_type": "run_quality_repair_batch",
            "allowed_actions": ["run_quality_repair_batch"],
            "owner_receipt_required": True,
            "paper_recovery_successor": {
                "source": "paper_recovery_state",
                "successor_ready": True,
                "provider_admission_allowed": True,
            },
        },
        "current_work_unit": {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "executable_owner_action",
            "owner": "write",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": WRITE_WORK_UNIT,
            "work_unit_fingerprint": WRITE_FINGERPRINT,
            "state": {
                "state_kind": "executable_owner_action",
                "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            },
        },
        "paper_recovery_state": {
            "surface_kind": "paper_recovery_state",
            "schema_version": 1,
            "study_id": STUDY_ID,
            "quest_id": STUDY_ID,
            "phase": "owner_action_ready",
            "current_authority": {
                "owner": "write",
                "authority": "med-autoscience",
                "obligation": {
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": WRITE_WORK_UNIT,
                    "work_unit_fingerprint": WRITE_FINGERPRINT,
                },
            },
            "next_safe_action": {
                "kind": "materialize_successor_owner_action",
                "owner": "write",
                "provider_admission_allowed": True,
                "successor_owner_action": {
                    "action_type": "run_quality_repair_batch",
                    "owner": "write",
                    "work_unit_id": WRITE_WORK_UNIT,
                    "work_unit_fingerprint": WRITE_FINGERPRINT,
                    "source_surface": "paper_recovery_state.owner_action_ready",
                    "source_ref": receipt_ref,
                },
            },
            "supervisor_decision": {
                "decision": "materialize_recovery_action",
                "identity_match": True,
            },
        },
    }

    result = surfaces.refresh_current_execution_surfaces(
        payload=payload,
        status={"study_id": STUDY_ID},
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "running_provider_attempt": False,
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "provider_admission_terminal_closeout_consumed": {
                "surface_kind": "provider_admission_terminal_closeout_consumed",
                "stage_attempt_id": "sat_a1ad96cc7cb753974a3b0acd",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": WRITE_WORK_UNIT,
                "work_unit_fingerprint": WRITE_FINGERPRINT,
                "action_fingerprint": WRITE_FINGERPRINT,
                "owner_receipt_ref": receipt_ref,
            },
            "current_work_unit": handoff_work_unit,
            "current_execution_envelope": {
                "state_kind": "owner_receipt_recorded",
                "owner": "write",
            },
        },
        runtime_health_snapshot={
            "runtime_health_epoch": "runtime-health-event-006980-c004aeb3b04b4dc7"
        },
    )

    assert result["current_executable_owner_action"] is None
    assert result["current_work_unit"]["status"] == "owner_receipt_recorded"
    assert result["current_work_unit"]["state"]["owner_receipt_ref"] == receipt_ref
    assert result["current_execution_envelope"]["state_kind"] == "owner_receipt_recorded"


def test_progress_first_projects_running_ai_reviewer_handoff_over_consumed_write_receipt() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    payload = _dm003_post_write_repair_payload()
    payload["current_executable_owner_action"] = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "domain_transition",
        "next_owner": "ai_reviewer",
        "work_unit_id": AI_REVIEWER_WORK_UNIT,
        "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
        "action_fingerprint": AI_REVIEWER_FINGERPRINT,
        "action_type": "return_to_ai_reviewer_workflow",
        "allowed_actions": ["return_to_ai_reviewer_workflow"],
        "owner_receipt_required": True,
        "owner_route_currentness_basis": {
            "source": "domain_transition",
            "work_unit_id": AI_REVIEWER_WORK_UNIT,
            "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
            "truth_epoch": "truth-current",
            "runtime_health_epoch": "runtime-current",
        },
    }
    payload["opl_current_control_state_handoff"] = {
        "study_id": STUDY_ID,
        "quest_id": STUDY_ID,
        "running_provider_attempt": True,
        "active_run_id": "opl-stage-attempt://sat_current_ai_reviewer",
        "active_stage_attempt_id": "sat_current_ai_reviewer",
        "active_workflow_id": "wf_current_ai_reviewer",
        "opl_domain_progress_transition_runtime_live_readback": _opl_transition_live_readback(
            STUDY_ID,
            work_unit_id=AI_REVIEWER_WORK_UNIT,
            fingerprint=AI_REVIEWER_FINGERPRINT,
            stage_run_id="sat_current_ai_reviewer",
        ),
        "next_owner": "ai_reviewer",
        "owner": "ai_reviewer",
        "action_type": "return_to_ai_reviewer_workflow",
        "work_unit_id": AI_REVIEWER_WORK_UNIT,
        "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
        "action_fingerprint": AI_REVIEWER_FINGERPRINT,
        "route_identity_key": f"provider-admission::{STUDY_ID}::{AI_REVIEWER_FINGERPRINT}",
        "attempt_idempotency_key": (
            f"provider-admission::{STUDY_ID}::{AI_REVIEWER_FINGERPRINT}"
        ),
        "idempotency_key": f"provider-admission::{STUDY_ID}::{AI_REVIEWER_FINGERPRINT}",
        "owner_route_currentness_basis": {
            "work_unit_id": AI_REVIEWER_WORK_UNIT,
            "work_unit_fingerprint": AI_REVIEWER_FINGERPRINT,
            "truth_epoch": "truth-current",
            "runtime_health_epoch": "runtime-current",
        },
        "runtime_health": {
            "runtime_liveness_status": "attempt_running",
            "health_status": "live",
        },
        "action_queue": [],
    }

    monitoring = module.build_progress_first_monitoring_summary(payload)

    assert monitoring["running_provider_attempt"] is True
    assert monitoring["execution_state_kind"] == "running_provider_attempt"
    assert monitoring["active_stage_attempt_id"] == "sat_current_ai_reviewer"
    assert monitoring["current_executable_owner_action"]["source"] == "domain_transition"
    admission = monitoring["owner_action_admission"]
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_proof"]["active_stage_attempt_id"] == (
        "sat_current_ai_reviewer"
    )
