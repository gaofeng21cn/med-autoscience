from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import domain_health_diagnostic_outer_loop_dispatch, domain_health_diagnostic_work_units
from med_autoscience.controllers.domain_health_diagnostic_outer_loop_policy import (
    outer_loop_request_requires_fresh_controller_execution,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.control_plane_gate import (
    CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
    apply_control_plane_dispatch_block,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.gate_specificity import _specificity_terminal_status_payload
from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import (
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
from med_autoscience.controllers.domain_health_diagnostic_parts import managed_recovery
from med_autoscience.controllers.domain_health_diagnostic_parts import provider_admission
from med_autoscience.controllers.domain_health_diagnostic_parts import report_aggregation
from med_autoscience.controllers.owner_route_reconcile_parts import supervision_surfaces
from med_autoscience.controllers.domain_health_diagnostic_parts.reporting import (
    _attach_family_companion_to_quest_report,
    _write_latest_domain_health_diagnostic_alias,
    render_domain_health_diagnostic_markdown,
    write_domain_health_diagnostic_report,
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
    request_opl_stage_attempt,
)


ControllerRunner = Callable[..., dict[str, Any]]
RunDomainHealthDiagnosticForQuest = Callable[..., dict[str, Any]]

_MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "domain_health_diagnostic_opl_stage_attempt_request"
_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE = "domain_health_diagnostic_controller_reroute"
_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE = "domain_health_diagnostic_outer_loop_wakeup"
_NO_OP_SUPPRESSION_SUMMARY = "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。"
_WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY = "同一 controller work unit 已达到有界 redrive 上限，需 OPL runtime handoff后再继续。"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _outer_loop_request_is_stop_runtime(tick_request: Mapping[str, Any]) -> bool:
    controller_actions = tick_request.get("controller_actions")
    first_action = (
        controller_actions[0]
        if isinstance(controller_actions, list | tuple) and controller_actions and isinstance(controller_actions[0], Mapping)
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
        json_path, md_path, latest_json, latest_markdown = write_domain_health_diagnostic_report(quest_root, quest_report)
        quest_report["report_json"] = str(json_path)
        quest_report["report_markdown"] = str(md_path)
        quest_report["latest_report_json"] = str(latest_json)
        quest_report["latest_report_markdown"] = str(latest_markdown)


def _materialize_placeholder_quest_diagnostic_report(status_payload: Mapping[str, Any]) -> dict[str, Any] | None:
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
    json_path, md_path, latest_json, latest_markdown = write_domain_health_diagnostic_report(quest_root, report)
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
    for key in (
        "current_work_unit",
        "current_execution_envelope",
        "current_executable_owner_action",
        "current_owner_ticket",
    ):
        if key in progress:
            value = progress.get(key)
            if isinstance(value, Mapping):
                payload[key] = dict(value)
            else:
                payload[key] = value
    if (generated_at := _non_empty_text(progress.get("generated_at"))) is not None:
        payload["study_progress_generated_at"] = generated_at
    return payload


def run_domain_health_diagnostic_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner],
    apply: bool,
    run_domain_health_diagnostic_for_quest_fn: RunDomainHealthDiagnosticForQuest,
    runtime_control_ports: RuntimeControlPorts,
    profile: WorkspaceProfile | None = None,
    study_ids: tuple[str, ...] = (),
    request_opl_stage_attempts: bool = False,
) -> dict[str, Any]:
    managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
    managed_study_auto_recoveries: list[dict[str, Any]] = []
    managed_study_recovery_holds: list[dict[str, Any]] = []
    managed_study_outer_loop_dispatches: list[dict[str, Any]] = []
    managed_study_outer_loop_wakeup_audits: list[dict[str, Any]] = []
    managed_study_no_op_suppressions: list[dict[str, Any]] = []
    managed_study_opl_runtime_owner_handoffs: list[dict[str, Any]] = []
    managed_study_opl_provider_admission_candidates: list[dict[str, Any]] = []
    managed_study_autonomy_slo_statuses: list[dict[str, Any]] = []
    managed_study_autonomy_repair_actions: list[dict[str, Any]] = []
    managed_study_progress_currentness: dict[str, dict[str, Any]] = {}
    managed_study_runtime_recovery_payloads: dict[str, dict[str, Any]] = {}
    managed_study_statuses = managed_recovery.managed_study_initial_statuses(
        runtime_control_ports=runtime_control_ports,
        profile=profile,
        apply=apply,
        request_opl_stage_attempts=request_opl_stage_attempts,
        study_ids=study_ids,
        auto_recoveries=managed_study_auto_recoveries,
        recovery_holds=managed_study_recovery_holds,
        runtime_recovery_payloads=managed_study_runtime_recovery_payloads,
    )
    scanned, reports, report_by_quest_root = report_aggregation.scan_active_quest_reports(
        runtime_root=runtime_root,
        controller_runners=controller_runners,
        apply=apply,
        run_domain_health_diagnostic_for_quest_fn=run_domain_health_diagnostic_for_quest_fn,
        study_ids=study_ids,
    )
    if apply and request_opl_stage_attempts and profile is not None:
        rerouted_managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
        for study_root, status_payload in managed_study_statuses:
            resolved_status_payload = status_payload
            if status_payload.get("domain_health_diagnostic_error_isolated") is True:
                rerouted_managed_study_statuses.append((study_root, resolved_status_payload))
                continue
            quest_root = status_payload.get("quest_root")
            quest_report = report_by_quest_root.get(str(Path(str(quest_root)).expanduser().resolve())) if quest_root else None
            if _quest_report_requests_managed_study_reroute(quest_report):
                rerouted_payload = request_opl_stage_attempt(
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
    managed_study_action_overrides: dict[str, dict[str, Any]] = {}
    for study_root, status_payload in managed_study_statuses:
        study_root_key = str(Path(study_root).expanduser().resolve())
        current_study_outer_loop_dispatched = False
        if profile is not None:
            if status_payload.get("domain_health_diagnostic_error_isolated") is not True:
                status_payload = runtime_control_ports.refresh_status_after_stage_request(
                    profile=profile,
                    study_root=study_root,
                    status_payload=status_payload,
                )
                status_payload = _with_fresh_progress_currentness(
                    profile=profile,
                    study_root=study_root,
                    status_payload=status_payload,
                )
                progress_currentness = {
                    key: status_payload[key]
                    for key in (
                        "current_work_unit",
                        "current_execution_envelope",
                        "current_executable_owner_action",
                        "current_owner_ticket",
                        "study_progress_generated_at",
                    )
                    if key in status_payload
                }
                study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
                if progress_currentness and study_id:
                    managed_study_progress_currentness[study_id] = progress_currentness
        if status_payload.get("domain_health_diagnostic_error_isolated") is True:
            continue
        quest_root = _candidate_path(status_payload.get("quest_root"))
        quest_report = report_by_quest_root.get(str(quest_root)) if quest_root is not None else None
        study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
        if study_id in managed_study_progress_currentness:
            status_payload = {
                **status_payload,
                **managed_study_progress_currentness[study_id],
            }
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
            elif domain_health_diagnostic_work_units.outer_loop_wakeup_inputs_unchanged(wakeup_audit):
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
                elif domain_health_diagnostic_work_units.needs_specificity_request(tick_request):
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "needs_specificity",
                        "reason": "publication gate blocker is not actionable without concrete repair targets",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "publication_gate_specificity",
                        **domain_health_diagnostic_work_units.context_payload(
                            tick_request,
                            work_unit_dispatch_key=domain_health_diagnostic_work_units.dispatch_key(tick_request),
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
                    for ref_key in ("controller_authorization_ref", "control_intent_lifecycle_ref"):
                        ref_value = specificity_decision_result.get(ref_key)
                        if ref_value is not None:
                            wakeup_audit[ref_key] = dict(ref_value) if isinstance(ref_value, Mapping) else ref_value
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
                    domain_health_diagnostic_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="needs_specificity",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif (
                    work_unit_duplicate := domain_health_diagnostic_work_units.dispatch_already_executed(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = domain_health_diagnostic_work_units.context_payload(
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
                    domain_health_diagnostic_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="skipped_duplicate",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif (
                    opl_handoff_closeout := domain_health_diagnostic_work_units.close_stale_opl_runtime_handoff_if_result_evidence(
                    study_root=study_root,
                    status_payload=status_payload,
                    tick_request=tick_request,
                    wakeup_audit=wakeup_audit,
                    default_recorded_at=utc_now(),
                    )
                ) is not None:
                    work_unit_dispatch_key = domain_health_diagnostic_work_units.dispatch_key(tick_request)
                    closure_payload = (
                        dict(opl_handoff_closeout.get("payload"))
                        if isinstance(opl_handoff_closeout.get("payload"), Mapping)
                        else {}
                    )
                    closure_reason = _non_empty_text(closure_payload.get("closure_reason"))
                    if closure_reason == "default_executor_closeout_after_opl_runtime_handoff":
                        dispatch_reason = (
                            "outer-loop wakeup dispatched after default executor closeout refs cleared platform repair lock"
                        )
                        blocked_reason = (
                            "outer-loop wakeup controller work unit failed closed after default executor closeout refs cleared platform repair lock"
                        )
                    else:
                        dispatch_reason = (
                            "outer-loop wakeup dispatched after meaningful artifact delta cleared platform repair lock"
                        )
                        blocked_reason = (
                            "outer-loop wakeup controller work unit failed closed after meaningful artifact delta cleared platform repair lock"
                        )
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
                            tick_request=domain_health_diagnostic_work_units.strip_context(tick_request),
                        )
                        blocked_wakeup_audit = _blocked_outer_loop_wakeup_audit(
                            wakeup_audit=wakeup_audit,
                            tick_request=tick_request,
                            outer_loop_result=outer_loop_result,
                            reason=blocked_reason,
                            work_unit_dispatch_key=work_unit_dispatch_key,
                        )
                        if blocked_wakeup_audit is not None:
                            wakeup_audit = blocked_wakeup_audit
                            _record_blocked_outer_loop_wakeup(
                                study_root=study_root,
                                status_payload=status_payload,
                                tick_request=tick_request,
                                wakeup_audit=wakeup_audit,
                                quest_report=quest_report,
                                managed_study_no_op_suppressions=managed_study_no_op_suppressions,
                                default_recorded_at=utc_now(),
                            )
                            status_payload = _managed_study_status_payload(
                                runtime_control_ports.get_status(profile=profile, study_root=study_root)
                            )
                        elif _non_empty_text(outer_loop_result.get("dispatch_status")) != "executed":
                            raise ValueError("domain health diagnostic outer-loop wakeup requires executed autonomous dispatch")
                        else:
                            dispatch_payload = domain_health_diagnostic_outer_loop_dispatch.serialize_outer_loop_dispatch(
                                tick_request=tick_request,
                                outer_loop_result=outer_loop_result,
                            )
                            managed_study_outer_loop_dispatches.append(dispatch_payload)
                            current_study_outer_loop_dispatched = True
                            if quest_report is None:
                                quest_report = _materialize_placeholder_quest_diagnostic_report(status_payload)
                                if isinstance(quest_report, dict):
                                    reports.append(quest_report)
                                    quest_root = _candidate_path(status_payload.get("quest_root"))
                                    if quest_root is not None:
                                        report_by_quest_root[str(quest_root)] = quest_report
                            if isinstance(quest_report, dict):
                                domain_health_diagnostic_outer_loop_dispatch.attach_to_quest_report(
                                    quest_report=quest_report,
                                    dispatch_payload=dispatch_payload,
                                    write_latest_watch_alias=_write_latest_domain_health_diagnostic_alias,
                                    render_domain_health_diagnostic_markdown=render_domain_health_diagnostic_markdown,
                                )
                            wakeup_audit = {
                                **wakeup_audit,
                                "outcome": "dispatched",
                                "reason": dispatch_reason,
                                "dispatch": dispatch_payload,
                                **domain_health_diagnostic_work_units.context_payload(
                                    tick_request,
                                    work_unit_dispatch_key=work_unit_dispatch_key,
                                ),
                            }
                            domain_health_diagnostic_work_units.append_ledger_event(
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
                    opl_runtime_handoff := domain_health_diagnostic_work_units.active_opl_runtime_handoff_required(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = domain_health_diagnostic_work_units.context_payload(
                        tick_request,
                        work_unit_dispatch_key=opl_runtime_handoff[1],
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "opl_runtime_handoff_required",
                        "reason": "outer-loop work unit is blocked on prior platform repair requirement",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_work_unit_opl_runtime_handoff",
                        "redrive_attempt_count": opl_runtime_handoff[2],
                        "max_redrive_attempts": domain_health_diagnostic_work_units.MAX_OPEN_REDRIVE_ATTEMPTS,
                        "opl_runtime_handoff_kind": "work_unit_redrive_exhausted_without_attempt_result",
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
                    domain_health_diagnostic_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="opl_runtime_handoff_required",
                        wakeup_audit=wakeup_audit,
                        default_recorded_at=utc_now(),
                    )
                elif (
                    redrive_exhaustion := domain_health_diagnostic_work_units.redrive_budget_exhausted(
                        study_root=study_root,
                        tick_request=tick_request,
                    )
                )[0]:
                    work_unit_context = domain_health_diagnostic_work_units.context_payload(
                        tick_request,
                        work_unit_dispatch_key=redrive_exhaustion[1],
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "opl_runtime_handoff_required",
                        "reason": "outer-loop work unit redrive budget exhausted without result evidence",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "controller_work_unit_redrive_budget",
                        "redrive_attempt_count": redrive_exhaustion[2],
                        "max_redrive_attempts": domain_health_diagnostic_work_units.MAX_OPEN_REDRIVE_ATTEMPTS,
                        "opl_runtime_handoff_kind": "work_unit_redrive_exhausted_without_attempt_result",
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
                    domain_health_diagnostic_work_units.append_ledger_event(
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        event_type="opl_runtime_handoff_required",
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
                elif _outer_loop_request_is_stop_runtime(tick_request):
                    decision_wakeup_audit = {
                        key: value
                        for key, value in wakeup_audit.items()
                        if key != "recorded_at"
                    }
                    decision_result = runtime_control_ports.materialize_non_dispatching_decision(
                        profile=profile,
                        study_root=study_root,
                        status_payload=status_payload,
                        tick_request=tick_request,
                        wakeup_audit=decision_wakeup_audit,
                    )
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "non_dispatching_runtime_stop",
                        "reason": "outer-loop wakeup materialized a stop-runtime controller decision without dispatch",
                        "no_op_acknowledged": True,
                        "dedupe_scope": "runtime_stop_controller_decision",
                        "controller_decision": {
                            "dispatch_status": decision_result.get("dispatch_status"),
                            "study_decision_ref": decision_result.get("study_decision_ref"),
                        },
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
                    work_unit_dispatch_key = domain_health_diagnostic_work_units.dispatch_key(tick_request)
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
                            tick_request=domain_health_diagnostic_work_units.strip_context(tick_request),
                        )
                        blocked_wakeup_audit = _blocked_outer_loop_wakeup_audit(
                            wakeup_audit=wakeup_audit,
                            tick_request=tick_request,
                            outer_loop_result=outer_loop_result,
                            reason="outer-loop wakeup controller work unit failed closed",
                            work_unit_dispatch_key=work_unit_dispatch_key,
                        )
                        if blocked_wakeup_audit is not None:
                            wakeup_audit = blocked_wakeup_audit
                            _record_blocked_outer_loop_wakeup(
                                study_root=study_root,
                                status_payload=status_payload,
                                tick_request=tick_request,
                                wakeup_audit=wakeup_audit,
                                quest_report=quest_report,
                                managed_study_no_op_suppressions=managed_study_no_op_suppressions,
                                default_recorded_at=utc_now(),
                            )
                            status_payload = _managed_study_status_payload(
                                runtime_control_ports.get_status(profile=profile, study_root=study_root)
                            )
                        elif _non_empty_text(outer_loop_result.get("dispatch_status")) != "executed":
                            raise ValueError("domain health diagnostic outer-loop wakeup requires executed autonomous dispatch")
                        else:
                            dispatch_payload = domain_health_diagnostic_outer_loop_dispatch.serialize_outer_loop_dispatch(
                                tick_request=tick_request,
                                outer_loop_result=outer_loop_result,
                            )
                            managed_study_outer_loop_dispatches.append(dispatch_payload)
                            current_study_outer_loop_dispatched = True
                            if quest_report is None:
                                quest_report = _materialize_placeholder_quest_diagnostic_report(status_payload)
                                if isinstance(quest_report, dict):
                                    reports.append(quest_report)
                                    quest_root = _candidate_path(status_payload.get("quest_root"))
                                    if quest_root is not None:
                                        report_by_quest_root[str(quest_root)] = quest_report
                            if isinstance(quest_report, dict):
                                domain_health_diagnostic_outer_loop_dispatch.attach_to_quest_report(
                                    quest_report=quest_report,
                                    dispatch_payload=dispatch_payload,
                                    write_latest_watch_alias=_write_latest_domain_health_diagnostic_alias,
                                    render_domain_health_diagnostic_markdown=render_domain_health_diagnostic_markdown,
                                )
                            wakeup_audit = {
                                **wakeup_audit,
                                "outcome": "dispatched",
                                "reason": "outer-loop wakeup dispatched an autonomous controller decision",
                                "dispatch": dispatch_payload,
                                **domain_health_diagnostic_work_units.context_payload(
                                    tick_request,
                                    work_unit_dispatch_key=work_unit_dispatch_key,
                                ),
                            }
                            domain_health_diagnostic_work_units.append_ledger_event(
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
        opl_runtime_owner_handoff = None
        if status_payload.get("domain_health_diagnostic_error_isolated") is not True:
            opl_runtime_owner_handoff = runtime_control_ports.materialize_opl_runtime_owner_handoff(
                study_root=study_root,
                status_payload=status_payload,
                recorded_at=utc_now(),
                apply=apply,
                domain_health_diagnostic_report_path=(
                    Path(str(quest_report.get("latest_report_json") or quest_report.get("report_json")))
                    if isinstance(quest_report, dict)
                    and str(quest_report.get("latest_report_json") or quest_report.get("report_json") or "").strip()
                    else None
                ),
            )
        if opl_runtime_owner_handoff is not None:
            managed_study_opl_runtime_owner_handoffs.append(opl_runtime_owner_handoff)
        study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
        candidate_status_payload = {
            **status_payload,
            **managed_study_progress_currentness.get(study_id, {}),
        }
        managed_study_opl_provider_admission_candidates.extend(
            _provider_admission_candidates_for_status(
                profile=profile,
                study_root=study_root,
                status_payload=candidate_status_payload,
            )
        )
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
        if profile is not None and status_payload.get("domain_health_diagnostic_error_isolated") is not True:
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
            if apply:
                runtime_control_ports.reconcile_ai_repair_lifecycle(
                    study_root=study_root,
                    status_payload=status_payload,
                )
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
        managed_study_opl_runtime_owner_handoffs=managed_study_opl_runtime_owner_handoffs,
        managed_study_opl_provider_admission_candidates=managed_study_opl_provider_admission_candidates,
        managed_study_progress_currentness=managed_study_progress_currentness,
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
    "_materialize_placeholder_quest_diagnostic_report",
    "_serialize_no_op_suppression",
    "run_domain_health_diagnostic_for_runtime",
]


def _provider_admission_candidates_for_status(
    *,
    profile: WorkspaceProfile | None,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> list[dict[str, Any]]:
    status_payload = _with_fresh_progress_currentness(
        profile=profile,
        study_root=study_root,
        status_payload=status_payload,
    )
    candidates = provider_admission.persisted_provider_admission_candidates(
        study_root=study_root,
        status_payload=status_payload,
    )
    if candidates or profile is None:
        return candidates
    current_control_path = supervision_surfaces.latest_path(profile)
    current_control_payload = supervision_surfaces.read_json_object(current_control_path)
    return provider_admission.current_control_provider_admission_candidates(
        current_control_payload,
        study_root=study_root,
        status_payload=status_payload,
        current_control_ref=str(current_control_path),
    )
