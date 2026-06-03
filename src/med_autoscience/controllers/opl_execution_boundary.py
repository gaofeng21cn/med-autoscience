from __future__ import annotations

from collections.abc import Mapping
from typing import Any


OPL_EXECUTION_AUTHORIZATION_BLOCKER = "opl_execution_authorization_required"
OPL_EXECUTION_AUTHORIZATION_OWNER = "one-person-lab"
OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT = "OPL provider attempt, lease, or closeout receipt binding"

_OPL_OWNER_VALUES = frozenset({"one-person-lab", "opl", "OPL"})
_OPL_DEFAULT_EXECUTORS = frozenset({"codex_cli", "codex_cli_default"})
_OPL_EXECUTION_REF_KEYS = (
    "provider_attempt_id",
    "attempt_id",
    "stage_attempt_id",
    "active_stage_attempt_id",
    "workflow_id",
    "active_workflow_id",
    "lease_id",
    "lease_ref",
    "attempt_lease_ref",
    "receipt_ref",
    "attempt_receipt_ref",
    "typed_closeout_ref",
    "typed_closeout_receipt_ref",
)


def first_trusted_opl_execution_authorization(*candidates: object) -> dict[str, Any] | None:
    for candidate in candidates:
        trusted = trusted_opl_execution_authorization(_mapping(candidate))
        if trusted is not None:
            return trusted
    return None


def trusted_opl_execution_authorization(candidate: Mapping[str, Any] | None) -> dict[str, Any] | None:
    payload = _mapping(candidate)
    if not payload:
        return None
    owner = (
        _text(payload.get("owner"))
        or _text(payload.get("runtime_owner"))
        or _text(payload.get("provider_attempt_owner"))
        or _text(payload.get("queue_owner"))
    )
    if owner not in _OPL_OWNER_VALUES:
        return None
    executor_kind = _text(payload.get("executor_kind")) or _text(payload.get("selected_executor"))
    if executor_kind is not None and executor_kind not in _OPL_DEFAULT_EXECUTORS:
        return None
    if not any(_text(payload.get(key)) is not None for key in _OPL_EXECUTION_REF_KEYS):
        return None
    return dict(payload)


def typed_blocker() -> dict[str, Any]:
    return {
        "blocker_id": OPL_EXECUTION_AUTHORIZATION_BLOCKER,
        "owner": OPL_EXECUTION_AUTHORIZATION_OWNER,
        "write_permitted": False,
        "required_input": OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    return value.strip() if isinstance(value, str) and value.strip() else None
