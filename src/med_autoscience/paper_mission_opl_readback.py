from __future__ import annotations

import json
import os
import signal
import shutil
import subprocess
import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any


CLOSEOUT_RELATIVE_ROOTS = (
    Path("artifacts/supervision/consumer/default_executor_execution"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
)
TERMINAL_READBACK_STATUS = "opl_runtime_terminal_readback_observed"
RUNNING_READBACK_STATUS = "opl_runtime_attempt_running_observed"
WAITING_READBACK_STATUS = "waiting_for_opl_runtime_live_readback"
PACKAGED_OPL_BIN = Path("/Users/gaofeng/Library/Application Support/OPL/runtime/current/bin/opl")
DEV_OPL_BIN = Path("/Users/gaofeng/workspace/one-person-lab/bin/opl")
PATH_OPL_BIN = "opl"
DEFAULT_OPL_READBACK_TIMEOUT_SECONDS = 8.0
DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS = 8.0
DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT = 2
OPL_STAGE_ROUTE_TASK_KIND = "paper_mission/stage-route"
OPL_DOMAIN_ID = "medautoscience"


def paper_mission_opl_runtime_carrier_readback(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
    opl_runtime_payload: Mapping[str, Any] | None = None,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any]:
    live_probe = None
    live_probe_attempted = False
    if opl_runtime_payload is None and enable_opl_live_probe:
        live_probe_attempted = True
        live_probe = _matching_opl_runtime_live_probe(carrier=carrier, opl_bin=opl_bin)
    running = None
    if live_probe is not None and live_probe[0] == "running":
        running = (live_probe[1], live_probe[2])
    elif not live_probe_attempted:
        running = _matching_opl_runtime_running_attempt(
            carrier=carrier,
            opl_runtime_payload=opl_runtime_payload,
            enable_opl_live_probe=enable_opl_live_probe,
        )
    if running is not None:
        attempt, attempt_ref = running
        return {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "schema_version": 1,
            "carrier_status": RUNNING_READBACK_STATUS,
            "runtime_readback_status": "running_attempt_observed",
            "dispatch_status": "provider_attempt_running",
            "domain_ready_verdict": "opl_runtime_attempt_running",
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "can_claim_provider_running": True,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "request_carrier_preserved": True,
            "running_attempt": _running_attempt_readback(
                attempt=attempt,
                attempt_ref=attempt_ref,
            ),
        }
    matched = None
    if live_probe is not None and live_probe[0] == "terminal":
        matched = (live_probe[1], live_probe[2])
    if matched is None:
        matched = _matching_terminal_closeout(carrier=carrier, study_root=study_root)
    if matched is None:
        if not live_probe_attempted:
            matched = _matching_opl_runtime_terminal_closeout(
                carrier=carrier,
                opl_runtime_payload=opl_runtime_payload,
                enable_opl_live_probe=enable_opl_live_probe,
            )
    if matched is None:
        return {
            "surface_kind": "paper_mission_opl_runtime_carrier_readback",
            "schema_version": 1,
            "carrier_status": WAITING_READBACK_STATUS,
            "runtime_readback_status": "missing",
            "dispatch_status": _text(carrier.get("dispatch_status"))
            or "transition_request_pending",
            "domain_ready_verdict": "opl_runtime_readback_missing",
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "can_claim_provider_running": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "request_carrier_preserved": True,
        }

    closeout, closeout_ref = matched
    return {
        "surface_kind": "paper_mission_opl_runtime_carrier_readback",
        "schema_version": 1,
        "carrier_status": TERMINAL_READBACK_STATUS,
        "runtime_readback_status": "terminal_closeout_observed",
        "dispatch_status": "terminal_closeout_observed",
        "domain_ready_verdict": "domain_gate_pending",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "terminal_closeout": _terminal_closeout_readback(
            closeout=closeout,
            closeout_ref=closeout_ref,
        ),
    }


def attach_opl_runtime_carrier_readback(
    *,
    readback: Mapping[str, Any],
    study_root: Path,
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
) -> dict[str, Any]:
    result = dict(readback)
    carrier = _mapping(result.get("opl_runtime_carrier"))
    if not carrier:
        return result
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    result["opl_runtime_carrier_readback"] = carrier_readback
    result["opl_runtime_readback_status"] = carrier_readback["carrier_status"]
    return result


def _matching_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
) -> tuple[dict[str, Any], str] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    matches: list[tuple[float, dict[str, Any], str]] = []
    for root_ref in CLOSEOUT_RELATIVE_ROOTS:
        closeout_root = resolved_study_root / root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in closeout_root.glob("*.json"):
            closeout = _read_json_object(closeout_path)
            if closeout is None:
                continue
            if not _matches_carrier(closeout=closeout, carrier=carrier):
                continue
            matches.append(
                (
                    closeout_path.stat().st_mtime,
                    closeout,
                    _study_relative_ref(
                        study_root=resolved_study_root,
                        path=closeout_path,
                    ),
                )
            )
    if not matches:
        return None
    _mtime, closeout, closeout_ref = sorted(
        matches,
        key=lambda item: item[0],
        reverse=True,
    )[0]
    return closeout, closeout_ref


def _matching_opl_runtime_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    opl_runtime_payload: Mapping[str, Any] | None,
    enable_opl_live_probe: bool,
) -> tuple[dict[str, Any], str] | None:
    if not _carrier_has_opl_route_identity(carrier):
        return None
    if opl_runtime_payload is not None:
        return _matching_opl_runtime_payload_closeout(
            carrier=carrier,
            payload=opl_runtime_payload,
        )
    if not enable_opl_live_probe:
        return None
    deadline = time.monotonic() + DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS
    list_args = (
        "family-runtime",
        "queue",
        "list",
        "--domain",
        OPL_DOMAIN_ID,
        "--study",
        _text(carrier.get("study_id")) or "",
        "--task-kind",
        OPL_STAGE_ROUTE_TASK_KIND,
        "--json",
    )
    inspect_args_prefix = (
        "family-runtime",
        "queue",
        "inspect",
    )
    for candidate in _ranked_opl_bin_candidates():
        if not candidate.exists():
            continue
        list_payload = _run_opl_json(
            candidate,
            list_args,
            timeout_seconds=_remaining_seconds(deadline),
        )
        for task in _matching_opl_tasks_from_list(
            carrier=carrier,
            payload=list_payload,
        )[:DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT]:
            task_id = _text(task.get("task_id"))
            if task_id is None:
                continue
            inspect_payload = _run_opl_json(
                candidate,
                (
                    *inspect_args_prefix,
                    task_id,
                    "--json",
                ),
                timeout_seconds=_remaining_seconds(deadline),
            )
            matched = _matching_opl_runtime_payload_closeout(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched is not None:
                return matched
    return None


def _matching_opl_runtime_live_probe(
    *,
    carrier: Mapping[str, Any],
    opl_bin: str | Path | None = None,
) -> tuple[str, dict[str, Any], str] | None:
    if not _carrier_has_opl_route_identity(carrier):
        return None
    deadline = time.monotonic() + DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS
    list_args = (
        "family-runtime",
        "queue",
        "list",
        "--domain",
        OPL_DOMAIN_ID,
        "--study",
        _text(carrier.get("study_id")) or "",
        "--task-kind",
        OPL_STAGE_ROUTE_TASK_KIND,
        "--json",
    )
    terminal_match: tuple[dict[str, Any], str] | None = None
    inspect_args_prefix = (
        "family-runtime",
        "queue",
        "inspect",
    )
    for candidate in _ranked_opl_live_probe_bin_candidates(opl_bin=opl_bin):
        if not candidate.exists():
            continue
        list_payload = _run_opl_json(
            candidate,
            list_args,
            timeout_seconds=_remaining_seconds(deadline),
        )
        terminal_match = _matching_opl_runtime_payload_closeout(
            carrier=carrier,
            payload=list_payload,
        )
        if terminal_match is not None:
            closeout, closeout_ref = terminal_match
            return "terminal", closeout, closeout_ref
        matched_running = _matching_opl_runtime_payload_running_attempt(
            carrier=carrier,
            payload=list_payload,
        )
        for task in _ranked_opl_probe_tasks(
            _matching_opl_tasks_from_list(
                carrier=carrier,
                payload=list_payload,
            )
        )[:DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT]:
            task_id = _text(task.get("task_id"))
            if task_id is None:
                continue
            inspect_payload = _run_opl_json(
                candidate,
                (
                    *inspect_args_prefix,
                    task_id,
                    "--json",
                ),
                timeout_seconds=_remaining_seconds(deadline),
            )
            matched_terminal = _matching_opl_runtime_payload_closeout(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched_terminal is not None:
                closeout, closeout_ref = matched_terminal
                return "terminal", closeout, closeout_ref
            inspected_running = _matching_opl_runtime_payload_running_attempt(
                carrier=carrier,
                payload=inspect_payload,
            )
            if inspected_running is not None:
                matched_running = inspected_running
        if matched_running is not None:
            attempt, attempt_ref = matched_running
            return "running", attempt, attempt_ref
    return None


def _matching_opl_runtime_running_attempt(
    *,
    carrier: Mapping[str, Any],
    opl_runtime_payload: Mapping[str, Any] | None,
    enable_opl_live_probe: bool,
) -> tuple[dict[str, Any], str] | None:
    if not _carrier_has_opl_route_identity(carrier):
        return None
    if opl_runtime_payload is not None:
        return _matching_opl_runtime_payload_running_attempt(
            carrier=carrier,
            payload=opl_runtime_payload,
        )
    if not enable_opl_live_probe:
        return None
    deadline = time.monotonic() + DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS
    list_args = (
        "family-runtime",
        "queue",
        "list",
        "--domain",
        OPL_DOMAIN_ID,
        "--study",
        _text(carrier.get("study_id")) or "",
        "--task-kind",
        OPL_STAGE_ROUTE_TASK_KIND,
        "--json",
    )
    inspect_args_prefix = (
        "family-runtime",
        "queue",
        "inspect",
    )
    for candidate in _ranked_opl_bin_candidates():
        if not candidate.exists():
            continue
        list_payload = _run_opl_json(
            candidate,
            list_args,
            timeout_seconds=_remaining_seconds(deadline),
        )
        matched = _matching_opl_runtime_payload_running_attempt(
            carrier=carrier,
            payload=list_payload,
        )
        if matched is not None:
            return matched
        for task in _matching_opl_tasks_from_list(
            carrier=carrier,
            payload=list_payload,
        )[:DEFAULT_OPL_LIVE_PROBE_MAX_INSPECT_COUNT]:
            task_id = _text(task.get("task_id"))
            if task_id is None:
                continue
            inspect_payload = _run_opl_json(
                candidate,
                (
                    *inspect_args_prefix,
                    task_id,
                    "--json",
                ),
                timeout_seconds=_remaining_seconds(deadline),
            )
            matched = _matching_opl_runtime_payload_running_attempt(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched is not None:
                return matched
    return None


def _matching_opl_runtime_payload_closeout(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    runtime_task = _mapping(_mapping(payload).get("family_runtime_task"))
    if runtime_task:
        task = _mapping(runtime_task.get("task"))
        if not _matches_opl_task(carrier=carrier, task=task):
            return None
        closeout = _opl_task_terminal_closeout(
            carrier=carrier,
            task=task,
            stage_attempts=runtime_task.get("stage_attempts"),
            events=runtime_task.get("events"),
            runtime_readback_source="opl_family_runtime_queue_inspect",
        )
        if closeout is None:
            return None
        return closeout, _opl_task_closeout_ref(task)

    for task in _matching_opl_tasks_from_list(carrier=carrier, payload=payload):
        closeout = _opl_task_terminal_closeout(
            carrier=carrier,
            task=task,
            stage_attempts=(),
            events=(),
            runtime_readback_source="opl_family_runtime_queue_list",
        )
        if closeout is not None:
            return closeout, _opl_task_closeout_ref(task)
    return None


def _matching_opl_runtime_payload_running_attempt(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    runtime_task = _mapping(_mapping(payload).get("family_runtime_task"))
    if runtime_task:
        task = _mapping(runtime_task.get("task"))
        if not _matches_opl_task(carrier=carrier, task=task):
            return None
        attempt = _opl_task_running_attempt(
            carrier=carrier,
            task=task,
            stage_attempts=runtime_task.get("stage_attempts"),
            runtime_readback_source="opl_family_runtime_queue_inspect",
        )
        if attempt is None:
            return None
        return attempt, _opl_attempt_ref(attempt)

    for task in _matching_opl_tasks_from_list(carrier=carrier, payload=payload):
        attempt = _opl_task_running_attempt(
            carrier=carrier,
            task=task,
            stage_attempts=(),
            runtime_readback_source="opl_family_runtime_queue_list",
        )
        if attempt is not None:
            return attempt, _opl_attempt_ref(attempt)
    return None


def _matching_opl_tasks_from_list(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    queue = _mapping(_mapping(payload).get("family_runtime_queue"))
    tasks = queue.get("tasks")
    if not isinstance(tasks, list | tuple):
        return []
    return [
        dict(task)
        for task in tasks
        if isinstance(task, Mapping) and _matches_opl_task(carrier=carrier, task=task)
    ]


def _ranked_opl_probe_tasks(tasks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return sorted(tasks, key=_opl_probe_task_rank)


def _opl_probe_task_rank(task: Mapping[str, Any]) -> tuple[int, int, int, str]:
    reason = _first_text(task.get("last_error"), task.get("dead_letter_reason"))
    stale_rank = 1 if _non_current_closeout_reason(reason) else 0
    status = _text(task.get("status"))
    status_rank = {
        "running": 0,
        "queued": 1,
        "blocked": 2,
        "succeeded": 2,
        "failed": 3,
        "dead_letter": 4,
    }.get(status or "", 5)
    gate_rank = 0 if (reason or "").endswith("_domain_gate_pending") else 1
    return stale_rank, status_rank, gate_rank, _text(task.get("task_id")) or ""


def _matches_opl_task(
    *,
    carrier: Mapping[str, Any],
    task: Mapping[str, Any],
) -> bool:
    payload = _mapping(task.get("payload"))
    if _text(task.get("domain_id")) != OPL_DOMAIN_ID:
        return False
    if _text(task.get("task_kind")) != OPL_STAGE_ROUTE_TASK_KIND:
        return False
    if _text(payload.get("study_id")) != _text(carrier.get("study_id")):
        return False
    if _text(payload.get("paper_mission_transaction_ref")) != _text(
        carrier.get("paper_mission_transaction_ref")
    ):
        return False
    if _text(payload.get("opl_route_command_ref")) != _text(
        carrier.get("opl_route_command_ref")
    ):
        return False
    command_kind = _carrier_command_kind(carrier)
    if command_kind is not None and _text(payload.get("command_kind")) != command_kind:
        return False
    route_target = _carrier_route_target(carrier)
    if (
        route_target is not None
        and not _payload_binds_route_identity(carrier=carrier, payload=payload)
        and _text(payload.get("route_target")) != route_target
    ):
        return False
    return True


def _opl_task_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    task: Mapping[str, Any],
    stage_attempts: object,
    events: object,
    runtime_readback_source: str,
) -> dict[str, Any] | None:
    status = _text(task.get("status"))
    current_control = _mapping(task.get("current_control_state"))
    closeout_status = _text(current_control.get("closeout_receipt_status"))
    closeout_refs = _text_list(current_control.get("closeout_refs"))
    typed_blocker_refs = _text_list(current_control.get("typed_blocker_refs"))
    stage_attempt = _matching_opl_stage_attempt(
        carrier=carrier,
        current_control=current_control,
        stage_attempts=stage_attempts,
    )
    stage_status = _text(stage_attempt.get("status"))
    stage_closeout_status = _text(stage_attempt.get("closeout_receipt_status"))
    stage_closeout_refs = _text_list(stage_attempt.get("closeout_refs"))
    stage_typed_blocker_refs = _text_list(stage_attempt.get("typed_blocker_refs"))
    stage_terminal = stage_status in {"completed", "blocked", "failed", "dead_letter"}
    if status not in {"blocked", "dead_letter", "failed", "succeeded"} and not stage_terminal:
        return None
    if status == "succeeded" and not stage_terminal:
        return None
    if (
        closeout_status != "accepted_typed_closeout"
        and not typed_blocker_refs
        and stage_closeout_status != "accepted_typed_closeout"
        and not stage_typed_blocker_refs
        and not stage_closeout_refs
    ):
        return None
    route_target = _carrier_route_target(carrier)
    if (
        route_target is not None
        and not _payload_binds_route_identity(
            carrier=carrier,
            payload=_mapping(task.get("payload")),
        )
        and not _payload_binds_route_identity(
            carrier=carrier,
            payload=_mapping(stage_attempt.get("workspace_locator")),
        )
    ):
        attempt_stage = _text(stage_attempt.get("stage_id"))
        control_stage = _text(_mapping(current_control.get("stage_run_currentness_identity")).get("stage_id"))
        if (attempt_stage or control_stage) not in {None, route_target}:
            return None
    blocked_reason = _first_text(
        task.get("last_error"),
        task.get("dead_letter_reason"),
        current_control.get("blocker_reason"),
        stage_attempt.get("blocked_reason"),
        "domain_gate_pending",
    )
    if _non_current_closeout_reason(blocked_reason):
        return None
    closeout_refs = closeout_refs or stage_closeout_refs or _event_closeout_refs(events)
    typed_blocker_ref = (
        typed_blocker_refs[0]
        if typed_blocker_refs
        else stage_typed_blocker_refs[0]
        if stage_typed_blocker_refs
        else None
    )
    stage_attempt_id = (
        _text(current_control.get("current_stage_attempt_id"))
        or _text(stage_attempt.get("stage_attempt_id"))
    )
    return {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": stage_status or status,
        "study_id": _text(carrier.get("study_id")),
        "stage_id": route_target or _text(stage_attempt.get("stage_id")),
        "stage_attempt_id": stage_attempt_id,
        "work_unit_id": _text(carrier.get("work_unit_id")),
        "work_unit_fingerprint": _text(carrier.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(carrier.get("stage_terminal_decision_ref")),
        "provider_attempt_ref": (
            _text(stage_attempt.get("provider_attempt_ref"))
            or (f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else None)
        ),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "typed_blocker_ref": typed_blocker_ref,
        "blocked_reason": blocked_reason,
        "closeout_refs": closeout_refs,
        "task_id": _text(task.get("task_id")),
        "task_status": status,
        "closeout_receipt_status": closeout_status or stage_closeout_status,
        "runtime_readback_source": runtime_readback_source,
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def _opl_task_running_attempt(
    *,
    carrier: Mapping[str, Any],
    task: Mapping[str, Any],
    stage_attempts: object,
    runtime_readback_source: str,
) -> dict[str, Any] | None:
    current_control = _mapping(task.get("current_control_state"))
    if (
        _text(task.get("status")) != "running"
        and current_control.get("running_provider_attempt") is not True
    ):
        return None
    stage_attempt = _matching_opl_stage_attempt(
        carrier=carrier,
        current_control=current_control,
        stage_attempts=stage_attempts,
    )
    if not stage_attempt:
        linked = _mapping(task.get("linked_stage_attempt_liveness"))
        if linked and _matches_opl_stage_attempt(carrier=carrier, stage_attempt=linked):
            stage_attempt = linked
    stage_status = _text(stage_attempt.get("status"))
    provider_run = _mapping(stage_attempt.get("provider_run"))
    provider_status = _text(provider_run.get("provider_status"))
    if (
        stage_status not in {"running", "started", "queued", "live"}
        and provider_status != "running"
    ):
        return None
    stage_attempt_id = _text(stage_attempt.get("stage_attempt_id"))
    return {
        "surface_kind": "opl_stage_attempt_running_readback",
        "status": "running",
        "study_id": _text(carrier.get("study_id")),
        "stage_id": _carrier_route_target(carrier) or _text(stage_attempt.get("stage_id")),
        "stage_attempt_id": stage_attempt_id,
        "work_unit_id": _text(carrier.get("work_unit_id")),
        "work_unit_fingerprint": _text(carrier.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(carrier.get("stage_terminal_decision_ref")),
        "provider_attempt_ref": (
            _text(stage_attempt.get("provider_attempt_ref"))
            or (f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else None)
        ),
        "provider_kind": _text(stage_attempt.get("provider_kind")),
        "workflow_id": _text(stage_attempt.get("workflow_id"))
        or _text(provider_run.get("workflow_id")),
        "provider_status": provider_status or stage_status,
        "last_heartbeat_at": _text(provider_run.get("last_heartbeat_at")),
        "last_runner_event_kind": _text(provider_run.get("last_runner_event_kind")),
        "task_id": _text(task.get("task_id")),
        "task_status": _text(task.get("status")),
        "runtime_readback_source": runtime_readback_source,
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_paper_progress": False,
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def _matching_opl_stage_attempt(
    *,
    carrier: Mapping[str, Any],
    current_control: Mapping[str, Any],
    stage_attempts: object,
) -> dict[str, Any]:
    wanted = _text(current_control.get("current_stage_attempt_id"))
    if isinstance(stage_attempts, list | tuple):
        for item in stage_attempts:
            candidate = _mapping(item)
            if (
                wanted is not None
                and _text(candidate.get("stage_attempt_id")) == wanted
                and _matches_opl_stage_attempt(carrier=carrier, stage_attempt=candidate)
            ):
                return candidate
        for item in reversed(stage_attempts):
            candidate = _mapping(item)
            if candidate and _matches_opl_stage_attempt(
                carrier=carrier,
                stage_attempt=candidate,
            ):
                return candidate
    return {}


def _matches_opl_stage_attempt(
    *,
    carrier: Mapping[str, Any],
    stage_attempt: Mapping[str, Any],
) -> bool:
    route_target = _carrier_route_target(carrier)
    locator = _mapping(stage_attempt.get("workspace_locator"))
    if (
        route_target is not None
        and not _payload_binds_route_identity(carrier=carrier, payload=locator)
        and _text(stage_attempt.get("stage_id")) != route_target
    ):
        return False
    if not locator:
        return True
    if _text(locator.get("study_id")) != _text(carrier.get("study_id")):
        return False
    for field in ("paper_mission_transaction_ref", "opl_route_command_ref"):
        carrier_value = _text(carrier.get(field))
        if carrier_value is not None and _text(locator.get(field)) != carrier_value:
            return False
    command_kind = _carrier_command_kind(carrier)
    if command_kind is not None and _text(locator.get("command_kind")) != command_kind:
        return False
    if (
        route_target is not None
        and not _payload_binds_route_identity(carrier=carrier, payload=locator)
        and _text(locator.get("route_target")) != route_target
    ):
        return False
    return True


def _payload_binds_route_identity(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    expected_transaction_ref = _text(carrier.get("paper_mission_transaction_ref"))
    expected_route_ref = _text(carrier.get("opl_route_command_ref"))
    if expected_transaction_ref is None or expected_route_ref is None:
        return False
    return (
        _text(payload.get("paper_mission_transaction_ref")) == expected_transaction_ref
        and _text(payload.get("opl_route_command_ref")) == expected_route_ref
    )


def _opl_task_closeout_ref(task: Mapping[str, Any]) -> str:
    task_id = _text(task.get("task_id")) or "unknown"
    return f"opl://family-runtime/tasks/{task_id}/terminal-closeout-readback"


def _opl_attempt_ref(attempt: Mapping[str, Any]) -> str:
    stage_attempt_id = _text(attempt.get("stage_attempt_id")) or "unknown"
    return f"opl://stage-attempts/{stage_attempt_id}/running-readback"


def _event_closeout_refs(events: object) -> list[str]:
    if not isinstance(events, list | tuple):
        return []
    refs: list[str] = []
    for event in events:
        payload = _mapping(_mapping(event).get("payload"))
        for ref in _text_list(payload.get("closeout_refs")):
            if ref not in refs:
                refs.append(ref)
    return refs


def _matches_carrier(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    if _text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet":
        return False
    if _text(closeout.get("study_id")) != _text(carrier.get("study_id")):
        return False
    if _text(closeout.get("work_unit_id")) != _text(carrier.get("work_unit_id")):
        return False
    if _text(closeout.get("work_unit_fingerprint")) != _text(
        carrier.get("work_unit_fingerprint")
    ):
        return False
    route_target = _carrier_route_target(carrier)
    if route_target is not None and _text(closeout.get("stage_id")) != route_target:
        return False
    if _carrier_has_opl_route_identity(carrier) and (
        _non_current_closeout_reason(closeout.get("blocked_reason"))
        or not _closeout_binds_route_identity(closeout=closeout, carrier=carrier)
    ):
        return False
    if closeout.get("provider_completion_is_domain_completion") is True:
        return False
    if closeout.get("provider_completion_is_domain_ready") is True:
        return False
    if closeout.get("domain_completion_claimed") is True:
        return False
    if closeout.get("domain_ready_claimed") is True:
        return False
    boundary = _mapping(closeout.get("authority_boundary"))
    return boundary.get("record_only_surface") is True


def _closeout_binds_route_identity(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    refs = {
        ref
        for ref in (
            _text(closeout.get("stage_packet_ref")),
            _text(closeout.get("opl_route_command_ref")),
            _text(closeout.get("route_command_ref")),
            *_text_list(closeout.get("closeout_refs")),
        )
        if ref is not None
    }
    expected_refs = {
        ref
        for ref in (
            _text(carrier.get("paper_mission_transaction_ref")),
            _text(carrier.get("stage_terminal_decision_ref")),
            _text(carrier.get("opl_route_command_ref")),
        )
        if ref is not None
    }
    return bool(refs.intersection(expected_refs))


def _non_current_closeout_reason(value: object) -> bool:
    reason = _text(value)
    if reason is None:
        return False
    return reason == "stage_attempt_currentness_mismatch" or reason.startswith(
        "operator_retired_stale_runtime_residue:"
    )


def _carrier_has_opl_route_identity(carrier: Mapping[str, Any]) -> bool:
    return (
        _text(carrier.get("study_id")) is not None
        and _text(carrier.get("work_unit_id")) is not None
        and _text(carrier.get("work_unit_fingerprint")) is not None
        and
        _text(carrier.get("paper_mission_transaction_ref")) is not None
        and _text(carrier.get("opl_route_command_ref")) is not None
    )


def _carrier_command_kind(carrier: Mapping[str, Any]) -> str | None:
    route = _mapping(carrier.get("opl_route_command"))
    return _text(carrier.get("command_kind")) or _text(route.get("command_kind"))


def _carrier_route_target(carrier: Mapping[str, Any]) -> str | None:
    command_kind = _carrier_command_kind(carrier)
    route_target = _text(carrier.get("route_target"))
    route = _mapping(carrier.get("opl_route_command"))
    route_target = route_target or _text(route.get("target"))
    if command_kind in {"start_next_stage", "resume_stage", "route_back"}:
        return route_target
    return None


def _terminal_closeout_readback(
    *,
    closeout: Mapping[str, Any],
    closeout_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": _text(closeout.get("surface_kind")),
        "closeout_ref": closeout_ref,
        "status": _text(closeout.get("status")),
        "study_id": _text(closeout.get("study_id")),
        "stage_id": _text(closeout.get("stage_id")),
        "stage_attempt_id": _text(closeout.get("stage_attempt_id")),
        "work_unit_id": _text(closeout.get("work_unit_id")),
        "work_unit_fingerprint": _text(closeout.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(closeout.get("stage_packet_ref")),
        "provider_attempt_ref": _text(closeout.get("provider_attempt_ref")),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "typed_blocker_ref": _text(closeout.get("typed_blocker_ref")),
        "blocked_reason": _text(closeout.get("blocked_reason")),
        "closeout_refs": _text_list(closeout.get("closeout_refs")),
        "task_id": _text(closeout.get("task_id")),
        "task_status": _text(closeout.get("task_status")),
        "closeout_receipt_status": _text(closeout.get("closeout_receipt_status")),
        "runtime_readback_source": _text(closeout.get("runtime_readback_source")),
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def _running_attempt_readback(
    *,
    attempt: Mapping[str, Any],
    attempt_ref: str,
) -> dict[str, Any]:
    return {
        "surface_kind": _text(attempt.get("surface_kind")),
        "attempt_ref": attempt_ref,
        "status": _text(attempt.get("status")),
        "study_id": _text(attempt.get("study_id")),
        "stage_id": _text(attempt.get("stage_id")),
        "stage_attempt_id": _text(attempt.get("stage_attempt_id")),
        "work_unit_id": _text(attempt.get("work_unit_id")),
        "work_unit_fingerprint": _text(attempt.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(attempt.get("stage_packet_ref")),
        "provider_attempt_ref": _text(attempt.get("provider_attempt_ref")),
        "provider_kind": _text(attempt.get("provider_kind")),
        "workflow_id": _text(attempt.get("workflow_id")),
        "provider_status": _text(attempt.get("provider_status")),
        "last_heartbeat_at": _text(attempt.get("last_heartbeat_at")),
        "last_runner_event_kind": _text(attempt.get("last_runner_event_kind")),
        "task_id": _text(attempt.get("task_id")),
        "task_status": _text(attempt.get("task_status")),
        "runtime_readback_source": _text(attempt.get("runtime_readback_source")),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_paper_progress": False,
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "provider_completion_is_domain_ready": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _ranked_opl_bin_candidates(opl_bin: str | Path | None = None) -> list[Path]:
    if opl_bin is not None:
        explicit = Path(opl_bin).expanduser()
        if explicit.exists():
            return [explicit]
        resolved = shutil.which(str(opl_bin))
        return [Path(resolved).expanduser()] if resolved is not None else [explicit]
    configured = os.environ.get("OPL_BIN") or os.environ.get("OPL_FAMILY_RUNTIME_BIN")
    if configured:
        return [Path(configured).expanduser()]
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


def _ranked_opl_live_probe_bin_candidates(
    *, opl_bin: str | Path | None = None
) -> list[Path]:
    try:
        return _ranked_opl_bin_candidates(opl_bin=opl_bin)
    except TypeError:
        return _ranked_opl_bin_candidates()


def _run_opl_json(
    opl_bin: Path,
    args: tuple[str, ...],
    *,
    timeout_seconds: float = DEFAULT_OPL_READBACK_TIMEOUT_SECONDS,
) -> dict[str, Any] | None:
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
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


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


def _study_relative_ref(*, study_root: Path, path: Path) -> str:
    try:
        return str(path.resolve().relative_to(study_root.resolve()))
    except ValueError:
        return str(path.resolve())


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list | tuple):
        return []
    return [text for item in value if (text := _text(item)) is not None]


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text is not None:
            return text
    return None


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "RUNNING_READBACK_STATUS",
    "TERMINAL_READBACK_STATUS",
    "WAITING_READBACK_STATUS",
    "attach_opl_runtime_carrier_readback",
    "paper_mission_opl_runtime_carrier_readback",
]
