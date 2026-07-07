from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from med_autoscience.paper_mission_opl_readback.primitives import (
    first_text as _first_text,
    idempotency_refs_mismatch as _idempotency_refs_mismatch,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_opl_readback.receipt_events import (
    carrier_command_kind as _carrier_command_kind,
    carrier_route_target as _carrier_route_target,
    event_closeout_refs as _event_closeout_refs,
    event_mas_impact_receipt as _event_mas_impact_receipt,
    event_opl_transition_receipt as _event_opl_transition_receipt,
    first_mas_impact_receipt as _first_mas_impact_receipt,
    first_opl_transition_receipt as _first_opl_transition_receipt,
    matches_receipt_command_kind as _matches_receipt_command_kind,
)
from med_autoscience.paper_mission_opl_readback.route_identity import (
    non_current_closeout_reason as _non_current_closeout_reason,
    payload_binds_route_identity as _payload_binds_route_identity,
)


OPL_STAGE_ROUTE_TASK_KIND = "paper_mission/stage-route"
OPL_DOMAIN_ID = "medautoscience"


def matching_opl_runtime_payload_closeout(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    runtime_task = _mapping(_mapping(payload).get("family_runtime_task"))
    if runtime_task:
        task = _mapping(runtime_task.get("task"))
        if not matches_opl_task(carrier=carrier, task=task):
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

    for task in ranked_opl_probe_tasks(
        matching_opl_tasks_from_list(carrier=carrier, payload=payload),
        carrier=carrier,
    ):
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


def matching_opl_runtime_payload_running_attempt(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    runtime_task = _mapping(_mapping(payload).get("family_runtime_task"))
    if runtime_task:
        task = _mapping(runtime_task.get("task"))
        if not matches_opl_task(carrier=carrier, task=task):
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

    for task in ranked_opl_probe_tasks(
        matching_opl_tasks_from_list(carrier=carrier, payload=payload),
        carrier=carrier,
    ):
        attempt = _opl_task_running_attempt(
            carrier=carrier,
            task=task,
            stage_attempts=(),
            runtime_readback_source="opl_family_runtime_queue_list",
        )
        if attempt is not None:
            return attempt, _opl_attempt_ref(attempt)
    return None


def matching_opl_tasks_from_list(
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
        if isinstance(task, Mapping) and matches_opl_task(carrier=carrier, task=task)
    ]


def ranked_opl_probe_tasks(
    tasks: list[dict[str, Any]],
    *,
    carrier: Mapping[str, Any] | None = None,
) -> list[dict[str, Any]]:
    return sorted(tasks, key=lambda task: _opl_probe_task_rank(task, carrier=carrier))


def _opl_probe_task_rank(
    task: Mapping[str, Any],
    *,
    carrier: Mapping[str, Any] | None = None,
) -> tuple[int, int, int, int, float, float, int, str]:
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
        _task_created_rank(task),
        _task_recency_rank(task),
        gate_rank,
        _text(task.get("task_id")) or "",
    )


def _task_created_rank(task: Mapping[str, Any]) -> float:
    current_control = _mapping(task.get("current_control_state"))
    linked = _mapping(task.get("linked_stage_attempt_liveness"))
    timestamps = [
        _text(task.get("created_at")),
        _text(current_control.get("created_at")),
        _text(linked.get("created_at")),
    ]
    parsed = [_parse_timestamp(value) for value in timestamps if value is not None]
    newest = max((value for value in parsed if value is not None), default=0.0)
    return -newest


def _task_recency_rank(task: Mapping[str, Any]) -> float:
    timestamps = [
        _text(task.get("updated_at")),
        _text(task.get("created_at")),
    ]
    current_control = _mapping(task.get("current_control_state"))
    provider_run = _mapping(current_control.get("provider_run"))
    timestamps.extend(
        [
            _text(current_control.get("updated_at")),
            _text(current_control.get("last_heartbeat_at")),
            _text(provider_run.get("last_heartbeat_at")),
            _text(provider_run.get("updated_at")),
        ]
    )
    linked = _mapping(task.get("linked_stage_attempt_liveness"))
    linked_provider_run = _mapping(linked.get("provider_run"))
    timestamps.extend(
        [
            _text(linked.get("updated_at")),
            _text(linked.get("last_heartbeat_at")),
            _text(linked_provider_run.get("last_heartbeat_at")),
            _text(linked_provider_run.get("updated_at")),
        ]
    )
    parsed = [_parse_timestamp(value) for value in timestamps if value is not None]
    newest = max((value for value in parsed if value is not None), default=0.0)
    return -newest


def _parse_timestamp(value: str) -> float | None:
    normalized = value.strip()
    if not normalized:
        return None
    if normalized.endswith("Z"):
        normalized = f"{normalized[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def matches_opl_task(
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
    if _idempotency_refs_mismatch(
        expected_payload=carrier,
        observed_payload=payload,
    ):
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
        control_stage = _text(
            _mapping(current_control.get("stage_run_currentness_identity")).get("stage_id")
        )
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
    stage_attempt_id = _text(stage_attempt.get("stage_attempt_id")) or _text(
        current_control.get("current_stage_attempt_id")
    )
    if not stage_attempt and stage_attempt_id is not None:
        return {
            "surface_kind": "opl_stage_attempt_running_readback",
            "status": "running",
            "study_id": _text(carrier.get("study_id")),
            "stage_id": _carrier_route_target(carrier),
            "stage_attempt_id": stage_attempt_id,
            "work_unit_id": _text(carrier.get("work_unit_id")),
            "work_unit_fingerprint": _text(carrier.get("work_unit_fingerprint")),
            "stage_packet_ref": _text(carrier.get("stage_terminal_decision_ref")),
            "provider_attempt_ref": f"opl://stage-attempts/{stage_attempt_id}",
            "provider_kind": _text(task.get("provider_kind"))
            or _text(current_control.get("provider_kind")),
            "workflow_id": _text(current_control.get("workflow_id")),
            "provider_status": "running",
            "last_heartbeat_at": _text(current_control.get("last_heartbeat_at")),
            "last_runner_event_kind": _text(
                current_control.get("last_runner_event_kind")
            ),
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
    stage_status = _text(stage_attempt.get("status"))
    provider_run = _mapping(stage_attempt.get("provider_run"))
    provider_status = _text(provider_run.get("provider_status"))
    if (
        stage_status not in {"running", "started", "queued", "live"}
        and provider_status != "running"
    ):
        return None
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
    if _idempotency_refs_mismatch(
        expected_payload=carrier,
        observed_payload=locator,
    ):
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


def _opl_task_closeout_ref(task: Mapping[str, Any]) -> str:
    task_id = _text(task.get("task_id")) or "unknown"
    return f"opl://family-runtime/tasks/{task_id}/terminal-closeout-readback"


def _opl_attempt_ref(attempt: Mapping[str, Any]) -> str:
    stage_attempt_id = _text(attempt.get("stage_attempt_id")) or "unknown"
    return f"opl://stage-attempts/{stage_attempt_id}/running-readback"


__all__ = [
    "OPL_DOMAIN_ID",
    "OPL_STAGE_ROUTE_TASK_KIND",
    "matching_opl_runtime_payload_closeout",
    "matching_opl_runtime_payload_running_attempt",
    "matching_opl_tasks_from_list",
    "matches_opl_task",
    "ranked_opl_probe_tasks",
]
