from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .evidence_gap_decision_parts import (
    DECISION_BY_GAP_CLASS,
    EvidenceGapDecision,
    TYPED_BLOCKER_GAP_CLASSES,
    classify_gap,
    merge_gap_decisions,
    normalize_decision,
    payload_from_decision,
    summarize_gap_decisions,
)


def classify_evidence_gap(
    *,
    surface_kind: str,
    missing_ref_family: str | None = None,
    identity: Mapping[str, Any] | None = None,
    evidence_refs: object | None = None,
    diagnostic_refs: object | None = None,
) -> EvidenceGapDecision:
    return classify_gap(
        surface_kind=surface_kind,
        missing_ref_family=missing_ref_family,
        identity=identity,
        evidence_refs=evidence_refs,
        diagnostic_refs=diagnostic_refs,
    )


def classify_missing_ref_family(
    missing_ref_family: str,
    *,
    surface_kind: str = "missing_ref_family",
    identity: Mapping[str, Any] | None = None,
    evidence_refs: object | None = None,
    diagnostic_refs: object | None = None,
) -> EvidenceGapDecision:
    return classify_evidence_gap(
        surface_kind=surface_kind,
        missing_ref_family=missing_ref_family,
        identity=identity,
        evidence_refs=evidence_refs,
        diagnostic_refs=diagnostic_refs,
    )


def is_hard_gate(decision: EvidenceGapDecision | Mapping[str, Any]) -> bool:
    normalized = normalize_decision(decision)
    return normalized.gap_class in TYPED_BLOCKER_GAP_CLASSES


def can_continue_current_action(decision: EvidenceGapDecision | Mapping[str, Any]) -> bool:
    return not is_hard_gate(decision)


def materialize_typed_blocker_if_required(
    decision: EvidenceGapDecision | Mapping[str, Any],
) -> dict[str, Any] | None:
    normalized = normalize_decision(decision)
    if not is_hard_gate(normalized):
        return None
    owner_surface = "human_decision_surface" if normalized.gap_class == "human_gate" else "mas_authority_surface"
    return {
        "surface_kind": "mas_evidence_gap_typed_blocker",
        "blocker_type": f"evidence_gap_{normalized.gap_class}",
        "gap_class": normalized.gap_class,
        "severity": normalized.severity,
        "write_permitted": False,
        "required_owner_surface": owner_surface,
        "owner": normalized.owner,
        "repair_owner": normalized.repair_owner,
        "escalation_policy": normalized.escalation_policy,
        "current_action_can_continue": False,
        "allowed_next_actions": list(normalized.allowed_next_actions),
        "forbidden_claims": list(normalized.forbidden_claims),
        "evidence_refs": list(normalized.evidence_refs),
        "diagnostic_refs": list(normalized.diagnostic_refs),
        "identity": dict(normalized.identity),
        "current_owner_delta_ref": normalized.current_owner_delta_ref,
        "typed_blocker_policy": normalized.typed_blocker_policy(),
        "decision": normalized.decision or DECISION_BY_GAP_CLASS[normalized.gap_class],
        "missing_ref_family": normalized.missing_ref_family,
        "reason": normalized.reason,
    }


__all__ = [
    "EvidenceGapDecision",
    "can_continue_current_action",
    "classify_evidence_gap",
    "classify_missing_ref_family",
    "is_hard_gate",
    "materialize_typed_blocker_if_required",
    "merge_gap_decisions",
    "summarize_gap_decisions",
]
