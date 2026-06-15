from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_opl_current_control_state_handoff_preserves_running_attempt_identity(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-13T09:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-live",
                    "active_stage_attempt_id": "sat-live",
                    "active_workflow_id": "wf-live",
                    "running_provider_attempt": True,
                    "action_type": "run_quality_repair_batch",
                    "work_unit_id": "medical_prose_write_repair",
                    "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                    "action_fingerprint": "publication-blockers::0915410f804b3697",
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": "publication-blockers::0915410f804b3697",
                        "action_fingerprint": "publication-blockers::0915410f804b3697",
                    },
                    "next_owner": "write",
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "active",
            "decision": "continue",
            "reason": "live_managed_runtime",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-before-live-attempt",
                "runtime_liveness_status": "queued",
                "attempt_state": "queued",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    current_work_unit = result["current_work_unit"]
    assert handoff["running_provider_attempt"] is True
    assert handoff["action_type"] == "run_quality_repair_batch"
    assert handoff["work_unit_id"] == "medical_prose_write_repair"
    assert handoff["work_unit_fingerprint"] == "publication-blockers::0915410f804b3697"
    assert handoff["runtime_health"]["action_type"] == "run_quality_repair_batch"
    assert handoff["runtime_health"]["work_unit_id"] == "medical_prose_write_repair"
    assert current_work_unit["status"] == "running_provider_attempt"
    assert current_work_unit["action_type"] == "run_quality_repair_batch"
    assert current_work_unit["work_unit_id"] == "medical_prose_write_repair"
    assert result["current_execution_envelope"]["state_kind"] == "running_provider_attempt"


def test_provider_admission_handoff_without_active_attempt_ids_is_not_running(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    fingerprint = "sha256:6423b231114cbec0e8d1ccb0b69adb117d0f2d8fa58d72751627c049a0dc10e4"
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    dispatch_path = (
        study_root
        / "artifacts"
        / "supervision"
        / "consumer"
        / "default_executor_dispatches"
        / "run_gate_clearing_batch.json"
    )
    _write_json(
        dispatch_path,
        {
            "surface": "default_executor_dispatch_request",
            "dispatch_status": "ready",
            "study_id": study_id,
            "quest_id": quest_id,
            "action_type": "run_gate_clearing_batch",
            "next_executable_owner": "gate_clearing_batch",
            "provider_attempt_or_lease_required": True,
            "provider_completion_is_domain_completion": False,
            "owner_route_current": True,
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "dispatch_path": str(dispatch_path),
            "required_output_surface": "artifacts/controller/gate_clearing_batch/latest.json",
        },
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-15T02:46:36+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_id": quest_id,
                    "quest_status": "provider_admission_pending",
                    "active_run_id": None,
                    "active_stage_attempt_id": None,
                    "active_workflow_id": None,
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "provider_admission_pending",
                        "runtime_liveness_status": "not_running",
                    },
                    "action_queue": [
                        {
                            "status": "queued",
                            "study_id": study_id,
                            "quest_id": quest_id,
                            "owner": "gate_clearing_batch",
                            "action_type": "run_gate_clearing_batch",
                            "work_unit_id": "publication_gate_replay",
                            "work_unit_fingerprint": fingerprint,
                            "action_fingerprint": fingerprint,
                            "provider_attempt_or_lease_required": True,
                            "authority": "mas_provider_admission_identity",
                            "dispatch_path": str(dispatch_path),
                            "owner_route": {
                                "next_owner": "gate_clearing_batch",
                                "allowed_actions": ["run_gate_clearing_batch"],
                                "work_unit_fingerprint": fingerprint,
                                "source_refs": {
                                    "work_unit_id": "publication_gate_replay",
                                    "work_unit_fingerprint": fingerprint,
                                    "owner_route_currentness_basis": {
                                        "work_unit_id": "publication_gate_replay",
                                        "work_unit_fingerprint": fingerprint,
                                        "truth_epoch": "truth-event-current",
                                        "runtime_health_epoch": "runtime-health-event-current",
                                    },
                                },
                            },
                        }
                    ],
                }
            ],
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": study_id,
            "study_root": str(study_root),
            "quest_id": quest_id,
            "quest_root": str(profile.runtime_root / quest_id),
            "quest_status": "running",
            "decision": "continue",
            "reason": "live_managed_runtime",
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
            },
            "current_work_unit": {
                "surface_kind": "current_work_unit",
                "status": "executable_owner_action",
                "study_id": study_id,
                "quest_id": quest_id,
                "owner": "gate_clearing_batch",
                "action_type": "run_gate_clearing_batch",
                "work_unit_id": "publication_gate_replay",
                "work_unit_fingerprint": fingerprint,
                "action_fingerprint": fingerprint,
                "currentness_basis": {
                    "work_unit_id": "publication_gate_replay",
                    "work_unit_fingerprint": fingerprint,
                    "truth_epoch": "truth-event-current",
                    "runtime_health_epoch": "runtime-health-event-current",
                },
                "state": {
                    "state_kind": "executable_owner_action",
                    "provider_admission_pending": False,
                },
            },
            "current_execution_envelope": {
                "state_kind": "executable_owner_action",
                "owner": "gate_clearing_batch",
                "next_work_unit": "publication_gate_replay",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["running_provider_attempt"] is False
    assert handoff["provider_attempt_owner"] is None
    assert handoff["runtime_owner"] is None
    assert handoff["queue_owner"] is None
    assert handoff["active_run_id"] is None
    assert handoff["active_stage_attempt_id"] is None
    assert handoff["active_workflow_id"] is None
    assert handoff["action_queue"][0]["action_type"] == "run_gate_clearing_batch"
    assert handoff["action_queue"][0]["work_unit_fingerprint"] == fingerprint


def test_study_progress_keeps_unbound_live_attempt_as_observability_only(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    domain_status = importlib.import_module("med_autoscience.controllers.domain_status_projection")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        quest_id="quest-001",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
        paper_framing_summary="A reproducible diabetes mortality prediction manuscript.",
        paper_urls=["https://example.org/diabetes-mortality"],
        journal_shortlist=["Journal of Clinical Epidemiology"],
        minimum_sci_ready_evidence_package=["main_result_table"],
    )
    handoff_path = (
        profile.workspace_root
        / "runtime"
        / "artifacts"
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-06-06T10:20:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "active",
                    "active_run_id": "opl-stage-attempt://sat-unbound",
                    "active_stage_attempt_id": "sat-unbound",
                    "active_workflow_id": "wf-unbound",
                    "running_provider_attempt": True,
                    "runtime_health": {
                        "health_status": "running",
                        "runtime_liveness_status": "live",
                    },
                }
            ],
        },
    )
    monkeypatch.setattr(
        domain_status,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_status": "active",
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "runtime_health_snapshot": {
                "health_status": "queued",
                "runtime_liveness_status": "queued",
            },
            "authority_snapshot": {},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    dashboard = result["opl_current_control_state_handoff"]
    assert dashboard["running_provider_attempt"] is True
    assert dashboard["active_stage_attempt_id"] == "sat-unbound"
    monitoring = result["progress_first_monitoring_summary"]
    assert monitoring["running_provider_attempt"] is False
    assert monitoring["active_stage_attempt_id"] is None
    assert monitoring["worker_liveness"]["stale_active_run_id"] == "opl-stage-attempt://sat-unbound"
    assert monitoring["current_executable_owner_action"]["source"] == "stage_artifact_index.next_owner_action"
