from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_watch_runtime_does_not_auto_recover_package_ready_handoff(
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
    calls: list[tuple[str, str]] = []

    def parked_status() -> dict[str, object]:
        return {
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_parked_on_unchanged_finalize_state",
            ),
            "study_root": str(study_root),
            "quest_root": str(quest_root),
            "quest_status": "active",
            "execution": {
                "engine": "mas-runtime-core",
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "001-risk",
                "auto_resume": True,
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
            },
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

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or parked_status(),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: pytest.fail("package-ready parked handoff must not auto-recover"),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [("status", "001-risk"), ("status", "001-risk")]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []

def test_watch_runtime_holds_auto_recovery_when_flapping_circuit_breaker_is_active(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"
    dump_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-04-26T00:00:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "health_status": "recovering",
            "runtime_stability_status": "flapping",
            "flapping_episode_count": 2,
            "flapping_circuit_breaker": True,
            "runtime_reason": "quest_marked_running_but_no_live_session",
        },
    )
    no_live_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_marked_running_but_no_live_session",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
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
    calls: list[tuple[str, str]] = []

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or no_live_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: (_ for _ in ()).throw(AssertionError("flapping circuit breaker must suppress blind resume")),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [("status", "001-risk"), ("status", "001-risk")]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_recovery_holds"] == [
        {
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "hold_reason": "flapping_circuit_breaker_active",
            "recommended_probe": "refresh_runtime_liveness_before_resume",
            "flapping_episode_count": 2,
            "recovery_probe": {
                "probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::2",
                "status": "hold_active",
                "recommended_action": "hold",
                "reason": "flapping_circuit_breaker_active",
                "next_probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::3",
                "liveness": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                    "worker_pending": False,
                    "stop_requested": False,
                },
                "current_status": {
                    "quest_status": "running",
                    "decision": "resume",
                    "reason": "quest_marked_running_but_no_live_session",
                    "runtime_stability_status": "flapping",
                    "flapping_circuit_breaker": True,
                    "flapping_episode_count": 2,
                },
            },
        }
    ]
    assert not (study_root / "artifacts" / "runtime" / "recovery_probe" / "latest.json").exists()

def test_runtime_watch_apply_can_run_supervisor_platform_repair_tick(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[dict[str, object]] = []

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    def fake_scan_domain_routes(**kwargs) -> dict[str, object]:
        calls.append(kwargs)
        return {
            "surface": "portable_domain_route_scan",
            "apply_runtime_platform_repair": kwargs["apply_runtime_platform_repair"],
            "study_count": len(kwargs["study_ids"]),
        }

    monkeypatch.setattr(module.domain_route_scan, "scan_domain_routes", fake_scan_domain_routes)

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
        apply_supervisor_platform_repair=True,
    )

    assert len(calls) == 1
    assert calls[0]["profile"] == profile
    assert calls[0]["study_ids"] == ("001-risk",)
    assert calls[0]["apply_safe_actions"] is True
    assert calls[0]["apply_runtime_platform_repair"] is True
    assert calls[0]["developer_supervisor_mode"] == "developer_apply_safe"
    assert result["supervisor_platform_repair"] == {
        "surface": "portable_domain_route_scan",
        "apply_runtime_platform_repair": True,
        "study_count": 1,
    }

def test_runtime_watch_does_not_run_supervisor_platform_repair_by_default(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.studies_root / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})

    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])
    monkeypatch.setattr(
        module.domain_route_scan,
        "scan_domain_routes",
        lambda **kwargs: pytest.fail("runtime watch must not apply platform repair unless explicitly enabled"),
    )

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert "supervisor_platform_repair" not in result

def test_hard_auto_recovery_ignores_stale_continuation_run_id() -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch_parts.managed_wakeup")

    assert module._should_hard_auto_recover_managed_study(
        {
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "quest_status": "running",
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-stale",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "decision:previous",
            },
            "runtime_liveness_audit": {
                "status": "none",
                "active_run_id": None,
                "runtime_audit": {
                    "status": "none",
                    "active_run_id": None,
                    "worker_running": False,
                },
            },
        }
    )

def test_flapping_recovery_probe_clears_hold_when_current_status_is_live(
    tmp_path: Path,
) -> None:
    policy = importlib.import_module("med_autoscience.controllers.runtime_watch_recovery_policy")
    study_root = tmp_path / "studies" / "001-risk"
    dump_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-04-26T00:01:00+00:00",
            "study_id": "001-risk",
            "quest_id": "001-risk",
            "health_status": "recovering",
            "runtime_stability_status": "flapping",
            "flapping_episode_count": 2,
            "flapping_circuit_breaker": True,
        },
    )

    hold = policy.hold_for_flapping_circuit_breaker(
        study_root=study_root,
        status_payload={
            **make_study_runtime_status_payload(
                study_id="001-risk",
                decision="resume",
                reason="quest_marked_running_but_no_live_session",
            ),
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-recovered",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-recovered",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
        },
    )

    assert hold is not None
    assert hold["recovery_probe"] == {
        "probe_id": "recovery-probe::001-risk::001-risk::flapping-circuit-breaker::2",
        "status": "clear_hold",
        "recommended_action": "ready_to_resume",
        "reason": "runtime_liveness_confirmed_live",
        "next_probe_id": None,
        "liveness": {
            "status": "live",
            "active_run_id": "run-recovered",
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
        },
        "current_status": {
            "quest_status": "running",
            "decision": "resume",
            "reason": "quest_marked_running_but_no_live_session",
            "runtime_stability_status": "live",
            "flapping_circuit_breaker": False,
            "flapping_episode_count": 2,
        },
    }
