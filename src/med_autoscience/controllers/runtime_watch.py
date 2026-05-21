from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

from med_autoscience import runtime_backend as runtime_backend_contract
from med_autoscience.controllers import (
    autonomy_ai_doctor,
    control_intent,
    data_asset_gate,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
    runtime_health_kernel,
    runtime_supervision,
    domain_route_scan,
    runtime_watch_alerts,
    runtime_watch_outer_loop_dispatch,
    runtime_watch_recovery_policy,
    runtime_watch_work_units,
    study_cycle_profiler,
    study_outer_loop,
    study_runtime_family_orchestration as family_orchestration,
    study_runtime_router,
)
from med_autoscience.controllers.runtime_watch_outer_loop_policy import (
    outer_loop_request_requires_fresh_controller_execution,
)
from med_autoscience.controllers.runtime_watch_parts.autonomy_repair import (
    apply_ready_ai_doctor_repair,
    reconcile_ai_repair_lifecycle,
    read_ai_repair_lifecycle,
    read_ready_ai_doctor_repair,
)
from med_autoscience.controllers.runtime_watch_parts.control_plane_gate import (
    CONTROL_PLANE_DISPATCH_BLOCKED_SUMMARY,
    apply_control_plane_dispatch_block,
    runtime_recovery_blocked_by_control_plane,
)
from med_autoscience.controllers.runtime_watch_parts.fingerprints import build_fingerprint
from med_autoscience.controllers.runtime_watch_parts.gate_specificity import (
    _clear_quest_user_messages_for_superseded_specificity,
    _compact_work_unit_payload,
    _gate_specificity_non_executable_contract,
    _materialize_specificity_controller_state,
    _specificity_control_intent_identity,
    _specificity_terminal_status_payload,
    _study_requests_gate_specificity_terminal,
    _write_runtime_state,
)
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
    _should_hard_auto_recover_managed_study,
    _should_refresh_managed_study_status_after_ensure,
    _write_outer_loop_wakeup_audit,
)
from med_autoscience.controllers.runtime_watch_parts.quest_scan import (
    DEFAULT_CONTROLLER_ORDER,
    ControllerRunner,
    _invoke_controller_runner,
    _publication_gate_ai_reviewer_eval_masks_return_to_gate,
    build_default_controller_runners,
    iter_ordered_controller_runners,
    run_watch_for_quest as _run_watch_for_quest_impl,
)
from med_autoscience.controllers.runtime_watch_parts.reporting import (
    _attach_family_companion_to_quest_report,
    _attach_family_companion_to_runtime_report,
    _write_latest_watch_alias,
    render_watch_markdown,
    write_watch_report,
)
from med_autoscience.controllers.runtime_watch_parts.runtime_scan import (
    _MANAGED_STUDY_AUTO_RECOVERY_SOURCE,
    _MANAGED_STUDY_CONTROLLER_REROUTE_SOURCE,
    _MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
    _NO_OP_SUPPRESSION_SUMMARY,
    _WORK_UNIT_REDRIVE_EXHAUSTED_SUMMARY,
    _attach_no_op_suppression_to_quest_report,
    _managed_study_recovery_failure_payload,
    _materialize_placeholder_quest_watch_report,
    _serialize_no_op_suppression,
    run_watch_for_runtime as _run_watch_for_runtime_impl,
    utc_now,
)
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context
from med_autoscience.runtime_control.ports import RuntimeControlPorts


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


def _materialize_runtime_watch_non_dispatching_decision(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
    tick_request: dict[str, Any],
    wakeup_audit: dict[str, Any],
) -> dict[str, Any]:
    if runtime_watch_work_units.needs_specificity_request(tick_request):
        return _materialize_specificity_controller_state(
            profile=profile,
            study_root=study_root,
            status_payload=status_payload,
            tick_request=tick_request,
            wakeup_audit=wakeup_audit,
            materialize_decision=study_outer_loop.materialize_non_dispatching_outer_loop_decision,
        )
    decision_payload = runtime_watch_work_units.strip_context(tick_request)
    decision_payload.pop("study_root", None)
    return study_outer_loop.materialize_non_dispatching_outer_loop_decision(
        profile=profile,
        study_root=study_root,
        status_payload=status_payload,
        source=_MANAGED_STUDY_OUTER_LOOP_WAKEUP_SOURCE,
        recorded_at=_non_empty_text(wakeup_audit.get("recorded_at")),
        **decision_payload,
    )


def _refresh_managed_study_status_after_ensure(
    *,
    profile: WorkspaceProfile,
    study_root: Path,
    status_payload: dict[str, Any],
) -> dict[str, Any]:
    if not _should_refresh_managed_study_status_after_ensure(status_payload):
        return status_payload
    return _managed_study_status_payload(
        study_runtime_router.study_runtime_status(profile=profile, study_root=study_root)
    )


def _build_runtime_control_ports() -> RuntimeControlPorts:
    return RuntimeControlPorts(
        get_status=lambda **kwargs: _managed_study_status_payload(
            study_runtime_router.study_runtime_status(**kwargs)
        ),
        ensure_runtime=lambda **kwargs: _managed_study_status_payload(
            study_runtime_router.ensure_study_runtime(**kwargs)
        ),
        build_outer_loop_request=study_outer_loop.build_runtime_watch_outer_loop_tick_request,
        dispatch_outer_loop=study_runtime_router.study_outer_loop_tick,
        materialize_non_dispatching_decision=_materialize_runtime_watch_non_dispatching_decision,
        refresh_status_after_ensure=_refresh_managed_study_status_after_ensure,
        materialize_supervision=runtime_supervision.materialize_runtime_supervision,
        deliver_alert=runtime_watch_alerts.deliver_runtime_alert,
        reconcile_health=runtime_health_kernel.reconcile_runtime_health_snapshot_from_status_payload,
        materialize_autonomy_slo=_materialize_managed_study_autonomy_slo,
        read_ready_ai_repair=read_ready_ai_doctor_repair,
        apply_ai_repair=apply_ready_ai_doctor_repair,
        read_ai_repair_lifecycle=read_ai_repair_lifecycle,
        reconcile_ai_repair_lifecycle=reconcile_ai_repair_lifecycle,
    )


def run_watch_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
) -> dict[str, Any]:
    return _run_watch_for_quest_impl(
        quest_root=quest_root,
        controller_runners=controller_runners,
        apply=apply,
        publication_gate_refresh_mask=_publication_gate_ai_reviewer_eval_masks_return_to_gate,
    )


def run_watch_for_runtime(
    *,
    runtime_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    profile: WorkspaceProfile | None = None,
    ensure_study_runtimes: bool = False,
    apply_supervisor_platform_repair: bool = False,
) -> dict[str, Any]:
    report = _run_watch_for_runtime_impl(
        runtime_root=runtime_root,
        controller_runners=controller_runners or build_default_controller_runners(),
        apply=apply,
        run_watch_for_quest_fn=run_watch_for_quest,
        runtime_control_ports=_build_runtime_control_ports(),
        profile=profile,
        ensure_study_runtimes=ensure_study_runtimes,
    )
    if apply and ensure_study_runtimes and apply_supervisor_platform_repair and profile is not None:
        report["supervisor_platform_repair"] = domain_route_scan.scan_domain_routes(
            profile=profile,
            study_ids=domain_route_scan.resolve_domain_route_scan_study_ids(profile),
            apply_safe_actions=True,
            apply_runtime_platform_repair=True,
            developer_supervisor_mode="developer_apply_safe",
        )
    return report


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
        apply_supervisor_platform_repair=True,
    )


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
        result = run_watch_for_quest(quest_root=args.quest_root, apply=args.apply)
    else:
        result = run_watch_for_runtime(runtime_root=args.runtime_root, apply=args.apply)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
