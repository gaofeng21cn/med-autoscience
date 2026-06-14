from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def admission_blocked_condition(
    progress: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not provider_admission_pending(progress):
        return None
    runtime_health = _mapping(progress.get("runtime_health_snapshot"))
    if (
        _text(runtime_health.get("canonical_runtime_action")) == "external_supervisor_required"
        or (
            runtime_health.get("retry_budget_remaining") is not None
            and int(runtime_health.get("retry_budget_remaining") or 0) <= 0
        )
    ):
        return {
            "condition": "provider_admission_pending_without_startable_dispatch",
            "reason": "runtime_recovery_retry_budget_exhausted",
        }
    explicit_pending_count = int(progress.get("provider_admission_pending_count") or 0)
    explicit_pending_candidates = [
        item for item in progress.get("provider_admission_candidates") or [] if isinstance(item, Mapping)
    ]
    diagnostic_pending_count = int(diagnostic.get("provider_admission_pending_count") or 0)
    if explicit_pending_count <= 0 and not explicit_pending_candidates and diagnostic_pending_count <= 0:
        if diagnostic.get("will_start_llm") is False and _text(diagnostic.get("action_class")) == "observe_only":
            return {
                "condition": "provider_admission_pending_without_startable_dispatch",
                "reason": "dhd_report_observe_only",
            }
        if diagnostic.get("will_start_llm") is False and int(diagnostic.get("codex_dispatch_count") or 0) == 0:
            return {
                "condition": "provider_admission_pending_without_startable_dispatch",
                "reason": "dhd_report_no_codex_dispatch",
            }
    return None


def provider_admission_pending(progress: Mapping[str, Any]) -> bool:
    if int(progress.get("provider_admission_pending_count") or 0) > 0:
        return True
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _current_work_unit_status(current_work_unit) == "executable_owner_action"
        and _mapping(current_work_unit.get("state")).get("provider_admission_pending") is True
    ):
        return True
    return bool([item for item in progress.get("provider_admission_candidates") or [] if isinstance(item, Mapping)])


def _current_work_unit_status(work_unit: Mapping[str, Any]) -> str | None:
    return _text(work_unit.get("status")) or _text(_mapping(work_unit.get("state")).get("state_kind"))


def _mapping(value: Any) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None


__all__ = [
    "admission_blocked_condition",
    "provider_admission_pending",
]
