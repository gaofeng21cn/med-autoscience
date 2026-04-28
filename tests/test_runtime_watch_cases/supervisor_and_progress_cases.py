from __future__ import annotations

from . import shared as _shared

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
                "engine": "med-deepscientist",
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
    persisted_probe = json.loads(
        (study_root / "artifacts" / "runtime" / "recovery_probe" / "latest.json").read_text(encoding="utf-8")
    )
    assert persisted_probe == result["managed_study_recovery_holds"][0]["recovery_probe"]


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


def test_run_watch_for_runtime_auto_recovers_stopped_controller_guard_quest(tmp_path: Path, monkeypatch) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    stopped_guard_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_stopped_by_controller_guard",
        ),
        "quest_status": "stopped",
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
    recovered_status = {
        **stopped_guard_status,
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
        "autonomous_runtime_notice": {
            "active_run_id": "run-recovered",
        },
    }

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or stopped_guard_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or recovered_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("status", "001-risk"),
        ("ensure", "runtime_watch_auto_recovery"),
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_stopped_by_controller_guard",
            "applied_decision": "resume",
            "applied_reason": "quest_stopped_by_controller_guard",
            "source": "runtime_watch_auto_recovery",
        }
    ]
def test_run_watch_for_runtime_rechecks_managed_study_immediately_after_figure_loop_guard_stop(
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
        quest_root / ".ds" / "runtime_state.json",
        {
            "quest_id": "001-risk",
            "status": "running",
            "active_run_id": "run-live",
        },
    )
    calls: list[tuple[str, str]] = []

    live_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="noop",
            reason="quest_already_running",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "running",
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
    }
    reroute_status = {
        **live_status,
        "decision": "resume",
        "reason": "quest_stale_decision_after_write_stage_ready",
        "publication_supervisor_state": {
            "supervisor_phase": "write_stage_ready",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "continue_write_stage",
            "deferred_downstream_actions": ["continue_bundle_stage"],
            "controller_stage_note": "write stage is clear and should continue",
        },
    }

    def fake_ensure(*, profile, study_root, source):
        calls.append(("ensure", source))
        if source == "runtime_watch":
            return live_status
        if source == "runtime_watch_controller_reroute":
            return reroute_status
        raise AssertionError(f"unexpected ensure source: {source}")

    monkeypatch.setattr(module.study_runtime_router, "ensure_study_runtime", fake_ensure)
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [quest_root])
    monkeypatch.setattr(
        module,
        "run_watch_for_quest",
        lambda *, quest_root, controller_runners, apply: {
            "quest_root": str(quest_root),
            "quest_status": "running",
            "controllers": {
                "figure_loop_guard": {
                    "status": "blocked",
                    "action": "applied",
                    "blockers": ["figure_loop_budget_exceeded"],
                    "advisories": [],
                    "report_json": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.json"),
                    "report_markdown": str(quest_root / "artifacts" / "reports" / "figure_loop_guard" / "latest.md"),
                    "suppression_reason": None,
                    "quest_stop_applied": True,
                    "quest_stop_status": "stopped",
                    "quest_stop_deferred": False,
                    "quest_stop_defer_reason": None,
                }
            },
        },
    )

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("ensure", "runtime_watch"),
        ("ensure", "runtime_watch_controller_reroute"),
    ]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_stale_decision_after_write_stage_ready",
        }
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "noop",
            "preflight_reason": "quest_already_running",
            "applied_decision": "resume",
            "applied_reason": "quest_stale_decision_after_write_stage_ready",
            "source": "runtime_watch_controller_reroute",
        }
    ]
def test_run_watch_for_runtime_tracks_stopped_auto_continuation_once_router_returns_resume(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    resumed_stopped_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_waiting_on_invalid_blocking",
        ),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "publication_supervisor_state": {
            "supervisor_phase": "bundle_stage_blocked",
            "phase_owner": "publication_gate",
            "upstream_scientific_anchor_ready": True,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "complete_bundle_stage",
            "deferred_downstream_actions": [],
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
        },
        "continuation_state": {
            "quest_status": "stopped",
            "active_run_id": None,
            "continuation_policy": "auto",
            "continuation_anchor": "write",
            "continuation_reason": "decision:decision-continue-001",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "family_checkpoint_lineage": {
            "resume_contract": {
                "resume_mode": "resume_from_checkpoint",
                "resume_handle": "study_runtime_status:001-risk:blocked",
                "human_gate_required": False,
            }
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
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or resumed_stopped_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or resumed_stopped_status,
    )
    monkeypatch.setattr(
        module,
        "_refresh_managed_study_status_after_ensure",
        lambda *, profile, study_root, status_payload: status_payload,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [
        ("status", "001-risk"),
        ("ensure", "runtime_watch_auto_recovery"),
    ]
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "resume",
            "preflight_reason": "quest_waiting_on_invalid_blocking",
            "applied_decision": "resume",
            "applied_reason": "quest_waiting_on_invalid_blocking",
            "source": "runtime_watch_auto_recovery",
        }
    ]
    assert result["managed_study_supervision"][0]["health_status"] == "recovering"
def test_run_watch_for_runtime_does_not_project_blocked_explicit_rerun_as_recovering(
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

    blocked_stopped_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "continuation_state": {
            "quest_status": "stopped",
            "active_run_id": None,
            "continuation_policy": "auto",
            "continuation_anchor": "write",
            "continuation_reason": "decision:decision-continue-001",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
        },
        "family_checkpoint_lineage": {
            "resume_contract": {
                "resume_mode": "resume_from_checkpoint",
                "resume_handle": "study_runtime_status:001-risk:blocked",
                "human_gate_required": False,
            }
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
        lambda *, profile, study_root: blocked_stopped_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda **kwargs: pytest.fail("ensure_study_runtime should not run for blocked explicit rerun status"),
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_supervision"][0]["health_status"] == "inactive"
def test_run_watch_for_runtime_does_not_auto_recover_submission_metadata_parking(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    parked_status = {
        **make_study_runtime_status_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_waiting_for_submission_metadata",
        ),
        "quest_status": "waiting_for_user",
        "execution": {
            "engine": "med-deepscientist",
            "auto_entry": "on_managed_research_intent",
            "quest_id": "001-risk",
            "auto_resume": True,
        },
        "continuation_state": {
            "quest_status": "waiting_for_user",
            "active_run_id": None,
            "continuation_policy": "wait_for_user_or_resume",
            "continuation_anchor": "decision",
            "continuation_reason": "paper_bundle_submitted",
            "runtime_state_path": str(profile.runtime_root / "001-risk" / ".ds" / "runtime_state.json"),
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
        lambda *, profile, study_root: calls.append(("status", Path(study_root).name)) or parked_status,
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: calls.append(("ensure", source)) or parked_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        ensure_study_runtimes=True,
    )

    assert calls == [("status", "001-risk")]
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "quest_waiting_for_submission_metadata",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []
def test_watch_quest_writes_latest_runtime_watch_alias(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    latest_json = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    latest_markdown = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.md"

    assert result["latest_report_json"] == str(latest_json)
    assert result["latest_report_markdown"] == str(latest_markdown)
    assert latest_json.exists()
    assert latest_markdown.exists()
def test_watch_quest_emits_family_orchestration_companion_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    quest_root = make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_quest(
        quest_root=quest_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["session"]["quest_id"] == "q001"
    assert result["family_event_envelope"]["session"]["active_run_id"] == "run-1"
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_checkpoint_lineage"]["session"]["active_run_id"] == "run-1"
    assert result["family_human_gates"] == []
def test_watch_runtime_emits_family_orchestration_companion_fields(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_runtime(
        runtime_root=runtime_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "clear",
                "blockers": [],
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    assert result["family_event_envelope"]["version"] == "family-event-envelope.v1"
    assert result["family_event_envelope"]["payload"]["scanned_quest_count"] == 1
    assert result["family_checkpoint_lineage"]["version"] == "family-checkpoint-lineage.v1"
    assert result["family_human_gates"] == []
def test_watch_runtime_aggregates_publication_gate_human_confirmation_into_family_gates(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.runtime_watch")
    runtime_root = tmp_path / "runtime" / "quests"
    make_quest(tmp_path, "q001", status="running")

    result = module.run_watch_for_runtime(
        runtime_root=runtime_root,
        controller_runners={
            "publication_gate": lambda *, quest_root, apply: {
                "status": "blocked",
                "blockers": ["human_confirmation_required"],
                "current_required_action": "human_confirmation_required",
                "report_json": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json"),
                "report_markdown": str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.md"),
            }
        },
        apply=False,
    )

    quest_report = result["reports"][0]
    quest_gate = quest_report["family_human_gates"][0]
    runtime_gate = result["family_human_gates"][0]

    assert quest_gate["version"] == "family-human-gate.v1"
    assert quest_gate["gate_kind"] == "publication_gate_human_confirmation"
    assert quest_gate["request_surface"]["surface_kind"] == "runtime_watch"
    assert runtime_gate == quest_gate
    assert result["family_event_envelope"]["human_gate_hint"]["gate_id"] == quest_gate["gate_id"]
    assert result["family_checkpoint_lineage"]["resume_contract"]["human_gate_required"] is True
def test_watch_runtime_writes_study_supervision_report_and_escalates_after_consecutive_failures(
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

    def failing_status() -> dict[str, object]:
        return {
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
        }

    monkeypatch.setattr(
        module.study_runtime_router,
        "ensure_study_runtime",
        lambda *, profile, study_root, source: failing_status(),
    )
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
    latest_path = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    latest_payload = json.loads(latest_path.read_text(encoding="utf-8"))
    escalation_path = quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"

    assert first_supervision["health_status"] == "degraded"
    assert first_supervision["consecutive_failure_count"] == 1
    assert second_supervision["health_status"] == "escalated"
    assert second_supervision["consecutive_failure_count"] == 2
    assert second_supervision["needs_human_intervention"] is True
    assert latest_payload["health_status"] == "escalated"
    assert latest_payload["next_action_summary"]
    assert escalation_path.exists()
    escalation_payload = json.loads(escalation_path.read_text(encoding="utf-8"))

    assert escalation_payload["reason"] == "resume_request_failed"
    assert "runtime_event_ref" not in latest_payload
    assert not (quest_root / "artifacts" / "reports" / "runtime_events" / "latest.json").exists()
