from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.opl_execution_boundary import (
    first_trusted_opl_execution_authorization,
)


def trusted_owner_callable_opl_proof(*payloads: object) -> dict[str, Any] | None:
    context_payloads = _iter_payloads(*payloads)
    for payload in context_payloads:
        authorization = _trusted_execution_authorization(payload)
        if authorization is not None:
            return {
                "proof_kind": "trusted_opl_execution_authorization",
                "trusted_opl_execution_authorization": authorization,
            }
        readback = bound_opl_transition_readback(payload, *context_payloads)
        if readback:
            return {
                "proof_kind": "domain_progress_transition_readback",
                "opl_domain_progress_transition_live_readback": readback,
                "opl_domain_progress_transition_result": readback,
            }
    return None


def bound_opl_transition_readback(payload: Mapping[str, Any], *context_payloads: object) -> dict[str, Any]:
    context = _merged_context_payload(payload, *context_payloads)
    return provider_admission_opl_transition_readback(
        context,
        require_explicit_identity=True,
    )


def has_bound_opl_transition_readback(payload: Mapping[str, Any], *context_payloads: object) -> bool:
    return bool(bound_opl_transition_readback(payload, *context_payloads))


def _trusted_execution_authorization(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    owner_route = _mapping(payload.get("owner_route"))
    return first_trusted_opl_execution_authorization(
        payload.get("opl_execution_authorization"),
        payload.get("opl_provider_attempt"),
        payload.get("stage_attempt"),
        prompt_contract.get("opl_execution_authorization"),
        prompt_contract.get("opl_provider_attempt"),
        owner_route.get("opl_execution_authorization"),
        owner_route.get("opl_provider_attempt"),
    )


def _merged_context_payload(payload: Mapping[str, Any], *context_payloads: object) -> dict[str, Any]:
    merged = dict(payload)
    context = _iter_payloads(payload, *context_payloads)
    for key, extractor in (
        ("study_id", _expected_study_ids),
        ("work_unit_id", _expected_work_unit_ids),
        ("work_unit_fingerprint", _expected_work_unit_fingerprints),
        ("route_identity_key", _expected_route_identity_keys),
        ("attempt_idempotency_key", _expected_attempt_idempotency_keys),
    ):
        if _text(merged.get(key)) is None and (value := _single_expected(extractor, context)) is not None:
            merged[key] = value
    if _text(merged.get("idempotency_key")) is None and (
        value := _single_expected(_expected_transition_request_keys, context)
    ) is not None:
        merged["idempotency_key"] = value
    return merged


def _single_expected(extractor: Any, payloads: list[Mapping[str, Any]]) -> str | None:
    values = _union_expected(extractor, payloads)
    return next(iter(values)) if len(values) == 1 else None


def _union_expected(
    extractor: Any,
    payloads: list[Mapping[str, Any]],
) -> set[str]:
    values: set[str] = set()
    for payload in payloads:
        values.update(extractor(payload))
    return values


def _expected_study_ids(payload: Mapping[str, Any]) -> set[str]:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_action = _mapping(payload.get("source_action"))
    return _non_empty_set(
        payload.get("study_id"),
        prompt_contract.get("study_id"),
        owner_route.get("study_id"),
        source_action.get("study_id"),
    )


def _expected_work_unit_ids(payload: Mapping[str, Any]) -> set[str]:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_action = _mapping(payload.get("source_action"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
    return _non_empty_set(
        _work_unit_id(payload.get("work_unit_id")),
        _work_unit_id(payload.get("next_work_unit")),
        _work_unit_id(prompt_contract.get("work_unit_id")),
        _work_unit_id(prompt_contract.get("next_work_unit")),
        _work_unit_id(source_action.get("work_unit_id")),
        _work_unit_id(source_action.get("next_work_unit")),
        _work_unit_id(source_refs.get("work_unit_id")),
        _work_unit_id(currentness_basis.get("work_unit_id")),
        _work_unit_id(transition_request.get("work_unit_id")),
        _work_unit_id(_mapping(transition_request.get("identity")).get("work_unit_id")),
    )


def _expected_work_unit_fingerprints(payload: Mapping[str, Any]) -> set[str]:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_action = _mapping(payload.get("source_action"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
    transition_identity = _mapping(transition_request.get("identity"))
    return _non_empty_set(
        payload.get("work_unit_fingerprint"),
        payload.get("action_fingerprint"),
        prompt_contract.get("work_unit_fingerprint"),
        source_action.get("work_unit_fingerprint"),
        source_action.get("action_fingerprint"),
        owner_route.get("work_unit_fingerprint"),
        source_refs.get("work_unit_fingerprint"),
        currentness_basis.get("work_unit_fingerprint"),
        transition_request.get("work_unit_fingerprint"),
        transition_identity.get("work_unit_fingerprint"),
    )


def _expected_route_identity_keys(payload: Mapping[str, Any]) -> set[str]:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_action = _mapping(payload.get("source_action"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
    transition_identity = _mapping(transition_request.get("identity"))
    stage_identity = _mapping(transition_request.get("stage_run_identity"))
    return _non_empty_set(
        payload.get("route_identity_key"),
        prompt_contract.get("route_identity_key"),
        owner_route.get("route_identity_key"),
        source_action.get("route_identity_key"),
        source_refs.get("route_identity_key"),
        currentness_basis.get("route_identity_key"),
        transition_request.get("route_identity_key"),
        transition_identity.get("route_identity_key"),
        stage_identity.get("route_identity_key"),
    )


def _expected_attempt_idempotency_keys(payload: Mapping[str, Any]) -> set[str]:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    owner_route = _mapping(payload.get("owner_route")) or _mapping(prompt_contract.get("owner_route"))
    source_action = _mapping(payload.get("source_action"))
    source_refs = _mapping(owner_route.get("source_refs"))
    currentness_basis = _mapping(source_refs.get("owner_route_currentness_basis")) or _mapping(
        _mapping(owner_route.get("currentness_contract")).get("basis")
    )
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
    transition_identity = _mapping(transition_request.get("identity"))
    stage_identity = _mapping(transition_request.get("stage_run_identity"))
    return _non_empty_set(
        payload.get("attempt_idempotency_key"),
        prompt_contract.get("attempt_idempotency_key"),
        owner_route.get("attempt_idempotency_key"),
        source_action.get("attempt_idempotency_key"),
        source_refs.get("attempt_idempotency_key"),
        currentness_basis.get("attempt_idempotency_key"),
        transition_request.get("attempt_idempotency_key"),
        transition_identity.get("attempt_idempotency_key"),
        stage_identity.get("attempt_idempotency_key"),
    )


def _expected_transition_request_keys(payload: Mapping[str, Any]) -> set[str]:
    prompt_contract = _mapping(payload.get("prompt_contract"))
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request"))
    transition_identity = _mapping(transition_request.get("identity"))
    return _non_empty_set(
        transition_request.get("idempotency_key"),
        transition_request.get("transition_request_idempotency_key"),
        transition_request.get("mas_transition_request_idempotency_key"),
        transition_identity.get("attempt_idempotency_key"),
        _mapping(payload.get("domain_intent")).get("idempotency_key"),
        _mapping(prompt_contract.get("domain_intent")).get("idempotency_key"),
    )


def _conflicts(expected: set[str], observed_values: list[str | None]) -> bool:
    observed = {value for value in observed_values if value is not None}
    return bool(expected and observed and observed.isdisjoint(expected))


def _iter_payloads(*values: object) -> list[Mapping[str, Any]]:
    payloads: list[Mapping[str, Any]] = []
    stack = list(values)
    seen: set[int] = set()
    while stack:
        value = stack.pop()
        if isinstance(value, Mapping):
            identity = id(value)
            if identity in seen:
                continue
            seen.add(identity)
            payload = _mapping(value)
            payloads.append(payload)
            for key in (
                "prompt_contract",
                "owner_route",
                "source_action",
                "opl_domain_progress_transition_request",
                "paper_progress_policy_result",
                "state",
            ):
                nested = payload.get(key)
                if isinstance(nested, Mapping):
                    stack.append(nested)
            continue
        if isinstance(value, (list, tuple)):
            stack.extend(item for item in value if isinstance(item, Mapping))
    return payloads


def _non_empty_set(*values: object) -> set[str]:
    return {text for value in values if (text := _text(value)) is not None}


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id")) or _text(value.get("work_unit_id"))
    return _text(value)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "bound_opl_transition_readback",
    "has_bound_opl_transition_readback",
    "trusted_owner_callable_opl_proof",
]
