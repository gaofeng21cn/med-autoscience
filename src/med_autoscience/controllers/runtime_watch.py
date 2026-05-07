from __future__ import annotations

import argparse
import json
import time
from collections.abc import Callable
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
    _refresh_managed_study_status_after_ensure,
    _serialize_managed_study_action,
    _serialize_managed_study_auto_recovery,
    _should_hard_auto_recover_managed_study,
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
    _materialize_managed_study_autonomy_slo,
    _materialize_placeholder_quest_watch_report,
    _serialize_no_op_suppression,
    run_watch_for_runtime as _run_watch_for_runtime_impl,
    utc_now,
)
from med_autoscience.controllers.runtime_watch_parts import runtime_scan as _runtime_scan_part
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context


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
) -> dict[str, Any]:
    _runtime_scan_part._refresh_managed_study_status_after_ensure = _refresh_managed_study_status_after_ensure
    return _run_watch_for_runtime_impl(
        runtime_root=runtime_root,
        controller_runners=controller_runners or build_default_controller_runners(),
        apply=apply,
        run_watch_for_quest_fn=run_watch_for_quest,
        profile=profile,
        ensure_study_runtimes=ensure_study_runtimes,
        materialize_managed_study_autonomy_slo=_materialize_managed_study_autonomy_slo,
    )


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
