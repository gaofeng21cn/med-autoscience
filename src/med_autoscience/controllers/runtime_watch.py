from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.controllers import (
    data_asset_gate,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
    runtime_supervision,
    runtime_watch_alerts,
    runtime_watch_recovery_policy,
    runtime_watch_outer_loop_dispatch,
    runtime_watch_work_units,
    study_outer_loop,
    study_runtime_family_orchestration as family_orchestration,
    study_runtime_router,
)
from med_autoscience.controllers.runtime_watch_parts.managed_wakeup import (
    _build_outer_loop_wakeup_audit,
    _candidate_path,
    _controller_decision_latest_matches_outer_loop_request,
    _managed_study_status_payload,
    _non_empty_text,
    _quest_report_requests_managed_study_reroute,
    _refresh_managed_study_status_after_ensure,
    _serialize_managed_study_action,
    _serialize_managed_study_auto_recovery,
    _should_hard_auto_recover_managed_study,
    _write_outer_loop_wakeup_audit,
)
from med_autoscience.controllers.runtime_watch_parts.reporting import (
    _attach_family_companion_to_quest_report,
    _attach_family_companion_to_runtime_report,
    _write_latest_watch_alias,
    render_watch_markdown,
    write_watch_report,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol
from med_autoscience.controllers.runtime_watch_outer_loop_policy import outer_loop_request_requires_fresh_controller_execution
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)


ControllerRunner = Callable[..., dict[str, Any]]

DEFAULT_CONTROLLER_ORDER: tuple[str, ...] = (
    "data_asset_gate",
    "medical_publication_surface",
    "publication_gate",
    "medical_literature_audit",
    "medical_reporting_audit",
    "figure_loop_guard",
)

_MANAGED_STUDY_AUTO_RECOVERY_SOURCE = "runtime_watch_auto_recovery"
_MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE = "runtime_watch_controller_reroute"
_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE = "runtime_watch_outer_loop_wakeup"
_NO_OP_SUPPRESSION_SUMMARY = "同一 blocker fingerprint 已执行过同一 controller work unit；继续空转不会增加论文证据。"

def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_default_controller_runners() -> dict[str, ControllerRunner]:
    return {
        "data_asset_gate": data_asset_gate.run_controller,
        "medical_publication_surface": medical_publication_surface.run_controller,
        "publication_gate": publication_gate.run_controller,
        "medical_literature_audit": medical_literature_audit.run_controller,
        "medical_reporting_audit": medical_reporting_audit.run_controller,
        "figure_loop_guard": figure_loop_guard.run_controller,
    }


def iter_ordered_controller_runners(
    controller_runners: dict[str, ControllerRunner],
) -> list[tuple[str, ControllerRunner]]:
    priority = {name: index for index, name in enumerate(DEFAULT_CONTROLLER_ORDER)}
    ordered_known: list[tuple[int, tuple[str, ControllerRunner]]] = []
    ordered_unknown: list[tuple[str, ControllerRunner]] = []
    for name, runner in controller_runners.items():
        entry = (name, runner)
        if name in priority:
            ordered_known.append((priority[name], entry))
        else:
            ordered_unknown.append(entry)
    return [entry for _, entry in sorted(ordered_known, key=lambda item: item[0])] + ordered_unknown


def build_fingerprint(controller_name: str, result: dict[str, Any]) -> str:
    if controller_name == "publication_gate":
        payload = {
            "status": result.get("status"),
            "allow_write": result.get("allow_write"),
            "blockers": result.get("blockers") or [],
            "missing_non_scalar_deliverables": result.get("missing_non_scalar_deliverables") or [],
            "submission_minimal_present": result.get("submission_minimal_present"),
            "draft_handoff_delivery_required": result.get("draft_handoff_delivery_required"),
            "draft_handoff_delivery_status": result.get("draft_handoff_delivery_status"),
            "supervisor_phase": result.get("supervisor_phase"),
            "phase_owner": result.get("phase_owner"),
            "upstream_scientific_anchor_ready": result.get("upstream_scientific_anchor_ready"),
            "bundle_tasks_downstream_only": result.get("bundle_tasks_downstream_only"),
            "current_required_action": result.get("current_required_action"),
            "deferred_downstream_actions": result.get("deferred_downstream_actions") or [],
            "controller_stage_note": result.get("controller_stage_note"),
        }
    elif controller_name == "medical_publication_surface":
        top_hits = result.get("top_hits") or []
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "top_hits": [
                {
                    "path": item.get("path"),
                    "location": item.get("location"),
                    "phrase": item.get("phrase"),
                }
                for item in top_hits[:10]
            ],
        }
    elif controller_name == "data_asset_gate":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "advisories": result.get("advisories") or [],
            "study_id": result.get("study_id"),
            "outdated_dataset_ids": result.get("outdated_dataset_ids") or [],
            "unresolved_dataset_ids": result.get("unresolved_dataset_ids") or [],
            "public_support_dataset_ids": result.get("public_support_dataset_ids") or [],
        }
    elif controller_name == "figure_loop_guard":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "dominant_figure_id": result.get("dominant_figure_id"),
            "dominant_figure_mentions": result.get("dominant_figure_mentions"),
            "reference_count": result.get("reference_count"),
        }
    elif controller_name == "medical_literature_audit":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "action": result.get("action"),
            "missing_pmids": result.get("missing_pmids") or [],
        }
    elif controller_name == "medical_reporting_audit":
        payload = {
            "status": result.get("status"),
            "blockers": result.get("blockers") or [],
            "action": result.get("action"),
        }
    else:
        payload = result
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _invoke_controller_runner(
    runner: ControllerRunner,
    *,
    quest_root: Path,
    apply: bool,
) -> dict[str, Any]:
    try:
        return runner(quest_root=quest_root, apply=apply)
    except FileNotFoundError as exc:
        return {
            "status": "awaiting_artifacts",
            "blockers": [],
            "advisories": [f"missing_artifact:{exc}"],
            "report_json": None,
            "report_markdown": None,
            "suppression_reason": "precondition_missing",
        }


def _serialize_no_op_suppression(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
    wakeup_audit: Mapping[str, Any],
) -> dict[str, Any] | None:
    outcome = _non_empty_text(wakeup_audit.get("outcome"))
    if outcome not in {"skipped_matching_work_unit", "skipped_matching_decision", "skipped_unchanged_inputs"}:
        return None
    payload: dict[str, Any] = {
        "study_id": _non_empty_text(status_payload.get("study_id")) or Path(study_root).name,
        "quest_id": _non_empty_text(status_payload.get("quest_id")),
        "outcome": outcome,
        "reason": _non_empty_text(wakeup_audit.get("reason")),
        "dedupe_scope": _non_empty_text(wakeup_audit.get("dedupe_scope")),
    }
    for key in ("work_unit_fingerprint", "next_work_unit"):
        value = wakeup_audit.get(key)
        if value is not None:
            payload[key] = dict(value) if isinstance(value, Mapping) else value
    if outcome == "skipped_matching_work_unit":
        payload["operator_summary"] = _NO_OP_SUPPRESSION_SUMMARY
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


def run_watch_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
) -> dict[str, Any]:
    controller_runners = controller_runners or build_default_controller_runners()
    current_state = runtime_watch_protocol.load_watch_state(quest_root)
    controller_state = dict(current_state.controllers)
    report: dict[str, Any] = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "quest_root": str(quest_root),
        "quest_status": quest_state.quest_status(quest_root),
        "controllers": {},
    }
    runtime_efficiency = _latest_run_telemetry_surface(
        quest_root=quest_root,
        status=quest_state.load_runtime_state(quest_root),
    )
    if runtime_efficiency is not None:
        report["runtime_efficiency"] = runtime_efficiency

    for name, runner in iter_ordered_controller_runners(controller_runners):
        dry_run_result = _invoke_controller_runner(runner, quest_root=quest_root, apply=False)
        fingerprint = build_fingerprint(name, dry_run_result)
        previous = controller_state.get(name) or runtime_watch_protocol.RuntimeWatchControllerState()
        intervention_statuses = {"blocked"}
        if name == "data_asset_gate":
            intervention_statuses.add("advisory")
        if (
            name == "publication_gate"
            and dry_run_result.get("draft_handoff_delivery_required") is True
            and str(dry_run_result.get("draft_handoff_delivery_status") or "").strip() in {"missing", "stale", "invalid"}
            and str(dry_run_result.get("status") or "").strip()
        ):
            intervention_statuses.add(str(dry_run_result.get("status") or "").strip())
        plan = runtime_watch_protocol.plan_controller_intervention(
            previous_controller_state=previous,
            dry_run_result=dry_run_result,
            fingerprint=fingerprint,
            apply=apply,
            scanned_at=report["scanned_at"],
            intervention_statuses=intervention_statuses,
        )
        final_result = dry_run_result
        if plan.should_apply:
            final_result = _invoke_controller_runner(runner, quest_root=quest_root, apply=True)
            final_fingerprint = build_fingerprint(name, final_result)
            controller_state[name] = runtime_watch_protocol.RuntimeWatchControllerState(
                last_seen_fingerprint=final_fingerprint,
                last_applied_fingerprint=final_fingerprint,
                last_applied_at=report["scanned_at"],
                last_status=str(final_result.get("status") or "").strip() or None,
                last_suppression_reason=None,
            )
        else:
            controller_state[name] = plan.controller_state
        report_result = final_result if plan.should_apply else dry_run_result
        status = report_result.get("status")
        suppression_reason = plan.suppression_reason
        report["controllers"][name] = {
            "status": status,
            "action": plan.action.value,
            "blockers": report_result.get("blockers") or [],
            "advisories": report_result.get("advisories") or [],
            "report_json": final_result.get("report_json"),
            "report_markdown": final_result.get("report_markdown"),
            "suppression_reason": suppression_reason,
        }
        if name == "publication_gate":
            report["controllers"][name].update(
                {
                    "supervisor_phase": report_result.get("supervisor_phase"),
                    "phase_owner": report_result.get("phase_owner"),
                    "upstream_scientific_anchor_ready": report_result.get("upstream_scientific_anchor_ready"),
                    "bundle_tasks_downstream_only": report_result.get("bundle_tasks_downstream_only"),
                    "current_required_action": report_result.get("current_required_action"),
                    "deferred_downstream_actions": report_result.get("deferred_downstream_actions") or [],
                    "controller_stage_note": report_result.get("controller_stage_note"),
                    "draft_handoff_delivery_required": report_result.get("draft_handoff_delivery_required"),
                    "draft_handoff_delivery_status": report_result.get("draft_handoff_delivery_status"),
                }
            )
        if name == "figure_loop_guard":
            report["controllers"][name].update(
                {
                    "quest_stop_applied": bool(report_result.get("quest_stop_applied")),
                    "quest_stop_status": report_result.get("quest_stop_status"),
                    "quest_stop_deferred": bool(report_result.get("quest_stop_deferred")),
                    "quest_stop_defer_reason": report_result.get("quest_stop_defer_reason"),
                }
            )

    _attach_family_companion_to_quest_report(report, quest_root=quest_root)
    runtime_watch_protocol.save_watch_state(
        quest_root=quest_root,
        payload=runtime_watch_protocol.RuntimeWatchState(
            schema_version=1,
            updated_at=report["scanned_at"],
            controllers=controller_state,
        ),
    )
    json_path, md_path, latest_json, latest_markdown = write_watch_report(quest_root, report)
    report["report_json"] = str(json_path)
    report["report_markdown"] = str(md_path)
    report["latest_report_json"] = str(latest_json)
    report["latest_report_markdown"] = str(latest_markdown)
    return report


def run_watch_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    ensure_study_runtimes: bool = False,
) -> dict[str, Any]:
    controller_runners = controller_runners or build_default_controller_runners()
    managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
    managed_study_auto_recoveries: list[dict[str, Any]] = []
    managed_study_recovery_holds: list[dict[str, Any]] = []
    managed_study_outer_loop_dispatches: list[dict[str, Any]] = []
    managed_study_outer_loop_wakeup_audits: list[dict[str, Any]] = []
    managed_study_no_op_suppressions: list[dict[str, Any]] = []
    managed_study_alert_deliveries: list[dict[str, Any]] = []
    if ensure_study_runtimes:
        if profile is None:
            raise ValueError("profile is required when ensure_study_runtimes is enabled")
        for study_root in sorted(profile.studies_root.iterdir()):
            if not study_root.is_dir():
                continue
            if not (study_root / "study.yaml").exists():
                continue
            if apply:
                action_payload = study_runtime_router.ensure_study_runtime(
                    profile=profile,
                    study_root=study_root,
                    source="runtime_watch",
                )
            else:
                action_payload = study_runtime_router.study_runtime_status(
                    profile=profile,
                    study_root=study_root,
                )
                if _should_hard_auto_recover_managed_study(action_payload):
                    preflight_payload = action_payload
                    recovery_hold = runtime_watch_recovery_policy.hold_for_flapping_circuit_breaker(
                        study_root=study_root,
                        status_payload=preflight_payload,
                    )
                    if recovery_hold is not None:
                        runtime_watch_recovery_policy.write_recovery_probe(
                            study_root=study_root,
                            recovery_hold=recovery_hold,
                        )
                        managed_study_recovery_holds.append(recovery_hold)
                    else:
                        action_payload = study_runtime_router.ensure_study_runtime(
                            profile=profile,
                            study_root=study_root,
                            source=_MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
                        )
                        managed_study_auto_recoveries.append(
                            _serialize_managed_study_auto_recovery(
                                preflight_payload=preflight_payload,
                                applied_payload=action_payload,
                                source=_MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
                            )
                        )
            managed_study_statuses.append((study_root, _managed_study_status_payload(action_payload)))
    scanned: list[str] = []
    reports: list[dict[str, Any]] = []
    for quest_root in quest_state.iter_active_quests(runtime_root):
        scanned.append(quest_root.name)
        reports.append(
            run_watch_for_quest(
                quest_root=quest_root,
                controller_runners=controller_runners,
                apply=apply,
            )
        )
    report_by_quest_root = {
        str(Path(str(report.get("quest_root") or "")).expanduser().resolve()): report
        for report in reports
        if str(report.get("quest_root") or "").strip()
    }
    if apply and ensure_study_runtimes and profile is not None:
        rerouted_managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
        for study_root, status_payload in managed_study_statuses:
            resolved_status_payload = status_payload
            quest_root = status_payload.get("quest_root")
            quest_report = report_by_quest_root.get(str(Path(str(quest_root)).expanduser().resolve())) if quest_root else None
            if _quest_report_requests_managed_study_reroute(quest_report):
                rerouted_payload = study_runtime_router.ensure_study_runtime(
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
    for study_root, status_payload in managed_study_statuses:
        if profile is not None:
            status_payload = _refresh_managed_study_status_after_ensure(
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
            if runtime_watch_work_units.outer_loop_wakeup_inputs_unchanged(wakeup_audit):
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
                tick_request = study_outer_loop.build_runtime_watch_outer_loop_tick_request(
                    study_root=study_root,
                    status_payload=status_payload,
                )
                if tick_request is None:
                    wakeup_audit = {
                        **wakeup_audit,
                        "outcome": "no_request",
                        "reason": "outer-loop wakeup did not produce an autonomous request",
                    }
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
                    outer_loop_result = study_runtime_router.study_outer_loop_tick(
                        profile=profile,
                        source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
                        **runtime_watch_work_units.strip_context(tick_request),
                    )
                    if _non_empty_text(outer_loop_result.get("dispatch_status")) != "executed":
                        raise ValueError("runtime watch outer-loop wakeup requires executed autonomous dispatch")
                    dispatch_payload = runtime_watch_outer_loop_dispatch.serialize_outer_loop_dispatch(
                        tick_request=tick_request,
                        outer_loop_result=outer_loop_result,
                    )
                    managed_study_outer_loop_dispatches.append(dispatch_payload)
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
                        study_runtime_router.study_runtime_status(
                            profile=profile,
                            study_root=study_root,
                        )
                    )
                _write_outer_loop_wakeup_audit(study_root=study_root, audit=wakeup_audit)
                managed_study_outer_loop_wakeup_audits.append(wakeup_audit)
        quest_root = _candidate_path(status_payload.get("quest_root"))
        quest_report = report_by_quest_root.get(str(quest_root)) if quest_root is not None else None
        supervision_report = runtime_supervision.materialize_runtime_supervision(
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
            alert_delivery = runtime_watch_alerts.deliver_runtime_alert(
                profile=profile,
                study_root=study_root,
                status_payload=status_payload,
                supervision_report=supervision_report,
                apply=apply,
            )
            if alert_delivery is not None:
                managed_study_alert_deliveries.append(alert_delivery)
    managed_study_actions = [
        _serialize_managed_study_action(status_payload)
        for _, status_payload in managed_study_statuses
    ]
    runtime_report = {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "runtime_root": str(runtime_root),
        "scanned_quests": scanned,
        "managed_study_actions": managed_study_actions,
        "managed_study_auto_recoveries": managed_study_auto_recoveries,
        "managed_study_recovery_holds": managed_study_recovery_holds,
        "managed_study_outer_loop_dispatches": managed_study_outer_loop_dispatches,
        "managed_study_outer_loop_wakeup_audits": managed_study_outer_loop_wakeup_audits,
        "managed_study_no_op_suppressions": managed_study_no_op_suppressions,
        "managed_study_supervision": managed_study_supervision,
        "managed_study_alert_deliveries": managed_study_alert_deliveries,
        "reports": reports,
    }
    _attach_family_companion_to_runtime_report(runtime_report, runtime_root=Path(runtime_root).expanduser().resolve())
    return runtime_report


def run_watch_loop(
    *,
    runtime_root: Path,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    ensure_study_runtimes: bool = False,
    interval_seconds: int = 300,
    max_ticks: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    resolved_runtime_root = Path(runtime_root).expanduser().resolve()
    if interval_seconds <= 0:
        raise ValueError("interval_seconds must be positive")
    if max_ticks is not None and max_ticks <= 0:
        raise ValueError("max_ticks must be positive when provided")

    tick_count = 0
    last_result: dict[str, Any] | None = None
    tick_errors: list[dict[str, Any]] = []
    started_at = utc_now()

    while True:
        tick_count += 1
        try:
            last_result = run_watch_for_runtime(
                runtime_root=resolved_runtime_root,
                controller_runners=None,
                apply=apply,
                profile=profile,
                ensure_study_runtimes=ensure_study_runtimes,
            )
        except Exception as exc:
            tick_errors.append(
                {
                    "tick": tick_count,
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )
        if max_ticks is not None and tick_count >= max_ticks:
            break
        sleep_fn(float(interval_seconds))

    return {
        "schema_version": 1,
        "mode": "loop",
        "started_at": started_at,
        "completed_at": utc_now(),
        "runtime_root": str(resolved_runtime_root),
        "apply": apply,
        "ensure_study_runtimes": ensure_study_runtimes,
        "interval_seconds": interval_seconds,
        "tick_count": tick_count,
        "tick_errors": tick_errors,
        "last_result": last_result,
    }


def run_managed_supervisor_tick(
    *,
    profile: WorkspaceProfile,
    apply: bool,
) -> dict[str, Any]:
    return run_watch_for_runtime(
        runtime_root=profile.runtime_root,
        apply=apply,
        profile=profile,
        ensure_study_runtimes=True,
    )


def run_managed_supervisor_loop(
    *,
    profile: WorkspaceProfile,
    apply: bool,
    interval_seconds: int = 300,
    max_ticks: int | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> dict[str, Any]:
    return run_watch_loop(
        runtime_root=profile.runtime_root,
        apply=apply,
        profile=profile,
        ensure_study_runtimes=True,
        interval_seconds=interval_seconds,
        max_ticks=max_ticks,
        sleep_fn=sleep_fn,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--loop", action="store_true")
    parser.add_argument("--interval-seconds", type=int, default=300)
    parser.add_argument("--max-ticks", type=int)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.quest_root) == bool(args.runtime_root):
        raise SystemExit("Specify exactly one of --quest-root or --runtime-root")
    if args.loop and args.quest_root:
        raise SystemExit("--loop is only supported with --runtime-root")
    if args.quest_root:
        result = run_watch_for_quest(quest_root=args.quest_root, apply=args.apply)
    elif args.loop:
        result = run_watch_loop(
            runtime_root=args.runtime_root,
            apply=args.apply,
            interval_seconds=args.interval_seconds,
            max_ticks=args.max_ticks,
        )
    else:
        result = run_watch_for_runtime(runtime_root=args.runtime_root, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
