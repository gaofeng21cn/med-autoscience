from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_authority_snapshot, study_progress, study_truth_kernel
from med_autoscience.controllers.study_runtime_types import ProgressProjectionStatus


def attach_status_read_model_projections(
    *,
    status: ProgressProjectionStatus,
    profile: Any,
    study_id: str,
    study_root: Path,
    recorded_at: str,
    entry_mode: str | None,
    include_progress_projection: bool,
) -> None:
    """Attach generic read-model snapshots after MAS authority has produced status refs."""
    status.extras["study_truth_snapshot"] = study_truth_kernel.derive_truth_snapshot_from_status_payload(
        study_root=study_root,
        study_id=study_id,
        status_payload=status.to_dict(),
        recorded_at=recorded_at,
    )
    status.extras["authority_snapshot"] = domain_authority_snapshot.build_authority_snapshot(
        status.to_dict()
    )
    if include_progress_projection:
        status.record_progress_projection(
            study_progress.build_study_progress_projection(
                profile=profile,
                study_id=study_id,
                study_root=study_root,
                status_payload=status,
                entry_mode=entry_mode,
            )
        )


__all__ = [name for name in globals() if not name.startswith("__")]
