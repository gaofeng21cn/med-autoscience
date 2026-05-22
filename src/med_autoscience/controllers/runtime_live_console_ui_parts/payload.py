from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.progress_portal_parts import local_time_projection
from med_autoscience.controllers.runtime_live_console_ui_parts.constants import (
    BRAND,
    LIVE_CONSOLE_HTML_REF,
    LIVE_CONSOLE_PAYLOAD_REF,
    SCHEMA_VERSION,
    SURFACE_KIND,
)
from med_autoscience.controllers.runtime_live_console_ui_parts.shared import (
    dedupe,
    mapping,
    mapping_list,
    string_list,
    text,
    utc_now,
)
from med_autoscience.runtime_protocol import live_console_contract


def build_live_console_ui_payload(
    *,
    live_console_snapshot: Mapping[str, Any],
    generated_at: str | None = None,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    progress_portal_href: str = "../progress/index.html",
    stream_href: str | None = None,
    terminal_attach_owner: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    workspace = mapping(live_console_snapshot.get("workspace"))
    studies = _studies(live_console_snapshot.get("studies"))
    live_runs = mapping_list(live_console_snapshot.get("runs"))
    selected_study_id = text(study_id) or text(live_console_snapshot.get("selected_study_id"))
    scope = "study" if selected_study_id else "profile"
    generated = generated_at or utc_now()
    no_live_blockers = _no_live_blockers(studies)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "brand": BRAND,
        "generated_at": generated,
        "generated_at_local": local_time_projection(generated, timezone_name=None),
        "scope": scope,
        "selected_study_id": selected_study_id,
        "payload_ref": LIVE_CONSOLE_PAYLOAD_REF,
        "html_ref": LIVE_CONSOLE_HTML_REF,
        "authority": {
            "kind": "read_only_live_observation_shell",
            "read_only": True,
            "writes_authority_surface": False,
            "state_interpretation_owner": "runtime_session_read_model",
            "authority_note": (
                "Live Console renders MAS live observation payloads and does not own runtime, "
                "publication, controller, package, or study truth."
            ),
        },
        "portal_handoff": {
            "progress_portal_href": progress_portal_href,
            "relationship": "navigation_return_link",
            "portal_owns_live_console_state_interpretation": False,
        },
        "stream": {
            "href": stream_href,
            "mode": "read_only_observation",
            "writes_authority_surface": False,
        },
        "terminal_attach_gate": live_console_contract.terminal_attach_gate_status(
            owner_contract=terminal_attach_owner or mapping(live_console_snapshot.get("terminal_attach_owner")),
            profile_ref=profile_ref,
            study_id=selected_study_id,
            study_root=study_root,
        ),
        "workspace": {
            "profile_name": text(workspace.get("profile_name")) or "unknown",
            "workspace_root": text(workspace.get("workspace_root")) or "",
            "workspace_status": text(workspace.get("workspace_status")) or "unknown",
        },
        "studies": studies,
        "empty_state": _empty_state(
            mapping(live_console_snapshot.get("empty_state")),
            studies=studies,
            runs=live_runs,
            no_live_blockers=no_live_blockers,
        ),
        "controller_action_intents": mapping_list(live_console_snapshot.get("controller_action_intents")),
        "source_refs": _source_refs(studies),
    }


def _studies(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    studies: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        study_id = text(item.get("study_id"))
        if study_id is None:
            continue
        studies.append(
            {
                "study_id": study_id,
                "state_label": text(item.get("state_label")),
                "current_stage": text(item.get("current_stage")),
                "active_run_id": text(item.get("active_run_id")),
                "runtime_health_status": text(item.get("runtime_health_status")),
                "supervisor_tick_status": text(item.get("supervisor_tick_status")),
                "worker_running": item.get("worker_running") if isinstance(item.get("worker_running"), bool) else None,
                "runtime_observation_status": text(item.get("runtime_observation_status")),
                "blocking_reasons": string_list(item.get("blocking_reasons")),
                "canonical_runtime_action": text(item.get("canonical_runtime_action")),
                "allowed_controller_actions": string_list(item.get("allowed_controller_actions")),
                "next_action_summary": text(item.get("next_action_summary")),
                "runs": _runs(item.get("runs")),
                "timeline": _timeline(item.get("timeline")),
                "terminal_sources": _stream_sources(item.get("terminal_sources")),
                "log_sources": _stream_sources(item.get("log_sources")),
                "artifact_refs": string_list(item.get("artifact_refs")),
                "event_refs": string_list(item.get("event_refs")),
            }
        )
    return studies


def _runs(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    runs: list[dict[str, Any]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        run_id = text(item.get("run_id"))
        if run_id is None:
            continue
        last_seen = text(item.get("last_seen_at"))
        runs.append(
            {
                "run_id": run_id,
                "status": text(item.get("status")),
                "started_at": text(item.get("started_at")),
                "last_seen_at": last_seen,
                "last_seen_at_local": local_time_projection(last_seen, timezone_name=None) if last_seen else None,
            }
        )
    return runs


def _timeline(value: object) -> list[dict[str, str | None]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    events: list[dict[str, str | None]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        summary = text(item.get("summary")) or text(item.get("status")) or text(item.get("source_ref"))
        if summary is None:
            continue
        events.append(
            {
                "observed_at": text(item.get("observed_at")),
                "observed_at_local": mapping(item.get("local_time"))
                or (
                    local_time_projection(str(item.get("observed_at")), timezone_name=None)
                    if text(item.get("observed_at"))
                    else {}
                ),
                "topic": text(item.get("topic")),
                "summary": summary,
                "source_ref": text(item.get("source_ref")),
            }
        )
    return events


def _stream_sources(value: object) -> list[dict[str, object]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    sources: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, Mapping):
            continue
        source_ref = text(item.get("source_ref"))
        tail = string_list(item.get("tail"))
        if source_ref is None and not tail:
            continue
        sources.append(
            {
                "label": text(item.get("label")) or _stream_label_for_source(item),
                "source_ref": source_ref,
                "status": text(item.get("status")) or "unknown",
                "tail": tail,
            }
        )
    return sources


def _source_refs(studies: list[dict[str, Any]]) -> list[str]:
    refs: list[str] = []
    for study in studies:
        for event in study.get("timeline") or []:
            if isinstance(event, Mapping):
                refs.append(str(event.get("source_ref") or ""))
        for key in ("terminal_sources", "log_sources"):
            for source in study.get(key) or []:
                if isinstance(source, Mapping):
                    refs.append(str(source.get("source_ref") or ""))
        refs.extend(string_list(study.get("artifact_refs")))
        refs.extend(string_list(study.get("event_refs")))
    return dedupe(refs)


def _stream_label_for_source(item: Mapping[str, Any]) -> str:
    source_ref = text(item.get("source_ref")) or text(item.get("path")) or ""
    if "worker.log" in source_ref or "/logs/" in source_ref:
        return "worker 日志"
    if "bash_exec" in source_ref or "stdout" in source_ref or "terminal" in source_ref:
        return "终端摘要"
    return "来源"


def _empty_state(
    explicit: Mapping[str, Any],
    *,
    studies: list[dict[str, Any]],
    runs: list[dict[str, Any]],
    no_live_blockers: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if explicit:
        return dict(explicit)
    if runs:
        return None
    if not studies:
        return {
            "reason": "no_studies",
            "summary": "当前 profile 没有发现可展示的 study。",
            "next_action": "确认 workspace profile 和 studies root。",
        }
    return {
        "reason": "no_live_run",
        "summary": "当前没有 live run；terminal/log 缺失是运行状态证据，而不是页面加载失败。",
        "study_count": len(studies),
        "study_blockers": no_live_blockers,
        "next_action": "回到 Progress Portal 查看 blocker，必要时通过 MAS controller 请求 reconcile。",
    }


def _no_live_blockers(studies: list[dict[str, Any]]) -> list[dict[str, Any]]:
    blockers: list[dict[str, Any]] = []
    for study in studies:
        if study.get("active_run_id"):
            continue
        reasons = string_list(study.get("blocking_reasons"))
        action = text(study.get("canonical_runtime_action"))
        health = text(study.get("runtime_health_status"))
        if (
            not reasons
            and action not in {"external_supervisor_required", "await_explicit_resume"}
            and health not in {"escalated", "parked", "missing", "none"}
        ):
            continue
        blockers.append(
            {
                "study_id": study.get("study_id"),
                "runtime_health_status": health,
                "blocking_reasons": reasons,
                "canonical_runtime_action": action,
                "next_action_summary": study.get("next_action_summary"),
            }
        )
    return blockers


__all__ = ["build_live_console_ui_payload"]
