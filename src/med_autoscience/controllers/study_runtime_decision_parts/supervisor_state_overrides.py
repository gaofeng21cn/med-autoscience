from __future__ import annotations

from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus


def _task_intake_publication_supervisor_state(task_intake_progress_override: dict[str, object] | None) -> dict[str, object] | None:
    if not isinstance(task_intake_progress_override, dict):
        return None
    quality_closure_truth = (
        dict(task_intake_progress_override.get("quality_closure_truth") or {})
        if isinstance(task_intake_progress_override.get("quality_closure_truth"), dict)
        else {}
    )
    if str(quality_closure_truth.get("state") or "").strip() == "manual_hold":
        lane = (
            dict(task_intake_progress_override.get("quality_execution_lane") or {})
            if isinstance(task_intake_progress_override.get("quality_execution_lane"), dict)
            else {}
        )
        summary = (
            str(lane.get("why_now") or "").strip()
            or str(quality_closure_truth.get("summary") or "").strip()
            or "latest task intake requires manual hold until explicit wakeup"
        )
        return {
            "supervisor_phase": "manual_hold",
            "phase_owner": "task_intake",
            "upstream_scientific_anchor_ready": False,
            "bundle_tasks_downstream_only": False,
            "current_required_action": "hold_until_explicit_wakeup",
            "deferred_downstream_actions": [],
            "controller_stage_note": summary,
        }
    if str(quality_closure_truth.get("state") or "").strip() != "stop_loss_recommended":
        return None
    lane = (
        dict(task_intake_progress_override.get("quality_execution_lane") or {})
        if isinstance(task_intake_progress_override.get("quality_execution_lane"), dict)
        else {}
    )
    return {
        "supervisor_phase": "stop_loss",
        "phase_owner": "task_intake",
        "upstream_scientific_anchor_ready": False,
        "bundle_tasks_downstream_only": False,
        "current_required_action": "stop_runtime",
        "deferred_downstream_actions": [],
        "controller_stage_note": str(lane.get("why_now") or "").strip()
        or str(quality_closure_truth.get("summary") or "").strip()
        or "latest task intake requires publishability stop-loss",
    }


def _publication_supervisor_requests_stop_loss(status: StudyRuntimeStatus) -> bool:
    payload = status.extras.get("publication_supervisor_state")
    if not isinstance(payload, dict):
        return False
    supervisor_phase = str(payload.get("supervisor_phase") or "").strip()
    current_required_action = str(payload.get("current_required_action") or "").strip()
    return supervisor_phase == "stop_loss" or current_required_action in {"stop_loss", "stop_runtime"}


def _publication_supervisor_requests_manual_hold(status: StudyRuntimeStatus) -> bool:
    payload = status.extras.get("publication_supervisor_state")
    if not isinstance(payload, dict):
        return False
    return str(payload.get("supervisor_phase") or "").strip() == "manual_hold" or str(
        payload.get("current_required_action") or ""
    ).strip() == "hold_until_explicit_wakeup"
