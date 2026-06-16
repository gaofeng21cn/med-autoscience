from __future__ import annotations

from collections.abc import Mapping
from typing import Any

OPL_TRANSITION_RUNTIME_OWNER = "one-person-lab"
OPL_TRANSITION_RUNTIME_KIND = "DomainProgressTransitionRuntime"


def valid_opl_transition_readback(value: Mapping[str, Any]) -> bool:
    result = _mapping(value)
    if not result:
        return False
    if _text(result.get("runtime_owner")) != OPL_TRANSITION_RUNTIME_OWNER:
        return False
    runtime_kind = _text(result.get("runtime_kind")) or _text(result.get("target_runtime_kind"))
    if runtime_kind != OPL_TRANSITION_RUNTIME_KIND:
        return False
    if _text(result.get("outcome_kind")) != "provider_admission_pending":
        return False
    return any(
        _text(result.get(key)) is not None
        for key in ("event_id", "outbox_item_id", "stage_run_id", "stage_run_identity_ref")
    ) or bool(_mapping(result.get("stage_run_identity")))


def candidate_opl_transition_readback(candidate: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        candidate.get("opl_domain_progress_transition_result"),
        candidate.get("opl_domain_progress_runtime_result"),
        candidate.get("opl_runtime_result"),
        _mapping(candidate.get("paper_progress_policy_result")).get("opl_runtime_result"),
        _mapping(candidate.get("state")).get("opl_domain_progress_transition_result"),
        _mapping(candidate.get("state")).get("opl_runtime_result"),
    ):
        result = _mapping(value)
        if valid_opl_transition_readback(result):
            return dict(result)
    return {}


def has_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(candidate_opl_transition_readback(candidate))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "OPL_TRANSITION_RUNTIME_KIND",
    "OPL_TRANSITION_RUNTIME_OWNER",
    "candidate_opl_transition_readback",
    "has_opl_transition_readback",
    "valid_opl_transition_readback",
]
