from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import time
from collections.abc import Callable, Iterable, Mapping
from pathlib import Path
from typing import Any

PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
LIVE_ATTEMPT_STATES = {"running", "checkpointed", "human_gate"}
TERMINAL_ATTEMPT_STATES = {"blocked", "completed", "failed", "terminal"}
STAGE_OUTCOME_OPL_HANDOFF_TASK_KIND = "stage_outcome/opl-handoff"


def opl_bin() -> Path | None:
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        path = Path(configured).expanduser()
        return path if path.exists() else None
    for path in _ranked_opl_bin_candidates():
        if path.exists():
            return path
    return None


def current_provider_status_payload(
    *,
    timeout_seconds: float,
    readiness_from_status: Callable[[Mapping[str, Any] | None], Mapping[str, Any] | None],
) -> dict[str, Any] | None:
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        path = Path(configured).expanduser()
        if not path.exists():
            return None
        return run_opl_json(
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
        remaining = remaining_seconds(deadline)
        if remaining <= 0:
            break
        payload = run_opl_json(
            candidate,
            ("family-runtime", "status", "--provider", "temporal", "--json"),
            timeout_seconds=remaining,
        )
        if first_payload is None:
            first_payload = payload
        readiness = readiness_from_status(payload)
        if provider_readiness_is_current(readiness):
            return payload
    return first_payload


def provider_readiness_is_current(readiness: Mapping[str, Any] | None) -> bool:
    payload = _mapping(readiness)
    return (
        payload.get("provider_ready") is True
        and payload.get("worker_ready") is True
        and payload.get("managed_worker_source_current") is True
    )


def run_opl_json(opl_bin: Path, args: tuple[str, ...], *, timeout_seconds: float) -> dict[str, Any] | None:
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


def remaining_seconds(deadline: float) -> float:
    return max(0.0, deadline - time.monotonic())


def candidate_attempts(
    attempts_payload: Mapping[str, Any],
    *,
    attempt_matches_study: Callable[[Mapping[str, Any]], bool],
    attempt_has_terminal_owner_callable_closeout: Callable[[Mapping[str, Any]], bool],
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
        if attempt_matches_study(attempt)
        and _text(attempt.get("domain_id")) == "medautoscience"
        and _text(attempt.get("stage_id")) == STAGE_OUTCOME_OPL_HANDOFF_TASK_KIND
        and attempt_is_live(attempt)
        and not attempt_has_terminal_owner_callable_closeout(attempt)
    ]
    return _prefer_matching_attempts(
        matched,
        preferred=preferred_action_keys(preferred_actions),
    )


def candidate_terminal_attempts(
    attempts_payload: Mapping[str, Any],
    *,
    attempt_matches_study: Callable[[Mapping[str, Any]], bool],
    attempt_has_terminal_owner_callable_closeout: Callable[[Mapping[str, Any]], bool],
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
        if attempt_matches_study(attempt)
        and _text(attempt.get("domain_id")) == "medautoscience"
        and _text(attempt.get("stage_id")) == STAGE_OUTCOME_OPL_HANDOFF_TASK_KIND
        and attempt_is_terminal(attempt)
        and not attempt_has_terminal_owner_callable_closeout(attempt)
    ]
    return _prefer_matching_attempts(
        matched,
        preferred=preferred_action_keys(preferred_actions),
    )


def preferred_action_keys(
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


def attempt_is_live(attempt: Mapping[str, Any]) -> bool:
    provider_run = _mapping(attempt.get("provider_run"))
    return (
        _text(attempt.get("status")) in LIVE_ATTEMPT_STATES
        or _text(provider_run.get("provider_status")) in LIVE_ATTEMPT_STATES
    )


def attempt_is_terminal(attempt: Mapping[str, Any]) -> bool:
    provider_run = _mapping(attempt.get("provider_run"))
    return (
        _text(attempt.get("status")) in TERMINAL_ATTEMPT_STATES
        or _text(provider_run.get("provider_status")) in TERMINAL_ATTEMPT_STATES
        or _text(attempt.get("closeout_receipt_status")) == "accepted_typed_closeout"
    )


def _prefer_matching_attempts(
    attempts: list[dict[str, Any]],
    *,
    preferred: set[tuple[str | None, str | None, str | None]],
) -> list[dict[str, Any]]:
    if not preferred:
        return attempts
    matching = [
        attempt
        for attempt in attempts
        if _attempt_matches_preferred(attempt, preferred)
    ]
    if not matching:
        return attempts
    return matching + [attempt for attempt in attempts if attempt not in matching]


def _attempt_matches_preferred(
    attempt: Mapping[str, Any],
    preferred: set[tuple[str | None, str | None, str | None]],
) -> bool:
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
    attempt_action_type = _text(payload_like.get("action_type"))
    attempt_work_unit_ids = _task_work_unit_ids(payload_like)
    attempt_dispatch_refs = _action_dispatch_refs(payload_like)
    for preferred_action, preferred_work_unit, preferred_dispatch_ref in preferred:
        if preferred_action is not None and preferred_action != attempt_action_type:
            continue
        if (
            preferred_work_unit is not None
            and preferred_work_unit not in attempt_work_unit_ids
        ):
            continue
        if (
            preferred_dispatch_ref is not None
            and preferred_dispatch_ref not in attempt_dispatch_refs
        ):
            continue
        return True
    return False


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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "candidate_attempts",
    "candidate_terminal_attempts",
    "current_provider_status_payload",
    "opl_bin",
    "attempt_is_live",
    "attempt_is_terminal",
    "remaining_seconds",
    "run_opl_json",
]
