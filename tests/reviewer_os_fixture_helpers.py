from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def ready_claim_evidence_alignment_gate(
    *,
    claim_evidence_map_ref: str = "paper/claim_evidence_map.json",
    evidence_ledger_ref: str = "paper/evidence_ledger.json",
) -> dict[str, Any]:
    return {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": "ready",
        "input_refs": {
            "claim_evidence_map": claim_evidence_map_ref,
            "evidence_ledger": evidence_ledger_ref,
        },
        "claim_count": 1,
        "aligned_claim_count": 1,
        "claims": [
            {
                "claim_id": "claim-primary",
                "status": "aligned",
                "evidence_item_refs": ["evidence-primary"],
                "support_levels": ["direct"],
            }
        ],
        "fail_closed_when_missing": True,
        "missing_required_fields": [],
        "blockers": [],
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }


def claim_evidence_alignment_digest(gate: dict[str, Any]) -> str:
    encoded = json.dumps(gate, ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def current_manuscript_routeback_reviewer_os(
    *,
    study_root: Path,
    manuscript_path: Path,
    manuscript_text: str,
    eval_id: str,
) -> dict[str, Any]:
    manuscript_ref = str(manuscript_path.resolve())
    manuscript_digest = "sha256:" + hashlib.sha256(manuscript_text.encode("utf-8")).hexdigest()
    evidence_ref = str(study_root / "paper" / "evidence_ledger.json")
    review_ref = str(study_root / "paper" / "review" / "review_ledger.json")
    claim_evidence_ref = str(study_root / "paper" / "claim_evidence_map.json")
    dimensions = (
        "clinical_significance",
        "evidence_strength",
        "novelty_positioning",
        "medical_journal_prose_quality",
        "human_review_readiness",
    )
    claim_alignment = ready_claim_evidence_alignment_gate(
        claim_evidence_map_ref=claim_evidence_ref,
        evidence_ledger_ref=evidence_ref,
    )
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {
            "manuscript": manuscript_ref,
            "study_charter": str(study_root / "artifacts" / "controller" / "study_charter.json"),
            "evidence_ledger": evidence_ref,
            "review_ledger": review_ref,
            "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "claim_evidence_map": claim_evidence_ref,
            "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "rubric_scores": {
            dimension: {
                "status": "blocked" if dimension == "medical_journal_prose_quality" else "ready",
                "rationale": f"{dimension} was reviewed against the current manuscript.",
                "evidence_refs": [manuscript_ref, evidence_ref],
            }
            for dimension in dimensions
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": "blocked" if dimension == "medical_journal_prose_quality" else "ready",
                "rationale": f"{dimension} was reviewed against the current manuscript.",
            }
            for dimension in dimensions
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": "sha256:" + "a" * 64,
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
                "route_back_required": True,
                "route_target": "write",
            },
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
                "reviewed_at": "2026-05-24T17:58:27+00:00",
            },
            "current_package_freshness": {
                "status": "downstream_pending",
                "source_eval_id": eval_id,
            },
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "ready",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": "sha256:" + "a" * 64,
            "evidence_ledger_digest": "sha256:" + "d" * 64,
            "claim_evidence_alignment_digest": claim_evidence_alignment_digest(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{eval_id}",
            "fail_closed_when_missing": True,
            "missing_required_fields": [],
        },
        "future_facing_limitations_plan": [
            {
                "limitation": "AI reviewer authorization is scoped to the current manuscript snapshot.",
                "impact_on_claim": "Claims must remain tied to the reviewed manuscript and evidence refs.",
                "required_future_analysis_data_or_design": "Repeat AI reviewer evaluation after substantive manuscript changes.",
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
            "recommended_action": "route_back_same_line",
            "rationale": "Current manuscript review still routes publication hardening to write.",
        },
    }


def claim_evidence_map_payload(*, evidence_ledger_ref: str) -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary manuscript claim is supported by the current analysis.",
                "status": "supported",
                "paper_role": "primary_result",
                "display_bindings": ["table-1"],
                "sections": ["Results"],
                "evidence_items": [
                    {
                        "item_id": "evidence-primary",
                        "support_level": "direct",
                        "source_paths": [evidence_ledger_ref],
                    }
                ],
            }
        ]
    }


def evidence_ledger_payload(*, evidence_ledger_ref: str, evidence_id: str = "evidence-primary") -> dict[str, Any]:
    return {
        "claims": [
            {
                "claim_id": "claim-primary",
                "statement": "Primary manuscript claim is supported by the current analysis.",
                "status": "supported",
                "submission_scope": "manuscript",
                "evidence": [
                    {
                        "evidence_id": evidence_id,
                        "kind": "analysis_result",
                        "source_paths": [evidence_ledger_ref],
                        "support_level": "direct",
                        "summary": "Current analysis supports the primary claim.",
                    }
                ],
                "gaps": [
                    {
                        "gap_id": "gap-none",
                        "description": "No blocking claim-evidence gap remains.",
                        "submission_impact": "none",
                    }
                ],
                "recommended_actions": [
                    {
                        "action_id": "action-none",
                        "priority": "none",
                        "description": "No claim-evidence repair required.",
                    }
                ],
            }
        ]
    }


def review_ledger_payload(*, revision_log_path: str | Path) -> dict[str, Any]:
    return {
        "schema_version": 1,
        "concerns": [
            {
                "concern_id": "concern-closed",
                "reviewer_id": "ai-reviewer",
                "summary": "Claim-evidence alignment reviewed.",
                "severity": "minor",
                "status": "resolved",
                "owner_action": "Keep claims tied to current evidence refs.",
                "revision_links": [
                    {
                        "revision_id": "revision-claim-alignment",
                        "revision_log_path": str(revision_log_path),
                    }
                ],
            }
        ],
    }
