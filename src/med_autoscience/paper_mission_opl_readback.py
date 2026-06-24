from __future__ import annotations

import json
import os
import shutil
import subprocess
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
OPL_STAGE_ROUTE_TASK_KIND = "paper_mission/stage-route"
OPL_DOMAIN_ID = "medautoscience"


def paper_mission_opl_runtime_carrier_readback(
    *,
    carrier: Mapping[str, Any],
    study_root: Path,
    opl_runtime_payload: Mapping[str, Any] | None = None,
    enable_opl_live_probe: bool = True,
) -> dict[str, Any]:
    matched = _matching_terminal_closeout(carrier=carrier, study_root=study_root)
    if matched is None:
        matched = _matching_opl_runtime_terminal_closeout(
            carrier=carrier,
            opl_runtime_payload=opl_runtime_payload,
            enable_opl_live_probe=enable_opl_live_probe,
        )
    if matched is None:
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
    enable_opl_live_probe: bool = True,
) -> dict[str, Any]:
    result = dict(readback)
    carrier = _mapping(result.get("opl_runtime_carrier"))
    if not carrier:
        return result
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=study_root,
        enable_opl_live_probe=enable_opl_live_probe,
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
        list_payload = _run_opl_json(candidate, list_args)
        for task in _matching_opl_tasks_from_list(carrier=carrier, payload=list_payload):
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
            )
            matched = _matching_opl_runtime_payload_closeout(
                carrier=carrier,
                payload=inspect_payload,
            )
            if matched is not None:
                return matched
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
        list_payload = _run_opl_json(candidate, list_args)
        for task in _matching_opl_tasks_from_list(carrier=carrier, payload=list_payload):
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
        )
        if attempt is None:
            return None
        return attempt, _opl_attempt_ref(attempt)

    for task in _matching_opl_tasks_from_list(carrier=carrier, payload=payload):
        attempt = _opl_task_running_attempt(
            carrier=carrier,
            task=task,
            stage_attempts=(),
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
    if route_target is not None and _text(payload.get("route_target")) != route_target:
        return False
    return True


def _opl_task_terminal_closeout(
    *,
    carrier: Mapping[str, Any],
    task: Mapping[str, Any],
    stage_attempts: object,
    events: object,
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
    if route_target is not None:
        attempt_stage = _text(stage_attempt.get("stage_id"))
        control_stage = _text(_mapping(current_control.get("stage_run_currentness_identity")).get("stage_id"))
        if (attempt_stage or control_stage) not in {None, route_target}:
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
        "blocked_reason": _first_text(
            task.get("last_error"),
            task.get("dead_letter_reason"),
            current_control.get("blocker_reason"),
            stage_attempt.get("blocked_reason"),
            "domain_gate_pending",
        ),
        "closeout_refs": closeout_refs,
        "task_id": _text(task.get("task_id")),
        "task_status": status,
        "closeout_receipt_status": closeout_status or stage_closeout_status,
        "runtime_readback_source": "opl_family_runtime_queue_inspect",
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
) -> dict[str, Any] | None:
    if _text(task.get("status")) != "running":
        return None
    stage_attempt = _matching_opl_stage_attempt(
        carrier=carrier,
        current_control=_mapping(task.get("current_control_state")),
        stage_attempts=stage_attempts,
    )
    stage_status = _text(stage_attempt.get("status"))
    provider_run = _mapping(stage_attempt.get("provider_run"))
    provider_status = _text(provider_run.get("provider_status"))
    if stage_status not in {"running", "started", "queued"} and provider_status != "running":
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
        "runtime_readback_source": "opl_family_runtime_queue_inspect",
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
    if route_target is not None and _text(stage_attempt.get("stage_id")) != route_target:
        return False
    locator = _mapping(stage_attempt.get("workspace_locator"))
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
    if route_target is not None and _text(locator.get("route_target")) != route_target:
        return False
    return True


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


def _ranked_opl_bin_candidates() -> list[Path]:
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


def _run_opl_json(opl_bin: Path, args: tuple[str, ...]) -> dict[str, Any] | None:
    process: subprocess.Popen[str] | None = None
    try:
        process = subprocess.Popen(
            [str(opl_bin), *args],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            start_new_session=True,
        )
        stdout, _ = process.communicate(timeout=DEFAULT_OPL_READBACK_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired:
        if process is not None:
            process.kill()
            process.communicate()
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
