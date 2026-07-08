from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_supervisor_tick_audit_uses_workspace_opl_current_control_state(
    monkeypatch,
    tmp_path: Path,
) -> None:
    runtime_decision = importlib.import_module(
        "med_autoscience.controllers.study_runtime_decision.publication_and_submission"
    )
    status_module = importlib.import_module("med_autoscience.controllers.study_runtime_types")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff",
            "schema_version": 1,
            "generated_at": "2026-05-24T22:50:48+00:00",
            "provider_readiness": {
                "surface_kind": "opl_provider_readiness_projection",
                "source": "opl_family_runtime_status",
                "provider_kind": "temporal",
                "provider_ready": True,
                "worker_ready": True,
                "managed_worker_source_current": True,
            },
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "running"},
                }
            ],
        },
    )
    monkeypatch.setattr(
        runtime_decision,
        "_supervisor_tick_now",
        lambda: datetime.fromisoformat("2026-05-24T22:52:00+00:00"),
    )
    status = status_module.ProgressProjectionStatus.from_payload(
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(profile.managed_runtime_home / "quests" / "quest-001"),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
        }
    )

    runtime_decision._record_supervisor_tick_audit(status=status, study_root=study_root)

    audit = status.extras["supervisor_tick_audit"]
    assert audit["status"] == "fresh"
    assert audit["reason"] == "opl_current_control_state_handoff_fresh"
    assert audit["latest_report_path"] == str(handoff_path)
    assert audit["latest_recorded_at"] == "2026-05-24T22:50:48+00:00"
    assert audit["seconds_since_latest_recorded_at"] == 72
    assert audit["provider_readiness"]["source"] == "opl_family_runtime_status"
    assert audit["provider_ready"] is True
    assert audit["worker_ready"] is True
    assert audit["managed_worker_source_current"] is True
