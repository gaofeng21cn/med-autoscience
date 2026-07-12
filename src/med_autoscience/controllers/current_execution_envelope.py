from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


RETIRED_AUTHORITY_BOUNDARY = {
    "surface_kind": "legacy_current_execution_envelope_authority_boundary",
    "status": "retired",
    "authority": "retired_projection",
    "replacement_authority": "StageOutcome -> NextActionEnvelope -> OPL StageAttemptReceipt",
    "default_selector_policy": "fail_closed",
    "diagnostic_only": True,
    "can_select_next_action": False,
    "can_authorize_dispatch": False,
    "can_authorize_provider_admission": False,
    "can_start_provider_attempt": False,
    "provider_completion_is_domain_completion": False,
    "can_claim_paper_progress": False,
}


def build_current_execution_evidence(
    *,
    action_queue: Sequence[Mapping[str, Any]] | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    no_op: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None = None,
    extra: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    evidence = {
        "surface_kind": "legacy_current_execution_evidence",
        "diagnostic_only": True,
        "authority_boundary": dict(RETIRED_AUTHORITY_BOUNDARY),
        "action_queue": [dict(item) for item in action_queue or [] if isinstance(item, Mapping)],
        "runtime_health": dict(runtime_health) if isinstance(runtime_health, Mapping) else None,
        "no_op": _no_op_evidence(no_op),
    }
    for key, value in _mapping(extra).items():
        if key not in evidence:
            evidence[key] = value
    return evidence


def retired_authority_boundary() -> dict[str, Any]:
    return dict(RETIRED_AUTHORITY_BOUNDARY)


def _no_op_evidence(value: Sequence[Mapping[str, Any]] | Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if isinstance(value, Mapping):
        return [dict(value)]
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "RETIRED_AUTHORITY_BOUNDARY",
    "build_current_execution_evidence",
    "retired_authority_boundary",
]
