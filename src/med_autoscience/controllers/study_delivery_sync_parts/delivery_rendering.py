from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.submission_package_layout import SUBMISSION_PACKAGE_LAYOUT_VERSION
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)


def build_submission_package_readme(*, study_id: str, stage: str, publication_profile: str) -> str:
    normalized_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")
    if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return (
            f"# Submission Package\n\n"
            f"- Study: `{study_id}`\n"
            f"- Sync stage: `{stage}`\n"
            f"- Contents:\n"
            f"  - `manuscript.docx`\n"
            f"  - `paper.pdf`\n"
            f"  - `audit/submission_manifest.json`\n"
            f"  - `audit/evidence_ledger.json`\n"
            f"  - `reproducibility/source_signature.json`\n"
            f"  - `figures/`\n"
            f"  - `tables/`\n\n"
            f"This directory is assembled automatically during study delivery sync so the manuscript and submission assets can be reviewed or handed off as one package.\n"
        )
    return (
        f"# Journal Submission Package\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{stage}`\n"
        f"- Publication profile: `{normalized_profile}`\n"
        f"- Contents:\n"
        f"  - `manuscript.docx`\n"
        f"  - `paper.pdf`\n"
        f"  - `audit/submission_manifest.json`\n"
        f"  - `audit/evidence_ledger.json`\n"
        f"  - `reproducibility/source_signature.json`\n"
        f"  - `Supplementary_Material.docx` (when generated)\n"
        f"  - `figures/`\n"
        f"  - `tables/`\n\n"
        f"This journal-specific package is assembled automatically so the target-journal version can coexist with the generic final delivery.\n"
    )


def build_general_delivery_readme(*, study_id: str, stage: str, source_relative_root: str) -> str:
    return (
        f"# Study Final Delivery\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{stage}`\n"
        f"- Canonical authority surface: `paper/`\n"
        f"- Controller-authorized package source: `{source_relative_root}/`\n"
        f"- This directory: `manuscript/` (human-facing delivery root)\n"
        f"- Stable human-facing entry: `manuscript/current_package/`\n"
        f"- Delivery manifest: `manuscript/delivery_manifest.json`\n\n"
        f"This directory is refreshed automatically from the controller-authorized paper package. "
        f"Humans should open `manuscript/current_package/`, not reconstruct stage-specific paths.\n"
    )


def _submission_delivery_stale_reason_label(stale_reason: str | None) -> str:
    normalized = str(stale_reason or "").strip()
    if normalized == "current_submission_source_missing":
        return "the current authority submission package has not been materialized"
    if normalized == "delivery_manifest_sources_missing":
        return "the recorded mirror still references sources that no longer exist"
    if normalized == "delivery_manifest_source_mismatch":
        return "the recorded mirror points at a different authority package root"
    if normalized == "delivery_manifest_source_changed":
        return "the authority submission package changed after the mirror was last synced"
    if normalized == "delivery_projection_missing":
        return "the stage-neutral current package projection has not been materialized yet"
    return normalized or "the current authority submission package is unavailable"


def build_unavailable_general_delivery_readme(
    *,
    study_id: str,
    stale_reason: str | None,
    source_relative_root: str,
) -> str:
    return (
        "# Study Final Delivery Unavailable\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: current submission package mirror is unavailable\n"
        f"- Reason: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/`\n"
        f"- Expected package root inside the authority surface: `{source_relative_root}/`\n"
        "- Human-facing delivery root: `manuscript/`\n\n"
        "This directory was cleared because the previous study-level mirror became stale. "
        "Wait for a fresh submission-minimal export before treating anything under `manuscript/` as the current package.\n"
    )


def build_preview_general_delivery_readme(
    *,
    study_id: str,
    stale_reason: str | None,
    source_relative_root: str,
) -> str:
    return (
        "# Study Delivery Audit Preview\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: audit preview only; not submission-ready\n"
        f"- Reason formal delivery is blocked: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/`\n"
        f"- Expected package root inside the authority surface: `{source_relative_root}/`\n"
        "- Human-facing review root: `manuscript/`\n\n"
        "This directory now exposes the latest auditable manuscript-facing materials that are still available from the authority surface. "
        "Treat it as a user review package only, not as a handoff-ready submission package.\n"
    )


def build_manuscript_root_readme() -> str:
    return (
        "# Manuscript Delivery Surface\n\n"
        "- Canonical authority surface: `paper/`\n"
        "- Human-facing delivery root: `manuscript/`\n"
        "- Stable human-facing package entry: `manuscript/current_package/`\n"
        "- Delivery manifest: `manuscript/delivery_manifest.json`\n\n"
        "Use `manuscript/` when a human needs the latest handoff-ready manuscript bundle. "
        "Edit or regenerate from `paper/`, not from this mirror.\n"
    )


def build_artifacts_root_readme() -> str:
    return (
        "# Artifact Auxiliary Surface\n\n"
        "- Canonical authority surface: `paper/`\n"
        "- Human-facing final delivery surface: `manuscript/`\n"
        "- This directory is reserved for machine-generated auxiliary/runtime/finalization evidence.\n"
        "- Figures/tables are no longer mirrored here during normal submission sync.\n\n"
        "Use `manuscript/` for the latest handoff-ready package. `artifacts/` is not part of the human-facing final delivery surface; touch it only when a runtime/finalize contract explicitly asks for auxiliary evidence.\n"
    )


def build_artifacts_finalize_readme(*, study_id: str, stage: str) -> str:
    return (
        f"# Finalization Evidence Surface\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{stage}`\n"
        "- This directory is not part of the human-facing final delivery surface.\n"
        "- Expected contents: finalize/manuscript build evidence such as `paper_bundle_manifest.json` and `compile_report.json`.\n"
        "- Stable human-facing package entry remains `manuscript/current_package/`.\n"
        "- Figures/tables remain in `manuscript/current_package/` for human review, and in `paper/` as authority.\n\n"
        "Use this directory only for machine-generated finalization evidence only, not for human-facing display lookup.\n"
    )


def build_unavailable_submission_package_readme(*, study_id: str, stale_reason: str | None) -> str:
    return (
        "# Submission Package Unavailable\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: current submission package mirror is unavailable\n"
        f"- Reason: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/submission_minimal/`\n"
        "- This directory no longer represents a current handoff-ready package.\n\n"
        "The previous mirror was cleared because the active authority package disappeared or no longer matches. "
        "Wait for a fresh submission-minimal export before using this path for review or handoff.\n"
    )


def build_submission_package_audit_preview_readme(*, study_id: str, stale_reason: str | None) -> str:
    return (
        "# Submission Package Audit Preview\n\n"
        f"- Study: `{study_id}`\n"
        "- Status: audit preview only; not submission-ready\n"
        f"- Reason formal delivery is blocked: {_submission_delivery_stale_reason_label(stale_reason)}\n"
        "- Canonical authority surface: `paper/`\n"
        "- This package mirrors the latest still-available manuscript, figure, table, and audit materials for human review.\n"
        "- Do not treat this directory as the formal submission handoff until a fresh `submission_minimal` export is materialized.\n"
    )


def build_delivery_surface_roles(
    *,
    paper_root: Path,
    source_root: Path,
    manuscript_root: Path | None = None,
    current_package_root: Path | None = None,
    current_package_zip: Path | None = None,
    auxiliary_evidence_root: Path | None = None,
    journal_submission_mirror_root: Path | None = None,
) -> dict[str, str | None]:
    return {
        "controller_authorized_paper_root": str(paper_root),
        "controller_authorized_package_source_root": str(source_root),
        "human_facing_delivery_root": str(manuscript_root) if manuscript_root is not None else None,
        "human_facing_current_package_root": str(current_package_root) if current_package_root is not None else None,
        "human_facing_current_package_zip": str(current_package_zip) if current_package_zip is not None else None,
        "auxiliary_evidence_root": str(auxiliary_evidence_root) if auxiliary_evidence_root is not None else None,
        "journal_submission_mirror_root": (
            str(journal_submission_mirror_root) if journal_submission_mirror_root is not None else None
        ),
    }


def build_promoted_delivery_readme(*, study_id: str, publication_profile: str, source_relative_root: str) -> str:
    return (
        f"# Study Final Delivery\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{publication_profile}_submission`\n"
        f"- Publication profile: `{publication_profile}`\n"
        f"- Controller-authorized package source: `{source_relative_root}/`\n"
        f"- Contents:\n"
        f"  - `manuscript.docx`\n"
        f"  - `paper.pdf`\n"
        f"  - `audit/submission_manifest.json`\n"
        f"  - `audit/evidence_ledger.json`\n"
        f"  - `reproducibility/source_signature.json`\n"
        f"  - `Supplementary_Material.docx` (when generated)\n"
        f"  - `current_package/`\n"
        f"  - `current_package.zip`\n"
        f"  - `journal_package_mirrors/{publication_profile}/`\n\n"
        f"This study-level final delivery is assembled automatically from the primary journal package so the canonical shallow handoff stays aligned with the active target-journal surface.\n"
    )


def ensure_manuscript_root_readme(*, manuscript_root: Path) -> None:
    from .delivery_io import write_text

    readme_path = manuscript_root / "README.md"
    if readme_path.exists():
        return
    write_text(readme_path, build_manuscript_root_readme())


FRONT_MATTER_LABELS = {
    "authors": "Authors",
    "affiliations": "Affiliations",
    "corresponding_author": "Corresponding author",
    "funding": "Funding",
    "conflict_of_interest": "Conflict of interest",
    "ethics": "Ethics",
    "data_availability": "Data availability",
}
METADATA_CLOSEOUT_LABELS = {
    "objective_metadata_closeout": "Objective metadata closeout",
    "journal_template_page_proof": "Journal template page proof",
}


def _humanize_submission_field(field_name: str) -> str:
    return FRONT_MATTER_LABELS.get(field_name, field_name.replace("_", " ").capitalize())


def _humanize_metadata_closeout_item(item_key: str) -> str:
    return METADATA_CLOSEOUT_LABELS.get(item_key, item_key.replace("_", " ").capitalize())


def _is_pending_submission_item(value: Any) -> bool:
    if value is None:
        return True
    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"", "pending", "missing", "todo", "tbd", "unknown", "required"}
    return False


def build_submission_todo_from_manifest(*, manifest_path: Path) -> str | None:
    if not manifest_path.exists():
        return None
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    placeholders = manifest.get("front_matter_placeholders")
    pending_items: list[tuple[str, str]] = []
    if isinstance(placeholders, dict):
        pending_items.extend(
            [
                (_humanize_submission_field(str(key)), "pending" if value is None else str(value).strip() or "pending")
                for key, value in sorted(placeholders.items())
                if _is_pending_submission_item(value)
            ]
        )
    if not pending_items:
        metadata_closeout = manifest.get("metadata_closeout")
        if isinstance(metadata_closeout, dict):
            followups = metadata_closeout.get("non_blocking_followups")
            if isinstance(followups, list):
                for item in followups:
                    if not isinstance(item, dict):
                        continue
                    key = str(item.get("key") or "").strip()
                    if not key:
                        continue
                    followup_status = str(item.get("status") or "").strip()
                    notes = str(item.get("notes") or "").strip()
                    if not followup_status and not notes:
                        continue
                    if followup_status in {"done", "completed", "not_applicable", "clear"}:
                        continue
                    pending_items.append(
                        (
                            _humanize_metadata_closeout_item(key),
                            notes or followup_status.replace("_", " "),
                        )
                    )
    if not pending_items:
        return None
    lines = [
        "# Submission TODO",
        "",
        "These items are administrative/front-matter handoff tasks. They are listed here so the current package can be reviewed for scientific audit while formal submission details are completed.",
        "",
        "Pending items:",
    ]
    lines.extend(f"- {label}: {status}" for label, status in pending_items)
    lines.append("")
    return "\n".join(lines)


def build_current_package_readme(
    *,
    study_id: str,
    stage: str,
    source_relative_root: str,
    status_line: str,
    charter_contract_linkage: dict[str, Any] | None = None,
) -> str:
    lines = [
        "# Current Human Package",
        "",
        f"- Study: `{study_id}`",
        f"- Active sync stage: `{stage}`",
        f"- Status: {status_line}",
        "- current_package/ is a human-facing mirror, not an edit source.",
        "",
        "## Submission files",
        "",
        "- Open this directory for the latest human-facing manuscript package.",
        "- Expected primary files: `manuscript.docx`, `paper.pdf`, `figures/`, and `tables/` when present.",
        "- Target-journal exports under `submission_packages/<journal_slug>/` are derived projections and require explicit target confirmation before final journal-ready use.",
        "",
        "## Audit and reproducibility",
        "",
        f"- Delivery layout: `{SUBMISSION_PACKAGE_LAYOUT_VERSION}`",
        "- Audit material: `audit/`",
        "- Reproducibility material: `reproducibility/`",
        "- Canonical authority surface: `paper/`",
        f"- Controller-authorized source: `{source_relative_root}`",
        "",
        "## Delivery status",
        "",
        "- This directory is the stable, stage-agnostic entry point for the latest human-facing package.",
        "- Publication quality and submission readiness remain owned by MAS durable quality and controller surfaces.",
    ]
    linkage = charter_contract_linkage or {}
    study_charter_ref = linkage.get("study_charter_ref") or {}
    paper_quality_contract = linkage.get("paper_quality_contract") or {}
    ledger_linkages = linkage.get("ledger_linkages") or {}
    if linkage:
        mirrored_charter_path = str(study_charter_ref.get("mirrored_artifact_path") or "").strip()
        lines.extend(
            [
                "",
                "## Charter Contract Linkage",
                "",
                f"- Study charter contract: `{study_charter_ref.get('charter_id')}`",
                f"- Study charter path: `{study_charter_ref.get('artifact_path')}`",
                f"- Mirrored study charter artifact: `{mirrored_charter_path or 'not_materialized'}`",
                f"- Paper quality contract present: `{paper_quality_contract.get('present', False)}`",
                f"- Evidence ledger linkage: {str((ledger_linkages.get('evidence_ledger') or {}).get('status') or 'study_root_unresolved')}",
                f"- Review ledger linkage: {str((ledger_linkages.get('review_ledger') or {}).get('status') or 'study_root_unresolved')}",
            ]
        )
    lines.extend(
        [
            "",
            "## Next controller-authorized sync",
            "",
            "- Refresh this mirror only through controller-authorized delivery sync/apply.",
            "- Do not patch files in this directory as the source of truth.",
            "",
            "Use this directory when a human wants the latest readable package without first deciding which stage-specific mirror to open. "
            "Regenerate from the controller-authorized source, not from this projection.",
            "",
        ]
    )
    return "\n".join(lines)
