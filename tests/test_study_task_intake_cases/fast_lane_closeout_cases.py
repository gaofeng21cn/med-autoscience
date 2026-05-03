from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _reviewer_revision_payload() -> dict[str, object]:
    return {
        "task_id": "study-task::001-dm-cvd-mortality-risk::20260426T072323Z",
        "emitted_at": "2026-04-26T07:23:23+00:00",
        "task_intent": (
            "用户已对当前 CVD 风险预测投稿包给出新的审稿式反馈；这是显式重新激活同一论文线的 "
            "reviewer revision / manuscript revision。"
        ),
        "constraints": ["不得手工 patch manuscript/current_package 投影作为最终修复。"],
        "first_cycle_outputs": [
            "review_matrix/action_plan mapping all user concerns to manuscript revisions"
        ],
    }


def _write_fast_lane_closeout(study_root: Path) -> None:
    _write_json(
        study_root
        / "artifacts"
        / "controller"
        / "task_intake"
        / "manuscript_fast_lane_closeout_20260428T005000Z.json",
        {
            "schema_version": 1,
            "record_type": "manuscript_fast_lane_closeout",
            "surface_kind": "manuscript_fast_lane_closeout",
            "created_at": "2026-04-28T00:50:00Z",
            "source_task_id": "study-task::001-dm-cvd-mortality-risk::20260426T072323Z",
            "status": "completed",
            "completion_state": "foreground_fast_lane_completed",
            "execution_owner": "codex_foreground_under_mas_controller",
            "canonical_write_surface": "paper/",
            "projection_surface": "manuscript/current_package/",
            "auto_resume_policy": "do_not_resume_superseded_task_intake",
            "scope": {
                "existing_evidence_only": True,
                "canonical_paper_text_or_structure_only": True,
                "new_analysis_performed": False,
            },
            "validation": {
                "canonical_paper_writeback_complete": True,
                "export_sync_complete": True,
                "qc_complete": True,
                "package_consistency_checked": True,
            },
        },
    )


def test_reviewer_revision_intake_yields_to_fresh_manuscript_fast_lane_closeout(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    closeout_module = importlib.import_module("med_autoscience.study_task_intake_fast_lane_closeout")
    study_root = tmp_path / "studies" / "001-dm-cvd-mortality-risk"
    payload = _reviewer_revision_payload()
    _write_json(module.latest_task_intake_json_path(study_root=study_root), payload)

    stale_override = module.build_task_intake_progress_override(payload, study_root=study_root)
    assert stale_override is not None
    assert stale_override["current_required_action"] == "continue_write_stage"

    _write_fast_lane_closeout(study_root)
    gate_report = {
        "generated_at": "2026-04-28T00:32:47+00:00",
        "status": "clear",
        "allow_write": True,
        "blockers": [],
        "current_required_action": "continue_bundle_stage",
    }
    evaluation_summary = {
        "generated_at": "2026-04-28T00:32:47+00:00",
        "quality_closure_truth": {
            "state": "bundle_only_remaining",
            "summary": "Scientific revision is closed; only downstream package handoff remains.",
            "current_required_action": "continue_bundle_stage",
            "route_target": "finalize",
        },
        "quality_review_loop": {
            "closure_state": "bundle_only_remaining",
            "current_phase": "bundle_stage_ready",
        },
    }

    assert closeout_module.task_intake_yields_to_verified_manuscript_fast_lane_closeout(
        payload,
        task_intake_root=module.task_intake_root(study_root=study_root),
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    ) is True
    assert module.task_intake_yields_to_manuscript_fast_lane_closeout(
        payload,
        study_root=study_root,
    ) is True
    assert (
        module.build_task_intake_progress_override(
            payload,
            study_root=study_root,
            publishability_gate_report=gate_report,
            evaluation_summary=evaluation_summary,
        )
        is None
    )


def test_reviewer_revision_fast_lane_closeout_does_not_yield_when_publication_gate_still_blocked(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.study_task_intake")
    study_root = tmp_path / "studies" / "001-dm-cvd-mortality-risk"
    payload = _reviewer_revision_payload()
    _write_fast_lane_closeout(study_root)
    gate_report = {
        "status": "blocked",
        "allow_write": False,
        "blockers": [
            "stale_submission_minimal_authority",
            "medical_publication_surface_blocked",
            "reviewer_first_concerns_unresolved",
            "claim_evidence_consistency_failed",
            "submission_hardening_incomplete",
        ],
        "current_required_action": "return_to_publishability_gate",
        "medical_publication_surface_status": "blocked",
        "bundle_tasks_downstream_only": True,
        "supervisor_phase": "publishability_gate_blocked",
    }
    evaluation_summary = {
        "quality_closure_truth": {
            "state": "review_required",
            "summary": "当前 publication_eval 只是机械投影；必须先由 AI reviewer 给出质量闭环判断。",
            "current_required_action": "return_to_ai_reviewer",
            "route_target": "publication_eval",
        },
        "quality_review_loop": {
            "closure_state": "review_required",
            "current_phase": "revision_required",
            "recommended_next_action": "先发起 AI reviewer 复评。",
        },
    }

    override = module.build_task_intake_progress_override(
        payload,
        study_root=study_root,
        publishability_gate_report=gate_report,
        evaluation_summary=evaluation_summary,
    )

    assert override is not None
    assert override["current_required_action"] == "continue_write_stage"
    assert override["quality_closure_truth"]["state"] == "quality_repair_required"
