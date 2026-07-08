from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from .policy_constants import MEDICAL_READINESS_BLOCKERS


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def stage_owner_readiness_blocker_should_own_identity(
    *,
    blocker: Mapping[str, Any],
    source: str,
    blocker_type: str,
) -> bool:
    if source != "stage_owner_answer":
        return False
    if blocker_type not in MEDICAL_READINESS_BLOCKERS:
        return False
    return _work_unit_id(blocker.get("work_unit_id")) == READINESS_ACTION_TYPE


def readiness_typed_blocker_currentness_basis(
    *,
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
    fallback_basis: Mapping[str, Any],
) -> dict[str, str]:
    study_id = _text(progress.get("study_id")) or "unknown-study"
    source_ref = (
        _text(blocker.get("source_ref"))
        or _text(blocker.get("typed_blocker_ref"))
        or _text(blocker.get("latest_owner_answer_ref"))
        or "current_work_unit.typed_blocker"
    )
    truth_epoch = _text(progress.get("truth_epoch")) or _text(fallback_basis.get("truth_epoch")) or (
        f"readiness-typed-blocker::{study_id}"
    )
    runtime_health = _mapping(progress.get("runtime_health_snapshot"))
    runtime_health_epoch = (
        _text(runtime_health.get("runtime_health_epoch"))
        or _text(progress.get("runtime_health_epoch"))
        or _text(fallback_basis.get("runtime_health_epoch"))
        or truth_epoch
    )
    work_unit_fingerprint = _text(blocker.get("work_unit_fingerprint")) or (
        "current-readiness-typed-blocker::"
        f"{study_id}::{_short_digest(source_ref, truth_epoch, runtime_health_epoch)}"
    )
    return {
        "source": "stage_owner_answer.typed_blocker",
        "truth_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_id": READINESS_ACTION_TYPE,
        "work_unit_fingerprint": work_unit_fingerprint,
        "source_ref": source_ref,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return (
            _text(value.get("unit_id"))
            or _text(value.get("work_unit_id"))
            or _text(value.get("id"))
            or _text(value.get("ref"))
        )
    return _text(value)


def _short_digest(*values: object) -> str:
    joined = "\n".join(str(value) for value in values)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


__all__ = [
    "readiness_typed_blocker_currentness_basis",
    "stage_owner_readiness_blocker_should_own_identity",
]
