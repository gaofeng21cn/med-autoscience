from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_ai_reviewer_publication_eval_workflow import (
    _publication_eval_record,
    _refs,
    _sha256_text,
    _write_ai_reviewer_alignment_inputs,
    _write_json,
    _write_text,
)


def test_request_bound_route_back_uses_record_current_manuscript_digest_over_stale_prose_review(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    old_manuscript_text = "# Old manuscript\n\nStale prose-review manuscript.\n"
    new_manuscript_text = "# Current manuscript\n\nRecord-bound manuscript with updated effect estimates.\n"
    request_digest = "sha256:" + "a" * 64
    old_manuscript_digest = _sha256_text(old_manuscript_text)
    new_manuscript_digest = _sha256_text(new_manuscript_text)
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    record = _publication_eval_record(study_root)
    record["verdict"] = {
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "summary": "Current AI reviewer record routes same-line manuscript repair.",
        "stop_loss_pressure": "watch",
    }
    record["quality_assessment"]["medical_journal_prose_quality"] = {
        "status": "blocked",
        "summary": "Methods and displays require journal-grade hardening.",
        "evidence_refs": [refs["medical_prose_review"], refs["manuscript"]],
        "reviewer_reason": "Current manuscript needs reproducibility and display repair.",
    }
    record["reviewer_operating_system"] = {
        "currentness_checks": {
            "medical_prose_review": {
                "status": "stale_for_live_manuscript",
                "used_as_context_not_clearance": True,
            },
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": new_manuscript_digest,
                "reviewed_at": "2026-05-25T00:58:29+00:00",
            },
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": new_manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": "sha256:record-evidence-placeholder",
            "claim_evidence_alignment_digest": "sha256:record-claim-alignment-placeholder",
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{record['eval_id']}",
            "fail_closed_when_missing": True,
            "missing_required_fields": [
                "methods_reconstructability_hardening",
                "display_source_reconciliation",
                "current_package_freshness",
                "owner_authorized_gate_replay",
            ],
        },
    }
    record["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::route-back-write::current-record",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route the current record back to write for same-line repair.",
            "route_target": "write",
            "route_key_question": "Can the current manuscript be hardened against the current reviewer record?",
            "route_rationale": "The current AI reviewer record is bound to the live manuscript.",
            "evidence_refs": [refs["manuscript"]],
            "requires_controller_decision": True,
            "work_unit_fingerprint": "current-record-route-back::write",
            "next_work_unit": {
                "unit_id": "current_record_methods_display_repair",
                "lane": "write",
                "summary": "Repair current manuscript methods and displays.",
            },
        }
    ]
    _write_text(Path(refs["manuscript"]), new_manuscript_text)
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": old_manuscript_digest},
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
                "manuscript_digest": old_manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite manuscript prose against the current evidence.",
                },
            },
        },
    )
    _write_ai_reviewer_alignment_inputs(study_root)

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
        record=record,
        workflow_currentness_mode="request_bound_ai_reviewer_record",
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    currentness = latest["reviewer_operating_system"]["currentness_checks"]
    readiness = latest["reviewer_operating_system"]["publication_quality_readiness"]

    assert result["status"] == "materialized"
    assert currentness["medical_prose_review"]["manuscript_digest"] == new_manuscript_digest
    assert currentness["medical_prose_review"]["review_request_manuscript_digest"] == old_manuscript_digest
    assert currentness["current_manuscript"]["manuscript_digest"] == new_manuscript_digest
    assert readiness["status"] == "blocked"
    assert readiness["current_manuscript_digest"] == new_manuscript_digest
    assert readiness["review_request_digest"] == request_digest
    assert readiness["evidence_ledger_digest"].startswith("sha256:")
    assert readiness["claim_evidence_alignment_digest"].startswith("sha256:")
    assert readiness["missing_required_fields"] == [
        "methods_reconstructability_hardening",
        "display_source_reconciliation",
        "current_package_freshness",
        "owner_authorized_gate_replay",
    ]


def test_request_bound_route_back_uses_current_request_digest_when_durable_prose_review_is_stale(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    manuscript_text = "# Current manuscript\n\nRecord-bound manuscript with updated request digest.\n"
    old_request_digest = "sha256:" + "a" * 64
    current_request_digest = "sha256:" + "b" * 64
    old_manuscript_digest = _sha256_text("# Old manuscript\n\nStale prose review input.\n")
    current_manuscript_digest = _sha256_text(manuscript_text)
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    record = _publication_eval_record(study_root)
    record["verdict"] = {
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "summary": "Current AI reviewer record routes same-line manuscript repair.",
        "stop_loss_pressure": "watch",
    }
    record["quality_assessment"]["medical_journal_prose_quality"] = {
        "status": "blocked",
        "summary": "Current manuscript still needs journal-grade hardening.",
        "evidence_refs": [refs["manuscript"], refs["medical_prose_review"]],
        "reviewer_reason": "The AI reviewer record is bound to the current manuscript snapshot.",
    }
    record["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::route-back-write::current-record",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route the current record back to write for same-line repair.",
            "route_target": "write",
            "route_key_question": "Can write repair close the current reviewer record?",
            "route_rationale": "The current record is bound to the live manuscript.",
            "evidence_refs": [refs["manuscript"]],
            "requires_controller_decision": True,
        }
    ]
    record["reviewer_operating_system"] = {
        "currentness_checks": {
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": current_manuscript_digest,
                "reviewed_at": "2026-05-28T04:21:12+00:00",
            },
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": current_manuscript_digest,
            "review_request_digest": current_request_digest,
            "evidence_ledger_digest": "sha256:" + "0" * 64,
            "claim_evidence_alignment_digest": "sha256:" + "1" * 64,
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{record['eval_id']}",
            "fail_closed_when_missing": True,
            "missing_required_fields": ["current_package_freshness"],
        },
    }
    _write_text(Path(refs["manuscript"]), manuscript_text)
    _write_json(
        request_path,
        {
            "surface": "medical_prose_review_request",
            "request_digest": current_request_digest,
            "manuscript": {"path": refs["manuscript"], "digest": current_manuscript_digest},
        },
    )
    _write_json(
        review_path,
        {
            "surface": "medical_prose_review",
            "assessment_provenance": {
                "owner": "ai_reviewer",
                "request_ref": str(request_path),
                "request_digest": old_request_digest,
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": old_manuscript_digest,
            },
            "medical_journal_prose_quality": {
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite manuscript prose against the current evidence.",
                },
            },
        },
    )
    _write_ai_reviewer_alignment_inputs(study_root)

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
        record=record,
        workflow_currentness_mode="request_bound_ai_reviewer_record",
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    medical_prose = latest["reviewer_operating_system"]["currentness_checks"]["medical_prose_review"]

    assert result["status"] == "materialized"
    assert medical_prose["request_digest"] == current_request_digest
    assert medical_prose["review_request_digest"] == old_request_digest
    assert medical_prose["durable_medical_prose_review_status"] == "stale_for_current_request"
    assert medical_prose["manuscript_digest"] == current_manuscript_digest


def test_request_bound_route_back_recomputes_live_evidence_ledger_digest_after_repair(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    manuscript_text = "# Current manuscript\n\nRecord-bound manuscript with repaired evidence ledger.\n"
    request_digest = "sha256:" + "a" * 64
    manuscript_digest = _sha256_text(manuscript_text)
    request_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review_request.json"
    review_path = study_root / "artifacts" / "publication_eval" / "medical_prose_review.json"
    record = _publication_eval_record(study_root)
    record["verdict"] = {
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "summary": "Current AI reviewer record routes same-line manuscript repair.",
        "stop_loss_pressure": "watch",
    }
    record["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::route-back-write::current-record",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Route the current record back to write for same-line repair.",
            "route_target": "write",
            "route_key_question": "Can the current manuscript be hardened against current evidence?",
            "route_rationale": "The current AI reviewer record is bound to the live evidence ledger.",
            "evidence_refs": [refs["manuscript"], refs["evidence_ledger"]],
            "requires_controller_decision": True,
            "work_unit_fingerprint": "current-record-route-back::write",
            "next_work_unit": {
                "unit_id": "current_record_methods_display_repair",
                "lane": "write",
                "summary": "Repair current manuscript methods and displays.",
            },
        }
    ]
    record["reviewer_operating_system"] = {
        "currentness_checks": {
            "current_manuscript": {
                "status": "current",
                "manuscript_ref": refs["manuscript"],
                "manuscript_digest": manuscript_digest,
                "reviewed_at": "2026-05-25T00:58:29+00:00",
            },
        },
        "publication_quality_readiness": {
            "surface_kind": "publication_quality_authority_kernel_v1",
            "status": "blocked",
            "current_manuscript_digest": manuscript_digest,
            "review_request_digest": request_digest,
            "evidence_ledger_digest": "sha256:" + "0" * 64,
            "claim_evidence_alignment_digest": "sha256:" + "1" * 64,
            "rubric_version": "medical_publication_critique_v1",
            "owner_attempt_id": f"ai-reviewer-publication-eval::{record['eval_id']}",
            "fail_closed_when_missing": True,
            "missing_required_fields": ["claim_evidence_alignment_digest", "display_source_reconciliation"],
        },
    }
    _write_text(Path(refs["manuscript"]), manuscript_text)
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
                "status": "partial",
                "overall_style_verdict": "revise",
                "route_back_recommendation": {
                    "required": True,
                    "route_target": "write",
                    "reason": "Rewrite manuscript prose against the current evidence.",
                },
            },
        },
    )
    _write_ai_reviewer_alignment_inputs(study_root)

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
        record=record,
        workflow_currentness_mode="request_bound_ai_reviewer_record",
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    readiness = latest["reviewer_operating_system"]["publication_quality_readiness"]

    assert result["status"] == "materialized"
    assert readiness["status"] == "blocked"
    assert readiness["evidence_ledger_digest"] == _sha256_text(Path(refs["evidence_ledger"]).read_text(encoding="utf-8"))
    assert readiness["evidence_ledger_digest"] != "sha256:" + "0" * 64
    assert readiness["claim_evidence_alignment_digest"] != "sha256:" + "1" * 64
    assert readiness["missing_required_fields"] == ["display_source_reconciliation"]
