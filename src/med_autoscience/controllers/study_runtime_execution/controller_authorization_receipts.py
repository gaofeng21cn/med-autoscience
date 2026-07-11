from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers import publication_work_unit_lifecycle

from ..progress_projection import ProgressProjectionStatus


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _active_run_id_from_status(*, status: ProgressProjectionStatus) -> str | None:
    payload = status.extras.get("runtime_liveness_audit")
    if isinstance(payload, dict):
        active_run_id = str(payload.get("active_run_id") or "").strip()
        if active_run_id:
            return active_run_id
        runtime_audit = payload.get("runtime_audit")
        if isinstance(runtime_audit, dict):
            active_run_id = str(runtime_audit.get("active_run_id") or "").strip()
            if active_run_id:
                return active_run_id
    return None


def _closed_publication_work_unit_lifecycle(
    *,
    study_root: Path,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    lifecycle_path = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "controller"
        / "publication_work_unit_lifecycle"
        / "latest.json"
    )
    try:
        payload = json.loads(lifecycle_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    if not publication_work_unit_lifecycle.lifecycle_payload_is_closed(payload):
        return None
    source_eval_id = _text(payload.get("source_eval_id"))
    authorization_eval_id = _text(authorization_context.get("publication_eval_id"))
    if source_eval_id is None or authorization_eval_id is None or source_eval_id != authorization_eval_id:
        return None
    lifecycle_work_unit = payload.get("work_unit")
    if not isinstance(lifecycle_work_unit, dict):
        return None
    work_unit_id = _text(authorization_context.get("work_unit_id"))
    if work_unit_id is None or _text(lifecycle_work_unit.get("unit_id")) != work_unit_id:
        return None
    return {
        "reason": "publication_work_unit_lifecycle_done",
        "status": _text(payload.get("status")),
        "source_eval_id": source_eval_id,
        "work_unit_id": work_unit_id,
        "lifecycle_path": str(lifecycle_path),
        "gate_replay_status": payload.get("gate_replay_status"),
        "unit_statuses": list(payload.get("unit_statuses") or []),
    }
