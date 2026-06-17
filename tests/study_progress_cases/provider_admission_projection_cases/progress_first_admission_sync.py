from __future__ import annotations

import importlib


def test_sync_progress_first_owner_action_admission_suppresses_stale_identity() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.payload_sync"
    )

    result = module.sync_progress_first_owner_action_admission(
        {
            "current_work_unit": {
                "status": "running_provider_attempt",
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": "sha256:current-gate-replay",
                "action_fingerprint": "sha256:current-gate-replay",
            },
            "current_execution_envelope": {
                "state_kind": "running_provider_attempt",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_requested": True,
                    "admission_pending": True,
                    "provider_attempt_start_requested": True,
                    "provider_attempt_running_proven": False,
                    "next_owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "allowed_actions": ["run_quality_repair_batch"],
                }
            },
        }
    )

    admission = result["owner_action_admission"]
    assert admission["admission_requested"] is False
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["blocked_by"] == "current_execution_identity_mismatch"
    assert admission["stale_admission_suppressed"] is True
    assert admission["admission_authority_boundary"] == {
        "surface_role": "mas_policy_admission_projection",
        "mas_role": "owner_action_policy_projection_and_monitoring",
        "runtime_owner": "one-person-lab",
        "provider_admission_authority_owner": "one-person-lab",
        "admission_requested_is_authority": False,
        "admission_pending_requires_opl_readback": True,
        "provider_attempt_running_requires_opl_liveness_proof": True,
        "can_authorize_provider_admission": False,
        "can_start_provider_attempt": False,
        "can_create_attempt": False,
        "can_create_outbox_record": False,
        "can_generate_next_action": False,
        "can_claim_runtime_currentness": False,
        "can_claim_stage_progress": False,
        "missing_candidate_outcome": "provider_admission_candidate_absent",
        "replacement_owner_surface": "OPL DomainProgressTransitionRuntime / StageRun provider admission",
    }
    monitoring = result["progress_first_monitoring_summary"]["owner_action_admission"]
    assert monitoring == admission


def test_sync_progress_first_owner_action_admission_rebuilds_after_provider_candidate_cleared() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.projection_payload_assembly_parts.payload_sync"
    )

    result = module.sync_progress_first_owner_action_admission(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "write",
                "action_type": "run_quality_repair_batch",
                "allowed_actions": ["run_quality_repair_batch"],
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                "action_fingerprint": "publication-blockers::0915410f804b3697",
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": False,
                },
            },
            "provider_admission_pending_count": 0,
            "provider_admission_candidates": [],
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "provider_admission_pending_count": 0,
                "provider_admission_candidates": [],
                "action_queue": [],
                "next_owner": "write",
            },
            "progress_first_monitoring_summary": {
                "owner_action_admission": {
                    "admission_requested": True,
                    "admission_pending": True,
                    "provider_attempt_start_requested": True,
                    "provider_attempt_running_proven": False,
                    "candidate_present": True,
                    "next_owner": "write",
                    "work_unit_id": "medical_prose_write_repair",
                    "allowed_actions": ["run_quality_repair_batch"],
                }
            },
        }
    )

    admission = result["owner_action_admission"]
    assert admission["admission_requested"] is True
    assert admission["admission_pending"] is False
    assert admission["provider_attempt_start_requested"] is False
    assert admission["provider_attempt_running_proven"] is False
    assert admission["candidate_present"] is False
    assert admission["blocked_by"] == "provider_admission_candidate_absent"
    boundary = admission["admission_authority_boundary"]
    assert boundary["surface_role"] == "mas_policy_admission_projection"
    assert boundary["admission_requested_is_authority"] is False
    assert boundary["admission_pending_requires_opl_readback"] is True
    assert boundary["provider_attempt_running_requires_opl_liveness_proof"] is True
    assert boundary["can_authorize_provider_admission"] is False
    assert boundary["can_start_provider_attempt"] is False
    assert boundary["can_create_outbox_record"] is False
    assert boundary["can_generate_next_action"] is False
    assert boundary["replacement_owner_surface"] == (
        "OPL DomainProgressTransitionRuntime / StageRun provider admission"
    )
    assert result["progress_first_monitoring_summary"]["owner_action_admission"] == admission
