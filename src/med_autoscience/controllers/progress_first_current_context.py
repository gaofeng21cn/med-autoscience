from __future__ import annotations

from collections.abc import Mapping
from typing import Any


INVALID_CURRENT_RECORD_REASON = "invalid_current_ai_reviewer_record"
SUPPORTED_BATCH_KINDS = frozenset({"quality_repair_batch", "gate_clearing_batch"})


def resolve_effective_current_context(
    *,
    study_id: str,
    quest_id: str | None = None,
    current_ai_reviewer_record: Mapping[str, Any] | None = None,
    latest_publication_eval: Mapping[str, Any] | None = None,
    current_work_unit: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    running_state: Mapping[str, Any] | None = None,
    closeout_state: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    current_record = _mapping(current_ai_reviewer_record)
    latest_eval = _mapping(latest_publication_eval)
    if current_record and not _valid_current_record(current_record, study_id=study_id, quest_id=quest_id):
        return _blocked_context(
            study_id=study_id,
            quest_id=quest_id,
            blocked_reason=INVALID_CURRENT_RECORD_REASON,
            latest_eval=latest_eval,
            current_work_unit=current_work_unit,
            owner_route=owner_route,
            running_state=running_state,
            closeout_state=closeout_state,
        )
    effective_eval = current_record if current_record else latest_eval
    effective_eval_id = _text(effective_eval.get("eval_id"))
    status = "current" if effective_eval_id else "blocked"
    blocked_reason = None if effective_eval_id else "effective_eval_missing"
    source_fingerprint = (
        _text(effective_eval.get("source_fingerprint"))
        or _text(_mapping(owner_route).get("source_fingerprint"))
        or _text(_mapping(_mapping(owner_route).get("source_refs")).get("source_fingerprint"))
    )
    packet = _immutable_dispatch_packet(
        status=status,
        study_id=study_id,
        quest_id=quest_id,
        effective_eval_id=effective_eval_id,
        effective_eval_ref=_eval_ref(effective_eval),
        current_work_unit=current_work_unit,
        owner_route=owner_route,
        source_fingerprint=source_fingerprint,
        blocked_reason=blocked_reason,
    )
    return {
        "surface": "progress_first_effective_current_context",
        "schema_version": 1,
        "status": status,
        "blocked_reason": blocked_reason,
        "study_id": study_id,
        "quest_id": quest_id,
        "current_ai_reviewer_record": current_record or None,
        "latest_publication_eval": latest_eval or None,
        "effective_eval_id": effective_eval_id,
        "effective_eval_ref": _eval_ref(effective_eval),
        "stale_latest_eval_id": _stale_latest_eval_id(
            latest_eval=latest_eval,
            effective_eval_id=effective_eval_id,
        ),
        "current_work_unit": _mapping(current_work_unit) or None,
        "owner_route": _mapping(owner_route) or None,
        "source_fingerprint": source_fingerprint,
        "running_state": _mapping(running_state) or None,
        "closeout_state": _mapping(closeout_state) or None,
        "immutable_dispatch_packet": packet,
    }


def batch_effective_eval_context(
    context: Mapping[str, Any],
    *,
    batch_kind: str,
) -> dict[str, Any]:
    if batch_kind not in SUPPORTED_BATCH_KINDS:
        raise ValueError(f"unsupported progress-first batch kind: {batch_kind}")
    payload = _mapping(context)
    packet = _mapping(payload.get("immutable_dispatch_packet"))
    return {
        "surface": "progress_first_batch_effective_eval_context",
        "schema_version": 1,
        "batch_kind": batch_kind,
        "status": _text(payload.get("status")),
        "blocked_reason": _text(payload.get("blocked_reason")),
        "study_id": _text(payload.get("study_id")),
        "quest_id": _text(payload.get("quest_id")),
        "effective_eval_id": _text(payload.get("effective_eval_id")),
        "effective_eval_ref": _text(payload.get("effective_eval_ref")),
        "work_unit_id": _text(packet.get("work_unit_id")),
        "source_fingerprint": _text(payload.get("source_fingerprint")),
        "immutable_dispatch_packet": packet,
    }


def _blocked_context(
    *,
    study_id: str,
    quest_id: str | None,
    blocked_reason: str,
    latest_eval: Mapping[str, Any],
    current_work_unit: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any] | None,
    running_state: Mapping[str, Any] | None,
    closeout_state: Mapping[str, Any] | None,
) -> dict[str, Any]:
    packet = _immutable_dispatch_packet(
        status="blocked",
        study_id=study_id,
        quest_id=quest_id,
        effective_eval_id=None,
        effective_eval_ref=None,
        current_work_unit=current_work_unit,
        owner_route=owner_route,
        source_fingerprint=_text(_mapping(owner_route).get("source_fingerprint")),
        blocked_reason=blocked_reason,
    )
    return {
        "surface": "progress_first_effective_current_context",
        "schema_version": 1,
        "status": "blocked",
        "blocked_reason": blocked_reason,
        "study_id": study_id,
        "quest_id": quest_id,
        "current_ai_reviewer_record": None,
        "latest_publication_eval": dict(latest_eval) if latest_eval else None,
        "effective_eval_id": None,
        "effective_eval_ref": None,
        "stale_latest_eval_id": _text(latest_eval.get("eval_id")),
        "current_work_unit": _mapping(current_work_unit) or None,
        "owner_route": _mapping(owner_route) or None,
        "source_fingerprint": packet.get("source_fingerprint"),
        "running_state": _mapping(running_state) or None,
        "closeout_state": _mapping(closeout_state) or None,
        "immutable_dispatch_packet": packet,
    }


def _immutable_dispatch_packet(
    *,
    status: str,
    study_id: str,
    quest_id: str | None,
    effective_eval_id: str | None,
    effective_eval_ref: str | None,
    current_work_unit: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any] | None,
    source_fingerprint: str | None,
    blocked_reason: str | None,
) -> dict[str, Any]:
    work_unit = _mapping(current_work_unit)
    route = _mapping(owner_route)
    return {
        "surface": "progress_first_immutable_dispatch_packet",
        "schema_version": 1,
        "dispatchable": status == "current" and blocked_reason is None,
        "blocked_reason": blocked_reason,
        "study_id": study_id,
        "quest_id": quest_id,
        "effective_eval_id": effective_eval_id,
        "effective_eval_ref": effective_eval_ref,
        "work_unit_id": _text(work_unit.get("work_unit_id")) or _text(work_unit.get("unit_id")),
        "owner_route": route or None,
        "source_fingerprint": source_fingerprint,
    }


def _valid_current_record(record: Mapping[str, Any], *, study_id: str, quest_id: str | None) -> bool:
    if _text(record.get("eval_id")) is None:
        return False
    record_study_id = _text(record.get("study_id"))
    if record_study_id is not None and record_study_id != study_id:
        return False
    record_quest_id = _text(record.get("quest_id"))
    if quest_id is not None and record_quest_id is not None and record_quest_id != quest_id:
        return False
    status = _text(record.get("currentness_status"))
    return record.get("record_current") is True or record.get("current") is True or status in {"current", "valid"}


def _eval_ref(payload: Mapping[str, Any]) -> str | None:
    return (
        _text(payload.get("projection_source_ref"))
        or _text(payload.get("publication_eval_record_ref"))
        or _text(payload.get("artifact_path"))
        or _text(payload.get("path"))
        or _text(payload.get("ref"))
    )


def _stale_latest_eval_id(*, latest_eval: Mapping[str, Any], effective_eval_id: str | None) -> str | None:
    latest_eval_id = _text(latest_eval.get("eval_id"))
    if latest_eval_id is None or latest_eval_id == effective_eval_id:
        return None
    return latest_eval_id


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "INVALID_CURRENT_RECORD_REASON",
    "SUPPORTED_BATCH_KINDS",
    "batch_effective_eval_context",
    "resolve_effective_current_context",
]
