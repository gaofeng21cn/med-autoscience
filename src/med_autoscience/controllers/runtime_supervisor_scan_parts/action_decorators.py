from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def decorate_action(
    *,
    study_id: str,
    quest_id: str | None,
    action: Mapping[str, Any],
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> dict[str, Any]:
    decorated = dict(action)
    action_type = _text(decorated.get("action_type")) or "unknown_action"
    reason = _text(decorated.get("reason")) or action_type
    decorated.setdefault("reason", reason)
    decorated["action_id"] = _action_id(study_id=study_id, action_type=action_type, reason=reason)
    decorated["handoff_packet"] = _handoff_packet(
        study_id=study_id,
        quest_id=quest_id,
        action=decorated,
        request_allowed_write_surfaces=request_allowed_write_surfaces,
        control_allowed_write_surfaces=control_allowed_write_surfaces,
        forbidden_actions=forbidden_actions,
    )
    decorated.setdefault("status", "queued")
    decorated.setdefault("quality_gate_relaxation_allowed", False)
    decorated.setdefault("paper_package_mutation_allowed", False)
    decorated.setdefault("manual_study_patch_allowed", False)
    decorated.setdefault("medical_claim_authoring_allowed", False)
    decorated.setdefault("allowed_write_surfaces", list(request_allowed_write_surfaces))
    decorated.setdefault("forbidden_actions", list(forbidden_actions))
    return decorated


def _action_id(*, study_id: str, action_type: str, reason: str | None) -> str:
    suffix = reason or action_type
    return f"supervisor-action::{study_id}::{action_type}::{suffix}"


def _owner_from_action(action: Mapping[str, Any]) -> str | None:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or _text(handoff_packet.get("next_executable_owner"))
    )


def _handoff_packet(
    *,
    study_id: str,
    quest_id: str | None,
    action: Mapping[str, Any],
    request_allowed_write_surfaces: list[str],
    control_allowed_write_surfaces: list[str],
    forbidden_actions: list[str],
) -> dict[str, Any]:
    authority = _text(action.get("authority")) or "observability_only"
    owner = _owner_from_action(action)
    recommended_owner = owner or ("external_engineering_agent" if authority == "external_supervisor" else authority)
    return {
        "packet_type": "external_supervisor_handoff",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": quest_id,
        "action_type": _text(action.get("action_type")),
        "reason": _text(action.get("reason")) or _text(action.get("action_type")),
        "authority": authority,
        "owner": owner,
        "request_owner": _text(action.get("request_owner")) or owner,
        "recommended_owner": recommended_owner,
        "next_executable_owner": recommended_owner,
        "supervisor_authority_boundary": "request_only" if authority == "observability_only" else "control_handoff",
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "allowed_write_surfaces": (
            list(control_allowed_write_surfaces)
            if authority == "external_supervisor"
            else list(request_allowed_write_surfaces)
        ),
        "forbidden_actions": list(forbidden_actions),
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["decorate_action"]
