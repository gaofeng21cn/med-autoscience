from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.medical_journal_style_corpus import stable_medical_journal_style_corpus_path
from med_autoscience.medical_manuscript_blueprint import stable_medical_manuscript_blueprint_path
from med_autoscience.medical_prose_review import stable_medical_prose_review_path
from med_autoscience.medical_prose_review_request import stable_medical_prose_review_request_path
from med_autoscience.retrospective_medical_prose_audit import (
    stable_retrospective_medical_prose_audit_path,
    stable_retrospective_medical_prose_audit_request_path,
)

from .shared import _mapping_copy, _non_empty_text, _read_json_object


def medical_writing_quality_surface_status(*, study_root: Path) -> dict[str, Any]:
    blueprint_path = stable_medical_manuscript_blueprint_path(study_root=study_root)
    style_corpus_path = stable_medical_journal_style_corpus_path(study_root=study_root)
    prose_review_request_path = stable_medical_prose_review_request_path(study_root=study_root)
    prose_review_path = stable_medical_prose_review_path(study_root=study_root)
    retrospective_request_path = stable_retrospective_medical_prose_audit_request_path(study_root=study_root)
    retrospective_audit_path = stable_retrospective_medical_prose_audit_path(study_root=study_root)

    blueprint_payload = _read_json_object(blueprint_path)
    corpus_payload = _read_json_object(style_corpus_path)
    request_payload = _read_json_object(prose_review_request_path)
    review_payload = _read_json_object(prose_review_path)
    retrospective_request_payload = _read_json_object(retrospective_request_path)
    retrospective_audit_payload = _read_json_object(retrospective_audit_path)
    review_quality = (
        _mapping_copy((review_payload or {}).get("medical_journal_prose_quality"))
        if review_payload is not None
        else {}
    )
    review_provenance = (
        _mapping_copy((review_payload or {}).get("assessment_provenance"))
        if review_payload is not None
        else {}
    )
    retrospective_samples = (
        list(retrospective_audit_payload.get("samples") or [])
        if isinstance(retrospective_audit_payload, dict)
        else []
    )
    return {
        "surface_kind": "medical_writing_quality_surfaces",
        "blueprint": {
            "present": blueprint_path.exists(),
            "valid": bool(blueprint_payload and blueprint_payload.get("surface") == "medical_manuscript_blueprint"),
            "path": str(blueprint_path),
            "argument_sequence": list((blueprint_payload or {}).get("argument_sequence") or []),
        },
        "style_corpus": {
            "present": style_corpus_path.exists(),
            "valid": bool(corpus_payload and corpus_payload.get("surface") == "medical_journal_style_corpus"),
            "path": str(style_corpus_path),
            "corpus_id": _non_empty_text((corpus_payload or {}).get("corpus_id")),
        },
        "prose_review_request": {
            "present": prose_review_request_path.exists(),
            "valid": bool(request_payload and request_payload.get("surface") == "medical_prose_review_request"),
            "path": str(prose_review_request_path),
            "review_owner": _non_empty_text((request_payload or {}).get("review_owner")),
        },
        "prose_review": {
            "present": prose_review_path.exists(),
            "valid": bool(
                review_payload
                and review_payload.get("surface") == "medical_prose_review"
                and review_provenance.get("owner") == "ai_reviewer"
            ),
            "path": str(prose_review_path),
            "owner": _non_empty_text(review_provenance.get("owner")),
            "verdict": _non_empty_text(review_quality.get("overall_style_verdict")),
            "summary": _non_empty_text(review_quality.get("summary")),
        },
        "retrospective_audit_request": {
            "present": retrospective_request_path.exists(),
            "valid": bool(
                retrospective_request_payload
                and retrospective_request_payload.get("surface") == "retrospective_medical_prose_audit_request"
            ),
            "path": str(retrospective_request_path),
        },
        "retrospective_audit": {
            "present": retrospective_audit_path.exists(),
            "valid": bool(
                retrospective_audit_payload
                and retrospective_audit_payload.get("surface") == "retrospective_medical_prose_audit"
                and _mapping_copy(retrospective_audit_payload.get("assessment_provenance")).get("owner") == "ai_reviewer"
            ),
            "path": str(retrospective_audit_path),
            "sample_count": len([item for item in retrospective_samples if isinstance(item, dict)]),
            "sample_ids": [
                _non_empty_text(item.get("sample_id"))
                for item in retrospective_samples
                if isinstance(item, dict) and _non_empty_text(item.get("sample_id")) is not None
            ],
        },
    }


__all__ = ["medical_writing_quality_surface_status"]
