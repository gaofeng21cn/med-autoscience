from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import study_macro_state, study_progress, study_runtime_router
from med_autoscience.controllers import paper_authority_migration
from med_autoscience.profiles import WorkspaceProfile


def read_study_projection_inputs(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    study_root: Path,
    status_reader: Any | None = None,
    progress_reader: Any | None = None,
) -> tuple[dict[str, Any], dict[str, Any], str | None, dict[str, Any]]:
    resolved_status_reader = status_reader or study_runtime_router.study_runtime_status
    resolved_progress_reader = progress_reader or study_progress.read_study_progress
    status = resolved_status_reader(profile=profile, study_id=study_id, study_root=study_root)
    progress = resolved_progress_reader(profile=profile, study_id=study_id, study_root=study_root)
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    resolved_quest_id = _text(status_payload.get("quest_id")) or _text(progress_payload.get("quest_id"))
    publication_eval = publication_eval_payload(status_payload, progress_payload)
    return status_payload, progress_payload, resolved_quest_id, publication_eval


def attach_study_macro_state(
    *,
    study_id: str,
    status_payload: Mapping[str, Any],
    progress_payload: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    macro_state = study_macro_state.derive_study_macro_state(
        study_id=study_id,
        status=status_payload,
        progress=progress_payload,
        publication_eval=publication_eval_payload,
    )
    return dict(status_payload), {**dict(progress_payload), "study_macro_state": macro_state}


def publication_eval_payload(status: Mapping[str, Any], progress: Mapping[str, Any]) -> dict[str, Any]:
    study_root = _study_root_from(status, progress)
    if study_root is not None and paper_authority_migration.cutover_requires_ai_reviewer(study_root=study_root):
        return paper_authority_migration.cutover_publication_eval_payload(study_root=study_root) or {}
    refs = _mapping(progress.get("refs"))
    publication_eval_path = _text(refs.get("publication_eval_path"))
    if publication_eval_path is not None:
        from_path = _read_json_object(Path(publication_eval_path)) or {}
        if _text(_mapping(from_path.get("assessment_provenance")).get("owner")) == "ai_reviewer":
            return from_path
    from_status = _mapping(status.get("publication_eval"))
    if from_status:
        return from_status
    if publication_eval_path is not None:
        return _read_json_object(Path(publication_eval_path)) or {}
    return {}


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _study_root_from(status: Mapping[str, Any], progress: Mapping[str, Any]) -> Path | None:
    text = _text(status.get("study_root")) or _text(progress.get("study_root"))
    return Path(text).expanduser().resolve() if text else None


__all__ = [
    "attach_study_macro_state",
    "publication_eval_payload",
    "read_study_projection_inputs",
]
