from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable

from med_autoscience.controllers import medical_paper_readiness_payload_authoring
from med_autoscience.controllers.owner_callable_action_policy import (
    request_packet_ref_for_action_type,
)
from med_autoscience.profiles import WorkspaceProfile


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def readiness_dispatch_enrichment(
    action: Mapping[str, Any],
    action_type: str,
    *,
    schema_version: int,
    profile: WorkspaceProfile | None = None,
    study_root: Callable[[WorkspaceProfile, str], Path],
) -> dict[str, Any]:
    if action_type != READINESS_ACTION_TYPE:
        return {}
    handoff_packet = _mapping(action.get("handoff_packet"))
    surface_key = (
        _text(action.get("surface_key"))
        or _text(handoff_packet.get("surface_key"))
        or _text(_mapping(action.get("next_action")).get("surface_key"))
        or _text(_mapping(handoff_packet.get("next_action")).get("surface_key"))
    )
    if surface_key is None:
        return {}
    readiness_surface_identity = {
        "action_type": READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "source": _text(action.get("source"))
        or _text(handoff_packet.get("source"))
        or "current_owner_action",
    }
    operator_payload = (
        _mapping(action.get("operator_payload"))
        or _mapping(action.get("medical_paper_readiness_payload"))
        or _mapping(handoff_packet.get("operator_payload"))
        or _mapping(handoff_packet.get("medical_paper_readiness_payload"))
    )
    if not operator_payload and profile is not None:
        study_id = _text(action.get("study_id")) or _text(handoff_packet.get("study_id"))
        if study_id:
            authored = medical_paper_readiness_payload_authoring.author_operator_payload(
                study_root=study_root(profile, study_id),
                surface_key=surface_key,
            )
            if _text(authored.get("status")) != "blocked":
                operator_payload = authored
    payload_authoring_target = {
        "surface": "medical_paper_readiness_operator_payload_authoring_target",
        "schema_version": schema_version,
        "study_id": _text(action.get("study_id")),
        "quest_id": _text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
        "action_type": READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "operator_payload": operator_payload or None,
        "operator_payload_contract": {
            "required": ["operator_payload"],
            "payload_owner": "MedAutoScience",
            "surface_key": surface_key,
            "payload_must_be_domain_authored": True,
            "empty_payload_is_not_success_evidence": True,
        },
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
    }
    request_packet_ref = request_packet_ref_for_action_type(READINESS_ACTION_TYPE)
    return {
        "readiness_surface_identity": readiness_surface_identity,
        "surface_key": surface_key,
        "operator_payload_ref": request_packet_ref,
        "medical_paper_readiness_payload_ref": request_packet_ref,
        "operator_payload_present": bool(operator_payload),
        "operator_payload": operator_payload if operator_payload else None,
        "medical_paper_readiness_payload": operator_payload if operator_payload else None,
        "payload_authoring_target": payload_authoring_target,
    }


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = ["READINESS_ACTION_TYPE", "readiness_dispatch_enrichment"]
