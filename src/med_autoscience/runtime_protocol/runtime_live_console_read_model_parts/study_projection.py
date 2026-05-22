from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import live_console_observation
from med_autoscience.runtime_protocol import live_console_read_model_io as io
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import context_projection
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import stream_projection


def workspace_projection(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = [context_projection.study_health_status(context) for context in study_contexts]
    if any(status in {"recovering", "stale", "blocked", "missing", "escalated"} for status in statuses):
        workspace_status = "attention_required"
    elif statuses:
        workspace_status = "active"
    else:
        workspace_status = "empty"
    return {
        "profile_name": profile.name,
        "workspace_root": str(profile.workspace_root),
        "profile_ref": str(profile_ref) if profile_ref is not None else None,
        "workspace_status": workspace_status,
        "study_count": len(study_contexts),
    }


def study_projection(context: Mapping[str, Any], *, selected_study_id: str | None) -> dict[str, Any]:
    study_id = str(context["study_id"])
    cockpit_item = _cockpit_study_item(context, study_id=study_id)
    progress = context_projection.surface_payload(context, "study_progress")
    status = context_projection.surface_payload(context, "study_runtime_status")
    summary = context_projection.surface_payload(context, "runtime_status_summary")
    health = context_projection.surface_payload(context, "runtime_health")
    supervision = context_projection.surface_payload(context, "runtime_supervision")
    user_visible = context_projection.mapping(progress.get("user_visible_projection"))
    active_run_id = context_projection.active_run_id(status=status, health=health, supervision=supervision)
    worker_running = context_projection.worker_running(status=status, health=health)
    health_status = context_projection.study_health_status(context)
    canonical_action = io.first_text(health.get("canonical_runtime_action"))
    state_label = io.first_text(
        user_visible.get("state_label"),
        progress.get("state_label"),
        cockpit_item.get("state_label"),
        status.get("quest_status"),
        health.get("health_status"),
    )
    current_stage = io.first_text(
        user_visible.get("current_stage"),
        progress.get("current_stage"),
        cockpit_item.get("current_stage"),
    )
    return {
        "study_id": study_id,
        "study_root": str(context["study_root"]),
        "selected": selected_study_id is not None and study_id == selected_study_id,
        "state_label": state_label
        or _derived_state_label(
            active_run_id=active_run_id,
            worker_running=worker_running,
            health_status=health_status,
            canonical_action=canonical_action,
        ),
        "current_stage": current_stage
        or _derived_current_stage(
            active_run_id=active_run_id,
            worker_running=worker_running,
            health_status=health_status,
            canonical_action=canonical_action,
        ),
        "paper_stage": io.first_text(user_visible.get("paper_stage"), progress.get("paper_stage"), cockpit_item.get("paper_stage")),
        "quest_id": io.first_text(status.get("quest_id"), summary.get("quest_id")),
        "active_run_id": active_run_id,
        "runtime_health_status": health_status,
        "supervisor_tick_status": io.first_text(
            supervision.get("supervisor_tick_status"),
            context_projection.mapping(health.get("supervisor_state")).get("status"),
            summary.get("supervisor_tick_status"),
            "missing" if not supervision else None,
        ),
        "worker_running": worker_running,
        "runtime_observation_status": live_console_observation.runtime_observation_status(
            active_run_id=active_run_id,
            worker_running=worker_running,
        ),
        "blocking_reasons": context_projection.string_list(health.get("blocking_reasons")),
        "canonical_runtime_action": canonical_action,
        "allowed_controller_actions": context_projection.string_list(health.get("allowed_controller_actions")),
        "next_action_summary": io.first_text(
            supervision.get("next_action_summary"),
            supervision.get("next_action"),
            cockpit_item.get("next_system_action"),
        ),
        "runs": [
            {
                "run_id": active_run_id,
                "status": health_status,
                "last_seen_at": io.first_text(status.get("last_seen_at"), health.get("last_seen_at")),
            }
        ]
        if active_run_id
        else [],
        "timeline": study_timeline(context),
        "terminal_sources": [context_projection.surface(context, "terminal_tail")],
        "log_sources": [context_projection.surface(context, "log_tail")],
        "artifact_refs": artifact_refs(context),
        "event_refs": event_refs(context),
    }


def runs(study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for context in study_contexts:
        status = context_projection.surface_payload(context, "study_runtime_status")
        health = context_projection.surface_payload(context, "runtime_health")
        supervision = context_projection.surface_payload(context, "runtime_supervision")
        active_run_id = context_projection.active_run_id(status=status, health=health, supervision=supervision)
        if active_run_id is None:
            continue
        result.append(
            {
                "study_id": str(context["study_id"]),
                "quest_id": io.first_text(
                    status.get("quest_id"),
                    context_projection.surface_payload(context, "runtime_status_summary").get("quest_id"),
                ),
                "active_run_id": active_run_id,
                "status": context_projection.study_health_status(context),
                "worker_running": context_projection.worker_running(status=status, health=health),
            }
        )
    return result


def workspace_source_refs(study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for context in study_contexts:
        for surface_kind, surface in context_projection.mapping(context.get("surfaces")).items():
            if not isinstance(surface, Mapping):
                continue
            ref = str(surface.get("path") or surface.get("source_ref") or "")
            if not ref:
                continue
            key = (str(surface_kind), ref)
            if key in seen:
                continue
            seen.add(key)
            refs.append(
                {
                    "surface_kind": str(surface_kind),
                    "study_id": str(context["study_id"]),
                    "source_ref": ref,
                    "status": "available" if surface.get("status") != "missing" else "missing",
                    "legacy_role": legacy_role(ref),
                }
            )
    return refs


def legacy_role(ref: str) -> str | None:
    if "/.ds/" in ref or "med-deepscientist" in ref:
        return "legacy_provenance"
    return None


def study_timeline(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in stream_projection.events(generated_at=_utc_now(), study_contexts=[context])
        if event.get("study_id") == str(context["study_id"])
    ]


def artifact_refs(context: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("runtime_health", "runtime_supervision", "runtime_status_summary"):
        path = context_projection.surface_path_text(context, key)
        if path:
            refs.append(path)
    return sorted(dict.fromkeys(refs))


def event_refs(context: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("study_runtime_status", "study_progress"):
        path = context_projection.surface_path_text(context, key)
        if path:
            refs.append(path)
    return sorted(dict.fromkeys(refs))


def _cockpit_study_item(context: Mapping[str, Any], *, study_id: str) -> dict[str, Any]:
    cockpit = context_projection.surface_payload(context, "workspace_cockpit")
    studies = cockpit.get("studies")
    if not isinstance(studies, list):
        return {}
    for item in studies:
        if not isinstance(item, Mapping):
            continue
        if io.text(item.get("study_id")) == study_id:
            return dict(item)
    return {}


def _derived_state_label(
    *,
    active_run_id: str | None,
    worker_running: bool,
    health_status: str,
    canonical_action: str | None,
) -> str:
    if active_run_id and worker_running:
        return "运行中"
    if canonical_action == "external_supervisor_required" or health_status == "escalated":
        return "需要外层 supervisor"
    if canonical_action == "await_explicit_resume" or health_status in {"parked", "awaiting_explicit_resume"}:
        return "等待显式恢复"
    if active_run_id:
        return "有 run 投影但 worker 未确认"
    return "无 live run"


def _derived_current_stage(
    *,
    active_run_id: str | None,
    worker_running: bool,
    health_status: str,
    canonical_action: str | None,
) -> str:
    if active_run_id and worker_running:
        return "runtime_live"
    if canonical_action == "external_supervisor_required" or health_status == "escalated":
        return "runtime_repair_required"
    if canonical_action == "await_explicit_resume" or health_status in {"parked", "awaiting_explicit_resume"}:
        return "awaiting_explicit_resume"
    if active_run_id:
        return "run_projection_without_worker"
    return "no_live_run"


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "artifact_refs",
    "event_refs",
    "legacy_role",
    "runs",
    "study_projection",
    "study_timeline",
    "workspace_projection",
    "workspace_source_refs",
]
