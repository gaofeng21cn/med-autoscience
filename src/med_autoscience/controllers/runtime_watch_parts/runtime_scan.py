from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import runtime_watch_outer_loop_dispatch, runtime_watch_work_units
from med_autoscience.controllers.runtime_watch_outer_loop_policy import (
    outer_loop_request_requires_fresh_controller_execution,
)
from med_autoscience.controllers.runtime_watch_parts.control_plane_gate import (
    CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
    apply_control_plane_dispatch_block,
)
from med_autoscience.controllers.runtime_watch_parts.gate_specificity import _specificity_terminal_status_payload
from med_autoscience.controllers.runtime_watch_parts.managed_wakeup import (
    _build_outer_loop_wakeup_audit,
    _candidate_path,
    _controller_decision_latest_matches_outer_loop_request,
    _managed_study_status_payload,
    _non_empty_text,
    _outer_loop_dispatch_blocked_by_explicit_wakeup_contract,
    _quest_report_requests_managed_study_reroute,
    _serialize_managed_study_action,
    _serialize_managed_study_auto_recovery,
    _write_outer_loop_wakeup_audit,
)
from med_autoscience.controllers.runtime_watch_parts import managed_recovery
from med_autoscience.controllers.runtime_watch_parts import report_aggregation
from med_autoscience.controllers.runtime_watch_parts.reporting import (
    _attach_family_companion_to_quest_report,
    _write_latest_watch_alias,
    render_watch_markdown,
    write_watch_report,
)
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_control.ports import (
    RuntimeControlPorts,
    build_outer_loop_request,
    dispatch_outer_loop,
    ensure_runtime,
)


ControllerRunner = Callable[..., dict[str, Any]]
RunWatchForQuest = Callable[..., dict[str, Any]]

_MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "runtime_watch_auto_recovery"
_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE = "runtime_watch_controller_reroute"
_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE = "runtime_watch_outer_loop_wakeup"
_NO_OP_SUPPRESSION_SUMMARY = "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。"
_WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY = "同一 controller work unit 已达到有界 redrive 上限，需 MAS/MDS 平台修复后再继续。"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


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
        "platform_repair_required",
        "control_plane_dispatch_blocked",
        "explicit_wakeup_required",
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
        "work_unit_dispatch_key",
        "redrive_attempt_count",
        "max_redrive_attempts",
        "platform_repair_kind",
        "control_plane_snapshot",
        "control_plane_blocking_reasons",
        "explicit_wakeup_contract",
    ):
        value = wakeup_audit.get(key)
        if value is not None:
            payload[key] = dict(value) if isinstance(value, Mapping) else value
    if outcome == "needs_specificity":
        payload["operator_summary"] = "Publication gate 只给出标签级 blocker；需先明确具体 claim、证据、图表、指标、引用或包件目标。"
    elif outcome == "skipped_matching_work_unit":
        payload["operator_summary"] = _NO_OP_SUPPRESSION_SUMMARY
    elif outcome == "platform_repair_required":
        payload["operator_summary"] = _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY
    elif outcome == "control_plane_dispatch_blocked":
        payload["operator_summary"] = CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY
    elif outcome == "explicit_wakeup_required":
        payload["operator_summary"] = "该 study 已进入用户暂停或手动停驻合同；继续监测，但等待显式唤醒前不派发自动 owner work。"
    else:
        payload["operator_summary"] = "外环输入或 controller decision 未变化；保持 no-op，等待新证据、新用户反馈或 blocker fingerprint 改变。"
    return payload


def _attach_no_op_suppression_to_quest_report(
    *,
    quest_report: dict[str, Any] | None,
    suppression: Mapping[str, Any] | None,
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
    quest_root = _candidate_path(quest_report.get("quest_root"))
    if quest_root is not None:
        json_path, md_path, latest_json, latest_markdown = write_watch_report(quest_root, quest_report)
        quest_report["report_json"] = str(json_path)
        quest_report["report_markdown"] = str(md_path)
        quest_report["latest_report_json"] = str(latest_json)
        quest_report["latest_report_markdown"] = str(latest_markdown)


def _materialize_placeholder_quest_watch_report(status_payload: Mapping[str, Any]) -> dict[str, Any] | None:
    quest_root = _candidate_path(status_payload.get("quest_root"))
    if quest_root is None:
        return None
    report = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "quest_root": str(quest_root),
        "quest_status": _non_empty_text(status_payload.get("quest_status")) or quest_state.quest_status(quest_root),
        "controllers": {},
    }
    runtime_efficiency = _latest_run_telemetry_surface(
        quest_root=quest_root,
        status=quest_state.load_runtime_state(quest_root),
    )
    if runtime_efficiency is not None:
        report["runtime_efficiency"] = runtime_efficiency
    _attach_family_companion_to_quest_report(report, quest_root=quest_root)
    json_path, md_path, latest_json, latest_markdown = write_watch_report(quest_root, report)
    report["report_json"] = str(json_path)
    report["report_markdown"] = str(md_path)
    report["latest_report_json"] = str(latest_json)
    report["latest_report_markdown"] = str(latest_markdown)
    return report


def run_watch_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner],
    apply: bool,
    run_watch_for_quest_fn: RunWatchForQuest,
    runtime_control_ports: RuntimeControlPorts,
    profile: WorkspaceProfile | None = None,
    ensure_study_runtimes: bool = False,
) -> dict[str, Any]:
    managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
    managed_study_auto_recoveries: list[dict[str, Any]] = []
    managed_study_recovery_holds: list[dict[str, Any]] = []
    managed_study_outer_loop_dispatches: list[dict[str, Any]] = []
    managed_study_outer_loop_wakeup_audits: list[dict[str, Any]] = []
    managed_study_no_op_suppressions: list[dict[str, Any]] = []
    managed_study_alert_deliveries: list[dict[str, Any]] = []
    managed_study_autonomy_slo_statuses: list[dict[str, Any]] = []
    managed_study_autonomy_repair_actions: list[dict[str, Any]] = []
    managed_study_runtime_recovery_payloads: dict[str, dict[str, Any]] = {}
    managed_study_statuses = managed_recovery.managed_study_initial_statuses(
        runtime_control_ports=runtime_control_ports,
        profile=profile,
        apply=apply,
        ensure_study_runtimes=ensure_study_runtimes,
        auto_recoveries=managed_study_auto_recoveries,
        recovery_holds=managed_study_recovery_holds,
        runtime_recovery_payloads=managed_study_runtime_recovery_payloads,
    )
    scanned, reports, report_by_quest_root = report_aggregation.scan_active_quest_reports(
        runtime_root=runtime_root,
        controller_runners=controller_runners,
        apply=apply,
        run_watch_for_quest_fn=run_watch_for_quest_fn,
    )
    if apply and ensure_study_runtimes and profile is not None:
        rerouted_managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
        for study_root, status_payload in managed_study_statuses:
            resolved_status_payload = status_payload
            quest_root = status_payload.get("quest_root")
            quest_report = report_by_quest_root.get(str(Path(str(quest_root)).expanduser().resolve())) if quest_root else None
            if _quest_report_requests_managed_study_reroute(quest_report):
                rerouted_payload = ensure_runtime(
                    ports=runtime_control_ports,
                    profile=profile,
                    study_root=study_root,
                    source=_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
                )
                managed_study_auto_recoveries.append(
                    _serialize_managed_study_auto_recovery(
                        preflight_payload=status_payload,
                        applied_payload=rerouted_payload,
                        source=_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
                    )
                )
                resolved_status_payload = _managed_study_status_payload(rerouted_payload)
            rerouted_managed_study_statuses.append((study_root, resolved_status_payload))
        managed_study_statuses = rerouted_managed_study_statuses
    managed_study_supervision: list[dict[str, Any]] = []
    managed_study_action_overrides: dict[str, dict[str, Any]] = {}
    for study_root, status_payload in managed_study_statuses:
        study_root_key = str(Path(study_root).expanduser().resolve())
        current_study_outer_loop_dispatched = False
        if profile is not None:
            status_payload = runtime_control_ports.refresh_status_after_ensure(
                profile=profile,
                study_root=study_root,
                status_payload=status_payload,
            )
        quest_root = _candidate_path(status_payload.get("quest_root"))
        quest_report = report_by_quest_root.get(str(quest_root)) if quest_root is not None else None
        if apply and profile is not None:
            wakeup_audit = _build_outer_loop_wakeup_audit(
                study_root=study_root,
                status_payload=status_payload,
            )
            if (
                explicit_wakeup_block := _outer_loop_dispatch_blocked_by_explicit_wakeup_contract(status_payload)
            ) is not None:
                wakeup_audit = {
                    **wakeup_audit,
                    "outcome": "explicit_wakeup_required",
                    "reason": "user pause or manual hold requires explicit wakeup before autonomous dispatch",
                    "no_op_acknowledged": True,
                    "dedupe_scope": "explicit_wakeup_contract",
                    **explicit_wakeup_block,
                }
                _write_outer_loop_wakeup_audit(study_root=study_root, audit=wakeup_audit)
                managed_study_outer_loop_wakeup_audits.append(wakeup_audit)
                suppression = _serialize_no_op_suppression(
                    study_root=study_root,
                    status_payload=status_payload,
                    wakeup_audit=wakeup_audit,
                )
                if suppression is not None:
                    managed_study_no_op_suppressions.append(suppression)
                    _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
            elif runtime_watch_work_units.outer_loop_wakeup_inputs_unchanged(wakeup_audit):
                wakeup_audit = {
                    **wakeup_audit,
                    "outcome": "skipped_unchanged_inputs",
                    "reason": "outer-loop wakeup inputs match a prior terminal no-op state",
                    "no_op_acknowledged": True,
                }
                _write_outer_loop_wakeup_audit(study_root=study_root, audit=wakeup_audit)
                managed_study_outer_loop_wakeup_audits.append(wakeup_audit)
                suppression = _serialize_no_op_suppression(
                    study_root=study_root,
                    status_payload=status_payload,
                    wakeup_audit=wakeup_audit,
                )
                if suppression is not None:
                    managed_study_no_op_suppressions.append(suppression)
                    _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
            else:
                tick_request = build_outer_loop_request(
                    ports=runtime_control_ports,
                    study_root=study_root,
                    status_payload=status_payload,
                )
                if tick_request is None:
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "no_request",
                        "reason": "outer-loop wakeup did not produce an autonomous request",
                    }
                elif runtime_watch_work_units.needs_specificity_request(tick_request):
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "needs_specificity",
                        "reason": "publication gate blocker is not actionable without concrete repair targets",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "publication_gate_specificity",
                        **runtime_watch_work_units.context_payload(
                            tick_request,
                            work_unit_dispatch_key=runtime_watch_work_units.dispatch_key(tick_request),
                        ),
                    }
                    specificity_decision_result = runtime_control_ports.materialize_non_dispatching_decision(
                        profile=profile,
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        wakeup_audit=wakeup_audit,
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "controller_decision": {
                            "dispatch_status": specificity_decision_result.get("dispatch_status"),
                            "study_decision_ref": specificity_decision_result.get("study_decision_ref"),
                        },
                    }
                    status_payload = _specificity_terminal_status_payload(
                        status_payload=status_payload,
                        tick_request=tick_request,
                    )
                    managed_study_action_overrides[study_root_key] = status_payload
                    suppression = _serialize_no_op_suppression(
                        study_root=study_root,
                        status_payload=status_payload,
                        wakeup_audit=wakeup_audit,
                    )
                    if suppression is not None:
                        managed_study_no_op_suppressions.append(suppression)
                        _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
                    runtime_watch_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="needs_specificity",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif (
                    work_unit_duplicate := runtime_watch_work_units.dispatch_already_executed(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = runtime_watch_work_units.context_payload(
                        tick_request,
                        work_unit_dispatch_key=work_unit_duplicate[1],
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "skipped_matching_work_unit",
                        "reason": "outer-loop work unit already dispatched for the same blocker fingerprint",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_decision_blocker_authority",
                        "operator_summary": _NO_OP_SUPPRESSION_SUMMARY,
                        **work_unit_context,
                    }
                    suppression = _serialize_no_op_suppression(
                        study_root=study_root,
                        status_payload=status_payload,
                        wakeup_audit=wakeup_audit,
                    )
                    if suppression is not None:
                        managed_study_no_op_suppressions.append(suppression)
                        _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
                    runtime_watch_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="skipped_duplicate",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif runtime_watch_work_units.close_stale_platform_repair_if_meaningful_delta(
                    study_root=study_root,
                    status_payload=status_payload,
                    tick_request=tick_request,
                    wakeup_audit=wakeup_audit,
                    default_recorded_at=utc_now(),
                ) is not None:
                    work_unit_dispatch_key = runtime_watch_work_units.dispatch_key(tick_request)
                    blocked_wakeup_audit = apply_control_plane_dispatch_block(
                        profile=profile,
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        wakeup_audit=wakeup_audit,
                        quest_report=quest_report,
                        managed_study_no_op_suppressions=managed_study_no_op_suppressions,
                        serialize_no_op_suppression=_serialize_no_op_suppression,
                        attach_no_op_suppression_to_quest_report=_attach_no_op_suppression_to_quest_report,
                        default_recorded_at=utc_now(),
                        controller_decision_matches=_controller_decision_latest_matches_outer_loop_request,
                        materialize_non_dispatching_decision=runtime_control_ports.materialize_non_dispatching_decision,
                    )
                    if blocked_wakeup_audit is not None:
                        wakeup_audit = blocked_wakeup_audit
                    else:
                        outer_loop_result = dispatch_outer_loop(
                            ports=runtime_control_ports,
                            profile=profile,
                            source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
                            tick_request=runtime_watch_work_units.strip_context(tick_request),
                        )
                        if _non_empty_text(outer_loop_result.get("dispatch_status")) != "executed":
                            raise ValueError("runtime watch outer-loop wakeup requires executed autonomous dispatch")
                        dispatch_payload = runtime_watch_outer_loop_dispatch.serialize_outer_loop_dispatch(
                            tick_request=tick_request,
                            outer_loop_result=outer_loop_result,
                        )
                        managed_study_outer_loop_dispatches.append(dispatch_payload)
                        current_study_outer_loop_dispatched = True
                        if quest_report is None:
                            quest_report = _materialize_placeholder_quest_watch_report(status_payload)
                            if isinstance(quest_report, dict):
                                reports.append(quest_report)
                                quest_root = _candidate_path(status_payload.get("quest_root"))
                                if quest_root is not None:
                                    report_by_quest_root[str(quest_root)] = quest_report
                        if isinstance(quest_report, dict):
                            runtime_watch_outer_loop_dispatch.attach_to_quest_report(
                                quest_report=quest_report,
                                dispatch_payload=dispatch_payload,
                                write_latest_watch_alias=_write_latest_watch_alias,
                                render_watch_markdown=render_watch_markdown,
                            )
                        wakeup_audit = {
                            **wakeup_audit,
                            "outcome": "dispatched",
                            "reason": "outer-loop wakeup dispatched after meaningful artifact delta cleared platform repair lock",
                            "dispatch": dispatch_payload,
                            **runtime_watch_work_units.context_payload(
                                tick_request,
                                work_unit_dispatch_key=work_unit_dispatch_key,
                            ),
                        }
                        runtime_watch_work_units.append_ledger_event(
                            study_root=study_root,
                            status_payload=status_payload,
                            tick_request=tick_request,
                            event_type="dispatched",
                            wakeup_audit=wakeup_audit,
                            default_recorded_at=utc_now(),
                        )
                        status_payload = _managed_study_status_payload(
                            runtime_control_ports.get_status(profile=profile, study_root=study_root)
                        )
                elif (
                    platform_repair := runtime_watch_work_units.active_platform_repair_required(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = runtime_watch_work_units.context_payload(
                        tick_request,
                        work_unit_dispatch_key=platform_repair[1],
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "platform_repair_required",
                        "reason": "outer-loop work unit is blocked on prior platform repair requirement",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_work_unit_platform_repair",
                        "redrive_attempt_count": platform_repair[2],
                        "max_redrive_attempts": runtime_watch_work_units.MAX_OPEN_REDRIVE_ATTEMPTS,
                        "platform_repair_kind": "work_unit_redrive_exhausted_without_attempt_result",
                        "operator_summary": _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY,
                        **work_unit_context,
                    }
                    suppression = _serialize_no_op_suppression(
                        study_root=study_root,
                        status_payload=status_payload,
                        wakeup_audit=wakeup_audit,
                    )
                    if suppression is not None:
                        managed_study_no_op_suppressions.append(suppression)
                        _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
                    runtime_watch_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="platform_repair_required",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif (
                    redrive_exhaustion := runtime_watch_work_units.redrive_budget_exhausted(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = runtime_watch_work_units.context_payload(
                        tick_request,
                        work_unit_dispatch_key=redrive_exhaustion[1],
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "platform_repair_required",
                        "reason": "outer-loop work unit redrive budget exhausted without result evidence",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_work_unit_redrive_budget",
                        "redrive_attempt_count": redrive_exhaustion[2],
                        "max_redrive_attempts": runtime_watch_work_units.MAX_OPEN_REDRIVE_ATTEMPTS,
                        "platform_repair_kind": "work_unit_redrive_exhausted_without_attempt_result",
                        "operator_summary": _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY,
                        **work_unit_context,
                    }
                    suppression = _serialize_no_op_suppression(
                        study_root=study_root,
                        status_payload=status_payload,
                        wakeup_audit=wakeup_audit,
                    )
                    if suppression is not None:
                        managed_study_no_op_suppressions.append(suppression)
                        _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
                    runtime_watch_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="platform_repair_required",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif _controller_decision_latest_matches_outer_loop_request(
                    study_root=study_root,
                    status_payload=status_payload,
                    tick_request=tick_request,
                ) and not outer_loop_request_requires_fresh_controller_execution(tick_request):
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "skipped_matching_decision",
                        "reason": "controller_decisions/latest.json already matches the wakeup request",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_decision",
                    }
                    suppression = _serialize_no_op_suppression(
                        study_root=study_root,
                        status_payload=status_payload,
                        wakeup_audit=wakeup_audit,
                    )
                    if suppression is not None:
                        managed_study_no_op_suppressions.append(suppression)
                        _attach_no_op_suppression_to_quest_report(quest_report=quest_report, suppression=suppression)
                else:
                    work_unit_dispatch_key = runtime_watch_work_units.dispatch_key(tick_request)
                    blocked_wakeup_audit = apply_control_plane_dispatch_block(
                        profile=profile,
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        wakeup_audit=wakeup_audit,
                        quest_report=quest_report,
                        managed_study_no_op_suppressions=managed_study_no_op_suppressions,
                        serialize_no_op_suppression=_serialize_no_op_suppression,
                        attach_no_op_suppression_to_quest_report=_attach_no_op_suppression_to_quest_report,
                        default_recorded_at=utc_now(),
                        controller_decision_matches=_controller_decision_latest_matches_outer_loop_request,
                        materialize_non_dispatching_decision=runtime_control_ports.materialize_non_dispatching_decision,
                    )
                    if blocked_wakeup_audit is not None:
                        wakeup_audit = blocked_wakeup_audit
                    else:
                        outer_loop_result = dispatch_outer_loop(
                            ports=runtime_control_ports,
                            profile=profile,
                            source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
                            tick_request=runtime_watch_work_units.strip_context(tick_request),
                        )
                        if _non_empty_text(outer_loop_result.get("dispatch_status")) != "executed":
                            raise ValueError("runtime watch outer-loop wakeup requires executed autonomous dispatch")
                        dispatch_payload = runtime_watch_outer_loop_dispatch.serialize_outer_loop_dispatch(
                            tick_request=tick_request,
                            outer_loop_result=outer_loop_result,
                        )
                        managed_study_outer_loop_dispatches.append(dispatch_payload)
                        current_study_outer_loop_dispatched = True
                        if quest_report is None:
                            quest_report = _materialize_placeholder_quest_watch_report(status_payload)
                            if isinstance(quest_report, dict):
                                reports.append(quest_report)
                                quest_root = _candidate_path(status_payload.get("quest_root"))
                                if quest_root is not None:
                                    report_by_quest_root[str(quest_root)] = quest_report
                        if isinstance(quest_report, dict):
                            runtime_watch_outer_loop_dispatch.attach_to_quest_report(
                                quest_report=quest_report,
                                dispatch_payload=dispatch_payload,
                                write_latest_watch_alias=_write_latest_watch_alias,
                                render_watch_markdown=render_watch_markdown,
                            )
                        wakeup_audit = {
                            **wakeup_audit,
                            "outcome": "dispatched",
                            "reason": "outer-loop wakeup dispatched an autonomous controller decision",
                            "dispatch": dispatch_payload,
                            **runtime_watch_work_units.context_payload(
                                tick_request,
                                work_unit_dispatch_key=work_unit_dispatch_key,
                            ),
                        }
                        runtime_watch_work_units.append_ledger_event(
                            study_root=study_root,
                            status_payload=status_payload,
                            tick_request=tick_request,
                            event_type="dispatched",
                            wakeup_audit=wakeup_audit,
                            default_recorded_at=utc_now(),
                        )
                        status_payload = _managed_study_status_payload(
                            runtime_control_ports.get_status(profile=profile, study_root=study_root)
                        )
                _write_outer_loop_wakeup_audit(study_root=study_root, audit=wakeup_audit)
                managed_study_outer_loop_wakeup_audits.append(wakeup_audit)
        quest_root = _candidate_path(status_payload.get("quest_root"))
        quest_report = report_by_quest_root.get(str(quest_root)) if quest_root is not None else None
        supervision_report = runtime_control_ports.materialize_supervision(
            study_root=study_root,
            status_payload=status_payload,
            recorded_at=utc_now(),
            apply=apply,
            runtime_watch_report_path=(
                Path(str(quest_report.get("latest_report_json") or quest_report.get("report_json")))
                if isinstance(quest_report, dict)
                and str(quest_report.get("latest_report_json") or quest_report.get("report_json") or "").strip()
                else None
            ),
        )
        if supervision_report is not None:
            managed_study_supervision.append(supervision_report)
            alert_delivery = runtime_control_ports.deliver_alert(
                profile=profile,
                study_root=study_root,
                status_payload=status_payload,
                supervision_report=supervision_report,
                apply=apply,
            )
            if alert_delivery is not None:
                managed_study_alert_deliveries.append(alert_delivery)
        if apply:
            study_id = str(status_payload.get("study_id") or "").strip()
            quest_id = str(status_payload.get("quest_id") or "").strip()
            if study_id and quest_id:
                runtime_control_ports.reconcile_health(
                    study_root=study_root,
                    study_id=study_id,
                    quest_id=quest_id,
                    status_payload=status_payload,
                    recorded_at=utc_now(),
                )
        if profile is not None:
            managed_study_autonomy_slo_statuses.append(
                runtime_control_ports.materialize_autonomy_slo(
                    profile=profile,
                    study_root=study_root,
                )
            )
            ready_ai_doctor_repair = runtime_control_ports.read_ready_ai_repair(study_root=study_root)
            if (
                apply
                and ready_ai_doctor_repair is not None
                and not current_study_outer_loop_dispatched
                and study_root_key not in managed_study_action_overrides
            ):
                autonomy_repair = runtime_control_ports.apply_ai_repair(
                    profile=profile,
                    study_root=study_root,
                    status_payload=status_payload,
                    runtime_recovery_payload=managed_study_runtime_recovery_payloads.get(study_root_key),
                    repair_payload=ready_ai_doctor_repair,
                )
                if autonomy_repair is not None:
                    managed_study_autonomy_repair_actions.append(autonomy_repair)
            lifecycle = runtime_control_ports.read_ai_repair_lifecycle(study_root=study_root)
            if isinstance(lifecycle, Mapping):
                status_payload["ai_repair_lifecycle"] = dict(lifecycle)
    managed_study_actions = [
        _serialize_managed_study_action(
            managed_study_action_overrides.get(str(Path(managed_study_root).expanduser().resolve()), status_payload)
        )
        for managed_study_root, status_payload in managed_study_statuses
    ]
    return report_aggregation.build_runtime_report(
        runtime_root=runtime_root,
        scanned=scanned,
        reports=reports,
        managed_study_actions=managed_study_actions,
        managed_study_auto_recoveries=managed_study_auto_recoveries,
        managed_study_recovery_holds=managed_study_recovery_holds,
        managed_study_outer_loop_dispatches=managed_study_outer_loop_dispatches,
        managed_study_outer_loop_wakeup_audits=managed_study_outer_loop_wakeup_audits,
        managed_study_no_op_suppressions=managed_study_no_op_suppressions,
        managed_study_supervision=managed_study_supervision,
        managed_study_alert_deliveries=managed_study_alert_deliveries,
        managed_study_autonomy_slo_statuses=managed_study_autonomy_slo_statuses,
        managed_study_autonomy_repair_actions=managed_study_autonomy_repair_actions,
    )


__all__ = [
    "_MANAGED_STUDY_AUTO_RECOVERY_SOURCE",
    "_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE",
    "_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE",
    "_NO_OP_SUPPRESSION_SUMMARY",
    "_WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY",
    "_attach_no_op_suppression_to_quest_report",
    "_managed_study_recovery_failure_payload",
    "_materialize_placeholder_quest_watch_report",
    "_serialize_no_op_suppression",
    "run_watch_for_runtime",
]
