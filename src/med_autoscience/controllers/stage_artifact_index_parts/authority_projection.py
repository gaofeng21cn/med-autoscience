from __future__ import annotations

from pathlib import Path
from typing import Any


def provider_liveness(*, study_root: Path) -> dict[str, Any]:
    runtime_ref = study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    return {
        "runtime_ref": str(runtime_ref),
        "runtime_ref_exists": runtime_ref.exists(),
        "provider_completion_is_paper_progress": False,
        "paper_progress_source": "stage_artifact_index",
    }


def stale_platform_repairs(*, study_root: Path, stages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    has_artifact_delta = any(
        stage["observed_artifact_refs"] or stage.get("legacy_observed_artifact_refs")
        for stage in stages
    )
    if not has_artifact_delta:
        return []
    candidates = (
        ("controller_decisions/latest.json", study_root / "artifacts" / "controller_decisions" / "latest.json"),
        ("publication_eval/latest.json", study_root / "artifacts" / "publication_eval" / "latest.json"),
        (
            "runtime/provider_liveness",
            study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",
        ),
    )
    return [
        {
            "source": source,
            "ref": str(path),
            "reason": "artifact_delta_takes_precedence_over_platform_currentness",
            "counts_as_paper_progress": False,
        }
        for source, path in candidates
        if path.exists()
    ]


def authority_boundary() -> dict[str, Any]:
    return {
        "mas_authority_functions": mas_authority_functions(),
        "artifact_first_can_determine_stage_progress": True,
        "can_write_mas_truth": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_readiness": False,
        "can_authorize_submission_readiness": False,
        "provider_completion_is_paper_progress": False,
    }


def mas_authority_functions() -> list[str]:
    return [
        "study_truth",
        "source_readiness",
        "reviewer_quality",
        "publication_gate",
        "artifact_package_authority",
        "memory_accept_reject",
        "typed_blocker",
        "medical_owner_receipt",
    ]
