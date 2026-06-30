from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    OPL_RUNTIME_TERMINAL_BLOCKERS,
)
from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME,
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)

from ..opl_current_control_state_handoff_values import (
    _number_value,
    _observability_mapping,
    _string_list,
    _work_unit_identity,
)
from ..opl_current_control_state_terminal_logs import _source_path_mtime
from ..shared_base import _mapping_copy, _non_empty_text

LIVE_ATTEMPT_SUPERSEDED_BLOCKERS = frozenset(
    {
        "blocked:unsupported_dispatch_surface",
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_execution_authorization_required",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "opl_stage_attempt_admission_required",
        "repair_progress_ai_reviewer_recheck_required",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS = frozenset(
    {
        "external_supervisor",
        "one-person-lab",
    }
)
TERMINAL_STAGE_LOG_STATUSES = frozenset(
    {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
        "typed_blocker",
    }
)

def _stage_ref_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    refs: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in refs:
            refs.append(text)
    return refs

def _action_with_handoff_packet_readback(action: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(action)
    handoff_packet = _observability_mapping(updated.get("handoff_packet"))
    if not handoff_packet:
        return updated
    for key in (
        "opl_domain_progress_transition_live_readback",
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_transition_result",
        "opl_domain_progress_runtime_result",
        "opl_runtime_result",
        "domain_progress_transition_runtime",
        "domain_progress_transition_runtime_result",
    ):
        if key not in updated and key in handoff_packet:
            updated[key] = handoff_packet[key]
    return updated


def _apply_matching_terminal_closeout_to_handoff(projection: dict[str, Any]) -> dict[str, Any]:
    if not _handoff_has_matching_terminal_closeout(projection):
        return projection
    updated = dict(projection)
    terminal = _observability_mapping(updated.get("latest_terminal_stage_log"))
    updated["running_provider_attempt"] = False
    updated["runtime_owner"] = None
    updated["provider_attempt_owner"] = None
    updated["queue_owner"] = None
    updated["active_run_id"] = None
    updated["active_workflow_id"] = None
    updated["active_stage_attempt_id"] = (
        _non_empty_text(terminal.get("stage_attempt_id"))
        or _non_empty_text(updated.get("active_stage_attempt_id"))
    )
    runtime_health = _observability_mapping(updated.get("runtime_health"))
    if runtime_health:
        runtime_health["runtime_liveness_status"] = "terminal"
        runtime_health["health_status"] = "terminal"
        updated["runtime_health"] = runtime_health
    provider_admission_pending = int(updated.get("provider_admission_pending_count") or 0) > 0
    transition_request_pending = int(updated.get("transition_request_pending_count") or 0) > 0
    if provider_admission_pending or transition_request_pending:
        provider_admission_candidates = _handoff_candidate_list(updated.get("provider_admission_candidates"))
        transition_request_candidates = _handoff_candidate_list(updated.get("transition_request_candidates"))
        matching_provider_admissions = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=provider_admission_candidates,
        )
        matching_transition_requests = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=transition_request_candidates,
        )
        if (
            _handoff_has_complete_current_transition_readback(updated)
            and provider_admission_pending
            and not matching_provider_admissions
            and not matching_transition_requests
        ):
            return projection
        if (
            matching_provider_admissions
            and any(provider_admission_opl_transition_readback(item) for item in matching_provider_admissions)
            and not _terminal_closeout_has_domain_delta(terminal)
        ):
            return projection
        if (
            (provider_admission_candidates or transition_request_candidates)
            and not matching_provider_admissions
            and not matching_transition_requests
        ):
            return projection
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        updated["transition_request_pending_count"] = 0
        updated["transition_request_candidates"] = []
        updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
            terminal=terminal,
            matching_provider_admission=matching_provider_admissions[0]
            if matching_provider_admissions
            else matching_transition_requests[0]
            if matching_transition_requests
            else None,
        )
    else:
        matching_consumed_action = _terminal_closeout_consumed_current_action_projection(
            terminal=terminal,
            projection=updated,
        )
        if matching_consumed_action is not None:
            updated["provider_admission_pending_count"] = 0
            updated["provider_admission_candidates"] = []
            updated["transition_request_pending_count"] = 0
            updated["transition_request_candidates"] = []
            updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
                terminal=terminal,
                matching_provider_admission=matching_consumed_action,
            )
    updated = _apply_terminal_closeout_next_owner(updated, terminal=terminal)
    return _apply_terminal_closeout_owner_answer_gate(updated)


def _apply_terminal_closeout_next_owner(
    projection: dict[str, Any],
    *,
    terminal: Mapping[str, Any],
) -> dict[str, Any]:
    next_owner = _terminal_closeout_next_owner(terminal) or _terminal_closeout_next_owner(projection)
    if next_owner is None:
        return projection
    owner_action = _terminal_closeout_next_owner_action(terminal) or _terminal_closeout_next_owner_action(projection)
    updated = dict(projection)
    updated["next_owner"] = next_owner
    owner_route = _observability_mapping(updated.get("owner_route"))
    if owner_route:
        owner_route["next_owner"] = next_owner
        updated["owner_route"] = owner_route
    current = _observability_mapping(updated.get("current_work_unit"))
    if current and _non_empty_text(current.get("status")) in {"executable_owner_action", "owner_receipt_recorded"}:
        current["owner"] = next_owner
        _apply_owner_action_identity_to_current_work_unit(current, owner_action=owner_action)
        updated["current_work_unit"] = current
    envelope = _observability_mapping(updated.get("current_execution_envelope"))
    if envelope and _non_empty_text(envelope.get("state_kind")) in {"executable_owner_action", "owner_receipt_recorded"}:
        envelope["owner"] = next_owner
        next_work_unit = _work_unit_identity(owner_action.get("work_unit_id")) or _work_unit_identity(
            owner_action.get("next_work_unit")
        )
        if next_work_unit is not None:
            envelope["next_work_unit"] = next_work_unit
        updated["current_execution_envelope"] = envelope
    return updated


def _terminal_closeout_next_owner_action(value: Mapping[str, Any]) -> dict[str, Any]:
    paper_log = _observability_mapping(value.get("paper_stage_log"))
    next_forced = _observability_mapping(value.get("next_forced_delta")) or _observability_mapping(
        paper_log.get("next_forced_delta")
    )
    return _observability_mapping(next_forced.get("owner_action"))


def _apply_owner_action_identity_to_current_work_unit(
    current: dict[str, Any],
    *,
    owner_action: Mapping[str, Any],
) -> None:
    if not owner_action:
        return
    action_type = _non_empty_text(owner_action.get("action_type"))
    if action_type is not None:
        current["action_type"] = action_type
    work_unit = _work_unit_identity(owner_action.get("work_unit_id")) or _work_unit_identity(
        owner_action.get("next_work_unit")
    )
    if work_unit is not None:
        current["work_unit_id"] = work_unit
    fingerprint = _non_empty_text(owner_action.get("work_unit_fingerprint")) or _non_empty_text(
        owner_action.get("action_fingerprint")
    )
    if fingerprint is not None:
        current["work_unit_fingerprint"] = fingerprint
        current["action_fingerprint"] = fingerprint
    state = _observability_mapping(current.get("state"))
    if state:
        if action_type is not None:
            state["action_type"] = action_type
        if work_unit is not None:
            state["next_work_unit"] = work_unit
        current["state"] = state


def _terminal_closeout_next_owner(value: Mapping[str, Any]) -> str | None:
    owner_action = _terminal_closeout_next_owner_action(value)
    paper_log = _observability_mapping(value.get("paper_stage_log"))
    next_forced = _observability_mapping(value.get("next_forced_delta")) or _observability_mapping(
        paper_log.get("next_forced_delta")
    )
    owner_route = _observability_mapping(value.get("owner_route"))
    return (
        _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
        or _non_empty_text(next_forced.get("next_owner"))
        or _non_empty_text(next_forced.get("owner"))
        or _non_empty_text(value.get("next_executable_owner"))
        or _non_empty_text(value.get("next_owner"))
        or _non_empty_text(value.get("owner"))
        or _non_empty_text(owner_route.get("next_owner"))
        or _non_empty_text(paper_log.get("current_owner"))
    )


def _handoff_candidate_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


def _terminal_matching_handoff_candidates(
    *,
    terminal: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        item
        for item in candidates
        if _terminal_closeout_matches_handoff_action(terminal=terminal, action=item)
    ]


def _terminal_closeout_consumed_current_action_projection(
    *,
    terminal: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(terminal.get("owner_receipt_ref")) is None:
        return None
    for source in (
        projection.get("current_work_unit"),
        projection.get("current_execution_envelope"),
        projection,
    ):
        action = _terminal_closeout_action_projection_from_source(source)
        if action and _terminal_closeout_matches_handoff_action(terminal=terminal, action=action):
            return action
    return None


def _terminal_closeout_action_projection_from_source(source: object) -> dict[str, Any]:
    mapping = _observability_mapping(source)
    if not mapping:
        return {}
    state = _observability_mapping(mapping.get("state"))
    identity = _observability_mapping(mapping.get("provider_admission_identity"))
    source_refs = _observability_mapping(mapping.get("source_refs"))
    action = {
        "status": _non_empty_text(mapping.get("status")) or "provider_admission_pending",
        "study_id": _non_empty_text(mapping.get("study_id")),
        "quest_id": _non_empty_text(mapping.get("quest_id")),
        "action_type": _non_empty_text(mapping.get("action_type")) or _non_empty_text(state.get("action_type")),
        "work_unit_id": _work_unit_identity(mapping.get("work_unit_id"))
        or _work_unit_identity(mapping.get("next_work_unit"))
        or _work_unit_identity(state.get("next_work_unit"))
        or _work_unit_identity(state.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(mapping.get("work_unit_fingerprint"))
        or _non_empty_text(mapping.get("action_fingerprint"))
        or _non_empty_text(state.get("work_unit_fingerprint"))
        or _non_empty_text(state.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(mapping.get("action_fingerprint"))
        or _non_empty_text(mapping.get("work_unit_fingerprint"))
        or _non_empty_text(state.get("action_fingerprint"))
        or _non_empty_text(state.get("work_unit_fingerprint")),
        "route_identity_key": _non_empty_text(mapping.get("route_identity_key"))
        or _non_empty_text(identity.get("route_identity_key"))
        or _non_empty_text(source_refs.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(mapping.get("attempt_idempotency_key"))
        or _non_empty_text(identity.get("attempt_idempotency_key"))
        or _non_empty_text(source_refs.get("attempt_idempotency_key")),
        "idempotency_key": _non_empty_text(mapping.get("idempotency_key"))
        or _non_empty_text(identity.get("idempotency_key"))
        or _non_empty_text(source_refs.get("idempotency_key")),
        "stage_packet_ref": _non_empty_text(mapping.get("stage_packet_ref"))
        or _non_empty_text(source_refs.get("stage_packet_ref")),
        "stage_packet_refs": _stage_ref_items(mapping.get("stage_packet_refs"))
        or _stage_ref_items(source_refs.get("stage_packet_refs")),
        "provider_admission_identity": identity,
        "source_refs": source_refs,
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def _provider_admission_terminal_closeout_consumed(
    *,
    terminal: Mapping[str, Any],
    matching_provider_admission: Mapping[str, Any] | None,
) -> dict[str, Any]:
    admission = _observability_mapping(matching_provider_admission)
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    next_forced_delta = _observability_mapping(paper_stage_log.get("next_forced_delta"))
    owner_action = _observability_mapping(next_forced_delta.get("owner_action"))
    consumed = {
        "surface_kind": "provider_admission_terminal_closeout_consumed",
        "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
        "stage_attempt_id": _non_empty_text(terminal.get("stage_attempt_id")),
        "action_type": _non_empty_text(admission.get("action_type"))
        or _non_empty_text(terminal.get("action_type"))
        or _non_empty_text(owner_action.get("action_type")),
        "closeout_action_type": _non_empty_text(terminal.get("action_type")),
        "work_unit_id": _work_unit_identity(terminal.get("work_unit_id"))
        or _work_unit_identity(admission.get("work_unit_id"))
        or _work_unit_identity(admission.get("next_work_unit"))
        or _work_unit_identity(next_forced_delta.get("work_unit_id"))
        or _work_unit_identity(owner_action.get("work_unit_id"))
        or _work_unit_identity(owner_action.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(terminal.get("work_unit_fingerprint"))
        or _non_empty_text(admission.get("work_unit_fingerprint"))
        or _non_empty_text(admission.get("action_fingerprint"))
        or _non_empty_text(admission.get("fingerprint"))
        or _non_empty_text(owner_action.get("work_unit_fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(terminal.get("action_fingerprint"))
        or _non_empty_text(admission.get("action_fingerprint"))
        or _non_empty_text(admission.get("work_unit_fingerprint"))
        or _non_empty_text(admission.get("fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint"))
        or _non_empty_text(owner_action.get("work_unit_fingerprint")),
        "owner_receipt_ref": _non_empty_text(terminal.get("owner_receipt_ref")),
        "typed_blocker_ref": _non_empty_text(terminal.get("typed_blocker_ref")),
        "route_identity_key": _non_empty_text(terminal.get("route_identity_key"))
        or _non_empty_text(admission.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(terminal.get("attempt_idempotency_key"))
        or _non_empty_text(admission.get("attempt_idempotency_key")),
        "closeout_receipt_status": _non_empty_text(terminal.get("closeout_receipt_status")),
        "authority_boundary": {
            "projection_only": True,
            "runtime_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "can_authorize_provider_admission": False,
            "can_start_provider_attempt": False,
            "provider_completion_is_domain_completion": False,
        },
    }
    return {key: value for key, value in consumed.items() if value not in (None, "", [], {})}


def _apply_terminal_closeout_owner_answer_gate(projection: dict[str, Any]) -> dict[str, Any]:
    terminal = _observability_mapping(projection.get("latest_terminal_stage_log"))
    if not terminal or _terminal_closeout_has_owner_answer(terminal, projection):
        return projection
    action_queue = [dict(item) for item in projection.get("action_queue") or [] if isinstance(item, Mapping)]
    matching_actions = [
        item
        for item in action_queue
        if _terminal_closeout_matches_handoff_action(terminal=terminal, action=item)
    ]
    if action_queue and not matching_actions:
        return projection
    updated = dict(projection)
    blocker = _terminal_closeout_owner_answer_blocker(
        terminal=terminal,
        matching_action=matching_actions[0] if matching_actions else None,
    )
    updated["typed_blocker"] = blocker
    updated["blocked_reason"] = blocker["blocker_id"]
    updated["next_owner"] = blocker["owner"]
    updated["external_supervisor_required"] = True
    updated["terminal_closeout_consumed"] = True
    why_not_applied = _string_list(updated.get("why_not_applied"))
    if blocker["blocker_id"] not in why_not_applied:
        why_not_applied.append(blocker["blocker_id"])
    updated["why_not_applied"] = why_not_applied
    if matching_actions:
        source_ref = _non_empty_text(terminal.get("record_path")) or _non_empty_text(terminal.get("source_path"))
        updated["consumed_action_queue"] = [
            {
                **dict(item),
                "consumption": {
                    **_observability_mapping(item.get("consumption")),
                    "state": "consumed_by_terminal_stage_closeout",
                    "typed_blocker_ref": source_ref,
                },
            }
            for item in matching_actions
        ]
        updated["action_queue"] = [
            dict(item)
            for item in action_queue
            if item not in matching_actions
        ]
    return updated


def _terminal_closeout_has_owner_answer(
    terminal: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> bool:
    if _observability_mapping(projection.get("latest_typed_owner_callable_closeout")):
        return True
    if _non_empty_text(terminal.get("closeout_receipt_status")) == "accepted_typed_closeout":
        return True
    if _observability_mapping(projection.get("typed_blocker")):
        return True
    if _observability_mapping(terminal.get("typed_blocker")):
        return True
    if _non_empty_text(terminal.get("typed_blocker_ref")) or _non_empty_text(terminal.get("owner_receipt_ref")):
        return True
    if _string_list(terminal.get("typed_blocker_refs")) or _string_list(terminal.get("owner_receipt_refs")):
        return True
    if _non_empty_text(terminal.get("route_outcome")) == "owner_receipt":
        return True
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    if _terminal_stage_log_has_next_owner_handoff(terminal=terminal, paper_stage_log=paper_stage_log):
        return True
    if _string_list(paper_stage_log.get("changed_paper_surfaces")):
        return True
    outcome = _non_empty_text(paper_stage_log.get("outcome"))
    return outcome in {
        "blocked_with_domain_typed_blocker",
        "owner_receipt",
        "owner_receipt_recorded",
        "handoff_ready",
        "next_handoff",
    }


def _terminal_stage_log_has_next_owner_handoff(
    *,
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> bool:
    next_forced_delta = _observability_mapping(terminal.get("next_forced_delta")) or _observability_mapping(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _observability_mapping(next_forced_delta.get("owner_action"))
    if (
        _non_empty_text(owner_action.get("action_type")) is not None
        and (
            _non_empty_text(owner_action.get("next_owner")) is not None
            or _non_empty_text(owner_action.get("owner")) is not None
        )
        and (
            _non_empty_text(owner_action.get("work_unit_id")) is not None
            or _non_empty_text(owner_action.get("next_work_unit")) is not None
            or _non_empty_text(next_forced_delta.get("work_unit_id")) is not None
        )
    ):
        return True
    if _non_empty_text(terminal.get("status")) != "closed_with_domain_owner_refs":
        return False
    domain_refs = _observability_mapping(terminal.get("domain_owner_refs"))
    return any(
        _non_empty_text(domain_refs.get(key)) is not None
        for key in (
            "next_dispatch_ref",
            "next_request_ref",
            "next_owner_ref",
            "route_back_evidence_ref",
        )
    )


def _terminal_closeout_matches_handoff_action(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if _action_requires_identity_bound_terminal_closeout(action):
        return _terminal_closeout_matches_action_bound_identity(terminal=terminal, action=action)
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    action_attempt_id = _non_empty_text(action.get("stage_attempt_id")) or _non_empty_text(
        action.get("active_stage_attempt_id")
    )
    if terminal_attempt_id and action_attempt_id:
        return terminal_attempt_id == action_attempt_id
    terminal_action_type = _non_empty_text(terminal.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if terminal_action_type and action_type and terminal_action_type != action_type:
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit and action_work_unit:
        return terminal_work_unit == action_work_unit
    return terminal_action_type is not None and terminal_action_type == action_type


def _action_requires_identity_bound_terminal_closeout(action: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(action):
        return True
    if _non_empty_text(action.get("status")) not in {
        "provider_admission_pending",
        "transition_request_pending",
    }:
        return False
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    if not identity:
        identity_sources = (action, source_refs)
    else:
        identity_sources = (action, identity, source_refs)
    return any(
        _non_empty_text(source.get(key)) is not None
        for source in identity_sources
        for key in (
            "stage_run_id",
            "stage_attempt_id",
            "active_stage_attempt_id",
            "route_identity_key",
            "attempt_idempotency_key",
            "idempotency_key",
            "stage_packet_ref",
            "stage_packet_path",
            "dispatch_ref",
            "dispatch_path",
        )
    ) or bool(_stage_packet_refs(action))


def _terminal_closeout_matches_action_bound_identity(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if (
        provider_admission_opl_transition_readback(action)
        and not _terminal_closeout_action_identity_matches_candidate(
            terminal=terminal,
            action=action,
        )
    ):
        return False
    if _terminal_closeout_request_wrapper_identity_matches_candidate(terminal=terminal, action=action):
        return True
    if not _terminal_closeout_action_identity_matches_candidate(
        terminal=terminal,
        action=action,
    ):
        return False
    terminal_stage_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if terminal_stage_attempt_id is not None and terminal_stage_attempt_id in _action_stage_run_ids(action):
        return True
    terminal_route_identity_key = _non_empty_text(terminal.get("route_identity_key"))
    if terminal_route_identity_key is not None and terminal_route_identity_key in _action_route_identity_keys(action):
        return True
    terminal_attempt_idempotency_key = _non_empty_text(terminal.get("attempt_idempotency_key"))
    if (
        terminal_attempt_idempotency_key is not None
        and terminal_attempt_idempotency_key in _action_attempt_idempotency_keys(action)
    ):
        return True
    terminal_idempotency_key = _non_empty_text(terminal.get("idempotency_key"))
    if terminal_idempotency_key is not None and terminal_idempotency_key in _action_idempotency_keys(action):
        return True
    terminal_stage_packet_refs = _stage_packet_refs(terminal)
    if terminal_stage_packet_refs and terminal_stage_packet_refs.intersection(_stage_packet_refs(action)):
        return True
    # Identity-bound admissions are backed by OPL runtime readback or explicit
    # dispatch identity; weak action/work-unit/fingerprint matching is legacy-only.
    return False


def _action_stage_run_ids(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    stage_run_identity = _observability_mapping(
        _observability_mapping(readback.get("identity")).get("stage_run_identity")
    )
    identity = _observability_mapping(action.get("provider_admission_identity"))
    return {
        value
        for value in (
            _non_empty_text(action.get("stage_run_id")),
            _non_empty_text(action.get("stage_attempt_id")),
            _non_empty_text(action.get("active_stage_attempt_id")),
            _non_empty_text(identity.get("stage_run_id")),
            _non_empty_text(identity.get("stage_attempt_id")),
            _non_empty_text(identity.get("active_stage_attempt_id")),
            _non_empty_text(stage_run_identity.get("stage_run_id")),
        )
        if value is not None
    }


def _action_route_identity_keys(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    stage_run_identity = _observability_mapping(
        _observability_mapping(readback.get("identity")).get("stage_run_identity")
    )
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    return {
        value
        for value in (
            _non_empty_text(action.get("route_identity_key")),
            _non_empty_text(identity.get("route_identity_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(stage_run_identity.get("route_identity_key")),
        )
        if value is not None
    }


def _action_attempt_idempotency_keys(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    stage_run_identity = _observability_mapping(
        _observability_mapping(readback.get("identity")).get("stage_run_identity")
    )
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    return {
        value
        for value in (
            _non_empty_text(action.get("attempt_idempotency_key")),
            _non_empty_text(identity.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(stage_run_identity.get("attempt_idempotency_key")),
        )
        if value is not None
    }


def _action_idempotency_keys(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    readback_identity = _observability_mapping(readback.get("identity"))
    idempotency_readback = _observability_mapping(readback.get("idempotency_readback"))
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    return {
        value
        for value in (
            _non_empty_text(action.get("idempotency_key")),
            _non_empty_text(action.get("route_identity_key")),
            _non_empty_text(action.get("attempt_idempotency_key")),
            _non_empty_text(identity.get("idempotency_key")),
            _non_empty_text(identity.get("route_identity_key")),
            _non_empty_text(identity.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("idempotency_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(readback_identity.get("idempotency_key")),
            _non_empty_text(idempotency_readback.get("idempotency_key")),
        )
        if value is not None
    }


def _stage_packet_refs(payload: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in ("stage_packet_ref", "stage_packet_path", "dispatch_ref", "dispatch_path"):
        if text := _non_empty_text(payload.get(key)):
            refs.add(text)
    for key in ("stage_packet_refs", "checkpoint_refs"):
        refs.update(_string_list(payload.get(key)))
    identity = _observability_mapping(payload.get("provider_admission_identity"))
    for key in ("stage_packet_ref", "stage_packet_path", "dispatch_ref", "dispatch_path"):
        if text := _non_empty_text(identity.get(key)):
            refs.add(text)
    for key in ("stage_packet_refs", "checkpoint_refs"):
        refs.update(_string_list(identity.get(key)))
    return refs


def _terminal_closeout_action_identity_matches_candidate(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    terminal_action_type = _non_empty_text(terminal.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if terminal_action_type is None or action_type is None or terminal_action_type != action_type:
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit is not None and action_work_unit is not None and terminal_work_unit != action_work_unit:
        return False
    terminal_fingerprint = _non_empty_text(terminal.get("work_unit_fingerprint")) or _non_empty_text(
        terminal.get("action_fingerprint")
    )
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if terminal_fingerprint is not None and action_fingerprint is not None and terminal_fingerprint != action_fingerprint:
        return False
    return True


def _terminal_closeout_request_wrapper_identity_matches_candidate(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("action_type")) != "request_opl_stage_attempt":
        return False
    if not _request_wrapper_action_has_opl_transition_identity(action):
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit is None or action_work_unit is None or terminal_work_unit != action_work_unit:
        return False
    terminal_fingerprint = _non_empty_text(terminal.get("work_unit_fingerprint")) or _non_empty_text(
        terminal.get("action_fingerprint")
    )
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if terminal_fingerprint is not None and action_fingerprint is not None:
        return terminal_fingerprint == action_fingerprint
    return _terminal_closeout_has_request_wrapper_domain_owner_delta(terminal)


def _request_wrapper_action_has_opl_transition_identity(action: Mapping[str, Any]) -> bool:
    return (
        bool(_action_route_identity_keys(action) or _action_attempt_idempotency_keys(action) or _action_idempotency_keys(action))
        and (candidate_opl_transition_readback(action) or provider_admission_opl_transition_readback(action))
    )


def _terminal_closeout_has_request_wrapper_domain_owner_delta(terminal: Mapping[str, Any]) -> bool:
    status = _non_empty_text(terminal.get("status"))
    if status not in {
        "closed_with_domain_owner_refs",
        "blocked_with_domain_owner_refs",
        "completed",
    }:
        return False
    if _non_empty_text(terminal.get("closeout_receipt_status")) == "accepted_typed_closeout":
        return True
    return _terminal_closeout_has_domain_delta(terminal)


def _terminal_closeout_owner_answer_blocker(
    *,
    terminal: Mapping[str, Any],
    matching_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action = _observability_mapping(matching_action)
    source_ref = _non_empty_text(terminal.get("record_path")) or _non_empty_text(terminal.get("source_path"))
    blocker = {
        "blocker_id": "typed_closeout_packet_required",
        "blocker_type": "typed_closeout_packet_required",
        "owner": "MedAutoScience",
        "source": "terminal_stage_closeout_missing_owner_answer",
        "summary": (
            "Terminal provider closeout must include a MAS owner receipt, typed blocker, or next handoff "
            "before the current work unit can continue."
        ),
        "required_input": "MAS owner receipt, typed blocker, or next handoff",
        "stage_attempt_id": _non_empty_text(terminal.get("stage_attempt_id")),
        "action_type": _non_empty_text(terminal.get("action_type")) or _non_empty_text(action.get("action_type")),
        "work_unit_id": _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
            action.get("next_work_unit")
        ),
        "work_unit_fingerprint": _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "action_fingerprint": _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "source_ref": source_ref,
        "typed_blocker_ref": source_ref,
        "closeout_refs": _string_list(terminal.get("closeout_refs")),
    }
    return {key: value for key, value in blocker.items() if value not in (None, "", [], {})}


def _apply_typed_owner_callable_adapter_closeout_to_handoff(
    projection: dict[str, Any],
    *,
    allow_stale_identity_override: bool = False,
) -> dict[str, Any]:
    typed_closeout = _observability_mapping(projection.get("latest_typed_owner_callable_closeout"))
    if not typed_closeout:
        return projection
    if _handoff_has_complete_current_transition_readback(projection) and not allow_stale_identity_override:
        return projection
    matching_actions = [
        item
        for item in projection.get("action_queue") or []
        if isinstance(item, Mapping)
        and _typed_closeout_matches_handoff_action(typed_closeout=typed_closeout, action=item)
    ]
    if projection.get("action_queue") and not matching_actions and not allow_stale_identity_override:
        return projection
    typed_blocker = _typed_closeout_blocker_projection(
        typed_closeout=typed_closeout,
        matching_action=matching_actions[0] if matching_actions else None,
    )
    if not typed_blocker:
        return projection
    updated = dict(projection)
    if matching_actions:
        consumed = [
            {
                **dict(item),
                "consumption": {
                    **_observability_mapping(item.get("consumption")),
                    "state": "consumed_by_typed_owner_callable_adapter_closeout",
                    "typed_blocker_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
                    or _non_empty_text(typed_closeout.get("source_path")),
                },
            }
            for item in matching_actions
        ]
        updated["consumed_action_queue"] = consumed
        updated["action_queue"] = [
            dict(item)
            for item in updated.get("action_queue") or []
            if isinstance(item, Mapping) and item not in matching_actions
        ]
    updated["typed_blocker"] = typed_blocker
    updated["blocked_reason"] = _non_empty_text(typed_blocker.get("blocker_type")) or updated.get("blocked_reason")
    updated["next_owner"] = _non_empty_text(typed_blocker.get("owner")) or updated.get("next_owner")
    updated["running_provider_attempt"] = False
    updated["runtime_owner"] = None
    updated["provider_attempt_owner"] = None
    updated["queue_owner"] = None
    if allow_stale_identity_override:
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        updated["transition_request_pending_count"] = 0
        updated["transition_request_candidates"] = []
        updated["current_executable_owner_action"] = None
        updated["current_work_unit"] = _typed_closeout_current_work_unit(
            typed_blocker=typed_blocker,
            typed_closeout=typed_closeout,
        )
        updated["current_execution_envelope"] = {
            "state_kind": "typed_blocker",
            "owner": _non_empty_text(typed_blocker.get("owner")),
            "action_type": _non_empty_text(typed_blocker.get("action_type")),
            "work_unit_id": _work_unit_identity(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(typed_blocker.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(typed_blocker.get("action_fingerprint")),
            "source": "latest_typed_owner_callable_closeout",
            "typed_blocker": typed_blocker,
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
            },
        }
        updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
            terminal={
                **typed_closeout,
                "typed_blocker_ref": _non_empty_text(typed_closeout.get("typed_blocker_ref"))
                or _non_empty_text(typed_closeout.get("receipt_ref"))
                or _non_empty_text(typed_closeout.get("source_path")),
            },
            matching_provider_admission=None,
        )
        updated["provider_admission_terminal_closeout_consumed"]["typed_blocker"] = typed_blocker
        updated["provider_admission_terminal_closeout_consumed"]["currentness_precedence"] = (
            "newer_terminal_typed_closeout_supersedes_stale_provider_admission"
        )
    return updated


def _newer_typed_closeout_blocks_stale_current_control(
    *,
    typed_closeout: Mapping[str, Any],
    projection: Mapping[str, Any],
    handoff_path: Path,
) -> bool:
    if not typed_closeout:
        return False
    embedded = _observability_mapping(typed_closeout.get("typed_blocker"))
    if not embedded and _non_empty_text(typed_closeout.get("status")) != "typed_blocker":
        return False
    if _terminal_closeout_has_domain_delta(typed_closeout):
        return False
    if _handoff_has_complete_current_transition_readback(projection):
        return False
    has_stale_provider_admission = (
        int(projection.get("provider_admission_pending_count") or 0) > 0
        or bool(_handoff_candidate_list(projection.get("provider_admission_candidates")))
        or any(
            _action_queue_item_has_provider_admission_readback(item)
            for item in projection.get("action_queue") or []
            if isinstance(item, Mapping)
        )
    )
    if not has_stale_provider_admission:
        return False
    closeout_observed_at = _closeout_observed_timestamp(typed_closeout)
    current_control_observed_at = _current_control_observed_timestamp(
        projection=projection,
        handoff_path=handoff_path,
    )
    if closeout_observed_at <= current_control_observed_at:
        return False
    closeout_study = _non_empty_text(typed_closeout.get("study_id"))
    projection_study = _non_empty_text(projection.get("study_id"))
    return closeout_study is None or projection_study is None or closeout_study == projection_study


def _closeout_observed_timestamp(typed_closeout: Mapping[str, Any]) -> float:
    return max(
        _number_value(typed_closeout.get("source_mtime"))
        or _source_path_mtime(Path(_non_empty_text(typed_closeout.get("source_path")) or "")),
        _epoch_seconds(_non_empty_text(typed_closeout.get("generated_at"))),
    )


def _current_control_observed_timestamp(
    *,
    projection: Mapping[str, Any],
    handoff_path: Path,
) -> float:
    generated_at = _epoch_seconds(_non_empty_text(projection.get("generated_at")))
    if generated_at:
        return generated_at
    return _source_path_mtime(handoff_path)


def _epoch_seconds(value: str | None) -> float:
    if value is None:
        return 0.0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _action_queue_item_has_provider_admission_readback(item: Mapping[str, Any]) -> bool:
    candidate = _action_with_handoff_packet_readback(item)
    if provider_admission_opl_transition_readback(candidate):
        return True
    readback = candidate_opl_transition_readback(candidate)
    outcome = _observability_mapping(readback.get("exactly_one_outcome"))
    return _non_empty_text(outcome.get("outcome_kind")) == LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME


def _typed_closeout_current_work_unit(
    *,
    typed_blocker: Mapping[str, Any],
    typed_closeout: Mapping[str, Any],
) -> dict[str, Any]:
    owner = _non_empty_text(typed_blocker.get("owner")) or _non_empty_text(typed_closeout.get("next_owner"))
    action = _non_empty_text(typed_blocker.get("action_type")) or _non_empty_text(typed_closeout.get("action_type"))
    work_unit = _work_unit_identity(typed_blocker.get("work_unit_id")) or _work_unit_identity(
        typed_closeout.get("work_unit_id")
    )
    fingerprint = _non_empty_text(typed_blocker.get("work_unit_fingerprint")) or _non_empty_text(
        typed_closeout.get("work_unit_fingerprint")
    )
    action_fingerprint = _non_empty_text(typed_blocker.get("action_fingerprint")) or fingerprint
    blocker_type = _non_empty_text(typed_blocker.get("blocker_type")) or _non_empty_text(
        typed_blocker.get("blocked_reason")
    )
    return {
        key: value
        for key, value in {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "typed_blocker",
            "study_id": _non_empty_text(typed_closeout.get("study_id")),
            "quest_id": _non_empty_text(typed_closeout.get("study_id")),
            "owner": owner,
            "action_type": action,
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": action_fingerprint,
            "blocker_type": blocker_type,
            "typed_blocker_ref": _non_empty_text(typed_blocker.get("typed_blocker_ref"))
            or _non_empty_text(typed_closeout.get("receipt_ref"))
            or _non_empty_text(typed_closeout.get("source_path")),
            "state": {
                "state_kind": "typed_blocker",
                "source": "latest_typed_owner_callable_closeout",
                "typed_blocker": dict(typed_blocker),
                "stage_attempt_id": _non_empty_text(typed_closeout.get("stage_attempt_id")),
                "stale_queue_or_handoff_can_override": False,
                "provider_completion_is_domain_completion": False,
            },
            "required_output_contract": {
                "owner_receipt_required": True,
                "typed_blocker_allowed": True,
                "provider_completion_is_domain_completion": False,
            },
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def _handoff_has_complete_current_transition_readback(projection: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(projection):
        return True
    non_advancing = _observability_mapping(
        projection.get("domain_progress_transition_non_advancing_apply_readback")
    )
    if non_advancing and candidate_opl_transition_readback(
        {
            **non_advancing,
            "opl_domain_progress_transition_runtime_live_readback": _observability_mapping(
                non_advancing.get("runtime_live_readback")
            ),
        }
    ):
        return True
    return any(
        candidate_opl_transition_readback(candidate)
        or provider_admission_opl_transition_readback(candidate)
        for candidate in projection.get("provider_admission_candidates") or []
        if isinstance(candidate, Mapping)
    )


def _terminal_closeout_has_domain_delta(terminal: Mapping[str, Any]) -> bool:
    if _non_empty_text(terminal.get("closeout_receipt_status")) == "accepted_typed_closeout":
        return True
    if _non_empty_text(terminal.get("owner_receipt_ref")):
        return True
    if _string_list(terminal.get("owner_receipt_refs")):
        return True
    if _non_empty_text(terminal.get("route_outcome")) == "owner_receipt":
        return True
    domain_refs = _observability_mapping(terminal.get("domain_owner_refs"))
    if _non_empty_text(domain_refs.get("route_back_evidence_ref")):
        return True
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    if _string_list(paper_stage_log.get("changed_paper_surfaces")):
        return True
    outcome = _non_empty_text(paper_stage_log.get("outcome"))
    if outcome in {"owner_receipt", "owner_receipt_recorded", "handoff_ready", "next_handoff"}:
        return True
    return False


def _typed_closeout_matches_handoff_action(
    *,
    typed_closeout: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    closeout_attempt_id = _non_empty_text(typed_closeout.get("execution_id")) or _non_empty_text(
        typed_closeout.get("stage_attempt_id")
    )
    action_attempt_id = _non_empty_text(action.get("stage_attempt_id")) or _non_empty_text(
        action.get("active_stage_attempt_id")
    )
    if closeout_attempt_id and action_attempt_id:
        return closeout_attempt_id == action_attempt_id
    projection_attempt_id = _non_empty_text(action.get("active_stage_attempt_id")) or _stage_attempt_id_from_active_run_id(
        action.get("active_run_id")
    )
    if closeout_attempt_id and projection_attempt_id:
        return closeout_attempt_id == projection_attempt_id
    closeout_action_type = _non_empty_text(typed_closeout.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if (
        closeout_action_type is not None
        and action_type == closeout_action_type
        and is_anti_loop_stop_loss_closeout(typed_closeout)
    ):
        return True
    closeout_fingerprints = _identity_values(
        typed_closeout,
        ("work_unit_fingerprint", "action_fingerprint", "fingerprint"),
    )
    action_fingerprints = _identity_values(
        action,
        ("work_unit_fingerprint", "action_fingerprint", "fingerprint"),
    )
    if closeout_fingerprints and action_fingerprints:
        return bool(closeout_fingerprints.intersection(action_fingerprints))
    closeout_work_unit = _work_unit_identity(typed_closeout.get("work_unit_id")) or _work_unit_identity(
        typed_closeout.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    return (
        closeout_work_unit is not None
        and action_work_unit == closeout_work_unit
        and closeout_action_type is not None
        and action_type == closeout_action_type
    )


def _identity_values(value: Mapping[str, Any], keys: tuple[str, ...]) -> set[str]:
    return {
        text
        for key in keys
        if (text := _non_empty_text(value.get(key))) is not None
    }


def _typed_closeout_blocker_projection(
    *,
    typed_closeout: Mapping[str, Any],
    matching_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    embedded = _observability_mapping(typed_closeout.get("typed_blocker"))
    blocked_reason = (
        _non_empty_text(typed_closeout.get("blocked_reason"))
        or _non_empty_text(embedded.get("blocker_type"))
        or _non_empty_text(embedded.get("blocker_kind"))
        or _non_empty_text(embedded.get("reason"))
        or _non_empty_text(embedded.get("blocked_reason"))
        or _non_empty_text(embedded.get("blocker_id"))
    )
    if blocked_reason is None:
        return {}
    owner = (
        _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(embedded.get("required_next_owner"))
        or _non_empty_text(embedded.get("phase_owner"))
        or _non_empty_text(typed_closeout.get("next_owner"))
    )
    if blocked_reason in OPL_RUNTIME_TERMINAL_BLOCKERS:
        owner = "one-person-lab"
    action = _observability_mapping(matching_action)
    blocker = {
        **embedded,
        "blocker_type": blocked_reason,
        "blocked_reason": blocked_reason,
        "owner": owner or "med-autoscience",
        "action_type": _non_empty_text(typed_closeout.get("action_type"))
        or _non_empty_text(action.get("action_type")),
        "work_unit_id": _work_unit_identity(typed_closeout.get("work_unit_id"))
        or _work_unit_identity(_mapping_copy(typed_closeout.get("next_forced_delta")).get("work_unit_id"))
        or _work_unit_identity(action.get("work_unit_id"))
        or _work_unit_identity(action.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(typed_closeout.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "action_fingerprint": _non_empty_text(typed_closeout.get("action_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "source_fingerprint": _non_empty_text(typed_closeout.get("source_fingerprint"))
        or _non_empty_text(action.get("source_fingerprint")),
        "idempotency_key": _non_empty_text(typed_closeout.get("idempotency_key"))
        or _non_empty_text(action.get("idempotency_key")),
        "stage_attempt_id": _non_empty_text(typed_closeout.get("stage_attempt_id"))
        or _non_empty_text(action.get("stage_attempt_id"))
        or _non_empty_text(action.get("active_stage_attempt_id")),
        "source_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
        or _non_empty_text(typed_closeout.get("source_path")),
        "typed_blocker_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
        or _non_empty_text(typed_closeout.get("source_path")),
        "closeout_refs": _string_list(typed_closeout.get("closeout_refs")),
    }
    owner_route = _observability_mapping(typed_closeout.get("owner_route"))
    source_refs = _observability_mapping(owner_route.get("source_refs"))
    currentness_basis = _observability_mapping(source_refs.get("owner_route_currentness_basis"))
    if currentness_basis:
        blocker["currentness_basis"] = currentness_basis
    return {key: value for key, value in blocker.items() if value not in (None, "", [], {})}


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _observability_mapping(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    if active_attempt_id is None and not _handoff_has_terminal_matching_pending_candidate(
        handoff=handoff,
        terminal=terminal,
    ) and _terminal_closeout_consumed_current_action_projection(
        terminal=terminal,
        projection=handoff,
    ) is None:
        return False
    status = _non_empty_text(terminal.get("status"))
    if status in TERMINAL_STAGE_LOG_STATUSES:
        return True
    return (
        _non_empty_text(terminal.get("source_path")) is not None
        and _non_empty_text(terminal.get("record_path")) is not None
    )


def _handoff_has_terminal_matching_pending_candidate(
    *,
    handoff: Mapping[str, Any],
    terminal: Mapping[str, Any],
) -> bool:
    candidates = [
        *_handoff_candidate_list(handoff.get("provider_admission_candidates")),
        *_handoff_candidate_list(handoff.get("transition_request_candidates")),
    ]
    return bool(
        candidates
        and _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=candidates,
        )
    )


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _non_empty_text(handoff.get("active_stage_attempt_id")):
        return text
    return _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))


def _stage_attempt_id_from_active_run_id(value: object) -> str | None:
    active_run_id = _non_empty_text(value)
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _handoff_live_attempt_identity_stale(
    *,
    handoff: Mapping[str, Any],
    live_attempt_handoff: Mapping[str, Any],
) -> bool:
    live_stage_attempt_id = _non_empty_text(live_attempt_handoff.get("active_stage_attempt_id"))
    if live_stage_attempt_id is None:
        return False
    handoff_stage_attempt_id = _non_empty_text(handoff.get("active_stage_attempt_id"))
    if handoff_stage_attempt_id in {None, live_stage_attempt_id}:
        return False
    handoff_run_attempt_id = _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))
    live_run_attempt_id = _stage_attempt_id_from_active_run_id(live_attempt_handoff.get("active_run_id"))
    return live_stage_attempt_id in {handoff_run_attempt_id, live_run_attempt_id}


def _live_attempt_supersedes_handoff_blocker(handoff: Mapping[str, Any]) -> bool:
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    if blocked_reason in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS:
        return True
    why_not_applied = set(_string_list(handoff.get("why_not_applied")))
    if why_not_applied.intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS):
        return True
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_blockers = set(_string_list(runtime_health.get("blocking_reasons")))
    return bool(runtime_blockers.intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS))
