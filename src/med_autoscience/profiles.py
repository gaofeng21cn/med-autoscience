from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import tomllib


@dataclass(frozen=True)
class WorkspaceProfile:
    name: str
    workspace_root: Path
    runtime_root: Path
    studies_root: Path
    portfolio_root: Path
    deepscientist_runtime_root: Path
    default_publication_profile: str
    default_citation_style: str


def load_profile(path: str | Path) -> WorkspaceProfile:
    profile_path = Path(path).expanduser().resolve()
    payload = tomllib.loads(profile_path.read_text(encoding="utf-8"))
    return WorkspaceProfile(
        name=str(payload["name"]),
        workspace_root=Path(payload["workspace_root"]).expanduser().resolve(),
        runtime_root=Path(payload["runtime_root"]).expanduser().resolve(),
        studies_root=Path(payload["studies_root"]).expanduser().resolve(),
        portfolio_root=Path(payload["portfolio_root"]).expanduser().resolve(),
        deepscientist_runtime_root=Path(payload["deepscientist_runtime_root"]).expanduser().resolve(),
        default_publication_profile=str(payload["default_publication_profile"]),
        default_citation_style=str(payload["default_citation_style"]),
    )

