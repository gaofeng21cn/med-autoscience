from __future__ import annotations

import hashlib
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable


REF_FIELDS = (
    "manuscript_ref",
    "ref",
    "path",
    "source_ref",
    "evidence_ref",
    "result_ref",
)
DIGEST_FIELDS = (
    "manuscript_digest",
    "digest",
    "sha256",
    "content_sha256",
    "file_sha256",
    "file_digest",
)


def currentness_blocker_evidence(
    *,
    study_root: Path,
    record: Mapping[str, Any],
    record_ref: str | None,
    missing_currentness_refs: list[str],
    blocked_reason: str,
    text: Callable[[object], str | None],
    mapping: Callable[[object], Mapping[str, Any]],
    resolved_text_ref: Callable[..., str | None],
    currentness_check_mappings: Callable[..., list[Mapping[str, Any]]],
) -> dict[str, Any]:
    currentness_checks = mapping(mapping(record.get("reviewer_operating_system")).get("currentness_checks"))
    return {
        "surface_kind": "ai_reviewer_record_currentness_evidence",
        "blocked_reason": blocked_reason,
        "stale_record_ref": record_ref,
        "missing_refs": [
            _missing_ref_evidence(
                study_root=study_root,
                currentness_checks=currentness_checks,
                required_ref=ref,
                text=text,
                resolved_text_ref=resolved_text_ref,
                currentness_check_mappings=currentness_check_mappings,
            )
            for ref in missing_currentness_refs
        ],
        "authority_boundary": {
            "owner": "ai_reviewer",
            "can_authorize_quality": False,
            "can_authorize_submission": False,
        },
    }


def _missing_ref_evidence(
    *,
    study_root: Path,
    currentness_checks: Mapping[str, Any],
    required_ref: str,
    text: Callable[[object], str | None],
    resolved_text_ref: Callable[..., str | None],
    currentness_check_mappings: Callable[..., list[Mapping[str, Any]]],
) -> dict[str, Any]:
    ref_path = Path(required_ref).expanduser().resolve()
    resolved_ref = str(ref_path)
    return {
        "required_ref": resolved_ref,
        "live_digest": _sha256_file(ref_path),
        "record_checks": [
            _check_projection(
                study_root=study_root,
                check=check,
                text=text,
                resolved_text_ref=resolved_text_ref,
            )
            for check in currentness_check_mappings(currentness_checks)
            if _check_refs_required_ref(
                study_root=study_root,
                check=check,
                required_ref=resolved_ref,
                resolved_text_ref=resolved_text_ref,
            )
        ],
    }


def _check_refs_required_ref(
    *,
    study_root: Path,
    check: Mapping[str, Any],
    required_ref: str,
    resolved_text_ref: Callable[..., str | None],
) -> bool:
    for field in REF_FIELDS:
        resolved = resolved_text_ref(study_root=study_root, value=check.get(field))
        if resolved == required_ref:
            return True
    return False


def _check_projection(
    *,
    study_root: Path,
    check: Mapping[str, Any],
    text: Callable[[object], str | None],
    resolved_text_ref: Callable[..., str | None],
) -> dict[str, str]:
    projection: dict[str, str] = {}
    if status := text(check.get("status")):
        projection["status"] = status
    for field in REF_FIELDS:
        if resolved := resolved_text_ref(study_root=study_root, value=check.get(field)):
            projection[field] = resolved
    for field in DIGEST_FIELDS:
        if digest := text(check.get(field)):
            projection[field] = digest
    return projection


def _sha256_file(path: Path) -> str | None:
    try:
        return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


__all__ = ["currentness_blocker_evidence"]
