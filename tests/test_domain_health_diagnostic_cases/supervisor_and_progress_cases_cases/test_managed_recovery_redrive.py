from __future__ import annotations

from tests.test_domain_health_diagnostic_cases import shared as _shared

globals().update({
    name: value
    for name, value in vars(_shared).items()
    if not name.startswith('__')
})

def test_run_domain_health_diagnostic_for_runtime_dry_run_reports_stopped_controller_guard_recovery_without_executing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    stopped_guard_status = {
        **make_progress_projection_payload(
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
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: calls.append(("status", Path(study_root).name)) or stopped_guard_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls == [("status", "001-risk")]
    assert result["managed_study_auto_recoveries"] == []
    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "resume",
            "reason": "quest_stopped_by_controller_guard",
        }
    ]

def test_run_domain_health_diagnostic_for_runtime_rechecks_managed_study_immediately_after_figure_loop_guard_stop(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
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
        **make_progress_projection_payload(
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
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: calls.append(("status", Path(study_root).name)) or live_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [quest_root])
    monkeypatch.setattr(
        module,
        "run_domain_health_diagnostic_for_quest",
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

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=True,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert calls[:2] == [("status", "001-risk"), ("status", "001-risk")]
    assert {study_id for _, study_id in calls} == {"001-risk"}
    assert result["managed_study_actions"][0]["study_id"] == "001-risk"
    assert result["managed_study_actions"][0]["decision"] == "blocked"
    assert result["managed_study_actions"][0]["reason"] == "quest_waiting_opl_runtime_owner_route"
    assert result["managed_study_actions"][0]["resume_postcondition"]["typed_blocker"]["owner"] == "one-person-lab"
    assert result["managed_study_auto_recoveries"] == [
        {
            "study_id": "001-risk",
            "preflight_decision": "blocked",
            "preflight_reason": "quest_waiting_opl_runtime_owner_route",
            "applied_decision": "blocked",
            "applied_reason": "quest_waiting_opl_runtime_owner_route",
            "source": "domain_health_diagnostic_controller_reroute",
        }
    ]

def test_run_domain_health_diagnostic_for_runtime_dry_run_tracks_stopped_auto_continuation_without_executing(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    calls: list[tuple[str, str]] = []

    resumed_stopped_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="resume",
            reason="quest_waiting_on_invalid_blocking",
        ),
        "quest_status": "stopped",
        "execution": {
            "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
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
                "resume_handle": "progress_projection:001-risk:blocked",
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
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: calls.append(("status", Path(study_root).name)) or resumed_stopped_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
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
    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    assert handoff["status"] == "handoff_required"
    assert handoff["runtime_owner"] == "one-person-lab"
    assert handoff["typed_blocker"]["blocker_type"] == "opl_runtime_owner_handoff_required"

def test_run_domain_health_diagnostic_for_runtime_does_not_project_blocked_explicit_rerun_as_recovering(
    tmp_path: Path,
    monkeypatch,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.domain_health_diagnostic")
    helpers = importlib.import_module("tests.study_runtime_test_helpers")
    profile = helpers.make_profile(tmp_path)
    study_root = profile.workspace_root / "studies" / "001-risk"
    study_root.mkdir(parents=True, exist_ok=True)
    dump_json(study_root / "study.yaml", {"study_id": "001-risk"})
    quest_root = profile.runtime_root / "001-risk"

    blocked_stopped_status = {
        **make_progress_projection_payload(
            study_id="001-risk",
            decision="blocked",
            reason="quest_stopped_requires_explicit_rerun",
        ),
        "study_root": str(study_root),
        "quest_root": str(quest_root),
        "quest_status": "stopped",
        "execution": {
            "engine": "opl-hosted-stage-runtime",
                "opl_runtime_ref": "opl_hosted_stage_runtime",
                "runtime_ref": "opl_hosted_stage_runtime",
                "runtime_engine_id": "opl-hosted-stage-runtime",
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
                "resume_handle": "progress_projection:001-risk:blocked",
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
        module.domain_status_projection,
        "progress_projection",
        lambda *, profile, study_root, **kwargs: blocked_stopped_status,
    )
    monkeypatch.setattr(module.quest_state, "iter_active_quests", lambda runtime_root: [])

    result = module.run_domain_health_diagnostic_for_runtime(
        runtime_root=profile.runtime_root,
        controller_runners={},
        apply=False,
        profile=profile,
        request_opl_stage_attempts=True,
    )

    assert result["managed_study_actions"] == [
        {
            "study_id": "001-risk",
            "decision": "blocked",
            "reason": "quest_stopped_requires_explicit_rerun",
        }
    ]
    assert result["managed_study_auto_recoveries"] == []
    handoff = result["managed_study_opl_runtime_owner_handoffs"][0]
    assert handoff["status"] == "handoff_required"
    assert handoff["runtime_owner"] == "one-person-lab"
    assert handoff["mas_materializes_runtime_supervision"] is False
