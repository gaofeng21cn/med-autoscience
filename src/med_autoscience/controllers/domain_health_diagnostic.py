from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import (
    autonomy_ai_doctor,
    control_intent,
    data_asset_gate,
    domain_action_request_materializer,
    domain_owner_action_dispatch,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
    runtime_health_kernel,
    owner_route_reconcile,
    domain_health_diagnostic_outer_loop_dispatch,
    domain_health_diagnostic_recovery_policy,
    domain_health_diagnostic_work_units,
    study_cycle_profiler,
    study_outer_loop,
    study_runtime_family_orchestration as family_orchestration,
    domain_status_projection,
    domain_transition_currentness,
)
from med_autoscience.controllers.domain_health_diagnostic_outer_loop_policy import (
    outer_loop_request_requires_fresh_controller_execution,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.autonomy_repair import (
    apply_ready_ai_doctor_repair,
    reconcile_ai_repair_lifecycle,
    read_ai_repair_lifecycle,
    read_ready_ai_doctor_repair,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.control_plane_gate import (
    CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
    apply_control_plane_dispatch_block,
    runtime_recovery_blocked_by_control_plane,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.fingerprints import build_fingerprint
from med_autoscience.controllers.domain_health_diagnostic_parts.gate_specificity import (
    _compact_work_unit_payload,
    _gate_specificity_non_executable_contract,
    _materialize_specificity_controller_state,
    _specificity_control_intent_identity,
    _specificity_terminal_status_payload,
    _study_requests_gate_specificity_terminal,
)
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
    _should_hard_auto_recover_managed_study,
    _should_refresh_managed_study_status_after_stage_request,
    _write_outer_loop_wakeup_audit,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.quest_scan import (
    DEFAULT_CONTROLLER_ORDER,
    ControllerRunner,
    _invoke_controller_runner,
    _publication_gate_ai_reviewer_eval_masks_return_to_gate,
    build_default_controller_runners,
    iter_ordered_controller_runners,
    run_domain_health_diagnostic_for_quest as _run_domain_health_diagnostic_for_quest_impl,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.reporting import (
    _attach_family_companion_to_quest_report,
    _attach_family_companion_to_runtime_report,
    _write_latest_domain_health_diagnostic_alias,
    render_domain_health_diagnostic_markdown,
    write_domain_health_diagnostic_report,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.runtime_scan import (
    _MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
    _MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
    _MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
    _NO_OP_SUPPRESSION_SUMMARY,
    _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY,
    _attach_no_op_suppression_to_quest_report,
    _managed_study_recovery_failure_payload,
    _materialize_placeholder_quest_diagnostic_report,
    _serialize_no_op_suppression,
    run_domain_health_diagnostic_for_runtime as _run_domain_health_diagnostic_for_runtime_impl,
    utc_now,
)
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.controllers.study_runtime_types import ProgressProjectionStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import domain_health_diagnostic as domain_health_diagnostic_protocol
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context
from med_autoscience.runtime_control.ports import RuntimeControlPorts


PROGRESS_FIRST_SAME_TICK_MAX_PASSES = 3


def _materialize_managed_study_autonomy_slo(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
) -> dict[str, Any]:
    profile_payload = study_cycle_profiler.profile_study_cycle(
        profile=profile,
        study_id=None,
        study_root=study_root,
    )
    slo_status = dict(profile_payload.get("autonomy_progress_slo_status") or {})
    return {
        "study_id": _non_empty_text(slo_status.get("study_id")) or Path(study_root).name,
        "quest_id": _non_empty_text(slo_status.get("quest_id")),
        "state": _non_empty_text(slo_status.get("state")) or "unknown",
        "breach_types": list(slo_status.get("breach_types") or []),
        "ai_doctor_request_required": bool(slo_status.get("ai_doctor_request_required")),
        "ai_doctor_state": _non_empty_text(slo_status.get("ai_doctor_state")) or "not_observed",
        "quality_gate_relaxation_allowed": False,
        "status_path": str(autonomy_ai_doctor.stable_slo_status_path(study_root=study_root)),
    }


def _materialize_domain_health_diagnostic_non_dispatching_decision(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
    tick_request: dict[str, Any],
    wakeup_audit: dict[str, Any],
) -> dict[str, Any]:
    if domain_health_diagnostic_work_units.needs_specificity_request(tick_request):
        return _materialize_specificity_controller_state(
            profile=profile,
            study_root=study_root,
            status_payload=status_payload,
            tick_request=tick_request,
            wakeup_audit=wakeup_audit,
            materialize_decision=study_outer_loop.materialize_non_dispatching_outer_loop_decision,
        )
    decision_payload = domain_health_diagnostic_work_units.strip_context(tick_request)
    decision_payload.pop("study_root", None)
    return study_outer_loop.materialize_non_dispatching_outer_loop_decision(
        profile=profile,
        study_root=study_root,
        status_payload=status_payload,
        source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
        recorded_at=_non_empty_text(wakeup_audit.get("recorded_at")),
        **decision_payload,
    )


def _refresh_managed_study_status_after_stage_request(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    if not _should_refresh_managed_study_status_after_stage_request(status_payload):
        return status_payload
    return _managed_study_status_payload(
        domain_status_projection.progress_projection(profile=profile, study_root=study_root)
    )


def _request_opl_stage_attempt(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    source: str,
) -> dict[str, Any]:
    status_payload = _managed_study_status_payload(
        domain_status_projection.progress_projection(profile=profile, study_root=study_root)
    )
    study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
    quest_id = _non_empty_text(status_payload.get("quest_id"))
    return {
        **status_payload,
        "decision": "blocked",
        "reason": "quest_waiting_opl_runtime_owner_route",
        "status": "opl_stage_attempt_admission_required",
        "source": source,
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "mas_executes_runtime_attempt": False,
        "provider_completion_is_domain_completion": False,
        "opl_stage_attempt_request": {
            "surface_kind": "mas_opl_stage_attempt_request",
            "study_id": study_id,
            "quest_id": quest_id,
            "study_root": str(Path(study_root).expanduser().resolve()),
            "source": source,
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "hydration_owner": "one-person-lab",
            "stage_attempt_state_owner": "one-person-lab",
            "mas_runtime_recovery_retired": True,
        },
        "resume_postcondition": {
            "effective": False,
            "status": "opl_stage_attempt_admission_required",
            "typed_blocker": {
                "blocker_type": "opl_stage_attempt_admission_required",
                "owner": "one-person-lab",
                "domain_owner": "med-autoscience",
                "reason": "mas_runtime_attempt_execution_retired",
                "required_handoff": "Hydrate MAS DomainIntent/owner-route refs through OPL current_control_state.",
            },
        },
    }


def _materialize_opl_runtime_owner_handoff(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
    recorded_at: str,
    apply: bool,
    domain_health_diagnostic_report_path: Path | None = None,
) -> dict[str, Any] | None:
    if status_payload.get("domain_health_diagnostic_error_isolated") is True:
        return None
    study_id = _non_empty_text(status_payload.get("study_id")) or Path(study_root).name
    quest_id = _non_empty_text(status_payload.get("quest_id"))
    quest_root = _candidate_path(status_payload.get("quest_root"))
    payload = {
        "surface_kind": "mas_opl_runtime_owner_handoff",
        "schema_version": 1,
        "recorded_at": recorded_at,
        "study_id": study_id,
        "quest_id": quest_id,
        "study_root": str(Path(study_root).expanduser().resolve()),
        "quest_root": str(quest_root) if quest_root is not None else None,
        "status": "handoff_required",
        "runtime_owner": "one-person-lab",
        "domain_owner": "med-autoscience",
        "provider_completion_is_domain_completion": False,
        "queue_succeeded_is_domain_completion": False,
        "mas_materializes_runtime_supervision": False,
        "mas_runtime_read_model_retired": True,
        "reason": _non_empty_text(status_payload.get("reason")) or "opl_current_control_state_required",
        "next_action_summary": (
            _non_empty_text(status_payload.get("next_action_summary"))
            or "Hydrate MAS owner-route refs through OPL current_control_state; OPL owns runtime retry/resume while MAS stays refs-only."
        ),
        "opl_current_control_state_ref": {
            "owner": "one-person-lab",
            "required": True,
            "hydrate_from": "MAS DomainIntent / owner-route refs",
        },
        "refs": {
            "domain_health_diagnostic_report_path": (
                str(domain_health_diagnostic_report_path.expanduser().resolve())
                if domain_health_diagnostic_report_path is not None
                else None
            ),
        },
        "typed_blocker": {
            "blocker_type": "opl_runtime_owner_handoff_required",
            "owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "reason": "mas_runtime_supervision_retired",
            "required_handoff": "Hydrate MAS owner-route refs through OPL current_control_state.",
        },
    }
    if apply:
        handoff_path = Path(study_root).expanduser().resolve() / "artifacts" / "supervision" / "opl_runtime_owner_handoff" / "latest.json"
        handoff_path.parent.mkdir(parents=True, exist_ok=True)
        handoff_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        payload["artifact_path"] = str(handoff_path)
    return payload


def _build_runtime_control_ports() -> RuntimeControlPorts:
    return RuntimeControlPorts(
        get_status=lambda **kwargs: _managed_study_status_payload(
            domain_status_projection.progress_projection(**kwargs)
        ),
        request_opl_stage_attempt=_request_opl_stage_attempt,
        build_outer_loop_request=_build_current_domain_transition_outer_loop_request,
        dispatch_outer_loop=domain_status_projection.study_outer_loop_tick,
        materialize_non_dispatching_decision=_materialize_domain_health_diagnostic_non_dispatching_decision,
        refresh_status_after_stage_request=_refresh_managed_study_status_after_stage_request,
        materialize_opl_runtime_owner_handoff=_materialize_opl_runtime_owner_handoff,
        reconcile_health=runtime_health_kernel.reconcile_runtime_health_snapshot_from_status_payload,
        materialize_autonomy_slo=_materialize_managed_study_autonomy_slo,
        read_ready_ai_repair=read_ready_ai_doctor_repair,
        apply_ai_repair=apply_ready_ai_doctor_repair,
        read_ai_repair_lifecycle=read_ai_repair_lifecycle,
        reconcile_ai_repair_lifecycle=reconcile_ai_repair_lifecycle,
    )


def _build_current_domain_transition_outer_loop_request(
    *,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any] | None:
    tick_request = study_outer_loop.build_domain_health_diagnostic_outer_loop_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if _tick_request_is_submission_milestone_autopark(tick_request):
        return tick_request
    fallback_tick_request = domain_transition_currentness.status_domain_transition_tick_request(
        study_root=study_root,
        status_payload=status_payload,
    )
    if isinstance(fallback_tick_request, dict) and not _tick_request_matches_status_transition(
        tick_request=tick_request,
        status_payload=status_payload,
    ):
        return fallback_tick_request
    return tick_request


def _tick_request_is_submission_milestone_autopark(tick_request: object) -> bool:
    if not isinstance(tick_request, dict):
        return False
    if str(tick_request.get("decision_type") or "").strip() != "continue_same_line":
        return False
    controller_actions = tick_request.get("controller_actions")
    first_action = (
        controller_actions[0]
        if isinstance(controller_actions, list) and controller_actions and isinstance(controller_actions[0], dict)
        else {}
    )
    return (
        str(first_action.get("action_type") or "").strip() == "stop_runtime"
        and str(tick_request.get("reason") or "").strip()
        == "Human-review milestone reached; stop the live runtime and wait for explicit resume."
    )

def _tick_request_matches_status_transition(
    *,
    tick_request: object,
    status_payload: dict[str, Any],
) -> bool:
    domain_transition = status_payload.get("domain_transition")
    if not isinstance(domain_transition, dict):
        return True
    transition_unit = domain_transition.get("next_work_unit")
    if not isinstance(transition_unit, dict):
        return True
    return domain_transition_currentness.tick_request_matches_domain_transition(
        tick_request=tick_request if isinstance(tick_request, dict) else {},
        transition_action=str(domain_transition.get("controller_action") or "").strip(),
        transition_type=str(domain_transition.get("decision_type") or "").strip(),
        transition_unit_id=str(transition_unit.get("unit_id") or "").strip(),
        transition_route_target=str(domain_transition.get("route_target") or "").strip() or None,
    )


def run_domain_health_diagnostic_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
) -> dict[str, Any]:
    return _run_domain_health_diagnostic_for_quest_impl(
        quest_root=quest_root,
        controller_runners=controller_runners,
        apply=apply,
        publication_gate_refresh_mask=_publication_gate_ai_reviewer_eval_masks_return_to_gate,
    )


def run_domain_health_diagnostic_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    request_opl_stage_attempts: bool = False,
    request_opl_owner_route_reconcile: bool = False,
) -> dict[str, Any]:
    report = _run_domain_health_diagnostic_for_runtime_impl(
        runtime_root=runtime_root,
        controller_runners=controller_runners or build_default_controller_runners(),
        apply=apply,
        run_domain_health_diagnostic_for_quest_fn=run_domain_health_diagnostic_for_quest,
        runtime_control_ports=_build_runtime_control_ports(),
        profile=profile,
        request_opl_stage_attempts=request_opl_stage_attempts,
    )
    if apply and request_opl_stage_attempts and request_opl_owner_route_reconcile and profile is not None:
        supervisor_tick = _run_developer_supervisor_same_tick(profile=profile)
        first_iteration = (supervisor_tick.get("iterations") or [{}])[0]
        report["opl_owner_route_reconcile_request"] = (
            _mapping(first_iteration).get("owner_route_reconcile") or {}
        )
        report["developer_supervisor_same_tick"] = supervisor_tick
    return report


def _run_developer_supervisor_same_tick(
    *,
    profile: WorkspaceProfile,
    max_passes: int = PROGRESS_FIRST_SAME_TICK_MAX_PASSES,
) -> dict[str, Any]:
    study_ids = owner_route_reconcile.resolve_owner_route_reconcile_study_ids(profile)
    iterations: list[dict[str, Any]] = []
    stop_reason = "max_passes_exhausted"
    for pass_index in range(1, max(1, max_passes) + 1):
        scan_result = owner_route_reconcile.scan_domain_routes(
            profile=profile,
            study_ids=study_ids,
            apply_safe_actions=True,
            developer_supervisor_mode="developer_apply_safe",
        )
        materialize_result = domain_action_request_materializer.materialize_domain_action_requests(
            profile=profile,
            study_ids=study_ids,
            mode="developer_apply_safe",
            apply=True,
        )
        dispatch_result = domain_owner_action_dispatch.dispatch_domain_owner_actions(
            profile=profile,
            study_ids=study_ids,
            action_types=(),
            mode="developer_apply_safe",
            apply=True,
        )
        iteration = {
            "pass_index": pass_index,
            "owner_route_reconcile": scan_result,
            "materialize": materialize_result,
            "dispatch": dispatch_result,
            "progress_first_delta": _same_tick_delta(
                scan_result=scan_result,
                materialize_result=materialize_result,
                dispatch_result=dispatch_result,
            ),
        }
        iterations.append(iteration)
        stop_reason = _same_tick_stop_reason(iteration)
        if stop_reason != "continue_same_tick_after_sync_owner_delta":
            break
    if stop_reason == "continue_same_tick_after_sync_owner_delta":
        stop_reason = "max_passes_exhausted_owner_delta_required"
    terminal_diagnostic = _same_tick_terminal_diagnostic(
        stop_reason=stop_reason,
        iterations=iterations,
    )
    return {
        "surface": "developer_supervisor_same_tick",
        "schema_version": 1,
        "mode": "developer_apply_safe",
        "study_ids": list(study_ids),
        "max_passes": max(1, max_passes),
        "pass_count": len(iterations),
        "stop_reason": stop_reason,
        "actions": [
            "owner-route-reconcile",
            "domain-action-request-materialize",
            "domain-owner-action-dispatch",
        ],
        "iterations": iterations,
        "owner_route_reconcile": _mapping(iterations[-1].get("owner_route_reconcile")) if iterations else {},
        "materialize": _mapping(iterations[-1].get("materialize")) if iterations else {},
        "dispatch": _mapping(iterations[-1].get("dispatch")) if iterations else {},
        "progress_first_terminal_diagnostic": terminal_diagnostic,
        "owner_boundaries": {
            "runtime_owner": "one-person-lab",
            "domain_owner": "med-autoscience",
            "paper_package_mutation_allowed": False,
            "quality_gate_relaxation_allowed": False,
            "manual_study_patch_allowed": False,
        },
    }


def _same_tick_delta(
    *,
    scan_result: Mapping[str, Any],
    materialize_result: Mapping[str, Any],
    dispatch_result: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "scan_action_count": _count(scan_result, "action_queue"),
        "materialized_request_count": _int_value(materialize_result.get("request_task_count")),
        "default_executor_dispatch_count": _int_value(materialize_result.get("default_executor_dispatch_count")),
        "dispatch_execution_count": _int_value(dispatch_result.get("execution_count")),
        "dispatch_executed_count": _int_value(dispatch_result.get("executed_count")),
        "dispatch_blocked_count": _int_value(dispatch_result.get("blocked_count")),
        "dispatch_repeat_suppressed_count": _int_value(dispatch_result.get("repeat_suppressed_count")),
        "codex_dispatch_count": _int_value(dispatch_result.get("codex_dispatch_count")),
        "handoff_ready_count": _execution_status_count(dispatch_result, "handoff_ready"),
    }


def _same_tick_stop_reason(iteration: Mapping[str, Any]) -> str:
    delta = _mapping(iteration.get("progress_first_delta"))
    if _int_value(delta.get("codex_dispatch_count")) > 0 or _int_value(delta.get("handoff_ready_count")) > 0:
        return "provider_handoff_started"
    if _int_value(delta.get("dispatch_blocked_count")) > 0:
        return "typed_blocker_or_dispatch_blocker_observed"
    if _int_value(delta.get("dispatch_repeat_suppressed_count")) > 0:
        return "repeat_suppressed_owner_delta_required"
    if _int_value(delta.get("dispatch_executed_count")) > 0:
        return "continue_same_tick_after_sync_owner_delta"
    if _int_value(delta.get("default_executor_dispatch_count")) > 0:
        return "dispatch_materialized_but_not_selected"
    if _int_value(delta.get("scan_action_count")) > 0:
        return "owner_action_projected_but_not_materialized"
    return "no_owner_action_remaining"


def _same_tick_terminal_diagnostic(
    *,
    stop_reason: str,
    iterations: list[dict[str, Any]],
) -> dict[str, Any]:
    last_iteration = iterations[-1] if iterations else {}
    last_delta = _mapping(last_iteration.get("progress_first_delta"))
    requires_next_owner_delta = stop_reason in {
        "repeat_suppressed_owner_delta_required",
        "max_passes_exhausted_owner_delta_required",
    }
    return {
        "surface": "progress_first_developer_supervisor_terminal_diagnostic",
        "schema_version": 1,
        "stop_reason": stop_reason,
        "requires_next_owner_delta": requires_next_owner_delta,
        "last_iteration_delta": dict(last_delta),
        "next_forced_delta": (
            {
                "required_delta_kind": (
                    "deliverable_progress_delta_or_domain_owner_receipt_or_typed_blocker"
                ),
                "reason": stop_reason,
                "target_surface": {
                    "surface_ref": "MAS owner receipt, domain typed blocker, or paper-facing deliverable delta",
                    "owner": "med-autoscience",
                },
                "acceptance_refs": [
                    "deliverable_progress_delta",
                    "domain_owner_receipt_ref",
                    "domain_typed_blocker_ref",
                    "human_gate_or_stop_loss_ref",
                ],
            }
            if requires_next_owner_delta
            else None
        ),
        "forbidden_next_actions": (
            [
                "repeat_receipt_reconcile_without_owner_delta",
                "repeat_read_model_reconcile_without_owner_delta",
                "start_new_provider_attempt_for_same_source_without_owner_delta",
            ]
            if requires_next_owner_delta
            else []
        ),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _count(payload: Mapping[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, list):
        return len(value)
    return _int_value(value)


def _execution_status_count(payload: Mapping[str, Any], status: str) -> int:
    return sum(
        1
        for item in payload.get("executions") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("execution_status")) == status
    )


def _int_value(value: object) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--quest-root", type=Path)
    parser.add_argument("--runtime-root", type=Path)
    parser.add_argument("--apply", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if bool(args.quest_root) == bool(args.runtime_root):
        raise SystemExit("Specify exactly one of --quest-root or --runtime-root")
    if args.quest_root:
        result = run_domain_health_diagnostic_for_quest(quest_root=args.quest_root, apply=args.apply)
    else:
        result = run_domain_health_diagnostic_for_runtime(runtime_root=args.runtime_root, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
