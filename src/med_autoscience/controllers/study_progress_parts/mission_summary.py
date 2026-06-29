from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_progress_parts.mission_summary_parts.materialized_readback import (
    _consume_result_for_consumption_ledger,
    _latest_consumption_ledger_readback,
    _latest_materialized_mission,
    _materialized_mission_summary,
    _materialized_study_root,
    _mission_state_for_consumption_ledger,
    _next_owner_decision_for_consumption_ledger,
)
from med_autoscience.paper_mission_run import (
    PaperMissionRun,
    REQUIRED_PAPER_AUDIT_PACK_FAMILIES,
)
from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
)
from med_autoscience.paper_mission_transaction import (
    PaperMissionTransaction,
    build_paper_mission_transaction,
    stage_terminal_decision_for_consume_result,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_projection,
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
    platform_diagnostics: dict[str, Any] = {}
    mission_state = _mission_state(
        latest_artifact_delta=latest_artifact_delta,
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
    effective_transaction = _mapping(paper_mission_run["paper_mission_transaction"])
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
        "opl_transition_receipt": _opl_transition_receipt(),
        "transaction_state": _transaction_state(effective_transaction),
        "mission_state": mission_state,
        "consume_candidate_status": effective_consume_candidate_status,
        "stage_closure_decision": stage_closure_decision_projection(
            readback={
                "paper_mission_transaction": effective_transaction,
                "stage_terminal_decision": _mapping(
                    effective_transaction.get("stage_terminal_decision")
                ),
                "consume_candidate_status": effective_consume_candidate_status,
                "opl_runtime_readback_status": "not_requested_from_study_progress",
            },
            consumption_ledger_readback=consumption_ledger_readback,
        ),
        "current_objective": current_objective,
        "latest_artifact_delta": {
            **latest_artifact_delta,
            "artifact_delta_ledger": artifact_delta_ledger,
        },
        "next_owner_or_human_decision": next_owner_or_human_decision,
        "default_progress_metric": "paper_artifact_delta",
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
            "legacy_projection_accepted": False,
        },
    }
    summary["paper_mission_run"] = _paper_mission_run_with_stage_closure_readback(
        paper_mission_run=summary["paper_mission_run"],
        stage_closure_decision=summary["stage_closure_decision"],
    )
    summary["status"] = mission_state
    return summary


def attach_artifact_first_mission_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    summary = build_artifact_first_mission_summary(updated)
    updated["artifact_first_mission_summary"] = summary
    updated["mission_state"] = summary["mission_state"]
    if "consume_candidate_status" in summary:
        updated["consume_candidate_status"] = summary["consume_candidate_status"]
    updated["stage_closure_decision"] = summary["stage_closure_decision"]
    updated["stage_closure_decision_ref"] = summary["stage_closure_decision"].get(
        "decision_ref"
    )
    updated["stage_closure_outcome"] = _mapping(
        summary["stage_closure_decision"].get("outcome")
    ).get("kind")
    updated["paper_mission_run"] = summary["paper_mission_run"]
    updated["current_objective"] = summary["current_objective"]
    updated["latest_artifact_delta"] = summary["latest_artifact_delta"]
    updated["next_owner_or_human_decision"] = summary["next_owner_or_human_decision"]
    updated["paper_mission_transaction"] = summary["paper_mission_transaction"]
    updated["stage_terminal_decision"] = summary["stage_terminal_decision"]
    updated["opl_route_command"] = summary["opl_route_command"]
    updated["opl_runtime_carrier"] = summary["opl_runtime_carrier"]
    updated["opl_transition_receipt"] = summary["opl_transition_receipt"]
    updated["transaction_state"] = summary["transaction_state"]
    updated.update(_top_level_stage_closure_projection(updated))
    updated.update(_top_level_current_package_projection(updated))
    return updated


def _opl_transition_receipt() -> dict[str, Any]:
    return {
        "surface_kind": "opl_transition_receipt",
        "status": "not_requested_from_study_progress",
        "role": "transport_receipt_only",
        "can_change_stage_terminal_decision": False,
        "can_select_next_owner": False,
    }


def _mission_state(
    *,
    latest_artifact_delta: Mapping[str, Any],
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
    return "planned"


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


def _paper_mission_run_with_stage_closure_readback(
    *,
    paper_mission_run: Mapping[str, Any],
    stage_closure_decision: Mapping[str, Any],
) -> dict[str, Any]:
    decision = _mapping(stage_closure_decision)
    stage_closure_readback = _compact(
        {
            "projection_status": _non_empty_text(decision.get("projection_status")),
            "decision_ref": _non_empty_text(decision.get("decision_ref")),
            "outcome": _mapping(decision.get("outcome")) or None,
            "outcome_kind": _non_empty_text(decision.get("outcome_kind")),
            "repair_budget": _mapping(decision.get("repair_budget")) or None,
            "package_kind": _non_empty_text(decision.get("package_kind")),
            "known_blockers": _text_list(decision.get("known_blockers")),
        }
    )
    if not stage_closure_readback:
        return dict(paper_mission_run)
    return {
        **dict(paper_mission_run),
        "stage_closure_readback": stage_closure_readback,
        "stage_closure_decision": decision,
        "stage_closure_decision_ref": stage_closure_readback.get("decision_ref"),
        "stage_closure_outcome": stage_closure_readback.get("outcome_kind")
        or _mapping(stage_closure_readback.get("outcome")).get("kind"),
    }


def _top_level_stage_closure_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("stage_closure_decision"))
    outcome = _mapping(decision.get("outcome"))
    repair_budget = _stage_closure_repair_budget(payload)
    return {
        "repair_budget": repair_budget or None,
        "stage_closure": _compact(
            {
                "projection_status": _non_empty_text(decision.get("projection_status")),
                "decision_ref": _non_empty_text(decision.get("decision_ref")),
                "outcome": outcome or None,
                "outcome_kind": _non_empty_text(decision.get("outcome_kind"))
                or _non_empty_text(outcome.get("kind")),
                "next_transition": _non_empty_text(
                    _mapping(outcome.get("next_transition")).get("transition_kind")
                )
                or _non_empty_text(outcome.get("next_action")),
                "package_kind": _non_empty_text(decision.get("package_kind")),
                "known_blockers": _text_list(decision.get("known_blockers")),
                "repair_budget": repair_budget or None,
            }
        )
        or None,
    }


def _stage_closure_repair_budget(payload: Mapping[str, Any]) -> dict[str, Any]:
    decision = _mapping(payload.get("stage_closure_decision"))
    candidates = (
        _mapping(decision.get("repair_budget")),
        _mapping(_mapping(payload.get("quality_repair_batch_followthrough")).get("repair_budget")),
        _mapping(_mapping(payload.get("gate_clearing_batch_followthrough")).get("repair_budget")),
        _mapping(payload.get("route_back_budget")),
    )
    for candidate in candidates:
        budget = _normalize_repair_budget(candidate)
        if budget:
            return budget
    return {}


def _normalize_repair_budget(value: Mapping[str, Any]) -> dict[str, Any]:
    budget = _mapping(value)
    max_count = _int_value(
        budget.get("repair_budget_max")
        or budget.get("max_attempts")
        or budget.get("max_opl_redrives")
    )
    attempt_count = _int_value(
        budget.get("repair_attempt_count")
        or budget.get("attempt_count")
        or budget.get("next_observed_count")
    )
    status = _non_empty_text(budget.get("repair_budget_status"))
    if status is None:
        if budget.get("budget_exhausted") is True:
            status = "exhausted"
        elif max_count is not None and attempt_count is not None:
            status = "exhausted" if attempt_count >= max_count else "remaining"
    return _compact(
        {
            "repair_budget_max": max_count,
            "repair_attempt_count": attempt_count,
            "repair_budget_status": status,
            "on_exhausted": _non_empty_text(budget.get("on_exhausted"))
            or ("degraded_handoff" if status == "exhausted" else None),
        }
    )


def _int_value(value: object) -> int | None:
    try:
        return int(value) if value is not None and str(value).strip() else None
    except (TypeError, ValueError):
        return None


def _top_level_current_package_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    delivery = _mapping(payload.get("delivery_inspection"))
    current_package = _mapping(delivery.get("current_package"))
    if not current_package:
        return {}
    return {"current_package": current_package}


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
    terminal_decision = stage_terminal_decision_for_consume_result(
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
            "status": "not_touched",
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
    "attach_artifact_first_mission_summary",
    "build_artifact_first_mission_summary",
]
