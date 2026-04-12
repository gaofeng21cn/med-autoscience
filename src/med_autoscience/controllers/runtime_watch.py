from __future__ import annotations

import argparse
import hashlib
import json
import time
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import (
    data_asset_gate,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
    runtime_supervision,
    study_runtime_router,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol


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
_HARD_AUTO_RECOVERY_QUEST_STATUSES = frozenset({"active", "running", "waiting_for_user"})
_HARD_AUTO_RECOVERY_REASONS = frozenset(
    {
        "quest_marked_running_but_no_live_session",
        "quest_parked_on_unchanged_finalize_state",
        "quest_waiting_on_invalid_blocking",
        "quest_completion_requested_before_publication_gate_clear",
        "quest_waiting_for_submission_metadata",
    }
)


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


def _serialize_managed_study_action(
    action_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any]:
    action = (
        action_payload
        if isinstance(action_payload, StudyRuntimeStatus)
        else StudyRuntimeStatus.from_payload(action_payload)
    )
    return {
        "study_id": action.study_id,
        "decision": action.decision.value if action.decision is not None else None,
        "reason": action.reason.value if action.reason is not None else None,
    }


def _managed_study_status_payload(
    action_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any]:
    if isinstance(action_payload, StudyRuntimeStatus):
        return action_payload.to_dict()
    return dict(action_payload)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping_value(payload: Mapping[str, Any], key: str) -> Mapping[str, Any]:
    value = payload.get(key)
    return value if isinstance(value, Mapping) else {}


def _payload_active_run_id(payload: Mapping[str, Any]) -> str | None:
    continuation_state = _mapping_value(payload, "continuation_state")
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    autonomous_runtime_notice = _mapping_value(payload, "autonomous_runtime_notice")
    execution_owner_guard = _mapping_value(payload, "execution_owner_guard")
    for candidate in (
        payload.get("active_run_id"),
        continuation_state.get("active_run_id"),
        runtime_liveness_audit.get("active_run_id"),
        runtime_audit.get("active_run_id"),
        autonomous_runtime_notice.get("active_run_id"),
        execution_owner_guard.get("active_run_id"),
    ):
        active_run_id = _non_empty_text(candidate)
        if active_run_id is not None:
            return active_run_id
    return None


def _payload_runtime_liveness_status(payload: Mapping[str, Any]) -> str | None:
    runtime_liveness_audit = _mapping_value(payload, "runtime_liveness_audit")
    runtime_audit = _mapping_value(runtime_liveness_audit, "runtime_audit")
    return _non_empty_text(runtime_liveness_audit.get("status")) or _non_empty_text(runtime_audit.get("status"))


def _should_hard_auto_recover_managed_study(action_payload: dict[str, Any] | StudyRuntimeStatus) -> bool:
    payload = _managed_study_status_payload(action_payload)
    if _non_empty_text(payload.get("decision")) != "resume":
        return False
    if _non_empty_text(payload.get("quest_status")) not in _HARD_AUTO_RECOVERY_QUEST_STATUSES:
        return False
    if _non_empty_text(payload.get("reason")) not in _HARD_AUTO_RECOVERY_REASONS:
        return False
    if _payload_active_run_id(payload) is not None:
        return False
    return _payload_runtime_liveness_status(payload) != "live"


def _serialize_managed_study_auto_recovery(
    *,
    preflight_payload: dict[str, Any] | StudyRuntimeStatus,
    applied_payload: dict[str, Any] | StudyRuntimeStatus,
    source: str,
) -> dict[str, Any]:
    preflight = _serialize_managed_study_action(preflight_payload)
    applied = _serialize_managed_study_action(applied_payload)
    return {
        "study_id": applied.get("study_id") or preflight.get("study_id"),
        "preflight_decision": preflight.get("decision"),
        "preflight_reason": preflight.get("reason"),
        "applied_decision": applied.get("decision"),
        "applied_reason": applied.get("reason"),
        "source": source,
    }


def _write_latest_watch_alias(*, report_dir: Path, report: Mapping[str, Any], markdown: str) -> tuple[Path, Path]:
    latest_json = report_dir / "latest.json"
    latest_markdown = report_dir / "latest.md"
    report_dir.mkdir(parents=True, exist_ok=True)
    latest_json.write_text(json.dumps(dict(report), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    latest_markdown.write_text(markdown, encoding="utf-8")
    return latest_json, latest_markdown


def render_watch_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# Runtime Watch Report",
        "",
        f"- scanned_at: `{report['scanned_at']}`",
        f"- quest_root: `{report['quest_root']}`",
        f"- quest_status: `{report['quest_status']}`",
        "",
        "## Controllers",
        "",
    ]
    for name, item in (report.get("controllers") or {}).items():
        lines.extend(
            [
                f"### {name}",
                "",
                f"- status: `{item.get('status')}`",
                f"- action: `{item.get('action')}`",
                f"- blockers: `{', '.join(item.get('blockers') or ['none'])}`",
                f"- advisories: `{', '.join(item.get('advisories') or ['none'])}`",
                f"- report_json: `{item.get('report_json')}`",
                f"- report_markdown: `{item.get('report_markdown')}`",
                f"- suppression_reason: `{item.get('suppression_reason') or 'none'}`",
                "",
            ]
        )
        if name == "publication_gate" and item.get("supervisor_phase"):
            lines.extend(
                [
                    "#### Publication Supervisor",
                    "",
                    f"- supervisor_phase: `{item.get('supervisor_phase')}`",
                    f"- phase_owner: `{item.get('phase_owner')}`",
                    f"- upstream_scientific_anchor_ready: `{str(item.get('upstream_scientific_anchor_ready')).lower()}`",
                    f"- bundle_tasks_downstream_only: `{str(item.get('bundle_tasks_downstream_only')).lower()}`",
                    f"- current_required_action: `{item.get('current_required_action')}`",
                    f"- deferred_downstream_actions: `{', '.join(item.get('deferred_downstream_actions') or ['none'])}`",
                    f"- controller_stage_note: `{item.get('controller_stage_note')}`",
                    "",
                ]
            )
    return "\n".join(lines)


def write_watch_report(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path, Path, Path]:
    markdown = render_watch_markdown(report)
    json_path, md_path = runtime_watch_protocol.write_watch_report(
        quest_root=quest_root,
        report=report,
        markdown=markdown,
    )
    latest_json, latest_markdown = _write_latest_watch_alias(
        report_dir=json_path.parent,
        report=report,
        markdown=markdown,
    )
    return json_path, md_path, latest_json, latest_markdown


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
    managed_study_actions: list[dict[str, Any]] = []
    managed_study_statuses: list[tuple[Path, dict[str, Any]]] = []
    managed_study_auto_recoveries: list[dict[str, Any]] = []
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
            managed_study_actions.append(_serialize_managed_study_action(action_payload))
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
    managed_study_supervision: list[dict[str, Any]] = []
    for study_root, status_payload in managed_study_statuses:
        quest_root = status_payload.get("quest_root")
        quest_report = report_by_quest_root.get(str(Path(str(quest_root)).expanduser().resolve())) if quest_root else None
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
    return {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "runtime_root": str(runtime_root),
        "scanned_quests": scanned,
        "managed_study_actions": managed_study_actions,
        "managed_study_auto_recoveries": managed_study_auto_recoveries,
        "managed_study_supervision": managed_study_supervision,
        "reports": reports,
    }


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
