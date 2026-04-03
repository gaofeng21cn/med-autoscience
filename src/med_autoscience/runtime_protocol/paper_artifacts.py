from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.publication_profiles import is_supported_publication_profile, normalize_publication_profile

from .quest_state import find_latest


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def resolve_latest_paper_root(quest_root: Path) -> Path:
    latest_manifest = resolve_paper_bundle_manifest(quest_root)
    if latest_manifest is None:
        raise FileNotFoundError(f"No paper_bundle_manifest.json found under {quest_root}")
    return latest_manifest.parent


def resolve_paper_bundle_manifest(quest_root: Path) -> Path | None:
    resolved_quest_root = _resolve_path(quest_root)
    candidates: list[Path] = []
    patterns = [
        ".ds/worktrees/*/paper/paper_bundle_manifest.json",
        "paper/paper_bundle_manifest.json",
    ]
    for pattern in patterns:
        candidates.extend(resolved_quest_root.glob(pattern))
    return find_latest(candidates)


def resolve_submission_minimal_manifest(paper_bundle_manifest_path: Path | None) -> Path | None:
    if paper_bundle_manifest_path is None:
        return None
    candidate = _resolve_path(paper_bundle_manifest_path).parent / "submission_minimal" / "submission_manifest.json"
    return candidate if candidate.exists() else None


def resolve_artifact_manifest_from_main_result(main_result: dict[str, Any]) -> Path | None:
    evidence_paths = [str(item) for item in (main_result.get("evidence_paths") or [])]
    worktree_root = _resolve_path(Path(str(main_result["worktree_root"])))
    for rel in evidence_paths:
        candidate = worktree_root / rel
        if candidate.name == "artifact_manifest.json" and candidate.exists():
            return candidate
    return None


def resolve_artifact_manifest(main_result: dict[str, Any]) -> Path | None:
    return resolve_artifact_manifest_from_main_result(main_result)


def resolve_submission_minimal_output_paths(
    *,
    paper_bundle_manifest_path: Path | None,
    submission_minimal_manifest: dict[str, Any] | None,
) -> tuple[Path | None, Path | None]:
    if paper_bundle_manifest_path is None or submission_minimal_manifest is None:
        return None, None
    workspace_root = _resolve_path(paper_bundle_manifest_path).parent.parent
    manuscript = submission_minimal_manifest.get("manuscript") or {}
    docx_relpath = str(manuscript.get("docx_path") or "").strip()
    pdf_relpath = str(manuscript.get("pdf_path") or "").strip()
    docx_path = workspace_root / docx_relpath if docx_relpath else None
    pdf_path = workspace_root / pdf_relpath if pdf_relpath else None
    return docx_path, pdf_path


def resolve_managed_submission_surface_roots(paper_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = _resolve_path(paper_root)
    if not resolved_paper_root.exists():
        return tuple()

    roots: list[Path] = []
    submission_minimal_root = resolved_paper_root / "submission_minimal"
    if submission_minimal_root.is_dir():
        roots.append(submission_minimal_root)

    journal_submissions_root = resolved_paper_root / "journal_submissions"
    if journal_submissions_root.is_dir():
        for candidate in sorted(journal_submissions_root.iterdir()):
            if not candidate.is_dir():
                continue
            if is_supported_publication_profile(candidate.name):
                roots.append(candidate.resolve())

    return tuple(root.resolve() for root in roots)


def find_unmanaged_submission_surface_roots(paper_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = _resolve_path(paper_root)
    if not resolved_paper_root.exists():
        return tuple()

    roots: list[Path] = []
    for candidate in sorted(resolved_paper_root.iterdir()):
        if not candidate.is_dir():
            continue
        if candidate.name.startswith("submission_") and candidate.name != "submission_minimal":
            roots.append(candidate.resolve())

    journal_submissions_root = resolved_paper_root / "journal_submissions"
    if journal_submissions_root.is_dir():
        for candidate in sorted(journal_submissions_root.iterdir()):
            if not candidate.is_dir():
                continue
            normalized_profile = normalize_publication_profile(candidate.name)
            if not is_supported_publication_profile(normalized_profile):
                roots.append(candidate.resolve())

    return tuple(roots)
