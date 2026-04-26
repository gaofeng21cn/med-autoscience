from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_runtime_types import StudyRuntimeStatus


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _read_json_object(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else None


def _status_payload(value: dict[str, Any] | StudyRuntimeStatus) -> dict[str, Any]:
    if isinstance(value, dict):
        return dict(value)
    return value.to_dict()


def _flapping_circuit_breaker_report(*, study_root: Path) -> dict[str, Any] | None:
    latest_path = (
        Path(study_root).expanduser().resolve()
        / "artifacts"
        / "runtime"
        / "runtime_supervision"
        / "latest.json"
    )
    latest = _read_json_object(latest_path)
    if not latest:
        return None
    if latest.get("flapping_circuit_breaker") is not True:
        return None
    if _non_empty_text(latest.get("runtime_stability_status")) != "flapping":
        return None
    return latest


def hold_for_flapping_circuit_breaker(
    *,
    study_root: Path,
    status_payload: dict[str, Any] | StudyRuntimeStatus,
) -> dict[str, Any] | None:
    flapping_report = _flapping_circuit_breaker_report(study_root=study_root)
    if flapping_report is None:
        return None
    payload = _status_payload(status_payload)
    return {
        "study_id": _non_empty_text(payload.get("study_id")),
        "quest_id": _non_empty_text(payload.get("quest_id")),
        "decision": _non_empty_text(payload.get("decision")),
        "reason": _non_empty_text(payload.get("reason")),
        "hold_reason": "flapping_circuit_breaker_active",
        "recommended_probe": "refresh_runtime_liveness_before_resume",
        "flapping_episode_count": int(flapping_report.get("flapping_episode_count") or 0),
    }
