from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from .event_projection import text


def allowed_controller_actions(
    *,
    canonical_runtime_action: str,
    base_allowed_actions: Iterable[str],
) -> list[str]:
    if canonical_runtime_action in {"recover_runtime", "relaunch_runtime", "probe_runtime_liveness"}:
        return [
            "read_runtime_status",
            "refresh_runtime_liveness",
            "recover_runtime",
            "relaunch_runtime",
            "open_monitoring_entry",
        ]
    if canonical_runtime_action in {"escalate_runtime", "external_supervisor_required"}:
        return ["read_runtime_status", "open_monitoring_entry", "manual_runtime_review"]
    return list(base_allowed_actions)


def diagnostic_hint_contract(
    *,
    canonical_runtime_action: str,
    attempt_state: str,
    retry_budget_remaining: int,
    opl_observability_readback_boundary: Mapping[str, Any],
    attempt_ledger_authority_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_runtime_health_diagnostic_hint_contract",
        "opl_observability_readback_boundary": dict(opl_observability_readback_boundary),
        "hint_only": True,
        "canonical_runtime_action_hint": canonical_runtime_action,
        "attempt_state_hint": attempt_state,
        "retry_budget_remaining_hint": retry_budget_remaining,
        "attempt_count_hint_is_lifecycle_authority": False,
        "failed_attempt_count_hint_is_lifecycle_authority": False,
        "canonical_runtime_action_is_authority": False,
        "allowed_controller_action_hints_are_authority": False,
        "runtime_liveness_hint_is_authority": False,
        "attempt_state_hint_is_lifecycle_authority": False,
        "retry_budget_hint_is_lifecycle_authority": False,
        "provider_admission_authority": False,
        "can_generate_next_action_authority": False,
        "can_create_worker_attempt": False,
        "can_retry_or_dead_letter": False,
        "can_authorize_running_progress": False,
        "opl_observability_readback_required": True,
        "opl_current_control_or_stage_run_readback_required": True,
        "mas_private_attempt_loop_forbidden": True,
        "attempt_ledger_authority_boundary": dict(attempt_ledger_authority_boundary),
    }


def diagnostic_hints(
    *,
    canonical_runtime_action: str,
    attempt_state: str,
    retry_budget_remaining: int,
    allowed_controller_action_hints: Iterable[str],
    opl_observability_readback_boundary: Mapping[str, Any],
    attempt_ledger_authority_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "runtime_health_diagnostic_hints",
        "diagnostic_only": True,
        "authority": False,
        "readiness_authority": False,
        "runtime_currentness_authority": False,
        "lifecycle_authority": False,
        "runtime_action_hint": canonical_runtime_action,
        "attempt_state_hint": attempt_state,
        "retry_budget_remaining_hint": retry_budget_remaining,
        "allowed_controller_action_hints": list(allowed_controller_action_hints),
        "field_authority": {
            "runtime_action_hint": False,
            "attempt_state_hint": False,
            "retry_budget_remaining_hint": False,
            "allowed_controller_action_hints": False,
            "worker_liveness_state": False,
        },
        "attempt_ledger_authority_boundary": dict(attempt_ledger_authority_boundary),
        "opl_observability_readback_boundary": dict(opl_observability_readback_boundary),
    }


def legacy_runtime_health_field_contract(
    *,
    canonical_runtime_action: str,
    attempt_state: str,
    retry_budget_remaining: int,
    worker_liveness_state: Mapping[str, Any],
    opl_observability_readback_boundary: Mapping[str, Any],
    attempt_ledger_authority_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "runtime_health_legacy_field_compatibility_contract",
        "compatibility_only": True,
        "diagnostic_only": True,
        "authority": False,
        "runtime_currentness_authority": False,
        "lifecycle_authority": False,
        "readiness_authority": False,
        "provider_admission_authority": False,
        "runtime_action_hint": canonical_runtime_action,
        "attempt_state_hint": attempt_state,
        "retry_budget_remaining_hint": retry_budget_remaining,
        "worker_liveness_state_hint": dict(worker_liveness_state),
        "field_authority": {
            "canonical_runtime_action": False,
            "attempt_state": False,
            "retry_budget_remaining": False,
            "worker_liveness_state": False,
            "allowed_controller_actions": False,
        },
        "replacement_namespace": "diagnostic_hints",
        "opl_observability_readback_boundary": dict(opl_observability_readback_boundary),
        "attempt_ledger_authority_boundary": dict(attempt_ledger_authority_boundary),
    }


def projection_metadata(
    *,
    dominant_event: Mapping[str, Any] | None,
    source_signature: str | None,
    opl_observability_readback_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    derived_from_event_id = text(dominant_event.get("event_id")) if dominant_event is not None else None
    return {
        "surface_kind": "runtime_health_diagnostic_projection_metadata",
        "opl_observability_readback_boundary": dict(opl_observability_readback_boundary),
        "authority": False,
        "fixed_point_runtime_owner": "one-person-lab",
        "derived_from_event_id": derived_from_event_id,
        "observed_generation": source_signature,
        "lag_status": "current" if derived_from_event_id is not None and source_signature is not None else "empty",
        "runtime_health_epoch_is_currentness_authority": False,
        "diagnostic_publisher_only": True,
    }
