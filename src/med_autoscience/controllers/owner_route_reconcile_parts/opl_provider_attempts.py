from __future__ import annotations

import json
import os
import signal
import subprocess
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


LIVE_ATTEMPT_STATES = {"running", "checkpointed", "human_gate"}
DEFAULT_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
STAGE_PROGRESS_LOG_KEYS = (
    "surface_kind",
    "projection_scope",
    "attempt_count",
    "completed_attempt_count",
    "blocked_attempt_count",
    "activity_event_count",
    "runner_progress_event_count",
    "duration_observed_attempt_count",
    "missing_usage_telemetry_attempt_count",
    "temporal_attempt_count",
    "temporal_webui_ref_count",
    "temporal_visibility_readiness_statuses",
    "activity_event_ref_count",
    "attempt_refs",
    "temporal_webui_refs",
    "authority_boundary",
)


def live_provider_attempt_for_study(
    *,
    profile: Any,
    study_id: str,
    timeout_seconds: float = 3.0,
    max_inspect_count: int = 2,
) -> dict[str, Any] | None:
    opl_bin = _opl_bin()
    if opl_bin is None:
        return None
    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    queue_payload = _run_opl_json(
        opl_bin,
        ("family-runtime", "queue", "list", "--json"),
        timeout_seconds=_remaining_seconds(deadline),
    )
    if queue_payload is None:
        return None
    candidate_tasks = _candidate_tasks(queue_payload, profile=profile, study_id=study_id)
    for task in candidate_tasks[: max(0, max_inspect_count)]:
        remaining_seconds = _remaining_seconds(deadline)
        if remaining_seconds <= 0:
            return None
        task_id = _text(task.get("task_id"))
        if task_id is None:
            continue
        inspected = _run_opl_json(
            opl_bin,
            ("family-runtime", "queue", "inspect", task_id, "--json"),
            timeout_seconds=remaining_seconds,
        )
        projection = _live_projection_from_inspect(inspected, profile=profile, study_id=study_id)
        if projection is not None:
            return projection
    return None


def action_is_covered_by_live_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    action: Mapping[str, Any],
) -> bool:
    if not live_attempt:
        return False
    live_action_type = _text(live_attempt.get("action_type"))
    action_type = _text(action.get("action_type"))
    if live_action_type is not None and action_type is not None and live_action_type != action_type:
        return False
    live_work_unit = _text(live_attempt.get("work_unit_id"))
    action_work_unit = _text(action.get("work_unit_id")) or _text(action.get("next_work_unit"))
    if live_work_unit is not None and action_work_unit is not None and live_work_unit != action_work_unit:
        return False
    return live_action_type is not None and action_type is not None


def filter_actions_covered_by_live_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    actions: Iterable[Mapping[str, Any]],
) -> list[Mapping[str, Any]]:
    return [
        action
        for action in actions
        if not action_is_covered_by_live_attempt(live_attempt=live_attempt, action=action)
    ]


def owner_route_is_covered_by_live_attempt(
    *,
    live_attempt: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any],
) -> bool:
    if not live_attempt:
        return False
    live_action_type = _text(live_attempt.get("action_type"))
    allowed_actions = {
        item
        for item in (_text(value) for value in _iter_values(owner_route.get("allowed_actions")))
        if item is not None
    }
    if live_action_type is not None and allowed_actions and live_action_type not in allowed_actions:
        return False
    live_work_unit = _text(live_attempt.get("work_unit_id"))
    route_work_unit = _text(owner_route.get("work_unit_id")) or _text(owner_route.get("next_work_unit"))
    if live_work_unit is not None and route_work_unit is not None and live_work_unit != route_work_unit:
        return False
    return live_action_type is not None and bool(allowed_actions)


def owner_state_overlay(
    *,
    live_attempt: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    if not owner_route_is_covered_by_live_attempt(live_attempt=live_attempt, owner_route=owner_route):
        return {}
    return {
        "why_not_applied": None,
        "blocked_reason": None,
        "next_owner": "supervisor_only/live_provider_attempt",
        "lifecycle": {},
    }


def projection_fields(
    *,
    live_attempt: Mapping[str, Any] | None,
    fallback_active_run_id: str | None,
    fallback_runtime_health: Mapping[str, Any],
) -> dict[str, Any]:
    if not live_attempt:
        return {
            "active_run_id": fallback_active_run_id,
            "active_stage_attempt_id": None,
            "active_workflow_id": None,
            "running_provider_attempt": False,
            "runtime_health": dict(fallback_runtime_health),
        }
    return {
        "active_run_id": _text(live_attempt.get("active_run_id")),
        "active_stage_attempt_id": _text(live_attempt.get("active_stage_attempt_id")),
        "active_workflow_id": _text(live_attempt.get("active_workflow_id")),
        "running_provider_attempt": bool(live_attempt.get("running_provider_attempt")),
        "runtime_health": _mapping(live_attempt.get("runtime_health")),
        "stage_progress_log": _stage_progress_log(live_attempt.get("stage_progress_log")),
    }


def _opl_bin() -> Path | None:
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    path = Path(configured).expanduser() if configured else DEFAULT_OPL_BIN
    return path if path.exists() else None


def _run_opl_json(opl_bin: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict[str, Any] | None:
    if timeout_seconds <= 0:
        return None
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            [str(opl_bin), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, _ = process.communicate(timeout=timeout_seconds)
    except subprocess.TimeoutExpired:
        if process is not None:
            _terminate_process_group(process)
        return None
    except OSError:
        return None
    if process.returncode != 0:
        return None
    try:
        parsed = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return dict(parsed) if isinstance(parsed, Mapping) else None


def _remaining_seconds(deadline: float) -> float:
    return max(0.0, deadline - time.monotonic())


def _terminate_process_group(process: subprocess.Popen[str]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except ProcessLookupError:
        return
    except OSError:
        process.kill()
        return
    try:
        process.communicate(timeout=0.2)
        return
    except subprocess.TimeoutExpired:
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        return
    except OSError:
        process.kill()
        return
    try:
        process.communicate(timeout=0.2)
    except subprocess.TimeoutExpired:
        pass


def _candidate_tasks(
    queue_payload: Mapping[str, Any],
    *,
    profile: Any,
    study_id: str,
) -> list[dict[str, Any]]:
    queue = _mapping(queue_payload.get("family_runtime_queue"))
    tasks = [
        dict(item)
        for item in queue.get("tasks") or queue.get("queue") or []
        if isinstance(item, Mapping)
    ]
    matched = [
        task
        for task in tasks
        if _task_matches_study(task, profile=profile, study_id=study_id)
        and _text(task.get("task_kind")) == "domain_owner/default-executor-dispatch"
        and _text(task.get("status")) in LIVE_ATTEMPT_STATES
    ]
    matched.sort(key=lambda task: _text(task.get("updated_at")) or "", reverse=True)
    matched.sort(key=_task_status_priority)
    return matched


def _task_matches_study(task: Mapping[str, Any], *, profile: Any, study_id: str) -> bool:
    payload = _mapping(task.get("payload"))
    if _text(payload.get("study_id")) != study_id:
        return False
    profile_ref = _text(payload.get("profile"))
    if profile_ref is None:
        workspace_root = _text(payload.get("workspace_root"))
        return workspace_root is None or Path(workspace_root).expanduser().resolve() == profile.workspace_root.resolve()
    try:
        resolved_profile = Path(profile_ref).expanduser().resolve()
    except OSError:
        return False
    return profile.workspace_root.resolve() in resolved_profile.parents


def _task_status_priority(task: Mapping[str, Any]) -> int:
    status = _text(task.get("status"))
    return 0 if status in LIVE_ATTEMPT_STATES else 1


def _live_projection_from_inspect(
    inspect_payload: Mapping[str, Any] | None,
    *,
    profile: Any,
    study_id: str,
) -> dict[str, Any] | None:
    if inspect_payload is None:
        return None
    task_surface = _mapping(inspect_payload.get("family_runtime_task"))
    task = _mapping(task_surface.get("task"))
    payload = _mapping(task.get("payload"))
    if _text(payload.get("study_id")) != study_id:
        return None
    control = _mapping(task.get("current_control_state"))
    if control.get("running_provider_attempt") is not True:
        return None
    active_run_id = _text(control.get("active_run_id"))
    if active_run_id is None:
        return None
    provider_run = _mapping(control.get("provider_run"))
    provider_status = _text(provider_run.get("provider_status"))
    attempt_state = _text(control.get("current_attempt_state")) or _text(control.get("reconciliation_status"))
    if provider_status not in LIVE_ATTEMPT_STATES and attempt_state not in LIVE_ATTEMPT_STATES:
        return None
    workspace_locator = _mapping(_first_attempt(task_surface).get("workspace_locator"))
    workspace_root = _text(workspace_locator.get("workspace_root"))
    if workspace_root is not None and Path(workspace_root).expanduser().resolve() != profile.workspace_root.resolve():
        return None
    projection = {
        "surface_kind": "opl_current_control_state_provider_attempt",
        "source": "opl_family_runtime_queue_inspect",
        "active_run_id": active_run_id,
        "active_stage_attempt_id": _text(control.get("active_stage_attempt_id")),
        "active_workflow_id": _text(control.get("active_workflow_id")),
        "running_provider_attempt": True,
        "task_id": _text(task.get("task_id")) or _text(control.get("task_id")),
        "task_kind": _text(task.get("task_kind")) or _text(control.get("task_kind")),
        "provider_kind": _text(control.get("provider_kind")),
        "action_type": _text(payload.get("action_type")) or _text(workspace_locator.get("action_type")),
        "work_unit_id": _text(payload.get("work_unit_id")),
        "dispatch_ref": _text(payload.get("dispatch_ref")) or _text(workspace_locator.get("dispatch_ref")),
        "current_attempt_state": attempt_state,
        "reconciliation_status": _text(control.get("reconciliation_status")),
        "provider_run": dict(provider_run),
        "runtime_health": {
            "health_status": "running",
            "runtime_liveness_status": "live",
            "summary": "OPL family-runtime has a live provider-backed stage attempt for this study.",
            "provider_status": provider_status,
        },
        "refs": {
            "opl_queue_task": f"opl://family-runtime/tasks/{_text(task.get('task_id')) or _text(control.get('task_id'))}",
            "opl_stage_attempt": (
                f"opl://stage_attempts/{_text(control.get('active_stage_attempt_id'))}"
                if _text(control.get("active_stage_attempt_id")) is not None
                else None
            ),
        },
        "authority_boundary": {
            "opl": "provider_attempt_liveness_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    }
    stage_progress_log = _stage_progress_log(control.get("stage_progress_log"))
    if stage_progress_log:
        projection["stage_progress_log"] = stage_progress_log
    return projection


def _first_attempt(task_surface: Mapping[str, Any]) -> dict[str, Any]:
    for item in task_surface.get("stage_attempts") or []:
        if isinstance(item, Mapping):
            return dict(item)
    return {}


def _iter_values(value: object) -> Iterable[object]:
    if isinstance(value, str):
        return (value,)
    if isinstance(value, Iterable) and not isinstance(value, Mapping | bytes):
        return value
    return ()


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _stage_progress_log(value: object) -> dict[str, Any] | None:
    if not isinstance(value, Mapping):
        return None
    projection = {key: value[key] for key in STAGE_PROGRESS_LOG_KEYS if key in value}
    return projection or None


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "action_is_covered_by_live_attempt",
    "filter_actions_covered_by_live_attempt",
    "live_provider_attempt_for_study",
    "owner_state_overlay",
    "owner_route_is_covered_by_live_attempt",
    "projection_fields",
]
