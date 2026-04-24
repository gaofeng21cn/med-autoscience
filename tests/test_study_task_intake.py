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
