from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_redrive_projection_prefers_current_opl_owner_handoff_over_stale_transition() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {
                "decision_owner": "ai_reviewer",
                "route_owner": "ai_reviewer",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
            "conditions": [
                {
                    "type": "DomainTransitionRedrive",
                    "status": "true",
                    "summary": "current domain transition names an owner work unit",
                }
            ],
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "next_owner": "write",
            "blocked_reason": "manuscript_story_surface_delta_missing",
            "action_queue": [
                {
                    "action_type": "run_quality_repair_batch",
                    "status": "queued",
                    "owner": "write",
                    "summary": "The current AI reviewer-backed write route requires manuscript story-surface repair.",
                }
            ],
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_target_label": "独立审阅与质控",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "operator_verdict": {
            "surface_kind": "study_operator_verdict",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "reason_summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "recovery_contract": {
            "contract_kind": "study_recovery_contract",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "autonomy_contract": {
            "contract_kind": "study_autonomy_contract",
            "next_signal": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "write owner" in result["next_system_action"]
    assert "run_quality_repair_batch" in result["next_system_action"]
    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" not in result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "write"
    assert result["user_visible_projection"]["next_step"] == result["next_system_action"]
    assert result["intervention_lane"]["route_target"] == "write"
    assert result["intervention_lane"]["route_key_question"] == "manuscript_story_surface_delta_missing"
    assert result["operator_verdict"]["summary"] == result["next_system_action"]
    assert result["operator_verdict"]["route_target"] == "write"
    assert result["recovery_contract"]["summary"] == result["next_system_action"]
    assert result["recovery_contract"]["route_target"] == "write"
    assert result["autonomy_contract"]["next_signal"] == result["next_system_action"]


def test_user_visible_projection_uses_current_domain_transition_owner_when_handoff_shell_is_stale() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "latest_events": [
            {
                "timestamp": "2026-05-30T10:20:17+00:00",
                "category": "controller_decision",
                "source": "controller_decision",
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
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "details": {
                "route_owner": "ai_reviewer",
                "route_target": "review",
                "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "generated_at": "2026-05-30T09:33:57+00:00",
            "next_owner": None,
            "blocked_reason": None,
            "latest_terminal_stage_log": {
                "generated_at": "2026-05-30T10:26:13+00:00",
                "status": "handoff_ready",
                "action_type": "return_to_ai_reviewer_workflow",
                "paper_stage_log": {
                    "current_owner": "ai_reviewer",
                    "remaining_blockers": [],
                },
            },
        },
    }

    projection = module.build_user_visible_projection(payload)

    assert projection["next_owner"] == "ai_reviewer"
    assert projection["paper_progress_state"]["next_owner"] == "ai_reviewer"


def test_redrive_projection_prefers_explicit_handoff_owner_over_stale_terminal_log() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "ai_reviewer_re_eval",
            "route_target": "review",
            "owner": "ai_reviewer",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "conditions": [
                {
                    "type": "DomainTransitionRedrive",
                    "status": "true",
                    "summary": "current domain transition names an owner work unit",
                }
            ],
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "quest_status": "waiting_for_user",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
            "action_queue": [],
            "latest_terminal_stage_log": {
                "surface_kind": "mas_latest_terminal_stage_log_projection",
                "action_type": "return_to_ai_reviewer_workflow",
                "status": "handoff_ready",
                "paper_stage_log": {
                    "current_owner": "ai_reviewer",
                    "problem_summary": "Stale terminal log should not override explicit OPL handoff owner.",
                },
            },
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "operator_verdict": {
            "surface_kind": "study_operator_verdict",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "reason_summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "recovery_contract": {
            "contract_kind": "study_recovery_contract",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "autonomy_contract": {
            "contract_kind": "study_autonomy_contract",
            "next_signal": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "external_supervisor owner" in result["next_system_action"]
    assert "request_opl_handoff_hydration" in result["next_system_action"]
    assert "quest_waiting_opl_runtime_owner_route" in result["next_system_action"]
    assert "return_to_ai_reviewer_workflow" not in result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "external_supervisor"
    assert result["intervention_lane"]["route_target"] == "external_supervisor"
    assert result["intervention_lane"]["route_key_question"] == "quest_waiting_opl_runtime_owner_route"
    assert result["operator_verdict"]["route_target"] == "external_supervisor"
    assert result["recovery_contract"]["route_target"] == "external_supervisor"
    assert result["autonomy_contract"]["next_signal"] == result["next_system_action"]


def test_redrive_projection_ignores_handoff_older_than_current_controller_truth() -> None:
    handoff_projection = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "quest_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "latest_events": [
            {
                "timestamp": "2026-05-30T06:50:18+00:00",
                "category": "controller_decision",
                "source": "controller_decision",
                "summary": "控制面正式决定：route back same line。",
            },
            {
                "timestamp": "2026-05-30T06:50:08+00:00",
                "category": "publication_eval",
                "source": "publication_eval",
                "summary": "最新 task intake 已明确要求回到待修订状态。",
            },
            {
                "timestamp": "2026-05-30T03:44:25+00:00",
                "category": "opl_runtime_owner_handoff",
                "source": "opl_runtime_owner_handoff",
                "summary": "OPL runtime owner handoff was recorded as a refs-only boundary artifact.",
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
        "study_macro_state": {
            "surface": "study_macro_state",
            "schema_version": 1,
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "writer_state": "queued",
            "user_next": "repair",
            "reason": "quality",
            "conditions": [
                {
                    "type": "DomainTransitionRedrive",
                    "status": "true",
                    "summary": "current domain transition names an owner work unit",
                }
            ],
        },
        "opl_current_control_state_handoff": {
            "surface_kind": "opl_current_control_state_study_handoff",
            "generated_at": "2026-05-30T06:28:48+00:00",
            "quest_status": "waiting_for_user",
            "next_owner": "external_supervisor",
            "external_supervisor_required": True,
            "blocked_reason": "quest_waiting_opl_runtime_owner_route",
            "why_not_applied": ["quest_waiting_opl_runtime_owner_route"],
            "action_queue": [],
        },
        "intervention_lane": {
            "lane_id": "quality_floor_blocker",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
        },
        "operator_verdict": {
            "surface_kind": "study_operator_verdict",
            "summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "reason_summary": "回到“独立审阅与质控”，回答“produce_ai_reviewer_publication_eval_record_against_current_inputs”。",
            "route_target": "review",
            "route_key_question": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
        },
        "refs": {"publication_eval_path": "/tmp/publication_eval/latest.json"},
    }
    payload["user_visible_projection"] = module.build_user_visible_projection(payload)

    result = handoff_projection.apply_current_owner_handoff_user_visible_status(payload)

    assert "produce_ai_reviewer_publication_eval_record_against_current_inputs" in result["next_system_action"]
    assert "request_opl_handoff_hydration" not in result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] != "external_supervisor"
    assert result["intervention_lane"]["route_target"] == "review"
