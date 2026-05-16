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


def direct_commit_repo_write_policy(*, source: str = "github") -> dict[str, Any]:
    return {
        "route": "direct_commit",
        "direct_repo_write_allowed": True,
        "pull_request_required": False,
        "source": source,
        "reason": None,
    }


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
    repo_write_policy: dict[str, Any] | None = None
    blocked_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        repo_write_policy = self.repo_write_policy or direct_commit_repo_write_policy()
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
            "repo_write_policy": dict(repo_write_policy),
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
    configured_login: str | None = None,
    source: str | None = None,
    environ: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    env = environ or os.environ
    expected = _text(env.get("MAS_DEVELOPER_SUPERVISOR_EXPECTED_GITHUB_LOGIN")) or expected_login
    if configured_login is not None:
        login = _text(configured_login)
        allowed = login == expected
        return {
            "expected_login": expected,
            "login": login,
            "allowed": allowed,
            "source": source or "profile",
            "reason": None if allowed else "github_user_requires_pull_request_route",
        }
    env_login = _text(env.get("MAS_DEVELOPER_SUPERVISOR_GITHUB_LOGIN"))
    if env_login is not None:
        allowed = env_login == expected
        return {
            "expected_login": expected,
            "login": env_login,
            "allowed": allowed,
            "source": "env",
            "reason": None if allowed else "github_user_requires_pull_request_route",
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
        reason = "github_user_requires_pull_request_route" if login else "github_user_lookup_failed"
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


def _profile_github_username(profile: object) -> str | None:
    if profile is None:
        return None
    return _text(getattr(profile, "github_username", None))


def _profile_mas_developer_github_usernames(profile: object) -> tuple[str, ...]:
    if profile is None:
        return (EXPECTED_DEVELOPER_GITHUB_LOGIN,)
    raw_values = getattr(profile, "mas_developer_github_usernames", None)
    if raw_values is None:
        return (EXPECTED_DEVELOPER_GITHUB_LOGIN,)
    if isinstance(raw_values, str):
        values = (_text(raw_values),)
    else:
        try:
            values = tuple(_text(item) for item in raw_values)
        except TypeError:
            values = ()
    normalized = tuple(value for value in values if value)
    return normalized or (EXPECTED_DEVELOPER_GITHUB_LOGIN,)


def _repo_write_policy(*, gate: Mapping[str, Any]) -> dict[str, Any]:
    if gate.get("allowed") is True:
        return {
            "route": "direct_commit",
            "direct_repo_write_allowed": True,
            "pull_request_required": False,
            "source": _text(gate.get("source")) or "github",
            "reason": None,
        }
    if _text(gate.get("login")) is not None:
        return {
            "route": "pull_request",
            "direct_repo_write_allowed": False,
            "pull_request_required": True,
            "source": _text(gate.get("source")) or "github",
            "reason": _text(gate.get("reason")) or "github_user_requires_pull_request_route",
        }
    return {
        "route": "blocked",
        "direct_repo_write_allowed": False,
        "pull_request_required": False,
        "source": _text(gate.get("source")) or "github",
        "reason": _text(gate.get("reason")) or "github_user_lookup_failed",
    }


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
    profile_developers = _profile_mas_developer_github_usernames(profile)
    user_config_expected = _text(user_config.get("auto_enable_github_login"))
    expected_login = (
        user_config_expected
        if user_config.get("source") == "user_config" and user_config_expected is not None
        else profile_developers[0]
    )
    configured_login = _profile_github_username(profile)
    gate = current_github_user_gate(
        expected_login=expected_login,
        configured_login=configured_login,
        source="profile" if configured_login is not None else None,
    )
    if configured_login is not None:
        developer_allowed = configured_login in profile_developers
        gate = {
            **gate,
            "expected_login": profile_developers[0],
            "allowed": developer_allowed,
            "reason": None if developer_allowed else "github_user_requires_pull_request_route",
        }
    write_policy = _repo_write_policy(gate=gate)
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
    elif requested == "developer_apply_safe" and write_policy["route"] == "blocked":
        effective = "external_observe"
        blocked_reason = _text(write_policy.get("reason")) or "github_user_lookup_failed"
        authority_gate = {
            "allowed": False,
            "source": "github_auto_default",
            "reason": blocked_reason,
        }
    elif requested == "developer_apply_safe" and write_policy["route"] == "pull_request":
        authority_gate = {
            "allowed": True,
            "source": "profile_developer_mode_pull_request",
            "reason": _text(write_policy.get("reason")) or "github_user_requires_pull_request_route",
        }
    elif requested == "developer_apply_safe":
        authority_gate = {
            "allowed": True,
            "source": "profile_developer_mode_direct_commit" if configured_login is not None else "github_auto_default",
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
        repo_write_policy=write_policy,
        blocked_reason=blocked_reason,
    )


__all__ = [
    "DEFAULT_DEVELOPER_SUPERVISOR_MODE",
    "EXPECTED_DEVELOPER_GITHUB_LOGIN",
    "SUPPORTED_DEVELOPER_SUPERVISOR_MODES",
    "DeveloperSupervisorMode",
    "current_github_user_gate",
    "direct_commit_repo_write_policy",
    "resolve_developer_supervisor_mode",
    "validate_developer_supervisor_mode",
]
