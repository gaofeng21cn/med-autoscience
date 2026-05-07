from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers.runtime_watch_parts.reporting import _attach_family_companion_to_runtime_report
from med_autoscience.runtime_protocol import quest_state


def scan_active_quest_reports(
    *,
    runtime_root: Path,
    controller_runners: dict[str, Callable[..., dict[str, Any]]],
    apply: bool,
    run_watch_for_quest_fn: Callable[..., dict[str, Any]],
) -> tuple[list[str], list[dict[str, Any]], dict[str, dict[str, Any]]]:
    scanned: list[str] = []
    reports: list[dict[str, Any]] = []
    for quest_root in quest_state.iter_active_quests(runtime_root):
        scanned.append(quest_root.name)
        reports.append(
            run_watch_for_quest_fn(
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
    return scanned, reports, report_by_quest_root


def build_runtime_report(
    *,
    runtime_root: Path,
    scanned: list[str],
    reports: list[dict[str, Any]],
    managed_study_actions: list[dict[str, Any]],
    managed_study_auto_recoveries: list[dict[str, Any]],
    managed_study_recovery_holds: list[dict[str, Any]],
    managed_study_outer_loop_dispatches: list[dict[str, Any]],
    managed_study_outer_loop_wakeup_audits: list[dict[str, Any]],
    managed_study_no_op_suppressions: list[dict[str, Any]],
    managed_study_supervision: list[dict[str, Any]],
    managed_study_alert_deliveries: list[dict[str, Any]],
    managed_study_autonomy_slo_statuses: list[dict[str, Any]],
    managed_study_autonomy_repair_actions: list[dict[str, Any]],
) -> dict[str, Any]:
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
        "managed_study_autonomy_slo_statuses": managed_study_autonomy_slo_statuses,
        "managed_study_autonomy_repair_actions": managed_study_autonomy_repair_actions,
        "reports": reports,
    }
    _attach_family_companion_to_runtime_report(runtime_report, runtime_root=Path(runtime_root).expanduser().resolve())
    return runtime_report


def utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = ["build_runtime_report", "scan_active_quest_reports"]
