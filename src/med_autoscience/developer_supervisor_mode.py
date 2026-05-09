from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import json
import os
from pathlib import Path
import shutil
import subprocess
from typing import Any


SUPPORTED_DEVELOPER_SUPERVISOR_MODES = (
    "internal_only",
    "external_observe",
    "developer_apply_safe",
)
DEFAULT_DEVELOPER_SUPERVISOR_MODE = "internal_only"
EXPECTED_DEVELOPER_GITHUB_LOGIN = "gaofeng21cn"


@dataclass(frozen=True)
class DeveloperSupervisorMode:
    mode: str
    requested_mode: str
    mode_source: str
    developer_mode_enabled: bool
    safe_actions_enabled: bool
    repo_level_repair_authority: bool
    scheduler_owner: str
    codex_app_heartbeat_required: bool
    github_user_gate: dict[str, Any]
    opl_family_user_config: dict[str, Any]
    authority_gate: dict[str, Any]
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "mode": self.mode,
            "requested_mode": self.requested_mode,
            "mode_source": self.mode_source,
            "developer_mode_enabled": self.developer_mode_enabled,
            "safe_actions_enabled": self.safe_actions_enabled,
            "repo_level_repair_authority": self.repo_level_repair_authority,
            "scheduler_owner": self.scheduler_owner,
            "codex_app_heartbeat_required": self.codex_app_heartbeat_required,
            "github_user_gate": dict(self.github_user_gate),
            "opl_family_user_config": dict(self.opl_family_user_config),
            "authority_gate": dict(self.authority_gate),
            "blocked_reason": self.blocked_reason,
            "authority_contract": {
                "paper_package_mutation_allowed": False,
                "quality_gate_relaxation_allowed": False,
                "manual_study_patch_allowed": False,
                "medical_conclusion_authoring_allowed": False,
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


def current_github_user_gate(
    *,
    expected_login: str = EXPECTED_DEVELOPER_GITHUB_LOGIN,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = environ or os.environ
    expected = _text(env.get("MAS_DEVELOPER_SUPERVISOR_EXPECTED_GITHUB_LOGIN")) or expected_login
    env_login = _text(env.get("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN"))
    if env_login is not None:
        allowed = env_login == expected
        return {
            "expected_login": expected,
            "login": env_login,
            "allowed": allowed,
            "source": "env",
            "reason": None if allowed else "github_user_not_authorized_for_developer_supervisor_mode",
        }
    if shutil.which("gh") is None:
        return {
            "expected_login": expected,
            "login": None,
            "allowed": False,
            "source": "gh",
            "reason": "github_cli_unavailable",
        }
    try:
        completed = subprocess.run(
            ["gh", "api", "user", "--jq", ".login"],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {
            "expected_login": expected,
            "login": None,
            "allowed": False,
            "source": "gh",
            "reason": "github_user_lookup_failed",
        }
    login = _text(completed.stdout)
    allowed = completed.returncode == 0 and login == expected
    reason = None
    if not allowed:
        reason = "github_user_not_authorized_for_developer_supervisor_mode" if login else "github_user_lookup_failed"
    return {
        "expected_login": expected,
        "login": login,
        "allowed": allowed,
        "source": "gh",
        "reason": reason,
    }


def _opl_state_dir(environ: Mapping[str, str]) -> Path:
    explicit = _text(environ.get("OPL_STATE_DIR"))
    if explicit is not None:
        return Path(explicit).expanduser().resolve()
    home = _text(environ.get("HOME")) or str(Path.home())
    return Path(home).expanduser() / "Library" / "Application Support" / "OPL" / "state"


def _read_opl_family_user_config(environ: Mapping[str, str] | None = None) -> dict[str, Any]:
    env = environ or os.environ
    path = _opl_state_dir(env) / "developer-supervisor.json"
    base = {
        "version": "g1",
        "enabled": "auto",
        "mode": "developer_apply_safe",
        "auto_enable_github_login": EXPECTED_DEVELOPER_GITHUB_LOGIN,
        "source": "default",
        "path": str(path),
        "valid": True,
    }
    if not path.is_file():
        return base
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return {
            **base,
            "source": "invalid",
            "valid": False,
            "reason": "opl_family_user_config_invalid",
            "details": str(exc),
        }
    if not isinstance(payload, Mapping):
        return {
            **base,
            "source": "invalid",
            "valid": False,
            "reason": "opl_family_user_config_invalid",
        }
    enabled = _text(payload.get("enabled")) or "auto"
    if enabled not in {"auto", "on", "off"}:
        enabled = "auto"
    mode = _text(payload.get("mode")) or "developer_apply_safe"
    if mode not in {"external_observe", "developer_apply_safe"}:
        mode = "external_observe"
    return {
        **base,
        "enabled": enabled,
        "mode": mode,
        "auto_enable_github_login": _text(payload.get("auto_enable_github_login")) or EXPECTED_DEVELOPER_GITHUB_LOGIN,
        "updated_at": _text(payload.get("updated_at")),
        "source": "user_config",
    }


def _profile_mode(profile: object) -> str | None:
    if profile is None:
        return None
    if getattr(profile, "developer_supervisor_mode_explicit", False) is not True:
        return None
    return _text(getattr(profile, "developer_supervisor_mode", None))


def resolve_developer_supervisor_mode(
    *,
    profile: object | None = None,
    requested_mode: str | None = None,
    apply_safe_actions: bool = False,
    scheduler_owner: str = "portable_supervisor",
) -> DeveloperSupervisorMode:
    if requested_mode is not None:
        requested = validate_developer_supervisor_mode(requested_mode)
        mode_source = "command"
    elif (profile_mode := _profile_mode(profile)) is not None:
        requested = validate_developer_supervisor_mode(profile_mode)
        mode_source = "profile"
    elif apply_safe_actions:
        requested = "developer_apply_safe"
        mode_source = "apply_safe_actions"
    else:
        requested = "external_observe"
        mode_source = "supervisor_scan"

    user_config = _read_opl_family_user_config()
    expected_login = _text(user_config.get("auto_enable_github_login")) or EXPECTED_DEVELOPER_GITHUB_LOGIN
    gate = current_github_user_gate(expected_login=expected_login)
    effective = requested
    blocked_reason = None
    authority_gate = {"allowed": True, "source": "mode", "reason": None}
    if user_config.get("valid") is False:
        effective = "external_observe"
        blocked_reason = _text(user_config.get("reason")) or "opl_family_user_config_invalid"
        authority_gate = {
            "allowed": False,
            "source": "opl_family_user_config",
            "reason": blocked_reason,
        }
        mode_source = "opl_family_user_config_invalid"
    elif user_config.get("enabled") == "off":
        effective = "external_observe"
        blocked_reason = "developer_supervisor_disabled_by_user_config"
        authority_gate = {
            "allowed": False,
            "source": "opl_family_user_config",
            "reason": blocked_reason,
        }
        mode_source = "opl_family_user_config_disabled"
    elif requested == "developer_apply_safe" and user_config.get("enabled") == "on":
        configured_mode = validate_developer_supervisor_mode(user_config.get("mode"))
        if configured_mode != "developer_apply_safe":
            effective = "external_observe"
            blocked_reason = "developer_apply_safe_not_allowed_by_user_config"
            authority_gate = {
                "allowed": False,
                "source": "opl_family_user_config",
                "reason": blocked_reason,
            }
        else:
            effective = "developer_apply_safe"
            authority_gate = {
                "allowed": True,
                "source": "opl_family_user_config",
                "reason": None,
            }
    elif requested == "developer_apply_safe" and gate.get("allowed") is not True:
        effective = "external_observe"
        blocked_reason = _text(gate.get("reason")) or "github_user_not_authorized_for_developer_supervisor_mode"
        authority_gate = {
            "allowed": False,
            "source": "github_auto_default",
            "reason": blocked_reason,
        }
    elif requested == "developer_apply_safe":
        authority_gate = {
            "allowed": True,
            "source": "github_auto_default",
            "reason": None,
        }

    safe_actions_enabled = effective == "developer_apply_safe" and apply_safe_actions
    return DeveloperSupervisorMode(
        mode=effective,
        requested_mode=requested,
        mode_source=mode_source,
        developer_mode_enabled=effective == "developer_apply_safe",
        safe_actions_enabled=safe_actions_enabled,
        repo_level_repair_authority=effective == "developer_apply_safe",
        scheduler_owner=scheduler_owner,
        codex_app_heartbeat_required=False,
        github_user_gate=gate,
        opl_family_user_config=user_config,
        authority_gate=authority_gate,
        blocked_reason=blocked_reason,
    )


__all__ = [
    "DEFAULT_DEVELOPER_SUPERVISOR_MODE",
    "EXPECTED_DEVELOPER_GITHUB_LOGIN",
    "SUPPORTED_DEVELOPER_SUPERVISOR_MODES",
    "DeveloperSupervisorMode",
    "current_github_user_gate",
    "resolve_developer_supervisor_mode",
    "validate_developer_supervisor_mode",
]
