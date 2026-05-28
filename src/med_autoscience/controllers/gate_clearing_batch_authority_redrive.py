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


def authority_settle_delivery_redrive_requested(
    *,
    latest_batch: dict[str, Any],
    study_delivery_status: str,
    bundle_stage_repair: bool,
    submission_minimal_refresh_requested: bool,
    submission_minimal_core_outputs_missing: bool,
    can_sync_study_delivery: bool,
) -> bool:
    if not previous_delivery_sync_awaited_authority_settle(latest_batch):
        return False
    if not can_sync_study_delivery:
        return False
    if study_delivery_status.startswith("stale"):
        return True
    return (
        bundle_stage_repair
        and submission_minimal_refresh_requested
        and not submission_minimal_core_outputs_missing
    )


def analysis_work_unit_authority_closure_unit_ids(
    *,
    selected_publication_work_unit: dict[str, Any] | None,
    submission_minimal_refresh_requested: bool,
    repair_units: list[Any],
) -> tuple[str, ...]:
    return ()
