from __future__ import annotations

import importlib

from tests.study_runtime_test_helpers import make_profile, write_study

from .shared import _write_json


def _write_ready_quality_repair_dispatch(study_root, *, study_id: str, fingerprint: str) -> None:
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_quality_repair_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "dispatch_authority": "quality_repair_batch_writer_handoff",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_quality_repair_batch",
            "next_executable_owner": "write",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "medical_prose_write_repair",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "required_output_surface": "artifacts/controller/quality_repair_batch/latest.json",
            "owner_route": {
                "next_owner": "write",
                "allowed_actions": ["run_quality_repair_batch"],
                "source_refs": {
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                    "owner_route_currentness_basis": {
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "truth_epoch": "truth::current",
                        "runtime_health_epoch": "runtime::current",
                    },
                },
            },
        },
    )


def _quality_repair_handoff(*, study_id: str, fingerprint: str) -> dict:
    return {
        "surface_kind": "opl_current_control_state_handoff",
        "source_path": "/tmp/opl_current_control_state/latest.json",
        "running_provider_attempt": False,
        "action_queue": [
            {
                "source_surface": "opl_current_control_state.action_queue",
                "status": "queued",
                "study_id": study_id,
                "quest_id": study_id,
                "action_type": "run_quality_repair_batch",
                "owner": "write",
                "next_executable_owner": "write",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "provider_attempt_or_lease_required": True,
                "provider_completion_is_domain_completion": False,
                "owner_route": {
                    "next_owner": "write",
                    "allowed_actions": ["run_quality_repair_batch"],
                    "source_refs": {
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "owner_route_currentness_basis": {
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": fingerprint,
                            "truth_epoch": "truth::current",
                            "runtime_health_epoch": "runtime::current",
                        },
                    },
                },
            }
        ],
    }


def _quality_repair_current_work_unit(*, study_id: str, fingerprint: str, status: str) -> dict:
    return {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": status,
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "write",
        "action_type": "run_quality_repair_batch",
        "work_unit_id": "medical_prose_write_repair",
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "state": {
            "state_kind": status,
            "typed_blocker": {
                "blocker_type": "medical_publication_surface_blocked",
                "owner": "write",
                "action_type": "run_quality_repair_batch",
                "work_unit_id": "medical_prose_write_repair",
                "work_unit_fingerprint": fingerprint,
            }
            if status == "typed_blocker"
            else None,
        },
    }


def test_provider_admission_projection_clears_candidates_under_typed_blocker(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="typed_blocker",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "medical_publication_surface_blocked",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields == {
        "provider_admission_pending_count": 0,
        "provider_admission_candidates": [],
    }


def test_provider_admission_projection_emits_candidate_for_current_executable_action(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="executable_owner_action",
            ),
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "write",
                "next_work_unit": "medical_prose_write_repair",
            },
        },
        handoff=_quality_repair_handoff(study_id=study_id, fingerprint=fingerprint),
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    assert len(fields["provider_admission_candidates"]) == 1
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["action_type"] == "run_quality_repair_batch"
    assert candidate["work_unit_id"] == "medical_prose_write_repair"
    assert candidate["work_unit_fingerprint"] == fingerprint
    assert candidate["next_executable_owner"] == "write"


def test_existing_projection_refresh_clears_stale_provider_admission_on_no_current_action(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "publication-blockers::0915410f804b3697"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(study_root, study_id=study_id, fingerprint=fingerprint)
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [{"status": "stale"}],
            "current_work_unit": _quality_repair_current_work_unit(
                study_id=study_id,
                fingerprint=fingerprint,
                status="typed_blocker",
            ),
            "current_execution_envelope": {
                "state_kind": "typed_blocker",
                "owner": "write",
                "typed_blocker": {
                    "blocker_type": "medical_publication_surface_blocked",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": fingerprint,
                },
            },
            "opl_current_control_state_handoff": _quality_repair_handoff(
                study_id=study_id,
                fingerprint=fingerprint,
            ),
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []


def test_existing_projection_refresh_prefers_live_attempt_over_stale_handoff(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:446e24afa9bc729b3fc0f43184024d2c95ddbcf71db0d8db0183e4c42467ee30"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "runtime_liveness_audit": {
                "source": "opl_current_control_state_provider_attempt",
                "active_run_id": "opl-stage-attempt://sat-live-gate-replay",
                "active_stage_attempt_id": "sat-live-gate-replay",
                "active_workflow_id": "wf-live-gate-replay",
                "running_provider_attempt": True,
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                    "provider_status": "running",
                },
                "stage_progress_log": {
                    "surface_kind": "temporal_workflow_stage_progress_log",
                    "attempt_refs": ["sat-live-gate-replay"],
                },
            },
            "progress_projection": {
                "study_id": study_id,
                "provider_admission_pending_count": 1,
                "provider_admission_candidates": [{"status": "stale"}],
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_type": "executed",
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "typed_blocker": {"blocker_type": "executed", "owner": "one-person-lab"},
                },
                "opl_current_control_state_handoff": {
                    "surface_kind": "opl_current_control_state_study_handoff",
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "blocked_reason": "provider_admission_current_control_state_required",
                    "next_owner": "one-person-lab",
                    "action_queue": [
                        {
                            "status": "queued",
                            "study_id": study_id,
                            "quest_id": study_id,
                            "owner": "gate_clearing_batch",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                        }
                    ],
                },
            },
        },
        materialize_read_model_artifacts=False,
    )

    assert result["active_run_id"] == "opl-stage-attempt://sat-live-gate-replay"
    assert result["active_stage_attempt_id"] == "sat-live-gate-replay"
    assert result["active_workflow_id"] == "wf-live-gate-replay"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["current_work_unit"]["status"] == "running_provider_attempt"
    assert result["current_execution_envelope"]["state_kind"] == "running_provider_attempt"


def test_existing_projection_refresh_rejects_superseded_live_attempt_identity(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    current_fingerprint = "sha256:current-publication-gate-replay"
    stale_fingerprint = "sha256:stale-publication-gate-replay"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module.build_study_progress_projection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
        status_payload={
            "study_id": study_id,
            "runtime_liveness_audit": {
                "source": "opl_current_control_state_provider_attempt",
                "active_run_id": "opl-stage-attempt://sat-stale-gate-replay",
                "active_stage_attempt_id": "sat-stale-gate-replay",
                "active_workflow_id": "wf-stale-gate-replay",
                "running_provider_attempt": True,
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": stale_fingerprint,
                "action_fingerprint": stale_fingerprint,
                "runtime_health": {
                    "health_status": "running",
                    "runtime_liveness_status": "live",
                    "provider_status": "running",
                },
            },
            "progress_projection": {
                "study_id": study_id,
                "current_executable_owner_action": {
                    "surface_kind": "current_executable_owner_action",
                    "status": "ready",
                    "next_owner": "gate_clearing_batch",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "action_fingerprint": current_fingerprint,
                },
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "status": "typed_blocker",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "one-person-lab",
                    "action_type": "run_gate_clearing_batch",
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": current_fingerprint,
                    "action_fingerprint": current_fingerprint,
                    "state": {
                        "state_kind": "typed_blocker",
                        "typed_blocker": {
                            "blocker_type": "executed",
                            "owner": "one-person-lab",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": current_fingerprint,
                        },
                    },
                },
                "current_execution_envelope": {
                    "state_kind": "typed_blocker",
                    "owner": "one-person-lab",
                    "typed_blocker": {
                        "blocker_type": "executed",
                        "owner": "one-person-lab",
                        "action_type": "run_gate_clearing_batch",
                        "work_unit_id": "publication_gate_replay",
                        "work_unit_fingerprint": current_fingerprint,
                    },
                },
                "opl_current_control_state_handoff": {
                    "surface_kind": "opl_current_control_state_study_handoff",
                    "running_provider_attempt": False,
                    "active_run_id": None,
                    "next_owner": "one-person-lab",
                    "blocked_reason": "executed",
                    "action_queue": [],
                },
            },
        },
        materialize_read_model_artifacts=False,
    )

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["running_provider_attempt"] is True
    assert handoff["work_unit_fingerprint"] == stale_fingerprint
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_run_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat-stale-gate-replay"
    )
    assert result["active_run_id"] is None
