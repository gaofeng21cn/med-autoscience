from __future__ import annotations

from pathlib import Path
from typing import Any

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
) -> dict[str, Any]:
    supervisor_tick = (
        f"{_command_prefix(profile_ref)} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {_profile_arg(profile_ref)} --request-opl-stage-attempts --dry-run"
    )
    return {
        "mainline_status": _command(profile_ref, "mainline-status"),
        "doctor": _command(profile_ref, "doctor", "--profile", _profile_arg(profile_ref)),
        "bootstrap": _command(profile_ref, "bootstrap", "--profile", _profile_arg(profile_ref)),
        "supervisor_tick": supervisor_tick,
        "supervisor_tick_policy": diagnostic_supervision_command_policy(
            command=supervisor_tick,
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
) -> dict[str, Any]:
    profile_arg = _profile_arg(profile_ref)
    prefix = _command_prefix(profile_ref)
    refresh_supervision = (
        f"{prefix} runtime domain-health-diagnostic --runtime-root {_quote_cli_arg(profile.runtime_root)} "
        f"--profile {profile_arg} --request-opl-stage-attempts --dry-run"
    )
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
        "refresh_supervision": refresh_supervision,
        "refresh_supervision_policy": diagnostic_supervision_command_policy(
            command=refresh_supervision,
        ),
    }


def diagnostic_supervision_command_policy(*, command: str) -> dict[str, object]:
    return {
        "command": command,
        "surface_role": "runtime_diagnostic_refresh",
        "dry_run": True,
        "diagnostic_only": True,
        "writes_authority": False,
        "writes_runtime": False,
        "can_select_next_paper_stage": False,
        "can_authorize_provider_admission": False,
        "counts_as_paper_progress": False,
        "default_paper_mission_entry": False,
        "required_followthrough": (
            "Use paper-mission inspect/start/resume or consume-candidate output "
            "for the MAS paper loop; this command only refreshes runtime diagnostics."
        ),
    }
