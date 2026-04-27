from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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


def test_reviewer_first_user_feedback_intake_detects_revision_reactivation() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "task_intent": (
            "Resume the same 001 manuscript line for reviewer-first revision based on explicit user feedback. "
            "Do not directly edit manuscript/current_package; use paper/rebuttal/input as trusted input and route "
            "the work back through MAS/MDS write/review/publication gate surfaces. Tighten Methods, calibration "
            "and clinical-claim boundaries, table/figure legends, TRIPOD/PROBAST reporting, and paper-facing wording."
        ),
        "constraints": [
            "Do not frame the model as ready for direct clinical decision-making; state internal validation and external-validation needs."
        ],
        "trusted_inputs": [
            "studies/001-dm-cvd-mortality-risk/paper/rebuttal/input/2026-04-26_user_feedback_methods_calibration_scope.md"
        ],
        "first_cycle_outputs": [
            "Create or update paper/rebuttal review matrix/action plan, revise paper-facing source surfaces, run publication/reporting gate."
        ],
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.task_intake_overrides_auto_manual_finish(payload) is True
    summary = module.summarize_task_intake(payload)
    assert summary["revision_intake"]["kind"] == "reviewer_revision"
    assert summary["revision_intake"]["reactivation_required"] is True


def test_manuscript_fast_lane_intake_exposes_controller_visible_contract() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "entry_mode": "manuscript_fast_lane",
        "task_intent": (
            "Reviewer feedback asks for text-only manuscript revision during manual finishing. "
            "Use existing evidence only and revise controller-authorized canonical paper sources."
        ),
        "constraints": [
            "runtime must be inactive or foreground takeover must be allowed before editing",
            "edit only canonical paper/ manuscript text and structure",
            "all claims must come from existing evidence; do not run new analysis",
        ],
        "first_cycle_outputs": [
            "controller-visible intake and handoff, canonical paper patch, export/sync, QC and package consistency checks"
        ],
    }

    summary = module.summarize_task_intake(payload)
    override = module.build_task_intake_progress_override(payload)

    assert module.task_intake_requests_manuscript_fast_lane(payload) is True
    assert summary["manuscript_fast_lane"]["status"] == "requested"
    assert summary["manuscript_fast_lane"]["execution_owner"] == "codex_foreground_under_mas_controller"
    assert "runtime_inactive_or_takeover_allowed" in summary["manuscript_fast_lane"]["required_conditions"]
    assert summary["revision_intake"]["manuscript_fast_lane"]["status"] == "requested"
    assert override["current_required_action"] == "run_manuscript_fast_lane"
    assert override["quality_execution_lane"]["lane_id"] == "manuscript_fast_lane"
    assert override["manuscript_fast_lane"]["canonical_write_surface"] == "paper/"


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


def test_reviewer_revision_intake_yields_to_ai_reviewer_quality_closure_after_verified_handoff(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    payload = {
        "task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
        "emitted_at": "2026-04-26T06:53:18+00:00",
        "task_intent": "Revise the manuscript after reviewer feedback and write manuscript revision outputs back.",
        "first_cycle_outputs": [
            "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
        ],
    }
    gate_report = {
        "generated_at": "2026-04-27T02:02:40+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-04-27T02:02:52+00:00",
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
        "quality_review_loop": {
            "closure_state": "quality_repair_required",
            "lane_id": "submission_hardening",
            "current_phase": "revision_required",
            "blocking_issues": ["缺少 assessment_provenance.owner=ai_reviewer 的当前质量判断。"],
            "next_review_focus": ["AI reviewer-backed publication_eval"],
            "recommended_next_action": (
                "先发起 AI reviewer 复评，并把 reviewer-authored assessment 写回 publication_eval。"
            ),
        },
    }

    stale_override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )
    assert stale_override is not None
    assert stale_override["paper_stage"] == "write"

    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "revision_handoff_verification_20260427T0159Z.json",
        {
            "schema_version": 1,
            "verification_id": "revision-handoff-verification::003-endocrine-burden-followup::20260427T0159Z",
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

    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_intake_yields_to_verified_bundle_only_closeout_with_admin_open_items(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "003-endocrine-burden-followup"
    payload = {
        "task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
        "emitted_at": "2026-04-26T06:53:18+00:00",
        "task_intent": "Revise the manuscript after reviewer feedback and write manuscript revision outputs back.",
        "first_cycle_outputs": [
            "当前最新 task intake 指定的首轮修订产出是否已经补齐并写回 manuscript？"
        ],
    }
    gate_report = {
        "generated_at": "2026-04-27T21:01:49+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-04-27T21:03:00+00:00",
        "promotion_gate_status": {
            "status": "clear",
            "allow_write": True,
            "current_required_action": "continue_bundle_stage",
            "blockers": [],
        },
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
            "route_target": "finalize",
        },
        "study_quality_truth": {
            "contract_closed": True,
            "narrowest_scientific_gap": {
                "state": "closed",
                "summary": "Open scientific gap is already closed; only finalize closeout remains.",
            },
            "reviewer_first": {
                "ready": False,
                "status": "blocked",
                "summary": (
                    "review ledger 仍有 2 个未关闭 concern，"
                    "but both are author/declaration metadata and post-metadata package audit."
                ),
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

    stale_override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )
    assert stale_override is not None
    assert stale_override["paper_stage"] == "write"

    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "revision_handoff_verification_20260427T2054Z.json",
        {
            "schema_version": 1,
            "record_type": "revision_handoff_verification",
            "created_at": "2026-04-27T20:54:33Z",
            "source_task_id": "study-task::003-endocrine-burden-followup::20260426T065318Z",
            "answer": "yes_first_cycle_revision_outputs_complete_and_written_back_to_manuscript",
            "task_intake_has_newer_superseding_task": False,
            "evidence": {
                "task_intake": {"newer_task_intake_found": False},
            },
            "boundary": {
                "not_first_cycle_writeback_blockers": True,
                "remaining_downstream_items": [
                    "external author/declaration metadata closeout",
                    "targeted package audit after metadata insertion",
                ],
            },
            "next_route": (
                "close_write_stage_route_key_question_then_return_to_controller_supervised_"
                "finalize_or_bundle_hardening_closeout"
            ),
        },
    )

    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
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
    assert summary["revision_intake"]["reactivation_required"] is True
    assert (
        summary["revision_intake"]["current_package_edit_policy"]["direct_current_package_edit_allowed"]
        is False
    )
    assert summary["revision_intake"]["handoff_required"] is True

    markdown = module.render_task_intake_markdown(payload)
    assert "## Revision Intake Checklist" in markdown
    assert "text revisions" in markdown
    assert "handoff/evidence surface" in markdown
    assert "stopped/submission-ready/finalize" in markdown
    assert "先通过 MAS/MDS relaunch/resume 接管 canonical paper surface" in markdown

    runtime_context = module.render_task_intake_runtime_context(payload)
    assert "Revision intake: reviewer_revision" in runtime_context
    assert "stopped milestone state is not foreground current_package edit permission" in runtime_context
    assert "Relaunch/resume MAS/MDS before editing canonical paper sources." in runtime_context


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
