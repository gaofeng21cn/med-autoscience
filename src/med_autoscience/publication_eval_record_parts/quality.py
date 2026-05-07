from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience.publication_eval_record_parts.validation import (
    _ALLOWED_QUALITY_DIMENSION_STATUSES,
    _QUALITY_ASSESSMENT_ALLOWED_FIELDS,
    _QUALITY_DIMENSION_ALLOWED_FIELDS,
    _optional_text,
    _payload_object,
    _payload_text,
    _reject_unknown_fields,
    _require_choice,
    _require_ref_text,
    _require_text,
    _require_text_sequence,
)


@dataclass(frozen=True)
class PublicationEvalQualityDimension:
    status: str
    summary: str
    evidence_refs: tuple[str, ...]
    reviewer_reason: str | None = None
    reviewer_revision_advice: str | None = None
    reviewer_next_round_focus: str | None = None

    def __post_init__(self) -> None:
        object.__setattr__(
            self,
            "status",
            _require_choice(
                "publication eval quality dimension",
                "status",
                self.status,
                _ALLOWED_QUALITY_DIMENSION_STATUSES,
            ),
        )
        object.__setattr__(
            self,
            "summary",
            _require_text("publication eval quality dimension", "summary", self.summary),
        )
        object.__setattr__(
            self,
            "evidence_refs",
            tuple(
                _require_ref_text("publication eval quality dimension", "evidence_ref", item)
                for item in self.evidence_refs
            ),
        )
        object.__setattr__(
            self,
            "reviewer_reason",
            _optional_text("publication eval quality dimension", "reviewer_reason", self.reviewer_reason),
        )
        object.__setattr__(
            self,
            "reviewer_revision_advice",
            _optional_text(
                "publication eval quality dimension",
                "reviewer_revision_advice",
                self.reviewer_revision_advice,
            ),
        )
        object.__setattr__(
            self,
            "reviewer_next_round_focus",
            _optional_text(
                "publication eval quality dimension",
                "reviewer_next_round_focus",
                self.reviewer_next_round_focus,
            ),
        )
        if not self.evidence_refs:
            raise ValueError("publication eval quality dimension evidence_refs must not be empty")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "status": self.status,
            "summary": self.summary,
            "evidence_refs": list(self.evidence_refs),
        }
        if self.reviewer_reason is not None:
            payload["reviewer_reason"] = self.reviewer_reason
        if self.reviewer_revision_advice is not None:
            payload["reviewer_revision_advice"] = self.reviewer_revision_advice
        if self.reviewer_next_round_focus is not None:
            payload["reviewer_next_round_focus"] = self.reviewer_next_round_focus
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalQualityDimension":
        if not isinstance(payload, dict):
            raise TypeError("publication eval quality dimension payload must be a mapping")
        _reject_unknown_fields(
            "publication eval quality dimension",
            payload,
            _QUALITY_DIMENSION_ALLOWED_FIELDS,
        )
        return cls(
            status=_payload_text(payload, "status", "publication eval quality dimension"),
            summary=_payload_text(payload, "summary", "publication eval quality dimension"),
            evidence_refs=tuple(
                _require_ref_text("publication eval quality dimension", "evidence_ref", item)
                for item in _require_text_sequence(
                    "publication eval quality dimension",
                    "evidence_refs",
                    payload.get("evidence_refs"),
                )
            ),
            reviewer_reason=_optional_text(
                "publication eval quality dimension",
                "reviewer_reason",
                payload.get("reviewer_reason"),
            ),
            reviewer_revision_advice=_optional_text(
                "publication eval quality dimension",
                "reviewer_revision_advice",
                payload.get("reviewer_revision_advice"),
            ),
            reviewer_next_round_focus=_optional_text(
                "publication eval quality dimension",
                "reviewer_next_round_focus",
                payload.get("reviewer_next_round_focus"),
            ),
        )


@dataclass(frozen=True)
class PublicationEvalQualityAssessment:
    clinical_significance: PublicationEvalQualityDimension
    evidence_strength: PublicationEvalQualityDimension
    novelty_positioning: PublicationEvalQualityDimension
    human_review_readiness: PublicationEvalQualityDimension
    medical_journal_prose_quality: PublicationEvalQualityDimension | None = None

    def __post_init__(self) -> None:
        for field_name in (
            "clinical_significance",
            "evidence_strength",
            "novelty_positioning",
            "human_review_readiness",
        ):
            value = getattr(self, field_name)
            object.__setattr__(
                self,
                field_name,
                value
                if isinstance(value, PublicationEvalQualityDimension)
                else PublicationEvalQualityDimension.from_payload(value),
            )
        if self.medical_journal_prose_quality is not None:
            object.__setattr__(
                self,
                "medical_journal_prose_quality",
                (
                    self.medical_journal_prose_quality
                    if isinstance(self.medical_journal_prose_quality, PublicationEvalQualityDimension)
                    else PublicationEvalQualityDimension.from_payload(self.medical_journal_prose_quality)
                ),
            )

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "clinical_significance": self.clinical_significance.to_dict(),
            "evidence_strength": self.evidence_strength.to_dict(),
            "novelty_positioning": self.novelty_positioning.to_dict(),
        }
        if self.medical_journal_prose_quality is not None:
            payload["medical_journal_prose_quality"] = self.medical_journal_prose_quality.to_dict()
        payload["human_review_readiness"] = self.human_review_readiness.to_dict()
        return payload

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "PublicationEvalQualityAssessment":
        if not isinstance(payload, dict):
            raise TypeError("publication eval quality assessment payload must be a mapping")
        _reject_unknown_fields(
            "publication eval quality assessment",
            payload,
            _QUALITY_ASSESSMENT_ALLOWED_FIELDS,
        )
        return cls(
            clinical_significance=PublicationEvalQualityDimension.from_payload(
                _payload_object(payload, "clinical_significance", "publication eval quality assessment")
            ),
            evidence_strength=PublicationEvalQualityDimension.from_payload(
                _payload_object(payload, "evidence_strength", "publication eval quality assessment")
            ),
            novelty_positioning=PublicationEvalQualityDimension.from_payload(
                _payload_object(payload, "novelty_positioning", "publication eval quality assessment")
            ),
            medical_journal_prose_quality=(
                PublicationEvalQualityDimension.from_payload(
                    _payload_object(payload, "medical_journal_prose_quality", "publication eval quality assessment")
                )
                if "medical_journal_prose_quality" in payload
                else None
            ),
            human_review_readiness=PublicationEvalQualityDimension.from_payload(
                _payload_object(payload, "human_review_readiness", "publication eval quality assessment")
            ),
        )


__all__ = ["PublicationEvalQualityAssessment", "PublicationEvalQualityDimension"]
