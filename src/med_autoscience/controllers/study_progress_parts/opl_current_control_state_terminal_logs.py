from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.controllers.domain_owner_action_dispatch_parts import execution_surfaces
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


def _terminal_stage_log_observability(
    value: Mapping[str, Any],
    *,
    paper_stage_log: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    stage_log = paper_stage_log or {}
    duration = _first_observed_observability(
        _duration_observability(value),
        _duration_observability(stage_log),
    )
    token_usage = _first_observed_observability(
        _token_usage_observability(value),
        _token_usage_observability(stage_log),
    )
    cost = _first_observed_observability(
        _cost_observability(value),
        _cost_observability(stage_log),
    )
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
        "usage_refs": _unique_strings([*_usage_refs(value), *_usage_refs(stage_log)]),
        "cost_refs": _unique_strings([*_cost_refs(value), *_cost_refs(stage_log)]),
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


def _first_observed_observability(
    primary: dict[str, Any],
    *fallbacks: dict[str, Any],
) -> dict[str, Any]:
    if not _observability_missing(primary):
        return primary
    for fallback in fallbacks:
        if not _observability_missing(fallback):
            return fallback
    return primary


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in result:
            result.append(text)
    return result


def _terminal_stage_logs_from_execution_latest(
    *,
    payload: Mapping[str, Any] | None,
    source_path: Path,
    study_id: str,
) -> list[dict[str, Any]]:
    if not isinstance(payload, Mapping):
        return []
    if _non_empty_text(payload.get("surface")) not in execution_surfaces.ACCEPTED_EXECUTION_LATEST_SURFACES:
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
    return _with_stage_log_workbench_summary(
        _normalize_terminal_stage_log_progress_fields(
            {
                "surface_kind": "mas_latest_terminal_stage_log_projection",
                "read_model": "study_latest_terminal_stage_log_projection",
                "authority": "observability_only",
                "source_path": str(source_path),
                "record_path": record_path,
                "source_mtime": _source_path_mtime(source_path),
                "generated_at": _non_empty_text(execution.get("generated_at")),
                "study_id": study_id,
                "stage_attempt_id": _non_empty_text(execution.get("stage_attempt_id")),
                "stage_id": _non_empty_text(execution.get("stage_id")) or "domain_owner/default-executor-dispatch",
                "action_type": _non_empty_text(execution.get("action_type")),
                "status": _non_empty_text(execution.get("execution_status"))
                or _non_empty_text(execution.get("status")),
                "route_outcome": _non_empty_text(execution.get("route_outcome")),
                "owner_receipt_ref": _non_empty_text(execution.get("owner_receipt_ref")),
                "typed_blocker_ref": _non_empty_text(execution.get("typed_blocker_ref")),
                "owner_receipt_refs": _string_list(execution.get("owner_receipt_refs")),
                "typed_blocker_refs": _string_list(execution.get("typed_blocker_refs")),
                "paper_stage_log": paper_stage_log,
                **_terminal_stage_log_observability(execution, paper_stage_log=paper_stage_log),
                "closeout_refs": _string_list(execution.get("closeout_refs")),
                "authority_boundary": _terminal_stage_log_authority_boundary(),
            }
        )
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
    return _with_stage_log_workbench_summary(
        _normalize_terminal_stage_log_progress_fields(
            {
                "surface_kind": "mas_latest_terminal_stage_log_projection",
                "read_model": "study_latest_terminal_stage_log_projection",
                "authority": "observability_only",
                "source_path": str(closeout_path),
                "source_mtime": _source_path_mtime(closeout_path),
                "generated_at": _non_empty_text(closeout.get("generated_at")),
                "study_id": study_id,
                "stage_attempt_id": _non_empty_text(closeout.get("stage_attempt_id")),
                "stage_id": _non_empty_text(closeout.get("stage_id")),
                "action_type": _non_empty_text(closeout.get("action_type")),
                "work_unit_id": _non_empty_text(closeout.get("work_unit_id"))
                or _non_empty_text(closeout.get("next_work_unit")),
                "work_unit_fingerprint": _non_empty_text(closeout.get("work_unit_fingerprint")),
                "action_fingerprint": _non_empty_text(closeout.get("action_fingerprint"))
                or _non_empty_text(closeout.get("work_unit_fingerprint")),
                "route_identity_key": _non_empty_text(closeout.get("route_identity_key")),
                "attempt_idempotency_key": _non_empty_text(closeout.get("attempt_idempotency_key")),
                "idempotency_key": _non_empty_text(closeout.get("idempotency_key")),
                "stage_packet_ref": _non_empty_text(closeout.get("stage_packet_ref")),
                "stage_packet_refs": _string_list(closeout.get("stage_packet_refs")),
                "status": _non_empty_text(closeout.get("status")),
                "route_outcome": _non_empty_text(closeout.get("route_outcome")),
                "owner_receipt_ref": _non_empty_text(closeout.get("owner_receipt_ref")),
                "typed_blocker_ref": _non_empty_text(closeout.get("typed_blocker_ref")),
                "owner_receipt_refs": _string_list(closeout.get("owner_receipt_refs")),
                "typed_blocker_refs": _string_list(closeout.get("typed_blocker_refs")),
                "paper_stage_log": paper_stage_log,
                **_terminal_stage_log_observability(closeout, paper_stage_log=paper_stage_log),
                "closeout_refs": _string_list(closeout.get("closeout_refs")),
                "authority_boundary": _terminal_stage_log_authority_boundary(),
            }
        )
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


def _with_stage_log_workbench_summary(projection: dict[str, Any]) -> dict[str, Any]:
    payload = dict(projection)
    paper_stage_log = _mapping_copy(payload.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(paper_stage_log.get("next_forced_delta"))
    if next_forced_delta:
        payload["next_forced_delta"] = next_forced_delta
    summary = _stage_log_workbench_summary(payload)
    if summary:
        payload["stage_log_workbench_summary"] = summary
    return payload


def _stage_log_workbench_summary(projection: Mapping[str, Any]) -> dict[str, Any]:
    paper_stage_log = _mapping_copy(projection.get("paper_stage_log"))
    if not paper_stage_log:
        return {}
    next_forced_delta = _mapping_copy(paper_stage_log.get("next_forced_delta"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    summary = {
        "surface_kind": "mas_stage_log_workbench_summary",
        "read_model": "stage_log_minimum_viability_workbench_projection",
        "schema_version": 1,
        "authority": "observability_only",
        "body_policy": "refs_only_body_free",
        "stage_attempt_id": _non_empty_text(projection.get("stage_attempt_id")),
        "stage_id": _non_empty_text(projection.get("stage_id")),
        "action_type": _non_empty_text(projection.get("action_type")),
        "status": _non_empty_text(projection.get("status")),
        "stage_goal": _field_presence_summary(paper_stage_log, "stage_goal"),
        "actual_work": _field_presence_summary(paper_stage_log, "stage_work_done"),
        "paper_delta": _delta_summary(
            delta=paper_stage_log.get("paper_progress_delta"),
            changed_surfaces=paper_stage_log.get("changed_paper_surfaces"),
            body_field=paper_stage_log.get("paper_work_done"),
        ),
        "deliverable_delta": _delta_summary(
            delta=paper_stage_log.get("deliverable_progress_delta"),
            changed_surfaces=paper_stage_log.get("changed_paper_surfaces"),
            body_field=paper_stage_log.get("paper_work_done"),
        ),
        "platform_delta": _delta_summary(
            delta=paper_stage_log.get("platform_repair_delta"),
            changed_surfaces=paper_stage_log.get("changed_stage_surfaces"),
            body_field=paper_stage_log.get("stage_work_done"),
        ),
        "observability": {
            "status": _non_empty_text(projection.get("observability_status")) or "missing",
            "duration": _observed_or_missing_status(projection.get("duration")),
            "token_usage": _observed_or_missing_status(projection.get("token_usage")),
            "cost": _observed_or_missing_status(projection.get("cost")),
            "missing_fields": _string_list(projection.get("missing_observability_fields")),
        },
        "evidence_refs": _unique_texts(
            [
                *_string_list(paper_stage_log.get("evidence_refs")),
                *_string_list(projection.get("closeout_refs")),
            ]
        ),
        "usage_refs": _unique_texts(
            [
                *_string_list(paper_stage_log.get("usage_refs")),
                *_string_list(projection.get("usage_refs")),
            ]
        ),
        "cost_refs": _unique_texts(
            [
                *_string_list(paper_stage_log.get("cost_refs")),
                *_string_list(projection.get("cost_refs")),
            ]
        ),
        "next_forced_delta": _next_forced_delta_workbench_summary(
            next_forced_delta=next_forced_delta,
            owner_action=owner_action,
        ),
        "missing_domain_fields": _string_list(projection.get("missing_domain_fields")),
        "semantic_gap": _mapping_copy(projection.get("semantic_gap")),
        "source_refs": _unique_texts(
            [
                _non_empty_text(projection.get("source_path")),
                *_string_list(projection.get("closeout_refs")),
            ]
        ),
        "authority_boundary": _stage_log_workbench_authority_boundary(),
    }
    return _stage_log_workbench_summary_payload(summary)


def _field_presence_summary(paper_stage_log: Mapping[str, Any], field: str) -> dict[str, Any]:
    value = paper_stage_log.get(field)
    refs = _field_refs(paper_stage_log, field)
    return {
        "field": field,
        "status": "missing" if _paper_stage_log_field_missing(field, paper_stage_log) else "present",
        "item_count": _item_count(value),
        "refs": refs,
        "body_included": False,
    }


def _delta_summary(
    *,
    delta: object,
    changed_surfaces: object,
    body_field: object,
) -> dict[str, Any]:
    delta_mapping = _mapping_copy(delta)
    summary = {
        "status": "present" if delta_mapping else "missing",
        "count": _number_or_none(delta_mapping.get("count")),
        "token_usage_total": _number_or_none(delta_mapping.get("token_usage_total")),
        "changed_surface_refs": _string_list(changed_surfaces),
        "work_item_count": _item_count(body_field),
        "body_included": False,
    }
    return {key: value for key, value in summary.items() if value not in (None, [], {})}


def _stage_log_workbench_summary_payload(summary: Mapping[str, Any]) -> dict[str, Any]:
    required_even_when_empty = {
        "evidence_refs",
        "usage_refs",
        "cost_refs",
        "next_forced_delta",
        "missing_domain_fields",
        "source_refs",
    }
    return {
        key: value
        for key, value in summary.items()
        if value is not None and (value not in ([], {}) or key in required_even_when_empty)
    }


def _observed_or_missing_status(value: object) -> dict[str, Any]:
    payload = _observability_mapping(value)
    if not payload:
        return {"status": "missing"}
    status = _non_empty_text(payload.get("status"))
    if status == "missing":
        return {"status": "missing", "missing_reason": _missing_reason(payload)}
    return {"status": "observed"}


def _missing_reason(value: Mapping[str, Any]) -> str | None:
    for key in (
        "missing_duration_reason",
        "missing_token_usage_reason",
        "missing_cost_reason",
        "missing_reason",
    ):
        if text := _non_empty_text(value.get(key)):
            return text
    return None


def _next_forced_delta_workbench_summary(
    *,
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
) -> dict[str, Any]:
    if not next_forced_delta and not owner_action:
        return {}
    summary = {
        "required_delta_kind": _non_empty_text(next_forced_delta.get("required_delta_kind")),
        "reason": _non_empty_text(next_forced_delta.get("reason")),
        "work_unit_id": _non_empty_text(next_forced_delta.get("work_unit_id")),
        "target_surface": _mapping_copy(next_forced_delta.get("target_surface")),
        "acceptance_refs": _string_list(next_forced_delta.get("acceptance_refs")),
        "owner_action": {
            "next_owner": _non_empty_text(owner_action.get("next_owner")),
            "action_type": _non_empty_text(owner_action.get("action_type")),
            "work_unit_id": _non_empty_text(owner_action.get("work_unit_id")),
        },
        "body_included": False,
    }
    owner_action_summary = {
        key: value
        for key, value in summary["owner_action"].items()
        if value is not None
    }
    if owner_action_summary:
        summary["owner_action"] = owner_action_summary
    else:
        summary.pop("owner_action", None)
    return {key: value for key, value in summary.items() if value not in (None, [], {})}


def _field_refs(paper_stage_log: Mapping[str, Any], field: str) -> list[str]:
    field_ref_keys = (
        f"{field}_ref",
        f"{field}_refs",
        f"{field}_source_ref",
        f"{field}_source_refs",
    )
    refs: list[str] = []
    for key in field_ref_keys:
        refs.extend(_string_list(paper_stage_log.get(key)))
    if field in {"stage_goal", "stage_work_done", "paper_work_done"}:
        refs.extend(_string_list(paper_stage_log.get("evidence_refs")))
    return _unique_texts(refs)


def _item_count(value: object) -> int:
    if isinstance(value, str):
        return 1 if value.strip() else 0
    if isinstance(value, Mapping):
        return 1 if value else 0
    if isinstance(value, list | tuple | set):
        return len(value)
    return 0 if value is None else 1


def _number_or_none(value: object) -> int | float | None:
    number = _number_value(value)
    if number is not None:
        return number
    return None


def _unique_texts(values: list[str | None]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = _non_empty_text(value)
        if text is not None and text not in result:
            result.append(text)
    return result


def _stage_log_workbench_authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "body_free": True,
        "observability_only": True,
        "can_mark_domain_ready": False,
        "can_write_paper_truth": False,
        "can_authorize_quality_verdict": False,
        "can_block_provider_admission": False,
    }


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


def _terminal_stage_log_sort_key(value: Mapping[str, Any]) -> tuple[float, str]:
    source_path = _non_empty_text(value.get("source_path"))
    mtime = _number_value(value.get("source_mtime")) or (
        _source_path_mtime(Path(source_path)) if source_path is not None else 0.0
    )
    return (mtime, _non_empty_text(value.get("generated_at")) or "")


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
        typed_blocker = _observability_mapping(execution.get("typed_blocker")) or _observability_mapping(
            _observability_mapping(execution.get("stage_closeout")).get("typed_blocker")
        )
        paper_stage_log = _observability_mapping(execution.get("paper_stage_log"))
        next_forced_delta = _observability_mapping(paper_stage_log.get("next_forced_delta"))
        next_owner_action = _observability_mapping(next_forced_delta.get("owner_action"))
        anti_loop_budget = _observability_mapping(typed_blocker.get("anti_loop_budget"))
        blocked_reason = (
            _non_empty_text(owner_result.get("blocked_reason"))
            or _non_empty_text(execution.get("blocked_reason"))
            or _non_empty_text(typed_blocker.get("blocker_type"))
            or _non_empty_text(typed_blocker.get("blocker_kind"))
            or _non_empty_text(typed_blocker.get("blocker_id"))
            or _non_empty_text(typed_blocker.get("reason"))
            or _non_empty_text(typed_blocker.get("blocked_reason"))
            or _non_empty_text(paper_stage_log.get("outcome"))
        )
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
                "stage_attempt_id": _non_empty_text(execution.get("stage_attempt_id")),
                "source_fingerprint": _non_empty_text(execution.get("source_fingerprint")),
                "idempotency_key": _non_empty_text(execution.get("idempotency_key")),
                "action_type": _non_empty_text(execution.get("action_type")),
                "status": "typed_blocker",
                "blocked_reason": blocked_reason,
                "work_unit_id": _non_empty_text(
                    next_owner_action.get("work_unit_id")
                )
                or _non_empty_text(next_forced_delta.get("work_unit_id"))
                or _non_empty_text(anti_loop_budget.get("work_unit_id"))
                or _non_empty_text(execution.get("work_unit_id"))
                or _non_empty_text(
                    _observability_mapping(execution.get("owner_route")).get("work_unit_id")
                )
                or _non_empty_text(
                    _observability_mapping(
                        _observability_mapping(execution.get("owner_route")).get("source_refs")
                    ).get("work_unit_id")
                ),
                "work_unit_fingerprint": _non_empty_text(
                    anti_loop_budget.get("work_unit_fingerprint")
                )
                or _non_empty_text(execution.get("work_unit_fingerprint"))
                or _non_empty_text(execution.get("action_fingerprint"))
                or _non_empty_text(
                    _observability_mapping(execution.get("owner_route")).get("work_unit_fingerprint")
                )
                or _non_empty_text(
                    _observability_mapping(
                        _observability_mapping(execution.get("owner_route")).get("source_refs")
                    ).get("work_unit_fingerprint")
                ),
                "action_fingerprint": _non_empty_text(execution.get("action_fingerprint"))
                or _non_empty_text(anti_loop_budget.get("work_unit_fingerprint")),
                "typed_blocker": typed_blocker,
                "next_owner": _non_empty_text(next_owner_action.get("next_owner"))
                or _non_empty_text(typed_blocker.get("required_next_owner"))
                or _non_empty_text(typed_blocker.get("owner"))
                or _non_empty_text(
                    _observability_mapping(execution.get("current_owner_route")).get("next_owner")
                ),
                "next_forced_delta": next_forced_delta,
                "paper_stage_log": paper_stage_log,
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


def _typed_closeout_sort_key(value: Mapping[str, Any]) -> tuple[float, str]:
    return (
        _number_value(value.get("source_mtime")) or 0.0,
        _non_empty_text(value.get("generated_at")) or "",
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
    if typed_source and typed_source.endswith(".closeout.json") and terminal_source and terminal_source.endswith(
        "/latest.json"
    ):
        return True
    typed_mtime = (
        (_number_value(typed.get("source_mtime")) or _source_path_mtime(Path(typed_source)))
        if typed_source
        else 0.0
    )
    terminal_mtime = (
        (_number_value(terminal.get("source_mtime")) or _source_path_mtime(Path(terminal_source)))
        if terminal_source
        else 0.0
    )
    return typed_mtime >= terminal_mtime
