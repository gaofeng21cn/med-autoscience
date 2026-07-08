from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    OPL_EXECUTION_AUTHORIZATION_OWNER,
    OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT,
)


def typed_blocker_phase(typed_blocker: Mapping[str, Any]) -> str:
    if _text(typed_blocker.get("requires_human_gate")) == "true":
        return "human_gate"
    if _text(typed_blocker.get("owner")) in {"user", "human", "PI"}:
        return "human_gate"
    return "domain_blocked"


def typed_blocker_recovery_owner(
    typed_blocker: Mapping[str, Any],
    *,
    current_work_unit: Mapping[str, Any] | None = None,
    obligation: Mapping[str, Any] | None = None,
    blocker_reason: str | None = None,
) -> str:
    if blocker_reason == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return OPL_EXECUTION_AUTHORIZATION_OWNER
    return (
        _text(typed_blocker.get("owner"))
        or _text(_mapping(current_work_unit).get("owner"))
        or _text(_mapping(obligation).get("owner"))
        or "MedAutoScience"
    )


def typed_blocker_next_action(
    typed_blocker: Mapping[str, Any],
    *,
    blocker_reason: str | None,
    owner: str,
) -> dict[str, Any]:
    if blocker_reason == OPL_EXECUTION_AUTHORIZATION_BLOCKER:
        return _clean_payload(
            {
                "kind": "provide_opl_execution_authorization_or_human_gate",
                "owner": owner,
                "provider_admission_allowed": False,
                "required_input": _text(typed_blocker.get("required_input"))
                or OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT,
            }
        )
    return _clean_payload(
        {
            "kind": "resolve_typed_blocker",
            "owner": owner,
            "provider_admission_allowed": False,
        }
    )


def _clean_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        value = str(value)
    text = value.strip()
    return text or None
