from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_projects_live_worker_stale_artifact_delta_as_recovering(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = helpers.write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.runtime_root / "quest-001"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "quest-001",
            "status": "running",
            "active_run_id": "run-stale",
            "worker_running": True,
        },
    )
    status_payload = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "execution": {
            "engine": "mas-runtime-core",
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "quest-001",
            "auto_resume": True,
        },
        "active_run_id": "run-stale",
        "worker_running": True,
        "runtime_liveness_status": "live",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-stale",
            "runtime_audit": {"status": "live", "worker_running": True, "active_run_id": "run-stale"},
        },
        "autonomy_slo": {
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
        },
        "supervisor_tick_audit": {
            "required": True,
            "status": "fresh",
            "latest_recorded_at": "2026-05-02T10:40:00+00:00",
        },
    }

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", lambda **_: status_payload)
    monkeypatch.setattr(module.study_runtime_router, "study_runtime_status", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_runtime_watch_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    supervision = result["managed_study_supervision"][0]
    assert supervision["health_status"] == "recovering"
    assert supervision["runtime_liveness_status"] == "live"
    assert supervision["worker_running"] is True
    assert supervision["active_run_id"] == "run-stale"
    assert supervision["runtime_health_snapshot"]["worker_liveness_state"]["state"] == "activity_timeout"
    assert supervision["summary"] != "托管运行时在线，研究仍在自动推进。"

