from __future__ import annotations

from typing import Any


def apply_startup_freshness_work_unit(
    *,
    publication_work_unit_payload: dict[str, Any],
    submission_minimal_refresh_requested: bool,
) -> dict[str, Any]:
    if submission_minimal_refresh_requested:
        startup_freshness_work_unit = {
            "unit_id": "submission_minimal_refresh",
            "lane": "finalize",
            "summary": "Refresh the stale submission_minimal package and current delivery bundle.",
        }
    else:
        startup_freshness_work_unit = {
            "unit_id": "submission_delivery_sync_closure",
            "lane": "controller",
            "summary": "Refresh the study delivery mirror from the current package, then replay the publication gate.",
            "control_surface": "gate_clearing_batch",
        }
    return {
        **publication_work_unit_payload,
        "next_work_unit": startup_freshness_work_unit,
        "blocking_work_units": [startup_freshness_work_unit],
        "actionability_status": "actionable",
    }
