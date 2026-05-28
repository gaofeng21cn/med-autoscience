from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.runtime_control import owner_route as owner_route_part


BRIDGE_AUTHORITY = "domain_action_request_materializer_publication_owner_bridge"
SOURCE_ACTION_TYPES = frozenset({"run_quality_repair_batch", "return_to_ai_reviewer_workflow"})
MATERIALIZED_OWNER_REASONS = frozenset(
    {
        "current_package_freshness_required",
        "publication_owner_materialization_required",
    }
)
MATERIALIZED_WORK_UNIT_IDS = frozenset({"current_package_freshness_required", "publication_gate_replay"})


def bridged_publication_owner_materialization_route_from_scan_payload(
    *,
    scan_payload: Mapping[str, Any] | None,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    current_study = _scan_study(scan_payload, study_id)
    for current_route in _scan_owner_route_candidates(current_study):
        if _bridged_publication_owner_materialization_route(dispatch=dispatch, current_route=current_route):
            return _dispatch_owner_route(dispatch)
    return None


def bridged_publication_owner_materialization_route_from_study(
    *,
    current_study: Mapping[str, Any],
    dispatch: Mapping[str, Any],
) -> dict[str, Any] | None:
    for current_route in _scan_owner_route_candidates(current_study):
        if _bridged_publication_owner_materialization_route(dispatch=dispatch, current_route=current_route):
            return _dispatch_owner_route(dispatch)
    return None


def _bridged_publication_owner_materialization_route(
    *,
    dispatch: Mapping[str, Any],
    current_route: Mapping[str, Any],
) -> bool:
    dispatch_route = _dispatch_owner_route(dispatch)
    normalized_current = owner_route_part.ensure_owner_route_v2(_mapping(current_route))
    return (
        _publication_owner_dispatch_shape(dispatch)
        and _publication_owner_route_shape(dispatch_route)
        and _bridge_refs_match_current(dispatch_route=dispatch_route, current_route=normalized_current)
        and _currentness_refs_match(dispatch_route=dispatch_route, current_route=normalized_current)
        and _current_route_allows_materialized_source_action(
            dispatch_route=dispatch_route,
            current_route=normalized_current,
        )
        and owner_route_part.route_allows_action(action=dispatch, owner_route=dispatch_route)
    )


def _publication_owner_dispatch_shape(dispatch: Mapping[str, Any]) -> bool:
    return (
        _text(dispatch.get("action_type")) == "run_gate_clearing_batch"
        and _text(dispatch.get("next_executable_owner")) == "gate_clearing_batch"
    )


def _publication_owner_route_shape(route: Mapping[str, Any]) -> bool:
    return (
        bool(route)
        and _text(route.get("next_owner")) == "gate_clearing_batch"
        and _route_reason(route) in MATERIALIZED_OWNER_REASONS
    )


def _bridge_refs_match_current(
    *,
    dispatch_route: Mapping[str, Any],
    current_route: Mapping[str, Any],
) -> bool:
    dispatch_refs = _mapping(dispatch_route.get("source_refs"))
    return (
        _text(dispatch_refs.get("bridge_authority")) == BRIDGE_AUTHORITY
        and _text(dispatch_refs.get("bridged_from_owner_reason")) == _route_reason(current_route)
        and _text(dispatch_refs.get("bridged_from_idempotency_key")) == _text(current_route.get("idempotency_key"))
        and _text(dispatch_refs.get("materialized_from_action_type")) in SOURCE_ACTION_TYPES
        and _text(dispatch_refs.get("materialized_work_unit_id")) in MATERIALIZED_WORK_UNIT_IDS
    )


def _currentness_refs_match(
    *,
    dispatch_route: Mapping[str, Any],
    current_route: Mapping[str, Any],
) -> bool:
    for key in (
        "study_id",
        "quest_id",
        "truth_epoch",
        "runtime_health_epoch",
        "work_unit_fingerprint",
        "source_fingerprint",
    ):
        if not _same_required_currentness_value(dispatch_route, current_route, key):
            return False
    dispatch_refs = _mapping(dispatch_route.get("source_refs"))
    current_refs = _mapping(current_route.get("source_refs"))
    return _same_required_currentness_value(
        dispatch_refs,
        current_refs,
        "work_unit_id",
    ) and _optional_currentness_value_matches(dispatch_refs, current_refs, "source_eval_id")


def _current_route_allows_materialized_source_action(
    *,
    dispatch_route: Mapping[str, Any],
    current_route: Mapping[str, Any],
) -> bool:
    dispatch_refs = _mapping(dispatch_route.get("source_refs"))
    source_action_type = _text(dispatch_refs.get("materialized_from_action_type"))
    if source_action_type is None:
        return False
    return owner_route_part.route_allows_action(
        action={
            "action_type": source_action_type,
            "next_executable_owner": _text(current_route.get("next_owner")),
        },
        owner_route=current_route,
    )


def _scan_owner_route_candidates(current_study: Mapping[str, Any]) -> list[dict[str, Any]]:
    candidates: list[dict[str, Any]] = []
    route = owner_route_part.ensure_owner_route_v2(_mapping(current_study.get("owner_route")))
    if route:
        candidates.append(route)
    for action in current_study.get("action_queue") or []:
        route = owner_route_part.ensure_owner_route_v2(_mapping(_mapping(action).get("owner_route")))
        if route:
            candidates.append(route)
    return _dedupe_routes(candidates)


def _dedupe_routes(routes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    unique: list[dict[str, Any]] = []
    seen: set[tuple[str | None, str | None]] = set()
    for route in routes:
        key = (_text(route.get("idempotency_key")), _text(route.get("source_fingerprint")))
        if key in seen:
            continue
        seen.add(key)
        unique.append(route)
    return unique


def _scan_study(scan_payload: Mapping[str, Any] | None, study_id: str) -> dict[str, Any]:
    latest = _mapping(scan_payload)
    for study in latest.get("studies") or []:
        payload = _mapping(study)
        if _text(payload.get("study_id")) == study_id:
            return payload
    return {}


def _dispatch_owner_route(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    return owner_route_part.ensure_owner_route_v2(
        _mapping(dispatch.get("owner_route")) or _mapping(_mapping(dispatch.get("prompt_contract")).get("owner_route"))
    )


def _route_reason(route: Mapping[str, Any]) -> str | None:
    return _text(route.get("owner_reason")) or _text(route.get("failure_signature"))


def _same_required_currentness_value(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    key: str,
) -> bool:
    left_value = _text(left.get(key))
    right_value = _text(right.get(key))
    return left_value is not None and right_value is not None and left_value == right_value


def _optional_currentness_value_matches(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
    key: str,
) -> bool:
    left_value = _text(left.get(key))
    right_value = _text(right.get(key))
    if left_value is None and right_value is None:
        return True
    return left_value is not None and right_value is not None and left_value == right_value


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
