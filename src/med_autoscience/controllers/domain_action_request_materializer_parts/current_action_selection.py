from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers import carry_forward_risk
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    current_action_authority,
    current_action_queue,
    domain_transition_current_actions,
    current_typed_blocker_transition_barrier,
    fresh_progress_current_action,
    fresh_progress_arbitration,
    repair_progress_currentness,
    current_action_selection_predicates,
)
from med_autoscience.controllers.study_progress_parts import canonical_next_action_gate
from med_autoscience.runtime_control import owner_route as owner_route_part
from med_autoscience.controllers.domain_action_request_materializer_parts import legacy_next_action_authority
from med_autoscience.controllers.owner_callable_action_policy import (
    SUPPORTED_ACTION_TYPES as SUPPORTED_REQUEST_ACTION_TYPES,
)


READINESS_ACTION_TYPE = current_action_authority.READINESS_ACTION_TYPE
LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON = (
    legacy_next_action_authority.LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON
)
_attach_owner_route_if_missing = current_action_queue.attach_owner_route_if_missing
_attach_canonical_next_action_if_missing = current_action_queue.attach_canonical_next_action_if_missing
_ignored_action = current_action_queue.ignored_action
_top_level_study_actions = current_action_queue.top_level_study_actions
_unique_actions = current_action_queue.unique_actions
_fresh_progress_is_repair_progress_followup = (
    current_action_selection_predicates.fresh_progress_is_repair_progress_followup
)
_fresh_progress_is_accepted_owner_gate_decision = (
    current_action_selection_predicates.fresh_progress_is_accepted_owner_gate_decision
)
_fresh_progress_is_current_execution_envelope_barrier = (
    current_action_selection_predicates.fresh_progress_is_current_execution_envelope_barrier
)
_fresh_progress_is_hard_current_execution_envelope_barrier = (
    current_action_selection_predicates.fresh_progress_is_hard_current_execution_envelope_barrier
)
_fresh_progress_is_terminal_current_execution_envelope_barrier = (
    current_action_selection_predicates.fresh_progress_is_terminal_current_execution_envelope_barrier
)
_fresh_progress_materializes_publication_routeback = (
    current_action_selection_predicates.fresh_progress_materializes_publication_routeback
)


def current_actions_for_studies(
    *,
    profile: WorkspaceProfile | None = None,
    scan_payload: Mapping[str, Any],
    study_ids: tuple[str, ...],
) -> tuple[list[dict[str, Any]] | None, list[dict[str, Any]]]:
    ignored: list[dict[str, Any]] = []
    if not study_ids:
        actions = scan_payload.get("action_queue")
        if isinstance(actions, list):
            return _retire_legacy_next_action_authority(actions, ignored)
        return None, ignored
    per_study_actions: list[dict[str, Any]] = []
    requested = set(study_ids)
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
        raw_per_study_action_queue_present = "action_queue" in study_payload and any(
            isinstance(item, Mapping) for item in study_payload.get("action_queue") or []
        )
        has_next_action_envelope = canonical_next_action_gate.has_canonical_next_action(study_payload)
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
        selectable_current_route_queue_actions, retired_current_route_queue_actions = (
            _selectable_candidate_actions(current_route_queue_actions)
        )
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
            _attach_canonical_next_action_if_missing(dict(item), study_payload)
            for item in study_payload.get("action_queue") or []
            if isinstance(item, Mapping)
        ]
        stale_candidate_actions = [
            *transition_actions,
            *top_level_study_actions,
            *per_study_queue_actions,
            *current_route_queue_actions,
        ]
        stale_candidate_actions = _unique_actions(stale_candidate_actions)
        canonical_next_action_available = (
            has_next_action_envelope
            or _action_has_canonical_next_action(fresh_progress_action)
            or any(_action_has_canonical_next_action(action) for action in stale_candidate_actions)
        )
        transition_barrier = None
        if (
            readiness_followup is None
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
                    *([readiness_followup] if readiness_followup is not None else []),
                    *top_level_study_actions,
                    *transition_actions,
                    *current_route_queue_actions,
                    *per_study_queue_actions,
                ]
                if action != fresh_progress_action
            )
            continue
        if _fresh_progress_is_hard_current_execution_envelope_barrier(fresh_progress_action):
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_work_unit_typed_blocker")
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *top_level_study_actions,
                    *transition_actions,
                    *current_route_queue_actions,
                    *per_study_queue_actions,
                ]
                if action != fresh_progress_action
            )
            continue
        if _fresh_progress_is_terminal_current_execution_envelope_barrier(fresh_progress_action):
            per_study_actions.append(fresh_progress_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_work_unit_owner_receipt")
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *top_level_study_actions,
                    *transition_actions,
                    *current_route_queue_actions,
                    *per_study_queue_actions,
                ]
                if action != fresh_progress_action
            )
            continue
        if transition_barrier is not None:
            per_study_actions.append(transition_barrier)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_work_unit_typed_blocker")
                for action in [
                    *stale_candidate_actions,
                    *([readiness_followup] if readiness_followup is not None else []),
                ]
                if action != transition_barrier
            )
            continue
        if not canonical_next_action_available:
            ignored.extend(
                _ignored_action(action, _noncanonical_action_ignored_reason(action))
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *stale_candidate_actions,
                ]
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
                stage_native_action=None,
                top_level_study_actions=top_level_study_actions,
            )
            and _text(fresh_progress_action.get("action_type")) != READINESS_ACTION_TYPE
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
                ]
            )
            continue
        if transition_actions:
            per_study_actions.extend(transition_actions)
            ignored.extend(
                _ignored_action(action, "superseded_by_current_consumed_domain_transition")
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
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
            and not _fresh_progress_materializes_publication_routeback(
                profile=profile,
                fresh_action=fresh_progress_action,
            )
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
            and not _fresh_progress_materializes_publication_routeback(
                profile=profile,
                fresh_action=fresh_progress_action,
            )
            and not fresh_progress_arbitration.can_preempt_scan(
                study=study_payload,
                fresh_action=fresh_progress_action,
                readiness_followup=readiness_followup,
                stage_native_action=None,
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
                if _fresh_progress_materializes_publication_routeback(
                    profile=profile,
                    fresh_action=fresh_progress_action,
                ):
                    per_study_actions.append(fresh_progress_action)
                    ignored.extend(
                        _ignored_action(action, "superseded_by_fresh_publication_routeback_typed_blocker")
                        for action in [
                            currentness_owner_action,
                            *([readiness_followup] if readiness_followup is not None else []),
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
            fresh_progress_superseded_reason = (
                "superseded_by_current_work_unit_typed_blocker"
                if _fresh_progress_is_current_execution_envelope_barrier(fresh_progress_action)
                else "superseded_by_fresh_study_progress_current_owner_ticket"
            )
            ignored.extend(
                _ignored_action(action, fresh_progress_superseded_reason)
                for action in [
                    *([readiness_followup] if readiness_followup is not None else []),
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
            )
            continue
        carry_forward_action = carry_forward_risk.carry_forward_successor_action(study_payload)
        if carry_forward_action is not None and has_next_action_envelope:
            per_study_actions.append(carry_forward_action)
            ignored.extend(
                _ignored_action(action, "superseded_by_progress_first_carry_forward_risk_successor")
                for action in [
                    *current_route_queue_actions,
                    *top_level_study_actions,
                    *[
                        dict(item)
                        for item in study_payload.get("action_queue") or []
                        if isinstance(item, Mapping)
                    ],
                ]
                if action != carry_forward_action
            )
            continue
        if current_route_queue_actions:
            if not selectable_current_route_queue_actions:
                if raw_per_study_action_queue_present and top_level_study_actions:
                    ignored.extend(retired_current_route_queue_actions)
                    per_study_actions.extend(top_level_study_actions)
                    continue
                ignored.extend(retired_current_route_queue_actions)
                continue
            per_study_actions.extend(selectable_current_route_queue_actions)
            selected_fingerprints = {
                _text(action.get("action_fingerprint"))
                or _text(action.get("work_unit_fingerprint"))
                or _text(action.get("action_id"))
                for action in selectable_current_route_queue_actions
            }
            ignored.extend(
                _ignored_action(
                    action,
                    _ignored_reason_for_superseded_action(
                        action,
                        selected_actions=selectable_current_route_queue_actions,
                        default="superseded_by_current_owner_route_action_queue",
                    ),
                )
                for action in [
                    *([fresh_progress_action] if fresh_progress_action is not None else []),
                    *([readiness_followup] if readiness_followup is not None else []),
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
        if raw_per_study_action_queue_present and not per_study_queue_actions and top_level_study_actions:
            per_study_actions.extend(top_level_study_actions)
            continue
        study_actions, study_ignored = _current_study_actions(
            study=study_payload,
            top_level_actions=top_level_actions,
        )
        study_actions, retired_actions = _selectable_candidate_actions(study_actions)
        per_study_actions.extend(study_actions)
        ignored.extend(study_ignored)
        ignored.extend(retired_actions)
    for study_id, action in fresh_progress_by_study.items():
        if study_id in suppressed_fresh_progress_studies:
            continue
        if (
            _fresh_progress_is_current_execution_envelope_barrier(action)
            and not _fresh_progress_is_hard_current_execution_envelope_barrier(action)
        ):
            ignored.append(_ignored_action(action, "unsupported_action_type"))
            continue
        if not any(_text(item.get("study_id")) == study_id for item in per_study_actions):
            per_study_actions.append(action)
    if per_study_actions or matched_requested_study:
        return _retire_legacy_next_action_authority(per_study_actions, ignored)
    actions = scan_payload.get("action_queue")
    if isinstance(actions, list):
        return _retire_legacy_next_action_authority(actions, ignored)
    return None, _unique_ignored_actions(ignored)


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
        return _attach_canonical_next_action_if_missing(
            _attach_owner_route_if_missing(payload, owner_route),
            study,
        )
    return None


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
    actions, _ = _selectable_candidate_actions(actions)
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
        "opl_stage_attempt_admission_required",
    }:
        return False
    return current_action_authority.action_allowed_by_owner_route(action, owner_route)


def _currentness_owner_action(
    *,
    study: Mapping[str, Any],
    top_level_actions: Iterable[Mapping[str, Any]],
) -> dict[str, Any] | None:
    actions, _ = _current_study_actions(study=study, top_level_actions=top_level_actions)
    actions, _ = _selectable_candidate_actions(actions)
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


def _unique_ignored_actions(actions: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None, str | None, str | None]] = set()
    for action in actions:
        payload = dict(action)
        identity = (
            _text(payload.get("study_id")),
            _text(payload.get("action_type")),
            _text(payload.get("action_id")),
            _text(payload.get("reason")),
        )
        if identity in seen:
            continue
        seen.add(identity)
        unique.append(payload)
    return unique


def _retire_legacy_next_action_authority(
    actions: Iterable[Mapping[str, Any]],
    ignored: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return legacy_next_action_authority.retire_incomplete_authority_actions(actions, ignored)


def _selectable_candidate_actions(
    actions: Iterable[Mapping[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    return _retire_legacy_next_action_authority(actions, [])


def _noncanonical_action_ignored_reason(action: Mapping[str, Any]) -> str:
    if _text(action.get("action_type")) not in SUPPORTED_REQUEST_ACTION_TYPES:
        return "unsupported_action_type"
    return LEGACY_NEXT_ACTION_AUTHORITY_RETIRED_REASON


def _action_has_canonical_next_action(action: Mapping[str, Any] | None) -> bool:
    if action is None:
        return False
    return canonical_next_action_gate.has_canonical_next_action(action)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["current_actions_for_studies", "domain_transition_owner_route_for_study"]
