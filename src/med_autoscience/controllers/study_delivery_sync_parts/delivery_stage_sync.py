from __future__ import annotations

import hashlib
import shutil
from pathlib import Path
from collections.abc import Mapping
from typing import Any

from med_autoscience.policies import medical_publication_surface as medical_surface_policy
from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.controllers.artifact_lifecycle_inventory import build_study_delivery_lifecycle_hook
from med_autoscience.controllers.authority_route_gate import (
    attach_authority_route_gate,
)
from med_autoscience.controllers.authority_write_route import (
    blocked_authority_write_payload,
    resolve_authority_write_route_context,
)

from .staging_and_sources import (
    SYNC_STAGES,
    utc_now,
    dump_json,
    build_charter_contract_linkage,
    write_text,
    reset_directory,
    remove_directory,
    create_staging_root,
)
from .staging_and_sources import (
    remap_staging_file_records,
    replace_directory_atomically,
    _resolve_delivery_context,
    copy_file,
    copy_tree,
    build_submission_source_root,
    build_submission_package_readme,
    build_general_delivery_readme,
)
from .staging_and_sources import (
    build_artifacts_root_readme,
    build_artifacts_finalize_readme,
    build_delivery_surface_roles,
    build_promoted_delivery_readme,
    ensure_manuscript_root_readme,
    resolve_finalize_resume_packet_source,
    build_zip_from_directory,
)
from .staging_and_sources import (
    build_authority_source_relative_root,
    build_current_package_readme,
)
from .current_package_projection import augment_submission_surface_in_place, sync_current_package_projection
from med_autoscience.controllers.submission_package_layout import (
    audit_path,
    build_submission_delivery_signature_block,
    resolve_evidence_ledger_path,
    resolve_review_ledger_path,
    resolve_submission_manifest_path,
)
from .delivery_descriptions import (
    _copy_relative_files,
    copy_review_ledger_to_delivery_root,
    _draft_handoff_source_relative_paths,
    _draft_handoff_source_signature,
    build_draft_handoff_readme,
)
from .submission_delivery_descriptions import (
    _submission_source_relative_paths,
    _submission_source_signature,
)
from .external_entry import _sync_user_delivery_entry
from .authority_refs import build_delivery_authority_ref_block
from .promoted_journal_delivery import sync_promoted_journal_delivery


def _submission_root(study_root: Path) -> Path:
    return study_root / "submission"


def _submission_zip(study_root: Path) -> Path:
    return study_root / "submission.zip"


def _delivery_evidence_ledger_source(*, paper_root: Path, source_root: Path) -> Path:
    for candidate in (
        resolve_evidence_ledger_path(source_root),
        paper_root / medical_surface_policy.EVIDENCE_LEDGER_BASENAME,
    ):
        if candidate.exists():
            return candidate
    return resolve_evidence_ledger_path(source_root)


def _delivery_review_ledger_source(*, paper_root: Path, source_root: Path) -> Path:
    for candidate in (
        resolve_review_ledger_path(source_root),
        paper_root / "review" / "review_ledger.json",
    ):
        if candidate.exists():
            return candidate
    return resolve_review_ledger_path(source_root)


def _write_study_delivery_manifest(
    *,
    manifest_root: Path,
    manifest: dict[str, Any],
) -> None:
    manifest_root.mkdir(parents=True, exist_ok=True)
    dump_json(manifest_root / "delivery_manifest.json", manifest)


def sync_draft_handoff_delivery(
    *,
    paper_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    known_blockers: tuple[str, ...] = (),
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    submission_root = _submission_root(study_root)
    submission_zip = _submission_zip(study_root)

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

    reset_directory(submission_root)
    _copy_relative_files(
        source_root=paper_root,
        relative_paths=relative_paths,
        target_root=submission_root,
        category="draft_handoff",
        copied_files=copied_files,
    )

    readme_path = submission_root / "README.md"
    write_text(readme_path, build_draft_handoff_readme(study_id=study_id))
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )
    current_package_readme_path = submission_root / "README.md"
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
    build_zip_from_directory(source_root=submission_root, output_path=submission_zip)
    generated_files.append(
        {
            "category": "submission_surface",
            "path": str(submission_zip.resolve()),
        }
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": "draft_handoff",
        "package_kind": "current_package",
        "can_submit": False,
        "quality_gate_status": "blocked" if known_blockers else "not_blocked",
        "known_blockers": list(known_blockers),
        "generated_from_current_source": True,
        "study_id": study_id,
        "quest_id": quest_id,
        "source_signature": source_signature,
        "source_relative_paths": [path.as_posix() for path in relative_paths],
        "source": {
            "paper_root": str(paper_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        **build_delivery_authority_ref_block(study_root=study_root),
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=submission_root,
            manuscript_root=submission_root,
            current_package_root=submission_root,
            current_package_zip=submission_zip,
        ),
        "targets": {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "submission_root": str(submission_root),
            "current_package_root": str(submission_root),
            "current_package_zip": str(submission_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
        "artifact_lifecycle": build_study_delivery_lifecycle_hook(
            study_root=study_root,
            current_package_root=submission_root,
            current_package_zip=submission_zip,
            copied_files=copied_files,
            generated_files=generated_files,
        ),
    }
    _write_study_delivery_manifest(manifest_root=manuscript_root, manifest=manifest)
    return manifest


def sync_general_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    known_blockers: tuple[str, ...] = (),
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    submission_root = _submission_root(study_root)
    submission_zip = _submission_zip(study_root)
    artifacts_final_root = study_root / "artifacts" / "final"
    staging_artifacts_final_root = (
        create_staging_root(target_root=artifacts_final_root)
        if normalized_stage == "finalize"
        else None
    )
    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    try:
        source_root = build_submission_source_root(paper_root=paper_root, publication_profile="general_medical_journal")
        evidence_ledger_source = _delivery_evidence_ledger_source(paper_root=paper_root, source_root=source_root)
        review_ledger_source = _delivery_review_ledger_source(paper_root=paper_root, source_root=source_root)
        charter_contract_linkage = build_charter_contract_linkage(
            study_root=study_root,
            evidence_ledger_path=evidence_ledger_source,
            review_ledger_path=review_ledger_source,
        )
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

        if normalized_stage == "finalize":
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

        if source_root.resolve() == submission_root.resolve():
            current_package_readme_payload = augment_submission_surface_in_place(
                paper_root=paper_root,
                source_root=source_root,
                submission_zip=submission_zip,
                study_id=study_id,
                stage=normalized_stage,
                source_relative_root=source_relative_root,
                copied_files=copied_files,
                generated_files=generated_files,
                review_ledger_source=review_ledger_source,
                charter_contract_linkage=charter_contract_linkage,
                quality_gate_status="blocked" if known_blockers else "not_blocked",
                known_blockers=known_blockers,
                source_signature=source_signature,
            )
        else:
            current_package_readme_payload = sync_current_package_projection(
                paper_root=paper_root,
                source_root=source_root,
                current_package_root=submission_root,
                current_package_zip=submission_zip,
                projected_current_package_root=submission_root,
                primary_artifact_delivery_root=submission_root,
                study_id=study_id,
                stage=normalized_stage,
                source_relative_root=source_relative_root,
                status_line="controller-generated submission package",
                copied_files=copied_files,
                generated_files=generated_files,
                review_ledger_source=review_ledger_source,
                charter_contract_linkage=charter_contract_linkage,
                quality_gate_status="blocked" if known_blockers else "not_blocked",
                known_blockers=known_blockers,
                source_signature=source_signature,
            )
        compatibility_mirrors = _sync_general_delivery_compatibility_mirrors(
            paper_root=paper_root,
            worktree_root=worktree_root,
            study_root=study_root,
            source_root=source_root,
            source_relative_root=source_relative_root,
            study_id=study_id,
            stage=normalized_stage,
            copied_files=copied_files,
            generated_files=generated_files,
            review_ledger_source=review_ledger_source,
            charter_contract_linkage=charter_contract_linkage,
            quality_gate_status="blocked" if known_blockers else "not_blocked",
            known_blockers=known_blockers,
            source_signature=source_signature,
        )

        targets = {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "submission_root": str(submission_root),
            "current_package_root": str(submission_root),
            "current_package_zip": str(submission_zip),
        }
        if normalized_stage == "finalize":
            targets["artifacts_final_root"] = str(artifacts_final_root)

        manifest = {
            "schema_version": 1,
            "generated_at": utc_now(),
            "stage": normalized_stage,
            "package_kind": "current_package",
            "can_submit": False,
            "quality_gate_status": "blocked" if known_blockers else "not_blocked",
            "known_blockers": list(known_blockers),
            "generated_from_current_source": True,
            "study_id": study_id,
            "quest_id": quest_id,
            "publication_profile": "general_medical_journal",
            **build_submission_delivery_signature_block(
                source_signature=source_signature,
                source_relative_paths=source_relative_paths,
                source_package_root=source_root,
                human_package_root=submission_root,
                package_role="human_facing_submission_root",
            ),
            "source": {
                "paper_root": str(paper_root),
                "worktree_root": str(worktree_root),
            },
            "controller_authorized_doctor_readme": current_package_readme_payload,
            "charter_contract_linkage": charter_contract_linkage,
            **build_delivery_authority_ref_block(study_root=study_root),
            "surface_roles": build_delivery_surface_roles(
                paper_root=paper_root,
                source_root=submission_root,
                manuscript_root=submission_root,
                current_package_root=submission_root,
                current_package_zip=submission_zip,
                auxiliary_evidence_root=artifacts_final_root if normalized_stage == "finalize" else None,
            ),
            "targets": targets,
            "compatibility_mirrors": compatibility_mirrors,
            "copied_files": copied_files,
            "generated_files": generated_files,
            "artifact_lifecycle": build_study_delivery_lifecycle_hook(
                study_root=study_root,
                current_package_root=submission_root,
                current_package_zip=submission_zip,
                copied_files=copied_files,
                generated_files=generated_files,
            ),
        }
        _write_study_delivery_manifest(manifest_root=manuscript_root, manifest=manifest)
        if normalized_stage == "finalize":
            assert staging_artifacts_final_root is not None
            replace_directory_atomically(
                staging_root=staging_artifacts_final_root,
                target_root=artifacts_final_root,
            )
    except Exception:
        if staging_artifacts_final_root is not None:
            shutil.rmtree(staging_artifacts_final_root, ignore_errors=True)
        raise

    if normalized_stage != "finalize":
        remove_directory(artifacts_final_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())
    return manifest


def _sync_general_delivery_compatibility_mirrors(
    *,
    paper_root: Path,
    worktree_root: Path,
    study_root: Path,
    source_root: Path,
    source_relative_root: str,
    study_id: str,
    stage: str,
    copied_files: list[dict[str, str]],
    generated_files: list[dict[str, str]],
    review_ledger_source: Path | None,
    charter_contract_linkage: dict[str, Any],
    quality_gate_status: str,
    known_blockers: tuple[str, ...],
    source_signature: str,
) -> list[dict[str, str]]:
    """Keep pre-existing legacy package aliases from remaining stale."""
    mirrors: list[dict[str, str]] = []
    resolved_source_root = source_root.resolve()

    legacy_submission_root = paper_root / "submission_minimal"
    if legacy_submission_root.exists() and legacy_submission_root.resolve() != resolved_source_root:
        reset_directory(legacy_submission_root)
        copy_tree(
            source_root=source_root,
            target_root=legacy_submission_root,
            category="legacy_submission_minimal_alias",
            copied_files=copied_files,
            preserve_metadata=False,
        )
        mirrors.append(
            {
                "role": "legacy_submission_minimal_alias",
                "root": str(legacy_submission_root),
                "source_root": str(source_root),
            }
        )

    current_package_roots = (
        worktree_root / "manuscript" / "current_package",
        study_root / "manuscript" / "current_package",
    )
    seen_current_package_roots: set[Path] = set()
    for current_package_root in current_package_roots:
        resolved_current_package_root = current_package_root.resolve()
        if resolved_current_package_root in seen_current_package_roots:
            continue
        seen_current_package_roots.add(resolved_current_package_root)
        if not current_package_root.exists() or resolved_current_package_root == resolved_source_root:
            continue
        current_package_zip = current_package_root.parent / "current_package.zip"
        sync_current_package_projection(
            paper_root=paper_root,
            source_root=source_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            study_id=study_id,
            stage=stage,
            source_relative_root=source_relative_root,
            status_line="compatibility current-package mirror; not a submission-ready package",
            copied_files=copied_files,
            generated_files=generated_files,
            review_ledger_source=review_ledger_source,
            charter_contract_linkage=charter_contract_linkage,
            quality_gate_status=quality_gate_status,
            known_blockers=known_blockers,
            source_signature=source_signature,
        )
        mirrors.append(
            {
                "role": "legacy_current_package_mirror",
                "root": str(current_package_root),
                "zip": str(current_package_zip),
                "source_root": str(source_root),
            }
        )

    return mirrors


def _sync_current_package_mirror_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    quest_id: str,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
    known_blockers: tuple[str, ...],
) -> dict[str, Any]:
    manuscript_root = study_root / "manuscript"
    current_package_root = manuscript_root / "current_package"
    current_package_zip = manuscript_root / "current_package.zip"
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)
    source_relative_root = build_authority_source_relative_root(paper_root=paper_root, source_root=source_root)
    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    manuscript_root.mkdir(parents=True, exist_ok=True)
    ensure_manuscript_root_readme(manuscript_root=manuscript_root)
    write_text(study_root / "artifacts" / "README.md", build_artifacts_root_readme())
    source_relative_paths = _submission_source_relative_paths(
        paper_root=paper_root,
        source_root=source_root,
    )
    evidence_ledger_source = _delivery_evidence_ledger_source(paper_root=paper_root, source_root=source_root)
    review_ledger_source = _delivery_review_ledger_source(paper_root=paper_root, source_root=source_root)
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=evidence_ledger_source,
        review_ledger_path=review_ledger_source,
    )
    source_signature = _submission_source_signature(
        paper_root=paper_root,
        source_root=source_root,
        relative_paths=source_relative_paths,
    )
    current_package_readme_payload = sync_current_package_projection(
        paper_root=paper_root,
        source_root=source_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        study_id=study_id,
        stage=f"{publication_profile}_{normalized_stage}",
        source_relative_root=source_relative_root,
        status_line="human-facing current package mirror; not a submission-ready package",
        copied_files=copied_files,
        generated_files=generated_files,
        review_ledger_source=review_ledger_source,
        charter_contract_linkage=charter_contract_linkage,
        quality_gate_status="blocked" if known_blockers else "not_blocked",
        known_blockers=known_blockers,
        source_signature=source_signature,
    )
    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "package_kind": "current_package",
        "can_submit": False,
        "quality_gate_status": "blocked" if known_blockers else "not_blocked",
        "known_blockers": list(known_blockers),
        "generated_from_current_source": True,
        "study_id": study_id,
        "quest_id": quest_id,
        "publication_profile": publication_profile,
        **build_submission_delivery_signature_block(
            source_signature=source_signature,
            source_relative_paths=source_relative_paths,
            source_package_root=source_root,
            human_package_root=current_package_root,
            package_role="human_facing_mirror",
        ),
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
            "package_source_root": str(source_root),
        },
        "controller_authorized_doctor_readme": current_package_readme_payload,
        "charter_contract_linkage": charter_contract_linkage,
        **build_delivery_authority_ref_block(study_root=study_root),
        "surface_roles": build_delivery_surface_roles(
            paper_root=paper_root,
            source_root=source_root,
            manuscript_root=manuscript_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            auxiliary_evidence_root=None,
            journal_submission_mirror_root=None,
        ),
        "targets": {
            "study_root": str(study_root),
            "manuscript_root": str(manuscript_root),
            "current_package_root": str(current_package_root),
            "current_package_zip": str(current_package_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
        "artifact_lifecycle": build_study_delivery_lifecycle_hook(
            study_root=study_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            copied_files=copied_files,
            generated_files=generated_files,
        ),
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    _sync_user_delivery_entry(
        study_root=study_root,
        study_id=study_id,
        stage=f"{publication_profile}_{normalized_stage}",
        source_relative_root=source_relative_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
    )
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
    evidence_ledger_source = _delivery_evidence_ledger_source(paper_root=paper_root, source_root=source_root)
    review_ledger_source = _delivery_review_ledger_source(paper_root=paper_root, source_root=source_root)
    charter_contract_linkage = build_charter_contract_linkage(
        study_root=study_root,
        evidence_ledger_path=evidence_ledger_source,
        review_ledger_path=review_ledger_source,
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
        source=resolve_submission_manifest_path(source_root),
        target=audit_path(journal_package_root, "submission_manifest"),
        category="journal_submission_package",
        copied_files=copied_files,
    )
    if evidence_ledger_source.exists():
        copy_file(
            source=evidence_ledger_source,
            target=audit_path(journal_package_root, "evidence_ledger"),
            category="journal_submission_package",
            copied_files=copied_files,
        )
    if review_ledger_source.exists():
        copy_file(
            source=review_ledger_source,
            target=audit_path(journal_package_root, "review_ledger"),
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
    current_package_readme_payload = sync_current_package_projection(
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
        review_ledger_source=review_ledger_source,
        charter_contract_linkage=charter_contract_linkage,
        source_signature=source_signature,
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
        **build_submission_delivery_signature_block(
            source_signature=source_signature,
            source_relative_paths=source_relative_paths,
            source_package_root=source_root,
            human_package_root=journal_package_root,
            package_role="journal_submission_mirror",
        ),
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
            "package_source_root": str(source_root),
        },
        "controller_authorized_doctor_readme": current_package_readme_payload,
        "charter_contract_linkage": charter_contract_linkage,
        **build_delivery_authority_ref_block(study_root=study_root),
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
        "artifact_lifecycle": build_study_delivery_lifecycle_hook(
            study_root=study_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            copied_files=copied_files,
            generated_files=generated_files,
        ),
    }
    dump_json(journal_package_root / "delivery_manifest.json", manifest)
    _sync_user_delivery_entry(
        study_root=study_root,
        study_id=study_id,
        stage=f"{publication_profile}_{normalized_stage}",
        source_relative_root=source_relative_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        journal_packages_root=journal_package_root.parent,
    )
    return manifest


__all__ = [name for name in globals() if not name.startswith("__")]
