from __future__ import annotations

from . import shared as _shared


def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value


_module_reexport(_shared)


def test_study_progress_verified_reviewer_handoff_surfaces_ai_reviewer_quality_closure(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "003-endocrine-burden-followup",
        study_archetype="clinical_classifier",
        endpoint_type="binary",
        manuscript_family="risk_stratification",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-003"
    _write_json(
        study_root / "artifacts" / "controller" / "task_intake" / "latest.json",
        {
            "task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
            "study_id": "003-endocrine-burden-followup",
            "emitted_at": "2026-04-26T06:53:18+00:00",
            "task_intent": (
                "Revise the 003 NF-PitNET manuscript after human reviewer feedback and write "
                "the manuscript revision outputs back."
            ),
            "first_cycle_outputs": [
                "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
            ],
        },
    )
    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "revision_handoff_verification_20260427T0159Z.json",
        {
            "schema_version": 1,
            "created_at": "2026-04-27T01:59:29Z",
            "source_task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
            "answer": "yes_same_scope_revalidated_after_correcting_stale_auxiliary_balance_note",
            "boundary": {
                "not_first_cycle_writeback_blockers": True,
                "remaining_downstream_items": ["AI-reviewer-backed finalize-quality closure"],
            },
            "next_route": "close_write_stage_route_key_question_then_return_to_controller_supervised_finalize_or_bundle_hardening_closeout",
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "schema_version": 1,
            "eval_id": "publication-eval::003-endocrine-burden-followup::quest-003::2099-01-01T00:00:00+00:00",
            "study_id": "003-endocrine-burden-followup",
            "quest_id": "quest-003",
            "emitted_at": "2099-01-01T00:00:00+00:00",
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "source_kind": "publication_gate_report",
                "policy_id": "publication_gate_projection_v1",
                "ai_reviewer_required": True,
            },
            "verdict": {
                "overall_verdict": "promising",
                "primary_claim_status": "supported",
                "summary": "bundle-stage work is unlocked and can proceed on the critical path",
                "stop_loss_pressure": "none",
            },
            "gaps": [],
            "recommended_actions": [],
        },
    )
    summary_path = study_root / "artifacts" / "eval_hygiene" / "evaluation_summary" / "latest.json"
    evaluation_summary = {
        "schema_version": 1,
        "summary_id": "evaluation-summary::003-endocrine-burden-followup::quest-003::2099-01-01T00:00:00+00:00",
        "study_id": "003-endocrine-burden-followup",
        "quest_id": "quest-003",
        "emitted_at": "2099-01-01T00:00:00+00:00",
        "overall_verdict": "promising",
        "primary_claim_status": "supported",
        "stop_loss_pressure": "none",
        "requires_controller_decision": False,
        "verdict_summary": "bundle-stage work is unlocked and can proceed on the critical path",
        "promotion_gate_status": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
        },
        "quality_closure_truth": {
            "state": "quality_repair_required",
            "summary": (
                "当前 publication_eval 只是机械投影；必须先由 AI reviewer 读取 manuscript、"
                "evidence ledger、review ledger 与 study charter 后再给出科学质量闭环判断。"
            ),
            "current_required_action": "continue_bundle_stage",
            "route_target": "finalize",
        },
        "quality_execution_lane": {
            "lane_id": "submission_hardening",
            "lane_label": "投稿包硬化收口",
            "repair_mode": "same_line_route_back",
            "route_target": "finalize",
            "route_key_question": "AI reviewer-backed publication_eval",
            "summary": "当前质量执行线聚焦 AI reviewer 质量闭环。",
        },
        "quality_review_loop": {
            "closure_state": "quality_repair_required",
            "lane_id": "submission_hardening",
            "current_phase": "revision_required",
            "current_phase_label": "修订待执行",
            "recommended_next_phase": "revision",
            "recommended_next_phase_label": "执行修订",
            "blocking_issue_count": 1,
            "blocking_issues": ["缺少 assessment_provenance.owner=ai_reviewer 的当前质量判断。"],
            "next_review_focus": ["AI reviewer-backed publication_eval"],
            "re_review_ready": False,
            "summary": "当前已经形成结构化质量修订计划，下一步应先执行修订，再回到 MAS 做复评。",
            "recommended_next_action": (
                "先发起 AI reviewer 复评，并把 reviewer-authored assessment 写回 publication_eval。"
            ),
        },
    }
    _write_json(summary_path, evaluation_summary)
    monkeypatch.setattr(module, "read_evaluation_summary", lambda *, study_root, ref: evaluation_summary)
    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "003-endocrine-burden-followup",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-003", "auto_resume": True},
            "quest_id": "quest-003",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_liveness_status": "live",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_ready",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "continue_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage work is unlocked and can proceed on the critical path",
            },
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "MedAutoScience 外环监管心跳新鲜，当前仍在按合同持续监管。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="003-endocrine-burden-followup")

    rendered_current = "\n".join(
        [result["current_stage_summary"], result["next_system_action"], *result["current_blockers"]]
    )
    assert "首轮修订产出是否已经补齐并写回 manuscript" not in rendered_current
    assert result["paper_stage"] == "bundle_stage_ready"
    assert "AI reviewer 复评" in result["next_system_action"]
    assert result["current_blockers"] == ["缺少 assessment_provenance.owner=ai_reviewer 的当前质量判断。"]
    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert result["intervention_lane"]["title"] == "优先完成 AI reviewer 质量闭环"
    assert result["quality_closure_truth"]["summary"].startswith("当前 publication_eval 只是机械投影")
    assert result["quality_review_loop"]["next_review_focus"] == ["AI reviewer-backed publication_eval"]


__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
