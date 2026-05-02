from __future__ import annotations

import importlib
from pathlib import Path


def _progress_snapshot(tmp_path: Path) -> dict[str, object]:
    return {
        "study_id": "001-risk",
        "study_root": str(tmp_path / "studies" / "001-risk"),
        "current_stage": "publication_supervision",
        "current_blockers": ["AI reviewer trace 还未闭环。"],
        "next_system_action": "回到 AI reviewer workflow 补齐质量授权。",
        "needs_user_decision": False,
        "needs_physician_decision": False,
        "progress_freshness": {"status": "stale", "summary": "最近没有有效研究推进。"},
        "ai_first_default_entry_state": {
            "surface": "ai_first_default_entry_state",
            "status": "review_required",
            "recommended_next_step": "先补齐 AI reviewer workflow，再刷新 artifact proof。",
            "human_review_required": True,
            "pre_draft": {
                "surface": "pre_draft_quality_runtime",
                "draft_ready": False,
                "route_back_required": True,
                "route_back_reason": "study_charter_missing",
                "summary": "写作前 readiness 未闭合。",
            },
            "ai_reviewer_workflow": {
                "surface": "ai_reviewer_runtime_workflow",
                "authority_state": "projection_only",
                "finalize_authorized": False,
                "submission_authorized": False,
                "summary": "当前质量判断仍是机械投影。",
                "trace_complete": False,
                "prompt": "internal prompt must stay hidden",
                "token_count": 1234,
            },
            "artifact_proof": {
                "surface": "artifact_runtime_proof",
                "rebuild_pending": True,
                "current_package_from_canonical_source": False,
                "summary": "artifact proof 未闭合。",
                "log_path": "/tmp/internal.log",
            },
            "route_back": {
                "required": True,
                "reason": "return_to_analysis_campaign",
                "ai_reviewer_target": "analysis-campaign",
            },
        },
        "ai_first_operations_dashboard": {
            "maintainer_view": {
                "ai_reviewer_trace": {"complete": False},
                "route_back": {"count": 1, "target": "analysis-campaign"},
                "artifact_stale": {
                    "stale_artifact_count": 2,
                    "current_package_from_canonical_source": False,
                },
            },
        },
        "refs": {
            "publication_eval_path": str(tmp_path / "studies" / "001-risk" / "artifacts" / "publication_eval" / "latest.json"),
            "controller_decision_path": str(tmp_path / "studies" / "001-risk" / "artifacts" / "controller_decisions" / "latest.json"),
            "ai_first_observability_delivery_manifest_path": str(tmp_path / "studies" / "001-risk" / "manuscript" / "delivery_manifest.json"),
            "medical_prose_review_path": str(tmp_path / "studies" / "001-risk" / "paper" / "review" / "medical_prose_review.json"),
        },
    }


def test_ai_first_feedback_state_classifies_runtime_feedback_without_quality_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_feedback")

    state = module.build_ai_first_feedback_state(progress_snapshot=_progress_snapshot(tmp_path))

    assert state["surface"] == "ai_first_feedback_state"
    assert state["read_model"] == "ai_first_feedback_read_model"
    assert state["authority"] == "observability_only"
    categories = {item["category"] for item in state["events"]}
    assert {
        "predraft_gap",
        "ai_reviewer_trace_gap",
        "route_back_open",
        "artifact_rebuild_pending",
        "manual_judgment_pending",
        "runtime_progress_stale",
    }.issubset(categories)
    assert state["primary_feedback"]["category"] == "ai_reviewer_trace_gap"
    assert state["counts"]["open_route_back_count"] == 1
    assert state["counts"]["artifact_rebuild_pending_count"] == 1
    assert state["counts"]["ai_reviewer_trace_incomplete_count"] == 1
    assert state["counts"]["manual_judgment_pending_count"] == 1
    assert state["authority_contract"]["feedback_can_authorize_quality"] is False
    assert state["authority_contract"]["feedback_can_authorize_submission"] is False
    assert "internal prompt" not in str(state["user_view"])
    assert "token_count" not in str(state["user_view"])


def test_ai_first_feedback_state_projects_category_actions_without_authority(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_feedback")

    state = module.build_ai_first_feedback_state(progress_snapshot=_progress_snapshot(tmp_path))

    actions = {
        item["category"]: item["action_recommendation"]
        for item in state["events"]
        if item.get("category") != "quality_toil_repeat"
    }
    assert actions["predraft_gap"]["action_id"] == "return_to_predraft_readiness"
    assert actions["predraft_gap"]["target_surface"] == "pre_draft_quality_runtime"
    assert actions["ai_reviewer_trace_gap"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert actions["ai_reviewer_trace_gap"]["target_surface"] == "ai_reviewer_runtime_workflow"
    assert actions["route_back_open"]["action_id"] == "continue_route_back"
    assert actions["route_back_open"]["target_surface"] == "same_line_route_back"
    assert actions["artifact_rebuild_pending"]["action_id"] == "rebuild_canonical_artifacts"
    assert actions["artifact_rebuild_pending"]["target_surface"] == "artifact_runtime_proof"
    assert actions["manual_judgment_pending"]["action_id"] == "request_human_decision"
    assert actions["manual_judgment_pending"]["target_surface"] == "human_decision_gate"
    assert actions["runtime_progress_stale"]["action_id"] == "refresh_runtime_progress"
    assert actions["runtime_progress_stale"]["target_surface"] == "runtime_progress_observer"
    assert state["primary_action"]["action_id"] == "return_to_ai_reviewer_workflow"
    assert state["user_view"]["next_action"] == "补齐 AI reviewer workflow、publication eval 与 medical prose review。"
    assert state["authority_contract"]["feedback_actions_can_authorize_quality"] is False
    assert state["authority_contract"]["feedback_actions_can_authorize_submission"] is False
    assert "internal prompt" not in str(state["primary_action"])
    assert "token_count" not in str(state["primary_action"])


def test_ai_first_feedback_ledger_tracks_repeat_and_closure(tmp_path: Path) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_feedback")
    study_root = tmp_path / "studies" / "001-risk"
    progress = _progress_snapshot(tmp_path)

    first = module.materialize_ai_first_feedback_state(
        study_root=study_root,
        progress_snapshot=progress,
        observed_at="2026-05-02T01:00:00+00:00",
    )
    second = module.materialize_ai_first_feedback_state(
        study_root=study_root,
        progress_snapshot=progress,
        observed_at="2026-05-02T02:00:00+00:00",
    )

    assert first["ledger"]["open_event_count"] >= 1
    assert second["counts"]["repeat_toil_count"] >= 1
    ledger = module.read_feedback_ledger(study_root=study_root)
    assert ledger is not None
    assert max(item["repeat_count"] for item in ledger["events"] if item["closed_at"] is None) == 2

    closed_progress = {
        "study_id": "001-risk",
        "current_stage": "bundle_stage_ready",
        "next_system_action": "continue_current_route",
        "progress_freshness": {"status": "fresh"},
        "ai_first_default_entry_state": {
            "surface": "ai_first_default_entry_state",
            "status": "ready_for_current_paper_route",
            "human_review_required": False,
            "pre_draft": {"draft_ready": True},
            "ai_reviewer_workflow": {
                "trace_complete": True,
                "finalize_authorized": True,
                "submission_authorized": True,
            },
            "artifact_proof": {
                "rebuild_pending": False,
                "current_package_from_canonical_source": True,
            },
            "route_back": {"required": False},
        },
        "ai_first_operations_dashboard": {
            "maintainer_view": {
                "ai_reviewer_trace": {"complete": True},
                "route_back": {"count": 0},
                "artifact_stale": {
                    "stale_artifact_count": 0,
                    "current_package_from_canonical_source": True,
                },
            },
        },
    }
    closed = module.materialize_ai_first_feedback_state(
        study_root=study_root,
        progress_snapshot=closed_progress,
        observed_at="2026-05-02T03:00:00+00:00",
    )

    assert closed["status"] == "on_track"
    ledger = module.read_feedback_ledger(study_root=study_root)
    assert ledger is not None
    assert ledger["open_event_count"] == 0
    assert ledger["closed_event_count"] >= second["ledger"]["open_event_count"]
