from __future__ import annotations

from collections.abc import Mapping
from typing import Any

OPL_TRANSITION_RUNTIME_OWNER = "one-person-lab"
OPL_TRANSITION_RUNTIME_KIND = "DomainProgressTransitionRuntime"
OPL_TRANSITION_RESULT_SURFACE = "opl_domain_progress_transition_result"
PROVIDER_ADMISSION_OUTCOME = "provider_admission_pending"

REQUIRED_READBACK_SECTIONS = (
    "identity",
    "causality",
    "authority_boundary",
    "exactly_one_outcome",
    "projection_metadata",
)
REQUIRED_RUNTIME_REFS = (
    "event_id",
    "outbox_item_id",
    "stage_run_identity",
)


def valid_opl_transition_readback(value: Mapping[str, Any]) -> bool:
    result = _mapping(value)
    if not result:
        return False
    if _text(result.get("surface_kind")) != OPL_TRANSITION_RESULT_SURFACE:
        return False
    if _text(result.get("runtime_owner")) != OPL_TRANSITION_RUNTIME_OWNER:
        return False
    runtime_kind = _text(result.get("runtime_kind")) or _text(result.get("target_runtime_kind"))
    if runtime_kind != OPL_TRANSITION_RUNTIME_KIND:
        return False
    if _text(result.get("outcome_kind")) != PROVIDER_ADMISSION_OUTCOME:
        return False
    if not _has_runtime_refs(result):
        return False
    return all(
        validator(_mapping(result.get(section)))
        for section, validator in (
            ("identity", _valid_identity),
            ("causality", _valid_causality),
            ("authority_boundary", _valid_authority_boundary),
            ("exactly_one_outcome", _valid_exactly_one_outcome),
            ("projection_metadata", _valid_projection_metadata),
        )
    )


def required_opl_transition_readback_shape() -> dict[str, Any]:
    return {
        "surface_kind": OPL_TRANSITION_RESULT_SURFACE,
        "runtime_owner": OPL_TRANSITION_RUNTIME_OWNER,
        "runtime_kind": OPL_TRANSITION_RUNTIME_KIND,
        "required_sections": list(REQUIRED_READBACK_SECTIONS),
        "required_runtime_refs": list(REQUIRED_RUNTIME_REFS),
        "accepted_outcome_kind": PROVIDER_ADMISSION_OUTCOME,
        "deprecated_projection_fields_not_authority": [
            "stage_run_id",
            "event_id_without_causality",
            "outbox_item_id_without_authority_boundary",
        ],
    }


def _has_runtime_refs(result: Mapping[str, Any]) -> bool:
    stage_run_identity = _mapping(result.get("stage_run_identity"))
    return (
        _text(result.get("event_id")) is not None
        and _text(result.get("outbox_item_id")) is not None
        and (
            _text(stage_run_identity.get("stage_run_id")) is not None
            or _text(stage_run_identity.get("stage_run_identity_ref")) is not None
        )
    )


def _valid_identity(identity: Mapping[str, Any]) -> bool:
    return all(
        _text(identity.get(key)) is not None
        for key in (
            "study_id",
            "work_unit_id",
            "work_unit_fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        )
    )


def _valid_causality(causality: Mapping[str, Any]) -> bool:
    if causality.get("derived_from_request") is not True:
        return False
    request_key = _text(causality.get("mas_transition_request_idempotency_key")) or _text(
        causality.get("transition_request_idempotency_key")
    )
    return (
        request_key is not None
        and _text(causality.get("source_generation")) is not None
        and _text(causality.get("expected_version")) is not None
    )


def _valid_authority_boundary(boundary: Mapping[str, Any]) -> bool:
    return (
        _text(boundary.get("runtime_owner")) == OPL_TRANSITION_RUNTIME_OWNER
        and _text(boundary.get("domain_state_owner")) == "med-autoscience"
        and boundary.get("mas_can_authorize_provider_admission") is False
        and boundary.get("mas_can_create_opl_outbox_record") is False
        and boundary.get("mas_can_create_opl_event") is False
        and boundary.get("mas_can_create_opl_stage_run") is False
        and boundary.get("provider_completion_is_domain_completion") is False
    )


def _valid_exactly_one_outcome(outcome: Mapping[str, Any]) -> bool:
    selected = _text(outcome.get("selected"))
    allowed = {
        text
        for item in outcome.get("allowed") or []
        if (text := _text(item)) is not None
    }
    if selected != PROVIDER_ADMISSION_OUTCOME or selected not in allowed:
        return False
    rejected = [
        text
        for item in outcome.get("rejected") or []
        if (text := _text(item)) is not None
    ]
    return selected not in rejected


def _valid_projection_metadata(metadata: Mapping[str, Any]) -> bool:
    return (
        metadata.get("authority") is False
        and _text(metadata.get("projection_owner")) == OPL_TRANSITION_RUNTIME_OWNER
        and _text(metadata.get("consumer")) == "med-autoscience"
        and _text(metadata.get("observed_generation")) is not None
    )


def candidate_opl_transition_readback(candidate: Mapping[str, Any]) -> dict[str, Any]:
    for value in (
        candidate.get("opl_domain_progress_transition_result"),
        candidate.get("opl_domain_progress_runtime_result"),
        candidate.get("opl_runtime_result"),
        _mapping(candidate.get("paper_progress_policy_result")).get("opl_runtime_result"),
        _mapping(candidate.get("state")).get("opl_domain_progress_transition_result"),
        _mapping(candidate.get("state")).get("opl_runtime_result"),
    ):
        result = _mapping(value)
        if valid_opl_transition_readback(result):
            return dict(result)
    return {}


def has_opl_transition_readback(candidate: Mapping[str, Any]) -> bool:
    return bool(candidate_opl_transition_readback(candidate))


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "OPL_TRANSITION_RUNTIME_KIND",
    "OPL_TRANSITION_RUNTIME_OWNER",
    "OPL_TRANSITION_RESULT_SURFACE",
    "candidate_opl_transition_readback",
    "has_opl_transition_readback",
    "required_opl_transition_readback_shape",
    "valid_opl_transition_readback",
]
