from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_stale_opl_handoff_refresh_uses_route_target_when_owner_missing(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress.projection")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk", quest_id="quest-001")
    stale_next_step = (
        "等待 external_supervisor owner 执行 request_opl_handoff_hydration，"
        "关闭 opl_stage_attempt_admission_required 或产出 typed blocker。"
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
                "blocked_reason": "opl_stage_attempt_admission_required",
                "why_not_applied": ["opl_stage_attempt_admission_required"],
            },
            "intervention_lane": {
                "lane_id": "quality_floor_blocker",
                "route_target": "external_supervisor",
                "route_key_question": "opl_stage_attempt_admission_required",
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
