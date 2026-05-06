from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.medical_journal_style_corpus import stable_medical_journal_style_corpus_path
from med_autoscience.medical_prose_review import stable_medical_prose_review_path
from med_autoscience.medical_prose_review_request import stable_medical_prose_review_request_path


def _read_json_mapping(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _surface_ref(path: Path, *, payload: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "path": str(path),
        "present": path.exists(),
        "surface": _text(payload.get("surface")),
    }


def _publication_eval_ref(path: Path) -> dict[str, Any]:
    payload = _read_json_mapping(path)
    provenance = payload.get("provenance")
    assessment_provenance = payload.get("assessment_provenance")
    verdict = payload.get("verdict")
    return {
        **_surface_ref(path, payload=payload),
        "owner": _text((provenance or {}).get("owner")) if isinstance(provenance, Mapping) else None,
        "assessment_owner": _text((assessment_provenance or {}).get("owner"))
        if isinstance(assessment_provenance, Mapping)
        else None,
        "overall_verdict": _text((verdict or {}).get("overall_verdict")) if isinstance(verdict, Mapping) else None,
    }


def _request_authority_ref(path: Path) -> dict[str, Any]:
    payload = _read_json_mapping(path)
    style_currentness = payload.get("style_currentness")
    return {
        **_surface_ref(path, payload=payload),
        "review_owner": _text(payload.get("review_owner")),
        "request_digest": _text(payload.get("request_digest")),
        "style_version": _text((style_currentness or {}).get("style_version"))
        if isinstance(style_currentness, Mapping)
        else None,
        "style_digest": _text((style_currentness or {}).get("style_digest"))
        if isinstance(style_currentness, Mapping)
        else None,
        "currentness_status": _text((payload.get("request_currentness") or {}).get("status"))
        if isinstance(payload.get("request_currentness"), Mapping)
        else None,
    }


def _review_authority_ref(path: Path) -> dict[str, Any]:
    payload = _read_json_mapping(path)
    provenance = payload.get("assessment_provenance")
    quality = payload.get("medical_journal_prose_quality")
    style_currentness = payload.get("style_currentness")
    return {
        **_surface_ref(path, payload=payload),
        "owner": _text((provenance or {}).get("owner")) if isinstance(provenance, Mapping) else None,
        "request_digest": _text((provenance or {}).get("request_digest")) if isinstance(provenance, Mapping) else None,
        "overall_style_verdict": _text((quality or {}).get("overall_style_verdict"))
        if isinstance(quality, Mapping)
        else None,
        "style_version": _text((style_currentness or {}).get("style_version"))
        if isinstance(style_currentness, Mapping)
        else None,
        "style_digest": _text((style_currentness or {}).get("style_digest"))
        if isinstance(style_currentness, Mapping)
        else None,
        "currentness_status": _text((style_currentness or {}).get("status"))
        if isinstance(style_currentness, Mapping)
        else None,
    }


def _style_corpus_authority_ref(path: Path) -> dict[str, Any]:
    payload = _read_json_mapping(path)
    currentness = payload.get("style_currentness")
    return {
        **_surface_ref(path, payload=payload),
        "corpus_id": _text(payload.get("corpus_id")),
        "style_version": _text(payload.get("style_version")),
        "source_set_id": _text(payload.get("source_set_id")),
        "style_digest": _text(payload.get("style_digest")),
        "currentness_status": _text((currentness or {}).get("status")) if isinstance(currentness, Mapping) else None,
    }


def _style_authority_currentness(
    *,
    style_corpus: Mapping[str, Any],
    prose_review_request: Mapping[str, Any],
    medical_prose_review: Mapping[str, Any],
) -> str:
    style_digest = _text(style_corpus.get("style_digest"))
    if not style_digest:
        return "missing_style_corpus"
    request_digest = _text(prose_review_request.get("style_digest"))
    review_digest = _text(medical_prose_review.get("style_digest"))
    if not request_digest or not review_digest:
        return "missing_prose_authority"
    if request_digest != style_digest or review_digest != style_digest:
        return "style_digest_mismatch"
    if (
        style_corpus.get("currentness_status") == "current"
        and prose_review_request.get("currentness_status") == "current"
        and medical_prose_review.get("currentness_status") == "current"
    ):
        return "current"
    return "currentness_incomplete"


def build_delivery_authority_ref_block(*, study_root: Path) -> dict[str, Any]:
    publication_eval_path = study_root / "artifacts" / "publication_eval" / "latest.json"
    style_corpus_path = stable_medical_journal_style_corpus_path(study_root=study_root)
    prose_review_request_path = stable_medical_prose_review_request_path(study_root=study_root)
    prose_review_path = stable_medical_prose_review_path(study_root=study_root)
    style_corpus = _style_corpus_authority_ref(style_corpus_path)
    prose_review_request = _request_authority_ref(prose_review_request_path)
    medical_prose_review = _review_authority_ref(prose_review_path)
    return {
        "publication_refs": {
            "publication_eval_latest": str(publication_eval_path) if publication_eval_path.exists() else None,
            "medical_journal_style_corpus": str(style_corpus_path) if style_corpus_path.exists() else None,
            "medical_prose_review_request": str(prose_review_request_path)
            if prose_review_request_path.exists()
            else None,
            "medical_prose_review": str(prose_review_path) if prose_review_path.exists() else None,
        },
        "quality_authority_refs": {
            "publication_eval_latest": _publication_eval_ref(publication_eval_path),
            "medical_prose_review_request": prose_review_request,
            "medical_prose_review": medical_prose_review,
            "derived_delivery_surface_can_authorize_quality": False,
        },
        "style_authority_refs": {
            "style_corpus": style_corpus,
            "medical_prose_review_request": prose_review_request,
            "medical_prose_review": medical_prose_review,
            "currentness_status": _style_authority_currentness(
                style_corpus=style_corpus,
                prose_review_request=prose_review_request,
                medical_prose_review=medical_prose_review,
            ),
            "package_requires_current_style_authority": True,
        },
    }
