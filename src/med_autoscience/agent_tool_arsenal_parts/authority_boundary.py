from __future__ import annotations

from typing import Any, Mapping


def non_read_only_gate(
    *,
    requires_human_gate: bool,
    requires_owner_receipt_or_typed_blocker: bool = True,
) -> dict[str, Any]:
    return {
        "surface_kind": "mas_agent_tool_non_read_only_gate",
        "gate_policy": "current_owner_delta_or_human_gate_with_owner_receipt_typed_blocker_proof",
        "requires_current_owner_delta": True,
        "requires_current_owner_delta_match": True,
        "requires_human_gate_or_owner_delta": True,
        "requires_human_gate": requires_human_gate,
        "requires_owner_receipt_or_typed_blocker_proof": requires_owner_receipt_or_typed_blocker,
        "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
        "can_substitute_owner_receipt": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_provider_admission": False,
        "can_start_worker_attempt": False,
    }


def non_read_only_authority_boundary_fields(gate: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "owner_receipt_or_typed_blocker_proof_replaces_publication_quality": False,
        "can_substitute_owner_receipt": False,
        "can_authorize_provider_admission": False,
        "can_start_worker_attempt": False,
        "non_read_only_gate_policy": _text(gate.get("gate_policy")),
    }


def admission_gate_false_boundary_fields() -> dict[str, bool]:
    return {
        "capability_or_sidecar_can_be_admission_gate": False,
        "missing_capability_blocks_owner_action": False,
        "failed_capability_blocks_owner_action": False,
        "low_confidence_capability_blocks_owner_action": False,
        "sidecar_completion_required_for_stage_closeout": False,
    }


def attach_non_read_only_invocation_gate_fields(card: dict[str, Any]) -> None:
    gate = _mapping(card.get("non_read_only_gate"))
    if not gate:
        return
    invocation_gate = dict(_mapping(card.get("invocation_gate")))
    invocation_gate["non_read_only_gate_policy"] = _text(gate.get("gate_policy"))
    invocation_gate["owner_receipt_or_typed_blocker_required"] = bool(
        gate.get("requires_owner_receipt_or_typed_blocker_proof")
    )
    card["invocation_gate"] = invocation_gate


def executor_receipt_ref_policy() -> dict[str, Any]:
    return {
        "field": "executor_receipt_ref",
        "required": False,
        "receipt_only": True,
        "can_block_current_owner_action": False,
    }


def _mapping(value: object) -> Mapping[str, Any]:
    return value if isinstance(value, Mapping) else {}


def _text(value: object) -> str:
    return str(value or "").strip()


__all__ = [
    "admission_gate_false_boundary_fields",
    "attach_non_read_only_invocation_gate_fields",
    "executor_receipt_ref_policy",
    "non_read_only_authority_boundary_fields",
    "non_read_only_gate",
]
