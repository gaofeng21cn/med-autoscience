from __future__ import annotations

from typing import Any

from .shared import _non_empty_text


def activity_timeout_state(progress_freshness: dict[str, Any]) -> str | None:
    activity_timeout = progress_freshness.get("activity_timeout")
    if not isinstance(activity_timeout, dict):
        return None
    return _non_empty_text(activity_timeout.get("state"))


def activity_timeout_lane(
    *,
    progress_freshness: dict[str, Any],
    current_stage_summary: str,
    blocker_summary: str | None,
    next_system_action: str,
) -> dict[str, Any]:
    activity_timeout = progress_freshness.get("activity_timeout")
    return {
        "lane_id": "runtime_recovery_required",
        "title": "优先处理 activity timeout",
        "severity": "critical",
        "summary": (
            _non_empty_text((activity_timeout or {}).get("summary"))
            or _non_empty_text(progress_freshness.get("summary"))
            or current_stage_summary
            or blocker_summary
            or next_system_action
        ),
        "recommended_action_id": "continue_or_relaunch",
        "activity_timeout": dict(activity_timeout or {}),
        "progress_pressure": dict((activity_timeout or {}).get("progress_pressure") or {}),
        "terminal_failure": False,
    }
