from __future__ import annotations

import argparse
import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.publication_profiles import (
    GENERAL_MEDICAL_JOURNAL_PROFILE,
    is_supported_publication_profile,
    normalize_publication_profile,
)
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context


SYNC_STAGES = ("submission_minimal", "finalize")


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def dump_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def reset_directory(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def can_sync_study_delivery(*, paper_root: Path) -> bool:
    try:
        resolve_paper_root_context(paper_root.resolve())
    except (FileNotFoundError, ValueError):
        return False
    return True


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
) -> None:
    if not source_root.exists():
        raise FileNotFoundError(f"missing delivery source directory: {source_root}")
    for source in sorted(source_root.rglob("*")):
        if not source.is_file():
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


def build_promoted_delivery_readme(*, study_id: str, publication_profile: str) -> str:
    return (
        f"# Study Final Delivery\n\n"
        f"- Study: `{study_id}`\n"
        f"- Sync stage: `{publication_profile}_submission`\n"
        f"- Publication profile: `{publication_profile}`\n"
        f"- Contents:\n"
        f"  - `manuscript.docx`\n"
        f"  - `paper.pdf`\n"
        f"  - `submission_manifest.json`\n"
        f"  - `Supplementary_Material.docx` (when generated)\n"
        f"  - `submission_package/`\n"
        f"  - `submission_package.zip`\n"
        f"  - `journal_package_mirrors/{publication_profile}/`\n\n"
        f"This study-level final delivery is assembled automatically from the primary journal package so the canonical shallow handoff stays aligned with the active target-journal surface.\n"
    )


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


def sync_general_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
) -> dict[str, Any]:
    manuscript_final_root = study_root / "manuscript" / "final"
    artifacts_final_root = study_root / "artifacts" / "final"
    submission_package_root = manuscript_final_root / "submission_package"
    submission_package_zip = manuscript_final_root / "submission_package.zip"

    reset_directory(manuscript_final_root)
    reset_directory(artifacts_final_root)

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile="general_medical_journal")

    copy_file(
        source=source_root / "manuscript.docx",
        target=manuscript_final_root / "manuscript.docx",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=manuscript_final_root / "paper.pdf",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=manuscript_final_root / "submission_manifest.json",
        category="manifest",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=source_root / "figures",
        target_root=artifacts_final_root / "figures",
        category="figures",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=source_root / "tables",
        target_root=artifacts_final_root / "tables",
        category="tables",
        copied_files=copied_files,
    )

    if normalized_stage == "finalize":
        copy_file(
            source=worktree_root / "SUMMARY.md",
            target=manuscript_final_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=worktree_root / "status.md",
            target=manuscript_final_root / "status.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "final_claim_ledger.md",
            target=manuscript_final_root / "final_claim_ledger.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=resolve_finalize_resume_packet_source(paper_root=paper_root, worktree_root=worktree_root),
            target=manuscript_final_root / "finalize_resume_packet.md",
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

    reset_directory(submission_package_root)
    copy_file(
        source=manuscript_final_root / "manuscript.docx",
        target=submission_package_root / "manuscript.docx",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=manuscript_final_root / "paper.pdf",
        target=submission_package_root / "paper.pdf",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=manuscript_final_root / "submission_manifest.json",
        target=submission_package_root / "submission_manifest.json",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=artifacts_final_root / "figures",
        target_root=submission_package_root / "figures",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=artifacts_final_root / "tables",
        target_root=submission_package_root / "tables",
        category="submission_package",
        copied_files=copied_files,
    )
    package_readme_path = submission_package_root / "README.md"
    write_text(
        package_readme_path,
        build_submission_package_readme(
            study_id=study_id,
            stage=normalized_stage,
            publication_profile="general_medical_journal",
        ),
    )
    generated_files.append(
        {
            "category": "submission_package",
            "path": str(package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(
        source_root=submission_package_root,
        output_path=submission_package_zip,
    )
    generated_files.append(
        {
            "category": "submission_package",
            "path": str(submission_package_zip.resolve()),
        }
    )

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": "general_medical_journal",
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
        },
        "targets": {
            "study_root": str(study_root),
            "manuscript_final_root": str(manuscript_final_root),
            "artifacts_final_root": str(artifacts_final_root),
            "submission_package_root": str(submission_package_root),
            "submission_package_zip": str(submission_package_zip),
        },
        "copied_files": copied_files,
        "generated_files": generated_files,
    }
    dump_json(manuscript_final_root / "delivery_manifest.json", manifest)
    return manifest


def sync_journal_specific_delivery(
    *,
    paper_root: Path,
    worktree_root: Path,
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
) -> dict[str, Any]:
    manuscript_final_root = study_root / "manuscript" / "final"
    journal_package_root = manuscript_final_root / "journal_packages" / publication_profile
    journal_package_zip = manuscript_final_root / f"{publication_profile}_submission_package.zip"
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)

    journal_package_root.parent.mkdir(parents=True, exist_ok=True)
    reset_directory(journal_package_root)

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
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

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": normalized_stage,
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": publication_profile,
        "source": {
            "paper_root": str(paper_root),
            "worktree_root": str(worktree_root),
            "package_source_root": str(source_root),
        },
        "targets": {
            "study_root": str(study_root),
            "manuscript_final_root": str(manuscript_final_root),
            "journal_package_root": str(journal_package_root),
            "journal_package_zip": str(journal_package_zip),
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
    study_id: str,
    study_root: Path,
    normalized_stage: str,
    publication_profile: str,
) -> dict[str, Any]:
    manuscript_final_root = study_root / "manuscript" / "final"
    artifacts_final_root = study_root / "artifacts" / "final"
    submission_package_root = manuscript_final_root / "submission_package"
    submission_package_zip = manuscript_final_root / "submission_package.zip"
    mirror_root = manuscript_final_root / "journal_package_mirrors" / publication_profile
    source_root = build_submission_source_root(paper_root=paper_root, publication_profile=publication_profile)

    reset_directory(manuscript_final_root)
    reset_directory(artifacts_final_root)

    copied_files: list[dict[str, str]] = []
    generated_files: list[dict[str, str]] = []
    copy_file(
        source=source_root / "manuscript.docx",
        target=manuscript_final_root / "manuscript.docx",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "paper.pdf",
        target=manuscript_final_root / "paper.pdf",
        category="manuscript",
        copied_files=copied_files,
    )
    copy_file(
        source=source_root / "submission_manifest.json",
        target=manuscript_final_root / "submission_manifest.json",
        category="manifest",
        copied_files=copied_files,
    )
    supplementary_docx = source_root / "Supplementary_Material.docx"
    if supplementary_docx.exists():
        copy_file(
            source=supplementary_docx,
            target=manuscript_final_root / "Supplementary_Material.docx",
            category="manuscript",
            copied_files=copied_files,
        )
    copy_tree(
        source_root=source_root / "figures",
        target_root=artifacts_final_root / "figures",
        category="figures",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=source_root / "tables",
        target_root=artifacts_final_root / "tables",
        category="tables",
        copied_files=copied_files,
    )

    if normalized_stage == "finalize":
        copy_file(
            source=worktree_root / "SUMMARY.md",
            target=manuscript_final_root / "SUMMARY.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=worktree_root / "status.md",
            target=manuscript_final_root / "status.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=paper_root / "final_claim_ledger.md",
            target=manuscript_final_root / "final_claim_ledger.md",
            category="closeout",
            copied_files=copied_files,
        )
        copy_file(
            source=resolve_finalize_resume_packet_source(paper_root=paper_root, worktree_root=worktree_root),
            target=manuscript_final_root / "finalize_resume_packet.md",
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

    readme_path = manuscript_final_root / "README.md"
    write_text(
        readme_path,
        build_promoted_delivery_readme(study_id=study_id, publication_profile=publication_profile),
    )
    generated_files.append(
        {
            "category": "delivery_readme",
            "path": str(readme_path.resolve()),
        }
    )

    reset_directory(submission_package_root)
    copy_file(
        source=manuscript_final_root / "manuscript.docx",
        target=submission_package_root / "manuscript.docx",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=manuscript_final_root / "paper.pdf",
        target=submission_package_root / "paper.pdf",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_file(
        source=manuscript_final_root / "submission_manifest.json",
        target=submission_package_root / "submission_manifest.json",
        category="submission_package",
        copied_files=copied_files,
    )
    if supplementary_docx.exists():
        copy_file(
            source=manuscript_final_root / "Supplementary_Material.docx",
            target=submission_package_root / "Supplementary_Material.docx",
            category="submission_package",
            copied_files=copied_files,
        )
    copy_tree(
        source_root=artifacts_final_root / "figures",
        target_root=submission_package_root / "figures",
        category="submission_package",
        copied_files=copied_files,
    )
    copy_tree(
        source_root=artifacts_final_root / "tables",
        target_root=submission_package_root / "tables",
        category="submission_package",
        copied_files=copied_files,
    )
    package_readme_path = submission_package_root / "README.md"
    write_text(
        package_readme_path,
        build_submission_package_readme(
            study_id=study_id,
            stage=f"{publication_profile}_submission",
            publication_profile=publication_profile,
        ),
    )
    generated_files.append(
        {
            "category": "submission_package",
            "path": str(package_readme_path.resolve()),
        }
    )
    build_zip_from_directory(
        source_root=submission_package_root,
        output_path=submission_package_zip,
    )
    generated_files.append(
        {
            "category": "submission_package",
            "path": str(submission_package_zip.resolve()),
        }
    )

    reset_directory(mirror_root)
    copy_tree(
        source_root=source_root,
        target_root=mirror_root,
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
        "quest_id": study_id,
        "publication_profile": publication_profile,
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
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

    manifest = {
        "schema_version": 1,
        "generated_at": utc_now(),
        "stage": f"{publication_profile}_submission",
        "study_id": study_id,
        "quest_id": study_id,
        "publication_profile": publication_profile,
        "source": {
            "paper_root": str(paper_root),
            "package_source_root": str(source_root),
        },
        "targets": {
            "study_root": str(study_root),
            "manuscript_final_root": str(manuscript_final_root),
            "artifacts_final_root": str(artifacts_final_root),
            "submission_package_root": str(submission_package_root),
            "submission_package_zip": str(submission_package_zip),
            "journal_package_mirror_root": str(mirror_root),
        },
        "copied_files": [
            item
            for item in copied_files
            if item["category"] != "journal_submission_mirror"
        ],
        "generated_files": generated_files,
    }
    dump_json(manuscript_final_root / "delivery_manifest.json", manifest)
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

    context = resolve_paper_root_context(paper_root.resolve())
    paper_root = context.paper_root
    worktree_root = context.worktree_root
    study_id = context.study_id
    study_root = context.study_root

    if normalized_publication_profile == GENERAL_MEDICAL_JOURNAL_PROFILE:
        return sync_general_delivery(
            paper_root=paper_root,
            worktree_root=worktree_root,
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
            study_id=study_id,
            study_root=study_root,
            normalized_stage=normalized_stage,
            publication_profile=normalized_publication_profile,
        )

    return sync_journal_specific_delivery(
        paper_root=paper_root,
        worktree_root=worktree_root,
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


if __name__ == "__main__":
    raise SystemExit(main())
