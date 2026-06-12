from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.study_progress_parts.shared import (
    _mapping_copy,
    _non_empty_text,
)


RUNNING_PROVIDER_STAGE_SUMMARY = "托管运行时正在自动推进研究，前台当前应以监督为主。"
RUNNING_PROVIDER_NEXT_ACTION = (
    "继续监督当前 OPL provider attempt；不要重复启动、hydrate 或 redrive 同一 current work unit。"
)
RUNNING_PROVIDER_SUPERSEDED_BLOCKERS = frozenset(
    {
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_execution_authorization_required",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "quest_waiting_opl_runtime_owner_route",
        "repair_progress_ai_reviewer_recheck_required",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
TERMINAL_CLOSEOUT_STATUSES = frozenset(
    {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "executed_with_owner_receipt",
        "failed",
        "record_only_archive_materialized",
        "terminal",
        "typed_blocked",
    }
)
TERMINAL_CLOSEOUT_OUTCOMES = frozenset(
    {
        "closed_with_domain_owner_refs",
        "completed",
        "completed_without_owner_answer",
        "owner_receipt",
        "typed_blocker",
    }
)


def apply_running_provider_attempt_top_level_status(payload: dict[str, Any]) -> dict[str, Any]:
    if not _payload_has_running_provider_attempt(payload):
        return payload
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    if _payload_has_matching_terminal_closeout(payload):
        return payload
    updated = dict(payload)
    active_run_id = (
        _non_empty_text(handoff.get("active_run_id"))
        or _non_empty_text(updated.get("active_run_id"))
        or _non_empty_text(_mapping_copy(updated.get("supervision")).get("active_run_id"))
    )
    monitoring = _mapping_copy(updated.get("progress_first_monitoring_summary"))
    active_stage_attempt_id = (
        _non_empty_text(handoff.get("active_stage_attempt_id"))
        or _non_empty_text(monitoring.get("active_stage_attempt_id"))
    )
    active_workflow_id = (
        _non_empty_text(handoff.get("active_workflow_id"))
        or _non_empty_text(monitoring.get("active_workflow_id"))
    )
    current_blockers = _running_provider_current_blockers(updated.get("current_blockers"))
    updated["current_stage"] = "managed_runtime_active"
    updated["current_stage_summary"] = RUNNING_PROVIDER_STAGE_SUMMARY
    updated["next_system_action"] = RUNNING_PROVIDER_NEXT_ACTION
    updated["active_run_id"] = active_run_id
    updated["current_blockers"] = current_blockers
    updated["auto_runtime_parked"] = _running_provider_superseded_parked_projection(
        updated.get("auto_runtime_parked")
    )
    updated["parked_state"] = None
    updated["parked_owner"] = None
    updated["resource_release_expected"] = False
    updated["awaiting_explicit_wakeup"] = False
    updated["auto_execution_complete"] = False
    updated["reopen_policy"] = None
    updated["study_macro_state"] = _running_provider_macro_state(
        payload=updated,
        active_run_id=active_run_id,
    )
    updated["intervention_lane"] = _running_provider_intervention_lane(
        handoff=handoff,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    updated["status_narration_contract"] = _running_provider_status_narration_contract(
        updated.get("status_narration_contract"),
        current_blockers=current_blockers,
    )
    updated["supervision"] = _running_provider_supervision(
        updated.get("supervision"),
        active_run_id=active_run_id,
    )
    updated["user_visible_projection"] = _running_provider_user_visible_projection(
        updated.get("user_visible_projection"),
        current_blockers=current_blockers,
        active_run_id=active_run_id,
    )
    updated["operator_status_card"] = _running_provider_operator_status_card(
        updated.get("operator_status_card"),
    )
    return updated


def _payload_has_running_provider_attempt(payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) == "running_provider_attempt":
        return True
    envelope = _mapping_copy(payload.get("current_execution_envelope"))
    if _non_empty_text(envelope.get("state_kind")) == "running_provider_attempt":
        return True
    monitoring = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    if monitoring.get("running_provider_attempt") is True:
        return True
    return _handoff_has_strict_live_provider_attempt(
        _mapping_copy(payload.get("opl_current_control_state_handoff"))
    )


def _running_provider_current_blockers(value: object) -> list[str]:
    blockers = _text_list(value)
    return [
        item
        for item in blockers
        if item not in RUNNING_PROVIDER_SUPERSEDED_BLOCKERS
    ][:8]


def _running_provider_superseded_parked_projection(value: object) -> dict[str, Any]:
    parked = _mapping_copy(value)
    if not parked:
        return {"parked": False, "superseded_by_running_provider_attempt": True}
    parked.update(
        {
            "parked": False,
            "parked_state": None,
            "parked_state_label": None,
            "parked_owner": None,
            "resource_release_expected": False,
            "awaiting_explicit_wakeup": False,
            "auto_execution_complete": False,
            "superseded_by_running_provider_attempt": True,
            "summary": RUNNING_PROVIDER_STAGE_SUMMARY,
            "next_action_summary": RUNNING_PROVIDER_NEXT_ACTION,
        }
    )
    return parked


def _running_provider_macro_state(
    *,
    payload: Mapping[str, Any],
    active_run_id: str | None,
) -> dict[str, Any]:
    macro = _mapping_copy(payload.get("study_macro_state"))
    details = _mapping_copy(macro.get("details"))
    details.update(
        {
            "active_run_id": active_run_id,
            "running_provider_attempt": True,
            "current_stage": "managed_runtime_active",
        }
    )
    return {
        **macro,
        "surface": _non_empty_text(macro.get("surface")) or "study_macro_state",
        "schema_version": macro.get("schema_version") or 1,
        "study_id": _non_empty_text(macro.get("study_id")) or _non_empty_text(payload.get("study_id")),
        "writer_state": "live",
        "user_next": "watch",
        "reason": "running_provider_attempt",
        "details": details,
    }


def _running_provider_intervention_lane(
    *,
    handoff: Mapping[str, Any],
    active_run_id: str | None,
    active_stage_attempt_id: str | None,
    active_workflow_id: str | None,
) -> dict[str, Any]:
    return {
        "lane_id": "runtime_running_watch",
        "title": "监督当前 OPL provider attempt",
        "severity": "monitor",
        "summary": RUNNING_PROVIDER_STAGE_SUMMARY,
        "recommended_action_id": "watch_running_provider_attempt",
        "route_target": "one-person-lab",
        "route_target_label": "one-person-lab",
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "source_path": _non_empty_text(handoff.get("source_path")),
    }


def _running_provider_status_narration_contract(
    value: object,
    *,
    current_blockers: list[str],
) -> dict[str, Any]:
    contract = _mapping_copy(value)
    if not contract:
        return {}
    stage = _mapping_copy(contract.get("stage"))
    stage["current_stage"] = "managed_runtime_active"
    stage["intervention_lane"] = "runtime_running_watch"
    contract["stage"] = stage
    contract["latest_update"] = RUNNING_PROVIDER_STAGE_SUMMARY
    contract["next_step"] = RUNNING_PROVIDER_NEXT_ACTION
    contract["current_blockers"] = current_blockers
    return contract


def _running_provider_supervision(
    value: object,
    *,
    active_run_id: str | None,
) -> dict[str, Any]:
    supervision = _mapping_copy(value)
    supervision["active_run_id"] = active_run_id
    supervision["health_status"] = "live"
    return supervision


def _running_provider_user_visible_projection(
    value: object,
    *,
    current_blockers: list[str],
    active_run_id: str | None,
) -> dict[str, Any]:
    user_visible = _mapping_copy(value)
    if not user_visible:
        return {}
    user_visible.update(
        {
            "owner_resolution_state": "runtime_running",
            "writer_state": "live",
            "user_next": "watch",
            "reason": "running_provider_attempt",
            "actual_write_active": True,
            "user_action_required": False,
            "needs_user_decision": False,
            "needs_physician_decision": False,
            "state_label": "自动运行中",
            "state_summary": RUNNING_PROVIDER_STAGE_SUMMARY,
            "current_stage": "live",
            "current_stage_label": "自动运行中",
            "current_stage_summary": RUNNING_PROVIDER_STAGE_SUMMARY,
            "status_summary": RUNNING_PROVIDER_STAGE_SUMMARY,
            "current_blockers": current_blockers,
            "next_system_action": RUNNING_PROVIDER_NEXT_ACTION,
            "next_step": RUNNING_PROVIDER_NEXT_ACTION,
            "why_not_progressing": None,
        }
    )
    supervision = _mapping_copy(user_visible.get("supervision"))
    supervision["active_run_id"] = active_run_id
    supervision["health_status"] = "live"
    user_visible["supervision"] = supervision
    return user_visible


def _running_provider_operator_status_card(value: object) -> dict[str, Any]:
    operator_status = _mapping_copy(value)
    if not operator_status:
        return {}
    for key in (
        "auto_runtime_parked",
        "parked_state",
        "resource_release_expected",
        "awaiting_explicit_wakeup",
        "auto_execution_complete",
        "reopen_policy",
    ):
        operator_status.pop(key, None)
    operator_status.update(
        {
            "handling_state": "monitor_only",
            "handling_state_label": "持续监管",
            "owner_summary": "OPL 持有当前 provider attempt，MAS 只投影 refs-only 监督状态。",
            "current_focus": RUNNING_PROVIDER_NEXT_ACTION,
            "human_surface_freshness": "monitoring_runtime",
            "human_surface_summary": "当前优先看结构化监管真相，给人看的稿件表面还不是主判断面。",
            "next_confirmation_signal": None,
            "user_visible_verdict": "OPL provider attempt 正在运行；MAS 不应重复启动或重派同一 work unit。",
        }
    )
    return operator_status


def _handoff_has_strict_live_provider_attempt(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if _handoff_has_matching_terminal_closeout(handoff):
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_liveness_status = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    return runtime_liveness_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } or health_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }


def _payload_has_matching_terminal_closeout(payload: Mapping[str, Any]) -> bool:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    monitoring = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    active_attempt_id = (
        _handoff_stage_attempt_id(handoff)
        or _non_empty_text(monitoring.get("active_stage_attempt_id"))
        or _stage_attempt_id_from_active_run_id(payload.get("active_run_id"))
        or _stage_attempt_id_from_active_run_id(
            _mapping_copy(payload.get("supervision")).get("active_run_id")
        )
    )
    return any(
        _terminal_matches_active_attempt(
            terminal=_mapping_copy(value),
            active_attempt_id=active_attempt_id,
        )
        for value in (
            handoff.get("latest_terminal_stage_log"),
            monitoring.get("latest_terminal_stage"),
            monitoring.get("latest_terminal_stage_log"),
            payload.get("latest_terminal_stage"),
            payload.get("latest_terminal_stage_log"),
        )
    )


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    return _terminal_matches_active_attempt(
        terminal=_mapping_copy(handoff.get("latest_terminal_stage_log")),
        active_attempt_id=_handoff_stage_attempt_id(handoff),
    )


def _terminal_matches_active_attempt(
    *,
    terminal: Mapping[str, Any],
    active_attempt_id: str | None,
) -> bool:
    if not terminal:
        return False
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _non_empty_text(terminal.get("status"))
    if status in TERMINAL_CLOSEOUT_STATUSES:
        return True
    outcome = _non_empty_text(terminal.get("outcome"))
    if outcome in TERMINAL_CLOSEOUT_OUTCOMES:
        return True
    if _text_list(terminal.get("closeout_refs")):
        return True
    return (
        _non_empty_text(terminal.get("source_path")) is not None
        and _non_empty_text(terminal.get("record_path")) is not None
    )


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _non_empty_text(handoff.get("active_stage_attempt_id")):
        return text
    if text := _non_empty_text(handoff.get("stage_attempt_id")):
        return text
    if text := _non_empty_text(handoff.get("attempt_id")):
        return text
    return _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))


def _stage_attempt_id_from_active_run_id(value: object) -> str | None:
    active_run_id = _non_empty_text(value)
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]
