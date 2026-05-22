from __future__ import annotations

import hashlib
from collections.abc import Callable
from pathlib import Path
from typing import Any, Mapping


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
    if work_unit_id != medical_prose_write_repair_work_unit_id:
        return False
    if not _previous_batch_blocks_same_story_surface_delta(
        previous_quality_repair_batch,
        source_eval_id=source_eval_id,
    ):
        return False
    previous_refs = _previous_batch_story_surface_refs(
        previous_quality_repair_batch,
        source_eval_id=source_eval_id,
    )
    if not previous_refs:
        return False
    previous_by_path = {
        _text(ref.get("path")): ref
        for ref in previous_refs
        if isinstance(ref, Mapping) and _text(ref.get("path")) is not None
    }
    story_texts: list[str] = []
    for relative_path in manuscript_story_surface_relative_paths:
        path = (paper_root / relative_path).expanduser().resolve()
        if not path.exists() or not path.is_file():
            return False
        previous_ref = previous_by_path.get(str(path))
        if not isinstance(previous_ref, Mapping):
            return False
        previous_fingerprint = _mapping(previous_ref.get("fingerprint"))
        current_fingerprint = _path_fingerprint(path)
        if not current_fingerprint or previous_fingerprint == current_fingerprint:
            return False
        story_texts.append(path.read_text(encoding="utf-8"))
    if not story_texts or any(not text.strip() for text in story_texts):
        return False
    if any(contains_forbidden_manuscript_terms(text) for text in story_texts):
        return False
    return len(set(story_texts)) == 1 and _current_writer_story_delta_is_journal_routable(story_texts[0])


def _previous_batch_blocks_same_story_surface_delta(
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
        return False
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


def _current_writer_story_delta_is_journal_routable(text: str) -> bool:
    required_sections = (
        "## Abstract",
        "## Introduction",
        "## Methods",
        "## Results",
        "## Discussion",
        "## Limitations",
        "## Conclusion",
    )
    required_domain_phrases = (
        "Phenotype derivation",
        "Data quality",
        "Statistical analysis",
    )
    gap_terminology_phrases = (
        "recorded medication-coverage gap",
        "recorded medication coverage gap",
        "recorded treatment-review gap",
        "potential treatment-review gap",
    )
    lowered = text.lower()
    return (
        all(phrase.lower() in lowered for phrase in required_sections)
        and all(phrase.lower() in lowered for phrase in required_domain_phrases)
        and any(phrase.lower() in lowered for phrase in gap_terminology_phrases)
    )


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
