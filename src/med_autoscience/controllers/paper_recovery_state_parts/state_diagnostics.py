from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    provider_admission_opl_transition_readback as _provider_admission_opl_transition_readback,
)


def clean_conditions(conditions: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        {key: value for key, value in condition.items() if value not in (None, "", [], {})}
        for condition in conditions
    ]


def provider_admission_readback(progress: Mapping[str, Any]) -> dict[str, Any]:
    for candidate in progress.get("provider_admission_candidates") or []:
        if not isinstance(candidate, Mapping):
            continue
        readback = _provider_admission_opl_transition_readback(candidate)
        if readback:
            return readback
    current_work_unit = mapping(progress.get("current_work_unit"))
    return _provider_admission_opl_transition_readback(current_work_unit)


def current_work_unit_status(current_work_unit: Mapping[str, Any]) -> str | None:
    return text(current_work_unit.get("status"))


def runtime_recovery_blocking_reason(progress: Mapping[str, Any]) -> str | None:
    runtime_health = mapping(progress.get("runtime_health_snapshot"))
    blocking_reasons = text_items(runtime_health.get("blocking_reasons"))
    if "runtime_recovery_retry_budget_exhausted" in blocking_reasons:
        return "runtime_recovery_retry_budget_exhausted"
    if text(runtime_health.get("canonical_runtime_action")) != "external_supervisor_required":
        return None
    retry_budget = int_or_none(runtime_health.get("retry_budget_remaining"))
    if retry_budget is not None and retry_budget <= 0:
        return "runtime_recovery_retry_budget_exhausted"
    return None


def int_or_none(value: object) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def has_running_provider_attempt(
    progress: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any],
) -> bool:
    if current_work_unit_status(current_work_unit) == "running_provider_attempt":
        return True
    envelope = mapping(progress.get("current_execution_envelope"))
    return text(envelope.get("state_kind")) == "running_provider_attempt"


def study_id(progress: Mapping[str, Any]) -> str | None:
    return text(progress.get("study_id")) or text(mapping(progress.get("current_work_unit")).get("study_id"))


def single_text_item(value: Any) -> str | None:
    items = text_items(value)
    if len(items) == 1:
        return items[0]
    return None


def obligation_identity(
    *,
    blocker_reason: str | None,
    fingerprint: str | None,
    current_work_unit: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
) -> str:
    if blocker_reason is not None:
        return blocker_reason
    if fingerprint is not None:
        return fingerprint
    return short_hash(
        {
            "phase": current_work_unit_status(current_work_unit),
            "action_type": action_type,
            "work_unit_id": work_unit_id,
        }
    )


def short_hash(payload: Mapping[str, Any]) -> str:
    digest = hashlib.sha256(repr(sorted(payload.items())).encode("utf-8")).hexdigest()
    return f"sha256:{digest[:16]}"


def mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    value = value.strip()
    return value or None


def first_text(*values: object) -> str | None:
    for value in values:
        if item := text(value):
            return item
    return None


def text_items(value: object) -> list[str]:
    if isinstance(value, str):
        item = value.strip()
        return [item] if item else []
    if not isinstance(value, list | tuple | set):
        return []
    return [item for value_item in value if (item := text(value_item)) is not None]


__all__ = [
    "clean_conditions",
    "current_work_unit_status",
    "first_text",
    "has_running_provider_attempt",
    "int_or_none",
    "mapping",
    "obligation_identity",
    "provider_admission_readback",
    "runtime_recovery_blocking_reason",
    "short_hash",
    "single_text_item",
    "study_id",
    "text",
    "text_items",
]
