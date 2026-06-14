from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)

from .action_types import QUALITY_REPAIR_ACTION
from .stage_kernel_readiness import READINESS_ACTION, current_owner_delta


def owner_action_from_publication_eval_readiness_blocker_repair(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    publication_eval = _mapping_copy(payload.get("publication_eval"))
    action = _publication_eval_route_back_action(publication_eval)
    if not action:
        source_publication_eval = _mapping_copy(publication_eval.get("source_publication_eval"))
        action = _publication_eval_route_back_action(source_publication_eval)
        if action:
            publication_eval = source_publication_eval
    if not action:
        return None
    owner_delta = current_owner_delta(payload)
    next_work_unit = _mapping_copy(action.get("next_work_unit"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    lane = _non_empty_text(next_work_unit.get("lane")) or _non_empty_text(action.get("route_target"))
    if work_unit_id is None or lane not in {"write", "analysis-campaign"}:
        return None
    action_type = QUALITY_REPAIR_ACTION
    source_ref = _text_items(action.get("evidence_refs"))[0] if _text_items(action.get("evidence_refs")) else None
    work_unit_fingerprint = _non_empty_text(action.get("work_unit_fingerprint"))
    stage_typed_blocker_ref = (
        _non_empty_text(owner_delta.get("source_ref"))
        or _non_empty_text(_mapping_copy(owner_delta.get("hard_gate")).get("owner_answer_ref"))
    )
    publication_eval_id = (
        _non_empty_text(publication_eval.get("eval_id"))
        or _non_empty_text(publication_eval.get("publication_eval_id"))
        or _non_empty_text(action.get("source_eval_id"))
    )
    gaps = [
        _compact(
            {
                "gap_id": _non_empty_text(gap.get("gap_id")),
                "gap_type": _non_empty_text(gap.get("gap_type")),
                "severity": _non_empty_text(gap.get("severity")),
                "summary": _non_empty_text(gap.get("summary")),
            }
        )
        for gap in _mapping_items(publication_eval.get("gaps"))
    ]
    gap_ids = [gap["gap_id"] for gap in gaps if _non_empty_text(gap.get("gap_id")) is not None]
    required_output_contract = {
        "accepted_outputs_any": [
            "canonical_manuscript_story_surface_delta",
            "claim_evidence_semantic_delta",
            "review_ledger_delta",
            "publication_gate_delta",
            "stage_owner_receipt_ref",
            "stable_typed_blocker_for_the_specific_repair_work_unit",
        ],
        "forbidden_outputs": [
            "publication_ready_claim",
            "submission_ready_claim",
            "current_package_authority",
            "publication_eval_latest_manual_write",
            "controller_decision_manual_write",
        ],
    }
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": "publication_eval.recommended_actions.readiness_blocker_repair",
            "next_owner": lane,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
            "required_delta_kind": "publication_eval_recommended_repair_delta_or_typed_blocker",
            "required_output_contract": required_output_contract,
            "stage_typed_blocker_ref": stage_typed_blocker_ref,
            "publication_eval_id": publication_eval_id,
            "gap_ids": gap_ids,
            "target_surface": {
                "ref_kind": "publication_eval_recommended_action",
                "route_target": lane,
                "surface_ref": "artifacts/controller/repair_execution_evidence/latest.json",
                "recommended_action_id": _non_empty_text(action.get("action_id")),
                "route_key_question": _non_empty_text(action.get("route_key_question")),
                "route_rationale": _non_empty_text(action.get("route_rationale")),
                "stage_typed_blocker_ref": stage_typed_blocker_ref,
                "publication_eval_id": publication_eval_id,
                "gap_ids": gap_ids,
                "required_output_contract": required_output_contract,
                "next_work_unit": next_work_unit or None,
                "blocking_work_units": _mapping_items(action.get("blocking_work_units")),
                "gaps": [gap for gap in gaps if gap],
            },
            "target_surface_specificity": "publication_eval_readiness_blocker_derived_repair",
            "source_ref": source_ref,
            "acceptance_refs": _dedupe_text(_text_items(action.get("evidence_refs"))),
            "readiness_blocker_precedence": {
                "superseded_readiness_action": READINESS_ACTION,
                "reason": "superseded_by_readiness_blocker_derived_repair",
                "publication_eval_verdict": _non_empty_text(
                    _mapping_copy(publication_eval.get("verdict")).get("overall_verdict")
                ),
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def _publication_eval_route_back_action(publication_eval: Mapping[str, Any]) -> dict[str, Any]:
    for action in _mapping_items(publication_eval.get("recommended_actions")):
        if _non_empty_text(action.get("action_type")) != "route_back_same_line":
            continue
        if _non_empty_text(action.get("priority")) not in {"now", "high", "required"}:
            continue
        if not _mapping_copy(action.get("next_work_unit")):
            continue
        return action
    return {}


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


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


__all__ = ["owner_action_from_publication_eval_readiness_blocker_repair"]
