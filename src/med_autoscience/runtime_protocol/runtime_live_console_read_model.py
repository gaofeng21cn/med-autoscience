from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.progress_portal_parts import local_time_projection
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import (
    live_console_contract,
    live_console_observation,
    live_console_read_model_io as io,
    runtime_session_read_model,
)


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_live_console_read_model"
SESSION_SURFACE_KIND = "mas_live_console_session_read_model"
STREAM_SURFACE_KIND = "mas_live_console_stream"
OWNER = "MedAutoScience"
LIVE_CONSOLE_READ_MODEL_REF = "artifacts/runtime/live_console/session_read_model/latest.json"
LIVE_CONSOLE_READ_MODEL_HISTORY_REF = "artifacts/runtime/live_console/session_read_model/history.jsonl"
STREAM_TOPICS = io.STREAM_TOPICS


def build_live_console_session_read_model(
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = io.text(generated_at) or _utc_now()
    selected_study_id, selected_study_root = _resolve_selection(
        profile=profile,
        study_id=study_id,
        study_root=study_root,
    )
    contexts = _study_contexts(
        profile=profile,
        selected_study_id=selected_study_id,
        selected_study_root=selected_study_root,
    )
    studies = [_study_projection(context, selected_study_id=selected_study_id) for context in contexts]
    runs = _runs(contexts)
    return {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SESSION_SURFACE_KIND,
        "owner": OWNER,
        "generated_at": generated,
        "generated_at_local": local_time_projection(generated, timezone_name=None),
        "authority": {
            "kind": "read_model_display_artifact",
            "mode": "read_only",
            "writes_authority_surface": False,
            "can_write_paper_or_package": False,
        },
        "workspace": _workspace_projection(
            profile=profile,
            profile_ref=profile_ref,
            study_contexts=contexts,
        ),
        "studies": studies,
        "selected_study_id": selected_study_id,
        "runs": runs,
        "empty_state": live_console_observation.empty_state(studies, runs),
        "stream_sources": _stream_sources(contexts),
        "events": _events(generated_at=generated, study_contexts=contexts),
        "controller_action_intents": _controller_action_intents(
            profile_ref=profile_ref,
            selected_study_id=selected_study_id,
        ),
        "source_refs": _workspace_source_refs(contexts),
    }


def materialize_live_console_session_read_model(
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    payload = build_live_console_session_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        generated_at=generated_at,
    )
    latest_path = (profile.workspace_root / LIVE_CONSOLE_READ_MODEL_REF).resolve()
    history_path = (profile.workspace_root / LIVE_CONSOLE_READ_MODEL_HISTORY_REF).resolve()
    io.write_json(latest_path, payload)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")
    return {
        "status": "materialized",
        "surface_kind": SESSION_SURFACE_KIND,
        "read_only": True,
        "payload_path": str(latest_path),
        "read_model_ref": str(latest_path),
        "session_read_model": payload,
        "history_path": str(history_path),
        "generated_at": payload["generated_at"],
    }


def live_console_stream_snapshot(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
    interval_seconds: int = 30,
) -> dict[str, Any]:
    materialized = materialize_live_console_session_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        generated_at=generated_at,
    )
    return {
        "status": "snapshot",
        "surface_kind": STREAM_SURFACE_KIND,
        "url": f"http://{host}:{int(port)}/events" if int(port) > 0 else f"http://{host}:0/events",
        "host": host,
        "port": int(port),
        "interval_seconds": max(1, int(interval_seconds)),
        "read_only": True,
        "payload_path": materialized["payload_path"],
        "history_path": materialized["history_path"],
        "generated_at": materialized["generated_at"],
        "session_read_model": materialized["session_read_model"],
        "events": _stream_events(materialized),
    }


def build_live_console_read_model(
    *,
    profile_name: str | None = None,
    workspace_root: str | Path | None = None,
    study_id: str | None = None,
    study_runtime_status: Mapping[str, Any] | None = None,
    study_runtime_status_path: Path | None = None,
    study_root: Path | None = None,
    quest_root: Path | None = None,
    db_path: Path | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    runtime_health_path: Path | None = None,
    runtime_supervision: Mapping[str, Any] | None = None,
    runtime_supervision_path: Path | None = None,
    terminal_sources: Sequence[Mapping[str, Any]] | None = None,
    log_sources: Sequence[Mapping[str, Any]] | None = None,
    artifact_delta: Mapping[str, Any] | None = None,
    generated_at: str | None = None,
    freshness_ttl_seconds: int | None = None,
    tail_limit: int = 120,
) -> dict[str, Any]:
    generated = io.text(generated_at) or _utc_now()
    resolved_workspace_root = Path(workspace_root).expanduser().resolve() if workspace_root is not None else None
    session_projection = runtime_session_read_model.build_runtime_session_read_model(
        study_runtime_status=study_runtime_status,
        study_runtime_status_path=study_runtime_status_path,
        study_root=study_root,
        quest_root=quest_root,
        db_path=db_path,
        generated_at=generated,
        freshness_ttl_seconds=freshness_ttl_seconds,
    )
    session = dict(session_projection["runtime_session"])
    resolved_study_id = io.first_text(study_id, session.get("study_id"))
    terminal = io.normalize_sources(terminal_sources, limit=tail_limit)
    logs = io.normalize_sources(log_sources, limit=tail_limit)
    health = io.load_payload(runtime_health, runtime_health_path)
    supervision = io.load_payload(runtime_supervision, runtime_supervision_path)
    artifact_payload = dict(artifact_delta or {})
    read_model = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "read_only": True,
        "generated_at": generated,
        "authority": live_console_contract.authority(),
        "workspace": {
            "profile_name": io.text(profile_name),
            "workspace_root": str(resolved_workspace_root) if resolved_workspace_root is not None else None,
        },
        "study": {
            "study_id": resolved_study_id,
            "quest_id": io.first_text(session.get("quest_id"), Path(quest_root).name if quest_root is not None else None),
        },
        "session": session,
        "runtime_health": health,
        "runtime_supervision": supervision,
        "terminal_sources": terminal,
        "log_sources": logs,
        "artifact_delta": artifact_payload,
        "stream_topics": io.stream_topics(terminal=terminal, logs=logs, artifact_delta=artifact_payload),
        "controller_action_links": live_console_contract.controller_action_links(study_id=resolved_study_id),
        "source_refs": live_console_contract.source_refs(
            session=session,
            runtime_health_path=runtime_health_path,
            runtime_supervision_path=runtime_supervision_path,
            terminal=terminal,
            logs=logs,
            artifact_delta=artifact_payload,
        ),
    }
    return read_model


def materialize_live_console_read_model(
    *,
    workspace_root: str | Path,
    profile_name: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    root = Path(workspace_root).expanduser().resolve()
    read_model = build_live_console_read_model(
        workspace_root=root,
        profile_name=profile_name,
        **kwargs,
    )
    latest_path = root / LIVE_CONSOLE_READ_MODEL_REF
    io.write_json(latest_path, read_model)
    return {
        "ok": True,
        "surface_kind": "mas_live_console_materialization",
        "read_model_ref": str(latest_path),
        "read_model": read_model,
    }


def build_live_console_stream_events(read_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    generated_at = io.text(read_model.get("generated_at")) or _utc_now()
    candidates: list[tuple[str, str, object]] = [
        ("workspace.status", "live_console.workspace", read_model.get("workspace")),
        ("study.status", "live_console.study", read_model.get("study")),
        ("runtime.health", "live_console.runtime_health", read_model.get("runtime_health")),
        ("runtime.supervision", "live_console.runtime_supervision", read_model.get("runtime_supervision")),
        (
            "terminal.tail",
            live_console_contract.first_source_ref(read_model.get("terminal_sources")) or "live_console.terminal",
            read_model.get("terminal_sources"),
        ),
        (
            "log.tail",
            live_console_contract.first_source_ref(read_model.get("log_sources")) or "live_console.log",
            read_model.get("log_sources"),
        ),
        (
            "artifact.delta",
            live_console_contract.artifact_source_ref(read_model.get("artifact_delta")) or "live_console.artifact_delta",
            read_model.get("artifact_delta"),
        ),
    ]
    events: list[dict[str, Any]] = []
    for sequence, (topic, source_ref, payload) in enumerate(candidates, start=1):
        events.append(
            {
                "schema_version": SCHEMA_VERSION,
                "sequence": sequence,
                "topic": topic,
                "source_ref": source_ref,
                "observed_at": generated_at,
                "read_only": True,
                "payload": payload if payload is not None else {},
            }
        )
    return events


def _resolve_selection(
    *,
    profile: WorkspaceProfile,
    study_id: str | None,
    study_root: str | Path | None,
) -> tuple[str | None, Path | None]:
    if io.text(study_id) and study_root is not None:
        raise ValueError("Specify only one of study_id or study_root")
    if study_root is not None:
        root = Path(study_root).expanduser().resolve()
        return root.name, root
    selected = io.text(study_id) or None
    if selected is None:
        return None, None
    return selected, (profile.studies_root / selected).expanduser().resolve()


def _study_contexts(
    *,
    profile: WorkspaceProfile,
    selected_study_id: str | None,
    selected_study_root: Path | None,
) -> list[dict[str, Any]]:
    roots = _discover_study_roots(profile)
    if selected_study_root is not None and selected_study_root not in roots:
        roots.append(selected_study_root)
    contexts = [_study_context(profile=profile, study_root=root) for root in sorted(set(roots))]
    if selected_study_id is None:
        return contexts
    return [context for context in contexts if context["study_id"] == selected_study_id]


def _discover_study_roots(profile: WorkspaceProfile) -> list[Path]:
    studies_root = profile.studies_root.expanduser().resolve()
    if not studies_root.exists():
        return []
    return [path.resolve() for path in studies_root.iterdir() if path.is_dir() and (path / "study.yaml").exists()]


def _study_context(*, profile: WorkspaceProfile, study_root: Path) -> dict[str, Any]:
    study_id = study_root.name
    cockpit_path, cockpit = io.read_first_json(
        (
            profile.workspace_root / "artifacts" / "workspace_cockpit" / "latest.json",
            profile.workspace_root / "artifacts" / "runtime" / "workspace_cockpit" / "latest.json",
        )
    )
    progress_path, progress = io.read_first_json(
        (
            study_root / "artifacts" / "study_progress" / "latest.json",
            study_root / "artifacts" / "runtime" / "study_progress" / "latest.json",
            study_root / "artifacts" / "progress" / "latest.json",
        )
    )
    runtime_status_path, runtime_status = io.read_first_json(
        (
            study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status.json",
        )
    )
    summary_path, summary = io.read_first_json((study_root / "artifacts" / "runtime" / "runtime_status_summary.json",))
    health_path, health = io.read_first_json((study_root / "artifacts" / "runtime" / "health" / "latest.json",))
    supervision_path, supervision = io.read_first_json(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",)
    )
    quest_root = _quest_root(profile=profile, runtime_status=runtime_status, summary=summary)
    return {
        "study_id": io.first_text(
            runtime_status.get("study_id"),
            progress.get("study_id"),
            summary.get("study_id"),
            health.get("study_id"),
            supervision.get("study_id"),
            study_id,
        ),
        "study_root": study_root,
        "quest_root": quest_root,
        "surfaces": {
            "workspace_cockpit": {"path": cockpit_path, "payload": cockpit},
            "study_progress": {"path": progress_path, "payload": progress},
            "study_runtime_status": {"path": runtime_status_path, "payload": runtime_status},
            "runtime_status_summary": {"path": summary_path, "payload": summary},
            "runtime_health": {"path": health_path, "payload": health},
            "runtime_supervision": {"path": supervision_path, "payload": supervision},
            "terminal_tail": io.terminal_source(quest_root=quest_root),
            "log_tail": io.log_source(quest_root=quest_root),
        },
    }


def _quest_root(
    *,
    profile: WorkspaceProfile,
    runtime_status: Mapping[str, Any],
    summary: Mapping[str, Any],
) -> Path | None:
    for value in (
        runtime_status.get("quest_root"),
        runtime_status.get("runtime_artifact_ref"),
        summary.get("runtime_artifact_ref"),
    ):
        text = io.text(value)
        if not text:
            continue
        candidate = Path(text).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    quest_id = io.first_text(runtime_status.get("quest_id"), summary.get("quest_id"))
    if quest_id is None:
        return None
    return (profile.runtime_root / quest_id).expanduser().resolve()


def _workspace_projection(
    *,
    profile: WorkspaceProfile,
    profile_ref: str | Path | None,
    study_contexts: list[dict[str, Any]],
) -> dict[str, Any]:
    statuses = [_study_health_status(context) for context in study_contexts]
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


def _study_projection(context: Mapping[str, Any], *, selected_study_id: str | None) -> dict[str, Any]:
    study_id = str(context["study_id"])
    cockpit_item = _cockpit_study_item(context, study_id=study_id)
    progress = _surface_payload(context, "study_progress")
    status = _surface_payload(context, "study_runtime_status")
    summary = _surface_payload(context, "runtime_status_summary")
    health = _surface_payload(context, "runtime_health")
    supervision = _surface_payload(context, "runtime_supervision")
    user_visible = _mapping(progress.get("user_visible_projection"))
    active_run_id = _active_run_id(status=status, health=health, supervision=supervision)
    worker_running = _worker_running(status=status, health=health)
    health_status = _study_health_status(context)
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
            _mapping(health.get("supervisor_state")).get("status"),
            summary.get("supervisor_tick_status"),
            "missing" if not supervision else None,
        ),
        "worker_running": worker_running,
        "runtime_observation_status": live_console_observation.runtime_observation_status(
            active_run_id=active_run_id,
            worker_running=worker_running,
        ),
        "blocking_reasons": _string_list(health.get("blocking_reasons")),
        "canonical_runtime_action": canonical_action,
        "allowed_controller_actions": _string_list(health.get("allowed_controller_actions")),
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
        "timeline": _study_timeline(context),
        "terminal_sources": [_surface(context, "terminal_tail")],
        "log_sources": [_surface(context, "log_tail")],
        "artifact_refs": _artifact_refs(context),
        "event_refs": _event_refs(context),
    }


def _runs(study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for context in study_contexts:
        status = _surface_payload(context, "study_runtime_status")
        health = _surface_payload(context, "runtime_health")
        supervision = _surface_payload(context, "runtime_supervision")
        active_run_id = _active_run_id(status=status, health=health, supervision=supervision)
        if active_run_id is None:
            continue
        runs.append(
            {
                "study_id": str(context["study_id"]),
                "quest_id": io.first_text(status.get("quest_id"), _surface_payload(context, "runtime_status_summary").get("quest_id")),
                "active_run_id": active_run_id,
                "status": _study_health_status(context),
                "worker_running": _worker_running(status=status, health=health),
            }
        )
    return runs


def _cockpit_study_item(context: Mapping[str, Any], *, study_id: str) -> dict[str, Any]:
    cockpit = _surface_payload(context, "workspace_cockpit")
    studies = cockpit.get("studies")
    if not isinstance(studies, list):
        return {}
    for item in studies:
        if not isinstance(item, Mapping):
            continue
        if io.text(item.get("study_id")) == study_id:
            return dict(item)
    return {}


def _stream_sources(study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for context in study_contexts:
        study_id = str(context["study_id"])
        result.extend(
            [
                _stream_source(topic="terminal.tail", study_id=study_id, source=_surface(context, "terminal_tail")),
                _stream_source(topic="log.tail", study_id=study_id, source=_surface(context, "log_tail")),
                _artifact_delta_source(context),
            ]
        )
    return result


def _stream_source(*, topic: str, study_id: str, source: Mapping[str, Any]) -> dict[str, Any]:
    status = io.first_text(source.get("status"), "missing")
    payload = {
        "topic": topic,
        "study_id": study_id,
        "status": status,
        "label": "终端摘要" if topic == "terminal.tail" else "worker 日志",
        "source_ref": source.get("source_ref"),
        "source_status": status,
        "read_only": True,
    }
    if source.get("tail"):
        payload["tail"] = list(source["tail"])
    return payload


def _artifact_delta_source(context: Mapping[str, Any]) -> dict[str, Any]:
    health = _surface_payload(context, "runtime_health")
    artifact_delta = _mapping(health.get("artifact_delta"))
    status = io.first_text(artifact_delta.get("status"), "missing")
    return {
        "topic": "artifact.delta",
        "study_id": str(context["study_id"]),
        "status": status,
        "label": "产物增量",
        "source_ref": _surface_path_text(context, "runtime_health"),
        "source_status": "available" if health else "missing",
        "latest_meaningful_delta_at": io.text(artifact_delta.get("latest_meaningful_delta_at")),
        "artifact_kind": io.text(artifact_delta.get("artifact_kind")),
        "read_only": True,
    }


def _events(*, generated_at: str, study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = [
        _event(
            sequence=1,
            topic="workspace.status",
            study_id=None,
            status="projected",
            source_ref="workspace",
            observed_at=generated_at,
        )
    ]
    for context in study_contexts:
        study_id = str(context["study_id"])
        health = _surface_payload(context, "runtime_health")
        supervision = _surface_payload(context, "runtime_supervision")
        for topic, status, source_ref in (
            (
                "study.status",
                io.first_text(_surface_payload(context, "study_runtime_status").get("quest_status"), "missing"),
                _surface_path_text(context, "study_runtime_status"),
            ),
            ("runtime.health", _study_health_status(context), _surface_path_text(context, "runtime_health")),
            (
                "runtime.supervision",
                io.first_text(supervision.get("supervisor_tick_status"), "missing"),
                _surface_path_text(context, "runtime_supervision"),
            ),
        ):
            events.append(
                _event(
                    sequence=len(events) + 1,
                    topic=topic,
                    study_id=study_id,
                    status=status,
                    source_ref=source_ref,
                    observed_at=generated_at,
                )
            )
        artifact_delta = _mapping(health.get("artifact_delta"))
        events.append(
            _event(
                sequence=len(events) + 1,
                topic="artifact.delta",
                study_id=study_id,
                status=io.first_text(artifact_delta.get("status"), "missing"),
                source_ref=_surface_path_text(context, "runtime_health"),
                observed_at=generated_at,
            )
        )
        for stream in (
            _stream_source(topic="terminal.tail", study_id=study_id, source=_surface(context, "terminal_tail")),
            _stream_source(topic="log.tail", study_id=study_id, source=_surface(context, "log_tail")),
        ):
            events.append(
                _event(
                    sequence=len(events) + 1,
                    topic=str(stream["topic"]),
                    study_id=study_id,
                    status=str(stream["status"]),
                    source_ref=io.text(stream.get("source_ref")),
                    observed_at=generated_at,
                )
            )
    return events


def _event(
    *,
    sequence: int,
    topic: str,
    study_id: str | None,
    status: str | None,
    source_ref: str | None,
    observed_at: str,
) -> dict[str, Any]:
    return {
        "sequence": sequence,
        "topic": topic,
        "study_id": study_id,
        "status": status or "missing",
        "source_ref": source_ref,
        "observed_at": observed_at,
        "local_time": local_time_projection(observed_at, timezone_name=None),
    }


def _stream_events(materialized: Mapping[str, Any]) -> list[dict[str, Any]]:
    payload_path = io.text(materialized.get("payload_path")) or LIVE_CONSOLE_READ_MODEL_REF
    model = _mapping(materialized.get("session_read_model"))
    events: list[dict[str, Any]] = []
    for event in model.get("events") if isinstance(model.get("events"), list) else []:
        if not isinstance(event, Mapping):
            continue
        projected = dict(event)
        source_ref = io.text(projected.get("source_ref"))
        projected["source_ref"] = payload_path if source_ref in {None, "workspace"} else source_ref
        events.append(projected)
    return events


def _controller_action_intents(
    *,
    profile_ref: str | Path | None,
    selected_study_id: str | None,
) -> list[dict[str, Any]]:
    profile_arg = str(profile_ref) if profile_ref is not None else "<profile>"
    study_arg = f" --study-id {selected_study_id}" if selected_study_id else ""
    return [
        {
            "intent": "inspect_progress",
            "authority": "controller_required",
            "executes_directly": False,
            "command": f"medautosci study progress --profile {profile_arg}{study_arg}",
        },
        {
            "intent": "open_study_runtime_status",
            "authority": "controller_required",
            "executes_directly": False,
            "command": f"medautosci study-runtime-status --profile {profile_arg}{study_arg}",
        },
        {
            "intent": "request_reconcile",
            "authority": "controller_required",
            "executes_directly": False,
            "command": f"medautosci runtime supervisor-reconcile --profile {profile_arg}{study_arg}",
        },
    ]


def _workspace_source_refs(study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    seen: set[tuple[str, str | None]] = set()
    for context in study_contexts:
        for surface_kind, surface in _mapping(context.get("surfaces")).items():
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
                    "legacy_role": _legacy_role(ref),
                }
            )
    return refs


def _legacy_role(ref: str) -> str | None:
    if "/.ds/" in ref or "med-deepscientist" in ref:
        return "legacy_provenance"
    return None


def _string_list(value: object) -> list[str]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    result: list[str] = []
    for item in value:
        text = io.first_text(item)
        if text:
            result.append(text)
    return result


def _active_run_id(
    *,
    status: Mapping[str, Any],
    health: Mapping[str, Any],
    supervision: Mapping[str, Any],
) -> str | None:
    return io.first_text(
        status.get("active_run_id"),
        _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit")).get("active_run_id"),
        health.get("active_run_id"),
        supervision.get("active_run_id"),
    )


def _worker_running(*, status: Mapping[str, Any], health: Mapping[str, Any]) -> bool:
    for value in (
        health.get("worker_running"),
        status.get("worker_running"),
        _mapping(_mapping(status.get("runtime_liveness_audit")).get("runtime_audit")).get("worker_running"),
    ):
        if isinstance(value, bool):
            return value
    return False


def _study_health_status(context: Mapping[str, Any]) -> str:
    health = _surface_payload(context, "runtime_health")
    summary = _surface_payload(context, "runtime_status_summary")
    status = _surface_payload(context, "study_runtime_status")
    return io.first_text(
        health.get("health_status"),
        health.get("attempt_state"),
        summary.get("health_status"),
        status.get("quest_status"),
        "missing",
    ) or "missing"


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


def _study_timeline(context: Mapping[str, Any]) -> list[dict[str, Any]]:
    return [
        event
        for event in _events(generated_at=_utc_now(), study_contexts=[context])
        if event.get("study_id") == str(context["study_id"])
    ]


def _artifact_refs(context: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("runtime_health", "runtime_supervision", "runtime_status_summary"):
        path = _surface_path_text(context, key)
        if path:
            refs.append(path)
    return sorted(dict.fromkeys(refs))


def _event_refs(context: Mapping[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in ("study_runtime_status", "study_progress"):
        path = _surface_path_text(context, key)
        if path:
            refs.append(path)
    return sorted(dict.fromkeys(refs))


def _surface(context: Mapping[str, Any], key: str) -> dict[str, Any]:
    return _mapping(_mapping(context.get("surfaces")).get(key))


def _surface_payload(context: Mapping[str, Any], key: str) -> dict[str, Any]:
    return _mapping(_surface(context, key).get("payload"))


def _surface_path_text(context: Mapping[str, Any], key: str) -> str | None:
    path = _surface(context, key).get("path")
    return str(path) if path is not None else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _utc_now() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat()


__all__ = [
    "LIVE_CONSOLE_READ_MODEL_REF",
    "SCHEMA_VERSION",
    "STREAM_TOPICS",
    "SURFACE_KIND",
    "build_live_console_read_model",
    "build_live_console_stream_events",
    "materialize_live_console_read_model",
]
