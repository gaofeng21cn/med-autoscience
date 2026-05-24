from __future__ import annotations

import importlib
import json
from pathlib import Path

from tests.test_ai_reviewer_publication_eval_workflow import (
    _publication_eval_record,
    _refs,
    _write_ai_reviewer_alignment_inputs,
    _write_ai_reviewer_currentness_inputs,
)


def test_ai_reviewer_publication_eval_workflow_materializes_route_back_when_claim_alignment_blocks(
    tmp_path: Path,
) -> None:
    module = importlib.import_module("med_autoscience.controllers.ai_reviewer_publication_eval_workflow")
    study_root = tmp_path / "study"
    refs = _refs(study_root)
    record = _publication_eval_record(study_root)
    record["verdict"] = {
        "overall_verdict": "blocked",
        "primary_claim_status": "partial",
        "summary": "Claim-evidence alignment blocks publication readiness.",
        "stop_loss_pressure": "watch",
    }
    record["quality_assessment"]["evidence_strength"] = {
        "status": "blocked",
        "summary": "The primary claim map no longer aligns with the evidence ledger.",
        "evidence_refs": [refs["claim_evidence_map"], refs["evidence_ledger"]],
        "reviewer_reason": "Claim evidence identifiers must be repaired before publication gate readiness.",
    }
    record["gaps"] = [
        {
            "gap_id": "claim-evidence-alignment-blocked",
            "gap_type": "evidence",
            "severity": "must_fix",
            "summary": "The claim-evidence map references an evidence identifier absent from the evidence ledger.",
            "evidence_refs": [refs["claim_evidence_map"], refs["evidence_ledger"]],
        }
    ]
    record["recommended_actions"] = [
        {
            "action_id": "publication-eval-action::route-back-analysis::claim-evidence",
            "action_type": "route_back_same_line",
            "priority": "now",
            "reason": "Repair claim-evidence alignment before publication readiness can be reconsidered.",
            "route_target": "analysis-campaign",
            "route_key_question": "Which current analysis evidence record should support each manuscript claim?",
            "route_rationale": "The AI reviewer OS trace is complete but carries a blocked claim-evidence gate.",
            "evidence_refs": [refs["claim_evidence_map"], refs["evidence_ledger"]],
            "requires_controller_decision": True,
            "work_unit_fingerprint": "claim-evidence-route-back::analysis-campaign",
            "next_work_unit": {
                "unit_id": "claim_evidence_alignment_repair",
                "lane": "analysis-campaign",
                "summary": "Repair claim-evidence identifiers and replay AI reviewer publication eval.",
            },
        }
    ]
    _write_ai_reviewer_currentness_inputs(study_root)
    _write_ai_reviewer_alignment_inputs(study_root, evidence_id="evidence-renamed")

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
    )

    latest = json.loads((study_root / "artifacts" / "publication_eval" / "latest.json").read_text(encoding="utf-8"))
    alignment_gate = latest["reviewer_operating_system"]["claim_evidence_alignment"]
    quality_readiness = latest["reviewer_operating_system"]["publication_quality_readiness"]

    assert result["status"] == "materialized"
    assert latest["assessment_provenance"]["owner"] == "ai_reviewer"
    assert latest["verdict"]["overall_verdict"] == "blocked"
    assert latest["recommended_actions"][0]["action_type"] == "route_back_same_line"
    assert latest["recommended_actions"][0]["route_target"] == "analysis-campaign"
    assert alignment_gate["status"] == "blocked"
    assert alignment_gate["claim_count"] == 1
    assert alignment_gate["aligned_claim_count"] == 0
    assert alignment_gate["missing_required_fields"] == []
    assert alignment_gate["blockers"] == ["claim-primary.evidence-primary_missing_from_evidence_ledger"]
    assert quality_readiness["status"] == "blocked"
    assert quality_readiness["claim_evidence_alignment_digest"].startswith("sha256:")
    assert quality_readiness["missing_required_fields"] == ["claim_evidence_alignment_digest"]
    assert latest["reviewer_operating_system"]["route_back_decision"] == {
        "recommended_action": "route_back_same_line",
        "rationale": "Repair claim-evidence alignment before publication readiness can be reconsidered.",
    }
