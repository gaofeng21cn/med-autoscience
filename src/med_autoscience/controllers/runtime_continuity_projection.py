from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def runtime_continuity_projection(
    progress: Mapping[str, Any],
    runtime: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    runtime = runtime or {}
    runtime_session = compact_runtime_session(progress.get("runtime_session")) or compact_runtime_session(
        runtime.get("runtime_session")
    )
    recovery_intent = compact_recovery_intent(progress.get("recovery_intent")) or compact_recovery_intent(
        runtime.get("recovery_intent")
    )
    return {
        "surface_kind": "mas_runtime_continuity_projection",
        "authority": {
            "kind": "read_model_projection",
            "writes_authority_surface": False,
            "quality_ready_authorized": False,
            "publication_ready_authorized": False,
            "submission_ready_authorized": False,
        },
        "runtime_session": runtime_session,
        "recovery_intent": recovery_intent,
    }


def compact_runtime_session(value: object) -> dict[str, Any] | None:
    session = _mapping(value)
    if not session:
        return None
    keys = (
        "study_id",
        "quest_id",
        "active_run_id",
        "last_known_run_id",
        "worker_state",
        "worker_running",
        "runtime_liveness_status",
        "started_at",
        "last_seen_at",
        "last_event_cursor",
        "last_stdout_ref",
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
        "freshness_state",
        "freshness_age_seconds",
        "source_priority",
        "generated_at",
    )
    compact = {key: session.get(key) for key in keys if session.get(key) is not None}
    evidence_refs = _refs_from_ref_field(session.get("evidence_refs"))
    if evidence_refs:
        compact["evidence_refs"] = evidence_refs
    return compact or None


def compact_recovery_intent(value: object) -> dict[str, Any] | None:
    intent = _mapping(value)
    if not intent:
        return None
    keys = (
        "reason",
        "next_owner",
        "retry_budget",
        "dedupe_fingerprint",
        "last_attempt",
        "last_result",
        "next_eligible_tick",
        "current_action",
        "generated_at",
    )
    compact = {key: intent.get(key) for key in keys if intent.get(key) is not None}
    evidence_refs = _refs_from_ref_field(intent.get("evidence_refs"))
    if evidence_refs:
        compact["evidence_refs"] = evidence_refs
    compact["authority"] = {
        "quality_ready_authorized": False,
        "publication_ready_authorized": False,
        "submission_ready_authorized": False,
    }
    return compact or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _refs_from_ref_field(value: object) -> list[str]:
    if isinstance(value, str) and value.strip():
        return [value.strip()]
    if isinstance(value, Mapping):
        result: list[str] = []
        for item in value.values():
            result.extend(_refs_from_ref_field(item))
        return result
    if isinstance(value, list | tuple):
        result: list[str] = []
        for item in value:
            result.extend(_refs_from_ref_field(item))
        return result
    return []


__all__ = [
    "compact_recovery_intent",
    "compact_runtime_session",
    "runtime_continuity_projection",
]
