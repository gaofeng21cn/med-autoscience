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

from .staging_and_sources import (
    SYNC_STAGES,
    FORMAL_PAPER_DELIVERY_RELATIVE_PATHS,
    utc_now,
    dump_json,
    _normalized_path,
    _build_ledger_contract_linkage,
    build_charter_contract_linkage,
    write_text,
    reset_directory,
    remove_directory,
    create_staging_root,
    remap_staging_path_string,
)
from .staging_and_sources import (
    remap_staging_file_records,
    replace_directory_atomically,
    clear_directory_contents,
    can_sync_study_delivery,
    _resolve_study_owned_paper_context,
    _resolve_delivery_context,
    copy_file,
    copy_tree,
    build_submission_source_root,
    build_submission_package_readme,
    build_general_delivery_readme,
    _submission_delivery_stale_reason_label,
)
from .staging_and_sources import (
    build_unavailable_general_delivery_readme,
    build_preview_general_delivery_readme,
    build_manuscript_root_readme,
    build_artifacts_root_readme,
    build_artifacts_finalize_readme,
    build_unavailable_submission_package_readme,
    build_submission_package_audit_preview_readme,
    build_delivery_surface_roles,
    build_promoted_delivery_readme,
    ensure_manuscript_root_readme,
    resolve_finalize_resume_packet_source,
    build_zip_from_directory,
)
from .staging_and_sources import (
    build_authority_source_relative_root,
    FRONT_MATTER_LABELS,
    METADATA_CLOSEOUT_LABELS,
    _humanize_submission_field,
    _humanize_metadata_closeout_item,
    _is_pending_submission_item,
    build_submission_todo_from_manifest,
    build_current_package_readme,
    sync_current_package_projection,
)
from .delivery_descriptions import (
    _copy_relative_files,
    copy_review_ledger_to_delivery_root,
    _copy_optional_file,
    _copy_optional_tree,
    _iter_relative_files,
    _draft_handoff_source_relative_paths,
    _draft_handoff_source_signature,
    _resolve_submission_source_path,
    _hash_file_bytes,
    CURRENT_PACKAGE_GENERATED_PROJECTION_RELATIVE_PATHS,
    CURRENT_PACKAGE_JSON_VOLATILE_TOP_LEVEL_KEYS,
    _submission_source_relative_paths,
)
from .delivery_descriptions import (
    _submission_source_signature,
    _load_json_file,
    _normalize_projection_json_payload,
    _submission_projection_file_matches_source,
    _submission_projection_matches_source,
    build_draft_handoff_readme,
    describe_draft_handoff_delivery,
    describe_submission_delivery,
    materialize_submission_delivery_stale_notice,
)



def sync_draft_handoff_delivery(
    *,
    paper_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        review_ledger_path=paper_root / "review" / "review_ledger.json",
    )
    relative_paths = _draft_handoff_source_relative_paths(paper_root=paper_root)
    source_signature = _draft_handoff_source_signature(
        paper_root=paper_root,
        relative_paths=relative_paths,
    )
    source_relative_root = build_authority_source_relative_root(
        paper_root=paper_root,
        source_root=paper_root,
    )

    reset_directory(manuscript_root)
    _copy_relative_files(
        source_root=paper_root,
        relative_paths=relative_paths,
        target_root=current_package_root,
        category="draft_handoff",
        copied_files=copied_files,
    )

    readme_path = manuscript_root / "README.md"
    write_text(readme_path, build_draft_handoff_readme(study_id=study_id))
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )
    current_package_readme_path = current_package_root / "README.md"
    write_text(
        current_package_readme_path,
        build_current_package_readme(
            study_id=study_id,
            stage="draft_handoff",
            source_relative_root=source_relative_root,
            status_line="review-only draft surface; not a submission-ready package",
            charter_contract_linkage=charter_contract_linkage,
        ),
    )
    generated_files.append(
        {
            "category": "current_package",
            "path": str(current_package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(source_root=current_package_root, output_path=current_package_zip)
    generated_files.append(
        {
            "category": "current_package",
            "path": str(current_package_zip.resolve()),
        }
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": "draft_handoff",
        "study_id": study_id,
        "quest_id": quest_id,
        "source_signature": source_signature,
        "source_relative_paths": [path.as_posix() for path in relative_paths],
        "source": {
            "paper_root": str(paper_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=paper_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
        ),
        "targets": {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    return manifest


def sync_general_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    artifacts_final_root = study_root / "artifacts" / "final"
    staging_manuscript_root = create_staging_root(target_root=manuscript_root)
    staging_artifacts_final_root = (
        create_staging_root(target_root=artifacts_final_root)
        if normalized_stage == "finalize"
        else None
    )
    current_package_root = staging_manuscript_root / "current_package"
    current_package_zip = staging_manuscript_root / "current_package.zip"
    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    try:
        charter_contract_linkage = build_charter_contract_linkage(
            study_root=study_root,
            evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
            review_ledger_path=paper_root / "review" / "review_ledger.json",
        )
        source_root = build_submission_source_root(paper_root=paper_root, publication_profile="general_medical_journal")
        source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)
        source_relative_paths = _submission_source_relative_paths(
            paper_root=paper_root,
            source_root=source_root,
        )
        source_signature = _submission_source_signature(
            paper_root=paper_root,
            source_root=source_root,
            relative_paths=source_relative_paths,
        )

        copy_file(
            source=source_root / "manuscript.docx",
            target=staging_manuscript_root / "manuscript.docx",
            category="manuscript",
            copied_files=copied_files,
        )
        copy_file(
            source=source_root / "paper.pdf",
            target=staging_manuscript_root / "paper.pdf",
            category="manuscript",
            copied_files=copied_files,
        )
        copy_file(
            source=source_root / "submission_manifest.json",
            target=staging_manuscript_root / "submission_manifest.json",
            category="manifest",
            copied_files=copied_files,
        )
        evidence_ledger_source = paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME
        if evidence_ledger_source.exists():
            copy_file(
                source=evidence_ledger_source,
                target=staging_manuscript_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
                category="evidence_ledger",
                copied_files=copied_files,
            )
        if normalized_stage == "finalize":
            copy_file(
                source=worktree_root / "SUMMARY.md",
                target=staging_manuscript_root / "SUMMARY.md",
                category="closeout",
                copied_files=copied_files,
            )
            copy_file(
                source=worktree_root / "status.md",
                target=staging_manuscript_root / "status.md",
                category="closeout",
                copied_files=copied_files,
            )
            copy_file(
                source=paper_root / "final_claim_ledger.md",
                target=staging_manuscript_root / "final_claim_ledger.md",
                category="closeout",
                copied_files=copied_files,
            )
            copy_file(
                source=resolve_finalize_resume_packet_source(paper_root=paper_root, worktree_root=worktree_root),
                target=staging_manuscript_root / "finalize_resume_packet.md",
                category="closeout",
                copied_files=copied_files,
            )
            assert staging_artifacts_final_root is not None
            copy_file(
                source=paper_root / "paper_bundle_manifest.json",
                target=staging_artifacts_final_root / "paper_bundle_manifest.json",
                category="manifest",
                copied_files=copied_files,
            )
            copy_file(
                source=paper_root / "build" / "compile_report.json",
                target=staging_artifacts_final_root / "compile_report.json",
                category="manifest",
                copied_files=copied_files,
            )

        readme_path = staging_manuscript_root / "README.md"
        write_text(
            readme_path,
            build_general_delivery_readme(
                study_id=study_id,
                stage=normalized_stage,
                source_relative_root=source_relative_root,
            ),
        )
        generated_files.append(
            {
                "category": "delivery_readme",
                "path": str(readme_path.resolve()),
            }
        )
        if normalized_stage == "finalize":
            assert staging_artifacts_final_root is not None
            artifacts_readme_path = staging_artifacts_final_root / "README.md"
            write_text(
                artifacts_readme_path,
                build_artifacts_finalize_readme(study_id=study_id, stage=normalized_stage),
            )
            generated_files.append(
                {
                    "category": "artifact_readme",
                    "path": str(artifacts_readme_path.resolve()),
                }
            )

        sync_current_package_projection(
            paper_root=paper_root,
            source_root=source_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            projected_current_package_root=manuscript_root / "current_package",
            study_id=study_id,
            stage=normalized_stage,
            source_relative_root=source_relative_root,
            status_line="human-facing manuscript handoff surface",
            copied_files=copied_files,
            generated_files=generated_files,
            review_ledger_source=paper_root / "review" / "review_ledger.json",
            charter_contract_linkage=charter_contract_linkage,
        )
        copy_review_ledger_to_delivery_root(
            paper_root=paper_root,
            target_root=staging_manuscript_root,
            category="review_surface",
            copied_files=copied_files,
        )

        remapped_copied_files = remap_staging_file_records(
            records=copied_files,
            staging_root=staging_manuscript_root,
            target_root=manuscript_root,
        )
        remapped_generated_files = remap_staging_file_records(
            records=generated_files,
            staging_root=staging_manuscript_root,
            target_root=manuscript_root,
        )
        if normalized_stage == "finalize":
            assert staging_artifacts_final_root is not None
            remapped_copied_files = remap_staging_file_records(
                records=remapped_copied_files,
                staging_root=staging_artifacts_final_root,
                target_root=artifacts_final_root,
            )
            remapped_generated_files = remap_staging_file_records(
                records=remapped_generated_files,
                staging_root=staging_artifacts_final_root,
                target_root=artifacts_final_root,
            )
        targets = {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "current_package_root": str(manuscript_root / "current_package"),
            "current_package_zip": str(manuscript_root / "current_package.zip"),
        }
        if normalized_stage == "finalize":
            targets["artifacts_final_root"] = str(artifacts_final_root)

        manifest = {
            "schema_version": 1,
            "generated_at": utc_now(),
            "stage": normalized_stage,
            "study_id": study_id,
            "quest_id": quest_id,
            "publication_profile": "general_medical_journal",
            "source_signature": source_signature,
            "source_relative_paths": [path.as_posix() for path in source_relative_paths],
            "source": {
                "paper_root": str(paper_root),
                "worktree_root": str(worktree_root),
            },
            "charter_contract_linkage": charter_contract_linkage,
            "surface_roles": build_delivery_surface_roles(
                paper_root=paper_root,
                source_root=source_root,
                manuscript_root=manuscript_root,
                current_package_root=manuscript_root / "current_package",
                current_package_zip=manuscript_root / "current_package.zip",
                auxiliary_evidence_root=artifacts_final_root if normalized_stage == "finalize" else None,
            ),
            "targets": targets,
            "copied_files": remapped_copied_files,
            "generated_files": remapped_generated_files,
        }
        dump_json(staging_manuscript_root / "delivery_manifest.json", manifest)
        replace_directory_atomically(
            staging_root=staging_manuscript_root,
            target_root=manuscript_root,
        )
        if normalized_stage == "finalize":
            assert staging_artifacts_final_root is not None
            replace_directory_atomically(
                staging_root=staging_artifacts_final_root,
                target_root=artifacts_final_root,
            )
    except Exception:
        shutil.rmtree(staging_manuscript_root, ignore_errors=True)
        if staging_artifacts_final_root is not None:
            shutil.rmtree(staging_artifacts_final_root, ignore_errors=True)
        raise

    if normalized_stage != "finalize":
        remove_directory(artifacts_final_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())
    return manifest


def sync_journal_specific_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    journal_package_root = manuscript_root / "journal_packages" / publication_profile
    journal_package_zip = manuscript_root / f"{publication_profile}_submission_package.zip"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)
    source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)

    manuscript_root.mkdir(parents=True, exist_ok=True)
    journal_package_root.parent.mkdir(parents=True, exist_ok=True)
    ensure_manuscript_root_readme(manuscript_root=manuscript_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())
    reset_directory(journal_package_root)

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        review_ledger_path=paper_root / "review" / "review_ledger.json",
    )
    source_relative_paths = _submission_source_relative_paths(
        paper_root=paper_root,
        source_root=source_root,
    )
    source_signature = _submission_source_signature(
        paper_root=paper_root,
        source_root=source_root,
        relative_paths=source_relative_paths,
    )
    copy_file(
        source=source_root / "manuscript.docx",
        target=journal_package_root / "manuscript.docx",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=journal_package_root / "paper.pdf",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=journal_package_root / "submission_manifest.json",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    evidence_ledger_source = paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME
    if evidence_ledger_source.exists():
        copy_file(
            source=evidence_ledger_source,
            target=journal_package_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
            category="journal_submission_package",
            copied_files=copied_files,
        )
    supplementary_docx = source_root / "Supplementary_Material.docx"
    if supplementary_docx.exists():
        copy_file(
            source=supplementary_docx,
            target=journal_package_root / "Supplementary_Material.docx",
            category="journal_submission_package",
            copied_files=copied_files,
        )
    copy_tree(
        source_root=source_root / "figures",
        target_root=journal_package_root / "figures",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=source_root / "tables",
        target_root=journal_package_root / "tables",
        category="journal_submission_package",
        copied_files=copied_files,
    )
    package_readme_path = journal_package_root / "README.md"
    write_text(
        package_readme_path,
        build_submission_package_readme(
            study_id=study_id,
            stage=normalized_stage,
            publication_profile=publication_profile,
        ),
    )
    generated_files.append(
        {
            "category": "journal_submission_package",
            "path": str(package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(
        source_root=journal_package_root,
        output_path=journal_package_zip,
    )
    generated_files.append(
        {
            "category": "journal_submission_package",
            "path": str(journal_package_zip.resolve()),
        }
    )
    sync_current_package_projection(
        paper_root=paper_root,
        source_root=journal_package_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        study_id=study_id,
        stage=f"{publication_profile}_{normalized_stage}",
        source_relative_root=source_relative_root,
        status_line="journal-specific human-facing manuscript package",
        copied_files=copied_files,
        generated_files=generated_files,
        review_ledger_source=paper_root / "review" / "review_ledger.json",
        charter_contract_linkage=charter_contract_linkage,
    )
    copy_review_ledger_to_delivery_root(
        paper_root=paper_root,
        target_root=journal_package_root,
        category="review_surface",
        copied_files=copied_files,
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "study_id": study_id,
        "quest_id": quest_id,
        "publication_profile": publication_profile,
        "source_signature": source_signature,
        "source_relative_paths": [path.as_posix() for path in source_relative_paths],
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
            "package_source_root": str(source_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            auxiliary_evidence_root=None,
        ),
        "targets": {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "journal_package_root": str(journal_package_root),
            "journal_package_zip": str(journal_package_zip),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    dump_json(journal_package_root / "delivery_manifest.json", manifest)
    return manifest


def sync_promoted_journal_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    artifacts_final_root = study_root / "artifacts" / "final"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    mirror_root = manuscript_root / "journal_package_mirrors" / publication_profile
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)
    source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)

    reset_directory(manuscript_root)
    remove_directory(artifacts_final_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        review_ledger_path=paper_root / "review" / "review_ledger.json",
    )
    source_relative_paths = _submission_source_relative_paths(
        paper_root=paper_root,
        source_root=source_root,
    )
    source_signature = _submission_source_signature(
        paper_root=paper_root,
        source_root=source_root,
        relative_paths=source_relative_paths,
    )
    copy_file(
        source=source_root / "manuscript.docx",
        target=manuscript_root / "manuscript.docx",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=manuscript_root / "paper.pdf",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=manuscript_root / "submission_manifest.json",
        category="manifest",
        copied_files=copied_files,
    )
    evidence_ledger_source = paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME
    if evidence_ledger_source.exists():
        copy_file(
            source=evidence_ledger_source,
            target=manuscript_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
            category="evidence_ledger",
            copied_files=copied_files,
        )
    supplementary_docx = source_root / "Supplementary_Material.docx"
    if supplementary_docx.exists():
        copy_file(
            source=supplementary_docx,
            target=manuscript_root / "Supplementary_Material.docx",
            category="manuscript",
            copied_files=copied_files,
        )
    if normalized_stage == "finalize":
        reset_directory(artifacts_final_root)
        copy_file(
            source=worktree_root / "SUMMARY.md",
            target=manuscript_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=worktree_root / "status.md",
            target=manuscript_root / "status.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "final_claim_ledger.md",
            target=manuscript_root / "final_claim_ledger.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=resolve_finalize_resume_packet_source(paper_root=paper_root, worktree_root=worktree_root),
            target=manuscript_root / "finalize_resume_packet.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "paper_bundle_manifest.json",
            target=artifacts_final_root / "paper_bundle_manifest.json",
            category="manifest",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "build" / "compile_report.json",
            target=artifacts_final_root / "compile_report.json",
            category="manifest",
            copied_files=copied_files,
        )

    readme_path = manuscript_root / "README.md"
    write_text(
        readme_path,
        build_promoted_delivery_readme(
            study_id=study_id,
            publication_profile=publication_profile,
            source_relative_root=source_relative_root,
        ),
    )
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )
    if normalized_stage == "finalize":
        artifacts_readme_path = artifacts_final_root / "README.md"
        write_text(
            artifacts_readme_path,
            build_artifacts_finalize_readme(study_id=study_id, stage=normalized_stage),
        )
        generated_files.append(
            {
                "category": "artifact_readme",
                "path": str(artifacts_readme_path.resolve()),
            }
        )

    sync_current_package_projection(
        paper_root=paper_root,
        source_root=source_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        study_id=study_id,
        stage=f"{publication_profile}_submission",
        source_relative_root=source_relative_root,
        status_line="promoted human-facing manuscript handoff surface",
        copied_files=copied_files,
        generated_files=generated_files,
        review_ledger_source=paper_root / "review" / "review_ledger.json",
        charter_contract_linkage=charter_contract_linkage,
    )
    copy_review_ledger_to_delivery_root(
        paper_root=paper_root,
        target_root=manuscript_root,
        category="review_surface",
        copied_files=copied_files,
    )

    reset_directory(mirror_root)
    copy_tree(
        source_root=source_root,
        target_root=mirror_root,
        category="journal_submission_mirror",
        copied_files=copied_files,
    )
    copy_file(
        source=paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        target=mirror_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
        category="journal_submission_mirror",
        copied_files=copied_files,
    )
    mirror_readme_path = mirror_root / "README.md"
    write_text(
        mirror_readme_path,
        build_submission_package_readme(
            study_id=study_id,
            stage=f"{publication_profile}_submission_mirror",
            publication_profile=publication_profile,
        ),
    )
    mirror_generated_files = [
        {
            "category": "journal_submission_mirror",
            "path": str(mirror_readme_path.resolve()),
        }
    ]
    mirror_manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": f"{publication_profile}_submission_mirror",
        "study_id": study_id,
        "quest_id": quest_id,
        "publication_profile": publication_profile,
        "source_signature": source_signature,
        "source_relative_paths": [path.as_posix() for path in source_relative_paths],
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            journal_submission_mirror_root=mirror_root,
        ),
        "targets": {
            "study_root": str(study_root),
            "journal_package_root": str(mirror_root),
        },
        "copied_files": [
            item
            for item in copied_files
            if item["category"] == "journal_submission_mirror"
        ],
        "generated_files": mirror_generated_files,
    }
    dump_json(mirror_root / "delivery_manifest.json", mirror_manifest)

    targets = {
        "study_root": str(study_root),
        "manuscript_root": str(manuscript_root),
        "current_package_root": str(current_package_root),
        "current_package_zip": str(current_package_zip),
        "journal_package_mirror_root": str(mirror_root),
    }
    if normalized_stage == "finalize":
        targets["artifacts_final_root"] = str(artifacts_final_root)

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": f"{publication_profile}_submission",
        "study_id": study_id,
        "quest_id": quest_id,
        "publication_profile": publication_profile,
        "source_signature": source_signature,
        "source_relative_paths": [path.as_posix() for path in source_relative_paths],
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            auxiliary_evidence_root=artifacts_final_root if normalized_stage == "finalize" else None,
            journal_submission_mirror_root=mirror_root,
        ),
        "targets": targets,
        "copied_files": [
            item
            for item in copied_files
            if item["category"] != "journal_submission_mirror"
        ],
        "generated_files": generated_files,
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    return manifest


def sync_study_delivery(
    *,
    paper_root: Path,
    stage: str,
    publication_profile: str = "general_medical_journal",
    promote_to_final: bool = False,
) -> dict[str, Any]:
    normalized_stage = str(stage or "").strip()
    if normalized_stage not in SYNC_STAGES:
        raise ValueError(f"unsupported sync stage: {stage}")
    normalized_publication_profile = normalize_publication_profile(publication_profile)
    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {publication_profile}")

    context = _resolve_delivery_context(paper_root.resolve())
    paper_root = context["paper_root"]
    worktree_root = context["worktree_root"]
    quest_id = context["quest_id"]
    study_id = context["study_id"]
    study_root = context["study_root"]

    if normalized_stage == "draft_handoff":
        if normalized_publication_profile != GENERAL_MEDICAL_JOURNAL_PROFILE:
            raise ValueError("draft_handoff only supports the general_medical_journal profile")
        return sync_draft_handoff_delivery(
            paper_root=paper_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
        )

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return sync_general_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
        )

    if not is_supported_publication_profile(normalized_publication_profile):
        raise ValueError(f"unsupported publication profile: {normalized_publication_profile}")

    if promote_to_final:
        return sync_promoted_journal_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
            quest_id=quest_id,
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
            publication_profile=normalized_publication_profile,
        )

    return sync_journal_specific_delivery(
        paper_root=paper_root,
        worktree_root=worktree_root,
        quest_id=quest_id,
        study_id=study_id,
        study_root=study_root,
        normalized_stage=normalized_stage,
        publication_profile=normalized_publication_profile,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync finalized paper deliverables into the study shallow path.")
    parser.add_argument("--paper-root", type=Path, required=True)
    parser.add_argument("--stage", choices=SYNC_STAGES, required=True)
    parser.add_argument("--publication-profile", default="general_medical_journal")
    parser.add_argument("--promote-to-final", action="store_true")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    sync_study_delivery(
        paper_root=args.paper_root,
        stage=args.stage,
        publication_profile=args.publication_profile,
        promote_to_final=args.promote_to_final,
    )
    return 0
