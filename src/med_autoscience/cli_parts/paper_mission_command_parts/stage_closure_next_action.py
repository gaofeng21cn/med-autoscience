from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _compact_mapping,
    _first_text,
    _first_text_item,
    _mapping,
    _optional_text,
    _text_list,
)
from med_autoscience.controllers.next_action_envelope import compile_next_action_envelope
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback,
    terminal_owner_gate_next_decision,
)


def merge_stage_closure_typed_blocker_gate_fields(
    *,
    transaction_output_fields: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    gate = terminal_owner_gate_from_stage_closure_decision(
        stage_closure_decision=stage_closure_decision,
        next_action=next_action,
    )
    if not gate:
        return dict(transaction_output_fields)
    merged = dict(transaction_output_fields)
    merged["terminal_owner_gate"] = gate
    authority_readback = terminal_owner_gate_authority_readback(gate)
    merged["terminal_owner_gate_authority_readback"] = authority_readback or None
    merged["next_owner_or_human_decision"] = terminal_owner_gate_next_decision(gate)
    readback = _mapping(merged.get("paper_mission_transaction_readback"))
    if readback:
        merged["paper_mission_transaction_readback"] = {
            **readback,
            "terminal_owner_gate": gate,
            "terminal_owner_gate_authority_readback": authority_readback or None,
            "next_owner_or_human_decision": merged["next_owner_or_human_decision"],
        }
    return merged


def terminal_owner_gate_from_stage_closure_decision(
    *,
    stage_closure_decision: Mapping[str, Any],
    next_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    if outcome.get("kind") != "typed_blocker":
        return {}
    action = _mapping(next_action)
    typed_blocker_ref = _first_text(
        outcome.get("typed_blocker_ref"),
        outcome.get("typed_blocker_evidence_ref"),
        decision.get("decision_ref"),
        action.get("outcome_ref"),
    )
    return _compact_mapping(
        {
            "surface_kind": "paper_mission_terminal_owner_gate",
            "owner": "mas_authority_kernel",
            "gate_kind": "typed_blocker",
            "blocked_reason": _first_text(
                outcome.get("blocker_id"),
                outcome.get("reason"),
                "typed_blocker",
            ),
            "typed_blocker_ref": typed_blocker_ref,
            "closeout_ref": _first_text(decision.get("decision_ref"), action.get("outcome_ref")),
            "stage_attempt_id": _first_text(
                outcome.get("stage_attempt_id"),
                decision.get("stage_attempt_id"),
            ),
            "work_unit_id": _first_text(
                outcome.get("work_unit_id"),
                decision.get("work_unit_id"),
                action.get("work_unit_id"),
            ),
            "can_claim_paper_progress": False,
            "can_claim_runtime_ready": False,
            "authority_materialized": False,
            "legal_next_action": "route_to_owner_or_human_gate",
        }
    )


def next_action_for_stage_closure_decision(
    *,
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    typed_blocker_resolution_readback: Mapping[str, Any] | None = None,
    receipt_owner_consumption_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any] | None:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    resolution = _mapping(typed_blocker_resolution_readback)
    stage_closure_transition = (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind")
        in {"route_back_candidate_checkpoint", "current_package_mirror_sync"}
    )
    if resolution and not stage_closure_transition:
        action = _mapping(resolution.get("next_owner_action"))
        if action:
            source_ref = _first_text(resolution.get("source_ref"), resolution.get("decision_ref"))
            action_type = _first_text(
                action.get("action_type"),
                action.get("next_action"),
                _first_text_item(action.get("allowed_actions")),
            )
            return compile_next_action_envelope(
                stage_outcome={
                    "kind": "next_stage_transition",
                    "study_id": _first_text(decision.get("study_id"), action.get("study_id")),
                    "stage_id": _first_text(
                        decision.get("stage_id"),
                        "submission_milestone_candidate",
                    ),
                    "work_unit_id": action.get("work_unit_id"),
                    "work_unit_fingerprint": action.get("work_unit_fingerprint"),
                    "action_family": "paper.package.submission_minimal",
                    "next_action": action_type,
                    "decision_signature": action.get("work_unit_fingerprint"),
                    "required_input_refs": action.get("acceptance_refs"),
                },
                study_id=_first_text(decision.get("study_id"), action.get("study_id")),
                stage_id=_first_text(
                    decision.get("stage_id"),
                    "submission_milestone_candidate",
                ),
                outcome_ref=source_ref,
                owner_route={
                    "next_owner": action.get("next_owner") or "mas_authority_kernel",
                    "allowed_actions": action.get("allowed_actions"),
                    "action_type": action_type,
                    "idempotency_key": action.get("work_unit_fingerprint"),
                    "action_family": "paper.package.submission_minimal",
                    "paper_facing_delta": action.get("paper_facing_delta"),
                    "accepted_answer_shape": action.get("accepted_answer_shape"),
                    "route_back": action.get("route_back"),
                    "verification": action.get("verification"),
                    "executable_owner_route": action.get("executable_owner_route"),
                },
                authority_boundary={
                    "projection_only": True,
                    "can_claim_stage_complete": False,
                    "can_claim_submission_ready": False,
                    "can_claim_publication_ready": False,
                },
                diagnostic_refs=[
                    {"role": "typed_blocker_resolution", "ref": source_ref}
                ]
                if source_ref is not None
                else [],
            )
    if outcome.get("kind") == "typed_blocker":
        transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
        return compile_next_action_envelope(
            stage_outcome={
                **outcome,
                "study_id": _first_text(decision.get("study_id"), transaction.get("study_id")),
                "stage_id": _first_text(decision.get("stage_id"), transaction.get("stage_id")),
                "work_unit_id": "paper_mission_typed_blocker_resolution",
                "work_unit_fingerprint": _first_text(
                    outcome.get("typed_blocker_evidence_ref"),
                    decision.get("decision_signature"),
                ),
                "stage_closure_decision_ref": decision.get("decision_ref"),
                "action_family": "blocked.typed",
            },
            study_id=_first_text(decision.get("study_id"), transaction.get("study_id")),
            stage_id=_first_text(decision.get("stage_id"), transaction.get("stage_id")),
            outcome_ref=decision.get("decision_ref"),
            owner_route={
                "next_owner": "mas_authority_kernel",
                "allowed_actions": ["materialize_typed_blocker_or_route_redesign"],
                "action_family": "blocked.typed",
            },
            authority_boundary={
                "projection_only": True,
                "can_claim_stage_complete": False,
                "can_claim_submission_ready": False,
                "can_claim_publication_ready": False,
            },
            diagnostic_refs=stage_closure_next_action_diagnostic_refs(
                stage_closure_decision=decision,
                transaction_readback=transaction_readback,
            ),
        )
    if (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "route_back_candidate_checkpoint"
    ):
        if _receipt_owner_consumed_same_route_checkpoint(
            stage_closure_decision=decision,
            receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        ):
            return None
        transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
        action_type = _first_text(
            outcome.get("next_action"),
            "consume_route_back_checkpoint_or_materialize_terminalizer_outcome",
        )
        return compile_next_action_envelope(
            stage_outcome={
                **outcome,
                "study_id": _first_text(decision.get("study_id"), transaction.get("study_id")),
                "stage_id": _first_text(decision.get("stage_id"), transaction.get("stage_id")),
                "work_unit_id": _first_text(
                    decision.get("work_unit_id"),
                    outcome.get("transition_kind"),
                ),
                "work_unit_fingerprint": _first_text(
                    decision.get("work_unit_fingerprint"),
                    decision.get("decision_signature"),
                ),
                "stage_closure_decision_ref": decision.get("decision_ref"),
                "action_family": "paper.stage_closure.owner_consumption",
                "next_action": action_type,
                "required_input_refs": _route_back_checkpoint_input_refs(
                    stage_closure_decision=decision,
                    transaction_readback=transaction_readback,
                ),
            },
            study_id=_first_text(decision.get("study_id"), transaction.get("study_id")),
            stage_id=_first_text(decision.get("stage_id"), transaction.get("stage_id")),
            outcome_ref=decision.get("decision_ref"),
            owner_route={
                "next_owner": _first_text(outcome.get("next_owner"), "MedAutoScience"),
                "allowed_actions": [action_type],
                "action_type": action_type,
                "idempotency_key": _first_text(
                    decision.get("decision_signature"),
                    decision.get("work_unit_fingerprint"),
                ),
                "action_family": "paper.stage_closure.owner_consumption",
                "accepted_answer_shape": "owner_receipt_typed_blocker_human_gate_or_next_stage_transition",
                "route_back": True,
            },
            authority_boundary={
                "projection_only": True,
                "can_claim_stage_complete": False,
                "can_claim_submission_ready": False,
                "can_claim_publication_ready": False,
            },
            diagnostic_refs=stage_closure_next_action_diagnostic_refs(
                stage_closure_decision=decision,
                transaction_readback=transaction_readback,
            ),
        )
    if (
        outcome.get("kind") == "next_stage_transition"
        and outcome.get("transition_kind") == "current_package_mirror_sync"
    ):
        transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
        action_type = _first_text(outcome.get("next_action"), "sync_current_package_mirror")
        return compile_next_action_envelope(
            stage_outcome={
                **outcome,
                "study_id": _first_text(decision.get("study_id"), transaction.get("study_id")),
                "stage_id": _first_text(decision.get("stage_id"), transaction.get("stage_id")),
                "work_unit_id": _first_text(
                    decision.get("work_unit_id"),
                    "submission_delivery_sync_closure",
                ),
                "work_unit_fingerprint": _first_text(
                    decision.get("work_unit_fingerprint"),
                    decision.get("decision_signature"),
                ),
                "stage_closure_decision_ref": decision.get("decision_ref"),
                "action_family": "paper.delivery_sync",
                "next_action": action_type,
                "required_input_refs": _text_list(
                    _mapping(decision.get("semantic_delta")).get("delivery_delta_refs")
                ),
            },
            study_id=_first_text(decision.get("study_id"), transaction.get("study_id")),
            stage_id=_first_text(decision.get("stage_id"), transaction.get("stage_id")),
            outcome_ref=decision.get("decision_ref"),
            owner_route={
                "next_owner": _first_text(outcome.get("next_owner"), "MedAutoScience"),
                "allowed_actions": [action_type],
                "action_type": action_type,
                "idempotency_key": _first_text(
                    decision.get("decision_signature"),
                    decision.get("work_unit_fingerprint"),
                ),
                "action_family": "paper.delivery_sync",
                "accepted_answer_shape": "delivery_sync_receipt_ref",
            },
            authority_boundary={
                "projection_only": True,
                "can_claim_stage_complete": False,
                "can_claim_submission_ready": False,
                "can_claim_publication_ready": False,
            },
            diagnostic_refs=stage_closure_next_action_diagnostic_refs(
                stage_closure_decision=decision,
                transaction_readback=transaction_readback,
            ),
        )
    if outcome.get("kind") != "owner_receipt":
        return None
    if outcome.get("package_kind") != "submission_ready_package":
        return None
    if outcome.get("can_submit") is not True:
        return None
    if _text_list(outcome.get("known_blockers")) or _text_list(
        decision.get("known_blockers")
    ):
        return None
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    return compile_next_action_envelope(
        stage_outcome={
            **outcome,
            "study_id": decision.get("study_id"),
            "stage_id": decision.get("stage_id"),
            "work_unit_id": decision.get("work_unit_id"),
            "work_unit_fingerprint": decision.get("work_unit_fingerprint"),
            "stage_closure_decision_ref": decision.get("decision_ref"),
            "decision_signature": decision.get("decision_signature"),
            "required_input_refs": [
                ref
                for ref in _text_list(
                    _mapping(decision.get("semantic_delta")).get("delivery_delta_refs")
                )
            ],
        },
        study_id=_first_text(decision.get("study_id"), transaction.get("study_id")),
        stage_id=_first_text(decision.get("stage_id"), transaction.get("stage_id")),
        outcome_ref=decision.get("decision_ref"),
        authority_boundary={
            "projection_only": True,
            "can_claim_stage_complete": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
        },
        diagnostic_refs=stage_closure_next_action_diagnostic_refs(
            stage_closure_decision=decision,
            transaction_readback=transaction_readback,
        ),
    )


def stage_closure_next_action_diagnostic_refs(
    *,
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for role, ref in (
        ("stage_closure_decision", stage_closure_decision.get("decision_ref")),
        (
            "paper_mission_transaction",
            _mapping(transaction_readback.get("paper_mission_transaction")).get(
                "transaction_id"
            ),
        ),
    ):
        text = _optional_text(ref)
        if text is not None:
            refs.append({"role": role, "ref": text})
    for ref in _text_list(
        _mapping(stage_closure_decision.get("semantic_delta")).get("delivery_delta_refs")
    ):
        refs.append({"role": "delivery_delta_ref", "ref": ref})
    return refs


def _route_back_checkpoint_input_refs(
    *,
    stage_closure_decision: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for item in stage_closure_next_action_diagnostic_refs(
        stage_closure_decision=stage_closure_decision,
        transaction_readback=transaction_readback,
    ):
        ref = _optional_text(item.get("ref"))
        if ref is not None:
            refs.append(ref)
    decision = _mapping(stage_closure_decision)
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    terminal = _mapping(transaction.get("stage_terminal_decision"))
    for ref in (
        terminal.get("route_back_evidence_ref"),
        _mapping(transaction_readback.get("stage_terminal_decision")).get(
            "route_back_evidence_ref"
        ),
    ):
        text = _optional_text(ref)
        if text is not None and text not in refs:
            refs.append(text)
    return refs


def _receipt_owner_consumed_same_route_checkpoint(
    *,
    stage_closure_decision: Mapping[str, Any],
    receipt_owner_consumption_readback: Mapping[str, Any] | None,
) -> bool:
    receipt = _mapping(receipt_owner_consumption_readback)
    if _optional_text(receipt.get("status")) != "owner_consumption_applied":
        return False
    consumption = _mapping(receipt.get("mas_receipt_consumption"))
    if _optional_text(consumption.get("status")) != "owner_consumed_route_checkpoint":
        return False
    receipt_decision = _mapping(receipt.get("stage_closure_decision"))
    if not receipt_decision:
        return False
    return _route_checkpoint_decisions_match(stage_closure_decision, receipt_decision)


def _route_checkpoint_decisions_match(
    left: Mapping[str, Any],
    right: Mapping[str, Any],
) -> bool:
    left_outcome = _mapping(left.get("outcome"))
    right_outcome = _mapping(right.get("outcome"))
    for outcome in (left_outcome, right_outcome):
        if (
            _optional_text(outcome.get("kind")) != "next_stage_transition"
            or _optional_text(outcome.get("transition_kind"))
            != "route_back_candidate_checkpoint"
        ):
            return False
    matched = False
    for key in ("stage_id", "work_unit_id"):
        left_value = _optional_text(left.get(key))
        right_value = _optional_text(right.get(key))
        if left_value is None or right_value is None:
            continue
        if left_value != right_value:
            return False
        matched = True
    for key in ("route_checkpoint_evidence_ref", "receipt_evidence_ref"):
        left_value = _first_text(left.get(key), left_outcome.get(key))
        right_value = _first_text(right.get(key), right_outcome.get(key))
        if left_value is None or right_value is None:
            continue
        if left_value != right_value:
            return False
        matched = True
    left_closeout = _optional_text(
        _mapping(left.get("opl_closeout")).get("stage_attempt_id")
    )
    right_closeout = _optional_text(
        _mapping(right.get("opl_closeout")).get("stage_attempt_id")
    )
    if left_closeout is not None and right_closeout is not None:
        if left_closeout != right_closeout:
            return False
        matched = True
    return matched


__all__ = [
    "merge_stage_closure_typed_blocker_gate_fields",
    "next_action_for_stage_closure_decision",
    "stage_closure_next_action_diagnostic_refs",
    "terminal_owner_gate_from_stage_closure_decision",
]
