from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
)


ACCEPTED_OWNER_ANSWER_SHAPES = (
    "domain_owner_receipt_ref",
    "quality_gate_receipt_ref",
    "paper_facing_delta_ref",
    "typed_blocker_ref",
    "human_gate_ref",
    "route_back_evidence_ref",
)
def terminal_owner_gate_owner_answer_readback(
    *,
    terminal_owner_gate: Mapping[str, Any],
    paper_mission_transaction: Mapping[str, Any],
    artifact_delta_refs: list[Mapping[str, Any]] | tuple[Mapping[str, Any], ...],
    paper_audit_pack_refs: Mapping[str, Any],
) -> dict[str, Any]:
    gate = _mapping(terminal_owner_gate)
    if not gate or _text(gate.get("owner")) != "mas_authority_kernel":
        return {}
    transaction = _mapping(paper_mission_transaction)
    gate_kind = _text(gate.get("gate_kind"))
    blocked_reason = _text(gate.get("blocked_reason")) or "domain_gate_pending"
    if gate_kind != "domain_gate" and not blocked_reason.endswith("_domain_gate_pending"):
        return {}

    study_id = _text(transaction.get("study_id")) or "unknown_study"
    mission_id = _text(transaction.get("mission_id")) or "unknown_mission"
    stage_id = _text(transaction.get("stage_id")) or _text(gate.get("work_unit_id"))
    stage_id = stage_id or "unknown_stage"
    stage_run_ref = _text(transaction.get("stage_run_ref")) or (
        f"opl-stage-run://paper-mission-owner-answer/{study_id}/{stage_id}"
    )
    evidence_ref = _route_back_evidence_ref(
        study_id=study_id,
        mission_id=mission_id,
        stage_id=stage_id,
        blocked_reason=blocked_reason,
        closeout_ref=_text(gate.get("closeout_ref")),
    )
    artifact_refs = [dict(item) for item in artifact_delta_refs]
    paper_facing_delta_ref = (
        None
        if artifact_refs
        else _paper_facing_delta_ref(
            study_id=study_id,
            mission_id=mission_id,
            stage_id=stage_id,
            route_back_evidence_ref=evidence_ref,
        )
    )
    selected_outcome = (
        "paper_facing_delta_ref"
        if paper_facing_delta_ref is not None
        else "route_back_evidence_ref"
    )
    if paper_facing_delta_ref is not None:
        artifact_refs = [
            {
                "ref_id": "paper_facing_delta_ref",
                "ref_kind": "paper_facing_delta_ref",
                "uri": paper_facing_delta_ref,
            }
        ]
    terminal_decision = {
        "decision_kind": "route_back",
        "status": "route_back",
        "reason": blocked_reason,
        "next_owner": "mission_executor",
        "target_stage_id": stage_id,
        "repair_scope": (
            "MAS authority kernel observed a domain gate terminal closeout; "
            "mission executor must revise the paper mission candidate or submit "
            "a concrete owner answer shape before OPL can advance."
        ),
        "route_back_evidence_ref": evidence_ref,
        **(
            {"paper_facing_delta_ref": paper_facing_delta_ref}
            if paper_facing_delta_ref is not None
            else {}
        ),
    }
    carry_forward_ref = _carry_forward_risk_receipt_ref(
        study_id=study_id,
        mission_id=mission_id,
        stage_id=stage_id,
        route_back_evidence_ref=evidence_ref,
    )
    owner_answer_transaction = build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=stage_run_ref,
        terminal_decision=terminal_decision,
        artifact_delta_refs=artifact_refs,
        paper_audit_pack_refs=paper_audit_pack_refs,
        idempotency_basis=f"terminal-owner-gate::{blocked_reason}",
    )
    return {
        "surface_kind": "mas_terminal_owner_gate_owner_answer_readback",
        "schema_version": 1,
        "status": "route_back",
        "selected_outcome": selected_outcome,
        "owner_answer_shape": selected_outcome,
        "accepted_owner_answer_shapes": list(ACCEPTED_OWNER_ANSWER_SHAPES),
        "carry_forward_risk_receipt_ref": carry_forward_ref,
        "route_back_evidence_ref": evidence_ref,
        **(
            {"paper_facing_delta_ref": paper_facing_delta_ref}
            if paper_facing_delta_ref is not None
            else {}
        ),
        "next_owner": "mission_executor",
        "terminal_owner_gate": gate,
        "paper_mission_transaction_ref": _text(transaction.get("transaction_id")),
        "stage_terminal_decision": owner_answer_transaction[
            "stage_terminal_decision"
        ],
        "ai_route_context": owner_answer_transaction["ai_route_context"],
        "paper_mission_transaction": owner_answer_transaction,
        "consume_result": {
            "status": "route_back",
            "outcome": selected_outcome,
            "authority_materialized": False,
            "authority_answer_readback_materialized": True,
            "authority_file_materialized": False,
            "carry_forward_risk_receipt_ref": carry_forward_ref,
        },
        "authority_materialized": False,
        "authority_answer_readback_materialized": True,
        "authority_file_materialized": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "write_plan": {
            "mode": "readback_only_owner_answer_packet",
            "written_files": [],
            "can_write_publication_eval_latest": False,
            "can_write_controller_decisions_latest": False,
            "can_write_owner_receipts": False,
            "can_write_typed_blockers": False,
            "can_write_human_gate_authority_records": False,
            "can_write_current_package": False,
            "can_write_paper_body": False,
            "can_write_runtime_queues_or_provider_attempts": False,
        },
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "authority_answer_surface": selected_outcome,
            "writes_authority_files": False,
            "authority_file_materialized": False,
            "writes_runtime": False,
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "can_authorize_provider_admission": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_write_current_package": False,
            "can_write_runtime_queue_or_provider_attempt": False,
        },
    }


def terminal_owner_gate_authority_consume_readback(
    *,
    terminal_owner_gate_authority_readback: Mapping[str, Any],
    owner_answer_readback: Mapping[str, Any],
) -> dict[str, Any]:
    authority_readback = _mapping(terminal_owner_gate_authority_readback)
    owner_answer = _mapping(owner_answer_readback)
    if not authority_readback:
        return {}
    if not owner_answer:
        return {
            **authority_readback,
            "owner_answer_materialized": False,
        }
    return {
        **authority_readback,
        "status": owner_answer["status"],
        "selected_outcome": owner_answer["selected_outcome"],
        "owner_answer_materialized": True,
        "owner_answer_readback": owner_answer,
        "route_back_evidence_ref": owner_answer.get("route_back_evidence_ref"),
        "paper_facing_delta_ref": owner_answer.get("paper_facing_delta_ref"),
        "carry_forward_risk_receipt_ref": owner_answer.get(
            "carry_forward_risk_receipt_ref"
        ),
        "stage_terminal_decision": owner_answer.get("stage_terminal_decision"),
        "ai_route_context": owner_answer.get("ai_route_context"),
        "consume_result": owner_answer["consume_result"],
        "write_plan": owner_answer["write_plan"],
        "authority_boundary": owner_answer["authority_boundary"],
    }


def terminal_owner_gate_owner_answer_next_decision(
    owner_answer_readback: Mapping[str, Any],
) -> dict[str, Any]:
    owner_answer = _mapping(owner_answer_readback)
    if not owner_answer:
        return {}
    route = _mapping(owner_answer.get("ai_route_context"))
    decision = {
        "kind": "owner_or_route",
        "next_owner": _text(owner_answer.get("next_owner")) or "mission_executor",
        "human_decision_required": False,
        "summary": _text(owner_answer.get("status")) or "route_back",
        "route_back_evidence_ref": owner_answer.get("route_back_evidence_ref"),
        "ai_route_context_ref": route.get("source_terminal_decision_ref"),
        "carry_forward_risk_receipt_ref": owner_answer.get(
            "carry_forward_risk_receipt_ref"
        ),
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    if owner_answer.get("paper_facing_delta_ref") is not None:
        decision["paper_facing_delta_ref"] = owner_answer.get("paper_facing_delta_ref")
    return decision


def _carry_forward_risk_receipt_ref(
    *,
    study_id: str,
    mission_id: str,
    stage_id: str,
    route_back_evidence_ref: str,
) -> str:
    digest = hashlib.sha256(
        json_digest_basis(
            {
                "study_id": study_id,
                "mission_id": mission_id,
                "stage_id": stage_id,
                "route_back_evidence_ref": route_back_evidence_ref,
            }
        ).encode("utf-8")
    ).hexdigest()[:16]
    return f"carry-forward-risk:paper-mission-owner-route:{study_id}:{digest}"


def json_digest_basis(payload: Mapping[str, Any]) -> str:
    import json

    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def _route_back_evidence_ref(
    *,
    study_id: str,
    mission_id: str,
    stage_id: str,
    blocked_reason: str,
    closeout_ref: str | None,
) -> str:
    basis = "::".join(
        [
            study_id,
            mission_id,
            stage_id,
            blocked_reason,
            closeout_ref or "missing-closeout-ref",
        ]
    )
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]
    return f"route-back:paper-mission-terminal-owner-gate:{study_id}:{digest}"


def _paper_facing_delta_ref(
    *,
    study_id: str,
    mission_id: str,
    stage_id: str,
    route_back_evidence_ref: str,
) -> str:
    basis = "::".join([study_id, mission_id, stage_id, route_back_evidence_ref])
    digest = hashlib.sha256(basis.encode("utf-8")).hexdigest()[:16]
    return f"paper-facing-delta:owner-answer:{study_id}:{digest}"


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


__all__ = [
    "ACCEPTED_OWNER_ANSWER_SHAPES",
    "terminal_owner_gate_authority_consume_readback",
    "terminal_owner_gate_owner_answer_next_decision",
    "terminal_owner_gate_owner_answer_readback",
]
