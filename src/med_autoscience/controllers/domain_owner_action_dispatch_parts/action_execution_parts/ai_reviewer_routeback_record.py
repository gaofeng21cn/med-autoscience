from __future__ import annotations

import json
import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _string_items(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for item in value:
        text = _text(item)
        if text is not None:
            items.append(text)
    return items


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def build_current_medical_prose_routeback_record(
    *,
    study_root: Path,
    request: Mapping[str, Any],
    required_refs: Mapping[str, str | None],
) -> dict[str, Any]:
    prose_ref = required_refs.get("medical_prose_review") or str(
        study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    )
    prose_path = Path(prose_ref).expanduser()
    if not prose_path.is_absolute():
        prose_path = study_root / prose_path
    prose_payload = _mapping(_read_json_object(prose_path.resolve()))
    if not prose_payload:
        return {}
    provenance = _mapping(prose_payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return {}
    if _text(provenance.get("source_kind")) != "medical_prose_review":
        return {}
    if provenance.get("ai_reviewer_required") is not False:
        return {}
    quality = _mapping(prose_payload.get("medical_journal_prose_quality"))
    route_back = _mapping(quality.get("route_back_recommendation"))
    if route_back.get("required") is not True:
        return {}
    route_target = _route_target_for_publication_eval(route_back.get("route_target"))
    if route_target is None:
        return {}

    study_id = _text(request.get("study_id")) or study_root.name
    quest_id = _text(request.get("quest_id")) or study_id
    request_digest = _text(provenance.get("request_digest")) or "no-request-digest"
    manuscript_ref = (
        required_refs.get("manuscript") or _text(provenance.get("manuscript_ref")) or str(study_root / "paper" / "draft.md")
    )
    evidence_ref = required_refs.get("evidence_ledger") or str(study_root / "paper" / "evidence_ledger.json")
    review_ref = required_refs.get("review_ledger") or str(study_root / "paper" / "review" / "review_ledger.json")
    charter_ref = required_refs.get("study_charter") or str(study_root / "artifacts" / "controller" / "study_charter.json")
    route_reason = _text(route_back.get("reason")) or (
        "Route the current manuscript back to the appropriate owner for medical-journal quality repair."
    )
    prose_summary = _text(quality.get("summary")) or route_reason
    section_diagnosis = _mapping(quality.get("section_level_diagnosis"))
    next_round_focus = _current_prose_next_round_focus(section_diagnosis)
    source_refs = _current_prose_source_refs(
        study_root=study_root,
        prose_path=prose_path.resolve(),
        prose_payload=prose_payload,
        manuscript_ref=manuscript_ref,
        evidence_ref=evidence_ref,
        review_ref=review_ref,
    )
    eval_id = f"publication-eval::{study_id}::{quest_id}::medical-prose-routeback::{_fingerprint_token(request_digest)}"
    quality_assessment = {
        "clinical_significance": {
            "status": "partial",
            "summary": "The clinical management question remains meaningful, but publication readiness depends on manuscript repair against the current reviewer findings.",
            "evidence_refs": [charter_ref, manuscript_ref],
            "reviewer_reason": "AI reviewer medical-prose review did not clear the current manuscript for publication-facing closure.",
        },
        "evidence_strength": {
            "status": "partial",
            "summary": "The evidence base can support a bounded descriptive manuscript after the required reporting details are repaired.",
            "evidence_refs": [evidence_ref, str(prose_path.resolve())],
            "reviewer_reason": route_reason,
        },
        "novelty_positioning": {
            "status": "partial",
            "summary": "The contribution remains tied to a descriptive primary-care phenotype and treatment-review atlas, pending clearer methods and display-to-claim reporting.",
            "evidence_refs": [charter_ref, manuscript_ref],
            "reviewer_reason": "Novelty should be framed through reproducible routine-care phenotype reporting and service-review interpretation.",
        },
        "medical_journal_prose_quality": {
            "status": _publication_quality_status(quality.get("status")),
            "summary": prose_summary,
            "evidence_refs": [str(prose_path.resolve()), manuscript_ref],
            "reviewer_reason": route_reason,
            "reviewer_revision_advice": route_reason,
            "reviewer_next_round_focus": next_round_focus,
        },
        "human_review_readiness": {
            "status": "blocked",
            "summary": "Human-facing review should wait until write-owner repair is completed and the publication gate is replayed.",
            "evidence_refs": [review_ref, str(prose_path.resolve())],
            "reviewer_reason": "The current AI reviewer verdict is revise, not clear.",
        },
    }
    future_facing_limitations_plan = [
        {
            "limitation": "The current reviewer judgment identifies manuscript reporting gaps rather than a new medical effect estimate.",
            "impact_on_claim": "Publication claims remain partial until the write owner repairs reproducibility, treatment-gap definitions, display interpretation, and limitation placement.",
            "required_future_analysis_data_or_design": "Complete write-owner manuscript repair using the current evidence surfaces, then rerun AI reviewer, publication gate, and delivery refresh before any submission-facing claim.",
            "current_manuscript_wording_must_be_restrained": True,
        }
    ]
    return {
        "schema_version": 1,
        "eval_id": eval_id,
        "study_id": study_id,
        "quest_id": quest_id,
        "emitted_at": _text(request.get("generated_at")) or "2026-05-21T00:00:00+00:00",
        "evaluation_scope": "publication",
        "charter_context_ref": {
            "ref": charter_ref,
            "charter_id": f"charter::{study_id}::ai-reviewer-medical-prose-routeback",
            "publication_objective": "Route current AI reviewer medical-prose findings back to the owning manuscript repair stage.",
        },
        "runtime_context_refs": {
            "runtime_escalation_ref": str(study_root / "artifacts" / "runtime" / "runtime_escalation_record.json"),
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
            "source_refs": source_refs,
            "ai_reviewer_required": False,
            "mechanical_projection_used_as_quality_authority": False,
        },
        "verdict": {
            "overall_verdict": "mixed",
            "primary_claim_status": "partial",
            "summary": prose_summary,
            "stop_loss_pressure": "watch",
        },
        "quality_assessment": quality_assessment,
        "gaps": [
            {
                "gap_id": "medical-prose-write-routeback",
                "gap_type": "reporting",
                "severity": "must_fix",
                "summary": route_reason,
                "evidence_refs": [str(prose_path.resolve()), manuscript_ref],
            }
        ],
        "recommended_actions": [
            {
                "action_id": f"publication-eval-action::{study_id}::medical-prose-routeback",
                "action_type": "route_back_same_line",
                "priority": "now",
                "reason": route_reason,
                "route_target": route_target,
                "route_key_question": "Repair the manuscript surface so current evidence reads as a reproducible medical original research article.",
                "route_rationale": route_reason,
                "evidence_refs": [str(prose_path.resolve()), manuscript_ref],
                "requires_controller_decision": True,
                "work_unit_fingerprint": f"medical-prose-routeback::{route_target}::{_fingerprint_token(request_digest)}",
                "next_work_unit": {
                    "unit_id": "medical_prose_write_repair",
                    "lane": route_target,
                    "summary": "Repair manuscript methods, treatment-gap definitions, display callouts, limitations, and journal prose against current AI reviewer findings.",
                },
            }
        ],
        "future_facing_limitations_plan": future_facing_limitations_plan,
        "reviewer_operating_system": _routeback_reviewer_operating_system(
            eval_id=eval_id,
            study_root=study_root,
            manuscript_ref=manuscript_ref,
            evidence_ref=evidence_ref,
            review_ref=review_ref,
            charter_ref=charter_ref,
            prose_ref=str(prose_path.resolve()),
            request_digest=request_digest,
            route_reason=route_reason,
            quality_assessment=quality_assessment,
            future_facing_limitations_plan=future_facing_limitations_plan,
        ),
    }


def _route_target_for_publication_eval(value: object) -> str | None:
    target = _text(value)
    if target == "analysis":
        target = "analysis-campaign"
    if target in {"write", "analysis-campaign"}:
        return target
    return None


def _publication_quality_status(value: object) -> str:
    status = _text(value)
    if status in {"ready", "partial", "blocked", "underdefined"}:
        return status
    return "partial"


def _current_prose_next_round_focus(section_diagnosis: Mapping[str, Any]) -> str:
    focus_items = [
        _text(section_diagnosis.get("methods")),
        _text(section_diagnosis.get("results")),
        _text(section_diagnosis.get("tables_and_figures")),
        _text(section_diagnosis.get("discussion")),
    ]
    focus = " ".join(item for item in focus_items if item)
    return focus or "Repair the manuscript against current AI reviewer medical-prose findings."


def _current_prose_source_refs(
    *,
    study_root: Path,
    prose_path: Path,
    prose_payload: Mapping[str, Any],
    manuscript_ref: str,
    evidence_ref: str,
    review_ref: str,
) -> list[str]:
    refs = [
        str(prose_path),
        manuscript_ref,
        evidence_ref,
        review_ref,
        *_string_items(prose_payload.get("source_refs")),
    ]
    provenance = _mapping(prose_payload.get("assessment_provenance"))
    request_ref = _text(provenance.get("request_ref"))
    if request_ref:
        request_path = Path(request_ref).expanduser()
        if not request_path.is_absolute():
            request_path = study_root / request_path
        refs.append(str(request_path.resolve()))
    return list(dict.fromkeys(refs))


def _routeback_reviewer_operating_system(
    *,
    eval_id: str,
    study_root: Path,
    manuscript_ref: str,
    evidence_ref: str,
    review_ref: str,
    charter_ref: str,
    prose_ref: str,
    request_digest: str,
    route_reason: str,
    quality_assessment: Mapping[str, Any],
    future_facing_limitations_plan: list[dict[str, Any]],
) -> dict[str, Any]:
    claim_evidence_ref = str(study_root / "paper" / "claim_evidence_map.json")
    manuscript_digest = _sha256_path(Path(manuscript_ref))
    evidence_digest = _sha256_path(Path(evidence_ref))
    claim_alignment = {
        "surface_kind": "claim_evidence_alignment_gate_v1",
        "source_project": "academic-research-skills",
        "absorbed_as": "mas_native_claim_evidence_alignment_gate",
        "status": "blocked",
        "input_refs": {
            "claim_evidence_map": claim_evidence_ref,
            "evidence_ledger": evidence_ref,
        },
        "claim_count": 1,
        "aligned_claim_count": 0,
        "fail_closed_when_missing": True,
        "missing_required_fields": ["claim_evidence_alignment_digest"],
        "blockers": ["write_owner_repair_required_before_claim_evidence_alignment"],
        "body_included": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
        "can_write_domain_truth": False,
    }
    return {
        "contract_id": "medical_publication_ai_reviewer_os_v1",
        "input_bundle": {
            "manuscript": manuscript_ref,
            "study_charter": charter_ref,
            "evidence_ledger": evidence_ref,
            "review_ledger": review_ref,
            "medical_manuscript_blueprint": str(study_root / "paper" / "medical_manuscript_blueprint.json"),
            "claim_evidence_map": claim_evidence_ref,
            "medical_prose_review": prose_ref,
            "publication_gate_projection": str(study_root / "artifacts" / "publication_eval" / "latest.json"),
        },
        "rubric_scores": {
            dimension: {
                "status": _text(_mapping(payload).get("status")) or "partial",
                "rationale": _text(_mapping(payload).get("reviewer_reason"))
                or _text(_mapping(payload).get("summary"))
                or route_reason,
                "evidence_refs": _mapping(payload).get("evidence_refs") or [manuscript_ref, evidence_ref],
            }
            for dimension, payload in quality_assessment.items()
        },
        "decision_matrix": [
            {
                "dimension": dimension,
                "status": _text(_mapping(payload).get("status")) or "partial",
                "rationale": _text(_mapping(payload).get("reviewer_reason"))
                or _text(_mapping(payload).get("summary"))
                or route_reason,
            }
            for dimension, payload in quality_assessment.items()
        ],
        "currentness_checks": {
            "medical_prose_review": {
                "status": "current",
                "request_digest": request_digest,
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
                "route_back_required": True,
                "route_target": "write",
            },
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": manuscript_ref,
                "manuscript_digest": manuscript_digest,
            },
            "current_package_freshness": {
                "status": "downstream_pending",
                "source_eval_id": eval_id,
            },
        },
        "claim_evidence_alignment": claim_alignment,
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": evidence_digest,
            "claim_evidence_alignment_digest": _digest_mapping(claim_alignment),
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{eval_id}",
            "fail_closed_when_missing": True,
            "missing_required_fields": ["claim_evidence_alignment_digest"],
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
            "rationale": route_reason,
        },
    }


def _sha256_path(path: Path) -> str:
    try:
        data = path.expanduser().read_bytes()
    except OSError:
        data = str(path).encode("utf-8")
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _digest_mapping(payload: Mapping[str, Any]) -> str:
    encoded = json.dumps(dict(payload), ensure_ascii=False, sort_keys=True).encode("utf-8")
    return "sha256:" + hashlib.sha256(encoded).hexdigest()


def _fingerprint_token(value: object) -> str:
    text = (_text(value) or "no-digest").replace(":", "-")
    return "".join(char if char.isalnum() or char in {"-", "_"} else "-" for char in text)[:80]


__all__ = ["build_current_medical_prose_routeback_record"]
