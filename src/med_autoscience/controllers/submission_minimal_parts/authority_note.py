from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .shared import (
    relpath_from_workspace,
    remap_staging_path_to_target,
    write_text,
)


FORBIDDEN_STUDY_ANCHOR_PATTERNS = (
    ("geo_accession", re.compile(r"\bGSE\d{3,}\b", flags=re.IGNORECASE)),
    ("cohort_or_dataset_claim", re.compile(r"\b(?:cohort|dataset|series)\b", flags=re.IGNORECASE)),
    ("phenotype_or_label_claim", re.compile(r"\b(?:phenotype|invasiveness|labeled)\b", flags=re.IGNORECASE)),
)


def build_submission_source_authority_note(
    *,
    canonical_full_surface: str,
    submission_projection: str,
    manifest_surface: str,
) -> str:
    return (
        "Package authority note for the minimal submission bundle; not the full manuscript surface.\n\n"
        f"Canonical full manuscript surface: {canonical_full_surface}.\n"
        f"Export-ready submission projection: {submission_projection}.\n"
        f"Manifest and source signature surface: {manifest_surface}.\n\n"
        "Projection role: human-facing delivery metadata only. Scientific quality closure and submission readiness "
        "still require an AI reviewer-backed quality record, a clear publication gate, a current source signature, "
        "and a fresh package projection.\n\n"
        "Paper content revisions belong in controller-authorized canonical paper sources followed by MAS export/sync/QC.\n"
    )


def write_submission_source_authority_note(
    *,
    output_path: Path,
    source_markdown_path: Path,
    compiled_markdown_path: Path,
    staging_root: Path,
    target_root: Path,
    workspace_root: Path,
) -> None:
    canonical_full_surface = relpath_from_workspace(compiled_markdown_path, workspace_root)
    submission_projection = relpath_from_workspace(
        remap_staging_path_to_target(
            path=source_markdown_path,
            staging_root=staging_root,
            target_root=target_root,
        ),
        workspace_root,
    )
    manifest_surface = (
        f"{relpath_from_workspace(target_root / 'submission_manifest.json', workspace_root)}#source_signature"
    )
    write_text(
        output_path,
        build_submission_source_authority_note(
            canonical_full_surface=canonical_full_surface,
            submission_projection=submission_projection,
            manifest_surface=manifest_surface,
        ),
    )


def inspect_submission_source_authority_note(path: Path) -> dict[str, Any]:
    if not path.exists() or not path.is_file():
        return {
            "exists": False,
            "role_clarity_pass": False,
            "is_full_manuscript_surface": False,
            "forbidden_study_anchor_hits": [],
            "heading_count": 0,
        }
    text = path.read_text(encoding="utf-8")
    lowered = text.lower()
    heading_count = sum(1 for line in text.splitlines() if line.lstrip().startswith("#"))
    forbidden_hits = [name for name, pattern in FORBIDDEN_STUDY_ANCHOR_PATTERNS if pattern.search(text)]
    role_markers = (
        "authority note",
        "not the full manuscript",
        "canonical full manuscript surface",
        "export-ready submission projection",
        "source signature",
    )
    role_clarity_pass = all(marker in lowered for marker in role_markers) and not forbidden_hits
    return {
        "exists": True,
        "role": "authority_note",
        "role_clarity_pass": role_clarity_pass,
        "is_full_manuscript_surface": False,
        "forbidden_study_anchor_hits": forbidden_hits,
        "heading_count": heading_count,
    }


def attach_submission_source_authority_note_qc(
    surface_qc: dict[str, Any],
    *,
    authority_note_path: Path | None,
) -> dict[str, Any]:
    if authority_note_path is None:
        return surface_qc
    updated = dict(surface_qc)
    failures = list(updated.get("failures") or [])
    inspection = inspect_submission_source_authority_note(authority_note_path)
    updated["authority_note"] = inspection
    if not inspection["exists"] or not inspection["role_clarity_pass"]:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "source_authority_note",
                "descriptor": authority_note_path.name,
                "qc_profile": updated.get("qc_profile") or "submission_manuscript_surface",
                "failure_reason": "submission_source_authority_note_role_unclear",
                "audit_classes": ["manuscript_surface", "authority_boundary"],
            }
        )
    if inspection["forbidden_study_anchor_hits"]:
        failures.append(
            {
                "collection": "manuscript",
                "item_id": "source_authority_note",
                "descriptor": authority_note_path.name,
                "qc_profile": updated.get("qc_profile") or "submission_manuscript_surface",
                "failure_reason": "submission_source_authority_note_study_specific_hardcoding",
                "audit_classes": ["manuscript_surface", "authority_boundary"],
                "forbidden_study_anchor_hits": inspection["forbidden_study_anchor_hits"],
            }
        )
    updated["failures"] = failures
    updated["status"] = "fail" if failures else "pass"
    return updated
