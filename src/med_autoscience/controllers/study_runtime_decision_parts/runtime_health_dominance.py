from __future__ import annotations

import json
from pathlib import Path

from med_autoscience.controllers import runtime_health_kernel
from med_autoscience.controllers.study_runtime_types import (
    StudyRuntimeAuditStatus,
    StudyRuntimeStatus,
    _LIVE_QUEST_STATUSES,
)


def _latest_runtime_health_snapshot(study_root: Path) -> dict[str, object]:
    path = runtime_health_kernel.runtime_health_snapshot_path(study_root=study_root)
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def _runtime_health_requires_explicit_resume(
    *,
    status: StudyRuntimeStatus,
    study_root: Path,
    study_id: str,
    quest_id: str,
) -> bool:
    if status.quest_status not in _LIVE_QUEST_STATUSES:
        return False
    try:
        if status.runtime_liveness_audit_record.status is StudyRuntimeAuditStatus.LIVE:
            return False
    except KeyError:
        pass
    try:
        continuation_state = status.continuation_state
    except KeyError:
        return False
    if continuation_state.active_run_id is not None:
        return False
    if continuation_state.continuation_policy != "wait_for_user_or_resume":
        return False
    snapshot = _latest_runtime_health_snapshot(study_root)
    if snapshot.get("study_id") != study_id or snapshot.get("quest_id") != quest_id:
        return False
    return (
        snapshot.get("canonical_runtime_action") == "await_explicit_resume"
        and snapshot.get("failure_reason") == "quest_stopped_requires_explicit_rerun"
    )
