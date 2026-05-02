from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_projects_ai_first_default_entry_state_fail_closed(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(
        publication_eval_path,
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "ai_reviewer_required": True,
            },
            "verdict": {
                "overall_verdict": "mixed",
                "summary": "Mechanical projection cannot authorize quality closure.",
            },
            "recommended_actions": [],
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-001",
            "publication_supervisor_state": {
                "supervisor_phase": "write",
                "phase_owner": "publication_gate",
                "current_required_action": "continue_write_stage",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    state = result["ai_first_default_entry_state"]
    assert state["surface"] == "ai_first_default_entry_state"
    assert state["status"] == "review_required"
    assert state["pre_draft"]["draft_ready"] is False
    assert state["pre_draft"]["route_back_required"] is True
    assert state["pre_draft"]["authoring_workplan_projection"] == {
        "surface": "authoring_workplan_projection",
        "exists": False,
        "status": "",
        "workplan_ready": False,
        "required_before": "first_full_draft",
        "source_family": "",
        "section_count": 0,
        "work_unit_count": 0,
        "blockers": ["authoring_workplan_missing"],
        "authority": {
            "read_only": True,
            "can_authorize_draft_readiness": False,
            "can_mutate_runtime": False,
        },
    }
    assert state["ai_reviewer_workflow"]["authority_state"] == "projection_only"
    assert state["ai_reviewer_workflow"]["finalize_authorized"] is False
    assert state["ai_reviewer_workflow"]["submission_authorized"] is False
    assert state["artifact_proof"]["rebuild_pending"] is True
    assert state["human_review_required"] is True
    assert state["authority"]["default_entry_can_authorize_quality"] is False
    assert result["ai_first_operations_dashboard"]["user_view"]["human_review_required"] is True
    assert "AI-first 默认入口状态" in markdown
    assert "Pre-draft readiness" in markdown
    assert "AI reviewer workflow" in markdown
    assert "Artifact proof" in markdown
    feedback = result["ai_first_feedback_state"]
    assert feedback["surface"] == "ai_first_feedback_state"
    assert feedback["authority"] == "observability_only"
    assert feedback["status"] == "attention_required"
    assert feedback["counts"]["ai_reviewer_trace_incomplete_count"] == 1
    assert feedback["counts"]["artifact_rebuild_pending_count"] == 1
    assert feedback["authority_contract"]["feedback_can_authorize_submission"] is False
    assert feedback["primary_action"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert feedback["user_view"]["next_action"] == "补齐 AI reviewer workflow、publication eval 与 medical prose review。"
    assert result["refs"]["ai_first_feedback_ledger_path"].endswith(
        "artifacts/runtime/ai_first_feedback_ledger/latest.json"
    )
    assert "AI-first 运行反馈" in markdown
    assert "建议动作: 补齐 AI reviewer workflow、publication eval 与 medical prose review。" in markdown
