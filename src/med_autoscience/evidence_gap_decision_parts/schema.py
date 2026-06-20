from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any


VERSION = "evidence-gap-decision.v1"
OWNER = "MedAutoScience"
ACTIVE_STATE = "active_gap_decision"
SURFACE_KIND = "mas_evidence_gap_decision"

IDENTITY_FIELDS = (
    "study_id",
    "quest_id",
    "work_unit_id",
    "work_unit_fingerprint",
    "route_identity_key",
    "attempt_idempotency_key",
)
REQUIRED_IDENTITY_FIELDS = (
    "study_id",
    "work_unit_id",
    "work_unit_fingerprint",
)
CLAIM_BOUNDARY = {
    "paper_progress_claim_allowed": False,
    "live_runtime_readiness_claim_allowed": False,
    "publication_readiness_claim_allowed": False,
    "production_readiness_claim_allowed": False,
}
FORBIDDEN_CLAIM_TERMS = (
    "live_runtime_ready",
    "paper_progress",
    "publication_ready",
    "submission_ready",
    "production_ready",
    "provider_running",
    "owner_receipt_closed",
    "quality_verdict",
    "domain_ready",
    "current_package_fresh",
)
TYPED_BLOCKER_GAP_CLASSES = frozenset({"authority_gate", "human_gate"})
DECISION_BY_GAP_CLASS = {
    "authority_gate": "materialize_typed_blocker",
    "human_gate": "open_human_gate",
    "proceed_with_assumption": "proceed_with_recorded_assumption",
    "soft_quality_gap": "continue_with_quality_followup",
    "observability_backlog": "continue_with_observability_followup",
    "evidence_tail": "record_evidence_tail",
}


@dataclass(frozen=True)
class EvidenceGapDecision:
    gap_class: str
    gap_id: str
    current_owner_delta_ref: str
    current_owner_delta_identity: dict[str, str]
    evidence_refs: tuple[str, ...]
    source_surface_kind: str
    decision_id: str | None = None
    state: str = ACTIVE_STATE
    decision: str | None = None
    typed_blocker_ref: str | None = None
    assumption_ref: str | None = None
    followup_work_order_ref: str | None = None
    missing_ref_family: str | None = None
    reason: str | None = None
    diagnostic_refs: tuple[str, ...] = ()
    helper_allowed_next_actions: tuple[str, ...] = ()
    helper_forbidden_claims: tuple[str, ...] = ()
    helper_repair_owner: str = "med-autoscience"
    helper_escalation_policy: str = "record_and_continue"
    helper_metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def typed_blocker_eligibility(self) -> bool:
        return self.gap_class in TYPED_BLOCKER_GAP_CLASSES

    @property
    def current_action_can_continue(self) -> bool:
        return not self.typed_blocker_eligibility

    @property
    def severity(self) -> str:
        if self.gap_class in TYPED_BLOCKER_GAP_CLASSES:
            return "hard_gate"
        if self.gap_class == "proceed_with_assumption":
            return "assumption"
        if self.gap_class == "observability_backlog":
            return "backlog"
        if self.gap_class == "evidence_tail":
            return "tail"
        return "soft"

    @property
    def allowed_next_actions(self) -> tuple[str, ...]:
        return self.helper_allowed_next_actions

    @property
    def forbidden_claims(self) -> tuple[str, ...]:
        return self.helper_forbidden_claims or FORBIDDEN_CLAIM_TERMS

    @property
    def identity(self) -> dict[str, str]:
        return dict(self.current_owner_delta_identity)

    @property
    def owner(self) -> str:
        return OWNER

    @property
    def repair_owner(self) -> str:
        return self.helper_repair_owner

    @property
    def escalation_policy(self) -> str:
        return self.helper_escalation_policy

    def to_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "surface_kind": SURFACE_KIND,
            "version": VERSION,
            "decision_id": self.decision_id or _stable_id(
                "egd",
                self.gap_class,
                self.gap_id,
                self.current_owner_delta_ref,
                self.current_owner_delta_identity,
                self.evidence_refs,
            ),
            "owner": OWNER,
            "state": self.state,
            "gap_class": self.gap_class,
            "gap_id": self.gap_id,
            "current_owner_delta_ref": self.current_owner_delta_ref,
            "current_owner_delta_identity": dict(self.current_owner_delta_identity),
            "evidence_refs": list(self.evidence_refs),
            "decision": self.decision or DECISION_BY_GAP_CLASS[self.gap_class],
            "typed_blocker_eligibility": self.typed_blocker_eligibility,
            "typed_blocker_policy": self.typed_blocker_policy(),
            "blocks_completion_claim": True,
            "completion_claim_allowed": False,
            "claim_boundary": dict(CLAIM_BOUNDARY),
            "forbidden_claim_terms": list(FORBIDDEN_CLAIM_TERMS),
        }
        if self.assumption_ref is not None:
            payload["assumption_ref"] = self.assumption_ref
        if self.followup_work_order_ref is not None:
            payload["followup_work_order_ref"] = self.followup_work_order_ref
        return payload

    def typed_blocker_policy(self) -> dict[str, Any]:
        if not self.typed_blocker_eligibility:
            return {
                "typed_blocker_countable": False,
                "materialization_allowed": False,
                "materialization_reason": "not_allowed",
                "typed_blocker_ref": None,
            }
        return {
            "typed_blocker_countable": True,
            "materialization_allowed": True,
            "materialization_reason": self.gap_class,
            "typed_blocker_ref": self.typed_blocker_ref
            or _stable_id("typed_blocker_ref", self.gap_class, self.gap_id),
        }


def payload_from_decision(decision: EvidenceGapDecision | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(decision, EvidenceGapDecision):
        return decision.to_payload()
    if isinstance(decision, Mapping):
        return dict(decision)
    raise TypeError("evidence gap decision must be EvidenceGapDecision or mapping payload")


def normalize_decision(decision: EvidenceGapDecision | Mapping[str, Any]) -> EvidenceGapDecision:
    if isinstance(decision, EvidenceGapDecision):
        return decision
    payload = payload_from_decision(decision)
    if payload.get("surface_kind") == SURFACE_KIND:
        return EvidenceGapDecision(
            gap_class=_required_text(payload, "gap_class"),
            gap_id=_required_text(payload, "gap_id"),
            current_owner_delta_ref=_required_text(payload, "current_owner_delta_ref"),
            current_owner_delta_identity=normalize_identity(payload.get("current_owner_delta_identity")),
            evidence_refs=tuple(_required_refs(payload.get("evidence_refs"))),
            source_surface_kind=SURFACE_KIND,
            decision_id=_text(payload.get("decision_id")),
            state=_text(payload.get("state")) or ACTIVE_STATE,
            decision=_text(payload.get("decision")),
            typed_blocker_ref=_typed_blocker_ref(payload.get("typed_blocker_policy")),
            assumption_ref=_text(payload.get("assumption_ref")),
            followup_work_order_ref=_text(payload.get("followup_work_order_ref")),
        )
    return EvidenceGapDecision(
        gap_class=_required_text(payload, "gap_class"),
        gap_id=_text(payload.get("gap_id")) or _gap_id(
            _text(payload.get("surface_kind")) or "legacy_evidence_gap",
            _text(payload.get("missing_ref_family")),
        ),
        current_owner_delta_ref=_text(payload.get("current_owner_delta_ref")) or "current_owner_delta:unknown",
        current_owner_delta_identity=normalize_identity(payload.get("identity")),
        evidence_refs=tuple(_required_refs(payload.get("evidence_refs"))),
        source_surface_kind=_text(payload.get("surface_kind")) or "legacy_evidence_gap",
        decision=_text(payload.get("decision")),
        assumption_ref=_assumption_ref(payload),
        followup_work_order_ref=_followup_ref(payload),
        missing_ref_family=_text(payload.get("missing_ref_family")),
        reason=_text(payload.get("reason")),
        diagnostic_refs=tuple(_text_list(payload.get("diagnostic_refs"))),
        helper_allowed_next_actions=tuple(_text_list(payload.get("allowed_next_actions"))),
        helper_forbidden_claims=tuple(_text_list(payload.get("forbidden_claims"))),
        helper_repair_owner=_text(payload.get("repair_owner")) or "med-autoscience",
        helper_escalation_policy=_text(payload.get("escalation_policy")) or "record_and_continue",
    )


def normalize_identity(value: object = None, **identity: Any) -> dict[str, str]:
    payload: dict[str, Any] = {}
    if isinstance(value, Mapping):
        payload.update(value)
    payload.update(identity)
    normalized = {
        field: text
        for field in IDENTITY_FIELDS
        if (text := _text(payload.get(field))) is not None
    }
    missing = [field for field in REQUIRED_IDENTITY_FIELDS if field not in normalized]
    if missing:
        source = _text(payload.get("source_surface_kind")) or _text(payload.get("surface_kind")) or "evidence_gap"
        ref_family = _text(payload.get("missing_ref_family")) or "unspecified"
        digest = _digest([source, ref_family, sorted(payload.items(), key=lambda item: item[0])])
        normalized.setdefault("study_id", _text(payload.get("program_id")) or "unknown-study")
        normalized.setdefault("work_unit_id", _slug(source) or "evidence_gap")
        normalized.setdefault("work_unit_fingerprint", f"evidence-gap::{digest}")
    return normalized


def normalize_refs(value: Iterable[object] | object | None) -> tuple[str, ...]:
    return tuple(_text_list(value))


def required_evidence_refs(
    evidence_refs: object | None,
    *,
    missing_ref_family: str | None,
    source_surface_kind: str,
) -> tuple[str, ...]:
    refs = normalize_refs(evidence_refs)
    if refs:
        return refs
    ref_family = missing_ref_family or source_surface_kind
    return (f"evidence_gap_ref:{_slug(ref_family) or 'unspecified'}",)


def make_gap_id(source_surface_kind: str, missing_ref_family: str | None, gap_class: str) -> str:
    return _gap_id(source_surface_kind, missing_ref_family or gap_class)


def make_owner_delta_ref(identity: Mapping[str, Any], source_surface_kind: str) -> str:
    study_id = _text(identity.get("study_id")) or "unknown-study"
    work_unit_id = _text(identity.get("work_unit_id")) or _slug(source_surface_kind) or "evidence_gap"
    fingerprint = _text(identity.get("work_unit_fingerprint")) or "unknown-fingerprint"
    return f"current_owner_delta:{study_id}/{work_unit_id}/{_digest([fingerprint])}"


def make_optional_ref(prefix: str, gap_id: str) -> str:
    return f"{prefix}:{gap_id}"


def _required_refs(value: object) -> list[str]:
    refs = _text_list(value)
    if not refs:
        raise ValueError("evidence gap decision payload missing evidence_refs")
    return refs


def _required_text(payload: Mapping[str, Any], key: str) -> str:
    text = _text(payload.get(key))
    if text is None:
        raise ValueError(f"evidence gap decision payload missing {key}")
    return text


def _typed_blocker_ref(value: object) -> str | None:
    if not isinstance(value, Mapping):
        return None
    return _text(value.get("typed_blocker_ref"))


def _assumption_ref(payload: Mapping[str, Any]) -> str | None:
    text = _text(payload.get("assumption_ref"))
    if text is not None:
        return text
    assumption = payload.get("assumption")
    if isinstance(assumption, Mapping):
        scope = _text(assumption.get("scope"))
        if scope is not None:
            return make_optional_ref("assumption_ref", _slug(scope) or "bounded-assumption")
    return None


def _followup_ref(payload: Mapping[str, Any]) -> str | None:
    text = _text(payload.get("followup_work_order_ref"))
    if text is not None:
        return text
    gap_class = _text(payload.get("gap_class"))
    if gap_class in {"soft_quality_gap", "observability_backlog", "evidence_tail"}:
        gap_id = _text(payload.get("gap_id")) or _gap_id(
            _text(payload.get("surface_kind")) or "evidence_gap",
            _text(payload.get("missing_ref_family")) or gap_class,
        )
        return make_optional_ref("work_order_ref", gap_id)
    return None


def _gap_id(source_surface_kind: str, missing_ref_family: str | None) -> str:
    stem = _slug(missing_ref_family) or _slug(source_surface_kind) or "unspecified"
    return f"{stem}_{_digest([source_surface_kind, missing_ref_family or ''])}"


def _stable_id(prefix: str, *parts: object) -> str:
    return f"{prefix}-{_digest(parts)}"


def _digest(parts: Iterable[object]) -> str:
    blob = repr(list(parts)).encode("utf-8")
    return sha256(blob).hexdigest()[:16]


def _slug(value: object) -> str | None:
    text = _text(value)
    if text is None:
        return None
    chars: list[str] = []
    previous_dash = False
    for char in text.casefold():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    return "".join(chars).strip("-")[:80] or None


def _text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = _text(value)
        return [text] if text is not None else []
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return []
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = _text(item)
        if text is None or text in seen:
            continue
        result.append(text)
        seen.add(text)
    return result


__all__ = [
    "ACTIVE_STATE",
    "CLAIM_BOUNDARY",
    "DECISION_BY_GAP_CLASS",
    "EvidenceGapDecision",
    "FORBIDDEN_CLAIM_TERMS",
    "IDENTITY_FIELDS",
    "OWNER",
    "REQUIRED_IDENTITY_FIELDS",
    "SURFACE_KIND",
    "TYPED_BLOCKER_GAP_CLASSES",
    "VERSION",
    "make_gap_id",
    "make_optional_ref",
    "make_owner_delta_ref",
    "normalize_decision",
    "normalize_identity",
    "normalize_refs",
    "payload_from_decision",
    "required_evidence_refs",
]
