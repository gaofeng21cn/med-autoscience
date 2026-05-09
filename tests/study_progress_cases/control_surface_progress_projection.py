from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_freshness_does_not_treat_control_surface_as_artifact_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-dm",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "recorded_at": "2026-05-09T07:05:46+00:00",
            "health_status": "live",
            "summary": "runtime heartbeat only",
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-dm",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
            "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
            "last_meaningful_progress": {
                "last_meaningful_progress_at": "2026-05-09T07:05:46+00:00",
                "source": "mas_control_surface",
                "source_ref": None,
            },
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": None,
                "meaningful_artifact_delta_kind": None,
                "turn_progress_kind": None,
            },
            "ai_doctor_request_required": True,
            "ai_doctor_state": "request_ready",
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-dm",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-002", "auto_resume": True},
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-live-control-only",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-control-only",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-control-only",
                    "worker_running": True,
                },
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-09T07:05:46+00:00",
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 9, 7, 5, 55, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="002-dm")

    assert result["last_meaningful_progress_at"] == "2026-05-09T07:05:46+00:00"
    assert result["progress_freshness"]["supervisor_tick_freshness"]["status"] == "fresh"
    artifact_freshness = result["progress_freshness"]["meaningful_artifact_delta_freshness"]
    assert artifact_freshness["status"] == "missing"
    assert artifact_freshness["latest_progress_at"] is None
    assert artifact_freshness["latest_progress_source"] == "mds_artifact_delta"
    assert result["progress_freshness"]["activity_timeout"]["state"] == "watching_new_run"
    assert result["user_visible_projection"]["actual_write_active"] is False
