from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from med_autoscience.profiles import WorkspaceProfile


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def readiness_surface_identity(
    *,
    action_type: str,
    current_owner_action: Mapping[str, Any],
) -> dict[str, str] | None:
    if action_type != READINESS_ACTION_TYPE:
        return None
    if _text(current_owner_action.get("action_type")) != READINESS_ACTION_TYPE:
        return None
    target_surface = _mapping(current_owner_action.get("target_surface"))
    next_action = _mapping(current_owner_action.get("next_action"))
    surface_key = (
        _text(current_owner_action.get("surface_key"))
        or _text(target_surface.get("surface_key"))
        or _text(next_action.get("surface_key"))
    )
    if surface_key is None:
        return None
    return {
        "action_type": READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "source": _text(current_owner_action.get("source")) or "current_owner_action",
    }


def dispatch_with_readiness_surface_identity(
    *,
    dispatch: Mapping[str, Any],
    readiness_surface_identity: Mapping[str, Any] | None,
) -> Mapping[str, Any]:
    identity = _mapping(readiness_surface_identity)
    surface_key = _text(identity.get("surface_key"))
    if surface_key is None:
        return dispatch
    previous_surface_key = _declared_surface_key(dispatch)
    updated = dict(dispatch)
    updated["readiness_surface_identity"] = {
        "action_type": _text(identity.get("action_type")) or READINESS_ACTION_TYPE,
        "surface_key": surface_key,
        "source": _text(identity.get("source")) or "current_owner_action",
    }
    updated["surface_key"] = surface_key
    prompt_contract = dict(_mapping(updated.get("prompt_contract")))
    prompt_contract["readiness_surface_identity"] = dict(updated["readiness_surface_identity"])
    prompt_contract["surface_key"] = surface_key
    updated["prompt_contract"] = prompt_contract
    if previous_surface_key is not None and previous_surface_key != surface_key:
        updated = _drop_stale_readiness_payloads(dispatch=updated, surface_key=surface_key)
    target = dict(_mapping(updated.get("payload_authoring_target")))
    if target:
        target["readiness_surface_identity"] = dict(updated["readiness_surface_identity"])
        target["surface_key"] = surface_key
        contract = dict(_mapping(target.get("operator_payload_contract")))
        if contract:
            contract["surface_key"] = surface_key
            target["operator_payload_contract"] = contract
        payload = dict(_mapping(target.get("operator_payload")))
        if payload:
            payload["surface_key"] = surface_key
            target["operator_payload"] = payload
        updated["payload_authoring_target"] = target
    if updated == dict(dispatch):
        return dispatch
    return updated


def persist_readiness_request_packet(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> None:
    if _text(dispatch.get("action_type")) != READINESS_ACTION_TYPE:
        return
    packet = _readiness_request_packet_from_dispatch(study_id=study_id, dispatch=dispatch)
    if not packet:
        return
    path = _readiness_request_packet_path(profile=profile, study_id=study_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _drop_stale_readiness_payloads(*, dispatch: dict[str, Any], surface_key: str) -> dict[str, Any]:
    prompt_contract = dict(_mapping(dispatch.get("prompt_contract")))
    for container in (dispatch, prompt_contract):
        for key in ("operator_payload", "medical_paper_readiness_payload"):
            payload = _mapping(container.get(key))
            if payload and not _payload_matches_surface(payload=payload, surface_key=surface_key):
                container.pop(key, None)
        container["operator_payload_present"] = bool(
            _mapping(container.get("operator_payload"))
            or _mapping(container.get("medical_paper_readiness_payload"))
        )
        target = dict(_mapping(container.get("payload_authoring_target")))
        if target:
            target["surface_key"] = surface_key
            target["readiness_surface_identity"] = dict(dispatch["readiness_surface_identity"])
            contract = dict(_mapping(target.get("operator_payload_contract")))
            if contract:
                contract["surface_key"] = surface_key
                target["operator_payload_contract"] = contract
            payload = _mapping(target.get("operator_payload"))
            if payload and not _payload_matches_surface(payload=payload, surface_key=surface_key):
                target.pop("operator_payload", None)
            container["payload_authoring_target"] = target
    dispatch["prompt_contract"] = prompt_contract
    return dispatch


def _payload_matches_surface(*, payload: Mapping[str, Any], surface_key: str) -> bool:
    payload_surface_key = _payload_surface_key(payload)
    return payload_surface_key == surface_key


def _payload_surface_key(payload: Mapping[str, Any]) -> str | None:
    if text := _text(payload.get("surface_key")):
        return text
    surface = _text(payload.get("surface"))
    aliases = {
        "literature_intelligence_os": "literature_scout",
        "study_line_decision": "study_line_selection",
        "study_line_selection_scorecard": "study_line_selection",
        "archetype_specific_analysis_contract": "archetype_analysis_contract",
        "route_control_stoploss": "stop_loss_memo",
        "target_journal_writing_layer": "target_journal_writing_layer",
    }
    if surface in aliases:
        return aliases[surface]
    return surface


def _declared_surface_key(dispatch: Mapping[str, Any]) -> str | None:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    for payload in (dispatch, prompt_contract):
        identity = _mapping(payload.get("readiness_surface_identity"))
        if text := _text(identity.get("surface_key")):
            return text
        if text := _text(payload.get("surface_key")):
            return text
    return None


def _readiness_request_packet_from_dispatch(
    *,
    study_id: str,
    dispatch: Mapping[str, Any],
) -> dict[str, Any]:
    prompt_contract = _mapping(dispatch.get("prompt_contract"))
    identity = _mapping(dispatch.get("readiness_surface_identity")) or _mapping(
        prompt_contract.get("readiness_surface_identity")
    )
    surface_key = (
        _text(identity.get("surface_key"))
        or _text(dispatch.get("surface_key"))
        or _text(prompt_contract.get("surface_key"))
    )
    if surface_key is None:
        return {}
    request_ref = "artifacts/supervision/requests/medical_paper_readiness/latest.json"
    operator_payload = _mapping(dispatch.get("operator_payload")) or _mapping(
        dispatch.get("medical_paper_readiness_payload")
    )
    if operator_payload and not _payload_matches_surface(payload=operator_payload, surface_key=surface_key):
        operator_payload = {}
    target = dict(
        _mapping(dispatch.get("payload_authoring_target"))
        or _mapping(prompt_contract.get("payload_authoring_target"))
    )
    if not target:
        target = {
            "surface": "medical_paper_readiness_operator_payload_authoring_target",
            "schema_version": 1,
            "study_id": study_id,
            "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
            "action_type": READINESS_ACTION_TYPE,
            "operator_payload_contract": {
                "required": ["operator_payload"],
                "payload_owner": "MedAutoScience",
                "payload_must_be_domain_authored": True,
                "empty_payload_is_not_success_evidence": True,
            },
            "quality_claim_authorized": False,
            "mechanical_projection_can_authorize_quality": False,
        }
    if target:
        target["surface_key"] = surface_key
        target["readiness_surface_identity"] = dict(identity)
        contract = dict(_mapping(target.get("operator_payload_contract")))
        if contract:
            contract["surface_key"] = surface_key
            target["operator_payload_contract"] = contract
        payload = _mapping(target.get("operator_payload"))
        if payload and not _payload_matches_surface(payload=payload, surface_key=surface_key):
            target.pop("operator_payload", None)
    return {
        "surface": "supervisor_request_handoff_packet",
        "schema_version": 1,
        "study_id": study_id,
        "quest_id": _text(dispatch.get("quest_id")) or _text(prompt_contract.get("quest_id")) or study_id,
        "request_kind": READINESS_ACTION_TYPE,
        "action_type": READINESS_ACTION_TYPE,
        "authority": _text(dispatch.get("authority")) or _text(prompt_contract.get("authority")) or "mas_owner_surface",
        "request_owner": _text(dispatch.get("request_owner"))
        or _text(prompt_contract.get("request_owner"))
        or "MedAutoScience",
        "expected_owner": _text(dispatch.get("expected_owner"))
        or _text(prompt_contract.get("expected_owner"))
        or "MedAutoScience",
        "next_executable_owner": _text(dispatch.get("next_executable_owner"))
        or _text(prompt_contract.get("next_executable_owner"))
        or "MedAutoScience",
        "required_output_surface": _text(dispatch.get("required_output_surface"))
        or _text(prompt_contract.get("required_output_surface"))
        or READINESS_ACTION_TYPE,
        "owner_route": _mapping(dispatch.get("owner_route")) or _mapping(prompt_contract.get("owner_route")) or None,
        "idempotency_key": _text(dispatch.get("idempotency_key")) or _text(prompt_contract.get("idempotency_key")),
        "request_packet_ref": request_ref,
        "readiness_surface_identity": dict(identity),
        "surface_key": surface_key,
        "operator_payload_ref": request_ref,
        "medical_paper_readiness_payload_ref": request_ref,
        "operator_payload_present": bool(operator_payload),
        **(
            {"operator_payload": operator_payload, "medical_paper_readiness_payload": operator_payload}
            if operator_payload
            else {}
        ),
        **({"payload_authoring_target": target} if target else {}),
        "quality_claim_authorized": False,
        "mechanical_projection_can_authorize_quality": False,
        "supervisor_authority_boundary": "request_only",
    }


def _readiness_request_packet_path(*, profile: WorkspaceProfile, study_id: str) -> Path:
    return (
        profile.studies_root
        / study_id
        / "artifacts"
        / "supervision"
        / "requests"
        / "medical_paper_readiness"
        / "latest.json"
    )


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "READINESS_ACTION_TYPE",
    "dispatch_with_readiness_surface_identity",
    "persist_readiness_request_packet",
    "readiness_surface_identity",
]
