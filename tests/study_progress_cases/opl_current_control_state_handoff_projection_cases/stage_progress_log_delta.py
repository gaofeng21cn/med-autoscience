from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_stage_progress_log_alone_does_not_trigger_platform_repair_delta(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "runtime" / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "healthy"},
                    "stage_progress_log": {"attempt_count": 1},
                    "blocked_reason": "waiting_for_quality_owner",
                    "next_owner": "write",
                }
            ],
        },
    )

    monkeypatch.setattr(
        module.domain_status_projection,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "continue",
            "reason": "quality_repair_followthrough",
            "runtime_health_snapshot": {"attempt_state": "running"},
            "authority_snapshot": {"control_state": "active"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    assert result["paper_progress_delta"]["count"] == 0
    assert result["paper_progress_delta"]["token_usage_total"] is None
    assert result["platform_repair_delta"]["count"] == 0
    assert result["platform_repair_delta"]["token_usage_total"] is None
