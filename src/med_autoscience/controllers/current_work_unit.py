from __future__ import annotations

from collections.abc import Mapping
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
    "retired_authority_boundary",
]
