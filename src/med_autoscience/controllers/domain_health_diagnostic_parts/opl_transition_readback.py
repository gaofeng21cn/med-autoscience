from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers import opl_domain_progress_transition_contract as transition_contract

OPL_TRANSITION_RUNTIME_OWNER = transition_contract.RUNTIME_OWNER
OPL_TRANSITION_RUNTIME_KIND = transition_contract.RUNTIME_KIND
OPL_TRANSITION_LIVE_READBACK_SURFACE = transition_contract.LIVE_READBACK_SURFACE
OPL_TRANSITION_RESULT_SURFACE = OPL_TRANSITION_LIVE_READBACK_SURFACE
LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME = transition_contract.PROVIDER_ADMISSION_OUTCOME
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
        _text(identity.get("latest_event_id")) is not None
        and _text(identity.get("latest_outbox_item_id")) is not None
        and _text(identity.get("latest_transaction_id")) is not None
        and latest_transaction.get("command_present") is True
        and latest_transaction.get("event_present") is True
        and latest_transaction.get("outbox_item_present") is True
        and latest_transaction.get("same_transaction_event_and_outbox") is True
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
    return (
        outcome.get("selected") is True
        and outcome.get("exactly_one_transition") is True
        and outcome.get("stable_outcome") is True
        and outcome.get("fail_closed") is False
        and _text(outcome.get("outcome_kind")) == LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME
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
    projection_metadata = _mapping(result.get("projection_metadata"))
    latest_transaction = _mapping(result.get("latest_transaction_readback"))

    event_id = _text(identity.get("latest_event_id"))
    outbox_item_id = _text(identity.get("latest_outbox_item_id"))
    transaction_id = _text(identity.get("latest_transaction_id"))
    if event_id is None or outbox_item_id is None or transaction_id is None:
        return False

    return (
        _same_text(causality.get("event_id"), event_id)
        and _same_text(causality.get("outbox_item_id"), outbox_item_id)
        and _same_text(causality.get("transaction_id"), transaction_id)
        and _same_text(projection_metadata.get("derived_from_event_id"), event_id)
        and _same_text(latest_transaction.get("event_id"), event_id)
        and _same_text(latest_transaction.get("outbox_item_id"), outbox_item_id)
        and _same_text(latest_transaction.get("transaction_id"), transaction_id)
        and _same_text(latest_transaction.get("transition_event_id"), event_id)
        and _same_text(latest_transaction.get("outbox_transition_event_id"), event_id)
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
    ):
        result = _prebuilt_opl_transition_readback(value)
        if result:
            return result
    return {}


def has_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(candidate_opl_transition_readback(candidate))


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
    "has_opl_transition_readback",
    "required_opl_transition_readback_shape",
    "valid_opl_transition_readback",
]
