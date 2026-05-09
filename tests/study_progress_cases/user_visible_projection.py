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
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
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
    assert user_projection["schema_version"] == 2
    assert user_projection["authority"] == "truth_projection"
    assert user_projection["projection_only"] is True
    assert user_projection["answer_focus"] == [
        "writer_state",
        "package_delivered",
        "actual_write_active",
        "user_next",
        "user_action_required",
        "evidence",
    ]
    macro_state = result["study_macro_state"]
    assert user_projection["study_id"] == result["study_id"]
    assert user_projection["quest_id"] == result["quest_id"]
    assert user_projection["writer_state"] == macro_state["writer_state"]
    assert user_projection["user_next"] == macro_state["user_next"]
    assert user_projection["reason"] == macro_state["reason"]
    assert user_projection["current_stage"] == macro_state["writer_state"]
    assert user_projection["state_label"]
    assert user_projection["state_summary"]
    assert user_projection["evidence"]["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert user_projection["evidence_refs"]["publication_eval_path"] == str(publication_eval_path)
    assert {
        item["type"]: item["status"]
        for item in user_projection["conditions"]
    } == {
        "macro_state_known": "true",
        "package_delivered": "false",
        "actual_write_active": "false",
        "blocked": "true",
        "next_action_known": "true",
        "evidence_available": "true",
        "user_action_required": "false",
        "runtime_supervised": "true",
    }


def test_user_visible_projection_uses_macro_state_as_single_user_status() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    payload = {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "current_stage": "legacy_top_level_stage",
        "current_stage_summary": "Legacy top-level stage should not drive the user visible state.",
        "current_blockers": ["legacy blocker"],
        "next_system_action": "legacy next action",
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "001-risk",
            "writer_state": "parked",
            "user_next": "submit_info",
            "reason": "external_info",
            "details": {
                "package_delivered": True,
                "missing_external_info": ["authors", "ethics"],
                "active_run_id": None,
            },
            "conditions": [
                {
                    "type": "ExternalInfoPending",
                    "status": "true",
                    "summary": "submission package waits for external metadata",
                }
            ],
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }

    projection = module.build_user_visible_projection(payload)

    assert projection["writer_state"] == "parked"
    assert projection["user_next"] == "submit_info"
    assert projection["reason"] == "external_info"
    assert projection["package_delivered"] is True
    assert projection["actual_write_active"] is False
    assert projection["user_action_required"] is True
    assert projection["state_label"] == "投稿包已交付，等待外部投稿信息"
    assert projection["current_stage"] == "parked"
    assert projection["current_blockers"] == ["缺少外部投稿信息: authors, ethics"]
    assert "投稿包已交付" in projection["state_summary"]
    assert projection["evidence_refs"]["publication_eval_path"] == "/tmp/publication_eval/latest.json"


def test_user_visible_projection_fails_closed_when_top_level_writer_conflicts_with_macro_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    projection = module.build_user_visible_projection(
        {
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "active_run_id": "run-legacy",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "001-risk",
                "writer_state": "parked",
                "user_next": "submit_info",
                "reason": "external_info",
                "details": {"package_delivered": True},
                "conditions": [],
            },
        }
    )

    assert projection["state"] == "inspect/conflict"
    assert projection["writer_state"] == "conflict"
    assert projection["user_next"] == "inspect"
    assert projection["reason"] == "truth_conflict"
    assert projection["actual_write_active"] is False
    assert projection["state_label"] == "状态需要检查"
    assert projection["conflict_reason"] == "macro_state_conflict"


def test_user_visible_projection_fails_closed_without_macro_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    projection = module.build_user_visible_projection(
        {
            "study_id": "001-risk",
            "current_stage": "manual_finishing",
            "current_blockers": [],
        }
    )

    assert projection["state"] == "inspect/conflict"
    assert projection["writer_state"] == "conflict"
    assert projection["conflict_reason"] == "missing_macro_state"


def test_user_visible_projection_does_not_call_live_worker_active_without_artifact_delta() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")

    projection = module.build_user_visible_projection(
        {
            "study_id": "002-dm",
            "active_run_id": "run-live-control-only",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "002-dm",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "run-live-control-only"},
                "conditions": [],
            },
            "progress_freshness": {
                "status": "stale",
                "meaningful_artifact_delta_freshness": {
                    "status": "missing",
                    "latest_progress_at": None,
                },
                "activity_timeout": {
                    "state": "at_risk",
                    "breach_types": ["same_fingerprint_loop"],
                },
            },
            "supervision": {
                "active_run_id": "run-live-control-only",
                "health_status": "live",
            },
        }
    )

    assert projection["state_label"] == "自动运行中"
    assert projection["actual_write_active"] is False
    assert "实际 writer/run 正在推进" not in projection["state_summary"]
    condition = next(item for item in projection["conditions"] if item["type"] == "actual_write_active")
    assert condition["reason"] == "writer_inactive"


def test_user_visible_projection_labels_all_macro_state_classes() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    cases = [
        (
            {"writer_state": "live", "user_next": "watch", "reason": "runtime", "details": {"active_run_id": "run-1"}},
            "自动运行中",
            True,
            False,
        ),
        (
            {"writer_state": "queued", "user_next": "watch", "reason": "runtime", "details": {}},
            "系统排队处理中",
            False,
            False,
        ),
        (
            {"writer_state": "parked", "user_next": "none", "reason": "runtime", "details": {"package_delivered": True}},
            "投稿包已交付，自动停驻",
            False,
            False,
        ),
        (
            {
                "writer_state": "parked",
                "user_next": "submit_info",
                "reason": "external_info",
                "details": {"package_delivered": True, "missing_external_info": ["authors"]},
            },
            "投稿包已交付，等待外部投稿信息",
            False,
            True,
        ),
        (
            {"writer_state": "parked", "user_next": "none", "reason": "user_stop", "details": {}},
            "用户暂停/手动停驻",
            False,
            True,
        ),
        (
            {"writer_state": "queued", "user_next": "repair", "reason": "quality", "details": {}},
            "质量修复/复审中",
            False,
            False,
        ),
        (
            {"writer_state": "parked", "user_next": "none", "reason": "stop_loss", "details": {}},
            "止损/终止",
            False,
            True,
        ),
    ]

    for macro_fields, expected_label, expected_write_active, expected_user_action in cases:
        projection = module.build_user_visible_projection(
            {
                "study_id": "001-risk",
                "study_macro_state": {
                    "surface": "study_macro_state",
                    "schema_version": 1,
                    "study_id": "001-risk",
                    "conditions": [],
                    **macro_fields,
                },
            }
        )

        assert projection["state_label"] == expected_label
        assert projection["actual_write_active"] is expected_write_active
        assert projection["user_action_required"] is expected_user_action
