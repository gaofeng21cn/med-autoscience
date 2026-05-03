from __future__ import annotations

import importlib
import json
from pathlib import Path


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def test_cross_study_completion_projects_feedback_dispatch_authority_and_artifact_state(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_cross_study_completion")
    studies_root = tmp_path / "studies"
    study_root = studies_root / "001-risk"
    _write_json(
        study_root / "artifacts" / "runtime" / "ai_first_feedback_state" / "latest.json",
        {
            "surface": "ai_first_feedback_state",
            "status": "attention_required",
            "counts": {"open_feedback_count": 2},
            "primary_action": {
                "action_id": "return_to_ai_reviewer_workflow",
                "summary": "补齐 AI reviewer workflow。",
            },
            "user_view": {
                "next_action": "补齐 AI reviewer workflow。",
                "human_review_required": True,
                "prompt": "USER_VIEW_PROMPT_CANARY",
            },
            "authority_contract": {
                "feedback_can_authorize_quality": False,
                "feedback_can_authorize_finalize": False,
                "feedback_can_authorize_submission": False,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "dispatch_ledger" / "latest.json",
        {
            "surface": "dispatch_ledger",
            "actions": [
                {"action_id": "act-1", "status": "completed"},
                {"action_id": "act-2", "status": "blocked"},
            ],
        },
    )
    _write_json(
        study_root / "artifacts" / "publication_eval" / "latest.json",
        {
            "assessment_provenance": {
                "owner": "mechanical_projection",
                "ai_reviewer_required": True,
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "runtime" / "artifact_runtime_proof" / "latest.json",
        {
            "surface": "artifact_runtime_proof",
            "rebuild_status": "blocked",
            "current_package_from_canonical_source": False,
            "blockers": [{"code": "delivery_manifest_stale"}],
            "raw_terminal_log": "RAW_LOG_CANARY",
        },
    )

    projection = module.build_ai_first_cross_study_completion_projection(studies_root=studies_root)

    assert projection["surface"] == "ai_first_cross_study_completion_projection"
    assert projection["read_model"] == "ai_first_cross_study_completion_read_model"
    assert projection["authority"] == "observability_governance_only"
    assert projection["status"] == "attention_required"
    assert projection["user_view"]["study_count"] == 1
    assert projection["user_view"]["attention_required_count"] == 1
    assert projection["user_view"]["human_review_required_count"] == 1
    assert projection["user_view"]["primary_next_action"] == "补齐 AI reviewer workflow。"
    assert "USER_VIEW_PROMPT_CANARY" not in str(projection["user_view"])
    assert "RAW_LOG_CANARY" not in str(projection["user_view"])

    study = projection["studies"][0]
    assert study["user_view"]["status"] == "attention_required"
    assert study["user_view"]["human_review_required"] is True
    maintainer = study["maintainer_view"]
    assert maintainer["feedback"]["open_feedback_count"] == 2
    assert maintainer["dispatch"]["open_action_count"] == 1
    assert maintainer["dispatch"]["failed_action_count"] == 1
    assert maintainer["ai_reviewer_authority"]["owner"] == "mechanical_projection"
    assert maintainer["ai_reviewer_authority"]["reviewer_backed"] is False
    assert maintainer["artifact_proof"]["rebuild_pending"] is True
    assert "raw_terminal_log" in maintainer["redacted_fields"]
    assert study["authority_contract"]["can_authorize_quality"] is False
    assert study["authority_contract"]["can_authorize_finalize"] is False
    assert study["authority_contract"]["can_authorize_submission"] is False


def test_cross_study_completion_can_use_synthetic_progress_snapshots_without_live_artifacts(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_cross_study_completion")
    study_root = tmp_path / "synthetic-studies" / "002-synthetic"
    progress_snapshots = {
        "002-synthetic": {
            "study_id": "002-synthetic",
            "current_stage": "finalize_handoff_observation",
            "next_system_action": "continue_current_route",
            "needs_user_decision": False,
            "ai_first_feedback_state": {
                "surface": "ai_first_feedback_state",
                "status": "on_track",
                "counts": {"open_feedback_count": 0},
                "user_view": {"human_review_required": False, "next_action": "continue_current_route"},
            },
            "dispatch_ledger": {
                "surface": "dispatch_ledger",
                "actions": [{"action_id": "act-1", "status": "completed"}],
            },
            "publication_eval": {
                "assessment_provenance": {
                    "owner": "ai_reviewer",
                    "ai_reviewer_required": False,
                },
                "reviewer_operating_system": {"trace_id": "reviewer-os-001"},
            },
            "ai_first_default_entry_state": {
                "human_review_required": False,
                "artifact_proof": {
                    "surface": "artifact_runtime_proof",
                    "rebuild_status": "current",
                    "current_package_from_canonical_source": True,
                    "rebuild_pending": False,
                    "blockers": [],
                },
                "ai_reviewer_workflow": {
                    "trace_complete": True,
                    "finalize_authorized": True,
                    "submission_authorized": True,
                    "full_prompt": "SYNTHETIC_PROMPT_CANARY",
                },
            },
        },
    }

    projection = module.build_ai_first_cross_study_completion_projection(
        study_roots=[study_root],
        progress_snapshots=progress_snapshots,
    )

    assert projection["status"] == "on_track"
    assert projection["user_view"] == {
        "status": "on_track",
        "study_count": 1,
        "attention_required_count": 0,
        "human_review_required_count": 0,
        "primary_next_action": "continue_current_study_routes",
        "studies": [
            {
                "study_id": "002-synthetic",
                "status": "on_track",
                "current_stage": "finalize_handoff_observation",
                "next_action": "continue_current_route",
                "human_review_required": False,
            }
        ],
    }
    study = projection["studies"][0]
    assert study["maintainer_view"]["ai_reviewer_authority"]["reviewer_backed"] is True
    assert study["maintainer_view"]["artifact_proof"]["rebuild_pending"] is False
    assert "full_prompt" in study["maintainer_view"]["redacted_fields"]
    assert "SYNTHETIC_PROMPT_CANARY" not in str(projection["user_view"])
    assert projection["authority_contract"] == {
        "authority": "observability_governance_only",
        "can_authorize_quality": False,
        "can_authorize_finalize": False,
        "can_authorize_submission": False,
        "can_mutate_runtime": False,
        "mechanical_projection_is_quality_authority": False,
    }


def test_cross_study_completion_reports_insufficient_observability_for_empty_fixture(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_first_cross_study_completion")
    study_root = tmp_path / "studies" / "003-empty"
    study_root.mkdir(parents=True)

    projection = module.build_ai_first_cross_study_completion_projection(studies_root=tmp_path / "studies")

    assert projection["status"] == "insufficient_observability"
    assert projection["user_view"]["primary_next_action"] == (
        "materialize_ai_first_feedback_dispatch_and_artifact_surfaces"
    )
    assert projection["maintainer_view"]["insufficient_observability_count"] == 1
    assert projection["studies"][0]["status"] == "insufficient_observability"
    assert projection["studies"][0]["authority_contract"]["can_authorize_submission"] is False
