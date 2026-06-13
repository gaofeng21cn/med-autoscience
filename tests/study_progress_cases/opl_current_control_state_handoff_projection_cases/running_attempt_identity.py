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
