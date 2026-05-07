from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience import publication_eval_specificity_targets as _specificity_targets
from med_autoscience.publication_eval_record_parts.validation import (
    _ALLOWED_ACTION_PRIORITIES,
    _ALLOWED_ACTION_TYPES,
    _ALLOWED_ROUTE_TARGETS,
    _RECOMMENDED_ACTION_ALLOWED_FIELDS,
    _ROUTE_CONTRACT_ACTION_TYPES,
    _optional_publication_work_unit,
    _optional_publication_work_units,
    _optional_text,
    _payload_text,
    _payload_true,
    _reject_unknown_fields,
    _require_choice,
    _require_ref_text,
    _require_text,
    _require_text_sequence,
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
    work_unit_fingerprint: str | None = None
    blocking_work_units: tuple[dict[str, str], ...] = ()
    next_work_unit: dict[str, str] | None = None
    specificity_targets: tuple[object, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "action_id",
            _require_text("publication eval recommended action", "action_id", self.action_id),
        )
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
        object.__setattr__(
            self,
            "reason",
            _require_text("publication eval recommended action", "reason", self.reason),
        )
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
        object.__setattr__(
            self,
            "work_unit_fingerprint",
            _optional_text(
                "publication eval recommended action",
                "work_unit_fingerprint",
                self.work_unit_fingerprint,
            ),
        )
        object.__setattr__(
            self,
            "blocking_work_units",
            tuple(
                work_unit
                for item in self.blocking_work_units
                if (work_unit := _optional_publication_work_unit(item)) is not None
            ),
        )
        object.__setattr__(self, "next_work_unit", _optional_publication_work_unit(self.next_work_unit))
        object.__setattr__(
            self,
            "specificity_targets",
            _specificity_targets.normalize_publication_eval_specificity_targets(list(self.specificity_targets)),
        )

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
        if self.work_unit_fingerprint is not None:
            payload["work_unit_fingerprint"] = self.work_unit_fingerprint
        if self.blocking_work_units:
            payload["blocking_work_units"] = list(self.blocking_work_units)
        if self.next_work_unit is not None:
            payload["next_work_unit"] = self.next_work_unit
        if self.specificity_targets:
            payload["specificity_targets"] = _specificity_targets.to_payload_list(self.specificity_targets)
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
            work_unit_fingerprint=_optional_text(
                "publication eval recommended action",
                "work_unit_fingerprint",
                payload.get("work_unit_fingerprint"),
            ),
            blocking_work_units=_optional_publication_work_units(payload.get("blocking_work_units")),
            next_work_unit=_optional_publication_work_unit(payload.get("next_work_unit")),
            specificity_targets=_specificity_targets.normalize_publication_eval_specificity_targets(
                payload.get("specificity_targets")
            ),
        )


__all__ = ["PublicationEvalRecommendedAction"]
