from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor
from med_autoscience.profiles import WorkspaceProfile

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
PAPER_STAGE_LOG_KEYS = (
    "surface_kind",
    "schema_version",
    "status",
    "stage_name",
    "current_owner",
    "problem_summary",
    "stage_goal",
    "stage_work_done",
    "paper_work_done",
    "changed_stage_surfaces",
    "changed_paper_surfaces",
    "outcome",
    "remaining_blockers",
    "duration",
    "token_usage",
    "cost",
    "usage_refs",
    "cost_refs",
    "evidence_refs",
    "research_pack_progress_summary",
    "research_evidence_pack_summary",
)
STAGE_PROGRESS_LOG_KEYS = (
    "surface_kind",
    "projection_scope",
    "attempt_count",
    "completed_attempt_count",
    "blocked_attempt_count",
    "activity_event_count",
    "runner_progress_event_count",
    "duration_observed_attempt_count",
    "missing_usage_telemetry_attempt_count",
    "temporal_attempt_count",
    "temporal_webui_ref_count",
    "temporal_visibility_readiness_statuses",
    "activity_event_ref_count",
    "attempt_refs",
    "temporal_webui_refs",
    "authority_boundary",
)
LIVE_ATTEMPT_HANDOFF_KEYS = (
    "active_run_id",
    "active_stage_attempt_id",
    "active_workflow_id",
    "running_provider_attempt",
)
OWNER_ROUTE_PROJECTION_KEYS = (
    "next_owner",
    "owner_reason",
    "failure_signature",
    "source_fingerprint",
    "source_refs",
    "allowed_actions",
    "idempotency_key",
)


def read_ai_repair_lifecycle(*, study_root: Path) -> dict[str, Any] | None:
    try:
        from med_autoscience.controllers.domain_health_diagnostic_parts import autonomy_repair

        return autonomy_repair.read_ai_repair_lifecycle(study_root=study_root)
    except Exception:
        return None


def current_status_suppresses_ai_repair_lifecycle(status_payload: Mapping[str, Any]) -> bool:
    reason = _non_empty_text(status_payload.get("reason"))
    next_route = _mapping_copy(status_payload.get("controller_work_unit_next_route"))
    return (
        reason == "controller_work_unit_evidence_adopted"
        and _non_empty_text(next_route.get("owner")) == "publication_gate"
        and next_route.get("runtime_relaunch_required") is False
    )


def current_status_publication_gate_stationary(status_payload: Mapping[str, Any]) -> bool:
    return current_status_suppresses_ai_repair_lifecycle(status_payload)


def _projection_string_items(value: object) -> set[str]:
    if isinstance(value, str):
        text = value.strip()
        return {text} if text else set()
    if not isinstance(value, list | tuple | set):
        return set()
    return {text for item in value if (text := _non_empty_text(item)) is not None}


def build_readonly_ai_repair_lifecycle_projection(
    *,
    study_root: Path,
    status_payload: Mapping[str, Any],
) -> dict[str, Any] | None:
    try:
        repair_path = autonomy_ai_doctor.repair_actions_root(study_root=study_root) / "latest.json"
        repair_payload = _read_json_object(repair_path)
    except Exception:
        return None
    if not isinstance(repair_payload, dict) or _non_empty_text(repair_payload.get("state")) != "ready_for_repair":
        return None
    actions = repair_payload.get("actions")
    if not isinstance(actions, list):
        return None
    top_action = next((dict(item) for item in actions if isinstance(item, Mapping)), None)
    if top_action is None:
        return None
    control_plane = _mapping_copy(status_payload.get("authority_snapshot"))
    dispatch_gate = _mapping_copy(control_plane.get("dispatch_gate"))
    route_authorization = _mapping_copy(control_plane.get("route_authorization"))
    runtime_health = _mapping_copy(status_payload.get("runtime_health_snapshot"))
    blocking_reasons = {
        *_projection_string_items(control_plane.get("blocking_reasons")),
        *_projection_string_items(dispatch_gate.get("blocking_reasons")),
        *_projection_string_items(runtime_health.get("blocking_reasons")),
    }
    runtime_blocked = (
        route_authorization.get("runtime_recovery_allowed") is False
        or _non_empty_text(dispatch_gate.get("state")) == "blocked"
        or "runtime_recovery_retry_budget_exhausted" in blocking_reasons
        or _non_empty_text(runtime_health.get("attempt_state")) == "escalated"
        or runtime_health.get("retry_budget_remaining") == 0
    )
    if runtime_blocked:
        blocked_reason = "runtime_recovery_not_authorized"
        next_owner = "external_supervisor"
        external_supervisor_required = True
        state = "external_supervisor_required"
    else:
        blocked_reason = "controller_repair_authorization_missing"
        next_owner = "mas_controller"
        external_supervisor_required = False
        state = "blocked"
    return {
        "surface": "ai_repair_lifecycle",
        "schema_version": 1,
        "study_id": _non_empty_text(repair_payload.get("study_id"))
        or _non_empty_text(status_payload.get("study_id")),
        "quest_id": _non_empty_text(repair_payload.get("quest_id"))
        or _non_empty_text(status_payload.get("quest_id")),
        "state": state,
        "top_action": top_action,
        "auto_apply_allowed": bool(top_action.get("auto_apply_allowed")),
        "last_apply_attempt_at": None,
        "applied_at": None,
        "blocked_reason": blocked_reason,
        "next_owner": next_owner,
        "external_supervisor_required": external_supervisor_required,
        "quality_gate_relaxation_allowed": False,
        "projection_only": True,
        "refs": {"repair_action_path": str(repair_path)},
    }


def opl_current_control_state_handoff_path(*, profile: WorkspaceProfile) -> Path:
    return profile.workspace_root / "artifacts" / "supervision" / "opl_current_control_state" / "latest.json"


def _copy_mapping_keys(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in keys if key in value}


def _first_present_mapping_value(mappings: tuple[Mapping[str, Any], ...], key: str) -> Any:
    for item in mappings:
        if key in item:
            return item[key]
    return None


def _string_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return [
        text
        for item in value
        if (text := _non_empty_text(item)) is not None
    ]


def _stage_log_mapping(value: object) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in PAPER_STAGE_LOG_KEYS if key in value}


def _stage_progress_log_mapping(value: object) -> dict[str, Any]:
    return _copy_mapping_keys(value, STAGE_PROGRESS_LOG_KEYS)


def _observability_mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _owner_route_projection(value: object) -> dict[str, Any]:
    return _copy_mapping_keys(value, OWNER_ROUTE_PROJECTION_KEYS)


def _number_value(value: object) -> int | float | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int | float):
        return value
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        try:
            parsed = float(text)
        except ValueError:
            return None
        return int(parsed) if parsed.is_integer() else parsed
    return None


def _first_number_value(*values: object) -> int | float | None:
    for value in values:
        number = _number_value(value)
        if number is not None:
            return number
    return None


def _duration_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    duration = _observability_mapping(value.get("duration"))
    if duration:
        return duration
    seconds = _first_number_value(
        value.get("duration_seconds"),
        value.get("elapsed_seconds"),
        value.get("runtime_duration_seconds"),
    )
    return {"seconds": seconds} if seconds is not None else {}


def _token_usage_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    for key in ("token_usage", "usage", "tokenUsage"):
        usage = _observability_mapping(value.get(key))
        if usage:
            return usage
    return {}


def _cost_observability(value: Mapping[str, Any]) -> dict[str, Any]:
    cost = _observability_mapping(value.get("cost"))
    if cost:
        return cost
    usd = _first_number_value(value.get("cost_usd"), value.get("usd_cost"))
    return {"usd": usd} if usd is not None else {}


def _refs_from_unknown(value: object) -> list[str]:
    if isinstance(value, Mapping):
        return [
            text
            for candidate in (
                value.get("ref"),
                value.get("ref_id"),
                value.get("path"),
                value.get("uri"),
            )
            if (text := _non_empty_text(candidate)) is not None
        ]
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list | tuple | set):
        return []
    refs: list[str] = []
    for item in value:
        refs.extend(_refs_from_unknown(item))
    return refs


def _unique_strings(values: list[str]) -> list[str]:
    result: list[str] = []
    for value in values:
        text = value.strip()
        if text and text not in result:
            result.append(text)
    return result


def _usage_refs(value: Mapping[str, Any]) -> list[str]:
    token_usage = _observability_mapping(value.get("token_usage"))
    usage = _observability_mapping(value.get("usage"))
    return _unique_strings(
        [
            *_refs_from_unknown(value.get("usage_ref")),
            *_refs_from_unknown(value.get("usage_refs")),
            *_refs_from_unknown(value.get("token_usage_ref")),
            *_refs_from_unknown(value.get("token_usage_refs")),
            *_refs_from_unknown(token_usage.get("source_refs")),
            *_refs_from_unknown(usage.get("source_refs")),
        ]
    )


def _cost_refs(value: Mapping[str, Any]) -> list[str]:
    cost = _observability_mapping(value.get("cost"))
    return _unique_strings(
        [
            *_refs_from_unknown(value.get("cost_ref")),
            *_refs_from_unknown(value.get("cost_refs")),
            *_refs_from_unknown(cost.get("source_refs")),
        ]
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
        if not observed
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
    return {
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
        "status": _non_empty_text(execution.get("execution_status")) or _non_empty_text(execution.get("status")),
        "paper_stage_log": paper_stage_log,
        **_terminal_stage_log_observability(execution),
        "closeout_refs": _string_list(execution.get("closeout_refs")),
        "authority_boundary": _terminal_stage_log_authority_boundary(),
    }


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
    return {
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


def _opl_current_control_state_mode_fields(payload: Mapping[str, Any]) -> dict[str, Any]:
    scheduler_contract = _mapping_copy(payload.get("scheduler_contract"))
    developer_supervisor = _mapping_copy(payload.get("developer_supervisor"))
    developer_supervisor_mode = _mapping_copy(payload.get("developer_supervisor_mode"))
    supervisor_mode = _mapping_copy(payload.get("supervisor_mode"))
    sources = (developer_supervisor, developer_supervisor_mode, supervisor_mode, scheduler_contract, payload)
    projection: dict[str, Any] = {}
    text_fields = (
        "mode",
        "mode_label",
        "scheduler_owner",
    )
    for key in text_fields:
        text = _non_empty_text(_first_present_mapping_value(sources, key))
        if text is not None:
            projection[key] = text
    for key in ("codex_app_heartbeat_required", "safe_actions_enabled", "repo_level_repair_authority"):
        for source in sources:
            if key in source:
                projection[key] = bool(source[key])
                break
    github_user_gate = _first_present_mapping_value(sources, "github_user_gate")
    if isinstance(github_user_gate, Mapping):
        projection["github_user_gate"] = dict(github_user_gate)
    else:
        text = _non_empty_text(github_user_gate)
        if text is not None:
            projection["github_user_gate"] = text
    authority_gate = _first_present_mapping_value(sources, "authority_gate")
    if isinstance(authority_gate, Mapping):
        projection["authority_gate"] = dict(authority_gate)
    else:
        text = _non_empty_text(authority_gate)
        if text is not None:
            projection["authority_gate"] = text
    if "safe_actions_enabled" not in projection and "apply_safe_actions" in payload:
        projection["safe_actions_enabled"] = bool(payload.get("apply_safe_actions"))
    return projection


def opl_current_control_state_study_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> dict[str, Any] | None:
    handoff_path = opl_current_control_state_handoff_path(profile=profile)
    payload = _read_json_object(handoff_path)
    if payload is None:
        return None
    matching = None
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            matching = dict(item)
            break
    if matching is None:
        return None
    action_queue = [
        _copy_mapping_keys(
            item,
            (
                "action_type",
                "summary",
                "status",
                "owner",
                "surface",
                "action_id",
                "fingerprint",
                "queue_age_hours",
                "queued_first_seen_at",
                "repeat_fingerprint",
                "next_work_unit",
                "controller_work_unit_id",
                "work_unit_id",
                "source_eval_id",
                "source_fingerprint",
                "owner_pickup",
                "consumption",
            ),
        )
        for item in matching.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    why_not_applied = _string_list(matching.get("why_not_applied"))
    latest_terminal_stage_log = _latest_terminal_stage_log_projection(
        profile=profile,
        study_id=study_id,
    )
    matching_terminal_stage_log = _observability_mapping(matching.get("latest_terminal_stage_log"))
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(payload.get("generated_at")),
        "study_id": study_id,
        "quest_status": _non_empty_text(matching.get("quest_status")),
        "active_run_id": _non_empty_text(matching.get("active_run_id")),
        "active_stage_attempt_id": _non_empty_text(matching.get("active_stage_attempt_id")),
        "active_workflow_id": _non_empty_text(matching.get("active_workflow_id")),
        "running_provider_attempt": (
            bool(matching.get("running_provider_attempt"))
            if "running_provider_attempt" in matching
            else False
        ),
        "runtime_health": _copy_mapping_keys(
            matching.get("runtime_health"),
            ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
        ),
        "artifact_delta": _copy_mapping_keys(
            matching.get("artifact_delta"),
            ("status", "summary", "latest_artifact_at", "latest_meaningful_delta_at"),
        ),
        "gate_specificity": _copy_mapping_keys(
            matching.get("gate_specificity"),
            ("status", "summary", "blocked_reason", "required_action"),
        ),
        "ai_reviewer_status": _copy_mapping_keys(
            matching.get("ai_reviewer_status"),
            ("status", "summary", "owner", "trace_complete", "blocked_reason"),
        ),
        "stage_progress_log": _stage_progress_log_mapping(matching.get("stage_progress_log")),
        "owner_route": _owner_route_projection(matching.get("owner_route")),
        "queue_slo": _copy_mapping_keys(
            matching.get("queue_slo"),
            (
                "max_queue_age_hours",
                "owner_pickup_overdue_count",
                "developer_supervisor_attention_required_count",
            ),
        ),
        "owner_pickup_overdue": bool(matching.get("owner_pickup_overdue")),
        "developer_supervisor_attention_required": bool(
            matching.get("developer_supervisor_attention_required")
        ),
        "action_queue": [item for item in action_queue if item],
        "why_not_applied": why_not_applied,
        "next_owner": _non_empty_text(matching.get("next_owner")),
        "external_supervisor_required": bool(matching.get("external_supervisor_required")),
        "blocked_reason": _non_empty_text(matching.get("blocked_reason")),
    }
    if latest_terminal_stage_log is not None:
        projection["latest_terminal_stage_log"] = latest_terminal_stage_log
    elif matching_terminal_stage_log:
        projection["latest_terminal_stage_log"] = matching_terminal_stage_log
    projection.update(_opl_current_control_state_mode_fields(payload))
    return projection


def opl_current_control_state_live_attempt_handoff_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    runtime_liveness_audit: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(runtime_liveness_audit.get("source")) != "opl_current_control_state_provider_attempt":
        return None
    stage_progress_log = _stage_progress_log_mapping(runtime_liveness_audit.get("stage_progress_log"))
    if not stage_progress_log:
        return None
    source_path = _non_empty_text(runtime_liveness_audit.get("handoff_path")) or str(
        opl_current_control_state_handoff_path(profile=profile)
    )
    runtime_health = _copy_mapping_keys(
        runtime_liveness_audit.get("runtime_health"),
        ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
    )
    return {
        "surface_kind": "opl_current_control_state_provider_attempt_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": _non_empty_text(runtime_liveness_audit.get("authority")) or "observability_only",
        "source_path": source_path,
        "generated_at": _non_empty_text(runtime_liveness_audit.get("handoff_generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": _non_empty_text(runtime_liveness_audit.get("active_run_id")),
        "active_stage_attempt_id": _non_empty_text(runtime_liveness_audit.get("active_stage_attempt_id")),
        "active_workflow_id": _non_empty_text(runtime_liveness_audit.get("active_workflow_id")),
        "running_provider_attempt": bool(runtime_liveness_audit.get("running_provider_attempt")),
        "runtime_health": runtime_health,
        "artifact_delta": {},
        "gate_specificity": {},
        "ai_reviewer_status": {},
        "stage_progress_log": stage_progress_log,
        "queue_slo": {},
        "owner_pickup_overdue": False,
        "developer_supervisor_attention_required": False,
        "action_queue": [],
        "why_not_applied": [],
        "next_owner": "supervisor_only/live_provider_attempt",
        "external_supervisor_required": False,
        "blocked_reason": None,
    }


def merge_live_attempt_observability_into_handoff(
    *,
    handoff: dict[str, Any] | None,
    live_attempt_handoff: dict[str, Any] | None,
) -> dict[str, Any] | None:
    if handoff is None:
        return live_attempt_handoff
    if live_attempt_handoff is None:
        return handoff
    active_run_id = _non_empty_text(handoff.get("active_run_id"))
    live_active_run_id = _non_empty_text(live_attempt_handoff.get("active_run_id"))
    if active_run_id and live_active_run_id and active_run_id != live_active_run_id:
        return handoff
    merged = dict(handoff)
    for key in LIVE_ATTEMPT_HANDOFF_KEYS:
        if key not in merged or merged.get(key) in {None, "", False}:
            if key in live_attempt_handoff:
                merged[key] = live_attempt_handoff[key]
    if not _stage_progress_log_mapping(merged.get("stage_progress_log")):
        stage_progress_log = _stage_progress_log_mapping(live_attempt_handoff.get("stage_progress_log"))
        if stage_progress_log:
            merged["stage_progress_log"] = stage_progress_log
    if not _copy_mapping_keys(merged.get("runtime_health"), ("health_status", "runtime_liveness_status")):
        runtime_health = _copy_mapping_keys(
            live_attempt_handoff.get("runtime_health"),
            ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
        )
        if runtime_health:
            merged["runtime_health"] = runtime_health
    return merged
