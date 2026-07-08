from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import opl_domain_progress_transition_contract as transition_contract
from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
)
from med_autoscience.controllers.opl_transition_readback import (
    has_opl_transition_readback,
)
from med_autoscience.controllers.provider_admission.provider_admission_boundaries import (
    domain_progress_transition_request_transport_fields,
)

from . import currentness_identity
from . import evidence_gap_decision as evidence_gap_decision_part
from . import materializer_core


TARGET_RUNTIME_OWNER = transition_contract.RUNTIME_OWNER


def runtime_postcondition() -> dict[str, Any]:
    return transition_contract.runtime_postcondition()


def authority_boundary() -> dict[str, Any]:
    return transition_contract.mas_projection_authority_boundary()


def apply_boundary(payload: dict[str, Any]) -> dict[str, Any]:
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
    payload["opl_transition_runtime_postcondition"] = runtime_postcondition()
    authority = dict(materializer_core.mapping(payload.get("authority_boundary")))
    authority.update(authority_boundary())
    payload["authority_boundary"] = authority
    return payload


def with_transition_request_projection(dispatch: Mapping[str, Any]) -> dict[str, Any]:
    payload = dict(dispatch)
    transition_request = materializer_core.mapping(payload.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = transition_request_for_owner_callable_adapter(payload)
    else:
        transition_request = with_owner_route_currentness_basis(
            transition_request,
            payload=payload,
        )
    if transition_request:
        payload["opl_domain_progress_transition_request"] = transition_request
    payload["surface"] = "mas_domain_progress_transition_request_projection"
    payload["legacy_surface"] = materializer_core.text(dispatch.get("surface"))
    payload["projection_only"] = True
    payload["owner_callable_adapter_diagnostic_only"] = True
    payload["owner_callable_adapter_readiness_authority"] = False
    payload["owner_callable_adapter_can_create_success_outcome"] = False
    payload["owner_callable_carrier_projection_only"] = True
    payload["mas_materializes_domain_intent"] = True
    payload["mas_creates_owner_callable_carrier"] = False
    payload["mas_local_dispatch_carrier_persistence"] = "forbidden"
    payload["opl_transition_runtime_required_for_durable_carrier"] = True
    apply_boundary(payload)
    payload.update(domain_progress_transition_request_transport_fields())

    prompt_contract = dict(materializer_core.mapping(payload.get("prompt_contract")))
    if transition_request:
        prompt_contract["opl_domain_progress_transition_request"] = transition_request
    prompt_contract["provider_admission_pending"] = False
    prompt_contract["provider_admission_requires_opl_runtime_result"] = True
    prompt_contract["opl_transition_runtime_postcondition"] = runtime_postcondition()
    prompt_contract.update(domain_progress_transition_request_transport_fields())
    prompt_contract["owner_callable_carrier_projection_only"] = True
    prompt_contract["mas_creates_owner_callable_carrier"] = False
    prompt_contract["mas_local_dispatch_carrier_persistence"] = "forbidden"
    prompt_contract["opl_transition_runtime_required_for_durable_carrier"] = True
    payload["prompt_contract"] = prompt_contract

    if materializer_core.text(payload.get("dispatch_status")) == "ready" and not has_opl_execution_proof(payload):
        payload["dispatch_status"] = "transition_request_pending"
        payload["blocked_reason"] = "opl_execution_authorization_required"
        payload["evidence_gap_inputs"] = [
            *evidence_gap_decision_part.inputs(payload),
            {
                "surface_kind": "opl_transition_runtime_authorization",
                "missing_ref_family": "OPL runtime outbox StageRun authorization currentness",
                "confidence": "high",
            },
        ]
        payload["owner_callable_surface"] = None
        payload["dispatch_ready_for_execution_authority"] = False
        payload["mas_dispatch_authority"] = False
        payload["mas_local_dispatch_carrier_persistence"] = "forbidden"
        payload["opl_transition_runtime_required_for_durable_carrier"] = True
        prompt_contract["dispatch_status"] = "transition_request_pending"
        prompt_contract["owner_callable_surface"] = None
    authority = dict(materializer_core.mapping(payload.get("authority_boundary")))
    authority.update(authority_boundary())
    payload["authority_boundary"] = authority
    projected = evidence_gap_decision_part.projection_for_action(
        payload,
        text=materializer_core.text,
        mapping=materializer_core.mapping,
    )
    projected = {**payload, **projected}
    prompt_contract = dict(materializer_core.mapping(projected.get("prompt_contract")))
    prompt_contract.update(
        evidence_gap_decision_part.prompt_fields(
            projected,
            mapping=materializer_core.mapping,
        )
    )
    projected["prompt_contract"] = prompt_contract
    return projected


def transition_request_for_owner_callable_adapter(payload: Mapping[str, Any]) -> dict[str, Any]:
    study_id = materializer_core.text(payload.get("study_id")) or "unknown-study"
    action_type = materializer_core.text(payload.get("action_type")) or "unknown_action"
    owner_route = materializer_core.mapping(payload.get("owner_route"))
    source_refs = materializer_core.mapping(owner_route.get("source_refs"))
    prompt_contract = materializer_core.mapping(payload.get("prompt_contract"))
    source_action = materializer_core.mapping(payload.get("source_action"))
    currentness_basis = currentness_identity.normalize_currentness_sources(
        currentness_identity.owner_route_basis(owner_route),
        prompt_contract.get("owner_route_currentness_basis"),
        source_action.get("owner_route_currentness_basis"),
        currentness_identity.action_basis(payload),
        currentness_identity.action_basis(source_action),
    )
    work_unit_id = (
        materializer_core.text(payload.get("work_unit_id"))
        or materializer_core.text(source_refs.get("materialized_work_unit_id"))
        or materializer_core.text(source_refs.get("work_unit_id"))
        or materializer_core.text(source_action.get("next_work_unit"))
    )
    work_unit_fingerprint = (
        materializer_core.text(payload.get("work_unit_fingerprint"))
        or materializer_core.text(payload.get("action_fingerprint"))
        or materializer_core.text(source_refs.get("work_unit_fingerprint"))
        or materializer_core.text(owner_route.get("work_unit_fingerprint"))
        or materializer_core.text(payload.get("repeat_suppression_key"))
    )
    return paper_progress_policy_adapter.build_transition_request(
        study_id=study_id,
        quest_id=materializer_core.text(payload.get("quest_id")) or study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        work_unit_fingerprint=work_unit_fingerprint,
        next_owner=materializer_core.text(payload.get("next_executable_owner")),
        source_generation=materializer_core.text(owner_route.get("source_fingerprint"))
        or work_unit_fingerprint,
        expected_version=work_unit_fingerprint,
        dispatch_ref=materializer_core.text(materializer_core.mapping(payload.get("refs")).get("dispatch_path")),
        dispatch_authority=materializer_core.text(payload.get("dispatch_authority")),
        required_output_surface=materializer_core.text(payload.get("required_output_surface")),
        currentness_basis=currentness_basis,
        idempotency_context={
            "action_id": materializer_core.text(payload.get("action_id")),
            "idempotency_key": materializer_core.text(payload.get("idempotency_key")),
            "dispatch_authority": materializer_core.text(payload.get("dispatch_authority")),
        },
    )


def with_owner_route_currentness_basis(
    transition_request: Mapping[str, Any],
    *,
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    request = dict(transition_request)
    owner_route = materializer_core.mapping(payload.get("owner_route"))
    prompt_contract = materializer_core.mapping(payload.get("prompt_contract"))
    source_action = materializer_core.mapping(payload.get("source_action"))
    basis = currentness_identity.normalize_currentness_sources(
        currentness_identity.owner_route_basis(owner_route),
        prompt_contract.get("owner_route_currentness_basis"),
        source_action.get("owner_route_currentness_basis"),
        currentness_identity.action_basis(payload),
        currentness_identity.action_basis(source_action),
    )
    return currentness_identity.normalize_transition_request_currentness(request, basis)


def has_opl_execution_proof(payload: Mapping[str, Any]) -> bool:
    if any(
        has_opl_transition_readback(item)
        for item in iter_payloads(payload)
        if materializer_core.text(item.get("surface_kind")) != "mas_domain_progress_transition_request"
    ):
        return True
    return any(
        first_trusted_opl_execution_authorization(
            item.get("opl_execution_authorization"),
            item.get("opl_provider_attempt"),
            item.get("stage_attempt"),
        )
        is not None
        for item in iter_payloads(payload)
    )


def iter_payloads(value: object) -> list[Mapping[str, Any]]:
    payloads: list[Mapping[str, Any]] = []
    stack = [value]
    seen: set[int] = set()
    while stack:
        item = stack.pop()
        if isinstance(item, Mapping):
            identity = id(item)
            if identity in seen:
                continue
            seen.add(identity)
            payload = materializer_core.mapping(item)
            payloads.append(payload)
            for key in (
                "prompt_contract",
                "owner_route",
                "source_action",
                "opl_domain_progress_transition_request",
                "opl_domain_progress_transition_result",
                "opl_domain_progress_runtime_result",
                "opl_runtime_result",
                "paper_progress_policy_result",
                "state",
            ):
                nested = payload.get(key)
                if isinstance(nested, Mapping):
                    stack.append(nested)
            continue
        if isinstance(item, (list, tuple)):
            stack.extend(candidate for candidate in item if isinstance(candidate, Mapping))
    return payloads


__all__ = [
    "TARGET_RUNTIME_OWNER",
    "apply_boundary",
    "authority_boundary",
    "has_opl_execution_proof",
    "iter_payloads",
    "runtime_postcondition",
    "transition_request_for_owner_callable_adapter",
    "with_owner_route_currentness_basis",
    "with_transition_request_projection",
]
