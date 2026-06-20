from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .schema import (
    EvidenceGapDecision,
    make_gap_id,
    make_optional_ref,
    make_owner_delta_ref,
    normalize_identity,
    required_evidence_refs,
)


AUTHORITY_GATE_TERMS = (
    "opl event",
    "outbox",
    "stagerun",
    "stage run",
    "currentness",
    "provider authorization",
    "provider_authorization",
    "source-data",
    "source data",
    "privacy",
    "forbidden-write",
    "forbidden write",
    "owner route",
)
HUMAN_GATE_TERMS = (
    "human",
    "submission",
    "irreversible",
)
SOFT_QUALITY_TERMS = (
    "reviewer polish",
    "reviewer",
    "polish",
    "structure",
    "non-hard concern",
    "non hard concern",
)
OBSERVABILITY_TERMS = (
    "telemetry",
    "token",
    "cost",
    "trace",
    "portal",
)
EVIDENCE_TAIL_TERMS = (
    "production soak",
    "direct-hosted parity",
    "direct hosted parity",
    "live-readiness tail",
    "live readiness tail",
)
ASSUMPTION_TERMS = (
    "safe non-critical",
    "safe non critical",
    "non-critical",
    "non critical",
)


def classify_gap(
    *,
    surface_kind: str,
    missing_ref_family: str | None = None,
    identity: Mapping[str, Any] | None = None,
    evidence_refs: object | None = None,
    diagnostic_refs: object | None = None,
) -> EvidenceGapDecision:
    normalized_surface = _required_text(surface_kind, "surface_kind")
    normalized_ref_family = _text(missing_ref_family)
    classification = _classification_for(normalized_surface, normalized_ref_family)
    normalized_identity = normalize_identity(
        identity,
        source_surface_kind=normalized_surface,
        missing_ref_family=normalized_ref_family,
    )
    gap_id = make_gap_id(
        normalized_surface,
        normalized_ref_family,
        classification["gap_class"],
    )
    return EvidenceGapDecision(
        gap_class=classification["gap_class"],
        gap_id=gap_id,
        current_owner_delta_ref=make_owner_delta_ref(normalized_identity, normalized_surface),
        current_owner_delta_identity=normalized_identity,
        evidence_refs=required_evidence_refs(
            evidence_refs,
            missing_ref_family=normalized_ref_family,
            source_surface_kind=normalized_surface,
        ),
        source_surface_kind=normalized_surface,
        assumption_ref=_assumption_ref(classification["gap_class"], gap_id),
        followup_work_order_ref=_followup_ref(classification["gap_class"], gap_id),
        missing_ref_family=normalized_ref_family,
        diagnostic_refs=required_evidence_refs(
            diagnostic_refs,
            missing_ref_family=normalized_ref_family,
            source_surface_kind=f"{normalized_surface}:diagnostic",
        )
        if diagnostic_refs is not None
        else (),
        helper_allowed_next_actions=tuple(classification["allowed_next_actions"]),
        helper_forbidden_claims=tuple(classification["forbidden_claims"]),
        helper_repair_owner=classification["repair_owner"],
        helper_escalation_policy=classification["escalation_policy"],
        reason=classification["reason"],
    )


def _classification_for(surface_kind: str, missing_ref_family: str | None) -> dict[str, Any]:
    haystack = _haystack(surface_kind, missing_ref_family)
    if _contains_any(haystack, AUTHORITY_GATE_TERMS):
        return _authority_gate()
    if _contains_any(haystack, HUMAN_GATE_TERMS):
        return _human_gate()
    if _contains_any(haystack, SOFT_QUALITY_TERMS):
        return _soft_quality_gap()
    if _contains_any(haystack, OBSERVABILITY_TERMS):
        return _observability_backlog()
    if _contains_any(haystack, EVIDENCE_TAIL_TERMS):
        return _evidence_tail()
    if _contains_any(haystack, ASSUMPTION_TERMS):
        return _proceed_with_assumption()
    return _authority_gate(reason="unclassified_gap_requires_owner_decision")


def _authority_gate(*, reason: str = "authority_surface_missing_or_not_current") -> dict[str, Any]:
    return {
        "gap_class": "authority_gate",
        "severity": "hard_gate",
        "current_action_can_continue": False,
        "allowed_next_actions": [
            "repair_authority_surface",
            "collect_owner_receipt_or_typed_blocker",
            "rerun_currentness_readback",
        ],
        "forbidden_claims": [
            "ready",
            "current",
            "authority_cleared",
            "evidence_complete",
            "production_ready",
        ],
        "owner": "med-autoscience",
        "repair_owner": "mas_authority_owner",
        "escalation_policy": "typed_blocker_required",
        "reason": reason,
    }


def _human_gate() -> dict[str, Any]:
    return {
        "gap_class": "human_gate",
        "severity": "hard_gate",
        "current_action_can_continue": False,
        "allowed_next_actions": [
            "request_human_decision",
            "record_human_gate_blocker",
        ],
        "forbidden_claims": [
            "ready",
            "human_approved",
            "submission_ready",
            "irreversible_action_authorized",
        ],
        "owner": "med-autoscience",
        "repair_owner": "human_owner",
        "escalation_policy": "human_decision_required",
        "reason": "human_or_irreversible_decision_required",
    }


def _soft_quality_gap() -> dict[str, Any]:
    return {
        "gap_class": "soft_quality_gap",
        "severity": "soft",
        "current_action_can_continue": True,
        "allowed_next_actions": [
            "continue_current_action",
            "schedule_quality_repair",
        ],
        "forbidden_claims": [
            "quality_complete",
            "reviewer_cleared",
        ],
        "owner": "med-autoscience",
        "repair_owner": "quality_repair_owner",
        "escalation_policy": "track_as_quality_repair",
        "reason": "non_hard_quality_concern",
    }


def _observability_backlog() -> dict[str, Any]:
    return {
        "gap_class": "observability_backlog",
        "severity": "backlog",
        "current_action_can_continue": True,
        "allowed_next_actions": [
            "continue_current_action",
            "schedule_observability_backlog",
        ],
        "forbidden_claims": [
            "observability_complete",
            "trace_complete",
            "cost_accounting_complete",
        ],
        "owner": "med-autoscience",
        "repair_owner": "observability_owner",
        "escalation_policy": "track_as_backlog",
        "reason": "non_blocking_observability_gap",
    }


def _evidence_tail() -> dict[str, Any]:
    return {
        "gap_class": "evidence_tail",
        "severity": "tail",
        "current_action_can_continue": True,
        "allowed_next_actions": [
            "continue_current_action",
            "collect_tail_evidence",
            "withhold_readiness_claim",
        ],
        "forbidden_claims": [
            "ready",
            "current",
            "production_ready",
            "live_ready",
            "evidence_complete",
        ],
        "owner": "med-autoscience",
        "repair_owner": "runtime_evidence_owner",
        "escalation_policy": "tail_evidence_required_before_readiness_claim",
        "reason": "readiness_or_live_tail_evidence_missing",
    }


def _proceed_with_assumption() -> dict[str, Any]:
    return {
        "gap_class": "proceed_with_assumption",
        "severity": "assumption",
        "current_action_can_continue": True,
        "allowed_next_actions": [
            "continue_current_action",
            "record_assumption",
        ],
        "forbidden_claims": [
            "ready",
            "current",
            "evidence_complete",
            "assumption_free",
        ],
        "owner": "med-autoscience",
        "repair_owner": "current_executor",
        "escalation_policy": "explicit_assumption_only",
        "reason": "safe_non_critical_ref_missing",
    }


def _assumption_ref(gap_class: str, gap_id: str) -> str | None:
    if gap_class != "proceed_with_assumption":
        return None
    return make_optional_ref("assumption_ref", gap_id)


def _followup_ref(gap_class: str, gap_id: str) -> str | None:
    if gap_class not in {"soft_quality_gap", "observability_backlog", "evidence_tail"}:
        return None
    return make_optional_ref("work_order_ref", gap_id)


def _haystack(surface_kind: str, missing_ref_family: str | None) -> str:
    return " ".join(item for item in (surface_kind, missing_ref_family) if item).casefold()


def _contains_any(haystack: str, terms: tuple[str, ...]) -> bool:
    return any(term in haystack for term in terms)


def _required_text(value: object, label: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{label} must be non-empty")
    return text


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


__all__ = ["classify_gap"]
