from __future__ import annotations

from typing import Any

from med_autoscience.developer_supervisor_mode import DeveloperSupervisorMode
from med_autoscience.profiles import WorkspaceProfile


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
    return {
        "surface": "workspace_daemon_lifecycle",
        "released": False,
        "reason": "opl_provider_liveness_owner_required",
        "runtime_root": str(profile.managed_runtime_home),
        "typed_blocker": {
            "blocker_type": "provider_liveness_owned_by_opl",
            "owner": "one-person-lab",
            "required_action": "Release or reconcile idle provider workers through OPL current_control_state.",
        },
    }


__all__ = ["workspace_daemon_lifecycle"]
