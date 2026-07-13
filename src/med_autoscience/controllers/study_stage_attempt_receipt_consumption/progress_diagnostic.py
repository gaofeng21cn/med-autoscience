from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PROGRESS_DIAGNOSTIC_REASON = "owner_callable_output_not_consumable"


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
    dispatch_zero_execution_diagnostic: bool,
) -> str:
    if action_type == "run_quality_repair_batch":
        if dispatch_zero_execution_diagnostic:
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
            return "required_story_surface_delta_missing"
    return (
        _text(owner_result.get("blocked_reason"))
        or _text(repair_evidence.get("blocked_reason"))
        or _text(owner_result.get("status"))
        or _text(repair_evidence.get("status"))
        or PROGRESS_DIAGNOSTIC_REASON
    )


def consumption(
    *,
    diagnostic: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> dict[str, Any]:
    detail_reason = _text(diagnostic.get("reason")) or PROGRESS_DIAGNOSTIC_REASON
    diagnostic_ref = f"mas-progress-diagnostic:{detail_reason}"
    return {
        "status": "consumed",
        "receipt_kind": "owner_callable_adapter_receipt",
        "receipt_ref": _text(diagnostic.get("receipt_ref")),
        "execution_id": _text(diagnostic.get("execution_id")),
        "action_type": _text(diagnostic.get("action_type")),
        "execution_status": "completed_with_quality_debt",
        "owner_result_status": "completed_with_quality_debt",
        "repair_execution_evidence_status": "progress_diagnostic",
        "progress_diagnostic": {
            "surface_kind": "mas_no_output_or_failure_diagnostic",
            "schema_version": 1,
            "diagnostic_ref": diagnostic_ref,
            "reason": PROGRESS_DIAGNOSTIC_REASON,
            "detail_reason": detail_reason,
            "consumable_by_next_stage": True,
            "route_selection_owner": "codex_cli",
        },
        "quality_debt": {
            "surface_kind": "mas_progress_first_quality_debt",
            "schema_version": 1,
            "reason": PROGRESS_DIAGNOSTIC_REASON,
            "detail_reason": detail_reason,
            "blocks_stage_transition": False,
            "blocks_quality_or_ready_claims": True,
            "route_selection_owner": "codex_cli",
        },
        "changed_artifact_ref_count": int(diagnostic.get("changed_artifact_ref_count") or 0),
        "consumed_owner_route_idempotency_key": _text(owner_route.get("idempotency_key")),
        "consumed_owner_route_epoch": _text(owner_route.get("route_epoch")),
        "consumed_owner_route_source_fingerprint": _text(owner_route.get("source_fingerprint")),
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


__all__ = ["PROGRESS_DIAGNOSTIC_REASON", "consumption", "match", "reason"]
