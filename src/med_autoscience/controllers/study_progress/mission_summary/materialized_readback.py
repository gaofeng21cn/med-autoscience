from __future__ import annotations

from collections.abc import Iterable, Mapping
import json
from pathlib import Path
from typing import Any

from med_autoscience.paper_mission_stage_run_context import (
    paper_mission_stage_run_context,
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
) -> dict[str, Any]:
    helpers = _summary_helpers()
    PAPER_MISSION_RUN_CONTRACT_REF = helpers.PAPER_MISSION_RUN_CONTRACT_REF
    PAPER_MISSION_RUN_VALIDATOR = helpers.PAPER_MISSION_RUN_VALIDATOR
    PAPER_MISSION_TRANSACTION_CONTRACT_REF = helpers.PAPER_MISSION_TRANSACTION_CONTRACT_REF
    PAPER_MISSION_TRANSACTION_VALIDATOR = helpers.PAPER_MISSION_TRANSACTION_VALIDATOR
    _consume_candidate_status = helpers._consume_candidate_status

    mission = dict(materialized_mission)
    study_id = _non_empty_text(mission.get("study_id")) or _study_id(progress)
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
            "can_authorize_provider_attempt": False,
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
    carrier = paper_mission_stage_run_context(transaction)
    live_readback = helpers._study_progress_opl_runtime_readback(
        study_root=_materialized_study_root(progress=progress),
        carrier=carrier,
        opl_runtime_payload=_mapping(progress.get("opl_runtime_payload")),
    )
    runtime_readback_status = (
        _non_empty_text(live_readback.get("opl_stage_attempt_readback_status"))
        or "not_requested_from_study_progress"
    )
    carrier_readback = _mapping(live_readback.get("opl_stage_attempt_readback"))
    effective_transaction = transaction
    effective_consume_candidate_status = _consume_candidate_status(
        mission,
        default_readback,
    )
    stage_closure_readback = _current_stage_closure_readback(
        progress=progress,
        consume_readback=None,
    )
    stage_closure_decision = stage_closure_decision_projection(
        readback={
            "paper_mission_transaction": effective_transaction,
            "stage_terminal_decision": _mapping(
                effective_transaction.get("stage_terminal_decision")
            ),
            **(
                {"stage_closure_decision": stage_closure_readback}
                if stage_closure_readback
                else {}
            ),
            "consume_candidate_status": effective_consume_candidate_status,
            "opl_stage_attempt_readback_status": runtime_readback_status,
            **(
                {"opl_stage_attempt_readback": carrier_readback}
                if carrier_readback
                else {}
            ),
        },
    )
    paper_mission_run = _summary_helpers()._paper_mission_run_with_stage_closure_readback(
        paper_mission_run=paper_mission_run,
        stage_closure_decision=stage_closure_decision,
    )
    receipt = helpers._opl_stage_attempt_receipt(
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
        "stage_terminal_decision": _mapping(
            effective_transaction.get("stage_terminal_decision")
        ),
        "ai_route_context": _mapping(effective_transaction.get("ai_route_context")),
        "opl_stage_run_context": carrier,
        **({"opl_stage_attempt_readback": carrier_readback} if carrier_readback else {}),
        "opl_stage_attempt_readback_status": runtime_readback_status,
        **({"opl_stage_attempt_receipt": receipt} if receipt else {}),
        "transaction_state": transaction_state,
        "mission_state": mission_state,
        "current_objective": current_objective,
        "current_mission": current_mission or None,
        "consume_candidate_status": effective_consume_candidate_status,
        "stage_closure_decision": stage_closure_decision,
        "current_stage_closure_readback": stage_closure_readback or None,
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
            "source_kind": "materialized_paper_mission_run",
            "materialized_mission_ref": _non_empty_text(
                mission.get("materialized_mission_ref")
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


def _current_stage_closure_readback(
    *,
    progress: Mapping[str, Any],
    consume_readback: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return _mapping(_mapping(consume_readback).get("stage_closure_decision")) or _mapping(
        progress.get("stage_closure_decision")
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
