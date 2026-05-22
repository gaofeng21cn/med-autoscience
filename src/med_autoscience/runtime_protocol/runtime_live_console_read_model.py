from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
import json
from pathlib import Path
from typing import Any

from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol import (
    live_console_contract,
    live_console_observation,
    live_console_read_model_io as io,
    local_time_projection,
    production_blocker_impact_projection,
    runtime_session_read_model,
)
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import session_projection


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
    return session_projection.build_live_console_session_read_model(
        profile,
        profile_ref=profile_ref,
        study_id=study_id,
        study_root=study_root,
        generated_at=generated_at,
    )


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
        "events": session_projection.stream_events(materialized, default_payload_ref=LIVE_CONSOLE_READ_MODEL_REF),
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
    source_status = io.load_payload(study_runtime_status, study_runtime_status_path)
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
    production_blocker_impact = production_blocker_impact_projection.build_production_blocker_impact_projection(
        {
            "study_id": resolved_study_id,
            "runtime_session": session,
            "recovery_intent": source_status.get("recovery_intent"),
            "runtime_reconcile_trigger": source_status.get("runtime_reconcile_trigger"),
            "owner_route": source_status.get("owner_route"),
            "paper_progress_stall": source_status.get("paper_progress_stall"),
            "runtime_health_snapshot": source_status.get("runtime_health_snapshot"),
            "control_plane_snapshot": source_status.get("control_plane_snapshot"),
            "current_stage": source_status.get("current_stage"),
            "current_blockers": source_status.get("current_blockers"),
            "refs": source_status.get("refs"),
        },
        {
            "study_id": resolved_study_id,
            "reason": source_status.get("reason"),
            "worker_state": source_status.get("worker_state"),
            "blocking_reasons": source_status.get("blocking_reasons"),
        },
        study_id=resolved_study_id,
    )
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
        "watchdog": _watchdog_projection(session),
        "runtime_health": health,
        "runtime_supervision": supervision,
        "production_blocker_impact": production_blocker_impact,
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
        ("runtime.watchdog", "live_console.watchdog", read_model.get("watchdog")),
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


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _watchdog_projection(session: Mapping[str, Any]) -> dict[str, Any]:
    keys = (
        "monitor_kind",
        "monitor_pid",
        "child_pid",
        "heartbeat_age_seconds",
        "last_output_at",
        "stdout_cursor",
        "stderr_cursor",
        "monitor_state",
        "stale_reason",
        "will_start_llm",
    )
    return {key: session.get(key) for key in keys if session.get(key) is not None}


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
