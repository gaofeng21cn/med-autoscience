from __future__ import annotations

from . import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_sends_recovery_resolution_after_previous_manual_intervention_alert(
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
    interactions: list[dict[str, object]] = []

    previous_alert_path = study_root / "artifacts" / "runtime" / "runtime_alert_delivery" / "latest.json"
    dump_json(
        previous_alert_path,
        {
            "schema_version": 1,
            "delivered_at": "2026-04-18T00:50:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "health_status": "escalated",
            "notification_state": "manual_intervention_required",
            "delivery_status": "delivered",
            "alert_fingerprint": "prior-alert",
        },
    )

    live_status = {
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
    }

    class FakeBackend:
        BACKEND_ID = "med_deepscientist"

        def artifact_interact(self, *, runtime_root: Path, quest_id: str, payload: dict[str, object]) -> dict[str, object]:
            interactions.append(
                {
                    "runtime_root": str(runtime_root),
                    "quest_id": quest_id,
                    "payload": dict(payload),
                }
            )
            return {"status": "ok", "interaction_id": "interaction-recovered"}

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: live_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "resolve_managed_runtime_backend",
        lambda execution: FakeBackend(),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "controlled_research_backend_metadata_for_backend_id",
        lambda backend_id: ("med_deepscientist", "med-deepscientist"),
    )
    monkeypatch.setattr(
        module.runtime_backend_contract,
        "get_managed_runtime_backend",
        lambda backend_id: FakeBackend(),
    )

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    latest_alert = json.loads(previous_alert_path.read_text(encoding="utf-8"))

    assert result["managed_study_supervision"][0]["health_status"] == "live"
    assert result["managed_study_supervision"][0]["last_transition"] == "live_confirmed"
    assert len(interactions) == 1
    assert interactions[0]["payload"]["kind"] == "milestone"
    assert "已恢复在线" in str(interactions[0]["payload"]["message"])
    assert latest_alert["notification_state"] == "recovered"
    assert latest_alert["delivery_status"] == "delivered"
def test_suppresses_duplicate_data_asset_gate_blocker(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["outdated_private_release"],
            "study_id": quest_root.name,
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_applies_data_asset_gate_advisory_once(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "advisory",
            "blockers": [],
            "advisories": ["public_data_extension_available"],
            "study_id": quest_root.name,
            "public_support_dataset_ids": ["geo-gse000001"],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["status"] == "advisory"
    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "suppressed"
    assert calls == [False, True, False]
def test_reapplies_data_asset_gate_when_unresolved_dataset_ids_change(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")
    calls: list[bool] = []
    state = {"unresolved_dataset_ids": ["ds_a"]}

    def fake_runner(*, quest_root: Path, apply: bool) -> dict:
        calls.append(apply)
        return {
            "status": "blocked",
            "blockers": ["unresolved_private_data_contract"],
            "advisories": [],
            "study_id": quest_root.name,
            "outdated_dataset_ids": [],
            "unresolved_dataset_ids": list(state["unresolved_dataset_ids"]),
            "public_support_dataset_ids": [],
            "report_json": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.json"),
            "report_markdown": str(quest_root / "artifacts" / "reports" / "data_asset_gate" / "latest.md"),
            "intervention_enqueued": apply,
        }

    first = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )
    state["unresolved_dataset_ids"] = ["ds_b"]
    second = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={"data_asset_gate": fake_runner},
        apply=True,
    )

    assert first["controllers"]["data_asset_gate"]["action"] == "applied"
    assert second["controllers"]["data_asset_gate"]["action"] == "applied"
    assert calls == [False, True, False, True]
def test_watch_loop_runs_runtime_ticks_on_interval(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    runtime_root.mkdir(parents=True)
    seen: list[tuple[str, object]] = []

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        seen.append(("tick", runtime_root, apply, ensure_study_runtimes))
        return {
            "runtime_root": str(runtime_root),
            "scanned_quests": [],
        }

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    def fake_sleep(seconds: float) -> None:
        seen.append(("sleep", seconds))

    result = module.run_watch_loop(
        runtime_root=runtime_root,
        apply=True,
        ensure_study_runtimes=True,
        interval_seconds=12,
        max_ticks=2,
        sleep_fn=fake_sleep,
    )

    assert result["tick_count"] == 2
    assert result["interval_seconds"] == 12
    assert result["last_result"] == {
        "runtime_root": str(runtime_root),
        "scanned_quests": [],
    }
    assert seen == [
        ("tick", runtime_root, True, True),
        ("sleep", 12),
        ("tick", runtime_root, True, True),
    ]
def test_watch_loop_continues_after_single_tick_failure(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    runtime_root.mkdir(parents=True)
    seen: list[tuple[str, object]] = []
    attempts = {"count": 0}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile=None,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        attempts["count"] += 1
        seen.append(("tick", attempts["count"]))
        if attempts["count"] == 1:
            raise RuntimeError("transient daemon read failed")
        return {
            "runtime_root": str(runtime_root),
            "scanned_quests": ["q001"],
        }

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    def fake_sleep(seconds: float) -> None:
        seen.append(("sleep", seconds))

    result = module.run_watch_loop(
        runtime_root=runtime_root,
        apply=True,
        ensure_study_runtimes=True,
        interval_seconds=12,
        max_ticks=2,
        sleep_fn=fake_sleep,
    )

    assert result["tick_count"] == 2
    assert result["last_result"] == {
        "runtime_root": str(runtime_root),
        "scanned_quests": ["q001"],
    }
    assert result["tick_errors"] == [
        {
            "tick": 1,
            "error_type": "RuntimeError",
            "error": "transient daemon read failed",
        }
    ]
    assert seen == [
        ("tick", 1),
        ("sleep", 12),
        ("tick", 2),
    ]
def test_run_managed_supervisor_tick_uses_profile_runtime_root_and_always_enables_study_runtime_ensure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="glioma",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
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
    called: dict[str, object] = {}

    def fake_run_watch_for_runtime(
        *,
        runtime_root: Path,
        controller_runners=None,
        apply: bool,
        profile,
        ensure_study_runtimes: bool = False,
    ) -> dict[str, object]:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        return {"mode": "managed_supervisor_tick"}

    monkeypatch.setattr(module, "run_watch_for_runtime", fake_run_watch_for_runtime)

    result = module.run_managed_supervisor_tick(profile=profile, apply=True)

    assert result == {"mode": "managed_supervisor_tick"}
    assert called == {
        "runtime_root": profile.runtime_root,
        "apply": True,
        "profile": profile,
        "ensure_study_runtimes": True,
    }
def test_run_managed_supervisor_loop_uses_profile_runtime_root_and_always_enables_study_runtime_ensure(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    profiles = importlib.import_module("med_autoscience.profiles")
    profile = profiles.WorkspaceProfile(
        name="glioma",
        workspace_root=tmp_path / "workspace",
        runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime" / "quests",
        studies_root=tmp_path / "workspace" / "studies",
        portfolio_root=tmp_path / "workspace" / "portfolio",
        med_deepscientist_runtime_root=tmp_path / "workspace" / "ops" / "med-deepscientist" / "runtime",
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
    called: dict[str, object] = {}

    def fake_run_watch_loop(
        *,
        runtime_root: Path,
        apply: bool,
        profile,
        ensure_study_runtimes: bool = False,
        interval_seconds: int,
        max_ticks: int | None,
        sleep_fn,
    ) -> dict[str, object]:
        called["runtime_root"] = runtime_root
        called["apply"] = apply
        called["profile"] = profile
        called["ensure_study_runtimes"] = ensure_study_runtimes
        called["interval_seconds"] = interval_seconds
        called["max_ticks"] = max_ticks
        called["sleep_fn"] = sleep_fn
        return {"mode": "managed_supervisor_loop"}

    monkeypatch.setattr(module, "run_watch_loop", fake_run_watch_loop)

    result = module.run_managed_supervisor_loop(
        profile=profile,
        apply=True,
        interval_seconds=45,
        max_ticks=3,
        sleep_fn=lambda _: None,
    )

    assert result == {"mode": "managed_supervisor_loop"}
    assert called["runtime_root"] == profile.runtime_root
    assert called["apply"] is True
    assert called["profile"] == profile
    assert called["ensure_study_runtimes"] is True
    assert called["interval_seconds"] == 45
    assert called["max_ticks"] == 3
