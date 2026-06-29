from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


RETIRED_AUTHORITY_BOUNDARY = {
    "surface_kind": "legacy_current_work_unit_authority_boundary",
    "status": "retired",
    "authority": "retired_projection",
    "replacement_authority": "StageOutcome -> NextActionEnvelope -> OPL TransitionReceipt",
    "default_selector_policy": "fail_closed",
    "diagnostic_only": True,
    "can_select_next_action": False,
    "can_authorize_dispatch": False,
    "can_start_provider_attempt": False,
    "can_claim_paper_progress": False,
}


def build_current_work_unit(
    *,
    status: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    actions: Sequence[Mapping[str, Any]] | None = None,
    current_executable_owner_action: Mapping[str, Any] | None = None,
    current_execution_envelope: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    provider_admission: Mapping[str, Any] | None = None,
    provider_running_proof: Mapping[str, Any] | None = None,
    live_provider_attempt: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
    next_owner: str | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    return {}


def action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any] | None,
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    return not _mapping(blocker)


def retired_authority_boundary() -> dict[str, Any]:
    return dict(RETIRED_AUTHORITY_BOUNDARY)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "RETIRED_AUTHORITY_BOUNDARY",
    "action_supersedes_typed_blocker",
    "build_current_work_unit",
    "retired_authority_boundary",
]
