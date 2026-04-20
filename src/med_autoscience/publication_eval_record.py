from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_RECORD_ALLOWED_FIELDS = frozenset(
    {
        "schema_version",
        "eval_id",
        "study_id",
        "quest_id",
        "emitted_at",
        "evaluation_scope",
        "charter_context_ref",
        "runtime_context_refs",
        "delivery_context_refs",
        "verdict",
        "gaps",
        "recommended_actions",
    }
)
_CHARTER_CONTEXT_REF_ALLOWED_FIELDS = frozenset({"ref", "charter_id", "publication_objective"})
_VERDICT_ALLOWED_FIELDS = frozenset({"overall_verdict", "primary_claim_status", "summary", "stop_loss_pressure"})
_GAP_ALLOWED_FIELDS = frozenset({"gap_id", "gap_type", "severity", "summary", "evidence_refs"})
_RECOMMENDED_ACTION_ALLOWED_FIELDS = frozenset(
    {
        "action_id",
        "action_type",
        "priority",
        "reason",
        "route_target",
        "route_key_question",
        "route_rationale",
        "evidence_refs",
        "requires_controller_decision",
    }
)
_ALLOWED_OVERALL_VERDICTS = frozenset({"promising", "mixed", "weak", "blocked"})
_ALLOWED_PRIMARY_CLAIM_STATUSES = frozenset({"supported", "partial", "unsupported", "blocked"})
_ALLOWED_STOP_LOSS_PRESSURES = frozenset({"none", "watch", "high"})
_ALLOWED_GAP_TYPES = frozenset({"claim", "evidence", "reporting", "delivery"})
_ALLOWED_GAP_SEVERITIES = frozenset({"must_fix", "important", "optional"})
_ALLOWED_ACTION_TYPES = frozenset(
    {
        "continue_same_line",
        "route_back_same_line",
        "bounded_analysis",
        "return_to_controller",
        "prepare_promotion_review",
    }
)
_ALLOWED_ACTION_PRIORITIES = frozenset({"now", "next"})
_ROUTE_CONTRACT_ACTION_TYPES = frozenset({"continue_same_line", "route_back_same_line", "bounded_analysis"})
_ALLOWED_ROUTE_TARGETS = frozenset(
    {
        "intake-audit",
        "scout",
        "baseline",
        "idea",
        "decision",
        "experiment",
        "analysis-campaign",
        "write",
        "review",
        "finalize",
    }
)
_REQUIRED_RUNTIME_CONTEXT_REF_KEYS = frozenset({"runtime_escalation_ref", "main_result_ref"})
_REQUIRED_DELIVERY_CONTEXT_REF_KEYS = frozenset({"paper_root_ref", "submission_minimal_ref"})


def _reject_unknown_fields(label: str, payload: dict[str, Any], allowed_fields: frozenset[str]) -> None:
    unknown_fields = sorted(set(payload) - allowed_fields)
    if unknown_fields:
        raise ValueError(f"{label} payload contains unknown fields: {', '.join(unknown_fields)}")


def _require_text(label: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _require_ref_text(label: str, field_name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be a ref string")
    return value.strip()


def _require_choice(label: str, field_name: str, value: Any, allowed_values: frozenset[str]) -> str:
    normalized = _require_text(label, field_name, value)
    if normalized not in allowed_values:
        allowed = ", ".join(sorted(allowed_values))
        raise ValueError(f"{label} {field_name} must be one of: {allowed}")
    return normalized


def _optional_text(label: str, field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    return _require_text(label, field_name, value)


def _payload_mapping(payload: dict[str, Any], field_name: str, label: str) -> dict[str, Any]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    return raw_value


def _payload_text(payload: dict[str, Any], field_name: str, label: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    return _require_text(label, field_name, payload.get(field_name))


def _payload_int(payload: dict[str, Any], field_name: str, label: str) -> int:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    value = payload.get(field_name)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be int")
    return value


def _payload_object(payload: dict[str, Any], field_name: str, label: str) -> dict[str, Any]:
    return _payload_mapping(payload, field_name, label)


def _require_ref_mapping(
    field_name: str,
    value: Any,
    *,
    required_keys: frozenset[str] | None = None,
) -> dict[str, str]:
    label = "publication eval record"
    if not isinstance(value, dict):
        raise ValueError(f"{label} {field_name} must be a mapping")
    normalized: dict[str, str] = {}
    for key, item in value.items():
        normalized_key = _require_text(label, f"{field_name} key", key)
        if not normalized_key.endswith("_ref"):
            raise ValueError(f"{label} {field_name} keys must end with _ref")
        normalized[normalized_key] = _require_ref_text(label, f"{field_name} value", item)
    if not normalized:
        raise ValueError(f"{label} {field_name} must not be empty")
    if required_keys is not None:
        missing_keys = sorted(required_keys - normalized.keys())
        if missing_keys:
            raise ValueError(f"{label} {field_name} must include {missing_keys[0]}")
        unexpected_keys = sorted(normalized.keys() - required_keys)
        if unexpected_keys:
            raise ValueError(f"{label} {field_name} contains unexpected ref key {unexpected_keys[0]}")
    return normalized


def _payload_ref_mapping(payload: dict[str, Any], field_name: str, label: str) -> dict[str, str]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    return _require_ref_mapping(field_name, payload.get(field_name))


def _require_text_sequence(label: str, field_name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} {field_name} must be a list")
    normalized = tuple(_require_text(label, field_name[:-1] if field_name.endswith('s') else field_name, item) for item in value)
    if not normalized:
        raise ValueError(f"{label} {field_name} must not be empty")
    return normalized


def _payload_object_sequence(payload: dict[str, Any], field_name: str, label: str) -> list[dict[str, Any]]:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    raw_value = payload.get(field_name)
    if not isinstance(raw_value, list):
        raise ValueError(f"{label} {field_name} must be a list")
    if not raw_value:
        raise ValueError(f"{label} {field_name} must not be empty")
    for item in raw_value:
        if not isinstance(item, dict):
            raise ValueError(f"{label} {field_name} entries must be mappings")
    return raw_value


def _payload_true(payload: dict[str, Any], field_name: str, label: str) -> bool:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    if payload.get(field_name) is not True:
        raise ValueError(f"{label} {field_name} must be true")
    return True


@dataclass(frozen=True)
class PublicationEvalCharterContextRef:
    ref: str
    charter_id: str
    publication_objective: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _require_ref_text("publication eval charter context ref", "ref", self.ref))
        object.__setattr__(self, "charter_id", _require_text("publication eval charter context ref", "charter_id", self.charter_id))
        object.__setattr__(
            self,
            "publication_objective",
            _require_text("publication eval charter context ref", "publication_objective", self.publication_objective),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "ref": self.ref,
            "charter_id": self.charter_id,
            "publication_objective": self.publication_objective,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalCharterContextRef":
        if not isinstance(payload, dict):
            raise TypeError("publication eval charter context ref payload must be a mapping")
        _reject_unknown_fields(
            "publication eval charter context ref",
            payload,
            _CHARTER_CONTEXT_REF_ALLOWED_FIELDS,
        )
        return cls(
            ref=_require_ref_text("publication eval charter context ref", "ref", payload.get("ref")),
            charter_id=_payload_text(payload, "charter_id", "publication eval charter context ref"),
            publication_objective=_payload_text(
                payload,
                "publication_objective",
                "publication eval charter context ref",
            ),
        )


@dataclass(frozen=True)
class PublicationEvalVerdict:
    overall_verdict: str
    primary_claim_status: str
    summary: str
    stop_loss_pressure: str

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "overall_verdict",
            _require_choice(
                "publication eval verdict",
                "overall_verdict",
                self.overall_verdict,
                _ALLOWED_OVERALL_VERDICTS,
            ),
        )
        object.__setattr__(
            self,
            "primary_claim_status",
            _require_choice(
                "publication eval verdict",
                "primary_claim_status",
                self.primary_claim_status,
                _ALLOWED_PRIMARY_CLAIM_STATUSES,
            ),
        )
        object.__setattr__(self, "summary", _require_text("publication eval verdict", "summary", self.summary))
        object.__setattr__(
            self,
            "stop_loss_pressure",
            _require_choice(
                "publication eval verdict",
                "stop_loss_pressure",
                self.stop_loss_pressure,
                _ALLOWED_STOP_LOSS_PRESSURES,
            ),
        )

    def to_dict(self) -> dict[str, str]:
        return {
            "overall_verdict": self.overall_verdict,
            "primary_claim_status": self.primary_claim_status,
            "summary": self.summary,
            "stop_loss_pressure": self.stop_loss_pressure,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalVerdict":
        if not isinstance(payload, dict):
            raise TypeError("publication eval verdict payload must be a mapping")
        _reject_unknown_fields("publication eval verdict", payload, _VERDICT_ALLOWED_FIELDS)
        return cls(
            overall_verdict=_payload_text(payload, "overall_verdict", "publication eval verdict"),
            primary_claim_status=_payload_text(payload, "primary_claim_status", "publication eval verdict"),
            summary=_payload_text(payload, "summary", "publication eval verdict"),
            stop_loss_pressure=_payload_text(payload, "stop_loss_pressure", "publication eval verdict"),
        )


@dataclass(frozen=True)
class PublicationEvalGap:
    gap_id: str
    gap_type: str
    severity: str
    summary: str
    evidence_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "gap_id", _require_text("publication eval gap", "gap_id", self.gap_id))
        object.__setattr__(
            self,
            "gap_type",
            _require_choice("publication eval gap", "gap_type", self.gap_type, _ALLOWED_GAP_TYPES),
        )
        object.__setattr__(
            self,
            "severity",
            _require_choice("publication eval gap", "severity", self.severity, _ALLOWED_GAP_SEVERITIES),
        )
        object.__setattr__(self, "summary", _require_text("publication eval gap", "summary", self.summary))
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(_require_ref_text("publication eval gap", "evidence_ref", item) for item in self.evidence_refs),
        )
        if not self.evidence_refs:
            raise ValueError("publication eval gap evidence_refs must not be empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "gap_id": self.gap_id,
            "gap_type": self.gap_type,
            "severity": self.severity,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalGap":
        if not isinstance(payload, dict):
            raise TypeError("publication eval gap payload must be a mapping")
        _reject_unknown_fields("publication eval gap", payload, _GAP_ALLOWED_FIELDS)
        return cls(
            gap_id=_payload_text(payload, "gap_id", "publication eval gap"),
            gap_type=_payload_text(payload, "gap_type", "publication eval gap"),
            severity=_payload_text(payload, "severity", "publication eval gap"),
            summary=_payload_text(payload, "summary", "publication eval gap"),
            evidence_refs=tuple(
                _require_ref_text("publication eval gap", "evidence_ref", item)
                for item in _require_text_sequence("publication eval gap", "evidence_refs", payload.get("evidence_refs"))
            ),
        )


@dataclass(frozen=True)
class PublicationEvalRecommendedAction:
    action_id: str
    action_type: str
    priority: str
    reason: str
    evidence_refs: tuple[str, ...]
    route_target: str | None = None
    route_key_question: str | None = None
    route_rationale: str | None = None
    requires_controller_decision: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "action_id", _require_text("publication eval recommended action", "action_id", self.action_id))
        object.__setattr__(
            self,
            "action_type",
            _require_choice(
                "publication eval recommended action",
                "action_type",
                self.action_type,
                _ALLOWED_ACTION_TYPES,
            ),
        )
        object.__setattr__(
            self,
            "priority",
            _require_choice(
                "publication eval recommended action",
                "priority",
                self.priority,
                _ALLOWED_ACTION_PRIORITIES,
            ),
        )
        object.__setattr__(self, "reason", _require_text("publication eval recommended action", "reason", self.reason))
        object.__setattr__(
            self,
            "route_target",
            _optional_text("publication eval recommended action", "route_target", self.route_target),
        )
        object.__setattr__(
            self,
            "route_key_question",
            _optional_text("publication eval recommended action", "route_key_question", self.route_key_question),
        )
        object.__setattr__(
            self,
            "route_rationale",
            _optional_text("publication eval recommended action", "route_rationale", self.route_rationale),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(
                _require_ref_text("publication eval recommended action", "evidence_ref", item)
                for item in self.evidence_refs
            ),
        )
        has_route_contract = any(
            value is not None
            for value in (
                self.route_target,
                self.route_key_question,
                self.route_rationale,
            )
        )
        if self.action_type in _ROUTE_CONTRACT_ACTION_TYPES:
            object.__setattr__(
                self,
                "route_target",
                _require_choice(
                    "publication eval recommended action",
                    "route_target",
                    self.route_target,
                    _ALLOWED_ROUTE_TARGETS,
                ),
            )
            if self.route_key_question is None:
                raise ValueError("publication eval recommended action route_key_question must be non-empty")
            if self.route_rationale is None:
                raise ValueError("publication eval recommended action route_rationale must be non-empty")
        elif has_route_contract:
            raise ValueError("publication eval recommended action route_target is only allowed for same-line actions")
        if not self.evidence_refs:
            raise ValueError("publication eval recommended action evidence_refs must not be empty")
        if self.requires_controller_decision is not True:
            raise ValueError("publication eval recommended action requires_controller_decision must be true")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "action_id": self.action_id,
            "action_type": self.action_type,
            "priority": self.priority,
            "reason": self.reason,
            "evidence_refs": list(self.evidence_refs),
            "requires_controller_decision": True,
        }
        if self.route_target is not None:
            payload["route_target"] = self.route_target
            payload["route_key_question"] = self.route_key_question
            payload["route_rationale"] = self.route_rationale
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalRecommendedAction":
        if not isinstance(payload, dict):
            raise TypeError("publication eval recommended action payload must be a mapping")
        _reject_unknown_fields(
            "publication eval recommended action",
            payload,
            _RECOMMENDED_ACTION_ALLOWED_FIELDS,
        )
        return cls(
            action_id=_payload_text(payload, "action_id", "publication eval recommended action"),
            action_type=_payload_text(payload, "action_type", "publication eval recommended action"),
            priority=_payload_text(payload, "priority", "publication eval recommended action"),
            reason=_payload_text(payload, "reason", "publication eval recommended action"),
            route_target=_optional_text(
                "publication eval recommended action",
                "route_target",
                payload.get("route_target"),
            ),
            route_key_question=_optional_text(
                "publication eval recommended action",
                "route_key_question",
                payload.get("route_key_question"),
            ),
            route_rationale=_optional_text(
                "publication eval recommended action",
                "route_rationale",
                payload.get("route_rationale"),
            ),
            evidence_refs=tuple(
                _require_ref_text("publication eval recommended action", "evidence_ref", item)
                for item in _require_text_sequence(
                    "publication eval recommended action",
                    "evidence_refs",
                    payload.get("evidence_refs"),
                )
            ),
            requires_controller_decision=_payload_true(
                payload,
                "requires_controller_decision",
                "publication eval recommended action",
            ),
        )


@dataclass(frozen=True)
class PublicationEvalRecord:
    schema_version: int
    eval_id: str
    study_id: str
    quest_id: str
    emitted_at: str
    evaluation_scope: str
    charter_context_ref: PublicationEvalCharterContextRef
    runtime_context_refs: dict[str, str]
    delivery_context_refs: dict[str, str]
    verdict: PublicationEvalVerdict
    gaps: tuple[PublicationEvalGap, ...]
    recommended_actions: tuple[PublicationEvalRecommendedAction, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.schema_version, int) or isinstance(self.schema_version, bool):
            raise TypeError("publication eval record schema_version must be int")
        if self.schema_version != 1:
            raise ValueError("publication eval record schema_version must be 1")
        object.__setattr__(self, "eval_id", _require_text("publication eval record", "eval_id", self.eval_id))
        object.__setattr__(self, "study_id", _require_text("publication eval record", "study_id", self.study_id))
        object.__setattr__(self, "quest_id", _require_text("publication eval record", "quest_id", self.quest_id))
        object.__setattr__(self, "emitted_at", _require_text("publication eval record", "emitted_at", self.emitted_at))
        object.__setattr__(
            self,
            "evaluation_scope",
            _require_choice(
                "publication eval record",
                "evaluation_scope",
                self.evaluation_scope,
                frozenset({"publication"}),
            ),
        )
        object.__setattr__(
            self,
            "charter_context_ref",
            self.charter_context_ref
            if isinstance(self.charter_context_ref, PublicationEvalCharterContextRef)
            else PublicationEvalCharterContextRef.from_payload(self.charter_context_ref),
        )
        object.__setattr__(
            self,
            "runtime_context_refs",
            _require_ref_mapping(
                "runtime_context_refs",
                self.runtime_context_refs,
                required_keys=_REQUIRED_RUNTIME_CONTEXT_REF_KEYS,
            ),
        )
        object.__setattr__(
            self,
            "delivery_context_refs",
            _require_ref_mapping(
                "delivery_context_refs",
                self.delivery_context_refs,
                required_keys=_REQUIRED_DELIVERY_CONTEXT_REF_KEYS,
            ),
        )
        object.__setattr__(
            self,
            "verdict",
            self.verdict if isinstance(self.verdict, PublicationEvalVerdict) else PublicationEvalVerdict.from_payload(self.verdict),
        )
        object.__setattr__(
            self,
            "gaps",
            tuple(
                gap if isinstance(gap, PublicationEvalGap) else PublicationEvalGap.from_payload(gap)
                for gap in self.gaps
            ),
        )
        if not self.gaps:
            raise ValueError("publication eval record gaps must not be empty")
        object.__setattr__(
            self,
            "recommended_actions",
            tuple(
                action
                if isinstance(action, PublicationEvalRecommendedAction)
                else PublicationEvalRecommendedAction.from_payload(action)
                for action in self.recommended_actions
            ),
        )
        if not self.recommended_actions:
            raise ValueError("publication eval record recommended_actions must not be empty")

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "eval_id": self.eval_id,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "emitted_at": self.emitted_at,
            "evaluation_scope": self.evaluation_scope,
            "charter_context_ref": self.charter_context_ref.to_dict(),
            "runtime_context_refs": dict(self.runtime_context_refs),
            "delivery_context_refs": dict(self.delivery_context_refs),
            "verdict": self.verdict.to_dict(),
            "gaps": [gap.to_dict() for gap in self.gaps],
            "recommended_actions": [action.to_dict() for action in self.recommended_actions],
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalRecord":
        if not isinstance(payload, dict):
            raise TypeError("publication eval record payload must be a mapping")
        _reject_unknown_fields("publication eval record", payload, _RECORD_ALLOWED_FIELDS)
        return cls(
            schema_version=_payload_int(payload, "schema_version", "publication eval record"),
            eval_id=_payload_text(payload, "eval_id", "publication eval record"),
            study_id=_payload_text(payload, "study_id", "publication eval record"),
            quest_id=_payload_text(payload, "quest_id", "publication eval record"),
            emitted_at=_payload_text(payload, "emitted_at", "publication eval record"),
            evaluation_scope=_payload_text(payload, "evaluation_scope", "publication eval record"),
            charter_context_ref=PublicationEvalCharterContextRef.from_payload(
                _payload_object(payload, "charter_context_ref", "publication eval record")
            ),
            runtime_context_refs=_payload_ref_mapping(payload, "runtime_context_refs", "publication eval record"),
            delivery_context_refs=_payload_ref_mapping(payload, "delivery_context_refs", "publication eval record"),
            verdict=PublicationEvalVerdict.from_payload(_payload_object(payload, "verdict", "publication eval record")),
            gaps=tuple(
                PublicationEvalGap.from_payload(item)
                for item in _payload_object_sequence(payload, "gaps", "publication eval record")
            ),
            recommended_actions=tuple(
                PublicationEvalRecommendedAction.from_payload(item)
                for item in _payload_object_sequence(payload, "recommended_actions", "publication eval record")
            ),
        )


__all__ = [
    "PublicationEvalCharterContextRef",
    "PublicationEvalGap",
    "PublicationEvalRecommendedAction",
    "PublicationEvalRecord",
    "PublicationEvalVerdict",
]
