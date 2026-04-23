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
