from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import ai_first_action_dispatch, ai_first_feedback


def attach_ai_first_runtime_projection(
    payload: dict[str, Any],
    *,
    study_root: Path,
    generated_at: str,
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

    action_dispatch_ledger = ai_first_action_dispatch.build_action_dispatch_projection(
        feedback_state=feedback_state,
        existing_ledger=ai_first_action_dispatch.read_action_dispatch_ledger(study_root=study_root),
        dispatch_owner="study_progress",
        status="open",
        observed_at=generated_at,
    )
    action_dispatch_ledger["study_root"] = str(study_root)
    action_dispatch_ledger["path"] = str(
        ai_first_action_dispatch.stable_action_dispatch_ledger_path(study_root=study_root)
    )
    action_dispatch_ledger["materialized"] = ai_first_action_dispatch.read_action_dispatch_ledger(
        study_root=study_root
    ) is not None
    action_lifecycle = ai_first_action_dispatch.build_operator_action_lifecycle(
        feedback_state=feedback_state,
        existing_ledger=action_dispatch_ledger,
        dispatch_owner="study_progress",
        observed_at=generated_at,
    )

    payload["ai_first_feedback_state"] = feedback_state
    payload["ai_first_action_dispatch_ledger"] = action_dispatch_ledger
    payload["ai_first_action_lifecycle"] = {
        "surface": "ai_first_action_lifecycle_projection",
        "authority": "operations_governance_only",
        "primary_action": dict((action_lifecycle.get("primary_action") or {})),
        "counts": dict(action_dispatch_ledger.get("counts") or {}),
        "open_action_count": (
            int((action_dispatch_ledger.get("counts") or {}).get("open") or 0)
            + int((action_dispatch_ledger.get("counts") or {}).get("accepted") or 0)
            + int((action_dispatch_ledger.get("counts") or {}).get("in_progress") or 0)
            + int((action_dispatch_ledger.get("counts") or {}).get("blocked") or 0)
        ),
        "closed_action_count": int((action_dispatch_ledger.get("counts") or {}).get("closed") or 0),
        "authority_contract": {
            "lifecycle_can_authorize_quality": False,
            "lifecycle_can_authorize_finalize": False,
            "lifecycle_can_authorize_submission": False,
            "lifecycle_can_mutate_runtime": False,
        },
    }
    payload["ai_first_action_dispatch_lifecycle"] = action_lifecycle
    refs = dict(payload.get("refs") or {})
    refs["ai_first_feedback_ledger_path"] = feedback_state["ledger"]["path"]
    refs["ai_first_action_dispatch_ledger_path"] = action_dispatch_ledger["path"]
    payload["refs"] = refs
    return payload
