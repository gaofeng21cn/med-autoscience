from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.stable_blocker_classes import stable_blocker_class
from med_autoscience.controllers.owner_route_handoff_parts.domain_dispatch_evidence_payload_export_parts.shared import (
    GATE_CLEARING_ACTION_TYPE,
    GATE_CLEARING_OWNER,
    OPL_RUNTIME_OWNER_ROUTE_REASON,
    OPL_STAGE_ATTEMPT_ADMISSION_REASON,
    OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_REASON,
    PAYLOAD_REASON_CONSUMED_AI_REVIEWER_PRODUCTION_HANDOFF,
    PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION,
    PAYLOAD_REASON_CONSUMED_AI_REVIEWER_SUPERSESSION,
    PAYLOAD_REASON_CURRENT_OWNER_ROUTE_TYPED_BLOCKER,
    PAYLOAD_REASON_DELIVERED_PACKAGE_HANDOFF_TYPED_BLOCKER,
    PAYLOAD_REASON_OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_STAGE_ATTEMPT_BLOCKER,
    PAYLOAD_REASON_PUBLICATION_GATE_ROUTE_SUPERSESSION,
    PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_CURRENTNESS,
    PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_STAGE_ADMISSION,
    PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_PUBLICATION_GATE_ROUTE,
    PAYLOAD_REASON_RUNTIME_RECOVERY_NOT_AUTHORIZED_STAGE_ATTEMPT_BLOCKER,
    PAYLOAD_REASON_RUNTIME_RECOVERY_RETRY_BUDGET_TERMINAL_BLOCKER,
    PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_STAGE_ADMISSION,
    PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_CONSUMED_AI_REVIEWER_ROUTEBACK,
    RUNTIME_RECOVERY_RETRY_BUDGET_EXHAUSTED_REASON,
    RUNTIME_RECOVERY_NOT_AUTHORIZED_REASON,
    PUBLICATION_GATE_ROUTE_BACK_WRITE_REQUIRED_REASON,
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
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and consumed_ai_reviewer_production_handoff_observed(study_scan)
    ):
        return PAYLOAD_REASON_CONSUMED_AI_REVIEWER_PRODUCTION_HANDOFF
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and current_ai_reviewer_stage_attempt_admission_observed(study_scan)
    ):
        return PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_STAGE_ADMISSION
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and ai_reviewer_currentness_supersession_observed(study_scan)
    ):
        return PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_CURRENTNESS
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and runtime_recovery_not_authorized_stage_attempt_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_RUNTIME_RECOVERY_NOT_AUTHORIZED_STAGE_ATTEMPT_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and delivered_package_handoff_typed_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_DELIVERED_PACKAGE_HANDOFF_TYPED_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and current_owner_route_typed_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_CURRENT_OWNER_ROUTE_TYPED_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and owner_authorized_publication_gate_replay_stage_attempt_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_STAGE_ATTEMPT_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and runtime_recovery_retry_budget_terminal_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_RUNTIME_RECOVERY_RETRY_BUDGET_TERMINAL_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and publication_gate_route_supersession_observed(study_scan)
    ):
        return PAYLOAD_REASON_REVIEWER_DISPATCH_SUPERSEDED_BY_PUBLICATION_GATE_ROUTE
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and consumed_ai_reviewer_routeback_observed(study_scan)
    ):
        return PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_CONSUMED_AI_REVIEWER_ROUTEBACK
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and current_ai_reviewer_stage_attempt_admission_observed(study_scan)
    ):
        return PAYLOAD_REASON_WRITER_DISPATCH_SUPERSEDED_BY_AI_REVIEWER_STAGE_ADMISSION
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and ai_reviewer_currentness_supersession_observed(study_scan)
    ):
        return PAYLOAD_REASON_AI_REVIEWER_CURRENTNESS_SUPERSESSION
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and runtime_recovery_not_authorized_stage_attempt_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_RUNTIME_RECOVERY_NOT_AUTHORIZED_STAGE_ATTEMPT_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and current_owner_route_typed_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_CURRENT_OWNER_ROUTE_TYPED_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and runtime_recovery_retry_budget_terminal_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_RUNTIME_RECOVERY_RETRY_BUDGET_TERMINAL_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and owner_authorized_publication_gate_replay_stage_attempt_blocker_observed(study_scan)
    ):
        return PAYLOAD_REASON_OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_STAGE_ATTEMPT_BLOCKER
    if (
        action_type == SUPPORTED_SUPERSEDED_WRITER_ACTION_TYPE
        and publication_gate_route_supersession_observed(study_scan)
    ):
        return PAYLOAD_REASON_PUBLICATION_GATE_ROUTE_SUPERSESSION
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


def consumed_ai_reviewer_production_handoff_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("decision_type")) == "ai_reviewer_re_eval"
        and text(domain_transition.get("route_target")) == "review"
        and text(domain_transition.get("owner")) == "ai_reviewer"
        and text(domain_transition.get("controller_action")) == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and text(completion.get("next_action")) == "honor_ai_reviewer_publication_eval_authority"
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
        and text(owner_route.get("next_owner")) in _ai_reviewer_currentness_next_owners()
        and blocked_reason == "ai_reviewer_record_stale_after_current_manuscript"
    )


def current_ai_reviewer_stage_attempt_admission_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("decision_type")) == "ai_reviewer_re_eval"
        and text(domain_transition.get("route_target")) == "review"
        and text(domain_transition.get("owner")) == "ai_reviewer"
        and text(domain_transition.get("controller_action")) == SUPPORTED_SUPERSEDED_ACTION_TYPE
        and text(owner_route.get("next_owner")) == "one-person-lab"
        and blocked_reason in _opl_stage_admission_reasons()
        and text(owner_reason_contract.get("owner")) == "one-person-lab"
        and sequence(owner_reason_contract.get("allowed_actions")) == []
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
    )


def runtime_recovery_retry_budget_terminal_blocker_observed(study_scan: Mapping[str, Any]) -> bool:
    return _runtime_stage_attempt_terminal_blocker_observed(
        study_scan=study_scan,
        blocked_reason_value=RUNTIME_RECOVERY_RETRY_BUDGET_EXHAUSTED_REASON,
    )


def runtime_recovery_not_authorized_stage_attempt_blocker_observed(
    study_scan: Mapping[str, Any],
) -> bool:
    return _runtime_stage_attempt_terminal_blocker_observed(
        study_scan=study_scan,
        blocked_reason_value=RUNTIME_RECOVERY_NOT_AUTHORIZED_REASON,
    )


def current_owner_route_typed_blocker_observed(
    study_scan: Mapping[str, Any],
) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    owner_route = mapping(study_scan.get("owner_route"))
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    domain_authority_handoff = mapping(study_scan.get("domain_authority_handoff"))
    typed_blocker = mapping(domain_authority_handoff.get("typed_blocker"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    next_owner = text(owner_route.get("next_owner"))
    owner_reason = text(owner_route.get("owner_reason"))
    return (
        not domain_transition
        and blocked_reason is not None
        and owner_reason == blocked_reason
        and next_owner is not None
        and owner_reason_contract.get("registered") is True
        and text(owner_reason_contract.get("reason")) == blocked_reason
        and text(owner_reason_contract.get("owner")) is not None
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
        and text(domain_authority_handoff.get("status")) == "typed_blocker"
        and _typed_blocker_matches_reason(typed_blocker, blocked_reason)
        and text(typed_blocker.get("next_owner")) == next_owner
    )


def delivered_package_handoff_typed_blocker_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    transition_blocker = mapping(domain_transition.get("typed_blocker"))
    owner_route = mapping(study_scan.get("owner_route"))
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    domain_authority_handoff = mapping(study_scan.get("domain_authority_handoff"))
    typed_blocker = mapping(domain_authority_handoff.get("typed_blocker"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    return (
        text(domain_transition.get("decision_type")) == "delivered_package_handoff"
        and text(domain_transition.get("route_target")) == "human_gate"
        and text(domain_transition.get("owner")) == "med-autoscience"
        and text(domain_transition.get("controller_action")) == "wait_for_human_gate"
        and text(transition_blocker.get("blocker_id")) == "package_delivered_not_publication_authority"
        and transition_blocker.get("write_permitted") is False
        and text(owner_route.get("next_owner")) == "external_supervisor"
        and blocked_reason == PUBLICATION_GATE_ROUTE_BACK_WRITE_REQUIRED_REASON
        and owner_reason_contract.get("registered") is True
        and text(owner_reason_contract.get("owner")) == WRITE_OWNER
        and WRITE_ACTION_TYPE in set(texts(sequence(owner_reason_contract.get("allowed_actions"))))
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
        and text(domain_authority_handoff.get("status")) == "typed_blocker"
        and _typed_blocker_matches_reason(typed_blocker, PUBLICATION_GATE_ROUTE_BACK_WRITE_REQUIRED_REASON)
        and text(typed_blocker.get("next_owner")) == "external_supervisor"
    )


def owner_authorized_publication_gate_replay_stage_attempt_blocker_observed(
    study_scan: Mapping[str, Any],
) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    domain_authority_handoff = mapping(study_scan.get("domain_authority_handoff"))
    typed_blocker = mapping(domain_authority_handoff.get("typed_blocker"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("route_target")) == "finalize"
        and text(domain_transition.get("owner")) == "finalize"
        and text(domain_transition.get("controller_action")) == "request_opl_stage_attempt"
        and text(owner_route.get("next_owner")) == "external_supervisor"
        and blocked_reason == OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_REASON
        and owner_reason_contract.get("registered") is True
        and text(owner_reason_contract.get("owner")) == GATE_CLEARING_OWNER
        and GATE_CLEARING_ACTION_TYPE in set(texts(sequence(owner_reason_contract.get("allowed_actions"))))
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
        and text(domain_authority_handoff.get("status")) == "typed_blocker"
        and _typed_blocker_matches_reason(typed_blocker, OWNER_AUTHORIZED_PUBLICATION_GATE_REPLAY_REASON)
        and text(typed_blocker.get("next_owner")) == "external_supervisor"
    )


def _runtime_stage_attempt_terminal_blocker_observed(
    *,
    study_scan: Mapping[str, Any],
    blocked_reason_value: str,
    next_owner_value: str = "one-person-lab",
    owner_reason_contract_registered: bool = True,
    owner_reason_contract_owner: str = "one-person-lab",
) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("route_target")) in _stage_attempt_route_targets()
        and text(domain_transition.get("owner")) in _stage_attempt_route_targets()
        and text(domain_transition.get("controller_action")) == "request_opl_stage_attempt"
        and text(owner_route.get("next_owner")) == next_owner_value
        and blocked_reason == blocked_reason_value
        and owner_reason_contract.get("registered") is owner_reason_contract_registered
        and text(owner_reason_contract.get("owner")) == owner_reason_contract_owner
        and sequence(owner_reason_contract.get("allowed_actions")) == []
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
    )


def publication_gate_route_supersession_observed(study_scan: Mapping[str, Any]) -> bool:
    domain_transition = mapping(study_scan.get("domain_transition"))
    completion = mapping(domain_transition.get("completion_receipt_consumption"))
    owner_route = mapping(study_scan.get("owner_route"))
    owner_reason_contract = mapping(owner_route.get("owner_reason_contract"))
    currentness_contract = mapping(owner_route.get("currentness_contract"))
    attempt_protocol = mapping(owner_route.get("owner_route_attempt_protocol"))
    blocked_reason = text(study_scan.get("blocked_reason")) or text(owner_route.get("owner_reason"))
    return (
        text(completion.get("status")) == "consumed"
        and text(completion.get("receipt_kind")) == "ai_reviewer_publication_eval"
        and text(domain_transition.get("decision_type")) == "publication_gate_blocker"
        and text(domain_transition.get("route_target")) == "review"
        and text(domain_transition.get("controller_action")) == "run_gate_clearing_batch"
        and text(domain_transition.get("owner")) == "publication_gate"
        and text(owner_route.get("next_owner")) == "one-person-lab"
        and blocked_reason == RUNTIME_RECOVERY_NOT_AUTHORIZED_REASON
        and owner_reason_contract.get("registered") is True
        and text(owner_reason_contract.get("owner")) == "one-person-lab"
        and sequence(owner_reason_contract.get("allowed_actions")) == []
        and currentness_contract.get("missing_required_fields") == []
        and attempt_protocol.get("dispatchable") is False
    )


def _typed_blocker_matches_reason(typed_blocker: Mapping[str, Any], reason: str | None) -> bool:
    reason_text = text(reason)
    if reason_text is None:
        return False
    blocker_reason = text(typed_blocker.get("reason"))
    if blocker_reason == reason_text:
        return True
    detail_reason = text(typed_blocker.get("detail_reason")) or text(
        mapping(typed_blocker.get("details")).get("detail_reason")
    )
    return blocker_reason == stable_blocker_class(reason_text) and detail_reason == reason_text


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


def _stage_attempt_route_targets() -> set[str]:
    return {
        WRITE_OWNER,
        "finalize",
    }


def _ai_reviewer_currentness_next_owners() -> set[str]:
    return {
        "ai_reviewer",
        "supervisor_only/live_quality_repair",
    }
