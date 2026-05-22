from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.owner_route_reconcile_parts import current_truth_owner
from med_autoscience.controllers.owner_route_reconcile_parts import platform_current_controller
from med_autoscience.controllers.owner_route_reconcile_parts import platform_repair_closeout_redrive


SPECIFICITY_WORK_UNIT_IDS = platform_repair_closeout_redrive.SPECIFICITY_WORK_UNIT_IDS
PACKAGE_FRESHNESS_TERMINAL_REASONS = platform_repair_closeout_redrive.PACKAGE_FRESHNESS_TERMINAL_REASONS


def runtime_relaunch_postcondition_failure(
    resume_result: Mapping[str, Any],
    *,
    controller_authorization: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    postcondition = _mapping(resume_result.get("resume_postcondition"))
    terminal_markers = {
        _text(resume_result.get("blocked_reason")),
        _text(resume_result.get("terminal_reason")),
        _text(postcondition.get("blocked_reason")),
        _text(postcondition.get("terminal_reason")),
    }
    if any(marker in SPECIFICITY_WORK_UNIT_IDS for marker in terminal_markers):
        return {
            "reason": "publication_gate_specificity_required",
            "resume_postcondition": postcondition or None,
        }
    if any(marker in PACKAGE_FRESHNESS_TERMINAL_REASONS for marker in terminal_markers):
        if platform_current_controller.controller_authorization_points_to_upstream_work_unit(
            controller_authorization
        ):
            return {
                "reason": current_truth_owner.RUNTIME_CONTROLLER_REDRIVE_REASON,
                "resume_postcondition": postcondition or None,
            }
        return {
            "reason": "current_package_freshness_required",
            "resume_postcondition": postcondition or None,
        }
    if postcondition and postcondition.get("effective") is not True:
        return {
            "reason": "runtime_relaunch_no_live_run_started",
            "resume_postcondition": postcondition,
        }
    if resume_result_active_run_id(resume_result) is None and not resume_result_worker_running(resume_result):
        return {
            "reason": "runtime_relaunch_no_live_run_started",
            "resume_postcondition": postcondition or None,
        }
    return None


def resume_result_active_run_id(resume_result: Mapping[str, Any]) -> str | None:
    runtime_liveness = _mapping(resume_result.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    snapshot = _mapping(resume_result.get("snapshot"))
    postcondition = _mapping(resume_result.get("resume_postcondition"))
    for value in (
        resume_result.get("active_run_id"),
        postcondition.get("active_run_id"),
        runtime_liveness.get("active_run_id"),
        runtime_audit.get("active_run_id"),
        snapshot.get("active_run_id"),
    ):
        if text := _text(value):
            return text
    return None


def resume_result_worker_running(resume_result: Mapping[str, Any]) -> bool:
    runtime_liveness = _mapping(resume_result.get("runtime_liveness_audit"))
    runtime_audit = _mapping(runtime_liveness.get("runtime_audit"))
    postcondition = _mapping(resume_result.get("resume_postcondition"))
    snapshot = _mapping(resume_result.get("snapshot"))
    if postcondition.get("effective") is True and (
        postcondition.get("started") is True
        or postcondition.get("scheduled") is True
        or postcondition.get("queued") is True
        or _text(postcondition.get("active_run_id")) is not None
    ):
        return True
    if snapshot.get("worker_running") is True:
        return True
    if runtime_audit.get("worker_running") is False:
        return False
    if runtime_liveness.get("worker_running") is False:
        return False
    return bool(runtime_audit.get("worker_running") or runtime_liveness.get("worker_running"))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "resume_result_active_run_id",
    "resume_result_worker_running",
    "runtime_relaunch_postcondition_failure",
]
