from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.ai_reviewer_record_contract import (
    ai_reviewer_record_has_valid_evaluation_scope,
)
from med_autoscience.publication_eval_reviewer_os import (
    validate_ai_reviewer_operating_system_trace,
)


AI_REVIEWER_PUBLICATION_EVAL_RECORD_GLOB = (
    "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json"
)
AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES = (
    Path("paper/draft.md"),
    Path("paper/manuscript.md"),
    Path("paper/build/review_manuscript.md"),
)
_STAGE_NATIVE_BODY_ROOT_RELPATH = (
    Path("artifacts")
    / "stage_outputs"
    / "_body_authority"
    / "paper_authority_cutover"
    / "current_body"
)
PROJECTION_SOURCE_REF_FIELD = "_projection_source_ref"
PROJECTION_SOURCE_KIND_FIELD = "_projection_source_kind"
PROJECTION_SOURCE_KIND_AI_REVIEWER_RECORD = "ai_reviewer_publication_eval_record"
_AI_REVIEWER_REQUIRED_QUALITY_DIMENSIONS = (
    "clinical_significance",
    "evidence_strength",
    "novelty_positioning",
    "medical_journal_prose_quality",
    "human_review_readiness",
)


def latest_current_ai_reviewer_publication_eval_record(
    *,
    study_root: str | Path,
    current_publication_eval: Mapping[str, Any] | None = None,
) -> tuple[dict[str, Any], Path] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    manuscript = current_manuscript_binding(study_root=resolved_study_root)
    if manuscript is None:
        return None
    for path in _candidate_record_paths(resolved_study_root):
        payload = _read_json_object(path)
        if payload is None or not ai_reviewer_publication_eval_record_valid(payload):
            continue
        if not record_matches_current_manuscript(record=payload, manuscript=manuscript):
            continue
        if not record_supersedes_publication_eval(record=payload, publication_eval=current_publication_eval):
            continue
        return with_projection_source(payload, path), path
    return None


def current_manuscript_binding(*, study_root: str | Path) -> dict[str, str] | None:
    root = Path(study_root).expanduser().resolve()
    for path in _current_manuscript_candidate_paths(root):
        digest = _sha256_file(path)
        if digest is not None:
            return {"ref": str(path), "digest": digest}
    return None


def _current_manuscript_candidate_paths(study_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for body_root in (study_root / _STAGE_NATIVE_BODY_ROOT_RELPATH, study_root):
        for relative_path in AI_REVIEWER_MANUSCRIPT_REF_CANDIDATES:
            candidates.append((body_root / relative_path).resolve())
    return candidates


def record_matches_current_manuscript(
    *,
    record: Mapping[str, Any],
    manuscript: Mapping[str, Any],
) -> bool:
    expected_digest = _text(manuscript.get("digest"))
    if expected_digest is None:
        return False
    currentness = _mapping(_mapping(record.get("reviewer_operating_system")).get("currentness_checks"))
    current_manuscript = _mapping(currentness.get("current_manuscript"))
    if _text(current_manuscript.get("status")) != "current":
        return False
    observed_digest = _text(current_manuscript.get("manuscript_digest"))
    if observed_digest != expected_digest:
        return False
    observed_ref = _text(current_manuscript.get("manuscript_ref"))
    expected_ref = _text(manuscript.get("ref"))
    return observed_ref in {None, expected_ref}


def ai_reviewer_publication_eval_record_valid(payload: Mapping[str, Any]) -> bool:
    provenance = _mapping(payload.get("assessment_provenance"))
    if _text(provenance.get("owner")) != "ai_reviewer":
        return False
    if _text(provenance.get("source_kind")) != "publication_eval_ai_reviewer":
        return False
    if provenance.get("ai_reviewer_required") is not False:
        return False
    if not ai_reviewer_record_has_valid_evaluation_scope(payload):
        return False
    if not _text(payload.get("eval_id")):
        return False
    quality_assessment = payload.get("quality_assessment")
    if not isinstance(quality_assessment, Mapping):
        return False
    for dimension in _AI_REVIEWER_REQUIRED_QUALITY_DIMENSIONS:
        if not isinstance(quality_assessment.get(dimension), Mapping):
            return False
    future_plan = payload.get("future_facing_limitations_plan")
    if not isinstance(future_plan, list) or not future_plan:
        return False
    reviewer_os = _mapping(payload.get("reviewer_operating_system"))
    return not validate_ai_reviewer_operating_system_trace(dict(reviewer_os))


def record_supersedes_publication_eval(
    *,
    record: Mapping[str, Any],
    publication_eval: Mapping[str, Any] | None,
) -> bool:
    if not publication_eval:
        return True
    if _publication_eval_requires_ai_reviewer_authority(publication_eval):
        return True
    if _text(record.get("eval_id")) == _text(publication_eval.get("eval_id")):
        return record_has_stronger_currentness_trace(record=record, publication_eval=publication_eval)
    record_timestamp = publication_eval_timestamp(record)
    publication_eval_timestamp_value = publication_eval_timestamp(publication_eval)
    if record_timestamp is None:
        return False
    if publication_eval_timestamp_value is None:
        return True
    return record_timestamp > publication_eval_timestamp_value


def _publication_eval_requires_ai_reviewer_authority(publication_eval: Mapping[str, Any]) -> bool:
    provenance = _mapping(publication_eval.get("assessment_provenance"))
    return (
        _text(provenance.get("owner")) == "mechanical_projection"
        and provenance.get("ai_reviewer_required") is True
        and provenance.get("mechanical_projection_used_as_quality_authority") is not True
    )


def record_has_stronger_currentness_trace(
    *,
    record: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
) -> bool:
    record_checks = _currentness_check_keys(record)
    eval_checks = _currentness_check_keys(publication_eval)
    if not record_checks or not eval_checks:
        return False
    return eval_checks < record_checks


def _currentness_check_keys(payload: Mapping[str, Any]) -> set[str]:
    currentness = _mapping(_mapping(payload.get("reviewer_operating_system")).get("currentness_checks"))
    return {key for key, value in currentness.items() if _text(key) and isinstance(value, Mapping)}


def publication_eval_timestamp(payload: Mapping[str, Any] | None) -> datetime | None:
    if not isinstance(payload, Mapping):
        return None
    for key in (
        "emitted_at",
        "generated_at",
        "completed_at",
        "finished_at",
        "updated_at",
        "created_at",
        "recorded_at",
    ):
        timestamp = _parse_timestamp(payload.get(key))
        if timestamp is not None:
            return timestamp
    return _parse_identifier_timestamp(payload.get("eval_id"))


def with_projection_source(payload: Mapping[str, Any], path: Path) -> dict[str, Any]:
    return {
        **dict(payload),
        PROJECTION_SOURCE_REF_FIELD: str(path.expanduser().resolve()),
        PROJECTION_SOURCE_KIND_FIELD: PROJECTION_SOURCE_KIND_AI_REVIEWER_RECORD,
    }


def projection_source_ref(payload: Mapping[str, Any], fallback: str | Path) -> str:
    return _text(payload.get(PROJECTION_SOURCE_REF_FIELD)) or str(fallback)


def _candidate_record_paths(study_root: Path) -> list[Path]:
    return sorted(
        (path.resolve() for path in study_root.glob(AI_REVIEWER_PUBLICATION_EVAL_RECORD_GLOB) if path.is_file()),
        key=lambda path: path.name,
        reverse=True,
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _sha256_file(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def _parse_identifier_timestamp(value: object) -> datetime | None:
    text = _text(value)
    if text is None or "::" not in text:
        return None
    for part in reversed(text.split("::")):
        timestamp = _parse_timestamp(part)
        if timestamp is not None:
            return timestamp
    return None


def _parse_timestamp(value: object) -> datetime | None:
    text = _text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "latest_current_ai_reviewer_publication_eval_record",
    "projection_source_ref",
]
