from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers.delivery_artifact_authority import build_study_delivery_lifecycle_hook
from med_autoscience.controllers.submission_package_layout import (
    audit_path,
    build_submission_delivery_signature_block,
    resolve_evidence_ledger_path,
    resolve_review_ledger_path,
    resolve_submission_manifest_path,
)
from med_autoscience.policies import medical_publication_surface as medical_surface_policy

from .authority_refs import build_delivery_authority_ref_block
from .current_package_projection import sync_current_package_projection
from .delivery_descriptions import copy_review_ledger_to_delivery_root
from .staging_and_sources import (
    build_artifacts_finalize_readme,
    build_artifacts_root_readme,
    build_authority_source_relative_root,
    build_charter_contract_linkage,
    build_delivery_surface_roles,
    build_promoted_delivery_readme,
    build_submission_package_readme,
    build_submission_source_root,
    build_zip_from_directory,
    copy_file,
    copy_tree,
    dump_json,
    remove_directory,
    reset_directory,
    resolve_finalize_resume_packet_source,
    utc_now,
    write_text,
)
from .submission_delivery_descriptions import (
    _submission_source_relative_paths,
    _submission_source_signature,
)
from .external_entry import _sync_user_delivery_entry


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


def sync_promoted_journal_delivery(
    *,
    paper_root: Path,
    context_root: Path,
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
        source=resolve_submission_manifest_path(source_root),
        target=audit_path(manuscript_root, "submission_manifest"),
        category="manifest",
        copied_files=copied_files,
    )
    if evidence_ledger_source.exists():
        copy_file(
            source=evidence_ledger_source,
            target=audit_path(manuscript_root, "evidence_ledger"),
            category="evidence_ledger",
            copied_files=copied_files,
        )
    if review_ledger_source.exists():
        copy_file(
            source=review_ledger_source,
            target=audit_path(manuscript_root, "review_ledger"),
            category="review_surface",
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
            source=context_root / "SUMMARY.md",
            target=manuscript_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=context_root / "status.md",
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
            source=resolve_finalize_resume_packet_source(paper_root=paper_root, context_root=context_root),
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

    current_package_readme_payload = sync_current_package_projection(
        paper_root=paper_root,
        source_root=source_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        primary_artifact_delivery_root=manuscript_root,
        study_id=study_id,
        stage=f"{publication_profile}_submission",
        source_relative_root=source_relative_root,
        status_line="promoted human-facing manuscript handoff surface",
        copied_files=copied_files,
        generated_files=generated_files,
        review_ledger_source=review_ledger_source,
        charter_contract_linkage=charter_contract_linkage,
        source_signature=source_signature,
    )
    submission_root = study_root / "submission"
    if source_root.resolve() == submission_root.resolve():
        submission_zip = study_root / "submission.zip"
        build_zip_from_directory(source_root=source_root, output_path=submission_zip)
        generated_files.append(
            {
                "category": "submission_surface",
                "path": str(submission_zip.resolve()),
            }
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
        source=evidence_ledger_source,
        target=audit_path(mirror_root, "evidence_ledger"),
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
        **build_submission_delivery_signature_block(
            source_signature=source_signature,
            source_relative_paths=source_relative_paths,
            source_package_root=source_root,
            human_package_root=mirror_root,
            package_role="journal_submission_mirror",
        ),
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
        "controller_authorized_doctor_readme": current_package_readme_payload,
        "charter_contract_linkage": charter_contract_linkage,
        **build_delivery_authority_ref_block(study_root=study_root),
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
        "artifact_lifecycle": build_study_delivery_lifecycle_hook(
            study_root=study_root,
            copied_files=[
                item
                for item in copied_files
                if item["category"] == "journal_submission_mirror"
            ],
            generated_files=mirror_generated_files,
        ),
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
        "package_kind": "submission_ready_package",
        "can_submit": True,
        "quality_gate_status": "clear",
        "known_blockers": [],
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
            "package_source_root": str(source_root),
        },
        "charter_contract_linkage": charter_contract_linkage,
        **build_delivery_authority_ref_block(study_root=study_root),
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
        "artifact_lifecycle": build_study_delivery_lifecycle_hook(
            study_root=study_root,
            current_package_root=current_package_root,
            current_package_zip=current_package_zip,
            copied_files=[
                item
                for item in copied_files
                if item["category"] != "journal_submission_mirror"
            ],
            generated_files=generated_files,
        ),
    }
    dump_json(manuscript_root / "delivery_manifest.json", manifest)
    _sync_user_delivery_entry(
        study_root=study_root,
        study_id=study_id,
        stage=f"{publication_profile}_submission",
        source_relative_root=source_relative_root,
        current_package_root=current_package_root,
        current_package_zip=current_package_zip,
        journal_package_mirrors_root=mirror_root.parent,
    )
    return manifest


__all__ = ["sync_promoted_journal_delivery"]
