from __future__ import annotations

from typing import Any

from med_autoscience.controllers import gate_clearing_batch_execution


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def previous_delivery_sync_awaited_authority_settle(latest_batch: dict[str, Any]) -> bool:
    sync_result = gate_clearing_batch_execution.latest_unit_result(
        latest_batch,
        unit_id="sync_submission_minimal_delivery",
    )
    if not isinstance(sync_result, dict):
        return False
    if _non_empty_text(sync_result.get("status")) != "skipped_authority_not_settled":
        return False
    return (
        gate_clearing_batch_execution.latest_unit_success_status(
            latest_batch,
            unit_id="create_submission_minimal_package",
        )
        is not None
    )


def analysis_work_unit_authority_closure_unit_ids(
    *,
    selected_publication_work_unit: dict[str, Any] | None,
    submission_minimal_refresh_requested: bool,
    repair_units: list[Any],
) -> tuple[str, ...]:
    return ()
