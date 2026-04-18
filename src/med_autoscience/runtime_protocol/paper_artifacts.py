from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.publication_profiles import is_supported_publication_profile, normalize_publication_profile

from .quest_state import find_latest


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _load_json_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


ARCHIVED_REFERENCE_ONLY_SURFACE_STATUS = "archived_reference_only"
SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS = frozenset(
    {
        "author_metadata",
        "author_affiliations",
        "corresponding_author",
        "corresponding_author_contact",
        "ethics_statement",
        "human_subjects_consent_statement",
        "ai_declaration",
        "funding_statement",
        "conflict_of_interest_statement",
        "data_availability_statement",
        "acknowledgments",
    }
)
_SUBMISSION_METADATA_ONLY_STATUS_TOKENS = (
    "external_metadata_gap",
    "external_metadata_blocker",
    "author_metadata_and_submission_declarations_pending",
)


def resolve_latest_paper_root(quest_root: Path) -> Path:
    latest_manifest = resolve_paper_bundle_manifest(quest_root)
    if latest_manifest is None:
        raise FileNotFoundError(f"No paper_bundle_manifest.json found under {quest_root}")
    return latest_manifest.parent


def _projected_manifest_has_authoritative_paper_line(quest_root: Path, manifest_path: Path) -> bool:
    return _resolve_projected_manifest_authoritative_paper_root(quest_root, manifest_path) is not None


def _resolve_projected_manifest_authoritative_paper_root(quest_root: Path, manifest_path: Path) -> Path | None:
    projected_root = _resolve_path(quest_root) / "paper"
    projected_manifest_path = projected_root / "paper_bundle_manifest.json"
    if _resolve_path(manifest_path) != projected_manifest_path:
        return None
    manifest_payload = _load_json_mapping(projected_manifest_path)
    paper_line_state = _load_json_mapping(projected_root / "paper_line_state.json")
    if manifest_payload is None or paper_line_state is None:
        return None
    manifest_branch = str(manifest_payload.get("paper_branch") or "").strip()
    line_branch = str(paper_line_state.get("paper_branch") or "").strip()
    if not manifest_branch or not line_branch or manifest_branch != line_branch:
        return None
    paper_root_raw = str(paper_line_state.get("paper_root") or "").strip()
    if not paper_root_raw:
        return None
    candidate = Path(paper_root_raw).expanduser()
    if not candidate.is_absolute():
        candidate = (projected_root.parent / candidate).resolve()
    else:
        candidate = candidate.resolve()
    if not candidate.exists() or candidate.name != "paper":
        return None
    worktree_root = candidate.parent
    if worktree_root.parent.name != "worktrees" or worktree_root.parent.parent.name != ".ds":
        return None
    return candidate


def _resolve_authoritative_paper_root_from_bundle_manifest_path(paper_bundle_manifest_path: Path) -> Path:
    resolved_manifest_path = _resolve_path(paper_bundle_manifest_path)
    paper_root = resolved_manifest_path.parent
    try:
        quest_root = resolved_manifest_path.parents[1]
    except IndexError:
        return paper_root
    authoritative_projected_root = _resolve_projected_manifest_authoritative_paper_root(quest_root, resolved_manifest_path)
    if authoritative_projected_root is not None:
        return authoritative_projected_root
    return paper_root


def _paper_bundle_manifest_rank(quest_root: Path, manifest_path: Path) -> tuple[int, float]:
    resolved_manifest = _resolve_path(manifest_path)
    try:
        relative_parts = resolved_manifest.relative_to(quest_root).parts
    except ValueError:
        relative_parts = resolved_manifest.parts
    if relative_parts == ("paper", "paper_bundle_manifest.json"):
        if _projected_manifest_has_authoritative_paper_line(quest_root, resolved_manifest):
            return (3, resolved_manifest.stat().st_mtime)
        return (1, resolved_manifest.stat().st_mtime)
    if len(relative_parts) >= 4 and relative_parts[:2] == (".ds", "worktrees"):
        worktree_name = relative_parts[2]
        if worktree_name.startswith("paper-"):
            return (2, resolved_manifest.stat().st_mtime)
    return (0, resolved_manifest.stat().st_mtime)


def resolve_paper_bundle_manifest(quest_root: Path) -> Path | None:
    resolved_quest_root = _resolve_path(quest_root)
    candidates: list[Path] = []
    patterns = [
        ".ds/worktrees/*/paper/paper_bundle_manifest.json",
        "paper/paper_bundle_manifest.json",
    ]
    for pattern in patterns:
        candidates.extend(resolved_quest_root.glob(pattern))
    if not candidates:
        return None
    return max(candidates, key=lambda item: _paper_bundle_manifest_rank(resolved_quest_root, item))


def resolve_submission_minimal_manifest(paper_bundle_manifest_path: Path | None) -> Path | None:
    if paper_bundle_manifest_path is None:
        return None
    candidate = (
        _resolve_authoritative_paper_root_from_bundle_manifest_path(paper_bundle_manifest_path)
        / "submission_minimal"
        / "submission_manifest.json"
    )
    return candidate if candidate.exists() else None


def resolve_submission_checklist_path(paper_bundle_manifest_path: Path | None) -> Path | None:
    if paper_bundle_manifest_path is None:
        return None
    candidate = _resolve_path(paper_bundle_manifest_path).parent / "review" / "submission_checklist.json"
    return candidate if candidate.exists() else None


def load_submission_checklist(paper_bundle_manifest_path: Path | None) -> dict[str, Any] | None:
    checklist_path = resolve_submission_checklist_path(paper_bundle_manifest_path)
    if checklist_path is None:
        return None
    try:
        payload = json.loads(checklist_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def normalize_submission_checklist_blocking_item_keys(payload: dict[str, Any] | None) -> tuple[str, ...]:
    if not isinstance(payload, dict):
        return ()
    raw_items = payload.get("blocking_items")
    if not isinstance(raw_items, list):
        return ()
    normalized: list[str] = []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        item_key = str(item.get("id") or item.get("key") or "").strip()
        if item_key:
            normalized.append(item_key)
    return tuple(normalized)


def submission_checklist_requires_external_metadata(payload: dict[str, Any] | None) -> bool:
    if not isinstance(payload, dict):
        return False
    blocking_item_ids = normalize_submission_checklist_blocking_item_keys(payload)
    if blocking_item_ids:
        return all(item_id in SUBMISSION_METADATA_ONLY_BLOCKING_ITEM_KEYS for item_id in blocking_item_ids)
    for key in ("overall_status", "package_status", "status"):
        normalized = str(payload.get(key) or "").strip().lower()
        if not normalized:
            continue
        if any(token in normalized for token in _SUBMISSION_METADATA_ONLY_STATUS_TOKENS):
            return True
    return False


def load_submission_surface_manifest(surface_root: Path) -> dict[str, Any] | None:
    manifest_path = _resolve_path(surface_root) / "submission_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None
    return payload if isinstance(payload, dict) else None


def _resolve_workspace_relative_path(*, paper_root: Path, raw_path: str) -> Path | None:
    normalized = str(raw_path or "").strip()
    if not normalized:
        return None
    candidate = Path(normalized).expanduser()
    if candidate.is_absolute():
        return candidate.resolve()
    return (_resolve_path(paper_root).parent / candidate).resolve()


def _is_path_within(root: Path, candidate: Path) -> bool:
    try:
        candidate.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def resolve_managed_submission_manifest_paths(paper_root: Path) -> tuple[Path, ...]:
    manifest_paths: list[Path] = []
    for root in resolve_managed_submission_surface_roots(paper_root):
        manifest_path = root / "submission_manifest.json"
        if manifest_path.exists():
            manifest_paths.append(manifest_path.resolve())
    return tuple(manifest_paths)


def is_archived_reference_only_submission_surface_manifest(
    *,
    paper_root: Path,
    surface_root: Path,
    manifest: dict[str, Any] | None,
) -> bool:
    if not isinstance(manifest, dict):
        return False
    resolved_paper_root = _resolve_path(paper_root)
    surface_status = str(manifest.get("surface_status") or "").strip().lower()
    if surface_status != ARCHIVED_REFERENCE_ONLY_SURFACE_STATUS:
        return False
    archive_reason = str(manifest.get("archive_reason") or "").strip()
    active_manifest_raw = str(manifest.get("active_managed_submission_manifest_path") or "").strip()
    if not archive_reason or not active_manifest_raw:
        return False
    active_manifest_path = _resolve_workspace_relative_path(paper_root=paper_root, raw_path=active_manifest_raw)
    if active_manifest_path is None or not active_manifest_path.exists():
        return False
    active_manifest_path = active_manifest_path.resolve()
    if not _is_path_within(resolved_paper_root, active_manifest_path):
        return False
    if active_manifest_path not in set(resolve_managed_submission_manifest_paths(resolved_paper_root)):
        return False
    active_manifest = load_submission_surface_manifest(active_manifest_path.parent)
    if not isinstance(active_manifest, dict):
        return False
    active_publication_profile = str(active_manifest.get("publication_profile") or "").strip()
    if not is_supported_publication_profile(active_publication_profile):
        return False
    return active_manifest_path.parent.resolve() != _resolve_path(surface_root)


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
    paper_root = _resolve_authoritative_paper_root_from_bundle_manifest_path(paper_bundle_manifest_path)
    workspace_root = paper_root.parent
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


def resolve_archived_submission_surface_roots(paper_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = _resolve_path(paper_root)
    if not resolved_paper_root.exists():
        return tuple()

    archived_roots: list[Path] = []
    journal_submissions_root = resolved_paper_root / "journal_submissions"
    journal_submission_candidates = (
        [candidate for candidate in sorted(journal_submissions_root.iterdir()) if candidate.is_dir()]
        if journal_submissions_root.is_dir()
        else []
    )
    for candidate in sorted(resolved_paper_root.iterdir()):
        if not candidate.is_dir():
            continue
        if candidate.name.startswith("submission_") and candidate.name != "submission_minimal":
            manifest = load_submission_surface_manifest(candidate)
            if is_archived_reference_only_submission_surface_manifest(
                paper_root=resolved_paper_root,
                surface_root=candidate,
                manifest=manifest,
            ):
                archived_roots.append(candidate.resolve())
    for candidate in journal_submission_candidates:
        normalized_profile = normalize_publication_profile(candidate.name)
        if is_supported_publication_profile(normalized_profile):
            continue
        manifest = load_submission_surface_manifest(candidate)
        if is_archived_reference_only_submission_surface_manifest(
            paper_root=resolved_paper_root,
            surface_root=candidate,
            manifest=manifest,
        ):
            archived_roots.append(candidate.resolve())
    return tuple(archived_roots)


def find_unmanaged_submission_surface_roots(paper_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = _resolve_path(paper_root)
    if not resolved_paper_root.exists():
        return tuple()

    archived_roots = {path.resolve() for path in resolve_archived_submission_surface_roots(resolved_paper_root)}
    roots: list[Path] = []
    for candidate in sorted(resolved_paper_root.iterdir()):
        if not candidate.is_dir():
            continue
        if candidate.name.startswith("submission_") and candidate.name != "submission_minimal":
            if candidate.resolve() in archived_roots:
                continue
            roots.append(candidate.resolve())

    journal_submissions_root = resolved_paper_root / "journal_submissions"
    if journal_submissions_root.is_dir():
        for candidate in sorted(journal_submissions_root.iterdir()):
            if not candidate.is_dir():
                continue
            if candidate.resolve() in archived_roots:
                continue
            normalized_profile = normalize_publication_profile(candidate.name)
            if not is_supported_publication_profile(normalized_profile):
                roots.append(candidate.resolve())

    return tuple(roots)
