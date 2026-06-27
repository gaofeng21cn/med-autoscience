from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_run import (
    PaperMissionRun,
    REQUIRED_PAPER_AUDIT_PACK_FAMILIES,
)
from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
)
from med_autoscience.paper_mission_opl_readback import (
    paper_mission_opl_runtime_carrier_readback,
)
from med_autoscience.paper_mission_owner_answer import (
    terminal_owner_gate_authority_consume_readback,
    terminal_owner_gate_owner_answer_next_decision,
    terminal_owner_gate_owner_answer_readback,
)
from med_autoscience.paper_mission_terminal_owner_gate import (
    terminal_owner_gate_authority_readback,
    terminal_owner_gate_from_carrier_readback,
    terminal_owner_gate_from_stage_terminal_decision,
    terminal_owner_gate_next_decision,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransaction,
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)


PAPER_MISSION_RUN_CONTRACT_VERSION = "paper-mission-run.v1"
PAPER_MISSION_RUN_CONTRACT_REF = "contracts/paper_mission_run_contract.json"
PAPER_MISSION_RUN_VALIDATOR = "med_autoscience.paper_mission_run.PaperMissionRun"
PAPER_MISSION_TRANSACTION_CONTRACT_REF = "contracts/paper_mission_transaction_contract.json"
PAPER_MISSION_TRANSACTION_VALIDATOR = (
    "med_autoscience.paper_mission_transaction.PaperMissionTransaction"
)
MISSION_STATES = (
    "planned",
    "running",
    "candidate_ready_for_consumption",
    "consumed",
    "route_back",
    "stable_blocker",
    "waiting_human_decision",
    "terminal_handoff",
)
PLATFORM_DIAGNOSTIC_TERMS = (
    "DHD",
    "domain-health-diagnostic",
    "currentness",
    "storage",
    "dispatch",
    "owner-route",
    "owner_route",
    "provider-admission",
    "provider_admission",
    "PaperRecovery",
    "paper_recovery",
    "read-model",
    "read_model",
)
PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_one_shot_migration"
)


def build_artifact_first_mission_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    progress = _mapping(payload)
    materialized_mission = _latest_materialized_mission(progress)
    if materialized_mission:
        return _materialized_mission_summary(
            progress=progress,
            materialized_mission=materialized_mission,
        )
    paper_delta = _mapping(
        progress.get("paper_progress_delta")
        or progress.get("deliverable_progress_delta")
    )
    deliverable_delta = _mapping(progress.get("deliverable_progress_delta") or paper_delta)
    platform_delta = _mapping(progress.get("platform_repair_delta"))
    next_forced_delta = _mapping(progress.get("next_forced_delta"))
    current_owner_delta = _mapping(progress.get("current_owner_delta"))
    current_work_unit = _mapping(progress.get("current_work_unit"))
    current_action = _mapping(progress.get("current_executable_owner_action"))
    user_visible = _mapping(progress.get("user_visible_projection"))
    source_refs = _source_refs(progress)
    latest_artifact_delta = _latest_artifact_delta(
        paper_delta=paper_delta,
        deliverable_delta=deliverable_delta,
        next_forced_delta=next_forced_delta,
        progress=progress,
    )
    artifact_delta_ledger = _artifact_delta_ledger(
        latest_artifact_delta=latest_artifact_delta,
        study_id=_study_id(progress),
    )
    platform_diagnostics = _platform_diagnostics(
        platform_delta=platform_delta,
        progress=progress,
    )
    mission_state = _mission_state(
        latest_artifact_delta=latest_artifact_delta,
        platform_diagnostics=platform_diagnostics,
        user_visible=user_visible,
        progress=progress,
    )
    current_objective = _current_objective(
        next_forced_delta=next_forced_delta,
        current_owner_delta=current_owner_delta,
        current_work_unit=current_work_unit,
        current_action=current_action,
        user_visible=user_visible,
    )
    next_owner_or_human_decision = _next_owner_or_human_decision(
        next_forced_delta=next_forced_delta,
        current_owner_delta=current_owner_delta,
        current_work_unit=current_work_unit,
        current_action=current_action,
        user_visible=user_visible,
    )
    paper_mission_run = _paper_mission_run_payload(
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=artifact_delta_ledger,
        source_refs=source_refs,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    effective_consume_candidate_status = _non_empty_text(
        _mapping(paper_mission_run.get("consume_result")).get("status")
    ) or "not_consumed"
    consumption_ledger_readback = _latest_consumption_ledger_readback(
        progress=progress,
        study_id=_study_id(progress),
    )
    if consumption_ledger_readback:
        effective_consume_candidate_status = (
            _non_empty_text(consumption_ledger_readback.get("consume_candidate_status"))
            or effective_consume_candidate_status
        )
        mission_state = _mission_state_for_consumption_ledger(
            consumption_ledger_readback
        )
        next_owner_or_human_decision = _next_owner_decision_for_consumption_ledger(
            readback=consumption_ledger_readback,
            fallback=next_owner_or_human_decision,
        )
        ledger_next_owner = _non_empty_text(
            next_owner_or_human_decision.get("next_owner")
        )
        if ledger_next_owner:
            current_objective = {
                **current_objective,
                "next_owner": ledger_next_owner,
            }
        paper_mission_run = {
            **paper_mission_run,
            "mission_state": mission_state,
            "consume_result": _consume_result_for_consumption_ledger(
                consumption_ledger_readback
            ),
            "paper_mission_transaction": consumption_ledger_readback[
                "paper_mission_transaction"
            ],
            "current_objective": current_objective,
            "next_owner_or_human_decision": next_owner_or_human_decision,
        }
    carrier = paper_mission_opl_runtime_carrier(
        paper_mission_run["paper_mission_transaction"]
    )
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=_materialized_study_root(progress=progress),
        enable_opl_live_probe=True,
    )
    terminal_owner_gate = terminal_owner_gate_from_carrier_readback(carrier_readback)
    if not terminal_owner_gate and consumption_ledger_readback:
        terminal_owner_gate = terminal_owner_gate_from_stage_terminal_decision(
            stage_terminal_decision=_mapping(
                paper_mission_run["paper_mission_transaction"].get(
                    "stage_terminal_decision"
                )
            ),
            paper_mission_transaction=paper_mission_run["paper_mission_transaction"],
        )
    terminal_gate_authority_readback = terminal_owner_gate_authority_readback(
        terminal_owner_gate
    )
    owner_answer_readback = terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate=terminal_owner_gate,
        paper_mission_transaction=paper_mission_run["paper_mission_transaction"],
        artifact_delta_refs=_mapping_list(
            paper_mission_run["paper_mission_transaction"].get("artifact_delta_refs")
        ),
        paper_audit_pack_refs=_mapping(
            paper_mission_run["paper_mission_transaction"].get("paper_audit_pack_refs")
        ),
    )
    terminal_gate_authority_readback = terminal_owner_gate_authority_consume_readback(
        terminal_owner_gate_authority_readback=terminal_gate_authority_readback,
        owner_answer_readback=owner_answer_readback,
    )
    effective_transaction = _mapping(paper_mission_run["paper_mission_transaction"])
    if owner_answer_readback and not consumption_ledger_readback:
        owner_answer_transaction = _mapping(
            owner_answer_readback.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            effective_transaction = owner_answer_transaction
            transaction_state = _transaction_state(effective_transaction)
            mission_state = "route_back"
    if terminal_owner_gate:
        next_owner_or_human_decision = (
            terminal_owner_gate_owner_answer_next_decision(owner_answer_readback)
            or terminal_owner_gate_next_decision(terminal_owner_gate)
        )
    summary = {
        "surface_kind": "artifact_first_paper_mission_summary",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_RUN_CONTRACT_REF,
        "validator": PAPER_MISSION_RUN_VALIDATOR,
        "transaction_contract_ref": PAPER_MISSION_TRANSACTION_CONTRACT_REF,
        "transaction_validator": PAPER_MISSION_TRANSACTION_VALIDATOR,
        "paper_mission_run": paper_mission_run,
        "paper_mission_transaction": effective_transaction,
        "stage_terminal_decision": _mapping(
            effective_transaction.get("stage_terminal_decision")
        ),
        "opl_route_command": _mapping(effective_transaction.get("opl_route_command")),
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": carrier_readback,
        "opl_runtime_readback_status": carrier_readback["carrier_status"],
        "transaction_state": _transaction_state(effective_transaction),
        "mission_state": mission_state,
        "consume_candidate_status": effective_consume_candidate_status,
        "current_objective": current_objective,
        "latest_artifact_delta": {
            **latest_artifact_delta,
            "artifact_delta_ledger": artifact_delta_ledger,
        },
        "next_owner_or_human_decision": next_owner_or_human_decision,
        "terminal_owner_gate": terminal_owner_gate or None,
        "terminal_owner_gate_authority_readback": (
            terminal_gate_authority_readback or None
        ),
        "terminal_owner_gate_owner_answer_readback": owner_answer_readback or None,
        "platform_diagnostics": platform_diagnostics,
        "default_progress_metric": "paper_artifact_delta",
        "legacy_path_role": "diagnostics_migration_provenance_only",
        "paper_progress_counting_policy": {
            "counts_as_paper_progress": [
                "canonical_manuscript_delta",
                "figure_or_table_delta",
                "evidence_ledger_delta",
                "reviewer_response_delta",
                "owner_decision_packet",
                "accepted_owner_receipt",
                "route_back",
                "human_gate",
                "stable_typed_blocker_with_recoverable_path",
            ],
            "diagnostics_only": list(PLATFORM_DIAGNOSTIC_TERMS),
            "platform_repair_counts_as_paper_progress": False,
            "legacy_current_work_unit_counts_as_next_action_authority": False,
        },
        "authority": {
            "projection_only": True,
            "writes_authority_surface": False,
            "can_authorize_publication_ready": False,
            "can_authorize_quality_verdict": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_mutate_current_package": False,
            "can_start_provider_attempt": False,
            "can_mark_dm002_dm003_complete": False,
        },
        "read_model_source": {
            "source_kind": (
                "paper_mission_consumption_ledger"
                if consumption_ledger_readback
                else "legacy_progress_projection_fallback"
            ),
            **(
                {
                    "consumption_ledger_ref": _non_empty_text(
                        consumption_ledger_readback.get("source_ref")
                    ),
                    "consumption_ledger_role": "current_paper_mission_transaction",
                }
                if consumption_ledger_readback
                else {}
            ),
            "legacy_projection_role": "diagnostic_fallback_not_execution_authority",
            "legacy_fields_folded": [
                "next_forced_delta",
                "current_owner_delta",
                "current_work_unit",
                "current_executable_owner_action",
            ],
            "current_objective_source": "diagnostic_fallback",
            "next_owner_source": "diagnostic_fallback",
            "can_select_next_runtime_action": False,
            "fallback_transaction_is_runnable": False,
            "can_authorize_provider_admission": False,
        },
    }
    summary["status"] = mission_state
    return summary


def attach_artifact_first_mission_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    summary = build_artifact_first_mission_summary(updated)
    updated["artifact_first_mission_summary"] = summary
    updated["mission_state"] = summary["mission_state"]
    if "consume_candidate_status" in summary:
        updated["consume_candidate_status"] = summary["consume_candidate_status"]
    updated["paper_mission_run"] = summary["paper_mission_run"]
    updated["current_objective"] = summary["current_objective"]
    updated["latest_artifact_delta"] = summary["latest_artifact_delta"]
    updated["next_owner_or_human_decision"] = summary["next_owner_or_human_decision"]
    updated["terminal_owner_gate"] = summary.get("terminal_owner_gate")
    updated["terminal_owner_gate_authority_readback"] = summary.get(
        "terminal_owner_gate_authority_readback"
    )
    updated["terminal_owner_gate_owner_answer_readback"] = summary.get(
        "terminal_owner_gate_owner_answer_readback"
    )
    updated["platform_diagnostics"] = summary["platform_diagnostics"]
    updated["paper_mission_transaction"] = summary["paper_mission_transaction"]
    updated["stage_terminal_decision"] = summary["stage_terminal_decision"]
    updated["opl_route_command"] = summary["opl_route_command"]
    updated["opl_runtime_carrier"] = summary["opl_runtime_carrier"]
    updated["opl_runtime_carrier_readback"] = summary["opl_runtime_carrier_readback"]
    updated["opl_runtime_readback_status"] = summary["opl_runtime_readback_status"]
    updated["transaction_state"] = summary["transaction_state"]
    return updated


def _mission_state(
    *,
    latest_artifact_delta: Mapping[str, Any],
    platform_diagnostics: Mapping[str, Any],
    user_visible: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> str:
    if bool(user_visible.get("needs_user_decision")):
        return "waiting_human_decision"
    owner_answer_kind = _owner_answer_kind(progress)
    if owner_answer_kind == "typed_blocker":
        return "stable_blocker"
    if owner_answer_kind == "owner_receipt":
        return "consumed"
    if owner_answer_kind in {"route_back", "routeback"}:
        return "route_back"
    if _delta_count(latest_artifact_delta) > 0:
        return "candidate_ready_for_consumption"
    if _non_empty_text(user_visible.get("writer_state")) == "live":
        return "running"
    if _diagnostic_count(platform_diagnostics) > 0:
        return "planned"
    return "planned"


def _materialized_mission_summary(
    *,
    progress: Mapping[str, Any],
    materialized_mission: Mapping[str, Any],
) -> dict[str, Any]:
    mission = dict(materialized_mission)
    study_id = _non_empty_text(mission.get("study_id")) or _study_id(progress)
    consumption_ledger_readback = _latest_consumption_ledger_readback(
        progress=progress,
        study_id=study_id,
    )
    if consumption_ledger_readback:
        ledger_transaction = _mapping(
            consumption_ledger_readback["paper_mission_transaction"]
        )
        ledger_mission_id = _non_empty_text(ledger_transaction.get("mission_id"))
        mission["mission_state"] = _mission_state_for_consumption_ledger(
            consumption_ledger_readback
        )
        if ledger_mission_id:
            mission["mission_id"] = ledger_mission_id
        mission["paper_mission_transaction"] = ledger_transaction
        mission["consume_result"] = _consume_result_for_consumption_ledger(
            consumption_ledger_readback
        )
    default_readback = _mapping(mission.get("one_shot_migration_readback"))
    mission_state = _non_empty_text(mission.get("mission_state")) or "planned"
    current_mission = _mapping(default_readback.get("current_mission"))
    required_output = _mapping(default_readback.get("required_output"))
    platform_diagnostics = _materialized_platform_diagnostics(
        progress=progress,
        default_readback=default_readback,
    )
    latest_artifact_delta = _materialized_latest_artifact_delta(mission=mission)
    next_owner = _first_text(
        default_readback.get("next_owner"),
        required_output.get("next_owner"),
    )
    next_owner_or_human_decision = _compact(
        {
            "kind": (
                "human_decision"
                if _consume_candidate_status(mission, default_readback) == "human_gate"
                else "owner_or_route"
            ),
            "next_owner": next_owner,
            "human_decision_required": _consume_candidate_status(
                mission,
                default_readback,
            )
            == "human_gate",
            "summary": _consume_candidate_status(mission, default_readback),
            "typed_blocker_ref": _typed_blocker_ref(default_readback),
            "owner_receipt_ref": _owner_receipt_ref(default_readback),
            "can_execute": False,
            "can_authorize_provider_admission": False,
        }
    )
    current_objective = _compact(
        {
            "mission_id": _non_empty_text(mission.get("mission_id")),
            "objective": _first_text(
                current_mission.get("objective_kind"),
                mission.get("objective"),
            ),
            "objective_id": current_mission.get("objective_id"),
            "objective_kind": current_mission.get("objective_kind"),
            "work_unit_id": required_output.get("work_unit_id"),
            "required_output": required_output or None,
            "next_owner": next_owner,
        }
    )
    paper_mission_run = _normalize_paper_mission_run_payload(
        progress=progress,
        mission=mission,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=[
            dict(item)
            for item in _mapping_list(latest_artifact_delta.get("artifact_delta_ledger"))
        ],
        source_refs=[dict(item) for item in _mapping_list(mission.get("source_refs"))],
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    transaction = _mapping(paper_mission_run.get("paper_mission_transaction"))
    transaction_state = _transaction_state(transaction)
    carrier = paper_mission_opl_runtime_carrier(transaction)
    carrier_readback = paper_mission_opl_runtime_carrier_readback(
        carrier=carrier,
        study_root=_materialized_study_root(progress=progress),
        enable_opl_live_probe=True,
    )
    terminal_owner_gate = terminal_owner_gate_from_carrier_readback(carrier_readback)
    if not terminal_owner_gate and consumption_ledger_readback:
        terminal_owner_gate = terminal_owner_gate_from_stage_terminal_decision(
            stage_terminal_decision=_mapping(transaction.get("stage_terminal_decision")),
            paper_mission_transaction=transaction,
        )
    terminal_gate_authority_readback = terminal_owner_gate_authority_readback(
        terminal_owner_gate
    )
    owner_answer_readback = terminal_owner_gate_owner_answer_readback(
        terminal_owner_gate=terminal_owner_gate,
        paper_mission_transaction=transaction,
        artifact_delta_refs=_mapping_list(transaction.get("artifact_delta_refs")),
        paper_audit_pack_refs=_mapping(transaction.get("paper_audit_pack_refs")),
    )
    terminal_gate_authority_readback = terminal_owner_gate_authority_consume_readback(
        terminal_owner_gate_authority_readback=terminal_gate_authority_readback,
        owner_answer_readback=owner_answer_readback,
    )
    effective_transaction = transaction
    effective_consume_candidate_status = _consume_candidate_status(
        mission,
        default_readback,
    )
    if consumption_ledger_readback:
        effective_consume_candidate_status = (
            _non_empty_text(consumption_ledger_readback.get("consume_candidate_status"))
            or effective_consume_candidate_status
        )
        next_owner_or_human_decision = _next_owner_decision_for_consumption_ledger(
            readback=consumption_ledger_readback,
            fallback=next_owner_or_human_decision,
        )
        ledger_next_owner = _non_empty_text(
            next_owner_or_human_decision.get("next_owner")
        )
        if ledger_next_owner:
            current_objective = {
                **current_objective,
                "next_owner": ledger_next_owner,
            }
            paper_mission_run = {
                **paper_mission_run,
                "current_objective": current_objective,
                "next_owner_or_human_decision": next_owner_or_human_decision,
            }
    if owner_answer_readback and not consumption_ledger_readback:
        owner_answer_transaction = _mapping(
            owner_answer_readback.get("paper_mission_transaction")
        )
        if owner_answer_transaction:
            effective_transaction = owner_answer_transaction
            transaction_state = _transaction_state(effective_transaction)
            mission_state = "route_back"
            effective_consume_candidate_status = "route_back"
    if terminal_owner_gate and not consumption_ledger_readback:
        next_owner_or_human_decision = (
            terminal_owner_gate_owner_answer_next_decision(owner_answer_readback)
            or terminal_owner_gate_next_decision(terminal_owner_gate)
        )
    summary = {
        "surface_kind": "artifact_first_paper_mission_summary",
        "schema_version": 1,
        "contract_ref": PAPER_MISSION_RUN_CONTRACT_REF,
        "validator": PAPER_MISSION_RUN_VALIDATOR,
        "transaction_contract_ref": PAPER_MISSION_TRANSACTION_CONTRACT_REF,
        "transaction_validator": PAPER_MISSION_TRANSACTION_VALIDATOR,
        "paper_mission_run": paper_mission_run,
        "paper_mission_transaction": effective_transaction,
        "stage_terminal_decision": _mapping(
            effective_transaction.get("stage_terminal_decision")
        ),
        "opl_route_command": _mapping(effective_transaction.get("opl_route_command")),
        "opl_runtime_carrier": carrier,
        "opl_runtime_carrier_readback": carrier_readback,
        "opl_runtime_readback_status": carrier_readback["carrier_status"],
        "transaction_state": transaction_state,
        "mission_state": mission_state,
        "current_objective": current_objective,
        "current_mission": current_mission or None,
        "consume_candidate_status": effective_consume_candidate_status,
        "latest_artifact_delta": latest_artifact_delta,
        "next_owner_or_human_decision": next_owner_or_human_decision,
        "terminal_owner_gate": terminal_owner_gate or None,
        "terminal_owner_gate_authority_readback": (
            terminal_gate_authority_readback or None
        ),
        "terminal_owner_gate_owner_answer_readback": owner_answer_readback or None,
        "platform_diagnostics": platform_diagnostics,
        "default_progress_metric": "paper_mission_run",
        "legacy_path_role": "diagnostics_migration_provenance_only",
        "paper_progress_counting_policy": {
            "counts_as_paper_progress": [
                "mission_artifact_delta",
                "owner_decision_packet",
                "accepted_owner_receipt",
                "route_back",
                "human_gate",
                "stable_typed_blocker_with_recoverable_path",
            ],
            "diagnostics_only": list(PLATFORM_DIAGNOSTIC_TERMS),
            "platform_repair_counts_as_paper_progress": False,
        },
        "authority": {
            "projection_only": True,
            "writes_authority_surface": False,
            "can_authorize_publication_ready": False,
            "can_authorize_quality_verdict": False,
            "can_write_owner_receipt": False,
            "can_write_typed_blocker": False,
            "can_write_human_gate": False,
            "can_mutate_current_package": False,
            "can_start_provider_attempt": False,
            "can_mark_dm002_dm003_complete": False,
        },
        "read_model_source": {
            "source_kind": (
                "paper_mission_consumption_ledger"
                if consumption_ledger_readback
                else "materialized_paper_mission_run"
            ),
            "materialized_mission_ref": _non_empty_text(
                mission.get("materialized_mission_ref")
            ),
            **(
                {
                    "consumption_ledger_ref": _non_empty_text(
                        consumption_ledger_readback.get("source_ref")
                    ),
                    "consumption_ledger_role": "current_paper_mission_transaction",
                }
                if consumption_ledger_readback
                else {}
            ),
            "legacy_progress_projection_role": "diagnostic_drilldown",
        },
    }
    summary["status"] = mission_state
    return summary


def _latest_materialized_mission(progress: Mapping[str, Any]) -> dict[str, Any]:
    study_id = _study_id(progress)
    study_root = _path_from_text(progress.get("study_root"))
    if study_root is None:
        study_root = _study_root_from_refs(progress=progress, study_id=study_id)
    if study_root is None:
        return {}
    workspace_root = _workspace_root_from_study_root(study_root)
    if workspace_root is None:
        return {}
    root = workspace_root / PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH
    if not root.exists():
        return {}
    candidates = sorted(
        (
            path
            for path in root.glob("*/*/paper_mission_run.json")
            if path.is_file()
            and _materialized_mission_path_matches(path, requested_study_id=study_id)
        ),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    for path in candidates:
        payload = _read_json_object(path)
        if not payload:
            continue
        payload["materialized_mission_ref"] = str(path)
        return payload
    return {}


def _latest_consumption_ledger_readback(
    *,
    progress: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    study_root = _materialized_study_root(progress=progress)
    workspace_root = _workspace_root_from_study_root(study_root)
    if workspace_root is None:
        return {}
    return latest_paper_mission_consumption_transaction_readback(
        workspace_root=workspace_root,
        study_id=study_id,
    ) or {}


def _mission_state_for_consumption_ledger(
    readback: Mapping[str, Any],
) -> str:
    status = _non_empty_text(readback.get("consume_candidate_status"))
    if status == "typed_blocker":
        return "stable_blocker"
    if status == "human_gate":
        return "waiting_human_decision"
    if status in {"route_back", "rejected"}:
        return "route_back"
    return "consumed"


def _consume_result_for_consumption_ledger(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    status = _non_empty_text(readback.get("consume_candidate_status"))
    selected_outcome = _non_empty_text(readback.get("selected_outcome"))
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


def _next_owner_decision_for_consumption_ledger(
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
    return _compact(
        {
            "kind": (
                "human_decision"
                if _non_empty_text(decision.get("decision_kind")) == "human_gate"
                else "owner_or_route"
            ),
            "next_owner": next_owner,
            "human_decision_required": (
                _non_empty_text(decision.get("decision_kind")) == "human_gate"
            ),
            "summary": status,
            "route_command": _non_empty_text(route.get("command_kind")),
            "route_target": _first_text(
                route.get("target"),
                route.get("route_target"),
                handoff.get("route_target"),
            ),
            "opl_route_handoff_ref": _non_empty_text(handoff.get("source_ref")),
            "can_execute": False,
            "can_authorize_provider_admission": False,
        }
    )


def _materialized_study_root(*, progress: Mapping[str, Any]) -> Path:
    study_id = _study_id(progress)
    study_root = _path_from_text(progress.get("study_root"))
    if study_root is not None:
        return study_root
    ref_study_root = _study_root_from_refs(progress=progress, study_id=study_id)
    if ref_study_root is not None:
        return ref_study_root
    return Path("studies") / study_id


def _materialized_mission_path_matches(
    path: Path,
    *,
    requested_study_id: str,
) -> bool:
    if _study_identity_matches(path.parent.name, requested_study_id):
        return True
    payload = _read_json_object(path)
    return _study_identity_matches(
        _non_empty_text(payload.get("study_id")) or "",
        requested_study_id,
    )


def _materialized_latest_artifact_delta(
    *,
    mission: Mapping[str, Any],
) -> dict[str, Any]:
    ledger = [dict(item) for item in _mapping_list(mission.get("artifact_delta_ledger"))]
    refs = [
        ref
        for item in ledger
        if (ref := _non_empty_text(item.get("artifact_ref"))) is not None
    ]
    return {
        "count": len(ledger),
        "token_usage_total": 0,
        "sources": ["materialized_paper_mission_run.artifact_delta_ledger"],
        "refs": refs,
        "classification": "mission_artifact_delta" if ledger else "none",
        "counts_as_paper_progress": bool(ledger),
        "platform_repair_excluded": True,
        "artifact_delta_ledger": ledger,
    }


def _materialized_platform_diagnostics(
    *,
    progress: Mapping[str, Any],
    default_readback: Mapping[str, Any],
) -> dict[str, Any]:
    imported = _mapping(default_readback.get("platform_diagnostics"))
    diagnostic_refs = _diagnostic_refs(progress)
    return {
        "count": _delta_count(_mapping(progress.get("platform_repair_delta"))),
        "sources": _dedupe_texts(
            [
                "materialized_paper_mission_run",
                *_text_list(imported.get("sources")),
                *_diagnostic_sources(progress),
            ]
        ),
        "refs": _dedupe_texts(
            [
                *_text_list(imported.get("refs")),
                *diagnostic_refs,
            ]
        ),
        "classification": "diagnostics_only",
        "folded_surfaces": list(PLATFORM_DIAGNOSTIC_TERMS),
        "counts_as_paper_progress": False,
        "repair_lane_required_for_platform_claims": bool(
            _delta_count(_mapping(progress.get("platform_repair_delta")))
            or diagnostic_refs
        ),
        "materialized_readback": imported or None,
    }


def _study_root_from_refs(
    *,
    progress: Mapping[str, Any],
    study_id: str,
) -> Path | None:
    refs = _mapping(progress.get("refs"))
    for value in refs.values():
        path = _path_from_text(value)
        if path is None:
            continue
        parts = path.parts
        for index, part in enumerate(parts[:-1]):
            if part == "studies" and index + 1 < len(parts):
                if _study_identity_matches(parts[index + 1], study_id):
                    return Path(*parts[: index + 2])
    return None


def _workspace_root_from_study_root(study_root: Path) -> Path | None:
    parts = study_root.parts
    for index, part in enumerate(parts[:-1]):
        if part == "studies" and index + 1 < len(parts):
            return Path(*parts[:index])
    return None


def _path_from_text(value: object) -> Path | None:
    text = _non_empty_text(value)
    if text is None:
        return None
    return Path(text).expanduser()


def _read_json_object(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return dict(payload) if isinstance(payload, Mapping) else {}


def _consume_candidate_status(
    mission: Mapping[str, Any],
    default_readback: Mapping[str, Any],
) -> str:
    status = _non_empty_text(default_readback.get("consume_candidate_status"))
    if status:
        return status
    consume_result = _mapping(mission.get("consume_result"))
    return _non_empty_text(consume_result.get("status")) or "not_consumed"


def _typed_blocker_ref(default_readback: Mapping[str, Any]) -> str | None:
    mission_input = _mapping(default_readback.get("mission_input"))
    legacy_blocker = _mapping(mission_input.get("legacy_blocker"))
    typed_blocker = _mapping(legacy_blocker.get("typed_blocker"))
    return _first_text(
        typed_blocker.get("typed_blocker_ref"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
    )


def _owner_receipt_ref(default_readback: Mapping[str, Any]) -> str | None:
    consume_readback = _mapping(default_readback.get("consume_candidate_readback"))
    return _first_text(
        consume_readback.get("owner_receipt_ref"),
        consume_readback.get("authority_receipt_ref"),
    )


def _current_objective(
    *,
    next_forced_delta: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    user_visible: Mapping[str, Any],
) -> dict[str, Any]:
    target_surface = (
        _mapping(next_forced_delta.get("target_surface"))
        or _mapping(current_owner_delta.get("target_surface"))
        or _mapping(current_action.get("target_surface"))
    )
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    return _compact(
        {
            "objective": _first_text(
                next_forced_delta.get("required_delta_kind"),
                current_owner_delta.get("required_delta_kind"),
                current_work_unit.get("required_output_contract"),
                user_visible.get("paper_stage_summary"),
                user_visible.get("current_stage_summary"),
            ),
            "work_unit_id": _first_text(
                next_forced_delta.get("work_unit_id"),
                current_owner_delta.get("work_unit_id"),
                current_work_unit.get("work_unit_id"),
                current_action.get("work_unit_id"),
            ),
            "action_type": _first_text(
                current_owner_delta.get("action_type"),
                current_action.get("action_type"),
                current_work_unit.get("action_type"),
            ),
            "target_surface": target_surface or None,
            "acceptance_refs": _text_list(next_forced_delta.get("acceptance_refs")),
            "next_owner": _first_text(
                owner_action.get("next_owner"),
                current_owner_delta.get("owner"),
                current_action.get("next_owner"),
                current_action.get("owner"),
                current_work_unit.get("owner"),
            ),
        }
    )


def _latest_artifact_delta(
    *,
    paper_delta: Mapping[str, Any],
    deliverable_delta: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> dict[str, Any]:
    refs = _dedupe_texts(
        [
            *_text_list(paper_delta.get("refs")),
            *_text_list(deliverable_delta.get("refs")),
            *_text_list(next_forced_delta.get("acceptance_refs")),
        ]
    )
    return {
        "count": _delta_count(paper_delta) or _delta_count(deliverable_delta),
        "token_usage_total": _number(
            paper_delta.get("token_usage_total")
            if paper_delta
            else deliverable_delta.get("token_usage_total")
        )
        or 0,
        "sources": _dedupe_texts(
            [
                *_text_list(paper_delta.get("sources")),
                *_text_list(deliverable_delta.get("sources")),
            ]
        ),
        "refs": refs,
        "classification": _non_empty_text(progress.get("progress_delta_classification")),
        "counts_as_paper_progress": (_delta_count(paper_delta) or _delta_count(deliverable_delta)) > 0,
        "platform_repair_excluded": True,
    }


def _artifact_delta_ledger(
    *,
    latest_artifact_delta: Mapping[str, Any],
    study_id: str,
) -> list[dict[str, Any]]:
    if _delta_count(latest_artifact_delta) <= 0:
        return []
    refs = _text_list(latest_artifact_delta.get("refs"))
    if not refs:
        refs = [f"mission://{study_id}/candidate-artifact-delta"]
    result: list[dict[str, Any]] = []
    for index, ref in enumerate(refs, start=1):
        result.append(
            {
                "delta_id": f"delta::{study_id}::{index}",
                "artifact_ref": ref,
                "delta_kind": "paper_artifact_delta",
                "status": "candidate",
            }
        )
    return result


def _next_owner_or_human_decision(
    *,
    next_forced_delta: Mapping[str, Any],
    current_owner_delta: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    current_action: Mapping[str, Any],
    user_visible: Mapping[str, Any],
) -> dict[str, Any]:
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    needs_human = bool(user_visible.get("needs_user_decision"))
    decision = {
        "kind": "human_decision" if needs_human else "owner_or_route",
        "next_owner": _first_text(
            owner_action.get("next_owner"),
            current_owner_delta.get("owner"),
            current_action.get("next_owner"),
            current_action.get("owner"),
            current_work_unit.get("owner"),
        ),
        "human_decision_required": needs_human,
        "summary": _first_text(
            user_visible.get("physician_decision_summary"),
            user_visible.get("user_decision_summary"),
            current_owner_delta.get("latest_owner_answer_kind"),
            next_forced_delta.get("reason"),
            user_visible.get("user_next"),
        ),
        "owner_receipt_ref": _first_text(
            current_owner_delta.get("owner_receipt_ref"),
            current_owner_delta.get("latest_owner_answer_ref")
            if current_owner_delta.get("latest_owner_answer_kind") == "owner_receipt"
            else None,
        ),
        "typed_blocker_ref": _first_text(
            current_owner_delta.get("typed_blocker_ref"),
            current_owner_delta.get("latest_owner_answer_ref")
            if current_owner_delta.get("latest_owner_answer_kind") == "typed_blocker"
            else None,
        ),
        "can_execute": False,
        "can_authorize_provider_admission": False,
    }
    return _compact(decision)


def _paper_mission_run_payload(
    *,
    progress: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
    artifact_delta_ledger: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _study_id(progress)
    objective = _non_empty_text(current_objective.get("objective")) or "inspect next paper artifact delta"
    mission_id = _mission_id(
        study_id=study_id,
        objective=objective,
        progress=progress,
        current_objective=current_objective,
    )
    consume_result = _consume_result(
        mission_state=mission_state,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    mission = {
        "schema_version": PAPER_MISSION_RUN_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": mission_state,
        "artifact_delta_ledger": artifact_delta_ledger,
        "source_refs": source_refs,
        "paper_audit_pack": _paper_audit_pack(
            study_id=study_id,
            mission_id=mission_id,
            objective=objective,
            artifact_delta_ledger=artifact_delta_ledger,
            source_refs=source_refs,
            platform_diagnostics=platform_diagnostics,
            next_owner_or_human_decision=next_owner_or_human_decision,
            current_objective=current_objective,
        ),
        "authority_touchpoints": _authority_touchpoints(
            platform_diagnostics=platform_diagnostics,
        ),
        "forbidden_write_guard": _forbidden_write_guard(),
        "consume_result": consume_result,
        "claim_permissions": {
            "can_claim_artifact_delta": bool(artifact_delta_ledger),
            "can_claim_owner_handoff": bool(next_owner_or_human_decision),
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": [],
        },
    }
    mission["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission=mission,
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=artifact_delta_ledger,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    return PaperMissionRun.from_payload(mission).to_dict()


def _normalize_paper_mission_run_payload(
    *,
    progress: Mapping[str, Any],
    mission: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
    artifact_delta_ledger: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    study_id = _non_empty_text(mission.get("study_id")) or _study_id(progress)
    objective = _non_empty_text(mission.get("objective")) or _first_text(
        current_objective.get("objective"),
        "inspect materialized paper mission",
    )
    mission_id = _non_empty_text(mission.get("mission_id")) or _mission_id(
        study_id=study_id,
        objective=objective,
        progress=progress,
        current_objective=current_objective,
    )
    if not source_refs:
        source_refs = _source_refs(progress)
    if not source_refs:
        source_refs = [
            {
                "ref_id": "source_ref::missing",
                "ref_kind": "missing_readback_ref",
                "uri": f"mission://{study_id}/source-refs/missing",
            }
        ]
    payload = {
        **dict(mission),
        "schema_version": PAPER_MISSION_RUN_CONTRACT_VERSION,
        "mission_id": mission_id,
        "study_id": study_id,
        "objective": objective,
        "mission_state": mission_state,
        "artifact_delta_ledger": artifact_delta_ledger,
        "source_refs": source_refs,
        "authority_touchpoints": _mapping_list(mission.get("authority_touchpoints"))
        or _authority_touchpoints(platform_diagnostics=platform_diagnostics),
        "forbidden_write_guard": _mapping(mission.get("forbidden_write_guard"))
        or _forbidden_write_guard(),
        "consume_result": _mapping(mission.get("consume_result"))
        or _consume_result(
            mission_state=mission_state,
            next_owner_or_human_decision=next_owner_or_human_decision,
        ),
        "claim_permissions": _mapping(mission.get("claim_permissions"))
        or {
            "can_claim_artifact_delta": bool(artifact_delta_ledger),
            "can_claim_owner_handoff": bool(next_owner_or_human_decision),
            "can_claim_publication_ready": False,
            "can_claim_current_package": False,
            "can_claim_owner_receipt_written": False,
            "claims": [],
        },
    }
    payload["paper_audit_pack"] = _mapping(mission.get("paper_audit_pack")) or _paper_audit_pack(
        study_id=study_id,
        mission_id=mission_id,
        objective=objective,
        artifact_delta_ledger=artifact_delta_ledger,
        source_refs=source_refs,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
        current_objective=current_objective,
    )
    payload["paper_mission_transaction"] = _paper_mission_transaction_payload(
        mission=payload,
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=artifact_delta_ledger,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    return PaperMissionRun.from_payload(payload).to_dict()


def _paper_mission_transaction_payload(
    *,
    mission: Mapping[str, Any],
    progress: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
    artifact_delta_ledger: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    existing = _mapping(mission.get("paper_mission_transaction"))
    if existing:
        try:
            transaction = PaperMissionTransaction.from_payload(existing)
        except ValueError:
            transaction = None
        if (
            transaction is not None
            and transaction.mission_id == _non_empty_text(mission.get("mission_id"))
            and transaction.study_id == _non_empty_text(mission.get("study_id"))
        ):
            return transaction.to_dict()
    stage_id = _materialized_transaction_stage_id(mission) or _stage_id(
        progress=progress,
        mission_state=mission_state,
        current_objective=current_objective,
    )
    consume_result = _mapping(mission.get("consume_result")) or _consume_result(
        mission_state=mission_state,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )
    mission_id = _non_empty_text(mission.get("mission_id")) or "paper-mission::unknown"
    study_id = _non_empty_text(mission.get("study_id")) or _study_id(progress)
    terminal_decision = (
        _diagnostic_fallback_terminal_decision(
            mission_id=mission_id,
            study_id=study_id,
            stage_id=stage_id,
        )
        if _diagnostic_fallback_requires_materialized_mission(
            mission_state=mission_state,
            artifact_delta_ledger=artifact_delta_ledger,
            platform_diagnostics=platform_diagnostics,
        )
        else stage_terminal_decision_for_consume_result(
            mission_id=mission_id,
            study_id=study_id,
            stage_id=stage_id,
            consume_result=consume_result,
            default_next_owner=_first_text(
                next_owner_or_human_decision.get("next_owner"),
                current_objective.get("next_owner"),
                "mas_authority_kernel",
            )
            or "mas_authority_kernel",
            default_next_stage_id=_next_stage_id(stage_id=stage_id),
            default_next_work_unit=_first_text(
                current_objective.get("work_unit_id"),
                current_objective.get("objective"),
                stage_id,
            )
            or stage_id,
            default_reason=_first_text(
                consume_result.get("reason"),
                next_owner_or_human_decision.get("summary"),
                "stage terminalized from artifact-first paper mission summary",
            )
            or "stage terminalized from artifact-first paper mission summary",
        )
    )
    return build_paper_mission_transaction(
        mission_id=mission_id,
        study_id=study_id,
        stage_id=stage_id,
        stage_run_ref=f"opl-stage-run://paper-mission-summary/{_study_id(progress)}/{stage_id}",
        terminal_decision=terminal_decision,
        artifact_delta_refs=_artifact_delta_refs_for_transaction(
            artifact_delta_ledger=artifact_delta_ledger,
            study_id=_study_id(progress),
        ),
        paper_audit_pack_refs=_paper_audit_pack_refs(_mapping(mission.get("paper_audit_pack"))),
        idempotency_basis=_first_text(
            consume_result.get("status"),
            current_objective.get("work_unit_id"),
            "projection",
        )
        or "projection",
    )


def _diagnostic_fallback_requires_materialized_mission(
    *,
    mission_state: str,
    artifact_delta_ledger: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
) -> bool:
    return (
        mission_state == "planned"
        and not artifact_delta_ledger
        and _diagnostic_count(platform_diagnostics) > 0
    )


def _diagnostic_fallback_terminal_decision(
    *,
    mission_id: str,
    study_id: str,
    stage_id: str,
) -> dict[str, Any]:
    return {
        "decision_kind": "human_gate",
        "status": "paper_mission_readback_missing",
        "reason": (
            "legacy progress/currentness diagnostics cannot select the next "
            "PaperMission stage; materialize a PaperMissionRun before routing "
            "work to OPL."
        ),
        "next_owner": "MedAutoScience",
        "question": (
            "Materialize a PaperMissionRun with MAS stage terminal decision "
            "before OPL runtime routing?"
        ),
        "required_receipt": (
            f"paper-mission-readback-missing::{study_id}::{stage_id}::{_slug(mission_id)}"
        ),
    }


def _paper_audit_pack(
    *,
    study_id: str,
    mission_id: str,
    objective: str,
    artifact_delta_ledger: list[dict[str, Any]],
    source_refs: list[dict[str, Any]],
    platform_diagnostics: Mapping[str, Any],
    next_owner_or_human_decision: Mapping[str, Any],
    current_objective: Mapping[str, Any],
) -> dict[str, Any]:
    source_uris = [
        uri for item in source_refs if (uri := _non_empty_text(item.get("uri"))) is not None
    ]
    artifact_uris = [
        uri
        for item in artifact_delta_ledger
        if (uri := _non_empty_text(item.get("artifact_ref"))) is not None
    ]
    diagnostic_refs = _text_list(platform_diagnostics.get("refs"))
    next_owner = _non_empty_text(next_owner_or_human_decision.get("next_owner"))
    work_unit_id = _non_empty_text(current_objective.get("work_unit_id"))
    refs_by_family = {
        "analysis_rationale_log": [
            mission_id,
            f"mission://{study_id}/objective/{_slug(objective)}",
        ],
        "decision_trace": [
            f"mission://{study_id}/stage-terminal-decision/{_slug(work_unit_id or objective)}",
            next_owner or "mas_authority_kernel",
        ],
        "evidence_ledger_delta": source_uris,
        "review_ledger_delta": [
            _non_empty_text(next_owner_or_human_decision.get("summary")) or "",
            f"mission://{study_id}/review-ledger/projection",
        ],
        "revision_log_delta": [
            f"mission://{study_id}/revision-log/{_slug(objective)}",
        ],
        "failed_path_ledger": diagnostic_refs
        or [f"mission://{study_id}/failed-path/no-current-diagnostic-ref"],
        "artifact_lineage": artifact_uris
        or [f"mission://{study_id}/artifact-lineage/no-artifact-delta-yet"],
        "reproducibility_refs": diagnostic_refs
        or source_uris
        or [f"mission://{study_id}/reproducibility/projection"],
    }
    return {
        family: {
            "status": "projection_ref_chain",
            "refs": _audit_refs(family=family, refs=refs_by_family.get(family, [])),
        }
        for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES
    }


def _audit_refs(*, family: str, refs: list[object]) -> list[dict[str, str]]:
    clean_refs = _dedupe_texts(refs)
    if not clean_refs:
        clean_refs = [f"mission://audit-pack/{family}/missing"]
    return [
        {
            "ref_id": f"{family}::{index}",
            "ref_kind": _ref_kind(ref),
            "uri": ref,
        }
        for index, ref in enumerate(clean_refs, start=1)
    ]


def _artifact_delta_refs_for_transaction(
    *,
    artifact_delta_ledger: list[dict[str, Any]],
    study_id: str,
) -> list[dict[str, str]]:
    refs: list[dict[str, str]] = []
    for index, delta in enumerate(artifact_delta_ledger, start=1):
        uri = _non_empty_text(delta.get("artifact_ref"))
        if not uri:
            continue
        refs.append(
            {
                "ref_id": _non_empty_text(delta.get("delta_id")) or f"artifact_delta::{index}",
                "ref_kind": _non_empty_text(delta.get("delta_kind")) or "artifact_delta",
                "uri": uri,
            }
        )
    return refs or [
        {
            "ref_id": "artifact_delta::missing",
            "ref_kind": "missing_artifact_delta",
            "uri": f"mission://{study_id}/artifact-delta/missing",
        }
    ]


def _paper_audit_pack_refs(audit_pack: Mapping[str, Any]) -> dict[str, list[dict[str, str]]]:
    refs_by_family: dict[str, list[dict[str, str]]] = {}
    for family in REQUIRED_PAPER_AUDIT_PACK_FAMILIES:
        family_payload = _mapping(audit_pack.get(family))
        refs = [
            {
                "ref_id": _non_empty_text(ref.get("ref_id")) or f"{family}::{index}",
                "ref_kind": _non_empty_text(ref.get("ref_kind")) or "artifact_ref",
                "uri": _non_empty_text(ref.get("uri")) or f"mission://audit-pack/{family}/missing",
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


def _stage_id(
    *,
    progress: Mapping[str, Any],
    mission_state: str,
    current_objective: Mapping[str, Any],
) -> str:
    raw = _first_text(
        progress.get("paper_stage"),
        progress.get("current_stage"),
        current_objective.get("objective"),
        current_objective.get("action_type"),
        mission_state,
    ) or "paper_mission_projection_stage"
    return _slug(raw).replace("-", "_")


def _materialized_transaction_stage_id(mission: Mapping[str, Any]) -> str | None:
    readback = _mapping(mission.get("one_shot_migration_readback"))
    if not readback:
        return None
    current_mission = _mapping(readback.get("current_mission"))
    required_output = _mapping(readback.get("required_output"))
    return _first_text(
        current_mission.get("objective_kind"),
        required_output.get("objective_kind"),
        current_mission.get("objective_id"),
    )


def _next_stage_id(*, stage_id: str) -> str:
    if stage_id == "gate_clearing_claim_evidence_repair":
        return "publication_gate_replay"
    if stage_id == "medical_prose_write_repair_publication_gate_replay":
        return "publication_quality_recheck"
    return f"{stage_id}::next"


def _transaction_state(transaction: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(transaction.get("stage_terminal_decision"))
    route = _mapping(transaction.get("opl_route_command"))
    boundary = _mapping(transaction.get("authority_boundary"))
    return _compact(
        {
            "transaction_id": _non_empty_text(transaction.get("transaction_id")),
            "contract_ref": PAPER_MISSION_TRANSACTION_CONTRACT_REF,
            "validator": PAPER_MISSION_TRANSACTION_VALIDATOR,
            "decision_kind": _non_empty_text(decision.get("decision_kind")),
            "route_command_kind": _non_empty_text(route.get("command_kind")),
            "mas_authority_owner": _non_empty_text(boundary.get("mas_authority_owner")),
            "runtime_owner": _non_empty_text(boundary.get("runtime_owner")),
            "projection_only": True,
            "writes_authority_surface": boundary.get("writes_authority_surface"),
            "writes_runtime_queue": boundary.get("writes_runtime_queue"),
            "writes_provider_attempt": boundary.get("writes_provider_attempt"),
        }
    )


def _source_refs(progress: Mapping[str, Any]) -> list[dict[str, Any]]:
    refs = _mapping(progress.get("refs"))
    result: list[dict[str, Any]] = []
    for key, value in refs.items():
        if text := _non_empty_text(value):
            result.append({"ref_id": str(key), "ref_kind": str(key), "uri": text})
    for ref in _text_list(progress.get("source_refs")):
        result.append({"ref_id": f"source::{len(result) + 1}", "ref_kind": "source_ref", "uri": ref})
    return result


def _authority_touchpoints(*, platform_diagnostics: Mapping[str, Any]) -> list[dict[str, Any]]:
    result = [
        {
            "touchpoint_id": "touchpoint::mas-authority-kernel",
            "owner": "MedAutoScience",
            "surface": "MAS Authority Kernel",
            "status": "not_touched",
        },
        {
            "touchpoint_id": "touchpoint::opl-runtime-readback",
            "owner": "one-person-lab",
            "surface": "OPL runtime/readback",
            "status": "read_only" if _diagnostic_count(platform_diagnostics) > 0 else "not_touched",
        },
    ]
    return result


def _forbidden_write_guard() -> dict[str, Any]:
    return {
        "blocked_paths": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "current_package",
            "runtime queue/provider attempts",
            "/Users/gaofeng/workspace/Yang/**",
        ],
        "forbidden_claims": [
            "publication_ready",
            "current_package",
            "owner_receipt_written",
        ],
        "candidate_writes_authority": False,
    }


def _consume_result(
    *,
    mission_state: str,
    next_owner_or_human_decision: Mapping[str, Any],
) -> dict[str, Any]:
    if mission_state == "consumed":
        return {"status": "accepted"}
    if mission_state == "route_back":
        return {"status": "route_back"}
    if mission_state == "stable_blocker":
        result = {"status": "typed_blocker"}
        if ref := _non_empty_text(next_owner_or_human_decision.get("typed_blocker_ref")):
            result["ref"] = ref
        return result
    if mission_state == "waiting_human_decision":
        return {"status": "human_gate"}
    return {"status": "not_consumed"}


def _platform_diagnostics(
    *,
    platform_delta: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> dict[str, Any]:
    diagnostic_refs = _diagnostic_refs(progress)
    return {
        "count": _delta_count(platform_delta),
        "sources": _dedupe_texts(
            [
                *_text_list(platform_delta.get("sources")),
                *_diagnostic_sources(progress),
            ]
        ),
        "refs": diagnostic_refs,
        "classification": "diagnostics_only" if _delta_count(platform_delta) or diagnostic_refs else "none",
        "folded_surfaces": list(PLATFORM_DIAGNOSTIC_TERMS),
        "counts_as_paper_progress": False,
        "repair_lane_required_for_platform_claims": (_delta_count(platform_delta) or len(diagnostic_refs)) > 0,
    }


def _diagnostic_sources(progress: Mapping[str, Any]) -> list[str]:
    refs = _mapping(progress.get("refs"))
    sources: list[str] = []
    if _non_empty_text(refs.get("domain_health_diagnostic")):
        sources.append("refs.domain_health_diagnostic")
    for key in (
        "runtime_health_snapshot",
        "opl_current_control_state_handoff",
        "provider_admission_candidates",
        "transition_request_candidates",
        "paper_recovery_state",
        "repair_progress_projection",
    ):
        value = progress.get(key)
        if value not in (None, "", [], {}):
            sources.append(key)
    return sources


def _diagnostic_refs(progress: Mapping[str, Any]) -> list[str]:
    refs = _mapping(progress.get("refs"))
    result = [
        _non_empty_text(refs.get("domain_health_diagnostic")),
        _non_empty_text(refs.get("progress_projection")),
    ]
    for key in (
        "diagnostic_ref",
        "domain_health_diagnostic_ref",
        "owner_route_ref",
        "dispatch_ref",
        "paper_recovery_ref",
    ):
        result.append(_non_empty_text(progress.get(key)))
    return _dedupe_texts(result)


def _owner_answer_kind(progress: Mapping[str, Any]) -> str | None:
    current_owner_delta = _mapping(progress.get("current_owner_delta"))
    if text := _non_empty_text(current_owner_delta.get("latest_owner_answer_kind")):
        return text
    if _non_empty_text(current_owner_delta.get("typed_blocker_ref")) is not None:
        return "typed_blocker"
    if _non_empty_text(current_owner_delta.get("owner_receipt_ref")) is not None:
        return "owner_receipt"
    if _non_empty_text(current_owner_delta.get("human_gate_ref")) is not None:
        return "human_gate"
    return None


def _has_current_objective(progress: Mapping[str, Any]) -> bool:
    for key in ("next_forced_delta", "current_owner_delta", "current_work_unit", "current_executable_owner_action"):
        if _mapping(progress.get(key)):
            return True
    return False


def _study_id(progress: Mapping[str, Any]) -> str:
    return _non_empty_text(progress.get("study_id")) or "unknown-study"


def _mission_id(
    *,
    study_id: str,
    objective: str,
    progress: Mapping[str, Any],
    current_objective: Mapping[str, Any],
) -> str:
    slug = _slug(objective)
    run_ref = _first_text(
        progress.get("active_run_id"),
        progress.get("current_active_run_id"),
        current_objective.get("work_unit_id"),
        progress.get("generated_at"),
        "projection",
    )
    return f"paper-mission::{study_id}::{slug}::{_slug(run_ref or 'projection')}"


def _slug(value: object) -> str:
    text = _non_empty_text(value) or "unknown"
    chars: list[str] = []
    previous_dash = False
    for char in text.lower():
        if char.isalnum():
            chars.append(char)
            previous_dash = False
        elif not previous_dash:
            chars.append("-")
            previous_dash = True
    slug = "".join(chars).strip("-")
    return slug or "unknown"


def _has_owner_answer(progress: Mapping[str, Any]) -> bool:
    if _owner_answer_kind(progress) is not None:
        return True
    current_owner_delta = _mapping(progress.get("current_owner_delta"))
    for key in ("owner_receipt_ref", "typed_blocker_ref", "human_gate_ref"):
        if _non_empty_text(current_owner_delta.get(key)) is not None:
            return True
    return False


def _delta_count(value: Mapping[str, Any]) -> int:
    number = _number(value.get("count"))
    return number or 0


def _diagnostic_count(value: Mapping[str, Any]) -> int:
    return _delta_count(value) + len(_text_list(value.get("refs")))


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _non_empty_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    text = value.strip()
    return text or None


def _first_text(*values: object) -> str | None:
    for value in values:
        if text := _non_empty_text(value):
            return text
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, Iterable) or isinstance(value, (bytes, Mapping)):
        return []
    return [text for item in value if (text := _non_empty_text(item)) is not None]


def _mapping_list(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, Iterable) or isinstance(value, (str, bytes, Mapping)):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _dedupe_texts(values: Iterable[object]) -> list[str]:
    result: list[str] = []
    for value in values:
        if text := _non_empty_text(value):
            if text not in result:
                result.append(text)
    return result


def _number(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            return int(float(text))
        except ValueError:
            return None
    return None


def _study_identity_matches(candidate: str, requested: str) -> bool:
    candidate_text = candidate.strip()
    requested_text = requested.strip()
    if not candidate_text or not requested_text:
        return False
    if candidate_text == requested_text:
        return True
    if candidate_text.lower() == requested_text.lower():
        return True
    candidate_code = _study_numeric_code(candidate_text)
    requested_code = _study_numeric_code(requested_text)
    return bool(candidate_code and requested_code and candidate_code == requested_code)


def _study_numeric_code(value: str) -> str | None:
    text = value.strip().lower()
    if text.startswith("dm"):
        text = text[2:]
    digits = []
    for char in text:
        if char.isdigit():
            digits.append(char)
            continue
        break
    if not digits:
        return None
    return f"{int(''.join(digits)):03d}"


def _ref_kind(ref: str) -> str:
    lowered = ref.lower()
    if "publication_eval" in lowered:
        return "publication_eval"
    if "controller_decision" in lowered:
        return "controller_decision"
    if "typed_blocker" in lowered or "typed-blocker" in lowered:
        return "typed_blocker"
    if "review" in lowered:
        return "review_ledger_ref"
    if "evidence" in lowered:
        return "evidence_ledger_ref"
    if lowered.startswith("mission://"):
        return "mission_ref"
    if lowered.startswith("runtime://"):
        return "runtime_ref"
    if lowered.startswith("/") or lowered.endswith(".json") or lowered.endswith(".md"):
        return "file_ref"
    return "artifact_ref"


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return {key: item for key, item in value.items() if item not in (None, "", [], {})}


__all__ = [
    "PLATFORM_DIAGNOSTIC_TERMS",
    "attach_artifact_first_mission_summary",
    "build_artifact_first_mission_summary",
]
