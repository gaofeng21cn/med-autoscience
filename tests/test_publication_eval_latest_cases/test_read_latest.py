from __future__ import annotations

import importlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.test_publication_eval_latest_cases.shared import (
    MODULE_NAME,
    _minimal_payload,
    _quality_assessment,
    _reviewer_operating_system,
    _write_cutover_receipt,
    _write_json,
)

def test_resolve_publication_eval_latest_ref_defaults_to_eval_owned_latest_surface(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"

    resolved = module.resolve_publication_eval_latest_ref(study_root=study_root)

    assert resolved == (study_root / "artifacts" / "publication_eval" / "latest.json").resolve()
def test_read_publication_eval_latest_reads_typed_latest_artifact(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved == {
        **payload,
        "assessment_provenance": {
            **payload["assessment_provenance"],
            "mechanical_projection_used_as_quality_authority": False,
        },
    }
def test_read_publication_eval_latest_accepts_quality_assessment(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    payload["quality_assessment"] = {
        "clinical_significance": {
            "status": "partial",
            "summary": "Clinical framing exists but interpretation targets remain incomplete.",
            "evidence_refs": [payload["delivery_context_refs"]["paper_root_ref"]],
        },
        "evidence_strength": {
            "status": "blocked",
            "summary": "Paper-facing evidence surface is still incomplete.",
            "evidence_refs": [payload["runtime_context_refs"]["main_result_ref"]],
        },
        "novelty_positioning": {
            "status": "underdefined",
            "summary": "Novelty framing has not been frozen in the charter.",
            "evidence_refs": [payload["charter_context_ref"]["ref"]],
        },
        "human_review_readiness": {
            "status": "blocked",
            "summary": "Human-facing package is not ready yet.",
            "evidence_refs": [payload["delivery_context_refs"]["submission_minimal_ref"]],
        },
    }
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved == {
        **payload,
        "assessment_provenance": {
            **payload["assessment_provenance"],
            "mechanical_projection_used_as_quality_authority": False,
        },
    }
def test_read_publication_eval_latest_marks_legacy_payload_as_projection_only(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    payload.pop("assessment_provenance")
    _write_json(latest_path, payload)

    resolved = module.read_publication_eval_latest(study_root=study_root)

    assert resolved["assessment_provenance"] == {
        "owner": "mechanical_projection",
        "source_kind": "legacy_publication_eval_projection",
        "policy_id": "publication_gate_projection_v1",
        "source_refs": [
            payload["charter_context_ref"]["ref"],
            payload["runtime_context_refs"]["runtime_escalation_ref"],
            payload["runtime_context_refs"]["main_result_ref"],
            payload["delivery_context_refs"]["paper_root_ref"],
            payload["delivery_context_refs"]["submission_minimal_ref"],
        ],
        "ai_reviewer_required": True,
        "mechanical_projection_used_as_quality_authority": False,
    }
def test_read_publication_eval_latest_rejects_legacy_ai_reviewer_recheck_route_verdict(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    payload = _minimal_payload(study_root)
    payload["assessment_provenance"] = {
        "owner": "ai_reviewer",
        "source_kind": "publication_eval_ai_reviewer_recheck",
        "policy_id": "medical_publication_critique_v1",
        "source_refs": [
            str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            str(study_root / "paper" / "draft.md"),
        ],
        "ai_reviewer_required": False,
        "mechanical_projection_used_as_quality_authority": False,
    }
    payload["verdict"] = {
        "overall_verdict": "review_owner_clear_for_bundle_stage",
        "primary_claim_status": "supported_with_limitations",
        "summary": "AI-reviewer recheck completed and selected downstream bundle-stage continuation.",
        "stop_loss_pressure": "watch",
    }
    payload["recommended_actions"] = [
        {
            "action_id": "continue-bundle-stage",
            "action_type": "continue_same_line",
            "priority": "next",
            "reason": "Continue downstream bundle-stage handling after AI-reviewer recheck.",
            "route_target": "controller",
            "route_key_question": "Continue downstream bundle-stage handling.",
            "route_rationale": "The AI reviewer recheck closed the review-workflow blocker.",
            "evidence_refs": [str(study_root / "paper" / "review" / "review_ledger.json")],
            "requires_controller_decision": False,
        }
    ]
    _write_json(latest_path, payload)

    with pytest.raises(ValueError, match="overall_verdict must be one of"):
        module.read_publication_eval_latest(study_root=study_root)
def test_resolve_publication_eval_latest_ref_rejects_med_deepscientist_runtime_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    workspace_root = tmp_path / "workspace"
    study_root = workspace_root / "studies" / "001-risk"
    runtime_ref = workspace_root / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001" / "artifacts" / "publication_eval" / "latest.json"

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.resolve_publication_eval_latest_ref(study_root=study_root, ref=runtime_ref)
def test_resolve_publication_eval_latest_ref_rejects_cross_repo_paths(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "repo-a" / "studies" / "001-risk"
    cross_repo_ref = tmp_path / "repo-b" / "studies" / "001-risk" / "artifacts" / "publication_eval" / "latest.json"

    with pytest.raises(ValueError, match="eval-owned latest artifact"):
        module.resolve_publication_eval_latest_ref(study_root=study_root, ref=cross_repo_ref)
def test_read_publication_eval_latest_rejects_non_object_payload(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    _write_json(latest_path, ["not", "an", "object"])

    with pytest.raises(ValueError, match="JSON object"):
        module.read_publication_eval_latest(study_root=study_root)
