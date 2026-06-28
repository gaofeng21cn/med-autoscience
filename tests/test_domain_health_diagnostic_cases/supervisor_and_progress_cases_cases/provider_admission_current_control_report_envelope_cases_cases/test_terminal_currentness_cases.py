from __future__ import annotations

import importlib
from pathlib import Path

from tests.provider_admission_current_control_helpers import opl_transition_readback


def test_runtime_report_prefers_owner_receipt_currentness_over_stale_user_waiting_action() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    owner_receipt_ref = (
        "/workspace/studies/003/artifacts/controller/quality_repair_batch/latest.json"
    )
    recovery_state = {
        "surface_kind": "paper_recovery_state",
        "phase": "owner_receipt_recorded",
        "current_authority": {
            "obligation": {
                "study_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            }
        },
        "next_safe_action": {
            "kind": "consume_owner_receipt",
            "owner": "write",
            "provider_admission_allowed": False,
            "owner_receipt_ref": owner_receipt_ref,
        },
        "owner_receipt_ref": owner_receipt_ref,
        "evidence_refs": [owner_receipt_ref],
        "supervisor_decision": {"decision": "stop_with_owner_receipt"},
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
                "runtime_health_snapshot": {
                    "canonical_runtime_action": "external_supervisor_required",
                },
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": owner_receipt_ref,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                    "next_work_unit": None,
                    "typed_blocker": None,
                    "parked_state": None,
                },
                "paper_recovery_state": recovery_state,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "owner_receipt_recorded"
    assert action["reason"] == "current_owner_receipt_recorded"
    assert action["running_provider_attempt"] is False
    assert action["current_work_unit"]["status"] == "owner_receipt_recorded"
    assert action["paper_recovery_state"]["phase"] == "owner_receipt_recorded"
    assert action["paper_recovery_state"]["next_safe_action"]["kind"] == "consume_owner_receipt"

def test_runtime_report_marks_current_executable_owner_action_ready_not_blocked() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::5d99b7c4019bd601"
    current_owner_action = {
        "surface_kind": "current_executable_owner_action",
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "next_owner": "analysis-campaign",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "resume_request_failed",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "executable_owner_action",
                    "owner": "analysis-campaign",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "executable_owner_action",
                        "active_caller_class": "mas_owner_callable",
                        "ordinary_schedulable": True,
                        "counts_as_paper_progress": False,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "analysis-campaign",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                },
                "current_executable_owner_action": current_owner_action,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "owner_action_ready"
    assert action["reason"] == "current_executable_owner_action_ready"
    assert action["running_provider_attempt"] is False
    assert action["current_work_unit"]["status"] == "executable_owner_action"
    assert action["current_work_unit"]["state"]["ordinary_schedulable"] is True
    assert action["current_executable_owner_action"] == current_owner_action

def test_runtime_report_marks_provider_admission_pending_not_blocked() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "analysis_claim_evidence_repair"
    fingerprint = "publication-blockers::5d99b7c4019bd601"
    idempotency_key = "paper-policy-request:601090ce8401049b401f90e3"
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": idempotency_key,
        "attempt_idempotency_key": idempotency_key,
        "dispatch_path": "/workspace/studies/003/artifacts/supervision/consumer/default_executor_dispatches/run_quality_repair_batch.json",
        "opl_domain_progress_transition_live_readback": opl_transition_readback(
            study_id=study_id,
            action_fingerprint=fingerprint,
            work_unit_id=work_unit_id,
            route_identity_key=idempotency_key,
            attempt_idempotency_key=idempotency_key,
            request_idempotency_key=idempotency_key,
            stage_run_id=f"stage-run:{study_id}:{work_unit_id}",
        ),
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_opl_runtime_owner_route",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[candidate],
        managed_study_progress_currentness={},
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
    )

    action = result["managed_study_actions"][0]
    assert action["decision"] == "pending_provider_admission"
    assert action["reason"] == "provider_admission_pending"
    assert action["running_provider_attempt"] is False
    assert action["provider_admission_state"]["status"] == "pending"
    [admission] = action["provider_admission_candidates"]
    assert admission["status"] == "provider_admission_pending"
    assert admission["route_identity_key"] == idempotency_key
    assert admission["attempt_idempotency_key"] == idempotency_key
    assert admission["work_unit_id"] == work_unit_id
    assert result["provider_admission_pending_count"] == 1

def test_runtime_report_consumes_terminal_owner_receipt_over_matching_transition_request() -> None:
    report_aggregation = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.report_aggregation"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "publication-blockers::0915410f804b3697"
    owner_receipt_ref = (
        "/workspace/studies/003/artifacts/controller/repair_execution_receipts/latest.json"
    )
    transition_request = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "transition_request_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_quality_repair_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "next_executable_owner": "write",
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
    }

    result = report_aggregation.build_runtime_report(
        runtime_root=Path("/workspace/runtime/quests"),
        scanned=[study_id],
        reports=[],
        managed_study_actions=[
            {
                "study_id": study_id,
                "decision": "blocked",
                "reason": "quest_waiting_for_user",
            }
        ],
        managed_study_auto_recoveries=[],
        managed_study_recovery_holds=[],
        managed_study_outer_loop_dispatches=[],
        managed_study_outer_loop_wakeup_audits=[],
        managed_study_no_op_suppressions=[],
        managed_study_opl_runtime_owner_handoffs=[],
        managed_study_opl_provider_admission_candidates=[],
        managed_study_progress_currentness={
            study_id: {
                "study_id": study_id,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "owner_receipt_recorded",
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "owner_receipt_recorded",
                        "owner_receipt_ref": owner_receipt_ref,
                    },
                    "required_output_contract": {
                        "owner_receipt_consumed": True,
                        "owner_receipt_ref": owner_receipt_ref,
                        "provider_completion_is_domain_completion": False,
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "owner_receipt_recorded",
                    "owner": "write",
                    "next_work_unit": None,
                    "typed_blocker": None,
                    "parked_state": None,
                },
                "current_executable_owner_action": None,
            }
        },
        managed_study_autonomy_slo_statuses=[],
        managed_study_autonomy_repair_actions=[],
        managed_study_opl_transition_request_candidates=[transition_request],
    )

    assert result["transition_request_pending_count"] == 0
    assert result["managed_study_opl_transition_request_candidates"] == []
    assert result["provider_admission_pending_count"] == 0
    action = result["managed_study_actions"][0]
    assert action["decision"] == "owner_receipt_recorded"
    assert action.get("current_executable_owner_action") is None
    assert action["current_work_unit"]["status"] == "owner_receipt_recorded"
