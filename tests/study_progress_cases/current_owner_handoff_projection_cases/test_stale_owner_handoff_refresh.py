from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_current_owner_receipt_consumption_suppresses_fresh_opl_owner_route(tmp_path: Path) -> None:
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
                "blocked_reason": "opl_stage_attempt_admission_required",
                "why_not_applied": ["opl_stage_attempt_admission_required"],
                "owner_route": {
                    "owner_reason": "opl_stage_attempt_admission_required",
                    "source_refs": {
                        "work_unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                    },
                },
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

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert_default_next_action_legacy_surfaces_retired(result)
    assert result["next_action"]["surface_kind"] == "mas_next_action_envelope"
    assert result["opl_current_control_state_handoff"] is None
    assert result["intervention_lane"]["route_target"] == "review"
    assert result["user_visible_projection"]["next_owner"] == "review"


def test_owner_receipt_recovery_visibility_supersedes_stale_anti_loop_lane() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress.projection_payload_assembly.paper_recovery_visibility"
    )
    receipt_ref = "/tmp/studies/002/artifacts/controller/gate_clearing_batch/latest.json"
    stale_next_step = (
        "等待 one-person-lab owner 处理当前 handoff，"
        "关闭 anti_loop_budget_exhausted 或产出 typed blocker。"
    )
    payload = {
        "study_id": "002-dm-china-us-mortality-attribution",
        "current_stage": "queued",
        "next_system_action": stale_next_step,
        "next_step": stale_next_step,
        "why_not_progressing": "owner_receipt_recorded",
        "current_blockers": ["anti_loop_budget_exhausted"],
        "current_work_unit": {
            "status": "owner_receipt_recorded",
            "owner": "gate_clearing_batch",
            "action_type": "run_gate_clearing_batch",
            "work_unit_id": "publication_gate_replay",
            "work_unit_fingerprint": "publication-blockers::497d1260db522f01",
            "state": {
                "state_kind": "owner_receipt_recorded",
                "next_safe_action_kind": "consume_owner_receipt",
                "owner_receipt_ref": receipt_ref,
            },
        },
        "current_execution_envelope": {
            "state_kind": "owner_receipt_recorded",
            "owner": "gate_clearing_batch",
            "typed_blocker": None,
        },
        "paper_recovery_state": {
            "phase": "owner_receipt_recorded",
            "current_authority": {"owner": "gate_clearing_batch"},
            "next_safe_action": {
                "kind": "consume_owner_receipt",
                "owner": "gate_clearing_batch",
                "provider_admission_allowed": False,
                "owner_receipt_ref": receipt_ref,
            },
        },
        "intervention_lane": {
            "lane_id": "current_owner_action_ready",
            "summary": stale_next_step,
            "route_target": "one-person-lab",
            "route_key_question": "anti_loop_budget_exhausted",
            "handoff_source": "opl_current_control_state.next_owner",
        },
        "operator_verdict": {
            "lane_id": "current_owner_action_ready",
            "summary": stale_next_step,
            "route_key_question": "anti_loop_budget_exhausted",
        },
        "operator_status_card": {
            "current_focus": "anti_loop_budget_exhausted",
            "paper_recovery_phase": "owner_receipt_recorded",
        },
        "user_visible_projection": {
            "next_step": stale_next_step,
            "why_not_progressing": "owner_receipt_recorded",
            "current_blockers": ["anti_loop_budget_exhausted"],
        },
    }

    result = module.apply_paper_recovery_state_user_visible_status(payload)

    assert result["next_system_action"] == "Consume the current owner receipt through MAS owner authority."
    assert result["next_step"] == result["next_system_action"]
    assert result["intervention_lane"]["lane_id"] == "paper_recovery_owner_receipt_recorded"
    assert result["intervention_lane"]["recommended_action_id"] == "consume_owner_receipt"
    assert result["intervention_lane"]["authority_owner"] == "gate_clearing_batch"
    assert "route_target" not in result["intervention_lane"]
    assert "anti_loop_budget_exhausted" not in result["intervention_lane"].get("summary", "")
    assert "route_key_question" not in result["intervention_lane"]
    assert result["operator_status_card"]["current_focus"] == result["next_system_action"]
    assert result["operator_verdict"]["summary"] == result["next_system_action"]
    assert "route_key_question" not in result["operator_verdict"]
    assert "handoff_source" not in result["operator_verdict"]
    assert result["user_visible_projection"]["next_step"] == result["next_system_action"]
    assert result["user_visible_projection"]["why_not_progressing"] == "owner_receipt_recorded"


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
