from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_owner_for_action_type,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    stage_native_next_action,
)
from med_autoscience.controllers.stage_route_currentness_identity import (
    currentness_identities_match,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
READINESS_BLOCKER_DERIVED_REPAIR_ACTION_TYPES = frozenset(
    {"run_quality_repair_batch", "run_gate_clearing_batch"}
)
STAGE_NATIVE_CURRENTNESS_BLOCKED_REASON = (
    "stage_native_workspace_next_action_requires_current_work_unit_currentness_match"
)


def route_allows_readiness_followup(owner_route: Mapping[str, Any]) -> bool:
    allowed_actions = {_text(item) for item in owner_route.get("allowed_actions") or []}
    allowed_actions.discard(None)
    return (
        _text(owner_route.get("next_owner")) == "MedAutoScience"
        and READINESS_ACTION_TYPE in allowed_actions
    )


def current_readiness_owner_action_matches(
    study: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    allowed_actions = {_text(item) for item in action.get("allowed_actions") or []}
    allowed_actions.discard(None)
    direct_readiness_action = _text(action.get("action_type")) == READINESS_ACTION_TYPE
    if not direct_readiness_action and READINESS_ACTION_TYPE not in allowed_actions:
        return False
    if _text(action.get("work_unit_id")) not in {READINESS_ACTION_TYPE, None}:
        return False
    if direct_readiness_action:
        return _readiness_action_matches_current_authority(study=study, action=action)
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
        if (
            READINESS_ACTION_TYPE not in current_allowed
            and _text(current.get("action_type")) != READINESS_ACTION_TYPE
        ):
            return False
    return _readiness_action_matches_current_authority(study=study, action=action)


def explicit_current_readiness_action(study: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(study.get("current_executable_owner_action"))
    if not current:
        return {}
    current_actions = {_text(item) for item in current.get("allowed_actions") or []}
    current_actions.discard(None)
    current_action_type = _text(current.get("action_type"))
    if (
        current_action_type not in {READINESS_ACTION_TYPE, None}
        and READINESS_ACTION_TYPE not in current_actions
    ):
        return {}
    current_work_unit = _text(current.get("work_unit_id")) or _work_unit_id(
        current.get("next_work_unit")
    )
    if current_work_unit not in {READINESS_ACTION_TYPE, None}:
        return {}
    return current


def stage_native_action_matches_current_study(
    *,
    study: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not _stage_native_action_has_authority_binding(action):
        return False
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    if (
        owner_route
        and owner_route_part.owner_route_matches(
            dispatch=action,
            current_route=owner_route,
        )
        and action_allowed_by_owner_route(action, owner_route)
    ):
        return True
    return any(
        currentness_identities_match(action, current, require_fingerprint=True)
        for current in _current_identity_payloads(study)
    )


def stage_native_action_derives_from_stable_readiness_answer(
    *,
    study: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not _stage_native_action_has_authority_binding(action):
        return False
    if _text(action.get("action_type")) not in READINESS_BLOCKER_DERIVED_REPAIR_ACTION_TYPES:
        return False
    return _study_has_stable_readiness_typed_blocker(study)


def stage_native_action_derives_from_readiness_barrier(
    *,
    fresh_action: Mapping[str, Any] | None,
    action: Mapping[str, Any],
) -> bool:
    if not _stage_native_action_has_authority_binding(action):
        return False
    if _text(action.get("action_type")) not in READINESS_BLOCKER_DERIVED_REPAIR_ACTION_TYPES:
        return False
    barrier = _mapping(fresh_action)
    if not (_text(barrier.get("action_type")) or "").startswith("current_execution_envelope_"):
        return False
    if _text(barrier.get("reason")) != "medical_paper_readiness_missing":
        return False
    stale_override = barrier.get("current_work_unit_stale_queue_or_handoff_can_override")
    if stale_override is True or _text(stale_override) == "true":
        return False
    if _text(barrier.get("current_work_unit_status")) != "typed_blocker" and _text(
        barrier.get("current_work_unit_state_kind")
    ) != "typed_blocker":
        return False
    if _text(barrier.get("current_work_unit_id")) not in {READINESS_ACTION_TYPE, None}:
        return False
    return _text(barrier.get("work_unit_id")) in {READINESS_ACTION_TYPE, None}


def stage_native_currentness_diagnostic(action: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **dict(action),
        "authority": stage_native_next_action.WORKSPACE_NEXT_ACTION_DIAGNOSTIC_AUTHORITY,
        "default_dispatch_allowed": False,
        "default_dispatch_blocked_reason": STAGE_NATIVE_CURRENTNESS_BLOCKED_REASON,
    }


def stage_native_action_supersedes_stable_readiness_answer(
    *,
    study: Mapping[str, Any],
    readiness_followup: Mapping[str, Any],
    stage_native_action: Mapping[str, Any] | None,
) -> bool:
    if not stage_native_action:
        return False
    if _text(stage_native_action.get("action_type")) == READINESS_ACTION_TYPE:
        return False
    return (
        _readiness_followup_is_stable_owner_answer(study=study, action=readiness_followup)
        or _study_has_stable_readiness_typed_blocker(study)
    )


def stage_native_superseded_reason(
    *,
    study: Mapping[str, Any],
    action: Mapping[str, Any],
    stage_native_action: Mapping[str, Any],
) -> str:
    if (
        _text(action.get("action_type")) == READINESS_ACTION_TYPE
        and stage_native_action_supersedes_stable_readiness_answer(
            study=study,
            readiness_followup=action,
            stage_native_action=stage_native_action,
        )
    ):
        return "superseded_by_stage_native_next_action_after_readiness_answer"
    return "superseded_by_stage_native_next_action"


def action_allowed_by_owner_route(
    action: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    action_type = _text(action.get("action_type")) or "unknown_action"
    return owner_route_part.route_allows_action(
        action={
            **dict(action),
            "next_executable_owner": _owner_from_action(action, action_type),
            "action_type": action_type,
        },
        owner_route=owner_route,
    )


def _readiness_action_matches_current_authority(
    *,
    study: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    current = explicit_current_readiness_action(study)
    if not current:
        return False
    owner_route = owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))
    action_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route"))
        or _mapping(_mapping(action.get("handoff_packet")).get("owner_route"))
    )
    if owner_route and route_allows_readiness_followup(owner_route):
        action_for_route = _readiness_action_for_route_check(action, current=current)
        if action_route:
            return (
                owner_route_part.owner_route_matches(
                    dispatch=action_for_route,
                    current_route=owner_route,
                )
                and action_allowed_by_owner_route(action_for_route, owner_route)
                and _readiness_action_matches_current_action(action, current=current)
            )
        if _readiness_action_matches_current_action(action, current=current):
            return action_allowed_by_owner_route(action_for_route, owner_route)
    if _readiness_action_matches_current_action(action, current=current):
        return currentness_identities_match(action, current, require_fingerprint=True)
    return False


def _readiness_action_matches_current_action(
    action: Mapping[str, Any],
    *,
    current: Mapping[str, Any],
) -> bool:
    action_type = _text(action.get("action_type"))
    action_allowed = {_text(item) for item in action.get("allowed_actions") or []}
    action_allowed.discard(None)
    if action_type not in {READINESS_ACTION_TYPE, None} and READINESS_ACTION_TYPE not in action_allowed:
        return False
    action_work_unit = _text(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    if action_work_unit not in {READINESS_ACTION_TYPE, None}:
        return False
    current_actions = {_text(item) for item in current.get("allowed_actions") or []}
    current_actions.discard(None)
    current_action_type = _text(current.get("action_type"))
    if (
        current_action_type not in {READINESS_ACTION_TYPE, None}
        and READINESS_ACTION_TYPE not in current_actions
    ):
        return False
    current_work_unit = _text(current.get("work_unit_id")) or _work_unit_id(
        current.get("next_work_unit")
    )
    return current_work_unit in {READINESS_ACTION_TYPE, None}


def _readiness_action_for_route_check(
    action: Mapping[str, Any],
    *,
    current: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **dict(current),
        **dict(action),
        "action_type": READINESS_ACTION_TYPE,
        "next_executable_owner": (
            _text(action.get("next_executable_owner"))
            or _text(action.get("owner"))
            or _text(action.get("request_owner"))
            or _text(action.get("recommended_owner"))
            or _text(current.get("next_owner"))
            or _text(current.get("owner"))
            or "MedAutoScience"
        ),
        "work_unit_id": READINESS_ACTION_TYPE,
    }


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


def _study_has_stable_readiness_typed_blocker(study: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping(study.get("current_work_unit"))
    work_unit_state = _mapping(current_work_unit.get("state"))
    stale_override = work_unit_state.get("stale_queue_or_handoff_can_override")
    if stale_override is True or _text(stale_override) == "true":
        return False
    if _text(current_work_unit.get("status")) == "typed_blocker" or _text(
        work_unit_state.get("state_kind")
    ) == "typed_blocker":
        blocker = (
            _mapping(work_unit_state.get("typed_blocker"))
            or _mapping(current_work_unit.get("typed_blocker"))
            or current_work_unit
        )
        if _readiness_typed_blocker(blocker):
            return True
    envelope = _mapping(study.get("current_execution_envelope"))
    if _text(envelope.get("state_kind")) != "typed_blocker":
        return False
    return _readiness_typed_blocker(_mapping(envelope.get("typed_blocker")) or envelope)


def _readiness_typed_blocker(blocker: Mapping[str, Any]) -> bool:
    reason = (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
    )
    if reason != "medical_paper_readiness_missing":
        return False
    work_unit_id = _text(blocker.get("work_unit_id"))
    return work_unit_id in {READINESS_ACTION_TYPE, None}


def _stage_native_action_has_authority_binding(action: Mapping[str, Any]) -> bool:
    admission = _mapping(action.get("stage_native_next_action_admission"))
    binding = _mapping(action.get("current_work_unit_binding"))
    return (
        _text(action.get("authority")) == stage_native_next_action.WORKSPACE_NEXT_ACTION_AUTHORITY
        and action.get("default_dispatch_allowed") is True
        and admission.get("default_dispatch_allowed") is True
        and _text(binding.get("source")) == "canonical_current_work_unit"
        and _text(binding.get("work_unit_id")) is not None
        and _text(binding.get("work_unit_fingerprint")) is not None
    )


def _current_identity_payloads(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    current_work_unit = _mapping(study.get("current_work_unit"))
    if _text(current_work_unit.get("status")) in {
        "executable_owner_action",
        "running_provider_attempt",
    }:
        payloads.append(current_work_unit)
    for value in (study.get("current_executable_owner_action"), study.get("owner_route")):
        payload = _mapping(value)
        if payload:
            payloads.append(payload)
    envelope = _mapping(study.get("current_execution_envelope"))
    if _text(envelope.get("state_kind")) == "executable_owner_action":
        payloads.append(
            {
                "action_type": _text(envelope.get("action_type")),
                "work_unit_id": _work_unit_id(envelope.get("next_work_unit")),
                "work_unit_fingerprint": _text(envelope.get("work_unit_fingerprint"))
                or _text(envelope.get("action_fingerprint")),
                "source_eval_id": _text(envelope.get("source_eval_id")),
            }
        )
    return payloads


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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "READINESS_ACTION_TYPE",
    "STAGE_NATIVE_CURRENTNESS_BLOCKED_REASON",
    "action_allowed_by_owner_route",
    "current_readiness_owner_action_matches",
    "explicit_current_readiness_action",
    "route_allows_readiness_followup",
    "stage_native_action_derives_from_readiness_barrier",
    "stage_native_action_derives_from_stable_readiness_answer",
    "stage_native_action_matches_current_study",
    "stage_native_action_supersedes_stable_readiness_answer",
    "stage_native_currentness_diagnostic",
    "stage_native_superseded_reason",
]
