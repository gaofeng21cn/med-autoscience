from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping
from typing import Any

from .schema import EvidenceGapDecision, normalize_decision, payload_from_decision


DecisionLike = EvidenceGapDecision | Mapping[str, Any]


def merge_gap_decisions(*decision_groups: Iterable[DecisionLike] | DecisionLike | None) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for group in decision_groups:
        if group is None:
            continue
        if isinstance(group, EvidenceGapDecision | Mapping):
            merged.append(payload_from_decision(group))
            continue
        for decision in group:
            merged.append(payload_from_decision(decision))
    return merged


def summarize_gap_decisions(decisions: Iterable[DecisionLike]) -> dict[str, Any]:
    normalized = [normalize_decision(decision) for decision in decisions]
    gap_counts = Counter(decision.gap_class for decision in normalized)
    severity_counts = Counter(decision.severity for decision in normalized)
    hard_gate_count = sum(1 for decision in normalized if decision.severity == "hard_gate")
    typed_blocker_countable_count = sum(
        1
        for decision in normalized
        if decision.typed_blocker_policy()["typed_blocker_countable"] is True
    )
    forbidden_claim_terms = _merged_texts(decision.forbidden_claims for decision in normalized)
    return {
        "surface_kind": "mas_evidence_gap_decision_summary",
        "total_count": len(normalized),
        "hard_gate_count": hard_gate_count,
        "typed_blocker_countable_count": typed_blocker_countable_count,
        "current_action_can_continue": all(decision.current_action_can_continue for decision in normalized),
        "counts_by_gap_class": dict(sorted(gap_counts.items())),
        "counts_by_severity": dict(sorted(severity_counts.items())),
        "allowed_next_actions": _merged_texts(decision.allowed_next_actions for decision in normalized),
        "forbidden_claim_terms": forbidden_claim_terms,
        "forbidden_claims": forbidden_claim_terms,
        "evidence_refs": _merged_texts(decision.evidence_refs for decision in normalized),
        "diagnostic_refs": _merged_texts(decision.diagnostic_refs for decision in normalized),
    }


def _merged_texts(groups: Iterable[Iterable[str]]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item in seen:
                continue
            merged.append(item)
            seen.add(item)
    return merged


__all__ = ["merge_gap_decisions", "summarize_gap_decisions"]
