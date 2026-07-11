from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile

from . import existing_projection_refresh as _existing_projection_refresh


def _refresh_existing_projection_user_visible_status(payload: dict[str, Any]) -> dict[str, Any]:
    return _existing_projection_refresh.refresh_existing_projection_user_visible_status(payload)


def _refresh_existing_projection_batch_followthroughs(
    *,
    payload: dict[str, Any],
    status: dict[str, Any],
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_id: str,
    study_root: Path,
    publication_eval_payload: dict[str, Any] | None,
) -> dict[str, Any]:
    return _existing_projection_refresh.refresh_existing_projection_batch_followthroughs(
        payload=payload,
        status=status,
        profile=profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )




_current_redrive_top_level_next_action = _existing_projection_refresh.current_redrive_top_level_next_action


_current_gate_clearing_eval_ids = _existing_projection_refresh.current_gate_clearing_eval_ids


__all__ = [
    "_current_gate_clearing_eval_ids",
    "_current_redrive_top_level_next_action",
    "_refresh_existing_projection_batch_followthroughs",
    "_refresh_existing_projection_user_visible_status",
]
