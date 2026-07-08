from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .stage_outcome import (
    STAGE_OUTCOME_SURFACE,
    STAGE_OUTCOME_TASK_KIND,
    stage_outcome_for_owner_callable_receipt,
)


SURFACE = STAGE_OUTCOME_SURFACE


def stage_outcome_authority(
    *,
    study_id: str,
    action_type: str,
    dispatch_path: Path,
    dispatch: Mapping[str, Any],
    execution: Mapping[str, Any],
) -> dict[str, Any]:
    return stage_outcome_for_owner_callable_receipt(
        study_id=study_id,
        action_type=action_type,
        dispatch_path=dispatch_path,
        dispatch=dispatch,
        execution=execution,
    )


__all__ = [
    "STAGE_OUTCOME_SURFACE",
    "STAGE_OUTCOME_TASK_KIND",
    "SURFACE",
    "stage_outcome_authority",
]
