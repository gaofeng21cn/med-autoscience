from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_domain.common import (
    _first_mapping,
    _first_text,
    _mapping,
    _mapping_list,
    _optional_text,
)
from med_autoscience.paper_mission_domain.materialized_readback_context import (
    paper_audit_pack_for_cli_readback as _paper_audit_pack_for_cli_readback,
)
from med_autoscience.controllers.study_interventions import read_intervention_events
from med_autoscience.controllers.study_progress.canonical_owner_action_projection import (
    submission_authority_owner_gate_readback,
)
from med_autoscience.paper_mission_stage_run_context import paper_mission_stage_run_context
from med_autoscience.paper_mission_stage_run_readback.receipt_events import (
    matches_receipt_bundle,
)
from med_autoscience.paper_mission_stage_run_readback import (
    attach_opl_stage_attempt_readback,
    attach_paper_mission_next_action,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_next_decision,
    terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    stage_terminal_next_owner_or_human_decision,
    terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback,
    terminal_owner_gate_from_stage_terminal_decision,
    terminal_owner_gate_next_decision,
)
from med_autoscience.paper_mission_domain.transaction_readback_candidates import (
    _candidate_manifest_transaction,
    _candidate_mission_id_for_readback,
    _placeholder_paper_mission_transaction,
    PAPER_AUDIT_PACK_FAMILIES,
    _transaction_from_materialized_legacy_mission,
)



FORBIDDEN_AUTHORITY_WRITES = (
    "publication_eval/latest.json",
    "controller_decisions/latest.json",
    "owner receipt",
    "typed blocker",
    "human gate",
    "current_package",
    "runtime queue/provider attempts",
    "/Users/gaofeng/workspace/Yang/**",
)
FORBIDDEN_AUTHORITY_CLAIMS = (
    "publication_ready",
    "submission_ready",
    "current_package",
    "owner_receipt_written",
    "typed_blocker_written",
    "human_gate_written",
    "controller_decision_written",
    "publication_eval_written",
    "quality_verdict",
    "artifact_authority",
    "runtime_queue_written",
    "provider_attempt_written",
    "yang_workspace_written",
)
PAPER_MISSION_CONTRACT_VERSION = "paper-mission-run.v1"
def _paper_mission_run_candidate(
    *,
    mission_id: str,
    study_id: str,
    objective: str,
    paper_mission_command: str,
    profile_ref: str | Path,
    study_root: Path,
    candidate_ref: str | None,
    authority_consume_readback: dict[str, Any] | None = None,
    paper_mission_transaction: dict[str, Any] | None = None,
) -> dict[str, Any]:
    source_refs = [
        {"ref_id": "profile", "ref_kind": "profile_ref", "uri": str(profile_ref)},
        {"ref_id": "study_root", "ref_kind": "workspace_path", "uri": str(study_root)},
    ]
    if candidate_ref is not None:
        source_refs.append(
            {"ref_id": "candidate", "ref_kind": "candidate_ref", "uri": candidate_ref}
        )
    consume_result = (
        dict(authority_consume_readback.get("consume_result") or {})
        if authority_consume_readback is not None
        else {"status": "not_consumed"}
    )
    mission_state = _mission_state_for_consume_result(consume_result)
    artifact_delta_status = (
        "candidate_consumed"
        if consume_result.get("status") == "accepted"
        else "planned"
        if consume_result.get("status") == "not_consumed"
        else "candidate_consume_result_recorded"
    )
    transaction = paper_mission_transaction or _placeholder_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        objective=objective,
        paper_mission_command=paper_mission_command,
        study_root=study_root,
        consume_result=consume_result,
    )
    return {
        "schema_version": PAPER_MISSION_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": mission_state,
        "artifact_delta_ledger": [
            {
                "delta_id": f"{paper_mission_command}_no_write_plan",
                "artifact_ref": str(study_root / "paper"),
                "delta_kind": "no_write_plan",
                "status": artifact_delta_status,
            }
        ],
        "source_refs": source_refs,
        "paper_audit_pack": _paper_audit_pack_for_cli_readback(
            study_id=study_id,
            paper_mission_command=paper_mission_command,
            source_refs=source_refs,
            paper_audit_pack_families=PAPER_AUDIT_PACK_FAMILIES,
        ),
        "authority_touchpoints": [
            {
                "touchpoint_id": "publication_eval",
                "owner": "MedAutoScience",
                "surface": "publication_eval/latest.json",
                "status": "not_touched",
            },
            {
                "touchpoint_id": "controller_decisions",
                "owner": "MedAutoScience",
                "surface": "controller_decisions/latest.json",
                "status": "not_touched",
            },
            {
                "touchpoint_id": "runtime_provider_attempts",
                "owner": "one-person-lab",
                "surface": "runtime queue/provider attempts",
                "status": "not_touched",
            },
        ],
        "forbidden_write_guard": {
            "candidate_writes_authority": False,
            "blocked_paths": [
                "publication_eval/latest.json",
                "controller_decisions/latest.json",
                "current_package",
                "runtime queue/provider attempts",
                "/Users/gaofeng/workspace/Yang/**",
            ],
            "forbidden_claims": list(FORBIDDEN_AUTHORITY_CLAIMS),
        },
        "consume_result": consume_result,
        "claim_permissions": {
            "can_claim_artifact_delta": False,
            "can_claim_owner_handoff": True,
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": ["paper_mission_no_write_plan"],
        },
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "ai_route_context": _mapping(transaction.get("ai_route_context")),
        "transaction_state": _transaction_state(transaction),
    }


def _paper_mission_transaction_readback(
    *,
    mission_id: str,
    study_id: str,
    objective: str,
    paper_mission_command: str,
    study_root: Path,
    mission: dict[str, Any] | None,
    candidate: str | Path | None = None,
    authority_consume_readback: dict[str, Any] | None = None,
    transaction_override: dict[str, Any] | None = None,
    transaction_source_override: str | None = None,
    opl_runtime_payload: Mapping[str, Any] | None = None,
    attach_runtime_readback=attach_opl_stage_attempt_readback,
    attach_next_action=attach_paper_mission_next_action,
) -> dict[str, Any]:
    transaction = _first_mapping(
        _mapping(transaction_override),
        _mapping((authority_consume_readback or {}).get("paper_mission_transaction")),
        _mapping((mission or {}).get("paper_mission_transaction")),
        _transaction_from_materialized_legacy_mission(
            mission=mission,
            study_id=study_id,
        ),
        _candidate_manifest_transaction(candidate),
    )
    source = (
        transaction_source_override
        if transaction_override
        else "materialized_paper_mission_run"
        if transaction
        else "placeholder_no_write"
    )
    if not transaction:
        consume_result = (
            _mapping((authority_consume_readback or {}).get("consume_result"))
            or _mapping((mission or {}).get("consume_result"))
            or {"status": "not_consumed"}
        )
        transaction = _placeholder_paper_mission_transaction(
            mission_id=mission_id,
            study_id=study_id,
            objective=objective,
            paper_mission_command=paper_mission_command,
            study_root=study_root,
            consume_result=consume_result,
        )
    elif mission is None and candidate is not None:
        source = "candidate_manifest"

    owner_answer_readback_prefill = (
        _owner_answer_readback_for_route_back_without_artifact_delta(transaction)
        if transaction_source_override != "authority_consume_readback"
        else {}
    )
    if owner_answer_readback_prefill:
        owner_answer_transaction = _mapping(
            owner_answer_readback_prefill.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            transaction = owner_answer_transaction

    readback = {
        "surface_kind": "paper_mission_transaction_pickup_readback",
        "schema_version": 1,
        "contract_ref": "contracts/paper_mission_transaction_contract.json",
        "contract_version": "paper-mission-transaction.v1",
        "source": source,
        "paper_mission_transaction": transaction,
        "stage_terminal_decision": _mapping(transaction.get("stage_terminal_decision")),
        "ai_route_context": _mapping(transaction.get("ai_route_context")),
        "opl_stage_run_context": paper_mission_stage_run_context(transaction),
        "transaction_state": _transaction_state(transaction),
        "writes_authority": False,
        "writes_runtime": False,
        "writes_yang_authority": False,
        "forbidden_authority_writes": list(FORBIDDEN_AUTHORITY_WRITES),
        "validation": _validate_paper_mission_transaction_if_available(transaction),
    }
    readback = attach_runtime_readback(
        readback=readback,
        study_root=study_root,
        opl_runtime_payload=opl_runtime_payload,
    )
    suppress_terminal_owner_gate = (
        _authority_consume_readback_supersedes_terminal_owner_gate(
            authority_consume_readback=authority_consume_readback,
            transaction=transaction,
            readback=readback,
            study_root=study_root,
        )
    )
    if suppress_terminal_owner_gate:
        readback["opl_stage_attempt_readback"] = (
            _runtime_readback_superseded_by_authority_consumption(readback)
        )
        readback["opl_stage_attempt_readback_status"] = "optional_stage_attempt_readback_missing"
    readback = attach_next_action(readback)
    terminal_owner_gate = (
        {}
        if suppress_terminal_owner_gate
        else _terminal_owner_gate_from_transaction_readback(readback)
    )
    readback["terminal_owner_gate"] = terminal_owner_gate or None
    terminal_gate_authority_readback = terminal_owner_gate_authority_readback(
        terminal_owner_gate
    )
    owner_answer_readback = (
        {}
        if suppress_terminal_owner_gate
        else terminal_owner_gate_owner_answer_readback(
            terminal_owner_gate=terminal_owner_gate,
            paper_mission_transaction=transaction,
            artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
            paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
        )
    ) if not owner_answer_readback_prefill else dict(owner_answer_readback_prefill)
    terminal_gate_authority_readback = terminal_owner_gate_authority_consume_readback(
        terminal_owner_gate_authority_readback=terminal_gate_authority_readback,
        owner_answer_readback=owner_answer_readback,
    )
    if owner_answer_readback and transaction_source_override != "authority_consume_readback":
        owner_answer_transaction = _mapping(
            owner_answer_readback.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            readback["source"] = "terminal_owner_gate_owner_answer"
            readback["paper_mission_transaction"] = owner_answer_transaction
            readback["stage_terminal_decision"] = _mapping(
                owner_answer_transaction.get("stage_terminal_decision")
            )
            readback["ai_route_context"] = _mapping(
                owner_answer_transaction.get("ai_route_context")
            )
            readback["opl_stage_run_context"] = paper_mission_stage_run_context(
                owner_answer_transaction
            )
            readback["transaction_state"] = _transaction_state(owner_answer_transaction)
            readback["consume_candidate_status_override"] = "route_back"
            if not _carrier_readback_has_consumable_receipt(
                _mapping(readback.get("opl_stage_attempt_readback")),
                request_carrier=_mapping(readback.get("opl_stage_run_context")),
            ):
                readback = attach_runtime_readback(
                    readback=readback,
                    study_root=study_root,
                    opl_runtime_payload=opl_runtime_payload,
                )
            readback = attach_next_action(readback)
    readback["terminal_owner_gate_authority_readback"] = (
        terminal_gate_authority_readback or None
    )
    readback["terminal_owner_gate_owner_answer_readback"] = (
        owner_answer_readback or None
    )
    owner_answer_next_decision = (
        {}
        if transaction_source_override == "authority_consume_readback"
        else terminal_owner_gate_owner_answer_next_decision(owner_answer_readback)
    )
    readback["next_owner_or_human_decision"] = (
        owner_answer_next_decision
        or _next_owner_or_human_decision_from_transaction_readback(
            readback=readback,
            terminal_owner_gate=terminal_owner_gate,
        )
    )
    owner_answer = _mapping(readback.get("terminal_owner_gate_owner_answer_readback"))
    if owner_answer:
        readback["carry_forward_risk_receipt_ref"] = owner_answer.get(
            "carry_forward_risk_receipt_ref"
        )
    return readback


def _owner_answer_readback_for_route_back_without_artifact_delta(
    transaction: Mapping[str, Any],
) -> dict[str, Any]:
    if _mapping_list(transaction.get("artifact_delta_refs")):
        return {}
    terminal_owner_gate = terminal_owner_gate_from_stage_terminal_decision(
        stage_terminal_decision=_mapping(transaction.get("stage_terminal_decision")),
        paper_mission_transaction=transaction,
    )
    if not terminal_owner_gate:
        return {}
    return terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate=terminal_owner_gate,
        paper_mission_transaction=transaction,
        artifact_delta_refs=[],
        paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
    )


def _authority_consume_readback_supersedes_terminal_owner_gate(
    *,
    authority_consume_readback: Mapping[str, Any] | None,
    transaction: Mapping[str, Any],
    readback: Mapping[str, Any],
    study_root: Path,
) -> bool:
    authority = _mapping(authority_consume_readback)
    if _first_text(
        authority.get("status"),
        authority.get("selected_outcome"),
        authority.get("consume_candidate_status"),
    ) not in {"accepted_candidate", "accepted_submission_milestone_candidate"}:
        return False
    consume_result = _mapping(authority.get("consume_result"))
    supersedes = _first_text(
        consume_result.get("paper_facing_delta_ref"),
        consume_result.get("canonical_paper_or_artifact_delta_ref"),
    ) is not None or bool(_mapping_list(transaction.get("artifact_delta_refs")))
    decision = _mapping(transaction.get("stage_terminal_decision"))
    supersedes = supersedes or (
        _optional_text(decision.get("decision_kind")) == "continue_same_stage"
        and _optional_text(decision.get("status"))
        == "accepted_submission_milestone_candidate"
    )
    if not supersedes:
        return False
    return _authority_acceptance_is_newer_than_terminal_closeout(
        authority_consume_readback=authority,
        readback=readback,
        study_root=study_root,
    )


def _authority_acceptance_is_newer_than_terminal_closeout(
    *,
    authority_consume_readback: Mapping[str, Any],
    readback: Mapping[str, Any],
    study_root: Path,
) -> bool:
    source_ref = _first_text(
        authority_consume_readback.get("source_ref"),
        authority_consume_readback.get("consume_record_ref"),
    )
    if source_ref is None:
        return True
    terminal_closeout = _mapping(
        _mapping(readback.get("opl_stage_attempt_readback")).get("terminal_closeout")
    )
    closeout_ref = _optional_text(terminal_closeout.get("closeout_ref"))
    if closeout_ref is None:
        return False
    source_mtime = _path_mtime(_resolve_workspace_ref(source_ref, study_root=study_root))
    closeout_mtime = _path_mtime(
        _resolve_workspace_ref(closeout_ref, study_root=study_root)
    )
    if source_mtime is None or closeout_mtime is None:
        return False
    return source_mtime >= closeout_mtime


def _runtime_readback_superseded_by_authority_consumption(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    carrier_readback = _mapping(readback.get("opl_stage_attempt_readback"))
    terminal_closeout = _mapping(carrier_readback.get("terminal_closeout"))
    return {
        "surface_kind": "paper_mission_stage_run_context_readback",
        "schema_version": 1,
        "carrier_status": "context_available",
        "runtime_readback_status": "terminal_closeout_superseded",
        "dispatch_status": "ai_route_context_available",
        "domain_ready_verdict": "authority_consumed_candidate_supersedes_terminal_closeout",
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_domain_ready": False,
        "can_claim_provider_running": False,
        "can_claim_paper_progress": False,
        "can_claim_runtime_ready": False,
        "authority_materialized": False,
        "request_carrier_preserved": True,
        "next_stage_may_start": True,
        "route_selection_owner": "codex_cli",
        **(
            {"superseded_terminal_closeout_ref": terminal_closeout["closeout_ref"]}
            if terminal_closeout.get("closeout_ref")
            else {}
        ),
    }


def _resolve_workspace_ref(ref: str, *, study_root: Path) -> Path:
    path = Path(ref)
    if path.is_absolute():
        return path
    if study_root.parent.name == "studies":
        return study_root.parent.parent / path
    return study_root / path


def _path_mtime(path: Path) -> float | None:
    try:
        return path.stat().st_mtime
    except OSError:
        return None


def _mission_state_for_materialized_readback(
    *,
    mission: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
) -> str:
    if transaction_readback.get("consume_candidate_status_override") == "route_back":
        return "route_back"
    return _optional_text(mission.get("mission_state")) or "planned"


def _consume_candidate_status_for_transaction_readback(
    *,
    transaction_readback: Mapping[str, Any],
    authority_consume_readback: Mapping[str, Any] | None,
) -> str:
    authority = _mapping(authority_consume_readback)
    selected = _optional_text(authority.get("selected_outcome"))
    status = _optional_text(authority.get("status"))
    if selected == "accepted_candidate" or status == "accepted_candidate":
        return "accepted_submission_milestone_candidate"
    decision = _mapping(transaction_readback.get("stage_terminal_decision"))
    decision_kind = _optional_text(decision.get("decision_kind"))
    if decision_kind == "route_back":
        return "route_back"
    if decision_kind == "typed_blocker":
        return "typed_blocker"
    if decision_kind == "human_gate":
        return "human_gate"
    if decision_kind == "mission_complete":
        return "mission_complete"
    if decision_kind in {"advance", "continue_same_stage"}:
        return selected or status or "accepted"
    if selected == "typed_blocker_required" or status == "typed_blocker_required":
        return "typed_blocker"
    if selected == "human_gate_required" or status == "human_gate_required":
        return "human_gate"
    if selected == "rejected_candidate" or status == "rejected_candidate":
        return "rejected"
    return selected or status or "not_consumed"


def _transaction_readback_output_fields(
    transaction_readback: dict[str, Any],
) -> dict[str, Any]:
    return {
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        "stage_terminal_decision": transaction_readback["stage_terminal_decision"],
        "ai_route_context": transaction_readback["ai_route_context"],
        "opl_stage_run_context": transaction_readback["opl_stage_run_context"],
        "opl_stage_attempt_readback": transaction_readback[
            "opl_stage_attempt_readback"
        ],
        "opl_stage_attempt_readback_status": transaction_readback[
            "opl_stage_attempt_readback_status"
        ],
        **(
            {"opl_route_handoff": transaction_readback["opl_route_handoff"]}
            if transaction_readback.get("opl_route_handoff")
            else {}
        ),
        "terminal_owner_gate": transaction_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": transaction_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": transaction_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "carry_forward_risk_receipt_ref": transaction_readback.get(
            "carry_forward_risk_receipt_ref"
        ),
        **(
            {"next_action": transaction_readback["next_action"]}
            if transaction_readback.get("next_action")
            else {}
        ),
        "next_owner_or_human_decision": transaction_readback[
            "next_owner_or_human_decision"
        ],
        "transaction_state": transaction_readback["transaction_state"],
        **(
            {
                "consume_candidate_status_override": transaction_readback[
                    "consume_candidate_status_override"
                ]
            }
            if transaction_readback.get("consume_candidate_status_override")
            else {}
        ),
        "paper_mission_transaction_readback": transaction_readback,
    }


def _submission_authority_owner_gate_readback(
    *,
    study_root: Path,
    study_id: str,
    next_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not next_action:
        return None
    return submission_authority_owner_gate_readback(
        {
            "study_id": study_id,
            "study_intervention_events": read_intervention_events(study_root=study_root),
        },
        next_action=next_action,
    )


def _durable_mission_stop_guard(
    *,
    consume_candidate_status: str | None,
    stage_closure_decision: Mapping[str, Any] | None,
) -> dict[str, Any]:
    decision = _mapping(stage_closure_decision)
    outcome = _mapping(decision.get("outcome"))
    status = str(consume_candidate_status or "").strip()
    outcome_kind = str(outcome.get("kind") or "").strip()
    transition_kind = str(outcome.get("transition_kind") or "").strip()
    checkpoint_only = {
        "accepted_submission_milestone_candidate",
        "accepted_candidate",
        "candidate_ready_for_consumption",
        "route_back",
    }
    non_terminal_next_stage_transitions = {
        "bounded_quality_repair_iteration",
        "current_package_mirror_sync",
        "route_back_candidate_checkpoint",
    }
    terminal_next_stage_transitions = {"degraded_handoff"}
    terminal_outcome_allowed = outcome_kind in {
        "typed_blocker",
        "human_gate",
        "owner_receipt",
    } or (
        outcome_kind == "next_stage_transition"
        and transition_kind in terminal_next_stage_transitions
    )
    return {
        "surface_kind": "paper_mission_durable_stop_guard",
        "accepted_submission_milestone_candidate_is_durable_stop": False,
        "checkpoint_only_statuses": sorted(checkpoint_only),
        "observed_consume_candidate_status": status or None,
        "observed_stage_closure_outcome": outcome_kind or None,
        "observed_next_stage_transition": transition_kind or None,
        "non_terminal_next_stage_transitions": sorted(non_terminal_next_stage_transitions),
        "terminal_next_stage_transitions": sorted(terminal_next_stage_transitions),
        "requires_terminalizer_outcome": True,
        "requires_submission_or_presubmission_deliverable": True,
        "requires_owner_receipt_or_human_gate_or_typed_blocker": True,
        "durable_stop_allowed": status not in checkpoint_only and terminal_outcome_allowed,
    }


def _terminal_owner_gate_from_transaction_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    carrier_gate = terminal_owner_gate_from_carrier_readback(
        _mapping(readback.get("opl_stage_attempt_readback"))
    )
    if carrier_gate:
        return carrier_gate
    return terminal_owner_gate_from_stage_terminal_decision(
        stage_terminal_decision=_mapping(readback.get("stage_terminal_decision")),
        paper_mission_transaction=_mapping(readback.get("paper_mission_transaction")),
    )


def _next_owner_or_human_decision_from_transaction_readback(
    *,
    readback: Mapping[str, Any],
    terminal_owner_gate: Mapping[str, Any],
) -> dict[str, Any]:
    if terminal_owner_gate:
        return terminal_owner_gate_next_decision(terminal_owner_gate)
    return stage_terminal_next_owner_or_human_decision(
        stage_terminal_decision=_mapping(readback.get("stage_terminal_decision")),
        ai_route_context=_mapping(readback.get("ai_route_context")),
    )


def _next_stage_id_for_materialized(stage_id: str) -> str:
    if stage_id == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if stage_id == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


def _carrier_readback_has_consumable_receipt(
    payload: Mapping[str, Any],
    *,
    request_carrier: Mapping[str, Any],
) -> bool:
    return matches_receipt_bundle(
        receipt=_mapping(payload.get("opl_stage_attempt_receipt")),
        evidence=_mapping(payload.get("receipt_evidence")),
        consumption=_mapping(payload.get("mas_receipt_consumption")),
        carrier=request_carrier,
    )


def _transaction_state(transaction: dict[str, Any]) -> str:
    explicit = _optional_text(transaction.get("transaction_state"))
    if explicit:
        return explicit
    terminal_status = _optional_text(
        _mapping(transaction.get("stage_terminal_decision")).get("status")
    )
    return terminal_status or "not_materialized"


def _validate_paper_mission_transaction_if_available(
    transaction: dict[str, Any],
) -> dict[str, Any]:
    try:
        from med_autoscience.paper_mission_transaction import PaperMissionTransaction
    except ModuleNotFoundError:
        return {
            "status": "pending_contract_module_not_available",
            "validator": (
                "med_autoscience.paper_mission_transaction.PaperMissionTransaction"
            ),
        }
    try:
        PaperMissionTransaction.from_payload(transaction)
    except Exception as exc:  # pragma: no cover - exact type belongs to contract lane.
        return {
            "status": "failed",
            "validator": (
                "med_autoscience.paper_mission_transaction.PaperMissionTransaction"
            ),
            "error": str(exc),
        }
    return {
        "status": "validated",
        "validator": "med_autoscience.paper_mission_transaction.PaperMissionTransaction",
    }


def _mission_state_for_consume_result(consume_result: dict[str, Any]) -> str:
    status = consume_result.get("status")
    if status == "accepted":
        return "consumed"
    if status == "route_back":
        return "route_back"
    if status == "typed_blocker":
        return "stable_blocker"
    if status == "human_gate":
        return "waiting_human_decision"
    if status == "rejected":
        return "route_back"
    return "planned"
