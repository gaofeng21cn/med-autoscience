from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import tempfile
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.study_charter import read_study_charter, resolve_study_charter_ref
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context



SYNC_STAGES = ("draft_handoff", "submission_minimal", "finalize")
FORMAL_PAPER_DELIVERY_RELATIVE_PATHS = (
    Path(medical_surface_policy.EVIDENCE_LEDGER_BASENAME),
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _normalized_path(path: Path | None) -> str | None:
    if path is None:
        return None
    return str(Path(path).expanduser().resolve())


def _build_ledger_contract_linkage(
    *,
    ledger_name: str,
    ledger_path: Path | None,
    study_context_status: str,
    charter_id: str | None,
    contract_role: str | None,
) -> dict[str, Any]:
    resolved_ledger_path = Path(ledger_path).expanduser().resolve() if ledger_path is not None else None
    ledger_present = bool(resolved_ledger_path and resolved_ledger_path.exists())
    normalized_role = str(contract_role or "").strip() or None
    if study_context_status == "linked_context":
        if normalized_role and ledger_present:
            status = "linked"
        elif normalized_role:
            status = "ledger_missing"
        else:
            status = "contract_role_missing"
    else:
        status = study_context_status
    return {
        "ledger_name": ledger_name,
        "ledger_path": _normalized_path(resolved_ledger_path),
        "ledger_present": ledger_present,
        "charter_id": charter_id,
        "contract_role_present": bool(normalized_role),
        "contract_role": normalized_role,
        "contract_role_json_pointer": f"/paper_quality_contract/downstream_contract_roles/{ledger_name}",
        "status": status,
    }


def build_charter_contract_linkage(
    *,
    study_root: Path | None,
    evidence_ledger_path: Path | None,
    review_ledger_path: Path | None,
) -> dict[str, Any]:
    resolved_study_root = Path(study_root).expanduser().resolve() if study_root is not None else None
    if resolved_study_root is None:
        study_context_status = "study_root_unresolved"
        charter_path = None
        charter_id = None
        paper_quality_contract_present = False
        downstream_contract_roles: dict[str, str] = {}
    else:
        charter_path = resolve_study_charter_ref(study_root=resolved_study_root)
        charter_id = None
        downstream_contract_roles = {}
        if not charter_path.exists():
            study_context_status = "study_charter_missing"
            paper_quality_contract_present = False
        else:
            try:
                charter_payload = read_study_charter(study_root=resolved_study_root, ref=charter_path)
            except (json.JSONDecodeError, ValueError):
                study_context_status = "study_charter_invalid"
                paper_quality_contract_present = False
            else:
                charter_id = str(charter_payload.get("charter_id") or "").strip() or None
                paper_quality_contract = charter_payload.get("paper_quality_contract")
                paper_quality_contract_present = isinstance(paper_quality_contract, dict)
                if paper_quality_contract_present:
                    raw_roles = paper_quality_contract.get("downstream_contract_roles")
                    if isinstance(raw_roles, dict):
                        downstream_contract_roles = {
                            str(key): str(value).strip()
                            for key, value in raw_roles.items()
                            if str(value).strip()
                        }
                study_context_status = "linked_context" if paper_quality_contract_present else "paper_quality_contract_missing"

    ledger_linkages = {
        "evidence_ledger": _build_ledger_contract_linkage(
            ledger_name="evidence_ledger",
            ledger_path=evidence_ledger_path,
            study_context_status=study_context_status,
            charter_id=charter_id,
            contract_role=downstream_contract_roles.get("evidence_ledger"),
        ),
        "review_ledger": _build_ledger_contract_linkage(
            ledger_name="review_ledger",
            ledger_path=review_ledger_path,
            study_context_status=study_context_status,
            charter_id=charter_id,
            contract_role=downstream_contract_roles.get("review_ledger"),
        ),
    }
    ledger_statuses = {payload["status"] for payload in ledger_linkages.values()}
    if study_context_status != "linked_context":
        status = study_context_status
    elif ledger_statuses == {"linked"}:
        status = "linked"
    elif "linked" in ledger_statuses:
        status = "partially_linked"
    else:
        status = "unlinked"
    return {
        "status": status,
        "study_root": _normalized_path(resolved_study_root),
        "study_charter_ref": {
            "charter_id": charter_id,
            "artifact_path": _normalized_path(charter_path),
        },
        "paper_quality_contract": {
            "present": paper_quality_contract_present,
            "artifact_path": _normalized_path(charter_path),
            "json_pointer": "/paper_quality_contract",
        },
        "ledger_linkages": ledger_linkages,
    }


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def remove_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)


def create_staging_root(*, target_root: Path) -> Path:
    return Path(
        tempfile.mkdtemp(
            dir=target_root.parent,
            prefix=f".{target_root.name}.tmp-",
        )
    ).resolve()


def remap_staging_path_string(*, value: str, staging_root: Path, target_root: Path) -> str:
    resolved_value = Path(value).expanduser().resolve()
    try:
        relative = resolved_value.relative_to(staging_root.expanduser().resolve())
    except ValueError:
        return str(resolved_value)
    return str((target_root.expanduser().resolve() / relative).resolve())


def remap_staging_file_records(
    *,
    records: list[dict[str, Any]],
    staging_root: Path,
    target_root: Path,
) -> list[dict[str, Any]]:
    remapped: list[dict[str, Any]] = []
    for record in records:
        updated = dict(record)
        for key in ("target_path", "path"):
            value = updated.get(key)
            if isinstance(value, str) and value.strip():
                updated[key] = remap_staging_path_string(
                    value=value,
                    staging_root=staging_root,
                    target_root=target_root,
                )
        remapped.append(updated)
    return remapped


def replace_directory_atomically(*, staging_root: Path, target_root: Path) -> None:
    resolved_staging_root = staging_root.expanduser().resolve()
    resolved_target_root = target_root.expanduser().resolve()
    backup_root = resolved_target_root.parent / (
        f".{resolved_target_root.name}.bak-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}"
    )
    replaced_existing_root = False
    try:
        if resolved_target_root.exists():
            resolved_target_root.replace(backup_root)
            replaced_existing_root = True
        resolved_staging_root.replace(resolved_target_root)
    except Exception:
        if resolved_target_root.exists():
            shutil.rmtree(resolved_target_root, ignore_errors=True)
        if replaced_existing_root and backup_root.exists():
            backup_root.replace(resolved_target_root)
        raise
    finally:
        if backup_root.exists():
            shutil.rmtree(backup_root, ignore_errors=True)


def clear_directory_contents(path: Path, *, keep_names: tuple[str, ...] = ()) -> list[str]:
    path.mkdir(parents=True, exist_ok=True)
    cleared_paths: list[str] = []
    for child in sorted(path.iterdir(), key=lambda item: item.name):
        if child.name in keep_names:
            continue
        if child.is_dir():
            shutil.rmtree(child)
        else:
            child.unlink()
        cleared_paths.append(str(child.resolve()))
    return cleared_paths


def can_sync_study_delivery(*, paper_root: Path) -> bool:
    try:
        _resolve_delivery_context(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return False
    return True


def _resolve_study_owned_paper_context(paper_root: Path) -> tuple[Path, Path, str] | None:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    if resolved_paper_root.name != "paper":
        return None
    study_root = resolved_paper_root.parent
    if study_root.parent.name != "studies":
        return None
    if not (study_root / "study.yaml").exists():
        return None
    return resolved_paper_root, study_root, study_root.name


def _resolve_delivery_context(paper_root: Path) -> dict[str, Any]:
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    try:
        context = resolve_paper_root_context(resolved_paper_root)
    except (FileNotFoundError, ValueError):
        direct_context = _resolve_study_owned_paper_context(resolved_paper_root)
        if direct_context is None:
            raise
        resolved_paper_root, study_root, study_id = direct_context
        return {
            "paper_root": resolved_paper_root,
            "worktree_root": study_root,
            "quest_root": None,
            "quest_id": study_id,
            "study_id": study_id,
            "study_root": study_root,
        }
    return {
        "paper_root": context.paper_root,
        "worktree_root": context.worktree_root,
        "quest_root": context.quest_root,
        "quest_id": context.quest_id,
        "study_id": context.study_id,
        "study_root": context.study_root,
    }


def copy_file(
    *,
    source: Path,
    target: Path,
    category: str,
    copied_files: list[dict[str, str]],
) -> None:
    if not source.exists():
        raise FileNotFoundError(f"missing delivery source: {source}")
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    copied_files.append(
        {
            "category": category,
            "source_path": str(source.resolve()),
            "target_path": str(target.resolve()),
        }
    )


def copy_tree(
    *,
    source_root: Path,
    target_root: Path,
    category: str,
    copied_files: list[dict[str, str]],
    ignore_filenames: tuple[str, ...] = (),
) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"missing delivery source directory: {source_root}")
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
            continue
        if source.name in ignore_filenames:
            continue
        relative = source.relative_to(source_root)
        copy_file(
            source=source,
            target=target_root / relative,
            category=category,
            copied_files=copied_files,
        )


def build_submission_source_root(*, paper_root: Path, publication_profile: str) -> Path:
    normalized_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")
    if normalized_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return paper_root / "submission_minimal"
    return paper_root / "journal_submissions" / normalized_profile


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
            f"  - `submission_manifest.json`\n"
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
        f"  - `submission_manifest.json`\n"
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
        f"  - `submission_manifest.json`\n"
        f"  - `Supplementary_Material.docx` (when generated)\n"
        f"  - `current_package/`\n"
        f"  - `current_package.zip`\n"
        f"  - `journal_package_mirrors/{publication_profile}/`\n\n"
        f"This study-level final delivery is assembled automatically from the primary journal package so the canonical shallow handoff stays aligned with the active target-journal surface.\n"
    )


def ensure_manuscript_root_readme(*, manuscript_root: Path) -> None:
    readme_path = manuscript_root / "README.md"
    if readme_path.exists():
        return
    write_text(readme_path, build_manuscript_root_readme())


def resolve_finalize_resume_packet_source(*, paper_root: Path, worktree_root: Path) -> Path:
    candidates = [
        paper_root / "finalize_resume_packet.md",
        worktree_root / "handoffs" / "finalize_resume_packet.md",
    ]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    raise FileNotFoundError(
        "missing delivery source: no finalize resume packet found in "
        f"{paper_root / 'finalize_resume_packet.md'} or {worktree_root / 'handoffs' / 'finalize_resume_packet.md'}"
    )


def build_zip_from_directory(*, source_root: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for source in sorted(source_root.rglob("*")):
            if not source.is_file():
                continue
            archive.write(source, source.relative_to(source_root).as_posix())


def build_authority_source_relative_root(*, paper_root: Path, source_root: Path) -> str:
    return source_root.resolve().relative_to(paper_root.resolve().parent).as_posix()


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
        f"- Controller-authorized source: `{source_relative_root}`",
        "- Canonical authority surface: `paper/`",
        "- This directory is the stable, stage-agnostic entry point for the latest human-facing package.",
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
            "Use this directory when a human wants the latest readable package without first deciding which stage-specific mirror to open. "
            "Regenerate from the controller-authorized source, not from this projection.",
            "",
        ]
    )
    return "\n".join(lines)


def sync_current_package_projection(
    *,
    paper_root: Path | None,
    source_root: Path,
    current_package_root: Path,
    current_package_zip: Path,
    projected_current_package_root: Path | None = None,
    study_id: str,
    stage: str,
    source_relative_root: str,
    status_line: str,
    copied_files: list[dict[str, str]],
    generated_files: list[dict[str, str]],
    review_ledger_source: Path | None = None,
    charter_contract_linkage: dict[str, Any] | None = None,
) -> None:
    reset_directory(current_package_root)
    resolved_projected_current_package_root = (
        Path(projected_current_package_root).expanduser().resolve()
        if projected_current_package_root is not None
        else current_package_root.expanduser().resolve()
    )
    copy_tree(
        source_root=source_root,
        target_root=current_package_root,
        category="current_package",
        copied_files=copied_files,
    )
    if paper_root is not None:
        resolved_paper_root = Path(paper_root).expanduser().resolve()
        for relative_path in FORMAL_PAPER_DELIVERY_RELATIVE_PATHS:
            source_path = resolved_paper_root / relative_path
            if not source_path.exists():
                continue
            copy_file(
                source=source_path,
                target=current_package_root / relative_path,
                category="current_package",
                copied_files=copied_files,
            )
    if review_ledger_source is not None and review_ledger_source.exists():
        copy_file(
            source=review_ledger_source,
            target=current_package_root / "review" / review_ledger_source.name,
            category="current_package_review_surface",
            copied_files=copied_files,
        )
    linkage_payload = charter_contract_linkage if charter_contract_linkage is not None else {}
    study_charter_ref = dict(linkage_payload.get("study_charter_ref") or {})
    mirrored_charter_path = None
    raw_charter_artifact_path = str(study_charter_ref.get("artifact_path") or "").strip()
    if raw_charter_artifact_path:
        charter_artifact_path = Path(raw_charter_artifact_path).expanduser()
        if charter_artifact_path.exists():
            mirrored_charter_path = current_package_root / "controller" / charter_artifact_path.name
            copy_file(
                source=charter_artifact_path,
                target=mirrored_charter_path,
                category="current_package_charter_surface",
                copied_files=copied_files,
            )
            study_charter_ref["mirrored_artifact_path"] = str(
                resolved_projected_current_package_root / "controller" / charter_artifact_path.name
            )
            linkage_payload["study_charter_ref"] = study_charter_ref
    readme_path = current_package_root / "README.md"
    write_text(
        readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage=stage,
            source_relative_root=source_relative_root,
            status_line=status_line,
            charter_contract_linkage=linkage_payload,
        ),
    )
    generated_files.append(
        {
            "category": "current_package",
            "path": str(readme_path.resolve()),
        }
    )
    submission_todo = build_submission_todo_from_manifest(
        manifest_path=current_package_root / "submission_manifest.json",
    )
    if submission_todo is not None:
        todo_path = current_package_root / "SUBMISSION_TODO.md"
        write_text(todo_path, submission_todo)
        generated_files.append(
            {
                "category": "current_package_submission_todo",
                "path": str(todo_path.resolve()),
            }
        )
    build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    generated_files.append(
        {
            "category": "current_package",
            "path": str(current_package_zip.resolve()),
        }
    )
