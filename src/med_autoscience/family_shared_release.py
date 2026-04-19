from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience import editable_shared_bootstrap as _editable_shared_bootstrap

_editable_shared_bootstrap.ensure_editable_dependency_paths()

from opl_harness_shared.family_shared_release import (  # noqa: E402
    inspect_current_repo_family_shared_alignment as _inspect_current_repo_family_shared_alignment,
)


FAMILY_SHARED_CONSUMER_REPO_ID = "medautoscience"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def inspect_current_repo_family_shared_alignment(
    *,
    repo_root_override: Path | str | None = None,
    owner_repo_root: Path | str | None = None,
    owner_repo: str = "one-person-lab",
) -> dict[str, Any]:
    resolved_repo_root = Path(repo_root_override).expanduser().resolve() if repo_root_override else repo_root()
    return _inspect_current_repo_family_shared_alignment(
        repo_root=resolved_repo_root,
        consumer_repo_id=FAMILY_SHARED_CONSUMER_REPO_ID,
        owner_repo_root=owner_repo_root,
        owner_repo=owner_repo,
    )
