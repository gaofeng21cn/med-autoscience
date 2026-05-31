from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_handoff_action_keeps_scalar_remaining_blocker_text() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    action = module.current_owner_handoff_action(
        {
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "handoff_ready",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "paper_stage_log": {
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": "ai_reviewer_record_stale_after_current_inputs",
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["blocked_reason"] == "ai_reviewer_record_stale_after_current_inputs"


def test_current_owner_handoff_action_ignores_structured_remaining_blocker_payload() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    action = module.current_owner_handoff_action(
        {
            "opl_current_control_state_handoff": {
                "latest_terminal_stage_log": {
                    "status": "handoff_ready",
                    "action_type": "return_to_ai_reviewer_workflow",
                    "paper_stage_log": {
                        "current_owner": "ai_reviewer",
                        "remaining_blockers": {
                            "reason": "ai_reviewer_record_stale_after_current_inputs"
                        },
                    },
                },
            },
        }
    )

    assert action is not None
    assert action["blocked_reason"] is None


def test_existing_progress_projection_refreshes_stale_opl_handoff_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    mcp_adapter = importlib.import_module("med_autoscience.mcp_server_parts.projection_adapters")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量复评待推进。",
            "paper_stage_summary": "待 AI reviewer 复评。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T06:50:18+00:00",
                    "category": "controller_decision",
                    "source": "controller_decision",
                },
                {
                    "timestamp": "2026-05-30T06:50:08+00:00",
                    "category": "publication_eval",
                    "source": "publication_eval",
                },
            ],
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    "summary": (
                        "Produce a current AI reviewer publication-eval record before dispatching "
                        "the publication-eval workflow."
                    ),
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "generated_at": "2026-05-30T03:44:25+00:00",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
            },
            "ai_repair_lifecycle": {
                "surface": "ai_repair_lifecycle",
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "last_apply_attempt_at": "2026-05-30T05:57:59+00:00",
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "operator_verdict": {
                "summary": stale_next_step,
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
            "refs": {
                "ai_repair_lifecycle_path": "/tmp/repair_lifecycle/latest.json",
                "opl_current_control_state_handoff_path": "/tmp/opl_current_control_state/latest.json",
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert "request_opl_handoff_hydration" not in result["next_system_action"]
    assert result["opl_current_control_state_handoff"] is None
    assert result["ai_repair_lifecycle"] is None
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"
    assert result["user_visible_projection"]["paper_progress_state"]["next_owner"] == "ai_reviewer"
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"].get("handoff_source") is None
    assert result["refs"]["ai_repair_lifecycle_path"] is None
    assert result["refs"]["opl_current_control_state_handoff_path"] is None
    mcp_result = mcp_adapter.render_study_progress_result(result)
    mcp_structured = mcp_result["structuredContent"]
    mcp_markdown = mcp_result["content"][0]["text"]
    assert mcp_structured.get("ai_repair_lifecycle") is None
    assert mcp_structured["next_owner"] == "ai_reviewer"
    assert mcp_structured["user_visible_projection"]["next_owner"] == "ai_reviewer"
    assert "request_opl_handoff_hydration" not in mcp_markdown
    assert "external_supervisor" not in mcp_markdown


def test_existing_projection_refreshes_stale_lane_after_handoff_surface_removed(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量复评待推进。",
            "paper_stage_summary": "待 AI reviewer 复评。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T06:50:18+00:00",
                    "category": "controller_decision",
                    "source": "controller_decision",
                },
                {
                    "timestamp": "2026-05-30T06:50:08+00:00",
                    "category": "publication_eval",
                    "source": "publication_eval",
                },
                {
                    "timestamp": "2026-05-30T03:44:25+00:00",
                    "category": "opl_runtime_owner_handoff",
                    "source": "opl_runtime_owner_handoff",
                },
            ],
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
            "opl_current_control_state_handoff": None,
            "ai_repair_lifecycle": None,
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["intervention_lane"].get("handoff_source") is None
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"


def test_current_owner_receipt_consumption_suppresses_fresh_opl_owner_route(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量复评待推进。",
            "paper_stage_summary": "待 AI reviewer 复评。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T07:09:29+00:00",
                    "category": "opl_runtime_owner_handoff",
                    "source": "opl_runtime_owner_handoff",
                },
            ],
            "domain_transition": {
                "decision_type": "ai_reviewer_re_eval",
                "route_target": "review",
                "owner": "ai_reviewer",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
                "completion_receipt_consumption": {
                    "status": "consumed",
                    "receipt_kind": "ai_reviewer_publication_eval",
                    "receipt_ref": "artifacts/publication_eval/latest.json",
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "generated_at": "2026-05-30T07:09:29+00:00",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
                "owner_route": {
                    "owner_reason": "quest_waiting_opl_runtime_owner_route",
                    "source_refs": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    },
                },
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert result["opl_current_control_state_handoff"] is None
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["user_visible_projection"]["next_owner"] == "ai_reviewer"


def test_stale_opl_handoff_refresh_uses_route_target_when_owner_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 quest_waiting_opl_runtime_owner_route 或产出 typed blocker。"
    )
    status_payload = {
        "study_id": "001-risk",
        "publication_supervisor_state": {},
        "progress_projection": {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "current_stage": "publication_revision",
            "current_stage_summary": "同线质量修复待推进。",
            "paper_stage_summary": "待 write owner 完成当前性复核。",
            "next_system_action": stale_next_step,
            "needs_physician_decision": False,
            "current_blockers": [],
            "latest_events": [
                {
                    "timestamp": "2026-05-30T10:15:14+00:00",
                    "category": "controller_decision",
                    "source": "controller_decision",
                },
            ],
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "route_target": "write",
                "next_work_unit": {
                    "unit_id": "medical_prose_currentness_recheck",
                },
            },
            "opl_current_control_state_handoff": {
                "surface_kind": "opl_current_control_state_study_handoff",
                "generated_at": "2026-05-30T09:33:57+00:00",
                "next_owner": "external_supervisor",
                "external_supervisor_required": True,
                "blocked_reason": "quest_waiting_opl_runtime_owner_route",
                "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "quest_waiting_opl_runtime_owner_route",
                "summary": stale_next_step,
                "handoff_source": "opl_current_control_state.next_owner",
            },
            "user_visible_projection": {
                "surface_kind": "study_progress_user_visible_projection",
                "schema_version": 2,
                "next_owner": "external_supervisor",
                "next_step": stale_next_step,
                "next_system_action": stale_next_step,
                "paper_progress_state": {"next_owner": "external_supervisor"},
            },
        },
    }

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload=status_payload,
        materialize_read_model_artifacts=False,
    )

    assert "medical_prose_currentness_recheck" in result["next_system_action"]
    assert result["opl_current_control_state_handoff"] is None
    assert result["intervention_lane"]["route_target"] == "write"
    assert result["intervention_lane"].get("handoff_source") is None
    assert result["user_visible_projection"]["next_owner"] == "write"
    assert result["user_visible_projection"]["paper_progress_state"]["next_owner"] == "write"
