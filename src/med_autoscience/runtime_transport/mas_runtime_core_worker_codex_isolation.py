from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tomllib
from typing import Any


BACKGROUND_CODEX_CONFIG_KEYS = (
    "model_provider",
    "model",
    "model_reasoning_effort",
    "service_tier",
    "sandbox_mode",
    "approval_policy",
)


def remove_active_python_virtualenv(env: dict[str, str]) -> None:
    virtual_env = env.pop("VIRTUAL_ENV", None)
    env.pop("__PYVENV_LAUNCHER__", None)
    if not virtual_env:
        return
    virtualenv_bin = Path(virtual_env) / "bin"
    path_entries = env.get("PATH", "").split(os.pathsep)
    kept_entries = [entry for entry in path_entries if not _same_path(Path(entry), virtualenv_bin)]
    env["PATH"] = os.pathsep.join(kept_entries)


def preserve_host_codex_canonical_bin(env: dict[str, str]) -> None:
    existing = _non_empty_env_path(env.get("CODEX_CANONICAL_BIN"))
    if existing is not None and _is_executable(existing):
        env["CODEX_CANONICAL_BIN"] = str(existing)
        return
    for candidate in _host_codex_candidates(env):
        if _is_executable(candidate):
            env["CODEX_CANONICAL_BIN"] = str(candidate)
            return
    env.pop("CODEX_CANONICAL_BIN", None)


def apply_managed_runtime_home(*, env: dict[str, str], quest_root: Path, run_id: str) -> None:
    runtime_home = _managed_runtime_home(quest_root=quest_root, run_id=run_id)
    source_codex_home = _source_codex_home(env)
    runtime_codex_home = runtime_home / ".codex"
    runtime_home.mkdir(parents=True, exist_ok=True)
    _prepare_runtime_codex_home(source_codex_home=source_codex_home, runtime_codex_home=runtime_codex_home)
    env["MED_AUTOSCIENCE_MANAGED_RUNTIME_WORKER"] = "1"
    env["MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ROOT"] = str(quest_root)
    env["MED_AUTOSCIENCE_MANAGED_RUNTIME_QUEST_ID"] = quest_root.name
    env["MED_AUTOSCIENCE_MANAGED_RUNTIME_RUN_ID"] = run_id
    env["HOME"] = str(runtime_home)
    env["CODEX_HOME"] = str(runtime_codex_home)
    env["XDG_CACHE_HOME"] = str(runtime_home / ".cache")
    env["XDG_CONFIG_HOME"] = str(runtime_home / ".config")
    env["XDG_DATA_HOME"] = str(runtime_home / ".local" / "share")
    env["NPM_CONFIG_CACHE"] = str(runtime_home / ".npm")
    env["UV_CACHE_DIR"] = str(runtime_home / ".cache" / "uv")


def _host_codex_candidates(env: dict[str, str]) -> list[Path]:
    roots: list[Path] = []
    nvm_dir = _non_empty_env_path(env.get("NVM_DIR"))
    if nvm_dir is not None:
        roots.append(nvm_dir)
    home = _non_empty_env_path(env.get("HOME"))
    if home is not None:
        home_nvm = home / ".nvm"
        if all(not _same_path(home_nvm, root) for root in roots):
            roots.append(home_nvm)

    candidates: list[Path] = []
    for root in roots:
        candidates.extend(
            [
                root / "current" / "bin" / "codex",
                root / "versions" / "node" / "v22.16.0" / "bin" / "codex",
            ]
        )
        versions_root = root / "versions" / "node"
        try:
            version_candidates = sorted(
                versions_root.glob("*/bin/codex"),
                key=lambda path: path.parent.parent.name,
                reverse=True,
            )
        except OSError:
            version_candidates = []
        candidates.extend(version_candidates)
    deduped: list[Path] = []
    for candidate in candidates:
        if all(not _same_path(candidate, existing) for existing in deduped):
            deduped.append(candidate)
    return deduped


def _managed_runtime_home(*, quest_root: Path, run_id: str) -> Path:
    return quest_root / ".ds" / "codex_homes" / run_id


def _source_codex_home(env: dict[str, str]) -> Path | None:
    codex_home = _non_empty_env_path(env.get("CODEX_HOME"))
    if codex_home is not None:
        return codex_home
    home = _non_empty_env_path(env.get("HOME"))
    return home / ".codex" if home is not None else None


def _prepare_runtime_codex_home(*, source_codex_home: Path | None, runtime_codex_home: Path) -> None:
    runtime_codex_home.mkdir(parents=True, exist_ok=True)
    if source_codex_home is not None:
        _copy_codex_auth(source_codex_home=source_codex_home, runtime_codex_home=runtime_codex_home)
    _write_runtime_codex_config(source_codex_home=source_codex_home, runtime_codex_home=runtime_codex_home)


def _copy_codex_auth(*, source_codex_home: Path, runtime_codex_home: Path) -> None:
    source_auth = source_codex_home / "auth.json"
    target_auth = runtime_codex_home / "auth.json"
    if not source_auth.is_file():
        return
    if _same_path(source_auth, target_auth):
        return
    shutil.copyfile(source_auth, target_auth)
    try:
        target_auth.chmod(0o600)
    except OSError:
        pass


def _write_runtime_codex_config(*, source_codex_home: Path | None, runtime_codex_home: Path) -> None:
    source_config = _read_source_codex_config(source_codex_home=source_codex_home)
    runtime_config: dict[str, Any] = {
        key: source_config[key] for key in BACKGROUND_CODEX_CONFIG_KEYS if key in source_config
    }
    provider_name = runtime_config.get("model_provider")
    providers = source_config.get("model_providers")
    if isinstance(provider_name, str) and isinstance(providers, dict):
        provider_config = providers.get(provider_name)
        if isinstance(provider_config, dict):
            runtime_config["model_providers"] = {provider_name: provider_config}
    target_config = runtime_codex_home / "config.toml"
    target_config.write_text(_to_toml(runtime_config), encoding="utf-8")
    try:
        target_config.chmod(0o600)
    except OSError:
        pass


def _read_source_codex_config(*, source_codex_home: Path | None) -> dict[str, Any]:
    if source_codex_home is None:
        return {}
    source_config = source_codex_home / "config.toml"
    try:
        payload = tomllib.loads(source_config.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError):
        return {}
    return dict(payload)


def _to_toml(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    scalar_items = [(key, value) for key, value in payload.items() if not isinstance(value, dict)]
    table_items = [(key, value) for key, value in payload.items() if isinstance(value, dict)]
    for key, value in scalar_items:
        rendered = _toml_value(value)
        if rendered is not None:
            lines.append(f"{key} = {rendered}")
    if scalar_items and table_items:
        lines.append("")
    for table_index, (key, value) in enumerate(table_items):
        if table_index:
            lines.append("")
        _append_toml_table(lines=lines, path=(key,), payload=value)
    return "\n".join(lines).rstrip() + "\n"


def _append_toml_table(*, lines: list[str], path: tuple[str, ...], payload: dict[str, Any]) -> None:
    scalar_items = [(key, value) for key, value in payload.items() if not isinstance(value, dict)]
    table_items = [(key, value) for key, value in payload.items() if isinstance(value, dict)]
    if scalar_items:
        lines.append(f"[{'.'.join(_toml_key(part) for part in path)}]")
        for key, value in scalar_items:
            rendered = _toml_value(value)
            if rendered is not None:
                lines.append(f"{_toml_key(key)} = {rendered}")
    for key, value in table_items:
        if lines and lines[-1]:
            lines.append("")
        _append_toml_table(lines=lines, path=(*path, key), payload=value)


def _toml_key(value: str) -> str:
    if value.replace("_", "").replace("-", "").isalnum() and not value[:1].isdigit():
        return value
    return json.dumps(value)


def _toml_value(value: Any) -> str | None:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int | float) and not isinstance(value, bool):
        return str(value)
    if isinstance(value, str):
        return json.dumps(value)
    if isinstance(value, list):
        rendered_items = [_toml_value(item) for item in value]
        if any(item is None for item in rendered_items):
            return None
        return "[" + ", ".join(str(item) for item in rendered_items) + "]"
    return None


def _non_empty_env_path(value: str | None) -> Path | None:
    text = str(value or "").strip()
    return Path(text).expanduser() if text else None


def _is_executable(path: Path) -> bool:
    return path.is_file() and os.access(path, os.X_OK)


def _same_path(left: Path, right: Path) -> bool:
    try:
        return left.resolve() == right.resolve()
    except OSError:
        return left == right


__all__ = [
    "apply_managed_runtime_home",
    "preserve_host_codex_canonical_bin",
    "remove_active_python_virtualenv",
]
