from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.runtime_protocol import runtime_session_read_model


SCHEMA_VERSION = 1
SURFACE_KIND = "mas_live_console_read_model"
LIVE_CONSOLE_READ_MODEL_REF = "artifacts/runtime/live_console/session_read_model/latest.json"
STREAM_TOPICS: tuple[str, ...] = (
    "workspace.status",
    "study.status",
    "runtime.health",
    "runtime.supervision",
    "terminal.tail",
    "log.tail",
    "artifact.delta",
)


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
