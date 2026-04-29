from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any

from med_autoscience.controllers.auto_runtime_parking import (
    build_auto_runtime_parked_projection,
    is_auto_runtime_parked,
)


def build_progress_parked_projection(
    status: Mapping[str, Any],
    *,
    needs_user_decision: bool,
    manual_finish_contract: Mapping[str, Any] | None,
    task_intake_progress_override: Mapping[str, Any] | None,
) -> dict[str, Any]:
    projection = build_auto_runtime_parked_projection(
        status,
        needs_user_decision=needs_user_decision,
        manual_finish_contract=manual_finish_contract,
    )
    if task_intake_progress_override and is_auto_runtime_parked(projection):
        quality_closure_truth = (
            dict(task_intake_progress_override.get("quality_closure_truth") or {})
            if isinstance(task_intake_progress_override.get("quality_closure_truth"), Mapping)
            else {}
        )
        if str(quality_closure_truth.get("state") or "").strip() == "stop_loss_recommended":
            return projection
        return {
            **projection,
            "parked": False,
            "resource_release_expected": False,
            "awaiting_explicit_wakeup": False,
            "auto_execution_complete": False,
            "superseded_by_task_intake": True,
            "summary": "最新用户反馈或 task intake 已重新激活当前论文线，原 parked 状态不再作为当前前台主状态。",
            "next_action_summary": "按最新用户反馈重新进入同一论文线修订。",
        }
    return projection


def projected_current_stage(current_stage: str, parked_projection: Mapping[str, Any]) -> str:
    return "auto_runtime_parked" if is_auto_runtime_parked(parked_projection) else current_stage


def parked_text_override(
    value: str,
    parked_projection: Mapping[str, Any],
    field: str,
    *,
    display_text: Callable[[object], str | None],
) -> str:
    if not is_auto_runtime_parked(parked_projection):
        return value
    parked_value = parked_projection.get(field)
    return display_text(parked_value) or str(parked_value or value)


def parked_progress_fields(parked_projection: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "auto_runtime_parked": parked_projection,
        "parked_state": parked_projection.get("parked_state"),
        "parked_owner": parked_projection.get("parked_owner"),
        "resource_release_expected": parked_projection.get("resource_release_expected"),
        "awaiting_explicit_wakeup": parked_projection.get("awaiting_explicit_wakeup"),
        "auto_execution_complete": parked_projection.get("auto_execution_complete"),
        "reopen_policy": parked_projection.get("reopen_policy"),
        "legacy_current_stage": parked_projection.get("legacy_current_stage"),
    }
