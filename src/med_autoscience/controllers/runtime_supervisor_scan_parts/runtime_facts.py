from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.runtime_supervisor_scan_parts import abnormal_stopped_runtime
from med_autoscience.controllers.runtime_supervisor_scan_parts import completion_evidence
from med_autoscience.controllers.runtime_supervisor_scan_parts import current_truth_owner
from med_autoscience.controllers.runtime_supervisor_scan_parts import gate_specificity as gate_specificity_part
from med_autoscience.controllers.runtime_supervisor_scan_parts.owner_tokens import owner_token
from med_autoscience.controllers.runtime_supervisor_scan_parts import parked_truth


def active_run_id(status: Mapping[str, Any], progress: Mapping[str, Any]) -> str | None:
    supervision = _mapping(progress.get("supervision"))
    runtime_audit = _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit"))
    for value in (
        supervision.get("active_run_id"),
        status.get("active_run_id"),
        _mapping(status.get("runtime_liveness_audit")).get("active_run_id"),
        runtime_audit.get("active_run_id"),
    ):
        if text := _text(value):
            return text
    return None


def worker_running(status: Mapping[str, Any]) -> bool:
    runtime_audit = _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit"))
    if runtime_audit.get("worker_running") is False:
        return False
    if _mapping(status.get("runtime_liveness_audit")).get("worker_running") is False:
        return False
    return bool(runtime_audit.get("worker_running") or _mapping(status.get("runtime_liveness_audit")).get("worker_running"))


def blocking_reasons(status: Mapping[str, Any], progress: Mapping[str, Any]) -> list[str]:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    control_plane = _mapping(status.get("control_plane_snapshot"))
    progress_control = _mapping(progress.get("control_plane_snapshot"))
    return list(
        dict.fromkeys(
            [
                *_string_items(status.get("blocking_reasons")),
                *_string_items(runtime_health.get("blocking_reasons")),
                *_string_items(control_plane.get("blocking_reasons")),
                *_string_items(_mapping(control_plane.get("dispatch_gate")).get("blocking_reasons")),
                *_string_items(progress_control.get("blocking_reasons")),
                *_string_items(progress.get("current_blockers")),
            ]
        )
    )


def retry_exhausted(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    reasons = set(blocking_reasons(status, progress))
    attempt_state = _text(runtime_health.get("attempt_state"))
    canonical_runtime_action = _text(runtime_health.get("canonical_runtime_action"))
    quest_status = _text(status.get("quest_status"))
    zero_budget_in_recovery_context = runtime_health.get("retry_budget_remaining") == 0 and (
        quest_status in {"active", "running"}
        or attempt_state in {"recovering", "retrying", "probing", "relaunching", "escalated"}
        or canonical_runtime_action in {"recover_runtime", "probe_runtime", "relaunch_runtime", "external_supervisor_required"}
    )
    return (
        "runtime_recovery_retry_budget_exhausted" in reasons
        or _text(status.get("reason")) == "runtime_recovery_retry_budget_exhausted"
        or attempt_state == "escalated"
        or zero_budget_in_recovery_context
    )


def supervisor_only(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if _mapping(status.get("execution_owner_guard")).get("supervisor_only") is True:
        return True
    return "execution_owner_guard.supervisor_only" in set(blocking_reasons(status, progress))


def runtime_platform_repair_required(
    status: Mapping[str, Any], progress: Mapping[str, Any], *, gate_specificity: Mapping[str, Any] | None = None
) -> bool:
    if completion_evidence.completed_current_truth(status, progress):
        return False
    if parked_truth.current_truth(status, progress):
        return False
    if gate_specificity_part.should_defer_runtime_platform_repair(
        gate_specificity
    ) and gate_specificity_part.controller_specificity_terminal(status):
        return False
    if abnormal_stopped_runtime.repair_required(status, progress):
        return True
    no_live_worker = not active_run_id(status, progress) or not worker_running(status)
    return retry_exhausted(status, progress) and no_live_worker and _text(status.get("quest_status")) in {"active", "running"}


def live_activity_timeout_current_controller_redrive_required(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    runtime_health = _mapping(status.get("runtime_health_snapshot"))
    worker_liveness = _mapping(runtime_health.get("worker_liveness_state"))
    reasons = set(blocking_reasons(status, progress))
    progress_timeout = _progress_activity_timeout(progress)
    return (
        _text(status.get("quest_status")) in {"active", "running"}
        and active_run_id(status, progress) is not None
        and worker_running(status)
        and (
            (
                _text(runtime_health.get("canonical_runtime_action")) == "recover_runtime"
                and _text(worker_liveness.get("state")) == "activity_timeout"
            )
            or progress_timeout["timed_out"]
        )
        and (
            "live_worker_meaningful_artifact_delta_timeout" in reasons
            or "same_fingerprint_loop" in reasons
            or "same_fingerprint_loop" in progress_timeout["breach_types"]
            or progress_timeout["timed_out"]
        )
    )


def live_activity_timeout_current_controller_route_available(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    study_root: Any,
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    return (
        live_activity_timeout_current_controller_redrive_required(status, progress)
        and current_truth_owner.current_controller_runtime_route(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        is not None
    )


def current_controller_owner_handoff_redrive_required(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    study_root: Any,
    publication_eval_payload: Mapping[str, Any],
) -> bool:
    if _text(status.get("quest_status")) != "waiting_for_user":
        return False
    if active_run_id(status, progress) is not None or worker_running(status):
        return False
    continuation_state = _mapping(status.get("continuation_state"))
    if int(continuation_state.get("pending_user_message_count") or 0) > 0:
        return False
    blocked_closeout = _mapping(status.get("blocked_turn_closeout"))
    if not blocked_closeout:
        blocked_closeout = _mapping(_mapping(status.get("interaction_arbitration")).get("blocked_turn_closeout"))
    if not blocked_closeout:
        interaction = _mapping(status.get("interaction_arbitration"))
        if _text(interaction.get("classification")) == "blocked_closeout_owner_wait":
            blocked_closeout = interaction
    return bool(
        _text(continuation_state.get("continuation_policy")) == "wait_for_user_or_resume"
        and _text(continuation_state.get("continuation_anchor")) == "turn_closeout"
        and _text(continuation_state.get("continuation_reason")) == "blocked_turn_closeout_waiting_for_owner"
        and owner_token(blocked_closeout.get("next_owner")) == "mas_controller"
        and current_truth_owner.current_controller_runtime_route(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        is not None
    )


def runtime_platform_repair_apply_required(
    *,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    publication_eval_payload: Mapping[str, Any],
    study_root: Any,
    gate_specificity: Mapping[str, Any] | None = None,
) -> bool:
    if runtime_platform_repair_required(status, progress, gate_specificity=gate_specificity):
        return True
    if _controller_work_unit_pending_redrive_required(status):
        return True
    if _external_supervisor_bounded_redrive_required(status, progress):
        return True
    if _pending_user_message_platform_redrive_required(status):
        return True
    if _publication_gate_closeout_targets_resolved_redrive_required(
        status=status,
        gate_specificity=gate_specificity,
    ):
        return True
    if _runtime_platform_repair_redrive_pending(status):
        return True
    if current_controller_owner_handoff_redrive_required(
        status=status,
        progress=progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    ):
        return True
    return live_activity_timeout_current_controller_route_available(
        status,
        progress,
        study_root=study_root,
        publication_eval_payload=publication_eval_payload,
    )


def current_controller_route_redrive_required(
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
    *,
    study_root: Any,
    publication_eval_payload: Mapping[str, Any],
    gate_specificity: Mapping[str, Any] | None = None,
) -> bool:
    if completion_evidence.completed_current_truth(status, progress):
        return False
    if active_run_id(status, progress) is not None or worker_running(status):
        return False
    if not (
        _publication_gate_closeout_targets_resolved_redrive_required(
            status=status,
            gate_specificity=gate_specificity,
        )
        or _runtime_platform_repair_redrive_pending(status)
    ):
        return False
    return (
        current_truth_owner.current_controller_runtime_route(
            study_root=study_root,
            publication_eval_payload=publication_eval_payload,
        )
        is not None
    )


def _pending_user_message_platform_redrive_required(status: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) != "waiting_for_user":
        return False
    if active_run_id(status, {}) is not None or worker_running(status):
        return False
    continuation_state = _mapping(status.get("continuation_state"))
    return bool(
        _text(continuation_state.get("continuation_policy")) == "auto"
        and _text(continuation_state.get("continuation_anchor")) == "user_message_queue"
        and _text(continuation_state.get("continuation_reason"))
        == "runtime_platform_repair_resume_existing_pending_user_message"
        and int(continuation_state.get("pending_user_message_count") or 0) > 0
    )


def _publication_gate_closeout_targets_resolved_redrive_required(
    *,
    status: Mapping[str, Any],
    gate_specificity: Mapping[str, Any] | None,
) -> bool:
    if _text(status.get("quest_status")) != "waiting_for_user":
        return False
    if active_run_id(status, {}) is not None or worker_running(status):
        return False
    continuation_state = _mapping(status.get("continuation_state"))
    if int(continuation_state.get("pending_user_message_count") or 0) > 0:
        return False
    blocked_closeout = _mapping(status.get("blocked_turn_closeout"))
    if not blocked_closeout:
        blocked_closeout = _mapping(_mapping(status.get("interaction_arbitration")).get("blocked_turn_closeout"))
    return bool(
        _text(continuation_state.get("continuation_policy")) == "wait_for_user_or_resume"
        and _text(continuation_state.get("continuation_anchor")) == "turn_closeout"
        and _text(continuation_state.get("continuation_reason")) == "blocked_turn_closeout_waiting_for_owner"
        and owner_token(blocked_closeout.get("next_owner")) in {"publication_gate", "mas_controller"}
        and _mapping(gate_specificity).get("specific_targets_present") is True
    )


def _runtime_platform_repair_redrive_pending(status: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) != "waiting_for_user":
        return False
    if active_run_id(status, {}) is not None or worker_running(status):
        return False
    continuation_state = _mapping(status.get("continuation_state"))
    if int(continuation_state.get("pending_user_message_count") or 0) > 0:
        return False
    return bool(
        _text(continuation_state.get("continuation_policy")) == "auto"
        and _text(continuation_state.get("continuation_anchor")) == "decision"
        and _text(continuation_state.get("continuation_reason"))
        in {
            "runtime_platform_repair_redrive",
            "controller_work_unit_pending",
        }
    )


def _controller_work_unit_pending_redrive_required(status: Mapping[str, Any]) -> bool:
    if _text(status.get("quest_status")) != "waiting_for_user":
        return False
    if active_run_id(status, {}) is not None or worker_running(status):
        return False
    interaction_arbitration = _mapping(status.get("interaction_arbitration"))
    return bool(
        _text(interaction_arbitration.get("classification")) == "controller_work_unit_pending_redrive"
        and _text(interaction_arbitration.get("action")) == "resume"
    )


def _external_supervisor_bounded_redrive_required(status: Mapping[str, Any], progress: Mapping[str, Any]) -> bool:
    if active_run_id(status, progress) is not None or worker_running(status):
        return False
    lifecycle = _mapping(progress.get("ai_repair_lifecycle"))
    if _text(lifecycle.get("state")) not in {"blocked", "external_supervisor_required"}:
        return False
    if lifecycle.get("external_supervisor_required") is not True:
        return False
    if _text(lifecycle.get("blocked_reason")) != "runtime_recovery_not_authorized":
        return False
    top_action = _mapping(lifecycle.get("top_action"))
    return bool(
        _text(top_action.get("action_type")) == "controller_repair"
        and _text(top_action.get("repair_kind")) == "bounded_work_unit_redrive"
        and top_action.get("auto_apply_allowed") is True
    )


def _string_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, Mapping | bytes):
        return []
    return list(dict.fromkeys(text for item in value if (text := _text(item)) is not None))


def _progress_activity_timeout(progress: Mapping[str, Any]) -> dict[str, Any]:
    progress_freshness = _mapping(progress.get("progress_freshness"))
    activity_timeout = _mapping(progress_freshness.get("activity_timeout"))
    return {
        "timed_out": _text(activity_timeout.get("state")) == "timed_out",
        "active_run_id": _text(activity_timeout.get("active_run_id")),
        "breach_types": set(_string_items(activity_timeout.get("breach_types"))),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "active_run_id",
    "blocking_reasons",
    "current_controller_owner_handoff_redrive_required",
    "current_controller_route_redrive_required",
    "live_activity_timeout_current_controller_route_available",
    "live_activity_timeout_current_controller_redrive_required",
    "retry_exhausted",
    "runtime_platform_repair_apply_required",
    "runtime_platform_repair_required",
    "supervisor_only",
    "worker_running",
]
