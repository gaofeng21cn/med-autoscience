from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.publication_eval_latest import materialize_ai_reviewer_publication_eval_latest
from med_autoscience.publication_eval_record import PublicationEvalRecord

from . import study_runtime_router

__all__ = ["materialize_ai_reviewer_publication_eval"]


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
        study_runtime_router.study_runtime_status(
            profile=profile,
            study_id=study_id,
            study_root=study_root,
            entry_mode=entry_mode,
        )
    )
    resolved_study_root = _resolved_study_root(status_payload)
    materialized = materialize_ai_reviewer_publication_eval_latest(
        study_root=resolved_study_root,
        record=record,
    )
    record_payload = record.to_dict() if isinstance(record, PublicationEvalRecord) else dict(record)
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
        "assessment_owner": "ai_reviewer",
        "publication_eval_surface": "artifacts/publication_eval/latest.json",
    }
