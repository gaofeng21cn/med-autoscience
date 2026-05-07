from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_emits_canonical_user_visible_projection(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profiler = importlib.import_module("med_autoscience.controllers.study_cycle_profiler")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "verdict": {"summary": "当前发表判断仍需补齐证据。"},
            "recommended_actions": [{"summary": "补齐外部验证证据。"}],
        },
    )
    monkeypatch.setattr(profiler, "profile_study_cycle", lambda **_: {})

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "blocked",
            "reason": "missing_external_validation",
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    user_projection = result["user_visible_projection"]
    assert user_projection["surface"] == "study_progress_user_visible_projection"
    assert user_projection["read_model"] == "study_progress_user_visible_read_model"
    assert user_projection["authority"] == "truth_projection"
    assert user_projection["projection_only"] is True
    assert user_projection["answer_focus"] == [
        "current_stage",
        "current_blockers",
        "next_step",
        "evidence",
    ]
    assert user_projection["study_id"] == result["study_id"]
    assert user_projection["quest_id"] == result["quest_id"]
    assert user_projection["current_stage"] == result["current_stage"]
    assert user_projection["current_stage_summary"] == result["current_stage_summary"]
    assert user_projection["paper_stage"] == result["paper_stage"]
    assert user_projection["paper_stage_summary"] == result["paper_stage_summary"]
    assert user_projection["current_blockers"] == result["current_blockers"]
    assert user_projection["next_system_action"] == result["next_system_action"]
    assert user_projection["evidence"]["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert {
        item["type"]: item["status"]
        for item in user_projection["conditions"]
    } == {
        "stage_known": "true",
        "blocked": "true",
        "next_action_known": "true",
        "evidence_available": "true",
        "human_decision_required": "false",
        "runtime_supervised": "true",
    }
