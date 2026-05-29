from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_platform_only_repair_projects_next_forced_paper_delta_without_counting_paper_progress(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    handoff_path = profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"
    _write_json(
        handoff_path,
        {
            "surface": "opl_current_control_state_handoff_projection",
            "schema_version": 1,
            "generated_at": "2026-05-29T00:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "escalated"},
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "next_owner": "runtime_mechanism_repair",
                    "owner_route": {
                        "next_owner": "runtime_mechanism_repair",
                        "source_refs": {
                            "work_unit_id": "publishability_repair_sprint",
                            "source_eval_id": "eval-current",
                        },
                        "source_fingerprint": "source-current",
                    },
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
            "decision": "blocked",
            "reason": "runtime_recovery_retry_budget_exhausted",
            "runtime_health_snapshot": {"attempt_state": "escalated"},
            "authority_snapshot": {"control_state": "blocked_runtime_escalation"},
        },
    )
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["deliverable_progress_delta"] == result["paper_progress_delta"]
    assert result["paper_progress_delta"]["count"] == 0
    assert result["platform_repair_delta"]["count"] == 1
    assert result["progress_delta_classification"] == "platform_repair"
    assert result["progress_first_sprint_state"]["deliverable_progress_delta"] == result["paper_progress_delta"]
    assert result["progress_first_sprint_state"]["classification"] == "platform_repair"
    assert result["progress_first_sprint_state"]["paper_progress_delta_counted"] is False
    assert result["next_forced_delta"]["required_delta_kind"] == "paper_progress_delta_or_typed_blocker"
    assert result["next_forced_delta"]["work_unit_id"] == "publishability_repair_sprint"
