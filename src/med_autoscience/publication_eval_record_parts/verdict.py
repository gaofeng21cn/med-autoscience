from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience.publication_eval_record_parts.validation import (
    _ALLOWED_OVERALL_VERDICTS,
    _ALLOWED_PRIMARY_CLAIM_STATUSES,
    _ALLOWED_STOP_LOSS_PRESSURES,
    _VERDICT_ALLOWED_FIELDS,
    _payload_text,
    _reject_unknown_fields,
    _require_choice,
    _require_text,
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


__all__ = ["PublicationEvalVerdict"]
