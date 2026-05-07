from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from med_autoscience.runtime_transport.med_deepscientist_parts.storage import _load_json_dict


STALE_PROGRESS_SILENCE_SECONDS = 30 * 60


def _interaction_watchdog_payload(snapshot: dict[str, Any]) -> dict[str, Any] | None:
    payload = snapshot.get("interaction_watchdog")
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def _nonnegative_int(value: object) -> int | None:
    try:
        resolved = int(value)
    except (TypeError, ValueError):
        return None
    return max(resolved, 0)


def _seconds_since_iso_timestamp(value: object) -> int | None:
    text = str(value or "").strip()
    if not text:
        return None
    if text.endswith("Z"):
        text = f"{text[:-1]}+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return max(int((datetime.now(UTC) - parsed.astimezone(UTC)).total_seconds()), 0)


def _missing_first_progress_watchdog(
    *,
    interaction_watchdog: dict[str, Any],
    snapshot: dict[str, Any],
    runtime_root: Path | None = None,
    quest_id: str | None = None,
) -> bool:
    if not bool(interaction_watchdog.get("active_execution_window")):
        return False
    if str(interaction_watchdog.get("last_artifact_interact_at") or "").strip():
        return False
    if str(interaction_watchdog.get("last_tool_activity_at") or "").strip():
        return False
    tool_calls_since_last_artifact_interact = _nonnegative_int(
        interaction_watchdog.get("tool_calls_since_last_artifact_interact")
    )
    if tool_calls_since_last_artifact_interact not in {None, 0}:
        return False
    last_transition_at = str(snapshot.get("last_transition_at") or "").strip() or None
    if last_transition_at is None and runtime_root is not None and quest_id:
        runtime_state_path = Path(runtime_root).expanduser().resolve() / "quests" / quest_id / ".ds" / "runtime_state.json"
        runtime_state = _load_json_dict(runtime_state_path)
        last_transition_at = str(runtime_state.get("last_transition_at") or "").strip() or None
    silence_seconds = _seconds_since_iso_timestamp(last_transition_at)
    return silence_seconds is not None and silence_seconds >= STALE_PROGRESS_SILENCE_SECONDS


def _stale_progress_watchdog(
    interaction_watchdog: dict[str, Any] | None,
    *,
    snapshot: dict[str, Any],
    runtime_root: Path | None = None,
    quest_id: str | None = None,
) -> bool:
    if not isinstance(interaction_watchdog, dict):
        return False
    if bool(interaction_watchdog.get("stale_visibility_gap")):
        return True
    if _missing_first_progress_watchdog(
        interaction_watchdog=interaction_watchdog,
        snapshot=snapshot,
        runtime_root=runtime_root,
        quest_id=quest_id,
    ):
        return True
    resolved_silence_seconds = _nonnegative_int(interaction_watchdog.get("seconds_since_last_artifact_interact"))
    if resolved_silence_seconds is None:
        return False
    return bool(interaction_watchdog.get("inspection_due")) and resolved_silence_seconds >= STALE_PROGRESS_SILENCE_SECONDS
