from __future__ import annotations

import os
from pathlib import Path
from shutil import which


TOOLUNIVERSE_ROLES = (
    "知识检索",
    "功能分析",
    "通路与调控解释",
)


def _resolve_root(*, workspace_root: Path | None, tooluniverse_root: Path | None) -> tuple[Path | None, str | None]:
    if tooluniverse_root is not None:
        return tooluniverse_root, "explicit"

    env_root = os.environ.get("TOOLUNIVERSE_ROOT")
    if env_root:
        return Path(env_root), "env"

    if workspace_root is not None:
        candidate = workspace_root / "ops" / "framework_refs" / "_repo_compare" / "ToolUniverse"
        if candidate.exists():
            return candidate, "workspace_reference"

    return None, None


def detect_tooluniverse(
    *,
    workspace_root: Path | None = None,
    tooluniverse_root: Path | None = None,
) -> dict[str, object]:
    resolved_root, root_source = _resolve_root(workspace_root=workspace_root, tooluniverse_root=tooluniverse_root)
    commands = {
        "tooluniverse": which("tooluniverse"),
        "tooluniverse-mcp": which("tooluniverse-mcp"),
        "tu": which("tu"),
    }
    available = (resolved_root is not None and resolved_root.exists()) or any(commands.values())
    return {
        "available": bool(available),
        "workspace_root": str(workspace_root) if workspace_root is not None else None,
        "root": str(resolved_root) if resolved_root is not None and resolved_root.exists() else None,
        "root_source": root_source if resolved_root is not None and resolved_root.exists() else None,
        "commands": commands,
        "roles": list(TOOLUNIVERSE_ROLES),
    }
