from __future__ import annotations

from typing import Any

from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_transport import med_deepscientist as med_deepscientist_transport


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
            "runtime_root": str(profile.med_deepscientist_runtime_root),
        }
    try:
        return med_deepscientist_transport.release_idle_workspace_daemon(
            runtime_root=profile.med_deepscientist_runtime_root,
        )
    except (FileNotFoundError, OSError, RuntimeError, ValueError) as exc:
        return {
            "surface": "workspace_daemon_lifecycle",
            "released": False,
            "reason": "workspace_daemon_release_unavailable",
            "runtime_root": str(profile.med_deepscientist_runtime_root),
            "error": str(exc),
        }


__all__ = ["med_deepscientist_transport", "workspace_daemon_lifecycle"]
