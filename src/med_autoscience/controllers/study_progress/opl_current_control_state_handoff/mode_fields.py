from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ..opl_current_control_state_handoff_values import (
    _copy_mapping_keys,
    _current_control_currentness_fields,
    _first_present_mapping_value,
    _observability_mapping,
    _owner_route_projection,
    _stage_progress_log_mapping,
)
from ..shared_base import _mapping_copy, _non_empty_text

def _opl_current_control_state_mode_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    scheduler_contract = _mapping_copy(payload.get("scheduler_contract"))
    developer_supervisor = _mapping_copy(payload.get("developer_supervisor"))
    developer_supervisor_mode = _mapping_copy(payload.get("developer_supervisor_mode"))
    supervisor_mode = _mapping_copy(payload.get("supervisor_mode"))
    sources = (developer_supervisor, developer_supervisor_mode, supervisor_mode, scheduler_contract, payload)
    projection: dict[str, Any] = {}
    text_fields = (
        "mode",
        "mode_label",
        "scheduler_owner",
    )
    for key in text_fields:
        text = _non_empty_text(_first_present_mapping_value(sources, key))
        if text is not None:
            projection[key] = text
    for key in ("codex_app_heartbeat_required", "safe_actions_enabled", "repo_level_repair_authority"):
        for source in sources:
            if key in source:
                projection[key] = bool(source[key])
                break
    github_user_gate = _first_present_mapping_value(sources, "github_user_gate")
    if isinstance(github_user_gate, Mapping):
        projection["github_user_gate"] = dict(github_user_gate)
    else:
        text = _non_empty_text(github_user_gate)
        if text is not None:
            projection["github_user_gate"] = text
    authority_gate = _first_present_mapping_value(sources, "authority_gate")
    if isinstance(authority_gate, Mapping):
        projection["authority_gate"] = dict(authority_gate)
    else:
        text = _non_empty_text(authority_gate)
        if text is not None:
            projection["authority_gate"] = text
    if "safe_actions_enabled" not in projection and "apply_safe_actions" in payload:
        projection["safe_actions_enabled"] = bool(payload.get("apply_safe_actions"))
    return projection
