from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import (
    AI_REVIEWER_ACTION,
    AI_REVIEWER_OWNER,
    AI_REVIEWER_WORK_UNIT,
    GATE_CLEARING_ACTION,
    GATE_CLEARING_OWNER,
    GATE_CLEARING_WORK_UNIT,
    REPAIR_PROGRESS_SOURCE,
)
from .stage_kernel_readiness import READINESS_ACTION


def owner_action_from_repair_progress_projection(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    repair_progress = _mapping_copy(payload.get("repair_progress_projection"))
    if repair_progress.get("paper_delta_observed") is not True:
        return None
    if repair_progress.get("accepted_owner_receipt") is not True:
        return None
    source_ref = _non_empty_text(repair_progress.get("repair_execution_evidence_ref")) or _non_empty_text(
        repair_progress.get("owner_receipt_ref")
    )
    ai_reviewer_request_ref = _non_empty_text(repair_progress.get("ai_reviewer_recheck_request_ref"))
    gate_replay_refs = _text_items(repair_progress.get("gate_replay_refs"))
    if gate_replay_refs and repair_progress.get("ai_reviewer_recheck_done") is True:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=GATE_CLEARING_OWNER,
            work_unit_id=GATE_CLEARING_WORK_UNIT,
            action_type=GATE_CLEARING_ACTION,
            required_delta_kind="publication_gate_replay_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "request_ref": gate_replay_refs[0],
            },
            acceptance_refs=gate_replay_refs,
            surface_kind=surface_kind,
        )
    if ai_reviewer_request_ref is not None:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=AI_REVIEWER_OWNER,
            work_unit_id=AI_REVIEWER_WORK_UNIT,
            action_type=AI_REVIEWER_ACTION,
            required_delta_kind="ai_reviewer_publication_eval_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "review",
                "surface_ref": "artifacts/publication_eval/latest.json",
                "request_ref": ai_reviewer_request_ref,
                "gate_replay_request_ref": gate_replay_refs[0] if gate_replay_refs else None,
            },
            acceptance_refs=[ai_reviewer_request_ref, *gate_replay_refs],
            surface_kind=surface_kind,
        )
    if gate_replay_refs:
        return _repair_followup_action(
            repair_progress=repair_progress,
            source_ref=source_ref,
            next_owner=GATE_CLEARING_OWNER,
            work_unit_id=GATE_CLEARING_WORK_UNIT,
            action_type=GATE_CLEARING_ACTION,
            required_delta_kind="publication_gate_replay_delta_or_typed_blocker",
            target_surface={
                "ref_kind": "route_obligation",
                "route_target": "finalize",
                "surface_ref": "artifacts/controller/gate_clearing_batch/latest.json",
                "request_ref": gate_replay_refs[0],
            },
            acceptance_refs=gate_replay_refs,
            surface_kind=surface_kind,
        )
    return None


def repair_progress_consumes_publication_repair(
    *,
    repair_progress_action: Mapping[str, Any] | None,
    publication_repair_action: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> bool:
    repair_action = _mapping_copy(repair_progress_action)
    publication_action = _mapping_copy(publication_repair_action)
    if not repair_action or not publication_action:
        return False
    if _non_empty_text(repair_action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    progress = _mapping_copy(payload.get("repair_progress_projection"))
    if progress.get("paper_delta_observed") is not True or progress.get("accepted_owner_receipt") is not True:
        return False
    source_work_unit = _non_empty_text(
        _mapping_copy(repair_action.get("repair_progress_precedence")).get("source_work_unit_id")
    )
    if source_work_unit is None:
        source_work_unit = _non_empty_text(progress.get("work_unit_id"))
    if source_work_unit is None:
        return False
    return source_work_unit == _non_empty_text(publication_action.get("work_unit_id"))


def _repair_followup_action(
    *,
    repair_progress: Mapping[str, Any],
    source_ref: str | None,
    next_owner: str,
    work_unit_id: str,
    action_type: str,
    required_delta_kind: str,
    target_surface: Mapping[str, Any],
    acceptance_refs: list[str],
    surface_kind: str,
) -> dict[str, Any]:
    owner_receipt_ref = _non_empty_text(repair_progress.get("owner_receipt_ref"))
    repair_evidence_ref = _non_empty_text(repair_progress.get("repair_execution_evidence_ref"))
    work_unit_fingerprint = (
        _non_empty_text(repair_progress.get("work_unit_fingerprint"))
        or _non_empty_text(repair_progress.get("action_fingerprint"))
        or _non_empty_text(repair_progress.get("source_fingerprint"))
    )
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": REPAIR_PROGRESS_SOURCE,
            "next_owner": next_owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "source_eval_id": _non_empty_text(repair_progress.get("source_eval_id")),
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
            "required_delta_kind": required_delta_kind,
            "target_surface": _compact(target_surface),
            "target_surface_specificity": "repair_progress_followup_owner_surface",
            "source_ref": source_ref,
            "acceptance_refs": _dedupe_text(
                [
                    repair_evidence_ref,
                    owner_receipt_ref,
                    *acceptance_refs,
                ]
            ),
            "repair_progress_precedence": {
                "paper_delta_observed": True,
                "accepted_owner_receipt": True,
                "superseded_stage_native_action": "run_quality_repair_batch",
                "superseded_readiness_action": READINESS_ACTION,
                "source_work_unit_id": _non_empty_text(repair_progress.get("work_unit_id")),
                "work_unit_fingerprint": _non_empty_text(repair_progress.get("work_unit_fingerprint")),
                "action_fingerprint": _non_empty_text(repair_progress.get("action_fingerprint")),
                "source_fingerprint": _non_empty_text(repair_progress.get("source_fingerprint")),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe_text(items: list[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "owner_action_from_repair_progress_projection",
    "repair_progress_consumes_publication_repair",
]
