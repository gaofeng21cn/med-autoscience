from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    provider_admission_opl_transition_readback,
)

from ..opl_current_control_state_handoff_values import (
    _observability_mapping,
    _string_list,
    _work_unit_identity,
)
from ..shared_base import _non_empty_text


ANTI_LOOP_BUDGET_EXHAUSTED = "anti_loop_budget_exhausted"
REPEAT_SUPPRESSED_TYPED_BLOCKER_OUTCOMES = frozenset(
    {"repeat_suppressed_with_typed_blocker", "typed_blocker_anti_loop_budget_exhausted"}
)


def is_anti_loop_stop_loss_closeout(closeout: Mapping[str, Any]) -> bool:
    typed_blocker = _observability_mapping(closeout.get("typed_blocker"))
    anti_loop_budget = _observability_mapping(typed_blocker.get("anti_loop_budget"))
    paper_stage_log = _observability_mapping(closeout.get("paper_stage_log"))
    next_forced_delta = _observability_mapping(paper_stage_log.get("next_forced_delta"))
    values = (
        closeout.get("blocked_reason"),
        closeout.get("typed_blocker_reason"),
        closeout.get("outcome"),
        closeout.get("status"),
        typed_blocker.get("blocker_kind"),
        typed_blocker.get("reason"),
        anti_loop_budget.get("status"),
        paper_stage_log.get("outcome"),
        next_forced_delta.get("reason"),
    )
    return any(
        (text := _non_empty_text(value)) in REPEAT_SUPPRESSED_TYPED_BLOCKER_OUTCOMES
        or text == ANTI_LOOP_BUDGET_EXHAUSTED
        or text == "exhausted" and bool(anti_loop_budget)
        or bool(text and ANTI_LOOP_BUDGET_EXHAUSTED in text)
        for value in values
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
    return bool(
        _action_route_identity_keys(action)
        or _action_attempt_idempotency_keys(action)
        or _action_idempotency_keys(action)
    ) and (candidate_opl_transition_readback(action) or provider_admission_opl_transition_readback(action))


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


def _stage_attempt_id_from_active_run_id(value: object) -> str | None:
    active_run_id = _non_empty_text(value)
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None
