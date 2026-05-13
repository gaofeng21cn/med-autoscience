from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .shared import (
    _candidate_path,
    _mapping_copy,
    resolve_effective_study_manual_finish_contract,
)


@dataclass(frozen=True)
class ProjectionStatusContext:
    publication_supervisor_state: dict[str, Any]
    autonomous_runtime_notice: dict[str, Any]
    execution_owner_guard: dict[str, Any]
    pending_user_interaction: dict[str, Any]
    interaction_arbitration: dict[str, Any]
    supervisor_tick_audit: dict[str, Any]
    continuation_state: dict[str, Any]
    family_checkpoint_lineage: dict[str, Any]
    runtime_health_snapshot: dict[str, Any]
    study_truth_snapshot: dict[str, Any]
    control_plane_snapshot: dict[str, Any]
    manual_finish_contract: dict[str, Any] | None


def build_projection_status_context(
    *,
    status: dict[str, Any],
    study_root: Path,
) -> ProjectionStatusContext:
    manual_finish_contract = _manual_finish_contract(status=status, study_root=study_root)
    return ProjectionStatusContext(
        publication_supervisor_state=_dict_field(status, "publication_supervisor_state"),
        autonomous_runtime_notice=_dict_field(status, "autonomous_runtime_notice"),
        execution_owner_guard=_dict_field(status, "execution_owner_guard"),
        pending_user_interaction=_dict_field(status, "pending_user_interaction"),
        interaction_arbitration=_dict_field(status, "interaction_arbitration"),
        supervisor_tick_audit=_dict_field(status, "supervisor_tick_audit"),
        continuation_state=_dict_field(status, "continuation_state"),
        family_checkpoint_lineage=_dict_field(status, "family_checkpoint_lineage"),
        runtime_health_snapshot=_mapping_copy(status.get("runtime_health_snapshot")),
        study_truth_snapshot=_mapping_copy(status.get("study_truth_snapshot")),
        control_plane_snapshot=_mapping_copy(status.get("control_plane_snapshot")),
        manual_finish_contract=manual_finish_contract,
    )


def _dict_field(status: dict[str, Any], key: str) -> dict[str, Any]:
    value = status.get(key)
    return dict(value) if isinstance(value, dict) else {}


def _manual_finish_contract(*, status: dict[str, Any], study_root: Path) -> dict[str, Any] | None:
    try:
        manual_finish = resolve_effective_study_manual_finish_contract(
            study_root=study_root,
            quest_root=_candidate_path(status.get("quest_root")),
        )
    except ValueError:
        manual_finish = None
    if manual_finish is None:
        return None
    return {
        "status": manual_finish.status.value,
        "summary": manual_finish.summary,
        "next_action_summary": manual_finish.next_action_summary,
        "manual_finish_guard_only": manual_finish.manual_finish_guard_only,
    }
