from __future__ import annotations

from pathlib import Path


PUBLICATION_ROUTE_MEMORY_RELPATH = Path("memory") / "portfolio" / "research_memory" / "publication_route_memory"
DATASETS_RELPATH = Path("data") / "datasets"
DATA_ASSETS_RELPATH = Path("memory") / "portfolio" / "data_assets"
DATA_ASSET_LAYER_IDS = (
    "restricted_raw",
    "deidentified_linkage",
    "master",
    "deidentified_longitudinal",
    "standardized_longitudinal",
    "external",
)
DATA_ASSET_REGISTRY_DIRECTORY_RELPATHS = (
    Path("private"),
    Path("public"),
    Path("impact"),
    Path("startup"),
    Path("mutations"),
    Path("lineage"),
)


def datasets_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / DATASETS_RELPATH


def portfolio_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / "memory" / "portfolio"


def data_assets_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / DATA_ASSETS_RELPATH


def data_asset_lineage_root(workspace_root: Path) -> Path:
    return data_assets_root(workspace_root) / "lineage"


def research_memory_root(workspace_root: Path) -> Path:
    return portfolio_root(workspace_root) / "research_memory"


def literature_root(workspace_root: Path) -> Path:
    return research_memory_root(workspace_root) / "literature"


def publication_route_memory_root(workspace_root: Path) -> Path:
    return Path(workspace_root).expanduser().resolve() / PUBLICATION_ROUTE_MEMORY_RELPATH


__all__ = [
    "DATA_ASSET_LAYER_IDS",
    "DATA_ASSET_REGISTRY_DIRECTORY_RELPATHS",
    "DATA_ASSETS_RELPATH",
    "DATASETS_RELPATH",
    "PUBLICATION_ROUTE_MEMORY_RELPATH",
    "data_asset_lineage_root",
    "data_assets_root",
    "datasets_root",
    "literature_root",
    "portfolio_root",
    "publication_route_memory_root",
    "research_memory_root",
]
