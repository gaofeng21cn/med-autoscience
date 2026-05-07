from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import (
    data_asset_gate,
    figure_loop_guard,
    medical_literature_audit,
    medical_publication_surface,
    medical_reporting_audit,
    publication_gate,
)
from med_autoscience.controllers.runtime_watch_parts.fingerprints import build_fingerprint
from med_autoscience.controllers.runtime_watch_parts.reporting import (
    _attach_family_companion_to_quest_report,
    write_watch_report,
)
from med_autoscience.controllers.study_progress_parts.runtime_efficiency import (
    _latest_run_telemetry_surface,
)
from med_autoscience.publication_eval_latest import read_publication_eval_latest
from med_autoscience.runtime_protocol import quest_state
from med_autoscience.runtime_protocol import runtime_watch as runtime_watch_protocol
from med_autoscience.runtime_protocol.topology import resolve_paper_root_context


ControllerRunner = Callable[..., dict[str, Any]]
PublicationGateRefreshMask = Callable[..., bool]

DEFAULT_CONTROLLER_ORDER: tuple[str, ...] = (
    "data_asset_gate",
    "medical_publication_surface",
    "publication_gate",
    "medical_literature_audit",
    "medical_reporting_audit",
    "figure_loop_guard",
)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


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


def _publication_gate_ai_reviewer_eval_masks_return_to_gate(*, dry_run_result: dict[str, Any]) -> bool:
    if str(dry_run_result.get("status") or "").strip() != "blocked":
        return False
    if str(dry_run_result.get("current_required_action") or "").strip() != "return_to_publishability_gate":
        return False
    report_path_text = _non_empty_text(dry_run_result.get("report_json"))
    if report_path_text is None:
        return False
    report_path = Path(report_path_text)
    if not report_path.exists():
        return False
    try:
        report_payload = json.loads(report_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if str(report_payload.get("gate_kind") or "").strip() != "publishability_control":
        return False
    paper_root_text = _non_empty_text(report_payload.get("paper_root"))
    if paper_root_text is None:
        return False
    try:
        paper_context = resolve_paper_root_context(Path(paper_root_text))
        publication_eval = read_publication_eval_latest(study_root=paper_context.study_root)
    except (FileNotFoundError, ValueError, OSError, json.JSONDecodeError, TypeError):
        return False
    provenance = publication_eval.get("assessment_provenance")
    if not isinstance(provenance, Mapping):
        return False
    return (
        str(provenance.get("owner") or "").strip() == "ai_reviewer"
        and provenance.get("ai_reviewer_required") is False
    )


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


def run_watch_for_quest(
    *,
    quest_root: Path,
    controller_runners: dict[str, ControllerRunner] | None = None,
    apply: bool,
    publication_gate_refresh_mask: PublicationGateRefreshMask = _publication_gate_ai_reviewer_eval_masks_return_to_gate,
) -> dict[str, Any]:
    controller_runners = controller_runners or build_default_controller_runners()
    current_state = runtime_watch_protocol.load_watch_state(quest_root)
    controller_state = dict(current_state.controllers)
    report: dict[str, Any] = {
        "schema_version": 1,
        "scanned_at": _utc_now(),
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
        if name == "publication_gate" and publication_gate_refresh_mask(dry_run_result=dry_run_result):
            fingerprint = f"{fingerprint}:refresh-publication-eval-from-return-to-gate"
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


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


__all__ = [
    "DEFAULT_CONTROLLER_ORDER",
    "ControllerRunner",
    "_invoke_controller_runner",
    "_publication_gate_ai_reviewer_eval_masks_return_to_gate",
    "build_default_controller_runners",
    "iter_ordered_controller_runners",
    "run_watch_for_quest",
]
