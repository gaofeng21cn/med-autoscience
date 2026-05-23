from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _manifest_open_auto_research_projection(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    projection = dict(value)
    studies: list[dict[str, Any]] = []
    for item in projection.get("study_projections") or []:
        if not isinstance(item, Mapping):
            continue
        study: dict[str, Any] = {}
        for key in (
            "study_id",
            "status",
            "counts",
            "delivery_journal_usability_guard",
            "authority",
            "refs",
        ):
            if key in item:
                study[key] = item[key]
        actions = item.get("actions")
        if isinstance(actions, list):
            study["actions"] = [
                {
                    key: action[key]
                    for key in ("action_id", "status", "surface")
                    if key in action
                }
                for action in actions
                if isinstance(action, Mapping)
            ][:4]
        studies.append(study)
    return {
        "surface_kind": projection.get("surface_kind") or "workspace_open_auto_research_projection",
        "read_model": "open_auto_research_projection_read_only_status_surface",
        "authority": "observability_only",
        "status": projection.get("status"),
        "summary": projection.get("summary"),
        "counts": dict(projection.get("counts") or {}),
        "study_projections": studies,
    }


def _manifest_opl_current_control_state_handoff_dashboard(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    projection = dict(value)
    studies: list[dict[str, Any]] = []
    for item in projection.get("studies") or []:
        if not isinstance(item, Mapping):
            continue
        study: dict[str, Any] = {}
        for key in (
            "study_id",
            "mode",
            "mode_label",
            "scheduler_owner",
            "codex_app_heartbeat_required",
            "safe_actions_enabled",
            "repo_level_repair_authority",
            "github_user_gate",
            "quest_status",
            "active_run_id",
            "runtime_health",
            "artifact_delta",
            "gate_specificity",
            "ai_reviewer_status",
            "queue_slo",
            "owner_pickup_overdue",
            "developer_supervisor_attention_required",
            "blocked_reason",
            "why_not_applied",
            "next_owner",
            "external_supervisor_required",
        ):
            if key in item:
                study[key] = item[key]
        actions = item.get("action_queue")
        if isinstance(actions, list):
            study["action_queue"] = [
                {
                    key: action[key]
                    for key in (
                        "action_type",
                        "summary",
                        "status",
                        "owner",
                        "surface",
                        "action_id",
                        "fingerprint",
                        "queue_age_hours",
                        "queued_first_seen_at",
                        "repeat_fingerprint",
                        "owner_pickup",
                        "consumption",
                    )
                    if key in action
                }
                for action in actions
                if isinstance(action, Mapping)
            ][:6]
        studies.append(study)
    return {
        "surface_kind": projection.get("surface_kind") or "opl_current_control_state_handoff_dashboard",
        "read_model": "workspace_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "status": projection.get("status"),
        "summary": projection.get("summary"),
        "source_path": projection.get("source_path"),
        "supervisor_mode": dict(projection.get("supervisor_mode") or {}),
        "counts": dict(projection.get("counts") or {}),
        "studies": studies,
    }

