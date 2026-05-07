from __future__ import annotations

from pathlib import Path
from typing import Any


def candidate_values_include_root(
    *,
    workspace_root: Path,
    candidate_values: list[object],
    root: Path,
    submission_minimal_controller: Any,
) -> bool:
    root_resolved = root.resolve()
    for candidate in candidate_values:
        if not isinstance(candidate, str):
            continue
        normalized = candidate.strip()
        if not normalized:
            continue
        try:
            submission_minimal_controller.resolve_relpath(workspace_root, normalized).resolve().relative_to(
                root_resolved
            )
        except ValueError:
            continue
        return True
    return False
