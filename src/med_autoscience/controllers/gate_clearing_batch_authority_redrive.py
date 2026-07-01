from __future__ import annotations

from typing import Any

from med_autoscience.controllers import gate_clearing_batch_execution


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _latest_batch_selected_work_unit_id(latest_batch: dict[str, Any]) -> str | None:
    selected = latest_batch.get("selected_publication_work_unit")
    if isinstance(selected, dict):
        return _non_empty_text(selected.get("unit_id"))
    lifecycle = latest_batch.get("publication_work_unit_lifecycle")
    if isinstance(lifecycle, dict):
        work_unit = lifecycle.get("work_unit")
        if isinstance(work_unit, dict):
            return _non_empty_text(work_unit.get("unit_id"))
    return None


def _same_authority_sync_identity(
    *,
    latest_batch: dict[str, Any],
    source_eval_id: str | None,
    current_work_unit_fingerprint: str | None,
    evaluated_source_signature: str | None,
    authority_source_signature: str | None,
    allow_mechanical_eval_id_drift: bool = False,
) -> bool:
    if (
        source_eval_id
        and not allow_mechanical_eval_id_drift
        and _non_empty_text(latest_batch.get("source_eval_id")) != source_eval_id
    ):
        return False
    latest_fingerprint = _non_empty_text(latest_batch.get("work_unit_fingerprint"))
    if latest_fingerprint is None:
        currentness = latest_batch.get("work_unit_currentness")
        if isinstance(currentness, dict):
            latest_fingerprint = _non_empty_text(currentness.get("current_work_unit_fingerprint"))
    if current_work_unit_fingerprint and latest_fingerprint != current_work_unit_fingerprint:
        return False
    latest_evaluated = _non_empty_text(latest_batch.get("evaluated_source_signature"))
    if evaluated_source_signature and latest_evaluated != evaluated_source_signature:
        return False
    latest_authority = _non_empty_text(latest_batch.get("authority_source_signature"))
    authority_settled_after_retry = (
        latest_authority is None
        and authority_source_signature is not None
        and evaluated_source_signature == authority_source_signature
    )
    if authority_source_signature and latest_authority != authority_source_signature and not authority_settled_after_retry:
        return False
    return True


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


def authority_settle_delivery_redrive_matches_current(
    *,
    latest_batch: dict[str, Any],
    source_eval_id: str | None,
    current_work_unit_fingerprint: str | None,
    evaluated_source_signature: str | None,
    authority_source_signature: str | None,
    can_sync_study_delivery: bool,
    allow_mechanical_eval_id_drift: bool = False,
) -> bool:
    if not can_sync_study_delivery:
        return False
    if not previous_delivery_sync_awaited_authority_settle(latest_batch):
        return False
    if _latest_batch_selected_work_unit_id(latest_batch) not in {
        "submission_authority_sync_closure",
        "submission_minimal_refresh",
        "submission_delivery_sync_closure",
    }:
        return False
    return _same_authority_sync_identity(
        latest_batch=latest_batch,
        source_eval_id=source_eval_id,
        current_work_unit_fingerprint=current_work_unit_fingerprint,
        evaluated_source_signature=evaluated_source_signature,
        authority_source_signature=authority_source_signature,
        allow_mechanical_eval_id_drift=allow_mechanical_eval_id_drift,
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
