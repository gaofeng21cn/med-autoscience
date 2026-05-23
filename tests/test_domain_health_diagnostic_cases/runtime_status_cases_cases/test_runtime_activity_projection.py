from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})


def test_watch_runtime_projects_live_worker_stale_artifact_delta_as_recovering(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_id": "quest-001",
        "quest_root": str(quest_root),
        "quest_status": "running",
        "execution": {
            "engine": "opl-provider-backed-stage-runtime",
                "runtime_backend_id": "opl_provider_backed_stage_runtime",
                "runtime_engine_id": "opl-provider-backed-stage-runtime",
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

    monkeypatch.setattr(module.domain_status_projection, "progress_projection", lambda **_: status_payload)
    monkeypatch.setattr(module.study_outer_loop, "build_domain_health_diagnostic_outer_loop_tick_request", lambda **_: None)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    assert handoff["status"] == "handoff_required"
    assert handoff["runtime_owner"] == "one-person-lab"
    assert handoff["mas_runtime_read_model_retired"] is True
    assert handoff["typed_blocker"]["blocker_type"] == "opl_runtime_owner_handoff_required"
