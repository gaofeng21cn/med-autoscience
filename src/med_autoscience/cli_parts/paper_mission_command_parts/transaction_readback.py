from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.cli_parts.paper_mission_command_parts.common import (
    _first_mapping,
    _first_text,
    _load_json_object,
    _mapping,
    _mapping_list,
    _optional_text,
    _slug,
)
from med_autoscience.cli_parts.paper_mission_command_parts.materialized_readback_context import (
    paper_audit_pack_for_cli_readback as _paper_audit_pack_for_cli_readback,
)
from med_autoscience.controllers.study_interventions import read_intervention_events
from med_autoscience.controllers.study_progress_parts.canonical_owner_action_projection import (
    submission_authority_owner_gate_readback,
)
from med_autoscience.paper_mission_opl_carrier import paper_mission_opl_runtime_carrier
from med_autoscience.paper_mission_opl_readback import (
    attach_opl_runtime_carrier_readback,
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
from med_autoscience.paper_mission_transaction import (
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
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
PAPER_AUDIT_PACK_FAMILIES = (
    "analysis_rationale_log",
    "decision_trace",
    "evidence_ledger_delta",
    "review_ledger_delta",
    "revision_log_delta",
    "failed_path_ledger",
    "artifact_lineage",
    "reproducibility_refs",
)

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
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
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
    enable_opl_live_probe: bool = False,
    opl_bin: str | Path | None = None,
    attach_runtime_readback=attach_opl_runtime_carrier_readback,
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
        if transaction_source_override != "paper_mission_consumption_ledger"
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
        "opl_route_command": _mapping(transaction.get("opl_route_command")),
        "opl_runtime_carrier": paper_mission_opl_runtime_carrier(transaction),
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
        enable_opl_live_probe=enable_opl_live_probe,
        opl_bin=opl_bin,
    )
    readback = attach_next_action(readback)
    terminal_owner_gate = _terminal_owner_gate_from_transaction_readback(readback)
    readback["terminal_owner_gate"] = terminal_owner_gate or None
    terminal_gate_authority_readback = terminal_owner_gate_authority_readback(
        terminal_owner_gate
    )
    owner_answer_readback = terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate=terminal_owner_gate,
        paper_mission_transaction=transaction,
        artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
        paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
    ) if not owner_answer_readback_prefill else dict(owner_answer_readback_prefill)
    terminal_gate_authority_readback = terminal_owner_gate_authority_consume_readback(
        terminal_owner_gate_authority_readback=terminal_gate_authority_readback,
        owner_answer_readback=owner_answer_readback,
    )
    if owner_answer_readback and transaction_source_override != "paper_mission_consumption_ledger":
        owner_answer_transaction = _mapping(
            owner_answer_readback.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            readback["source"] = "terminal_owner_gate_owner_answer"
            readback["paper_mission_transaction"] = owner_answer_transaction
            readback["stage_terminal_decision"] = _mapping(
                owner_answer_transaction.get("stage_terminal_decision")
            )
            readback["opl_route_command"] = _mapping(
                owner_answer_transaction.get("opl_route_command")
            )
            readback["opl_runtime_carrier"] = paper_mission_opl_runtime_carrier(
                owner_answer_transaction
            )
            readback["transaction_state"] = _transaction_state(owner_answer_transaction)
            readback["consume_candidate_status_override"] = "route_back"
            readback = attach_next_action(readback)
    readback["terminal_owner_gate_authority_readback"] = (
        terminal_gate_authority_readback or None
    )
    readback["terminal_owner_gate_owner_answer_readback"] = (
        owner_answer_readback or None
    )
    owner_answer_next_decision = (
        {}
        if transaction_source_override == "paper_mission_consumption_ledger"
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
        readback["semantic_progress_signature"] = owner_answer.get(
            "semantic_progress_signature"
        )
        readback["route_back_budget"] = owner_answer.get("route_back_budget")
        readback["mission_executor_fallback_action"] = owner_answer.get(
            "mission_executor_fallback_action"
        )
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


def _mission_state_for_materialized_readback(
    *,
    mission: Mapping[str, Any],
    transaction_readback: Mapping[str, Any],
    consumption_ledger_readback: Mapping[str, Any] | None,
) -> str:
    if consumption_ledger_readback is not None:
        status = _optional_text(consumption_ledger_readback.get("consume_candidate_status"))
        if status in {"typed_blocker", "human_gate"}:
            return "stable_blocker" if status == "typed_blocker" else "waiting_human_decision"
        if status in {"route_back", "rejected"}:
            return "route_back"
        return "consumed"
    if transaction_readback.get("consume_candidate_status_override") == "route_back":
        return "route_back"
    return _optional_text(mission.get("mission_state")) or "planned"


def _consume_result_for_consumption_ledger_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    status = _optional_text(readback.get("consume_candidate_status"))
    selected_outcome = _optional_text(readback.get("selected_outcome"))
    if status == "route_back":
        result_status = "route_back"
    elif status == "human_gate":
        result_status = "human_gate"
    elif status == "typed_blocker":
        result_status = "typed_blocker"
    elif status == "rejected":
        result_status = "rejected"
    elif status:
        result_status = "accepted"
    else:
        result_status = "not_consumed"
    return {
        "status": result_status,
        "outcome": status or selected_outcome or result_status,
        "authority_materialized": False,
    }


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


def _next_owner_decision_for_consumption_ledger_readback(
    *,
    readback: Mapping[str, Any],
    fallback: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(readback.get("stage_terminal_decision"))
    handoff = _mapping(readback.get("opl_route_handoff"))
    route = _mapping(readback.get("opl_route_command"))
    next_owner = _first_text(
        decision.get("next_owner"),
        handoff.get("next_owner"),
        readback.get("next_owner"),
        fallback.get("next_owner"),
    )
    status = _first_text(
        readback.get("consume_candidate_status"),
        readback.get("selected_outcome"),
        decision.get("decision_kind"),
        fallback.get("summary"),
    )
    return {
        "kind": (
            "human_decision"
            if _optional_text(decision.get("decision_kind")) == "human_gate"
            else "owner_or_route"
        ),
        "next_owner": next_owner,
        "human_decision_required": (
            _optional_text(decision.get("decision_kind")) == "human_gate"
        ),
        "summary": status,
        **(
            {"route_command": route_command}
            if (route_command := _optional_text(route.get("command_kind"))) is not None
            else {}
        ),
        **(
            {"route_target": route_target}
            if (
                route_target := _first_text(
                    route.get("target"),
                    route.get("route_target"),
                    handoff.get("route_target"),
                )
            )
            is not None
            else {}
        ),
        **(
            {"opl_route_handoff_ref": handoff_ref}
            if (handoff_ref := _optional_text(handoff.get("source_ref"))) is not None
            else {}
        ),
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }


def _transaction_readback_output_fields(
    transaction_readback: dict[str, Any],
) -> dict[str, Any]:
    return {
        "paper_mission_transaction": transaction_readback[
            "paper_mission_transaction"
        ],
        "stage_terminal_decision": transaction_readback["stage_terminal_decision"],
        "opl_route_command": transaction_readback["opl_route_command"],
        "opl_runtime_carrier": transaction_readback["opl_runtime_carrier"],
        "opl_runtime_carrier_readback": transaction_readback[
            "opl_runtime_carrier_readback"
        ],
        "opl_runtime_readback_status": transaction_readback[
            "opl_runtime_readback_status"
        ],
        "terminal_owner_gate": transaction_readback.get("terminal_owner_gate"),
        "terminal_owner_gate_authority_readback": transaction_readback.get(
            "terminal_owner_gate_authority_readback"
        ),
        "terminal_owner_gate_owner_answer_readback": transaction_readback.get(
            "terminal_owner_gate_owner_answer_readback"
        ),
        "semantic_progress_signature": transaction_readback.get(
            "semantic_progress_signature"
        ),
        "route_back_budget": transaction_readback.get("route_back_budget"),
        "mission_executor_fallback_action": transaction_readback.get(
            "mission_executor_fallback_action"
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
        _mapping(readback.get("opl_runtime_carrier_readback"))
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
        opl_route_command=_mapping(readback.get("opl_route_command")),
    )


def _candidate_manifest_transaction(candidate: str | Path | None) -> dict[str, Any]:
    if candidate is None:
        return {}
    path = Path(candidate).expanduser()
    if not path.exists():
        return {}
    try:
        payload = _load_json_object(path)
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    package_candidate_ref = _optional_text(
        _mapping(payload.get("artifact_refs")).get("candidate_manifest")
    )
    if package_candidate_ref is not None:
        package_candidate_path = Path(package_candidate_ref).expanduser()
        if not package_candidate_path.is_absolute():
            package_candidate_path = path.parent / package_candidate_path
        if package_candidate_path != path:
            package_transaction = _candidate_manifest_transaction(package_candidate_path)
            if package_transaction:
                return package_transaction
    inline = _mapping(payload.get("paper_mission_transaction"))
    if inline:
        return inline
    sidecar_refs = _mapping(payload.get("mission_candidate_sidecar_refs"))
    readback_ref = _optional_text(sidecar_refs.get("paper_mission_readback"))
    if readback_ref is not None:
        try:
            readback = _load_json_object(Path(readback_ref).expanduser())
        except (OSError, json.JSONDecodeError, ValueError):
            readback = {}
        transaction = _mapping(readback.get("paper_mission_transaction"))
        if transaction:
            return transaction
    mission_ref = _optional_text(sidecar_refs.get("paper_mission_run"))
    if mission_ref is not None:
        try:
            mission = _load_json_object(Path(mission_ref).expanduser())
        except (OSError, json.JSONDecodeError, ValueError):
            mission = {}
        transaction = _mapping(mission.get("paper_mission_transaction"))
        if transaction:
            return transaction
    default_readback_ref = _optional_text(sidecar_refs.get("default_readback"))
    if default_readback_ref is None:
        return {}
    try:
        default_readback = _load_json_object(Path(default_readback_ref).expanduser())
    except (OSError, json.JSONDecodeError, ValueError):
        return {}
    return _mapping(default_readback.get("paper_mission_transaction"))


def _candidate_mission_id_for_readback(
    *,
    selected_mission_id: str,
    transaction_readback: dict[str, Any],
    authority_consume_readback: dict[str, Any] | None,
) -> str:
    transaction = _mapping(transaction_readback.get("paper_mission_transaction"))
    if transaction_readback.get("source") != "placeholder_no_write":
        transaction_mission_id = _optional_text(transaction.get("mission_id"))
        if transaction_mission_id:
            return transaction_mission_id
    readback_mission_id = _optional_text((authority_consume_readback or {}).get("mission_id"))
    if readback_mission_id and readback_mission_id != "unknown_mission":
        return readback_mission_id
    return selected_mission_id


def _placeholder_paper_mission_transaction(
    *,
    mission_id: str,
    study_id: str,
    objective: str,
    paper_mission_command: str,
    study_root: Path,
    consume_result: dict[str, Any],
) -> dict[str, Any]:
    stage_id = f"paper-mission-cli::{paper_mission_command}"
    stage_run_ref = f"paper-mission-cli://{study_id}/{paper_mission_command}"
    transaction_id = f"paper-mission-transaction::{study_id}::{paper_mission_command}::{_slug(mission_id)}"
    next_work_unit = objective or "paper mission no-write readback"
    terminal_decision = {
        "decision_kind": "continue_same_stage",
        "status": "not_materialized",
        "reason": (
            "No MAS-authored PaperMissionTransaction was materialized; CLI reports "
            "a no-write placeholder only."
        ),
        "next_owner": "mission_executor",
        "next_work_unit": next_work_unit,
        "authority_materialized": False,
        "consume_result_status": _optional_text(consume_result.get("status"))
        or "not_consumed",
    }
    route_command = {
        "command_kind": "resume_stage",
        "target": next_work_unit,
        "reason": "No materialized MAS stage terminal decision is available.",
        "source_terminal_decision_ref": f"{transaction_id}#stage_terminal_decision",
        "stage_run_ref": stage_run_ref,
        "runtime_owner": "one-person-lab",
        "authority_materialized": False,
    }
    transaction = {
        "schema_version": "paper-mission-transaction.v1",
        "transaction_id": transaction_id,
        "mission_id": mission_id,
        "study_id": study_id,
        "stage_id": stage_id,
        "stage_run_ref": stage_run_ref,
        "stage_terminal_decision": terminal_decision,
        "opl_route_command": route_command,
        "artifact_delta_refs": [
            {
                "ref_id": "paper_mission_cli_no_write_plan",
                "ref_kind": "workspace_path",
                "uri": str(study_root / "paper"),
            }
        ],
        "paper_audit_pack_refs": {
            family: [
                {
                    "ref_id": f"{family}::paper-mission-cli",
                    "ref_kind": "paper_mission_cli_readback",
                    "uri": f"paper-mission-cli://{study_id}/{paper_mission_command}/{family}",
                }
            ]
            for family in PAPER_AUDIT_PACK_FAMILIES
        },
        "authority_boundary": {
            "mas_authority_owner": "MedAutoScience",
            "runtime_owner": "one-person-lab",
            "writes_authority_surface": False,
            "writes_publication_eval": False,
            "writes_controller_decision": False,
            "writes_owner_receipt": False,
            "writes_typed_blocker": False,
            "writes_human_gate": False,
            "writes_current_package": False,
            "writes_runtime_queue": False,
            "writes_provider_attempt": False,
            "writes_yang_authority": False,
        },
        "idempotency": {
            "idempotency_key": f"{study_id}::{stage_id}::{_slug(mission_id)}",
            "transaction_fingerprint": (
                f"{mission_id}::{stage_id}::continue_same_stage::not_materialized"
            ),
        },
        "transaction_state": "not_materialized",
    }
    return transaction


def _transaction_from_materialized_legacy_mission(
    *,
    mission: dict[str, Any] | None,
    study_id: str,
) -> dict[str, Any]:
    if not mission:
        return {}
    consume_result = _mapping(mission.get("consume_result"))
    if not consume_result:
        return {}
    mission_id = _optional_text(mission.get("mission_id")) or "paper-mission::unknown"
    readback = _mapping(mission.get("one_shot_migration_readback"))
    current_mission = _mapping(readback.get("current_mission"))
    required_output = _mapping(readback.get("required_output"))
    stage_id = _first_text(
        current_mission.get("objective_kind"),
        required_output.get("objective_kind"),
        "paper_mission_materialized_legacy_stage",
    )
    terminal_decision = stage_terminal_decision_for_consume_result(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        consume_result=_enriched_materialized_consume_result(
            consume_result=consume_result,
            readback=readback,
        ),
        default_next_owner=_first_text(
            required_output.get("next_owner"),
            readback.get("next_owner"),
            "mas_authority_kernel",
        )
        or "mas_authority_kernel",
        default_next_stage_id=_next_stage_id_for_materialized(stage_id),
        default_next_work_unit=_first_text(
            required_output.get("work_unit_id"),
            current_mission.get("objective_id"),
            stage_id,
        )
        or stage_id,
        default_reason=_first_text(
            consume_result.get("reason"),
            readback.get("consume_candidate_status"),
            "materialized legacy PaperMissionRun terminalized by CLI readback",
        )
        or "materialized legacy PaperMissionRun terminalized by CLI readback",
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=f"opl-stage-run://paper-mission-materialized/{study_id}/{stage_id}/{_slug(mission_id)}",
        terminal_decision=terminal_decision,
        artifact_delta_refs=_artifact_delta_refs_for_transaction(mission),
        paper_audit_pack_refs=_paper_audit_pack_refs_for_transaction(mission),
        idempotency_basis=_first_text(
            consume_result.get("outcome"),
            consume_result.get("status"),
            stage_id,
        )
        or stage_id,
    )


def _enriched_materialized_consume_result(
    *,
    consume_result: dict[str, Any],
    readback: dict[str, Any],
) -> dict[str, Any]:
    enriched = dict(consume_result)
    if not _optional_text(enriched.get("status")):
        enriched["status"] = _optional_text(readback.get("consume_candidate_status")) or "not_consumed"
    if not _optional_text(enriched.get("resume_condition")):
        enriched["resume_condition"] = _first_text(
            readback.get("resume_condition"),
            _mapping(readback.get("consume_candidate_readback")).get("resume_condition"),
        )
    blocker = _mapping(_mapping(readback.get("mission_input")).get("legacy_blocker"))
    typed_blocker = _mapping(blocker.get("typed_blocker"))
    if typed_blocker:
        enriched["blocker_id"] = _first_text(
            typed_blocker.get("blocker_id"),
            typed_blocker.get("blocker_type"),
            enriched.get("blocker_id"),
        )
        enriched["unblock_condition"] = _first_text(
            typed_blocker.get("required_input"),
            enriched.get("unblock_condition"),
            enriched.get("resume_condition"),
        )
    return enriched


def _artifact_delta_refs_for_transaction(mission: dict[str, Any]) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, delta in enumerate(_mapping_list(mission.get("artifact_delta_ledger")), start=1):
        uri = _optional_text(delta.get("artifact_ref"))
        if not uri:
            continue
        refs.append(
            {
                "ref_id": _optional_text(delta.get("delta_id")) or f"artifact_delta::{index}",
                "ref_kind": _optional_text(delta.get("delta_kind")) or "artifact_delta",
                "uri": uri,
            }
        )
    return refs or [
        {
            "ref_id": "artifact_delta::missing",
            "ref_kind": "missing_artifact_delta",
            "uri": "mission://artifact-delta/missing",
        }
    ]


def _paper_audit_pack_refs_for_transaction(
    mission: dict[str, Any],
) -> dict[str, list[dict[str, str]]]:
    audit_pack = _mapping(mission.get("paper_audit_pack"))
    refs_by_family: dict[str, list[dict[str, str]]] = {}
    for family in PAPER_AUDIT_PACK_FAMILIES:
        family_payload = _mapping(audit_pack.get(family))
        refs = [
            {
                "ref_id": _optional_text(ref.get("ref_id")) or f"{family}::{index}",
                "ref_kind": _optional_text(ref.get("ref_kind")) or "artifact_ref",
                "uri": _optional_text(ref.get("uri")) or f"mission://audit-pack/{family}/missing",
            }
            for index, ref in enumerate(_mapping_list(family_payload.get("refs")), start=1)
        ]
        refs_by_family[family] = refs or [
            {
                "ref_id": f"{family}::missing",
                "ref_kind": "missing_audit_ref",
                "uri": f"mission://audit-pack/{family}/missing",
            }
        ]
    return refs_by_family


def _next_stage_id_for_materialized(stage_id: str) -> str:
    if stage_id == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if stage_id == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


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
