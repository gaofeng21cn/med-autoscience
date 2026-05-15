from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: dict[str, object]) -> None:
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


def test_reviewer_revision_intake_yields_to_current_delivery_package_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "002-dm"
    package_root = study_root / "manuscript" / "current_package"
    (package_root / "figures").mkdir(parents=True)
    (package_root / "tables").mkdir()
    for path in (
        package_root / "manuscript.docx",
        package_root / "paper.pdf",
        package_root / "references.bib",
        package_root / "figures" / "Figure1.png",
        package_root / "tables" / "Table1.md",
    ):
        path.write_text("package artifact\n", encoding="utf-8")
    (package_root / "SUBMISSION_TODO.md").write_text("# Submission TODO\n", encoding="utf-8")
    (study_root / "manuscript" / "current_package.zip").write_text("zip\n", encoding="utf-8")
    _write_json(
        package_root / "audit" / "submission_manifest.json",
        {
            "schema_version": 1,
            "figures": [{"figure_id": "Figure1"}],
            "tables": [{"table_id": "Table1"}],
            "manuscript": {"surface_qc": {"status": "pass", "failures": []}},
        },
    )
    _write_json(
        study_root / "manuscript" / "delivery_manifest.json",
        {
            "schema_version": 1,
            "generated_at": "2026-05-13T05:27:45+00:00",
            "stage": "submission_minimal",
            "source_signature": "source::ready",
            "evaluated_source_signature": "source::ready",
            "authority_source_signature": "source::ready",
            "surface_roles": {
                "controller_authorized_paper_root": str(study_root / "paper"),
                "human_facing_current_package_root": str(package_root),
                "human_facing_current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
            },
        },
    )
    payload = {
        "emitted_at": "2026-04-27T02:05:48+00:00",
        "task_intent": "用户已对糖尿病002投稿包给出明确审稿式反馈，必须作为 reviewer_revision 重新激活同一论文线。",
        "constraints": ["完成前维持 audit preview only / not submission-ready 判断。"],
        "first_cycle_outputs": [
            "paper/rebuttal/review_matrix.md and action_plan.md covering all feedback items.",
        ],
    }
    gate_report = {
        "generated_at": "2026-05-15T05:28:48+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "supervisor_phase": "bundle_stage_ready",
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
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


def test_reviewer_revision_intake_does_not_yield_to_submission_closeout_with_open_review_ledger_concerns() -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")

    payload = {
        "emitted_at": "2026-04-25T04:10:49+00:00",
        "task_intent": "Reviewer revision: absorb reviewer feedback and revise manuscript tables and figures.",
        "constraints": ["Do not keep previous submission-ready/finalize parking as current truth."],
        "first_cycle_outputs": ["revised manuscript package"],
    }
    gate_report = {
        "emitted_at": "2026-05-09T22:39:41+00:00",
        "status": "blocked",
        "blockers": ["submission_surface_qc_failure_present"],
        "paper_line_open_supplementary_count": 0,
        "medical_publication_surface_status": "clear",
        "medical_publication_surface_current": True,
    }
    evaluation_summary = {
        "emitted_at": "2026-05-09T22:39:45+00:00",
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "complete_bundle_stage",
            "route_target": "finalize",
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
            "blocking_issue_count": 2,
        },
        "study_quality_truth": {
            "reviewer_first": {
                "ready": False,
                "status": "blocked",
                "open_concern_count": 1,
                "resolved_concern_count": 4,
            }
        },
        "quality_assessment": {
            "human_review_readiness": {
                "status": "blocked",
            }
        },
    }

    override = module.build_task_intake_progress_override(
        payload,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )

    assert override is not None
    assert override["quality_closure_truth"]["state"] == "quality_repair_required"
    assert override["paper_stage"] == "write"


def test_reviewer_revision_yields_to_complete_rebuttal_route_coverage_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "study"

    payload = {
        "task_id": "study-task::002::reviewer-feedback",
        "emitted_at": "2026-04-27T02:05:48+00:00",
        "task_intent": "Reviewer revision: update review matrix and action plan for all reviewer feedback.",
        "constraints": ["Do not write current_package directly."],
        "first_cycle_outputs": ["paper/rebuttal/review_matrix.md and action_plan.md"],
    }
    _write_json(
        study_root
        / "artifacts"
        / "stage_knowledge"
        / "analysis-campaign"
        / "closeouts"
        / "rebuttal_route_coverage_20260515T004548Z.json",
        {
            "generated_at": "2026-05-15T00:45:48Z",
            "route_outcome": "bounded_analysis_complete",
            "coverage_complete": True,
            "feedback_items_total": 11,
            "items_with_valid_route": 11,
            "required_route_classes_present": 5,
            "active_upstream_repair_units": 0,
            "next_owner_recommendation": "MAS finalize/bundle-stage owner",
            "slice_ledger": [
                {
                    "slice_id": "reviewer_revision_route_coverage",
                    "status": "complete",
                    "covered_items": 11,
                    "route_families": [
                        "paper_text",
                        "figure_table",
                        "analysis",
                        "claim_evidence",
                        "package",
                    ],
                }
            ],
            "authority_boundary": {
                "mutated_submission_package": False,
                "mutated_current_package": False,
            },
        },
    )
    gate_report = {
        "generated_at": "2026-05-15T00:45:49Z",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
        "supervisor_phase": "bundle_stage_ready",
    }
    evaluation_summary = {
        "emitted_at": "2026-05-15T00:45:50Z",
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "current_required_action": "continue_bundle_stage",
        },
        "study_quality_truth": {
            "contract_closed": True,
            "reviewer_first": {
                "ready": False,
                "status": "blocked",
                "open_concern_count": 1,
            },
        },
        "quality_review_loop": {"closure_state": "bundle_only_remaining"},
    }

    assert module.task_intake_is_reviewer_revision(payload) is True
    assert module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is None


def test_reviewer_revision_keeps_override_when_rebuttal_route_coverage_incomplete(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "study"

    payload = {
        "task_id": "study-task::002::reviewer-feedback",
        "emitted_at": "2026-04-27T02:05:48+00:00",
        "task_intent": "Reviewer revision: update review matrix and action plan for all reviewer feedback.",
        "first_cycle_outputs": ["paper/rebuttal/review_matrix.md and action_plan.md"],
    }
    _write_json(
        study_root
        / "artifacts"
        / "stage_knowledge"
        / "analysis-campaign"
        / "closeouts"
        / "rebuttal_route_coverage_20260515T004548Z.json",
        {
            "generated_at": "2026-05-15T00:45:48Z",
            "coverage_complete": False,
            "feedback_items_total": 11,
            "items_with_valid_route": 10,
            "active_upstream_repair_units": 1,
            "next_owner_recommendation": "MAS finalize/bundle-stage owner",
            "slice_ledger": [
                {
                    "slice_id": "reviewer_revision_route_coverage",
                    "status": "partial",
                    "covered_items": 10,
                }
            ],
        },
    )
    gate_report = {
        "generated_at": "2026-05-15T00:45:49Z",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "emitted_at": "2026-05-15T00:45:50Z",
        "quality_closure_truth": {"state": "bundle_only_remaining"},
        "study_quality_truth": {
            "reviewer_first": {
                "ready": False,
                "status": "blocked",
                "open_concern_count": 1,
            },
        },
        "quality_review_loop": {"closure_state": "bundle_only_remaining"},
    }

    override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )

    assert override is not None
    assert override["paper_stage"] == "write"


def test_reviewer_revision_route_coverage_closeout_cannot_override_publishability_gate_block(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "study"

    payload = {
        "task_id": "study-task::002::reviewer-feedback",
        "emitted_at": "2026-04-27T02:05:48+00:00",
        "task_intent": "Reviewer revision: update review matrix and action plan for all reviewer feedback.",
        "first_cycle_outputs": ["paper/rebuttal/review_matrix.md and action_plan.md"],
    }
    _write_json(
        study_root
        / "artifacts"
        / "stage_knowledge"
        / "analysis-campaign"
        / "closeouts"
        / "rebuttal_route_coverage_20260515T004548Z.json",
        {
            "generated_at": "2026-05-15T00:45:48Z",
            "coverage_complete": True,
            "feedback_items_total": 11,
            "items_with_valid_route": 11,
            "required_route_classes_present": 5,
            "active_upstream_repair_units": 0,
            "next_owner_recommendation": "MAS finalize/bundle-stage owner",
            "slice_ledger": [
                {
                    "slice_id": "reviewer_revision_route_coverage",
                    "status": "complete",
                    "covered_items": 11,
                }
            ],
        },
    )
    gate_report = {
        "generated_at": "2026-05-15T00:45:49Z",
        "status": "blocked",
        "allow_write": False,
        "blockers": ["medical_publication_surface_blocked"],
        "current_required_action": "return_to_publishability_gate",
    }
    evaluation_summary = {
        "emitted_at": "2026-05-15T00:45:50Z",
        "quality_closure_truth": {"state": "quality_repair_required"},
        "study_quality_truth": {
            "reviewer_first": {
                "ready": False,
                "status": "blocked",
                "open_concern_count": 1,
            },
        },
    }

    override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )

    assert override is not None
    assert override["quality_closure_truth"]["state"] == "quality_repair_required"
