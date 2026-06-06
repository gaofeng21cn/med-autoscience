from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    RETIRED_ABSENT_SURFACES,
    request_output_surface_for_action_type,
    request_output_target_surface_for_action_type,
    request_owner_for_action_type,
    request_packet_ref_for_action_type,
)
from med_autoscience.runtime_control import owner_route as owner_route_part

READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"


def request_task(
    *,
    action: Mapping[str, Any],
    schema_version: int,
    developer_mode_payload: Mapping[str, Any],
    apply: bool,
    supported_mode: str,
    packet_path: Path,
    scan_latest_path: Path,
    forbidden_surfaces: Iterable[str],
    allowed_write_surfaces: Iterable[str],
) -> dict[str, Any]:
    study_id = _text(action.get("study_id")) or "unknown-study"
    action_type = _text(action.get("action_type")) or "unknown_action"
    handoff_packet = _mapping(action.get("handoff_packet"))
    apply_allowed = (
        apply
        and _text(developer_mode_payload.get("mode")) == supported_mode
        and developer_mode_payload.get("safe_actions_enabled") is True
    )
    blocked_reason = None if apply_allowed or not apply else _github_block_reason(developer_mode_payload, supported_mode)
    authority = _text(action.get("authority")) or _text(handoff_packet.get("authority")) or "observability_only"
    request_owner = _owner_from_action(action, action_type)
    required_output_surface = _required_output_surface(action, action_type)
    required_output_target_surface = request_output_target_surface_for_action_type(action_type)
    request_packet_ref = request_packet_ref_for_action_type(action_type)
    readiness_request = _readiness_request_enrichment(action=action, action_type=action_type)
    owner_route = owner_route_part.ensure_owner_route_v2(
        _mapping(action.get("owner_route")) or _mapping(handoff_packet.get("owner_route"))
    )
    idempotency_key = _text(owner_route.get("idempotency_key"))
    owner_route_current = owner_route_part.route_allows_action(
        action={**dict(action), "next_executable_owner": request_owner, "action_type": action_type},
        owner_route=owner_route,
    )
    blocked_reason = _owner_route_block_reason(
        blocked_reason=blocked_reason,
        apply=apply,
        owner_route_current=owner_route_current,
    )
    dispatch_status = "applied" if apply_allowed and owner_route_current else "dry_run" if not apply else "blocked"
    owner_pickup = _owner_pickup(
        request_owner=request_owner,
        required_output_surface=required_output_surface,
        required_output_target_surface=required_output_target_surface,
        owner_route=owner_route,
        idempotency_key=idempotency_key,
        request_packet_ref=request_packet_ref,
    )
    handoff = request_task_handoff_packet(
        source_handoff=handoff_packet,
        schema_version=schema_version,
        study_id=study_id,
        quest_id=_text(action.get("quest_id")) or _text(handoff_packet.get("quest_id")),
        action_type=action_type,
        authority=authority,
        request_owner=request_owner,
        required_output_surface=required_output_surface,
        required_output_target_surface=required_output_target_surface,
        owner_route=owner_route,
        idempotency_key=idempotency_key,
        request_packet_ref=request_packet_ref,
        owner_pickup=owner_pickup,
        effective_mode=_text(developer_mode_payload.get("mode")),
        readiness_request=readiness_request,
    )
    return {
        "surface": "supervisor_request_handoff_task",
        "schema_version": schema_version,
        "study_id": study_id,
        "quest_id": handoff["quest_id"],
        "action_type": action_type,
        "action_id": _text(action.get("action_id")),
        "reason": _text(action.get("reason")) or _text(handoff_packet.get("reason")),
        "authority": authority,
        "request_owner": request_owner,
        "expected_owner": request_owner,
        "next_executable_owner": request_owner,
        "required_output_surface": required_output_surface,
        **(
            {"required_output_target_surface": required_output_target_surface}
            if required_output_target_surface is not None
            else {}
        ),
        "request_packet_ref": request_packet_ref,
        **readiness_request,
        "owner_pickup": owner_pickup,
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "owner_route_current": owner_route_current,
        "dispatch_status": dispatch_status,
        "blocked_reason": blocked_reason,
        "dry_run": not apply,
        "forbidden_surfaces": list(forbidden_surfaces),
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "allowed_write_surfaces": list(allowed_write_surfaces),
        "github_gate": dict(_mapping(developer_mode_payload.get("github_user_gate"))),
        "effective_mode": _text(developer_mode_payload.get("mode")),
        "requested_mode": _text(developer_mode_payload.get("requested_mode")),
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "platform_code_mutation_allowed": False,
        "source_action": dict(action),
        "handoff_packet": handoff,
        "refs": {"scan_latest": str(scan_latest_path), "request_packet_path": str(packet_path)},
    }


def _owner_route_block_reason(
    *,
    blocked_reason: str | None,
    apply: bool,
    owner_route_current: bool,
) -> str | None:
    if blocked_reason is not None or not apply or owner_route_current:
        return blocked_reason
    return "owner_route_next_owner_mismatch"


def _owner_pickup(
    *,
    request_owner: str,
    required_output_surface: str,
    required_output_target_surface: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any],
    idempotency_key: str | None,
    request_packet_ref: str,
) -> dict[str, Any]:
    pickup = {
        "owner": request_owner,
        "state": "pending",
        "required_output_surface": required_output_surface,
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "request_packet_ref": request_packet_ref,
        "supervisor_authority_boundary": "request_only",
    }
    if required_output_target_surface is not None:
        pickup["required_output_target_surface"] = dict(required_output_target_surface)
    return pickup


def request_task_handoff_packet(
    *,
    source_handoff: Mapping[str, Any],
    schema_version: int,
    study_id: str,
    quest_id: str | None,
    action_type: str,
    authority: str,
    request_owner: str,
    required_output_surface: str,
    required_output_target_surface: Mapping[str, Any] | None,
    owner_route: Mapping[str, Any],
    idempotency_key: str | None,
    request_packet_ref: str,
    owner_pickup: Mapping[str, Any],
    effective_mode: str | None,
    readiness_request: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    readiness_request_payload = dict(readiness_request or {})
    return {
        **dict(source_handoff),
        "surface": "supervisor_request_handoff_packet",
        "schema_version": schema_version,
        "study_id": study_id,
        "quest_id": quest_id,
        "request_kind": _text(source_handoff.get("request_kind")) or action_type,
        "action_type": action_type,
        "authority": authority,
        "request_owner": request_owner,
        "expected_owner": request_owner,
        "next_executable_owner": request_owner,
        "required_output_surface": required_output_surface,
        **(
            {"required_output_target_surface": dict(required_output_target_surface)}
            if required_output_target_surface is not None
            else {}
        ),
        "owner_route": owner_route or None,
        "idempotency_key": idempotency_key,
        "request_packet_ref": request_packet_ref,
        **readiness_request_payload,
        "owner_pickup": dict(owner_pickup),
        "supervisor_authority_boundary": "request_only",
        "consumer_mutation_scope": "supervision_handoff_only",
        "consumer_does_not_mutate": [
            "paper",
            "manuscript",
            "current_package",
            "submission_minimal",
            "publication_eval",
            "medical_claims",
        ],
        "retired_absent_surfaces": list(RETIRED_ABSENT_SURFACES),
        "effective_mode": effective_mode,
        "paper_package_mutation_allowed": False,
        "quality_gate_relaxation_allowed": False,
        "manual_study_patch_allowed": False,
        "medical_claim_authoring_allowed": False,
        "platform_code_mutation_allowed": False,
    }


def _readiness_request_enrichment(*, action: Mapping[str, Any], action_type: str) -> dict[str, Any]:
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
    operator_payload = (
        _mapping(action.get("operator_payload"))
        or _mapping(action.get("medical_paper_readiness_payload"))
        or _mapping(handoff_packet.get("operator_payload"))
        or _mapping(handoff_packet.get("medical_paper_readiness_payload"))
    )
    payload_authoring_target = {
        "surface": "medical_paper_readiness_operator_payload_authoring_target",
        "schema_version": 1,
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
    return {
        "surface_key": surface_key,
        "operator_payload_ref": request_packet_ref_for_action_type(READINESS_ACTION_TYPE),
        "medical_paper_readiness_payload_ref": request_packet_ref_for_action_type(READINESS_ACTION_TYPE),
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


def _github_block_reason(developer_mode_payload: Mapping[str, Any], supported_mode: str) -> str | None:
    if text := _text(developer_mode_payload.get("blocked_reason")):
        return text
    gate = _mapping(developer_mode_payload.get("github_user_gate"))
    if text := _text(gate.get("reason")):
        return text
    if _text(developer_mode_payload.get("mode")) != supported_mode:
        return "developer_apply_safe_required"
    return None


def _owner_from_action(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
        or _text(handoff_packet.get("owner"))
        or _text(handoff_packet.get("request_owner"))
        or _text(handoff_packet.get("recommended_owner"))
        or request_owner_for_action_type(action_type)
    )


def _required_output_surface(action: Mapping[str, Any], action_type: str) -> str:
    handoff_packet = _mapping(action.get("handoff_packet"))
    return (
        _text(action.get("required_output_surface"))
        or _text(handoff_packet.get("required_output_surface"))
        or request_output_surface_for_action_type(action_type)
    )


__all__ = ["request_task", "request_task_handoff_packet"]
