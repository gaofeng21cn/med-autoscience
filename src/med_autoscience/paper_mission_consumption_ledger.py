from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any


def write_paper_mission_consumption_ledger_outputs(
    *,
    output_root: Path,
    study_id: str,
    candidate_ref: str,
    authority_consume_readback: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    mission_candidate: Mapping[str, Any],
    source: str,
    writes_yang_ops_consumption_ledger: bool,
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    study_root = output_root.expanduser().resolve() / study_id
    study_root.mkdir(parents=True, exist_ok=True)
    consume_record = paper_mission_consumption_record(
        study_id=study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        transaction_readback=transaction_readback,
        source=source,
        forbidden_authority_writes=forbidden_authority_writes,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    terminal_decision_packet = stage_terminal_decision_packet(
        study_id=study_id,
        candidate_ref=candidate_ref,
        transaction_readback=transaction_readback,
        forbidden_authority_writes=forbidden_authority_writes,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    route_command_packet = opl_route_command_packet(
        study_id=study_id,
        candidate_ref=candidate_ref,
        transaction_readback=transaction_readback,
        forbidden_authority_writes=forbidden_authority_writes,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    route_handoff = opl_route_handoff_record(
        study_id=study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        transaction_readback=transaction_readback,
        mission_candidate=mission_candidate,
        source=source,
        forbidden_authority_writes=forbidden_authority_writes,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    normalized_consume_readback = paper_mission_consumption_ledger_readback(
        study_id=study_id,
        candidate_ref=candidate_ref,
        authority_consume_readback=authority_consume_readback,
        transaction_readback=transaction_readback,
        route_handoff=route_handoff,
        forbidden_authority_writes=forbidden_authority_writes,
        forbidden_authority_claims=forbidden_authority_claims,
    )
    outputs = {
        "consume_record": study_root / "consume_record.json",
        "consume_readback": study_root / "consume_readback.json",
        "stage_terminal_decision": study_root / "stage_terminal_decision.json",
        "opl_route_command": study_root / "opl_route_command.json",
        "opl_route_handoff": study_root / "opl_route_handoff.json",
    }
    payloads = {
        "consume_record": consume_record,
        "consume_readback": normalized_consume_readback,
        "stage_terminal_decision": terminal_decision_packet,
        "opl_route_command": route_command_packet,
        "opl_route_handoff": route_handoff,
    }
    written_files: list[str] = []
    file_sha256: dict[str, str] = {}
    for key, path in outputs.items():
        text = json.dumps(payloads[key], ensure_ascii=False, indent=2) + "\n"
        path.write_text(text, encoding="utf-8")
        written_files.append(str(path))
        file_sha256[str(path)] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return {
        "mode": "governed_consume_record",
        "output_root": str(study_root),
        "written_files": written_files,
        "file_sha256": file_sha256,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_yang_ops_consumption_ledger": writes_yang_ops_consumption_ledger,
        "consume_record_ref": str(outputs["consume_record"]),
        "consume_readback_ref": str(outputs["consume_readback"]),
        "stage_terminal_decision_ref": str(outputs["stage_terminal_decision"]),
        "opl_route_command_ref": str(outputs["opl_route_command"]),
        "opl_route_handoff_ref": str(outputs["opl_route_handoff"]),
        "route_handoff_status": route_handoff["handoff_status"],
        "route_command_kind": route_handoff["route_command_kind"],
        "next_owner": route_handoff["next_owner"],
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def paper_mission_consumption_ledger_readback(
    *,
    study_id: str,
    candidate_ref: str,
    authority_consume_readback: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    route_handoff: Mapping[str, Any],
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    route = _mapping(transaction_readback.get("opl_route_command"))
    selected_outcome = _text(authority_consume_readback.get("selected_outcome"))
    status = _text(authority_consume_readback.get("status"))
    next_owner = _next_owner(authority_consume_readback, transaction_readback)
    handoff_status = _text(route_handoff.get("handoff_status")) or _route_handoff_status(
        selected_outcome=selected_outcome,
        status=status,
        transaction_readback=transaction_readback,
    )
    return {
        **dict(authority_consume_readback),
        "surface_kind": "mas_paper_mission_candidate_consume_readback",
        "schema_version": 1,
        "study_id": study_id,
        "candidate_ref": candidate_ref,
        "consume_candidate_status": _consume_candidate_status_from_terminal(
            status=status,
            selected_outcome=selected_outcome,
            stage_terminal_decision=decision,
        ),
        "selected_outcome": selected_outcome,
        "consume_result": _mapping(authority_consume_readback.get("consume_result")),
        "next_owner": next_owner,
        "route_handoff_status": handoff_status,
        "paper_mission_transaction": transaction,
        "paper_mission_transaction_ref": _transaction_id(transaction_readback),
        "stage_terminal_decision": decision,
        "stage_terminal_decision_ref": _stage_terminal_decision_ref(
            transaction_readback
        ),
        "opl_route_command": route,
        "opl_route_command_ref": _opl_route_command_ref(transaction_readback),
        "opl_runtime_carrier": _mapping(transaction_readback.get("opl_runtime_carrier")),
        "transaction_state": _text(transaction_readback.get("transaction_state")),
        "authority_materialized": False,
        "candidate_is_authority": False,
        "counts_as_owner_consumption_evidence": True,
        "counts_as_stage_terminalizer_evidence": _transaction_materialized(
            transaction_readback
        ),
        "counts_as_opl_route_handoff_evidence": _transaction_materialized(
            transaction_readback
        ),
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "can_submit_to_opl_runtime": bool(
            _transaction_materialized(transaction_readback)
            and handoff_status == "ready_for_opl_route_command"
        ),
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_boundary": _no_authority_boundary(
            surface_role="paper_mission_consumption_ledger_readback"
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def paper_mission_consumption_record(
    *,
    study_id: str,
    candidate_ref: str,
    authority_consume_readback: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    source: str,
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    consume_result = _mapping(authority_consume_readback.get("consume_result"))
    selected_outcome = _text(authority_consume_readback.get("selected_outcome"))
    status = _text(authority_consume_readback.get("status"))
    candidate_id = _text(authority_consume_readback.get("candidate_id"))
    mission_id = _text(authority_consume_readback.get("mission_id"))
    route_handoff_status = _route_handoff_status(
        selected_outcome=selected_outcome,
        status=status,
        transaction_readback=transaction_readback,
    )
    next_owner = _next_owner(authority_consume_readback, transaction_readback)
    return {
        "surface_kind": "mas_paper_mission_candidate_consumption_record",
        "schema_version": 1,
        "source": source,
        "study_id": study_id,
        "mission_id": mission_id,
        "candidate_id": candidate_id,
        "candidate_ref": candidate_ref,
        "status": status,
        "selected_outcome": selected_outcome,
        "consume_result": consume_result,
        "next_owner": next_owner,
        "route_handoff_status": route_handoff_status,
        "authority_materialized": False,
        "candidate_is_authority": False,
        "counts_as_owner_consumption_evidence": True,
        "counts_as_stage_terminalizer_evidence": _transaction_materialized(
            transaction_readback
        ),
        "counts_as_opl_route_handoff_evidence": _transaction_materialized(
            transaction_readback
        ),
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "governed_owner_surface": "paper_mission_consumption_ledger",
        "required_followthrough": _consumption_required_followthrough(
            status=status,
            selected_outcome=selected_outcome,
            next_owner=next_owner,
            route_handoff_status=route_handoff_status,
        ),
        "accepted_candidate": authority_consume_readback.get("accepted_candidate"),
        "route_back": authority_consume_readback.get("route_back"),
        "typed_blocker_required": authority_consume_readback.get(
            "typed_blocker_required"
        ),
        "human_gate_required": authority_consume_readback.get("human_gate_required"),
        "rejected_candidate": authority_consume_readback.get("rejected_candidate"),
        "source_readiness_refs": authority_consume_readback.get(
            "source_readiness_refs",
            [],
        ),
        "paper_mission_transaction_ref": _transaction_id(transaction_readback),
        "stage_terminal_decision_ref": _stage_terminal_decision_ref(
            transaction_readback
        ),
        "opl_route_command_ref": _opl_route_command_ref(transaction_readback),
        "authority_boundary": _no_authority_boundary(
            surface_role="governed_paper_mission_candidate_consumption_record"
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def stage_terminal_decision_packet(
    *,
    study_id: str,
    candidate_ref: str,
    transaction_readback: Mapping[str, Any],
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    return {
        "surface_kind": "mas_paper_mission_stage_terminal_decision_packet",
        "schema_version": 1,
        "study_id": study_id,
        "candidate_ref": candidate_ref,
        "paper_mission_transaction_ref": _transaction_id(transaction_readback),
        "stage_terminal_decision_ref": _stage_terminal_decision_ref(
            transaction_readback
        ),
        "transaction_state": _text(transaction_readback.get("transaction_state")),
        "stage_id": _text(transaction.get("stage_id")),
        "stage_run_ref": _text(transaction.get("stage_run_ref")),
        "terminal_decision_materialized": _transaction_materialized(
            transaction_readback
        ),
        "stage_terminal_decision": decision,
        "next_owner": _text(decision.get("next_owner")) or "mas_authority_kernel",
        "authority_boundary": _no_authority_boundary(
            surface_role="stage_terminal_decision_packet"
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def opl_route_command_packet(
    *,
    study_id: str,
    candidate_ref: str,
    transaction_readback: Mapping[str, Any],
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    route = _mapping(transaction_readback.get("opl_route_command"))
    carrier = _mapping(transaction_readback.get("opl_runtime_carrier"))
    return {
        "surface_kind": "mas_paper_mission_opl_route_command_packet",
        "schema_version": 1,
        "study_id": study_id,
        "candidate_ref": candidate_ref,
        "paper_mission_transaction_ref": _transaction_id(transaction_readback),
        "opl_route_command_ref": _opl_route_command_ref(transaction_readback),
        "route_command_materialized": _transaction_materialized(transaction_readback),
        "command_kind": _text(route.get("command_kind")),
        "target": _text(route.get("target")),
        "runtime_owner": _text(route.get("runtime_owner")) or "one-person-lab",
        "opl_route_command": route,
        "opl_runtime_carrier": carrier,
        "projection_only": True,
        "writes_opl_outbox": False,
        "writes_opl_event": False,
        "writes_opl_stage_run": False,
        "writes_provider_attempt": False,
        "authority_boundary": _no_authority_boundary(
            surface_role="opl_route_command_packet"
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def opl_route_handoff_record(
    *,
    study_id: str,
    candidate_ref: str,
    authority_consume_readback: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    mission_candidate: Mapping[str, Any],
    source: str,
    forbidden_authority_writes: tuple[str, ...],
    forbidden_authority_claims: tuple[str, ...],
) -> dict[str, Any]:
    route = _mapping(transaction_readback.get("opl_route_command"))
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    carrier = _mapping(transaction_readback.get("opl_runtime_carrier"))
    carrier_identity = _opl_runtime_carrier_identity(carrier)
    selected_outcome = _text(authority_consume_readback.get("selected_outcome"))
    status = _text(authority_consume_readback.get("status"))
    handoff_status = _route_handoff_status(
        selected_outcome=selected_outcome,
        status=status,
        transaction_readback=transaction_readback,
    )
    transaction_materialized = _transaction_materialized(transaction_readback)
    command_kind = _text(route.get("command_kind")) or "not_materialized"
    next_owner = _next_owner(authority_consume_readback, transaction_readback)
    return {
        "surface_kind": "mas_paper_mission_opl_route_handoff_record",
        "schema_version": 1,
        "source": source,
        "study_id": study_id,
        "mission_id": _text(mission_candidate.get("mission_id")),
        "candidate_ref": candidate_ref,
        "candidate_id": _text(authority_consume_readback.get("candidate_id")),
        "status": status,
        "selected_outcome": selected_outcome,
        "handoff_status": handoff_status,
        "next_owner": next_owner,
        "paper_mission_transaction_ref": _transaction_id(transaction_readback),
        "transaction_state": _text(transaction_readback.get("transaction_state")),
        "stage_terminal_decision_ref": _stage_terminal_decision_ref(
            transaction_readback
        ),
        "stage_terminal_decision": decision,
        "opl_route_command_ref": _opl_route_command_ref(transaction_readback),
        "opl_route_command": route,
        "opl_runtime_carrier": carrier,
        "route_identity_key": carrier_identity.get("route_identity_key"),
        "attempt_idempotency_key": carrier_identity.get("attempt_idempotency_key"),
        "request_idempotency_key": carrier_identity.get("request_idempotency_key"),
        "idempotency_key": carrier_identity.get("idempotency_key"),
        "route_command_kind": command_kind,
        "route_target": _text(route.get("target")),
        "transaction_materialized": transaction_materialized,
        "can_submit_to_opl_runtime": transaction_materialized
        and handoff_status == "ready_for_opl_route_command",
        "can_claim_opl_runtime_enqueued": False,
        "can_claim_opl_stage_run_created": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "mission_candidate_summary": _mission_candidate_summary(mission_candidate),
        "required_followthrough": _route_handoff_required_followthrough(
            handoff_status=handoff_status,
            route_command_kind=command_kind,
            next_owner=next_owner,
        ),
        "authority_boundary": _no_authority_boundary(
            surface_role="opl_route_handoff_record"
        ),
        "forbidden_authority_claims": list(forbidden_authority_claims),
        "forbidden_authority_writes": list(forbidden_authority_writes),
    }


def _opl_runtime_carrier_identity(carrier: Mapping[str, Any]) -> dict[str, str | None]:
    return {
        "route_identity_key": _text(carrier.get("route_identity_key")),
        "attempt_idempotency_key": _text(carrier.get("attempt_idempotency_key")),
        "request_idempotency_key": _text(carrier.get("request_idempotency_key")),
        "idempotency_key": _text(carrier.get("idempotency_key")),
    }


def _mission_candidate_summary(mission_candidate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "mission_id": _text(mission_candidate.get("mission_id")),
        "mission_state": _text(mission_candidate.get("mission_state")),
        "transaction_state": _text(mission_candidate.get("transaction_state")),
        "consume_result": _mapping(mission_candidate.get("consume_result")),
        "artifact_delta_refs": [
            {
                "delta_id": _text(delta.get("delta_id")),
                "artifact_ref": _text(delta.get("artifact_ref")),
                "delta_kind": _text(delta.get("delta_kind")),
                "status": _text(delta.get("status")),
            }
            for delta in _mapping_list(mission_candidate.get("artifact_delta_ledger"))
        ],
    }


def _route_handoff_status(
    *,
    selected_outcome: str | None,
    status: str | None,
    transaction_readback: Mapping[str, Any],
) -> str:
    if selected_outcome == "typed_blocker_required" or status == "typed_blocker_required":
        return "waiting_for_typed_blocker_authority"
    if selected_outcome == "human_gate_required" or status == "human_gate_required":
        return "waiting_for_human_gate_authority"
    if selected_outcome == "rejected_candidate" or status == "rejected_candidate":
        return "waiting_for_corrected_candidate"
    if not _transaction_materialized(transaction_readback):
        return "not_actionable_without_materialized_transaction"
    route = _mapping(transaction_readback.get("opl_route_command"))
    command_kind = _text(route.get("command_kind"))
    if command_kind in {"start_next_stage", "resume_stage", "route_back"}:
        return "ready_for_opl_route_command"
    if command_kind == "stop_with_typed_blocker":
        return "waiting_for_typed_blocker_authority"
    if command_kind == "wait_for_human":
        return "waiting_for_human_gate_authority"
    if command_kind == "complete_mission":
        return "waiting_for_mission_complete_authority"
    return "waiting_for_owner_resolution"


def _consume_candidate_status_from_terminal(
    *,
    status: str | None,
    selected_outcome: str | None,
    stage_terminal_decision: Mapping[str, Any],
) -> str:
    decision_kind = _text(stage_terminal_decision.get("decision_kind"))
    if decision_kind == "route_back":
        return "route_back"
    if decision_kind == "typed_blocker":
        return "typed_blocker"
    if decision_kind == "human_gate":
        return "human_gate"
    if decision_kind == "continue_same_stage":
        return selected_outcome or status or "accepted"
    if decision_kind == "advance":
        return selected_outcome or status or "accepted"
    if decision_kind == "mission_complete":
        return "mission_complete"
    if selected_outcome == "typed_blocker_required" or status == "typed_blocker_required":
        return "typed_blocker"
    if selected_outcome == "human_gate_required" or status == "human_gate_required":
        return "human_gate"
    if selected_outcome == "rejected_candidate" or status == "rejected_candidate":
        return "rejected"
    return selected_outcome or status or "not_consumed"


def _consumption_required_followthrough(
    *,
    status: str | None,
    selected_outcome: str | None,
    next_owner: str,
    route_handoff_status: str,
) -> str:
    if route_handoff_status == "ready_for_opl_route_command":
        return (
            f"{next_owner} can consume the OPL route handoff for the same "
            "PaperMissionTransaction; this ledger still does not prove OPL "
            "outbox/event/StageRun creation or paper progress."
        )
    if route_handoff_status == "not_actionable_without_materialized_transaction":
        return (
            "A materialized PaperMissionTransaction is required before this consume "
            "record can become an OPL route handoff."
        )
    if status == "typed_blocker_required" or selected_outcome == "typed_blocker_required":
        return (
            f"{next_owner} must materialize or reject the typed blocker request; "
            "this ledger record is not the typed blocker authority file."
        )
    if status == "human_gate_required" or selected_outcome == "human_gate_required":
        return (
            f"{next_owner} must record the human gate decision receipt; this ledger "
            "record is not a human gate authority file."
        )
    if status == "rejected_candidate" or selected_outcome == "rejected_candidate":
        return (
            f"{next_owner} must submit a corrected candidate before this mission can "
            "advance."
        )
    return f"{next_owner} must resolve the recorded candidate consume outcome."


def _route_handoff_required_followthrough(
    *,
    handoff_status: str,
    route_command_kind: str,
    next_owner: str,
) -> str:
    if handoff_status == "ready_for_opl_route_command":
        return (
            f"{next_owner} should hand this `{route_command_kind}` command to OPL "
            "DomainProgressTransitionRuntime and then require OPL outbox/event/"
            "StageRun readback before runtime progress is claimed."
        )
    if handoff_status == "not_actionable_without_materialized_transaction":
        return (
            "Repackage the candidate with a materialized PaperMissionTransaction; "
            "placeholder no-write transactions cannot drive OPL routing."
        )
    if handoff_status == "waiting_for_typed_blocker_authority":
        return (
            f"{next_owner} must produce or reject the typed blocker authority file; "
            "OPL must not infer it from this handoff record."
        )
    if handoff_status == "waiting_for_human_gate_authority":
        return (
            f"{next_owner} must produce the human gate question/receipt authority; "
            "OPL must wait for that interrupt rather than guessing."
        )
    return f"{next_owner} must resolve `{handoff_status}` before mission progress is claimed."


def _next_owner(
    authority_consume_readback: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
) -> str:
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    return (
        _text(decision.get("next_owner"))
        or _text(_mapping(authority_consume_readback.get("typed_blocker_required")).get("next_owner"))
        or _text(_mapping(authority_consume_readback.get("human_gate_required")).get("next_owner"))
        or _text(_mapping(authority_consume_readback.get("route_back")).get("next_owner"))
        or _text(authority_consume_readback.get("next_owner"))
        or "mas_authority_kernel"
    )


def _transaction_materialized(transaction_readback: Mapping[str, Any]) -> bool:
    return _text(transaction_readback.get("transaction_state")) != "not_materialized"


def _transaction_id(transaction_readback: Mapping[str, Any]) -> str | None:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    return _text(transaction.get("transaction_id"))


def _stage_terminal_decision_ref(transaction_readback: Mapping[str, Any]) -> str | None:
    transaction_id = _transaction_id(transaction_readback)
    return f"{transaction_id}#stage_terminal_decision" if transaction_id else None


def _opl_route_command_ref(transaction_readback: Mapping[str, Any]) -> str | None:
    transaction_id = _transaction_id(transaction_readback)
    return f"{transaction_id}#opl_route_command" if transaction_id else None


def _no_authority_boundary(*, surface_role: str) -> dict[str, bool | str]:
    return {
        "surface_role": surface_role,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_write_owner_receipt": False,
        "can_write_typed_blocker": False,
        "can_write_human_gate": False,
        "can_write_current_package": False,
        "can_write_paper_body": False,
        "can_write_runtime_queue_or_provider_attempt": False,
        "can_write_opl_outbox": False,
        "can_write_opl_event": False,
        "can_write_opl_stage_run": False,
        "can_authorize_publication_ready": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_provider_admission": False,
        "can_claim_runtime_ready": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "opl_route_command_packet",
    "opl_route_handoff_record",
    "paper_mission_consumption_ledger_readback",
    "paper_mission_consumption_record",
    "stage_terminal_decision_packet",
    "write_paper_mission_consumption_ledger_outputs",
]
