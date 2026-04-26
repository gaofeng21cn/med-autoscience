from __future__ import annotations

import importlib
from typing import Any


def _closed_quality_gate() -> dict[str, Any]:
    guidelines = importlib.import_module("med_autoscience.controllers.medical_reporting_guidelines")
    payload = guidelines.build_guideline_quality_gate_expectation("STROBE")
    for gate in payload["gates"].values():
        gate["status"] = "closed"
    return payload


def _closed_evidence_ledger() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "closed",
        "charter_expectation_closures": [
            {
                "expectation_key": "minimum_sci_ready_evidence_package",
                "expectation_text": "Primary claim evidence package is closed.",
                "status": "closed",
                "closed_at": "2026-04-25T10:00:00+00:00",
            }
        ],
    }


def _closed_review_ledger() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "status": "closed",
        "charter_expectation_closures": [
            {
                "expectation_key": "scientific_followup_questions",
                "expectation_text": "Reviewer-first scientific concerns are closed.",
                "status": "closed",
                "closed_at": "2026-04-25T10:00:00+00:00",
            },
            {
                "expectation_key": "manuscript_conclusion_redlines",
                "expectation_text": "Conclusion boundary redlines are closed.",
                "status": "closed",
                "closed_at": "2026-04-25T10:00:00+00:00",
            },
        ],
    }


def _ready_publication_eval() -> dict[str, Any]:
    return {
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-25T10:00:00+00:00",
        "verdict": {
            "overall_verdict": "promising",
            "primary_claim_status": "supported",
            "summary": "Publication gate is clear.",
        },
        "gaps": [],
        "recommended_actions": [],
    }


def _repairable_publication_eval(*, evidence_ref: str = "paper/review/review_ledger.json") -> dict[str, Any]:
    return {
        "eval_id": "publication-eval::001-risk::quest-001::2026-04-25T10:05:00+00:00",
        "verdict": {
            "overall_verdict": "blocked",
            "primary_claim_status": "partial",
            "summary": "A bounded same-line repair is required.",
        },
        "gaps": [
            {
                "gap_id": "review-ledger-followup-open",
                "gap_type": "evidence",
                "severity": "must_fix",
                "summary": "Review ledger closure remains open.",
                "evidence_refs": [evidence_ref],
            }
        ],
        "recommended_actions": [
            {
                "action_id": "bounded-analysis::review-ledger-followup-open",
                "action_type": "bounded_analysis",
                "priority": "now",
                "reason": "Close the explicitly referenced review-ledger gap.",
                "route_target": "analysis-campaign",
                "route_key_question": "Which ledger closure remains open?",
                "route_rationale": "Close only the referenced ledger gap and replay publication eval.",
                "evidence_refs": [evidence_ref],
                "requires_controller_decision": True,
                "work_unit_fingerprint": "quality-ledger-review-followup-open",
                "blocking_work_units": [
                    {
                        "unit_id": "review_ledger_followup_closure",
                        "lane": "quality_ledger_repair",
                        "summary": "Close the review-ledger follow-up item.",
                    }
                ],
                "next_work_unit": {
                    "unit_id": "review_ledger_followup_closure",
                    "lane": "quality_ledger_repair",
                    "summary": "Close the review-ledger follow-up item.",
                },
            }
        ],
    }


def test_fast_lane_allowed_when_quality_ledgers_eval_and_guideline_gate_are_closed() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_ledger_enforcer")

    result = module.build_quality_gate_ledger_enforcement(
        evidence_ledger_payload=_closed_evidence_ledger(),
        review_ledger_payload=_closed_review_ledger(),
        publication_eval_payload=_ready_publication_eval(),
        reporting_guideline_gate_payload=_closed_quality_gate(),
    )

    assert result["surface"] == "quality_gate_ledger_enforcement"
    assert result["fast_lane_execution_allowed"] is True
    assert result["fast_lane_execution_state"] == "ready"
    assert result["gate_relaxation_allowed"] is False
    assert result["hard_blockers"] == []
    assert result["repairable_blockers"] == []


def test_fast_lane_blocks_open_review_ledger_without_explicit_repair_action() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_ledger_enforcer")
    review_ledger = _closed_review_ledger()
    review_ledger["charter_expectation_closures"][0]["status"] = "open"

    result = module.build_quality_gate_ledger_enforcement(
        evidence_ledger_payload=_closed_evidence_ledger(),
        review_ledger_payload=review_ledger,
        publication_eval_payload=_ready_publication_eval(),
        reporting_guideline_gate_payload=_closed_quality_gate(),
    )

    assert result["fast_lane_execution_allowed"] is False
    assert result["fast_lane_execution_state"] == "blocked"
    assert "review_ledger_charter_expectation_not_closed" in result["hard_blockers"]
    assert result["repairable_blockers"] == []


def test_fast_lane_allows_explicit_repair_for_referenced_ledger_gap() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_ledger_enforcer")
    review_ledger = _closed_review_ledger()
    review_ledger["charter_expectation_closures"][0]["status"] = "blocked"

    result = module.build_quality_gate_ledger_enforcement(
        evidence_ledger_payload=_closed_evidence_ledger(),
        review_ledger_payload=review_ledger,
        publication_eval_payload=_repairable_publication_eval(),
        reporting_guideline_gate_payload=_closed_quality_gate(),
    )

    assert result["fast_lane_execution_allowed"] is True
    assert result["fast_lane_execution_state"] == "repairable"
    assert result["hard_blockers"] == []
    assert "review_ledger_charter_expectation_not_closed" in result["repairable_blockers"]
    assert "publication_eval_must_fix_gap" in result["repairable_blockers"]


def test_fast_lane_blocks_reporting_guideline_gate_relaxation_request() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_ledger_enforcer")
    quality_gate = _closed_quality_gate()
    quality_gate["gate_relaxation_allowed"] = True

    result = module.build_quality_gate_ledger_enforcement(
        evidence_ledger_payload=_closed_evidence_ledger(),
        review_ledger_payload=_closed_review_ledger(),
        publication_eval_payload=_ready_publication_eval(),
        reporting_guideline_gate_payload=quality_gate,
    )

    assert result["gate_relaxation_allowed"] is False
    assert result["fast_lane_execution_allowed"] is False
    assert "reporting_guideline_gate_relaxation_requested" in result["hard_blockers"]


def test_fast_lane_blocks_open_reporting_guideline_gate_without_explicit_repair() -> None:
    module = importlib.import_module("med_autoscience.controllers.quality_ledger_enforcer")
    quality_gate = _closed_quality_gate()
    quality_gate["gates"]["before_review_handoff"]["status"] = "open"

    result = module.build_quality_gate_ledger_enforcement(
        evidence_ledger_payload=_closed_evidence_ledger(),
        review_ledger_payload=_closed_review_ledger(),
        publication_eval_payload=_ready_publication_eval(),
        reporting_guideline_gate_payload=quality_gate,
    )

    assert result["fast_lane_execution_allowed"] is False
    assert "reporting_guideline_gate_not_closed" in result["hard_blockers"]
