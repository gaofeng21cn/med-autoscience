from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts import provider_admission
from med_autoscience.controllers.owner_route_reconcile_parts import current_owner_action_identity


def current_control_payload(
    *,
    studies: list[dict[str, Any]],
    action_queue: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "surface": "opl_current_control_state_handoff",
        "studies": studies,
        "action_queue": [
            {
                **dict(action),
                "status": _text(action.get("status")) or "queued",
            }
            for action in action_queue
            if isinstance(action, Mapping)
        ],
    }


def candidates_from_current_control(
    *,
    studies: list[dict[str, Any]],
    action_queue: list[dict[str, Any]],
    current_control_ref: str,
) -> list[dict[str, Any]]:
    current_control = current_control_payload(studies=studies, action_queue=action_queue)
    actions_by_study_id: dict[str, list[dict[str, Any]]] = {}
    for action in current_control["action_queue"]:
        study_id = _text(action.get("study_id"))
        if study_id is None:
            continue
        actions_by_study_id.setdefault(study_id, []).append(dict(action))
    candidates: list[dict[str, Any]] = []
    for study in studies:
        study_id = _text(study.get("study_id"))
        study_root_text = _text(study.get("study_root"))
        if study_id is None or study_root_text is None:
            continue
        study_actions = actions_by_study_id.get(study_id, [])
        status_payload = {
            "study_id": study_id,
            "current_execution_envelope": _mapping(study.get("current_execution_envelope")),
            "current_executable_owner_action": current_owner_action_identity.current_executable_owner_action_identity_from_study(
                study=study,
                fallback_action=study_actions[0] if study_actions else {},
            ),
        }
        candidates.extend(
            provider_admission.current_control_provider_admission_candidates(
                current_control,
                study_root=Path(study_root_text),
                status_payload=status_payload,
                current_control_ref=current_control_ref,
            )
        )
    return candidates


def attach_candidates(
    *,
    studies: list[dict[str, Any]],
    candidates: list[dict[str, Any]],
) -> None:
    by_study_id: dict[str, list[dict[str, Any]]] = {}
    for candidate in candidates:
        study_id = _text(candidate.get("study_id"))
        if study_id is None:
            continue
        by_study_id.setdefault(study_id, []).append(dict(candidate))
    for study in studies:
        study_candidates = by_study_id.get(_text(study.get("study_id")) or "", [])
        study["provider_admission_pending_count"] = len(study_candidates)
        study["provider_admission_candidates"] = study_candidates


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["attach_candidates", "candidates_from_current_control", "current_control_payload"]
