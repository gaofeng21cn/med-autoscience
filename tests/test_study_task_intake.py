from __future__ import annotations

import importlib


def test_task_intake_progress_override_yields_to_deterministic_submission_closeout() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intent": (
            "当前稿件不能按已达投稿包里程碑直接收口；必须补做分层统计分析，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        "constraints": ["本轮不得直接按外投收口。"],
        "evidence_boundary": ["统计扩展限于预设 subgroup / association analysis。"],
        "first_cycle_outputs": ["价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。"],
    }
    gate_report = {
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "stale_study_delivery_mirror",
            "submission_surface_qc_failure_present",
        ],
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }

    assert module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=gate_report,
    ) is None


def test_task_intake_progress_override_yields_to_fresh_bundle_only_closeout() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "emitted_at": "2026-04-22T08:53:48+00:00",
        "task_intent": (
            "当前稿件不能按已达投稿包里程碑直接收口；必须补做分层统计分析，"
            "并把当前 submission-ready/finalize 判断降回待修订后再评估。"
        ),
        "constraints": ["本轮不得直接按外投收口。"],
        "first_cycle_outputs": ["价格顾虑有/无分层的生物制剂使用结构比较表与统计检验结果。"],
    }
    gate_report = {
        "emitted_at": "2026-04-24T04:07:59+00:00",
        "status": "clear",
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-04-24T04:24:18+00:00",
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "ready",
            }
        },
    }

    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    assert module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_does_not_yield_to_fresh_bundle_only_closeout() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "emitted_at": "2026-04-25T04:10:49+00:00",
        "task_intent": "根据审稿意见和用户反馈执行 manuscript revision，清理 Figure/Table feedback 与 Methods 缺口。",
        "constraints": ["不得按旧 submission-ready/finalize 判断直接收口。"],
        "first_cycle_outputs": ["revision checklist mapping each reviewer concern to manuscript deltas"],
    }
    gate_report = {
        "emitted_at": "2026-04-25T04:11:18+00:00",
        "status": "clear",
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-04-25T04:11:18+00:00",
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "ready",
            }
        },
    }

    override = module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert override is not None
    assert override["quality_closure_truth"]["state"] == "quality_repair_required"
    assert override["paper_stage"] == "write"
    assert "revision checklist" in override["next_system_action"]


def test_reviewer_revision_intake_detects_chinese_submission_review_feedback_reactivation() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intent": (
            "用户已对修改后投稿包给出新的审稿式反馈；这不是 submission metadata 收口，"
            "而是显式重新激活同一论文线，要求 MAS/MDS 以 revision/rebuttal 模式重新处理。"
            "必须先把反馈拆成可审计 action matrix，然后完成结构性返修与重建投稿包。"
        ),
        "constraints": ["不得手工 patch current_package 投影作为最终修复。"],
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    assert module.summarize_task_intake(payload)["revision_intake"]["kind"] == "reviewer_revision"


def test_reviewer_revision_intake_yields_to_reviewer_first_bundle_stage_closeout() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "emitted_at": "2026-04-25T04:10:49+00:00",
        "task_intent": "根据审稿意见和用户反馈执行 manuscript revision，清理 Figure/Table feedback 与 Methods 缺口。",
        "constraints": ["不得按旧 submission-ready/finalize 判断直接收口。"],
        "first_cycle_outputs": ["revision checklist mapping each reviewer concern to manuscript deltas"],
    }
    gate_report = {
        "generated_at": "2026-04-26T04:42:25+00:00",
        "status": "clear",
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "bundle_tasks_downstream_only": False,
    }
    evaluation_summary = {
        "emitted_at": "2026-04-26T04:49:24+00:00",
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
        },
        "study_quality_truth": {
            "reviewer_first": {
                "ready": True,
                "status": "ready",
                "summary": "review ledger 已把 reviewer concerns 全部收口。",
            },
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "ready",
            }
        },
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_yields_to_evaluation_promotion_gate_when_gate_report_not_loaded() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "emitted_at": "2026-04-25T04:10:49+00:00",
        "task_intent": "根据审稿意见和用户反馈执行 manuscript revision，清理 Figure/Table feedback 与 Methods 缺口。",
        "constraints": ["不得按旧 submission-ready/finalize 判断直接收口。"],
        "first_cycle_outputs": ["revision checklist mapping each reviewer concern to manuscript deltas"],
    }
    evaluation_summary = {
        "emitted_at": "2026-04-26T04:56:24+00:00",
        "promotion_gate_status": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
        },
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
        },
        "study_quality_truth": {
            "reviewer_first": {
                "ready": True,
                "status": "ready",
            },
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "ready",
            }
        },
    }

    assert module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=None,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_yields_to_blocked_deterministic_submission_closeout() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "emitted_at": "2026-04-25T04:10:49+00:00",
        "task_intent": "根据审稿意见和用户反馈执行 manuscript revision，清理 Figure/Table feedback 与 Methods 缺口。",
        "constraints": ["不得按旧 submission-ready/finalize 判断直接收口。"],
        "first_cycle_outputs": ["revision checklist mapping each reviewer concern to manuscript deltas"],
    }
    gate_report = {
        "emitted_at": "2026-04-26T04:27:45+00:00",
        "status": "blocked",
        "blockers": [
            "stale_submission_minimal_authority",
            "submission_surface_qc_failure_present",
        ],
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }
    evaluation_summary = {
        "emitted_at": "2026-04-26T04:30:27+00:00",
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
            "current_phase": "bundle_hardening",
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "blocked",
            }
        },
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_is_detected_and_summarized() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "study_id": "study-revision",
        "emitted_at": "2026-04-24T00:00:00+00:00",
        "task_intent": "根据导师反馈和审稿意见推进论文修改，补齐 Introduction/Methods/Results/Figure/Table feedback。",
        "constraints": ["前台直接改稿后必须留下 durable handoff。"],
        "trusted_inputs": ["reviewer feedback letter", "导师反馈截图"],
        "first_cycle_outputs": ["revision checklist", "MDS handoff note"],
    }

    summary = module.summarize_task_intake(payload)
    assert summary["revision_intake"]["kind"] == "reviewer_revision"
    assert summary["revision_intake"]["status"] == "active"
    assert summary["revision_intake"]["checklist"] == [
        "text_revisions",
        "methods_completeness",
        "statistical_analysis",
        "tables_figures",
        "follow_up_evidence",
        "discussion_claim_guardrails",
        "handoff_evidence_surface",
    ]
    assert summary["revision_intake"]["handoff_required"] is True

    markdown = module.render_task_intake_markdown(payload)
    assert "## Revision Intake Checklist" in markdown
    assert "text revisions" in markdown
    assert "handoff/evidence surface" in markdown

    runtime_context = module.render_task_intake_runtime_context(payload)
    assert "Revision intake: reviewer_revision" in runtime_context
    assert "Latest revision handoff/evidence surface must be read before MDS resume." in runtime_context


def test_non_revision_intake_does_not_emit_revision_checklist() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "study_id": "study-scout",
        "emitted_at": "2026-04-24T00:00:00+00:00",
        "task_intent": "为新队列做 early evidence framing。",
        "trusted_inputs": ["dataset dictionary"],
    }

    summary = module.summarize_task_intake(payload)
    assert summary.get("revision_intake") is None
    assert "Revision Intake Checklist" not in module.render_task_intake_markdown(payload)
