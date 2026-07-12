from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
)
from med_autoscience.controllers.opl_stage_attempt_readback import (
    candidate_opl_stage_attempt_readback,
)


def trusted_owner_callable_opl_proof(*payloads: object) -> dict[str, Any] | None:
    for payload in _iter_payloads(*payloads):
        nested_authorization = payload.get("opl_execution_authorization")
        if isinstance(nested_authorization, Mapping) and (
            nested_authorization.get("provider_attempt_ref")
            or nested_authorization.get("execution_authorization_decision_ref")
        ):
            return {
                "proof_kind": "trusted_opl_execution_authorization",
                "trusted_opl_execution_authorization": dict(nested_authorization),
                "semantic_route_authority": False,
            }
        authorization = first_trusted_opl_execution_authorization(payload)
        if authorization is not None:
            return {
                "proof_kind": "trusted_opl_execution_authorization",
                "trusted_opl_execution_authorization": authorization,
                "semantic_route_authority": False,
            }
        readback = candidate_opl_stage_attempt_readback(payload)
        if readback:
            return {
                "proof_kind": "opl_stage_attempt_transport_readback",
                "opl_stage_attempt_readback": readback,
                "semantic_route_authority": False,
            }
    return None


def bound_opl_stage_attempt_readback(
    payload: Mapping[str, Any],
    *context_payloads: object,
) -> dict[str, Any]:
    for candidate in (payload, *_iter_payloads(*context_payloads)):
        readback = candidate_opl_stage_attempt_readback(candidate)
        if readback:
            return readback
    return {}


def has_bound_opl_stage_attempt_readback(
    payload: Mapping[str, Any],
    *context_payloads: object,
) -> bool:
    return bool(bound_opl_stage_attempt_readback(payload, *context_payloads))


def _iter_payloads(*payloads: object) -> list[Mapping[str, Any]]:
    return [payload for payload in payloads if isinstance(payload, Mapping)]


__all__ = [
    "bound_opl_stage_attempt_readback",
    "has_bound_opl_stage_attempt_readback",
    "trusted_owner_callable_opl_proof",
]
