from __future__ import annotations

import os
import shlex
from pathlib import Path


WORKSPACE_MAS_ENV_KEYS = frozenset(
    {
        "MED_AUTOSCIENCE_REPO",
        "MED_AUTOSCIENCE_UV_BIN",
        "MED_AUTOSCIENCE_PROFILE",
        "MED_AUTOSCIENCE_RSCRIPT_BIN",
        "MED_AUTOSCIENCE_NODE_BIN",
    }
)


def load_workspace_mas_config_env(*, quest_root: Path, env: dict[str, str]) -> None:
    workspace_root = workspace_root_from_quest_root(quest_root)
    if workspace_root is None:
        return
    config_env_path = workspace_root / "ops" / "medautoscience" / "config.env"
    if not config_env_path.is_file():
        return
    env.setdefault("WORKSPACE_ROOT", str(workspace_root))
    for raw_line in config_env_path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        lhs, rhs = stripped.split("=", 1)
        key = lhs.removeprefix("export ").strip()
        if key not in WORKSPACE_MAS_ENV_KEYS or env.get(key):
            continue
        value = _parse_config_env_value(raw_value=rhs)
        if value is None:
            continue
        env[key] = value.replace("${WORKSPACE_ROOT}", str(workspace_root))


def prepend_configured_tool_dirs_to_path(env: dict[str, str]) -> None:
    configured_dirs: list[str] = []
    for key in ("MED_AUTOSCIENCE_UV_BIN", "MED_AUTOSCIENCE_RSCRIPT_BIN", "MED_AUTOSCIENCE_NODE_BIN"):
        tool_path = _non_empty_env_path(env.get(key))
        if tool_path is None or not tool_path.is_absolute():
            continue
        parent = tool_path.parent
        if not parent.is_dir():
            continue
        parent_text = str(parent)
        if parent_text not in configured_dirs:
            configured_dirs.append(parent_text)
    path_entries = [entry for entry in env.get("PATH", "").split(os.pathsep) if entry]
    kept_entries = [entry for entry in path_entries if entry not in configured_dirs]
    env["PATH"] = os.pathsep.join([*configured_dirs, *kept_entries])


def workspace_root_from_quest_root(quest_root: Path) -> Path | None:
    resolved = Path(quest_root).expanduser().resolve()
    parts = resolved.parts
    for index in range(len(parts) - 2):
        if tuple(parts[index : index + 2]) == ("runtime", "quests"):
            return Path(*parts[:index])
    return None


def _parse_config_env_value(*, raw_value: str) -> str | None:
    try:
        tokens = shlex.split(raw_value.strip(), posix=True)
    except ValueError:
        return None
    if len(tokens) != 1 or not tokens[0].strip():
        return None
    return tokens[0].strip()


def _non_empty_env_path(value: str | None) -> Path | None:
    text = str(value or "").strip()
    return Path(text).expanduser() if text else None
