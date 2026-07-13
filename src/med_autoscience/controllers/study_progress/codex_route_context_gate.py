from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.ai_route_context import is_nonbinding_codex_route_context


def has_nonbinding_codex_route_context(payload: Mapping[str, Any]) -> bool:
    context = _mapping(payload.get("ai_route_context")) or _mapping(
        payload.get("next_action")
    )
    return is_nonbinding_codex_route_context(context)


def legacy_programmatic_next_action_retirement() -> dict[str, Any]:
    return {
        "status": "retired",
        "authority": "codex_cli",
        "retired_authority": "NextActionEnvelope",
        "reason": "programmatic_next_action_authority_retired_use_codex_selected_stage",
        "retired_surfaces": [
            "current_work_unit",
            "current_executable_owner_action",
            "provider_attempt",
            "current_execution_envelope",
        ],
        "default_selector_policy": "codex_selected_declared_stage",
        "diagnostic_only": True,
        "missing_route_context_blocks_stage_transition": False,
    }


def _mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "has_nonbinding_codex_route_context",
    "legacy_programmatic_next_action_retirement",
]
