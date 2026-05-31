from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime
from pathlib import Path
from typing import Any, Callable


TextFn = Callable[[object], str | None]
MappingFn = Callable[[object], Mapping[str, Any]]
ResolvedTextRefFn = Callable[..., str | None]
Sha256FileFn = Callable[[Path], str | None]
PayloadTimestampFn = Callable[[Mapping[str, Any]], datetime | None]
RecordSourceRefsFn = Callable[..., set[str]]
RecordTimestampFn = Callable[[Mapping[str, Any]], datetime | None]
RefTimestampFn = Callable[[Path], datetime | None]
CurrentnessMappingsFn = Callable[..., list[Mapping[str, Any]]]
CurrentnessMatchesFn = Callable[..., bool]

CURRENTNESS_REF_FIELDS = (
    "manuscript_ref",
    "ref",
    "path",
    "source_ref",
    "evidence_ref",
    "result_ref",
)


def record_currentness_covers_ref(
    *,
    study_root: Path,
    record: Mapping[str, Any],
    required_ref: str,
    mapping: MappingFn,
    text: TextFn,
    sha256_file: Sha256FileFn,
    resolved_text_ref: ResolvedTextRefFn,
    currentness_check_mappings: CurrentnessMappingsFn,
    currentness_check_matches_live_ref: CurrentnessMatchesFn,
) -> bool:
    reviewer_os = mapping(record.get("reviewer_operating_system"))
    currentness_checks = mapping(reviewer_os.get("currentness_checks"))
    if not currentness_checks:
        return False
    live_digest = sha256_file(Path(required_ref))
    if live_digest is None:
        return False
    return any(
        currentness_check_matches_live_ref(
            study_root=study_root,
            check=check,
            required_ref=required_ref,
            live_digest=live_digest,
            text=text,
            resolved_text_ref=resolved_text_ref,
        )
        for check in currentness_check_mappings(currentness_checks)
    )


def record_source_ref_is_current(
    *,
    study_root: Path,
    record: Mapping[str, Any],
    required_ref: str,
    source_refs: set[str] | None,
    record_timestamp: datetime | None,
    resolved_text_ref: ResolvedTextRefFn,
    record_source_refs: RecordSourceRefsFn,
    reviewer_assessment_timestamp: RecordTimestampFn,
    ref_timestamp: RefTimestampFn,
) -> bool:
    resolved_ref = resolved_text_ref(study_root=study_root, value=required_ref)
    if not resolved_ref:
        return False
    if source_refs is None:
        source_refs = record_source_refs(study_root=study_root, record=record)
    if resolved_ref not in source_refs:
        return False
    if record_timestamp is None:
        record_timestamp = reviewer_assessment_timestamp(record)
    required_ref_timestamp = ref_timestamp(Path(resolved_ref))
    return (
        record_timestamp is not None
        and required_ref_timestamp is not None
        and record_timestamp >= required_ref_timestamp
    )


def record_currentness_mentions_ref(
    *,
    study_root: Path,
    record: Mapping[str, Any],
    required_ref: str,
    mapping: MappingFn,
    resolved_text_ref: ResolvedTextRefFn,
    currentness_check_mappings: CurrentnessMappingsFn,
) -> bool:
    reviewer_os = mapping(record.get("reviewer_operating_system"))
    currentness_checks = mapping(reviewer_os.get("currentness_checks"))
    if not currentness_checks:
        return False
    resolved_ref = resolved_text_ref(study_root=study_root, value=required_ref)
    if not resolved_ref:
        return False
    return any(
        currentness_check_mentions_ref(
            study_root=study_root,
            check=check,
            required_ref=resolved_ref,
            resolved_text_ref=resolved_text_ref,
        )
        for check in currentness_check_mappings(currentness_checks)
    )


def currentness_check_mentions_ref(
    *,
    study_root: Path,
    check: Mapping[str, Any],
    required_ref: str,
    resolved_text_ref: ResolvedTextRefFn,
) -> bool:
    for field in CURRENTNESS_REF_FIELDS:
        if resolved_text_ref(study_root=study_root, value=check.get(field)) == required_ref:
            return True
    return False


__all__ = [
    "record_currentness_covers_ref",
    "record_currentness_mentions_ref",
    "record_source_ref_is_current",
]
