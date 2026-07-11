from __future__ import annotations

from collections.abc import Mapping
from copy import deepcopy
from typing import Any

from med_autoscience.controllers import (
    opl_domain_progress_transition_contract as transition_contract,
)
from med_autoscience.paper_mission_transaction import (
    CONTRACT_VERSION as TRANSACTION_CONTRACT_VERSION,
    PaperMissionTransaction,
    PaperMissionTransactionContractError,
)


SURFACE_KIND = "mas_domain_progress_transition_request"
SOURCE_KIND = "paper_mission_transaction_opl_route_command"
OPL_DOMAIN_ID = "mas"


def paper_mission_opl_runtime_carrier(
    transaction_payload: Mapping[str, Any],
) -> dict[str, Any]:
    """Build the MAS request-only carrier OPL can consume for a paper mission."""

    transaction = PaperMissionTransaction.from_payload(transaction_payload).to_dict()
    transaction_id = _required_text(transaction, "transaction_id")
    mission_id = _required_text(transaction, "mission_id")
    study_id = _required_text(transaction, "study_id")
    stage_id = _required_text(transaction, "stage_id")
    stage_run_ref = _required_text(transaction, "stage_run_ref")
    decision = _mapping(transaction.get("stage_terminal_decision"))
    route = _mapping(transaction.get("opl_route_command"))
    idempotency = _mapping(transaction.get("idempotency"))
    idempotency_key = _required_text(idempotency, "idempotency_key")
    transaction_fingerprint = _required_text(
        idempotency,
        "transaction_fingerprint",
    )
    work_unit_id = _transaction_work_unit_id(
        stage_id=stage_id,
        decision=decision,
    )
    work_unit_fingerprint = _transaction_work_unit_fingerprint(
        fallback=transaction_fingerprint,
        decision=decision,
    )
    route_identity_key = f"{transaction_id}::route"
    attempt_idempotency_key = f"{idempotency_key}::opl-attempt"
    request_idempotency_key = f"{idempotency_key}::opl-request"
    carrier = {
        "surface_kind": SURFACE_KIND,
        "schema_version": 1,
        "source_kind": SOURCE_KIND,
        "target_runtime_owner": transition_contract.RUNTIME_OWNER,
        "target_runtime_kind": transition_contract.RUNTIME_KIND,
        "domain_id": OPL_DOMAIN_ID,
        "runtime_contract_ref": transition_contract.CONTRACT_REF,
        "projection_only": True,
        "transition_request_payload_scope": "identity_refs_and_contract_metadata_only",
        "paper_mission_transaction_ref": transaction_id,
        "stage_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
        "opl_route_command_ref": f"{transaction_id}#opl_route_command",
        "domain_route_handoff_ref": f"{transaction_id}#domain_route_handoff",
        "domain_route_transaction_ref": transaction_id,
        "domain_route_command_ref": f"{transaction_id}#opl_route_command",
        "opl_route_command": deepcopy(route),
        **(
            {
                "declarative_target_stage_id": _required_text(
                    route, "declarative_target_stage_id"
                )
            }
            if _optional_text(route.get("declarative_target_stage_id")) is not None
            else {}
        ),
        "stage_run_ref": stage_run_ref,
        "study_id": study_id,
        "action_type": _required_text(decision, "decision_kind"),
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "route_identity_key": route_identity_key,
        "attempt_idempotency_key": attempt_idempotency_key,
        "idempotency_key": idempotency_key,
        "request_idempotency_key": request_idempotency_key,
        "source_generation": TRANSACTION_CONTRACT_VERSION,
        "expected_version": TRANSACTION_CONTRACT_VERSION,
        "aggregate_identity": {
            "aggregate_kind": "paper_mission_transaction",
            "aggregate_id": transaction_id,
            "mission_id": mission_id,
            "study_id": study_id,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
        },
        "required_postcondition": transition_contract.runtime_postcondition(),
        "required_readback_shape": transition_contract.required_readback_shape(),
        "authority_boundary": transition_contract.mas_request_authority_boundary(
            {
                "paper_mission_transaction_ref": transaction_id,
                "stage_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
                "opl_route_command_ref": f"{transaction_id}#opl_route_command",
            }
        ),
        "forbidden_runtime_fields": transition_contract.request_forbidden_runtime_fields(),
        "mas_projection_cannot_replace": list(
            transition_contract.MAS_PROJECTION_CANNOT_REPLACE
        ),
        "provider_admission_pending": False,
        "provider_admission_requires_opl_runtime_result": True,
        "provider_completion_is_domain_completion": False,
        "dispatch_status": "transition_request_pending",
        "carrier_status": "waiting_for_opl_runtime_payload",
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "can_write_opl_outbox": False,
        "can_write_opl_event": False,
        "can_write_opl_stage_run": False,
        "can_write_provider_attempt": False,
    }
    return validate_paper_mission_opl_runtime_carrier(carrier)


def validate_paper_mission_opl_runtime_carrier(
    carrier: Mapping[str, Any],
) -> dict[str, Any]:
    payload = deepcopy(dict(carrier))
    if _required_text(payload, "surface_kind") != SURFACE_KIND:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier surface_kind must be mas_domain_progress_transition_request"
        )
    if _required_text(payload, "target_runtime_owner") != transition_contract.RUNTIME_OWNER:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier target_runtime_owner must be one-person-lab"
        )
    if _required_text(payload, "target_runtime_kind") != transition_contract.RUNTIME_KIND:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier target_runtime_kind must be DomainProgressTransitionRuntime"
        )
    if _required_text(payload, "domain_id") != OPL_DOMAIN_ID:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier domain_id must be mas"
        )
    for field in (
        "paper_mission_transaction_ref",
        "stage_terminal_decision_ref",
        "opl_route_command_ref",
        "domain_route_handoff_ref",
        "domain_route_transaction_ref",
        "domain_route_command_ref",
        "stage_run_ref",
        "study_id",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "idempotency_key",
        "attempt_idempotency_key",
        "request_idempotency_key",
        "source_generation",
        "expected_version",
    ):
        _required_text(payload, field)
    route = _mapping(payload.get("opl_route_command"))
    if not route:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier opl_route_command must be a mapping"
        )
    _validate_carrier_identity(payload=payload, route=route)
    if not _mapping(payload.get("required_postcondition")):
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier required_postcondition must be a mapping"
        )
    boundary = _mapping(payload.get("authority_boundary"))
    for field in (
        "mas_can_create_opl_outbox_record",
        "mas_can_create_opl_event",
        "mas_can_create_opl_stage_run",
        "mas_can_authorize_provider_admission",
        "mas_can_mark_provider_attempt_running",
        "provider_completion_is_domain_completion",
    ):
        if boundary.get(field) is not False:
            raise PaperMissionTransactionContractError(
                f"paper mission OPL carrier authority_boundary {field} must be false"
            )
    for field in transition_contract.FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS:
        if field in payload:
            raise PaperMissionTransactionContractError(
                f"paper mission OPL carrier must not include runtime field: {field}"
            )
    return payload


def _validate_carrier_identity(
    *,
    payload: Mapping[str, Any],
    route: Mapping[str, Any],
) -> None:
    transaction_ref = _required_text(payload, "domain_route_transaction_ref")
    expected_stage_decision_ref = f"{transaction_ref}#stage_terminal_decision"
    expected_route_ref = f"{transaction_ref}#opl_route_command"
    expected_handoff_ref = f"{transaction_ref}#domain_route_handoff"
    if _required_text(payload, "paper_mission_transaction_ref") != transaction_ref:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier paper_mission_transaction_ref must match domain route transaction"
        )
    if _required_text(payload, "stage_terminal_decision_ref") != expected_stage_decision_ref:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier stage_terminal_decision_ref must match transaction"
        )
    if _required_text(payload, "opl_route_command_ref") != expected_route_ref:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier opl_route_command_ref must match transaction"
        )
    if _required_text(payload, "domain_route_handoff_ref") != expected_handoff_ref:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier domain_route_handoff_ref must match transaction"
        )
    if _required_text(payload, "domain_route_command_ref") != expected_route_ref:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier domain_route_command_ref must match transaction"
        )
    if _required_text(route, "source_terminal_decision_ref") != expected_stage_decision_ref:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier route source_terminal_decision_ref must match transaction"
        )
    if _required_text(route, "stage_run_ref") != _required_text(payload, "stage_run_ref"):
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier route stage_run_ref must match carrier"
        )
    if _required_text(route, "runtime_owner") != _required_text(payload, "target_runtime_owner"):
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier route runtime_owner must match target runtime owner"
        )
    command_kind = _required_text(route, "command_kind")
    if command_kind in {"start_next_stage", "resume_stage", "route_back"}:
        route_target_stage_id = _required_text(route, "declarative_target_stage_id")
        if _required_text(payload, "declarative_target_stage_id") != route_target_stage_id:
            raise PaperMissionTransactionContractError(
                "paper mission OPL carrier declarative_target_stage_id must match route"
            )
    idempotency_key = _required_text(payload, "idempotency_key")
    if _required_text(payload, "route_identity_key") != f"{transaction_ref}::route":
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier route_identity_key must bind transaction"
        )
    if _required_text(payload, "attempt_idempotency_key") != f"{idempotency_key}::opl-attempt":
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier attempt_idempotency_key must derive from idempotency_key"
        )
    if _required_text(payload, "request_idempotency_key") != f"{idempotency_key}::opl-request":
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier request_idempotency_key must derive from idempotency_key"
        )
    aggregate_identity = _mapping(payload.get("aggregate_identity"))
    if not aggregate_identity:
        raise PaperMissionTransactionContractError(
            "paper mission OPL carrier aggregate_identity must be a mapping"
        )
    expected_aggregate_values = {
        "aggregate_kind": "paper_mission_transaction",
        "aggregate_id": transaction_ref,
        "study_id": _required_text(payload, "study_id"),
        "work_unit_id": _required_text(payload, "work_unit_id"),
        "work_unit_fingerprint": _required_text(payload, "work_unit_fingerprint"),
    }
    for field, expected in expected_aggregate_values.items():
        if _required_text(aggregate_identity, field) != expected:
            raise PaperMissionTransactionContractError(
                f"paper mission OPL carrier aggregate_identity {field} must match carrier"
            )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _transaction_work_unit_id(*, stage_id: str, decision: Mapping[str, Any]) -> str:
    decision_kind = _required_text(decision, "decision_kind")
    if decision_kind == "continue_same_stage":
        return _required_text(decision, "next_work_unit")
    return stage_id


def _transaction_work_unit_fingerprint(
    *,
    fallback: str,
    decision: Mapping[str, Any],
) -> str:
    return _optional_text(decision.get("work_unit_fingerprint")) or fallback


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    text = value.strip() if isinstance(value, str) else None
    if not text:
        raise PaperMissionTransactionContractError(
            f"paper mission OPL carrier {field} must be a non-empty string"
        )
    return text


def _optional_text(value: object) -> str | None:
    text = value.strip() if isinstance(value, str) else None
    return text or None


__all__ = [
    "SOURCE_KIND",
    "OPL_DOMAIN_ID",
    "SURFACE_KIND",
    "paper_mission_opl_runtime_carrier",
    "validate_paper_mission_opl_runtime_carrier",
]
