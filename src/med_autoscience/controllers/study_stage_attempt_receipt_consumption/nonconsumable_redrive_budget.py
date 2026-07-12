from __future__ import annotations

from collections.abc import Mapping
from typing import Any


REDRIVE_BUDGET = 1
REDRIVE_BUDGET_EXHAUSTED_REASON = "progress_first_owner_redrive_budget_exhausted"


def match(
    *,
    execution: Mapping[str, Any],
    receipt_ref: str,
    action_type: str | None,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
    reason: str,
) -> dict[str, Any]:
    return {
        "receipt_ref": str(receipt_ref),
        "execution_id": _text(execution.get("execution_id")),
        "action_type": action_type,
        "execution_status": _text(execution.get("execution_status")),
        "owner_result_status": _text(owner_result.get("status")),
        "repair_execution_evidence_status": _text(repair_evidence.get("status")),
        "reason": reason,
        "changed_artifact_ref_count": len(_mapping_list(repair_evidence.get("changed_artifact_refs"))),
    }


def reason(
    *,
    action_type: str | None,
    owner_result: Mapping[str, Any],
    repair_evidence: Mapping[str, Any],
    dispatch_zero_execution_blocker: bool,
) -> str:
    if action_type == "run_quality_repair_batch":
        if dispatch_zero_execution_blocker:
            return "stage_outcome_authority_execution_count_zero"
        hygiene = _mapping(repair_evidence.get("manuscript_surface_hygiene"))
        if (
            hygiene.get("story_surface_delta_required") is True
            and hygiene.get("story_surface_delta_present") is not True
        ):
            return "manuscript_story_surface_delta_missing"
        if blocked_reason := _text(owner_result.get("blocked_reason")):
            return blocked_reason
        if _text(repair_evidence.get("status")) == "progress_delta_candidate":
            return "required_story_surface_delta_or_typed_blocker_missing"
    return (
        _text(owner_result.get("blocked_reason"))
        or _text(repair_evidence.get("blocked_reason"))
        or _text(owner_result.get("status"))
        or _text(repair_evidence.get("status"))
        or "owner_callable_adapter_closeout_not_consumable"
    )


def budget_exhausted(matches: list[Mapping[str, Any]]) -> bool:
    return len(matches) > REDRIVE_BUDGET


def consumption(
    *,
    latest: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    repeat_count: int,
) -> dict[str, Any]:
    reason = _text(latest.get("reason")) or "owner_callable_adapter_closeout_not_consumable"
    return {
        "status": "consumed",
        "receipt_kind": "owner_callable_adapter_receipt",
        "receipt_ref": _text(latest.get("receipt_ref")),
        "execution_id": _text(latest.get("execution_id")),
        "action_type": _text(latest.get("action_type")),
        "execution_status": "completed_with_quality_debt",
        "owner_result_status": "completed_with_quality_debt",
        "repair_execution_evidence_status": "quality_budget_exhausted",
        "quality_debt": {
            "surface_kind": "mas_progress_first_quality_debt",
            "schema_version": 1,
            "reason": REDRIVE_BUDGET_EXHAUSTED_REASON,
            "detail_reason": reason,
            "repeat_count": repeat_count,
            "nonconsumable_closeout_redrive_budget": REDRIVE_BUDGET,
            "blocks_stage_transition": False,
            "blocks_quality_or_ready_claims": True,
            "route_selection_owner": "codex_cli",
        },
        "nonconsumable_closeout_reason": reason,
        "nonconsumable_closeout_repeat_count": repeat_count,
        "nonconsumable_closeout_redrive_budget": REDRIVE_BUDGET,
        "consumed_owner_route_idempotency_key": _text(owner_route.get("idempotency_key")),
        "consumed_owner_route_epoch": _text(owner_route.get("route_epoch")),
        "consumed_owner_route_source_fingerprint": _text(owner_route.get("source_fingerprint")),
        "changed_artifact_ref_count": int(latest.get("changed_artifact_ref_count") or 0),
        "quality_authorized": False,
        "submission_authorized": False,
        "current_package_write_authorized": False,
        "next_action": "codex_select_next_declared_stage_with_quality_debt",
        "next_stage_may_start": True,
    }


def _mapping_list(value: object) -> list[Mapping[str, Any]]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, Mapping)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "REDRIVE_BUDGET",
    "REDRIVE_BUDGET_EXHAUSTED_REASON",
    "budget_exhausted",
    "consumption",
    "match",
    "reason",
]
