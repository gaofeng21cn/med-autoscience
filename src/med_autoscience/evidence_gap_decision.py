from __future__ import annotations

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from typing import Any


SCHEMA_VERSION = 1
DECISION_SURFACE_KIND = "mas_evidence_gap_decision"
SUMMARY_SURFACE_KIND = "mas_evidence_gap_decision_summary"

GAP_CLASSES = (
    "authority_gate",
    "human_gate",
    "proceed_with_assumption",
    "soft_quality_gap",
    "observability_backlog",
    "evidence_tail",
)
HARD_GATE_CLASSES = frozenset({"authority_gate", "human_gate"})
NONBLOCKING_GAP_CLASSES = frozenset(
    {"proceed_with_assumption", "soft_quality_gap", "observability_backlog", "evidence_tail"}
)
IDENTITY_FIELDS = (
    "program_id",
    "study_id",
    "quest_id",
    "active_run_id",
    "stage_id",
    "stage_run_id",
    "work_unit_id",
    "work_unit_fingerprint",
    "action_id",
    "action_type",
    "request_id",
    "trace_id",
)
READINESS_FORBIDDEN_CLAIMS = (
    "owner_receipt_closed",
    "paper_progress",
    "publication_ready",
    "submission_ready",
    "live_runtime_ready",
    "production_ready",
    "provider_running",
)

_AUTHORITY_TERMS = (
    "authority violation",
    "authority_violation",
    "artifact mutation authorization",
    "submission authorization",
    "provider credential",
    "forbidden write",
    "forbidden-write",
    "forbidden_write",
    "write permission",
    "privacy",
    "phi",
)
_HUMAN_TERMS = (
    "explicit human decision",
    "explicit_human_decision",
    "human gate",
    "human_gate",
    "manual approval",
    "pi approval",
    "submit now",
    "submit_now",
    "irreversible",
    "owner decision",
    "user authorization",
)
_OBSERVABILITY_TERMS = (
    "telemetry",
    "observability",
    "token",
    "cost",
    "trace",
    "portal",
    "dashboard freshness",
    "report freshness",
)
_EVIDENCE_TAIL_TERMS = (
    "production soak",
    "live readiness",
    "live-readiness",
    "direct-hosted parity",
    "direct hosted parity",
    "canary",
    "release evidence",
    "runtime tail",
)
_SOFT_QUALITY_TERMS = (
    "reviewer",
    "reviewer concern",
    "non-hard concern",
    "non hard concern",
    "polish",
    "structure",
    "ledger field",
    "missing field",
    "citation polish",
)
_ASSUMPTION_TERMS = (
    "non-critical",
    "non critical",
    "minor",
    "bibliography helper",
    "explanatory ref",
    "safe assumption",
    "safe non-critical",
)


@dataclass(frozen=True)
class EvidenceGapDecision:
    surface_kind: str
    gap_class: str
    severity: str
    current_action_can_continue: bool
    allowed_next_actions: tuple[str, ...]
    forbidden_claims: tuple[str, ...]
    owner: str
    repair_owner: str
    escalation_policy: str
    identity: dict[str, Any] = field(default_factory=dict)
    missing_ref_family: str | None = None
    reason: str | None = None
    assumption: dict[str, Any] | None = None
    evidence_refs: tuple[str, ...] = ()
    diagnostic_refs: tuple[str, ...] = ()
    confidence: str = "medium"
    decision_trace: tuple[str, ...] = ()

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "surface_kind": DECISION_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "source_surface_kind": self.surface_kind,
            "gap_class": self.gap_class,
            "severity": self.severity,
            "current_action_can_continue": self.current_action_can_continue,
            "allowed_next_actions": list(self.allowed_next_actions),
            "forbidden_claims": list(self.forbidden_claims),
            "owner": self.owner,
            "repair_owner": self.repair_owner,
            "escalation_policy": self.escalation_policy,
            "typed_blocker_eligibility": self.gap_class in HARD_GATE_CLASSES,
            "claim_boundary": claim_boundary(self),
            "identity": dict(self.identity),
            "identity_fields": list(IDENTITY_FIELDS),
            "assumption": dict(self.assumption) if self.assumption is not None else None,
            "evidence_refs": list(self.evidence_refs),
            "diagnostic_refs": list(self.diagnostic_refs),
            "confidence": self.confidence,
            "decision_trace": list(self.decision_trace),
        }
        if self.missing_ref_family is not None:
            payload["missing_ref_family"] = self.missing_ref_family
        if self.reason is not None:
            payload["reason"] = self.reason
        return payload


def classify_evidence_gap(
    *,
    surface_kind: str,
    missing_ref_family: str | None = None,
    identity: Mapping[str, Any] | None = None,
    evidence_refs: object | None = None,
    diagnostic_refs: object | None = None,
    confidence: str | None = None,
) -> EvidenceGapDecision:
    source_surface_kind = _required_text(surface_kind, "surface_kind")
    ref_family = _text(missing_ref_family)
    gap_class = _gap_class_for(source_surface_kind, ref_family)
    policy = _policy_for(gap_class)
    return EvidenceGapDecision(
        surface_kind=source_surface_kind,
        gap_class=gap_class,
        severity=policy["severity"],
        current_action_can_continue=policy["current_action_can_continue"],
        allowed_next_actions=tuple(policy["allowed_next_actions"]),
        forbidden_claims=tuple(policy["forbidden_claims"]),
        owner=policy["owner"],
        repair_owner=policy["repair_owner"],
        escalation_policy=policy["escalation_policy"],
        identity=normalize_identity(identity),
        missing_ref_family=ref_family,
        reason=policy["reason"],
        assumption=_assumption_payload(gap_class, ref_family),
        evidence_refs=normalize_refs(evidence_refs),
        diagnostic_refs=normalize_refs(diagnostic_refs),
        confidence=_text(confidence) or policy["confidence"],
        decision_trace=(
            "classify_missing_evidence_by_authority_boundary",
            f"gap_class:{gap_class}",
            f"current_action_can_continue:{policy['current_action_can_continue']}",
        ),
    )


def classify_missing_ref_family(
    missing_ref_family: str,
    *,
    surface_kind: str = "missing_evidence_ref",
    identity: Mapping[str, Any] | None = None,
    evidence_refs: object | None = None,
    diagnostic_refs: object | None = None,
    confidence: str | None = None,
) -> EvidenceGapDecision:
    return classify_evidence_gap(
        surface_kind=surface_kind,
        missing_ref_family=missing_ref_family,
        identity=identity,
        evidence_refs=evidence_refs,
        diagnostic_refs=diagnostic_refs,
        confidence=confidence,
    )


def payload_from_decision(decision: EvidenceGapDecision | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(decision, EvidenceGapDecision):
        return decision.to_payload()
    if isinstance(decision, Mapping):
        return dict(decision)
    raise TypeError("evidence gap decision must be EvidenceGapDecision or mapping")


def normalize_decision(decision: EvidenceGapDecision | Mapping[str, Any]) -> EvidenceGapDecision:
    if isinstance(decision, EvidenceGapDecision):
        return decision
    payload = payload_from_decision(decision)
    source_surface_kind = (
        _text(payload.get("source_surface_kind"))
        or _text(payload.get("surface_kind"))
        or "unknown_surface"
    )
    gap_class = _text(payload.get("gap_class")) or "authority_gate"
    policy = _policy_for(gap_class if gap_class in GAP_CLASSES else "authority_gate")
    return EvidenceGapDecision(
        surface_kind=source_surface_kind,
        gap_class=gap_class,
        severity=_text(payload.get("severity")) or policy["severity"],
        current_action_can_continue=payload.get("current_action_can_continue") is True,
        allowed_next_actions=tuple(normalize_refs(payload.get("allowed_next_actions"))),
        forbidden_claims=tuple(normalize_refs(payload.get("forbidden_claims"))),
        owner=_text(payload.get("owner")) or policy["owner"],
        repair_owner=_text(payload.get("repair_owner")) or policy["repair_owner"],
        escalation_policy=_text(payload.get("escalation_policy")) or policy["escalation_policy"],
        identity=normalize_identity(_mapping(payload.get("identity"))),
        missing_ref_family=_text(payload.get("missing_ref_family")),
        reason=_text(payload.get("reason")),
        assumption=dict(payload["assumption"]) if isinstance(payload.get("assumption"), Mapping) else None,
        evidence_refs=normalize_refs(payload.get("evidence_refs")),
        diagnostic_refs=normalize_refs(payload.get("diagnostic_refs")),
        confidence=_text(payload.get("confidence")) or policy["confidence"],
        decision_trace=tuple(normalize_refs(payload.get("decision_trace"))),
    )


def is_hard_gate(decision: EvidenceGapDecision | Mapping[str, Any]) -> bool:
    return normalize_decision(decision).gap_class in HARD_GATE_CLASSES


def can_continue_current_action(decision: EvidenceGapDecision | Mapping[str, Any]) -> bool:
    return normalize_decision(decision).current_action_can_continue


def materialize_typed_blocker_if_required(
    decision: EvidenceGapDecision | Mapping[str, Any],
) -> dict[str, Any] | None:
    normalized = normalize_decision(decision)
    if normalized.gap_class not in HARD_GATE_CLASSES:
        return None
    payload = normalized.to_payload()
    blocker_type = (
        "evidence_gap_human_gate_required"
        if normalized.gap_class == "human_gate"
        else "evidence_gap_authority_gate_required"
    )
    return {
        "surface_kind": "mas_evidence_gap_typed_blocker",
        "schema_version": SCHEMA_VERSION,
        "blocker_type": blocker_type,
        "blocked_reason": normalized.reason or normalized.gap_class,
        "gap_class": normalized.gap_class,
        "severity": normalized.severity,
        "owner": normalized.owner,
        "required_next_owner": normalized.repair_owner,
        "required_owner_surface": (
            "human_decision_surface"
            if normalized.gap_class == "human_gate"
            else "mas_authority_surface"
        ),
        "write_permitted": False,
        "current_action_can_continue": False,
        "forbidden_claims": list(normalized.forbidden_claims),
        "evidence_gap_decision": payload,
        "identity": dict(normalized.identity),
        "evidence_refs": list(normalized.evidence_refs),
        "diagnostic_refs": list(normalized.diagnostic_refs),
    }


def merge_gap_decisions(
    *decision_groups: Iterable[EvidenceGapDecision | Mapping[str, Any]]
    | EvidenceGapDecision
    | Mapping[str, Any]
    | None,
) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    for group in decision_groups:
        if group is None:
            continue
        if isinstance(group, EvidenceGapDecision) or isinstance(group, Mapping):
            merged.append(payload_from_decision(group))
            continue
        for decision in group:
            merged.append(payload_from_decision(decision))
    return _dedupe_decisions(merged)


def summarize_gap_decisions(
    decisions: Iterable[EvidenceGapDecision | Mapping[str, Any]],
) -> dict[str, Any]:
    normalized = [normalize_decision(decision) for decision in decisions]
    gap_counts = Counter(decision.gap_class for decision in normalized)
    severity_counts = Counter(decision.severity for decision in normalized)
    forbidden_claims = _merged_texts(decision.forbidden_claims for decision in normalized)
    return {
        "surface_kind": SUMMARY_SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "total_count": len(normalized),
        "hard_gate_count": sum(decision.gap_class == "authority_gate" for decision in normalized),
        "human_gate_count": sum(decision.gap_class == "human_gate" for decision in normalized),
        "soft_gap_count": sum(decision.gap_class == "soft_quality_gap" for decision in normalized),
        "assumption_count": sum(decision.gap_class == "proceed_with_assumption" for decision in normalized),
        "observability_backlog_count": sum(
            decision.gap_class == "observability_backlog" for decision in normalized
        ),
        "evidence_tail_count": sum(decision.gap_class == "evidence_tail" for decision in normalized),
        "current_action_can_continue": all(
            decision.current_action_can_continue for decision in normalized
        ),
        "counts_by_gap_class": dict(sorted(gap_counts.items())),
        "counts_by_severity": dict(sorted(severity_counts.items())),
        "allowed_next_actions": _merged_texts(
            decision.allowed_next_actions for decision in normalized
        ),
        "forbidden_claims": forbidden_claims,
        "claim_boundary": {
            "paper_progress_claim_allowed": "paper_progress" not in forbidden_claims,
            "publication_readiness_claim_allowed": "publication_ready" not in forbidden_claims,
            "submission_readiness_claim_allowed": "submission_ready" not in forbidden_claims,
            "live_runtime_readiness_claim_allowed": "live_runtime_ready" not in forbidden_claims,
            "production_readiness_claim_allowed": "production_ready" not in forbidden_claims,
        },
        "evidence_refs": _merged_texts(decision.evidence_refs for decision in normalized),
        "diagnostic_refs": _merged_texts(decision.diagnostic_refs for decision in normalized),
    }


def claim_boundary(decision: EvidenceGapDecision | Mapping[str, Any]) -> dict[str, bool]:
    normalized = normalize_decision(decision) if not isinstance(decision, EvidenceGapDecision) else decision
    forbidden = set(normalized.forbidden_claims)
    return {
        "paper_progress_claim_allowed": "paper_progress" not in forbidden,
        "owner_receipt_claim_allowed": "owner_receipt_closed" not in forbidden,
        "publication_readiness_claim_allowed": "publication_ready" not in forbidden,
        "submission_readiness_claim_allowed": "submission_ready" not in forbidden,
        "live_runtime_readiness_claim_allowed": "live_runtime_ready" not in forbidden,
        "production_readiness_claim_allowed": "production_ready" not in forbidden,
    }


def normalize_identity(value: Mapping[str, Any] | None = None, **identity: Any) -> dict[str, Any]:
    payload: dict[str, Any] = {}
    if isinstance(value, Mapping):
        payload.update(value)
    payload.update(identity)
    return {
        field: payload[field]
        for field in IDENTITY_FIELDS
        if field in payload and payload[field] not in (None, "")
    }


def normalize_refs(value: object | None) -> tuple[str, ...]:
    if isinstance(value, str):
        text = _text(value)
        return (text,) if text is not None else ()
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return ()
    refs: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _text(item)
        if text is None or text in seen:
            continue
        refs.append(text)
        seen.add(text)
    return tuple(refs)


def _gap_class_for(surface_kind: str, missing_ref_family: str | None) -> str:
    haystack = " ".join(item for item in (surface_kind, missing_ref_family) if item).casefold()
    if _contains_any(haystack, _HUMAN_TERMS):
        return "human_gate"
    if _contains_any(haystack, _AUTHORITY_TERMS):
        return "authority_gate"
    if _contains_any(haystack, _OBSERVABILITY_TERMS):
        return "observability_backlog"
    if _contains_any(haystack, _EVIDENCE_TAIL_TERMS):
        return "evidence_tail"
    if _contains_any(haystack, _SOFT_QUALITY_TERMS):
        return "soft_quality_gap"
    if _contains_any(haystack, _ASSUMPTION_TERMS):
        return "proceed_with_assumption"
    return "proceed_with_assumption"


def _policy_for(gap_class: str) -> dict[str, Any]:
    if gap_class == "authority_gate":
        return {
            "severity": "hard_gate",
            "current_action_can_continue": False,
            "allowed_next_actions": (
                "repair_authority_surface",
                "collect_owner_receipt_or_typed_blocker",
                "rerun_currentness_readback",
            ),
            "forbidden_claims": READINESS_FORBIDDEN_CLAIMS,
            "owner": "med-autoscience",
            "repair_owner": "mas_authority_owner",
            "escalation_policy": "typed_blocker_required",
            "reason": "authority_surface_missing_or_not_current",
            "confidence": "high",
        }
    if gap_class == "human_gate":
        return {
            "severity": "hard_gate",
            "current_action_can_continue": False,
            "allowed_next_actions": ("request_human_decision", "record_human_gate"),
            "forbidden_claims": READINESS_FORBIDDEN_CLAIMS
            + ("human_approved", "irreversible_action_authorized"),
            "owner": "med-autoscience",
            "repair_owner": "human_owner",
            "escalation_policy": "human_decision_required",
            "reason": "human_or_irreversible_decision_required",
            "confidence": "high",
        }
    if gap_class == "soft_quality_gap":
        return {
            "severity": "soft",
            "current_action_can_continue": True,
            "allowed_next_actions": ("continue_current_action", "schedule_quality_repair"),
            "forbidden_claims": READINESS_FORBIDDEN_CLAIMS + (
                "quality_complete",
                "reviewer_cleared",
            ),
            "owner": "med-autoscience",
            "repair_owner": "quality_repair_owner",
            "escalation_policy": "track_as_quality_repair",
            "reason": "non_hard_quality_concern",
            "confidence": "medium",
        }
    if gap_class == "observability_backlog":
        return {
            "severity": "backlog",
            "current_action_can_continue": True,
            "allowed_next_actions": ("continue_current_action", "schedule_observability_backlog"),
            "forbidden_claims": READINESS_FORBIDDEN_CLAIMS + (
                "observability_complete",
                "trace_complete",
                "cost_accounting_complete",
            ),
            "owner": "med-autoscience",
            "repair_owner": "observability_owner",
            "escalation_policy": "track_as_observability_backlog",
            "reason": "non_blocking_observability_gap",
            "confidence": "medium",
        }
    if gap_class == "evidence_tail":
        return {
            "severity": "tail",
            "current_action_can_continue": True,
            "allowed_next_actions": (
                "continue_current_action",
                "collect_tail_evidence",
                "withhold_readiness_claim",
            ),
            "forbidden_claims": READINESS_FORBIDDEN_CLAIMS + ("evidence_complete",),
            "owner": "med-autoscience",
            "repair_owner": "runtime_evidence_owner",
            "escalation_policy": "tail_evidence_required_before_readiness_claim",
            "reason": "readiness_or_live_tail_evidence_missing",
            "confidence": "medium",
        }
    return {
        "severity": "assumption",
        "current_action_can_continue": True,
        "allowed_next_actions": ("continue_current_action", "record_assumption"),
        "forbidden_claims": READINESS_FORBIDDEN_CLAIMS + (
            "evidence_complete",
            "assumption_free",
        ),
        "owner": "med-autoscience",
        "repair_owner": "current_executor",
        "escalation_policy": "explicit_assumption_only",
        "reason": "safe_non_critical_ref_missing",
        "confidence": "medium",
    }


def _assumption_payload(gap_class: str, missing_ref_family: str | None) -> dict[str, Any] | None:
    if gap_class != "proceed_with_assumption":
        return None
    return {
        "surface_kind": "mas_evidence_gap_assumption",
        "status": "explicit_assumption",
        "scope": missing_ref_family or "safe_non_critical_evidence_gap",
        "does_not_authorize_claims": list(READINESS_FORBIDDEN_CLAIMS),
    }


def _dedupe_decisions(decisions: Sequence[dict[str, Any]]) -> list[dict[str, Any]]:
    merged: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None]] = set()
    for decision in decisions:
        identity = _mapping(decision.get("identity"))
        key = (
            _text(decision.get("source_surface_kind")) or _text(decision.get("surface_kind")),
            _text(decision.get("gap_class")),
            _text(decision.get("missing_ref_family")) or _text(identity.get("work_unit_id")),
        )
        if key in seen:
            continue
        merged.append(decision)
        seen.add(key)
    return merged


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


def _contains_any(haystack: str, terms: Iterable[str]) -> bool:
    return any(term in haystack for term in terms)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _required_text(value: object, label: str) -> str:
    text = _text(value)
    if text is None:
        raise ValueError(f"{label} must be non-empty")
    return text


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


__all__ = [
    "DECISION_SURFACE_KIND",
    "GAP_CLASSES",
    "HARD_GATE_CLASSES",
    "IDENTITY_FIELDS",
    "NONBLOCKING_GAP_CLASSES",
    "READINESS_FORBIDDEN_CLAIMS",
    "SCHEMA_VERSION",
    "SUMMARY_SURFACE_KIND",
    "EvidenceGapDecision",
    "can_continue_current_action",
    "claim_boundary",
    "classify_evidence_gap",
    "classify_missing_ref_family",
    "is_hard_gate",
    "materialize_typed_blocker_if_required",
    "merge_gap_decisions",
    "normalize_decision",
    "normalize_identity",
    "normalize_refs",
    "payload_from_decision",
    "summarize_gap_decisions",
]
