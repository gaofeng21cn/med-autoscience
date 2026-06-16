from __future__ import annotations

from collections.abc import Mapping
from typing import Any


CANONICAL_NEXT_ACTIONS = (
    "request_opl_runtime_owner",
    "run_domain_work_unit",
    "wait_human",
    "opl_runtime_handoff",
    "sync_package",
    "complete",
)


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _next_work_unit(payload: Mapping[str, Any]) -> Mapping[str, Any]:
    direct = _mapping(payload.get("next_work_unit"))
    if direct:
        return direct
    gate_summary = _mapping(payload.get("gate_blocker_summary"))
    direct = _mapping(gate_summary.get("next_work_unit"))
    if direct:
        return direct
    wakeup = _mapping(payload.get("domain_health_diagnostic_wakeup_dedupe_summary"))
    return _mapping(wakeup.get("next_work_unit"))


def _has_package_sync_work(payload: Mapping[str, Any], next_work_unit: Mapping[str, Any]) -> bool:
    unit_id = _text(next_work_unit.get("unit_id"))
    if unit_id in {"submission_minimal_refresh", "submission_delivery_sync_closure"}:
        return True
    package_currentness = _mapping(payload.get("package_currentness"))
    return _text(package_currentness.get("status")) in {"stale", "missing"}


def reconcile_next_action(
    *,
    current_state: str,
    state_spec: Mapping[str, Any],
    profile_payload: Mapping[str, Any],
    auto_runtime_parked: Mapping[str, Any],
    runtime_failure_classification: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _mapping(profile_payload)
    next_work_unit = _next_work_unit(payload)
    runtime_health = _mapping(payload.get("runtime_health_snapshot"))
    runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    reason = _text(payload.get("reason")) or _text(payload.get("runtime_reason"))
    failure_action = _text(runtime_failure_classification.get("action_mode"))

    if current_state == "blocked_opl_runtime" or failure_action in {
        "opl_runtime_handoff_required",
        "platform_startup_backoff_and_recheck",
    }:
        action = "opl_runtime_handoff"
    elif current_state == "blocked_external" or current_state == "blocked_human":
        action = "wait_human"
    elif runtime_action == "recover_runtime" or reason == "quest_marked_running_but_no_live_session" or current_state in {
        "no_live",
        "recovering",
        "stalled",
    }:
        action = "request_opl_runtime_owner"
    elif next_work_unit:
        action = "sync_package" if _has_package_sync_work(payload, next_work_unit) else "run_domain_work_unit"
    elif bool(auto_runtime_parked.get("parked")):
        action = "wait_human"
    elif current_state == "live":
        action = "complete" if _text(payload.get("status")) == "complete" else "run_domain_work_unit"
    else:
        action = "run_domain_work_unit"

    return {
        "surface": "domain_next_action_projection",
        "schema_version": 1,
        "projection_role": "body_free_diagnostic_projection",
        "authority": False,
        "can_authorize_provider_admission": False,
        "can_create_opl_command_event_or_outbox": False,
        "can_start_worker": False,
        "canonical_next_action_is_authority": False,
        "runtime_health_action_is_authority": False,
        "opl_readback_required_for_execution": action in {"request_opl_runtime_owner", "run_domain_work_unit"},
        "opl_current_control_or_stage_run_readback_required": action
        in {"request_opl_runtime_owner", "run_domain_work_unit"},
        "mas_private_attempt_loop_forbidden": True,
        "canonical_next_action": action,
        "owner": state_spec.get("owner"),
        "human_gate_required": bool(state_spec.get("human_gate_required")),
        "quality_gate_relaxation_allowed": False,
        "opl_stage_attempt_required": action == "request_opl_runtime_owner",
        "work_unit_pending": bool(next_work_unit),
        "next_work_unit": dict(next_work_unit) if next_work_unit else None,
        "allowed_actions": list(CANONICAL_NEXT_ACTIONS),
    }
