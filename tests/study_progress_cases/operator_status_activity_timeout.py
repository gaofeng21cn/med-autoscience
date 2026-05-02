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
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-002"
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
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)

    monkeypatch.setattr(
        module,
        "_progress_freshness_now",
        lambda: datetime(2026, 5, 2, 10, 0, tzinfo=timezone.utc),
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
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
    assert result["intervention_lane"]["lane_id"] == "runtime_recovery_required"
    assert result["operator_status_card"]["handling_state"] == "runtime_recovering"
    assert result["operator_status_card"]["human_surface_freshness"] == "monitoring_runtime"
    assert "meaningful artifact delta" in result["operator_status_card"]["next_confirmation_signal"]


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
