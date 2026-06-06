from __future__ import annotations

from .. import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_user_visible_projection_prefers_current_executable_owner_action_over_stale_paper_state() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "queued",
                "user_next": "repair",
                "reason": "quality",
                "details": {
                    "route_owner": "ai_reviewer",
                    "next_work_unit": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
                "conditions": [],
            },
            "paper_progress_state": {"next_owner": "ai_reviewer"},
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "finalize",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    )

    assert projection["next_owner"] == "finalize"
    assert projection["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert projection["current_executable_owner_action"]["next_owner"] == "finalize"

def test_user_visible_projection_does_not_mark_stale_live_macro_state_as_running_when_owner_action_is_pending() -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress_parts.user_visible_projection")

    projection = module.build_user_visible_projection(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "study_macro_state": {
                "surface": "study_macro_state",
                "schema_version": 1,
                "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
                "writer_state": "live",
                "user_next": "watch",
                "reason": "runtime",
                "details": {"active_run_id": "opl-stage-attempt://sat-stale"},
                "conditions": [],
            },
            "progress_freshness": {
                "meaningful_artifact_delta_freshness": {"status": "stale"},
                "activity_timeout": {"state": "timed_out"},
            },
            "runtime_health_snapshot": {
                "canonical_runtime_action": "recover_runtime",
                "attempt_state": "recovering",
            },
            "opl_current_control_state_handoff": {
                "running_provider_attempt": False,
                "artifact_delta": {"status": "stale"},
            },
            "current_executable_owner_action": {
                "surface_kind": "current_executable_owner_action",
                "schema_version": 1,
                "status": "ready",
                "next_owner": "gate_clearing_batch",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "allowed_actions": ["run_gate_clearing_batch"],
            },
        }
    )

    assert projection["writer_state"] == "live"
    assert projection["actual_write_active"] is False
    assert projection["owner_resolution_state"] == "ready_for_owner_action"
    assert projection["next_owner"] == "gate_clearing_batch"
    assert projection["next_system_action"] == (
        "等待 gate_clearing_batch owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )

def test_current_owner_handoff_projection_prefers_current_executable_owner_action_next_step() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {
            "decision_type": "route_back_same_line",
            "owner": "ai_reviewer",
            "controller_action": "return_to_ai_reviewer_workflow",
            "next_work_unit": {
                "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
            },
        },
        "next_system_action": "等待显式 resume、rerun 或 relaunch。",
        "status_narration_contract": {"next_step": "等待显式 resume、rerun 或 relaunch。"},
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        "user_visible_projection": {
            "surface_kind": "study_progress_user_visible_projection",
            "schema_version": 2,
            "next_owner": "ai_reviewer",
            "next_step": "等待旧 reviewer route。",
            "next_system_action": "等待旧 reviewer route。",
        },
    }

    result = module.apply_current_owner_handoff_user_visible_status(payload)

    assert result["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert result["user_visible_projection"]["next_system_action"] == result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "finalize"
    assert result["status_narration_contract"]["next_step"] == result["next_system_action"]

def test_current_owner_handoff_decision_uses_current_executable_owner_action_next_step() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.current_owner_handoff_projection"
    )

    payload = {
        "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
        "domain_transition": {"decision_type": "current_owner_handoff"},
        "next_system_action": "等待显式 resume、rerun 或 relaunch。",
        "status_narration_contract": {"next_step": "等待显式 resume、rerun 或 relaunch。"},
        "current_executable_owner_action": {
            "surface_kind": "current_executable_owner_action",
            "next_owner": "finalize",
            "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
            "allowed_actions": ["run_gate_clearing_batch"],
        },
        "user_visible_projection": {
            "surface_kind": "study_progress_user_visible_projection",
            "schema_version": 2,
            "next_owner": "ai_reviewer",
            "next_step": "等待旧 reviewer route。",
            "next_system_action": "等待旧 reviewer route。",
        },
    }

    result = module.apply_current_owner_handoff_user_visible_status(payload)

    assert result["next_system_action"] == (
        "等待 finalize owner 执行 run_gate_clearing_batch，"
        "处理 work unit dpcc_publication_gate_replay_after_current_ai_reviewer_record，"
        "产出 owner receipt、typed blocker 或下一 owner handoff。"
    )
    assert result["user_visible_projection"]["next_system_action"] == result["next_system_action"]
    assert result["user_visible_projection"]["next_owner"] == "finalize"
    assert result["status_narration_contract"]["next_step"] == result["next_system_action"]

__all__ = [name for name in globals() if name.startswith("test_")]
