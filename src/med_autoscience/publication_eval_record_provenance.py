from __future__ import annotations

from dataclasses import dataclass
from typing import Any


_ASSESSMENT_PROVENANCE_ALLOWED_FIELDS = frozenset(
    {
        "owner",
        "source_kind",
        "policy_id",
        "source_refs",
        "ai_reviewer_required",
    }
)
_ALLOWED_ASSESSMENT_PROVENANCE_OWNERS = frozenset({"mechanical_projection", "ai_reviewer"})


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


def _payload_text(payload: dict[str, Any], field_name: str, label: str) -> str:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    return _require_text(label, field_name, payload.get(field_name))


def _payload_bool(payload: dict[str, Any], field_name: str, label: str) -> bool:
    if field_name not in payload:
        raise ValueError(f"{label} payload missing {field_name}")
    value = payload.get(field_name)
    if not isinstance(value, bool):
        raise TypeError(f"{label} {field_name} must be bool")
    return value


def _require_text_sequence(label: str, field_name: str, value: Any) -> tuple[str, ...]:
    if not isinstance(value, (list, tuple)):
        raise ValueError(f"{label} {field_name} must be a list")
    normalized = tuple(
        _require_text(label, field_name[:-1] if field_name.endswith("s") else field_name, item)
        for item in value
    )
    if not normalized:
        raise ValueError(f"{label} {field_name} must not be empty")
    return normalized


@dataclass(frozen=True)
class PublicationEvalAssessmentProvenance:
    owner: str
    source_kind: str
    policy_id: str
    source_refs: tuple[str, ...]
    ai_reviewer_required: bool

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "owner",
            _require_choice(
                "publication eval assessment provenance",
                "owner",
                self.owner,
                _ALLOWED_ASSESSMENT_PROVENANCE_OWNERS,
            ),
        )
        object.__setattr__(
            self,
            "source_kind",
            _require_text("publication eval assessment provenance", "source_kind", self.source_kind),
        )
        object.__setattr__(
            self,
            "policy_id",
            _require_text("publication eval assessment provenance", "policy_id", self.policy_id),
        )
        object.__setattr__(
            self,
            "source_refs",
            tuple(
                _require_ref_text("publication eval assessment provenance", "source_ref", item)
                for item in self.source_refs
            ),
        )
        if not self.source_refs:
            raise ValueError("publication eval assessment provenance source_refs must not be empty")
        if not isinstance(self.ai_reviewer_required, bool):
            raise TypeError("publication eval assessment provenance ai_reviewer_required must be bool")
        if self.owner == "ai_reviewer" and self.ai_reviewer_required:
            raise ValueError("ai_reviewer publication eval provenance cannot require another AI reviewer")
        if self.owner == "mechanical_projection" and not self.ai_reviewer_required:
            raise ValueError("mechanical publication eval projection must require AI reviewer judgment")

    def to_dict(self) -> dict[str, object]:
        return {
            "owner": self.owner,
            "source_kind": self.source_kind,
            "policy_id": self.policy_id,
            "source_refs": list(self.source_refs),
            "ai_reviewer_required": self.ai_reviewer_required,
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalAssessmentProvenance":
        if not isinstance(payload, dict):
            raise TypeError("publication eval assessment provenance payload must be a mapping")
        _reject_unknown_fields(
            "publication eval assessment provenance",
            payload,
            _ASSESSMENT_PROVENANCE_ALLOWED_FIELDS,
        )
        return cls(
            owner=_payload_text(payload, "owner", "publication eval assessment provenance"),
            source_kind=_payload_text(payload, "source_kind", "publication eval assessment provenance"),
            policy_id=_payload_text(payload, "policy_id", "publication eval assessment provenance"),
            source_refs=tuple(
                _require_ref_text("publication eval assessment provenance", "source_ref", item)
                for item in _require_text_sequence(
                    "publication eval assessment provenance",
                    "source_refs",
                    payload.get("source_refs"),
                )
            ),
            ai_reviewer_required=_payload_bool(
                payload,
                "ai_reviewer_required",
                "publication eval assessment provenance",
            ),
        )


__all__ = ["PublicationEvalAssessmentProvenance"]
