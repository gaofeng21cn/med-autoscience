from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_research_pack_progress_summary_projects_from_current_control_state(
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
            "generated_at": "2026-05-04T06:00:00+00:00",
            "authority": "observability_only",
            "studies": [
                {
                    "study_id": "001-risk",
                    "quest_status": "running",
                    "active_run_id": "run-001",
                    "runtime_health": {"health_status": "escalated"},
                    "blocked_reason": "runtime_recovery_retry_budget_exhausted",
                    "latest_terminal_stage_log": {
                        "surface_kind": "mas_latest_terminal_stage_log_projection",
                        "read_model": "study_latest_terminal_stage_log_projection",
                        "authority": "observability_only",
                        "study_id": "001-risk",
                        "paper_stage_log": {
                            "surface_kind": "mas_paper_facing_stage_log_summary",
                            "stage_name": "write",
                            "research_pack_progress_summary": {
                                "surface_kind": "mas_research_pack_progress_summary",
                                "body_included": False,
                                "paper_body_included": False,
                                "deliverable_progress_delta": {
                                    "count": 1,
                                    "refs": ["studies/001-risk/paper/draft.md"],
                                },
                                "paper_progress_delta": {
                                    "count": 1,
                                    "refs": ["studies/001-risk/paper/draft.md"],
                                },
                                "platform_repair_delta": {
                                    "count": 1,
                                    "refs": [
                                        "studies/001-risk/artifacts/controller/currentness/latest.json"
                                    ],
                                    "counts_as_paper_progress": False,
                                },
                                "negative_result_count": 2,
                                "route_switch_count": 1,
                                "missing_reproducibility_refs": ["parameter_seed_refs"],
                                "single_next_owner_blocker": {
                                    "status": "blocked",
                                    "ref": "studies/001-risk/artifacts/blockers/next-owner.json",
                                    "candidate_count": 1,
                                    "body_included": False,
                                    "is_route_authority": False,
                                },
                            },
                        },
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

    assert result["refs"]["opl_current_control_state_handoff_path"] == str(handoff_path)
    research_pack_summary = result["research_pack_progress_summary"]
    assert research_pack_summary["body_included"] is False
    assert research_pack_summary["paper_body_included"] is False
    assert research_pack_summary["deliverable_progress_delta"]["count"] == 1
    assert research_pack_summary["paper_progress_delta"]["count"] == 1
    assert research_pack_summary["platform_repair_delta"] == {
        "count": 1,
        "refs": ["studies/001-risk/artifacts/controller/currentness/latest.json"],
        "counts_as_paper_progress": False,
    }
    assert research_pack_summary["negative_result_count"] == 2
    assert research_pack_summary["route_switch_count"] == 1
    assert research_pack_summary["missing_reproducibility_refs"] == ["parameter_seed_refs"]
    assert research_pack_summary["single_next_owner_blocker"]["ref"] == (
        "studies/001-risk/artifacts/blockers/next-owner.json"
    )
    assert research_pack_summary["single_next_owner_blocker"]["is_route_authority"] is False
    assert research_pack_summary["authority"]["is_route_authority"] is False
    assert research_pack_summary["authority"]["platform_repair_counts_as_paper_progress"] is False
