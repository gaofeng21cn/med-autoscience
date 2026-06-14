from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_handoff_preserves_current_control_current_work_unit(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_id = "003-dpcc-primary-care-phenotype-treatment-gap"
    quest_id = study_id
    study_root = write_study(profile.workspace_root, study_id, quest_id=quest_id)
    fingerprint = "publication-blockers::0915410f804b3697"
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
            "generated_at": "2026-06-14T09:58:23+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": study_id,
                    "quest_status": "active",
                    "running_provider_attempt": False,
                    "current_work_unit": {
                        "surface_kind": "current_work_unit",
                        "schema_version": 1,
                        "status": "typed_blocker",
                        "study_id": study_id,
                        "quest_id": quest_id,
                        "owner": "med-autoscience",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                        "action_fingerprint": fingerprint,
                        "state": {
                            "state_kind": "typed_blocker",
                            "source": "accepted_closeout_consumed_pending",
                            "typed_blocker": {
                                "blocker_type": "provider_completion_is_not_domain_ready",
                                "owner": "med-autoscience",
                                "action_type": "run_quality_repair_batch",
                                "work_unit_id": "medical_prose_write_repair",
                                "work_unit_fingerprint": fingerprint,
                                "typed_blocker_ref": (
                                    "artifacts/supervision/consumer/default_executor_execution/"
                                    "sat_f8e1cfe49a3aa3cf95d0584d.closeout.json"
                                ),
                            },
                        },
                    },
                    "current_execution_envelope": {
                        "state_kind": "typed_blocker",
                        "owner": "med-autoscience",
                        "source": "accepted_closeout_consumed_pending",
                        "typed_blocker": {
                            "blocker_type": "provider_completion_is_not_domain_ready",
                            "owner": "med-autoscience",
                            "action_type": "run_quality_repair_batch",
                            "work_unit_id": "medical_prose_write_repair",
                            "work_unit_fingerprint": fingerprint,
                        },
                    },
                    "provider_admission_pending_count": 0,
                    "provider_admission_candidates": [],
                    "typed_blocker": {
                        "blocker_type": "provider_completion_is_not_domain_ready",
                        "owner": "med-autoscience",
                        "action_type": "run_quality_repair_batch",
                        "work_unit_id": "medical_prose_write_repair",
                        "work_unit_fingerprint": fingerprint,
                    },
                    "blocked_reason": "provider_completion_is_not_domain_ready",
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
            "decision": "blocked",
            "reason": "quest_waiting_opl_runtime_owner_route",
            "active_run_id": None,
            "runtime_health_snapshot": {
                "runtime_health_epoch": "runtime-health-event-after-closeout",
                "runtime_liveness_status": "none",
                "attempt_state": "blocked",
            },
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id=study_id)

    handoff = result["opl_current_control_state_handoff"]
    assert handoff["current_work_unit"]["status"] == "typed_blocker"
    assert handoff["current_work_unit"]["work_unit_fingerprint"] == fingerprint
    assert handoff["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert handoff["provider_admission_pending_count"] == 0
    assert handoff["provider_admission_candidates"] == []
    assert result["current_work_unit"]["status"] == "typed_blocker"
    assert result["current_work_unit"]["state"]["typed_blocker"]["blocker_type"] == (
        "provider_completion_is_not_domain_ready"
    )
    assert result["current_execution_envelope"]["state_kind"] == "typed_blocker"
    assert result["provider_admission_pending_count"] == 0
    assert result["provider_admission_candidates"] == []
    assert result["current_executable_owner_action"] is None
