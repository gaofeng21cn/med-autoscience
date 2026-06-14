from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    current_action_authority,
    current_action_queue,
    domain_transition_current_actions,
    current_work_unit_action,
    current_typed_blocker_transition_barrier,
    fresh_progress_current_action,
    fresh_progress_arbitration,
    paper_recovery_owner_callable,
    repair_progress_currentness,
    stage_native_next_action,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


READINESS_ACTION_TYPE = current_action_authority.READINESS_ACTION_TYPE
_attach_owner_route_if_missing = current_action_queue.attach_owner_route_if_missing
_ignored_action = current_action_queue.ignored_action
_top_level_study_actions = current_action_queue.top_level_study_actions
_unique_actions = current_action_queue.unique_actions


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
    fresh_progress_actions = fresh_progress_current_action.current_actions(
        profile=profile,
        study_ids=study_ids,
        domain_transition_actions=domain_transition_current_actions.current_actions,
        explicit_readiness_action=current_action_authority.explicit_current_readiness_action,
    )
    fresh_progress_by_study = {
        study_id: action
        for action in fresh_progress_actions
        if (study_id := _text(action.get("study_id"))) is not None
    }
    fresh_paper_recovery_by_study = paper_recovery_owner_callable.current_actions(
        profile=profile,
        study_ids=study_ids,
    )
    top_level_actions = [
        dict(action) for action in scan_payload.get("action_queue") or [] if isinstance(action, Mapping)
    ]
    matched_requested_study = False
    matched_scan_study_ids: set[str] = set()
    suppressed_fresh_progress_studies: set[str] = set()
    for study in scan_payload.get("studies") or []:
        study_payload = _mapping(study)
        study_id = _text(study_payload.get("study_id"))
        if study_id not in requested:
            continue
        matched_requested_study = True
        matched_scan_study_ids.add(study_id)
        stage_native_action = dispatchable_stage_native_by_study.get(study_id)
        original_stage_native_action = stage_native_action
        diagnostic_stage_native_action = diagnostic_stage_native_by_study.get(study_id)
        stage_native_derives_from_readiness_answer = (
            stage_native_action is not None
            and current_action_authority.stage_native_action_derives_from_stable_readiness_answer(
                study=study_payload,
                action=stage_native_action,
            )
        )
        if (
            stage_native_action is not None
            and not stage_native_derives_from_readiness_answer
            and not current_action_authority.stage_native_action_matches_current_study(
                study=study_payload,
                action=stage_native_action,
            )
        ):
            diagnostic_stage_native_action = current_action_authority.stage_native_currentness_diagnostic(
                stage_native_action
            )
            stage_native_action = None
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
        paper_recovery_owner_callable_action = paper_recovery_owner_callable.action_for_study(
            study_payload
        ) or fresh_paper_recovery_by_study.get(study_id)
        canonical_current_action = current_work_unit_action.canonical_current_work_unit_action(study_payload)
        writer_handoff_owner_action = _current_writer_handoff_owner_action(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        currentness_owner_action = writer_handoff_owner_action or _currentness_owner_action(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        transition_actions = domain_transition_current_actions.consumed_current_actions(study_payload)
        per_study_queue_actions = [
            dict(item)
            for item in study_payload.get("action_queue") or []
            if isinstance(item, Mapping)
        ]
        stale_candidate_actions = [
            *transition_actions,
            *top_level_study_actions,
            *per_study_queue_actions,
            *current_route_queue_actions,
        ]
        if canonical_current_action is not None:
            stale_candidate_actions.append(canonical_current_action)
        stale_candidate_actions = _unique_actions(stale_candidate_actions)
        transition_barrier = None
        if (
            canonical_current_action is None
            and readiness_followup is None
            and stage_native_action is None
            and not stage_native_derives_from_readiness_answer
            and not _fresh_progress_is_repair_progress_followup(fresh_progress_action)
            and not _fresh_progress_is_accepted_owner_gate_decision(fresh_progress_action)
        ):
            transition_barrier = (
                current_typed_blocker_transition_barrier.current_typed_blocker_barrier_for_actions(
                    study=study_payload,
                    fresh_action=fresh_progress_action,
                    candidate_actions=stale_candidate_actions,
                )
            )
        if (
            fresh_progress_action is not None
            and _fresh_progress_is_accepted_owner_gate_decision(fresh_progress_action)
        ):
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_fresh_study_progress_current_owner_ticket")
                for action in [
                    *([canonical_current_action] if canonical_current_action is not None else []),
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *transition_actions,
                    *current_route_queue_actions,
                    *per_study_queue_actions,
                ]
                if action != fresh_progress_action
            )
            continue
        if paper_recovery_owner_callable_action is not None and readiness_followup is None:
            per_study_actions.append(paper_recovery_owner_callable_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_paper_recovery_owner_callable")
                for action in [
                    *stale_candidate_actions,
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *([fresh_progress_action] if fresh_progress_action is not None else []),
                ]
                if action != paper_recovery_owner_callable_action
            )
            continue
        if _fresh_progress_is_current_execution_envelope_barrier(fresh_progress_action):
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_work_unit_typed_blocker")
                for action in [
                    *([canonical_current_action] if canonical_current_action is not None else []),
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                    *top_level_study_actions,
                    *transition_actions,
                    *current_route_queue_actions,
                    *per_study_queue_actions,
                ]
                if action != fresh_progress_action
            )
            continue
        if fresh_progress_action is not None and not _mapping(study_payload.get("current_work_unit")):
            canonical_current_action = None
        stage_native_derives_from_readiness_answer = (
            original_stage_native_action is not None
            and (
                stage_native_derives_from_readiness_answer
                or current_action_authority.stage_native_action_derives_from_readiness_barrier(
                    fresh_action=fresh_progress_action,
                    action=original_stage_native_action,
                )
            )
        )
        if stage_native_action is None and stage_native_derives_from_readiness_answer:
            stage_native_action = original_stage_native_action
            diagnostic_stage_native_action = None
            transition_barrier = None
        if transition_barrier is not None:
            per_study_actions.append(transition_barrier)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_work_unit_typed_blocker")
                for action in [
                    *stale_candidate_actions,
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                ]
                if action != transition_barrier
            )
            continue
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
        if (
            readiness_followup is not None
            and fresh_progress_action is not None
            and not _scan_currentness_preempts_fresh_progress(
                study_payload,
                fresh_action=fresh_progress_action,
            )
            and fresh_progress_arbitration.can_preempt_scan(
                study=study_payload,
                fresh_action=fresh_progress_action,
                readiness_followup=readiness_followup,
                stage_native_action=stage_native_action,
                top_level_study_actions=top_level_study_actions,
            )
            and _text(fresh_progress_action.get("action_type")) != READINESS_ACTION_TYPE
            and not current_action_authority.stage_native_action_supersedes_stable_readiness_answer(
                study=study_payload,
                readiness_followup=readiness_followup,
                stage_native_action=stage_native_action,
            )
            and not fresh_progress_arbitration.has_current_quality_repair_writer_handoff(
                profile=profile,
                study=study_payload,
                fresh_action=fresh_progress_action,
            )
        ):
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_fresh_study_progress_current_owner_ticket")
                for action in [
                    readiness_followup,
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
                if action != fresh_progress_action
            )
            continue
        if readiness_followup is not None:
            if current_action_authority.stage_native_action_supersedes_stable_readiness_answer(
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
                        *transition_actions,
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
                    *transition_actions,
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
        if stage_native_derives_from_readiness_answer and stage_native_action is not None:
            per_study_actions.append(stage_native_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_readiness_blocker_derived_repair")
                for action in [
                    *top_level_study_actions,
                    *transition_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                    *([diagnostic_stage_native_action] if diagnostic_stage_native_action is not None else []),
                ]
                if action != stage_native_action
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
        if (
            fresh_progress_action is not None
            and not _fresh_progress_is_accepted_owner_gate_decision(fresh_progress_action)
            and _scan_currentness_preempts_fresh_progress(
                study_payload,
                fresh_action=fresh_progress_action,
            )
        ):
            suppressed_fresh_progress_studies.add(study_id)
            fresh_progress_action = None
        if (
            fresh_progress_action is not None
            and not _fresh_progress_is_accepted_owner_gate_decision(fresh_progress_action)
            and not fresh_progress_arbitration.can_preempt_scan(
                study=study_payload,
                fresh_action=fresh_progress_action,
                readiness_followup=readiness_followup,
                stage_native_action=stage_native_action,
                top_level_study_actions=top_level_study_actions,
            )
        ):
            fresh_progress_action = None
        if (
            fresh_progress_action is not None
            and not _fresh_progress_is_accepted_owner_gate_decision(fresh_progress_action)
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
                if (
                    fresh_progress_arbitration.fresh_action_supersedes_currentness_action(
                        fresh_action=fresh_progress_action,
                        currentness_action=currentness_owner_action,
                    )
                    or _fresh_repair_progress_action_matches_action_currentness(
                        fresh_action=fresh_progress_action,
                        currentness_action=currentness_owner_action,
                    )
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
                    current_action_authority.stage_native_superseded_reason(
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
    for study_id, action in fresh_paper_recovery_by_study.items():
        if study_id in suppressed_fresh_progress_studies:
            continue
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    for study_id, action in fresh_progress_by_study.items():
        if study_id in suppressed_fresh_progress_studies:
            continue
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    for study_id, action in dispatchable_stage_native_by_study.items():
        if study_id in matched_scan_study_ids:
            ignored.append(
                _ignored_action(
                    action,
                    stage_native_next_action.diagnostic_blocked_reason(
                        current_action_authority.stage_native_currentness_diagnostic(action)
                    ),
                )
            )
            continue
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
    if not current_action_authority.route_allows_readiness_followup(owner_route):
        return None
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return None
    quest_id = _text(study.get("quest_id"))
    for action in study.get("action_queue") or []:
        payload = _mapping(action)
        if _text(payload.get("action_type")) != READINESS_ACTION_TYPE:
            continue
        if not current_action_authority.current_readiness_owner_action_matches(study, payload):
            continue
        payload["study_id"] = _text(payload.get("study_id")) or study_id
        if quest_id is not None:
            payload["quest_id"] = _text(payload.get("quest_id")) or quest_id
        return _attach_owner_route_if_missing(payload, owner_route)
    action = _mapping(study.get("current_executable_owner_action"))
    if not current_action_authority.current_readiness_owner_action_matches(study, action):
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


def _fresh_progress_is_repair_progress_followup(action: Mapping[str, Any] | None) -> bool:
    return action is not None and repair_progress_currentness.generated_action_is_repair_progress_followup(action)


def _fresh_progress_is_accepted_owner_gate_decision(action: Mapping[str, Any] | None) -> bool:
    if action is None:
        return False
    return (
        _text(action.get("authority")) == "paper_recovery_state.accepted_owner_gate_decision"
        or _text(action.get("source_surface")) == "paper_recovery_state.accepted_owner_gate_decision"
        or _text(action.get("current_action_source")) == "paper_recovery_state.accepted_owner_gate_decision"
    )


def _fresh_progress_is_current_execution_envelope_barrier(action: Mapping[str, Any] | None) -> bool:
    return action is not None and (_text(action.get("action_type")) or "").startswith(
        "current_execution_envelope_"
    )


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
    return current_action_queue.current_study_actions(
        study=study,
        top_level_actions=top_level_actions,
        readiness_action_type=READINESS_ACTION_TYPE,
    )


def _current_owner_route_queue_actions(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    return current_action_queue.current_owner_route_queue_actions(
        study=study,
        top_level_actions=top_level_actions,
        readiness_action_type=READINESS_ACTION_TYPE,
    )


def _scan_domain_transition_has_current_action(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any],
) -> bool:
    if not _mapping(study.get("domain_transition")):
        return False
    return bool(domain_transition_current_actions.current_actions(study))


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
    return current_action_authority.action_allowed_by_owner_route(action, owner_route)


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
    return current_action_authority.action_allowed_by_owner_route(action, owner_route)


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


def domain_transition_owner_route_for_study(study: Mapping[str, Any]) -> dict[str, Any]:
    return domain_transition_current_actions.owner_route_for_study(study)


def _readiness_blocker_derived_repair_action(action: Mapping[str, Any]) -> bool:
    if _text(action.get("reason")) != "medical_paper_readiness_repair_required":
        return False
    return _text(action.get("readiness_blocker_followup_superseded")) == READINESS_ACTION_TYPE


def _scan_currentness_preempts_fresh_progress(
    study: Mapping[str, Any],
    *,
    fresh_action: Mapping[str, Any],
) -> bool:
    if fresh_progress_arbitration.can_preempt_scan(
        study=study,
        fresh_action=fresh_action,
        readiness_followup=None,
        stage_native_action=None,
        top_level_study_actions=[],
    ):
        return False
    if fresh_progress_arbitration.gate_followthrough_owner_action_has_strong_identity(fresh_action):
        return False
    if repair_progress_currentness.generated_action_matches_scan_currentness(
        study=study,
        fresh_action=fresh_action,
    ):
        return False
    if repair_progress_currentness.generated_action_is_repair_progress_followup(fresh_action):
        return False
    transition = _mapping(study.get("domain_transition"))
    if _text(transition.get("decision_type")) is not None:
        return True
    return current_action_queue.current_execution_is_authoritative(study)


def _fresh_repair_progress_action_matches_action_currentness(
    *,
    fresh_action: Mapping[str, Any],
    currentness_action: Mapping[str, Any],
) -> bool:
    return repair_progress_currentness.generated_action_matches_action_currentness(
        fresh_action=fresh_action,
        currentness_action=currentness_action,
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_actions_for_studies", "domain_transition_owner_route_for_study"]
