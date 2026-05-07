from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience.publication_eval_record_parts.validation import (
    _ALLOWED_GAP_SEVERITIES,
    _ALLOWED_GAP_TYPES,
    _GAP_ALLOWED_FIELDS,
    _payload_text,
    _reject_unknown_fields,
    _require_choice,
    _require_ref_text,
    _require_text,
    _require_text_sequence,
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


__all__ = ["PublicationEvalGap"]
