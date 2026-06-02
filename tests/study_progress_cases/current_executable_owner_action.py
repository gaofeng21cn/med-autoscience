from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_progress_first_monitoring_exposes_current_executable_owner_action_from_next_forced_delta() -> None:
    module = importlib.import_module(
        "med_autoscience.controllers.study_progress_parts.progress_first_monitoring"
    )

    monitoring = module.build_progress_first_monitoring_summary(
        {
            "study_id": "003-dpcc-primary-care-phenotype-treatment-gap",
            "next_forced_delta": {
                "required_delta_kind": "review_current_paper_delta",
                "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                "target_surface": {
                    "ref_kind": "route_obligation",
                    "route_target": "finalize",
                    "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                },
                "target_surface_specificity": "explicit_owner_route_target",
                "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
                "owner_action": {
                    "next_owner": "finalize",
                    "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
                    "allowed_actions": ["run_gate_clearing_batch"],
                    "owner_receipt_required": True,
                },
            },
            "domain_transition": {
                "decision_type": "route_back_same_line",
                "owner": "ai_reviewer",
                "controller_action": "return_to_ai_reviewer_workflow",
                "next_work_unit": {
                    "unit_id": "produce_ai_reviewer_publication_eval_record_against_current_inputs",
                },
            },
        }
    )

    action = monitoring["current_executable_owner_action"]
    assert action == {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "study_progress.next_forced_delta.owner_action",
        "next_owner": "finalize",
        "work_unit_id": "dpcc_publication_gate_replay_after_current_ai_reviewer_record",
        "allowed_actions": ["run_gate_clearing_batch"],
        "owner_receipt_required": True,
        "required_delta_kind": "review_current_paper_delta",
        "target_surface": {
            "ref_kind": "route_obligation",
            "route_target": "finalize",
            "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
        },
        "target_surface_specificity": "explicit_owner_route_target",
        "acceptance_refs": ["progress_first_sprint_state.deliverable_progress_delta"],
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }
    assert monitoring["next_owner"] == "finalize"
    assert monitoring["controller_action"] == "run_gate_clearing_batch"
    assert monitoring["next_work_unit"] == "dpcc_publication_gate_replay_after_current_ai_reviewer_record"


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
