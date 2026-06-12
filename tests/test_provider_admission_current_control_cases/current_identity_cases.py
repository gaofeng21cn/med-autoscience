from __future__ import annotations

import importlib
from pathlib import Path

from tests.test_domain_health_diagnostic_cases.shared import dump_json


def test_provider_admission_current_control_prefers_live_attempt_over_pending_candidate(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control"
    )
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "dpcc_publication_gate_replay_after_current_ai_reviewer_record"
    action_fingerprint = (
        "current-ai-reviewer-gate-replay::003-dpcc-primary-care-phenotype-treatment-gap::"
        "dpcc_publication_gate_replay_after_current_ai_reviewer_record::"
        "publication-eval::003-dpcc-primary-care-phenotype-treatment-gap::"
        "ai-reviewer-record::20260610T155750Z::sat_619d680b6dc5c74022af4a3b"
    )
    candidate = {
        "surface": "opl_provider_admission_candidate",
        "schema_version": 1,
        "status": "provider_admission_pending",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_path": (
            "/workspace/studies/003-dpcc-primary-care-phenotype-treatment-gap/"
            "artifacts/supervision/consumer/default_executor_dispatches/run_gate_clearing_batch.json"
        ),
        "next_executable_owner": "finalize",
        "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        "provider_attempt_or_lease_required": True,
        "provider_completion_is_domain_completion": False,
        "currentness_basis": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": action_fingerprint,
            "truth_epoch": "truth-event-000032-097fe584ce2a78fb",
            "runtime_health_epoch": "runtime-health-event-006579-e40441bd3cd1029f",
        },
    }
    live_attempt = {
        "surface_kind": "opl_current_control_state_provider_attempt",
        "source": "opl_family_runtime_attempt_inspect",
        "active_run_id": "opl-stage-attempt://sat-live",
        "active_stage_attempt_id": "sat-live",
        "active_workflow_id": "wf-live",
        "running_provider_attempt": True,
        "runtime_owner": "one-person-lab",
        "provider_attempt_owner": "one-person-lab",
        "queue_owner": "one-person-lab",
        "task_id": "frt-live",
        "task_kind": "domain_owner/default-executor-dispatch",
        "provider_kind": "temporal",
        "action_type": "run_gate_clearing_batch",
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": action_fingerprint,
        "action_fingerprint": action_fingerprint,
        "dispatch_ref": candidate["dispatch_path"],
        "current_attempt_state": "running",
        "provider_run": {
            "provider_status": "running",
            "workflow_id": "wf-live",
            "last_heartbeat_at": "2026-06-10T17:17:28Z",
        },
        "runtime_health": {
            "health_status": "running",
            "runtime_liveness_status": "live",
            "provider_status": "running",
            "summary": "OPL family-runtime has a live provider-backed stage attempt for this study.",
        },
    }

    result = module.materialize_provider_admission_current_control_state(
        profile=profile,
        candidates=[candidate],
        generated_at="2026-06-10T17:18:00+00:00",
        apply=False,
        scanned_studies=[
            {
                "study_id": study_id,
                "quest_id": study_id,
                "handoff_scan_status": "scanned_no_provider_admission",
                "provider_admission_pending_count": 0,
                "action_queue": [],
                "opl_provider_attempt": live_attempt,
                "current_execution_envelope": {
                    "state_kind": "running_provider_attempt",
                    "owner": "supervisor_only/live_provider_attempt",
                    "next_work_unit": work_unit_id,
                    "typed_blocker": None,
                    "parked_state": None,
                    "source": "opl_provider_attempt",
                },
            }
        ],
    )

    assert result is not None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["queue_history"]["provider_admission_pending_count"] == 0
    assert result["action_queue"] == []
    study = result["studies"][0]
    assert study["study_id"] == study_id
    assert study["running_provider_attempt"] is True
    assert study["active_stage_attempt_id"] == "sat-live"
    assert study["active_workflow_id"] == "wf-live"
    assert study["provider_admission_pending_count"] == 0
    assert study["current_execution_envelope"]["state_kind"] == "running_provider_attempt"
    assert result["current_execution_envelopes"][study_id]["state_kind"] == "running_provider_attempt"
    assert result["stage_route_arbiter"]["decision_counts"] == {
        "running_identity_observed": 1,
    }
    decision = result["stage_route_arbiter_decisions"][0]
    assert decision["decision"] == "running_identity_observed"
    assert decision["effect"] == "suppress_provider_admission_pending"
    assert decision["study_id"] == study_id
    assert decision["action_type"] == "run_gate_clearing_batch"
    assert decision["work_unit_id"] == work_unit_id
    assert decision["work_unit_fingerprint"] == action_fingerprint
    assert decision["active_stage_attempt_id"] == "sat-live"
    assert decision["active_workflow_id"] == "wf-live"
    assert decision["authority_boundary"] == {
        "arbiter_surface": "currentness_projection_only",
        "can_write_domain_truth": False,
        "can_authorize_publication_ready": False,
        "provider_completion_is_domain_ready": False,
    }


def test_provider_admission_prefers_canonical_current_work_unit_over_stale_current_action(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    study_root = tmp_path / "studies" / study_id
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    action_fingerprint = "sha256:current-canonical-gate-replay"
    work_unit_id = "publication_gate_replay"
    dump_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "dispatch_status": "ready",
            "dispatch_authority": "consumer_default_executor_dispatch",
            "next_executable_owner": "gate_clearing_batch",
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
            "action_fingerprint": "sha256:stale-dispatch-fingerprint",
            "refs": {"dispatch_path": str(dispatch_path)},
        },
    )

    result = provider_admission.current_control_provider_admission_candidates(
        {
            "surface": "opl_current_control_state_handoff",
            "action_queue": [
                {
                    "study_id": study_id,
                    "quest_id": study_id,
                    "action_type": "run_gate_clearing_batch",
                    "status": "queued",
                    "owner": "gate_clearing_batch",
                    "next_work_unit": work_unit_id,
                    "action_fingerprint": action_fingerprint,
                    "refs": {"dispatch_path": str(dispatch_path)},
                }
            ],
            "studies": [],
        },
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": action_fingerprint,
                "action_fingerprint": action_fingerprint,
                "currentness_basis": {
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": action_fingerprint,
                },
                "state": {
                    "source": "canonical_current_work_unit",
                },
            },
            "current_executable_owner_action": {
                "source": "stale_projection",
                "next_owner": "ai_reviewer",
                "action_type": "return_to_ai_reviewer_workflow",
                "work_unit_id": "stale_ai_reviewer_recheck",
                "work_unit_fingerprint": "sha256:stale-current-action",
                "allowed_actions": ["return_to_ai_reviewer_workflow"],
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": work_unit_id,
                "typed_blocker": None,
            },
        },
        current_control_ref="/workspace/runtime/artifacts/supervision/opl_current_control_state/latest.json",
    )

    assert len(result) == 1
    candidate = result[0]
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == work_unit_id
    assert candidate["action_fingerprint"] == action_fingerprint


def test_provider_admission_rejects_same_fingerprint_with_stale_action_identity(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch_path = tmp_path / "dispatches" / "return_to_ai_reviewer_workflow.json"
    current_fingerprint = "sha256:current-gate-clearing"
    execution = {
        "source": "default_executor_execution",
        "execution_status": "handoff_ready",
        "study_id": study_id,
        "quest_id": study_id,
        "action_type": "return_to_ai_reviewer_workflow",
        "dispatch_path": str(dispatch_path),
        "dispatch_authority": "ai_reviewer_record_production_handoff",
        "next_executable_owner": "ai_reviewer",
        "provider_attempt_or_lease_required": True,
        "owner_route_current": True,
        "action_fingerprint": current_fingerprint,
        "owner_route": {
            "source_refs": {
                "work_unit_id": "stale_ai_reviewer_recheck",
                "work_unit_fingerprint": current_fingerprint,
            }
        },
    }

    candidate = provider_admission.provider_admission_candidate_from_execution(
        execution,
        execution_ref="runtime/artifacts/supervision/consumer/default_executor_execution/latest.json",
        status_study_id=study_id,
        current_action_identity={
            "action_ids": ["run_gate_clearing_batch", "publication_gate_replay"],
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": current_fingerprint,
            "work_unit_fingerprints": [current_fingerprint],
        },
    )

    assert candidate is None


def test_provider_admission_execution_requires_current_identity_for_current_control_status(
    tmp_path: Path,
) -> None:
    provider_admission = importlib.import_module(
        "med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission"
    )
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    dispatch_path = tmp_path / "dispatches" / "run_gate_clearing_batch.json"
    action_fingerprint = "sha256:stale-persisted-default-executor"
    execution_payload = {
        "surface": "domain_owner_action_dispatch",
        "executions": [
            {
                "source": "default_executor_execution",
                "execution_status": "handoff_ready",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_gate_clearing_batch",
                "dispatch_path": str(dispatch_path),
                "dispatch_authority": "consumer_default_executor_dispatch",
                "next_executable_owner": "gate_clearing_batch",
                "provider_attempt_or_lease_required": True,
                "owner_route_current": True,
                "action_fingerprint": action_fingerprint,
                "owner_route": {
                    "source_refs": {
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": action_fingerprint,
                    }
                },
            }
        ],
    }

    candidates = provider_admission.provider_admission_candidates_from_execution_payload(
        execution_payload,
        execution_ref="runtime/artifacts/supervision/consumer/default_executor_execution/latest.json",
        status_payload={
            "study_id": study_id,
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "opl_current_control_state_handoff": {
                "surface": "opl_current_control_state_handoff",
                "action_queue": [
                    {
                        "study_id": study_id,
                        "action_type": "run_gate_clearing_batch",
                        "status": "queued",
                    }
                ],
            },
        },
    )

    assert candidates == []
