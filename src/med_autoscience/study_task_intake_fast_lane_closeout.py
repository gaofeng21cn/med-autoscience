from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MANUSCRIPT_FAST_LANE_CLOSEOUT_GLOB = "manuscript_fast_lane_closeout_*.json"
MANUSCRIPT_FAST_LANE_CLOSEOUT_SURFACE_KINDS = frozenset(
    {
        "manuscript_fast_lane_closeout",
        "foreground_manuscript_fast_lane_closeout",
    }
)
MANUSCRIPT_FAST_LANE_CLOSEOUT_STATUSES = frozenset({"complete", "completed", "closed"})
MANUSCRIPT_FAST_LANE_CLOSEOUT_STATES = frozenset(
    {
        "foreground_fast_lane_completed",
        "manuscript_fast_lane_completed",
        "manual_foreground_revision_completed",
    }
)
MANUSCRIPT_FAST_LANE_CLOSEOUT_AUTO_RESUME_POLICIES = frozenset(
    {
        "do_not_resume_superseded_task_intake",
        "manual_handoff_only",
    }
)


def _non_empty_text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _normalize_timestamp(value: object) -> datetime | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _surface_emitted_at(payload: dict[str, Any] | None) -> datetime | None:
    if not isinstance(payload, dict):
        return None
    return _normalize_timestamp(payload.get("emitted_at") or payload.get("generated_at") or payload.get("created_at"))


def _mapping_value(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, dict) else {}


def _closeout_surface_is_fresher_than_task_intake(
    task_intake_payload: dict[str, Any] | None,
    closeout_payload: dict[str, Any] | None,
) -> bool:
    task_intake_emitted_at = _surface_emitted_at(task_intake_payload)
    closeout_emitted_at = _surface_emitted_at(closeout_payload)
    return (
        task_intake_emitted_at is not None
        and closeout_emitted_at is not None
        and closeout_emitted_at >= task_intake_emitted_at
    )


def latest_manuscript_fast_lane_closeout(*, task_intake_root: Path | None) -> dict[str, Any] | None:
    if task_intake_root is None:
        return None
    root = Path(task_intake_root).expanduser().resolve()
    if not root.exists():
        return None
    candidates: list[tuple[datetime, str, dict[str, Any]]] = []
    for path in root.glob(MANUSCRIPT_FAST_LANE_CLOSEOUT_GLOB):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(payload, dict):
            continue
        timestamp = _surface_emitted_at(payload)
        if timestamp is None:
            try:
                timestamp = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
            except OSError:
                continue
        candidates.append((timestamp, path.name, payload))
    if not candidates:
        return None
    return max(candidates, key=lambda item: (item[0], item[1]))[2]


def _payload_text_set(payload: dict[str, Any], keys: tuple[str, ...]) -> set[str]:
    values: list[object] = []
    for key in keys:
        value = payload.get(key)
        if isinstance(value, list):
            values.extend(value)
        else:
            values.append(value)
    return {
        text
        for text in (_non_empty_text(value) for value in values)
        if text is not None
    }


def _closeout_references_task(
    *,
    task_intake_payload: dict[str, Any] | None,
    closeout_payload: dict[str, Any],
) -> bool:
    task_id = _non_empty_text((task_intake_payload or {}).get("task_id"))
    if task_id is None:
        return False
    referenced_task_ids = _payload_text_set(
        closeout_payload,
        (
            "source_task_id",
            "source_task_ids",
            "superseded_task_intake_id",
            "superseded_task_intake_ids",
            "retired_task_intake_id",
            "retired_task_intake_ids",
        ),
    )
    source_task = closeout_payload.get("source_task")
    if isinstance(source_task, dict):
        source_task_id = _non_empty_text(source_task.get("task_id"))
        if source_task_id is not None:
            referenced_task_ids.add(source_task_id)
    return task_id in referenced_task_ids


def _closeout_has_required_scope(closeout_payload: dict[str, Any]) -> bool:
    scope = _mapping_value(closeout_payload.get("scope"))
    evidence = _mapping_value(closeout_payload.get("evidence"))
    validation = _mapping_value(closeout_payload.get("validation"))
    return (
        scope.get("existing_evidence_only") is True
        and scope.get("canonical_paper_text_or_structure_only") is True
        and scope.get("new_analysis_performed") is False
        and validation.get("canonical_paper_writeback_complete") is True
        and validation.get("export_sync_complete") is True
        and validation.get("qc_complete") is True
        and validation.get("package_consistency_checked") is True
        and evidence.get("claim_guardrails_preserved", True) is not False
    )


def manuscript_fast_lane_closeout_confirms_old_task_retired(
    *,
    task_intake_payload: dict[str, Any] | None,
    closeout_payload: dict[str, Any] | None,
) -> bool:
    if not isinstance(task_intake_payload, dict) or not isinstance(closeout_payload, dict):
        return False
    if not _closeout_surface_is_fresher_than_task_intake(task_intake_payload, closeout_payload):
        return False
    surface_kind = _non_empty_text(closeout_payload.get("surface_kind"))
    record_type = _non_empty_text(closeout_payload.get("record_type"))
    if surface_kind not in MANUSCRIPT_FAST_LANE_CLOSEOUT_SURFACE_KINDS and (
        record_type not in MANUSCRIPT_FAST_LANE_CLOSEOUT_SURFACE_KINDS
    ):
        return False
    if not _closeout_references_task(
        task_intake_payload=task_intake_payload,
        closeout_payload=closeout_payload,
    ):
        return False
    status = (_non_empty_text(closeout_payload.get("status")) or "").lower()
    completion_state = (_non_empty_text(closeout_payload.get("completion_state")) or "").lower()
    if status not in MANUSCRIPT_FAST_LANE_CLOSEOUT_STATUSES:
        return False
    if completion_state not in MANUSCRIPT_FAST_LANE_CLOSEOUT_STATES:
        return False
    auto_resume_policy = (_non_empty_text(closeout_payload.get("auto_resume_policy")) or "").lower()
    if auto_resume_policy not in MANUSCRIPT_FAST_LANE_CLOSEOUT_AUTO_RESUME_POLICIES:
        return False
    if _non_empty_text(closeout_payload.get("canonical_write_surface")) != "paper/":
        return False
    if _non_empty_text(closeout_payload.get("projection_surface")) != "manuscript/current_package/":
        return False
    return _closeout_has_required_scope(closeout_payload)


def task_intake_yields_to_manuscript_fast_lane_closeout(
    payload: dict[str, Any] | None,
    *,
    task_intake_root: Path | None,
) -> bool:
    return manuscript_fast_lane_closeout_confirms_old_task_retired(
        task_intake_payload=payload,
        closeout_payload=latest_manuscript_fast_lane_closeout(task_intake_root=task_intake_root),
    )
