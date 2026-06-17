from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    SUPPORTED_ACTION_TYPES,
)
from med_autoscience.controllers.owner_route_reconcile_parts import (
    action_decorators,
    domain_route_contract,
    domain_transition_actions,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    current_action_authority,
    owner_route_currentness_projection,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


def current_actions(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    study_id = _text(study.get("study_id"))
    if study_id is None:
        return []
    generated = domain_transition_actions.actions(study)
    if not generated:
        return []
    quest_id = _text(study.get("quest_id"))
    owner_route = owner_route_for_generated(
        study=study,
        generated=generated,
        study_id=study_id,
        quest_id=quest_id,
    )
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
        if current_action_authority.action_allowed_by_owner_route(routed, owner_route):
            decorated_actions.append(routed)
    return decorated_actions


def consumed_current_actions(study: Mapping[str, Any]) -> list[dict[str, Any]]:
    transition = _mapping(study.get("domain_transition"))
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return []
    if _text(transition.get("controller_action")) is None:
        return []
    if not _mapping(transition.get("next_work_unit")):
        return []
    return current_actions(study)


def owner_route_for_study(study: Mapping[str, Any]) -> dict[str, Any]:
    study_payload = _mapping(study)
    study_id = _text(study_payload.get("study_id"))
    if study_id is None:
        return {}
    generated = domain_transition_actions.actions(study_payload)
    if not generated:
        return {}
    return owner_route_for_generated(
        study=study_payload,
        generated=generated,
        study_id=study_id,
        quest_id=_text(study_payload.get("quest_id")),
    )


def owner_route_for_generated(
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
            action_allowed_by_owner_route=current_action_authority.action_allowed_by_owner_route,
        )
        route = owner_route_part.build_owner_route(
            study_id=study_id,
            quest_id=quest_id,
            status=current_study,
            progress={},
            actions=generated,
            blocked_reason=_text(generated[0].get("reason")),
            next_owner=_text(generated[0].get("owner")) or _text(generated[0].get("request_owner")),
            active_run_id=_text(current_study.get("active_run_id")),
        )
        return _with_transition_source_eval_id(route, transition=transition)
    return owner_route_part.ensure_owner_route_v2(_mapping(study.get("owner_route")))


def _with_transition_source_eval_id(
    route: Mapping[str, Any],
    *,
    transition: Mapping[str, Any],
) -> dict[str, Any]:
    source_eval_id = (
        _text(_mapping(transition.get("completion_receipt_consumption")).get("eval_id"))
        or _text(transition.get("source_eval_id"))
        or _text(transition.get("publication_eval_id"))
        or _text(_mapping(transition.get("publication_eval_ref")).get("eval_id"))
    )
    payload = dict(route)
    if source_eval_id is None:
        return payload
    source_refs = dict(_mapping(payload.get("source_refs")))
    source_refs["source_eval_id"] = source_eval_id
    basis = dict(_mapping(source_refs.get("owner_route_currentness_basis")))
    basis["source_eval_id"] = source_eval_id
    source_refs["owner_route_currentness_basis"] = basis
    payload["source_refs"] = source_refs
    currentness_contract = dict(_mapping(payload.get("currentness_contract")))
    contract_basis = dict(_mapping(currentness_contract.get("basis")))
    contract_basis["source_eval_id"] = source_eval_id
    currentness_contract["basis"] = contract_basis
    payload["currentness_contract"] = currentness_contract
    return payload


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["consumed_current_actions", "current_actions", "owner_route_for_study"]
