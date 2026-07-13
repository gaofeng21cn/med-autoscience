from __future__ import annotations

from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_progress.mission_summary.materialized_readback import (
    _current_stage_closure_readback,
    _latest_materialized_mission,
    _materialized_mission_summary,
    _materialized_study_root,
)
from med_autoscience.paper_mission_stage_run_context import paper_mission_stage_run_context
from med_autoscience.paper_mission_stage_run_readback import (
    attach_opl_stage_attempt_readback,
    paper_mission_next_action_envelope,
)
from med_autoscience.controllers.stage_closure_terminalizer import stage_closure_decision_projection
from ..codex_route_context_gate import (
    has_nonbinding_codex_route_context,
    legacy_programmatic_next_action_retirement,
)
from .receipt_projection import (
    _opl_stage_attempt_receipt,
    _summary_with_receipt_projection,
)
from .paper_mission_payload import (
    _normalize_paper_mission_run_payload,
    _paper_mission_run_payload,
    _source_refs,
    _transaction_state,
)
from .stage_closure_projection import top_level_stage_closure_projection


PAPER_MISSION_RUN_CONTRACT_VERSION = "paper-mission-run.v1"
PAPER_MISSION_RUN_CONTRACT_REF = "contracts/paper_mission_run_contract.json"
PAPER_MISSION_RUN_VALIDATOR = "med_autoscience.paper_mission_run.PaperMissionRun"
PAPER_MISSION_TRANSACTION_CONTRACT_REF = "contracts/paper_mission_transaction_contract.json"
PAPER_MISSION_TRANSACTION_VALIDATOR = "med_autoscience.paper_mission_transaction.PaperMissionTransaction"
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
PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH = Path("ops") / "medautoscience" / "paper_mission_one_shot_migration"
CANONICAL_OWNER_ACTION_AUTHORITY = "study_progress.canonical_owner_action_projection"


def build_artifact_first_mission_summary(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    progress = _mapping(payload)
    materialized_mission = _latest_materialized_mission(progress)
    if materialized_mission:
        return _summary_with_receipt_projection(
            _materialized_mission_summary(
                progress=progress,
                materialized_mission=materialized_mission,
            ),
            progress=progress,
        )
    paper_delta = _mapping(
        progress.get("paper_progress_delta")
        or progress.get("deliverable_progress_delta")
    )
    deliverable_delta = _mapping(progress.get("deliverable_progress_delta") or paper_delta)
    next_forced_delta = _mapping(progress.get("next_forced_delta"))
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
        user_visible=user_visible,
    )
    next_owner_or_human_decision = _next_owner_or_human_decision(
        next_forced_delta=next_forced_delta,
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
    carrier = paper_mission_stage_run_context(paper_mission_run["paper_mission_transaction"])
    effective_transaction = _mapping(paper_mission_run["paper_mission_transaction"])
    stage_closure_readback = _current_stage_closure_readback(
        progress=progress,
        consume_readback=None,
    )
    if stage_closure_readback:
        stage_closure_source = {"stage_closure_decision": stage_closure_readback}
    elif _mapping(progress.get("stage_closure_decision")):
        stage_closure_source = {"stage_closure_decision": progress["stage_closure_decision"]}
    else:
        stage_closure_source = {}
    live_readback = _study_progress_opl_runtime_readback(
        study_root=_materialized_study_root(progress=progress),
        carrier=carrier,
        opl_runtime_payload=_mapping(progress.get("opl_runtime_payload")),
    )
    runtime_readback_status = _non_empty_text(live_readback.get("opl_stage_attempt_readback_status")) or "not_requested_from_study_progress"
    carrier_readback = _mapping(live_readback.get("opl_stage_attempt_readback"))
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            **stage_closure_source,
            "paper_mission_transaction": effective_transaction,
            "stage_terminal_decision": _mapping(effective_transaction.get("stage_terminal_decision")),
            "consume_candidate_status": effective_consume_candidate_status,
            "opl_stage_attempt_readback_status": runtime_readback_status,
            **({"opl_stage_attempt_readback": carrier_readback} if carrier_readback else {}),
        },
    )
    next_action = paper_mission_next_action_envelope(
        transaction=effective_transaction,
        stage_terminal_decision=_mapping(effective_transaction.get("stage_terminal_decision")),
        ai_route_context=_mapping(effective_transaction.get("ai_route_context")),
        opl_stage_run_context=carrier,
        opl_route_handoff={},
        diagnostic_refs=[],
    )
    receipt = _opl_stage_attempt_receipt(
        progress=progress,
        carrier=carrier,
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
        "stage_terminal_decision": _mapping(effective_transaction.get("stage_terminal_decision")),
        "ai_route_context": _mapping(effective_transaction.get("ai_route_context")),
        "opl_stage_run_context": carrier,
        **({"opl_stage_attempt_readback": carrier_readback} if carrier_readback else {}),
        "opl_stage_attempt_readback_status": runtime_readback_status,
        "next_action": next_action,
        **({"opl_stage_attempt_receipt": receipt} if receipt else {}),
        "transaction_state": _transaction_state(effective_transaction),
        "mission_state": mission_state,
        "consume_candidate_status": effective_consume_candidate_status,
        "stage_closure_decision": stage_closure_decision,
        "current_stage_closure_readback": stage_closure_readback or None,
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
            "source_kind": "materialized_paper_mission_run",
            "legacy_projection_accepted": False,
        },
    }
    summary = _summary_with_receipt_projection(
        summary,
        progress=progress,
    )
    summary["paper_mission_run"] = _paper_mission_run_with_stage_closure_readback(
        paper_mission_run=summary["paper_mission_run"],
        stage_closure_decision=summary["stage_closure_decision"],
    )
    summary["status"] = mission_state
    return summary


def attach_artifact_first_mission_summary(
    payload: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(payload)
    existing_next_action = (
        _mapping(payload.get("next_action"))
        if has_nonbinding_codex_route_context(payload)
        else {}
    )
    summary = build_artifact_first_mission_summary(updated)
    summary_next_action = _mapping(summary.get("next_action"))
    summary_next_action_promotable = _summary_next_action_is_promotable(summary)
    next_action = (
        existing_next_action
        or (summary_next_action if summary_next_action_promotable else {})
    )
    if next_action:
        summary = {key: value for key, value in summary.items() if key != "next_action"}
        summary["route_context_ref"] = next_action.get("action_id")
        summary["next_action_projection"] = "nonbinding_codex_route_context"
    elif summary_next_action:
        summary = {key: value for key, value in summary.items() if key != "next_action"}
        summary["next_action_projection"] = (
            "suppressed_noncanonical_legacy_progress_fallback"
        )
    updated["artifact_first_mission_summary"] = summary
    updated["mission_state"] = summary["mission_state"]
    if "consume_candidate_status" in summary:
        updated["consume_candidate_status"] = summary["consume_candidate_status"]
    updated["stage_closure_decision"] = summary["stage_closure_decision"]
    updated["stage_closure_decision_ref"] = summary["stage_closure_decision"].get("decision_ref")
    updated["stage_closure_outcome"] = _mapping(summary["stage_closure_decision"].get("outcome")).get("kind")
    updated["paper_mission_run"] = summary["paper_mission_run"]
    updated["current_objective"] = summary["current_objective"]
    updated["latest_artifact_delta"] = summary["latest_artifact_delta"]
    updated["next_owner_or_human_decision"] = summary["next_owner_or_human_decision"]
    updated["paper_mission_transaction"] = summary["paper_mission_transaction"]
    updated["stage_terminal_decision"] = summary["stage_terminal_decision"]
    updated["ai_route_context"] = summary["ai_route_context"]
    updated["opl_stage_run_context"] = summary["opl_stage_run_context"]
    if "opl_stage_attempt_readback" in summary:
        updated["opl_stage_attempt_readback"] = summary["opl_stage_attempt_readback"]
    if "opl_stage_attempt_readback_status" in summary:
        updated["opl_stage_attempt_readback_status"] = summary["opl_stage_attempt_readback_status"]
    if next_action:
        updated["next_action"] = next_action
        updated.pop("canonical_next_action_source", None)
        updated["next_action_projection_role"] = "nonbinding_codex_route_context"
        updated = without_legacy_next_action_authority(updated)
    elif summary_next_action:
        updated.pop("next_action", None)
        updated.pop("canonical_next_action_source", None)
        updated = without_legacy_next_action_authority(updated)
    if "opl_stage_attempt_receipt" in summary:
        updated["opl_stage_attempt_receipt"] = summary["opl_stage_attempt_receipt"]
    else:
        updated.pop("opl_stage_attempt_receipt", None)
    updated["receipt_evidence"] = summary["receipt_evidence"]
    updated["mas_receipt_consumption"] = summary["mas_receipt_consumption"]
    updated["transaction_state"] = summary["transaction_state"]
    updated.update(top_level_stage_closure_projection(updated))
    updated.update(_top_level_current_package_projection(updated))
    return updated


def refresh_top_level_stage_closure_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    updated.update(top_level_stage_closure_projection(updated))
    return updated


def without_legacy_next_action_authority(payload: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(payload)
    current_action = _mapping(updated.get("current_executable_owner_action")) or (
        _current_executable_owner_action_from_paper_facing_action(
            updated.get("paper_facing_action")
        )
    )
    for key in (
        "current_work_unit",
        "current_executable_owner_action",
        "paper_recovery_state",
        "provider_attempt_candidates",
        "provider_attempt_pending_count",
        "provider_attempt_terminal_closeout_consumed",
        "transition_request_candidates",
        "transition_request_pending_count",
        "owner_action_admission",
        "current_execution_envelope",
        "current_execution_evidence",
        "progress_first_monitoring_summary",
    ):
        updated.pop(key, None)
    if _current_executable_owner_action_is_retained_authority(current_action):
        updated["current_executable_owner_action"] = current_action
    updated["legacy_next_action_authority_retired"] = (
        legacy_programmatic_next_action_retirement()
    )
    return updated


def _current_executable_owner_action_is_retained_authority(action: Mapping[str, Any]) -> bool:
    if _non_empty_text(action.get("authority")) == CANONICAL_OWNER_ACTION_AUTHORITY:
        return True
    return (
        _non_empty_text(action.get("surface_kind")) == "current_executable_owner_action"
        and _non_empty_text(action.get("source")) == "paper_mission_typed_blocker_resolution"
        and _non_empty_text(action.get("required_delta_kind"))
        == "typed_blocker_resolution_owner_action"
        and _non_empty_text(action.get("work_unit_id")) is not None
        and _non_empty_text(action.get("work_unit_fingerprint")) is not None
    )


def _current_executable_owner_action_from_paper_facing_action(value: object) -> dict[str, Any]:
    action = _mapping(value)
    if not (
        _non_empty_text(action.get("surface_kind")) == "paper_mission_paper_facing_action"
        and _non_empty_text(action.get("status")) == "owner_action_ready"
        and _non_empty_text(action.get("required_delta_kind"))
        == "typed_blocker_resolution_owner_action"
        and _non_empty_text(action.get("target_surface_specificity"))
        == "typed_blocker_resolution"
        and _non_empty_text(action.get("work_unit_id")) is not None
        and _non_empty_text(action.get("work_unit_fingerprint")) is not None
    ):
        return {}
    return {
        "surface_kind": "current_executable_owner_action",
        "schema_version": 1,
        "status": "ready",
        "source": "paper_mission_typed_blocker_resolution",
        "study_id": _non_empty_text(action.get("study_id")),
        "next_owner": _non_empty_text(action.get("next_owner")),
        "owner": _non_empty_text(action.get("next_owner")),
        "action_type": _non_empty_text(action.get("action_type")),
        "allowed_actions": list(action.get("allowed_actions") or []),
        "work_unit_id": _non_empty_text(action.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(action.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(action.get("work_unit_fingerprint")),
        "required_delta_kind": _non_empty_text(action.get("required_delta_kind")),
        "target_surface": _mapping(action.get("target_surface")),
        "target_surface_specificity": _non_empty_text(action.get("target_surface_specificity")),
        "paper_facing_delta": _mapping(action.get("paper_facing_delta")),
        "accepted_answer_shape": _mapping(action.get("accepted_answer_shape")),
        "route_back": _mapping(action.get("route_back")),
        "verification": _mapping(action.get("verification")),
        "owner_receipt_required_for_quality_or_ready_claim": True,
        "authority": "study_progress.current_executable_owner_action",
        "authority_boundary": _mapping(action.get("authority_boundary")),
    }


def _summary_next_action_is_promotable(summary: Mapping[str, Any]) -> bool:
    return bool(_mapping(summary.get("next_action")))


def _study_progress_opl_runtime_readback(
    *,
    study_root: Path,
    carrier: Mapping[str, Any],
    opl_runtime_payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return attach_opl_stage_attempt_readback(
        readback={"opl_stage_run_context": carrier},
        study_root=study_root,
        opl_runtime_payload=opl_runtime_payload,
    )


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


def _consume_candidate_status(mission: Mapping[str, Any], default_readback: Mapping[str, Any]) -> str:
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


def _current_objective(*, next_forced_delta: Mapping[str, Any], user_visible: Mapping[str, Any]) -> dict[str, Any]:
    target_surface = _mapping(next_forced_delta.get("target_surface"))
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    return _compact(
        {
            "objective": _first_text(
                next_forced_delta.get("required_delta_kind"),
                user_visible.get("paper_stage_summary"),
                user_visible.get("current_stage_summary"),
                "paper_mission_readback_missing",
            ),
            "work_unit_id": _first_text(next_forced_delta.get("work_unit_id")),
            "action_type": _first_text(owner_action.get("action_type")),
            "target_surface": target_surface or None,
            "acceptance_refs": _text_list(next_forced_delta.get("acceptance_refs")),
            "next_owner": _first_text(owner_action.get("next_owner")),
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


def _artifact_delta_ledger(*, latest_artifact_delta: Mapping[str, Any], study_id: str) -> list[dict[str, Any]]:
    if _delta_count(latest_artifact_delta) <= 0:
        return []
    refs = _text_list(latest_artifact_delta.get("refs"))
    if not refs:
        refs = [f"mission://{study_id}/candidate-artifact-delta"]
    result: list[dict[str, Any]] = []
    for index, ref in enumerate(refs, start=1):
        result.append({
            "delta_id": f"delta::{study_id}::{index}",
            "artifact_ref": ref,
            "delta_kind": "paper_artifact_delta",
            "status": "candidate",
        })
    return result


def _next_owner_or_human_decision(*, next_forced_delta: Mapping[str, Any], user_visible: Mapping[str, Any]) -> dict[str, Any]:
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    needs_human = bool(user_visible.get("needs_user_decision"))
    decision = {
        "kind": "human_decision" if needs_human else "owner_or_route",
        "next_owner": _first_text(owner_action.get("next_owner")),
        "human_decision_required": needs_human,
        "summary": _first_text(
            user_visible.get("physician_decision_summary"),
            user_visible.get("user_decision_summary"),
            next_forced_delta.get("reason"),
            user_visible.get("user_next"),
        ),
        "can_execute": False,
        "can_authorize_provider_attempt": False,
    }
    return _compact(decision)


def _paper_mission_run_with_stage_closure_readback(*, paper_mission_run: Mapping[str, Any], stage_closure_decision: Mapping[str, Any]) -> dict[str, Any]:
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


def _top_level_current_package_projection(payload: Mapping[str, Any]) -> dict[str, Any]:
    delivery = _mapping(payload.get("delivery_inspection"))
    current_package = _mapping(delivery.get("current_package"))
    if not current_package:
        return {}
    return {"current_package": current_package}


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


__all__ = ["attach_artifact_first_mission_summary", "build_artifact_first_mission_summary", "refresh_top_level_stage_closure_projection", "without_legacy_next_action_authority"]
