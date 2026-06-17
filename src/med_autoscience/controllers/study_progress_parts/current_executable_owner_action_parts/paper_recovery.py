from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)
from med_autoscience.runtime_control.owner_route_attempt_protocol import normalize_currentness_sources


PAPER_RECOVERY_SUCCESSOR_SOURCE = "paper_recovery_state.next_safe_action.successor_owner_action"
PAPER_RECOVERY_SUCCESSOR_DELTA_KIND = "paper_recovery_successor_owner_delta_or_typed_blocker"


def owner_action_from_paper_recovery_state(
    payload: Mapping[str, Any],
    *,
    surface_kind: str,
) -> dict[str, Any] | None:
    recovery = _mapping_copy(payload.get("paper_recovery_state"))
    if _non_empty_text(recovery.get("phase")) != "owner_action_ready":
        return None
    decision = _mapping_copy(recovery.get("supervisor_decision"))
    if _non_empty_text(decision.get("decision")) not in {
        None,
        "materialize_recovery_action",
    }:
        return None
    next_safe_action = _mapping_copy(recovery.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) != "materialize_successor_owner_action":
        return None
    successor = _mapping_copy(next_safe_action.get("successor_owner_action"))
    action_type = _non_empty_text(successor.get("action_type"))
    work_unit_id = _non_empty_text(successor.get("work_unit_id"))
    if action_type is None or work_unit_id is None:
        return None
    owner = (
        _non_empty_text(successor.get("owner"))
        or _non_empty_text(next_safe_action.get("owner"))
        or _non_empty_text(_mapping_copy(recovery.get("current_authority")).get("owner"))
    )
    if owner is None:
        return None
    fingerprint = _non_empty_text(successor.get("work_unit_fingerprint")) or _non_empty_text(
        successor.get("action_fingerprint")
    )
    if fingerprint is None:
        return None
    source_eval_id = _non_empty_text(successor.get("source_eval_id")) or _non_empty_text(
        _mapping_copy(payload.get("publication_eval")).get("eval_id")
    )
    source_ref = _non_empty_text(successor.get("source_ref"))
    source_surface = _non_empty_text(successor.get("source_surface"))
    supervisor_decision_ref = (
        _non_empty_text(decision.get("decision_id"))
        or _non_empty_text(decision.get("paper_autonomy_obligation_ref"))
        or _non_empty_text(decision.get("source_recovery_obligation_ref"))
    )
    owner_route_currentness_basis = normalize_currentness_sources(
        _mapping_copy(successor.get("owner_route_currentness_basis")),
        _mapping_copy(successor.get("currentness_basis")),
        _mapping_copy(next_safe_action.get("owner_route_currentness_basis")),
        _mapping_copy(recovery.get("owner_route_currentness_basis")),
        {
            "source_eval_id": source_eval_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
        },
    )
    return _compact(
        {
            "surface_kind": surface_kind,
            "schema_version": 1,
            "status": "ready",
            "source": "paper_recovery_state.next_safe_action.successor_owner_action",
            "source_surface": source_surface,
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": fingerprint,
            "source_eval_id": source_eval_id,
            "action_type": action_type,
            "allowed_actions": [action_type],
            "owner_receipt_required": True,
            "required_delta_kind": "paper_recovery_successor_owner_delta_or_typed_blocker",
            "target_surface": _compact(
                {
                    "ref_kind": "paper_recovery_successor_owner_action",
                    "route_target": owner,
                    "surface_ref": _required_output_surface(action_type),
                    "source_surface": source_surface,
                    "source_ref": source_ref,
                    "supervisor_decision_ref": supervisor_decision_ref,
                }
            ),
            "target_surface_specificity": "paper_recovery_successor_owner_action",
            "source_ref": source_ref,
            "acceptance_refs": _dedupe_text(
                [
                    source_ref,
                    supervisor_decision_ref,
                    *_text_items(decision.get("evidence_refs")),
                    *_text_items(successor.get("evidence_refs")),
                ]
            ),
            "owner_route_currentness_basis": owner_route_currentness_basis,
            "paper_recovery_successor": {
                "phase": "owner_action_ready",
                "source_next_safe_action_kind": "materialize_successor_owner_action",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
                "opl_transition_runtime_required": True,
                "source_surface": source_surface,
            },
            "authority_boundary": _authority_boundary(),
        }
    )


def paper_recovery_successor_supersedes_gate_replay_blocker(
    *,
    paper_recovery_action: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> bool:
    action = _mapping_copy(paper_recovery_action)
    if not action:
        return False
    successor = _mapping_copy(action.get("paper_recovery_successor"))
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    blocker_type = (
        _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocker_id"))
        or _non_empty_text(typed_blocker.get("blocked_reason"))
        or _non_empty_text(current_work_unit.get("blocked_reason"))
        or _non_empty_text(state.get("blocked_reason"))
    )
    if blocker_type != "publication_gate_replay_blocked":
        return False
    return paper_recovery_successor_action_ready(action)


def paper_recovery_successor_action_ready(
    paper_recovery_action: Mapping[str, Any] | None,
) -> bool:
    action = _mapping_copy(paper_recovery_action)
    if not action:
        return False
    if _non_empty_text(action.get("source")) != PAPER_RECOVERY_SUCCESSOR_SOURCE:
        return False
    if action.get("owner_receipt_required") is not True:
        return False
    successor = _mapping_copy(action.get("paper_recovery_successor"))
    if successor and _non_empty_text(successor.get("source_next_safe_action_kind")) not in {
        None,
        "materialize_successor_owner_action",
    }:
        return False
    if _non_empty_text(action.get("required_delta_kind")) != PAPER_RECOVERY_SUCCESSOR_DELTA_KIND:
        return False
    return (
        _non_empty_text(action.get("action_type")) is not None
        and _non_empty_text(action.get("work_unit_id")) is not None
        and _non_empty_text(action.get("work_unit_fingerprint")) is not None
    )


def _required_output_surface(action_type: str) -> str:
    if action_type == "run_quality_repair_batch":
        return "artifacts/controller/repair_execution_evidence/latest.json"
    if action_type == "run_gate_clearing_batch":
        return "artifacts/controller/gate_clearing_batch/latest.json"
    if action_type == "return_to_ai_reviewer_workflow":
        return "artifacts/publication_eval/latest.json"
    return "owner receipt or stable typed blocker"


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
    "owner_action_from_paper_recovery_state",
    "paper_recovery_successor_action_ready",
    "paper_recovery_successor_supersedes_gate_replay_blocker",
]
