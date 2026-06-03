from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
    typed_blocker as opl_execution_authorization_typed_blocker,
)


def block_if_missing_authorization(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
    current_study: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _authorized(
        dispatch=dispatch,
        owner_route_basis=owner_route_basis,
        current_study=current_study,
    ):
        return None
    return {
        "execution_status": "blocked",
        "blocked_reason": "opl_execution_authorization_required",
        "typed_blocker": opl_execution_authorization_typed_blocker(),
        "owner_callable_surface": None,
        "mas_private_attempt_loop_forbidden": True,
        "provider_attempt_or_lease_required": True,
    }


def _authorized(
    *,
    dispatch: Mapping[str, Any],
    owner_route_basis: str | None,
    current_study: Mapping[str, Any],
) -> bool:
    if owner_route_basis == "live_provider_attempt_dispatch":
        live_attempt = _mapping(current_study.get("opl_provider_attempt")) or current_study
        return first_trusted_opl_execution_authorization(live_attempt) is not None
    return first_trusted_opl_execution_authorization(
        dispatch.get("opl_execution_authorization"),
        dispatch.get("opl_provider_attempt"),
        dispatch.get("stage_attempt"),
        _mapping(dispatch.get("prompt_contract")).get("opl_execution_authorization"),
        _mapping(dispatch.get("prompt_contract")).get("opl_provider_attempt"),
        _mapping(dispatch.get("owner_route")).get("opl_execution_authorization"),
        _mapping(dispatch.get("owner_route")).get("opl_provider_attempt"),
    ) is not None


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}
