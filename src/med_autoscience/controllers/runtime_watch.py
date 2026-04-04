from __future__ import annotations

import argparse
import hashlib
import json
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
    study_runtime_router,
)
from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol


ControllerRunner = Callable[..., dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def build_default_controller_runners() -> dict[str, ControllerRunner]:
    return {
        "data_asset_gate": data_asset_gate.run_controller,
        "publication_gate": publication_gate.run_controller,
        "medical_publication_surface": medical_publication_surface.run_controller,
        "medical_literature_audit": medical_literature_audit.run_controller,
        "medical_reporting_audit": medical_reporting_audit.run_controller,
        "figure_loop_guard": figure_loop_guard.run_controller,
    }


def build_fingerprint(controller_name: str, result: dict[str, Any]) -> str:
    if controller_name == "publication_gate":
        payload = {
            "status": result.get("status"),
            "allow_write": result.get("allow_write"),
            "blockers": result.get("blockers") or [],
            "missing_non_scalar_deliverables": result.get("missing_non_scalar_deliverables") or [],
            "submission_minimal_present": result.get("submission_minimal_present"),
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
    return "\n".join(lines)


def write_watch_report(quest_root: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    return runtime_watch_protocol.write_watch_report(
        quest_root=quest_root,
        report=report,
        markdown=render_watch_markdown(report),
    )


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

    for name, runner in controller_runners.items():
        dry_run_result = _invoke_controller_runner(runner, quest_root=quest_root, apply=False)
        fingerprint = build_fingerprint(name, dry_run_result)
        previous = controller_state.get(name) or runtime_watch_protocol.RuntimeWatchControllerState()
        intervention_statuses = {"blocked"}
        if name == "data_asset_gate":
            intervention_statuses.add("advisory")
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
        controller_state[name] = plan.controller_state
        status = dry_run_result.get("status")
        suppression_reason = plan.suppression_reason
        report["controllers"][name] = {
            "status": status,
            "action": plan.action.value,
            "blockers": dry_run_result.get("blockers") or [],
            "advisories": dry_run_result.get("advisories") or [],
            "report_json": final_result.get("report_json"),
            "report_markdown": final_result.get("report_markdown"),
            "suppression_reason": suppression_reason,
        }

    runtime_watch_protocol.save_watch_state(
        quest_root=quest_root,
        payload=runtime_watch_protocol.RuntimeWatchState(
            schema_version=1,
            updated_at=report["scanned_at"],
            controllers=controller_state,
        ),
    )
    json_path, md_path = write_watch_report(quest_root, report)
    report["report_json"] = str(json_path)
    report["report_markdown"] = str(md_path)
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
            managed_study_actions.append(_serialize_managed_study_action(action_payload))
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
    return {
        "schema_version": 1,
        "scanned_at": utc_now(),
        "runtime_root": str(runtime_root),
        "scanned_quests": scanned,
        "managed_study_actions": managed_study_actions,
        "reports": reports,
    }


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
