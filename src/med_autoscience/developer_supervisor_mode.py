from __future__ import annotations

from dataclasses import dataclass
from typing import Any


SUPPORTED_DEVELOPER_SUPERVISOR_MODES = (
    "internal_only",
    "external_observe",
    "developer_apply_safe",
)
DEFAULT_DEVELOPER_SUPERVISOR_MODE = "external_observe"


@dataclass(frozen=True)
class DeveloperSupervisorMode:
    mode: str
    requested_mode: str
    mode_source: str
    safe_actions_enabled: bool
    scheduler_owner: str
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "requested_mode": self.requested_mode,
            "mode_source": self.mode_source,
            "developer_mode_enabled": self.safe_actions_enabled,
            "safe_actions_enabled": self.safe_actions_enabled,
            "repo_level_repair_authority": False,
            "scheduler_owner": self.scheduler_owner,
            "codex_app_heartbeat_required": False,
            "blocked_reason": self.blocked_reason,
            "projection_role": "mas_domain_action_projection_only",
            "execution_authorization_owner": "one-person-lab",
            "authority_contract": {
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_conclusion_authoring_allowed": False,
                "mas_can_define_developer_identity_policy": False,
                "mas_can_define_repo_write_policy": False,
                "mas_can_authorize_provider_admission": False,
            },
        }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def validate_developer_supervisor_mode(mode: object) -> str:
    text = _text(mode) or DEFAULT_DEVELOPER_SUPERVISOR_MODE
    if text not in SUPPORTED_DEVELOPER_SUPERVISOR_MODES:
        supported = ", ".join(SUPPORTED_DEVELOPER_SUPERVISOR_MODES)
        raise ValueError(f"developer_supervisor_mode must be one of: {supported}")
    return text


def resolve_developer_supervisor_mode(
    *,
    requested_mode: str | None = None,
    apply_safe_actions: bool = False,
    scheduler_owner: str = "opl_current_control_state",
) -> DeveloperSupervisorMode:
    requested = validate_developer_supervisor_mode(
        requested_mode or ("developer_apply_safe" if apply_safe_actions else None)
    )
    safe_actions_enabled = requested == "developer_apply_safe" and apply_safe_actions
    return DeveloperSupervisorMode(
        mode=requested,
        requested_mode=requested,
        mode_source="explicit_domain_projection_request" if requested_mode else "scan_domain_routes",
        safe_actions_enabled=safe_actions_enabled,
        scheduler_owner=scheduler_owner,
        blocked_reason=None,
    )


__all__ = [
    "DEFAULT_DEVELOPER_SUPERVISOR_MODE",
    "SUPPORTED_DEVELOPER_SUPERVISOR_MODES",
    "DeveloperSupervisorMode",
    "resolve_developer_supervisor_mode",
    "validate_developer_supervisor_mode",
]
