from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from med_autoscience.publication_eval_record_parts import (
    PublicationEvalCharterContextRef,
    PublicationEvalGap,
    PublicationEvalQualityAssessment,
    PublicationEvalRecommendedAction,
    PublicationEvalVerdict,
)
from med_autoscience.publication_eval_record_parts.quality import PublicationEvalQualityDimension
from med_autoscience.publication_eval_record_parts.validation import (
    _RECORD_ALLOWED_FIELDS,
    _REQUIRED_DELIVERY_CONTEXT_REF_KEYS,
    _REQUIRED_RUNTIME_CONTEXT_REF_KEYS,
    _dedupe_ref_texts,
    _payload_int,
    _payload_object,
    _payload_object_sequence,
    _payload_ref_mapping,
    _payload_text,
    _optional_authority_boundary,
    _reject_unknown_fields,
    _require_choice,
    _require_ref_mapping,
    _require_text,
)
from med_autoscience.publication_eval_record_provenance import PublicationEvalAssessmentProvenance


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
    assessment_provenance: PublicationEvalAssessmentProvenance | None = None
    authority_boundary: dict[str, bool] | None = None
    quality_assessment: PublicationEvalQualityAssessment | None = None
    reviewer_operating_system: dict[str, Any] | None = None

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
        if self.assessment_provenance is None:
            object.__setattr__(
                self,
                "assessment_provenance",
                PublicationEvalAssessmentProvenance(
                    owner="mechanical_projection",
                    source_kind="legacy_publication_eval_projection",
                    policy_id="publication_gate_projection_v1",
                    source_refs=_dedupe_ref_texts(
                        self.charter_context_ref.ref,
                        self.runtime_context_refs,
                        self.delivery_context_refs,
                    ),
                    ai_reviewer_required=True,
                ),
            )
        else:
            object.__setattr__(
                self,
                "assessment_provenance",
                (
                    self.assessment_provenance
                    if isinstance(self.assessment_provenance, PublicationEvalAssessmentProvenance)
                    else PublicationEvalAssessmentProvenance.from_payload(self.assessment_provenance)
                ),
            )
        if self.authority_boundary is not None:
            object.__setattr__(
                self,
                "authority_boundary",
                _optional_authority_boundary(self.authority_boundary),
            )
        object.__setattr__(
            self,
            "verdict",
            self.verdict
            if isinstance(self.verdict, PublicationEvalVerdict)
            else PublicationEvalVerdict.from_payload(self.verdict),
        )
        if self.quality_assessment is not None:
            object.__setattr__(
                self,
                "quality_assessment",
                (
                    self.quality_assessment
                    if isinstance(self.quality_assessment, PublicationEvalQualityAssessment)
                    else PublicationEvalQualityAssessment.from_payload(self.quality_assessment)
                ),
            )
        if self.reviewer_operating_system is not None and not isinstance(self.reviewer_operating_system, dict):
            raise TypeError("publication eval record reviewer_operating_system must be a mapping")
        if self.reviewer_operating_system is not None:
            object.__setattr__(self, "reviewer_operating_system", dict(self.reviewer_operating_system))
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
        payload = {
            "schema_version": self.schema_version,
            "eval_id": self.eval_id,
            "study_id": self.study_id,
            "quest_id": self.quest_id,
            "emitted_at": self.emitted_at,
            "evaluation_scope": self.evaluation_scope,
            "charter_context_ref": self.charter_context_ref.to_dict(),
            "runtime_context_refs": dict(self.runtime_context_refs),
            "delivery_context_refs": dict(self.delivery_context_refs),
            "assessment_provenance": self.assessment_provenance.to_dict(),
            "verdict": self.verdict.to_dict(),
            "gaps": [gap.to_dict() for gap in self.gaps],
            "recommended_actions": [action.to_dict() for action in self.recommended_actions],
        }
        if isinstance(self.authority_boundary, dict):
            payload["authority_boundary"] = dict(self.authority_boundary)
        if isinstance(self.quality_assessment, PublicationEvalQualityAssessment):
            payload["quality_assessment"] = self.quality_assessment.to_dict()
        if isinstance(self.reviewer_operating_system, dict):
            payload["reviewer_operating_system"] = self.reviewer_operating_system
        return payload

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
            assessment_provenance=(
                PublicationEvalAssessmentProvenance.from_payload(
                    _payload_object(payload, "assessment_provenance", "publication eval record")
                )
                if "assessment_provenance" in payload
                else None
            ),
            authority_boundary=(
                _optional_authority_boundary(_payload_object(payload, "authority_boundary", "publication eval record"))
                if "authority_boundary" in payload
                else None
            ),
            verdict=PublicationEvalVerdict.from_payload(_payload_object(payload, "verdict", "publication eval record")),
            quality_assessment=(
                PublicationEvalQualityAssessment.from_payload(
                    _payload_object(payload, "quality_assessment", "publication eval record")
                )
                if "quality_assessment" in payload
                else None
            ),
            reviewer_operating_system=_payload_object(payload, "reviewer_operating_system", "publication eval record")
            if "reviewer_operating_system" in payload
            else None,
            gaps=tuple(
                PublicationEvalGap.from_payload(item)
                for item in _payload_object_sequence(payload, "gaps", "publication eval record")
            ),
            recommended_actions=tuple(
                PublicationEvalRecommendedAction.from_payload(item)
                for item in _payload_object_sequence(payload, "recommended_actions", "publication eval record")
            ),
        )
