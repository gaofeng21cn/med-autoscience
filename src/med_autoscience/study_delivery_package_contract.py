from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def current_delivery_manifest_payload(*, study_root: Path) -> dict[str, Any] | None:
    root = Path(study_root).expanduser().resolve()
    manifest_path = root / "manuscript" / "delivery_manifest.json"
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, Mapping):
        return None
    manifest = dict(payload)
    if _text(manifest.get("stage")) != "submission_minimal":
        return None
    source_signature = _text(manifest.get("source_signature"))
    evaluated_signature = _text(manifest.get("evaluated_source_signature"))
    authority_signature = _text(manifest.get("authority_source_signature"))
    if (
        source_signature is None
        or source_signature != evaluated_signature
        or source_signature != authority_signature
    ):
        return None
    return manifest


def delivery_manifest_allows_directory_current_package(
    *,
    study_root: Path,
    package_root: Path,
    package_zip: Path,
) -> bool:
    root = Path(study_root).expanduser().resolve()
    payload = current_delivery_manifest_payload(study_root=root)
    if payload is None:
        return False
    surface_roles = _mapping(payload.get("surface_roles"))
    expected_root = _path_from_role(
        surface_roles.get("human_facing_current_package_root"),
        default=root / "manuscript" / "current_package",
    )
    expected_zip = _path_from_role(
        surface_roles.get("human_facing_current_package_zip"),
        default=root / "manuscript" / "current_package.zip",
    )
    return expected_root == Path(package_root).expanduser().resolve() and expected_zip == Path(package_zip).expanduser().resolve()


def delivered_package_handoff_allowed(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    verdict = _mapping(publication_eval.get("verdict"))
    quality_closure_truth = _mapping(publication_eval.get("quality_closure_truth"))
    mechanical_required = _text(provenance.get("owner")) == "mechanical_projection" and provenance.get("ai_reviewer_required") is True
    quality_assessment = _mapping(publication_eval.get("quality_assessment"))
    prose_quality = _mapping(quality_assessment.get("medical_journal_prose_quality"))
    gaps = [item for item in publication_eval.get("gaps") or [] if isinstance(item, Mapping)]
    blocking_eval = (
        _text(publication_eval.get("status")) == "blocked"
        or _text(verdict.get("overall_verdict")) == "blocked"
        or bool(publication_eval.get("blockers"))
        or _text(quality_closure_truth.get("state")) == "quality_repair_required"
        or (
            _text(provenance.get("owner")) == "ai_reviewer"
            and provenance.get("ai_reviewer_required") is False
            and _text(prose_quality.get("status")) not in {None, "ready"}
        )
        or any(_text(item.get("severity")) in {"must_fix", "blocking", "blocked"} for item in gaps)
    )
    return not mechanical_required and not blocking_eval


def _path_from_role(value: object, *, default: Path) -> Path:
    text = _text(value)
    return Path(text).expanduser().resolve() if text is not None else default.expanduser().resolve()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_delivery_manifest_payload",
    "delivery_manifest_allows_directory_current_package",
    "delivered_package_handoff_allowed",
]
