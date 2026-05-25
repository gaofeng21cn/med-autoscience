from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Callable, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.journal_routable_story_delta import (
    current_writer_story_delta_is_journal_routable,
)
from med_autoscience.controllers.story_surface_work_units import is_story_surface_delta_write_work_unit


EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER = (
    "quality_repair_batch_current_manuscript_digest_mismatch"
)

def eval_bound_current_story_delta_refs(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> list[dict[str, Any]]:
    currentness = _eval_bound_current_story_delta(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
        manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
        contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    )
    if currentness is None:
        return []
    return [
        {
            "path": str(path.resolve()),
            "artifact_role": "canonical_manuscript_story_surface",
            "reason": "ai_reviewer_eval_bound_current_manuscript_preserved",
            "source_eval_id": currentness["source_eval_id"],
            "reviewer_manuscript_ref": currentness["manuscript_ref"],
            "reviewer_manuscript_digest": currentness["manuscript_digest"],
            "fingerprint": _path_fingerprint(path),
        }
        for path in currentness["story_surface_paths"]
    ]


def eval_bound_current_story_delta_is_preservable(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> bool:
    return (
        _eval_bound_current_story_delta(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
            manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
            contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
            source_eval_id=source_eval_id,
            publication_eval_payload=publication_eval_payload,
        )
        is not None
    )


def eval_bound_current_story_delta_blocker(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    currentness = _eval_bound_current_story_delta_state(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
        manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
        contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    )
    if currentness is None or currentness.get("status") != "digest_mismatch":
        return {}
    return {
        "blocked_reason": EVAL_BOUND_CURRENT_MANUSCRIPT_DIGEST_MISMATCH_BLOCKER,
        "source_eval_id": currentness.get("source_eval_id"),
        "reviewer_manuscript_ref": currentness.get("manuscript_ref"),
        "reviewer_manuscript_digest": currentness.get("manuscript_digest"),
        "story_surface_digests": currentness.get("story_surface_digests") or [],
    }


def eval_bound_current_story_delta_source_basis(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any]:
    currentness = _eval_bound_current_story_delta(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
        manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
        contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    )
    if currentness is None:
        return {}
    return {
        "source_eval_id": currentness["source_eval_id"],
        "manuscript_ref": currentness["manuscript_ref"],
        "manuscript_digest": currentness["manuscript_digest"],
        "request_digest": currentness["request_digest"],
        "story_surface_digests": [
            ref["fingerprint"]["content_sha256"]
            for ref in eval_bound_current_story_delta_refs(
                paper_root=paper_root,
                work_unit_id=work_unit_id,
                medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
                manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
                contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
                source_eval_id=source_eval_id,
                publication_eval_payload=publication_eval_payload,
            )
        ],
    }


def _eval_bound_current_story_delta(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    currentness = _eval_bound_current_story_delta_state(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
        manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
        contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        publication_eval_payload=publication_eval_payload,
    )
    if currentness is None or currentness.get("status") != "preservable":
        return None
    return currentness


def _eval_bound_current_story_delta_state(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    publication_eval_payload: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    if not (
        work_unit_id == medical_prose_write_repair_work_unit_id
        or is_story_surface_delta_write_work_unit(work_unit_id)
    ):
        return None
    payload = dict(publication_eval_payload) if isinstance(publication_eval_payload, Mapping) else {}
    eval_id = _text(payload.get("eval_id"))
    if source_eval_id and eval_id != source_eval_id:
        return None
    prose_currentness = _medical_prose_currentness(payload)
    if _text(prose_currentness.get("status")) != "current":
        return None
    if _text(prose_currentness.get("route_target")) not in {None, "write"}:
        return None
    request_digest = _text(prose_currentness.get("request_digest"))
    manuscript_ref = _text(prose_currentness.get("manuscript_ref"))
    manuscript_digest = _text(prose_currentness.get("manuscript_digest"))
    if not request_digest or not manuscript_ref or not manuscript_digest:
        return None
    if not manuscript_digest.startswith("sha256:"):
        return None
    resolved_paper_root = Path(paper_root).expanduser().resolve()
    story_surface_paths = [
        (resolved_paper_root / relative_path).expanduser().resolve()
        for relative_path in manuscript_story_surface_relative_paths
    ]
    manuscript_path = Path(manuscript_ref).expanduser()
    if not manuscript_path.is_absolute():
        manuscript_path = (resolved_paper_root.parent / manuscript_path).resolve()
    else:
        manuscript_path = manuscript_path.resolve()
    if manuscript_path not in story_surface_paths:
        return None
    story_texts: list[str] = []
    story_surface_digests: list[dict[str, Any]] = []
    digest_mismatch = False
    for path in story_surface_paths:
        if not path.exists() or not path.is_file():
            digest_mismatch = True
            story_surface_digests.append({"path": str(path), "present": False})
            continue
        path_digest = _sha256_file(path)
        story_surface_digests.append({"path": str(path), "present": True, "digest": path_digest})
        if path_digest != manuscript_digest:
            digest_mismatch = True
            continue
        text = path.read_text(encoding="utf-8")
        if not text.strip() or contains_forbidden_manuscript_terms(text):
            return None
        story_texts.append(text)
    if digest_mismatch:
        return {
            "status": "digest_mismatch",
            "source_eval_id": eval_id,
            "request_digest": request_digest,
            "manuscript_ref": str(manuscript_path),
            "manuscript_digest": manuscript_digest,
            "story_surface_paths": story_surface_paths,
            "story_surface_digests": story_surface_digests,
        }
    if len(set(story_texts)) != 1:
        return None
    if not current_writer_story_delta_is_journal_routable(story_texts[0]):
        return None
    return {
        "status": "preservable",
        "source_eval_id": eval_id,
        "request_digest": request_digest,
        "manuscript_ref": str(manuscript_path),
        "manuscript_digest": manuscript_digest,
        "story_surface_paths": story_surface_paths,
        "story_surface_digests": story_surface_digests,
    }


def _medical_prose_currentness(publication_eval_payload: Mapping[str, Any]) -> dict[str, Any]:
    reviewer_os = publication_eval_payload.get("reviewer_operating_system")
    if not isinstance(reviewer_os, Mapping):
        return {}
    currentness_checks = reviewer_os.get("currentness_checks")
    if not isinstance(currentness_checks, Mapping):
        return {}
    prose_currentness = currentness_checks.get("medical_prose_review")
    return dict(prose_currentness) if isinstance(prose_currentness, Mapping) else {}


def _path_fingerprint(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    return {
        "size": len(data),
        "content_sha256": hashlib.sha256(data).hexdigest(),
    }


def _sha256_file(path: Path) -> str:
    return f"sha256:{hashlib.sha256(path.read_bytes()).hexdigest()}"


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
