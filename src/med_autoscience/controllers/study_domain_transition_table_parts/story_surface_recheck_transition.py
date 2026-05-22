from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.quality_repair_batch_parts import story_surface_delta
from med_autoscience.controllers.study_domain_transition_table_parts import publication_gate_lifecycle_transitions

REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH = Path("artifacts/controller/repair_execution_evidence/latest.json")


def project_transition(
    *,
    study_root: Path,
    study_id: str,
    lifecycle: Mapping[str, Any],
    lifecycle_ref: str | None,
    publication_eval: Mapping[str, Any],
    source_refs: list[str],
    completion_receipt_consumption: Mapping[str, Any],
) -> dict[str, Any] | None:
    root = Path(study_root).expanduser().resolve()
    story_recheck_transition = _story_surface_ai_reviewer_recheck_transition(
        study_root=root,
        study_id=study_id,
        lifecycle=lifecycle,
        publication_eval=publication_eval,
        source_refs=source_refs,
        completion_receipt_consumption=completion_receipt_consumption,
    )
    if story_recheck_transition is not None:
        return story_recheck_transition
    return publication_gate_lifecycle_transitions.project_transition(
        study_root=root,
        study_id=study_id,
        lifecycle=lifecycle,
        lifecycle_ref=lifecycle_ref,
        publication_eval=publication_eval,
        source_refs=source_refs,
        completion_receipt_consumption=completion_receipt_consumption,
    )


def _story_surface_ai_reviewer_recheck_transition(
    *,
    study_root: Path,
    study_id: str,
    lifecycle: Mapping[str, Any],
    publication_eval: Mapping[str, Any],
    source_refs: list[str],
    completion_receipt_consumption: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not story_surface_delta.ai_reviewer_recheck_supersedes_lifecycle(
        study_root=study_root,
        lifecycle=lifecycle,
        publication_eval=publication_eval,
        repair_evidence_path=study_root / REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH,
    ):
        return None
    return story_surface_delta.ai_reviewer_recheck_action_from_story_delta(
        study_id=study_id,
        source_refs=source_refs,
        completion_receipt_consumption=completion_receipt_consumption,
    )


__all__ = ["REPAIR_EXECUTION_EVIDENCE_RELATIVE_PATH", "project_transition"]
