from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import paper_authority_migration
from med_autoscience.runtime_protocol import resolve_study_root_from_paper_root


def pending_clean_migration_blocker(*, study_root: Path) -> dict[str, Any] | None:
    resolved_study_root = Path(study_root).expanduser().resolve()
    if not paper_authority_migration.cutover_requires_ai_reviewer(study_root=resolved_study_root):
        return None
    receipt_path = paper_authority_migration.paper_authority_cutover_latest_path(study_root=resolved_study_root)
    receipt = paper_authority_migration.read_paper_authority_cutover(study_root=resolved_study_root) or {}
    return {
        "status": "paper_authority_clean_migration_pending",
        "blocked_reason": "paper_authority_clean_migration_required",
        "next_owner": "ai_reviewer",
        "paper_authority_cutover_ref": str(receipt_path),
        "cutover_status": _text(receipt.get("status")) or "missing_or_stale",
        "blocked_surfaces": [
            "paper/submission_minimal",
            "manuscript/delivery_manifest.json",
            "manuscript/current_package",
            "manuscript/current_package.zip",
            "artifacts/controller/current_package_freshness/latest.json",
        ],
        "required_next_actions": ["return_to_ai_reviewer_workflow", "publication_gate", "sync_study_delivery"],
    }


def delivery_write_blocked(*, study_root: Path) -> bool:
    return pending_clean_migration_blocker(study_root=study_root) is not None


def study_root_for_paper_delivery(*, paper_root: Path) -> Path:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    try:
        _study_id, study_root = resolve_study_root_from_paper_root(resolved_paper_root)
    except (FileNotFoundError, ValueError):
        return resolved_paper_root.parent
    return Path(study_root).expanduser().resolve()


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "delivery_write_blocked",
    "pending_clean_migration_blocker",
    "study_root_for_paper_delivery",
]
