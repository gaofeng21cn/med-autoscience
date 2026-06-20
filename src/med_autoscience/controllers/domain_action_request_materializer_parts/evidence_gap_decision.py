from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.evidence_gap_projection import attach_evidence_gap_projection


def projection_for_action(
    action: Mapping[str, Any],
    *,
    text,
    mapping,
) -> dict[str, Any]:
    return attach_evidence_gap_projection(
        {
            "study_id": text(action.get("study_id")),
            "quest_id": text(action.get("quest_id")) or text(mapping(action.get("handoff_packet")).get("quest_id")),
            "current_executable_owner_action": dict(action),
            "evidence_gap_decisions": list(action.get("evidence_gap_decisions") or []),
            "evidence_gap_inputs": _evidence_gap_inputs(action),
            "missing_evidence_refs": list(action.get("missing_evidence_refs") or []),
            "refs": mapping(action.get("refs")),
        }
    )


def prompt_fields(projection: Mapping[str, Any], *, mapping) -> dict[str, Any]:
    summary = mapping(projection.get("evidence_gap_decision_summary"))
    return {
        "evidence_gap_decisions": list(projection.get("evidence_gap_decisions") or []),
        "evidence_gap_decision_summary": dict(summary),
        "assumption_ledger": list(projection.get("assumption_ledger") or []),
        "soft_gap_ledger": list(projection.get("soft_gap_ledger") or []),
        "observability_backlog": list(projection.get("observability_backlog") or []),
        "evidence_tail_ledger": list(projection.get("evidence_tail_ledger") or []),
        "evidence_gap_typed_blockers": list(projection.get("evidence_gap_typed_blockers") or []),
        "evidence_gap_typed_blocker_count": int(projection.get("evidence_gap_typed_blocker_count") or 0),
        "forbidden_claims": list(summary.get("forbidden_claims") or []),
        "current_action_can_continue": summary.get("current_action_can_continue") is True,
        "paper_progress_claim_authorized_by_evidence_gap_policy": False,
        "readiness_claim_authorized_by_evidence_gap_policy": False,
    }


def blocked_reason(projection: Mapping[str, Any], *, mapping) -> str | None:
    summary = mapping(projection.get("evidence_gap_decision_summary"))
    if int(summary.get("hard_gate_count") or 0) > 0:
        return "evidence_gap_authority_gate_required"
    if int(summary.get("human_gate_count") or 0) > 0:
        return "evidence_gap_human_gate_required"
    return None


def inputs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    return _evidence_gap_inputs(payload)


def _evidence_gap_inputs(payload: Mapping[str, Any]) -> list[dict[str, Any]]:
    inputs: list[dict[str, Any]] = []
    for key in ("evidence_gap_inputs", "evidence_gap_decision_inputs"):
        for item in payload.get(key) or []:
            if isinstance(item, Mapping):
                inputs.append(dict(item))
    handoff = payload.get("handoff_packet")
    if not isinstance(handoff, Mapping):
        return inputs
    for key in ("evidence_gap_inputs", "evidence_gap_decision_inputs"):
        for item in handoff.get(key) or []:
            if isinstance(item, Mapping):
                inputs.append(dict(item))
    return inputs


__all__ = ["blocked_reason", "inputs", "projection_for_action", "prompt_fields"]
