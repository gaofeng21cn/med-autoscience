from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any


MODULE_NAME = "med_autoscience.controllers.ai_reviewer_runtime_workflow"


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _surface_refs(study_root: Path) -> dict[str, str]:
    paper_root = study_root / "paper"
    return {
        "manuscript": str(paper_root / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(paper_root / "evidence_ledger.json"),
        "review_ledger": str(paper_root / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(paper_root / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(paper_root / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }


def _reviewer_operating_system(study_root: Path) -> dict[str, Any]:
    refs = _surface_refs(study_root)
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": refs,
        "rubric_scores": {
            dimension: {
                "status": "ready",
                "rationale": f"{dimension} is closed against reviewer-visible evidence.",
                "evidence_refs": [refs["manuscript"], refs["evidence_ledger"], refs["review_ledger"]],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is closed against reviewer-visible evidence.",
            }
            for dimension in dimensions
        ],
        "future_facing_limitations_plan": [
            {
                "limitation": "Finalize authorization is scoped to the reviewed paper snapshot.",
                "impact_on_claim": "Final claims must remain restrained to reviewed evidence support.",
                "required_future_analysis_data_or_design": "Refresh AI reviewer workflow before future substantive changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "continue_finalize",
            "rationale": "AI reviewer workflow evidence is closed for finalize handoff.",
        },
    }


def _quality_assessment(study_root: Path) -> dict[str, Any]:
    refs = _surface_refs(study_root)
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical framing is closed.",
            "evidence_refs": [refs["study_charter"]],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Claim evidence is closed.",
            "evidence_refs": [refs["evidence_ledger"]],
        },
        "novelty_positioning": {
            "status": "ready",
            "summary": "Novelty boundary is closed.",
            "evidence_refs": [refs["study_charter"]],
        },
        "medical_journal_prose_quality": {
            "status": "ready",
            "summary": "Medical journal prose review is clear.",
            "evidence_refs": [refs["medical_prose_review"]],
        },
        "human_review_readiness": {
            "status": "ready",
            "summary": "Human review package is closed.",
            "evidence_refs": [refs["review_ledger"]],
        },
    }


def _publication_eval_payload(study_root: Path, *, owner: str = "ai_reviewer") -> dict[str, Any]:
    refs = _surface_refs(study_root)
    ai_reviewer = owner == "ai_reviewer"
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-05-02T08:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-05-02T08:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": refs["study_charter"],
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "Submit a manuscript-safe clinical prediction paper.",
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
            "owner": owner,
            "source_kind": "publication_eval_ai_reviewer" if ai_reviewer else "publication_gate_report",
            "policy_id": "medical_publication_critique_v1" if ai_reviewer else "publication_gate_projection_v1",
            "source_refs": [refs["manuscript"], refs["evidence_ledger"], refs["review_ledger"]],
            "ai_reviewer_required": not ai_reviewer,
        },
        "verdict": {
            "overall_verdict": "promising" if ai_reviewer else "mixed",
            "primary_claim_status": "supported" if ai_reviewer else "partial",
            "summary": "AI reviewer closed the paper-facing quality workflow."
            if ai_reviewer
            else "Mechanical projection cannot authorize quality closure.",
            "stop_loss_pressure": "none",
        },
        "quality_assessment": _quality_assessment(study_root),
        "reviewer_operating_system": _reviewer_operating_system(study_root) if ai_reviewer else None,
        "gaps": [
            {
                "gap_id": "delivery-metadata-check",
                "gap_type": "delivery",
                "severity": "optional",
                "summary": "Only non-quality delivery metadata remains.",
                "evidence_refs": [str(study_root / "paper" / "submission_minimal" / "submission_manifest.json")],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "continue-finalize",
                "action_type": "continue_same_line" if ai_reviewer else "return_to_controller",
                "priority": "next",
                "reason": "Continue finalize handoff." if ai_reviewer else "Return for AI reviewer judgment.",
                "evidence_refs": [refs["review_ledger"]],
                "requires_controller_decision": True,
                **(
                    {
                        "route_target": "finalize",
                        "route_key_question": "Complete final author-facing handoff.",
                        "route_rationale": "AI reviewer workflow evidence is closed.",
                    }
                    if ai_reviewer
                    else {}
                ),
            }
        ],
    }


def _write_publication_eval(study_root: Path, *, owner: str = "ai_reviewer") -> None:
    payload = _publication_eval_payload(study_root, owner=owner)
    if payload["reviewer_operating_system"] is None:
        payload.pop("reviewer_operating_system")
        payload.pop("quality_assessment")
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)


def _style_currentness(study_root: Path) -> dict[str, Any]:
    from med_autoscience.medical_journal_style_corpus import (
        materialize_medical_journal_style_corpus,
        read_medical_journal_style_corpus,
    )

    materialize_medical_journal_style_corpus(study_root=study_root)
    corpus = read_medical_journal_style_corpus(study_root=study_root)
    return {
        "status": "current",
        "style_corpus_ref": str(study_root / "paper" / "medical_journal_style_corpus.json"),
        "corpus_id": corpus["corpus_id"],
        "style_version": corpus["style_version"],
        "source_set_id": corpus["source_set_id"],
        "style_digest": corpus["style_digest"],
        "style_corpus_currentness": corpus["style_currentness"],
    }


def _medical_prose_review_payload(study_root: Path, *, route_back_required: bool = False) -> dict[str, Any]:
    request_digest = "sha256:" + ("a" * 64)
    return {
        "schema_version": 1,
        "surface": "medical_prose_review",
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "medical_prose_review",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "request_digest": request_digest,
        },
        "style_currentness": _style_currentness(study_root),
        "medical_journal_prose_quality": {
            "status": "partial" if route_back_required else "ready",
            "overall_style_verdict": "revise" if route_back_required else "clear",
            "summary": "Rewrite figure-led prose." if route_back_required else "Medical journal prose is clear.",
            "route_back_recommendation": {
                "required": route_back_required,
                "route_target": "write" if route_back_required else "none",
                "reason": "Rewrite figure-led prose." if route_back_required else "No route back required.",
            },
        },
        "mechanical_safety_flags": [],
        "source_refs": [str(study_root / "paper" / "manuscript.md")],
    }


def _write_medical_prose_review(study_root: Path, *, route_back_required: bool = False) -> None:
    _write_json(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json",
        _medical_prose_review_payload(study_root, route_back_required=route_back_required),
    )


def _write_closed_ledgers(study_root: Path) -> None:
    _write_json(
        study_root / "paper" / "review" / "review_ledger.json",
        {
            "schema_version": 1,
            "status": "closed",
            "concerns": [
                {
                    "concern_id": "RC1",
                    "reviewer_id": "reviewer-1",
                    "summary": "Clarify the endpoint boundary.",
                    "severity": "major",
                    "status": "resolved",
                }
            ],
            "charter_expectation_closures": [
                {
                    "expectation_key": "scientific_followup_questions",
                    "expectation_text": "Reviewer-first concerns are closed.",
                    "status": "closed",
                    "closed_at": "2026-05-02T08:00:00+00:00",
                }
            ],
        },
    )
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "status": "closed",
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The primary claim is directly supported.",
                    "status": "supported",
                }
            ],
            "charter_expectation_closures": [
                {
                    "expectation_key": "minimum_sci_ready_evidence_package",
                    "expectation_text": "Primary evidence package is closed.",
                    "status": "closed",
                    "closed_at": "2026-05-02T08:00:00+00:00",
                }
            ],
        },
    )


def _write_complete_workflow(study_root: Path) -> None:
    _write_publication_eval(study_root)
    _write_medical_prose_review(study_root)
    _write_closed_ledgers(study_root)


def test_complete_ai_reviewer_workflow_authorizes_finalize_and_submission(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_complete_workflow(study_root)

    state = module.build_ai_reviewer_runtime_workflow_state(study_root)

    assert state["surface"] == "ai_reviewer_runtime_workflow_state"
    assert state["schema_version"] == 1
    assert state["quality_authority"]["owner"] == "ai_reviewer"
    assert state["quality_authority"]["state"] == "authorized"
    assert state["quality_authority"]["mechanical_projection_can_authorize_quality"] is False
    assert state["finalize_authorization"] == {
        "authorized": True,
        "status": "authorized",
        "reason": "AI reviewer publication eval, medical prose review, review ledger, and evidence ledger are closed.",
    }
    assert state["submission_authorization"] == {
        "authorized": True,
        "status": "authorized",
        "reason": "AI reviewer publication eval, medical prose review, review ledger, and evidence ledger are closed.",
    }
    assert state["route_back"] == {
        "required": False,
        "target": None,
        "reason": None,
        "source": None,
    }
    assert state["blockers"] == []
    assert state["refs"]["review_ledger"]["relative_path"] == "paper/review/review_ledger.json"


def test_mechanical_publication_eval_is_projection_only_and_review_required(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_complete_workflow(study_root)
    _write_publication_eval(study_root, owner="mechanical_projection")

    state = module.build_ai_reviewer_runtime_workflow_state(study_root)

    assert state["quality_authority"]["owner"] == "mechanical_projection"
    assert state["quality_authority"]["state"] == "projection_only"
    assert state["finalize_authorization"]["authorized"] is False
    assert state["finalize_authorization"]["status"] == "review_required"
    assert state["submission_authorization"]["authorized"] is False
    assert state["submission_authorization"]["status"] == "review_required"
    assert "publication_eval_not_ai_reviewer_authority" in state["blockers"]
    assert state["route_back"]["required"] is True
    assert state["route_back"]["target"] == "ai_reviewer"


def test_ai_reviewer_publication_eval_with_unready_prose_quality_blocks_finalize_and_submission(
    tmp_path: Path,
) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_complete_workflow(study_root)
    payload = _publication_eval_payload(study_root, owner="ai_reviewer")
    payload["quality_assessment"]["medical_journal_prose_quality"]["status"] = "underdefined"
    payload["quality_assessment"]["medical_journal_prose_quality"]["summary"] = (
        "AI reviewer has not closed manuscript-native medical journal prose quality."
    )
    _write_json(study_root / "artifacts" / "publication_eval" / "latest.json", payload)

    state = module.build_ai_reviewer_runtime_workflow_state(study_root)

    assert state["quality_authority"]["state"] == "review_required"
    assert state["finalize_authorization"]["authorized"] is False
    assert state["submission_authorization"]["authorized"] is False
    assert "medical_journal_prose_quality_not_ready" in state["blockers"]


def test_missing_medical_prose_review_blocks_finalize_and_submission(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_publication_eval(study_root)
    _write_closed_ledgers(study_root)

    state = module.build_ai_reviewer_runtime_workflow_state(study_root)

    assert state["quality_authority"]["state"] == "review_required"
    assert state["finalize_authorization"]["authorized"] is False
    assert state["submission_authorization"]["authorized"] is False
    assert "medical_prose_review_missing" in state["blockers"]


def test_medical_prose_review_route_back_blocks_finalize_and_submission(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_publication_eval(study_root)
    _write_medical_prose_review(study_root, route_back_required=True)
    _write_closed_ledgers(study_root)

    state = module.build_ai_reviewer_runtime_workflow_state(study_root)

    assert state["quality_authority"]["state"] == "review_required"
    assert state["finalize_authorization"]["authorized"] is False
    assert state["submission_authorization"]["authorized"] is False
    assert "medical_prose_review_route_back_required" in state["blockers"]
    assert state["route_back"] == {
        "required": True,
        "target": "write",
        "reason": "Rewrite figure-led prose.",
        "source": "medical_prose_review",
    }


def test_present_but_unclosed_ledger_blocks_finalize_and_submission(tmp_path: Path) -> None:
    module = importlib.import_module(MODULE_NAME)
    study_root = tmp_path / "workspace" / "studies" / "001-risk"
    _write_complete_workflow(study_root)
    _write_json(
        study_root / "paper" / "evidence_ledger.json",
        {
            "schema_version": 1,
            "claims": [
                {
                    "claim_id": "C1",
                    "statement": "The primary claim is directly supported.",
                    "status": "supported",
                }
            ],
        },
    )

    state = module.build_ai_reviewer_runtime_workflow_state(study_root)

    assert state["quality_authority"]["state"] == "review_required"
    assert state["finalize_authorization"]["authorized"] is False
    assert state["submission_authorization"]["authorized"] is False
    assert "evidence_ledger_not_closed" in state["blockers"]
    assert state["refs"]["evidence_ledger"]["present"] is True
    assert state["refs"]["evidence_ledger"]["valid"] is False
