from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.publication_eval_latest import (
    canonicalize_ai_reviewer_publication_eval_record,
    materialize_ai_reviewer_publication_eval_latest,
)
from med_autoscience.publication_eval_record import PublicationEvalRecord

from . import domain_status_projection

__all__ = [
    "materialize_ai_reviewer_publication_eval",
    "materialize_ai_reviewer_publication_eval_record",
]


AI_REVIEWER_RESPONSE_RECORD_DIR = Path("artifacts") / "publication_eval" / "ai_reviewer_responses"


def _mapping_payload(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return dict(value)
    to_dict = getattr(value, "to_dict", None)
    if callable(to_dict):
        payload = to_dict()
        if isinstance(payload, Mapping):
            return dict(payload)
    raise TypeError("study runtime status must be a mapping or expose to_dict()")


def _optional_text(value: object) -> str | None:
    text = str(value).strip() if value is not None else ""
    return text or None


def _resolved_study_root(status_payload: Mapping[str, Any]) -> Path:
    raw_study_root = _optional_text(status_payload.get("study_root"))
    if raw_study_root is None:
        raise ValueError("Unable to resolve study_root for AI reviewer publication eval")
    return Path(raw_study_root).expanduser().resolve()


def _record_timestamp(record_payload: Mapping[str, Any]) -> str:
    emitted_at = _optional_text(record_payload.get("emitted_at"))
    if emitted_at:
        try:
            parsed = datetime.fromisoformat(emitted_at.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is not None:
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            return parsed.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _materialize_ai_reviewer_publication_eval_record(
    *,
    study_root: Path,
    record: PublicationEvalRecord,
) -> Path:
    payload = record.to_dict()
    record_dir = study_root / AI_REVIEWER_RESPONSE_RECORD_DIR
    record_dir.mkdir(parents=True, exist_ok=True)
    record_path = record_dir / f"{_record_timestamp(payload)}_publication_eval_record.json"
    record_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return record_path.resolve()


def _normalize_publication_eval_record(record: PublicationEvalRecord | dict[str, Any]) -> PublicationEvalRecord:
    return record if isinstance(record, PublicationEvalRecord) else PublicationEvalRecord.from_payload(record)


def materialize_ai_reviewer_publication_eval_record(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
    entry_mode: str | None,
    record: PublicationEvalRecord | dict[str, Any],
    source: str,
) -> dict[str, Any]:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")

    status_payload = _mapping_payload(
        domain_status_projection.progress_projection(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
        )
    )
    resolved_study_root = _resolved_study_root(status_payload)
    normalized_record = _normalize_publication_eval_record(record)
    record_path = _materialize_ai_reviewer_publication_eval_record(
        study_root=resolved_study_root,
        record=normalized_record,
    )
    record_payload = normalized_record.to_dict()
    resolved_study_id = (
        _optional_text(status_payload.get("study_id"))
        or _optional_text(record_payload.get("study_id"))
        or resolved_study_root.name
    )
    return {
        "status": "materialized",
        "source": source,
        "study_id": resolved_study_id,
        "quest_id": _optional_text(status_payload.get("quest_id")) or _optional_text(record_payload.get("quest_id")),
        "eval_id": record_payload["eval_id"],
        "publication_eval_record_ref": str(record_path),
        "publication_eval_record_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "assessment_owner": "ai_reviewer",
        "publication_eval_surface": "not_written",
    }


def materialize_ai_reviewer_publication_eval(
    *,
    profile: Any,
    study_id: str | None,
    study_root: Path | None,
    entry_mode: str | None,
    record: PublicationEvalRecord | dict[str, Any],
    source: str,
) -> dict[str, Any]:
    if bool(study_id) == bool(study_root):
        raise ValueError("Specify exactly one of study_id or study_root")

    status_payload = _mapping_payload(
        domain_status_projection.progress_projection(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
        )
    )
    resolved_study_root = _resolved_study_root(status_payload)
    normalized_record = canonicalize_ai_reviewer_publication_eval_record(
        _normalize_publication_eval_record(record)
    )
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=normalized_record,
    )
    record_path = _materialize_ai_reviewer_publication_eval_record(
        study_root=resolved_study_root,
        record=normalized_record,
    )
    record_payload = normalized_record.to_dict()
    resolved_study_id = (
        _optional_text(status_payload.get("study_id"))
        or _optional_text(record_payload.get("study_id"))
        or resolved_study_root.name
    )

    return {
        "status": "materialized",
        "source": source,
        "study_id": resolved_study_id,
        "quest_id": _optional_text(status_payload.get("quest_id")) or _optional_text(record_payload.get("quest_id")),
        "eval_id": materialized["eval_id"],
        "artifact_path": materialized["artifact_path"],
        "publication_eval_record_ref": str(record_path),
        "publication_eval_record_surface": "artifacts/publication_eval/ai_reviewer_responses/*_publication_eval_record.json",
        "assessment_owner": "ai_reviewer",
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
    }
