from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.runtime_protocol import live_console_read_model_io as io
from med_autoscience.runtime_protocol import local_time_projection
from med_autoscience.runtime_protocol.runtime_live_console_read_model_parts import context_projection


def stream_events(materialized: Mapping[str, Any], *, default_payload_ref: str) -> list[dict[str, Any]]:
    payload_path = io.text(materialized.get("payload_path")) or default_payload_ref
    model = context_projection.mapping(materialized.get("session_read_model"))
    events: list[dict[str, Any]] = []
    for event in model.get("events") if isinstance(model.get("events"), list) else []:
        if not isinstance(event, Mapping):
            continue
        projected = dict(event)
        source_ref = io.text(projected.get("source_ref"))
        projected["source_ref"] = payload_path if source_ref in {None, "workspace"} else source_ref
        events.append(projected)
    return events


def stream_sources(study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for context in study_contexts:
        study_id = str(context["study_id"])
        result.extend(
            [
                stream_source(topic="terminal.tail", study_id=study_id, source=context_projection.surface(context, "terminal_tail")),
                stream_source(topic="log.tail", study_id=study_id, source=context_projection.surface(context, "log_tail")),
                artifact_delta_source(context),
            ]
        )
    return result


def stream_source(*, topic: str, study_id: str, source: Mapping[str, Any]) -> dict[str, Any]:
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


def artifact_delta_source(context: Mapping[str, Any]) -> dict[str, Any]:
    health = context_projection.surface_payload(context, "runtime_health")
    artifact_delta = context_projection.mapping(health.get("artifact_delta"))
    status = io.first_text(artifact_delta.get("status"), "missing")
    return {
        "topic": "artifact.delta",
        "study_id": str(context["study_id"]),
        "status": status,
        "label": "产物增量",
        "source_ref": context_projection.surface_path_text(context, "runtime_health"),
        "source_status": "available" if health else "missing",
        "latest_meaningful_delta_at": io.text(artifact_delta.get("latest_meaningful_delta_at")),
        "artifact_kind": io.text(artifact_delta.get("artifact_kind")),
        "read_only": True,
    }


def events(*, generated_at: str, study_contexts: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    projected_events: list[dict[str, Any]] = [
        event(
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
        health = context_projection.surface_payload(context, "runtime_health")
        supervision = context_projection.surface_payload(context, "runtime_supervision")
        for topic, status, source_ref in (
            (
                "study.status",
                io.first_text(context_projection.surface_payload(context, "study_runtime_status").get("quest_status"), "missing"),
                context_projection.surface_path_text(context, "study_runtime_status"),
            ),
            (
                "runtime.health",
                context_projection.study_health_status(context),
                context_projection.surface_path_text(context, "runtime_health"),
            ),
            (
                "runtime.supervision",
                io.first_text(supervision.get("supervisor_tick_status"), "missing"),
                context_projection.surface_path_text(context, "runtime_supervision"),
            ),
        ):
            projected_events.append(
                event(
                    sequence=len(projected_events) + 1,
                    topic=topic,
                    study_id=study_id,
                    status=status,
                    source_ref=source_ref,
                    observed_at=generated_at,
                )
            )
        artifact_delta = context_projection.mapping(health.get("artifact_delta"))
        projected_events.append(
            event(
                sequence=len(projected_events) + 1,
                topic="artifact.delta",
                study_id=study_id,
                status=io.first_text(artifact_delta.get("status"), "missing"),
                source_ref=context_projection.surface_path_text(context, "runtime_health"),
                observed_at=generated_at,
            )
        )
        for stream in (
            stream_source(
                topic="terminal.tail",
                study_id=study_id,
                source=context_projection.surface(context, "terminal_tail"),
            ),
            stream_source(topic="log.tail", study_id=study_id, source=context_projection.surface(context, "log_tail")),
        ):
            projected_events.append(
                event(
                    sequence=len(projected_events) + 1,
                    topic=str(stream["topic"]),
                    study_id=study_id,
                    status=str(stream["status"]),
                    source_ref=io.text(stream.get("source_ref")),
                    observed_at=generated_at,
                )
            )
    return projected_events


def event(
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
        "local_time": local_time_projection.local_time_projection(observed_at, timezone_name=None),
    }


__all__ = [
    "artifact_delta_source",
    "event",
    "events",
    "stream_events",
    "stream_source",
    "stream_sources",
]
