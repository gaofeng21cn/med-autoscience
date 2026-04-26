from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item or "").strip())]


def _read_json_mapping(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8")) or {}
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(payload, dict):
        return None
    return dict(payload)


def publishability_gate_is_clear(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False
    status = str(payload.get("status") or "").strip()
    blockers = _text_list(payload.get("blockers"))
    return status == "clear" and payload.get("allow_write") is True and not blockers


def current_state_summary(
    *,
    study_root: Path,
    publishability_gate_latest: Mapping[str, Any] | None,
) -> dict[str, Any]:
    latest_runtime_supervision = _read_json_mapping(
        study_root / "artifacts" / "runtime" / "runtime_supervision" / "latest.json"
    )
    runtime_reason = (
        str((latest_runtime_supervision or {}).get("runtime_reason") or "").strip()
        if isinstance(latest_runtime_supervision, Mapping)
        else ""
    )
    runtime_decision = (
        str((latest_runtime_supervision or {}).get("runtime_decision") or "").strip()
        if isinstance(latest_runtime_supervision, Mapping)
        else ""
    )
    supervisor_phase = (
        str((publishability_gate_latest or {}).get("supervisor_phase") or "").strip()
        if isinstance(publishability_gate_latest, Mapping)
        else ""
    )
    current_required_action = (
        str((publishability_gate_latest or {}).get("current_required_action") or "").strip()
        if isinstance(publishability_gate_latest, Mapping)
        else ""
    )
    if (
        runtime_reason == "quest_waiting_for_submission_metadata"
        and runtime_decision in {"blocked", "pause", ""}
        and publishability_gate_is_clear(publishability_gate_latest)
        and supervisor_phase == "bundle_stage_ready"
        and current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}
    ):
        return {
            "state": "manual_finishing",
            "runtime_reason": runtime_reason,
            "runtime_decision": runtime_decision or None,
            "supervisor_phase": supervisor_phase,
            "current_required_action": current_required_action,
            "summary": "Current status is parked at a milestone package/manual-finishing state.",
        }
    return {
        "state": "active_or_unresolved",
        "runtime_reason": runtime_reason or None,
        "runtime_decision": runtime_decision or None,
        "supervisor_phase": supervisor_phase or None,
        "current_required_action": current_required_action or None,
    }
