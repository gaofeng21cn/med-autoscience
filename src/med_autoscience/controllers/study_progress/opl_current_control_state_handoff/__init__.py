from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.workspace_contracts import build_workspace_runtime_layout_for_profile

from ..opl_current_control_state_handoff_values import (
    _copy_mapping_keys,
    _stage_progress_log_mapping,
    _strict_running_provider_attempt,
    _work_unit_identity,
)
from ..shared_base import _mapping_copy, _non_empty_text, _read_json_object
from .lifecycle import build_readonly_ai_repair_lifecycle_projection, read_ai_repair_lifecycle


def opl_current_control_state_handoff_path(*, profile: WorkspaceProfile) -> Path:
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )


def opl_current_control_state_study_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    source_path = opl_current_control_state_handoff_path(profile=profile)
    payload = _read_json_object(source_path)
    if not payload:
        return None
    studies = payload.get("studies") if isinstance(payload.get("studies"), list) else []
    study = next(
        (dict(item) for item in studies if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id),
        {},
    )
    if not study and _non_empty_text(payload.get("study_id")) == study_id:
        study = dict(payload)
    if not study:
        return None
    active_run_id = _non_empty_text(study.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(study.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(study.get("active_workflow_id"))
    projection = {
        "surface_kind": "opl_stage_attempt_context_handoff",
        "read_model": "study_opl_stage_attempt_context_projection",
        "authority": "observability_only",
        "source_path": str(source_path),
        "study_id": study_id,
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": _strict_running_provider_attempt(
            study,
            active_run_id=active_run_id,
            active_stage_attempt_id=active_stage_attempt_id,
            active_workflow_id=active_workflow_id,
        ),
        "action_type": _non_empty_text(study.get("action_type")),
        "work_unit_id": _work_unit_identity(study.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(study.get("work_unit_fingerprint")),
        "runtime_health": _copy_mapping_keys(
            study.get("runtime_health"),
            (
                "health_status",
                "runtime_liveness_status",
                "summary",
                "blocked_reason",
                "action_type",
                "work_unit_id",
                "work_unit_fingerprint",
                "action_fingerprint",
            ),
        ),
        "stage_progress_log": _stage_progress_log_mapping(study.get("stage_progress_log")),
        "artifact_refs": list(study.get("artifact_refs") or []),
        "progress_first": {
            "transport_readback_cannot_select_semantic_route": True,
            "missing_transport_readback_blocks_stage_transition": False,
            "next_stage_may_start": True,
            "route_selection_owner": "codex_cli",
        },
        "quality_debt": {
            "blocks_stage_transition": False,
            "blocks_ready_or_publication_claims": False,
        },
    }
    return projection


def opl_current_control_state_live_attempt_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    runtime_liveness_audit: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(runtime_liveness_audit.get("source")) != "opl_current_control_state_provider_attempt":
        return None
    active_run_id = _non_empty_text(runtime_liveness_audit.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(runtime_liveness_audit.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(runtime_liveness_audit.get("active_workflow_id"))
    running = _strict_running_provider_attempt(
        runtime_liveness_audit,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    return {
        "surface_kind": "opl_stage_attempt_context_handoff",
        "read_model": "study_opl_stage_attempt_context_projection",
        "authority": "observability_only",
        "source_path": _non_empty_text(runtime_liveness_audit.get("handoff_path"))
        or str(opl_current_control_state_handoff_path(profile=profile)),
        "study_id": study_id,
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running,
        "action_type": _non_empty_text(runtime_liveness_audit.get("action_type")),
        "work_unit_id": _work_unit_identity(runtime_liveness_audit.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "runtime_health": _copy_mapping_keys(
            runtime_liveness_audit.get("runtime_health"),
            ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
        ),
        "stage_progress_log": _stage_progress_log_mapping(runtime_liveness_audit.get("stage_progress_log")),
        "progress_first": {
            "transport_readback_cannot_select_semantic_route": True,
            "next_stage_may_start": True,
            "route_selection_owner": "codex_cli",
        },
    }


def merge_live_attempt_observability_into_handoff(
    *,
    handoff: dict[str, Any] | None,
    live_attempt_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if handoff is None:
        return live_attempt_handoff
    if live_attempt_handoff is None:
        return handoff
    merged = dict(handoff)
    if live_attempt_handoff.get("running_provider_attempt") is True:
        for key in (
            "active_run_id",
            "active_stage_attempt_id",
            "active_workflow_id",
            "running_provider_attempt",
            "runtime_health",
            "stage_progress_log",
        ):
            if key in live_attempt_handoff:
                merged[key] = live_attempt_handoff[key]
    merged["progress_first"] = {
        "transport_readback_cannot_select_semantic_route": True,
        "next_stage_may_start": True,
        "route_selection_owner": "codex_cli",
    }
    return merged


__all__ = [
    "build_readonly_ai_repair_lifecycle_projection",
    "merge_live_attempt_observability_into_handoff",
    "opl_current_control_state_handoff_path",
    "opl_current_control_state_live_attempt_handoff_projection",
    "opl_current_control_state_study_handoff_projection",
    "read_ai_repair_lifecycle",
]
