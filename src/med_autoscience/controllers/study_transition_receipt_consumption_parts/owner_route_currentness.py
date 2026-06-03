from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def execution_matches_owner_route(
    *,
    execution: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    prompt_contract = mapping(execution.get("prompt_contract"))
    for execution_route in (
        mapping(execution.get("current_owner_route")),
        mapping(execution.get("owner_route")),
        mapping(prompt_contract.get("owner_route")),
    ):
        if owner_route_currentness_matches(execution_route=execution_route, owner_route=owner_route):
            return True
    return False


def owner_route_currentness_matches(
    *,
    execution_route: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    if not execution_route:
        return False
    for key in ("route_epoch", "next_owner"):
        current_value = text(owner_route.get(key))
        execution_value = text(execution_route.get(key))
        if key == "route_epoch" and current_value and not execution_value:
            if _route_epoch_missing_allowed(execution_route=execution_route, owner_route=owner_route):
                continue
        if current_value and execution_value and current_value != execution_value:
            return False
        if current_value and not execution_value:
            return False
    if not owner_route_work_unit_currentness_matches(execution_route=execution_route, owner_route=owner_route):
        return False
    current_allowed = {text(item) for item in owner_route.get("allowed_actions") or []}
    execution_allowed = {text(item) for item in execution_route.get("allowed_actions") or []}
    current_allowed.discard("")
    execution_allowed.discard("")
    return bool(current_allowed) and current_allowed == execution_allowed


def owner_route_work_unit_currentness_matches(
    *,
    execution_route: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    current_basis = owner_route_currentness_basis(owner_route)
    execution_basis = owner_route_currentness_basis(execution_route)
    for key in ("truth_epoch", "work_unit_fingerprint", "work_unit_id"):
        current_value = text(current_basis.get(key))
        execution_value = text(execution_basis.get(key))
        if key == "truth_epoch" and current_value and not execution_value:
            if _truth_epoch_missing_allowed(current_basis=current_basis, execution_basis=execution_basis):
                continue
        if current_value and not execution_value:
            return False
        if current_value and execution_value and current_value != execution_value:
            return False
    current_source_eval_id = text(current_basis.get("source_eval_id"))
    execution_source_eval_id = text(execution_basis.get("source_eval_id"))
    if current_source_eval_id and execution_source_eval_id and current_source_eval_id != execution_source_eval_id:
        return False
    if (
        current_source_eval_id
        and not execution_source_eval_id
        and not all(
            text(current_basis.get(key)) == text(execution_basis.get(key)) and text(current_basis.get(key))
            for key in ("truth_epoch", "runtime_health_epoch", "work_unit_fingerprint", "work_unit_id")
        )
    ):
        return False
    return bool(text(current_basis.get("work_unit_fingerprint")) or text(current_basis.get("work_unit_id")))


def _truth_epoch_missing_allowed(
    *,
    current_basis: Mapping[str, Any],
    execution_basis: Mapping[str, Any],
) -> bool:
    if not all(
        text(current_basis.get(key)) and text(current_basis.get(key)) == text(execution_basis.get(key))
        for key in ("work_unit_fingerprint", "work_unit_id")
    ):
        return False
    current_source_eval_id = text(current_basis.get("source_eval_id"))
    execution_source_eval_id = text(execution_basis.get("source_eval_id"))
    return not (current_source_eval_id and execution_source_eval_id and current_source_eval_id != execution_source_eval_id)


def _route_epoch_missing_allowed(*, execution_route: Mapping[str, Any], owner_route: Mapping[str, Any]) -> bool:
    current_basis = owner_route_currentness_basis(owner_route)
    execution_basis = owner_route_currentness_basis(execution_route)
    if not all(
        text(current_basis.get(key)) and text(current_basis.get(key)) == text(execution_basis.get(key))
        for key in ("work_unit_fingerprint", "work_unit_id")
    ):
        return False
    current_source_eval_id = text(current_basis.get("source_eval_id"))
    execution_source_eval_id = text(execution_basis.get("source_eval_id"))
    return not (current_source_eval_id and execution_source_eval_id and current_source_eval_id != execution_source_eval_id)


def owner_route_currentness_basis(route: Mapping[str, Any]) -> dict[str, Any]:
    source_refs = mapping(route.get("source_refs"))
    nested_basis = mapping(source_refs.get("owner_route_currentness_basis"))
    return {
        "truth_epoch": (
            text(nested_basis.get("truth_epoch"))
            or text(source_refs.get("study_truth_epoch"))
            or text(route.get("truth_epoch"))
            or text(route.get("route_epoch"))
        ),
        "runtime_health_epoch": (
            text(nested_basis.get("runtime_health_epoch"))
            or text(source_refs.get("runtime_health_epoch"))
            or text(route.get("runtime_health_epoch"))
        ),
        "work_unit_fingerprint": (
            text(nested_basis.get("work_unit_fingerprint"))
            or text(source_refs.get("work_unit_fingerprint"))
            or text(route.get("work_unit_fingerprint"))
        ),
        "work_unit_id": text(nested_basis.get("work_unit_id")) or text(source_refs.get("work_unit_id")),
        "source_eval_id": (
            text(nested_basis.get("source_eval_id"))
            or text(source_refs.get("source_eval_id"))
            or text(route.get("source_eval_id"))
        ),
    }


def source_eval_id(route: Mapping[str, Any]) -> str:
    source_refs = mapping(route.get("source_refs"))
    nested_basis = mapping(source_refs.get("owner_route_currentness_basis"))
    return text(nested_basis.get("source_eval_id")) or text(source_refs.get("source_eval_id")) or text(
        route.get("source_eval_id")
    )


def same_non_empty_text(left: str, right: str) -> bool:
    return bool(left and right and left == right)


def mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "execution_matches_owner_route",
    "owner_route_currentness_basis",
    "owner_route_currentness_matches",
    "owner_route_work_unit_currentness_matches",
    "same_non_empty_text",
    "source_eval_id",
]
