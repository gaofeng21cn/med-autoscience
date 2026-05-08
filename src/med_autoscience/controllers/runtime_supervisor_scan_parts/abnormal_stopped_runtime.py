from __future__ import annotations

from collections.abc import Mapping
from typing import Any


ABNORMAL_STOPPED_RUNTIME_REASONS = {
    "quest_stopped_by_controller_guard",
}

RESUME_REQUIRED_DECISIONS = {
    "resume",
    "continue",
    "relaunch",
}

REPAIR_REASON = "abnormal_stopped_runtime_resume_required"
FAILED_REPAIR_REASON = "failed_quest_runtime_relaunch_required"
LIVE_QUEST_STATUSES = {"active", "running"}
PAUSED_QUEST_STATUSES = {"paused"}
FAILED_QUEST_STATUSES = {"failed"}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _active_run_id(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    supervision = _mapping(progress.get("supervision"))
    runtime_liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    for value in (
        supervision.get("active_run_id"),
        status.get("active_run_id"),
        runtime_liveness.get("active_run_id"),
        runtime_audit.get("active_run_id"),
    ):
        if text := _text(value):
            return text
    return None


def _worker_running(status: Mapping[str, Any]) -> bool:
    runtime_liveness = _mapping(status.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    if runtime_audit.get("worker_running") is False:
        return False
    if runtime_liveness.get("worker_running") is False:
        return False
    return bool(runtime_audit.get("worker_running") or runtime_liveness.get("worker_running"))


def _auto_completion_parked(progress: Mapping[str, Any]) -> bool:
    auto_runtime_parked = _mapping(progress.get("auto_runtime_parked"))
    return auto_runtime_parked.get("parked") is True or auto_runtime_parked.get("auto_execution_complete") is True


def _manual_or_completed_parked(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    auto_runtime_parked = _mapping(status.get("auto_runtime_parked")) or _mapping(progress.get("auto_runtime_parked"))
    parked_state = _text(auto_runtime_parked.get("parked_state"))
    if parked_state in {
        "package_ready_handoff",
        "publishability_stop_loss",
        "manual_hold",
        "external_metadata_pending",
        "waiting_user_decision",
        "external_input_pending",
    }:
        return True
    if auto_runtime_parked.get("auto_execution_complete") is True:
        return True
    macro_state = _mapping(status.get("study_macro_state")) or _mapping(progress.get("study_macro_state"))
    return _text(macro_state.get("writer_state")) == "parked" and _text(macro_state.get("reason")) in {
        "user_stop",
        "stop_loss",
        "external_info",
    }


def _continuation_allows_platform_redrive(status: Mapping[str, Any]) -> bool:
    continuation_state = _mapping(status.get("continuation_state"))
    policy = _text(continuation_state.get("continuation_policy"))
    if policy in {"wait_for_user_or_resume", "manual", "manual_hold"}:
        return False
    return True


def _failed_non_resumable_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) not in FAILED_QUEST_STATUSES:
        return False
    if _active_run_id(status, progress) or _worker_running(status):
        return False
    if _manual_or_completed_parked(status, progress):
        return False
    if not _continuation_allows_platform_redrive(status):
        return False
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    observed_state = _mapping(runtime_health.get("observed_quest_state"))
    blocking_reasons = {
        item
        for source in (
            status.get("blocking_reasons"),
            runtime_health.get("blocking_reasons"),
            _mapping(status.get("control_plane_snapshot")).get("blocking_reasons"),
            _mapping(_mapping(status.get("control_plane_snapshot")).get("dispatch_gate")).get("blocking_reasons"),
            _mapping(progress.get("control_plane_snapshot")).get("blocking_reasons"),
            progress.get("current_blockers"),
        )
        for item in _string_items(source)
    }
    reason = _text(status.get("reason"))
    return bool(
        reason == "quest_exists_with_non_resumable_state"
        or _text(observed_state.get("reason")) == "quest_exists_with_non_resumable_state"
        or "runtime_recovery_retry_budget_exhausted" in blocking_reasons
        or _text(runtime_health.get("attempt_state")) == "escalated"
        or runtime_health.get("retry_budget_remaining") == 0
    )


def _live_status_no_worker_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) not in LIVE_QUEST_STATUSES:
        return False
    if _active_run_id(status, progress) or _worker_running(status):
        return False
    if _auto_completion_parked(progress):
        return False
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    blocking_reasons = {
        item
        for source in (
            status.get("blocking_reasons"),
            runtime_health.get("blocking_reasons"),
            _mapping(status.get("control_plane_snapshot")).get("blocking_reasons"),
            _mapping(_mapping(status.get("control_plane_snapshot")).get("dispatch_gate")).get("blocking_reasons"),
            _mapping(progress.get("control_plane_snapshot")).get("blocking_reasons"),
            progress.get("current_blockers"),
        )
        for item in _string_items(source)
    }
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    return bool(
        "runtime_recovery_retry_budget_exhausted" in blocking_reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or attempt_state == "escalated"
        or (
            runtime_health.get("retry_budget_remaining") == 0
            and (
                attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
                or canonical_runtime_action in {
                    "recover_runtime",
                    "probe_runtime",
                    "relaunch_runtime",
                    "external_supervisor_required",
                }
            )
        )
    )


def _paused_resume_no_worker_repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) not in PAUSED_QUEST_STATUSES:
        return False
    if _active_run_id(status, progress) or _worker_running(status):
        return False
    if _auto_completion_parked(progress):
        return False
    decision = _text(status.get("decision")) or _text(status.get("runtime_decision"))
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    blocking_reasons = {
        item
        for source in (
            status.get("blocking_reasons"),
            runtime_health.get("blocking_reasons"),
            _mapping(status.get("control_plane_snapshot")).get("blocking_reasons"),
            _mapping(_mapping(status.get("control_plane_snapshot")).get("dispatch_gate")).get("blocking_reasons"),
            _mapping(progress.get("control_plane_snapshot")).get("blocking_reasons"),
            progress.get("current_blockers"),
        )
        for item in _string_items(source)
    }
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    return bool(
        decision in RESUME_REQUIRED_DECISIONS
        and (
            "runtime_recovery_retry_budget_exhausted" in blocking_reasons
            or attempt_state == "escalated"
            or canonical_runtime_action in {
                "recover_runtime",
                "probe_runtime",
                "relaunch_runtime",
                "external_supervisor_required",
            }
        )
    )


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, (list, tuple, set)):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def repair_kind(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    if _failed_non_resumable_repair_required(status, progress):
        return "failed_non_resumable_relaunch"
    if _live_status_no_worker_repair_required(status, progress):
        return "active_runtime_no_live_worker_relaunch"
    if _paused_resume_no_worker_repair_required(status, progress):
        return "abnormal_stopped_runtime_relaunch"
    if _text(status.get("quest_status")) != "stopped":
        return None
    if _active_run_id(status, progress) or _worker_running(status):
        return None
    if _auto_completion_parked(progress):
        return None
    decision = _text(status.get("decision")) or _text(status.get("runtime_decision"))
    reason = _text(status.get("reason")) or _text(status.get("runtime_reason"))
    current_stage = _text(progress.get("current_stage"))
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    if (
        decision in RESUME_REQUIRED_DECISIONS
        or reason in ABNORMAL_STOPPED_RUNTIME_REASONS
        or current_stage in {"managed_runtime_recovering", "managed_runtime_degraded", "managed_runtime_escalated"}
        or attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
        or canonical_runtime_action in {"recover_runtime", "probe_runtime", "relaunch_runtime"}
    ):
        return "abnormal_stopped_runtime_relaunch"
    return None


def repair_reason(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    kind = repair_kind(status, progress)
    if kind == "abnormal_stopped_runtime_relaunch":
        return REPAIR_REASON
    if kind == "failed_non_resumable_relaunch":
        return FAILED_REPAIR_REASON
    return None


def repair_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    return repair_kind(status, progress) is not None
