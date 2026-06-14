from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import (
    domain_health_diagnostic_outer_loop_dispatch,
    domain_health_diagnostic_work_units,
)
from med_autoscience.controllers.domain_health_diagnostic_parts import managed_recovery
from med_autoscience.controllers.domain_health_diagnostic_parts.control_plane_gate import (
    CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
    _candidate_path,
    _non_empty_text,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.reporting import (
    _attach_family_companion_to_quest_report,
    write_domain_health_diagnostic_report,
)
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state


_NO_OP_SUPPRESSION_SUMMARY = "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。"
_WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY = "同一 controller work unit 已达到有界 redrive 上限，需 OPL runtime handoff后再继续。"
PROGRESS_CURRENTNESS_KEYS = (
    "study_id",
    "quest_id",
    "study_root",
    "workspace_root",
    "runtime_root",
    "current_work_unit",
    "current_execution_envelope",
    "current_executable_owner_action",
    "current_owner_ticket",
    "domain_transition",
    "progress_first_monitoring_summary",
    "gate_clearing_batch_followthrough",
    "opl_current_control_state_handoff",
    "intervention_lane",
    "study_intervention_events",
    "provider_admission_candidates",
    "provider_admission_pending_count",
    "paper_recovery_state",
)


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _outer_loop_request_is_stop_runtime(tick_request: Mapping[str, Any]) -> bool:
    controller_actions = tick_request.get("controller_actions")
    first_action = (
        controller_actions[0]
        if isinstance(controller_actions, list | tuple)
        and controller_actions
        and isinstance(controller_actions[0], Mapping)
        else {}
    )
    return _non_empty_text(first_action.get("action_type")) == "stop_runtime"


def _managed_study_recovery_failure_payload(
    *,
    preflight_payload: Mapping[str, Any],
    error: Exception,
) -> dict[str, Any]:
    return managed_recovery.recovery_failure_payload(
        preflight_payload=preflight_payload,
        error=error,
    )


def _serialize_no_op_suppression(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    wakeup_audit: Mapping[str, Any],
) -> dict[str, Any] | None:
    outcome = _non_empty_text(wakeup_audit.get("outcome"))
    if outcome not in {
        "skipped_matching_work_unit",
        "skipped_matching_decision",
        "skipped_unchanged_inputs",
        "needs_specificity",
        "opl_runtime_handoff_required",
        "controller_work_unit_blocked",
        "control_plane_dispatch_blocked",
        "explicit_wakeup_required",
        "non_dispatching_runtime_stop",
    }:
        return None
    payload: dict[str, Any] = {
        "study_id": _non_empty_text(status_payload.get("study_id")) or Path(study_root).name,
        "quest_id": _non_empty_text(status_payload.get("quest_id")),
        "outcome": outcome,
        "reason": _non_empty_text(wakeup_audit.get("reason")),
        "dedupe_scope": _non_empty_text(wakeup_audit.get("dedupe_scope")),
    }
    for key in (
        "work_unit_fingerprint",
        "next_work_unit",
        "specificity_questions",
        "specificity_targets",
        "work_unit_dispatch_key",
        "redrive_attempt_count",
        "max_redrive_attempts",
        "opl_runtime_handoff_kind",
        "controller_work_unit_block",
        "authority_snapshot",
        "control_plane_blocking_reasons",
        "explicit_wakeup_contract",
        "controller_authorization_ref",
        "control_intent_lifecycle_ref",
    ):
        value = wakeup_audit.get(key)
        if value is not None:
            payload[key] = dict(value) if isinstance(value, Mapping) else value
    if outcome == "needs_specificity":
        payload["operator_summary"] = "Publication gate 只给出标签级 blocker；需先明确具体 claim、证据、图表、指标、引用或包件目标。"
    elif outcome == "skipped_matching_work_unit":
        payload["operator_summary"] = _NO_OP_SUPPRESSION_SUMMARY
    elif outcome == "opl_runtime_handoff_required":
        payload["operator_summary"] = _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY
    elif outcome == "controller_work_unit_blocked":
        payload["operator_summary"] = "MAS controller work unit failed closed; supervisor/read-model surfaces must route the typed blocker to the next owner."
    elif outcome == "control_plane_dispatch_blocked":
        payload["operator_summary"] = CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY
    elif outcome == "explicit_wakeup_required":
        payload["operator_summary"] = "该 study 已进入用户暂停或手动停驻合同；继续监测，但等待显式唤醒前不派发自动 owner work。"
    elif outcome == "non_dispatching_runtime_stop":
        payload["operator_summary"] = "运行时停止类 controller decision 已物化；不通过外环 dispatch 启动新的执行。"
    else:
        payload["operator_summary"] = "外环输入或 controller decision 未变化；保持 no-op，等待新证据、新用户反馈或 blocker fingerprint 改变。"
    return payload


def _blocked_outer_loop_wakeup_audit(
    *,
    wakeup_audit: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    outer_loop_result: Mapping[str, Any],
    reason: str,
    work_unit_dispatch_key: str | None,
) -> dict[str, Any] | None:
    if _non_empty_text(outer_loop_result.get("dispatch_status")) != "blocked":
        return None
    executed_action = outer_loop_result.get("executed_controller_action")
    action_result = (
        executed_action.get("result")
        if isinstance(executed_action, Mapping) and isinstance(executed_action.get("result"), Mapping)
        else None
    )
    blockers: list[str] = []
    if action_result is not None:
        for value in (
            action_result.get("blocked_reason"),
            action_result.get("status"),
        ):
            if text := _non_empty_text(value):
                blockers.append(text)
        for item in action_result.get("blockers") or []:
            if text := _non_empty_text(item):
                blockers.append(text)
    return {
        **wakeup_audit,
        "outcome": "controller_work_unit_blocked",
        "reason": reason,
        "no_op_acknowledged": True,
        "dedupe_scope": "controller_work_unit_blocked",
        "operator_summary": "MAS controller work unit failed closed; domain_health_diagnostic recorded the blocker and left the next owner route to supervisor/read-model surfaces.",
        "dispatch": domain_health_diagnostic_outer_loop_dispatch.serialize_outer_loop_dispatch(
            tick_request=tick_request,
            outer_loop_result=outer_loop_result,
        ),
        "controller_work_unit_block": {
            "dispatch_status": "blocked",
            "blocked_reason": next(iter(dict.fromkeys(blockers)), None),
            "blocking_reasons": list(dict.fromkeys(blockers)),
            "executed_controller_action": dict(executed_action) if isinstance(executed_action, Mapping) else None,
        },
        **domain_health_diagnostic_work_units.context_payload(
            tick_request,
            work_unit_dispatch_key=work_unit_dispatch_key,
        ),
    }


def _record_blocked_outer_loop_wakeup(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    tick_request: Mapping[str, Any],
    wakeup_audit: Mapping[str, Any],
    quest_report: dict[str, Any] | None,
    managed_study_no_op_suppressions: list[dict[str, Any]],
    default_recorded_at: str,
) -> None:
    suppression = _serialize_no_op_suppression(
        study_root=study_root,
        status_payload=status_payload,
        wakeup_audit=wakeup_audit,
    )
    if suppression is not None:
        managed_study_no_op_suppressions.append(suppression)
        _attach_no_op_suppression_to_quest_report(
            quest_report=quest_report,
            suppression=suppression,
        )
    domain_health_diagnostic_work_units.append_ledger_event(
        study_root=study_root,
        status_payload=status_payload,
        tick_request=tick_request,
        event_type="controller_work_unit_blocked",
        wakeup_audit=wakeup_audit,
        default_recorded_at=default_recorded_at,
    )


def _attach_no_op_suppression_to_quest_report(
    *,
    quest_report: dict[str, Any] | None,
    suppression: Mapping[str, Any] | None,
    persist_diagnostic_reports: bool = True,
) -> None:
    if quest_report is None or suppression is None:
        return
    existing = [
        dict(item)
        for item in (quest_report.get("managed_study_no_op_suppressions") or [])
        if isinstance(item, Mapping)
    ]
    existing.append(dict(suppression))
    quest_report["managed_study_no_op_suppressions"] = existing
    if not persist_diagnostic_reports:
        return
    quest_root = _candidate_path(quest_report.get("quest_root"))
    if quest_root is not None:
        json_path, md_path, latest_json, latest_markdown = write_domain_health_diagnostic_report(
            quest_root,
            quest_report,
        )
        quest_report["report_json"] = str(json_path)
        quest_report["report_markdown"] = str(md_path)
        quest_report["latest_report_json"] = str(latest_json)
        quest_report["latest_report_markdown"] = str(latest_markdown)


def _materialize_placeholder_quest_diagnostic_report(
    status_payload: Mapping[str, Any],
    *,
    persist_diagnostic_reports: bool = True,
) -> dict[str, Any] | None:
    quest_root = _candidate_path(status_payload.get("quest_root"))
    if quest_root is None:
        return None
    report = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "quest_root": str(quest_root),
        "quest_status": _non_empty_text(status_payload.get("quest_status"))
        or quest_state.quest_status(quest_root),
        "controllers": {},
    }
    runtime_efficiency = _latest_run_telemetry_surface(
        quest_root=quest_root,
        status=quest_state.load_runtime_state(quest_root),
    )
    if runtime_efficiency is not None:
        report["runtime_efficiency"] = runtime_efficiency
    _attach_family_companion_to_quest_report(report, quest_root=quest_root)
    report["diagnostic_report_persistence"] = {
        "persisted": persist_diagnostic_reports,
        "policy": "apply_or_explicit_refresh",
    }
    if persist_diagnostic_reports:
        json_path, md_path, latest_json, latest_markdown = write_domain_health_diagnostic_report(
            quest_root,
            report,
        )
        report["report_json"] = str(json_path)
        report["report_markdown"] = str(md_path)
        report["latest_report_json"] = str(latest_json)
        report["latest_report_markdown"] = str(latest_markdown)
    return report


def _with_fresh_progress_currentness(
    *,
    profile: WorkspaceProfile | None,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(status_payload)
    if profile is None:
        return payload
    study_id = _non_empty_text(payload.get("study_id")) or Path(study_root).name
    if study_id is None:
        return payload
    try:
        from med_autoscience.controllers import study_progress

        progress = study_progress.read_study_progress(
            profile=profile,
            study_id=study_id,
            sync_runtime_summary=False,
            materialize_read_model_artifacts=False,
        )
    except Exception:
        return payload
    if not isinstance(progress, Mapping):
        return payload
    for key in PROGRESS_CURRENTNESS_KEYS:
        if key in progress:
            value = progress.get(key)
            if isinstance(value, Mapping):
                payload[key] = dict(value)
            elif isinstance(value, list):
                payload[key] = [
                    dict(item) if isinstance(item, Mapping) else item
                    for item in value
                ]
            else:
                payload[key] = value
    if (generated_at := _non_empty_text(progress.get("generated_at"))) is not None:
        payload["study_progress_generated_at"] = generated_at
    return payload
