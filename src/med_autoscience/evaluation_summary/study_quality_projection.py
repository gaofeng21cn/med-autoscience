from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.publication_eval_latest import stable_publication_eval_latest_path

from .refs_and_validation import (
    _required_bool,
    _required_choice,
    _required_string_list,
    _required_text,
)


def normalized_study_quality_assessment_provenance(
    study_quality_truth: dict[str, Any],
    *,
    study_root: Path,
) -> dict[str, Any]:
    provenance = (
        dict(study_quality_truth.get("assessment_provenance") or {})
        if isinstance(study_quality_truth.get("assessment_provenance"), dict)
        else None
    )
    if provenance is None:
        return {
            "owner": "mechanical_projection",
            "source_kind": "legacy_study_quality_projection",
            "policy_id": "publication_gate_projection_v1",
            "source_refs": [str(stable_publication_eval_latest_path(study_root=study_root))],
            "ai_reviewer_required": True,
        }
    return {
        "owner": _required_choice(
            "evaluation summary study_quality_truth assessment_provenance",
            "owner",
            provenance.get("owner"),
            frozenset({"mechanical_projection", "ai_reviewer"}),
        ),
        "source_kind": _required_text(
            "evaluation summary study_quality_truth assessment_provenance",
            "source_kind",
            provenance.get("source_kind"),
        ),
        "policy_id": _required_text(
            "evaluation summary study_quality_truth assessment_provenance",
            "policy_id",
            provenance.get("policy_id"),
        ),
        "source_refs": _required_string_list(
            "evaluation summary study_quality_truth assessment_provenance",
            "source_refs",
            provenance.get("source_refs"),
        ),
        "ai_reviewer_required": _required_bool(
            "evaluation summary study_quality_truth assessment_provenance",
            "ai_reviewer_required",
            provenance.get("ai_reviewer_required"),
        ),
    }
