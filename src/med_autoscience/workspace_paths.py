from __future__ import annotations

from pathlib import Path


def datasets_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / "data" / "datasets"


def portfolio_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / "memory" / "portfolio"


def data_assets_root(workspace_root: Path) -> Path:
    return portfolio_root(workspace_root) / "data_assets"


def research_memory_root(workspace_root: Path) -> Path:
    return portfolio_root(workspace_root) / "research_memory"


def literature_root(workspace_root: Path) -> Path:
    return research_memory_root(workspace_root) / "literature"


__all__ = [
    "data_assets_root",
    "datasets_root",
    "literature_root",
    "portfolio_root",
    "research_memory_root",
]
