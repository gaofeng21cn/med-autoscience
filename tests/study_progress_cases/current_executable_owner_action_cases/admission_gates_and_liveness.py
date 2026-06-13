from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_blocks_owner_action_admission_on_hard_gate_forbidden_write_and_missing_callable() -> None:
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
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "interaction_arbitration": {
                "classification": "human_gate",
                "requires_user_input": True,
                "blocked_reason": "needs_physician_decision",
            },
            "execution_owner_guard": {
                "supervisor_only": True,
                "forbidden_write_refs": ["runtime/current_execution_envelope.json"],
            },
            "owner_callable_surface": {
                "status": "missing",
                "reason_code": "owner_callable_surface_missing",
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_blocked"] is True
    assert admission["hard_gate_reasons"] == [
        "human_gate_required",
        "forbidden_write_refs",
        "owner_callable_surface_missing",
    ]
    assert admission["blocked_by"] == {
        "human_gate": {
            "requires_user_input": True,
            "blocked_reason": "needs_physician_decision",
        },
        "forbidden_write_refs": ["runtime/current_execution_envelope.json"],
        "owner_callable_surface": {
            "status": "missing",
            "reason_code": "owner_callable_surface_missing",
        },
    }

def test_progress_first_monitoring_blocks_owner_action_admission_on_existing_owner_callable_missing_surfaces() -> None:
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
            "interaction_arbitration": {
                "classification": "blocked_closeout_owner_redrive",
                "action": "resume",
                "requires_user_input": False,
                "blocked_reason": "owner_callable_surface_missing",
            },
            "current_execution_envelope": {
                "typed_blocker": {
                    "blocker_id": "owner_callable_surface_missing",
                    "owner": "ai_reviewer",
                },
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_started"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["hard_gate_reasons"] == ["owner_callable_surface_missing"]
    assert admission["blocked_by"]["owner_callable_surface"] == {
        "status": "missing",
        "reason_code": "owner_callable_surface_missing",
        "sources": [
            "interaction_arbitration.blocked_reason",
            "current_execution_envelope.typed_blocker",
        ],
    }

def test_progress_first_monitoring_distinguishes_admission_request_from_running_provider_proof() -> None:
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
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "allowed_actions": ["run_quality_repair_batch"],
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "write",
                "active_stage_attempt_id": "sat-running",
                "active_workflow_id": "wf-running",
                "action_queue": [
                    {
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                    }
                ],
            },
        }
    )

    admission = monitoring["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is True
    assert admission["provider_attempt_started"] is True
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_proof"] == {
        "running_provider_attempt": True,
        "active_stage_attempt_id": "sat-running",
        "active_run_id": None,
        "active_workflow_id": "wf-running",
    }

def test_progress_first_monitoring_keeps_stale_active_run_id_out_of_running_fields() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "active_run_id": "opl-stage-attempt://sat-stale",
            "supervision": {"active_run_id": "opl-stage-attempt://sat-stale"},
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "opl_current_control_state_handoff": {
                "active_run_id": None,
                "active_stage_attempt_id": None,
                "active_workflow_id": None,
                "running_provider_attempt": False,
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-stale"
    assert monitoring["owner_action_admission"]["admission_pending"] is True
    assert monitoring["owner_action_admission"]["provider_attempt_started"] is False

def test_progress_first_monitoring_keeps_handoff_active_run_ref_out_of_running_fields_without_running_provider_proof() -> None:
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
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
            "opl_current_control_state_handoff": {
                "active_run_id": "opl-stage-attempt://sat-handoff-ref",
                "active_stage_attempt_id": "sat-not-running",
                "active_workflow_id": "wf-not-running",
                "running_provider_attempt": False,
            },
        }
    )

    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["active_workflow_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-handoff-ref"
    assert monitoring["owner_action_admission"]["provider_attempt_running_proven"] is False
    assert monitoring["owner_action_admission"]["provider_attempt_started"] is False


def test_progress_first_monitoring_keeps_running_provider_proof_when_handoff_identity_matches_without_queue() -> None:
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
                "source": "publication_eval.recommended_actions.readiness_blocker_repair",
                "next_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": True,
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "active_run_id": "opl-stage-attempt://sat-current",
                "active_stage_attempt_id": "sat-current",
                "active_workflow_id": "wf-current",
                "runtime_health": {"runtime_liveness_status": "live"},
                "action_queue": [],
            },
        }
    )

    assert monitoring["running_provider_attempt"] is True
    assert monitoring["active_run_id"] == "opl-stage-attempt://sat-current"
    assert monitoring["active_stage_attempt_id"] == "sat-current"
    admission = monitoring["owner_action_admission"]
    assert admission["provider_attempt_running_proven"] is True
    assert admission["provider_attempt_proof"]["active_stage_attempt_id"] == "sat-current"


__all__ = [name for name in globals() if name.startswith("test_")]
