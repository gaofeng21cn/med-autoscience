from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

from tests.reviewer_os_fixture_helpers import claim_evidence_map_payload, evidence_ledger_payload, review_ledger_payload


def _sha256_text(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def _relative_refs() -> dict[str, str]:
    return {
        "manuscript": "paper/manuscript.md",
        "study_charter": "artifacts/controller/study_charter.json",
        "evidence_ledger": "paper/evidence_ledger.json",
        "review_ledger": "paper/review/review_ledger.json",
        "medical_manuscript_blueprint": "paper/medical_manuscript_blueprint.json",
        "claim_evidence_map": "paper/claim_evidence_map.json",
        "medical_prose_review": "artifacts/publication_eval/medical_prose_review.json",
        "publication_gate_projection": "artifacts/publication_gate/latest.json",
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


def _reviewer_operating_system(study_root: Path) -> dict[str, Any]:
    refs = _refs(study_root)
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
                "rationale": f"{dimension} is closed.",
                "evidence_refs": [refs["manuscript"]],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "ready",
                "rationale": f"{dimension} is closed.",
            }
            for dimension in dimensions
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": "sha256:" + "c" * 64,
            },
            "current_package_freshness": {
                "status": "fresh",
                "source_eval_id": "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
            },
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "Medication coverage is based on recorded medication fields.",
                "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
                "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
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
            "recommended_action": "continue_same_line",
            "rationale": "Proceed to first full draft.",
        },
        "sci_clinical_registry_review": _sci_clinical_registry_review(study_root),
    }


def _sci_clinical_registry_review(study_root: Path) -> list[dict[str, Any]]:
    refs = _refs(study_root)
    return [
        {
            "concern_id": f"sci-registry-{domain}",
            "domain": domain,
            "status": "clear",
            "severity": "note",
            "finding": f"{domain} was checked against high-quality medical SCI expectations.",
            "evidence_refs": [refs["manuscript"], refs["evidence_ledger"]],
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
        "future_facing_limitations_plan": [
            {
                "limitation": "Medication coverage is based on recorded medication fields.",
                "impact_on_claim": "Treatment-gap language must remain documentation-aware.",
                "required_future_analysis_data_or_design": "Link pharmacy or insurance dispensing data.",
                "current_manuscript_wording_must_be_restrained": True,
            }
        ],
        "sci_clinical_registry_review": _sci_clinical_registry_review(study_root),
    }


def _canonical_publication_eval_record(study_root: Path) -> dict[str, Any]:
    record = _publication_eval_record(study_root)
    record.pop("sci_clinical_registry_review", None)
    return record


def _write_ai_reviewer_currentness_inputs(
    study_root: Path,
    *,
    source_eval_id: str | None = None,
    prose_status: str = "ready",
    style_verdict: str = "clear",
    route_back_required: bool = False,
) -> None:
    refs = _refs(study_root)
    request_digest = "sha256:" + "a" * 64
    manuscript_text = "# Current manuscript\n\nEvidence-bound clinical manuscript body.\n"
    _write_text(Path(refs["manuscript"]), manuscript_text)
    manuscript_digest = _sha256_text(manuscript_text)
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": manuscript_digest},
        },
    )
    _write_json(
        review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": prose_status,
                "overall_style_verdict": style_verdict,
                "route_back_recommendation": {
                    "required": route_back_required,
                    "route_target": "write" if route_back_required else "none",
                    "reason": "Rewrite manuscript prose against the current evidence." if route_back_required else "",
                },
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": source_eval_id
            or "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
            "current_package_root": str(study_root / "manuscript" / "current_package"),
            "current_package_zip": str(study_root / "manuscript" / "current_package.zip"),
        },
    )
    _write_ai_reviewer_alignment_inputs(study_root)


def _write_ai_reviewer_alignment_inputs(study_root: Path, *, evidence_id: str = "evidence-primary") -> None:
    refs = _refs(study_root)
    _write_json(Path(refs["claim_evidence_map"]), claim_evidence_map_payload(evidence_ledger_ref=refs["evidence_ledger"]))
    _write_json(
        Path(refs["evidence_ledger"]),
        evidence_ledger_payload(evidence_ledger_ref=refs["evidence_ledger"], evidence_id=evidence_id),
    )
    _write_json(Path(refs["review_ledger"]), review_ledger_payload(revision_log_path=study_root / "paper" / "revision_log.json"))
    _write_json(
        Path(refs["study_charter"]),
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "Submit a clinically restrained manuscript.",
        },
    )
    _write_json(
        Path(refs["publication_gate_projection"]),
        {
            "surface": "publication_gate_projection",
            "status": "ready",
        },
    )


def _write_relative_ai_reviewer_currentness_inputs(
    study_root: Path,
    *,
    source_eval_id: str | None = None,
) -> None:
    refs = _relative_refs()
    request_digest = "sha256:" + "a" * 64
    manuscript_text = "# Current manuscript\n\nEvidence-bound clinical manuscript body.\n"
    _write_text(study_root / refs["manuscript"], manuscript_text)
    manuscript_digest = _sha256_text(manuscript_text)
    request_ref = "artifacts/publication_eval/medical_prose_review_request.json"
    _write_json(
        study_root / request_ref,
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": manuscript_digest},
        },
    )
    _write_json(
        study_root / refs["medical_prose_review"],
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": request_ref,
                "request_digest": request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": "ready",
                "overall_style_verdict": "clear",
                "route_back_recommendation": {"required": False, "route_target": "none"},
            },
        },
    )
    _write_json(
        study_root / "artifacts" / "controller" / "current_package_freshness" / "latest.json",
        {
            "schema_version": 1,
            "status": "fresh",
            "source_eval_id": source_eval_id
            or "publication-eval::001-risk::quest-001::2026-05-04T00:00:00+00:00",
            "current_package_root": "manuscript/current_package",
            "current_package_zip": "manuscript/current_package.zip",
        },
    )
    _write_relative_ai_reviewer_alignment_inputs(study_root)


def _write_relative_ai_reviewer_alignment_inputs(study_root: Path) -> None:
    refs = _relative_refs()
    _write_json(study_root / refs["claim_evidence_map"], claim_evidence_map_payload(evidence_ledger_ref=refs["evidence_ledger"]))
    _write_json(study_root / refs["evidence_ledger"], evidence_ledger_payload(evidence_ledger_ref=refs["evidence_ledger"]))
    _write_json(study_root / refs["review_ledger"], review_ledger_payload(revision_log_path="paper/revision_log.json"))
    _write_json(
        study_root / refs["study_charter"],
        {
            "charter_id": "charter::001-risk::v1",
            "publication_objective": "Submit a clinically restrained manuscript.",
        },
    )
    _write_json(
        study_root / refs["publication_gate_projection"],
        {
            "surface": "publication_gate_projection",
            "status": "ready",
        },
    )

