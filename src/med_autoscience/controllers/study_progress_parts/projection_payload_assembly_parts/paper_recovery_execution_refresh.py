from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from ..shared import _mapping_copy


def refresh_after_paper_recovery_state(
    *,
    payload: dict[str, Any],
    status: Mapping[str, Any],
    handoff: Mapping[str, Any],
    runtime_health_snapshot: Mapping[str, Any],
    study_root: object,
    build_current_executable_owner_action: Callable[[Mapping[str, Any]], dict[str, Any] | None],
    refresh_current_execution_surfaces: Callable[..., dict[str, Any]],
    provider_admission_projection_fields: Callable[..., dict[str, Any]],
    sync_progress_first_owner_action_admission: Callable[[dict[str, Any]], dict[str, Any]],
    build_paper_recovery_state: Callable[[Mapping[str, Any]], dict[str, Any]],
) -> dict[str, Any]:
    recovery_current_action = build_current_executable_owner_action(payload)
    recovery_probe = refresh_current_execution_surfaces(
        payload={**payload, "current_executable_owner_action": recovery_current_action},
        status=status,
        handoff=handoff,
        runtime_health_snapshot=runtime_health_snapshot,
    )
    if (
        recovery_current_action == _mapping_copy(payload.get("current_executable_owner_action"))
        and _mapping_copy(recovery_probe.get("current_work_unit"))
        == _mapping_copy(payload.get("current_work_unit"))
    ):
        return payload
    updated = recovery_probe
    updated.update(
        provider_admission_projection_fields(
            payload=updated,
            handoff=handoff,
            study_root=study_root,
        )
    )
    updated = sync_progress_first_owner_action_admission(updated)
    updated["paper_recovery_state"] = build_paper_recovery_state(updated)
    return updated


__all__ = ["refresh_after_paper_recovery_state"]
