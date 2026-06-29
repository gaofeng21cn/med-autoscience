from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    REASON_ONLY_TYPED_BLOCKERS,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import mapping, text
from med_autoscience.controllers.current_work_unit_parts.running_provider_attempt import (
    running_work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.work_unit_fields import route_work_unit_id
from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    currentness_basis as owner_route_currentness_basis,
    normalize_currentness_sources,
    owner_reason_contract,
)


def typed_blocker(
    typed_blocker: Mapping[str, Any] | None,
    *,
    blocked_reason: str | None,
    owner: str | None,
) -> dict[str, Any] | None:
    if isinstance(typed_blocker, Mapping) and typed_blocker:
        return dict(typed_blocker)
    reason = text(blocked_reason)
    if reason is None:
        return None
    if not reason_only_blocked_reason_is_typed_blocker(reason=reason, owner=owner):
        return None
    return minimal_blocker(reason, owner=owner)


def minimal_blocker(blocker_type: str, *, owner: str | None) -> dict[str, Any]:
    return {
        "blocker_type": blocker_type,
        "owner": text(owner) or "med-autoscience",
    }


def reason_only_blocked_reason_is_typed_blocker(*, reason: str, owner: str | None) -> bool:
    if reason in REASON_ONLY_TYPED_BLOCKERS:
        return True
    contract = owner_reason_contract(reason=reason, owner=owner)
    if contract.get("registered") is not True:
        return True
    return not any(text(action) is not None for action in contract.get("allowed_actions") or [])


def currentness_basis(
    *,
    owner_route: Mapping[str, Any],
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
    runtime_health: Mapping[str, Any],
    running_attempt: Mapping[str, Any] | None,
) -> dict[str, Any]:
    basis = mapping(owner_route_currentness_basis(owner_route)) if owner_route else {}
    action_payload = mapping(action)
    action_source_refs = mapping(action_payload.get("source_refs"))
    embedded = (
        mapping(action_payload.get("owner_route_currentness_basis"))
        or mapping(action_payload.get("currentness_basis"))
        or mapping(action_source_refs.get("owner_route_currentness_basis"))
    )
    publication_eval = mapping(progress.get("publication_eval"))
    running = mapping(running_attempt)
    fingerprint_basis = normalize_currentness_sources(basis, embedded)
    return normalize_currentness_sources(
        basis,
        embedded,
        {
            "source_eval_id": (
                text(action_payload.get("source_eval_id"))
                or text(action_source_refs.get("source_eval_id"))
                or text(publication_eval.get("eval_id"))
            ),
            "work_unit_id": work_unit_id(action_payload.get("work_unit_id"))
            or work_unit_id(action_payload.get("next_work_unit"))
            or route_work_unit_id(owner_route)
            or running_work_unit_id(running),
            "work_unit_fingerprint": work_unit_fingerprint(
                action_payload,
                currentness_basis=fingerprint_basis,
            )
            or text(running.get("work_unit_fingerprint")),
            "truth_epoch": text(action_payload.get("truth_epoch")) or text(progress.get("truth_epoch")),
            "runtime_health_epoch": text(runtime_health.get("runtime_health_epoch"))
            or text(action_payload.get("runtime_health_epoch")),
        },
    )


__all__ = [
    "currentness_basis",
    "minimal_blocker",
    "typed_blocker",
]
