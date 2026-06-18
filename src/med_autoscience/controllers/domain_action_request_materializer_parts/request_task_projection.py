from __future__ import annotations

from collections.abc import Iterable, Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import (
    currentness_identity,
)


def request_task_ref_projections(
    tasks: Iterable[Mapping[str, Any]],
    *,
    schema_version: int,
    target_runtime_owner: str,
    transition_runtime_postcondition: Mapping[str, Any],
    authority_boundary: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        _request_task_ref_projection(
            task,
            schema_version=schema_version,
            target_runtime_owner=target_runtime_owner,
            transition_runtime_postcondition=transition_runtime_postcondition,
            authority_boundary=authority_boundary,
        )
        for task in tasks
    ]


def legacy_request_task_diagnostics(
    request_task_refs: Iterable[Mapping[str, Any]],
    *,
    schema_version: int,
) -> dict[str, Any]:
    refs = [dict(item) for item in request_task_refs if isinstance(item, Mapping)]
    return {
        "surface": "legacy_request_task_diagnostics",
        "schema_version": schema_version,
        "canonical_transition_request_surface": "domain_progress_transition_requests",
        "diagnostic_only": True,
        "diagnostic_ref_only": True,
        "counts_authority": False,
        "readiness_authority": False,
        "can_create_success_outcome": False,
        "body_authority": False,
        "body_projection": False,
        "legacy_payload_scope": "identity_refs_only",
        "legacy_request_task_count": len(refs),
        "legacy_request_task_refs": refs,
        "legacy_request_task_body_omitted": True,
        "legacy_alias_field": "request_tasks",
        "legacy_alias_retirement_gate": "no_active_caller_before_physical_delete",
        "omitted_body_fields": [
            "handoff_packet",
            "owner_route",
            "operator_payload",
            "payload_authoring_target",
            "source_action",
        ],
    }


def _request_task_ref_projection(
    task: Mapping[str, Any],
    *,
    schema_version: int,
    target_runtime_owner: str,
    transition_runtime_postcondition: Mapping[str, Any],
    authority_boundary: Mapping[str, Any],
) -> dict[str, Any]:
    payload = _mapping(task)
    owner_pickup = _mapping(payload.get("owner_pickup"))
    refs = _mapping(payload.get("refs"))
    owner_route = _mapping(payload.get("owner_route"))
    source_action = _mapping(payload.get("source_action"))
    currentness_basis = currentness_identity.normalize_currentness_sources(
        currentness_identity.owner_route_basis(owner_route),
        currentness_identity.action_basis(payload),
        currentness_identity.action_basis(source_action),
    )
    request_ref = {
        "surface": "supervisor_request_handoff_task_ref",
        "schema_version": schema_version,
        "diagnostic_ref_only": True,
        "payload_body_omitted": True,
        "request_packet_body_omitted": True,
        "handoff_packet_body_omitted": True,
        "source_action_body_omitted": True,
        "owner_route_body_omitted": True,
        "operator_payload_body_omitted": True,
        "payload_authoring_target_body_omitted": True,
        "body_authority": False,
        "request_packet_authority": False,
        "can_create_success_outcome": False,
        "readiness_authority": False,
        "study_id": _text(payload.get("study_id")),
        "quest_id": _text(payload.get("quest_id")),
        "action_type": _text(payload.get("action_type")),
        "action_id": _text(payload.get("action_id")),
        "reason": _text(payload.get("reason")),
        "authority": _text(payload.get("authority")),
        "request_owner": _text(payload.get("request_owner")),
        "expected_owner": _text(payload.get("expected_owner")),
        "next_executable_owner": _text(payload.get("next_executable_owner")),
        "required_output_surface": _text(payload.get("required_output_surface")),
        "required_output_target_surface": _mapping(payload.get("required_output_target_surface")) or None,
        "surface_key": _text(payload.get("surface_key")),
        "readiness_surface_identity": _mapping(payload.get("readiness_surface_identity")) or None,
        "operator_payload_ref": _text(payload.get("operator_payload_ref")),
        "operator_payload_present": payload.get("operator_payload_present"),
        "request_packet_ref": _text(payload.get("request_packet_ref")),
        "idempotency_key": _text(payload.get("idempotency_key")),
        "work_unit_id": _text(currentness_basis.get("work_unit_id"))
        or _text(payload.get("work_unit_id"))
        or _text(source_action.get("work_unit_id"))
        or _text(source_action.get("next_work_unit")),
        "work_unit_fingerprint": _text(currentness_basis.get("work_unit_fingerprint"))
        or _text(payload.get("work_unit_fingerprint"))
        or _text(payload.get("action_fingerprint"))
        or _text(source_action.get("work_unit_fingerprint"))
        or _text(source_action.get("action_fingerprint")),
        "action_fingerprint": _text(payload.get("action_fingerprint"))
        or _text(source_action.get("action_fingerprint")),
        "owner_route_current": payload.get("owner_route_current"),
        "dispatch_status": _text(payload.get("dispatch_status")),
        "blocked_reason": _text(payload.get("blocked_reason")),
        "dry_run": payload.get("dry_run"),
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
        "mas_local_request_packet_persistence": "forbidden",
        "mas_dispatch_authority": False,
        "mas_creates_owner_callable_carrier": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "target_runtime_owner": target_runtime_owner,
        "opl_transition_runtime_required_for_durable_carrier": True,
        "opl_transition_runtime_postcondition": dict(transition_runtime_postcondition),
        "authority_boundary": dict(authority_boundary),
        "currentness_basis": currentness_basis or None,
        "owner_pickup": _request_task_owner_pickup_ref(owner_pickup),
        "refs": _request_task_refs(refs),
        "canonical_transition_request_surface": "domain_progress_transition_requests",
    }
    return {key: value for key, value in request_ref.items() if value is not None}


def _request_task_owner_pickup_ref(owner_pickup: Mapping[str, Any]) -> dict[str, Any] | None:
    if not owner_pickup:
        return None
    pickup_ref = {
        "owner": _text(owner_pickup.get("owner")),
        "state": _text(owner_pickup.get("state")),
        "required_output_surface": _text(owner_pickup.get("required_output_surface")),
        "required_output_target_surface": _mapping(owner_pickup.get("required_output_target_surface")) or None,
        "idempotency_key": _text(owner_pickup.get("idempotency_key")),
        "request_packet_ref": _text(owner_pickup.get("request_packet_ref")),
        "supervisor_authority_boundary": _text(owner_pickup.get("supervisor_authority_boundary")),
        "diagnostic_ref_only": True,
        "owner_route_body_omitted": True,
    }
    return {key: value for key, value in pickup_ref.items() if value is not None}


def _request_task_refs(refs: Mapping[str, Any]) -> dict[str, Any] | None:
    if not refs:
        return None
    ref_projection = {
        "scan_latest": _text(refs.get("scan_latest")),
        "request_packet_path": _text(refs.get("request_packet_path")),
    }
    return {key: value for key, value in ref_projection.items() if value is not None} or None


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = ["legacy_request_task_diagnostics", "request_task_ref_projections"]
