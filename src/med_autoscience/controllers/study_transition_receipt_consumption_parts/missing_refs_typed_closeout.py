from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

_DEFAULT_EXECUTOR_BLOCKED_STATUSES = frozenset({"blocked"})
_TYPED_CLOSEOUT_STATUSES = frozenset(
    {
        "blocked",
        "blocked_with_domain_typed_blocker",
        "closed_with_typed_blocker",
        "typed_blocker",
    }
)
_TYPED_CLOSEOUT_OUTCOMES = frozenset(
    {
        "blocked_with_domain_typed_blocker",
        "repeat_suppressed_with_typed_blocker",
        "typed_blocker",
        "typed_blocker_anti_loop_budget_exhausted",
    }
)
_ANTI_LOOP_BUDGET_EXHAUSTED = "anti_loop_budget_exhausted"


def is_blocked_typed_closeout(
    *,
    execution: Mapping[str, Any],
    receipt_ref: str,
) -> bool:
    if not str(receipt_ref).endswith(".closeout.json"):
        return False
    owner_result = _mapping(execution.get("owner_result"))
    if (
        _text(execution.get("execution_status")) in _DEFAULT_EXECUTOR_BLOCKED_STATUSES
        and bool(_text(owner_result.get("blocked_reason")))
    ):
        return True
    if _typed_blocker_reason(execution):
        return True
    if _anti_loop_budget_exhausted(execution):
        return True
    return _text(execution.get("stage_closeout_status")) in _TYPED_CLOSEOUT_STATUSES or _text(
        execution.get("stage_closeout_outcome")
    ) in _TYPED_CLOSEOUT_OUTCOMES


def is_missing_refs_typed_closeout(
    *,
    execution: Mapping[str, Any],
    receipt_ref: str,
) -> bool:
    if _text(execution.get("stage_closeout_surface_kind")) != "stage_attempt_closeout_packet":
        return False
    if not str(receipt_ref).endswith(".closeout.json"):
        return False
    required_ref_field = _text(execution.get("stage_closeout_required_ref_field")) or "closeout_refs"
    if required_ref_field != "closeout_refs":
        return False
    closeout_refs = _text_list(execution.get("stage_closeout_refs"))
    if closeout_refs:
        return False
    return _text(execution.get("stage_closeout_status")) in {"completed", "executed", "blocked"}


def consumption(
    *,
    execution: Mapping[str, Any],
    receipt_ref: str,
    owner_route: Mapping[str, Any],
    action_type: str | None,
) -> dict[str, Any]:
    reason = "typed_closeout_packet_required"
    closeout_ref = _relative_study_artifact_ref(receipt_ref) or str(receipt_ref)
    return {
        "status": "consumed",
        "receipt_kind": "default_executor_execution",
        "receipt_ref": str(receipt_ref),
        "closeout_ref": closeout_ref,
        "execution_id": _text(execution.get("execution_id")) or _text(execution.get("stage_attempt_id")),
        "action_type": action_type or _text(execution.get("action_type")),
        "execution_status": "blocked",
        "blocked_reason": reason,
        "owner_result_status": "blocked",
        "repair_execution_evidence_status": "typed_blocker",
        "typed_blocker": {
            "reason": reason,
            "next_owner": "one-person-lab",
            "write_permitted": False,
        },
        "consumed_owner_route_idempotency_key": _text(owner_route.get("idempotency_key")),
        "consumed_owner_route_epoch": _text(owner_route.get("route_epoch")),
        "consumed_owner_route_source_fingerprint": _text(owner_route.get("source_fingerprint")),
        "changed_artifact_ref_count": 0,
        "quality_authorized": False,
        "submission_authorized": False,
        "current_package_write_authorized": False,
        "next_action": "honor_typed_blocker_without_redrive",
    }


def _relative_study_artifact_ref(path_text: str) -> str:
    text = _text(path_text)
    if not text:
        return ""
    parts = Path(text).parts
    if "studies" in parts:
        index = parts.index("studies")
        if len(parts) > index + 2:
            return "/".join(parts[index + 2 :])
    return text


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [_text(item) for item in value if _text(item)]


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


def _typed_blocker_reason(execution: Mapping[str, Any]) -> str:
    typed_blocker = _mapping(execution.get("typed_blocker"))
    stage_closeout = _mapping(execution.get("stage_closeout"))
    stage_typed_blocker = _mapping(stage_closeout.get("typed_blocker"))
    paper_stage_log = _mapping(execution.get("paper_stage_log"))
    for value in (
        execution.get("typed_blocker_reason"),
        execution.get("blocked_reason"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocker_kind"),
        typed_blocker.get("reason"),
        typed_blocker.get("blocked_reason"),
        typed_blocker.get("blocker_id"),
        stage_typed_blocker.get("blocker_type"),
        stage_typed_blocker.get("blocker_kind"),
        stage_typed_blocker.get("reason"),
        stage_typed_blocker.get("blocked_reason"),
        stage_typed_blocker.get("blocker_id"),
    ):
        if text := _text(value):
            return text
    if _text(paper_stage_log.get("progress_delta_classification")) == "typed_blocker":
        return _text(paper_stage_log.get("outcome")) or "typed_blocker"
    return ""


def _anti_loop_budget_exhausted(execution: Mapping[str, Any]) -> bool:
    typed_blocker = _mapping(execution.get("typed_blocker"))
    stage_closeout = _mapping(execution.get("stage_closeout"))
    stage_typed_blocker = _mapping(stage_closeout.get("typed_blocker"))
    anti_loop_budget = _mapping(typed_blocker.get("anti_loop_budget")) or _mapping(
        stage_typed_blocker.get("anti_loop_budget")
    )
    paper_stage_log = _mapping(execution.get("paper_stage_log"))
    next_forced_delta = _mapping(paper_stage_log.get("next_forced_delta"))
    for value in (
        execution.get("typed_blocker_reason"),
        execution.get("blocked_reason"),
        execution.get("stage_closeout_outcome"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocker_kind"),
        typed_blocker.get("reason"),
        typed_blocker.get("blocked_reason"),
        stage_typed_blocker.get("blocker_type"),
        stage_typed_blocker.get("blocker_kind"),
        stage_typed_blocker.get("reason"),
        stage_typed_blocker.get("blocked_reason"),
        anti_loop_budget.get("status"),
        paper_stage_log.get("outcome"),
        next_forced_delta.get("reason"),
    ):
        text = _text(value)
        if text == _ANTI_LOOP_BUDGET_EXHAUSTED:
            return True
        if text == "exhausted" and anti_loop_budget:
            return True
        if _ANTI_LOOP_BUDGET_EXHAUSTED in text:
            return True
    return False
