from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
    request_output_surface_for_action_type,
    request_owner_for_action_type,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.owner_route_reconcile_parts import (
    action_decorators,
    domain_route_contract,
    domain_transition_actions,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    current_work_unit_action,
    fresh_progress_arbitration,
    owner_route_currentness_projection,
    repair_progress_currentness,
    stage_native_next_action,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def current_actions_for_studies(
    *,
    profile: WorkspaceProfile | None = None,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]:
    ignored: list[dict[str, Any]] = []
    if not study_ids:
        actions = scan_payload.get("action_queue")
        return (list(actions), ignored) if isinstance(actions, list) else (None, ignored)
    per_study_actions: list[dict[str, Any]] = []
    requested = set(study_ids)
    stage_native_actions = stage_native_next_action.stage_native_next_actions(profile=profile, study_ids=study_ids)
    stage_native_by_study = {
        study_id: action for action in stage_native_actions if (study_id := _text(action.get("study_id"))) is not None
    }
    dispatchable_stage_native_by_study = {
        study_id: action
        for study_id, action in stage_native_by_study.items()
        if stage_native_next_action.default_dispatch_allowed(action)
    }
    diagnostic_stage_native_by_study = {
        study_id: action
        for study_id, action in stage_native_by_study.items()
        if study_id not in dispatchable_stage_native_by_study
    }
    current_writer_handoff_by_study = _current_writer_handoff_actions(profile=profile, study_ids=study_ids)
    fresh_progress_actions = _fresh_progress_current_actions(profile=profile, study_ids=study_ids)
    fresh_progress_by_study = {
        study_id: action
        for action in fresh_progress_actions
        if (study_id := _text(action.get("study_id"))) is not None
    }
    top_level_actions = [
        dict(action) for action in scan_payload.get("action_queue") or [] if isinstance(action, Mapping)
    ]
    matched_requested_study = False
    suppressed_fresh_progress_studies: set[str] = set()
    for study in scan_payload.get("studies") or []:
        study_payload = _mapping(study)
        study_id = _text(study_payload.get("study_id"))
        if study_id not in requested:
            continue
        matched_requested_study = True
        stage_native_action = dispatchable_stage_native_by_study.get(study_id)
        diagnostic_stage_native_action = diagnostic_stage_native_by_study.get(study_id)
        readiness_followup = _current_readiness_followup_action(study_payload)
        fresh_progress_action = fresh_progress_by_study.get(study_id)
        top_level_study_actions = _top_level_study_actions(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        current_route_queue_actions = _current_owner_route_queue_actions(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        canonical_current_action = current_work_unit_action.canonical_current_work_unit_action(study_payload)
        writer_handoff_owner_action = _current_writer_handoff_owner_action(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        currentness_owner_action = writer_handoff_owner_action or _currentness_owner_action(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        transition_actions = _consumed_domain_transition_actions(study_payload)
        if fresh_progress_action is not None and not _mapping(study_payload.get("current_work_unit")):
            canonical_current_action = None
        if canonical_current_action is not None:
            per_study_actions.append(canonical_current_action)
            ignored.extend(
                _ignored_action(
                    action,
                    _ignored_reason_for_superseded_action(
                        action,
                        selected_actions=[canonical_current_action],
                        default="superseded_by_canonical_current_work_unit",
                    ),
                )
                for action in [
                    *([fresh_progress_action] if fresh_progress_action is not None else []),
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *transition_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
                if action != canonical_current_action
            )
            continue
        if transition_actions:
            per_study_actions.extend(transition_actions)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_consumed_domain_transition")
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        if fresh_progress_action is not None and _scan_currentness_preempts_fresh_progress(
            study_payload,
            fresh_action=fresh_progress_action,
        ):
            suppressed_fresh_progress_studies.add(study_id)
            fresh_progress_action = None
        if fresh_progress_action is not None and not fresh_progress_arbitration.can_preempt_scan(
            study=study_payload,
            fresh_action=fresh_progress_action,
            readiness_followup=readiness_followup,
            stage_native_action=stage_native_action,
            top_level_study_actions=top_level_study_actions,
        ):
            fresh_progress_action = None
        if (
            fresh_progress_action is not None
            and fresh_progress_arbitration.has_current_quality_repair_writer_handoff(
                profile=profile,
                study=study_payload,
                fresh_action=fresh_progress_action,
            )
        ):
            fresh_progress_action = None
        current_writer_handoff_action = current_writer_handoff_by_study.get(study_id)
        if current_writer_handoff_action is not None:
            per_study_actions.append(current_writer_handoff_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_quality_repair_writer_handoff")
                for action in [
                    *([fresh_progress_action] if fresh_progress_action is not None else []),
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        if fresh_progress_action is not None:
            if currentness_owner_action is not None:
                if _fresh_repair_progress_action_matches_action_currentness(
                    fresh_action=fresh_progress_action,
                    currentness_action=currentness_owner_action,
                ):
                    per_study_actions.append(fresh_progress_action)
                    ignored.extend(
                        _ignored_action(action, "superseded_by_fresh_study_progress_current_owner_ticket")
                        for action in [
                            currentness_owner_action,
                            *([readiness_followup] if readiness_followup is not None else []),
                            *([stage_native_action] if stage_native_action is not None else []),
                            *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                            *top_level_study_actions,
                            *[
                                dict(item)
                                for item in study_payload.get("action_queue") or []
                                if isinstance(item, Mapping)
                            ],
                        ]
                        if action != fresh_progress_action
                    )
                    continue
                per_study_actions.append(currentness_owner_action)
                ignored.extend(
                    _ignored_action(action, _currentness_owner_action_ignored_reason(currentness_owner_action))
                    for action in [
                        fresh_progress_action,
                        *([readiness_followup] if readiness_followup is not None else []),
                        *([stage_native_action] if stage_native_action is not None else []),
                        *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                        *top_level_study_actions,
                        *[
                            dict(item)
                            for item in study_payload.get("action_queue") or []
                            if isinstance(item, Mapping)
                        ],
                    ]
                    if action != currentness_owner_action
                )
                continue
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_fresh_study_progress_current_owner_ticket")
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        if stage_native_action is not None:
            per_study_actions.append(stage_native_action)
            ignored.extend(
                _ignored_action(
                    action,
                    _stage_native_superseded_reason(
                        study=study_payload,
                        action=action,
                        stage_native_action=stage_native_action,
                    ),
                )
                for action in [
                    *current_route_queue_actions,
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
                if action != stage_native_action
            )
            continue
        if current_route_queue_actions:
            per_study_actions.extend(current_route_queue_actions)
            selected_fingerprints = {
                _text(action.get("action_fingerprint"))
                or _text(action.get("work_unit_fingerprint"))
                or _text(action.get("action_id"))
                for action in current_route_queue_actions
            }
            ignored.extend(
                _ignored_action(
                    action,
                    _ignored_reason_for_superseded_action(
                        action,
                        selected_actions=current_route_queue_actions,
                        default="superseded_by_current_owner_route_action_queue",
                    ),
                )
                for action in [
                    *([fresh_progress_action] if fresh_progress_action is not None else []),
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
                if (
                    _text(action.get("action_fingerprint"))
                    or _text(action.get("work_unit_fingerprint"))
                    or _text(action.get("action_id"))
                )
                not in selected_fingerprints
            )
            continue
        if readiness_followup is not None:
            if _stage_native_action_supersedes_stable_readiness_answer(
                study=study_payload,
                readiness_followup=readiness_followup,
                stage_native_action=stage_native_action,
            ):
                per_study_actions.append(dict(stage_native_action))
                ignored.extend(
                    _ignored_action(action, "superseded_by_stage_native_next_action_after_readiness_answer")
                    for action in [
                        readiness_followup,
                        *top_level_study_actions,
                        *[
                            dict(item)
                            for item in study_payload.get("action_queue") or []
                            if isinstance(item, Mapping)
                        ],
                    ]
                )
                continue
            per_study_actions.append(readiness_followup)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_stage_readiness_followup")
                for action in [
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                        and _text(item.get("action_type")) != READINESS_ACTION_TYPE
                    ],
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                ]
            )
            continue
        study_actions, study_ignored = _current_study_actions(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        per_study_actions.extend(study_actions)
        ignored.extend(study_ignored)
        if diagnostic_stage_native_action is not None:
            ignored.append(
                _ignored_action(
                    diagnostic_stage_native_action,
                    stage_native_next_action.diagnostic_blocked_reason(diagnostic_stage_native_action),
                )
            )
    for study_id, action in fresh_progress_by_study.items():
        if study_id in suppressed_fresh_progress_studies:
            continue
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    for study_id, action in dispatchable_stage_native_by_study.items():
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    for study_id, action in diagnostic_stage_native_by_study.items():
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            ignored.append(
                _ignored_action(
                    action,
                    stage_native_next_action.diagnostic_blocked_reason(action),
                )
            )
    if per_study_actions or matched_requested_study:
        return per_study_actions, ignored
    actions = scan_payload.get("action_queue")
    return (list(actions), ignored) if isinstance(actions, list) else (None, ignored)


def _current_writer_handoff_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    if profile is None:
        return {}
    try:
        from med_autoscience.controllers.domain_action_request_materializer_parts import current_writer_handoff
    except Exception:
        return {}
    actions: dict[str, dict[str, Any]] = {}
    for study_id in study_ids:
        action = current_writer_handoff.current_quality_repair_writer_handoff_action(
            profile=profile,
            study_id=study_id,
        )
        if action is not None:
            actions[study_id] = action
    return actions


def _current_readiness_followup_action(study: Mapping[str, Any]) -> dict[str, Any] | None:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    if not _route_allows_readiness_followup(owner_route):
        return None
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return None
    quest_id = _text(study.get("quest_id"))
    for action in study.get("action_queue") or []:
        payload = _mapping(action)
        if _text(payload.get("action_type")) != READINESS_ACTION_TYPE:
            continue
        if not _current_readiness_owner_action_matches(study, payload):
            continue
        payload["study_id"] = _text(payload.get("study_id")) or study_id
        if quest_id is not None:
            payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
        return _attach_owner_route_if_missing(payload, owner_route)
    action = _mapping(study.get("current_executable_owner_action"))
    if not _current_readiness_owner_action_matches(study, action):
        return None
    owner = _text(action.get("next_owner")) or _text(owner_route.get("next_owner")) or "MedAutoScience"
    payload = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": READINESS_ACTION_TYPE,
        "action_id": f"current-stage-readiness-followup::{study_id}",
        "reason": "medical_paper_readiness_not_ready",
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "mas_owner_surface",
        "required_output_surface": READINESS_ACTION_TYPE,
        "surface_key": _text(action.get("surface_key")) or _text(_mapping(action.get("target_surface")).get("surface_key")),
        "source_surface": _text(action.get("source")) or "current_executable_owner_action",
        "source_ref": _text(action.get("source_ref")),
        "work_unit_id": READINESS_ACTION_TYPE,
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint"))
        or _text(_mapping(owner_route.get("source_refs")).get("work_unit_fingerprint")),
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": READINESS_ACTION_TYPE,
            "request_owner": owner,
            "recommended_owner": owner,
            "surface_key": _text(action.get("surface_key"))
            or _text(_mapping(action.get("target_surface")).get("surface_key")),
            "source": _text(action.get("source")) or "current_executable_owner_action",
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in payload.items() if value is not None}


def _fresh_progress_supersedes_scan_action(
    *,
    fresh_progress_action: Mapping[str, Any],
    readiness_followup: Mapping[str, Any] | None,
    stage_native_action: Mapping[str, Any] | None,
) -> bool:
    action_type = _text(fresh_progress_action.get("action_type"))
    if action_type is not None and action_type.startswith("current_execution_envelope_"):
        return True
    if readiness_followup is not None:
        return True
    source_surface = _text(fresh_progress_action.get("source_surface")) or _text(fresh_progress_action.get("source"))
    return (
        stage_native_action is not None
        and action_type != _text(stage_native_action.get("action_type"))
        and source_surface == "domain_transition"
    )


def _fresh_progress_current_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    if profile is None:
        return []
    actions: list[dict[str, Any]] = []
    for study_id in study_ids:
        progress = _read_fresh_study_progress(profile=profile, study_id=study_id)
        if progress is None:
            continue
        action = _fresh_progress_current_action(study_id=study_id, progress=progress)
        if action is not None:
            actions.append(action)
    return actions


def _read_fresh_study_progress(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    try:
        from med_autoscience.controllers import study_progress

        payload = study_progress.read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except Exception:
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _fresh_progress_current_action(
    *,
    study_id: str,
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    barrier = _fresh_progress_currentness_barrier(study_id=study_id, progress=progress)
    if barrier is not None:
        return barrier
    if not _progress_has_executable_owner_action(progress):
        return None
    current_action = _mapping(progress.get("current_executable_owner_action"))
    repair_progress_followup = repair_progress_currentness.current_action_is_repair_progress_followup(
        current_action
    )
    ticket = {} if repair_progress_followup else _current_owner_ticket(progress)
    target_surface = _mapping(ticket.get("target_surface")) or _mapping(current_action.get("target_surface"))
    surface_key = (
        _text(ticket.get("surface_key"))
        or _text(target_surface.get("surface_key"))
        or _text(current_action.get("surface_key"))
        or _text(_mapping(current_action.get("target_surface")).get("surface_key"))
    )
    ticket_action_type = _text(ticket.get("allowed_action"))
    action_type = ticket_action_type if ticket_action_type in SUPPORTED_ACTION_TYPES else None
    source_surface = "study_progress.current_owner_ticket"
    if repair_progress_followup:
        action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
        source_surface = "study_progress.current_executable_owner_action"
    if action_type is None:
        transition_action = _fresh_progress_domain_transition_action(
            study_id=study_id,
            progress=progress,
            current_action=current_action,
        )
        if transition_action is not None:
            return transition_action
        action_type = fresh_progress_arbitration.current_action_supported_action_type(current_action)
        source_surface = "study_progress.current_executable_owner_action"
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    if action_type == READINESS_ACTION_TYPE:
        transition_action = _fresh_progress_domain_transition_action(
            study_id=study_id,
            progress=progress,
            current_action=current_action,
        )
        if transition_action is not None:
            return transition_action
        if surface_key is None:
            return None
    quest_id = _text(progress.get("quest_id"))
    work_unit_id = (
        _text(_mapping(ticket.get("work_unit")).get("work_unit_id"))
        or _text(current_action.get("work_unit_id"))
        or action_type
    )
    owner = (
        _text(ticket.get("owner"))
        or _text(current_action.get("next_owner"))
        or request_owner_for_action_type(action_type)
    )
    owner_route = _fresh_progress_owner_route(
        progress=progress,
        study_id=study_id,
        quest_id=quest_id,
        action_type=action_type,
        owner=owner,
        work_unit_id=work_unit_id,
    )
    action = {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"study-progress-current-owner-ticket::{study_id}::{action_type}",
        "reason": work_unit_id,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": source_surface,
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": source_surface,
        "current_action_source": _text(current_action.get("source"))
        or _text(current_action.get("source_surface")),
        "source_ref": _text(current_action.get("source_ref")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "surface_key": surface_key,
        "target_surface": target_surface or None,
        "repair_progress_precedence": _mapping(current_action.get("repair_progress_precedence")) or None,
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": source_surface,
            "current_action_source": _text(current_action.get("source"))
            or _text(current_action.get("source_surface")),
            "source_ref": _text(current_action.get("source_ref")),
            "surface_key": surface_key,
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in action.items() if value is not None}


def _fresh_progress_currentness_barrier(
    *,
    study_id: str,
    progress: Mapping[str, Any],
) -> dict[str, Any] | None:
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind not in {"typed_blocker", "parked", "running_provider_attempt"}:
        return None
    current_action = _mapping(progress.get("current_executable_owner_action"))
    if repair_progress_currentness.typed_blocker_allows_repair_progress_followup(
        envelope=envelope,
        current_action=current_action,
    ):
        return None
    blocker = _mapping(envelope.get("typed_blocker"))
    reason = (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
        or state_kind
    )
    if state_kind == "typed_blocker" and reason == "medical_paper_readiness_missing":
        return None
    owner = _text(envelope.get("owner")) or _text(blocker.get("owner")) or "MedAutoScience"
    return {
        "study_id": study_id,
        "quest_id": _text(progress.get("quest_id")),
        "action_type": f"current_execution_envelope_{state_kind}",
        "action_id": f"study-progress-current-execution-envelope::{study_id}::{state_kind}",
        "reason": reason,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "study_progress.current_execution_envelope",
        "source_surface": "study_progress.current_execution_envelope",
        "source_ref": _text(blocker.get("source_ref")),
        "work_unit_id": _text(blocker.get("work_unit_id")) or _work_unit_id(envelope.get("next_work_unit")),
    }


def _fresh_progress_typed_blocker_reason(envelope: Mapping[str, Any]) -> str | None:
    blocker = _mapping(envelope.get("typed_blocker"))
    return (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
    )


def _progress_has_executable_owner_action(progress: Mapping[str, Any]) -> bool:
    current_action = _mapping(progress.get("current_executable_owner_action"))
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind is not None:
        if repair_progress_currentness.typed_blocker_allows_repair_progress_followup(
            envelope=envelope,
            current_action=current_action,
        ):
            return _text(current_action.get("surface_kind")) == "current_executable_owner_action"
        if state_kind == "typed_blocker" and _fresh_progress_typed_blocker_reason(envelope) == "medical_paper_readiness_missing":
            return _text(current_action.get("surface_kind")) == "current_executable_owner_action"
        return state_kind == "executable_owner_action"
    return _text(current_action.get("surface_kind")) == "current_executable_owner_action"


def _fresh_progress_domain_transition_action(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    source = _text(current_action.get("source")) or _text(current_action.get("source_surface"))
    if source != "domain_transition":
        return None
    if _text(current_action.get("work_unit_id")) == READINESS_ACTION_TYPE:
        return None
    study_payload = _fresh_progress_domain_transition_study(
        study_id=study_id,
        progress=progress,
        current_action=current_action,
    )
    actions = _domain_transition_current_actions(study_payload)
    return actions[0] if actions else None


def _fresh_progress_domain_transition_study(
    *,
    study_id: str,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(progress)
    payload["study_id"] = _text(payload.get("study_id")) or study_id
    if quest_id := _text(progress.get("quest_id")):
        payload["quest_id"] = quest_id
    payload["current_executable_owner_action"] = dict(current_action)
    if _mapping(payload.get("domain_transition")):
        return payload
    transition = _domain_transition_from_current_action(progress=progress, current_action=current_action)
    if transition:
        payload["domain_transition"] = transition
    return payload


def _domain_transition_from_current_action(
    *,
    progress: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any]:
    envelope = _mapping(progress.get("current_execution_envelope"))
    work_unit_id = (
        _text(current_action.get("work_unit_id"))
        or _text(current_action.get("executable_work_unit"))
        or _work_unit_id(current_action.get("next_work_unit"))
        or _text(envelope.get("next_work_unit"))
    )
    if work_unit_id is None:
        return {}
    next_work_unit = _mapping(current_action.get("next_work_unit")) or {"unit_id": work_unit_id}
    if "lane" not in next_work_unit:
        if "gate_replay" in work_unit_id or "publication_gate" in work_unit_id:
            next_work_unit["lane"] = "publication_gate"
        elif _text(current_action.get("next_owner")) == "write" or _text(envelope.get("owner")) == "write":
            next_work_unit["lane"] = "write"
    route_target = (
        _text(current_action.get("route_target"))
        or _text(current_action.get("original_route_target"))
        or _text(current_action.get("next_owner"))
        or _text(envelope.get("owner"))
        or "controller"
    )
    return {
        "decision_type": _text(current_action.get("domain_transition_decision_type")) or "route_back_same_line",
        "route_target": route_target,
        "owner": route_target,
        "controller_action": _text(current_action.get("controller_action")) or "request_opl_stage_attempt",
        "next_work_unit": next_work_unit,
        "completion_receipt_consumption": {
            "status": "consumed",
            "receipt_ref": _text(current_action.get("source_ref")),
        },
    }


def _current_owner_ticket(progress: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        progress.get("current_owner_ticket"),
        _mapping(progress.get("progress_first_sprint_state")).get("current_owner_ticket"),
        _mapping(progress.get("next_forced_delta")).get("current_owner_ticket"),
    ):
        payload = _mapping(value)
        if _text(payload.get("surface_kind")) == "mas_current_owner_ticket":
            return payload
    return {}


def _fresh_progress_owner_route(
    *,
    progress: Mapping[str, Any],
    study_id: str,
    quest_id: str | None,
    action_type: str,
    owner: str,
    work_unit_id: str,
) -> dict[str, Any]:
    current_route = owner_route_part.ensure_owner_route_v2(_mapping(progress.get("owner_route")))
    candidate_action = {
        "action_type": action_type,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "next_executable_owner": owner,
    }
    if current_route and owner_route_part.route_allows_action(
        action=candidate_action,
        owner_route=current_route,
    ):
        return current_route
    current_action = _mapping(progress.get("current_executable_owner_action"))
    source_ref = _text(current_action.get("source_ref")) or _text(progress.get("generated_at")) or "unknown"
    truth = _mapping(progress.get("study_truth_snapshot"))
    runtime_health = _mapping(progress.get("runtime_health_snapshot"))
    truth_epoch = _text(progress.get("truth_epoch")) or _text(truth.get("truth_epoch")) or (
        f"study-progress-current-owner-ticket::{study_id}"
    )
    runtime_health_epoch = _text(progress.get("runtime_health_epoch")) or _text(
        runtime_health.get("runtime_health_epoch")
    ) or truth_epoch
    source_fingerprint = _text(current_action.get("source_fingerprint")) or (
        f"study-progress-current-owner-ticket::{study_id}::{action_type}::{source_ref}"
    )
    work_unit_fingerprint = _text(current_action.get("work_unit_fingerprint")) or (
        f"study-progress-current-owner-ticket::{study_id}::{work_unit_id}::{action_type}"
    )
    owner_reason = _text(current_action.get("reason")) or work_unit_id
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "failure_signature": owner_reason,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": truth_epoch,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": owner_reason,
        "active_run_id": _text(progress.get("active_run_id")),
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "source_surface": "study_progress.current_owner_ticket",
            "source_ref": source_ref,
            "owner_route_currentness_basis": {
                "truth_epoch": truth_epoch,
                "runtime_health_epoch": runtime_health_epoch,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
            },
        },
        "idempotency_key": (
            f"owner-route::{study_id}::{truth_epoch}::{owner}::{action_type}::{work_unit_fingerprint}"
        ),
    }
    return owner_route_part.ensure_owner_route_v2(route)


def _stage_native_action_supersedes_stable_readiness_answer(
    *,
    study: Mapping[str, Any],
    readiness_followup: Mapping[str, Any],
    stage_native_action: Mapping[str, Any] | None,
) -> bool:
    if not stage_native_action:
        return False
    if _text(stage_native_action.get("action_type")) == READINESS_ACTION_TYPE:
        return False
    return _readiness_followup_is_stable_owner_answer(study=study, action=readiness_followup)


def _stage_native_superseded_reason(
    *,
    study: Mapping[str, Any],
    action: Mapping[str, Any],
    stage_native_action: Mapping[str, Any],
) -> str:
    if (
        _text(action.get("action_type")) == READINESS_ACTION_TYPE
        and _stage_native_action_supersedes_stable_readiness_answer(
            study=study,
            readiness_followup=action,
            stage_native_action=stage_native_action,
        )
    ):
        return "superseded_by_stage_native_next_action_after_readiness_answer"
    return "superseded_by_stage_native_next_action"


def _readiness_followup_is_stable_owner_answer(
    *,
    study: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if _text(action.get("reason")) == "medical_paper_readiness_missing":
        return True
    current = _mapping(study.get("current_executable_owner_action"))
    precedence = _mapping(current.get("artifact_first_precedence"))
    return (
        _text(current.get("latest_owner_answer_kind")) == "typed_blocker"
        and _text(precedence.get("reason")) == "medical_paper_readiness_missing"
    )


def _route_allows_readiness_followup(owner_route: Mapping[str, Any]) -> bool:
    allowed_actions = {_text(item) for item in owner_route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    return _text(owner_route.get("next_owner")) == "MedAutoScience" and READINESS_ACTION_TYPE in allowed_actions


def _current_readiness_owner_action_matches(study: Mapping[str, Any], action: Mapping[str, Any]) -> bool:
    if _text(action.get("action_type")) == READINESS_ACTION_TYPE:
        return True
    allowed_actions = {_text(item) for item in action.get("allowed_actions") or []}
    allowed_actions.discard(None)
    if READINESS_ACTION_TYPE not in allowed_actions:
        return False
    if _text(action.get("work_unit_id")) not in {READINESS_ACTION_TYPE, None}:
        return False
    source = _text(action.get("source")) or _text(action.get("source_surface"))
    if source not in {
        "stage_kernel_projection.current_owner_delta",
        "current_executable_owner_action",
    }:
        return False
    current = _mapping(study.get("current_executable_owner_action"))
    if current:
        current_allowed = {_text(item) for item in current.get("allowed_actions") or []}
        current_allowed.discard(None)
        return READINESS_ACTION_TYPE in current_allowed
    return True


def _requires_manuscript_story_surface_delta(value: object) -> bool:
    text = str(value or "").strip().lower()
    return (
        "canonical manuscript story-surface delta" in text
        and "typed blocker:manuscript_story_surface_delta_missing" in text
    )


def _current_study_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    top_level_study_actions = _top_level_study_actions(study=study, top_level_actions=top_level_actions)
    queue_actions, queue_source = _study_queue_actions(
        study=study,
        top_level_study_actions=top_level_study_actions,
    )
    current_queue_actions = [
        action for action in queue_actions if _queue_action_allowed_by_current_study_route(action, study)
    ]
    if current_queue_actions:
        return current_queue_actions, _ignored_actions_superseded_by_readiness_blocker_repair(
            queue_actions=queue_actions,
            selected_actions=current_queue_actions,
        )
    transition_actions = _domain_transition_current_actions(study)
    if not transition_actions:
        if queue_source == "per_study_empty":
            return [], [
                _ignored_action(action, "superseded_by_current_study_empty_action_queue")
                for action in top_level_study_actions
            ]
        if _current_execution_is_authoritative(study):
            return [], [
                _ignored_action(action, "superseded_by_current_execution_envelope")
                for action in top_level_study_actions
            ]
        stale_route_actions = [
            action for action in queue_actions if _queue_action_disallowed_by_current_study_route(action, study)
        ]
        if stale_route_actions:
            stale_ids = {_action_identity(action) for action in stale_route_actions}
            remaining_actions = [
                action for action in queue_actions if _action_identity(action) not in stale_ids
            ]
            return remaining_actions, [
                _ignored_action(action, "superseded_by_current_owner_route_action_queue")
                for action in stale_route_actions
            ]
        return queue_actions, []
    ignored = [_ignored_action(action, "superseded_by_current_domain_transition") for action in queue_actions]
    if queue_source == "per_study_empty":
        ignored.extend(
            _ignored_action(action, "superseded_by_current_domain_transition")
            for action in top_level_study_actions
        )
    return transition_actions, ignored


def _current_owner_route_queue_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    queue_actions, _queue_source = _study_queue_actions(
        study=study,
        top_level_study_actions=_top_level_study_actions(
            study=study,
            top_level_actions=top_level_actions,
        ),
    )
    return [
        action
        for action in queue_actions
        if _text(action.get("action_type")) != READINESS_ACTION_TYPE
        and _queue_action_allowed_by_current_study_route(action, study)
    ]


def _scan_domain_transition_has_current_action(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any],
) -> bool:
    if not _mapping(study.get("domain_transition")):
        return False
    return bool(_domain_transition_current_actions(study))


def _current_writer_handoff_owner_action(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    actions, _ = _current_study_actions(study=study, top_level_actions=top_level_actions)
    for action in actions:
        if _writer_handoff_owner_action_preempts_fresh_progress(action=action, study=study):
            return action
    return None


def _writer_handoff_owner_action_preempts_fresh_progress(
    *,
    action: Mapping[str, Any],
    study: Mapping[str, Any],
) -> bool:
    action_type = _text(action.get("action_type"))
    if action_type != "run_quality_repair_batch":
        return False
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
        or _mapping(study.get("owner_route"))
    )
    if not owner_route:
        return False
    if _text(owner_route.get("next_owner")) != "write":
        return False
    if _text(owner_route.get("owner_reason")) not in {
        "manuscript_story_surface_delta_missing",
        "quest_waiting_opl_runtime_owner_route",
    }:
        return False
    return _action_allowed_by_owner_route(action, owner_route)


def _currentness_owner_action(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    actions, _ = _current_study_actions(study=study, top_level_actions=top_level_actions)
    for action in actions:
        if _ai_reviewer_currentness_action_preempts_fresh_progress(action=action, study=study):
            return action
    return None


def _ai_reviewer_currentness_action_preempts_fresh_progress(
    *,
    action: Mapping[str, Any],
    study: Mapping[str, Any],
) -> bool:
    if _text(action.get("action_type")) != "return_to_ai_reviewer_workflow":
        return False
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
        or _mapping(study.get("owner_route"))
    )
    if not owner_route:
        return False
    if _text(owner_route.get("next_owner")) != "ai_reviewer":
        return False
    owner_contract = _mapping(owner_route.get("owner_reason_contract"))
    if not _has_explicit_ai_reviewer_currentness_contract(action=action, owner_route=owner_route):
        return False
    if _text(action.get("required_output_surface")) != "artifacts/publication_eval/latest.json" and _text(
        owner_contract.get("required_output")
    ) != "artifacts/publication_eval/latest.json":
        return False
    forbidden = {_text(item) for item in owner_contract.get("forbidden_surfaces") or []}
    forbidden.discard(None)
    if "artifacts/publication_eval/latest.json" not in forbidden:
        return False
    return _action_allowed_by_owner_route(action, owner_route)


def _has_explicit_ai_reviewer_currentness_contract(
    *,
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    basis = _mapping(_mapping(owner_route.get("currentness_contract")).get("basis"))
    if basis:
        return True
    source_refs = _mapping(owner_route.get("source_refs"))
    if _mapping(source_refs.get("owner_route_currentness_basis")) and (
        _text(action.get("source_surface")) in {"owner_route_currentness", "ai_reviewer_record_currentness"}
        or _text(action.get("next_work_unit")) == "produce_ai_reviewer_publication_eval_record_against_current_inputs"
        or _text(action.get("next_work_unit"))
        == "produce_ai_reviewer_publication_eval_record_against_current_manuscript"
    ):
        return True
    owner_contract = _mapping(owner_route.get("owner_reason_contract"))
    forbidden = {_text(item) for item in owner_contract.get("forbidden_surfaces") or []}
    forbidden.discard(None)
    return "artifacts/publication_eval/latest.json" in forbidden


def _currentness_owner_action_ignored_reason(action: Mapping[str, Any]) -> str:
    if _text(action.get("action_type")) == "run_quality_repair_batch":
        return "superseded_by_current_writer_handoff_owner_action"
    return "superseded_by_current_owner_route_currentness_action"


def _ignored_reason_for_superseded_action(
    action: Mapping[str, Any],
    *,
    selected_actions: Iterable[Mapping[str, Any]],
    default: str,
) -> str:
    if _text(action.get("action_type")) == READINESS_ACTION_TYPE and any(
        _readiness_blocker_derived_repair_action(selected) for selected in selected_actions
    ):
        return "superseded_by_readiness_blocker_derived_repair"
    return default


def _study_queue_actions(
    *,
    study: Mapping[str, Any],
    top_level_study_actions: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], str]:
    study_id = _text(study.get("study_id"))
    quest_id = _text(study.get("quest_id"))
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    actions: list[dict[str, Any]] = []
    if "action_queue" in study:
        for action in study.get("action_queue") or []:
            if not isinstance(action, Mapping):
                continue
            payload = dict(action)
            if study_id is not None:
                payload["study_id"] = _text(payload.get("study_id")) or study_id
            if quest_id is not None:
                payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
            actions.append(_attach_owner_route_if_missing(payload, owner_route))
        return actions, "per_study" if actions else "per_study_empty"
    if _current_execution_is_authoritative(study):
        return [], "current_execution_envelope"
    for action in top_level_study_actions:
        payload = dict(action)
        if quest_id is not None:
            payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
        actions.append(_attach_owner_route_if_missing(payload, owner_route))
    return actions, "top_level"


def _top_level_study_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    study_id = _text(study.get("study_id"))
    return [
        dict(action)
        for action in top_level_actions
        if isinstance(action, Mapping) and _text(action.get("study_id")) == study_id
    ]


def _attach_owner_route_if_missing(action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(action)
    if not owner_route:
        return payload
    handoff = dict(_mapping(payload.get("handoff_packet")))
    if _mapping(payload.get("owner_route")) or _mapping(handoff.get("owner_route")):
        return payload
    payload["owner_route"] = dict(owner_route)
    handoff["owner_route"] = dict(owner_route)
    if idempotency_key := _text(owner_route.get("idempotency_key")):
        handoff["idempotency_key"] = idempotency_key
    payload["handoff_packet"] = handoff
    return payload


def _domain_transition_current_actions(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return []
    generated = domain_transition_actions.actions(study)
    if not generated:
        return []
    quest_id = _text(study.get("quest_id"))
    owner_route = _domain_transition_owner_route(study=study, generated=generated, study_id=study_id, quest_id=quest_id)
    if not owner_route:
        return []
    decorated_actions: list[dict[str, Any]] = []
    for action in generated:
        if not isinstance(action, Mapping):
            continue
        action_type = _text(action.get("action_type"))
        if action_type not in SUPPORTED_ACTION_TYPES:
            continue
        decorated = action_decorators.decorate_action(
            study_id=study_id,
            quest_id=quest_id,
            action=action,
            request_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_REQUEST_ALLOWED_WRITE_SURFACES),
            control_allowed_write_surfaces=list(domain_route_contract.SUPERVISION_CONTROL_ALLOWED_WRITE_SURFACES),
            forbidden_actions=list(domain_route_contract.SUPERVISION_FORBIDDEN_ACTIONS),
        )
        decorated["study_id"] = study_id
        if quest_id is not None:
            decorated["quest_id"] = quest_id
        routed = owner_route_part.decorate_actions(actions=[decorated], owner_route=owner_route)[0]
        if _action_allowed_by_owner_route(routed, owner_route):
            decorated_actions.append(routed)
    return decorated_actions


def _consumed_domain_transition_actions(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    transition = _mapping(study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return []
    if _text(transition.get("controller_action")) is None:
        return []
    if not _mapping(transition.get("next_work_unit")):
        return []
    return _domain_transition_current_actions(study)


def _domain_transition_owner_route(
    *,
    study: Mapping[str, Any],
    generated: list[dict[str, Any]],
    study_id: str,
    quest_id: str | None,
) -> dict[str, Any]:
    transition = _mapping(study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if (
        _text(completion.get("status")) in {"consumed", "receipt_consumed", "completed"}
        and _text(transition.get("controller_action")) is not None
        and _mapping(transition.get("next_work_unit"))
    ):
        current_study = owner_route_currentness_projection.study_with_owner_route_currentness(
            study,
            generated=generated,
            ensure_owner_route_v2=owner_route_part.ensure_owner_route_v2,
            action_allowed_by_owner_route=_action_allowed_by_owner_route,
        )
        return owner_route_part.build_owner_route(
            study_id=study_id,
            quest_id=quest_id,
            status=current_study,
            progress={},
            actions=generated,
            blocked_reason=_text(generated[0].get("reason")),
            next_owner=_text(generated[0].get("owner")) or _text(generated[0].get("request_owner")),
            active_run_id=_text(current_study.get("active_run_id")),
        )
    return owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))


def domain_transition_owner_route_for_study(study: Mapping[str, Any]) -> dict[str, Any]:
    study_payload = _mapping(study)
    study_id = _text(study_payload.get("study_id"))
    if study_id is None:
        return {}
    generated = domain_transition_actions.actions(study_payload)
    if not generated:
        return {}
    return _domain_transition_owner_route(
        study=study_payload,
        generated=generated,
        study_id=study_id,
        quest_id=_text(study_payload.get("quest_id")),
    )


def _queue_action_allowed_by_current_study_route(action: Mapping[str, Any], study: Mapping[str, Any]) -> bool:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    if not owner_route or not _action_allowed_by_owner_route(action, owner_route):
        return False
    action_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    return not action_route or owner_route_part.owner_route_matches(
        dispatch=action,
        current_route=owner_route,
    )


def _queue_action_disallowed_by_current_study_route(
    action: Mapping[str, Any],
    study: Mapping[str, Any],
) -> bool:
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    if not owner_route:
        return False
    action_type = _text(action.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return False
    allowed_actions = {_text(item) for item in owner_route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    if bool(allowed_actions) and action_type not in allowed_actions:
        return True
    action_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    return bool(action_route) and not owner_route_part.owner_route_matches(
        dispatch=action,
        current_route=owner_route,
    )


def _action_identity(action: Mapping[str, Any]) -> tuple[str | None, str | None, str | None]:
    return (
        _text(action.get("study_id")),
        _text(action.get("action_type")),
        _text(action.get("action_id")),
    )


def _ignored_actions_superseded_by_readiness_blocker_repair(
    *,
    queue_actions: list[dict[str, Any]],
    selected_actions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not any(_readiness_blocker_derived_repair_action(action) for action in selected_actions):
        return []
    ignored: list[dict[str, Any]] = []
    selected_fingerprints = {
        _text(action.get("work_unit_fingerprint"))
        for action in selected_actions
        if _text(action.get("work_unit_fingerprint")) is not None
    }
    for action in queue_actions:
        if _text(action.get("work_unit_fingerprint")) in selected_fingerprints:
            continue
        if _text(action.get("action_type")) != READINESS_ACTION_TYPE:
            continue
        ignored.append(_ignored_action(action, "superseded_by_readiness_blocker_derived_repair"))
    return ignored


def _readiness_blocker_derived_repair_action(action: Mapping[str, Any]) -> bool:
    if _text(action.get("reason")) != "medical_paper_readiness_repair_required":
        return False
    return _text(action.get("readiness_blocker_followup_superseded")) == READINESS_ACTION_TYPE


def _action_allowed_by_owner_route(action: Mapping[str, Any], owner_route: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type")) or "unknown_action"
    return owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": _owner_from_action(action, action_type),
            "action_type": action_type,
        },
        owner_route=owner_route,
    )


def _current_execution_is_authoritative(study: Mapping[str, Any]) -> bool:
    envelope = _mapping(study.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    return state_kind in {
        "typed_blocker",
        "blocked_typed_owner",
        "parked",
        "executable_owner_action",
        "running_provider_attempt",
    }


def _scan_currentness_preempts_fresh_progress(
    study: Mapping[str, Any],
    *,
    fresh_action: Mapping[str, Any],
) -> bool:
    if repair_progress_currentness.generated_action_matches_scan_currentness(
        study=study,
        fresh_action=fresh_action,
    ):
        return False
    transition = _mapping(study.get("domain_transition"))
    if _text(transition.get("decision_type")) is not None:
        return True
    return _current_execution_is_authoritative(study)


def _fresh_repair_progress_action_matches_action_currentness(
    *,
    fresh_action: Mapping[str, Any],
    currentness_action: Mapping[str, Any],
) -> bool:
    return repair_progress_currentness.generated_action_matches_action_currentness(
        fresh_action=fresh_action,
        currentness_action=currentness_action,
    )


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or request_owner_for_action_type(action_type)
    )


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
    if stage_native_next_action.is_diagnostic_action(action):
        reason = stage_native_next_action.diagnostic_blocked_reason(action)
    return {
        "study_id": _text(action.get("study_id")),
        "action_type": _text(action.get("action_type")),
        "action_id": _text(action.get("action_id")),
        "reason": reason,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_actions_for_studies", "domain_transition_owner_route_for_study"]
