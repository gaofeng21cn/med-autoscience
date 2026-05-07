from __future__ import annotations

from pathlib import Path

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.product_entry_parts.shared_labels import _non_empty_text
from med_autoscience.controllers.product_entry_parts.shared import (
    _command_prefix,
    _profile_arg,
    _quote_cli_arg,
    _study_selector,
)


def study_commands(
    *,
    profile_ref: str | Path | None,
    study_id: str | None,
) -> dict[str, str]:
    resolved_study_id = _non_empty_text(study_id) or ""
    return {
        "launch": (
            f"{_command_prefix(profile_ref)} launch-study --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "progress": (
            f"{_command_prefix(profile_ref)} study-progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study-runtime-status --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
    }


def workspace_commands(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, str]:
    return {
        "mainline_status": f"{_command_prefix(profile_ref)} mainline-status",
        "doctor": f"{_command_prefix(profile_ref)} doctor --profile {_profile_arg(profile_ref)}",
        "bootstrap": f"{_command_prefix(profile_ref)} bootstrap --profile {_profile_arg(profile_ref)}",
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --ensure-study-runtimes --apply"
        ),
        "service_install": f"{_command_prefix(profile_ref)} runtime-ensure-supervision --profile {_profile_arg(profile_ref)}",
        "service_status": f"{_command_prefix(profile_ref)} runtime-supervision-status --profile {_profile_arg(profile_ref)}",
    }


def user_loop_commands(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, str]:
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    return {
        "mainline_status": f"{prefix} mainline-status",
        "phase_status_current": f"{prefix} mainline-phase --phase current",
        "phase_status_next": f"{prefix} mainline-phase --phase next",
        "open_workspace_cockpit": f"{prefix} workspace-cockpit --profile {profile_arg}",
        "submit_task_template": (
            f"{prefix} submit-study-task --profile {profile_arg} --study-id <study_id> "
            "--task-intent '<task_intent>'"
        ),
        "launch_study_template": f"{prefix} launch-study --profile {profile_arg} --study-id <study_id>",
        "watch_progress_template": f"{prefix} study-progress --profile {profile_arg} --study-id <study_id>",
        "refresh_supervision": (
            f"{prefix} watch --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {profile_arg} --ensure-study-runtimes --apply"
        ),
    }
