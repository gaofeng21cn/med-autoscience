from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import paper_progress_policy_adapter
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
    non_empty_text as _non_empty_text,
)


def candidate_with_opl_transition_request(
    candidate: Mapping[str, Any],
    *,
    source: str,
    current_action_source: str | None = None,
) -> dict[str, Any]:
    payload = dict(candidate)
    trusted_provider_readback = provider_admission_opl_transition_readback(payload)
    policy_result = _mapping(payload.get("paper_progress_policy_result"))
    transition_request = _mapping(payload.get("opl_domain_progress_transition_request")) or _mapping(
        policy_result.get("opl_domain_progress_transition_request")
    )
    if not policy_result or not transition_request:
        policy_result = paper_progress_policy_adapter.build_policy_result(
            {
                "study_id": _non_empty_text(payload.get("study_id")),
                "quest_id": _non_empty_text(payload.get("quest_id")),
                "current_work_unit": _candidate_current_work_unit(payload),
                "current_executable_owner_action": _candidate_current_action(
                    payload,
                    current_action_source=current_action_source,
                ),
                "paper_recovery_state": _candidate_provider_admission_recovery(payload),
            },
            source=source,
        )
        transition_request = _mapping(policy_result.get("opl_domain_progress_transition_request"))
    transition_request = _transition_request_bound_to_provider_readback(
        transition_request,
        readback=trusted_provider_readback,
    )
    if policy_result:
        policy_payload = dict(policy_result)
        if transition_request:
            policy_payload["opl_domain_progress_transition_request"] = dict(transition_request)
        payload["paper_progress_policy_result"] = policy_payload
    if transition_request:
        payload["opl_domain_progress_transition_request"] = dict(transition_request)
    has_readback = bool(provider_admission_opl_transition_readback(payload))
    payload["projection_metadata"] = _projection_metadata(
        transition_request=transition_request,
        policy_result=policy_result,
        candidate=payload,
    )
    payload["provider_admission_pending"] = has_readback
    payload["provider_admission_requires_opl_runtime_result"] = not has_readback
    payload.setdefault(
        "status",
        "provider_admission_pending" if has_readback else "transition_request_pending",
    )
    if not has_readback:
        payload["provider_attempt_or_lease_required"] = False
    return payload


def _candidate_current_work_unit(candidate: Mapping[str, Any]) -> dict[str, Any]:
    currentness_basis = _mapping(candidate.get("currentness_basis"))
    return {
        key: value
        for key, value in {
            "surface_kind": "current_work_unit",
            "status": "executable_owner_action",
            "owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "action_type": _non_empty_text(candidate.get("action_type")),
            "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
            or _non_empty_text(candidate.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint"))
            or _non_empty_text(candidate.get("work_unit_fingerprint")),
            "currentness_basis": dict(currentness_basis) if currentness_basis else None,
            "projection_metadata": _projection_metadata(
                transition_request=_mapping(candidate.get("opl_domain_progress_transition_request")),
                policy_result=_mapping(candidate.get("paper_progress_policy_result")),
                candidate=candidate,
            ),
        }.items()
        if value not in (None, "", [], {})
    }


def _candidate_provider_admission_recovery(candidate: Mapping[str, Any]) -> dict[str, Any]:
    if provider_admission_opl_transition_readback(candidate):
        return {
            key: value
            for key, value in {
                "surface_kind": "paper_recovery_state",
                "phase": "admission_pending",
                "next_safe_action": {
                    "kind": "admit_provider_attempt",
                    "owner": _non_empty_text(candidate.get("next_executable_owner"))
                    or _non_empty_text(candidate.get("owner")),
                    "provider_admission_allowed": True,
                    "provider_admission_requires_opl_runtime_result": False,
                },
            }.items()
            if value not in (None, "", [], {})
        }
    return {
        key: value
        for key, value in {
            "surface_kind": "paper_recovery_state",
            "phase": "transition_request_pending",
            "next_safe_action": {
                "kind": "await_opl_transition_readback",
                "owner": "one-person-lab",
                "provider_admission_allowed": False,
                "provider_admission_requires_opl_runtime_result": True,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def _transition_request_bound_to_provider_readback(
    transition_request: Mapping[str, Any],
    *,
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    request = dict(transition_request)
    if not request or not readback:
        return request
    identity = _mapping(readback.get("identity"))
    aggregate_identity = _mapping(identity.get("aggregate_identity"))
    causality = _mapping(readback.get("causality"))
    stage_run_identity = _mapping(identity.get("stage_run_identity"))
    readback_idempotency_key = _non_empty_text(identity.get("idempotency_key"))
    if readback_idempotency_key is not None:
        request["idempotency_key"] = readback_idempotency_key
        request["request_idempotency_key"] = readback_idempotency_key
    if aggregate_identity:
        request["aggregate_identity"] = {
            **_mapping(request.get("aggregate_identity")),
            **{
                key: value
                for key, value in {
                    "aggregate_kind": _non_empty_text(aggregate_identity.get("aggregate_kind")),
                    "aggregate_id": _non_empty_text(aggregate_identity.get("aggregate_id")),
                    "study_id": _non_empty_text(aggregate_identity.get("study_id")),
                    "work_unit_id": _non_empty_text(aggregate_identity.get("work_unit_id")),
                    "work_unit_fingerprint": _non_empty_text(
                        aggregate_identity.get("work_unit_fingerprint")
                    ),
                }.items()
                if value is not None
            },
        }
        for key in ("study_id", "work_unit_id", "work_unit_fingerprint"):
            value = _non_empty_text(aggregate_identity.get(key))
            if value is not None:
                request[key] = value
    source_generation = _non_empty_text(causality.get("source_generation")) or _non_empty_text(
        stage_run_identity.get("source_generation")
    )
    expected_version = _non_empty_text(causality.get("expected_version"))
    if source_generation is not None:
        request["source_generation"] = source_generation
    if expected_version is not None:
        request["expected_version"] = expected_version
    route_identity_key = _non_empty_text(stage_run_identity.get("route_identity_key"))
    attempt_idempotency_key = _non_empty_text(
        stage_run_identity.get("attempt_idempotency_key")
    )
    if route_identity_key is not None:
        request["route_identity_key"] = route_identity_key
    if attempt_idempotency_key is not None:
        request["attempt_idempotency_key"] = attempt_idempotency_key
    return request


def _candidate_current_action(
    candidate: Mapping[str, Any],
    *,
    current_action_source: str | None,
) -> dict[str, Any]:
    currentness_basis = _mapping(candidate.get("currentness_basis"))
    return {
        key: value
        for key, value in {
            "surface_kind": "current_executable_owner_action",
            "status": "ready",
            "source": current_action_source or _non_empty_text(candidate.get("source")),
            "next_owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "owner": _non_empty_text(candidate.get("next_executable_owner"))
            or _non_empty_text(candidate.get("owner")),
            "action_type": _non_empty_text(candidate.get("action_type")),
            "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
            or _non_empty_text(candidate.get("action_fingerprint")),
            "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint"))
            or _non_empty_text(candidate.get("work_unit_fingerprint")),
            "currentness_basis": dict(currentness_basis) if currentness_basis else None,
            "projection_metadata": _projection_metadata(
                transition_request=_mapping(candidate.get("opl_domain_progress_transition_request")),
                policy_result=_mapping(candidate.get("paper_progress_policy_result")),
                candidate=candidate,
            ),
        }.items()
        if value not in (None, "", [], {})
    }


def _projection_metadata(
    *,
    transition_request: Mapping[str, Any],
    policy_result: Mapping[str, Any] | None = None,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    del transition_request
    request_metadata = _mapping(_mapping(policy_result).get("projection_metadata"))
    return {
        "authority": False,
        "projection_owner": "med-autoscience",
        "fixed_point_runtime_owner": "one-person-lab",
        "derived_from_event_id": _non_empty_text(request_metadata.get("derived_from_event_id"))
        or _non_empty_text(candidate.get("derived_from_event_id")),
        "observed_generation": _non_empty_text(request_metadata.get("observed_generation"))
        or _non_empty_text(candidate.get("observed_generation"))
        or _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
    }
