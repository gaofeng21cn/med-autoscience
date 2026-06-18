from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    has_provider_admission_opl_transition_readback as _has_opl_transition_readback,
)


MAS_TRANSITION_REQUEST_SURFACE = "mas_domain_progress_transition_request"
OPL_TRANSITION_RUNTIME_OWNER = "one-person-lab"
OPL_TRANSITION_RUNTIME_KIND = "DomainProgressTransitionRuntime"
FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS = frozenset(
    {
        "current_control_command_outbox_record",
        "opl_domain_progress_transition_command",
        "opl_domain_progress_transition_event",
        "opl_domain_progress_transition_outbox_item",
        "stage_run_identity",
        "projection_metadata",
        "read_model_generation_metadata",
    }
)


def admission_blocked_condition(
    progress: Mapping[str, Any],
    diagnostic: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not provider_admission_pending(progress) and not transition_request_pending(progress):
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
    candidates = _provider_admission_candidates(progress)
    if int(progress.get("provider_admission_pending_count") or 0) > 0 and any(
        _has_opl_transition_readback(candidate) for candidate in candidates
    ):
        return True
    current_work_unit = _mapping(progress.get("current_work_unit"))
    if (
        _current_work_unit_status(current_work_unit) == "executable_owner_action"
        and _mapping(current_work_unit.get("state")).get("provider_admission_pending") is True
        and _has_opl_transition_readback(current_work_unit)
    ):
        return True
    return any(_has_opl_transition_readback(candidate) for candidate in candidates)


def _provider_admission_candidates(progress: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    return [item for item in progress.get("provider_admission_candidates") or [] if isinstance(item, Mapping)]


def _has_opl_transition_boundary(value: Mapping[str, Any]) -> bool:
    return _has_mas_transition_request(value) or _has_opl_transition_readback(value)


def transition_request_pending(progress: Mapping[str, Any]) -> bool:
    candidates = _provider_admission_candidates(progress)
    if any(_has_mas_transition_request(candidate) for candidate in candidates):
        return True
    current_work_unit = _mapping(progress.get("current_work_unit"))
    state = _mapping(current_work_unit.get("state"))
    return bool(state.get("provider_admission_pending") is True and _has_mas_transition_request(current_work_unit))


def _has_mas_transition_request(value: Mapping[str, Any]) -> bool:
    request = _mapping(value.get("opl_domain_progress_transition_request"))
    if not request:
        request = _mapping(
            _mapping(value.get("paper_progress_policy_result")).get("opl_domain_progress_transition_request")
        )
    if not request:
        request = _mapping(_mapping(value.get("state")).get("opl_domain_progress_transition_request"))
    if not request:
        request = _mapping(
            _mapping(_mapping(value.get("state")).get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if _text(request.get("surface_kind")) != MAS_TRANSITION_REQUEST_SURFACE:
        return False
    if _text(request.get("target_runtime_owner")) != OPL_TRANSITION_RUNTIME_OWNER:
        return False
    runtime_kind = _text(request.get("target_runtime_kind")) or _text(request.get("runtime_kind"))
    if runtime_kind != OPL_TRANSITION_RUNTIME_KIND:
        return False
    if request.get("mas_can_create_opl_outbox_record") is not False:
        return False
    if any(field in request for field in FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS):
        return False
    aggregate_identity = _mapping(request.get("aggregate_identity"))
    required_identity = (
        aggregate_identity.get("aggregate_kind"),
        aggregate_identity.get("aggregate_id"),
        aggregate_identity.get("study_id"),
        aggregate_identity.get("work_unit_id"),
        request.get("idempotency_key"),
        request.get("source_generation"),
        request.get("expected_version"),
    )
    if any(_text(item) is None for item in required_identity):
        return False
    return bool(_mapping(request.get("required_postcondition")))


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
    "transition_request_pending",
]
