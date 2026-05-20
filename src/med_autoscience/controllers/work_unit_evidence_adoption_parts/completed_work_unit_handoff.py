from __future__ import annotations

from pathlib import Path
from typing import Any

from med_autoscience.controllers import control_intent
from med_autoscience.controllers.work_unit_evidence_adoption_parts import generic_completed_work_unit


def existing_adoption_payload(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    existing_payload = _existing_artifact_written_payload(
        study_root=study_root,
        identity=identity,
        authorization_context=authorization_context,
    )
    if existing_payload is None:
        return None
    return {
        **existing_payload,
        "already_recorded": True,
    }


def ensure_existing_completed_handoff(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    evidence_adoption: dict[str, Any],
    source: str,
) -> None:
    if not generic_completed_work_unit.is_completed_adoption_payload(evidence_adoption):
        return
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    if lifecycle.get("terminal_consumed") is True:
        return
    report_ref = _text(evidence_adoption.get("report_ref"))
    if report_ref is None:
        return
    control_intent.append_event(
        study_root=study_root,
        identity=identity,
        event_type="owner_handoff",
        payload=generic_completed_work_unit.owner_handoff_payload(report_path=Path(report_ref), source=source),
    )


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _existing_artifact_written_payload(
    *,
    study_root: Path,
    identity: control_intent.ControlIntentIdentity,
    authorization_context: dict[str, Any],
) -> dict[str, Any] | None:
    payload = _latest_artifact_written_payload(
        control_intent.events_for_business_key_since(
            study_root=study_root,
            business_key=identity.business_key,
            recorded_at=authorization_context.get("decision_emitted_at"),
        )
    )
    if payload is not None:
        return payload
    lifecycle = control_intent.lifecycle_state(study_root=study_root, identity=identity)
    if lifecycle.get("terminal_consumed") is not True:
        return None
    return _latest_artifact_written_payload(
        control_intent.events_for_business_key(
            study_root=study_root,
            business_key=identity.business_key,
        )
    )


def _latest_artifact_written_payload(events: list[dict[str, Any]]) -> dict[str, Any] | None:
    for event in reversed(events):
        event_type = _text(event.get("event_type"))
        if event_type == "delivered":
            return None
        if event_type != "artifact_written":
            continue
        payload = event.get("payload")
        if isinstance(payload, dict):
            return dict(payload)
        return {}
    return None
