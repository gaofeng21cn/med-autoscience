from __future__ import annotations

import time
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_opl_readback_parts.closeout_discovery import (
    matching_terminal_closeout as _discover_matching_terminal_closeout,
)
from med_autoscience.paper_mission_opl_readback_parts.next_action_envelope import (
    attach_paper_mission_next_action,
    paper_mission_next_action_envelope,
)
from med_autoscience.paper_mission_opl_readback_parts.opl_cli_probe import (
    DEFAULT_OPL_READBACK_TIMEOUT_SECONDS,
    DEV_OPL_BIN,
    PACKAGED_OPL_BIN,
    PATH_OPL_BIN,
    ranked_opl_bin_candidates,
    remaining_seconds,
    run_opl_json,
)
from med_autoscience.paper_mission_opl_readback_parts.primitives import (
    first_text as _first_text,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_opl_readback_parts.receipt_events import (
    carrier_command_kind as _carrier_command_kind,
    carrier_route_target as _carrier_route_target,
    event_closeout_refs as _event_closeout_refs,
    event_mas_impact_receipt as _event_mas_impact_receipt,
    event_opl_transition_receipt as _event_opl_transition_receipt,
    first_mas_impact_receipt as _first_mas_impact_receipt,
    first_opl_transition_receipt as _first_opl_transition_receipt,
    matches_mas_impact_receipt as _matches_mas_impact_receipt,
    matches_opl_transition_receipt as _matches_opl_transition_receipt,
    matches_receipt_command_kind as _matches_receipt_command_kind,
)
from med_autoscience.paper_mission_opl_readback_parts.runtime_readback_payloads import (
    accounting_mapping as _accounting_mapping,
    mas_receipt_consumption_readback as _mas_receipt_consumption_readback,
    opl_transition_receipt_readback as _opl_transition_receipt_readback,
    receipt_evidence_readback as _receipt_evidence_readback,
    running_attempt_readback as _running_attempt_readback,
    terminal_closeout_readback as _terminal_closeout_readback,
)


CLOSEOUT_RELATIVE_ROOTS = (
    Path("artifacts/supervision/consumer/owner_callable_adapter_receipt"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
)
WORKSPACE_CLOSEOUT_RELATIVE_ROOTS = (
    Path("ops/medautoscience/paper_mission_consumption_ledger"),
    Path("ops/medautoscience/paper_mission_stage_attempts"),
)
TERMINAL_READBACK_STATUS = "opl_runtime_terminal_readback_observed"
RUNNING_READBACK_STATUS = "opl_runtime_attempt_running_observed"
WAITING_READBACK_STATUS = "waiting_for_opl_runtime_live_readback"
DEFAULT_OPL_LIVE_PROBE_BUDGET_SECONDS = 30.0
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
    terminal_closeout = _terminal_closeout_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
    )
    opl_transition_receipt = _opl_transition_receipt_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
    )
    receipt_evidence = _receipt_evidence_readback(
        closeout=closeout,
        closeout_ref=closeout_ref,
        opl_transition_receipt=opl_transition_receipt,
    )
    mas_receipt_consumption = _mas_receipt_consumption_readback(
        receipt_evidence=receipt_evidence,
    )
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
        "terminal_closeout": terminal_closeout,
        **(
            {"opl_transition_receipt": opl_transition_receipt}
            if opl_transition_receipt
            else {}
        ),
        **({"receipt_evidence": receipt_evidence} if receipt_evidence else {}),
        **(
            {"mas_receipt_consumption": mas_receipt_consumption}
            if mas_receipt_consumption
            else {}
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
    return _discover_matching_terminal_closeout(
        carrier=carrier,
        study_root=study_root,
        closeout_relative_roots=CLOSEOUT_RELATIVE_ROOTS,
        workspace_closeout_relative_roots=WORKSPACE_CLOSEOUT_RELATIVE_ROOTS,
        matches_carrier=_matches_carrier,
    )

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
            timeout_seconds=remaining_seconds(deadline),
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
                timeout_seconds=remaining_seconds(deadline),
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
            timeout_seconds=remaining_seconds(deadline),
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
            _matching_opl_tasks_from_list(carrier=carrier, payload=list_payload),
            carrier=carrier,
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
                timeout_seconds=remaining_seconds(deadline),
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
            timeout_seconds=remaining_seconds(deadline),
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
                timeout_seconds=remaining_seconds(deadline),
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

def _ranked_opl_probe_tasks(
    tasks: list[dict[str, Any]],
    *,
    carrier: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return sorted(tasks, key=lambda task: _opl_probe_task_rank(task, carrier=carrier))

def _opl_probe_task_rank(
    task: Mapping[str, Any],
    *,
    carrier: Mapping[str, Any] | None = None,
) -> tuple[int, int, int, int, int, str]:
    reason = _first_text(task.get("last_error"), task.get("dead_letter_reason"))
    stale_rank = 1 if _non_current_closeout_reason(reason) else 0
    payload = _mapping(task.get("payload"))
    route_target = _carrier_route_target(_mapping(carrier))
    target_rank = (
        0
        if route_target is not None and _text(payload.get("route_target")) == route_target
        else 1
    )
    command_kind = _carrier_command_kind(_mapping(carrier))
    command_rank = (
        0
        if command_kind is not None and _text(payload.get("command_kind")) == command_kind
        else 1
    )
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
    return (
        stale_rank,
        target_rank,
        command_rank,
        status_rank,
        gate_rank,
        _text(task.get("task_id")) or "",
    )

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
    if not _matches_receipt_command_kind(
        carrier_command_kind=command_kind,
        observed_command_kind=_text(payload.get("command_kind")),
    ):
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
    opl_transition_receipt = _first_opl_transition_receipt(
        carrier,
        current_control,
        stage_attempt,
        task,
    ) or _event_opl_transition_receipt(events=events, carrier=carrier)
    if opl_transition_receipt is None:
        return None
    mas_impact_receipt = _first_mas_impact_receipt(
        carrier,
        current_control,
        stage_attempt,
        task,
    ) or _event_mas_impact_receipt(events=events, carrier=carrier)
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
        **(
            {"opl_transition_receipt": opl_transition_receipt}
            if opl_transition_receipt
            else {}
        ),
        **({"mas_impact_receipt": mas_impact_receipt} if mas_impact_receipt else {}),
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
    if not _matches_receipt_command_kind(
        carrier_command_kind=command_kind,
        observed_command_kind=_text(locator.get("command_kind")),
    ):
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

def _matches_carrier(
    *,
    closeout: Mapping[str, Any],
    carrier: Mapping[str, Any],
) -> bool:
    if _text(closeout.get("surface_kind")) != "stage_attempt_closeout_packet":
        return False
    if _text(closeout.get("study_id")) != _text(carrier.get("study_id")):
        return False
    has_route_identity = _carrier_has_opl_route_identity(carrier)
    closeout_fingerprint = _text(closeout.get("work_unit_fingerprint"))
    if not has_route_identity or not _closeout_binds_route_identity(
        closeout=closeout,
        carrier=carrier,
    ):
        if _text(closeout.get("work_unit_id")) != _text(carrier.get("work_unit_id")):
            return False
        if closeout_fingerprint is not None and closeout_fingerprint != _text(
            carrier.get("work_unit_fingerprint")
        ):
            return False
    route_target = _carrier_route_target(carrier)
    if route_target is not None and _text(closeout.get("stage_id")) != route_target:
        return False
    if has_route_identity and (
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
    return _closeout_is_record_only(closeout)

def _closeout_is_record_only(closeout: Mapping[str, Any]) -> bool:
    boundary = _mapping(closeout.get("authority_boundary"))
    if boundary.get("record_only_surface") is False:
        return False
    if boundary.get("record_only_surface") is True:
        return True
    false_authority_fields = (
        "writes_authority",
        "writes_runtime",
        "writes_yang_authority",
        "writes_current_package",
        "writes_publication_eval",
        "writes_controller_decision",
        "writes_owner_receipt",
        "writes_typed_blocker",
        "writes_human_gate",
        "writes_runtime_queue_or_provider_attempt",
    )
    if not false_authority_fields or not any(field in boundary for field in false_authority_fields):
        return False
    if any(boundary.get(field) is not False for field in false_authority_fields if field in boundary):
        return False
    false_claim_fields = (
        "can_claim_paper_progress",
        "can_claim_submission_ready",
        "can_claim_publication_ready",
        "can_claim_current_package",
    )
    return not any(boundary.get(field) is True for field in false_claim_fields)

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
        and _text(carrier.get("paper_mission_transaction_ref")) is not None
        and _text(carrier.get("opl_route_command_ref")) is not None
    )

def _ranked_opl_bin_candidates(opl_bin: str | Path | None = None) -> list[Path]:
    return ranked_opl_bin_candidates(opl_bin=opl_bin)

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
    return run_opl_json(opl_bin, args, timeout_seconds=timeout_seconds)


__all__ = [
    "RUNNING_READBACK_STATUS",
    "TERMINAL_READBACK_STATUS",
    "WAITING_READBACK_STATUS",
    "attach_opl_runtime_carrier_readback",
    "attach_paper_mission_next_action",
    "paper_mission_opl_runtime_carrier_readback",
    "paper_mission_next_action_envelope",
]
