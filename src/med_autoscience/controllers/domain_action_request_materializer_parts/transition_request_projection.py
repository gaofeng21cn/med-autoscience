from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_action_request_materializer_parts import (
    currentness_identity,
    transition_request_record_fields,
)

TARGET_RUNTIME_OWNER = "one-person-lab"
_OPL_TRANSITION_RUNTIME_POSTCONDITION = {
    "surface_kind": "opl_domain_progress_transition_runtime_postcondition",
    "required_owner_surface": "one-person-lab DomainProgressTransitionRuntime",
    "mas_surface_role": "domain_intent_and_policy_request_projection",
    "mas_can_satisfy_readback": False,
    "request_projection_only": True,
    "required_readback_shape": {
        "identity": True,
        "causality": True,
        "authority_boundary": True,
        "exactly_one_outcome": True,
        "projection_metadata": True,
        "event_id": True,
        "outbox_item_id": True,
        "stage_run_identity": True,
    },
    "mas_projection_cannot_replace": [
        "opl_command",
        "opl_event",
        "opl_transactional_outbox",
        "opl_stage_run",
        "opl_provider_admission",
        "opl_fixed_point_reconcile",
    ],
}
_MAS_TRANSITION_PROJECTION_AUTHORITY_BOUNDARY = {
    "mas_materializes_domain_intent": True,
    "mas_creates_owner_callable_carrier": False,
    "mas_creates_opl_outbox": False,
    "mas_creates_opl_event": False,
    "mas_creates_opl_stage_run": False,
    "mas_dispatch_authority": False,
    "provider_admission_pending": False,
    "can_create_success_outcome": False,
    "can_select_next_action": False,
    "target_runtime_owner": TARGET_RUNTIME_OWNER,
    "execution_requires_opl_authorization": True,
    "durable_carrier_owner": TARGET_RUNTIME_OWNER,
    "projection_only": True,
}


def domain_progress_transition_request_projection(dispatches: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for dispatch in dispatches:
        record = _domain_progress_transition_request_record(dispatch)
        if record:
            records.append(record)
    for record in records:
        record["projection_source"] = "domain_action_request_materializer"
        record["legacy_owner_callable_adapter_readback"] = False
        record["domain_intent_producer"] = "med_autoscience.paper_progress_policy_adapter"
        record["durable_carrier_owner"] = TARGET_RUNTIME_OWNER
        record["opl_transition_runtime_required_for_durable_carrier"] = True
        _apply_transition_projection_boundary(record)
    return records



def _domain_progress_transition_request_record(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    request = _mapping(dispatch.get("opl_domain_progress_transition_request")) or _mapping(
        _mapping(dispatch.get("prompt_contract")).get("opl_domain_progress_transition_request")
    )
    record = {
        **_transition_request_identity_fields(dispatch),
        "surface": "mas_domain_progress_transition_request_projection",
        "legacy_surface": _text(dispatch.get("legacy_surface")) or _text(dispatch.get("surface")),
        "legacy_owner_callable_adapter_readback": False,
        "legacy_owner_callable_adapter_missing_opl_request": not bool(request),
        "opl_domain_progress_transition_request": request or None,
        "domain_intent": _mapping(dispatch.get("domain_intent")) or None,
        "authority_boundary": _mapping(dispatch.get("authority_boundary")) or None,
        "stage_transition_authority_boundary": _mapping(dispatch.get("stage_transition_authority_boundary"))
        or None,
        **transition_request_record_fields.transition_request_record_extra_fields(
            dispatch,
            text=_text,
            mapping=_mapping,
        ),
        "refs": _mapping(dispatch.get("refs")) or None,
        "source_action": _mapping(dispatch.get("source_action")) or None,
        "owner_route": _mapping(dispatch.get("owner_route")) or None,
        "prompt_contract_ref": _mapping(dispatch.get("prompt_contract")) or None,
        "progress_first_closeout_admission": _mapping(dispatch.get("progress_first_closeout_admission"))
        or None,
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
        "mas_dispatch_authority": False,
        "mas_creates_owner_callable_carrier": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "target_runtime_owner": _text(dispatch.get("target_runtime_owner")) or TARGET_RUNTIME_OWNER,
        "dispatch_status": _text(dispatch.get("dispatch_status")) or "transition_request_pending",
        "blocked_reason": _text(dispatch.get("blocked_reason")),
    }
    _apply_transition_projection_boundary(record)
    if not any(
        record.get(key)
        for key in (
            "study_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "dispatch_path",
        )
    ):
        return {}
    return {key: value for key, value in record.items() if value is not None}


def _transition_request_identity_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    refs = _mapping(payload.get("refs"))
    source_action = _mapping(payload.get("source_action"))
    prompt_contract = _mapping(payload.get("prompt_contract"))
    request = _mapping(payload.get("opl_domain_progress_transition_request")) or _mapping(
        prompt_contract.get("opl_domain_progress_transition_request")
    )
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    owner_route_source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _transition_request_currentness_basis(
        payload=payload,
        request=request,
        prompt_contract=prompt_contract,
        owner_route=owner_route,
        source_action=source_action,
    )
    return {
        key: value
        for key, value in {
            "study_id": _first_text(
                payload,
                request,
                prompt_contract,
                source_action,
                key="study_id",
            ),
            "quest_id": _first_text(
                payload,
                request,
                prompt_contract,
                source_action,
                key="quest_id",
            ),
            "action_type": _first_text(
                payload,
                request,
                prompt_contract,
                source_action,
                key="action_type",
            ),
            "route_identity_key": _first_text(
                payload,
                request,
                prompt_contract,
                refs,
                owner_route,
                owner_route_source_refs,
                currentness_basis,
                key="route_identity_key",
            ),
            "attempt_idempotency_key": _first_text(
                payload,
                request,
                prompt_contract,
                refs,
                owner_route,
                owner_route_source_refs,
                currentness_basis,
                key="attempt_idempotency_key",
            ),
            "work_unit_id": (
                _text(payload.get("work_unit_id"))
                or _text(payload.get("next_work_unit"))
                or _text(source_action.get("work_unit_id"))
                or _text(request.get("work_unit_id"))
                or _text(prompt_contract.get("work_unit_id"))
                or _text(owner_route_source_refs.get("work_unit_id"))
                or _text(currentness_basis.get("work_unit_id"))
            ),
            "work_unit_fingerprint": (
                _text(payload.get("work_unit_fingerprint"))
                or _text(payload.get("action_fingerprint"))
                or _text(source_action.get("work_unit_fingerprint"))
                or _text(request.get("work_unit_fingerprint"))
                or _text(prompt_contract.get("work_unit_fingerprint"))
                or _text(owner_route.get("work_unit_fingerprint"))
                or _text(owner_route_source_refs.get("work_unit_fingerprint"))
                or _text(currentness_basis.get("work_unit_fingerprint"))
            ),
            "action_fingerprint": _text(payload.get("action_fingerprint"))
            or _text(payload.get("work_unit_fingerprint")),
            "next_executable_owner": _text(payload.get("next_executable_owner"))
            or _text(request.get("next_owner"))
            or _text(prompt_contract.get("next_executable_owner")),
            "required_output_surface": _text(payload.get("required_output_surface"))
            or _text(request.get("required_output_surface"))
            or _text(prompt_contract.get("required_output_surface")),
            "dispatch_authority": _text(payload.get("dispatch_authority"))
            or _text(request.get("dispatch_authority")),
            "dispatch_path": _text(payload.get("dispatch_path")) or _text(refs.get("dispatch_path")),
            "stage_packet_ref": _text(payload.get("stage_packet_ref")) or _text(refs.get("stage_packet_ref")),
            "stage_packet_refs": payload.get("stage_packet_refs") or refs.get("stage_packet_refs"),
            "currentness_basis": currentness_basis or None,
        }.items()
        if value is not None
    }


def _transition_request_currentness_basis(
    *,
    payload: Mapping[str, Any],
    request: Mapping[str, Any],
    prompt_contract: Mapping[str, Any],
    owner_route: Mapping[str, Any],
    source_action: Mapping[str, Any],
) -> dict[str, Any]:
    return currentness_identity.normalize_currentness_sources(
        _mapping(request.get("currentness_basis")),
        currentness_identity.owner_route_basis(owner_route),
        _mapping(prompt_contract.get("owner_route_currentness_basis")),
        _mapping(source_action.get("owner_route_currentness_basis")),
        currentness_identity.action_basis(payload),
        currentness_identity.action_basis(source_action),
    )


def _first_text(*payloads: Mapping[str, Any], key: str) -> str | None:
    for payload in payloads:
        value = _text(payload.get(key))
        if value is not None:
            return value
    return None



def _apply_transition_projection_boundary(payload: dict[str, Any]) -> dict[str, Any]:
    payload["provider_admission_pending"] = False
    payload["provider_admission_requires_opl_runtime_result"] = True
    payload["provider_completion_is_domain_completion"] = False
    payload["mas_dispatch_authority"] = False
    payload["mas_creates_owner_callable_carrier"] = False
    payload["mas_creates_opl_outbox"] = False
    payload["mas_creates_opl_event"] = False
    payload["mas_creates_opl_stage_run"] = False
    payload["target_runtime_owner"] = TARGET_RUNTIME_OWNER
    payload["opl_transition_runtime_required_for_durable_carrier"] = True
    payload["opl_transition_runtime_postcondition"] = _opl_transition_runtime_postcondition()
    authority_boundary = dict(_mapping(payload.get("authority_boundary")))
    authority_boundary.update(_mas_transition_projection_authority_boundary())
    payload["authority_boundary"] = authority_boundary
    return payload


def _opl_transition_runtime_postcondition() -> dict[str, Any]:
    return {
        key: dict(value) if isinstance(value, Mapping) else list(value) if isinstance(value, list) else value
        for key, value in _OPL_TRANSITION_RUNTIME_POSTCONDITION.items()
    }


def _mas_transition_projection_authority_boundary() -> dict[str, Any]:
    return dict(_MAS_TRANSITION_PROJECTION_AUTHORITY_BOUNDARY)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = ["domain_progress_transition_request_projection"]
