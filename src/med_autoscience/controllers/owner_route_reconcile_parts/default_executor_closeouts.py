from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


LIVE_ATTEMPT_STATES = frozenset({"running", "checkpointed", "human_gate"})
NON_TERMINAL_CLOSEOUT_STATUSES = LIVE_ATTEMPT_STATES | {
    "admitted",
    "created",
    "hydrated",
    "in_progress",
    "pending",
    "queued",
    "started",
    "starting",
}
TERMINAL_CLOSEOUT_STATUS_PREFIXES = (
    "blocked",
    "closed",
    "completed",
    "executed",
    "failed",
    "materialized_record",
    "owner_output_already_current",
    "progress_delta",
    "record_materialized",
    "record_only_archive",
    "succeeded",
    "terminal",
    "typed_blocker",
    "typed_blocked",
)


def has_terminal_default_executor_closeout(
    *,
    profile: Any,
    study_id: str,
    stage_attempt_id: str | None,
) -> bool:
    if stage_attempt_id is None:
        return False
    for path in _default_executor_closeout_paths(
        profile=profile,
        study_id=study_id,
        stage_attempt_id=stage_attempt_id,
    ):
        payload = _read_json_object(path)
        if _closeout_payload_closes_stage_attempt(payload, stage_attempt_id=stage_attempt_id):
            return True
    return False


def _default_executor_closeout_paths(
    *,
    profile: Any,
    study_id: str,
    stage_attempt_id: str,
) -> tuple[Path, ...]:
    roots: list[Path] = []
    studies_root = getattr(profile, "studies_root", None)
    if studies_root is not None:
        roots.append(Path(studies_root).expanduser() / study_id)
    workspace_root = getattr(profile, "workspace_root", None)
    if workspace_root is not None:
        roots.append(Path(workspace_root).expanduser() / "studies" / study_id)

    paths: list[Path] = []
    seen: set[Path] = set()
    for root in roots:
        path = (
            root
            / "artifacts"
            / "supervision"
            / "consumer"
            / "default_executor_execution"
            / f"{stage_attempt_id}.closeout.json"
        )
        try:
            resolved = path.resolve()
        except OSError:
            resolved = path
        if resolved in seen or not path.exists():
            continue
        seen.add(resolved)
        paths.append(path)
    return tuple(paths)


def _closeout_payload_closes_stage_attempt(
    payload: Mapping[str, Any] | None,
    *,
    stage_attempt_id: str,
) -> bool:
    closeout = _mapping(payload)
    if not closeout:
        return False
    payload_stage_attempt_id = _text(closeout.get("stage_attempt_id")) or _text(
        closeout.get("active_stage_attempt_id")
    )
    if payload_stage_attempt_id is not None and payload_stage_attempt_id != stage_attempt_id:
        return False

    status = _text(closeout.get("status"))
    if status in NON_TERMINAL_CLOSEOUT_STATUSES:
        return False
    surface_kind = _text(closeout.get("surface_kind")) or _text(closeout.get("surface"))
    if surface_kind == "stage_attempt_closeout_packet":
        return True
    return status is not None and _closeout_status_is_terminal(status)


def _closeout_status_is_terminal(status: str) -> bool:
    normalized = status.strip().lower()
    return any(
        normalized == prefix or normalized.startswith(f"{prefix}_")
        for prefix in TERMINAL_CLOSEOUT_STATUS_PREFIXES
    )


def _read_json_object(path: Path) -> dict[str, Any] | None:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    return dict(payload) if isinstance(payload, Mapping) else None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["has_terminal_default_executor_closeout"]
