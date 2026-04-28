from __future__ import annotations

from . import shared as _shared
from . import runtime_projection_basics as _runtime_projection_basics

def _module_reexport(module) -> None:
    for name, value in vars(module).items():
        if not name.startswith("__") and name != "_module_reexport":
            globals()[name] = value

_module_reexport(_shared)
_module_reexport(_runtime_projection_basics)

def test_study_progress_autonomy_contract_projects_latest_outer_loop_dispatch(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    runtime_watch_path = quest_root / "artifacts" / "reports" / "runtime_watch" / "latest.json"
    _write_json(
        runtime_watch_path,
        {
            "schema_version": 1,
            "scanned_at": "2026-04-21T04:16:00+00:00",
            "managed_study_outer_loop_dispatches": [
                {
                    "study_id": "001-risk",
                    "quest_id": "quest-001",
                    "decision_type": "continue_same_line",
                    "route_target": "write",
                    "route_key_question": "当前同线稿件还差哪一步最窄修订？",
                    "controller_action_type": "ensure_study_runtime_relaunch_stopped",
                    "dispatch_status": "executed",
                    "source": "runtime_watch_outer_loop_wakeup",
                }
            ],
            "controllers": {},
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "当前同线质量修复仍在继续。",
            },
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-001",
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
            "family_checkpoint_lineage": {
                "version": "family-checkpoint-lineage.v1",
                "resume_contract": {
                    "resume_mode": "resume_from_checkpoint",
                    "human_gate_required": False,
                },
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    assert result["autonomy_contract"]["summary"] == (
        "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。"
    )
    assert result["autonomy_contract"]["latest_outer_loop_dispatch"] == {
        "decision_type": "continue_same_line",
        "route_target": "write",
        "route_target_label": "论文写作与结果收紧",
        "route_key_question": "当前同线稿件还差哪一步最窄修订？",
        "dispatch_status": "executed",
        "summary": "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。",
    }
    assert result["autonomy_soak_status"] == {
        "surface_kind": "study_autonomy_soak_status",
        "status": "autonomous_dispatch_visible",
        "summary": "最近一次自治外环已转到“论文写作与结果收紧”，当前关键问题是“当前同线稿件还差哪一步最窄修订？”。",
        "autonomy_state": "autonomous_progress",
        "dispatch_status": "executed",
        "route_target": "write",
        "route_target_label": "论文写作与结果收紧",
        "route_key_question": "当前同线稿件还差哪一步最窄修订？",
        "progress_freshness_status": "missing",
        "next_confirmation_signal": "先补齐论文证据与叙事，再回到发表门控复核。",
        "proof_refs": [
            str(runtime_watch_path),
            str(study_root / "artifacts" / "controller_decisions" / "latest.json"),
        ],
    }
    assert "最近一次自治续跑" in markdown
    assert "自治 Proof / Soak" in markdown
    assert "当前同线稿件还差哪一步最窄修订？" in markdown


def test_study_progress_projects_quality_closure_truth_and_basis(monkeypatch, tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_study_charter_and_controller_summary(study_root)
    _write_publication_eval(
        study_root,
        quest_root,
        assessment_provenance={
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
                str(study_root / "paper" / "review" / "review_ledger.json"),
                str(study_root / "artifacts" / "controller" / "study_charter.json"),
            ],
            "ai_reviewer_required": False,
        },
        quality_assessment={
            "clinical_significance": {
                "status": "ready",
                "summary": "临床问题与结果表面已经足够稳定，可以继续推进。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
            "evidence_strength": {
                "status": "ready",
                "summary": "核心科学证据已经闭环，剩余工作不在核心证据面。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
            "novelty_positioning": {
                "status": "ready",
                "summary": "创新性边界已经在 charter 与论文线中固定。",
                "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
            },
            "human_review_readiness": {
                "status": "partial",
                "summary": "当前 package 还需要一轮 finalize 收口后再进入人工审阅。",
                "evidence_refs": [str(quest_root / "artifacts" / "reports" / "publishability_gate" / "latest.json")],
            },
        },
        recommended_actions=[
            {
                "action_id": "action-001",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "当前主线只剩 finalize / bundle 收口。",
                "route_target": "finalize",
                "route_key_question": "当前论文线还差哪一步 finalize / submission bundle 收口？",
                "route_rationale": "核心科学问题已经回答，当前只剩同线 finalize 收口。",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json")
                ],
                "requires_controller_decision": True,
            }
        ],
    )
    _write_runtime_escalation(quest_root, study_root)
    _write_runtime_watch(quest_root)
    _write_bash_summary(quest_root)
    _write_details_projection(quest_root)
    publishability_gate_path = _write_publishability_gate_report(quest_root)
    _write_json(
        publishability_gate_path,
        {
            "schema_version": 1,
            "gate_kind": "publishability_control",
            "generated_at": "2026-04-10T09:06:00+00:00",
            "quest_id": "quest-001",
            "status": "blocked",
            "allow_write": False,
            "recommended_action": "complete_bundle_stage",
            "latest_gate_path": str(publishability_gate_path),
            "supervisor_phase": "bundle_stage_blocked",
            "current_required_action": "complete_bundle_stage",
            "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            "blockers": ["missing_submission_minimal"],
            "medical_publication_surface_named_blockers": ["submission_hardening_incomplete"],
            "medical_publication_surface_route_back_recommendation": "return_to_finalize",
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "noop",
            "reason": "quest_already_running",
            "publication_supervisor_state": {
                "supervisor_phase": "bundle_stage_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": False,
                "current_required_action": "complete_bundle_stage",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle-stage blockers are now on the critical path for this paper line",
            },
            "runtime_escalation_ref": {
                "record_id": "runtime-escalation::001-risk::quest-001::publishability_gate_blocked::2026-04-10T09:07:00+00:00",
                "artifact_path": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                "summary_ref": str(study_root / "artifacts" / "runtime" / "last_launch_report.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")
    markdown = module.render_study_progress_markdown(result)

    assert result["quality_closure_truth"] == {
        "state": "bundle_only_remaining",
        "summary": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
        "current_required_action": "complete_bundle_stage",
        "route_target": "finalize",
    }
    assert result["quality_execution_lane"] == {
        "lane_id": "submission_hardening",
        "lane_label": "投稿包硬化收口",
        "repair_mode": "same_line_route_back",
        "route_target": "finalize",
        "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "summary": "当前质量执行线聚焦投稿包硬化收口；先回到定稿与投稿收尾，回答“当前论文线还差哪一个最窄的定稿或投稿包收尾动作？”。",
        "why_now": "核心科学问题已经回答，当前只剩同线 finalize 收口。",
    }
    assert result["same_line_route_truth"] == {
        "surface_kind": "same_line_route_truth",
        "same_line_state": "finalize_only_remaining",
        "same_line_state_label": "同线定稿与投稿包收尾",
        "route_mode": "return",
        "route_target": "finalize",
        "route_target_label": "定稿与投稿收尾",
        "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
        "current_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
    }
    assert result["quality_closure_basis"]["evidence_strength"]["status"] == "ready"
    assert result["module_surfaces"]["eval_hygiene"]["quality_closure_truth"] == result["quality_closure_truth"]
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] == result["same_line_route_truth"]
    assert result["quality_review_agenda"] == {
        "top_priority_issue": "必须优先修复：外部验证队列还没有补齐。",
        "suggested_revision": "先在 finalize 修订：当前主线只剩 finalize / bundle 收口。",
        "next_review_focus": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
        "agenda_summary": (
            "优先修复：必须优先修复：外部验证队列还没有补齐。；"
            "建议修订：先在 finalize 修订：当前主线只剩 finalize / bundle 收口。；"
            "下一轮复评重点：当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"
        ),
    }
    assert result["quality_revision_plan"] == {
        "policy_id": "medical_publication_critique_v1",
        "plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "execution_status": "planned",
        "overall_diagnosis": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
        "weight_contract": {
            "clinical_significance": 25,
            "evidence_strength": 35,
            "novelty_positioning": 20,
            "human_review_readiness": 20,
        },
        "items": [
            {
                "item_id": "quality-revision-item-1",
                "priority": "p0",
                "dimension": "human_review_readiness",
                "action_type": "stabilize_submission_bundle",
                "action": "先在 finalize 修订，完成当前最小投稿包收口。",
                "rationale": "核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。",
                "done_criteria": "下一轮复评能够明确确认：当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                "route_target": "finalize",
            }
        ],
        "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
    }
    assert result["quality_review_loop"] == {
        "policy_id": "medical_publication_critique_v1",
        "loop_id": "quality-review-loop::evaluation-summary::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "closure_state": "bundle_only_remaining",
        "lane_id": "submission_hardening",
        "current_phase": "bundle_hardening",
        "current_phase_label": "投稿包收口",
        "recommended_next_phase": "finalize",
        "recommended_next_phase_label": "定稿与投稿收尾",
        "active_plan_id": "quality-revision-plan::evaluation-summary::001-risk::quest-001::2026-04-10T09:09:00+00:00",
        "active_plan_execution_status": "planned",
        "blocking_issue_count": 1,
        "blocking_issues": ["核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。"],
        "next_review_focus": ["当前论文线还差哪一个最窄的定稿或投稿包收尾动作？"],
        "re_review_ready": False,
        "summary": "核心科学质量已经闭环，当前只剩投稿包与人工审阅面的收口修订。",
        "recommended_next_action": "先在 finalize 修订，完成当前最小投稿包收口。",
    }
    assert result["module_surfaces"]["eval_hygiene"]["quality_review_agenda"] == result["quality_review_agenda"]
    assert result["module_surfaces"]["eval_hygiene"]["quality_revision_plan"] == result["quality_revision_plan"]
    assert result["module_surfaces"]["eval_hygiene"]["quality_review_loop"] == result["quality_review_loop"]
    assert result["module_surfaces"]["eval_hygiene"]["quality_execution_lane"] == result["quality_execution_lane"]
    assert "## 质量闭环" in markdown
    assert "## 质量评审议程" in markdown
    assert "## 质量评审闭环" in markdown
    assert "## 质量修订计划" in markdown
    assert "当前闭环阶段: 投稿包收口" in markdown
    assert "下一跳: 定稿与投稿收尾" in markdown
    assert "当前阻塞数: 1" in markdown
    assert "闭环摘要: 核心科学质量已经闭环，当前只剩投稿包与人工审阅面的收口修订。" in markdown
    assert "下一动作: 先在 定稿与投稿收尾 修订，完成当前最小投稿包收口。" in markdown
    assert "当前阻塞项: 核心科学质量已经闭环；剩余工作收口在定稿与投稿包收尾，同一论文线可以继续自动推进。" in markdown
    assert "复评关注点: 当前论文线还差哪一个最窄的定稿或投稿包收尾动作？" in markdown
    assert "当前优先问题: 必须优先修复：外部验证队列还没有补齐。" in markdown
    assert "建议修订动作:" in markdown
    assert "当前主线只剩 定稿与投稿收尾 / bundle 收口。" in markdown
    assert "下一轮复评重点: 当前论文线还差哪一个最窄的定稿或投稿包收尾动作？" in markdown
    assert "P0 [人工审阅准备度] -> 定稿与投稿收尾" in markdown
    assert "完成当前最小投稿包收口。" in markdown
    assert "完成标准: 下一轮复评能够明确确认：当前论文线还差哪一个最窄的定稿或投稿包收尾动作？" in markdown
    assert "核心科学质量已经闭环" in markdown
    assert "核心科学证据已经闭环，剩余工作不在核心证据面。" in markdown
    assert "当前质量执行线聚焦投稿包硬化收口" in markdown


def test_study_progress_normalizes_legacy_non_mapping_quality_execution_lane_from_existing_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "progress_projection": {
                "schema_version": 1,
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_stage_summary": "当前主线在 finalize 收口。",
                "paper_stage": "finalize",
                "paper_stage_summary": "当前主线只剩 finalize 收口。",
                "next_system_action": "继续 finalize 收口。",
                "needs_physician_decision": False,
                "quality_execution_lane": "legacy-string-payload",
                "module_surfaces": {
                    "eval_hygiene": {
                        "quality_execution_lane": {
                            "lane_id": "submission_hardening",
                            "summary": "Only finalize-level submission hardening remains.",
                        }
                    }
                },
            }
        },
    )

    assert result["quality_execution_lane"] == {
        "lane_id": "submission_hardening",
        "summary": "Only finalize-level submission hardening remains.",
    }
    assert result["same_line_route_truth"] == {
        "surface_kind": "same_line_route_truth",
        "same_line_state": "finalize_only_remaining",
        "same_line_state_label": "同线定稿与投稿包收尾",
        "route_mode": "return",
        "route_target": "finalize",
        "route_target_label": "定稿与投稿收尾",
        "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
        "current_focus": "Only finalize-level submission hardening remains.",
    }
    assert result["module_surfaces"]["eval_hygiene"]["quality_execution_lane"] == result["quality_execution_lane"]
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] == result["same_line_route_truth"]
    markdown = module.render_study_progress_markdown(result)
    assert "# 研究进度" in markdown
    assert "study_id: `001-risk`" in markdown


def test_study_progress_normalizes_legacy_runtime_control_projection_from_existing_projection(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "progress_projection": {
                "schema_version": 1,
                "study_id": "001-risk",
                "current_stage": "waiting_physician_decision",
                "current_stage_summary": "当前需要用户确认恢复策略。",
                "paper_stage": "publishability_gate_blocked",
                "paper_stage_summary": "发表门控仍未放行。",
                "next_system_action": "先确认是否继续当前恢复动作。",
                "needs_physician_decision": True,
                "intervention_lane": {
                    "lane_id": "human_decision_gate",
                    "summary": "等待用户确认下一步。",
                    "recommended_action_id": "human_decision_review",
                },
                "operator_status_card": {
                    "current_focus": "先确认是否继续当前恢复动作。",
                },
                "autonomy_contract": {
                    "restore_point": {
                        "summary": "恢复点已冻结；恢复前仍需人工确认。",
                    }
                },
                "refs": {
                    "evaluation_summary_path": "/tmp/evaluation/latest.json",
                    "publication_eval_path": "/tmp/publication_eval/latest.json",
                    "controller_decision_path": "/tmp/controller_decisions/latest.json",
                },
                "research_runtime_control_projection": {
                    "surface_kind": "research_runtime_control_projection",
                    "command_templates": {
                        "resume": "uv run python -m med_autoscience.cli launch-study --study-id 001-risk",
                    },
                    "research_gate_surface": {
                        "surface_kind": "study_progress",
                    },
                },
            }
        },
    )

    projection = result["research_runtime_control_projection"]
    assert projection["surface_kind"] == "research_runtime_control_projection"
    assert projection["restore_point_surface"]["summary"] == "恢复点已冻结；恢复前仍需人工确认。"
    assert projection["progress_surface"]["current_focus"] == "先确认是否继续当前恢复动作。"
    assert projection["command_templates"]["resume"] == (
        "uv run python -m med_autoscience.cli launch-study --study-id 001-risk"
    )
    assert projection["command_templates"]["check_progress"] is None
    assert projection["command_templates"]["check_runtime_status"] is None
    assert projection["research_gate_surface"]["approval_gate_field"] == "needs_user_decision"
    assert projection["research_gate_surface"]["legacy_approval_gate_field"] == "needs_physician_decision"
    assert projection["research_gate_surface"]["approval_gate_required"] is True
    assert projection["research_gate_surface"]["interrupt_policy"] == "human_decision_review"
    assert projection["research_gate_surface"]["gate_lane"] == "user_decision_gate"
    assert projection["research_gate_surface"]["gate_summary"] == "等待用户确认下一步。"
    assert projection["artifact_pickup_surface"]["pickup_refs"] == [
        "/tmp/evaluation/latest.json",
        "/tmp/publication_eval/latest.json",
        "/tmp/controller_decisions/latest.json",
    ]


def test_study_progress_suppresses_same_line_route_when_publication_supervisor_blocks_bundle_tasks(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(profile.workspace_root, "001-risk")

    result = module.build_study_progress_projection(
        profile=profile,
        study_id="001-risk",
        study_root=study_root,
        status_payload={
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
            },
            "progress_projection": {
                "schema_version": 1,
                "study_id": "001-risk",
                "current_stage": "publication_supervision",
                "current_stage_summary": "当前主线仍需先回到发表门控。",
                "paper_stage": "publishability_gate_blocked",
                "paper_stage_summary": "当前发表门控仍未放行。",
                "next_system_action": "先回到发表门控。",
                "needs_physician_decision": False,
                "quality_execution_lane": {
                    "lane_id": "submission_hardening",
                    "summary": "Only finalize-level submission hardening remains.",
                },
                "same_line_route_truth": {
                    "surface_kind": "same_line_route_truth",
                    "same_line_state": "finalize_only_remaining",
                    "same_line_state_label": "同线定稿与投稿包收尾",
                    "route_mode": "return",
                    "route_target": "finalize",
                    "route_target_label": "定稿与投稿收尾",
                    "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
                    "current_focus": "Only finalize-level submission hardening remains.",
                },
                "same_line_route_surface": {
                    "surface_kind": "same_line_route_surface",
                    "lane_id": "submission_hardening",
                    "repair_mode": "same_line_route_back",
                    "route_target": "finalize",
                    "route_target_label": "定稿与投稿收尾",
                    "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                    "summary": "当前质量执行线聚焦投稿包硬化收口；先回到定稿与投稿收尾，回答“当前论文线还差哪一个最窄的定稿或投稿包收尾动作？”。",
                    "why_now": "bundle-stage work is unlocked and can proceed on the critical path",
                    "current_required_action": "continue_bundle_stage",
                    "closure_state": "bundle_only_remaining",
                },
                "module_surfaces": {
                    "eval_hygiene": {
                        "same_line_route_truth": {
                            "surface_kind": "same_line_route_truth",
                            "same_line_state": "finalize_only_remaining",
                            "same_line_state_label": "同线定稿与投稿包收尾",
                            "route_mode": "return",
                            "route_target": "finalize",
                            "route_target_label": "定稿与投稿收尾",
                            "summary": "当前同线路由已经收窄到定稿与投稿包收尾；先回到定稿与投稿收尾，完成当前最小投稿包收口。",
                            "current_focus": "Only finalize-level submission hardening remains.",
                        },
                        "same_line_route_surface": {
                            "surface_kind": "same_line_route_surface",
                            "lane_id": "submission_hardening",
                            "repair_mode": "same_line_route_back",
                            "route_target": "finalize",
                            "route_target_label": "定稿与投稿收尾",
                            "route_key_question": "当前论文线还差哪一个最窄的定稿或投稿包收尾动作？",
                            "summary": "当前质量执行线聚焦投稿包硬化收口；先回到定稿与投稿收尾，回答“当前论文线还差哪一个最窄的定稿或投稿包收尾动作？”。",
                            "why_now": "bundle-stage work is unlocked and can proceed on the critical path",
                            "current_required_action": "continue_bundle_stage",
                            "closure_state": "bundle_only_remaining",
                        },
                    }
                },
            },
        },
    )

    assert result["same_line_route_truth"] is None
    assert result["same_line_route_surface"] is None
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_truth"] is None
    assert result["module_surfaces"]["eval_hygiene"]["same_line_route_surface"] is None


def test_study_progress_does_not_project_resume_arbitration_as_physician_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    controller_decision_path = study_root / "artifacts" / "controller_decisions" / "latest.json"
    _write_json(
        controller_decision_path,
        {
            "schema_version": 1,
            "decision_id": "study-decision::001-risk::quest-001::continue_same_line::2026-04-10T09:10:00+00:00",
            "study_id": "001-risk",
            "quest_id": "quest-001",
            "emitted_at": "2026-04-10T09:10:00+00:00",
            "decision_type": "continue_same_line",
            "requires_human_confirmation": False,
            "controller_actions": [
                {
                    "action_type": "ensure_study_runtime",
                    "payload_ref": str(controller_decision_path),
                }
            ],
            "reason": "控制面要求继续 write/review，不需要医生追加确认。",
        },
    )
    launch_report_path = study_root / "artifacts" / "runtime" / "last_launch_report.json"
    _write_json(
        launch_report_path,
        {
            "recorded_at": "2026-04-10T09:05:00+00:00",
            "source": "controller",
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "quest_status": "active",
        },
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "quest_parked_on_unchanged_finalize_state",
            "publication_supervisor_state": {
                "supervisor_phase": "scientific_anchor_missing",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": False,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
                "controller_stage_note": "bundle suggestions are downstream-only until the publication gate allows write",
            },
            "pending_user_interaction": {
                "interaction_id": "progress-finalize-001",
                "kind": "decision_request",
                "waiting_interaction_id": "progress-finalize-001",
                "default_reply_interaction_id": "progress-finalize-001",
                "pending_decisions": ["progress-finalize-001"],
                "blocking": True,
                "reply_mode": "blocking",
                "expects_reply": True,
                "allow_free_text": False,
                "message": "这一步已经处理完，等待 Gateway 接管。",
                "summary": "运行时把 finalize 本地总结暂时停在这里。",
                "reply_schema": {"type": "decision", "decision_type": "finalize_paper_line"},
                "decision_type": "finalize_paper_line",
                "options_count": 1,
                "guidance_requires_user_decision": True,
                "source_artifact_path": str(quest_root / "artifacts" / "decisions" / "progress-finalize-001.json"),
                "relay_required": True,
            },
            "interaction_arbitration": {
                "classification": "invalid_blocking",
                "action": "resume",
                "reason_code": "mas_managed_policy_rejects_runtime_user_gate",
                "requires_user_input": False,
                "valid_blocking": False,
                "kind": "decision_request",
                "decision_type": "finalize_paper_line",
                "source_artifact_path": str(quest_root / "artifacts" / "decisions" / "progress-finalize-001.json"),
                "controller_stage_note": (
                    "MAS-managed studies must keep routing, finalize, adequacy, publishability, and completion "
                    "decisions inside the MAS outer loop; runtime blocking may only ask for external secrets or credentials."
                ),
            },
            "continuation_state": {
                "quest_status": "active",
                "active_run_id": None,
                "continuation_policy": "wait_for_user_or_resume",
                "continuation_anchor": "decision",
                "continuation_reason": "unchanged_finalize_state",
                "runtime_state_path": str(quest_root / ".ds" / "runtime_state.json"),
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["study_id"] == "001-risk"
    assert result["current_stage"] == "publication_supervision"
    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert "等待用户" not in result["next_system_action"]
    assert all("finalize 本地总结" not in item for item in result["current_blockers"])
    assert result["paper_stage"] == "scientific_anchor_missing"
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["controller_confirmation_summary_path"] is None


def test_study_progress_does_not_project_autonomous_controller_gate_as_physician_decision(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    publication_eval_path = _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="continue_same_line",
        requires_human_confirmation=True,
        action_type="ensure_study_runtime",
        reason="MAS should decide the current evidence repair line autonomously.",
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["current_stage"] == "publication_supervision"
    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert result["refs"]["publication_eval_path"] == str(publication_eval_path)
    assert result["refs"]["controller_confirmation_summary_path"] is None


def test_study_progress_labels_bounded_analysis_as_autonomous_next_step(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_publication_eval(study_root, quest_root)
    _write_controller_decision(
        study_root,
        quest_root,
        decision_type="bounded_analysis",
        requires_human_confirmation=False,
        action_type="ensure_study_runtime",
        reason="MAS 将先完成一轮有限补充分析，再继续当前论文主线。",
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {
                "engine": "med-deepscientist",
                "auto_entry": "on_managed_research_intent",
                "quest_id": "quest-001",
                "auto_resume": True,
            },
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "active",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "deferred_downstream_actions": [],
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["needs_physician_decision"] is False
    assert result["physician_decision_summary"] is None
    assert any("有限补充分析" in str(item.get("summary") or "") for item in result["latest_events"])


def test_study_progress_surfaces_same_line_route_back_quality_focus(
    monkeypatch,
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.study_progress")
    profile = make_profile(tmp_path)
    study_root = write_study(
        profile.workspace_root,
        "001-risk",
        study_archetype="clinical_classifier",
        endpoint_type="time_to_event",
        manuscript_family="prediction_model",
    )
    quest_root = profile.med_deepscientist_runtime_root / "quests" / "quest-001"
    _write_publication_eval(
        study_root,
        quest_root,
        recommended_actions=[
            {
                "action_id": "action-101",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": "当前先修正稿面 claim-evidence 对齐，再继续同线推进。",
                "route_target": "write",
                "route_key_question": "当前稿面最窄的 claim-evidence 修复动作是什么？",
                "route_rationale": "研究方向不变，质量硬阻塞集中在写作面，应该直接回到 write 收口。",
                "evidence_refs": [
                    str(
                        quest_root
                        / "artifacts"
                        / "reports"
                        / "escalation"
                        / "runtime_escalation_record.json"
                    )
                ],
                "requires_controller_decision": True,
            }
        ],
    )

    monkeypatch.setattr(
        module.study_runtime_router,
        "study_runtime_status",
        lambda **_: {
            "schema_version": 1,
            "study_id": "001-risk",
            "study_root": str(study_root),
            "entry_mode": "full_research",
            "execution": {"engine": "med-deepscientist", "quest_id": "quest-001", "auto_resume": True},
            "quest_id": "quest-001",
            "quest_root": str(quest_root),
            "quest_exists": True,
            "quest_status": "running",
            "runtime_binding_path": str(study_root / "runtime_binding.yaml"),
            "runtime_binding_exists": True,
            "study_completion_contract": {},
            "decision": "resume",
            "reason": "publishability_gate_blocked",
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "phase_owner": "publication_gate",
                "upstream_scientific_anchor_ready": True,
                "bundle_tasks_downstream_only": True,
                "current_required_action": "return_to_publishability_gate",
                "controller_stage_note": "当前论文仍需先修质量面，再考虑后续打包。",
            },
            "pending_user_interaction": {},
            "interaction_arbitration": None,
            "supervisor_tick_audit": {
                "required": True,
                "status": "fresh",
                "summary": "监管心跳新鲜。",
            },
        },
    )

    result = module.read_study_progress(profile=profile, study_id="001-risk")

    assert result["intervention_lane"]["lane_id"] == "quality_floor_blocker"
    assert result["intervention_lane"]["repair_mode"] == "same_line_route_back"
    assert result["intervention_lane"]["route_target"] == "write"
    assert result["intervention_lane"]["route_key_question"] == "当前稿面最窄的 claim-evidence 修复动作是什么？"
    assert "论文写作与结果收紧" in result["current_stage_summary"]
    assert "当前稿面最窄的 claim-evidence 修复动作是什么？" in result["next_system_action"]
    assert "论文写作与结果收紧" in result["operator_status_card"]["current_focus"]
    assert "当前稿面最窄的 claim-evidence 修复动作是什么？" in result["operator_status_card"]["current_focus"]
    assert result["needs_physician_decision"] is False
__all__ = [name for name in globals() if not name.startswith("__") and name != "_module_reexport"]
