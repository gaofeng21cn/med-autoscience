from __future__ import annotations

from collections.abc import Mapping
from typing import Any


_READBACK_KEYS = (
    "opl_stage_attempt_readback",
    "stage_attempt_readback",
    "provider_attempt_readback",
    "opl_execution_authorization",
    "opl_runtime_result",
    "opl_stage_attempt_readback",
)


def candidate_opl_stage_attempt_readback(candidate: Mapping[str, Any]) -> dict[str, Any]:
    for value in (candidate, *(_mapping(candidate.get(key)) for key in _READBACK_KEYS)):
        payload = _mapping(value)
        if _is_transport_readback(payload):
            return dict(payload)
    state = _mapping(candidate.get("state"))
    for key in _READBACK_KEYS:
        payload = _mapping(state.get(key))
        if _is_transport_readback(payload):
            return dict(payload)
    return {}


def has_opl_stage_attempt_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(candidate_opl_stage_attempt_readback(candidate))


def provider_admission_stage_attempt_readback(
    candidate: Mapping[str, Any],
    *,
    require_explicit_identity: bool = False,
) -> dict[str, Any]:
    readback = candidate_opl_stage_attempt_readback(candidate)
    if not readback:
        return {}
    if require_explicit_identity and not _has_identity(readback):
        return {}
    return readback


def _is_transport_readback(payload: Mapping[str, Any]) -> bool:
    surface = _text(payload.get("surface_kind"))
    status = _text(payload.get("status")) or _text(payload.get("runtime_readback_status"))
    return bool(
        surface
        and (
            "stage_attempt" in surface
            or "execution_authorization" in surface
            or "runtime_carrier_readback" in surface
        )
        and status not in {"failed", "permission_denied", "identity_mismatch"}
    ) or bool(
        payload.get("stage_attempt_ref")
        or payload.get("stage_run_ref")
        or payload.get("provider_attempt_ref")
        or payload.get("execution_authorization_decision_ref")
    )


def _has_identity(payload: Mapping[str, Any]) -> bool:
    identity = _mapping(payload.get("identity"))
    return bool(
        payload.get("stage_attempt_ref")
        or payload.get("stage_run_ref")
        or identity.get("stage_attempt_id")
        or identity.get("stage_run_id")
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None


__all__ = [
    "candidate_opl_stage_attempt_readback",
    "has_opl_stage_attempt_readback",
    "provider_admission_stage_attempt_readback",
]
