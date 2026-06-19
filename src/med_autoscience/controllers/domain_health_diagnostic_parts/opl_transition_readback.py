from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import opl_domain_progress_transition_contract as transition_contract

OPL_TRANSITION_RUNTIME_OWNER = transition_contract.RUNTIME_OWNER
OPL_TRANSITION_RUNTIME_KIND = transition_contract.RUNTIME_KIND
OPL_TRANSITION_LIVE_READBACK_SURFACE = transition_contract.LIVE_READBACK_SURFACE
OPL_TRANSITION_RESULT_SURFACE = OPL_TRANSITION_LIVE_READBACK_SURFACE
LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME = transition_contract.PROVIDER_ADMISSION_OUTCOME
LIVE_READBACK_NON_ADVANCING_APPLY_OUTCOME = transition_contract.NON_ADVANCING_APPLY_OUTCOME
LIVE_READBACK_COMPLETE_STATUS = transition_contract.LIVE_READBACK_COMPLETE_STATUS

REQUIRED_READBACK_SECTIONS = transition_contract.REQUIRED_READBACK_SECTIONS
REQUIRED_RUNTIME_REFS = transition_contract.REQUIRED_RUNTIME_REFS

_RUNTIME_ID = transition_contract.RUNTIME_ID


def valid_opl_transition_readback(value: Mapping[str, Any]) -> bool:
    result = _mapping(value)
    if not result:
        return False
    return _valid_live_transition_readback(result)


def required_opl_transition_readback_shape() -> dict[str, Any]:
    return transition_contract.required_readback_shape()


def opl_transition_readback_source_claimability(value: Mapping[str, Any]) -> dict[str, Any]:
    source = _mapping(value.get("evidence_source"))
    source_kind = _text(source.get("source_kind"))
    source_ref = _text(source.get("source_ref"))
    shape_valid = valid_opl_transition_readback(value)
    runtime_claimable = source_kind in transition_contract.LIVE_READBACK_CLAIMABLE_SOURCE_KINDS
    replay_or_fixture = source_kind in transition_contract.LIVE_READBACK_NON_CLAIMABLE_SOURCE_KINDS
    return {
        "source_kind": source_kind,
        "source_ref": source_ref,
        "fresh_live_claim_allowed": shape_valid and runtime_claimable,
        "runtime_claimable": runtime_claimable,
        "shape_valid": shape_valid,
        "replay_or_fixture": replay_or_fixture,
        "missing_source_kind": source_kind is None,
    }


def _valid_live_transition_readback(result: Mapping[str, Any]) -> bool:
    if _text(result.get("surface_kind")) != OPL_TRANSITION_LIVE_READBACK_SURFACE:
        return False
    if _text(result.get("runtime_readback_status")) != LIVE_READBACK_COMPLETE_STATUS:
        return False
    if result.get("transaction_complete") is not True:
        return False
    if not _has_live_runtime_refs(result):
        return False
    return all(
        validator(_mapping(result.get(section)))
        for section, validator in (
            ("identity", _valid_live_identity),
            ("causality", _valid_live_causality),
            ("authority_boundary", _valid_live_authority_boundary),
            ("exactly_one_outcome", _valid_live_exactly_one_outcome),
            ("projection_metadata", _valid_live_projection_metadata),
        )
    ) and _valid_live_readback_consistency(result)


def _has_live_runtime_refs(result: Mapping[str, Any]) -> bool:
    identity = _mapping(result.get("identity"))
    latest_transaction = _mapping(result.get("latest_transaction_readback"))
    return (
        all(
            _text(identity.get(key)) is not None
            for key in transition_contract.LIVE_READBACK_IDENTITY_TRANSACTION_REFS
        )
        and all(
            latest_transaction.get(key) is True
            for key in transition_contract.LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS
        )
    )


def _valid_live_identity(identity: Mapping[str, Any]) -> bool:
    aggregate_identity = _mapping(identity.get("aggregate_identity"))
    stage_run_identity = _mapping(identity.get("stage_run_identity"))
    return all(
        _text(aggregate_identity.get(key)) is not None
        for key in (
            "study_id",
            "work_unit_id",
            "work_unit_fingerprint",
        )
    ) and all(
        _text(stage_run_identity.get(key)) is not None
        for key in (
            "route_identity_key",
            "attempt_idempotency_key",
        )
    ) and (
        _text(stage_run_identity.get("stage_run_id")) is not None
        or _text(stage_run_identity.get("stage_run_identity_ref")) is not None
    )


def _valid_live_causality(causality: Mapping[str, Any]) -> bool:
    if causality.get("transaction_complete") is not True:
        return False
    if _text(causality.get("runtime_readback_status")) != LIVE_READBACK_COMPLETE_STATUS:
        return False
    return (
        _text(causality.get("event_id")) is not None
        and _text(causality.get("outbox_item_id")) is not None
        and causality.get("same_transaction_event_and_outbox") is True
        and _text(causality.get("source_generation")) is not None
        and _text(causality.get("expected_version")) is not None
    )


def _valid_live_authority_boundary(boundary: Mapping[str, Any]) -> bool:
    return (
        _text(boundary.get("runtime_owner")) == OPL_TRANSITION_RUNTIME_OWNER
        and boundary.get("authority") is False
        and boundary.get("opl_can_write_domain_truth") is False
        and boundary.get("opl_can_write_mas_truth") is False
        and boundary.get("opl_can_create_domain_owner_receipt") is False
        and boundary.get("opl_can_create_domain_typed_blocker") is False
        and boundary.get("provider_completion_is_domain_completion") is False
    )


def _valid_live_exactly_one_outcome(outcome: Mapping[str, Any]) -> bool:
    outcome_kind = _text(outcome.get("outcome_kind"))
    return outcome.get("selected") is True and outcome.get("exactly_one_transition") is True and (
        outcome.get("stable_outcome") is True
        and outcome.get("fail_closed") is False
        and outcome_kind
        in {
            LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME,
            LIVE_READBACK_NON_ADVANCING_APPLY_OUTCOME,
        }
        and (
            outcome_kind != LIVE_READBACK_NON_ADVANCING_APPLY_OUTCOME
            or (
                outcome.get("non_advancing_apply") is True
                and _text(outcome.get("transition_kind")) == "NonAdvancingApply"
            )
        )
    )


def _valid_live_projection_metadata(metadata: Mapping[str, Any]) -> bool:
    return (
        metadata.get("authority") is False
        and _text(metadata.get("runtime_id")) == _RUNTIME_ID
        and _text(metadata.get("read_model_rebuild_owner")) == OPL_TRANSITION_RUNTIME_OWNER
        and _text(metadata.get("derived_from_event_id")) is not None
        and _text(metadata.get("observed_generation")) is not None
    )


def _valid_live_readback_consistency(result: Mapping[str, Any]) -> bool:
    identity = _mapping(result.get("identity"))
    causality = _mapping(result.get("causality"))
    authority_boundary = _mapping(result.get("authority_boundary"))
    exactly_one_outcome = _mapping(result.get("exactly_one_outcome"))
    projection_metadata = _mapping(result.get("projection_metadata"))
    latest_transaction = _mapping(result.get("latest_transaction_readback"))
    read_model = _mapping(result.get("read_model_readback"))

    event_id = _text(identity.get("latest_event_id"))
    outbox_item_id = _text(identity.get("latest_outbox_item_id"))
    transaction_id = _text(identity.get("latest_transaction_id"))
    if event_id is None or outbox_item_id is None or transaction_id is None:
        return False
    expected = {
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "transaction_id": transaction_id,
    }

    return (
        all(
            _same_text(causality.get(key), expected[key])
            for key in transition_contract.LIVE_READBACK_CAUSALITY_TRANSACTION_REF_FIELDS
        )
        and _same_text(projection_metadata.get("derived_from_event_id"), event_id)
        and all(
            _same_text(latest_transaction.get(key), expected.get(key, event_id))
            for key in transition_contract.LIVE_READBACK_LATEST_TRANSACTION_REF_FIELDS
        )
        and _read_model_rebuild_matches_live_sections(
            read_model,
            identity=identity,
            causality=causality,
            authority_boundary=authority_boundary,
            exactly_one_outcome=exactly_one_outcome,
            projection_metadata=projection_metadata,
        )
    )


def _read_model_rebuild_matches_live_sections(
    read_model: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    causality: Mapping[str, Any],
    authority_boundary: Mapping[str, Any],
    exactly_one_outcome: Mapping[str, Any],
    projection_metadata: Mapping[str, Any],
) -> bool:
    if not read_model:
        return False
    expected_sections = {
        "identity": identity,
        "causality": causality,
        "authority_boundary": authority_boundary,
        "exactly_one_outcome": exactly_one_outcome,
        "projection_metadata": projection_metadata,
    }
    return all(
        _mapping(read_model.get(section)) == dict(expected)
        for section, expected in expected_sections.items()
    )


def candidate_opl_transition_readback(candidate: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        candidate,
        candidate.get("opl_domain_progress_transition_live_readback"),
        candidate.get("opl_domain_progress_transition_runtime_live_readback"),
        candidate.get("opl_domain_progress_transition_result"),
        candidate.get("opl_domain_progress_runtime_result"),
        candidate.get("opl_runtime_result"),
        candidate.get("domain_progress_transition_runtime"),
        candidate.get("domain_progress_transition_runtime_result"),
        _mapping(candidate.get("provider_admission_identity")).get(
            "opl_domain_progress_transition_live_readback"
        ),
        _mapping(candidate.get("provider_admission_identity")).get(
            "opl_domain_progress_transition_runtime_live_readback"
        ),
        _mapping(candidate.get("provider_admission_identity")).get(
            "opl_domain_progress_transition_result"
        ),
        _mapping(candidate.get("provider_admission_identity")).get("opl_runtime_result"),
        _mapping(candidate.get("provider_admission_identity")).get(
            "domain_progress_transition_runtime"
        ),
        _mapping(candidate.get("paper_progress_policy_result")).get("opl_runtime_result"),
        _mapping(candidate.get("paper_progress_policy_result")).get(
            "domain_progress_transition_runtime"
        ),
        _mapping(candidate.get("state")).get("opl_domain_progress_transition_result"),
        _mapping(candidate.get("state")).get("opl_domain_progress_transition_live_readback"),
        _mapping(candidate.get("state")).get("opl_runtime_result"),
        _mapping(candidate.get("state")).get("domain_progress_transition_runtime"),
        _mapping(candidate.get("domain_progress_transition_non_advancing_apply_readback")).get(
            "runtime_live_readback"
        ),
        _mapping(candidate.get("domain_progress_transition_non_advancing_apply_readback")).get(
            "runtime_result"
        ),
    ):
        result = _prebuilt_opl_transition_readback(value)
        if result:
            return result
    return {}


def has_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(candidate_opl_transition_readback(candidate))


def non_advancing_apply_opl_transition_readback(candidate: Mapping[str, Any]) -> dict[str, Any]:
    readback = candidate_opl_transition_readback(candidate)
    if not readback:
        return {}
    if not _readback_is_non_advancing_apply(readback):
        return {}
    return readback


def has_non_advancing_apply_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(non_advancing_apply_opl_transition_readback(candidate))


def provider_admission_opl_transition_readback(
    candidate: Mapping[str, Any],
    *,
    require_explicit_identity: bool = False,
) -> dict[str, Any]:
    readback = candidate_opl_transition_readback(candidate)
    if not readback:
        return {}
    if not _readback_is_provider_admission(readback):
        return {}
    if not _readback_matches_provider_admission_identity(
        candidate,
        readback,
        require_explicit_identity=require_explicit_identity,
    ):
        return {}
    return readback


def has_provider_admission_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(provider_admission_opl_transition_readback(candidate))


def _readback_is_provider_admission(readback: Mapping[str, Any]) -> bool:
    return _readback_outcome_kind(readback) == LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME


def _readback_is_non_advancing_apply(readback: Mapping[str, Any]) -> bool:
    outcome = _mapping(readback.get("exactly_one_outcome"))
    return (
        _readback_outcome_kind(readback) == LIVE_READBACK_NON_ADVANCING_APPLY_OUTCOME
        and outcome.get("non_advancing_apply") is True
        and _text(outcome.get("transition_kind")) == "NonAdvancingApply"
    )


def _readback_outcome_kind(readback: Mapping[str, Any]) -> str | None:
    outcome = _mapping(readback.get("exactly_one_outcome"))
    return _text(outcome.get("outcome_kind")) or _text(
        _mapping(readback.get("identity")).get("outcome_kind")
    )


def _prebuilt_opl_transition_readback(value: object) -> dict[str, Any]:
    payload = _mapping(value)
    if not payload:
        return {}
    if valid_opl_transition_readback(payload):
        return dict(payload)
    for key in (
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_transition_live_readback",
        "opl_runtime_live_readback",
    ):
        readback = _mapping(payload.get(key))
        if valid_opl_transition_readback(readback):
            return dict(readback)
    for key in (
        "domain_progress_transition_runtime",
        "domain_progress_transition_runtime_result",
        "opl_domain_progress_transition_runtime_result",
        "opl_domain_progress_transition_result",
    ):
        readback = _prebuilt_opl_transition_readback(payload.get(key))
        if readback:
            return readback
    if _is_opl_transition_runtime_container(payload):
        readback = _prebuilt_opl_transition_readback(payload.get("result"))
        if readback:
            return readback
    return {}


def _is_opl_transition_runtime_container(payload: Mapping[str, Any]) -> bool:
    return (
        _text(payload.get("surface_kind"))
        in {
            "opl_domain_progress_transition_runtime_result",
            "domain_progress_transition_runtime_result",
        }
        or _text(payload.get("runtime_id")) == "opl_domain_progress_transition_runtime"
        or _text(payload.get("runtime_kind")) == OPL_TRANSITION_RUNTIME_KIND
    )


def _readback_matches_provider_admission_identity(
    candidate: Mapping[str, Any],
    readback: Mapping[str, Any],
    *,
    require_explicit_identity: bool = False,
) -> bool:
    expected = _provider_admission_identity(
        candidate,
        require_explicit_identity=require_explicit_identity,
    )
    return transition_contract.readback_matches_provider_admission_identity(readback, expected)


def _provider_admission_identity(
    candidate: Mapping[str, Any],
    *,
    require_explicit_identity: bool = False,
) -> dict[str, Any]:
    transition_request = _transition_request(candidate)
    request_identity = _mapping(transition_request.get("aggregate_identity"))
    request_stage_identity = _mapping(transition_request.get("stage_run_identity"))
    transition_identity = _mapping(transition_request.get("identity"))
    state = _mapping(candidate.get("state"))
    state_request = _transition_request(state)
    state_request_identity = _mapping(state_request.get("aggregate_identity"))
    state_request_stage_identity = _mapping(state_request.get("stage_run_identity"))
    state_transition_identity = _mapping(state_request.get("identity"))
    policy = _mapping(candidate.get("paper_progress_policy_result"))
    policy_request = _transition_request(policy)
    policy_request_identity = _mapping(policy_request.get("aggregate_identity"))
    policy_request_stage_identity = _mapping(policy_request.get("stage_run_identity"))
    policy_transition_identity = _mapping(policy_request.get("identity"))

    study_id = (
        _text(candidate.get("study_id"))
        or _text(request_identity.get("study_id"))
        or _text(state.get("study_id"))
        or _text(state_request_identity.get("study_id"))
        or _text(policy_request_identity.get("study_id"))
    )
    work_unit_fingerprint = (
        _text(candidate.get("work_unit_fingerprint"))
        or _text(candidate.get("action_fingerprint"))
        or _text(request_identity.get("work_unit_fingerprint"))
        or _text(state.get("work_unit_fingerprint"))
        or _text(state.get("action_fingerprint"))
        or _text(state_request_identity.get("work_unit_fingerprint"))
        or _text(policy_request_identity.get("work_unit_fingerprint"))
    )
    route_identity_key = (
        _text(candidate.get("route_identity_key"))
        or _text(transition_request.get("route_identity_key"))
        or _text(request_stage_identity.get("route_identity_key"))
        or _text(transition_identity.get("route_identity_key"))
        or _text(state.get("route_identity_key"))
        or _text(state_request.get("route_identity_key"))
        or _text(state_request_stage_identity.get("route_identity_key"))
        or _text(state_transition_identity.get("route_identity_key"))
        or _text(policy.get("route_identity_key"))
        or _text(policy_request.get("route_identity_key"))
        or _text(policy_request_stage_identity.get("route_identity_key"))
        or _text(policy_transition_identity.get("route_identity_key"))
    )
    if (
        route_identity_key is None
        and not require_explicit_identity
        and study_id is not None
        and work_unit_fingerprint is not None
    ):
        route_identity_key = f"provider-admission::{study_id}::{work_unit_fingerprint}"
    attempt_idempotency_key = (
        _text(candidate.get("attempt_idempotency_key"))
        or _text(transition_request.get("attempt_idempotency_key"))
        or _text(request_stage_identity.get("attempt_idempotency_key"))
        or _text(transition_identity.get("attempt_idempotency_key"))
        or _text(state.get("attempt_idempotency_key"))
        or _text(state_request.get("attempt_idempotency_key"))
        or _text(state_request_stage_identity.get("attempt_idempotency_key"))
        or _text(state_transition_identity.get("attempt_idempotency_key"))
        or _text(policy.get("attempt_idempotency_key"))
        or _text(policy_request.get("attempt_idempotency_key"))
        or _text(policy_request_stage_identity.get("attempt_idempotency_key"))
        or _text(policy_transition_identity.get("attempt_idempotency_key"))
    )
    if attempt_idempotency_key is None and not require_explicit_identity:
        attempt_idempotency_key = route_identity_key
    return {
        "study_id": study_id,
        "work_unit_id": (
            _text(candidate.get("work_unit_id"))
            or _text(candidate.get("next_work_unit"))
            or _text(request_identity.get("work_unit_id"))
            or _text(state.get("work_unit_id"))
            or _text(state.get("next_work_unit"))
            or _text(state_request_identity.get("work_unit_id"))
            or _text(policy_request_identity.get("work_unit_id"))
        ),
        "work_unit_fingerprint": work_unit_fingerprint,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
        "request_idempotency_key": (
            _text(candidate.get("idempotency_key"))
            or _text(candidate.get("request_idempotency_key"))
            or _text(candidate.get("route_identity_key"))
            or _text(candidate.get("attempt_idempotency_key"))
            or _text(transition_request.get("idempotency_key"))
            or _text(transition_request.get("request_idempotency_key"))
            or _text(state_request.get("idempotency_key"))
            or _text(state_request.get("request_idempotency_key"))
            or _text(policy_request.get("idempotency_key"))
            or _text(policy_request.get("request_idempotency_key"))
            or _text(transition_identity.get("request_idempotency_key"))
            or _text(state_transition_identity.get("request_idempotency_key"))
            or _text(policy_transition_identity.get("request_idempotency_key"))
            or route_identity_key
            or attempt_idempotency_key
        ),
    }


def _transition_request(value: Mapping[str, Any]) -> Mapping[str, Any]:
    request = _mapping(value.get("opl_domain_progress_transition_request"))
    if request:
        return request
    policy = _mapping(value.get("paper_progress_policy_result"))
    return _mapping(policy.get("opl_domain_progress_transition_request"))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _same_text(value: object, expected: str) -> bool:
    return _text(value) == expected


__all__ = [
    "OPL_TRANSITION_RUNTIME_KIND",
    "OPL_TRANSITION_RUNTIME_OWNER",
    "OPL_TRANSITION_RESULT_SURFACE",
    "candidate_opl_transition_readback",
    "has_non_advancing_apply_opl_transition_readback",
    "has_provider_admission_opl_transition_readback",
    "has_opl_transition_readback",
    "non_advancing_apply_opl_transition_readback",
    "opl_transition_readback_source_claimability",
    "provider_admission_opl_transition_readback",
    "required_opl_transition_readback_shape",
    "valid_opl_transition_readback",
]
