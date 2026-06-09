from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from med_autoscience.publication_profiles import is_supported_publication_profile, normalize_publication_profile
from med_autoscience.runtime_protocol.topology import resolve_study_root_from_quest_root

from .artifact_authority import artifact_authority_record
from .submission_package_layout import (
    legacy_submission_manifest_path,
    resolve_submission_manifest_path as resolve_package_submission_manifest_path,
    submission_manifest_path as v2_submission_manifest_path,
)


_CANONICAL_STUDY_PAPER_REQUIRED_SURFACES = (
    "paper_bundle_manifest.json",
    "draft.md",
    "medical_manuscript_blueprint.json",
    "medical_prose_review.json",
    "claim_evidence_map.json",
    "results_narrative_map.json",
    "figure_semantics_manifest.json",
    "figures/figure_catalog.json",
    "tables/table_catalog.json",
)
_STAGE_NATIVE_BODY_PAPER_ROOT_RELPATH = (
    Path("artifacts")
    / "stage_outputs"
    / "_body_authority"
    / "paper_authority_cutover"
    / "current_body"
    / "paper"
)


def _resolve_path(path: Path) -> Path:
    return Path(path).expanduser().resolve()


def _load_json_mapping(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


ARCHIVED_REFERENCE_ONLY_SURFACE_STATUS = "archived_reference_only"
ARCHIVED_REFERENCE_ONLY_ARCHIVE_REASON = "Retained only as a historical journal-target package."
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


def resolve_latest_paper_root(
    quest_root: Path,
) -> Path:
    latest_manifest = resolve_paper_bundle_manifest(quest_root)
    if latest_manifest is None:
        raise FileNotFoundError(f"No paper_bundle_manifest.json found under {quest_root}")
    return _resolve_authoritative_paper_root_from_bundle_manifest_path(latest_manifest)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bundle_manifest_branch(manifest_payload: dict[str, Any] | None) -> str | None:
    if not isinstance(manifest_payload, dict):
        return None
    return _non_empty_text(manifest_payload.get("paper_branch"))


def _paper_line_branch(paper_line_state: dict[str, Any] | None) -> str | None:
    if not isinstance(paper_line_state, dict):
        return None
    return _non_empty_text(paper_line_state.get("paper_branch"))


def _resolve_bound_study_paper_bundle_manifest_by_branch(
    *,
    quest_root: Path,
    paper_branch: str | None,
) -> Path | None:
    try:
        binding = resolve_study_root_from_quest_root(quest_root)
    except (FileNotFoundError, ValueError):
        return None
    if binding is None:
        return None
    _, study_root = binding
    for paper_root in _bound_study_paper_roots(study_root):
        candidate = paper_root / "paper_bundle_manifest.json"
        if not candidate.exists():
            continue
        payload = _load_json_mapping(candidate)
        candidate_branch = _bundle_manifest_branch(payload)
        if candidate_branch != paper_branch:
            continue
        return candidate.resolve()
    return None


def _is_complete_bound_study_canonical_paper_root(paper_root: Path) -> bool:
    return all((paper_root / relpath).exists() for relpath in _CANONICAL_STUDY_PAPER_REQUIRED_SURFACES)


def _bound_study_paper_roots(study_root: Path) -> tuple[Path, ...]:
    resolved_study_root = _resolve_path(study_root)
    return (
        resolved_study_root / _STAGE_NATIVE_BODY_PAPER_ROOT_RELPATH,
        resolved_study_root / "paper",
    )


def _resolve_complete_bound_study_paper_bundle_manifest(quest_root: Path) -> Path | None:
    try:
        binding = resolve_study_root_from_quest_root(quest_root)
    except (FileNotFoundError, ValueError):
        return None
    if binding is None:
        return None
    _, study_root = binding
    for paper_root in _bound_study_paper_roots(study_root):
        candidate = paper_root / "paper_bundle_manifest.json"
        if not candidate.exists() or not _is_complete_bound_study_canonical_paper_root(paper_root):
            continue
        return candidate.resolve()
    return None


def _prefer_newer_bound_study_manifest(
    *,
    quest_root: Path,
    current_manifest_path: Path,
    paper_branch: str | None,
) -> Path:
    study_manifest = _resolve_bound_study_paper_bundle_manifest_by_branch(
        quest_root=quest_root,
        paper_branch=paper_branch,
    )
    if study_manifest is None:
        return current_manifest_path.resolve()
    resolved_current = current_manifest_path.resolve()
    if study_manifest == resolved_current:
        return resolved_current
    if study_manifest.stat().st_mtime > resolved_current.stat().st_mtime:
        return study_manifest
    return resolved_current


def _projected_manifest_has_authoritative_paper_line(quest_root: Path, manifest_path: Path) -> bool:
    return _resolve_projected_manifest_authoritative_paper_root(quest_root, manifest_path) is not None


def _resolve_projected_manifest_authoritative_paper_root(quest_root: Path, manifest_path: Path) -> Path | None:
    return _resolve_projected_manifest_authoritative_paper_root_impl(
        quest_root=quest_root,
        manifest_path=manifest_path,
    )


def _resolve_projected_manifest_authoritative_paper_root_impl(
    *,
    quest_root: Path,
    manifest_path: Path,
) -> Path | None:
    projected_root = _resolve_path(quest_root) / "paper"
    projected_manifest_path = projected_root / "paper_bundle_manifest.json"
    if _resolve_path(manifest_path) != projected_manifest_path:
        return None
    manifest_payload = _load_json_mapping(projected_manifest_path)
    paper_line_state = _load_json_mapping(projected_root / "paper_line_state.json")
    if manifest_payload is None or paper_line_state is None:
        return None
    manifest_branch = _bundle_manifest_branch(manifest_payload)
    line_branch = _paper_line_branch(paper_line_state)
    if manifest_branch is not None and line_branch is not None and manifest_branch != line_branch:
        authoritative_manifest = _resolve_bound_study_paper_bundle_manifest_by_branch(
            quest_root=quest_root,
            paper_branch=manifest_branch,
        )
        if authoritative_manifest is not None:
            return authoritative_manifest.parent.resolve()
    return None


def _resolve_authoritative_paper_root_from_bundle_manifest_path(
    paper_bundle_manifest_path: Path,
) -> Path:
    resolved_manifest_path = _resolve_path(paper_bundle_manifest_path)
    paper_root = resolved_manifest_path.parent
    try:
        quest_root = resolved_manifest_path.parents[1]
    except IndexError:
        return paper_root
    authoritative_projected_root = _resolve_projected_manifest_authoritative_paper_root_impl(
        quest_root=quest_root,
        manifest_path=resolved_manifest_path,
    )
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
    return (0, resolved_manifest.stat().st_mtime)


def resolve_paper_bundle_manifest(quest_root: Path) -> Path | None:
    resolved_quest_root = _resolve_path(quest_root)
    complete_study_manifest = _resolve_complete_bound_study_paper_bundle_manifest(resolved_quest_root)
    if complete_study_manifest is not None:
        return complete_study_manifest
    candidates: list[Path] = []
    patterns = ["paper/paper_bundle_manifest.json"]
    for pattern in patterns:
        candidates.extend(resolved_quest_root.glob(pattern))
    if not candidates:
        return None
    selected = max(candidates, key=lambda item: _paper_bundle_manifest_rank(resolved_quest_root, item)).resolve()
    selected_payload = _load_json_mapping(selected)
    return _prefer_newer_bound_study_manifest(
        quest_root=resolved_quest_root,
        current_manifest_path=selected,
        paper_branch=_bundle_manifest_branch(selected_payload),
    )


def resolve_submission_minimal_manifest(paper_bundle_manifest_path: Path | None) -> Path | None:
    if paper_bundle_manifest_path is None:
        return None
    candidate = resolve_package_submission_manifest_path(
        _resolve_authoritative_paper_root_from_bundle_manifest_path(paper_bundle_manifest_path)
        / "submission_minimal"
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
    manifest_path = resolve_package_submission_manifest_path(_resolve_path(surface_root))
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
        manifest_path = resolve_package_submission_manifest_path(root)
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
    active_surface_root = _surface_root_from_submission_manifest_path(active_manifest_path)
    active_manifest = load_submission_surface_manifest(active_surface_root)
    if not isinstance(active_manifest, dict):
        return False
    active_publication_profile = str(active_manifest.get("publication_profile") or "").strip()
    if not is_supported_publication_profile(active_publication_profile):
        return False
    return active_surface_root != _resolve_path(surface_root)


def _workspace_relative_manifest_path(*, paper_root: Path, manifest_path: Path) -> str:
    resolved_paper_root = _resolve_path(paper_root)
    resolved_manifest_path = _resolve_path(manifest_path)
    try:
        return resolved_manifest_path.relative_to(resolved_paper_root.parent).as_posix()
    except ValueError:
        return str(resolved_manifest_path)


def _surface_root_from_submission_manifest_path(manifest_path: Path) -> Path:
    resolved_manifest_path = _resolve_path(manifest_path)
    if resolved_manifest_path.name == "submission_manifest.json" and resolved_manifest_path.parent.name == "audit":
        return resolved_manifest_path.parent.parent.resolve()
    return resolved_manifest_path.parent.resolve()


def surface_root_from_submission_manifest_path(manifest_path: Path) -> Path:
    return _surface_root_from_submission_manifest_path(manifest_path)


def _prune_archived_reference_only_surface_root(*, surface_root: Path, manifest_path: Path) -> bool:
    pruned = False
    resolved_manifest_path = manifest_path.resolve()
    for child in sorted(surface_root.iterdir()):
        resolved_child = child.resolve()
        if resolved_child == resolved_manifest_path:
            continue
        if child.is_dir() and _is_path_within(resolved_child, resolved_manifest_path):
            for nested in sorted(child.rglob("*"), reverse=True):
                if nested.resolve() == resolved_manifest_path:
                    continue
                if nested.is_dir():
                    try:
                        nested.rmdir()
                    except OSError:
                        pass
                    continue
                nested.unlink()
                pruned = True
            continue
        if child.is_dir():
            shutil.rmtree(child)
            pruned = True
            continue
        child.unlink()
        pruned = True
    return pruned


def _iter_legacy_submission_surface_roots(paper_root: Path) -> tuple[Path, ...]:
    resolved_paper_root = _resolve_path(paper_root)
    if not resolved_paper_root.exists():
        return tuple()

    roots: list[Path] = []
    for candidate in sorted(resolved_paper_root.iterdir()):
        if candidate.is_dir() and candidate.name.startswith("submission_") and candidate.name != "submission_minimal":
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


def materialize_archived_reference_only_submission_surface_manifests(
    paper_root: Path,
    *,
    active_manifest_path: Path | None = None,
) -> tuple[Path, ...]:
    resolved_paper_root = _resolve_path(paper_root)
    if not resolved_paper_root.exists():
        return tuple()

    managed_manifest_paths = set(resolve_managed_submission_manifest_paths(resolved_paper_root))
    if not managed_manifest_paths:
        return tuple()

    if active_manifest_path is None:
        preferred_manifest_path = v2_submission_manifest_path(resolved_paper_root / "submission_minimal").resolve()
        legacy_preferred_manifest_path = legacy_submission_manifest_path(
            resolved_paper_root / "submission_minimal"
        ).resolve()
        resolved_active_manifest_path = (
            preferred_manifest_path
            if preferred_manifest_path in managed_manifest_paths
            else (
                legacy_preferred_manifest_path
                if legacy_preferred_manifest_path in managed_manifest_paths
                else sorted(managed_manifest_paths)[0]
            )
        )
    else:
        resolved_active_manifest_path = _resolve_path(active_manifest_path)

    if resolved_active_manifest_path not in managed_manifest_paths:
        return tuple()

    active_manifest = load_submission_surface_manifest(
        _surface_root_from_submission_manifest_path(resolved_active_manifest_path)
    )
    if not isinstance(active_manifest, dict):
        return tuple()
    active_publication_profile = str(active_manifest.get("publication_profile") or "").strip()
    if not is_supported_publication_profile(active_publication_profile):
        return tuple()

    archive_manifest = {
        "schema_version": 1,
        "surface_status": ARCHIVED_REFERENCE_ONLY_SURFACE_STATUS,
        "archive_reason": ARCHIVED_REFERENCE_ONLY_ARCHIVE_REASON,
        "active_managed_submission_manifest_path": _workspace_relative_manifest_path(
            paper_root=resolved_paper_root,
            manifest_path=resolved_active_manifest_path,
        ),
    }
    materialized_roots: list[Path] = []
    for surface_root in _iter_legacy_submission_surface_roots(resolved_paper_root):
        if surface_root == _surface_root_from_submission_manifest_path(resolved_active_manifest_path):
            continue
        manifest_path = v2_submission_manifest_path(surface_root)
        existing_manifest = load_submission_surface_manifest(surface_root)
        pruned_surface = _prune_archived_reference_only_surface_root(
            surface_root=surface_root,
            manifest_path=manifest_path,
        )
        if existing_manifest == archive_manifest:
            if pruned_surface:
                materialized_roots.append(surface_root.resolve())
            continue
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(json.dumps(archive_manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        materialized_roots.append(surface_root.resolve())

    return tuple(materialized_roots)


def resolve_artifact_manifest_from_main_result(main_result: dict[str, Any]) -> Path | None:
    evidence_paths = [str(item) for item in (main_result.get("evidence_paths") or [])]
    worktree_root_value = str(main_result.get("worktree_root") or "").strip()
    worktree_root = _resolve_path(Path(worktree_root_value)) if worktree_root_value else None
    for rel in evidence_paths:
        raw_candidate = Path(rel)
        if raw_candidate.is_absolute():
            candidate = _resolve_path(raw_candidate)
        elif worktree_root is not None:
            candidate = worktree_root / rel
        else:
            continue
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


def _submission_minimal_authority_record(path: Path | None, *, artifact_format: str) -> dict[str, Any]:
    if path is not None:
        artifact = artifact_authority_record(path=path, study_root=path.parent)
    else:
        artifact = {
            "role": "derived_projection",
            "lifecycle": "rebuildable_projection",
            "owner": "artifact_lifecycle_authority_kernel",
            "authority_allowed": {"edit": False, "quality": False, "dispatch": False},
            "projection_currentness": "projection_only",
        }
    return {
        "path": str(path) if path is not None else None,
        "format": artifact_format,
        "role": artifact["role"],
        "lifecycle": artifact["lifecycle"],
        "owner": artifact["owner"],
        "authority_allowed": artifact["authority_allowed"],
        "projection_currentness": artifact["projection_currentness"],
        "edit_source_allowed": artifact["authority_allowed"]["edit"],
        "quality_authority_allowed": artifact["authority_allowed"]["quality"],
        "dispatch_authority_allowed": artifact["authority_allowed"]["dispatch"],
        "authority_source_roles": ["canonical_source"],
    }


def resolve_submission_minimal_artifact_authority(
    *,
    paper_bundle_manifest_path: Path | None,
    submission_minimal_manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    docx_path, pdf_path = resolve_submission_minimal_output_paths(
        paper_bundle_manifest_path=paper_bundle_manifest_path,
        submission_minimal_manifest=submission_minimal_manifest,
    )
    return {
        "schema_version": 1,
        "surface_kind": "paper_artifact_authority_resolution",
        "status": "resolved" if docx_path is not None or pdf_path is not None else "unresolved",
        "docx": _submission_minimal_authority_record(docx_path, artifact_format="docx"),
        "pdf": _submission_minimal_authority_record(pdf_path, artifact_format="pdf"),
        "submission_minimal_edit_source_allowed": False,
        "submission_minimal_quality_authority_allowed": False,
        "submission_minimal_dispatch_authority_allowed": False,
    }


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
