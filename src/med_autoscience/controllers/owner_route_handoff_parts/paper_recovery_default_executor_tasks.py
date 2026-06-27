from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile


def paper_recovery_default_executor_dispatch_tasks(
    *,
    current_progress: Mapping[str, Any],
    profile: WorkspaceProfile,
    profile_ref: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    """Retired PaperRecovery no-op diagnostic surface.

    PaperRecovery no longer materializes ordinary
    ``domain_owner/default-executor-dispatch`` tasks. The replacement default
    paper entry is ``paper_mission/start_or_resume`` from the domain-handler
    export, and this helper must not claim paper progress, provider admission,
    or current task ownership.
    """
    return []


__all__ = ["paper_recovery_default_executor_dispatch_tasks"]
