from __future__ import annotations

from pathlib import Path


PUBLICATION_ROUTE_MEMORY_RELPATH = Path("memory") / "portfolio" / "research_memory" / "publication_route_memory"


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


def publication_route_memory_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / PUBLICATION_ROUTE_MEMORY_RELPATH


__all__ = [
    "PUBLICATION_ROUTE_MEMORY_RELPATH",
    "data_assets_root",
    "datasets_root",
    "literature_root",
    "portfolio_root",
    "publication_route_memory_root",
    "research_memory_root",
]
