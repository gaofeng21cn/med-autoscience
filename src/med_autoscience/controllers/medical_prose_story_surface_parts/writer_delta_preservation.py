from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers.medical_prose_story_surface_parts.journal_routable_story_delta import (
    current_writer_story_delta_is_journal_routable,
)
from med_autoscience.controllers.story_surface_work_units import (
    is_story_surface_delta_write_work_unit,
)


def preserve_current_writer_story_delta(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    previous_quality_repair_batch: Mapping[str, Any] | None,
) -> bool:
    if not current_writer_story_delta_is_preservable(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
        manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
        contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        previous_quality_repair_batch=previous_quality_repair_batch,
    ):
        return False
    return True


def materialize_current_writer_story_delta(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    previous_quality_repair_batch: Mapping[str, Any] | None,
) -> list[str]:
    story_text = _current_writer_story_delta_text(
        paper_root=paper_root,
        work_unit_id=work_unit_id,
        medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
        manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
        contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        source_eval_id=source_eval_id,
        previous_quality_repair_batch=previous_quality_repair_batch,
    )
    if story_text is None:
        return []
    rendered = story_text if story_text.endswith("\n") else f"{story_text}\n"
    paths: list[str] = []
    for relative_path in manuscript_story_surface_relative_paths:
        path = (paper_root / relative_path).expanduser().resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            current = path.read_text(encoding="utf-8") if path.exists() else None
        except OSError:
            current = None
        if current != rendered:
            path.write_text(rendered, encoding="utf-8")
            paths.append(str(path))
    return paths


def current_writer_story_delta_is_preservable(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    previous_quality_repair_batch: Mapping[str, Any] | None,
) -> bool:
    return (
        _current_writer_story_delta_text(
            paper_root=paper_root,
            work_unit_id=work_unit_id,
            medical_prose_write_repair_work_unit_id=medical_prose_write_repair_work_unit_id,
            manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
            contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
            source_eval_id=source_eval_id,
            previous_quality_repair_batch=previous_quality_repair_batch,
        )
        is not None
    )


def _current_writer_story_delta_text(
    *,
    paper_root: Path,
    work_unit_id: str,
    medical_prose_write_repair_work_unit_id: str,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
    source_eval_id: str | None,
    previous_quality_repair_batch: Mapping[str, Any] | None,
) -> str | None:
    if not (
        is_story_surface_delta_write_work_unit(work_unit_id)
        or work_unit_id == medical_prose_write_repair_work_unit_id
    ):
        return None
    if not _previous_batch_can_anchor_writer_story_delta(
        previous_quality_repair_batch,
        source_eval_id=source_eval_id,
    ):
        return _current_divergent_story_surface_text(
            paper_root=paper_root,
            manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
            contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        )
    previous_refs = _previous_batch_story_surface_refs(
        previous_quality_repair_batch,
        source_eval_id=source_eval_id,
    )
    if not previous_refs:
        return None
    previous_by_path = {
        _text(ref.get("path")): ref
        for ref in previous_refs
        if isinstance(ref, Mapping) and _text(ref.get("path")) is not None
    }
    changed_story_texts: list[str] = []
    for relative_path in manuscript_story_surface_relative_paths:
        path = (paper_root / relative_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            continue
        previous_ref = previous_by_path.get(str(path))
        if not isinstance(previous_ref, Mapping):
            continue
        previous_fingerprint = _mapping(previous_ref.get("fingerprint"))
        current_fingerprint = _path_fingerprint(path)
        if not current_fingerprint or previous_fingerprint == current_fingerprint:
            continue
        changed_story_texts.append(path.read_text(encoding="utf-8"))
    if not changed_story_texts:
        return _current_divergent_story_surface_text(
            paper_root=paper_root,
            manuscript_story_surface_relative_paths=manuscript_story_surface_relative_paths,
            contains_forbidden_manuscript_terms=contains_forbidden_manuscript_terms,
        )
    if any(not text.strip() for text in changed_story_texts):
        return None
    if any(contains_forbidden_manuscript_terms(text) for text in changed_story_texts):
        return None
    unique_texts = set(changed_story_texts)
    if len(unique_texts) != 1:
        return None
    story_text = next(iter(unique_texts))
    if not current_writer_story_delta_is_journal_routable(story_text):
        return None
    return story_text


def _current_divergent_story_surface_text(
    *,
    paper_root: Path,
    manuscript_story_surface_relative_paths: tuple[Path, ...],
    contains_forbidden_manuscript_terms: Callable[[str], bool],
) -> str | None:
    current_texts: list[str] = []
    for relative_path in manuscript_story_surface_relative_paths:
        path = (paper_root / relative_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        if text.strip():
            current_texts.append(text)
    if len(set(current_texts)) <= 1:
        return None
    routable_texts = {
        text
        for text in current_texts
        if not contains_forbidden_manuscript_terms(text)
        and current_writer_story_delta_is_journal_routable(text)
    }
    if len(routable_texts) != 1:
        return None
    return next(iter(routable_texts))


def _previous_batch_can_anchor_writer_story_delta(
    previous_quality_repair_batch: Mapping[str, Any] | None,
    *,
    source_eval_id: str | None,
) -> bool:
    payload = _mapping(previous_quality_repair_batch)
    if not payload:
        return False
    if _text(payload.get("source_eval_id")) != source_eval_id:
        return False
    if _text(payload.get("blocked_reason")) == "manuscript_story_surface_delta_missing":
        return True
    evidence = _mapping(payload.get("repair_execution_evidence"))
    if _text(evidence.get("status")) != "blocked":
        hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
        return _text(evidence.get("status")) == "progress_delta_candidate" and hygiene.get(
            "story_surface_delta_present"
        ) is True
    return "manuscript_story_surface_delta_missing" in {
        _text(blocker) for blocker in evidence.get("blockers") or ()
    }


def _previous_batch_story_surface_refs(
    previous_quality_repair_batch: Mapping[str, Any] | None,
    *,
    source_eval_id: str | None,
) -> list[Mapping[str, Any]]:
    payload = _mapping(previous_quality_repair_batch)
    if not payload or _text(payload.get("source_eval_id")) != source_eval_id:
        return []
    evidence = _mapping(payload.get("repair_execution_evidence"))
    hygiene = _mapping(evidence.get("manuscript_surface_hygiene"))
    refs = hygiene.get("surface_refs")
    if not isinstance(refs, list):
        return []
    return [ref for ref in refs if isinstance(ref, Mapping)]


def _path_fingerprint(path: Path) -> dict[str, Any] | None:
    resolved = Path(path).expanduser().resolve()
    if not resolved.exists() or not resolved.is_file():
        return None
    data = resolved.read_bytes()
    return {
        "size": len(data),
        "content_sha256": hashlib.sha256(data).hexdigest(),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None
