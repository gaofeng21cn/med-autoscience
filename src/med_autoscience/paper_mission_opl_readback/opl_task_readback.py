from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_opl_readback.primitives import (
    first_text as _first_text,
    idempotency_refs_mismatch as _idempotency_refs_mismatch,
    mapping as _mapping,
    text_list as _text_list,
    text_value as _text,
)
from med_autoscience.paper_mission_opl_readback.receipt_events import (
    OPL_DOMAIN_ROUTE_DOMAIN_ID,
    carrier_command_kind as _carrier_command_kind,
    carrier_route_target as _carrier_route_target,
    first_mas_impact_receipt as _first_mas_impact_receipt,
    first_opl_transition_receipt as _first_opl_transition_receipt,
    matches_receipt_command_kind as _matches_receipt_command_kind,
)
from med_autoscience.paper_mission_opl_readback.route_identity import (
    non_current_closeout_reason as _non_current_closeout_reason,
    payload_binds_route_identity as _payload_binds_route_identity,
)


OPL_DOMAIN_ID = OPL_DOMAIN_ROUTE_DOMAIN_ID
OPL_RUNTIME_DOMAIN_ID = "medautoscience"
LIVE_ATTEMPT_STATUSES = {"running", "checkpointed", "human_gate"}


def matching_opl_runtime_payload_closeout(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    query = _stage_attempt_query(payload)
    attempt = _matching_opl_stage_attempt(carrier=carrier, query=query)
    if attempt is None:
        return None
    for closeout_entry in reversed(_records(query.get("closeouts"))):
        closeout = _stage_attempt_closeout(
            carrier=carrier,
            attempt=attempt,
            packet=_mapping(closeout_entry.get("packet")),
        )
        if closeout is not None:
            return closeout, _closeout_ref(attempt=attempt, entry=closeout_entry)
    return None


def matching_opl_runtime_payload_running_attempt(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> tuple[dict[str, Any], str] | None:
    query = _stage_attempt_query(payload)
    attempt = _matching_opl_stage_attempt(carrier=carrier, query=query)
    if attempt is None or not _attempt_is_live(attempt):
        return None
    return _stage_attempt_running_projection(carrier=carrier, attempt=attempt), _attempt_ref(attempt)


def matching_opl_stage_attempts_from_list(
    *,
    carrier: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    attempts = _mapping(_mapping(payload).get("family_runtime_stage_attempts")).get("attempts")
    if not isinstance(attempts, list | tuple):
        return []
    return [
        dict(attempt)
        for attempt in attempts
        if isinstance(attempt, Mapping)
        and _matches_opl_stage_attempt_list_candidate(carrier=carrier, attempt=attempt)
    ]


def _stage_attempt_query(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    surface = _mapping(_mapping(payload).get("family_runtime_stage_attempt_query"))
    return _mapping(surface.get("stage_attempt_query"))


def _matching_opl_stage_attempt(
    *,
    carrier: Mapping[str, Any],
    query: Mapping[str, Any],
) -> dict[str, Any] | None:
    attempt = _mapping(query.get("attempt"))
    return dict(attempt) if _matches_opl_stage_attempt(carrier=carrier, attempt=attempt) else None


def _matches_opl_stage_attempt_list_candidate(
    *,
    carrier: Mapping[str, Any],
    attempt: Mapping[str, Any],
) -> bool:
    if _text(attempt.get("domain_id")) != OPL_RUNTIME_DOMAIN_ID:
        return False
    if _text(attempt.get("stage_attempt_id")) is None:
        return False
    locator = _mapping(attempt.get("workspace_locator"))
    study_id = _first_text(
        attempt.get("study_id"),
        attempt.get("quest_id"),
        locator.get("study_id"),
        locator.get("quest_id"),
    )
    return study_id == _text(carrier.get("study_id"))


def _matches_opl_stage_attempt(
    *,
    carrier: Mapping[str, Any],
    attempt: Mapping[str, Any],
) -> bool:
    if _text(attempt.get("domain_id")) != OPL_RUNTIME_DOMAIN_ID:
        return False
    if _text(attempt.get("stage_attempt_id")) is None:
        return False
    locator = _mapping(attempt.get("workspace_locator"))
    study_id = _first_text(locator.get("study_id"), locator.get("quest_id"), attempt.get("study_id"))
    if study_id != _text(carrier.get("study_id")):
        return False
    if not _payload_binds_route_identity(carrier=carrier, payload=locator):
        return False
    if _idempotency_refs_mismatch(expected_payload=carrier, observed_payload=attempt):
        return False
    if _idempotency_refs_mismatch(expected_payload=carrier, observed_payload=locator):
        return False
    command_kind = _carrier_command_kind(carrier)
    observed_command_kind = _first_text(locator.get("command_kind"), attempt.get("command_kind"))
    if not _matches_receipt_command_kind(
        carrier_command_kind=command_kind,
        observed_command_kind=observed_command_kind,
    ):
        return False
    route_target = _carrier_route_target(carrier)
    return route_target is None or _first_text(
        locator.get("route_target"), attempt.get("route_target")
    ) == route_target


def _stage_attempt_closeout(
    *,
    carrier: Mapping[str, Any],
    attempt: Mapping[str, Any],
    packet: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _text(packet.get("surface_kind")) != "stage_attempt_closeout_packet":
        return None
    stage_attempt_id = _text(attempt.get("stage_attempt_id"))
    if stage_attempt_id is None:
        return None
    if _first_text(packet.get("stage_attempt_id"), stage_attempt_id) != stage_attempt_id:
        return None
    if _first_text(packet.get("study_id"), carrier.get("study_id")) != _text(
        carrier.get("study_id")
    ):
        return None
    if any(
        packet.get(field) is True
        for field in (
            "provider_completion_is_domain_completion",
            "provider_completion_is_domain_ready",
            "domain_completion_claimed",
            "domain_ready_claimed",
        )
    ):
        return None
    blocked_reason = _first_text(packet.get("blocked_reason"), attempt.get("blocked_reason"))
    if _non_current_closeout_reason(blocked_reason):
        return None
    transition_receipt = _first_opl_transition_receipt(carrier, packet, attempt)
    if transition_receipt is None:
        return None
    if _text(transition_receipt.get("stage_attempt_id")) != stage_attempt_id:
        return None
    closeout_refs = _text_list(packet.get("closeout_refs")) or _text_list(attempt.get("closeout_refs"))
    closeout_receipt_status = _first_text(
        packet.get("closeout_receipt_status"), attempt.get("closeout_receipt_status")
    )
    if closeout_receipt_status != "accepted_typed_closeout" and not closeout_refs:
        return None
    locator = _mapping(attempt.get("workspace_locator"))
    route_impact = _mapping(packet.get("route_impact")) or _mapping(attempt.get("route_impact"))
    return {
        "surface_kind": "stage_attempt_closeout_packet",
        "status": _first_text(packet.get("status"), attempt.get("status")),
        "study_id": _text(carrier.get("study_id")),
        "stage_id": _carrier_route_target(carrier)
        or _first_text(packet.get("stage_id"), attempt.get("stage_id")),
        "stage_attempt_id": stage_attempt_id,
        "work_unit_id": _text(carrier.get("work_unit_id")),
        "work_unit_fingerprint": _text(carrier.get("work_unit_fingerprint")),
        "domain_route_handoff_ref": _text(carrier.get("domain_route_handoff_ref")),
        "domain_route_transaction_ref": _text(carrier.get("domain_route_transaction_ref")),
        "domain_route_command_ref": _text(carrier.get("domain_route_command_ref")),
        "stage_packet_ref": _text(carrier.get("stage_terminal_decision_ref")),
        "provider_attempt_ref": _first_text(
            packet.get("provider_attempt_ref"),
            attempt.get("provider_attempt_ref"),
            f"opl://stage-attempts/{stage_attempt_id}",
        ),
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "domain_completion_claimed": False,
        "domain_ready_claimed": False,
        "typed_blocker_ref": _first_text(
            packet.get("typed_blocker_ref"),
            transition_receipt.get("typed_runtime_blocker_ref"),
        ),
        "blocked_reason": blocked_reason,
        "closeout_refs": closeout_refs,
        "opl_transition_receipt": transition_receipt,
        **(
            {"mas_impact_receipt": impact_receipt}
            if (impact_receipt := _first_mas_impact_receipt(carrier, packet, attempt))
            else {}
        ),
        "closeout_receipt_status": closeout_receipt_status,
        "route_impact": route_impact,
        "dispatch_ref": _first_text(locator.get("dispatch_ref"), attempt.get("dispatch_ref")),
        "runtime_readback_source": "opl_family_runtime_stage_attempt_query",
        "authority_boundary": {
            "record_only_surface": True,
            "provider_completion_is_domain_completion": False,
            "artifact_mutation_authorized": False,
            "publication_eval_latest_write_authorized": False,
            "controller_decision_write_authorized": False,
        },
    }


def _stage_attempt_running_projection(
    *,
    carrier: Mapping[str, Any],
    attempt: Mapping[str, Any],
) -> dict[str, Any]:
    locator = _mapping(attempt.get("workspace_locator"))
    provider_run = _mapping(attempt.get("provider_run"))
    stage_attempt_id = _text(attempt.get("stage_attempt_id"))
    return {
        "surface_kind": "opl_stage_attempt_running_readback",
        "status": _text(attempt.get("status")),
        "study_id": _text(carrier.get("study_id")),
        "stage_id": _carrier_route_target(carrier) or _text(attempt.get("stage_id")),
        "stage_attempt_id": stage_attempt_id,
        "work_unit_id": _text(carrier.get("work_unit_id")),
        "work_unit_fingerprint": _text(carrier.get("work_unit_fingerprint")),
        "stage_packet_ref": _text(carrier.get("stage_terminal_decision_ref")),
        "provider_attempt_ref": _first_text(
            attempt.get("provider_attempt_ref"),
            f"opl://stage-attempts/{stage_attempt_id}",
        ),
        "provider_kind": _first_text(
            attempt.get("provider_kind"), provider_run.get("provider_kind")
        ),
        "workflow_id": _first_text(
            attempt.get("workflow_id"), provider_run.get("workflow_id")
        ),
        "provider_status": _first_text(
            provider_run.get("provider_status"), attempt.get("status")
        ),
        "last_heartbeat_at": _text(provider_run.get("last_heartbeat_at")),
        "last_runner_event_kind": _text(provider_run.get("last_runner_event_kind")),
        "action_type": _first_text(locator.get("action_type"), attempt.get("action_type")),
        "runtime_readback_source": "opl_family_runtime_stage_attempt_query",
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


def _attempt_is_live(attempt: Mapping[str, Any]) -> bool:
    provider_run = _mapping(attempt.get("provider_run"))
    return (
        _text(attempt.get("status")) in LIVE_ATTEMPT_STATUSES
        or _text(provider_run.get("provider_status")) in LIVE_ATTEMPT_STATUSES
    )


def _records(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _attempt_ref(attempt: Mapping[str, Any]) -> str:
    stage_attempt_id = _text(attempt.get("stage_attempt_id"))
    return f"opl://stage-attempts/{stage_attempt_id}" if stage_attempt_id else "opl://stage-attempts/unknown"


def _closeout_ref(*, attempt: Mapping[str, Any], entry: Mapping[str, Any]) -> str:
    stage_attempt_id = _text(attempt.get("stage_attempt_id")) or "unknown"
    closeout_id = _text(entry.get("closeout_id")) or "latest"
    return f"opl://stage-attempts/{stage_attempt_id}/closeouts/{closeout_id}"
