from __future__ import annotations

from pathlib import Path
from typing import Any


def find_latest(paths: list[Path]) -> Path | None:
    if not paths:
        return None
    return max(paths, key=lambda item: item.stat().st_mtime)


def resolve_latest_paper_root(quest_root: Path) -> Path:
    candidates = list(quest_root.glob(".ds/worktrees/*/paper/paper_bundle_manifest.json"))
    candidates.extend(quest_root.glob("paper/paper_bundle_manifest.json"))
    latest_manifest = find_latest(candidates)
    if latest_manifest is None:
        raise FileNotFoundError(f"No paper_bundle_manifest.json found under {quest_root}")
    return latest_manifest.parent


def resolve_paper_bundle_manifest(quest_root: Path) -> Path | None:
    candidates: list[Path] = []
    patterns = [
        ".ds/worktrees/*/paper/paper_bundle_manifest.json",
        "paper/paper_bundle_manifest.json",
    ]
    for pattern in patterns:
        candidates.extend(quest_root.glob(pattern))
    return find_latest(candidates)


def resolve_submission_minimal_manifest(paper_bundle_manifest_path: Path | None) -> Path | None:
    if paper_bundle_manifest_path is None:
        return None
    candidate = paper_bundle_manifest_path.parent / "submission_minimal" / "submission_manifest.json"
    return candidate if candidate.exists() else None


def resolve_artifact_manifest(main_result: dict[str, Any]) -> Path | None:
    evidence_paths = [str(item) for item in (main_result.get("evidence_paths") or [])]
    worktree_root = Path(str(main_result["worktree_root"]))
    for rel in evidence_paths:
        candidate = worktree_root / rel
        if candidate.name == "artifact_manifest.json" and candidate.exists():
            return candidate
    return None


def resolve_submission_minimal_output_paths(
    *,
    paper_bundle_manifest_path: Path | None,
    submission_minimal_manifest: dict[str, Any] | None,
) -> tuple[Path | None, Path | None]:
    if paper_bundle_manifest_path is None or submission_minimal_manifest is None:
        return None, None
    workspace_root = paper_bundle_manifest_path.parent.parent
    manuscript = submission_minimal_manifest.get("manuscript") or {}
    docx_relpath = str(manuscript.get("docx_path") or "").strip()
    pdf_relpath = str(manuscript.get("pdf_path") or "").strip()
    docx_path = workspace_root / docx_relpath if docx_relpath else None
    pdf_path = workspace_root / pdf_relpath if pdf_relpath else None
    return docx_path, pdf_path
