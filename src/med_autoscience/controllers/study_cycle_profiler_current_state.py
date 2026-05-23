from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping

from med_autoscience.controllers import auto_runtime_parking


def _text_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [text for item in value if (text := str(item or "").strip())]


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _external_submission_metadata_pending(payload: Mapping[str, Any] | None) -> bool:
    if not isinstance(payload, Mapping):
        return False
    state = _text(
        payload.get("submission_metadata_state")
        or payload.get("external_submission_metadata_state")
        or payload.get("metadata_state")
    )
    if state in {"pending", "required", "missing", "external_metadata_pending"}:
        return True
    return payload.get("external_submission_metadata_pending") is True


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
        publishability_gate_is_clear(publishability_gate_latest)
        and supervisor_phase == "bundle_stage_ready"
        and current_required_action in {"continue_bundle_stage", "complete_bundle_stage"}
        and _external_submission_metadata_pending(publishability_gate_latest)
    ):
        domain_reason = "quest_waiting_for_submission_metadata"
        domain_decision = "blocked"
        parked = auto_runtime_parking.build_auto_runtime_parked_projection(
            {
                "reason": domain_reason,
                "decision": domain_decision,
            }
        )
        return {
            "state": "auto_runtime_parked",
            "auto_runtime_parked": parked,
            "parked_state": parked.get("parked_state"),
            "supervisor_phase": supervisor_phase,
            "current_required_action": current_required_action,
            "summary": parked.get("summary") or "Current status is parked at a submission handoff state.",
        }
    return {
        "state": "active_or_unresolved",
        "supervisor_phase": supervisor_phase or None,
        "current_required_action": current_required_action or None,
    }
