from __future__ import annotations

from collections.abc import Mapping, Sequence
from copy import deepcopy
from dataclasses import dataclass
from typing import Any


CONTRACT_VERSION = "paper-mission-transaction.v1"
REQUIRED_FIELDS = (
    "transaction_id",
    "mission_id",
    "study_id",
    "stage_id",
    "stage_run_ref",
    "stage_terminal_decision",
    "opl_route_command",
    "artifact_delta_refs",
    "paper_audit_pack_refs",
    "authority_boundary",
    "idempotency",
)
ALLOWED_DECISION_KINDS = frozenset(
    {
        "advance",
        "continue_same_stage",
        "route_back",
        "typed_blocker",
        "human_gate",
        "mission_complete",
    }
)
ALLOWED_ROUTE_COMMAND_KINDS = frozenset(
    {
        "start_next_stage",
        "resume_stage",
        "route_back",
        "wait_for_human",
        "stop_with_typed_blocker",
        "complete_mission",
    }
)
DECISION_KIND_TO_ROUTE_COMMAND = {
    "advance": "start_next_stage",
    "continue_same_stage": "resume_stage",
    "route_back": "route_back",
    "typed_blocker": "stop_with_typed_blocker",
    "human_gate": "wait_for_human",
    "mission_complete": "complete_mission",
}
REQUIRED_DECISION_FIELDS_BY_KIND = {
    "advance": ("next_stage_id",),
    "continue_same_stage": ("next_work_unit",),
    "route_back": ("target_stage_id", "repair_scope"),
    "typed_blocker": ("blocker_id", "unblock_condition"),
    "human_gate": ("question", "required_receipt"),
    "mission_complete": ("package_ref",),
}
REQUIRED_PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)
AUTHORITY_FLAGS_MUST_BE_FALSE = (
    "writes_authority_surface",
    "writes_publication_eval",
    "writes_controller_decision",
    "writes_owner_receipt",
    "writes_typed_blocker",
    "writes_human_gate",
    "writes_current_package",
    "writes_runtime_queue",
    "writes_provider_attempt",
    "writes_yang_authority",
)


class PaperMissionTransactionContractError(ValueError):
    """Raised when a PaperMissionTransaction payload violates the MAS/OPL boundary."""


@dataclass(frozen=True)
class PaperMissionTransaction:
    transaction_id: str
    mission_id: str
    study_id: str
    stage_id: str
    stage_run_ref: str
    stage_terminal_decision: dict[str, Any]
    opl_route_command: dict[str, Any]
    artifact_delta_refs: tuple[dict[str, Any], ...]
    paper_audit_pack_refs: dict[str, Any]
    authority_boundary: dict[str, Any]
    idempotency: dict[str, Any]
    payload: dict[str, Any]

    @classmethod
    def from_payload(cls, payload: Mapping[str, Any]) -> "PaperMissionTransaction":
        if not isinstance(payload, Mapping):
            raise PaperMissionTransactionContractError(
                "PaperMissionTransaction payload must be a mapping"
            )
        normalized = deepcopy(dict(payload))
        _validate_required_fields(normalized)
        schema_version = _optional_text(normalized.get("schema_version"))
        if schema_version is not None and schema_version != CONTRACT_VERSION:
            raise PaperMissionTransactionContractError(
                f"unsupported PaperMissionTransaction schema_version: {schema_version}"
            )

        transaction = cls(
            transaction_id=_required_text(normalized, "transaction_id"),
            mission_id=_required_text(normalized, "mission_id"),
            study_id=_required_text(normalized, "study_id"),
            stage_id=_required_text(normalized, "stage_id"),
            stage_run_ref=_required_text(normalized, "stage_run_ref"),
            stage_terminal_decision=_required_mapping(
                normalized,
                "stage_terminal_decision",
            ),
            opl_route_command=_required_mapping(normalized, "opl_route_command"),
            artifact_delta_refs=_required_mapping_list(
                normalized,
                "artifact_delta_refs",
            ),
            paper_audit_pack_refs=_required_mapping(
                normalized,
                "paper_audit_pack_refs",
            ),
            authority_boundary=_required_mapping(normalized, "authority_boundary"),
            idempotency=_required_mapping(normalized, "idempotency"),
            payload=normalized,
        )
        return transaction.validate()

    def validate(self) -> "PaperMissionTransaction":
        _validate_required_fields(self.payload)
        _validate_identity(self)
        _validate_artifact_delta_refs(self.artifact_delta_refs)
        _validate_stage_terminal_decision(self.stage_terminal_decision)
        _validate_opl_route_command(
            transaction=self,
            decision=self.stage_terminal_decision,
            route=self.opl_route_command,
        )
        _validate_paper_audit_pack_refs(self.paper_audit_pack_refs)
        _validate_authority_boundary(self.authority_boundary)
        _validate_idempotency(self.idempotency)
        return self

    def to_dict(self) -> dict[str, Any]:
        return deepcopy(self.payload)


def stage_terminal_decision_for_consume_result(
    *,
    mission_id: str,
    study_id: str,
    stage_id: str,
    consume_result: Mapping[str, Any],
    default_next_owner: str,
    default_next_stage_id: str,
    default_next_work_unit: str,
    default_reason: str,
) -> dict[str, Any]:
    status = _text(consume_result.get("status")) or "not_consumed"
    outcome = _text(consume_result.get("outcome")) or status
    if status == "accepted":
        decision = {
            "decision_kind": "advance",
            "status": "accepted",
            "reason": default_reason,
            "next_owner": default_next_owner,
            "next_stage_id": default_next_stage_id,
            "accepted_result": outcome,
        }
    elif status == "route_back":
        decision = {
            "decision_kind": "route_back",
            "status": "route_back",
            "reason": default_reason,
            "next_owner": "mission_executor",
            "target_stage_id": stage_id,
            "repair_scope": _text(consume_result.get("resume_condition"))
            or "revise paper mission candidate and resubmit to MAS authority",
        }
    elif status == "typed_blocker":
        decision = {
            "decision_kind": "typed_blocker",
            "status": "typed_blocker",
            "reason": default_reason,
            "next_owner": default_next_owner,
            "blocker_id": _text(consume_result.get("blocker_id"))
            or "mas_stage_terminal_typed_blocker",
            "unblock_condition": _text(consume_result.get("resume_condition"))
            or "named owner supplies the required typed-blocker input",
        }
    elif status == "human_gate":
        decision = {
            "decision_kind": "human_gate",
            "status": "human_gate",
            "reason": default_reason,
            "next_owner": "human",
            "question": _text(consume_result.get("question"))
            or "Should MAS accept, route back, or block this paper mission candidate?",
            "required_receipt": _text(consume_result.get("required_receipt"))
            or f"human-gate::{study_id}::{stage_id}::{mission_id}",
        }
    elif status == "rejected":
        decision = {
            "decision_kind": "route_back",
            "status": "rejected",
            "reason": default_reason,
            "next_owner": "mission_executor",
            "target_stage_id": stage_id,
            "repair_scope": _text(consume_result.get("resume_condition"))
            or "remove rejected claims and resubmit a corrected candidate",
        }
    else:
        decision = {
            "decision_kind": "continue_same_stage",
            "status": status,
            "reason": default_reason,
            "next_owner": default_next_owner,
            "next_work_unit": default_next_work_unit,
        }
    _validate_stage_terminal_decision(decision)
    return decision


def opl_route_command_for_terminal_decision(
    *,
    terminal_decision: Mapping[str, Any],
    transaction_id: str,
    stage_run_ref: str,
) -> dict[str, Any]:
    decision_kind = _text(terminal_decision.get("decision_kind"))
    command_kind = DECISION_KIND_TO_ROUTE_COMMAND.get(decision_kind or "")
    if command_kind is None:
        raise PaperMissionTransactionContractError(
            f"unsupported terminal decision kind for route command: {decision_kind}"
        )
    target = _route_target(terminal_decision)
    command = {
        "command_kind": command_kind,
        "target": target,
        "reason": _text(terminal_decision.get("reason"))
        or "mas_stage_terminal_decision",
        "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
        "stage_run_ref": stage_run_ref,
        "runtime_owner": "one-person-lab",
        "authority_note": (
            "OPL may carry this route command but cannot reinterpret provider "
            "completion as MAS paper authority completion."
        ),
    }
    _validate_opl_route_command_shape(decision=terminal_decision, route=command)
    return command


def build_paper_mission_transaction(
    *,
    mission_id: str,
    study_id: str,
    stage_id: str,
    stage_run_ref: str,
    terminal_decision: Mapping[str, Any],
    artifact_delta_refs: Sequence[Mapping[str, Any]],
    paper_audit_pack_refs: Mapping[str, Any],
    idempotency_basis: str,
) -> dict[str, Any]:
    transaction_id = f"paper-mission-transaction::{study_id}::{stage_id}::{mission_id}"
    route_command = opl_route_command_for_terminal_decision(
        terminal_decision=terminal_decision,
        transaction_id=transaction_id,
        stage_run_ref=stage_run_ref,
    )
    payload = {
        "schema_version": CONTRACT_VERSION,
        "transaction_id": transaction_id,
        "mission_id": mission_id,
        "study_id": study_id,
        "stage_id": stage_id,
        "stage_run_ref": stage_run_ref,
        "stage_terminal_decision": deepcopy(dict(terminal_decision)),
        "opl_route_command": route_command,
        "artifact_delta_refs": [deepcopy(dict(item)) for item in artifact_delta_refs],
        "paper_audit_pack_refs": deepcopy(dict(paper_audit_pack_refs)),
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            **{flag: False for flag in AUTHORITY_FLAGS_MUST_BE_FALSE},
        },
        "idempotency": {
            "idempotency_key": f"{study_id}::{stage_id}::{idempotency_basis}",
            "transaction_fingerprint": (
                f"{mission_id}::{stage_id}::"
                f"{_text(terminal_decision.get('decision_kind')) or 'decision'}::"
                f"{_text(terminal_decision.get('status')) or 'status'}"
            ),
        },
    }
    return PaperMissionTransaction.from_payload(payload).to_dict()


def _validate_required_fields(payload: Mapping[str, Any]) -> None:
    for field in REQUIRED_FIELDS:
        if field not in payload:
            raise PaperMissionTransactionContractError(
                f"missing required field: {field}"
            )


def _validate_identity(transaction: PaperMissionTransaction) -> None:
    for field, value in (
        ("transaction_id", transaction.transaction_id),
        ("mission_id", transaction.mission_id),
        ("study_id", transaction.study_id),
        ("stage_id", transaction.stage_id),
        ("stage_run_ref", transaction.stage_run_ref),
    ):
        if value != _required_text(transaction.payload, field):
            raise PaperMissionTransactionContractError(f"{field} does not match payload")


def _validate_artifact_delta_refs(refs: tuple[dict[str, Any], ...]) -> None:
    if not refs:
        raise PaperMissionTransactionContractError(
            "artifact_delta_refs must not be empty"
        )
    _validate_mapping_items(
        refs,
        "artifact_delta_refs",
        ("ref_id", "ref_kind", "uri"),
    )


def _validate_stage_terminal_decision(decision: Mapping[str, Any]) -> None:
    decision_kind = _required_text(decision, "decision_kind")
    if decision_kind not in ALLOWED_DECISION_KINDS:
        raise PaperMissionTransactionContractError(
            f"unsupported stage_terminal_decision decision_kind: {decision_kind}"
        )
    _required_text(decision, "status")
    _required_text(decision, "reason")
    _required_text(decision, "next_owner")
    for field in REQUIRED_DECISION_FIELDS_BY_KIND[decision_kind]:
        _required_text(decision, field)


def _validate_opl_route_command(
    *,
    transaction: PaperMissionTransaction,
    decision: Mapping[str, Any],
    route: Mapping[str, Any],
) -> None:
    _validate_opl_route_command_shape(decision=decision, route=route)
    source_ref = _required_text(route, "source_terminal_decision_ref")
    expected_source_ref = f"{transaction.transaction_id}#stage_terminal_decision"
    if source_ref != expected_source_ref:
        raise PaperMissionTransactionContractError(
            "opl_route_command source_terminal_decision_ref must match transaction"
        )
    if _required_text(route, "stage_run_ref") != transaction.stage_run_ref:
        raise PaperMissionTransactionContractError(
            "opl_route_command stage_run_ref must match transaction stage_run_ref"
        )
    if _required_text(route, "runtime_owner") != "one-person-lab":
        raise PaperMissionTransactionContractError(
            "opl_route_command runtime_owner must be one-person-lab"
        )


def _validate_opl_route_command_shape(
    *,
    decision: Mapping[str, Any],
    route: Mapping[str, Any],
) -> None:
    command_kind = _required_text(route, "command_kind")
    if command_kind not in ALLOWED_ROUTE_COMMAND_KINDS:
        raise PaperMissionTransactionContractError(
            f"unsupported opl_route_command command_kind: {command_kind}"
        )
    decision_kind = _required_text(decision, "decision_kind")
    expected_command_kind = DECISION_KIND_TO_ROUTE_COMMAND[decision_kind]
    if command_kind != expected_command_kind:
        raise PaperMissionTransactionContractError(
            "opl_route_command command_kind does not match stage_terminal_decision"
        )
    _required_text(route, "target")
    _required_text(route, "reason")
    _required_text(route, "source_terminal_decision_ref")
    _required_text(route, "stage_run_ref")
    _required_text(route, "runtime_owner")


def _validate_paper_audit_pack_refs(audit_pack_refs: Mapping[str, Any]) -> None:
    for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES:
        family_refs = audit_pack_refs.get(family)
        try:
            refs = _required_mapping_list({family: family_refs}, family)
        except PaperMissionTransactionContractError as exc:
            message = str(exc)
            family_prefix = f"{family} "
            if message.startswith(family_prefix):
                message = message[len(family_prefix):]
            raise PaperMissionTransactionContractError(
                f"paper_audit_pack_refs.{family} {message}"
            ) from exc
        if not refs:
            raise PaperMissionTransactionContractError(
                f"paper_audit_pack_refs.{family} must not be empty"
            )
        _validate_mapping_items(
            refs,
            f"paper_audit_pack_refs.{family}",
            ("ref_id", "ref_kind", "uri"),
        )


def _validate_authority_boundary(boundary: Mapping[str, Any]) -> None:
    if _required_text(boundary, "mas_authority_owner") != "MedAutoScience":
        raise PaperMissionTransactionContractError(
            "authority_boundary mas_authority_owner must be MedAutoScience"
        )
    if _required_text(boundary, "runtime_owner") != "one-person-lab":
        raise PaperMissionTransactionContractError(
            "authority_boundary runtime_owner must be one-person-lab"
        )
    for flag in AUTHORITY_FLAGS_MUST_BE_FALSE:
        if boundary.get(flag) is not False:
            raise PaperMissionTransactionContractError(
                f"authority_boundary {flag} must be false"
            )


def _validate_idempotency(idempotency: Mapping[str, Any]) -> None:
    _required_text(idempotency, "idempotency_key")
    _required_text(idempotency, "transaction_fingerprint")


def _route_target(decision: Mapping[str, Any]) -> str:
    decision_kind = _required_text(decision, "decision_kind")
    if decision_kind == "advance":
        return _required_text(decision, "next_stage_id")
    if decision_kind == "continue_same_stage":
        return _required_text(decision, "next_work_unit")
    if decision_kind == "route_back":
        return _required_text(decision, "target_stage_id")
    if decision_kind == "typed_blocker":
        return _required_text(decision, "blocker_id")
    if decision_kind == "human_gate":
        return _required_text(decision, "required_receipt")
    if decision_kind == "mission_complete":
        return _required_text(decision, "package_ref")
    raise PaperMissionTransactionContractError(
        f"unsupported terminal decision kind for route target: {decision_kind}"
    )


def _required_mapping(payload: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = payload.get(field)
    if not isinstance(value, Mapping):
        raise PaperMissionTransactionContractError(f"{field} must be a mapping")
    return deepcopy(dict(value))


def _required_mapping_list(
    payload: Mapping[str, Any],
    field: str,
) -> tuple[dict[str, Any], ...]:
    value = payload.get(field)
    if isinstance(value, (str, bytes)) or not isinstance(value, Sequence):
        raise PaperMissionTransactionContractError(f"{field} must be a list of mappings")
    items: list[dict[str, Any]] = []
    for index, item in enumerate(value):
        if not isinstance(item, Mapping):
            raise PaperMissionTransactionContractError(
                f"{field}[{index}] must be a mapping"
            )
        items.append(deepcopy(dict(item)))
    return tuple(items)


def _validate_mapping_items(
    items: tuple[dict[str, Any], ...],
    field: str,
    required_fields: tuple[str, ...],
) -> None:
    for index, item in enumerate(items):
        for required_field in required_fields:
            if not _text(item.get(required_field)):
                raise PaperMissionTransactionContractError(
                    f"{field}[{index}] missing required field: {required_field}"
                )


def _required_text(payload: Mapping[str, Any], field: str) -> str:
    value = payload.get(field)
    text = _text(value)
    if text is None:
        raise PaperMissionTransactionContractError(
            f"{field} must be a non-empty string"
        )
    return text


def _optional_text(value: Any) -> str | None:
    if value is None:
        return None
    text = _text(value)
    if text is None:
        raise PaperMissionTransactionContractError(
            "optional text value must be a non-empty string"
        )
    return text


def _text(value: Any) -> str | None:
    if not isinstance(value, str):
        return None
    stripped = value.strip()
    return stripped or None


__all__ = [
    "ALLOWED_DECISION_KINDS",
    "ALLOWED_ROUTE_COMMAND_KINDS",
    "CONTRACT_VERSION",
    "PaperMissionTransaction",
    "PaperMissionTransactionContractError",
    "build_paper_mission_transaction",
    "opl_route_command_for_terminal_decision",
    "stage_terminal_decision_for_consume_result",
]
