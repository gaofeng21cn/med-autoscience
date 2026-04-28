from __future__ import annotations

import os
from pathlib import Path
import shlex


def _read_optional_config_env_value(*, path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        lhs, rhs = stripped.split("=", 1)
        normalized_key = lhs.removeprefix("export ").strip()
        if normalized_key != key:
            continue
        value = rhs.strip()
        if not value:
            raise ValueError(f"{key} is empty in {path}")
        try:
            tokens = shlex.split(value, posix=True)
        except ValueError as exc:
            raise ValueError(f"invalid {key} assignment in {path}") from exc
        if len(tokens) != 1 or not tokens[0].strip():
            raise ValueError(f"{key} must resolve to one absolute path in {path}")
        return tokens[0].strip()
    return None


def _read_config_env_value(*, path: Path, key: str) -> str:
    value = _read_optional_config_env_value(path=path, key=key)
    if value is not None:
        return value
    if not path.exists():
        raise FileNotFoundError(f"missing med-deepscientist launcher config: {path}")
    raise ValueError(f"{key} is not configured in {path}")


def _read_launcher_text(*, launcher_path: Path) -> str | None:
    try:
        return launcher_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _launcher_looks_like_python_console_script(*, launcher_path: Path) -> bool:
    launcher_text = _read_launcher_text(launcher_path=launcher_path)
    if not launcher_text:
        return False
    return "from deepscientist.cli import main" in launcher_text


def _repo_root_from_repo_local_venv_path(*, path: Path) -> Path | None:
    resolved_path = Path(path).expanduser().resolve()
    if resolved_path.parent.name != "bin":
        return None
    venv_root = resolved_path.parent.parent
    if venv_root.name != ".venv":
        return None
    return venv_root.parent


def _companion_js_launcher_path(*, launcher_path: Path) -> Path | None:
    repo_root = _repo_root_from_repo_local_venv_path(path=launcher_path)
    if repo_root is None:
        return None
    candidate = repo_root / "bin" / "ds.js"
    if not candidate.exists():
        return None
    return candidate.resolve()


def _resolve_launcher_path(*, runtime_root: Path) -> Path:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    launcher_value = _read_config_env_value(
        path=resolved_runtime_root.parent / "config.env",
        key="MED_DEEPSCIENTIST_LAUNCHER",
    )
    launcher_path = Path(launcher_value).expanduser()
    if not launcher_path.is_absolute():
        raise ValueError(f"MED_DEEPSCIENTIST_LAUNCHER must be an absolute path: {launcher_value}")
    resolved_launcher_path = launcher_path.resolve()
    if not resolved_launcher_path.exists():
        raise FileNotFoundError(f"med-deepscientist launcher does not exist: {resolved_launcher_path}")
    if _launcher_looks_like_python_console_script(launcher_path=resolved_launcher_path):
        companion_launcher_path = _companion_js_launcher_path(launcher_path=resolved_launcher_path)
        if companion_launcher_path is None:
            raise ValueError(
                "MED_DEEPSCIENTIST_LAUNCHER points to a Python DeepScientist console script, "
                "but no compatible repo-local bin/ds.js launcher was found"
            )
        return companion_launcher_path
    return resolved_launcher_path


def _launcher_requires_node(*, launcher_path: Path) -> bool:
    launcher_text = _read_launcher_text(launcher_path=launcher_path)
    if not launcher_text:
        return False
    first_line = launcher_text.splitlines()[0] if launcher_text.splitlines() else ""
    if not first_line.startswith("#!"):
        return False
    return "node" in first_line


def _resolve_launcher_node_binary(*, runtime_root: Path) -> str | None:
    configured_node = str(os.environ.get("MED_AUTOSCIENCE_NODE_BIN") or "").strip()
    if not configured_node:
        workspace_root = Path(runtime_root).expanduser().resolve().parents[2]
        configured_value = _read_optional_config_env_value(
            path=workspace_root / "ops" / "medautoscience" / "config.env",
            key="MED_AUTOSCIENCE_NODE_BIN",
        )
        configured_node = str(configured_value or "").strip()
    if not configured_node:
        return None
    if not os.path.isabs(configured_node):
        raise ValueError(f"MED_AUTOSCIENCE_NODE_BIN must be an absolute path: {configured_node}")
    if not os.access(configured_node, os.X_OK):
        raise ValueError(f"MED_AUTOSCIENCE_NODE_BIN is not executable: {configured_node}")
    return configured_node


def _launcher_command(*, runtime_root: Path, args: tuple[str, ...]) -> list[str]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    launcher_path = _resolve_launcher_path(runtime_root=resolved_runtime_root)
    if _launcher_requires_node(launcher_path=launcher_path):
        node_binary = _resolve_launcher_node_binary(runtime_root=resolved_runtime_root)
        if node_binary:
            return [node_binary, str(launcher_path), "--home", str(resolved_runtime_root), *args]
    return [str(launcher_path), "--home", str(resolved_runtime_root), *args]

