from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.missing_refs_typed_closeout import (
    is_blocked_typed_closeout,
)
from med_autoscience.profiles import WorkspaceProfile

from .opl_current_control_state_handoff_values import (
    _cost_observability,
    _cost_refs,
    _number_value,
    _observability_mapping,
    _owner_route_projection,
    _stage_log_mapping,
    _string_list,
    _duration_observability,
    _token_usage_observability,
    _usage_refs,
)
from .shared_base import _mapping_copy, _non_empty_text, _read_json_object

TERMINAL_STAGE_CLOSEOUT_ROOT_REFS = (
    Path("artifacts/supervision/consumer/default_executor_execution"),
    Path("artifacts/supervision/consumer/stage_attempt_closeouts"),
)
TERMINAL_STAGE_LOG_CLOSEOUT_SURFACES = frozenset(
    {
        "stage_attempt_closeout_packet",
        "stage_memory_closeout_packet",
        "domain_stage_closeout_packet",
    }
)
REQUIRED_USER_PROGRESS_FIELDS = (
    "stage_work_done",
    "paper_work_done",
    "changed_stage_surfaces",
    "changed_paper_surfaces",
    "progress_delta_classification",
)


def _terminal_stage_log_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    duration = _duration_observability(value)
    token_usage = _token_usage_observability(value)
    cost = _cost_observability(value)
    missing = [
        key
        for key, observed in (
            ("duration", duration),
            ("token_usage", token_usage),
            ("cost", cost),
        )
        if _observability_missing(observed)
    ]
    return {
        "observability_status": "observed" if not missing else "missing",
        "duration": duration,
        "token_usage": token_usage,
        "cost": cost,
        "usage_refs": _usage_refs(value),
        "cost_refs": _cost_refs(value),
        "missing_observability_fields": missing,
    }


def _latest_terminal_stage_log_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    study_root = profile.studies_root / study_id
    if not study_root.is_dir():
        return None
    candidates: list[dict[str, Any]] = []
    for root_ref in TERMINAL_STAGE_CLOSEOUT_ROOT_REFS:
        closeout_root = study_root / root_ref
        if not closeout_root.is_dir():
            continue
        for closeout_path in closeout_root.glob("*.json"):
            closeout = _read_json_object(closeout_path)
            candidates.extend(
                _terminal_stage_logs_from_execution_latest(
                    payload=closeout,
                    source_path=closeout_path,
                    study_id=study_id,
                )
            )
            projection = _terminal_stage_log_from_closeout(
                closeout=closeout,
                closeout_path=closeout_path,
                study_id=study_id,
            )
            if projection is not None:
                candidates.append(projection)
    if not candidates:
        return None
    candidates.sort(key=_terminal_stage_log_sort_key, reverse=True)
    return candidates[0]


def _observability_missing(value: Mapping[str, Any]) -> bool:
    if not value:
        return True
    return _non_empty_text(value.get("status")) == "missing"


def _terminal_stage_logs_from_execution_latest(
    *,
    payload: Mapping[str, Any] | None,
    source_path: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    if _non_empty_text(payload.get("surface")) != "default_executor_dispatch_execution_study_latest":
        return []
    if _non_empty_text(payload.get("study_id")) not in {None, study_id}:
        return []
    records: list[dict[str, Any]] = []
    for collection_key in ("executions", "execution_ledger"):
        collection = payload.get(collection_key)
        if not isinstance(collection, list):
            continue
        for index, item in enumerate(collection):
            if not isinstance(item, Mapping):
                continue
            projection = _terminal_stage_log_from_execution_record(
                execution=item,
                source_path=source_path,
                record_path=f"{source_path}#{collection_key}/{index}",
                study_id=study_id,
            )
            if projection is not None:
                records.append(projection)
    return records


def _terminal_stage_log_from_execution_record(
    *,
    execution: Mapping[str, Any],
    source_path: Path,
    record_path: str,
    study_id: str,
) -> dict[str, Any] | None:
    if _non_empty_text(execution.get("study_id")) not in {None, study_id}:
        return None
    paper_stage_log = (
        _stage_log_mapping(execution.get("paper_stage_log"))
        or _stage_log_mapping(execution.get("user_stage_log"))
        or _stage_log_mapping(execution.get("stage_log_summary"))
    )
    if not paper_stage_log:
        return None
    return _normalize_terminal_stage_log_progress_fields(
        {
            "surface_kind": "mas_latest_terminal_stage_log_projection",
            "read_model": "study_latest_terminal_stage_log_projection",
            "authority": "observability_only",
            "source_path": str(source_path),
            "record_path": record_path,
            "generated_at": _non_empty_text(execution.get("generated_at")),
            "study_id": study_id,
            "stage_attempt_id": _non_empty_text(execution.get("stage_attempt_id")),
            "stage_id": _non_empty_text(execution.get("stage_id")) or "domain_owner/default-executor-dispatch",
            "action_type": _non_empty_text(execution.get("action_type")),
            "status": _non_empty_text(execution.get("execution_status"))
            or _non_empty_text(execution.get("status")),
            "paper_stage_log": paper_stage_log,
            **_terminal_stage_log_observability(execution),
            "closeout_refs": _string_list(execution.get("closeout_refs")),
            "authority_boundary": _terminal_stage_log_authority_boundary(),
        }
    )


def _terminal_stage_log_from_closeout(
    *,
    closeout: Mapping[str, Any] | None,
    closeout_path: Path,
    study_id: str,
) -> dict[str, Any] | None:
    if not isinstance(closeout, Mapping):
        return None
    if _non_empty_text(closeout.get("surface_kind")) not in TERMINAL_STAGE_LOG_CLOSEOUT_SURFACES:
        return None
    if _non_empty_text(closeout.get("study_id")) not in {None, study_id}:
        return None
    paper_stage_log = (
        _stage_log_mapping(closeout.get("paper_stage_log"))
        or _stage_log_mapping(closeout.get("user_stage_log"))
        or _stage_log_mapping(closeout.get("stage_log_summary"))
    )
    if not paper_stage_log:
        return None
    return _normalize_terminal_stage_log_progress_fields(
        {
            "surface_kind": "mas_latest_terminal_stage_log_projection",
            "read_model": "study_latest_terminal_stage_log_projection",
            "authority": "observability_only",
            "source_path": str(closeout_path),
            "generated_at": _non_empty_text(closeout.get("generated_at")),
            "study_id": study_id,
            "stage_attempt_id": _non_empty_text(closeout.get("stage_attempt_id")),
            "stage_id": _non_empty_text(closeout.get("stage_id")),
            "action_type": _non_empty_text(closeout.get("action_type")),
            "status": _non_empty_text(closeout.get("status")),
            "paper_stage_log": paper_stage_log,
            **_terminal_stage_log_observability(closeout),
            "closeout_refs": _string_list(closeout.get("closeout_refs")),
            "authority_boundary": _terminal_stage_log_authority_boundary(),
        }
    )


def _normalize_terminal_stage_log_progress_fields(projection: dict[str, Any]) -> dict[str, Any]:
    paper_stage_log = _mapping_copy(projection.get("paper_stage_log"))
    missing = [
        field
        for field in REQUIRED_USER_PROGRESS_FIELDS
        if _paper_stage_log_field_missing(field, paper_stage_log)
    ]
    if not missing:
        return projection
    if missing == ["progress_delta_classification"]:
        inferred = _infer_progress_delta_classification(paper_stage_log)
        if inferred is not None:
            projection = dict(projection)
            normalized_log = dict(paper_stage_log)
            normalized_log["progress_delta_classification"] = inferred
            normalized_log["progress_delta_classification_source"] = (
                "inferred_from_changed_paper_surfaces"
                if inferred == "deliverable_progress"
                else "inferred_from_changed_stage_surfaces"
            )
            projection["diagnostic"] = "progress_delta_classification_inferred_from_changed_surfaces"
            projection["missing_user_stage_log_fields"] = missing
            projection["missing_domain_fields"] = missing
            projection["paper_stage_log"] = normalized_log
            return projection
    projection = dict(projection)
    projection["typed_blocker_reason"] = "typed_closeout_packet_required"
    projection["diagnostic"] = "user_stage_log_missing_required_progress_fields"
    projection["missing_user_stage_log_fields"] = missing
    projection["missing_domain_fields"] = missing
    projection["semantic_gap"] = _semantic_gap(missing)
    if missing == ["progress_delta_classification"]:
        return projection
    normalized_log = dict(paper_stage_log)
    normalized_log["outcome"] = "typed_blocker"
    normalized_log["remaining_blockers"] = ["typed_closeout_packet_required"]
    projection["status"] = "typed_blocker"
    projection["paper_stage_log"] = normalized_log
    return projection


def _semantic_gap(missing: list[str]) -> dict[str, Any]:
    return {
        "reason": "domain_closeout_provided_incomplete_user_stage_log",
        "missing_domain_fields": list(missing),
        "source": "paper_stage_log",
        "owner": "MedAutoScience",
    }


def _paper_stage_log_field_missing(field: str, paper_stage_log: Mapping[str, Any]) -> bool:
    if field not in paper_stage_log:
        return True
    if field in {"changed_stage_surfaces", "changed_paper_surfaces"}:
        return False
    value = paper_stage_log.get(field)
    return value in (None, "", [], {})


def _infer_progress_delta_classification(paper_stage_log: Mapping[str, Any]) -> str | None:
    if _string_list(paper_stage_log.get("changed_paper_surfaces")):
        return "deliverable_progress"
    if _string_list(paper_stage_log.get("changed_stage_surfaces")):
        return "platform_repair"
    return None


def _terminal_stage_log_authority_boundary() -> dict[str, bool]:
    return {
        "observability_only": True,
        "can_mark_live_run": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
        "can_write_paper_or_package": False,
    }


def _terminal_stage_log_sort_key(value: Mapping[str, Any]) -> tuple[str, float]:
    source_path = _non_empty_text(value.get("source_path"))
    try:
        mtime = Path(source_path).stat().st_mtime if source_path is not None else 0.0
    except OSError:
        mtime = 0.0
    return (_non_empty_text(value.get("generated_at")) or "", mtime)


def _latest_typed_default_executor_closeout_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    study_root = profile.studies_root / study_id
    if not study_root.is_dir():
        return None
    candidates: list[dict[str, Any]] = []
    for execution, receipt_ref in default_executor_execution_candidates(study_root=study_root):
        if not is_blocked_typed_closeout(execution=execution, receipt_ref=receipt_ref):
            continue
        owner_result = _observability_mapping(execution.get("owner_result"))
        blocked_reason = _non_empty_text(owner_result.get("blocked_reason"))
        if blocked_reason is None:
            continue
        source_path = study_root / receipt_ref
        candidates.append(
            {
                "surface_kind": "mas_latest_default_executor_typed_closeout_projection",
                "read_model": "study_opl_current_control_state_handoff_projection",
                "authority": "observability_only",
                "source_path": str(source_path),
                "source_mtime": _source_path_mtime(source_path),
                "receipt_ref": receipt_ref,
                "generated_at": _non_empty_text(execution.get("generated_at")),
                "study_id": study_id,
                "execution_id": _non_empty_text(execution.get("execution_id")),
                "action_type": _non_empty_text(execution.get("action_type")),
                "status": "typed_blocker",
                "blocked_reason": blocked_reason,
                "work_unit_id": _non_empty_text(
                    _observability_mapping(execution.get("owner_route")).get("work_unit_id")
                )
                or _non_empty_text(
                    _observability_mapping(
                        _observability_mapping(execution.get("owner_route")).get("source_refs")
                    ).get("work_unit_id")
                ),
                "work_unit_fingerprint": _non_empty_text(
                    _observability_mapping(execution.get("owner_route")).get("work_unit_fingerprint")
                )
                or _non_empty_text(
                    _observability_mapping(
                        _observability_mapping(execution.get("owner_route")).get("source_refs")
                    ).get("work_unit_fingerprint")
                ),
                "typed_blocker": _observability_mapping(execution.get("typed_blocker"))
                or _observability_mapping(
                    _observability_mapping(execution.get("stage_closeout")).get("typed_blocker")
                ),
                "next_owner": _non_empty_text(
                    _observability_mapping(execution.get("current_owner_route")).get("next_owner")
                ),
                "owner_route": _owner_route_projection(execution.get("current_owner_route"))
                or _owner_route_projection(execution.get("owner_route")),
                "closeout_refs": _string_list(execution.get("stage_closeout_refs")),
                "authority_boundary": _terminal_stage_log_authority_boundary(),
            }
        )
    if not candidates:
        return None
    candidates.sort(key=_typed_closeout_sort_key, reverse=True)
    return candidates[0]


def _typed_closeout_sort_key(value: Mapping[str, Any]) -> tuple[str, float]:
    return (
        _non_empty_text(value.get("generated_at")) or "",
        _number_value(value.get("source_mtime")) or 0.0,
    )


def _source_path_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _typed_closeout_supersedes_terminal(
    *,
    typed_closeout: Mapping[str, Any] | None,
    terminal_stage_log: Mapping[str, Any] | None,
) -> bool:
    typed = _observability_mapping(typed_closeout)
    if not typed:
        return False
    terminal = _observability_mapping(terminal_stage_log)
    if not terminal:
        return True
    typed_source = _non_empty_text(typed.get("source_path"))
    terminal_source = _non_empty_text(terminal.get("source_path"))
    if typed_source and terminal_source and typed_source == terminal_source:
        return True
    typed_mtime = (
        (_number_value(typed.get("source_mtime")) or _source_path_mtime(Path(typed_source)))
        if typed_source
        else 0.0
    )
    terminal_mtime = _source_path_mtime(Path(terminal_source)) if terminal_source else 0.0
    return typed_mtime >= terminal_mtime
