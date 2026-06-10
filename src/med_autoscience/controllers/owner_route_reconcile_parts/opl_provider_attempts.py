from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import time
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any


LIVE_ATTEMPT_STATES = {"running", "checkpointed", "human_gate"}
PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
DEFAULT_LIVE_ATTEMPT_INSPECTION_TIMEOUT_SECONDS = 8.0
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
OPL_PROVIDER_READINESS_KEYS = (
    "surface_kind",
    "source",
    "provider_kind",
    "provider_ready",
    "full_online_ready",
    "durable_online_ready",
    "degraded",
    "degraded_reason",
    "worker_ready",
    "managed_worker_source_current",
    "managed_worker_pid",
    "task_queue",
    "selected_provider_can_replace_domain_daemons",
    "provider_completion_is_domain_ready",
    "can_write_domain_truth",
    "can_authorize_publication_ready",
)


def live_provider_attempt_for_study(
    *,
    profile: Any,
    study_id: str,
    timeout_seconds: float = DEFAULT_LIVE_ATTEMPT_INSPECTION_TIMEOUT_SECONDS,
    max_inspect_count: int = 2,
    preferred_actions: Iterable[Mapping[str, Any]] | None = None,
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
    if queue_payload is not None:
        candidate_tasks = _candidate_tasks(
            queue_payload,
            profile=profile,
            study_id=study_id,
            preferred_actions=preferred_actions,
        )
        for task in candidate_tasks:
            projection = _live_projection_from_queue_task(task, profile=profile, study_id=study_id)
            if projection is not None:
                return projection
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
    return _live_projection_from_attempt_ledger(
        opl_bin=opl_bin,
        profile=profile,
        study_id=study_id,
        deadline=deadline,
        max_inspect_count=max_inspect_count,
        preferred_actions=preferred_actions,
    )


def current_provider_readiness(
    *,
    timeout_seconds: float = 3.0,
) -> dict[str, Any] | None:
    status_payload = _current_provider_status_payload(timeout_seconds=timeout_seconds)
    if status_payload is None:
        return None
    return _provider_readiness_from_status(status_payload)


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
    if configured:
        path = Path(configured).expanduser()
        return path if path.exists() else None
    for path in _ranked_opl_bin_candidates():
        if path.exists():
            return path
    return None


def _current_provider_status_payload(*, timeout_seconds: float) -> dict[str, Any] | None:
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        path = Path(configured).expanduser()
        if not path.exists():
            return None
        return _run_opl_json(
            path,
            ("family-runtime", "status", "--provider", "temporal", "--json"),
            timeout_seconds=timeout_seconds,
        )
    candidates = [path for path in _ranked_opl_bin_candidates() if path.exists()]
    if not candidates:
        return None
    deadline = time.monotonic() + max(timeout_seconds, 0.0)
    first_payload: dict[str, Any] | None = None
    for candidate in candidates:
        remaining_seconds = _remaining_seconds(deadline)
        if remaining_seconds <= 0:
            break
        payload = _run_opl_json(
            candidate,
            ("family-runtime", "status", "--provider", "temporal", "--json"),
            timeout_seconds=remaining_seconds,
        )
        if first_payload is None:
            first_payload = payload
        readiness = _provider_readiness_from_status(payload)
        if _provider_readiness_is_current(readiness):
            return payload
    return first_payload


def _ranked_opl_bin_candidates() -> list[Path]:
    candidates: list[Path] = []
    path_candidate = shutil.which(PATH_OPL_BIN)
    if path_candidate is not None:
        candidates.append(Path(path_candidate).expanduser())
    candidates.extend([PACKAGED_OPL_BIN, DEV_OPL_BIN])
    ranked: list[Path] = []
    seen: set[Path] = set()
    for candidate in candidates:
        try:
            resolved = candidate.resolve()
        except OSError:
            resolved = candidate
        if resolved in seen:
            continue
        seen.add(resolved)
        ranked.append(candidate)
    return ranked


def _provider_readiness_is_current(readiness: Mapping[str, Any] | None) -> bool:
    payload = _mapping(readiness)
    return (
        payload.get("provider_ready") is True
        and payload.get("worker_ready") is True
        and payload.get("managed_worker_source_current") is True
    )


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
    preferred_actions: Iterable[Mapping[str, Any]] | None = None,
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
    preferred = _preferred_action_keys(preferred_actions)
    matched.sort(key=lambda task: _text(task.get("updated_at")) or "", reverse=True)
    if preferred:
        matched.sort(key=lambda task: _preferred_task_rank(task, preferred))
    matched.sort(key=_task_status_priority)
    return matched


def _live_projection_from_attempt_ledger(
    *,
    opl_bin: Path,
    profile: Any,
    study_id: str,
    deadline: float,
    max_inspect_count: int,
    preferred_actions: Iterable[Mapping[str, Any]] | None,
) -> dict[str, Any] | None:
    remaining_seconds = _remaining_seconds(deadline)
    if remaining_seconds <= 0:
        return None
    attempts_payload = _run_opl_json(
        opl_bin,
        ("family-runtime", "attempt", "list", "--json"),
        timeout_seconds=remaining_seconds,
    )
    if attempts_payload is None:
        return None
    candidate_attempts = _candidate_attempts(
        attempts_payload,
        profile=profile,
        study_id=study_id,
        preferred_actions=preferred_actions,
    )
    for attempt in candidate_attempts[: max(0, max_inspect_count)]:
        remaining_seconds = _remaining_seconds(deadline)
        if remaining_seconds <= 0:
            return None
        stage_attempt_id = _text(attempt.get("stage_attempt_id"))
        if stage_attempt_id is None:
            continue
        inspected = _run_opl_json(
            opl_bin,
            ("family-runtime", "attempt", "inspect", stage_attempt_id, "--json"),
            timeout_seconds=remaining_seconds,
        )
        projection = _live_projection_from_attempt_inspect(
            inspected,
            profile=profile,
            study_id=study_id,
        )
        if projection is not None:
            return projection
    return None


def _candidate_attempts(
    attempts_payload: Mapping[str, Any],
    *,
    profile: Any,
    study_id: str,
    preferred_actions: Iterable[Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    attempts_surface = _mapping(attempts_payload.get("family_runtime_stage_attempts"))
    attempts = [
        dict(item)
        for item in attempts_surface.get("attempts") or attempts_surface.get("stage_attempts") or []
        if isinstance(item, Mapping)
    ]
    matched = [
        attempt
        for attempt in attempts
        if _attempt_matches_study(attempt, profile=profile, study_id=study_id)
        and _text(attempt.get("domain_id")) == "medautoscience"
        and _text(attempt.get("stage_id")) == "domain_owner/default-executor-dispatch"
        and _attempt_is_live(attempt)
    ]
    preferred = _preferred_action_keys(preferred_actions)
    matched.sort(key=lambda attempt: _attempt_updated_at(attempt) or "", reverse=True)
    if preferred:
        matched.sort(key=lambda attempt: _preferred_attempt_rank(attempt, preferred))
    matched.sort(key=_attempt_status_priority)
    return matched


def _attempt_matches_study(attempt: Mapping[str, Any], *, profile: Any, study_id: str) -> bool:
    locator = _mapping(attempt.get("workspace_locator"))
    attempt_study_id = _text(locator.get("study_id")) or _text(attempt.get("study_id"))
    attempt_quest_id = _text(locator.get("quest_id")) or _text(attempt.get("quest_id"))
    if study_id not in {attempt_study_id, attempt_quest_id}:
        return False
    workspace_root = _text(locator.get("workspace_root")) or _text(attempt.get("workspace_root"))
    if workspace_root is None:
        return True
    try:
        return Path(workspace_root).expanduser().resolve() == profile.workspace_root.resolve()
    except OSError:
        return False


def _attempt_is_live(attempt: Mapping[str, Any]) -> bool:
    provider_run = _mapping(attempt.get("provider_run"))
    return (
        _text(attempt.get("status")) in LIVE_ATTEMPT_STATES
        or _text(provider_run.get("provider_status")) in LIVE_ATTEMPT_STATES
    )


def _attempt_status_priority(attempt: Mapping[str, Any]) -> int:
    return 0 if _attempt_is_live(attempt) else 1


def _attempt_updated_at(attempt: Mapping[str, Any]) -> str | None:
    provider_run = _mapping(attempt.get("provider_run"))
    return (
        _text(provider_run.get("last_heartbeat_at"))
        or _text(attempt.get("updated_at"))
        or _text(attempt.get("created_at"))
    )


def _preferred_attempt_rank(
    attempt: Mapping[str, Any],
    preferred: set[tuple[str | None, str | None, str | None]],
) -> int:
    locator = _mapping(attempt.get("workspace_locator"))
    payload_like = {
        "action_type": _text(locator.get("action_type")) or _text(attempt.get("action_type")),
        "work_unit_id": _text(locator.get("work_unit_id")) or _text(attempt.get("work_unit_id")),
        "executable_work_unit": _text(locator.get("executable_work_unit"))
        or _text(attempt.get("executable_work_unit")),
        "controller_work_unit_id": _text(locator.get("controller_work_unit_id"))
        or _text(attempt.get("controller_work_unit_id")),
        "dispatch_ref": _text(locator.get("dispatch_ref")) or _text(attempt.get("dispatch_ref")),
    }
    return _preferred_task_rank({"payload": payload_like}, preferred)


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


def _preferred_action_keys(
    actions: Iterable[Mapping[str, Any]] | None,
) -> set[tuple[str | None, str | None, str | None]]:
    keys: set[tuple[str | None, str | None, str | None]] = set()
    for action in actions or []:
        if not isinstance(action, Mapping):
            continue
        action_type = _text(action.get("action_type"))
        work_unit_ids = _action_work_unit_ids(action)
        dispatch_refs = _action_dispatch_refs(action)
        if action_type is None and not work_unit_ids and not dispatch_refs:
            continue
        for work_unit_id in work_unit_ids or {None}:
            for dispatch_ref in dispatch_refs or {None}:
                keys.add((action_type, work_unit_id, dispatch_ref))
        if action_type is not None:
            keys.add((action_type, None, None))
    return keys


def _preferred_task_rank(
    task: Mapping[str, Any],
    preferred: set[tuple[str | None, str | None, str | None]],
) -> int:
    payload = _mapping(task.get("payload"))
    task_action_type = _text(payload.get("action_type"))
    task_work_unit_ids = _task_work_unit_ids(payload)
    task_dispatch_refs = _action_dispatch_refs(payload)
    best_rank = 99
    for preferred_action, preferred_work_unit, preferred_dispatch_ref in preferred:
        if preferred_action is not None and preferred_action != task_action_type:
            continue
        if preferred_work_unit is not None and preferred_work_unit not in task_work_unit_ids:
            continue
        if preferred_dispatch_ref is not None and preferred_dispatch_ref not in task_dispatch_refs:
            continue
        specificity = sum(
            value is not None
            for value in (preferred_action, preferred_work_unit, preferred_dispatch_ref)
        )
        best_rank = min(best_rank, max(0, 3 - specificity))
    return best_rank


def _action_work_unit_ids(action: Mapping[str, Any]) -> set[str]:
    next_work_unit = action.get("next_work_unit")
    candidates = {
        _text(action.get("work_unit_id")),
        _text(action.get("executable_work_unit")),
        _text(action.get("controller_work_unit_id")),
        _text(next_work_unit),
        _text(_mapping(next_work_unit).get("unit_id")),
    }
    return {candidate for candidate in candidates if candidate is not None}


def _task_work_unit_ids(payload: Mapping[str, Any]) -> set[str]:
    basis = _mapping(payload.get("owner_route_currentness_basis"))
    candidates = {
        _text(payload.get("work_unit_id")),
        _text(payload.get("executable_work_unit")),
        _text(payload.get("controller_work_unit_id")),
        _text(basis.get("work_unit_id")),
    }
    return {candidate for candidate in candidates if candidate is not None}


def _action_dispatch_refs(action: Mapping[str, Any]) -> set[str]:
    candidates = {
        _text(action.get("dispatch_ref")),
        _text(action.get("dispatch_path")),
    }
    return {candidate for candidate in candidates if candidate is not None}


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
        "runtime_owner": "one-person-lab",
        "provider_attempt_owner": "one-person-lab",
        "queue_owner": "one-person-lab",
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


def _live_projection_from_queue_task(
    task: Mapping[str, Any],
    *,
    profile: Any,
    study_id: str,
) -> dict[str, Any] | None:
    if not _task_matches_study(task, profile=profile, study_id=study_id):
        return None
    liveness = _mapping(task.get("linked_stage_attempt_liveness"))
    if _text(liveness.get("status")) != "live":
        return None
    provider_status = _text(liveness.get("provider_status"))
    attempt_state = _text(liveness.get("stage_attempt_status"))
    if provider_status not in LIVE_ATTEMPT_STATES and attempt_state not in LIVE_ATTEMPT_STATES:
        return None
    stage_attempt_id = _text(liveness.get("stage_attempt_id"))
    if stage_attempt_id is None:
        return None
    payload = _mapping(task.get("payload"))
    workspace_root = _text(payload.get("workspace_root"))
    if workspace_root is not None and Path(workspace_root).expanduser().resolve() != profile.workspace_root.resolve():
        return None
    workflow_id = _text(liveness.get("workflow_id"))
    task_id = _text(task.get("task_id"))
    provider_run = {
        key: value
        for key, value in {
            "provider_kind": _text(liveness.get("provider_kind")),
            "workflow_id": workflow_id,
            "provider_status": provider_status,
            "last_heartbeat_at": _text(liveness.get("last_heartbeat_at")),
            "ledger_last_heartbeat_at": _text(liveness.get("ledger_last_heartbeat_at")),
            "liveness_source": _text(liveness.get("liveness_source")),
            "last_activity_heartbeat_kind": _text(liveness.get("last_activity_heartbeat_kind")),
            "last_runner_event_kind": _text(liveness.get("last_runner_event_kind")),
        }.items()
        if value is not None
    }
    return {
        "surface_kind": "opl_current_control_state_provider_attempt",
        "source": "opl_family_runtime_queue_list_linked_liveness",
        "active_run_id": f"opl-stage-attempt://{stage_attempt_id}",
        "active_stage_attempt_id": stage_attempt_id,
        "active_workflow_id": workflow_id,
        "running_provider_attempt": True,
        "runtime_owner": "one-person-lab",
        "provider_attempt_owner": "one-person-lab",
        "queue_owner": "one-person-lab",
        "task_id": task_id,
        "task_kind": _text(task.get("task_kind")),
        "provider_kind": _text(liveness.get("provider_kind")),
        "action_type": _text(payload.get("action_type")),
        "work_unit_id": _text(payload.get("work_unit_id")),
        "work_unit_fingerprint": _text(payload.get("work_unit_fingerprint"))
        or _text(payload.get("action_fingerprint"))
        or _text(payload.get("source_fingerprint")),
        "dispatch_ref": _text(payload.get("dispatch_ref")),
        "dispatch_path": _text(payload.get("dispatch_path")),
        "current_attempt_state": attempt_state,
        "reconciliation_status": attempt_state,
        "provider_run": provider_run,
        "runtime_health": {
            "health_status": "running",
            "runtime_liveness_status": "live",
            "summary": "OPL family-runtime has a live provider-backed stage attempt for this study.",
            "provider_status": provider_status,
        },
        "refs": {
            "opl_queue_task": f"opl://family-runtime/tasks/{task_id}" if task_id is not None else None,
            "opl_stage_attempt": f"opl://stage_attempts/{stage_attempt_id}",
        },
        "authority_boundary": {
            "opl": "provider_attempt_liveness_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    }


def _live_projection_from_attempt_inspect(
    inspect_payload: Mapping[str, Any] | None,
    *,
    profile: Any,
    study_id: str,
) -> dict[str, Any] | None:
    if inspect_payload is None:
        return None
    attempt_surface = _mapping(inspect_payload.get("family_runtime_stage_attempt"))
    attempt = _mapping(attempt_surface.get("attempt"))
    if not attempt:
        return None
    if not _attempt_matches_study(attempt, profile=profile, study_id=study_id):
        return None
    if _text(attempt.get("domain_id")) != "medautoscience":
        return None
    if _text(attempt.get("stage_id")) != "domain_owner/default-executor-dispatch":
        return None
    if not _attempt_is_live(attempt):
        return None
    stage_attempt_id = _text(attempt.get("stage_attempt_id"))
    if stage_attempt_id is None:
        return None
    locator = _mapping(attempt.get("workspace_locator"))
    provider_run = _mapping(attempt.get("provider_run"))
    provider_status = _text(provider_run.get("provider_status"))
    attempt_state = _text(attempt.get("status"))
    workflow_id = (
        _text(attempt.get("workflow_id"))
        or _text(provider_run.get("workflow_id"))
        or _text(provider_run.get("run_id"))
    )
    task_id = _text(attempt.get("task_id"))
    projection = {
        "surface_kind": "opl_current_control_state_provider_attempt",
        "source": "opl_family_runtime_attempt_inspect",
        "active_run_id": f"opl-stage-attempt://{stage_attempt_id}",
        "active_stage_attempt_id": stage_attempt_id,
        "active_workflow_id": workflow_id,
        "running_provider_attempt": True,
        "runtime_owner": "one-person-lab",
        "provider_attempt_owner": "one-person-lab",
        "queue_owner": "one-person-lab",
        "task_id": task_id,
        "task_kind": "domain_owner/default-executor-dispatch",
        "provider_kind": _text(attempt.get("provider_kind")) or _text(provider_run.get("provider_kind")),
        "action_type": _text(locator.get("action_type")) or _text(attempt.get("action_type")),
        "work_unit_id": _text(locator.get("work_unit_id")) or _text(attempt.get("work_unit_id")),
        "dispatch_ref": _text(locator.get("dispatch_ref")) or _text(attempt.get("dispatch_ref")),
        "current_attempt_state": attempt_state,
        "reconciliation_status": attempt_state,
        "provider_run": dict(provider_run),
        "runtime_health": {
            "health_status": "running",
            "runtime_liveness_status": "live",
            "summary": "OPL family-runtime has a live provider-backed stage attempt for this study.",
            "provider_status": provider_status,
        },
        "refs": {
            "opl_queue_task": f"opl://family-runtime/tasks/{task_id}" if task_id is not None else None,
            "opl_stage_attempt": f"opl://stage_attempts/{stage_attempt_id}",
        },
        "authority_boundary": {
            "opl": "provider_attempt_liveness_projection_only",
            "domain": "truth_quality_artifact_gate_owner",
            "provider_completion_is_domain_ready": False,
            "can_write_domain_truth": False,
            "can_authorize_publication_ready": False,
        },
    }
    stage_progress_log = _stage_progress_log(attempt.get("stage_progress_log"))
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


def _provider_readiness_from_status(status_payload: Mapping[str, Any] | None) -> dict[str, Any] | None:
    if status_payload is None:
        return None
    family_runtime = _mapping(status_payload.get("family_runtime"))
    readiness = _mapping(family_runtime.get("readiness"))
    provider_runtime = _mapping(family_runtime.get("provider_runtime"))
    configured_provider = _text(family_runtime.get("configured_provider")) or "temporal"
    provider = _mapping(_mapping(provider_runtime.get("providers")).get(configured_provider))
    selected = _mapping(provider_runtime.get("selected"))
    provider_details = _mapping(provider.get("details")) or _mapping(selected.get("details"))
    worker_readiness = _mapping(provider_details.get("worker_readiness"))
    authority_boundary = _mapping(_mapping(family_runtime.get("periodic_execution")).get("authority_boundary"))
    projection = {
        "surface_kind": "opl_provider_readiness_projection",
        "source": "opl_family_runtime_status",
        "provider_kind": configured_provider,
        "provider_ready": readiness.get("provider_ready") is True,
        "full_online_ready": readiness.get("full_online_ready") is True,
        "durable_online_ready": readiness.get("durable_online_ready") is True,
        "degraded": readiness.get("degraded") is True,
        "degraded_reason": _text(readiness.get("degraded_reason")),
        "worker_ready": provider_details.get("worker_ready") is True,
        "managed_worker_source_current": worker_readiness.get("managed_worker_source_current") is True,
        "managed_worker_pid": worker_readiness.get("managed_worker_pid"),
        "task_queue": _text(provider.get("task_queue")) or _text(provider_details.get("task_queue")),
        "selected_provider_can_replace_domain_daemons": (
            readiness.get("selected_provider_can_replace_domain_daemons") is True
        ),
        "provider_completion_is_domain_ready": False,
        "can_write_domain_truth": authority_boundary.get("can_write_domain_truth") is True,
        "can_authorize_publication_ready": authority_boundary.get("can_authorize_publication_ready") is True,
    }
    return {key: projection[key] for key in OPL_PROVIDER_READINESS_KEYS if key in projection}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "action_is_covered_by_live_attempt",
    "filter_actions_covered_by_live_attempt",
    "live_provider_attempt_for_study",
    "current_provider_readiness",
    "owner_state_overlay",
    "owner_route_is_covered_by_live_attempt",
    "projection_fields",
]
