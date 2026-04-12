from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.hermes_runtime_contract import inspect_hermes_runtime_contract
from med_autoscience.profiles import WorkspaceProfile


def _determine_decision(external_runtime_check: dict[str, Any]) -> tuple[str, list[str]]:
    actions: list[str] = []

    if not external_runtime_check.get("configured"):
        actions.append("configure_hermes_agent_repo_root_in_profile")
        return "blocked_hermes_repo_not_configured", actions

    if not external_runtime_check.get("repo_exists"):
        actions.append("ensure_hermes_agent_repo_root_exists_locally")
        return "blocked_hermes_repo_missing", actions

    if not external_runtime_check.get("is_git_repo"):
        actions.append("point_profile_to_a_valid_hermes_agent_git_repo")
        return "blocked_hermes_repo_not_git", actions

    if (
        not external_runtime_check.get("launcher_exists")
        or not external_runtime_check.get("gateway_launcher_exists")
        or not external_runtime_check.get("managed_python_exists")
    ):
        actions.append("install_hermes_agent_runtime")
        return "blocked_hermes_installation_incomplete", actions

    if (
        not external_runtime_check.get("hermes_home_exists")
        or not external_runtime_check.get("state_db_exists")
        or not external_runtime_check.get("logs_dir_exists")
        or not external_runtime_check.get("sessions_dir_exists")
    ):
        actions.append("run_hermes_setup")
        return "blocked_hermes_home_not_initialized", actions

    if not external_runtime_check.get("provider_ready"):
        actions.append("configure_hermes_model_or_provider")
        if not external_runtime_check.get("gateway_service_loaded"):
            actions.append("install_or_start_hermes_gateway_service")
        return "blocked_hermes_provider_not_configured", actions

    if not external_runtime_check.get("gateway_service_loaded"):
        actions.append("install_or_start_hermes_gateway_service")
        return "blocked_hermes_gateway_not_loaded", actions

    actions.append("promote_repo_side_seam_to_real_adapter")
    return "ready_for_adapter_cutover", actions


def run_hermes_runtime_check(
    *,
    profile: WorkspaceProfile | None = None,
    hermes_agent_repo_root: Path | None = None,
    hermes_home_root: Path | None = None,
) -> dict[str, Any]:
    resolved_repo_root = hermes_agent_repo_root or (profile.hermes_agent_repo_root if profile else None)
    resolved_hermes_home_root = hermes_home_root or (profile.hermes_home_root if profile else None)
    external_runtime_check = inspect_hermes_runtime_contract(
        hermes_agent_repo_root=resolved_repo_root,
        hermes_home_root=resolved_hermes_home_root,
    )
    decision, recommended_actions = _determine_decision(external_runtime_check)
    return {
        "profile": profile.name if profile else None,
        "decision": decision,
        "recommended_actions": recommended_actions,
        "external_runtime_check": external_runtime_check,
    }
