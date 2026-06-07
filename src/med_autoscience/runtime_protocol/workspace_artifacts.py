from __future__ import annotations

from pathlib import Path


def workspace_runtime_artifacts_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / "runtime" / "artifacts"


def workspace_runtime_artifact_path(workspace_root: Path, *parts: str) -> Path:
    return workspace_runtime_artifacts_root(workspace_root).joinpath(*parts)


def workspace_runtime_artifact_relative_path(*parts: str) -> Path:
    return Path("runtime", "artifacts", *parts)


__all__ = [
    "workspace_runtime_artifact_path",
    "workspace_runtime_artifact_relative_path",
    "workspace_runtime_artifacts_root",
]
