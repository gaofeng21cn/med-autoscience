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
    publication_eval_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    projection = build_auto_runtime_parked_projection(
        status,
        needs_user_decision=needs_user_decision,
        manual_finish_contract=manual_finish_contract,
    )
    if _ai_reviewer_parked_state_superseded(
        projection,
        publication_eval_payload=publication_eval_payload,
    ):
        return {
            **projection,
            "parked": False,
            "parked_state": None,
            "parked_state_label": None,
            "parked_owner": None,
            "resource_release_expected": False,
            "awaiting_explicit_wakeup": False,
            "auto_execution_complete": False,
            "superseded_by_publication_eval": True,
            "summary": "AI reviewer 已经写入 publication_eval；当前不再是等待 AI reviewer，而是回到发表门控或控制面处理剩余科学锚点。",
            "next_action_summary": "按最新 publication_eval 继续处理发表门控、科学锚点或质量修订。",
        }
    if task_intake_progress_override and is_auto_runtime_parked(projection):
        if (
            projection.get("parked_state") == "explicit_resume_pending"
            and projection.get("source_reason")
            in {"completed_parked_auto_continue_no_new_message", "parked_after_checkpoint_no_new_message"}
        ):
            return projection
        quality_closure_truth = (
            dict(task_intake_progress_override.get("quality_closure_truth") or {})
            if isinstance(task_intake_progress_override.get("quality_closure_truth"), Mapping)
            else {}
        )
        if str(quality_closure_truth.get("state") or "").strip() == "stop_loss_recommended":
            return projection
        if str(quality_closure_truth.get("state") or "").strip() == "manual_hold":
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


def _ai_reviewer_parked_state_superseded(
    projection: Mapping[str, Any],
    *,
    publication_eval_payload: Mapping[str, Any] | None,
) -> bool:
    if projection.get("parked_state") != "ai_reviewer_pending":
        return False
    provenance = (
        dict(publication_eval_payload.get("assessment_provenance") or {})
        if isinstance(publication_eval_payload, Mapping)
        and isinstance(publication_eval_payload.get("assessment_provenance"), Mapping)
        else {}
    )
    return str(provenance.get("owner") or "").strip() == "ai_reviewer"


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
