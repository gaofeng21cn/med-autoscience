from __future__ import annotations

from pathlib import Path

from med_autoscience.profiles import WorkspaceProfile

from med_autoscience.controllers.product_entry_parts.shared_labels import _non_empty_text
from med_autoscience.controllers.product_entry_parts.shared import (
    _command,
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
            f"{_command(profile_ref, 'launch-study', '--profile', _profile_arg(profile_ref))} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "progress": (
            f"{_command(profile_ref, 'study-progress', '--profile', _profile_arg(profile_ref))} "
            f"{_study_selector(study_id=resolved_study_id)}"
        ),
        "status": (
            f"{_command_prefix(profile_ref)} study progress --profile {_profile_arg(profile_ref)} "
            f"{_study_selector(study_id=resolved_study_id)} --format json"
        ),
    }


def workspace_commands(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, str]:
    return {
        "mainline_status": _command(profile_ref, "mainline-status"),
        "doctor": _command(profile_ref, "doctor", "--profile", _profile_arg(profile_ref)),
        "bootstrap": _command(profile_ref, "bootstrap", "--profile", _profile_arg(profile_ref)),
        "supervisor_tick": (
            f"{_command_prefix(profile_ref)} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {_profile_arg(profile_ref)} --request-opl-stage-attempts --dry-run"
        ),
        "service_status": _command(
            profile_ref,
            "study-progress",
            "--profile",
            _profile_arg(profile_ref),
            "--format json",
        ),
    }


def user_loop_commands(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
) -> dict[str, str]:
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    return {
        "mainline_status": _command(profile_ref, "mainline-status"),
        "phase_status_current": _command(profile_ref, "mainline-phase", "--phase current"),
        "phase_status_next": _command(profile_ref, "mainline-phase", "--phase next"),
        "open_workspace_cockpit": _command(profile_ref, "workspace-cockpit", "--profile", profile_arg),
        "submit_task_template": (
            f"{_command(profile_ref, 'submit-study-task', '--profile', profile_arg)} --study-id <study_id> "
            "--task-intent '<task_intent>'"
        ),
        "launch_study_template": _command(
            profile_ref,
            "launch-study",
            "--profile",
            profile_arg,
            "--study-id <study_id>",
        ),
        "watch_progress_template": _command(
            profile_ref,
            "study-progress",
            "--profile",
            profile_arg,
            "--study-id <study_id>",
        ),
        "refresh_supervision": (
            f"{prefix} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
            f"--profile {profile_arg} --request-opl-stage-attempts --dry-run"
        ),
    }
