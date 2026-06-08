from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from pathlib import Path
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
    fresh_progress_arbitration,
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
    stage_native_actions = _stage_native_next_actions(profile=profile, study_ids=study_ids)
    stage_native_by_study = {
        study_id: action for action in stage_native_actions if (study_id := _text(action.get("study_id"))) is not None
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
    for study in scan_payload.get("studies") or []:
        study_payload = _mapping(study)
        study_id = _text(study_payload.get("study_id"))
        if study_id not in requested:
            continue
        matched_requested_study = True
        stage_native_action = stage_native_by_study.get(study_id)
        readiness_followup = _current_readiness_followup_action(study_payload)
        fresh_progress_action = fresh_progress_by_study.get(study_id)
        if fresh_progress_action is not None and not fresh_progress_arbitration.can_preempt_scan(
            study=study_payload,
            fresh_action=fresh_progress_action,
            readiness_followup=readiness_followup,
            stage_native_action=stage_native_action,
            top_level_study_actions=_top_level_study_actions(
                study=study_payload,
                top_level_actions=top_level_actions,
            ),
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
                    *_top_level_study_actions(study=study_payload, top_level_actions=top_level_actions),
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        if fresh_progress_action is not None:
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_fresh_study_progress_current_owner_ticket")
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *([stage_native_action] if stage_native_action is not None else []),
                    *_top_level_study_actions(study=study_payload, top_level_actions=top_level_actions),
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
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
                        *_top_level_study_actions(study=study_payload, top_level_actions=top_level_actions),
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
                    *_top_level_study_actions(study=study_payload, top_level_actions=top_level_actions),
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                        and _text(item.get("action_type")) != READINESS_ACTION_TYPE
                    ],
                    *(
                        [stage_native_by_study[study_id]]
                        if study_id in stage_native_by_study
                        else []
                    ),
                ]
            )
            continue
        if stage_native_action is not None:
            per_study_actions.append(stage_native_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_stage_native_next_action")
                for action in [
                    *_top_level_study_actions(study=study_payload, top_level_actions=top_level_actions),
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        study_actions, study_ignored = _current_study_actions(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        per_study_actions.extend(study_actions)
        ignored.extend(study_ignored)
    for study_id, action in fresh_progress_by_study.items():
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    for study_id, action in stage_native_by_study.items():
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
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
    ticket = _current_owner_ticket(progress)
    target_surface = _mapping(ticket.get("target_surface"))
    surface_key = (
        _text(ticket.get("surface_key"))
        or _text(target_surface.get("surface_key"))
        or _text(current_action.get("surface_key"))
        or _text(_mapping(current_action.get("target_surface")).get("surface_key"))
    )
    action_type = _text(ticket.get("allowed_action"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return _fresh_progress_domain_transition_action(
            study_id=study_id,
            progress=progress,
            current_action=current_action,
        )
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
        "authority": "study_progress.current_owner_ticket",
        "required_output_surface": request_output_surface_for_action_type(action_type),
        "source_surface": "study_progress.current_owner_ticket",
        "source_ref": _text(current_action.get("source_ref")),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "surface_key": surface_key,
        "target_surface": target_surface or None,
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": action_type,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "source_surface": "study_progress.current_owner_ticket",
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


def _progress_has_executable_owner_action(progress: Mapping[str, Any]) -> bool:
    envelope = _mapping(progress.get("current_execution_envelope"))
    state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if state_kind is not None:
        return state_kind == "executable_owner_action"
    current_action = _mapping(progress.get("current_executable_owner_action"))
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


def _stage_native_next_actions(
    *,
    profile: WorkspaceProfile | None,
    study_ids: tuple[str, ...],
) -> list[dict[str, Any]]:
    if profile is None:
        return []
    actions: list[dict[str, Any]] = []
    for study_id in study_ids:
        action = _stage_native_next_action(profile=profile, study_id=study_id)
        if action is not None:
            actions.append(action)
    return actions


def _stage_native_next_action(*, profile: WorkspaceProfile, study_id: str) -> dict[str, Any] | None:
    study_root = profile.studies_root / study_id
    next_action = _read_json_mapping(study_root / "control" / "next_action.json")
    if next_action is None:
        return None
    action_type = _text(next_action.get("action_id")) or _text(next_action.get("action_type"))
    if action_type not in SUPPORTED_ACTION_TYPES:
        return None
    if _text(next_action.get("status")) != "ready_for_owner_action":
        return None
    owner = _text(next_action.get("owner")) or request_owner_for_action_type(action_type)
    quest_id = _read_quest_id(study_root=study_root, fallback=study_id)
    owner_route = _stage_native_owner_route(
        study_id=study_id,
        quest_id=quest_id,
        action_type=action_type,
        owner=owner,
        next_action=next_action,
    )
    return {
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": action_type,
        "action_id": f"stage-native-next-action::{study_id}::{action_type}",
        "reason": action_type,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "stage_native_workspace_next_action",
        "required_output_surface": _text(next_action.get("target_surface"))
        or _text(next_action.get("required_output_surface"))
        or "artifacts/reports/medical_publication_surface/latest.json",
        "source_surface": _text(next_action.get("source_surface")),
        "stage_index_ref": _text(next_action.get("stage_index_ref")),
        "current_stage_id": _text(next_action.get("current_stage_id")),
        "current_package_status": _text(next_action.get("current_package_status")),
        "owner_route": owner_route,
        "handoff_packet": {
            "owner": owner,
            "request_owner": owner,
            "recommended_owner": owner,
            "next_executable_owner": owner,
            "owner_route": owner_route,
            "source_surface": _text(next_action.get("source_surface")),
        },
    }


def _stage_native_owner_route(
    *,
    study_id: str,
    quest_id: str,
    action_type: str,
    owner: str,
    next_action: Mapping[str, Any],
) -> dict[str, Any]:
    current_stage_id = _text(next_action.get("current_stage_id")) or "unknown_stage"
    source_surface = _text(next_action.get("source_surface")) or "control/next_action.json"
    fingerprint = f"stage-native-next-action::{current_stage_id}::{action_type}::{source_surface}"
    epoch = f"stage-native-next-action::{study_id}::{current_stage_id}"
    return {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": quest_id,
        "truth_epoch": epoch,
        "runtime_health_epoch": epoch,
        "work_unit_fingerprint": fingerprint,
        "failure_signature": action_type,
        "trace_id": f"owner-route-trace::{study_id}::{action_type}",
        "route_epoch": epoch,
        "source_fingerprint": fingerprint,
        "current_owner": "mas_controller",
        "next_owner": owner,
        "owner_reason": action_type,
        "active_run_id": None,
        "allowed_actions": [action_type],
        "blocked_actions": sorted(item for item in SUPPORTED_ACTION_TYPES if item != action_type),
        "source_refs": {
            "work_unit_id": action_type,
            "work_unit_fingerprint": fingerprint,
            "source_surface": source_surface,
            "stage_index_ref": _text(next_action.get("stage_index_ref")),
            "current_stage_id": current_stage_id,
            "owner_route_currentness_basis": {
                "truth_epoch": epoch,
                "runtime_health_epoch": epoch,
                "work_unit_id": action_type,
                "work_unit_fingerprint": fingerprint,
            },
        },
        "idempotency_key": f"owner-route::{study_id}::{epoch}::{owner}::{action_type}",
    }


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _requires_manuscript_story_surface_delta(value: object) -> bool:
    text = str(value or "").strip().lower()
    return (
        "canonical manuscript story-surface delta" in text
        and "typed blocker:manuscript_story_surface_delta_missing" in text
    )


def _read_quest_id(*, study_root: Path, fallback: str) -> str:
    study_yaml = study_root / "study.yaml"
    try:
        text = study_yaml.read_text(encoding="utf-8")
    except OSError:
        return fallback
    for line in text.splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() == "quest_id":
            return value.strip().strip("\"'") or fallback
    return fallback


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
        return queue_actions, []
    ignored = [_ignored_action(action, "superseded_by_current_domain_transition") for action in queue_actions]
    if queue_source == "per_study_empty":
        ignored.extend(
            _ignored_action(action, "superseded_by_current_domain_transition")
            for action in top_level_study_actions
        )
    return transition_actions, ignored


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
        current_study = _study_with_owner_route_currentness(study, generated=generated)
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
    return bool(owner_route) and _action_allowed_by_owner_route(action, owner_route)


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


def _study_with_owner_route_currentness(
    study: Mapping[str, Any],
    *,
    generated: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = dict(study)
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(payload.get("owner_route")))
    if not owner_route or not _owner_route_currentness_applies_to_generated(
        owner_route=owner_route,
        generated=generated,
    ):
        return payload
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(_mapping(owner_route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    if "runtime_health_snapshot" not in payload and (runtime_epoch := _text(basis.get("runtime_health_epoch"))):
        payload["runtime_health_snapshot"] = {"runtime_health_epoch": runtime_epoch}
    if "study_truth_snapshot" not in payload:
        truth_epoch = _text(basis.get("truth_epoch")) or _text(owner_route.get("truth_epoch"))
        source_signature = _text(owner_route.get("source_fingerprint"))
        if truth_epoch or source_signature:
            payload["study_truth_snapshot"] = {
                key: value
                for key, value in {
                    "truth_epoch": truth_epoch,
                    "source_signature": source_signature,
                }.items()
                if value is not None
            }
    if "publication_eval" not in payload and (source_eval_id := _text(basis.get("source_eval_id"))):
        payload["publication_eval"] = {"eval_id": source_eval_id}
    return payload


def _owner_route_currentness_applies_to_generated(
    *,
    owner_route: Mapping[str, Any],
    generated: list[dict[str, Any]],
) -> bool:
    if any(_action_allowed_by_owner_route(action, owner_route) for action in generated):
        return True
    source_refs = _mapping(owner_route.get("source_refs"))
    basis = _mapping(_mapping(owner_route.get("currentness_contract")).get("basis")) or _mapping(
        source_refs.get("owner_route_currentness_basis")
    )
    route_work_unit_id = _text(basis.get("work_unit_id")) or _text(source_refs.get("work_unit_id"))
    route_work_unit_fingerprint = _text(basis.get("work_unit_fingerprint")) or _text(
        source_refs.get("work_unit_fingerprint")
    )
    if route_work_unit_id is None and route_work_unit_fingerprint is None:
        return False
    for action in generated:
        action_work_unit_id = (
            _text(action.get("controller_work_unit_id"))
            or _text(action.get("executable_work_unit"))
            or _work_unit_id(action.get("next_work_unit"))
        )
        action_work_unit_fingerprint = _text(action.get("work_unit_fingerprint"))
        if (
            route_work_unit_id is not None
            and route_work_unit_id == action_work_unit_id
            and (
                _action_allowed_by_owner_route(action, owner_route)
                or _ai_reviewer_record_production_work_unit(action_work_unit_id)
            )
        ):
            return True
        if (
            route_work_unit_fingerprint is not None
            and action_work_unit_fingerprint is not None
            and route_work_unit_fingerprint != action_work_unit_fingerprint
        ):
            continue
        if (
            route_work_unit_fingerprint is not None
            and action_work_unit_fingerprint is not None
            and route_work_unit_fingerprint == action_work_unit_fingerprint
        ):
            return True
    return False


def _ai_reviewer_record_production_work_unit(work_unit_id: str | None) -> bool:
    return work_unit_id in domain_transition_actions.AI_REVIEWER_RECORD_PRODUCTION_WORK_UNIT_IDS


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _request_owner_for_action_type(action_type)
    )


def _request_owner_for_action_type(action_type: str) -> str:
    from med_autoscience.controllers.default_executor_action_policy import request_owner_for_action_type

    return request_owner_for_action_type(action_type)


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _ignored_action(action: Mapping[str, Any], reason: str) -> dict[str, Any]:
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
