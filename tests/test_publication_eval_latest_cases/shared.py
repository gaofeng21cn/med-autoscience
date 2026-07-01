from __future__ import annotations

import importlib
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from tests.reviewer_os_fixture_helpers import (
    claim_evidence_alignment_digest,
    claim_evidence_map_payload,
    evidence_ledger_payload,
    ready_claim_evidence_alignment_gate,
)


MODULE_NAME = "med_autoscience.publication_eval_latest"


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _minimal_payload(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "schema_version": 1,
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "emitted_at": "2026-04-05T06:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "risk stratification external validation",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
            "main_result_ref": str(quest_root / "artifacts" / "results" / "main_result.json"),
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [
                str(study_root / "paper"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
            "ai_reviewer_required": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Primary claim still lacks external validation support.",
            "stop_loss_pressure": "watch",
        },
        "gaps": [
            {
                "gap_id": "gap-001",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "External validation cohort is still missing.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "results" / "main_result.json"),
                ],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "action-001",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "Controller must decide whether to invest in external validation.",
                "evidence_refs": [
                    str(quest_root / "artifacts" / "reports" / "escalation" / "runtime_escalation_record.json"),
                ],
                "requires_controller_decision": True,
            }
        ],
        "sci_clinical_registry_review": _sci_clinical_registry_review(study_root),
    }


def _quality_assessment(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    return {
        "clinical_significance": {
            "status": "ready",
            "summary": "Clinical framing is stable.",
            "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
        },
        "evidence_strength": {
            "status": "ready",
            "summary": "Core evidence is traceable.",
            "evidence_refs": [str(quest_root / "artifacts" / "results" / "main_result.json")],
        },
        "novelty_positioning": {
            "status": "partial",
            "summary": "Contribution boundary is defined but still needs tightening.",
            "evidence_refs": [str(study_root / "artifacts" / "controller" / "study_charter.json")],
        },
        "medical_journal_prose_quality": {
            "status": "partial",
            "summary": "AI reviewer found prose that needs a journal-voice revision pass before closure.",
            "evidence_refs": [str(study_root / "paper" / "manuscript.md")],
            "reviewer_reason": "Results flow still follows displays more than clinical findings.",
            "reviewer_revision_advice": "Rewrite representative figure-led sentences as finding-led sentences.",
            "reviewer_next_round_focus": "Results main finding and Discussion principal finding paragraphs.",
        },
        "human_review_readiness": {
            "status": "partial",
            "summary": "Human-facing package is not ready yet.",
            "evidence_refs": [str(study_root / "paper" / "submission_minimal" / "submission_manifest.json")],
        },
    }


def _sci_clinical_registry_review(study_root: Path) -> list[dict[str, object]]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    manuscript_ref = str(study_root / "paper" / "manuscript.md")
    evidence_ref = str(quest_root / "artifacts" / "results" / "main_result.json")
    return [
        {
            "concern_id": f"sci-registry-{domain}",
            "domain": domain,
            "status": "clear",
            "severity": "note",
            "finding": f"{domain} was checked against medical SCI expectations.",
            "evidence_refs": [manuscript_ref, evidence_ref],
            "required_disposition": "accept_as_is",
        }
        for domain in (
            "clinical_contribution",
            "reporting_metadata",
            "population_applicability",
            "variable_ascertainment",
            "source_heterogeneity",
            "display_to_claim",
        )
    ]


def _reviewer_operating_system(study_root: Path) -> dict[str, object]:
    quest_root = study_root.parents[1] / "ops" / "med-deepscientist" / "runtime" / "quests" / "quest-001"
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = "sha256:" + "c" * 64
    source_eval_id = "publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00"
    input_bundle = {
        "manuscript": str(study_root / "paper" / "manuscript.md"),
        "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
        "evidence_ledger": str(study_root / "paper" / "evidence_ledger.json"),
        "review_ledger": str(study_root / "paper" / "review" / "review_ledger.json"),
        "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
        "claim_evidence_map": str(study_root / "paper" / "claim_evidence_map.json"),
        "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
        "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
    }
    rubric_scores = {
        dimension: {
            "status": "partial" if dimension in {"novelty_positioning", "human_review_readiness"} else "ready",
            "rationale": f"{dimension} was judged from manuscript and ledger evidence.",
            "evidence_refs": [
                str(study_root / "paper" / "manuscript.md"),
                str(quest_root / "artifacts" / "results" / "main_result.json"),
            ],
        }
        for dimension in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "medical_journal_prose_quality",
            "human_review_readiness",
        )
    }
    claim_alignment = ready_claim_evidence_alignment_gate(
        claim_evidence_map_ref=input_bundle["claim_evidence_map"],
        evidence_ledger_ref=input_bundle["evidence_ledger"],
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": input_bundle,
        "rubric_scores": rubric_scores,
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": score["status"],
                "rationale": score["rationale"],
            }
            for dimension, score in rubric_scores.items()
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": request_digest,
                "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
                "manuscript_digest": manuscript_digest,
            },
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": str(study_root / "paper" / "manuscript.md"),
                "manuscript_digest": manuscript_digest,
            },
            "source_eval": {
                "status": "current",
                "eval_id": source_eval_id,
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": source_eval_id,
            },
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "ready",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": "sha256:" + "d" * 64,
            "claim_evidence_alignment_digest": claim_evidence_alignment_digest(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": "ai-reviewer-publication-eval::publication-eval::001-risk::quest-001::2026-04-05T06:00:00+00:00",
            "fail_closed_when_missing": True,
            "missing_required_fields": [],
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Current AI reviewer closure depends on the manuscript and ledger snapshot.",
                "impact_on_claim": "Claim strength must remain tied to the reviewed evidence snapshot.",
                "required_future_analysis_data_or_design": "Rerun AI reviewer if the manuscript or evidence ledger changes.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "sci_clinical_registry_review": _sci_clinical_registry_review(study_root),
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "revise_medical_journal_prose",
            "rationale": "The next pass should repair prose and human-review readiness before closure.",
        },
    }


def _write_cutover_receipt(study_root: Path, *, status: str = "awaiting_new_mas_authority") -> Path:
    path = (
        study_root
        / "artifacts"
        / "stage_outputs"
        / "_body_authority"
        / "paper_authority_cutover"
        / "latest.json"
    )
    _write_json(
        path,
        {
            "schema_version": 1,
            "surface_kind": "paper_authority_clean_migration_receipt",
            "status": status,
            "study_id": study_root.name,
            "study_root": str(study_root),
            "authority_boundary": {
                "quality_verdict_written": False,
                "submission_package_regenerated": False,
            },
            "required_next_actions": [
                "return_to_ai_reviewer_workflow",
                "publication_gate",
                "sync_study_delivery",
            ],
        },
    )
    return path

