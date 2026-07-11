from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _compact_non_null_mapping,
    _first_text,
    _load_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
    _paper_mission_sorted_mapping,
    _stable_sha256,
)

PAPER_MISSION_ROUTE_BACK_BUDGET_LEDGER_FILENAME = "route_back_budget_ledger.json"
PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS = 2
NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS = (
    "owner_decision_packet",
    "human_gate_question",
    "paper_facing_delta",
    "typed_blocker_materialization",
)


def _paper_mission_mas_owned_executor_stage_packet(
    *,
    signature: str,
    signature_payload: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_mas_owned_executor_stage_packet",
        "schema_version": 1,
        "stage_type": "paper_mission_semantic_progress_executor",
        "owner": "MedAutoScience",
        "executor": "Codex CLI",
        "trigger": "non_advancing_route_back",
        "semantic_progress_signature": signature,
        "semantic_progress_signature_payload": signature_payload,
        "required_outputs": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
        "next_legal_action": "materialize_mas_owned_executor_delta_before_redrive",
        "forbidden_next_action": "synonymous_route_back_redrive",
        "authority_boundary": {
            "writes_authority": False,
            "writes_runtime": False,
            "writes_yang_authority": False,
            "writes_paper_body": False,
            "can_claim_paper_progress": False,
            "can_claim_submission_ready": False,
            "can_claim_publication_ready": False,
            "can_claim_runtime_ready": False,
        },
    }


def _paper_mission_route_back_budget_ledger_path(
    *,
    ledger_root: Path,
    study_id: str,
) -> Path:
    resolved_ledger_root = ledger_root.expanduser().resolve()
    return (
        resolved_ledger_root.parent
        / "_route_back_budget"
        / study_id
        / PAPER_MISSION_ROUTE_BACK_BUDGET_LEDGER_FILENAME
    )


def _load_paper_mission_route_back_budget_ledger(
    *,
    ledger_ref: Path,
    study_id: str,
) -> dict[str, Any]:
    if not ledger_ref.exists():
        return _empty_paper_mission_route_back_budget_ledger(study_id=study_id)
    payload = _load_json_object(ledger_ref)
    if (
        payload.get("surface_kind")
        != "paper_mission_route_back_budget_ledger"
        or _optional_text(payload.get("study_id")) != study_id
    ):
        return _empty_paper_mission_route_back_budget_ledger(study_id=study_id)
    signatures = _mapping(payload.get("signatures"))
    return {
        "surface_kind": "paper_mission_route_back_budget_ledger",
        "schema_version": 1,
        "study_id": study_id,
        "budget_kind": "synonymous_route_back_cross_run_budget",
        "max_opl_redrives": PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS,
        "signatures": signatures,
        "authority_boundary": _paper_mission_route_back_budget_authority_boundary(),
    }


def _empty_paper_mission_route_back_budget_ledger(*, study_id: str) -> dict[str, Any]:
    return {
        "surface_kind": "paper_mission_route_back_budget_ledger",
        "schema_version": 1,
        "study_id": study_id,
        "budget_kind": "synonymous_route_back_cross_run_budget",
        "max_opl_redrives": PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS,
        "signatures": {},
        "authority_boundary": _paper_mission_route_back_budget_authority_boundary(),
    }


def _paper_mission_route_back_budget_authority_boundary() -> dict[str, Any]:
    return {
        "ledger_is_authority": False,
        "counts_as_paper_progress": False,
        "counts_as_runtime_truth": False,
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "writes_paper_body": False,
        "writes_owner_receipt": False,
        "writes_typed_blocker": False,
        "writes_human_gate": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "can_claim_runtime_ready": False,
    }


def _paper_mission_route_back_budget_status(
    *,
    signature: str,
    signature_payload: Mapping[str, Any],
    ledger: Mapping[str, Any] | None,
    has_required_delta: bool,
) -> dict[str, Any]:
    eligible_route_back = _paper_mission_signature_is_route_back_to_mission_executor(
        signature_payload
    )
    entry = _mapping(_mapping(ledger).get("signatures")).get(signature)
    observed_count = int(entry.get("observed_count") or 0) if entry else 0
    next_observed_count = (
        observed_count + 1
        if eligible_route_back and not has_required_delta
        else observed_count
    )
    budget_exhausted = (
        eligible_route_back
        and not has_required_delta
        and next_observed_count
        >= PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS
    )
    next_mode = (
        "mas_mission_executor_fallback"
        if budget_exhausted
        else "opl_targeted_redrive_allowed"
    )
    return {
        "surface_kind": "paper_mission_route_back_budget_status",
        "schema_version": 1,
        "budget_kind": "synonymous_route_back_cross_run_budget",
        "signature": signature,
        "signature_payload": dict(signature_payload),
        "eligible_route_back": eligible_route_back,
        "previous_observed_count": observed_count,
        "next_observed_count": next_observed_count,
        "max_opl_redrives": PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS,
        "opl_redrive_budget_remaining": max(
            PAPER_MISSION_ROUTE_BACK_BUDGET_MAX_OPL_REDIRECTS
            - next_observed_count,
            0,
        ),
        "budget_exhausted": budget_exhausted,
        "next_mode": next_mode,
        "required_next_owner": (
            "mission_executor" if budget_exhausted else "one-person-lab"
        ),
        "stop_same_semantic_redrive": budget_exhausted,
        "authority_boundary": _paper_mission_route_back_budget_authority_boundary(),
    }


def _paper_mission_signature_is_route_back_to_mission_executor(
    signature_payload: Mapping[str, Any],
) -> bool:
    route_back_identity = _mapping(signature_payload.get("route_back_identity"))
    return (
        _optional_text(route_back_identity.get("decision_kind")) == "route_back"
        and _optional_text(route_back_identity.get("next_owner")) == "mission_executor"
    )


def _record_paper_mission_route_back_budget_ledger(
    *,
    ledger: Mapping[str, Any],
    ledger_ref: Path,
    progress_guard: Mapping[str, Any],
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    trigger: str,
    source: str,
) -> dict[str, Any]:
    budget = _mapping(progress_guard.get("route_back_budget"))
    signature = _optional_text(progress_guard.get("signature"))
    if (
        signature is None
        or not budget
        or budget.get("eligible_route_back") is not True
    ):
        return dict(ledger)
    updated = dict(ledger)
    signatures = dict(_mapping(updated.get("signatures")))
    previous = _mapping(signatures.get(signature))
    observed_count = int(budget.get("next_observed_count") or 0)
    signatures[signature] = {
        "signature": signature,
        "signature_payload": _mapping(progress_guard.get("signature_payload")),
        "observed_count": observed_count,
        "budget_exhausted": budget.get("budget_exhausted") is True,
        "next_mode": _optional_text(budget.get("next_mode")),
        "last_trigger": trigger,
        "last_source": source,
        "last_candidate_ref": _first_text(
            consume_readback.get("candidate_ref"),
            handoff.get("candidate_ref"),
        ),
        "last_paper_mission_transaction_ref": _first_text(
            handoff.get("paper_mission_transaction_ref"),
            _mapping(consume_readback.get("paper_mission_transaction")).get(
                "transaction_id"
            ),
        ),
        "first_observed_count": int(previous.get("first_observed_count") or 1),
    }
    updated.update(
        {
            "signatures": signatures,
            "signature_count": len(signatures),
            "latest_signature": signature,
            "latest_budget_status": dict(budget),
        }
    )
    ledger_ref.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(updated, ensure_ascii=False, indent=2) + "\n"
    ledger_ref.write_text(text, encoding="utf-8")
    updated["source_ref"] = str(ledger_ref)
    updated["file_sha256"] = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return updated


def _paper_mission_route_back_budget_exhausted(
    progress_guard: Mapping[str, Any],
) -> bool:
    return _mapping(progress_guard.get("route_back_budget")).get(
        "budget_exhausted"
    ) is True


def _paper_mission_semantic_progress_signature_payload(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(consume_readback.get("paper_mission_transaction"))
    decision = _mapping(consume_readback.get("stage_terminal_decision"))
    route = _mapping(consume_readback.get("opl_route_command"))
    next_decision = _mapping(consume_readback.get("next_owner_or_human_decision"))
    terminal_gate = _mapping(consume_readback.get("terminal_owner_gate"))
    owner_answer = _mapping(
        consume_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    owner_answer_decision = _mapping(owner_answer.get("stage_terminal_decision"))
    progress_refs = _paper_mission_progress_refs(
        consume_readback=consume_readback,
        handoff=handoff,
        transaction=transaction,
        owner_answer=owner_answer,
    )
    return {
        "study_id": _first_text(
            consume_readback.get("study_id"),
            handoff.get("study_id"),
            transaction.get("study_id"),
        ),
        "mission_id": _paper_mission_canonical_followthrough_identity(
            _first_text(
                consume_readback.get("mission_id"),
                handoff.get("mission_id"),
                transaction.get("mission_id"),
            )
        ),
        "transaction_identity": {
            "paper_mission_transaction_ref": _paper_mission_canonical_followthrough_identity(
                _first_text(
                    handoff.get("paper_mission_transaction_ref"),
                    route.get("paper_mission_transaction_ref"),
                    transaction.get("transaction_id"),
                )
            ),
            "stage_id": _first_text(
                transaction.get("stage_id"),
                decision.get("target_stage_id"),
                decision.get("next_stage_id"),
            ),
            "stage_run_ref": _optional_text(transaction.get("stage_run_ref")),
        },
        "route_back_identity": {
            "decision_kind": _first_text(
                owner_answer_decision.get("decision_kind"),
                decision.get("decision_kind"),
            ),
            "decision_status": _first_text(
                owner_answer_decision.get("status"),
                decision.get("status"),
            ),
            "next_owner": _first_text(
                owner_answer_decision.get("next_owner"),
                decision.get("next_owner"),
                next_decision.get("next_owner"),
                handoff.get("next_owner"),
            ),
            "route_command": _first_text(
                handoff.get("route_command_kind"),
                route.get("command_kind"),
            ),
            "route_target": _first_text(
                handoff.get("route_target"),
                route.get("target"),
                decision.get("target_stage_id"),
                decision.get("next_stage_id"),
            ),
            "repair_scope": _first_text(
                owner_answer_decision.get("repair_scope"),
                decision.get("repair_scope"),
                decision.get("next_work_unit"),
            ),
            "route_back_evidence_kind": _route_back_evidence_kind(
                _first_text(
                    owner_answer_decision.get("route_back_evidence_ref"),
                    decision.get("route_back_evidence_ref"),
                )
            ),
        },
        "domain_gate_identity": {
            "gate_owner": _optional_text(terminal_gate.get("owner")),
            "gate_kind": _optional_text(terminal_gate.get("gate_kind")),
            "blocked_reason": _first_text(
                terminal_gate.get("blocked_reason"),
                terminal_gate.get("reason"),
                owner_answer.get("blocked_reason"),
            ),
            "owner_answer_shape": _optional_text(owner_answer.get("owner_answer_shape")),
            "owner_answer_status": _optional_text(owner_answer.get("status")),
        },
        "semantic_delta_refs": _paper_mission_semantic_delta_refs(progress_refs),
    }


def _paper_mission_progress_refs_for_guard(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    transaction = _mapping(consume_readback.get("paper_mission_transaction"))
    owner_answer = _mapping(
        consume_readback.get("terminal_owner_gate_owner_answer_readback")
    )
    return _paper_mission_progress_refs(
        consume_readback=consume_readback,
        handoff=handoff,
        transaction=transaction,
        owner_answer=owner_answer,
    )


def _paper_mission_progress_refs(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
    transaction: Mapping[str, Any],
    owner_answer: Mapping[str, Any],
) -> dict[str, Any]:
    authority_readback = _mapping(consume_readback.get("authority_consume_readback"))
    consume_result = _mapping(authority_readback.get("consume_result"))
    return {
        "accepted_owner_receipt_ref": _first_text(
            consume_result.get("domain_owner_receipt_ref"),
            consume_result.get("quality_gate_receipt_ref"),
            owner_answer.get("domain_owner_receipt_ref"),
            owner_answer.get("quality_gate_receipt_ref"),
        ),
        "typed_blocker_ref": _first_text(
            consume_result.get("typed_blocker_ref"),
            owner_answer.get("typed_blocker_ref"),
        ),
        "human_gate_ref": _first_text(
            consume_result.get("human_gate_ref"),
            owner_answer.get("human_gate_ref"),
        ),
        "route_back_evidence_ref": _first_text(
            consume_result.get("route_back_evidence_ref"),
            owner_answer.get("route_back_evidence_ref"),
            _mapping(owner_answer.get("stage_terminal_decision")).get(
                "route_back_evidence_ref"
            ),
            _mapping(transaction.get("stage_terminal_decision")).get(
                "route_back_evidence_ref"
            ),
        ),
        "paper_facing_delta_ref": _first_text(
            consume_result.get("paper_facing_delta_ref"),
            owner_answer.get("paper_facing_delta_ref"),
        ),
        "owner_decision_packet_ref": _first_text(
            consume_result.get("owner_decision_packet_ref"),
            owner_answer.get("owner_decision_packet_ref"),
        ),
        "successor_work_unit_ref": _first_text(
            consume_result.get("successor_work_unit_ref"),
            owner_answer.get("successor_work_unit_ref"),
            _mapping(owner_answer.get("stage_terminal_decision")).get(
                "successor_work_unit_ref"
            ),
            _mapping(transaction.get("stage_terminal_decision")).get(
                "successor_work_unit_ref"
            ),
        ),
        "carry_forward_risk_receipt_ref": _first_text(
            consume_result.get("carry_forward_risk_receipt_ref"),
            owner_answer.get("carry_forward_risk_receipt_ref"),
            _mapping(owner_answer.get("stage_terminal_decision")).get(
                "carry_forward_risk_receipt_ref"
            ),
            _mapping(transaction.get("stage_terminal_decision")).get(
                "carry_forward_risk_receipt_ref"
            ),
        ),
        "canonical_paper_or_artifact_delta_ref": _first_text(
            consume_result.get("canonical_paper_or_artifact_delta_ref"),
            owner_answer.get("canonical_paper_or_artifact_delta_ref"),
            consume_result.get("canonical_artifact_delta_ref"),
            owner_answer.get("canonical_artifact_delta_ref"),
        ),
        "ai_reviewer_or_publication_gate_delta_ref": _first_text(
            consume_result.get("ai_reviewer_or_publication_gate_delta_ref"),
            owner_answer.get("ai_reviewer_or_publication_gate_delta_ref"),
            consume_result.get("ai_reviewer_delta_ref"),
            owner_answer.get("ai_reviewer_delta_ref"),
            consume_result.get("publication_gate_delta_ref"),
            owner_answer.get("publication_gate_delta_ref"),
        ),
        "artifact_delta_refs": _paper_mission_artifact_delta_ref_ids(transaction),
        "paper_audit_pack_refs": _paper_mission_sorted_mapping(
            _mapping(transaction.get("paper_audit_pack_refs"))
        ),
    }


def _paper_mission_semantic_delta_refs(
    progress_refs: Mapping[str, Any],
) -> dict[str, Any]:
    return _compact_non_null_mapping(
        {
            "accepted_owner_receipt_ref": progress_refs.get("accepted_owner_receipt_ref"),
            "typed_blocker_ref": progress_refs.get("typed_blocker_ref"),
            "human_gate_ref": progress_refs.get("human_gate_ref"),
            "successor_work_unit_ref": progress_refs.get("successor_work_unit_ref"),
            "carry_forward_risk_receipt_ref": progress_refs.get(
                "carry_forward_risk_receipt_ref"
            ),
            "canonical_paper_or_artifact_delta_ref": progress_refs.get(
                "canonical_paper_or_artifact_delta_ref"
            ),
            "ai_reviewer_or_publication_gate_delta_ref": progress_refs.get(
                "ai_reviewer_or_publication_gate_delta_ref"
            ),
        }
    )


def _paper_mission_canonical_followthrough_identity(value: str | None) -> str | None:
    if value is None:
        return None
    marker = "::followthrough"
    index = value.find(marker)
    if index < 0:
        return value
    return value[:index]


def _paper_mission_compact_followthrough_identity(value: str | None) -> str | None:
    if value is None:
        return None
    marker = "::followthrough"
    index = value.find(marker)
    if index < 0:
        return value
    return f"{value[:index]}{marker}"


def _canonicalize_followthrough_transaction_identity(
    transaction: Mapping[str, Any],
) -> dict[str, Any]:
    payload = dict(_mapping(transaction))
    mission_id = _paper_mission_canonical_followthrough_identity(
        _optional_text(payload.get("mission_id"))
    )
    if mission_id is not None:
        payload["mission_id"] = mission_id
    transaction_id = _paper_mission_compact_followthrough_identity(
        _optional_text(payload.get("transaction_id"))
    )
    if transaction_id is not None:
        payload["transaction_id"] = transaction_id
    route = dict(_mapping(payload.get("opl_route_command")))
    if route and transaction_id is not None:
        decision = _mapping(payload.get("stage_terminal_decision"))
        if (
            _optional_text(decision.get("decision_kind")) == "route_back"
            and (target_stage_id := _optional_text(decision.get("target_stage_id")))
            is not None
        ):
            route["target"] = target_stage_id
        route["source_terminal_decision_ref"] = f"{transaction_id}#stage_terminal_decision"
        payload["opl_route_command"] = route
    return payload


def _route_back_evidence_kind(ref: str | None) -> str | None:
    if ref is None:
        return None
    if ref.startswith("route-back:"):
        parts = ref.split(":")
        return ":".join(parts[:3]) if len(parts) >= 3 else ref
    return ref


def _paper_mission_required_executor_delta_present(
    *,
    consume_readback: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    signature_payload = _paper_mission_semantic_progress_signature_payload(
        consume_readback=consume_readback,
        handoff=handoff,
    )
    progress_refs = _mapping(signature_payload.get("semantic_delta_refs"))
    return any(
        progress_refs.get(key)
        for key in (
            "accepted_owner_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "successor_work_unit_ref",
            "carry_forward_risk_receipt_ref",
            "canonical_paper_or_artifact_delta_ref",
            "ai_reviewer_or_publication_gate_delta_ref",
        )
    )


def _paper_mission_route_request_progress_guard(
    *,
    handoff: Mapping[str, Any],
) -> dict[str, Any]:
    route = _mapping(handoff.get("opl_route_command"))
    payload = {
        "study_id": _optional_text(handoff.get("study_id")),
        "mission_id": _optional_text(handoff.get("mission_id")),
        "paper_mission_transaction_ref": _optional_text(
            handoff.get("paper_mission_transaction_ref")
        ),
        "candidate_ref": _optional_text(handoff.get("candidate_ref")),
        "route_command": _first_text(
            handoff.get("route_command_kind"),
            route.get("command_kind"),
        ),
        "route_target": _first_text(handoff.get("route_target"), route.get("target")),
        "semantic_progress_guard_kind": "non_advancing_route_back_detection",
    }
    signature = _stable_sha256(payload)
    executor_stage = _paper_mission_mas_owned_executor_stage_packet(
        signature=signature,
        signature_payload=payload,
    )
    return {
        "surface_kind": "opl_route_semantic_progress_guard",
        "schema_version": 1,
        "guard_kind": "non_advancing_route_back_detection",
        "signature": signature,
        "signature_payload": payload,
        "non_advancing_status": "not_evaluated_by_mas_payload_only",
        "required_executor_outputs": list(NON_ADVANCING_ROUTE_BACK_REQUIRED_OUTPUTS),
        "mas_owned_executor_stage": executor_stage,
        "runtime_owner_expected_action": (
            "If OPL observes the same route-back/domain gate transaction without a "
            "new accepted owner answer, human gate, typed blocker, or paper-facing "
            "delta, stop ordinary redrive and return non_advancing_route_back to MAS."
        ),
        "can_claim_paper_progress": False,
    }


def _paper_mission_artifact_delta_ref_ids(
    transaction: Mapping[str, Any],
) -> list[str]:
    refs: list[str] = []
    for item in _mapping_list(transaction.get("artifact_delta_refs")):
        ref = _first_text(item.get("uri"), item.get("ref_id"), item.get("artifact_ref"))
        if ref is not None:
            refs.append(ref)
    return sorted(set(refs))
