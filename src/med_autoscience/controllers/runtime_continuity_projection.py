from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def runtime_continuity_projection(
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    runtime = runtime or {}
    handoff = compact_domain_authority_handoff(progress.get("domain_authority_handoff")) or compact_domain_authority_handoff(
        runtime.get("domain_authority_handoff")
    )
    return {
        "surface_kind": "mas_domain_authority_control_projection",
        "authority": {
            "kind": "read_model_projection",
            "writes_authority_surface": False,
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        },
        "domain_authority_handoff": handoff,
        "opl_control_plane": {
            "runtime_control_owner": "one-person-lab",
            "stage_attempt_state_owned_by_mas": False,
            "provider_completion_is_domain_completion": False,
            "queue_succeeded_is_domain_completion": False,
        },
    }


def compact_domain_authority_handoff(value: object) -> dict[str, Any] | None:
    handoff = _mapping(value)
    if not handoff:
        return None
    keys = (
        "surface_kind",
        "study_id",
        "quest_id",
        "status",
        "generated_at",
        "owner_route",
        "typed_blocker",
        "action_refs",
        "opl_control_plane",
        "authority",
    )
    compact = {key: handoff.get(key) for key in keys if handoff.get(key) is not None}
    return compact or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _refs_from_ref_field(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_refs_from_ref_field(item))
        return result
    if isinstance(value, list | tuple):
        result: list[str] = []
        for item in value:
            result.extend(_refs_from_ref_field(item))
        return result
    return []


__all__ = [
    "compact_domain_authority_handoff",
    "runtime_continuity_projection",
]
