from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.gate_clearing_batch_work_units import PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS


def current_ai_reviewer_gate_replay_fingerprint(
    *,
    study_id: str | None,
    action_type: str | None,
    work_unit_id: str | None,
    source_eval_id: str | None,
) -> str | None:
    if (
        study_id is None
        or action_type != "run_gate_clearing_batch"
        or work_unit_id not in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS
        or source_eval_id is None
    ):
        return None
    return f"current-ai-reviewer-gate-replay::{study_id}::{work_unit_id}::{source_eval_id}"


def is_current_ai_reviewer_gate_replay_fingerprint(value: str | None) -> bool:
    return bool(value and value.startswith("current-ai-reviewer-gate-replay::"))


def current_ai_reviewer_gate_replay_source_eval_id(
    *,
    study: Mapping[str, Any],
    current: Mapping[str, Any],
    action_type: str | None,
    work_unit_id: str | None,
) -> str | None:
    if action_type != "run_gate_clearing_batch" or work_unit_id not in PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS:
        return None
    current_work_unit = _mapping(study.get("current_work_unit"))
    currentness_basis = _mapping(current_work_unit.get("currentness_basis"))
    for mapping in (
        current,
        currentness_basis,
        current_work_unit,
        _mapping(current_work_unit.get("state")),
        _mapping(study.get("domain_transition")),
        _mapping(_mapping(study.get("domain_transition")).get("completion_receipt_consumption")),
        _mapping(study.get("progress_first_monitoring_summary")),
        _mapping(_mapping(study.get("progress_first_monitoring_summary")).get("dispatch_consumption")),
        _mapping(study.get("owner_route")),
        _mapping(_mapping(study.get("owner_route")).get("source_refs")),
        _mapping(
            _mapping(_mapping(study.get("owner_route")).get("source_refs")).get(
                "owner_route_currentness_basis"
            )
        ),
    ):
        source_eval_id = source_eval_id_from_mapping(mapping)
        if _is_current_ai_reviewer_source_eval_id(source_eval_id):
            return source_eval_id
    checklist = _mapping(_mapping(study.get("intervention_lane")).get("route_back_checklist"))
    source_eval_id = source_eval_id_from_mapping(checklist)
    if _is_current_ai_reviewer_source_eval_id(source_eval_id):
        return source_eval_id
    for ref in _text_items(checklist.get("evidence_refs")):
        if _looks_like_ai_reviewer_record_ref(ref):
            return _source_eval_id_from_ai_reviewer_record_ref(ref)
    for ref in _text_items(current_work_unit.get("input_refs")):
        if _looks_like_ai_reviewer_record_ref(ref):
            return _source_eval_id_from_ai_reviewer_record_ref(ref)
    return None


def source_eval_id_from_mapping(mapping: Mapping[str, Any]) -> str | None:
    source_refs = _mapping(mapping.get("source_refs"))
    basis = _mapping(source_refs.get("owner_route_currentness_basis"))
    for value in (
        mapping.get("source_eval_id"),
        mapping.get("eval_id"),
        mapping.get("publication_eval_id"),
        source_refs.get("source_eval_id"),
        basis.get("source_eval_id"),
    ):
        source_eval_id = _non_empty_text(value)
        if source_eval_id is not None:
            return source_eval_id
    return None


def study_currentness_basis(
    *,
    study: Mapping[str, Any],
    current: Mapping[str, Any],
    work_unit_id: str,
    work_unit_fingerprint: str | None,
    source_eval_id: str | None = None,
) -> dict[str, Any]:
    current_work_unit = _mapping(study.get("current_work_unit"))
    basis = _mapping(current_work_unit.get("currentness_basis"))
    return {
        key: value
        for key, value in {
            **basis,
            "work_unit_id": _non_empty_text(basis.get("work_unit_id")) or work_unit_id,
            "work_unit_fingerprint": (
                work_unit_fingerprint
                if is_current_ai_reviewer_gate_replay_fingerprint(work_unit_fingerprint)
                else _non_empty_text(basis.get("work_unit_fingerprint")) or work_unit_fingerprint
            ),
            "source_eval_id": (
                source_eval_id
                or _non_empty_text(basis.get("source_eval_id"))
                or source_eval_id_from_mapping(current)
            ),
            "source": _non_empty_text(current.get("source")),
        }.items()
        if value is not None
    }


def _is_current_ai_reviewer_source_eval_id(value: str | None) -> bool:
    if value is None:
        return False
    return "ai-reviewer-record" in value.replace("_", "-")


def _looks_like_ai_reviewer_record_ref(value: str) -> bool:
    normalized = value.replace("_", "-")
    return "publication-eval/ai-reviewer-responses/" in normalized and normalized.endswith(
        "-publication-eval-record.json"
    )


def _source_eval_id_from_ai_reviewer_record_ref(value: str) -> str:
    return f"ai-reviewer-record-ref::{value}"


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        return [value] if value.strip() else []
    if not isinstance(value, list | tuple | set):
        return []
    return [str(item).strip() for item in value if str(item or "").strip()]


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_ai_reviewer_gate_replay_fingerprint",
    "current_ai_reviewer_gate_replay_source_eval_id",
    "is_current_ai_reviewer_gate_replay_fingerprint",
    "source_eval_id_from_mapping",
    "study_currentness_basis",
]
