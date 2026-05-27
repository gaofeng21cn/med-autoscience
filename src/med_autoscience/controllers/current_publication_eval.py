from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_reviewer_publication_eval_records
from med_autoscience.publication_eval_latest import (
    read_publication_eval_latest,
    stable_publication_eval_latest_path,
)


def read_current_publication_eval_for_controller(
    *,
    study_root: Path,
) -> dict[str, Any]:
    return read_current_publication_eval_with_ref(study_root=study_root)[0]


def read_current_publication_eval_with_ref(
    *,
    study_root: Path,
) -> tuple[dict[str, Any], Path]:
    resolved_study_root = Path(study_root).expanduser().resolve()
    stable_eval = read_publication_eval_latest(study_root=resolved_study_root)
    current_record = ai_reviewer_publication_eval_records.latest_current_ai_reviewer_publication_eval_record(
        study_root=resolved_study_root,
        current_publication_eval=stable_eval,
    )
    if current_record is not None:
        return current_record
    return stable_eval, stable_publication_eval_latest_path(study_root=resolved_study_root)


def publication_eval_source_ref(
    publication_eval_payload: Mapping[str, Any],
    *,
    fallback_ref: str | Path,
) -> str:
    return ai_reviewer_publication_eval_records.projection_source_ref(
        publication_eval_payload,
        Path(fallback_ref).expanduser(),
    )


__all__ = [
    "publication_eval_source_ref",
    "read_current_publication_eval_for_controller",
    "read_current_publication_eval_with_ref",
]
