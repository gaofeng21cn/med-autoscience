from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.claim_evidence_alignment import build_claim_evidence_alignment_gate


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := _text(item))]


def build_clean_migration_request_record(
    *,
    study_root: Path,
    request: Mapping[str, Any],
    refs: Mapping[str, str | None],
) -> dict[str, Any]:
    study_id = _text(request.get("study_id")) or study_root.name
    quest_id = _text(request.get("quest_id")) or study_id
    emitted_at = _text(request.get("generated_at")) or "2026-05-17T00:00:00+00:00"
    manuscript_ref = refs.get("manuscript") or str(study_root / "paper" / "manuscript.md")
    evidence_ref = refs.get("evidence_ledger") or str(study_root / "paper" / "evidence_ledger.json")
    review_ref = refs.get("review_ledger") or str(study_root / "paper" / "review" / "review_ledger.json")
    charter_ref = refs.get("study_charter") or str(study_root / "artifacts" / "controller" / "study_charter.json")
    eval_id = f"publication-eval::{study_id}::{quest_id}::{emitted_at}"
    quality_assessment = _quality_assessment(
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
        charter_ref=charter_ref,
    )
    future_plan = [
        {
            "limitation": "This clean-migration assessment only re-establishes authority; it does not repair manuscript scientific gaps by itself.",
            "impact_on_claim": "Publication claims remain provisional until publication gate and delivery owners rerun on the new eval.",
            "required_future_analysis_data_or_design": "Rerun publication gate, delivery sync, and any study-specific analysis owner routes required by the new AI reviewer result.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]
    return {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": emitted_at,
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": charter_ref,
            "charter_id": f"charter::{study_id}::paper-authority-clean-migration",
            "publication_objective": "Re-establish publication authority after clean paper-authority migration.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json"),
            "main_result_ref": evidence_ref,
        },
        "delivery_context_refs": {
            "paper_root_ref": str(study_root / "paper"),
            "submission_minimal_ref": str(study_root / "paper" / "submission_minimal" / "submission_manifest.json"),
        },
        "assessment_provenance": {
            "owner": "ai_reviewer",
            "source_kind": "publication_eval_ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "source_refs": [manuscript_ref, evidence_ref, review_ref, charter_ref],
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "Clean migration requires a fresh AI reviewer pass before quality closure or delivery.",
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": quality_assessment,
        "gaps": [
            {
                "gap_id": "paper-authority-clean-migration",
                "gap_type": "delivery",
                "severity": "must_fix",
                "summary": "Legacy publication and delivery authority surfaces were archived; new MAS owners must rebuild them.",
                "evidence_refs": [
                    str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json")
                ],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "paper-authority-clean-migration-rebuild",
                "action_type": "return_to_controller",
                "priority": "now",
                "reason": "After AI reviewer writeback, rerun publication gate and delivery sync.",
                "evidence_refs": [
                    str(study_root / "artifacts" / "migration" / "paper_authority_cutover" / "latest.json")
                ],
                "requires_controller_decision": True,
            }
        ],
        "future_facing_limitations_plan": future_plan,
        "reviewer_operating_system": _reviewer_operating_system(
            eval_id=eval_id,
            study_root=study_root,
            manuscript_ref=manuscript_ref,
            evidence_ref=evidence_ref,
            review_ref=review_ref,
            charter_ref=charter_ref,
            quality_assessment=quality_assessment,
            future_facing_limitations_plan=future_plan,
        ),
    }


def _quality_assessment(
    *,
    manuscript_ref: str,
    evidence_ref: str,
    review_ref: str,
    charter_ref: str,
) -> dict[str, Any]:
    return {
        "clinical_significance": {
            "status": "underdefined",
            "summary": "Clinical significance requires fresh review under the new paper-authority surface.",
            "evidence_refs": [charter_ref, manuscript_ref],
        },
        "evidence_strength": {
            "status": "underdefined",
            "summary": "Evidence strength requires fresh review under the new paper-authority surface.",
            "evidence_refs": [evidence_ref],
        },
        "novelty_positioning": {
            "status": "underdefined",
            "summary": "Novelty positioning requires fresh review under the new paper-authority surface.",
            "evidence_refs": [charter_ref],
        },
        "medical_journal_prose_quality": {
            "status": "underdefined",
            "summary": "Medical journal prose must be reviewed by the AI reviewer before quality closure.",
            "evidence_refs": [manuscript_ref, review_ref],
            "reviewer_reason": "Legacy prose and package authority were archived by clean migration.",
            "reviewer_revision_advice": "Use the current manuscript, evidence ledger, review ledger, and prose review inputs to produce a new AI-reviewer-backed quality judgment.",
            "reviewer_next_round_focus": "Methods completeness, results numeric sufficiency, tables/figures, clinical context, and restrained journal prose.",
        },
        "human_review_readiness": {
            "status": "blocked",
            "summary": "Human review readiness cannot be claimed until new MAS delivery is rebuilt.",
            "evidence_refs": [review_ref],
        },
    }


def _reviewer_operating_system(
    *,
    eval_id: str,
    study_root: Path,
    manuscript_ref: str,
    evidence_ref: str,
    review_ref: str,
    charter_ref: str,
    quality_assessment: Mapping[str, Any],
    future_facing_limitations_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    claim_evidence_ref = str(study_root / "paper" / "claim_evidence_map.json")
    request_digest = "sha256:" + _sha256_text(
        "|".join(["paper_authority_clean_migration", manuscript_ref, evidence_ref, review_ref, charter_ref])
    )
    manuscript_digest = _sha256_ref(manuscript_ref)
    evidence_digest = _sha256_ref(evidence_ref)
    claim_alignment = _claim_alignment(
        study_root=study_root,
        claim_evidence_ref=claim_evidence_ref,
        evidence_ref=evidence_ref,
    )
    readiness_missing = ["claim_evidence_alignment_digest"] if _text(claim_alignment.get("status")) != "ready" else []
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {
            "manuscript": manuscript_ref,
            "study_charter": charter_ref,
            "evidence_ledger": evidence_ref,
            "review_ledger": review_ref,
            "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "claim_evidence_map": claim_evidence_ref,
            "medical_prose_review": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"),
            "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "rubric_scores": {
            dimension: {
                "status": _text(_mapping(payload).get("status")) or "underdefined",
                "rationale": _text(_mapping(payload).get("reviewer_reason"))
                or _text(_mapping(payload).get("summary"))
                or "Clean migration requires fresh AI reviewer authority before publication closure.",
                "evidence_refs": _mapping(payload).get("evidence_refs") or [manuscript_ref, evidence_ref],
            }
            for dimension, payload in quality_assessment.items()
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": _text(_mapping(payload).get("status")) or "underdefined",
                "rationale": _text(_mapping(payload).get("reviewer_reason"))
                or _text(_mapping(payload).get("summary"))
                or "Clean migration requires fresh AI reviewer authority before publication closure.",
            }
            for dimension, payload in quality_assessment.items()
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "requested",
                "request_ref": str(study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"),
                "request_digest": request_digest,
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
                "route_back_required": True,
                "route_target": "review",
                "authority_source_signature": "paper_authority_clean_migration",
            },
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
            },
            "source_eval": {
                "status": "current",
                "eval_id": eval_id,
            },
            "current_package_freshness": {"status": "fresh", "source_eval_id": eval_id},
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked" if readiness_missing else "ready",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": evidence_digest,
            "claim_evidence_alignment_digest": _digest_mapping(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{eval_id}",
            "fail_closed_when_missing": True,
            "missing_required_fields": readiness_missing,
        },
        "future_facing_limitations_plan": future_facing_limitations_plan,
        "provenance_checks": {
            "assessment_owner": "ai_reviewer",
            "policy_id": "medical_publication_critique_v1",
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "route_back_decision": {
            "recommended_action": "route_back_same_line",
            "route_target": "review",
            "rationale": "After AI reviewer writeback, rerun publication gate and delivery sync.",
        },
    }


def _claim_alignment(*, study_root: Path, claim_evidence_ref: str, evidence_ref: str) -> dict[str, Any]:
    try:
        gate = build_claim_evidence_alignment_gate(
            study_root=study_root,
            claim_evidence_map_ref=claim_evidence_ref,
            evidence_ledger_ref=evidence_ref,
        )
        if isinstance(gate.get("claim_count"), int) and gate.get("claim_count") > 0:
            return gate
        return _blocked_claim_alignment_gate(
            claim_evidence_ref=claim_evidence_ref,
            evidence_ref=evidence_ref,
            blockers=[*_string_items(gate.get("blockers")), "claim_evidence_alignment_recheck_required"],
            missing_required_fields=_string_items(gate.get("missing_required_fields")) or ["claim_evidence_alignment"],
        )
    except (OSError, TypeError, ValueError, RuntimeError) as exc:
        return _blocked_claim_alignment_gate(
            claim_evidence_ref=claim_evidence_ref,
            evidence_ref=evidence_ref,
            blockers=[str(exc)],
            missing_required_fields=["claim_evidence_alignment"],
        )


def _blocked_claim_alignment_gate(
    *,
    claim_evidence_ref: str,
    evidence_ref: str,
    blockers: list[str],
    missing_required_fields: list[str],
) -> dict[str, Any]:
    return {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": "blocked",
        "input_refs": {"claim_evidence_map": claim_evidence_ref, "evidence_ledger": evidence_ref},
        "claim_count": 1,
        "aligned_claim_count": 0,
        "claims": [
            {
                "claim_id": "clean_migration_claim_evidence_recheck",
                "status": "blocked",
                "evidence_item_refs": [],
                "support_levels": [],
                "defect_stage": "claim_evidence_alignment_gate",
            }
        ],
        "fail_closed_when_missing": True,
        "missing_required_fields": missing_required_fields,
        "blockers": blockers,
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }


def _sha256_ref(ref: str) -> str:
    path = Path(ref).expanduser()
    try:
        data = path.read_bytes()
    except OSError:
        data = str(ref).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


__all__ = ["build_clean_migration_request_record"]
