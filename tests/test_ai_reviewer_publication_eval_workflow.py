from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _refs(study_root: Path) -> dict[str, str]:
    return {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_gate" / "latest.json"),
    }


def _quality_assessment(study_root: Path) -> dict[str, Any]:
    refs = _refs(study_root)
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical question is manuscript-safe.",
            "evidence_refs": [refs["study_charter"], refs["manuscript"]],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Claim evidence is closed.",
            "evidence_refs": [refs["evidence_ledger"]],
        },
        "novelty_positioning": {
            "status": "ready",
            "summary": "Novelty boundary is explicit.",
            "evidence_refs": [refs["study_charter"]],
        },
        "medical_journal_prose_quality": {
            "status": "ready",
            "summary": "Medical prose review is clear.",
            "evidence_refs": [refs["medical_prose_review"]],
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "Review ledger is closed.",
            "evidence_refs": [refs["review_ledger"]],
        },
    }


def _publication_eval_record(study_root: Path) -> dict[str, Any]:
    refs = _refs(study_root)
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-04T00:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": refs["study_charter"],
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "Submit a clinically restrained manuscript.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "runtime" / "runtime_escalation_record.json"),
            "main_result_ref": str(study_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [refs["manuscript"], refs["evidence_ledger"], refs["review_ledger"]],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "AI reviewer closed publication-facing quality.",
            "stop_loss_pressure": "none",
        },
        "quality_assessment": _quality_assessment(study_root),
        "gaps": [
            {
                "gap_id": "gap-closed-001",
                "gap_type": "evidence",
                "severity": "optional",
                "summary": "No blocking evidence gap remains after AI reviewer closure.",
                "evidence_refs": [refs["evidence_ledger"]],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "continue-first-draft",
                "action_type": "continue_same_line",
                "priority": "next",
                "reason": "Proceed to first full draft.",
                "route_target": "write",
                "route_key_question": "Write the first full draft.",
                "route_rationale": "Reviewer OS trace is complete.",
                "evidence_refs": [refs["review_ledger"]],
                "requires_controller_decision": True,
            }
        ],
    }


def test_ai_reviewer_publication_eval_workflow_materializes_latest_with_reviewer_os_trace(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)

    result = module.run_ai_reviewer_publication_eval_workflow(
        study_root=study_root,
        manuscript_ref=refs["manuscript"],
        evidence_ref=refs["evidence_ledger"],
        review_ref=refs["review_ledger"],
        charter_ref=refs["study_charter"],
        additional_refs={
            "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
            "claim_evidence_map": refs["claim_evidence_map"],
            "medical_prose_review": refs["medical_prose_review"],
            "publication_gate_projection": refs["publication_gate_projection"],
        },
        record=_publication_eval_record(study_root),
    )

    latest_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    latest = json.loads(latest_path.read_text(encoding="utf-8"))

    assert result["surface"] == "ai_reviewer_publication_eval_workflow"
    assert result["status"] == "materialized"
    assert result["artifact_path"] == str(latest_path.resolve())
    assert latest["assessment_provenance"]["owner"] == "ai_reviewer"
    assert latest["assessment_provenance"]["ai_reviewer_required"] is False
    assert latest["emitted_at"] > "2026-05-04T00:00:00+00:00"
    assert latest["reviewer_operating_system"]["input_bundle"]["manuscript"] == refs["manuscript"]
    assert latest["reviewer_operating_system"]["route_back_decision"] == {
        "recommended_action": "continue_same_line",
        "rationale": "Proceed to first full draft.",
    }


def test_ai_reviewer_publication_eval_workflow_fails_closed_when_required_ref_missing(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)

    try:
        module.run_ai_reviewer_publication_eval_workflow(
            study_root=study_root,
            manuscript_ref=refs["manuscript"],
            evidence_ref=refs["evidence_ledger"],
            review_ref=refs["review_ledger"],
            charter_ref=refs["study_charter"],
            additional_refs={
                "medical_manuscript_blueprint": refs["medical_manuscript_blueprint"],
                "claim_evidence_map": refs["claim_evidence_map"],
                "medical_prose_review": refs["medical_prose_review"],
            },
            record=_publication_eval_record(study_root),
        )
    except ValueError as exc:
        assert "missing input ref for publication_gate_projection" in str(exc)
    else:
        raise AssertionError("workflow accepted incomplete reviewer OS input refs")

    assert not (study_root / "artifacts" / "publication_eval" / "latest.json").exists()
