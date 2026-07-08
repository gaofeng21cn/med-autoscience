from __future__ import annotations

import importlib

from tests.provider_admission_current_control_helpers import opl_transition_readback
from tests.study_runtime_test_helpers import make_profile, write_study
from tests.study_progress_cases.shared import _write_json
from tests.study_progress_cases.provider_admission_projection import (
    _opl_transition_result,
    _quality_repair_current_work_unit,
    _quality_repair_handoff,
    _write_ready_quality_repair_dispatch,
)


def test_provider_admission_projection_uses_current_work_unit_pending_identity(tmp_path) -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.provider_admission_projection"
    )
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    _write_ready_quality_repair_dispatch(
        study_root,
        study_id=study_id,
        fingerprint=fingerprint,
    )
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "opl_domain_progress_transition_result": _opl_transition_result(
                study_id=study_id,
                work_unit_id="publication_gate_replay",
                fingerprint=fingerprint,
                stage_run_id="stage-run-gate-replay",
            ),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    )

    fields = module.provider_admission_projection_fields(
        payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "target_surface": {
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
        },
        handoff={
            "surface_kind": "opl_current_control_state_study_handoff",
            "source_path": "/tmp/opl_current_control_state/latest.json",
            "running_provider_attempt": False,
            "studies": [
                {
                    "study_id": study_id,
                    "current_executable_owner_action": {
                        "surface_kind": "current_executable_owner_action",
                        "status": "ready",
                        "source": "stale_handoff_study_entry",
                        "next_owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "allowed_actions": ["run_quality_repair_batch"],
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::old",
                        "action_fingerprint": "publication-blockers::old",
                    },
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "status": "executable_owner_action",
                        "owner": "write",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::old",
                        "action_fingerprint": "publication-blockers::old",
                        "state": {
                            "state_kind": "executable_owner_action",
                            "provider_admission_pending": True,
                        },
                    },
                },
            ],
            "action_queue": [
                {
                    "status": "queued",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::old",
                    "action_fingerprint": "publication-blockers::old",
                }
            ],
        },
        study_root=study_root,
    )

    assert fields["provider_admission_pending_count"] == 1
    candidate = fields["provider_admission_candidates"][0]
    assert candidate["source"] == "opl_current_control_state.study_current_executable_owner_action"
    assert candidate["action_type"] == "run_gate_clearing_batch"
    assert candidate["work_unit_id"] == "publication_gate_replay"
    assert candidate["work_unit_fingerprint"] == fingerprint


def test_existing_projection_refresh_promotes_progress_first_owner_action_admission(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    fingerprint = "sha256:2c4793a4e41859fd21a0bc088459c85f298bacb7d06eea811b44beae568fbf9f"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "owner_callable_adapters"
        / "run_gate_clearing_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "owner_callable_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": "run_gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "opl_domain_progress_transition_result": _opl_transition_result(
                study_id=study_id,
                work_unit_id="publication_gate_replay",
                fingerprint=fingerprint,
                stage_run_id="stage-run-gate-replay",
            ),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    )
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "status": "ready",
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
                "next_owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "allowed_actions": ["run_gate_clearing_batch"],
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "owner_route_currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth::current",
                    "runtime_health_epoch": "runtime::current",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": True,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "action_queue": [],
            },
        },
        status={"study_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    admission = result["owner_action_admission"]
    assert admission == result["progress_first_monitoring_summary"]["owner_action_admission"]
    assert admission["admission_pending"] is True
    assert admission["provider_attempt_running_proven"] is False
    assert admission["allowed_actions"] == ["run_gate_clearing_batch"]
    assert result["provider_admission_pending_count"] == 1
    assert result["provider_admission_candidates"][0]["source"] == (
        "opl_current_control_state.study_current_executable_owner_action"
    )


def test_existing_projection_refresh_clears_stale_provider_admission_on_no_current_action(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
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


def test_existing_projection_refresh_consumes_same_identity_provider_readback(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    work_unit_id = "medical_prose_write_repair"
    fingerprint = "domain-transition::route_back_same_line::medical_prose_write_repair"
    route_key = "paper-policy-request:5c447e99601513e78e08ca8f"
    study_root = write_study(profile.workspace_root, study_id, quest_id=study_id)
    readback = opl_transition_readback(
        study_id,
        action_fingerprint=fingerprint,
        work_unit_id=work_unit_id,
        route_identity_key=route_key,
        attempt_idempotency_key=route_key,
        request_idempotency_key=route_key,
    )
    request_action = {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
        "source_surface": "opl_current_control_state.transition_request_candidates",
        "study_id": study_id,
        "quest_id": study_id,
        "next_owner": "write",
        "owner": "write",
        "action_type": "request_opl_stage_attempt",
        "allowed_actions": ["request_opl_stage_attempt"],
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": fingerprint,
        "action_fingerprint": fingerprint,
        "route_identity_key": route_key,
        "attempt_idempotency_key": route_key,
        "idempotency_key": route_key,
        "provider_admission_pending": False,
        "transition_request_pending": True,
        "provider_attempt_or_lease_required": False,
        "provider_admission_requires_opl_runtime_result": True,
        "opl_transition_runtime_required": True,
    }
    provider_candidate = {
        **request_action,
        "surface": "opl_provider_admission_candidate",
        "status": "provider_admission_pending",
        "source": "opl_current_control_state.provider_admission_candidates",
        "next_executable_owner": "write",
        "provider_admission_pending": True,
        "transition_request_pending": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }
    monkeypatch.setattr(
        module,
        "_attach_delivery_inspection_projection",
        lambda payload, **_: dict(payload),
    )

    result = module._refresh_existing_projection_current_owner_surfaces(
        payload={
            "study_id": study_id,
            "quest_id": study_id,
            "current_executable_owner_action": request_action,
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "schema_version": 1,
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": study_id,
                "owner": "write",
                "action_type": "request_opl_stage_attempt",
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "state": {
                    "state_kind": "executable_owner_action",
                    "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                    "provider_admission_pending": False,
                    "transition_request_pending": True,
                },
            },
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
                    },
                },
            },
            "provider_admission_pending_count": 1,
            "provider_admission_candidates": [provider_candidate],
            "transition_request_pending_count": 0,
            "transition_request_candidates": [],
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "study_id": study_id,
                "quest_id": study_id,
                "quest_status": "provider_admission_pending",
                "source_path": "/tmp/opl_current_control_state/latest.json",
                "running_provider_attempt": False,
                "provider_admission_pending_count": 1,
                "provider_admission_candidates": [provider_candidate],
                "transition_request_pending_count": 0,
                "transition_request_candidates": [],
                "current_executable_owner_action": request_action,
                "current_work_unit": {
                    "surface_kind": "current_work_unit",
                    "schema_version": 1,
                    "status": "executable_owner_action",
                    "study_id": study_id,
                    "quest_id": study_id,
                    "owner": "write",
                    "action_type": "request_opl_stage_attempt",
                    "work_unit_id": work_unit_id,
                    "work_unit_fingerprint": fingerprint,
                    "action_fingerprint": fingerprint,
                    "state": {
                        "state_kind": "executable_owner_action",
                        "source": "paper_recovery_state.next_safe_action.successor_owner_action",
                        "provider_admission_pending": False,
                        "transition_request_pending": True,
                    },
                },
            },
        },
        status={"study_id": study_id, "quest_id": study_id},
        profile=profile,
        profile_ref=None,
        study_root=study_root,
        publication_eval_payload=None,
    )

    action = result["current_executable_owner_action"]
    work_unit = result["current_work_unit"]
    assert result["provider_admission_pending_count"] == 1
    assert result["transition_request_pending_count"] == 0
    assert action["source"] == "opl_current_control_state.provider_admission_candidates"
    assert action["provider_admission_pending"] is True
    assert action.get("transition_request_pending") is not True
    assert action["provider_attempt_or_lease_required"] is True
    assert action["provider_admission_requires_opl_runtime_result"] is False
    assert "provider_attempt_running_proven" not in action
    assert work_unit["status"] == "executable_owner_action"
    assert work_unit["state"]["source"] == "opl_current_control_state.provider_admission_candidates"
    assert work_unit["state"]["provider_admission_pending"] is True
    assert work_unit["state"].get("transition_request_pending") is not True


def test_existing_projection_refresh_prefers_live_attempt_over_stale_handoff(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
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

    assert result.get("active_run_id") is None
    assert result.get("active_stage_attempt_id") is None
    assert result.get("active_workflow_id") is None
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["running_provider_attempt"] is False
    assert monitoring["worker_liveness"]["stale_active_run_id"] == (
        "opl-stage-attempt://sat-live-gate-replay"
    )


def test_existing_projection_refresh_rejects_superseded_live_attempt_identity(
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
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
    assert result.get("active_run_id") is None
