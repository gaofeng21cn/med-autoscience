from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def _supervisor_decision(decision: str) -> dict:
    return {
        "surface_kind": "paper_autonomy_supervisor_decision",
        "decision": decision,
        "identity_match": True,
        "paper_autonomy_obligation": {
            "surface_kind": "paper_autonomy_obligation",
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "stage_id": "publication_supervision",
            "action_type": "run_quality_repair_batch",
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            "route_identity_key": "provider-admission::003-dpcc::0915410f804b3697",
            "attempt_idempotency_key": "provider-admission::003-dpcc::0915410f804b3697",
        },
        "evidence_refs": [
            "provider-admission::003-dpcc::0915410f804b3697",
            "stage-run-identity::003-dpcc::0915410f804b3697",
        ],
        "missing_evidence_refs": [],
    }


def test_progress_first_monitoring_honors_current_control_executable_handoff_over_stale_gate_replay() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    gate_fingerprint = "sha256:bfcf03bacdcb4e58edd085444dda2f3906814c8a1806afb63b8095b90408bac9"
    repair_fingerprint = "publication-blockers::0915410f804b3697"
    action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "gate_clearing_batch_followthrough.actionable_current_work_unit",
        "next_owner": "write",
        "action_type": "run_quality_repair_batch",
        "allowed_actions": ["run_quality_repair_batch"],
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": repair_fingerprint,
        "action_fingerprint": repair_fingerprint,
        "owner_receipt_required": True,
    }

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": study_id,
            "quest_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": repair_fingerprint,
                "action_fingerprint": repair_fingerprint,
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
            "current_executable_owner_action": action,
            "repair_progress_projection": {
                "surface_kind": "repair_progress_projection",
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "gate_replay_done": True,
                "ai_reviewer_recheck_done": True,
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "running_provider_attempt": False,
                "blocked_reason": "publication_gate_replay_blocked",
                "next_owner": "publication_gate",
                "typed_blocker": {
                    "blocker_type": "publication_gate_replay_blocked",
                    "owner": "publication_gate",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": gate_fingerprint,
                    "action_fingerprint": gate_fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": repair_fingerprint,
                    "action_fingerprint": repair_fingerprint,
                },
                "current_execution_envelope": {
                    "state_kind": "executable_owner_action",
                    "owner": "write",
                    "next_work_unit": "medical_prose_write_repair",
                },
                "current_executable_owner_action": action,
            },
        }
    )

    assert monitoring["current_executable_owner_action"] == action
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"] == "provider_admission_candidate_absent"
    assert admission["hard_gate_blocked"] is False
    assert admission["next_owner"] == "write"
    assert admission["work_unit_id"] == "medical_prose_write_repair"


def test_progress_first_monitoring_requires_running_provider_proof_for_current_write_action_without_queue_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "one-person-lab",
                "active_run_id": "opl-stage-attempt://sat-stale-gate",
                "active_stage_attempt_id": "sat-stale-gate",
                "active_workflow_id": "wf-stale-gate",
                "runtime_health": {"runtime_liveness_status": "live"},
                "action_queue": [],
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-stale-gate"
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["next_owner"] == "write"
    assert monitoring["controller_action"] == "run_quality_repair_batch"
    assert monitoring["next_work_unit"] == "medical_prose_write_repair"
    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"] == "provider_admission_candidate_absent"
    assert admission["provider_attempt_running_proven"] is False
    assert admission["provider_attempt_proof"] is None


def test_progress_first_monitoring_blocks_owner_action_admission_under_supervisor_wait_decision() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "human_gate",
                "supervisor_decision": _supervisor_decision("wait_for_owner_with_resume_token"),
            },
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "action_queue": [
                    {
                        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    }
                ],
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"]["paper_autonomy_supervisor_decision"]["decision"] == (
        "wait_for_owner_with_resume_token"
    )
    assert admission["hard_gate_reasons"] == ["paper_autonomy_supervisor_decision"]


def test_progress_first_monitoring_execute_decision_allows_owner_action_admission() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "paper_recovery_state": {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "supervisor_decision": _supervisor_decision("execute_current_owner_delta"),
            },
            "current_work_unit": {
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "action_queue": [],
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"] == "provider_admission_candidate_absent"


def test_progress_first_monitoring_suppresses_running_current_work_unit_when_owner_action_unbound() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_work_unit": {
                "status": "running_provider_attempt",
                "owner": "supervisor_only/live_provider_attempt",
                "work_unit_id": "medical_prose_write_repair",
                "state": {
                    "state_kind": "running_provider_attempt",
                    "provider_attempt_proof": {
                        "running_provider_attempt": True,
                        "active_run_id": "opl-stage-attempt://sat-stale-ai-reviewer",
                        "active_stage_attempt_id": "sat-stale-ai-reviewer",
                        "active_workflow_id": "wf-stale-ai-reviewer",
                    },
                },
            },
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "owner_receipt_required": True,
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "supervisor_only/live_provider_attempt",
                "active_run_id": "opl-stage-attempt://sat-stale-ai-reviewer",
                "active_stage_attempt_id": "sat-stale-ai-reviewer",
                "active_workflow_id": "wf-stale-ai-reviewer",
                "runtime_health": {
                    "health_status": "live",
                    "runtime_liveness_status": "live",
                },
                "action_queue": [],
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat-stale-ai-reviewer"
    )
    assert monitoring["execution_state_kind"] == "executable_owner_action"
    assert monitoring["current_executable_owner_action"]["work_unit_id"] == "medical_prose_write_repair"
    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"] == "provider_admission_candidate_absent"
    assert admission["provider_attempt_running_proven"] is False
    assert admission["provider_attempt_proof"] is None


def test_progress_first_monitoring_keeps_paper_line_owner_delta_and_platform_repair_accounting_separate() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    paper_line_monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "progress_first_sprint_state": {
                "classification": "deliverable_progress",
                "paper_progress_delta_counted": True,
                "platform_repair_delta_counted": False,
                "deliverable_progress_delta": {
                    "count": 1,
                    "owner_receipt_refs": [
                        "artifacts/controller/gate_clearing_batch/latest.json#owner_receipt"
                    ],
                },
                "platform_repair_delta": {"count": 0},
            },
        }
    )

    assert paper_line_monitoring["progress_delta_classification"] == "deliverable_progress"
    assert paper_line_monitoring["paper_progress_delta_counted"] is True
    assert paper_line_monitoring["platform_repair_delta_counted"] is False

    platform_repair_monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["produce_publication_eval"],
            },
            "progress_first_sprint_state": {
                "classification": "platform_repair",
                "paper_progress_delta_counted": False,
                "platform_repair_delta_counted": True,
                "deliverable_progress_delta": {"count": 0},
                "platform_repair_delta": {
                    "count": 1,
                    "refs": ["runtime/artifacts/supervision/opl_current_control_state/latest.json#read_model_hygiene"],
                },
            },
            "opl_current_control_state_handoff": {
                "stage_progress_log": {
                    "attempt_count": 1,
                    "missing_usage_telemetry_attempt_count": 1,
                    "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
                },
            },
        }
    )

    assert platform_repair_monitoring["progress_delta_classification"] == "platform_repair"
    assert platform_repair_monitoring["paper_progress_delta_counted"] is False
    assert platform_repair_monitoring["platform_repair_delta_counted"] is True
    assert platform_repair_monitoring["owner_action_admission"]["admission_requested"] is True
    assert platform_repair_monitoring["owner_action_admission"]["hard_gate_blocked"] is False
    assert platform_repair_monitoring["owner_action_admission"]["observability_diagnostics"] == [
        {
            "diagnostic": "missing_usage_telemetry",
            "authority": "observability_only",
            "attempt_count": 1,
            "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
        }
    ]


def test_progress_first_monitoring_treats_missing_telemetry_and_closeout_as_observability_diagnostics_not_admission_gates() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "ai_reviewer",
                "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                "allowed_actions": ["produce_publication_eval"],
            },
            "opl_current_control_state_handoff": {
                "stage_progress_log": {
                    "attempt_count": 1,
                    "missing_usage_telemetry_attempt_count": 1,
                    "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
                },
                "latest_terminal_stage_log": {
                    "stage_attempt_id": "sat-closeout-missing",
                    "status": "completed",
                    "missing_user_stage_log_fields": [
                        "stage_work_done",
                        "paper_work_done",
                        "changed_stage_surfaces",
                        "changed_paper_surfaces",
                        "progress_delta_classification",
                    ],
                    "missing_observability_fields": ["duration", "token_usage", "cost"],
                },
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["blocked_by"] == "provider_admission_candidate_absent"
    assert admission["hard_gate_blocked"] is False
    assert admission["hard_gate_reasons"] == []
    assert admission["observability_diagnostics"] == [
        {
            "diagnostic": "missing_usage_telemetry",
            "authority": "observability_only",
            "attempt_count": 1,
            "attempt_refs": ["runtime/stage_attempts/sat-telemetry-missing.json"],
        },
        {
            "diagnostic": "terminal_closeout_observability_incomplete",
            "authority": "observability_only",
            "stage_attempt_id": "sat-closeout-missing",
            "missing_user_stage_log_fields": [
                "stage_work_done",
                "paper_work_done",
                "changed_stage_surfaces",
                "changed_paper_surfaces",
                "progress_delta_classification",
            ],
            "missing_observability_fields": ["duration", "token_usage", "cost"],
        },
    ]


__all__ = [name for name in globals() if name.startswith("test_")]
