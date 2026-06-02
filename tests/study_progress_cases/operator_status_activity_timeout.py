from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_activity_timeout_takes_priority_over_paper_surface_refresh_gap(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "emitted_at": "2026-05-02T08:30:00+00:00",
            "verdict": {
                "overall_verdict": "blocked",
                "summary": "论文门控仍 blocked，投稿包镜像也 stale。",
            },
            "gaps": [
                {
                    "gap_id": "stale_study_delivery_mirror",
                    "gap_type": "delivery_surface",
                    "severity": "must_fix",
                    "summary": "study 目录里的投稿包镜像已经过期，仍停在旧版本，不能当作当前包。",
                }
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "002-risk",
            "quest_id": "quest-002",
            "state": "breach",
            "breach_types": ["read_churn_without_artifact_delta"],
            "last_meaningful_progress_at": "2026-05-01T18:30:00+00:00",
            "mds_progress_markers": {
                "meaningful_artifact_delta_at": "2026-05-01T18:30:00+00:00",
                "meaningful_artifact_delta_kind": "paper_bundle",
            },
        },
    )
    _write_domain_health_diagnostic(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 10, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-live-stale",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-stale",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-stale",
                    "worker_running": True,
                },
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "科学真相还在推进，给人看的投稿包需要同步刷新。",
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_id": "quest-002",
                "quest_status": "running",
                "active_run_id": "run-live-stale",
                "browser_url": "http://127.0.0.1:21999/quests/quest-002",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-live-stale",
                "current_required_action": "supervise_runtime_only",
                "publication_gate_allows_direct_write": False,
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MAS 外环监管心跳新鲜。",
                "latest_recorded_at": "2026-05-02T09:59:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["progress_freshness"]["activity_timeout"]["state"] == "timed_out"
    assert result["progress_freshness"]["activity_timeout"]["progress_pressure"] == {
        "surface": "progress_first_activity_timeout_pressure",
        "status": "advance_now",
        "purpose": "continue_progress",
        "timeout_is_terminal_failure": False,
        "no_progress_is_terminal_failure": False,
        "continuation_required": True,
        "next_owner": "one-person-lab",
        "next_action_type": "continue_or_relaunch",
        "quality_gate_relaxation_allowed": False,
    }
    assert result["intervention_lane"]["lane_id"] == "runtime_recovery_required"
    assert result["intervention_lane"]["progress_pressure"]["timeout_is_terminal_failure"] is False
    assert result["intervention_lane"]["terminal_failure"] is False
    assert result["operator_status_card"]["handling_state"] == "runtime_recovering"
    assert result["operator_status_card"]["human_surface_freshness"] == "monitoring_runtime"
    assert "meaningful artifact delta" in result["operator_status_card"]["next_confirmation_signal"]


def test_runtime_health_snapshot_recovery_dominates_stale_live_runtime_module_projection(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "002-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-002"
    _write_json(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        {
            "schema_version": 1,
            "recorded_at": "2026-05-02T10:55:00+00:00",
            "study_id": "002-risk",
            "study_root": str(study_root),
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "health_status": "live",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-live-stale",
            "runtime_decision": "noop",
            "runtime_reason": "quest_already_running",
            "quest_status": "running",
            "next_action": "continue_supervising_runtime",
            "next_action_summary": "继续监督当前托管运行，并等待新的阶段事件。",
            "summary": "托管运行时在线，研究仍在自动推进。",
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "002-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-002",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "worker_running": True,
            "active_run_id": "run-live-stale",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-stale",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-stale",
                    "worker_running": True,
                },
            },
            "runtime_health_snapshot": {
                "surface": "runtime_health_snapshot",
                "study_id": "002-risk",
                "quest_id": "quest-002",
                "attempt_state": "recovering",
                "canonical_runtime_action": "recover_runtime",
                "retry_budget_remaining": 2,
                "worker_liveness_state": {
                    "state": "activity_timeout",
                    "runtime_liveness_status": "live",
                    "worker_running": True,
                    "active_run_id": "run-live-stale",
                },
                "blocking_reasons": ["live_worker_meaningful_artifact_delta_timeout"],
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_id": "quest-002",
                "quest_status": "running",
                "active_run_id": "run-live-stale",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "active_run_id": "run-live-stale",
                "current_required_action": "supervise_runtime_only",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "latest_recorded_at": "2026-05-02T11:00:00+00:00",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="002-risk")

    assert result["current_stage"] == "managed_runtime_recovering"
    assert result["supervision"]["health_status"] == "recovering"
    assert result["module_surfaces"]["runtime"]["health_status"] == "recovering"
    assert result["module_surfaces"]["runtime"]["next_action_summary"] != "继续监督当前托管运行，并等待新的阶段事件。"


def test_study_progress_does_not_extend_new_run_grace_from_fresh_supervisor_ticks(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-dpcc",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="clinical_epidemiology",
    )
    quest_root = profile.managed_runtime_home / "quests" / "quest-003"
    _write_publication_eval(study_root, quest_root)
    _write_json(
        study_root / "artifacts" / "autonomy" / "slo_status" / "latest.json",
        {
            "surface": "autonomy_progress_slo_status",
            "schema_version": 1,
            "study_id": "003-dpcc",
            "quest_id": "quest-003",
            "state": "breach",
            "breach_types": ["same_fingerprint_loop"],
            "mds_progress_markers": {},
            "quality_gate_relaxation_allowed": False,
        },
    )
    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "003-dpcc",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-003", "auto_resume": True},
            "quest_id": "quest-003",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "runtime_liveness_status": "live",
            "active_run_id": "run-stalled",
            "worker_running": True,
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-stalled",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-stalled",
                    "worker_running": True,
                    "worker_watchdog": {
                        "started_at": "2026-05-02T10:00:00+00:00",
                        "last_output_at": "2026-05-02T10:01:00+00:00",
                        "last_seen_at": "2026-05-02T14:30:00+00:00",
                    },
                },
            },
            "autonomous_runtime_notice": {
                "required": True,
                "quest_status": "running",
                "active_run_id": "run-stalled",
                "browser_url": "http://127.0.0.1:20999",
            },
            "execution_owner_guard": {
                "owner": "managed_runtime",
                "supervisor_only": True,
                "guard_reason": "live_managed_runtime",
                "active_run_id": "run-stalled",
                "current_required_action": "supervise_managed_runtime",
                "publication_gate_allows_direct_write": False,
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-stalled",
                "continuation_policy": "auto",
                "continuation_anchor": "decision",
                "continuation_reason": "controller_work_unit_pending",
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "current_required_action": "return_to_publishability_gate",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
                "latest_recorded_at": "2026-05-02T14:30:00+00:00",
            },
            "runtime_health_snapshot": {
                "generated_at": "2026-05-02T14:30:00+00:00",
                "dominant_runtime_refs": [
                    {
                        "recorded_at": "2026-05-02T14:30:00+00:00",
                    }
                ],
            },
        },
    )
    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 14, 30, tzinfo=timezone.utc),
    )

    result = module.read_study_progress(profile=profile, study_id="003-dpcc")

    assert result["progress_freshness"]["worker_liveness_freshness"]["status"] == "fresh"
    assert result["progress_freshness"]["meaningful_artifact_delta_freshness"]["status"] == "missing"
    assert result["progress_freshness"]["activity_timeout"]["state"] == "timed_out"
    assert "new_run_grace" not in result["progress_freshness"]["activity_timeout"]
    assert result["intervention_lane"]["lane_id"] == "runtime_recovery_required"


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
