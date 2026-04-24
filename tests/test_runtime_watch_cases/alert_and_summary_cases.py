from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_writes_supervision_changed_event_when_degraded_runtime_recovers_to_live(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    dump_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "runtime_watch",
            "decision": "blocked",
            "reason": "resume_request_failed",
        },
    )

    states = [
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "blocked",
            "reason": "resume_request_failed",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": "run-stale",
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": "run-stale",
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "launch_report_path": str(launch_report_path),
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    ]
    call_index = {"value": 0}

    def next_status(*, profile, study_root, source):
        index = min(call_index["value"], len(states) - 1)
        call_index["value"] += 1
        return states[index]

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", next_status)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    first = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    second = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    first_supervision = first["managed_study_supervision"][0]
    second_supervision = second["managed_study_supervision"][0]
    latest_payload = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )

    assert first_supervision["health_status"] == "degraded"
    assert second_supervision["health_status"] == "live"
    assert second_supervision["last_transition"] == "recovered"
    assert "runtime_event_ref" not in latest_payload
    assert not (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").exists()
def test_watch_runtime_refreshes_recovery_requested_status_to_live_within_same_tick(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    workspace_root = tmp_path / "workspace"
    profile = profiles.WorkspaceProfile(
        name="diabetes",
        workspace_root=workspace_root,
        runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=workspace_root / "studies",
        portfolio_root=workspace_root / "portfolio",
        med_deepscientist_runtime_root=workspace_root / "ops" / "med-deepscientist" / "runtime",
        med_deepscientist_repo_root=tmp_path / "med-deepscientist",
        default_publication_profile="general_medical_journal",
        default_citation_style="AMA",
        enable_medical_overlay=True,
        medical_overlay_scope="workspace",
        medical_overlay_skills=("intake-audit", "baseline"),
        research_route_bias_policy="high_plasticity_medical",
        preferred_study_archetypes=("clinical_classifier",),
        default_submission_targets=(),
    )
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "001-risk",
            "status": "running",
            "active_run_id": "run-live",
        },
    )

    calls: list[tuple[str, str]] = []
    recovery_requested = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }
    live_status = {
        **recovery_requested,
        "decision": "noop",
        "reason": "quest_already_running",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live",
            "runtime_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "worker_running": True,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
        "autonomous_runtime_notice": {
            "active_run_id": "run-live",
            "browser_url": "http://127.0.0.1:21003",
            "quest_session_api_url": "http://127.0.0.1:21003/api/quests/001-risk/session",
        },
        "execution_owner_guard": {
            "active_run_id": "run-live",
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or recovery_requested,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [quest_root])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    supervision = result["managed_study_supervision"][0]
    latest_payload = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json").read_text(encoding="utf-8")
    )

    assert calls == [
        ("ensure", "runtime_watch"),
        ("status", "001-risk"),
    ]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
        }
    ]
    assert supervision["health_status"] == "live"
    assert supervision["runtime_decision"] == "noop"
    assert supervision["active_run_id"] == "run-live"
    assert latest_payload["health_status"] == "live"
    assert latest_payload["runtime_decision"] == "noop"
    assert latest_payload["active_run_id"] == "run-live"
def test_watch_runtime_relays_recovery_alerts_to_bound_conversations_without_path_leaks(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    states = [
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
            "autonomous_runtime_notice": {
                "active_run_id": "run-live",
            },
            "execution_owner_guard": {
                "active_run_id": "run-live",
            },
        },
        {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "hermes",
                "runtime_backend_id": "hermes",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "quest_id": "001-risk",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    ]
    state_index = {"value": 0}
    interaction_calls: list[dict[str, object]] = []

    class FakeBackend:
        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            interaction_calls.append(
                {
                    "runtime_root": str(runtime_root),
                    "quest_id": quest_id,
                    "payload": dict(payload),
                }
            )
            return {
                "status": "ok",
                "interaction_id": f"interaction-{len(interaction_calls)}",
            }

    def next_status(*, profile, study_root, source):
        index = min(state_index["value"], len(states) - 1)
        state_index["value"] += 1
        return states[index]

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", next_status)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: states[min(max(state_index["value"] - 1, 0), len(states) - 1)],
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FakeBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert_path = study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json"
    latest_alert = json.loads(latest_alert_path.read_text(encoding="utf-8"))

    assert len(interaction_calls) == 3
    assert interaction_calls[0]["quest_id"] == "001-risk"
    assert interaction_calls[0]["payload"]["kind"] == "progress"
    assert interaction_calls[0]["payload"]["deliver_to_bound_conversations"] is True
    assert interaction_calls[0]["payload"]["reply_mode"] == "threaded"
    assert "自动恢复中" in str(interaction_calls[0]["payload"]["message"])
    assert str(study_root) not in str(interaction_calls[0]["payload"]["message"])
    assert str(profile.runtime_root) not in str(interaction_calls[0]["payload"]["message"])
    assert interaction_calls[1]["payload"]["kind"] == "milestone"
    assert "已恢复在线" in str(interaction_calls[1]["payload"]["message"])
    assert interaction_calls[2]["payload"]["kind"] == "progress"
    assert latest_alert["delivery_status"] == "delivered"
    assert latest_alert["health_status"] == "recovering"
def test_watch_runtime_relays_manual_intervention_alert_once_per_escalated_state(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    interaction_calls: list[dict[str, object]] = []

    failing_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "blocked",
        "reason": "resume_request_failed",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    class FakeBackend:
        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            interaction_calls.append(dict(payload))
            return {"status": "ok", "interaction_id": f"interaction-{len(interaction_calls)}"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: failing_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FakeBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    assert len(interaction_calls) == 2
    assert interaction_calls[0]["kind"] == "progress"
    assert interaction_calls[1]["kind"] == "milestone"
    assert "人工介入" in str(interaction_calls[1]["message"])
    assert latest_alert["delivery_status"] == "delivered"
    assert latest_alert["health_status"] == "escalated"
    assert latest_alert["needs_human_intervention"] is True
def test_watch_runtime_retries_alert_delivery_after_previous_failure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    attempts = {"value": 0}

    recovering_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    class FlakyBackend:
        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            attempts["value"] += 1
            if attempts["value"] == 1:
                raise RuntimeError("relay transport temporarily unavailable")
            return {"status": "ok", "interaction_id": "interaction-2"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: recovering_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: recovering_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FlakyBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    failed_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )
    delivered_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    assert attempts["value"] == 2
    assert failed_alert["delivery_status"] == "failed"
    assert "temporarily unavailable" in failed_alert["error"]
    assert delivered_alert["delivery_status"] == "delivered"
    assert delivered_alert["health_status"] == "recovering"
def test_watch_runtime_routes_alert_delivery_through_controlled_research_backend(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    (study_root / "study.yaml").write_text("study_id: 001-risk\n", encoding="utf-8")
    quest_root = profile.runtime_root / "001-risk"
    calls: list[dict[str, object]] = []

    recovering_status = {
        "schema_version": 1,
        "study_id": "001-risk",
        "study_root": str(study_root),
        "entry_mode": "full_research",
        "execution": {
            "engine": "hermes",
            "runtime_backend_id": "hermes",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "quest_id": "001-risk",
        "quest_root": str(quest_root),
        "quest_exists": True,
        "quest_status": "running",
        "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
        "runtime_binding_exists": True,
        "study_completion_contract": {},
        "decision": "resume",
        "reason": "quest_marked_running_but_no_live_session",
        "runtime_liveness_audit": {
            "status": "none",
            "active_run_id": None,
            "runtime_audit": {
                "status": "none",
                "active_run_id": None,
                "worker_running": False,
                "worker_pending": False,
                "stop_requested": False,
            },
        },
    }

    class OuterBackend:
        BACKEND_ID = "hermes"

    class ControlledBackend:
        BACKEND_ID = "med_deepscientist"

        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            calls.append(
                {
                    "runtime_root": str(runtime_root),
                    "quest_id": quest_id,
                    "payload": dict(payload),
                }
            )
            return {"status": "ok", "interaction_id": "interaction-controlled"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: recovering_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: recovering_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: OuterBackend(),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "controlled_research_backend_metadata_for_backend_id",
        lambda backend_id: ("med_deepscientist", "med-deepscientist"),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "get_managed_runtime_backend",
        lambda backend_id: ControlledBackend(),
    )

    module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert = json.loads(
        (study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json").read_text(encoding="utf-8")
    )

    assert len(calls) == 1
    assert calls[0]["quest_id"] == "001-risk"
    assert calls[0]["runtime_root"] == str(profile.med_deepscientist_runtime_root)
    assert latest_alert["delivery_status"] == "delivered"
