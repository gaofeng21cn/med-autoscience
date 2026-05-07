from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience.publication_eval_record_parts.validation import (
    _CHARTER_CONTEXT_REF_ALLOWED_FIELDS,
    _payload_text,
    _reject_unknown_fields,
    _require_ref_text,
    _require_text,
)


@dataclass(frozen=True)
class PublicationEvalCharterContextRef:
    ref: str
    charter_id: str
    publication_objective: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "ref", _require_ref_text("publication eval charter context ref", "ref", self.ref))
        object.__setattr__(
            self,
            "charter_id",
            _require_text("publication eval charter context ref", "charter_id", self.charter_id),
        )
        object.__setattr__(
            self,
            "publication_objective",
            _require_text(
                "publication eval charter context ref",
                "publication_objective",
                self.publication_objective,
            ),
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


__all__ = ["PublicationEvalCharterContextRef"]
