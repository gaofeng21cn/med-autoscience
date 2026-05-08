from __future__ import annotations

from tests.test_runtime_watch_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_watch_for_runtime_dry_run_reports_stopped_controller_guard_recovery_without_executing(
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

    assert calls == [("status", "001-risk"), ("status", "001-risk")]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
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

def test_run_watch_for_runtime_dry_run_tracks_stopped_auto_continuation_without_executing(
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
            "engine": "mas-runtime-core",
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
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

    assert calls == [("status", "001-risk")]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_waiting_on_invalid_blocking",
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
            "engine": "mas-runtime-core",
                "runtime_backend_id": "mas_runtime_core",
                "runtime_engine_id": "mas-runtime-core",
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
