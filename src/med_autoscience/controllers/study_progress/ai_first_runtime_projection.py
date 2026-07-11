from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_first_feedback


def attach_ai_first_runtime_projection(
    payload: dict[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    feedback_ledger = ai_first_feedback.read_feedback_ledger(study_root=study_root)
    feedback_state = ai_first_feedback.build_ai_first_feedback_state(
        progress_snapshot=payload,
        feedback_ledger=feedback_ledger,
    )
    feedback_state["ledger"] = {
        "surface": ai_first_feedback.LEDGER_SURFACE,
        "path": str(ai_first_feedback.stable_feedback_ledger_path(study_root=study_root)),
        "open_event_count": int((feedback_ledger or {}).get("open_event_count") or 0),
        "closed_event_count": int((feedback_ledger or {}).get("closed_event_count") or 0),
        "materialized": feedback_ledger is not None,
    }

    payload["ai_first_feedback_state"] = feedback_state
    refs = dict(payload.get("refs") or {})
    refs["ai_first_feedback_ledger_path"] = feedback_state["ledger"]["path"]
    payload["refs"] = refs
    return payload
