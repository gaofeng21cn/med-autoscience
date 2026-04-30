from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class ControlPlaneFactCase:
    case_id: str
    payload: dict[str, Any]
    supervisor_tick_audit: dict[str, Any] | None
    expected: dict[str, Any]


def stale_continuation_run_id_case() -> ControlPlaneFactCase:
    return ControlPlaneFactCase(
        case_id="stale_continuation_run_id",
        payload={
            "quest_status": "active",
            "runtime_liveness_status": "unknown",
            "reason": "quest_marked_running_but_no_live_session",
            "continuation_state": {
                "quest_status": "running",
                "active_run_id": "run-stale-continuation",
            },
        },
        supervisor_tick_audit={"status": "stale"},
        expected={
            "active_run_id": "run-stale-continuation",
            "active_run_id_source": "continuation_state.active_run_id",
            "strict_live": False,
            "missing_live_session": True,
            "recovery_pending": True,
        },
    )


def active_run_projection_case() -> ControlPlaneFactCase:
    return ControlPlaneFactCase(
        case_id="active_run_projection",
        payload={
            "quest_status": "running",
            "runtime_liveness_audit": {
                "status": "live",
                "active_run_id": "run-live-projected",
                "runtime_audit": {
                    "status": "live",
                    "active_run_id": "run-live-projected",
                    "worker_running": True,
                    "worker_pending": False,
                    "stop_requested": False,
                },
            },
            "autonomous_runtime_notice": {"browser_url": "http://127.0.0.1:20999"},
        },
        supervisor_tick_audit={"status": "fresh"},
        expected={
            "active_run_id": "run-live-projected",
            "active_run_id_source": "runtime_liveness_audit.active_run_id",
            "runtime_liveness_status": "live",
            "strict_live": True,
            "worker_running": True,
            "worker_pending": False,
            "stop_requested": False,
            "recovery_pending": False,
        },
    )


def stale_gate_authority_case() -> ControlPlaneFactCase:
    return ControlPlaneFactCase(
        case_id="stale_gate_authority",
        payload={
            "quest_status": "running",
            "decision": "continue",
            "reason": "stale_submission_minimal_authority",
            "runtime_liveness_status": "live",
            "runtime_liveness_audit": {
                "status": "live",
                "runtime_audit": {
                    "active_run_id": "run-authority",
                    "worker_running": True,
                },
            },
            "publication_supervisor_state": {
                "supervisor_phase": "publishability_gate_blocked",
                "current_required_action": "return_to_publishability_gate",
            },
        },
        supervisor_tick_audit={"status": "fresh"},
        expected={
            "active_run_id": "run-authority",
            "active_run_id_source": "runtime_audit.active_run_id",
            "strict_live": True,
            "missing_live_session": False,
            "recovery_pending": False,
        },
    )


def fact_cases() -> tuple[ControlPlaneFactCase, ...]:
    return (
        stale_continuation_run_id_case(),
        active_run_projection_case(),
        stale_gate_authority_case(),
    )


def supervisor_lightweight_payload() -> dict[str, Any]:
    return {
        "quest_status": "running",
        "runtime_liveness_status": "unknown",
        "execution_owner_guard": {
            "supervisor_only": True,
            "guard_reason": "live_managed_runtime",
            "active_run_id": "run-lightweight-live",
        },
        "autonomous_runtime_notice": {
            "notification_reason": "detected_existing_live_managed_runtime",
        },
        "continuation_state": {
            "quest_status": "running",
            "active_run_id": "run-lightweight-live",
        },
    }


def package_handoff_parked_status() -> dict[str, Any]:
    return {
        "quest_status": "stopped",
        "decision": "blocked",
        "reason": "quest_parked_on_unchanged_finalize_state",
        "publication_supervisor_state": {
            "supervisor_phase": "bundle_stage_ready",
            "current_required_action": "complete_bundle_stage",
            "bundle_tasks_downstream_only": False,
        },
    }


def external_upstream_parked_status() -> dict[str, Any]:
    return {
        "quest_status": "stopped",
        "decision": "blocked",
        "reason": "provider_rate_limit",
        "runtime_failure_classification": {
            "blocker_class": "external_upstream_unavailable",
            "action_mode": "external_fix_required",
            "requires_human_gate": True,
        },
    }


def same_fingerprint_status_payload() -> dict[str, Any]:
    return {
        "study_id": "001-risk",
        "quest_id": "quest-001",
        "quest_status": "running",
        "decision": "continue",
        "reason": "stale_submission_minimal_authority",
        "runtime_liveness_status": "live",
        "runtime_liveness_audit": {
            "status": "live",
            "active_run_id": "run-live-fingerprint",
            "runtime_audit": {
                "active_run_id": "run-live-fingerprint",
                "worker_running": True,
            },
        },
        "publication_supervisor_state": {
            "supervisor_phase": "publishability_gate_blocked",
            "current_required_action": "return_to_publishability_gate",
        },
    }
