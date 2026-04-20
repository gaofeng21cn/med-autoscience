from __future__ import annotations

import json
from pathlib import Path
from typing import Any

__all__ = [
    "STABLE_RUNTIME_STATUS_SUMMARY_RELATIVE_PATH",
    "build_runtime_status_summary",
    "materialize_runtime_status_summary",
    "read_runtime_status_summary",
    "resolve_runtime_status_summary_ref",
    "stable_runtime_status_summary_path",
]


STABLE_RUNTIME_STATUS_SUMMARY_RELATIVE_PATH = Path("artifacts/runtime/runtime_status_summary.json")

_REQUIRED_TEXT_FIELDS = (
    "summary_id",
    "study_id",
    "generated_at",
    "runtime_status_ref",
    "runtime_artifact_ref",
    "health_status",
    "runtime_decision",
    "recovery_action_mode",
    "status_summary",
    "next_action_summary",
)
_OPTIONAL_TEXT_FIELDS = (
    "quest_id",
    "runtime_escalation_record_ref",
    "runtime_watch_ref",
    "runtime_reason",
    "supervisor_tick_status",
    "current_required_action",
    "controller_stage_note",
)


def stable_runtime_status_summary_path(*, study_root: Path) -> Path:
    return (Path(study_root).expanduser().resolve() / STABLE_RUNTIME_STATUS_SUMMARY_RELATIVE_PATH).resolve()


def resolve_runtime_status_summary_ref(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> Path:
    stable_path = stable_runtime_status_summary_path(study_root=study_root)
    if ref is None:
        return stable_path
    candidate = Path(ref).expanduser()
    if candidate.is_absolute():
        candidate = candidate.resolve()
    else:
        candidate = (Path(study_root).expanduser().resolve() / candidate).resolve()
    if candidate != stable_path:
        raise ValueError("runtime status summary reader only accepts the stable runtime artifact")
    return stable_path


def _required_text(label: str, field_name: str, value: object) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label} {field_name} must be non-empty")
    return value.strip()


def _optional_text(label: str, field_name: str, value: object) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{label} {field_name} must be str or None")
    text = value.strip()
    return text or None


def _normalized_payload(payload: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(payload, dict):
        raise TypeError("runtime status summary payload must be a mapping")
    if payload.get("schema_version") != 1:
        raise ValueError("runtime status summary schema_version must be 1")
    normalized: dict[str, Any] = {"schema_version": 1}
    for field_name in _REQUIRED_TEXT_FIELDS:
        normalized[field_name] = _required_text("runtime status summary", field_name, payload.get(field_name))
    for field_name in _OPTIONAL_TEXT_FIELDS:
        normalized[field_name] = _optional_text("runtime status summary", field_name, payload.get(field_name))
    needs_human_intervention = payload.get("needs_human_intervention")
    if not isinstance(needs_human_intervention, bool):
        raise TypeError("runtime status summary needs_human_intervention must be bool")
    normalized["needs_human_intervention"] = needs_human_intervention
    return normalized


def build_runtime_status_summary(
    *,
    study_id: str,
    quest_id: str | None,
    generated_at: str,
    runtime_status_ref: str,
    runtime_artifact_ref: str,
    runtime_escalation_record_ref: str | None,
    runtime_watch_ref: str | None,
    health_status: str,
    runtime_decision: str,
    runtime_reason: str | None,
    recovery_action_mode: str,
    supervisor_tick_status: str | None,
    current_required_action: str | None,
    controller_stage_note: str | None,
    status_summary: str,
    next_action_summary: str,
    needs_human_intervention: bool,
) -> dict[str, Any]:
    normalized_study_id = _required_text("runtime status summary", "study_id", study_id)
    normalized_generated_at = _required_text("runtime status summary", "generated_at", generated_at)
    normalized_quest_id = _optional_text("runtime status summary", "quest_id", quest_id)
    summary_scope = normalized_quest_id or "none"
    return _normalized_payload(
        {
            "schema_version": 1,
            "summary_id": f"runtime-status::{normalized_study_id}::{summary_scope}::{normalized_generated_at}",
            "study_id": normalized_study_id,
            "quest_id": normalized_quest_id,
            "generated_at": normalized_generated_at,
            "runtime_status_ref": runtime_status_ref,
            "runtime_artifact_ref": runtime_artifact_ref,
            "runtime_escalation_record_ref": runtime_escalation_record_ref,
            "runtime_watch_ref": runtime_watch_ref,
            "health_status": health_status,
            "runtime_decision": runtime_decision,
            "runtime_reason": runtime_reason,
            "recovery_action_mode": recovery_action_mode,
            "supervisor_tick_status": supervisor_tick_status,
            "current_required_action": current_required_action,
            "controller_stage_note": controller_stage_note,
            "status_summary": status_summary,
            "next_action_summary": next_action_summary,
            "needs_human_intervention": needs_human_intervention,
        }
    )


def read_runtime_status_summary(
    *,
    study_root: Path,
    ref: str | Path | None = None,
) -> dict[str, Any]:
    summary_path = resolve_runtime_status_summary_ref(study_root=study_root, ref=ref)
    payload = json.loads(summary_path.read_text(encoding="utf-8")) or {}
    if not isinstance(payload, dict):
        raise ValueError(f"runtime status summary payload must be a JSON object: {summary_path}")
    return _normalized_payload(payload)


def materialize_runtime_status_summary(
    *,
    study_root: Path,
    summary: dict[str, Any],
) -> dict[str, str]:
    normalized = _normalized_payload(summary)
    summary_path = stable_runtime_status_summary_path(study_root=study_root)
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    summary_path.write_text(json.dumps(normalized, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        "summary_id": str(normalized["summary_id"]),
        "artifact_path": str(summary_path),
    }
