from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME,
    provider_admission_opl_transition_readback,
)

from ..opl_current_control_state_handoff_values import (
    _observability_mapping,
    _string_list,
    _work_unit_identity,
)
from ..shared_base import _non_empty_text
from .non_advancing_readback import provider_admission_identity_from_readback
from .terminal_closeout import (
    _action_with_handoff_packet_readback,
    _handoff_candidate_list,
    _provider_admission_terminal_closeout_consumed,
)
from .terminal_closeout_identity import (
    _stage_ref_items,
    _terminal_matching_handoff_candidates,
)
from .transition_readbacks import _transition_request_identity_key


def current_control_provider_admission_candidates(
    *,
    payload: Mapping[str, Any],
    matching: Mapping[str, Any] | None,
    matching_top_level_provider_admissions: list[dict[str, Any]],
    matching_top_level_transition_requests: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates = [
        dict(item)
        for item in matching_top_level_provider_admissions
        if isinstance(item, Mapping) and provider_admission_opl_transition_readback(item)
    ]
    candidates.extend(
        dict(item)
        for item in matching_top_level_transition_requests or []
        if isinstance(item, Mapping) and transition_request_candidate_can_anchor_terminal_probe(item)
    )
    if isinstance(matching, Mapping):
        candidates.extend(
            dict(item)
            for item in matching.get("provider_admission_candidates") or []
            if isinstance(item, Mapping) and provider_admission_opl_transition_readback(item)
        )
        candidates.extend(
            dict(item)
            for item in matching.get("transition_request_candidates") or []
            if isinstance(item, Mapping) and transition_request_candidate_can_anchor_terminal_probe(item)
        )
    if not candidates:
        return []
    provider_pending = int(payload.get("provider_admission_pending_count") or 0) > 0
    transition_pending = int(payload.get("transition_request_pending_count") or 0) > 0
    if isinstance(matching, Mapping):
        provider_pending = provider_pending or int(matching.get("provider_admission_pending_count") or 0) > 0
        transition_pending = transition_pending or int(matching.get("transition_request_pending_count") or 0) > 0
    return candidates if provider_pending or transition_pending else []


def transition_request_candidate_can_anchor_terminal_probe(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return True
    if _non_empty_text(candidate.get("status")) != "transition_request_pending":
        return False
    return (
        _non_empty_text(candidate.get("action_type")) is not None
        and _work_unit_identity(candidate.get("work_unit_id")) is not None
        and (
            _non_empty_text(candidate.get("work_unit_fingerprint")) is not None
            or _non_empty_text(candidate.get("action_fingerprint")) is not None
        )
        and (
            _non_empty_text(candidate.get("attempt_idempotency_key")) is not None
            or _non_empty_text(_observability_mapping(candidate.get("source_refs")).get("attempt_idempotency_key"))
            is not None
        )
    )


def terminal_consumption_candidate_can_anchor_terminal_probe(candidate: Mapping[str, Any]) -> bool:
    return provider_admission_opl_transition_readback(candidate) or transition_request_candidate_can_anchor_terminal_probe(
        candidate
    )


def apply_top_level_provider_admissions_to_handoff(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(projection)
    provider_candidates = dedupe_provider_admission_candidates(
        [
            dict(item)
            for item in candidates
            if provider_admission_opl_transition_readback(item)
        ]
    )
    if not provider_candidates:
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        return updated
    updated["provider_admission_pending_count"] = len(provider_candidates)
    updated["provider_admission_candidates"] = provider_candidates
    current = provider_candidates[0]
    for key in ("action_type", "work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current.get(key))
        if text is not None:
            updated[key] = text
    work_unit_id = _work_unit_identity(current.get("work_unit_id"))
    if work_unit_id is not None:
        updated["work_unit_id"] = work_unit_id
    copy_stage_packet_ref_family_to_projection(updated, current)
    if _non_empty_text(current.get("status")) == "provider_admission_pending" and provider_candidates:
        updated["blocked_reason"] = None
        updated.pop("typed_blocker", None)
    return updated


def apply_top_level_transition_requests_to_handoff(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if projection.get("running_provider_attempt") is True:
        request_candidates_for_running = [
            dict(item)
            for item in candidates
            if transition_request_candidate_can_anchor_terminal_probe(item)
            and not provider_admission_opl_transition_readback(item)
        ]
        if any(handoff_candidate_matches_projection(candidate, projection) for candidate in request_candidates_for_running):
            return handoff_without_same_identity_pending(projection, request_candidates_for_running)
    request_candidates = [
        dict(item)
        for item in candidates
        if transition_request_candidate_can_anchor_terminal_probe(item)
        and not provider_admission_opl_transition_readback(item)
    ]
    if not request_candidates:
        return dict(projection)
    updated = dict(projection)
    updated["transition_request_pending_count"] = len(request_candidates)
    updated["transition_request_candidates"] = request_candidates
    updated.setdefault("provider_admission_pending_count", 0)
    updated.setdefault("provider_admission_candidates", [])
    current = request_candidates[0]
    for key in ("action_type", "work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current.get(key))
        if text is not None:
            updated[key] = text
    work_unit_id = _work_unit_identity(current.get("work_unit_id"))
    if work_unit_id is not None:
        updated["work_unit_id"] = work_unit_id
    copy_stage_packet_ref_family_to_projection(updated, current)
    updated["next_owner"] = _non_empty_text(current.get("next_owner")) or updated.get("next_owner")
    updated["blocked_reason"] = _non_empty_text(current.get("blocked_reason")) or updated.get("blocked_reason")
    return updated


def handoff_without_same_identity_pending(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(projection)
    matching_identity_keys = {
        key
        for candidate in candidates
        if handoff_candidate_matches_projection(candidate, projection)
        for key in handoff_candidate_runtime_identity_keys(candidate)
    }
    if not matching_identity_keys:
        return updated
    provider_candidates = [
        dict(item)
        for item in updated.get("provider_admission_candidates") or []
        if not handoff_candidate_runtime_identity_keys(item).intersection(matching_identity_keys)
    ]
    transition_candidates = [
        dict(item)
        for item in updated.get("transition_request_candidates") or []
        if not handoff_candidate_runtime_identity_keys(item).intersection(matching_identity_keys)
    ]
    updated["provider_admission_candidates"] = provider_candidates
    updated["provider_admission_pending_count"] = len(provider_candidates)
    updated["transition_request_candidates"] = transition_candidates
    updated["transition_request_pending_count"] = len(transition_candidates)
    updated["blocked_reason"] = None
    updated["external_supervisor_required"] = False
    return updated


def handoff_candidate_runtime_identity_keys(candidate: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(candidate) or provider_admission_opl_transition_readback(
        candidate
    )
    readback_identity = _observability_mapping(readback.get("identity"))
    stage_run_identity = _observability_mapping(readback_identity.get("stage_run_identity"))
    idempotency_readback = _observability_mapping(readback.get("idempotency_readback"))
    provider_identity = _observability_mapping(candidate.get("provider_admission_identity"))
    source_refs = _observability_mapping(candidate.get("source_refs"))
    return {
        key
        for key in (
            _transition_request_identity_key(candidate),
            _non_empty_text(candidate.get("route_identity_key")),
            _non_empty_text(candidate.get("attempt_idempotency_key")),
            _non_empty_text(candidate.get("idempotency_key")),
            _non_empty_text(provider_identity.get("route_identity_key")),
            _non_empty_text(provider_identity.get("attempt_idempotency_key")),
            _non_empty_text(provider_identity.get("idempotency_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("idempotency_key")),
            _non_empty_text(stage_run_identity.get("route_identity_key")),
            _non_empty_text(stage_run_identity.get("attempt_idempotency_key")),
            _non_empty_text(readback_identity.get("idempotency_key")),
            _non_empty_text(idempotency_readback.get("idempotency_key")),
        )
        if key is not None
    }


def handoff_candidate_matches_projection(
    candidate: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> bool:
    for key in ("study_id", "action_type"):
        candidate_value = _non_empty_text(candidate.get(key))
        projection_value = _non_empty_text(projection.get(key))
        if candidate_value is not None and projection_value is not None and candidate_value != projection_value:
            return False
    candidate_work_unit = _work_unit_identity(candidate.get("work_unit_id")) or _work_unit_identity(
        candidate.get("next_work_unit")
    )
    projection_work_unit = _work_unit_identity(projection.get("work_unit_id")) or _work_unit_identity(
        projection.get("next_work_unit")
    )
    if candidate_work_unit is not None and projection_work_unit is not None and candidate_work_unit != projection_work_unit:
        return False
    candidate_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    projection_fingerprint = _non_empty_text(projection.get("work_unit_fingerprint")) or _non_empty_text(
        projection.get("action_fingerprint")
    )
    if (
        candidate_fingerprint is not None
        and projection_fingerprint is not None
        and candidate_fingerprint != projection_fingerprint
    ):
        return False
    for key in ("route_identity_key", "attempt_idempotency_key", "idempotency_key"):
        candidate_value = _non_empty_text(candidate.get(key))
        projection_value = _non_empty_text(projection.get(key))
        if candidate_value is not None and projection_value is not None and candidate_value == projection_value:
            return True
    return candidate_work_unit is not None and projection_work_unit is not None and candidate_work_unit == projection_work_unit


def copy_stage_packet_ref_family_to_projection(
    projection: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    source_refs = _observability_mapping(source.get("source_refs"))
    stage_packet_ref = _non_empty_text(source.get("stage_packet_ref")) or _non_empty_text(
        source_refs.get("stage_packet_ref")
    )
    stage_packet_refs = _stage_ref_items(source.get("stage_packet_refs")) or _stage_ref_items(
        source_refs.get("stage_packet_refs")
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = _stage_ref_items(source.get("checkpoint_refs")) or _stage_ref_items(
        source_refs.get("checkpoint_refs")
    ) or list(stage_packet_refs)
    for key in ("dispatch_ref", "dispatch_path"):
        value = _non_empty_text(source.get(key)) or _non_empty_text(source_refs.get(key))
        if value is not None:
            projection[key] = value
    if stage_packet_ref is not None:
        projection["stage_packet_ref"] = stage_packet_ref
    if stage_packet_refs:
        projection["stage_packet_refs"] = stage_packet_refs
    if checkpoint_refs:
        projection["checkpoint_refs"] = checkpoint_refs


def apply_action_queue_provider_readbacks_to_handoff(
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    consumed = _observability_mapping(projection.get("provider_admission_terminal_closeout_consumed"))
    if consumed:
        terminal = terminal_stage_log_from_terminal_consumed_readback(consumed)
        action_queue = _handoff_candidate_list(projection.get("action_queue"))
        matching_actions = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=action_queue,
        )
        if matching_actions:
            projection = {
                **dict(projection),
                "action_queue": [
                    dict(item)
                    for item in action_queue
                    if item not in matching_actions
                ],
                "consumed_action_queue": [
                    {
                        **dict(item),
                        "consumption": {
                            **_observability_mapping(item.get("consumption")),
                            "state": "consumed_by_provider_admission_terminal_readback",
                            "terminal_stage_attempt_id": _non_empty_text(
                                consumed.get("terminal_stage_attempt_id")
                            )
                            or _non_empty_text(consumed.get("stage_attempt_id")),
                        },
                    }
                    for item in matching_actions
                ],
            }
    projection_readback_candidate = provider_readback_candidate_from_projection(projection)
    action_provider_candidates = [
        dict(item)
        for item in projection.get("action_queue") or []
        if isinstance(item, Mapping) and provider_admission_opl_transition_readback(_action_with_handoff_packet_readback(item))
    ]
    if projection_readback_candidate:
        action_provider_candidates.extend(
            bind_projection_provider_readback_to_actions(
                projection,
                readback_candidate=projection_readback_candidate,
            )
        )
    action_provider_candidates = dedupe_provider_admission_candidates(action_provider_candidates)
    if not action_provider_candidates:
        return dict(projection)
    updated = apply_top_level_provider_admissions_to_handoff(
        projection,
        action_provider_candidates,
    )
    provider_keys = {
        _transition_request_identity_key(candidate)
        for candidate in action_provider_candidates
        if _transition_request_identity_key(candidate) is not None
    }
    remaining_transition_requests = [
        dict(item)
        for item in updated.get("transition_request_candidates") or []
        if _transition_request_identity_key(item) not in provider_keys
    ]
    updated["transition_request_candidates"] = remaining_transition_requests
    updated["transition_request_pending_count"] = len(remaining_transition_requests)
    updated["quest_status"] = "provider_admission_pending"
    return updated


def dedupe_provider_admission_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for candidate in candidates:
        identity = tuple(sorted(handoff_candidate_runtime_identity_keys(candidate)))
        if not identity:
            identity = tuple(
                value
                for value in (
                    _non_empty_text(candidate.get("study_id")),
                    _work_unit_identity(candidate.get("work_unit_id"))
                    or _work_unit_identity(candidate.get("next_work_unit")),
                    _non_empty_text(candidate.get("work_unit_fingerprint"))
                    or _non_empty_text(candidate.get("action_fingerprint")),
                )
                if value is not None
            )
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(candidate)
    return deduped


def provider_readback_candidate_from_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    readback = candidate_opl_transition_readback(projection)
    if not readback:
        return {}
    outcome_kind = _non_empty_text(_observability_mapping(readback.get("exactly_one_outcome")).get("outcome_kind"))
    if outcome_kind != LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME:
        return {}
    identity = provider_admission_identity_from_readback(readback)
    if not identity:
        return {}
    action_type = _non_empty_text(projection.get("action_type"))
    work_unit_id = _work_unit_identity(projection.get("work_unit_id")) or _work_unit_identity(
        identity.get("work_unit_id")
    )
    work_unit_fingerprint = _non_empty_text(projection.get("work_unit_fingerprint")) or _non_empty_text(
        projection.get("action_fingerprint")
    ) or _non_empty_text(identity.get("work_unit_fingerprint"))
    return {
        **identity,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": _non_empty_text(projection.get("action_fingerprint"))
        or work_unit_fingerprint,
        "next_executable_owner": _non_empty_text(projection.get("next_owner")),
        "owner": _non_empty_text(projection.get("next_owner")),
        "status": "provider_admission_pending",
        "provider_admission_pending": True,
        "transition_request_pending": False,
        "provider_attempt_or_lease_required": True,
        "provider_admission_requires_opl_runtime_result": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }


def bind_projection_provider_readback_to_actions(
    projection: Mapping[str, Any],
    *,
    readback_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for item in projection.get("action_queue") or []:
        if not isinstance(item, Mapping):
            continue
        action = _action_with_handoff_packet_readback(item)
        if not same_provider_readback_identity(action, readback_candidate):
            continue
        action_readback = provider_admission_opl_transition_readback(action) or readback_candidate[
            "opl_domain_progress_transition_runtime_live_readback"
        ]
        bound.append(
            {
                **action,
                "status": "provider_admission_pending",
                "provider_admission_pending": True,
                "transition_request_pending": False,
                "provider_attempt_or_lease_required": True,
                "provider_admission_requires_opl_runtime_result": False,
                "provider_admission_identity": {
                    **_observability_mapping(action.get("provider_admission_identity")),
                    **dict(readback_candidate),
                },
                "opl_domain_progress_transition_runtime_live_readback": action_readback,
            }
        )
    return bound


def same_provider_readback_identity(
    action: Mapping[str, Any],
    readback_candidate: Mapping[str, Any],
) -> bool:
    action_study = _non_empty_text(action.get("study_id"))
    readback_study = _non_empty_text(readback_candidate.get("study_id"))
    if action_study is not None and readback_study is not None and action_study != readback_study:
        return False
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    readback_work_unit = _work_unit_identity(readback_candidate.get("work_unit_id"))
    if action_work_unit is None or readback_work_unit is None or action_work_unit != readback_work_unit:
        return False
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    readback_fingerprint = _non_empty_text(readback_candidate.get("work_unit_fingerprint"))
    if action_fingerprint is None or readback_fingerprint is None or action_fingerprint != readback_fingerprint:
        return False
    for key in ("route_identity_key", "attempt_idempotency_key"):
        action_value = _non_empty_text(action.get(key))
        readback_value = _non_empty_text(readback_candidate.get(key))
        if action_value is not None and readback_value is not None and action_value != readback_value:
            return False
    return True


def latest_provider_admission_terminal_consumed_readback_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    readback = _observability_mapping(payload.get("latest_provider_admission_terminal_consumed_readback"))
    if _non_empty_text(readback.get("status")) != "provider_admission_terminal_consumed":
        return {}
    identity = _observability_mapping(readback.get("currentness_identity"))
    readback_study = _non_empty_text(identity.get("study_id")) or _non_empty_text(readback.get("study_id"))
    if readback_study is not None and readback_study != study_id:
        return {}
    return dict(readback)


def apply_terminal_consumed_readback_to_handoff(
    projection: Mapping[str, Any],
    readback: Mapping[str, Any],
    *,
    apply_matching_terminal_closeout_to_handoff,
) -> dict[str, Any]:
    terminal = terminal_stage_log_from_terminal_consumed_readback(readback)
    if not terminal:
        return dict(projection)
    updated = dict(projection)
    existing_terminal = _observability_mapping(updated.get("latest_terminal_stage_log"))
    if not existing_terminal:
        updated["latest_terminal_stage_log"] = terminal
    candidate_sources = [
        *_handoff_candidate_list(updated.get("provider_admission_candidates")),
        *_handoff_candidate_list(updated.get("transition_request_candidates")),
        *_handoff_candidate_list(updated.get("action_queue")),
    ]
    if candidate_sources and not _terminal_matching_handoff_candidates(
        terminal=terminal,
        candidates=candidate_sources,
    ):
        return updated
    updated = apply_matching_terminal_closeout_to_handoff(updated)
    return consume_terminal_matching_action_queue(
        updated,
        terminal=terminal,
        consumed_readback=readback,
    )


def consume_terminal_matching_action_queue(
    projection: Mapping[str, Any],
    *,
    terminal: Mapping[str, Any],
    consumed_readback: Mapping[str, Any],
) -> dict[str, Any]:
    action_queue = _handoff_candidate_list(projection.get("action_queue"))
    matching_actions = _terminal_matching_handoff_candidates(
        terminal=terminal,
        candidates=action_queue,
    )
    if not matching_actions:
        return dict(projection)
    updated = dict(projection)
    consumed_entries = [
        {
            **dict(item),
            "consumption": {
                **_observability_mapping(item.get("consumption")),
                "state": "consumed_by_provider_admission_terminal_readback",
                "terminal_stage_attempt_id": _non_empty_text(
                    consumed_readback.get("terminal_stage_attempt_id")
                )
                or _non_empty_text(consumed_readback.get("stage_attempt_id")),
            },
        }
        for item in matching_actions
    ]
    prior_consumed = [
        dict(item)
        for item in updated.get("consumed_action_queue") or []
        if isinstance(item, Mapping)
    ]
    updated["consumed_action_queue"] = [*prior_consumed, *consumed_entries]
    updated["action_queue"] = [
        dict(item)
        for item in action_queue
        if item not in matching_actions
    ]
    updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
        terminal=terminal,
        matching_provider_admission=matching_actions[0],
    )
    return updated


def terminal_stage_log_from_terminal_consumed_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    if _non_empty_text(readback.get("status")) != "provider_admission_terminal_consumed":
        return {}
    identity = _observability_mapping(readback.get("currentness_identity"))
    terminal = {
        "surface_kind": "stage_attempt_closeout_packet",
        "source": "opl_current_control_state.latest_provider_admission_terminal_consumed_readback",
        "status": _non_empty_text(readback.get("terminal_stage_attempt_status")) or "completed",
        "stage_attempt_id": _non_empty_text(readback.get("terminal_stage_attempt_id"))
        or _non_empty_text(identity.get("stage_attempt_id")),
        "action_type": _non_empty_text(identity.get("action_type")) or _non_empty_text(readback.get("action_type")),
        "work_unit_id": _work_unit_identity(identity.get("work_unit_id"))
        or _work_unit_identity(readback.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(readback.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(readback.get("action_fingerprint")),
        "route_identity_key": _non_empty_text(identity.get("route_identity_key"))
        or _non_empty_text(readback.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(identity.get("attempt_idempotency_key"))
        or _non_empty_text(readback.get("attempt_idempotency_key")),
        "idempotency_key": _non_empty_text(identity.get("idempotency_key"))
        or _non_empty_text(readback.get("idempotency_key"))
        or _non_empty_text(identity.get("attempt_idempotency_key")),
        "closeout_refs": _string_list(readback.get("closeout_refs")),
        "provider_completion_is_domain_completion": readback.get("provider_completion_is_domain_completion"),
        "provider_completion_is_domain_ready": readback.get("provider_completion_is_domain_ready"),
    }
    return {key: value for key, value in terminal.items() if value not in (None, "", [], {})}


__all__ = [
    "apply_action_queue_provider_readbacks_to_handoff",
    "apply_terminal_consumed_readback_to_handoff",
    "apply_top_level_provider_admissions_to_handoff",
    "apply_top_level_transition_requests_to_handoff",
    "current_control_provider_admission_candidates",
    "dedupe_provider_admission_candidates",
    "handoff_candidate_matches_projection",
    "handoff_candidate_runtime_identity_keys",
    "latest_provider_admission_terminal_consumed_readback_for_study",
    "provider_readback_candidate_from_projection",
    "terminal_consumption_candidate_can_anchor_terminal_probe",
    "terminal_stage_log_from_terminal_consumed_readback",
    "transition_request_candidate_can_anchor_terminal_probe",
]
