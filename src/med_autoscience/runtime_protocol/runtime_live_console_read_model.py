from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.progress_portal_parts import local_time_projection
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import runtime_session_read_model


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_live_console_read_model"
SESSION_SURFACE_KIND = "mas_live_console_session_read_model"
STREAM_SURFACE_KIND = "mas_live_console_stream"
OWNER = "MedAutoScience"
LIVE_CONSOLE_READ_MODEL_REF = "artifacts/runtime/live_console/session_read_model/latest.json"
LIVE_CONSOLE_READ_MODEL_HISTORY_REF = "artifacts/runtime/live_console/session_read_model/history.jsonl"
STREAM_TOPICS: tuple[str, ...] = (
    "workspace.status",
    "study.status",
    "runtime.health",
    "runtime.supervision",
    "terminal.tail",
    "log.tail",
    "artifact.delta",
)


def build_live_console_session_read_model(
    profile: WorkspaceProfile,
    profile_ref: str | Path | None = None,
    study_id: str | None = None,
    study_root: str | Path | None = None,
    generated_at: str | None = None,
) -> dict[str, Any]:
    generated = _text(generated_at) or _utc_now()
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
        "studies": [_study_projection(context, selected_study_id=selected_study_id) for context in contexts],
        "selected_study_id": selected_study_id,
        "runs": _runs(contexts),
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
    _write_json(latest_path, payload)
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
    generated = _text(generated_at) or _utc_now()
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
    resolved_study_id = _first_text(study_id, session.get("study_id"))
    terminal = _normalize_sources(terminal_sources, limit=tail_limit)
    logs = _normalize_sources(log_sources, limit=tail_limit)
    health = _load_payload(runtime_health, runtime_health_path)
    supervision = _load_payload(runtime_supervision, runtime_supervision_path)
    artifact_payload = dict(artifact_delta or {})
    read_model = {
        "schema_version": SCHEMA_VERSION,
        "surface_kind": SURFACE_KIND,
        "read_only": True,
        "generated_at": generated,
        "authority": _authority(),
        "workspace": {
            "profile_name": _text(profile_name),
            "workspace_root": str(resolved_workspace_root) if resolved_workspace_root is not None else None,
        },
        "study": {
            "study_id": resolved_study_id,
            "quest_id": _first_text(session.get("quest_id"), Path(quest_root).name if quest_root is not None else None),
        },
        "session": session,
        "runtime_health": health,
        "runtime_supervision": supervision,
        "terminal_sources": terminal,
        "log_sources": logs,
        "artifact_delta": artifact_payload,
        "stream_topics": _stream_topics(terminal=terminal, logs=logs, artifact_delta=artifact_payload),
        "controller_action_links": _controller_action_links(study_id=resolved_study_id),
        "source_refs": _source_refs(
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
    _write_json(latest_path, read_model)
    return {
        "ok": True,
        "surface_kind": "mas_live_console_materialization",
        "read_model_ref": str(latest_path),
        "read_model": read_model,
    }


def build_live_console_stream_events(read_model: Mapping[str, Any]) -> list[dict[str, Any]]:
    generated_at = _text(read_model.get("generated_at")) or _utc_now()
    candidates: list[tuple[str, str, object]] = [
        ("workspace.status", "live_console.workspace", read_model.get("workspace")),
        ("study.status", "live_console.study", read_model.get("study")),
        ("runtime.health", "live_console.runtime_health", read_model.get("runtime_health")),
        ("runtime.supervision", "live_console.runtime_supervision", read_model.get("runtime_supervision")),
        ("terminal.tail", _first_source_ref(read_model.get("terminal_sources")) or "live_console.terminal", read_model.get("terminal_sources")),
        ("log.tail", _first_source_ref(read_model.get("log_sources")) or "live_console.log", read_model.get("log_sources")),
        ("artifact.delta", _artifact_source_ref(read_model.get("artifact_delta")) or "live_console.artifact_delta", read_model.get("artifact_delta")),
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
    if _text(study_id) and study_root is not None:
        raise ValueError("Specify only one of study_id or study_root")
    if study_root is not None:
        root = Path(study_root).expanduser().resolve()
        return root.name, root
    selected = _text(study_id) or None
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
    selected = [context for context in contexts if context["study_id"] == selected_study_id]
    others = [context for context in contexts if context["study_id"] != selected_study_id]
    return [*selected, *others] if selected else contexts


def _discover_study_roots(profile: WorkspaceProfile) -> list[Path]:
    studies_root = profile.studies_root.expanduser().resolve()
    if not studies_root.exists():
        return []
    return [path.resolve() for path in studies_root.iterdir() if path.is_dir() and (path / "study.yaml").exists()]


def _study_context(*, profile: WorkspaceProfile, study_root: Path) -> dict[str, Any]:
    study_id = study_root.name
    cockpit_path, cockpit = _read_first_json(
        (
            profile.workspace_root / "artifacts" / "workspace_cockpit" / "latest.json",
            profile.workspace_root / "artifacts" / "runtime" / "workspace_cockpit" / "latest.json",
        )
    )
    progress_path, progress = _read_first_json(
        (
            study_root / "artifacts" / "study_progress" / "latest.json",
            study_root / "artifacts" / "runtime" / "study_progress" / "latest.json",
            study_root / "artifacts" / "progress" / "latest.json",
        )
    )
    runtime_status_path, runtime_status = _read_first_json(
        (
            study_root / "artifacts" / "runtime" / "study_runtime_status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status" / "latest.json",
            study_root / "artifacts" / "runtime" / "status.json",
        )
    )
    summary_path, summary = _read_first_json((study_root / "artifacts" / "runtime" / "runtime_status_summary.json",))
    health_path, health = _read_first_json((study_root / "artifacts" / "runtime" / "health" / "latest.json",))
    supervision_path, supervision = _read_first_json(
        (study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json",)
    )
    quest_root = _quest_root(profile=profile, runtime_status=runtime_status, summary=summary)
    return {
        "study_id": _first_text(
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
            "terminal_tail": _terminal_source(quest_root=quest_root),
            "log_tail": _log_source(quest_root=quest_root),
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
        text = _text(value)
        if not text:
            continue
        candidate = Path(text).expanduser().resolve()
        if candidate.is_dir():
            return candidate
    quest_id = _first_text(runtime_status.get("quest_id"), summary.get("quest_id"))
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
    progress = _surface_payload(context, "study_progress")
    status = _surface_payload(context, "study_runtime_status")
    summary = _surface_payload(context, "runtime_status_summary")
    health = _surface_payload(context, "runtime_health")
    supervision = _surface_payload(context, "runtime_supervision")
    user_visible = _mapping(progress.get("user_visible_projection"))
    active_run_id = _active_run_id(status=status, health=health, supervision=supervision)
    return {
        "study_id": study_id,
        "study_root": str(context["study_root"]),
        "selected": selected_study_id is not None and study_id == selected_study_id,
        "state_label": _first_text(
            user_visible.get("state_label"),
            progress.get("state_label"),
            status.get("quest_status"),
            health.get("health_status"),
            "unknown",
        ),
        "current_stage": _first_text(user_visible.get("current_stage"), progress.get("current_stage")),
        "paper_stage": _first_text(user_visible.get("paper_stage"), progress.get("paper_stage")),
        "quest_id": _first_text(status.get("quest_id"), summary.get("quest_id")),
        "active_run_id": active_run_id,
        "runtime_health_status": _study_health_status(context),
        "supervisor_tick_status": _first_text(
            supervision.get("supervisor_tick_status"),
            summary.get("supervisor_tick_status"),
            "missing" if not supervision else None,
        ),
        "worker_running": _worker_running(status=status, health=health),
        "runs": [
            {
                "run_id": active_run_id,
                "status": _study_health_status(context),
                "last_seen_at": _first_text(status.get("last_seen_at"), health.get("last_seen_at")),
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
                "quest_id": _first_text(status.get("quest_id"), _surface_payload(context, "runtime_status_summary").get("quest_id")),
                "active_run_id": active_run_id,
                "status": _study_health_status(context),
                "worker_running": _worker_running(status=status, health=health),
            }
        )
    return runs


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
    status = _first_text(source.get("status"), "missing")
    payload = {
        "topic": topic,
        "study_id": study_id,
        "status": status,
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
    status = _first_text(artifact_delta.get("status"), "missing")
    return {
        "topic": "artifact.delta",
        "study_id": str(context["study_id"]),
        "status": status,
        "source_ref": _surface_path_text(context, "runtime_health"),
        "source_status": "available" if health else "missing",
        "latest_meaningful_delta_at": _text(artifact_delta.get("latest_meaningful_delta_at")),
        "artifact_kind": _text(artifact_delta.get("artifact_kind")),
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
                _first_text(_surface_payload(context, "study_runtime_status").get("quest_status"), "missing"),
                _surface_path_text(context, "study_runtime_status"),
            ),
            ("runtime.health", _study_health_status(context), _surface_path_text(context, "runtime_health")),
            (
                "runtime.supervision",
                _first_text(supervision.get("supervisor_tick_status"), "missing"),
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
                status=_first_text(artifact_delta.get("status"), "missing"),
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
                    source_ref=_text(stream.get("source_ref")),
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
    payload_path = _text(materialized.get("payload_path")) or LIVE_CONSOLE_READ_MODEL_REF
    model = _mapping(materialized.get("session_read_model"))
    events: list[dict[str, Any]] = []
    for event in model.get("events") if isinstance(model.get("events"), list) else []:
        if not isinstance(event, Mapping):
            continue
        projected = dict(event)
        source_ref = _text(projected.get("source_ref"))
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


def _terminal_source(*, quest_root: Path | None) -> dict[str, Any]:
    if quest_root is None:
        return {"status": "missing", "source_ref": None, "tail": []}
    path, payload = _read_first_json((quest_root / ".ds" / "bash_exec" / "summary.json",))
    if not payload:
        summary_path = quest_root / ".ds" / "bash_exec" / "summary.json"
        return {"status": "missing", "path": str(summary_path), "source_ref": str(summary_path), "tail": []}
    return {
        "status": "available",
        "path": str(path) if path is not None else None,
        "source_ref": str(path) if path is not None else None,
        "tail": _tail_source_lines(payload.get("tail")),
    }


def _log_source(*, quest_root: Path | None) -> dict[str, Any]:
    if quest_root is None:
        return {"status": "missing", "source_ref": None, "tail": []}
    log_path = quest_root / "logs" / "worker.log"
    if not log_path.is_file():
        return {"status": "missing", "path": str(log_path), "source_ref": str(log_path), "tail": []}
    return {
        "status": "available",
        "path": str(log_path),
        "source_ref": str(log_path),
        "tail": log_path.read_text(encoding="utf-8", errors="replace").splitlines()[-20:],
    }


def _tail_source_lines(value: object) -> list[str]:
    if isinstance(value, str):
        return value.splitlines()[-20:]
    if not isinstance(value, Iterable):
        return []
    return [str(item) for item in value if isinstance(item, str)][-20:]


def _active_run_id(
    *,
    status: Mapping[str, Any],
    health: Mapping[str, Any],
    supervision: Mapping[str, Any],
) -> str | None:
    return _first_text(
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
    return _first_text(
        health.get("health_status"),
        summary.get("health_status"),
        status.get("quest_status"),
        "missing",
    ) or "missing"


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


def _read_first_json(paths: Iterable[Path]) -> tuple[Path | None, dict[str, Any]]:
    for path in paths:
        if not path.is_file():
            continue
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(payload, Mapping):
            return path.resolve(), dict(payload)
    return None, {}


def _normalize_sources(sources: Sequence[Mapping[str, Any]] | None, *, limit: int) -> list[dict[str, Any]]:
    normalized: list[dict[str, Any]] = []
    for source in sources or ():
        raw_path = source.get("path")
        path_text = str(raw_path) if isinstance(raw_path, Path) else _text(raw_path)
        path = Path(path_text).expanduser().resolve() if path_text else None
        source_ref = path_text or _text(source.get("source_ref")) or _text(source.get("ref"))
        payload = {
            "source": _text(source.get("source")) or _text(source.get("kind")) or "runtime_stream",
            "source_ref": str(path) if path is not None else source_ref,
            "read_only": True,
            "tail": _tail_lines(path, limit=limit) if path is not None else list(source.get("tail") or []),
        }
        payload["status"] = "available" if payload["tail"] or (path is not None and path.exists()) else "missing"
        normalized.append(payload)
    return normalized


def _tail_lines(path: Path, *, limit: int) -> list[str]:
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return []
    rendered: list[str] = []
    for line in lines[-max(limit, 1) :]:
        rendered_line = _line_from_json(line)
        if rendered_line:
            rendered.append(rendered_line)
    return rendered


def _line_from_json(line: str) -> str:
    try:
        payload = json.loads(line)
    except json.JSONDecodeError:
        return line
    if isinstance(payload, Mapping):
        return _first_text(payload.get("line"), payload.get("message"), payload.get("text"), payload.get("content")) or line
    return line


def _load_payload(payload: Mapping[str, Any] | None, path: Path | None) -> dict[str, Any]:
    if payload is not None:
        return dict(payload)
    if path is None:
        return {}
    try:
        loaded = json.loads(Path(path).expanduser().resolve().read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return dict(loaded) if isinstance(loaded, Mapping) else {}


def _stream_topics(
    *,
    terminal: Sequence[Mapping[str, Any]],
    logs: Sequence[Mapping[str, Any]],
    artifact_delta: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        {"topic": topic, "read_only": True, "source_ref": _topic_source_ref(topic, terminal, logs, artifact_delta)}
        for topic in STREAM_TOPICS
    ]


def _topic_source_ref(
    topic: str,
    terminal: Sequence[Mapping[str, Any]],
    logs: Sequence[Mapping[str, Any]],
    artifact_delta: Mapping[str, Any],
) -> str:
    if topic == "terminal.tail":
        return _first_source_ref(terminal) or "live_console.terminal"
    if topic == "log.tail":
        return _first_source_ref(logs) or "live_console.log"
    if topic == "artifact.delta":
        return _artifact_source_ref(artifact_delta) or "live_console.artifact_delta"
    return f"live_console.{topic}"


def _source_refs(
    *,
    session: Mapping[str, Any],
    runtime_health_path: Path | None,
    runtime_supervision_path: Path | None,
    terminal: Sequence[Mapping[str, Any]],
    logs: Sequence[Mapping[str, Any]],
    artifact_delta: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for ref in session.get("evidence_refs") or []:
        if isinstance(ref, Mapping):
            refs.append(_first_text(ref.get("path"), ref.get("source")) or "")
        elif isinstance(ref, str):
            refs.append(ref)
    refs.extend(str(Path(path).expanduser().resolve()) for path in (runtime_health_path, runtime_supervision_path) if path)
    refs.extend(_first_source_ref(items) or "" for items in (terminal, logs))
    refs.append(_artifact_source_ref(artifact_delta) or "")
    return [ref for ref in refs if ref]


def _controller_action_links(*, study_id: str | None) -> list[dict[str, Any]]:
    suffix = f" --study-id {study_id}" if study_id else ""
    return [
        {
            "action": "inspect_progress",
            "label": "inspect progress",
            "command": f"medautosci study progress{suffix}",
            "direct_execution_allowed": False,
        },
        {
            "action": "request_reconcile",
            "label": "request reconcile through MAS controller",
            "command": f"medautosci runtime supervisor-reconcile{suffix}",
            "direct_execution_allowed": False,
        },
    ]


def _authority() -> dict[str, bool | str]:
    return {
        "kind": "read_only_runtime_projection",
        "writes_authority_surface": False,
        "controller_action_execution_allowed": False,
        "quality_authority_allowed": False,
        "publication_authority_allowed": False,
        "submission_authority_allowed": False,
    }


def _first_source_ref(value: object) -> str | None:
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):
        for item in value:
            if isinstance(item, Mapping):
                text = _first_text(item.get("source_ref"), item.get("path"), item.get("ref"))
                if text:
                    return text
    return None


def _artifact_source_ref(value: object) -> str | None:
    payload = value if isinstance(value, Mapping) else {}
    refs = payload.get("refs")
    if isinstance(refs, Sequence) and not isinstance(refs, (str, bytes)):
        return _first_text(*refs)
    return _first_text(payload.get("source_ref"), payload.get("path"), payload.get("ref"))


def _write_json(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _first_text(*values: object) -> str | None:
    for value in values:
        text = _text(value)
        if text:
            return text
    return None


def _text(value: object) -> str:
    return value.strip() if isinstance(value, str) else ""


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
