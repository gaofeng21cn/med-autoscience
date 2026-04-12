from __future__ import annotations

from pathlib import Path
import os
import sqlite3
import subprocess
import sys
from typing import Any

import yaml


_PROVIDER_ENV_KEYS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "ANTHROPIC_API_KEY",
    "ZAI_API_KEY",
    "GLM_API_KEY",
    "KIMI_API_KEY",
    "MOONSHOT_API_KEY",
    "MINIMAX_API_KEY",
    "MINIMAX_CN_API_KEY",
    "NOUS_API_KEY",
)


def _run_command(*, command: list[str], cwd: Path | None = None) -> tuple[int, str]:
    completed = subprocess.run(
        command,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=False,
    )
    output = completed.stdout.strip() or completed.stderr.strip()
    return completed.returncode, output


def _is_git_repo(repo_root: Path) -> bool:
    exit_code, output = _run_command(command=["git", "rev-parse", "--is-inside-work-tree"], cwd=repo_root)
    return exit_code == 0 and output.lower() == "true"


def _managed_python_path(repo_root: Path) -> Path | None:
    candidates = (
        repo_root / ".venv" / "bin" / "python",
        repo_root / ".venv" / "Scripts" / "python.exe",
    )
    for candidate in candidates:
        if candidate.is_file():
            return candidate
    return None


def _load_env_file(path: Path) -> dict[str, str]:
    if not path.is_file():
        return {}
    values: dict[str, str] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _provider_keys_from_env(path: Path) -> tuple[str, ...]:
    entries = _load_env_file(path)
    return tuple(sorted(key for key in _PROVIDER_ENV_KEYS if entries.get(key)))


def _provider_config_from_yaml(path: Path) -> dict[str, str | None]:
    if not path.is_file():
        return {"provider": None, "model": None}
    try:
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {"provider": None, "model": None}
    if not isinstance(payload, dict):
        return {"provider": None, "model": None}
    provider = str(payload.get("provider") or "").strip() or None
    model = str(payload.get("model") or "").strip() or None
    return {"provider": provider, "model": model}


def _state_db_counts(path: Path) -> tuple[int | None, int | None]:
    if not path.is_file():
        return None, None
    try:
        with sqlite3.connect(path) as connection:
            session_count = connection.execute("select count(*) from sessions").fetchone()
            message_count = connection.execute("select count(*) from messages").fetchone()
    except sqlite3.Error:
        return None, None
    return int(session_count[0]), int(message_count[0])


def _inspect_gateway_service(*, hermes_home_root: Path) -> dict[str, Any]:
    if sys.platform == "darwin":
        service_label = "ai.hermes.gateway"
        service_file = Path.home() / "Library" / "LaunchAgents" / f"{service_label}.plist"
        exit_code, _ = _run_command(command=["launchctl", "print", f"gui/{os.getuid()}/{service_label}"])
        return {
            "manager": "launchd",
            "service_label": service_label,
            "service_file_exists": service_file.is_file(),
            "loaded": exit_code == 0,
            "issues": [] if exit_code == 0 else ["external_runtime.gateway_service_not_loaded"],
        }

    if sys.platform.startswith("linux"):
        service_label = "hermes-gateway"
        service_file = Path.home() / ".config" / "systemd" / "user" / f"{service_label}.service"
        exit_code, _ = _run_command(command=["systemctl", "--user", "is-active", service_label])
        return {
            "manager": "systemd",
            "service_label": service_label,
            "service_file_exists": service_file.is_file(),
            "loaded": exit_code == 0,
            "issues": [] if exit_code == 0 else ["external_runtime.gateway_service_not_loaded"],
        }

    return {
        "manager": None,
        "service_label": "hermes-gateway",
        "service_file_exists": False,
        "loaded": False,
        "issues": ["external_runtime.gateway_service_not_loaded"],
    }


def inspect_hermes_runtime_contract(
    *,
    hermes_agent_repo_root: Path | None,
    hermes_home_root: Path | None = None,
) -> dict[str, Any]:
    resolved_repo_root = Path(hermes_agent_repo_root).expanduser().resolve() if hermes_agent_repo_root else None
    resolved_hermes_home_root = (
        Path(hermes_home_root).expanduser().resolve() if hermes_home_root else (Path.home() / ".hermes").resolve()
    )

    configured = resolved_repo_root is not None
    repo_exists = bool(resolved_repo_root and resolved_repo_root.exists())
    is_git_repo = bool(repo_exists and _is_git_repo(resolved_repo_root))
    launcher_path = resolved_repo_root / "hermes" if resolved_repo_root else None
    gateway_launcher_path = resolved_repo_root / "scripts" / "hermes-gateway" if resolved_repo_root else None
    launcher_exists = bool(launcher_path and launcher_path.is_file())
    gateway_launcher_exists = bool(gateway_launcher_path and gateway_launcher_path.is_file())
    managed_python_path = _managed_python_path(resolved_repo_root) if resolved_repo_root else None
    managed_python_exists = bool(managed_python_path and managed_python_path.is_file())
    pyproject_exists = bool(resolved_repo_root and (resolved_repo_root / "pyproject.toml").is_file())
    install_method = "repo_uv" if pyproject_exists and managed_python_exists else None

    hermes_home_exists = resolved_hermes_home_root.exists()
    state_db_path = resolved_hermes_home_root / "state.db"
    state_db_exists = state_db_path.is_file()
    logs_dir_exists = (resolved_hermes_home_root / "logs").is_dir()
    sessions_dir_exists = (resolved_hermes_home_root / "sessions").is_dir()
    env_file_path = resolved_hermes_home_root / ".env"
    env_file_exists = env_file_path.is_file()
    provider_env_keys = _provider_keys_from_env(env_file_path)
    config_yaml_path = resolved_hermes_home_root / "config.yaml"
    config_yaml_exists = config_yaml_path.is_file()
    config_provider = _provider_config_from_yaml(config_yaml_path)
    provider_ready = bool(provider_env_keys or config_provider["provider"] or config_provider["model"])

    session_count, message_count = _state_db_counts(state_db_path)
    gateway_status = _inspect_gateway_service(hermes_home_root=resolved_hermes_home_root)
    gateway_service_loaded = bool(gateway_status["loaded"])

    issues: list[str] = []
    if not configured:
        issues.append("external_runtime.repo_not_configured")
    if configured and not repo_exists:
        issues.append("external_runtime.repo_missing")
    elif repo_exists and not is_git_repo:
        issues.append("external_runtime.repo_not_git")
    if configured and not launcher_exists:
        issues.append("external_runtime.launcher_missing")
    if configured and not gateway_launcher_exists:
        issues.append("external_runtime.gateway_launcher_missing")
    if configured and not managed_python_exists:
        issues.append("external_runtime.managed_python_missing")
    if not hermes_home_exists:
        issues.append("external_runtime.home_missing")
    elif not state_db_exists:
        issues.append("external_runtime.state_db_missing")
    if hermes_home_exists and not logs_dir_exists:
        issues.append("external_runtime.logs_dir_missing")
    if hermes_home_exists and not sessions_dir_exists:
        issues.append("external_runtime.sessions_dir_missing")
    if not provider_ready:
        issues.append("external_runtime.provider_not_configured")
    if not gateway_service_loaded:
        issues.append("external_runtime.gateway_service_not_loaded")

    ready = (
        configured
        and repo_exists
        and is_git_repo
        and launcher_exists
        and gateway_launcher_exists
        and managed_python_exists
        and hermes_home_exists
        and state_db_exists
        and logs_dir_exists
        and sessions_dir_exists
        and provider_ready
        and gateway_service_loaded
    )

    return {
        "configured": configured,
        "repo_root": str(resolved_repo_root) if resolved_repo_root else None,
        "repo_exists": repo_exists,
        "is_git_repo": is_git_repo,
        "launcher_path": str(launcher_path) if launcher_path else None,
        "launcher_exists": launcher_exists,
        "gateway_launcher_path": str(gateway_launcher_path) if gateway_launcher_path else None,
        "gateway_launcher_exists": gateway_launcher_exists,
        "managed_python_path": str(managed_python_path) if managed_python_path else None,
        "managed_python_exists": managed_python_exists,
        "install_method": install_method,
        "hermes_home_root": str(resolved_hermes_home_root),
        "hermes_home_exists": hermes_home_exists,
        "state_db_path": str(state_db_path),
        "state_db_exists": state_db_exists,
        "logs_dir_exists": logs_dir_exists,
        "sessions_dir_exists": sessions_dir_exists,
        "env_file_path": str(env_file_path),
        "env_file_exists": env_file_exists,
        "provider_env_keys": list(provider_env_keys),
        "config_yaml_path": str(config_yaml_path),
        "config_yaml_exists": config_yaml_exists,
        "config_provider": config_provider,
        "provider_ready": provider_ready,
        "session_count": session_count,
        "message_count": message_count,
        "gateway_service_manager": gateway_status["manager"],
        "gateway_service_label": gateway_status["service_label"],
        "gateway_service_file_exists": bool(gateway_status["service_file_exists"]),
        "gateway_service_loaded": gateway_service_loaded,
        "issues": issues,
        "ready": ready,
    }
