from __future__ import annotations

from typing import Any

from .publication_runtime import _publication_eval_specificity_request
from .shared import _timestamp_is_newer


def task_intake_override_superseded_by_gate_specificity(
    *,
    task_intake_progress_override: dict[str, Any] | None,
    latest_task_intake_payload: dict[str, Any] | None,
    publication_eval_payload: dict[str, Any] | None,
) -> bool:
    if not task_intake_progress_override:
        return False
    if _publication_eval_specificity_request(publication_eval_payload) is None:
        return False
    return _timestamp_is_newer(
        (publication_eval_payload or {}).get("emitted_at"),
        (latest_task_intake_payload or {}).get("emitted_at"),
    )


__all__ = ["task_intake_override_superseded_by_gate_specificity"]
