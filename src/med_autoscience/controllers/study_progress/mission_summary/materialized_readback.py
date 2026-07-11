from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_consumption_readback import (
    latest_paper_mission_consumption_transaction_readback,
)
from med_autoscience.controllers.paper_mission_receipt_owner_consumption import (
    latest_receipt_owner_consumption_readback,
)
from med_autoscience.controllers.paper_mission_currentness import (
    receipt_owner_consumption_superseded_by_consumption,
)
from med_autoscience.paper_mission_opl_carrier import (
    paper_mission_opl_runtime_carrier,
)
from med_autoscience.controllers.stage_closure_terminalizer import (
    stage_closure_decision_projection,
)


PAPER_MISSION_ONE_SHOT_OUTPUT_RELPATH = (
    Path("ops") / "medautoscience" / "paper_mission_one_shot_migration"
)


def _summary_helpers():
    from med_autoscience.controllers.study_progress import mission_summary

    return mission_summary


def _compact(value: Mapping[str, Any]) -> dict[str, Any]:
    return _summary_helpers()._compact(value)


def _dedupe_texts(values: Iterable[object]) -> list[str]:
    return _summary_helpers()._dedupe_texts(values)


def _delta_count(value: Mapping[str, Any]) -> int:
    return _summary_helpers()._delta_count(value)


def _first_text(*values: object) -> str | None:
    return _summary_helpers()._first_text(*values)


def _mapping(value: object) -> dict[str, Any]:
    return _summary_helpers()._mapping(value)


def _mapping_list(value: object) -> list[dict[str, Any]]:
    return _summary_helpers()._mapping_list(value)


def _non_empty_text(value: object) -> str | None:
    return _summary_helpers()._non_empty_text(value)


def _study_identity_matches(candidate: str, requested: str) -> bool:
    return _summary_helpers()._study_identity_matches(candidate, requested)


def _study_id(progress: Mapping[str, Any]) -> str:
    return _summary_helpers()._study_id(progress)


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
    return _summary_helpers()._normalize_paper_mission_run_payload(
        progress=progress,
        mission=mission,
        mission_state=mission_state,
        current_objective=current_objective,
        artifact_delta_ledger=artifact_delta_ledger,
        source_refs=source_refs,
        platform_diagnostics=platform_diagnostics,
        next_owner_or_human_decision=next_owner_or_human_decision,
    )


def _text_list(value: object) -> list[str]:
    return _summary_helpers()._text_list(value)


def _transaction_state(transaction: Mapping[str, Any]) -> dict[str, Any]:
    return _summary_helpers()._transaction_state(transaction)


def _typed_blocker_ref(default_readback: Mapping[str, Any]) -> str | None:
    return _summary_helpers()._typed_blocker_ref(default_readback)


def _owner_receipt_ref(default_readback: Mapping[str, Any]) -> str | None:
    return _summary_helpers()._owner_receipt_ref(default_readback)


def _materialized_mission_summary(
    *,
    progress: Mapping[str, Any],
    materialized_mission: Mapping[str, Any],
    enable_opl_live_probe: bool = False,
) -> dict[str, Any]:
    helpers = _summary_helpers()
    PAPER_MISSION_RUN_CONTRACT_REF = helpers.PAPER_MISSION_RUN_CONTRACT_REF
    PAPER_MISSION_RUN_VALIDATOR = helpers.PAPER_MISSION_RUN_VALIDATOR
    PAPER_MISSION_TRANSACTION_CONTRACT_REF = helpers.PAPER_MISSION_TRANSACTION_CONTRACT_REF
    PAPER_MISSION_TRANSACTION_VALIDATOR = helpers.PAPER_MISSION_TRANSACTION_VALIDATOR
    _consume_candidate_status = helpers._consume_candidate_status

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
    platform_diagnostics: dict[str, Any] = {}
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
    if consumption_ledger_readback:
        ledger_transaction = _mapping(
            consumption_ledger_readback.get("paper_mission_transaction")
        )
        ledger_mission_id = _non_empty_text(ledger_transaction.get("mission_id"))
        if ledger_mission_id:
            paper_mission_run = {
                **paper_mission_run,
                "mission_id": ledger_mission_id,
                "paper_mission_transaction": ledger_transaction,
            }
    transaction = _mapping(paper_mission_run.get("paper_mission_transaction"))
    transaction_state = _transaction_state(transaction)
    carrier = paper_mission_opl_runtime_carrier(transaction)
    live_readback = helpers._study_progress_opl_runtime_readback(
        study_root=_materialized_study_root(progress=progress),
        carrier=carrier,
        enable_opl_live_probe=enable_opl_live_probe,
    )
    runtime_readback_status = (
        _non_empty_text(live_readback.get("opl_runtime_readback_status"))
        or "not_requested_from_study_progress"
    )
    carrier_readback = _mapping(live_readback.get("opl_runtime_carrier_readback"))
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
    stage_closure_readback = _current_stage_closure_readback(
        progress=progress,
        consume_readback=consumption_ledger_readback,
    )
    receipt_owner_consumption_readback = _latest_receipt_owner_consumption_readback(
        progress=progress,
        study_id=study_id,
    )
    if receipt_owner_consumption_readback and receipt_owner_consumption_superseded_by_consumption(
        receipt_owner_consumption_readback=receipt_owner_consumption_readback,
        consumption_ledger_readback=consumption_ledger_readback,
    ):
        receipt_owner_consumption_readback = None
    if receipt_owner_consumption_readback:
        effective_consume_candidate_status = (
            _effective_consume_candidate_status_for_receipt_owner_consumption(
                fallback=effective_consume_candidate_status,
                receipt_owner_consumption_readback=receipt_owner_consumption_readback,
            )
        )
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            "paper_mission_transaction": effective_transaction,
            "stage_terminal_decision": _mapping(
                effective_transaction.get("stage_terminal_decision")
            ),
            **(
                {
                    "stage_closure_decision": receipt_owner_consumption_readback[
                        "stage_closure_decision"
                    ]
                }
                if receipt_owner_consumption_readback
                else {"stage_closure_decision": stage_closure_readback}
                if stage_closure_readback
                else {}
            ),
            "consume_candidate_status": effective_consume_candidate_status,
            "opl_runtime_readback_status": runtime_readback_status,
            **(
                {"opl_runtime_carrier_readback": carrier_readback}
                if carrier_readback
                else {}
            ),
        },
        consumption_ledger_readback=consumption_ledger_readback,
    )
    paper_mission_run = _summary_helpers()._paper_mission_run_with_stage_closure_readback(
        paper_mission_run=paper_mission_run,
        stage_closure_decision=stage_closure_decision,
    )
    receipt = helpers._opl_transition_receipt(
        progress=progress,
        consumption_ledger_readback=consumption_ledger_readback,
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
        "stage_terminal_decision": _mapping(
            effective_transaction.get("stage_terminal_decision")
        ),
        "opl_route_command": _mapping(effective_transaction.get("opl_route_command")),
        "opl_runtime_carrier": carrier,
        **({"opl_runtime_carrier_readback": carrier_readback} if carrier_readback else {}),
        "opl_runtime_readback_status": runtime_readback_status,
        **({"opl_transition_receipt": receipt} if receipt else {}),
        "transaction_state": transaction_state,
        "mission_state": mission_state,
        "current_objective": current_objective,
        "current_mission": current_mission or None,
        "consume_candidate_status": effective_consume_candidate_status,
        "stage_closure_decision": stage_closure_decision,
        "current_stage_closure_readback": stage_closure_readback or None,
        "receipt_owner_consumption_readback": (
            receipt_owner_consumption_readback or None
        ),
        "latest_artifact_delta": latest_artifact_delta,
        "next_owner_or_human_decision": next_owner_or_human_decision,
        "default_progress_metric": "paper_mission_run",
        "paper_progress_counting_policy": {
            "counts_as_paper_progress": [
                "mission_artifact_delta",
                "owner_decision_packet",
                "accepted_owner_receipt",
                "route_back",
                "human_gate",
                "stable_typed_blocker_with_recoverable_path",
            ],
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
            "legacy_projection_accepted": False,
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


def _current_stage_closure_readback(
    *,
    progress: Mapping[str, Any],
    consume_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _mapping(_mapping(consume_readback).get("stage_closure_decision")) or _mapping(
        progress.get("stage_closure_decision")
    )


def _latest_receipt_owner_consumption_readback(
    *,
    progress: Mapping[str, Any],
    study_id: str,
) -> dict[str, Any]:
    study_root = _materialized_study_root(progress=progress)
    workspace_root = _workspace_root_from_study_root(study_root)
    if workspace_root is None:
        return {}
    return latest_receipt_owner_consumption_readback(
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


def _effective_consume_candidate_status_for_receipt_owner_consumption(
    *,
    fallback: str,
    receipt_owner_consumption_readback: Mapping[str, Any],
) -> str:
    receipt = _mapping(receipt_owner_consumption_readback)
    consumption = _mapping(receipt.get("mas_receipt_consumption"))
    status = _non_empty_text(consumption.get("status"))
    if status == "owner_consumed_route_checkpoint":
        return "route_back"
    if status == "owner_consumed_typed_blocker":
        return "typed_blocker"
    outcome = _mapping(_mapping(receipt.get("stage_closure_decision")).get("outcome"))
    if (
        _non_empty_text(outcome.get("kind")) == "next_stage_transition"
        and _non_empty_text(outcome.get("transition_kind"))
        == "route_back_candidate_checkpoint"
    ):
        return "route_back"
    return fallback or "typed_blocker"


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
