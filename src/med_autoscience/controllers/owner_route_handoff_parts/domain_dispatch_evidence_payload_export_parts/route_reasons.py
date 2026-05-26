from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    OPL_RUNTIME_OWNER_ROUTE_REASON,
    OPL_STAGE_ATTEMPT_ADMISSION_REASON,
    PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION,
    PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION,
    PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_CONSUMED_AI_REVIEWER_ROUTEBACK,
    RUNTIME_RECOVERY_NOT_AUTHORIZED_REASON,
    SUPPORTED_SUPERSEDED_ACTION_TYPE,
    SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE,
    WRITE_ACTION_TYPE,
    WRITE_OWNER,
    mapping,
    sequence,
    text,
    texts,
)


def payload_reason_for_superseded_dispatch(
    *,
    action_type: str | None,
    study_scan: Mapping[str, Any],
) -> str | None:
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and consumed_ai_reviewer_routeback_observed(study_scan)
    ):
        return PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and consumed_ai_reviewer_routeback_observed(study_scan)
    ):
        return PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_CONSUMED_AI_REVIEWER_ROUTEBACK
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and ai_reviewer_currentness_supersession_observed(study_scan)
    ):
        return PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION
    return None


def blocked_reason_for_action_type(action_type: str | None) -> str:
    if action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE:
        return "ai_reviewer_currentness_supersession_not_observed"
    return "consumed_ai_reviewer_routeback_not_observed"


def consumed_ai_reviewer_routeback_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("route_target")) == "write"
        and text(domain_transition.get("owner")) == "write"
        and text(domain_transition.get("controller_action")) == "request_opl_stage_attempt"
        and (
            _opl_stage_admission_observed(study_scan=study_scan, owner_route=owner_route)
            or _registered_write_routeback_transport_wait_observed(
                study_scan=study_scan,
                owner_route=owner_route,
            )
        )
    )


def ai_reviewer_currentness_supersession_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("controller_action")) == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and text(domain_transition.get("owner")) == "ai_reviewer"
        and text(owner_route.get("next_owner")) == "ai_reviewer"
        and blocked_reason == "ai_reviewer_record_stale_after_current_manuscript"
    )


def _opl_stage_admission_observed(
    *,
    study_scan: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    return (
        text(owner_route.get("next_owner")) == "one-person-lab"
        and (
            text(study_scan.get("blocked_reason")) in _opl_stage_admission_reasons()
            or text(owner_route.get("owner_reason")) in _opl_stage_admission_reasons()
        )
    )


def _registered_write_routeback_transport_wait_observed(
    *,
    study_scan: Mapping[str, Any],
    owner_route: Mapping[str, Any],
) -> bool:
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    return (
        text(owner_route.get("next_owner")) == "external_supervisor"
        and (
            text(study_scan.get("blocked_reason")) == OPL_RUNTIME_OWNER_ROUTE_REASON
            or text(owner_route.get("owner_reason")) == OPL_RUNTIME_OWNER_ROUTE_REASON
        )
        and owner_reason_contract.get("registered") is True
        and text(owner_reason_contract.get("owner")) == WRITE_OWNER
        and WRITE_ACTION_TYPE in set(texts(sequence(owner_reason_contract.get("allowed_actions"))))
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
    )


def _opl_stage_admission_reasons() -> set[str]:
    return {
        OPL_STAGE_ATTEMPT_ADMISSION_REASON,
        RUNTIME_RECOVERY_NOT_AUTHORIZED_REASON,
    }
