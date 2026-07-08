from __future__ import annotations

from typing import Any


def authority_boundary() -> dict[str, Any]:
    return {
        "domain_truth_owner": "med-autoscience",
        "quality_gate_owner": "med-autoscience",
        "artifact_authority_owner": "med-autoscience",
        "writes_current_package": False,
        "quality_authorized": False,
        "submission_authorized": False,
    }


def would_write(work_unit_type: str) -> list[str]:
    if work_unit_type == "claim_downgrade":
        return ["paper/draft.md", "paper/evidence_ledger.json", "paper/review/review_ledger.json"]
    if work_unit_type == "text_repair":
        return ["paper/draft.md", "paper/review/review_ledger.json"]
    if work_unit_type == "evidence_ledger_repair":
        return ["paper/evidence_ledger.json"]
    if work_unit_type == "review_ledger_repair":
        return ["paper/review/review_ledger.json"]
    if work_unit_type == "analysis_repair":
        return ["paper/draft.md", "paper/evidence_ledger.json"]
    if work_unit_type == "route_decision":
        return ["paper/evidence_ledger.json", "paper/review/review_ledger.json"]
    return []


__all__ = ["authority_boundary", "would_write"]
