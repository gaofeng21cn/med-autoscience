from __future__ import annotations

from typing import Any

from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_transport import mas_runtime_core as mas_runtime_transport


def workspace_daemon_lifecycle(
    *,
    profile: WorkspaceProfile,
    developer_mode: DeveloperSupervisorMode,
) -> dict[str, Any]:
    if not developer_mode.safe_actions_enabled:
        return {
            "surface": "workspace_daemon_lifecycle",
            "released": False,
            "reason": "safe_actions_not_enabled",
            "runtime_root": str(profile.managed_runtime_home),
        }
    try:
        return mas_runtime_transport.release_idle_workspace_daemon(
            runtime_root=profile.managed_runtime_home,
        )
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        return {
            "surface": "workspace_daemon_lifecycle",
            "released": False,
            "reason": "workspace_daemon_release_unavailable",
            "runtime_root": str(profile.managed_runtime_home),
            "error": str(exc),
        }


__all__ = ["mas_runtime_transport", "workspace_daemon_lifecycle"]
