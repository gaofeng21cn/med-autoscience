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
    from med_autoscience.controllers import ai_first_action_dispatch

    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
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
        "progress_projection",
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
    assert markdown.strip()
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
    assert result["refs"]["ai_first_action_dispatch_ledger_path"].endswith(
        "artifacts/runtime/ai_first_action_dispatch_ledger/latest.json"
    )
    action_dispatch = result["ai_first_action_dispatch_ledger"]
    assert action_dispatch["surface"] == "ai_first_action_dispatch_ledger"
    assert action_dispatch["authority"] == "operations_governance_only"
    assert action_dispatch["counts"]["open"] >= 1
    assert action_dispatch["counts"]["total"] == len(action_dispatch["dispatches"])
    assert action_dispatch["materialized"] is False
    assert ai_first_action_dispatch.read_action_dispatch_ledger(study_root=study_root) is None
    lifecycle = result["ai_first_action_lifecycle"]
    assert lifecycle["surface"] == "ai_first_action_lifecycle_projection"
    assert lifecycle["primary_action"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert lifecycle["open_action_count"] == action_dispatch["counts"]["open"]
    assert lifecycle["authority_contract"]["lifecycle_can_authorize_quality"] is False
    assert lifecycle["authority_contract"]["lifecycle_can_authorize_submission"] is False
    second = module.read_study_progress(profile=profile, study_id="001-risk")
    first_keys = {item["dispatch_key"] for item in action_dispatch["dispatches"]}
    second_keys = {
        item["dispatch_key"]
        for item in second["ai_first_action_dispatch_ledger"]["dispatches"]
    }
    assert first_keys == second_keys
    assert len(second_keys) == second["ai_first_action_dispatch_ledger"]["counts"]["total"]
    assert markdown.strip()


def test_study_progress_default_read_does_not_materialize_ai_first_ledgers(
    monkeypatch,
    tmp_path: Path,
) -> None:
    from med_autoscience.controllers import ai_first_action_dispatch, ai_first_feedback

    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")
    quest_root = profile.managed_runtime_home / "quests" / "quest-001"
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "ai_reviewer_required": True,
            },
            "verdict": {"overall_verdict": "mixed"},
            "recommended_actions": [],
        },
    )
    monkeypatch.setattr(
        module.study_runtime_router,
        "progress_projection",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_status": "running",
            "decision": "noop",
            "reason": "quest_already_running",
            "active_run_id": "run-001",
            "publication_supervisor_state": {
                "supervisor_phase": "write",
                "phase_owner": "publication_gate",
                "current_required_action": "continue_write_stage",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    feedback_ledger_path = ai_first_feedback.stable_feedback_ledger_path(study_root=study_root)
    action_dispatch_path = ai_first_action_dispatch.stable_action_dispatch_ledger_path(
        study_root=study_root,
    )
    assert result["ai_first_feedback_state"]["surface"] == "ai_first_feedback_state"
    assert result["ai_first_action_dispatch_ledger"]["surface"] == "ai_first_action_dispatch_ledger"
    assert result["ai_first_action_dispatch_ledger"]["materialized"] is False
    assert result["refs"]["ai_first_feedback_ledger_path"] == str(feedback_ledger_path)
    assert result["refs"]["ai_first_action_dispatch_ledger_path"] == str(action_dispatch_path)
    assert not feedback_ledger_path.exists()
    assert not action_dispatch_path.exists()
