from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from med_autoscience.controllers import autonomy_ai_doctor
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    OPL_RUNTIME_TERMINAL_BLOCKERS,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback,
    LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME,
    non_advancing_apply_opl_transition_readback,
    provider_admission_opl_transition_readback,
)
from med_autoscience.controllers.owner_route_reconcile_parts.opl_provider_attempts import (
    terminal_provider_attempt_closeout_for_study,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.default_executor_candidates import (
    default_executor_execution_candidates,
)
from med_autoscience.controllers.study_transition_receipt_consumption_parts.missing_refs_typed_closeout import (
    is_blocked_typed_closeout,
)
from med_autoscience.profiles import WorkspaceProfile
from med_autoscience.runtime_protocol.layout import build_workspace_runtime_layout_for_profile

from .opl_current_control_state_handoff_values import (
    _copy_mapping_keys,
    _current_control_currentness_fields,
    _first_present_mapping_value,
    _observability_mapping,
    _owner_route_projection,
    _stage_progress_log_mapping,
    _number_value,
    _strict_running_provider_attempt,
    _string_list,
    _work_unit_identity,
)
from .opl_current_control_state_handoff_identity import bind_live_attempt_to_handoff_identity
from .opl_current_control_state_terminal_logs import (
    _latest_terminal_stage_log_projection,
    _latest_typed_default_executor_closeout_projection,
    _source_path_mtime,
    _typed_closeout_supersedes_terminal,
)
from .shared_base import _mapping_copy, _non_empty_text, _read_json_object

LIVE_ATTEMPT_HANDOFF_KEYS = (
    "active_run_id",
    "active_stage_attempt_id",
    "active_workflow_id",
    "running_provider_attempt",
)
ATTEMPT_IDENTITY_KEYS = (
    "action_type",
    "work_unit_id",
    "next_work_unit",
    "work_unit_fingerprint",
    "action_fingerprint",
    "lineage_ref",
)
LIVE_ATTEMPT_SUPERSEDED_BLOCKERS = frozenset(
    {
        "blocked:unsupported_dispatch_surface",
        "live_worker_requires_worker_running",
        "managed_runtime_audit_unhealthy",
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
        "opl_execution_authorization_required",
        "opl_current_control_state.handoff_required",
        "opl_stage_attempt_admission_required",
        "provider_admission_current_control_state_required",
        "opl_stage_attempt_admission_required",
        "repair_progress_ai_reviewer_recheck_required",
        "runtime_recovery_not_authorized",
        "runtime_recovery_retry_budget_exhausted",
    }
)
LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS = frozenset(
    {
        "external_supervisor",
        "one-person-lab",
    }
)
TERMINAL_STAGE_LOG_STATUSES = frozenset(
    {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
        "typed_blocker",
    }
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
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "opl_current_control_state"
        / "latest.json"
    )


def _domain_progress_transition_command_event_log_path(*, profile: WorkspaceProfile) -> Path:
    return (
        build_workspace_runtime_layout_for_profile(profile).runtime_artifacts_root
        / "supervision"
        / "domain_progress_transition_runtime"
        / "command_event_log.jsonl"
    )



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
    latest_terminal_stage_log = _latest_terminal_stage_log_projection(
        profile=profile,
        study_id=study_id,
    )
    latest_typed_closeout = _latest_typed_default_executor_closeout_projection(
        profile=profile,
        study_id=study_id,
    )
    if payload is None:
        if latest_terminal_stage_log is None and latest_typed_closeout is None:
            return None
        return _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
        )
    matching = None
    for item in payload.get("studies") or []:
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id:
            matching = dict(item)
            break
    matching_top_level_provider_admissions = _top_level_provider_admission_candidates_for_study(
        payload,
        study_id=study_id,
    )
    matching_provider_admissions = [
        dict(item)
        for item in matching.get("provider_admission_candidates") or []
        if isinstance(item, Mapping)
    ] if matching is not None else []
    matching_top_level_transition_requests = _top_level_transition_request_candidates_for_study(
        payload,
        study_id=study_id,
    )
    matching_top_level_transition_requests = _transition_candidates_with_live_log_readback(
        profile=profile,
        candidates=matching_top_level_transition_requests,
    )
    latest_opl_terminal_closeout = _latest_opl_terminal_provider_attempt_closeout_projection(
        profile=profile,
        study_id=study_id,
        payload=payload,
        matching=matching,
        matching_top_level_provider_admissions=matching_top_level_provider_admissions,
        matching_top_level_transition_requests=matching_top_level_transition_requests,
    )
    if latest_opl_terminal_closeout is not None:
        latest_terminal_stage_log = latest_opl_terminal_closeout
    latest_terminal_consumed_readback = _latest_provider_admission_terminal_consumed_readback_for_study(
        payload,
        study_id=study_id,
    )
    if matching is None:
        if (
            latest_terminal_stage_log is None
            and latest_typed_closeout is None
            and not latest_terminal_consumed_readback
            and not matching_top_level_provider_admissions
            and not matching_top_level_transition_requests
        ):
            return None
        projection = _closeout_only_study_handoff_projection(
            handoff_path=handoff_path,
            latest_terminal_stage_log=latest_terminal_stage_log,
            latest_typed_closeout=latest_typed_closeout,
            study_id=study_id,
            payload=payload,
        )
        if matching_top_level_provider_admissions:
            projection = _apply_top_level_provider_admissions_to_handoff(
                projection,
                matching_top_level_provider_admissions,
            )
        if matching_top_level_transition_requests:
            projection = _apply_top_level_transition_requests_to_handoff(
                projection,
                matching_top_level_transition_requests,
            )
        if latest_terminal_consumed_readback:
            projection = _apply_terminal_consumed_readback_to_handoff(
                projection,
                latest_terminal_consumed_readback,
            )
        return projection
    matching = _matching_with_live_log_transition_readbacks(
        profile=profile,
        matching=matching,
    )
    action_queue = [
        {
            **_copy_mapping_keys(
                item,
                (
                    "action_type",
                    "study_id",
                    "quest_id",
                    "summary",
                    "status",
                    "owner",
                    "surface",
                    "action_id",
                    "fingerprint",
                    "action_fingerprint",
                    "work_unit_fingerprint",
                    "authority",
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
                    "route_identity_key",
                    "attempt_idempotency_key",
                    "idempotency_key",
                    "provider_admission_identity",
                    "dispatch_ref",
                    "dispatch_path",
                    "stage_packet_ref",
                    "stage_packet_refs",
                    "checkpoint_refs",
                    "source_refs",
                    "opl_domain_progress_transition_live_readback",
                    "opl_domain_progress_transition_runtime_live_readback",
                    "opl_domain_progress_transition_result",
                ),
            ),
            "source": "opl_current_control_state_action_queue",
        }
        for item in matching.get("action_queue") or []
        if isinstance(item, Mapping)
    ]
    why_not_applied = _string_list(matching.get("why_not_applied"))
    matching_terminal_stage_log = _observability_mapping(matching.get("latest_terminal_stage_log"))
    active_run_id = _non_empty_text(matching.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(matching.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(matching.get("active_workflow_id"))
    running_provider_attempt = _strict_running_provider_attempt(
        matching,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(payload.get("generated_at")),
        "study_id": study_id,
        "quest_status": _non_empty_text(matching.get("quest_status")),
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "runtime_owner": "one-person-lab" if running_provider_attempt else None,
        "provider_attempt_owner": "one-person-lab" if running_provider_attempt else None,
        "queue_owner": "one-person-lab" if running_provider_attempt else None,
        "action_type": _non_empty_text(matching.get("action_type")),
        "work_unit_id": _work_unit_identity(matching.get("work_unit_id")),
        "next_work_unit": _work_unit_identity(matching.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(matching.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(matching.get("action_fingerprint"))
        or _non_empty_text(matching.get("work_unit_fingerprint")),
        "runtime_health": _copy_mapping_keys(
            matching.get("runtime_health"),
            (
                "health_status",
                "runtime_liveness_status",
                "summary",
                "blocked_reason",
                *ATTEMPT_IDENTITY_KEYS,
            ),
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
    projection.update(_current_control_currentness_fields(matching))
    _copy_opl_transition_readback_fields(projection, matching)
    provider_admission_candidates = [
        *matching_provider_admissions,
        *matching_top_level_provider_admissions,
    ]
    if provider_admission_candidates:
        projection = _apply_top_level_provider_admissions_to_handoff(
            projection,
            provider_admission_candidates,
        )
    if matching_top_level_transition_requests:
        projection = _apply_top_level_transition_requests_to_handoff(
            projection,
            matching_top_level_transition_requests,
        )
    projection = _apply_action_queue_provider_readbacks_to_handoff(projection)
    if _typed_closeout_supersedes_terminal(
        typed_closeout=latest_typed_closeout,
        terminal_stage_log=latest_terminal_stage_log or matching_terminal_stage_log,
    ):
        typed_closeout = _observability_mapping(latest_typed_closeout)
        projection["latest_typed_default_executor_closeout"] = typed_closeout
        if _newer_typed_closeout_blocks_stale_current_control(
            typed_closeout=typed_closeout,
            projection=projection,
            handoff_path=handoff_path,
        ):
            projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
            projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
            projection = _apply_typed_default_executor_closeout_to_handoff(
                projection,
                allow_stale_identity_override=True,
            )
        elif not _handoff_has_complete_current_transition_readback(projection):
            projection["blocked_reason"] = _non_empty_text(typed_closeout.get("blocked_reason"))
            projection["next_owner"] = _non_empty_text(typed_closeout.get("next_owner")) or projection["next_owner"]
            projection = _apply_typed_default_executor_closeout_to_handoff(projection)
    if latest_terminal_stage_log is not None:
        projection["latest_terminal_stage_log"] = latest_terminal_stage_log
    elif matching_terminal_stage_log:
        projection["latest_terminal_stage_log"] = matching_terminal_stage_log
    if latest_terminal_consumed_readback:
        projection = _apply_terminal_consumed_readback_to_handoff(
            projection,
            latest_terminal_consumed_readback,
        )
    projection.update(_opl_current_control_state_mode_fields(payload))
    return _apply_matching_terminal_closeout_to_handoff(projection)


def _matching_with_live_log_transition_readbacks(
    *,
    profile: WorkspaceProfile,
    matching: Mapping[str, Any],
) -> dict[str, Any]:
    updated = dict(matching)
    for key in ("action_queue", "transition_request_candidates"):
        candidates = [dict(item) for item in updated.get(key) or [] if isinstance(item, Mapping)]
        if not candidates:
            continue
        attached = _transition_candidates_with_live_log_readback(
            profile=profile,
            candidates=candidates,
        )
        updated[key] = attached
    return updated


def _top_level_provider_admission_candidates_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in payload.get("provider_admission_candidates") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id
    ]


def _top_level_transition_request_candidates_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in payload.get("transition_request_candidates") or []
        if isinstance(item, Mapping) and _non_empty_text(item.get("study_id")) == study_id
    ]


def _transition_candidates_with_live_log_readback(
    *,
    profile: WorkspaceProfile,
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if not candidates:
        return []
    log_path = _domain_progress_transition_command_event_log_path(profile=profile)
    readbacks_by_idempotency_key = _domain_progress_transition_log_readbacks_by_idempotency_key(log_path)
    if not readbacks_by_idempotency_key:
        return [dict(candidate) for candidate in candidates]
    updated: list[dict[str, Any]] = []
    for candidate in candidates:
        item = dict(candidate)
        if candidate_opl_transition_readback(item):
            updated.append(item)
            continue
        key = _transition_request_identity_key(item)
        readback = readbacks_by_idempotency_key.get(key) if key is not None else None
        if readback is not None and provider_admission_opl_transition_readback(
            {**item, "opl_domain_progress_transition_runtime_live_readback": readback},
            require_explicit_identity=True,
        ):
            item["opl_domain_progress_transition_runtime_live_readback"] = readback
            provider_identity = _observability_mapping(item.get("provider_admission_identity"))
            provider_identity["opl_domain_progress_transition_runtime_live_readback"] = readback
            item["provider_admission_identity"] = provider_identity
        updated.append(item)
    return updated


def _transition_request_identity_key(candidate: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(candidate.get("idempotency_key"))
        or _non_empty_text(candidate.get("request_idempotency_key"))
        or _non_empty_text(candidate.get("route_identity_key"))
        or _non_empty_text(candidate.get("attempt_idempotency_key"))
        or _non_empty_text(_observability_mapping(candidate.get("source_refs")).get("attempt_idempotency_key"))
    )


def _domain_progress_transition_log_readbacks_by_idempotency_key(
    path: Path,
) -> dict[str, dict[str, Any]]:
    transactions: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return {}
    except OSError:
        return {}
    for line in lines:
        text = line.strip()
        if not text:
            continue
        try:
            entry = json.loads(text)
        except json.JSONDecodeError:
            continue
        if not isinstance(entry, Mapping):
            continue
        if _non_empty_text(entry.get("runtime_id")) != "opl_domain_progress_transition_runtime":
            continue
        idempotency_key = _non_empty_text(entry.get("idempotency_key"))
        transaction_id = _non_empty_text(entry.get("transaction_id"))
        entry_kind = _non_empty_text(entry.get("entry_kind"))
        if idempotency_key is None or transaction_id is None or entry_kind is None:
            continue
        bucket = transactions.setdefault(
            (idempotency_key, transaction_id),
            {
                "idempotency_key": idempotency_key,
                "transaction_id": transaction_id,
            },
        )
        bucket[entry_kind] = dict(entry)
    readbacks: dict[str, dict[str, Any]] = {}
    for (idempotency_key, _transaction_id), transaction in transactions.items():
        readback = _readback_from_domain_progress_transaction(transaction)
        if readback:
            readbacks[idempotency_key] = readback
    return readbacks


def _readback_from_domain_progress_transaction(transaction: Mapping[str, Any]) -> dict[str, Any]:
    command = _observability_mapping(transaction.get("command"))
    event = _observability_mapping(transaction.get("event"))
    outbox = _observability_mapping(transaction.get("outbox_item"))
    command_payload = _observability_mapping(command.get("payload"))
    event_payload = _observability_mapping(event.get("payload"))
    outbox_payload = _observability_mapping(outbox.get("payload"))
    transaction_id = _non_empty_text(transaction.get("transaction_id"))
    idempotency_key = _non_empty_text(transaction.get("idempotency_key"))
    event_id = _non_empty_text(event_payload.get("event_id")) or _non_empty_text(event.get("event_id"))
    outbox_item_id = _non_empty_text(outbox_payload.get("outbox_item_id")) or _non_empty_text(
        outbox.get("outbox_item_id")
    )
    command_id = _non_empty_text(command_payload.get("command_id")) or _non_empty_text(command.get("command_id"))
    aggregate_identity = _observability_mapping(event_payload.get("aggregate_identity")) or _observability_mapping(
        command_payload.get("aggregate_identity")
    ) or _observability_mapping(outbox_payload.get("aggregate_identity"))
    command_stage = _observability_mapping(command_payload.get("stage_run_identity"))
    event_stage = _observability_mapping(event_payload.get("stage_run_identity"))
    outbox_stage = _observability_mapping(outbox_payload.get("stage_run_identity"))
    if any(value is None for value in (transaction_id, idempotency_key, event_id, outbox_item_id, command_id)):
        return {}
    if not aggregate_identity or not command_stage or command_stage != event_stage or command_stage != outbox_stage:
        return {}
    transition_kind = _non_empty_text(event_payload.get("transition_kind")) or "StartProviderAttempt"
    outcome = _observability_mapping(event_payload.get("outcome"))
    outcome_kind = _non_empty_text(outcome.get("kind")) or (
        "non_advancing_apply_typed_blocker_ref"
        if transition_kind == "NonAdvancingApply"
        else "provider_admission_enqueued_or_blocked"
    )
    replay = {
        "surface_kind": "opl_domain_progress_transition_replay_audit",
        "runtime_id": "opl_domain_progress_transition_runtime",
        "authority": False,
        "replay_status": "replay_ready",
        "read_model_projection_consumable": True,
        "exactly_one_complete_transaction": True,
        "transaction_complete": True,
        "transition_count": 1,
        "aggregate_identity": dict(aggregate_identity),
        "aggregate_version": event.get("aggregate_version") or command.get("aggregate_version") or 1,
        "transaction_id": transaction_id,
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "idempotency_key": idempotency_key,
        "command_id": command_id,
        "command_present": True,
        "event_present": True,
        "outbox_item_present": True,
        "same_outbox_identity": True,
        "same_transaction_event_and_outbox": True,
        "same_stage_run_identity": True,
        "stage_run_identity_readback": {
            "surface_kind": "opl_domain_progress_stage_run_identity_readback",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "same_stage_run_identity": True,
            "command_stage_run_identity_present": True,
            "event_stage_run_identity_present": True,
            "outbox_stage_run_identity_present": True,
            "command_stage_run_identity": dict(command_stage),
            "event_stage_run_identity": dict(event_stage),
            "outbox_stage_run_identity": dict(outbox_stage),
            **dict(command_stage),
            "fail_closed_reason": None,
        },
        "exactly_one_outcome": {
            "surface_kind": "opl_domain_progress_exactly_one_outcome",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "selected": True,
            "exactly_one_transition": True,
            "transition_count": 1,
            "transition_kind": transition_kind,
            "outcome_kind": outcome_kind,
            "stable_outcome": outcome.get("stable_outcome") is not False,
            "non_advancing_apply": transition_kind == "NonAdvancingApply",
            "fail_closed": False,
        },
        "projection_metadata": {
            "surface_kind": "opl_domain_progress_transition_replay_projection_metadata",
            "runtime_id": "opl_domain_progress_transition_runtime",
            "authority": False,
            "projection_role": "replay_ready_complete_transaction",
            "read_model_projection_consumable": True,
            "transaction_complete": True,
            "replay_status": "replay_ready",
            "exactly_one_complete_transaction": True,
            "derived_from_event_id": event_id,
            "observed_generation": _non_empty_text(event_payload.get("source_generation"))
            or _non_empty_text(command_stage.get("source_generation")),
            "read_model_rebuild_owner": "one-person-lab",
        },
        "source_generation": _non_empty_text(event_payload.get("source_generation"))
        or _non_empty_text(command_stage.get("source_generation")),
        "expected_version": _non_empty_text(event_payload.get("expected_version"))
        or _non_empty_text(event_payload.get("source_generation"))
        or _non_empty_text(command_stage.get("source_generation")),
    }
    return candidate_opl_transition_readback({"opl_domain_progress_transition_result": replay})


def _latest_opl_terminal_provider_attempt_closeout_projection(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    payload: Mapping[str, Any],
    matching: Mapping[str, Any] | None,
    matching_top_level_provider_admissions: list[dict[str, Any]],
    matching_top_level_transition_requests: list[dict[str, Any]],
) -> dict[str, Any] | None:
    preferred_actions = _current_control_provider_admission_candidates(
        payload=payload,
        matching=matching,
        matching_top_level_provider_admissions=matching_top_level_provider_admissions,
        matching_top_level_transition_requests=matching_top_level_transition_requests,
    )
    if not preferred_actions:
        return None
    closeout = terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        timeout_seconds=8.0,
        max_inspect_count=2,
        preferred_actions=preferred_actions,
    )
    if not closeout:
        return None
    if not any(
        _terminal_closeout_matches_handoff_action(terminal=closeout, action=action)
        for action in preferred_actions
    ):
        return None
    return closeout


def refresh_handoff_with_terminal_closeout_candidates(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    handoff: Mapping[str, Any] | None,
    candidates: list[Mapping[str, Any]],
) -> dict[str, Any] | None:
    if handoff is None:
        return None
    preferred_actions = [
        dict(item)
        for item in candidates
        if isinstance(item, Mapping) and _terminal_consumption_candidate_can_anchor_terminal_probe(item)
    ]
    if not preferred_actions:
        return dict(handoff)
    closeout = terminal_provider_attempt_closeout_for_study(
        profile=profile,
        study_id=study_id,
        timeout_seconds=8.0,
        max_inspect_count=2,
        preferred_actions=preferred_actions,
    )
    if not closeout:
        closeout = _terminal_default_executor_closeout_for_preferred_actions(
            profile=profile,
            study_id=study_id,
            preferred_actions=preferred_actions,
        )
    if not closeout:
        return dict(handoff)
    if not any(
        _terminal_closeout_matches_handoff_action(terminal=closeout, action=action)
        for action in preferred_actions
    ):
        return dict(handoff)
    refreshed = {
        **dict(handoff),
        "latest_terminal_stage_log": closeout,
        "active_stage_attempt_id": _non_empty_text(closeout.get("stage_attempt_id")),
        "active_run_id": (
            f"opl-stage-attempt://{stage_attempt_id}"
            if (stage_attempt_id := _non_empty_text(closeout.get("stage_attempt_id"))) is not None
            else None
        ),
        "transition_request_pending_count": len(preferred_actions),
        "transition_request_candidates": preferred_actions,
    }
    return _apply_matching_terminal_closeout_to_handoff(refreshed)


def _terminal_default_executor_closeout_for_preferred_actions(
    *,
    profile: WorkspaceProfile,
    study_id: str,
    preferred_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    study_root = _study_root_for_default_executor_candidates(profile=profile, study_id=study_id)
    if study_root is None:
        return None
    for execution, receipt_ref in default_executor_execution_candidates(study_root=study_root):
        closeout = dict(execution)
        closeout.setdefault("receipt_ref", receipt_ref)
        closeout.setdefault("source", "mas_default_executor_closeout")
        if any(_default_executor_closeout_can_consume_preferred_action(closeout, action) for action in preferred_actions):
            return closeout
    return None


def _default_executor_closeout_can_consume_preferred_action(
    closeout: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if not _terminal_closeout_matches_handoff_action(terminal=closeout, action=action):
        return False
    if (
        provider_admission_opl_transition_readback(action)
        and _non_empty_text(closeout.get("owner_receipt_ref")) is None
    ):
        return False
    return True


def _study_root_for_default_executor_candidates(
    *,
    profile: WorkspaceProfile,
    study_id: str,
) -> Path | None:
    candidates = [
        profile.studies_root / study_id,
        build_workspace_runtime_layout_for_profile(profile).workspace_root / "studies" / study_id,
        profile.workspace_root / "studies" / study_id,
    ]
    for candidate in candidates:
        try:
            resolved = candidate.expanduser().resolve()
        except OSError:
            continue
        if resolved.exists():
            return resolved
    return candidates[0].expanduser().resolve() if candidates else None


def _current_control_provider_admission_candidates(
    *,
    payload: Mapping[str, Any],
    matching: Mapping[str, Any] | None,
    matching_top_level_provider_admissions: list[dict[str, Any]],
    matching_top_level_transition_requests: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    candidates = [
        dict(item)
        for item in matching_top_level_provider_admissions
        if isinstance(item, Mapping) and provider_admission_opl_transition_readback(item)
    ]
    candidates.extend(
        dict(item)
        for item in matching_top_level_transition_requests or []
        if isinstance(item, Mapping) and _transition_request_candidate_can_anchor_terminal_probe(item)
    )
    if isinstance(matching, Mapping):
        candidates.extend(
            dict(item)
            for item in matching.get("provider_admission_candidates") or []
            if isinstance(item, Mapping) and provider_admission_opl_transition_readback(item)
        )
        candidates.extend(
            dict(item)
            for item in matching.get("transition_request_candidates") or []
            if isinstance(item, Mapping) and _transition_request_candidate_can_anchor_terminal_probe(item)
        )
    if not candidates:
        return []
    provider_pending = int(payload.get("provider_admission_pending_count") or 0) > 0
    transition_pending = int(payload.get("transition_request_pending_count") or 0) > 0
    if isinstance(matching, Mapping):
        provider_pending = provider_pending or int(matching.get("provider_admission_pending_count") or 0) > 0
        transition_pending = transition_pending or int(matching.get("transition_request_pending_count") or 0) > 0
    return candidates if provider_pending or transition_pending else []


def _transition_request_candidate_can_anchor_terminal_probe(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return True
    if _non_empty_text(candidate.get("status")) != "transition_request_pending":
        return False
    return (
        _non_empty_text(candidate.get("action_type")) is not None
        and _work_unit_identity(candidate.get("work_unit_id")) is not None
        and (
            _non_empty_text(candidate.get("work_unit_fingerprint")) is not None
            or _non_empty_text(candidate.get("action_fingerprint")) is not None
        )
        and (
            _non_empty_text(candidate.get("attempt_idempotency_key")) is not None
            or _non_empty_text(_observability_mapping(candidate.get("source_refs")).get("attempt_idempotency_key"))
            is not None
        )
    )


def _terminal_consumption_candidate_can_anchor_terminal_probe(candidate: Mapping[str, Any]) -> bool:
    return provider_admission_opl_transition_readback(candidate) or _transition_request_candidate_can_anchor_terminal_probe(
        candidate
    )


def _apply_top_level_provider_admissions_to_handoff(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(projection)
    provider_candidates = _dedupe_provider_admission_candidates(
        [
            dict(item)
            for item in candidates
            if provider_admission_opl_transition_readback(item)
        ]
    )
    if not provider_candidates:
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        return updated
    updated["provider_admission_pending_count"] = len(provider_candidates)
    updated["provider_admission_candidates"] = provider_candidates
    current = provider_candidates[0]
    for key in ("action_type", "work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current.get(key))
        if text is not None:
            updated[key] = text
    work_unit_id = _work_unit_identity(current.get("work_unit_id"))
    if work_unit_id is not None:
        updated["work_unit_id"] = work_unit_id
    _copy_stage_packet_ref_family_to_projection(updated, current)
    if _non_empty_text(current.get("status")) == "provider_admission_pending" and provider_candidates:
        updated["blocked_reason"] = None
        updated.pop("typed_blocker", None)
    return updated


def _apply_top_level_transition_requests_to_handoff(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    if projection.get("running_provider_attempt") is True:
        request_candidates_for_running = [
            dict(item)
            for item in candidates
            if _transition_request_candidate_can_anchor_terminal_probe(item)
            and not provider_admission_opl_transition_readback(item)
        ]
        if any(_handoff_candidate_matches_projection(candidate, projection) for candidate in request_candidates_for_running):
            return _handoff_without_same_identity_pending(projection, request_candidates_for_running)
    request_candidates = [
        dict(item)
        for item in candidates
        if _transition_request_candidate_can_anchor_terminal_probe(item)
        and not provider_admission_opl_transition_readback(item)
    ]
    if not request_candidates:
        return dict(projection)
    updated = dict(projection)
    updated["transition_request_pending_count"] = len(request_candidates)
    updated["transition_request_candidates"] = request_candidates
    updated.setdefault("provider_admission_pending_count", 0)
    updated.setdefault("provider_admission_candidates", [])
    current = request_candidates[0]
    for key in ("action_type", "work_unit_fingerprint", "action_fingerprint"):
        text = _non_empty_text(current.get(key))
        if text is not None:
            updated[key] = text
    work_unit_id = _work_unit_identity(current.get("work_unit_id"))
    if work_unit_id is not None:
        updated["work_unit_id"] = work_unit_id
    _copy_stage_packet_ref_family_to_projection(updated, current)
    updated["next_owner"] = _non_empty_text(current.get("next_owner")) or updated.get("next_owner")
    updated["blocked_reason"] = _non_empty_text(current.get("blocked_reason")) or updated.get("blocked_reason")
    return updated


def _handoff_without_same_identity_pending(
    projection: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    updated = dict(projection)
    matching_identity_keys = {
        key
        for candidate in candidates
        if _handoff_candidate_matches_projection(candidate, projection)
        for key in _handoff_candidate_runtime_identity_keys(candidate)
    }
    if not matching_identity_keys:
        return updated
    provider_candidates = [
        dict(item)
        for item in updated.get("provider_admission_candidates") or []
        if not _handoff_candidate_runtime_identity_keys(item).intersection(matching_identity_keys)
    ]
    transition_candidates = [
        dict(item)
        for item in updated.get("transition_request_candidates") or []
        if not _handoff_candidate_runtime_identity_keys(item).intersection(matching_identity_keys)
    ]
    updated["provider_admission_candidates"] = provider_candidates
    updated["provider_admission_pending_count"] = len(provider_candidates)
    updated["transition_request_candidates"] = transition_candidates
    updated["transition_request_pending_count"] = len(transition_candidates)
    updated["blocked_reason"] = None
    updated["external_supervisor_required"] = False
    return updated


def _handoff_candidate_runtime_identity_keys(candidate: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(candidate) or provider_admission_opl_transition_readback(
        candidate
    )
    readback_identity = _observability_mapping(readback.get("identity"))
    stage_run_identity = _observability_mapping(readback_identity.get("stage_run_identity"))
    idempotency_readback = _observability_mapping(readback.get("idempotency_readback"))
    provider_identity = _observability_mapping(candidate.get("provider_admission_identity"))
    source_refs = _observability_mapping(candidate.get("source_refs"))
    return {
        key
        for key in (
            _transition_request_identity_key(candidate),
            _non_empty_text(candidate.get("route_identity_key")),
            _non_empty_text(candidate.get("attempt_idempotency_key")),
            _non_empty_text(candidate.get("idempotency_key")),
            _non_empty_text(provider_identity.get("route_identity_key")),
            _non_empty_text(provider_identity.get("attempt_idempotency_key")),
            _non_empty_text(provider_identity.get("idempotency_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("idempotency_key")),
            _non_empty_text(stage_run_identity.get("route_identity_key")),
            _non_empty_text(stage_run_identity.get("attempt_idempotency_key")),
            _non_empty_text(readback_identity.get("idempotency_key")),
            _non_empty_text(idempotency_readback.get("idempotency_key")),
        )
        if key is not None
    }


def _handoff_candidate_matches_projection(
    candidate: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> bool:
    for key in ("study_id", "action_type"):
        candidate_value = _non_empty_text(candidate.get(key))
        projection_value = _non_empty_text(projection.get(key))
        if candidate_value is not None and projection_value is not None and candidate_value != projection_value:
            return False
    candidate_work_unit = _work_unit_identity(candidate.get("work_unit_id")) or _work_unit_identity(
        candidate.get("next_work_unit")
    )
    projection_work_unit = _work_unit_identity(projection.get("work_unit_id")) or _work_unit_identity(
        projection.get("next_work_unit")
    )
    if candidate_work_unit is not None and projection_work_unit is not None and candidate_work_unit != projection_work_unit:
        return False
    candidate_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    projection_fingerprint = _non_empty_text(projection.get("work_unit_fingerprint")) or _non_empty_text(
        projection.get("action_fingerprint")
    )
    if (
        candidate_fingerprint is not None
        and projection_fingerprint is not None
        and candidate_fingerprint != projection_fingerprint
    ):
        return False
    for key in ("route_identity_key", "attempt_idempotency_key", "idempotency_key"):
        candidate_value = _non_empty_text(candidate.get(key))
        projection_value = _non_empty_text(projection.get(key))
        if candidate_value is not None and projection_value is not None and candidate_value == projection_value:
            return True
    return candidate_work_unit is not None and projection_work_unit is not None and candidate_work_unit == projection_work_unit


def _copy_stage_packet_ref_family_to_projection(
    projection: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    source_refs = _observability_mapping(source.get("source_refs"))
    stage_packet_ref = _non_empty_text(source.get("stage_packet_ref")) or _non_empty_text(
        source_refs.get("stage_packet_ref")
    )
    stage_packet_refs = _stage_ref_items(source.get("stage_packet_refs")) or _stage_ref_items(
        source_refs.get("stage_packet_refs")
    )
    if stage_packet_ref is not None and stage_packet_ref not in stage_packet_refs:
        stage_packet_refs.insert(0, stage_packet_ref)
    checkpoint_refs = _stage_ref_items(source.get("checkpoint_refs")) or _stage_ref_items(
        source_refs.get("checkpoint_refs")
    ) or list(stage_packet_refs)
    for key in ("dispatch_ref", "dispatch_path"):
        value = _non_empty_text(source.get(key)) or _non_empty_text(source_refs.get(key))
        if value is not None:
            projection[key] = value
    if stage_packet_ref is not None:
        projection["stage_packet_ref"] = stage_packet_ref
    if stage_packet_refs:
        projection["stage_packet_refs"] = stage_packet_refs
    if checkpoint_refs:
        projection["checkpoint_refs"] = checkpoint_refs


def _stage_ref_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    refs: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in refs:
            refs.append(text)
    return refs


def _apply_action_queue_provider_readbacks_to_handoff(
    projection: Mapping[str, Any],
) -> dict[str, Any]:
    consumed = _observability_mapping(projection.get("provider_admission_terminal_closeout_consumed"))
    if consumed:
        terminal = _terminal_stage_log_from_terminal_consumed_readback(consumed)
        action_queue = _handoff_candidate_list(projection.get("action_queue"))
        matching_actions = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=action_queue,
        )
        if matching_actions:
            projection = {
                **dict(projection),
                "action_queue": [
                    dict(item)
                    for item in action_queue
                    if item not in matching_actions
                ],
                "consumed_action_queue": [
                    {
                        **dict(item),
                        "consumption": {
                            **_observability_mapping(item.get("consumption")),
                            "state": "consumed_by_provider_admission_terminal_readback",
                            "terminal_stage_attempt_id": _non_empty_text(
                                consumed.get("terminal_stage_attempt_id")
                            )
                            or _non_empty_text(consumed.get("stage_attempt_id")),
                        },
                    }
                    for item in matching_actions
                ],
            }
    projection_readback_candidate = _provider_readback_candidate_from_projection(projection)
    action_provider_candidates = [
        dict(item)
        for item in projection.get("action_queue") or []
        if isinstance(item, Mapping) and provider_admission_opl_transition_readback(_action_with_handoff_packet_readback(item))
    ]
    if projection_readback_candidate:
        action_provider_candidates.extend(
            _bind_projection_provider_readback_to_actions(
                projection,
                readback_candidate=projection_readback_candidate,
            )
        )
    action_provider_candidates = _dedupe_provider_admission_candidates(action_provider_candidates)
    if not action_provider_candidates:
        return dict(projection)
    updated = _apply_top_level_provider_admissions_to_handoff(
        projection,
        action_provider_candidates,
    )
    provider_keys = {
        _transition_request_identity_key(candidate)
        for candidate in action_provider_candidates
        if _transition_request_identity_key(candidate) is not None
    }
    remaining_transition_requests = [
        dict(item)
        for item in updated.get("transition_request_candidates") or []
        if _transition_request_identity_key(item) not in provider_keys
    ]
    updated["transition_request_candidates"] = remaining_transition_requests
    updated["transition_request_pending_count"] = len(remaining_transition_requests)
    updated["quest_status"] = "provider_admission_pending"
    return updated


def _dedupe_provider_admission_candidates(candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, ...]] = set()
    for candidate in candidates:
        identity = tuple(sorted(_handoff_candidate_runtime_identity_keys(candidate)))
        if not identity:
            identity = tuple(
                value
                for value in (
                    _non_empty_text(candidate.get("study_id")),
                    _work_unit_identity(candidate.get("work_unit_id"))
                    or _work_unit_identity(candidate.get("next_work_unit")),
                    _non_empty_text(candidate.get("work_unit_fingerprint"))
                    or _non_empty_text(candidate.get("action_fingerprint")),
                )
                if value is not None
            )
        if identity in seen:
            continue
        seen.add(identity)
        deduped.append(candidate)
    return deduped


def _provider_readback_candidate_from_projection(projection: Mapping[str, Any]) -> dict[str, Any]:
    readback = candidate_opl_transition_readback(projection)
    if not readback:
        return {}
    outcome_kind = _non_empty_text(_observability_mapping(readback.get("exactly_one_outcome")).get("outcome_kind"))
    if outcome_kind != LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME:
        return {}
    identity = _provider_admission_identity_from_readback(readback)
    if not identity:
        return {}
    action_type = _non_empty_text(projection.get("action_type"))
    work_unit_id = _work_unit_identity(projection.get("work_unit_id")) or _work_unit_identity(
        identity.get("work_unit_id")
    )
    work_unit_fingerprint = _non_empty_text(projection.get("work_unit_fingerprint")) or _non_empty_text(
        projection.get("action_fingerprint")
    ) or _non_empty_text(identity.get("work_unit_fingerprint"))
    return {
        **identity,
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": _non_empty_text(projection.get("action_fingerprint"))
        or work_unit_fingerprint,
        "next_executable_owner": _non_empty_text(projection.get("next_owner")),
        "owner": _non_empty_text(projection.get("next_owner")),
        "status": "provider_admission_pending",
        "provider_admission_pending": True,
        "transition_request_pending": False,
        "provider_attempt_or_lease_required": True,
        "provider_admission_requires_opl_runtime_result": False,
        "opl_domain_progress_transition_runtime_live_readback": readback,
    }


def _action_with_handoff_packet_readback(action: Mapping[str, Any]) -> dict[str, Any]:
    updated = dict(action)
    handoff_packet = _observability_mapping(updated.get("handoff_packet"))
    if not handoff_packet:
        return updated
    for key in (
        "opl_domain_progress_transition_live_readback",
        "opl_domain_progress_transition_runtime_live_readback",
        "opl_domain_progress_transition_result",
        "opl_domain_progress_runtime_result",
        "opl_runtime_result",
        "domain_progress_transition_runtime",
        "domain_progress_transition_runtime_result",
    ):
        if key not in updated and key in handoff_packet:
            updated[key] = handoff_packet[key]
    return updated


def _bind_projection_provider_readback_to_actions(
    projection: Mapping[str, Any],
    *,
    readback_candidate: Mapping[str, Any],
) -> list[dict[str, Any]]:
    bound: list[dict[str, Any]] = []
    for item in projection.get("action_queue") or []:
        if not isinstance(item, Mapping):
            continue
        action = _action_with_handoff_packet_readback(item)
        if not _same_provider_readback_identity(action, readback_candidate):
            continue
        action_readback = provider_admission_opl_transition_readback(action) or readback_candidate[
            "opl_domain_progress_transition_runtime_live_readback"
        ]
        bound.append(
            {
                **action,
                "status": "provider_admission_pending",
                "provider_admission_pending": True,
                "transition_request_pending": False,
                "provider_attempt_or_lease_required": True,
                "provider_admission_requires_opl_runtime_result": False,
                "provider_admission_identity": {
                    **_observability_mapping(action.get("provider_admission_identity")),
                    **dict(readback_candidate),
                },
                "opl_domain_progress_transition_runtime_live_readback": action_readback,
            }
        )
    return bound


def _same_provider_readback_identity(
    action: Mapping[str, Any],
    readback_candidate: Mapping[str, Any],
) -> bool:
    action_study = _non_empty_text(action.get("study_id"))
    readback_study = _non_empty_text(readback_candidate.get("study_id"))
    if action_study is not None and readback_study is not None and action_study != readback_study:
        return False
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    readback_work_unit = _work_unit_identity(readback_candidate.get("work_unit_id"))
    if action_work_unit is None or readback_work_unit is None or action_work_unit != readback_work_unit:
        return False
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    readback_fingerprint = _non_empty_text(readback_candidate.get("work_unit_fingerprint"))
    if action_fingerprint is None or readback_fingerprint is None or action_fingerprint != readback_fingerprint:
        return False
    for key in ("route_identity_key", "attempt_idempotency_key"):
        action_value = _non_empty_text(action.get(key))
        readback_value = _non_empty_text(readback_candidate.get(key))
        if action_value is not None and readback_value is not None and action_value != readback_value:
            return False
    return True


def _latest_provider_admission_terminal_consumed_readback_for_study(
    payload: Mapping[str, Any],
    *,
    study_id: str,
) -> dict[str, Any]:
    readback = _observability_mapping(payload.get("latest_provider_admission_terminal_consumed_readback"))
    if _non_empty_text(readback.get("status")) != "provider_admission_terminal_consumed":
        return {}
    identity = _observability_mapping(readback.get("currentness_identity"))
    readback_study = _non_empty_text(identity.get("study_id")) or _non_empty_text(readback.get("study_id"))
    if readback_study is not None and readback_study != study_id:
        return {}
    return dict(readback)


def _apply_terminal_consumed_readback_to_handoff(
    projection: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    terminal = _terminal_stage_log_from_terminal_consumed_readback(readback)
    if not terminal:
        return dict(projection)
    updated = dict(projection)
    existing_terminal = _observability_mapping(updated.get("latest_terminal_stage_log"))
    if not existing_terminal:
        updated["latest_terminal_stage_log"] = terminal
    candidate_sources = [
        *_handoff_candidate_list(updated.get("provider_admission_candidates")),
        *_handoff_candidate_list(updated.get("transition_request_candidates")),
        *_handoff_candidate_list(updated.get("action_queue")),
    ]
    if candidate_sources and not _terminal_matching_handoff_candidates(
        terminal=terminal,
        candidates=candidate_sources,
    ):
        return updated
    updated = _apply_matching_terminal_closeout_to_handoff(updated)
    return _consume_terminal_matching_action_queue(
        updated,
        terminal=terminal,
        consumed_readback=readback,
    )


def _consume_terminal_matching_action_queue(
    projection: Mapping[str, Any],
    *,
    terminal: Mapping[str, Any],
    consumed_readback: Mapping[str, Any],
) -> dict[str, Any]:
    action_queue = _handoff_candidate_list(projection.get("action_queue"))
    matching_actions = _terminal_matching_handoff_candidates(
        terminal=terminal,
        candidates=action_queue,
    )
    if not matching_actions:
        return dict(projection)
    updated = dict(projection)
    consumed_entries = [
        {
            **dict(item),
            "consumption": {
                **_observability_mapping(item.get("consumption")),
                "state": "consumed_by_provider_admission_terminal_readback",
                "terminal_stage_attempt_id": _non_empty_text(
                    consumed_readback.get("terminal_stage_attempt_id")
                )
                or _non_empty_text(consumed_readback.get("stage_attempt_id")),
            },
        }
        for item in matching_actions
    ]
    prior_consumed = [
        dict(item)
        for item in updated.get("consumed_action_queue") or []
        if isinstance(item, Mapping)
    ]
    updated["consumed_action_queue"] = [*prior_consumed, *consumed_entries]
    updated["action_queue"] = [
        dict(item)
        for item in action_queue
        if item not in matching_actions
    ]
    updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
        terminal=terminal,
        matching_provider_admission=matching_actions[0],
    )
    return updated


def _terminal_stage_log_from_terminal_consumed_readback(
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    if _non_empty_text(readback.get("status")) != "provider_admission_terminal_consumed":
        return {}
    identity = _observability_mapping(readback.get("currentness_identity"))
    terminal = {
        "surface_kind": "stage_attempt_closeout_packet",
        "source": "opl_current_control_state.latest_provider_admission_terminal_consumed_readback",
        "status": _non_empty_text(readback.get("terminal_stage_attempt_status")) or "completed",
        "stage_attempt_id": _non_empty_text(readback.get("terminal_stage_attempt_id"))
        or _non_empty_text(identity.get("stage_attempt_id")),
        "action_type": _non_empty_text(identity.get("action_type")) or _non_empty_text(readback.get("action_type")),
        "work_unit_id": _work_unit_identity(identity.get("work_unit_id"))
        or _work_unit_identity(readback.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(readback.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(readback.get("action_fingerprint")),
        "route_identity_key": _non_empty_text(identity.get("route_identity_key"))
        or _non_empty_text(readback.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(identity.get("attempt_idempotency_key"))
        or _non_empty_text(readback.get("attempt_idempotency_key")),
        "idempotency_key": _non_empty_text(identity.get("idempotency_key"))
        or _non_empty_text(readback.get("idempotency_key"))
        or _non_empty_text(identity.get("attempt_idempotency_key")),
        "closeout_refs": _string_list(readback.get("closeout_refs")),
        "provider_completion_is_domain_completion": readback.get("provider_completion_is_domain_completion"),
        "provider_completion_is_domain_ready": readback.get("provider_completion_is_domain_ready"),
    }
    return {key: value for key, value in terminal.items() if value not in (None, "", [], {})}


def _closeout_only_study_handoff_projection(
    *,
    handoff_path: Path,
    latest_terminal_stage_log: Mapping[str, Any] | None,
    latest_typed_closeout: Mapping[str, Any] | None,
    study_id: str,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source_payload = _mapping_copy(payload)
    terminal_stage_log = _observability_mapping(latest_terminal_stage_log)
    typed_closeout = _observability_mapping(latest_typed_closeout)
    projection = {
        "surface_kind": "opl_current_control_state_study_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": "observability_only",
        "source_path": str(handoff_path),
        "generated_at": _non_empty_text(source_payload.get("generated_at"))
        or _non_empty_text(terminal_stage_log.get("generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": None,
        "active_stage_attempt_id": _non_empty_text(terminal_stage_log.get("stage_attempt_id"))
        or _non_empty_text(typed_closeout.get("execution_id")),
        "active_workflow_id": None,
        "running_provider_attempt": False,
        "runtime_health": {},
        "artifact_delta": {},
        "gate_specificity": {},
        "ai_reviewer_status": {},
        "stage_progress_log": {},
        "owner_route": {},
        "queue_slo": {},
        "owner_pickup_overdue": False,
        "developer_supervisor_attention_required": False,
        "action_queue": [],
        "why_not_applied": [],
        "next_owner": _non_empty_text(typed_closeout.get("next_owner")),
        "external_supervisor_required": False,
        "blocked_reason": _non_empty_text(typed_closeout.get("blocked_reason"))
        or _non_empty_text(terminal_stage_log.get("typed_blocker_reason")),
    }
    if terminal_stage_log:
        projection["latest_terminal_stage_log"] = dict(terminal_stage_log)
    if typed_closeout:
        projection["latest_typed_default_executor_closeout"] = dict(typed_closeout)
        projection = _apply_typed_default_executor_closeout_to_handoff(projection)
    projection.update(_opl_current_control_state_mode_fields(source_payload))
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
    source_path = _non_empty_text(runtime_liveness_audit.get("handoff_path")) or str(
        opl_current_control_state_handoff_path(profile=profile)
    )
    runtime_health = _copy_mapping_keys(
        runtime_liveness_audit.get("runtime_health"),
        (
            "health_status",
            "runtime_liveness_status",
            "summary",
            "blocked_reason",
            *ATTEMPT_IDENTITY_KEYS,
        ),
    )
    active_run_id = _non_empty_text(runtime_liveness_audit.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(runtime_liveness_audit.get("active_stage_attempt_id"))
    active_workflow_id = _non_empty_text(runtime_liveness_audit.get("active_workflow_id"))
    running_provider_attempt = _strict_running_provider_attempt(
        runtime_liveness_audit,
        active_run_id=active_run_id,
        active_stage_attempt_id=active_stage_attempt_id,
        active_workflow_id=active_workflow_id,
    )
    return {
        "surface_kind": "opl_current_control_state_provider_attempt_handoff",
        "read_model": "study_opl_current_control_state_handoff_projection",
        "authority": _non_empty_text(runtime_liveness_audit.get("authority")) or "observability_only",
        "source_path": source_path,
        "generated_at": _non_empty_text(runtime_liveness_audit.get("handoff_generated_at")),
        "study_id": study_id,
        "quest_status": None,
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "action_type": _non_empty_text(runtime_liveness_audit.get("action_type")),
        "work_unit_id": _work_unit_identity(runtime_liveness_audit.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(runtime_liveness_audit.get("action_fingerprint"))
        or _non_empty_text(runtime_liveness_audit.get("work_unit_fingerprint")),
        "runtime_owner": "one-person-lab" if running_provider_attempt else None,
        "provider_attempt_owner": "one-person-lab" if running_provider_attempt else None,
        "queue_owner": "one-person-lab" if running_provider_attempt else None,
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


def _copy_opl_transition_readback_fields(
    projection: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    readback = candidate_opl_transition_readback(source)
    if not readback:
        return
    projection["opl_domain_progress_transition_runtime_live_readback"] = readback
    projection["provider_admission_identity"] = _provider_admission_identity_from_readback(readback)
    _apply_non_advancing_apply_readback_to_handoff(projection, source=source, readback=readback)


def _apply_non_advancing_apply_readback_to_handoff(
    projection: dict[str, Any],
    *,
    source: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> None:
    readback_container = _observability_mapping(
        source.get("domain_progress_transition_non_advancing_apply_readback")
    )
    non_advancing = non_advancing_apply_opl_transition_readback(
        {
            **readback_container,
            "opl_domain_progress_transition_runtime_live_readback": readback,
        }
    )
    if not non_advancing:
        return
    readback_identity = _provider_admission_identity_from_readback(non_advancing)
    study_id = (
        _non_empty_text(projection.get("study_id"))
        or _non_empty_text(readback_identity.get("study_id"))
    )
    action_type = (
        _non_empty_text(readback_container.get("action_type"))
        or _non_empty_text(projection.get("action_type"))
        or _non_empty_text(_observability_mapping(non_advancing.get("identity")).get("transition_kind"))
    )
    work_unit_id = _work_unit_identity(readback_container.get("work_unit_id")) or _work_unit_identity(
        readback_identity.get("work_unit_id")
    )
    work_unit_fingerprint = (
        _non_empty_text(readback_container.get("work_unit_fingerprint"))
        or _non_empty_text(readback_identity.get("work_unit_fingerprint"))
    )
    typed_blocker = {
        key: value
        for key, value in {
            "surface_kind": "mas_current_control_typed_blocker_projection",
            "blocker_type": "non_advancing_apply",
            "blocked_reason": _non_empty_text(readback_container.get("reason"))
            or "opl_transition_request_missing_for_authorized_stage_packet",
            "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
            "owner": "one-person-lab",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "route_identity_key": _non_empty_text(readback_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(readback_identity.get("attempt_idempotency_key")),
            "request_idempotency_key": _non_empty_text(readback_identity.get("request_idempotency_key")),
            "stage_run_id": _non_empty_text(readback_identity.get("stage_run_id")),
            "event_id": _non_empty_text(readback_identity.get("event_id")),
            "outbox_item_id": _non_empty_text(readback_identity.get("outbox_item_id")),
            "transaction_id": _non_empty_text(readback_identity.get("transaction_id")),
            "non_advancing_apply": True,
            "provider_admission_allowed": False,
            "current_executable_owner_action_allowed": False,
            "paper_progress_delta": False,
            "provider_completion_is_domain_completion": False,
            "authority_boundary": _non_advancing_apply_authority_boundary(readback_container),
        }.items()
        if value not in (None, "", [], {})
    }
    projection["running_provider_attempt"] = False
    projection["active_run_id"] = None
    projection["active_workflow_id"] = None
    projection["current_executable_owner_action"] = None
    projection["provider_admission_pending_count"] = 0
    projection["provider_admission_candidates"] = []
    projection["transition_request_pending_count"] = 0
    projection["transition_request_candidates"] = []
    projection["blocked_reason"] = typed_blocker["blocked_reason"]
    projection["next_owner"] = "one-person-lab"
    projection["typed_blocker"] = typed_blocker
    projection["current_work_unit"] = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "one-person-lab",
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "state": {
            "state_kind": "typed_blocker",
            "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
            "typed_blocker": typed_blocker,
        },
    }
    projection["current_execution_envelope"] = {
        "state_kind": "typed_blocker",
        "owner": "one-person-lab",
        "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
        "typed_blocker": typed_blocker,
    }
    projection["domain_progress_transition_non_advancing_apply_readback"] = dict(readback_container)
    projection["domain_progress_transition_projection_metadata"] = _observability_mapping(
        source.get("domain_progress_transition_projection_metadata")
    )


def _non_advancing_apply_authority_boundary(readback_container: Mapping[str, Any]) -> dict[str, Any]:
    boundary = _observability_mapping(readback_container.get("authority_boundary"))
    return {
        **boundary,
        "projection_only": True,
        "runtime_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "can_authorize_provider_admission": False,
        "can_start_provider_attempt": False,
        "provider_running_is_paper_progress": False,
        "provider_completion_is_domain_completion": False,
        "paper_progress_delta": False,
    }


def _provider_admission_identity_from_readback(readback: Mapping[str, Any]) -> dict[str, Any]:
    identity = _observability_mapping(readback.get("identity"))
    aggregate_identity = _observability_mapping(identity.get("aggregate_identity"))
    stage_run_identity = _observability_mapping(identity.get("stage_run_identity"))
    return {
        key: value
        for key, value in {
            "study_id": _non_empty_text(aggregate_identity.get("study_id")),
            "work_unit_id": _work_unit_identity(aggregate_identity.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(
                aggregate_identity.get("work_unit_fingerprint")
            ),
            "route_identity_key": _non_empty_text(stage_run_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(
                stage_run_identity.get("attempt_idempotency_key")
            ),
            "request_idempotency_key": _non_empty_text(identity.get("idempotency_key"))
            or _non_empty_text(identity.get("request_idempotency_key")),
            "stage_run_id": _non_empty_text(stage_run_identity.get("stage_run_id")),
            "event_id": _non_empty_text(identity.get("latest_event_id"))
            or _non_empty_text(identity.get("event_id")),
            "outbox_item_id": _non_empty_text(identity.get("latest_outbox_item_id"))
            or _non_empty_text(identity.get("outbox_item_id")),
            "transaction_id": _non_empty_text(identity.get("latest_transaction_id"))
            or _non_empty_text(identity.get("transaction_id")),
        }.items()
        if value is not None
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
    live_attempt_running = live_attempt_handoff.get("running_provider_attempt") is True
    if live_attempt_running and _live_attempt_supersedes_handoff_blocker(merged):
        merged["external_supervisor_required"] = False
        merged["blocked_reason"] = None
        merged.pop("typed_blocker", None)
        merged["why_not_applied"] = [
            reason
            for reason in _string_list(merged.get("why_not_applied"))
            if reason not in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS
        ]
        if _non_empty_text(merged.get("next_owner")) in LIVE_ATTEMPT_SUPERSEDED_NEXT_OWNERS:
            merged["next_owner"] = _non_empty_text(live_attempt_handoff.get("next_owner"))
    for key in LIVE_ATTEMPT_HANDOFF_KEYS:
        if (
            key == "active_stage_attempt_id"
            and live_attempt_running
            and _handoff_live_attempt_identity_stale(
                handoff=merged,
                live_attempt_handoff=live_attempt_handoff,
            )
        ):
            merged[key] = live_attempt_handoff[key]
            continue
        if key not in merged or merged.get(key) in {None, "", False}:
            if key in live_attempt_handoff:
                merged[key] = live_attempt_handoff[key]
    if live_attempt_running:
        for key in ("runtime_owner", "provider_attempt_owner", "queue_owner"):
            value = _non_empty_text(live_attempt_handoff.get(key)) or "one-person-lab"
            merged[key] = value
    if not _stage_progress_log_mapping(merged.get("stage_progress_log")):
        stage_progress_log = _stage_progress_log_mapping(live_attempt_handoff.get("stage_progress_log"))
        if stage_progress_log:
            merged["stage_progress_log"] = stage_progress_log
    live_runtime_health = _copy_mapping_keys(
        live_attempt_handoff.get("runtime_health"),
        ("health_status", "runtime_liveness_status", "summary", "blocked_reason"),
    )
    if live_runtime_health and (
        live_attempt_running
        or not _copy_mapping_keys(merged.get("runtime_health"), ("health_status", "runtime_liveness_status"))
    ):
        merged["runtime_health"] = live_runtime_health
    if live_attempt_running:
        merged = bind_live_attempt_to_handoff_identity(
            handoff=merged,
            live_attempt_handoff=live_attempt_handoff,
        )
    return _apply_matching_terminal_closeout_to_handoff(merged)


def _apply_matching_terminal_closeout_to_handoff(projection: dict[str, Any]) -> dict[str, Any]:
    if not _handoff_has_matching_terminal_closeout(projection):
        return projection
    updated = dict(projection)
    terminal = _observability_mapping(updated.get("latest_terminal_stage_log"))
    updated["running_provider_attempt"] = False
    updated["runtime_owner"] = None
    updated["provider_attempt_owner"] = None
    updated["queue_owner"] = None
    updated["active_run_id"] = None
    updated["active_workflow_id"] = None
    updated["active_stage_attempt_id"] = (
        _non_empty_text(terminal.get("stage_attempt_id"))
        or _non_empty_text(updated.get("active_stage_attempt_id"))
    )
    runtime_health = _observability_mapping(updated.get("runtime_health"))
    if runtime_health:
        runtime_health["runtime_liveness_status"] = "terminal"
        runtime_health["health_status"] = "terminal"
        updated["runtime_health"] = runtime_health
    provider_admission_pending = int(updated.get("provider_admission_pending_count") or 0) > 0
    transition_request_pending = int(updated.get("transition_request_pending_count") or 0) > 0
    if provider_admission_pending or transition_request_pending:
        provider_admission_candidates = _handoff_candidate_list(updated.get("provider_admission_candidates"))
        transition_request_candidates = _handoff_candidate_list(updated.get("transition_request_candidates"))
        matching_provider_admissions = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=provider_admission_candidates,
        )
        matching_transition_requests = _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=transition_request_candidates,
        )
        if (
            _handoff_has_complete_current_transition_readback(updated)
            and provider_admission_pending
            and not matching_provider_admissions
            and not matching_transition_requests
        ):
            return projection
        if (
            matching_provider_admissions
            and any(provider_admission_opl_transition_readback(item) for item in matching_provider_admissions)
            and not _terminal_closeout_has_domain_delta(terminal)
        ):
            return projection
        if (
            (provider_admission_candidates or transition_request_candidates)
            and not matching_provider_admissions
            and not matching_transition_requests
        ):
            return projection
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        updated["transition_request_pending_count"] = 0
        updated["transition_request_candidates"] = []
        updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
            terminal=terminal,
            matching_provider_admission=matching_provider_admissions[0]
            if matching_provider_admissions
            else matching_transition_requests[0]
            if matching_transition_requests
            else None,
        )
    else:
        matching_consumed_action = _terminal_closeout_consumed_current_action_projection(
            terminal=terminal,
            projection=updated,
        )
        if matching_consumed_action is not None:
            updated["provider_admission_pending_count"] = 0
            updated["provider_admission_candidates"] = []
            updated["transition_request_pending_count"] = 0
            updated["transition_request_candidates"] = []
            updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
                terminal=terminal,
                matching_provider_admission=matching_consumed_action,
            )
    updated = _apply_terminal_closeout_next_owner(updated, terminal=terminal)
    return _apply_terminal_closeout_owner_answer_gate(updated)


def _apply_terminal_closeout_next_owner(
    projection: dict[str, Any],
    *,
    terminal: Mapping[str, Any],
) -> dict[str, Any]:
    next_owner = _terminal_closeout_next_owner(terminal) or _terminal_closeout_next_owner(projection)
    if next_owner is None:
        return projection
    owner_action = _terminal_closeout_next_owner_action(terminal) or _terminal_closeout_next_owner_action(projection)
    updated = dict(projection)
    updated["next_owner"] = next_owner
    owner_route = _observability_mapping(updated.get("owner_route"))
    if owner_route:
        owner_route["next_owner"] = next_owner
        updated["owner_route"] = owner_route
    current = _observability_mapping(updated.get("current_work_unit"))
    if current and _non_empty_text(current.get("status")) in {"executable_owner_action", "owner_receipt_recorded"}:
        current["owner"] = next_owner
        _apply_owner_action_identity_to_current_work_unit(current, owner_action=owner_action)
        updated["current_work_unit"] = current
    envelope = _observability_mapping(updated.get("current_execution_envelope"))
    if envelope and _non_empty_text(envelope.get("state_kind")) in {"executable_owner_action", "owner_receipt_recorded"}:
        envelope["owner"] = next_owner
        next_work_unit = _work_unit_identity(owner_action.get("work_unit_id")) or _work_unit_identity(
            owner_action.get("next_work_unit")
        )
        if next_work_unit is not None:
            envelope["next_work_unit"] = next_work_unit
        updated["current_execution_envelope"] = envelope
    return updated


def _terminal_closeout_next_owner_action(value: Mapping[str, Any]) -> dict[str, Any]:
    paper_log = _observability_mapping(value.get("paper_stage_log"))
    next_forced = _observability_mapping(value.get("next_forced_delta")) or _observability_mapping(
        paper_log.get("next_forced_delta")
    )
    return _observability_mapping(next_forced.get("owner_action"))


def _apply_owner_action_identity_to_current_work_unit(
    current: dict[str, Any],
    *,
    owner_action: Mapping[str, Any],
) -> None:
    if not owner_action:
        return
    action_type = _non_empty_text(owner_action.get("action_type"))
    if action_type is not None:
        current["action_type"] = action_type
    work_unit = _work_unit_identity(owner_action.get("work_unit_id")) or _work_unit_identity(
        owner_action.get("next_work_unit")
    )
    if work_unit is not None:
        current["work_unit_id"] = work_unit
    fingerprint = _non_empty_text(owner_action.get("work_unit_fingerprint")) or _non_empty_text(
        owner_action.get("action_fingerprint")
    )
    if fingerprint is not None:
        current["work_unit_fingerprint"] = fingerprint
        current["action_fingerprint"] = fingerprint
    state = _observability_mapping(current.get("state"))
    if state:
        if action_type is not None:
            state["action_type"] = action_type
        if work_unit is not None:
            state["next_work_unit"] = work_unit
        current["state"] = state


def _terminal_closeout_next_owner(value: Mapping[str, Any]) -> str | None:
    owner_action = _terminal_closeout_next_owner_action(value)
    paper_log = _observability_mapping(value.get("paper_stage_log"))
    next_forced = _observability_mapping(value.get("next_forced_delta")) or _observability_mapping(
        paper_log.get("next_forced_delta")
    )
    owner_route = _observability_mapping(value.get("owner_route"))
    return (
        _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
        or _non_empty_text(next_forced.get("next_owner"))
        or _non_empty_text(next_forced.get("owner"))
        or _non_empty_text(value.get("next_executable_owner"))
        or _non_empty_text(value.get("next_owner"))
        or _non_empty_text(value.get("owner"))
        or _non_empty_text(owner_route.get("next_owner"))
        or _non_empty_text(paper_log.get("current_owner"))
    )


def _handoff_candidate_list(value: object) -> list[dict[str, Any]]:
    return [dict(item) for item in value or [] if isinstance(item, Mapping)]


def _terminal_matching_handoff_candidates(
    *,
    terminal: Mapping[str, Any],
    candidates: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    return [
        item
        for item in candidates
        if _terminal_closeout_matches_handoff_action(terminal=terminal, action=item)
    ]


def _terminal_closeout_consumed_current_action_projection(
    *,
    terminal: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> dict[str, Any] | None:
    if _non_empty_text(terminal.get("owner_receipt_ref")) is None:
        return None
    for source in (
        projection.get("current_work_unit"),
        projection.get("current_execution_envelope"),
        projection,
    ):
        action = _terminal_closeout_action_projection_from_source(source)
        if action and _terminal_closeout_matches_handoff_action(terminal=terminal, action=action):
            return action
    return None


def _terminal_closeout_action_projection_from_source(source: object) -> dict[str, Any]:
    mapping = _observability_mapping(source)
    if not mapping:
        return {}
    state = _observability_mapping(mapping.get("state"))
    identity = _observability_mapping(mapping.get("provider_admission_identity"))
    source_refs = _observability_mapping(mapping.get("source_refs"))
    action = {
        "status": _non_empty_text(mapping.get("status")) or "provider_admission_pending",
        "study_id": _non_empty_text(mapping.get("study_id")),
        "quest_id": _non_empty_text(mapping.get("quest_id")),
        "action_type": _non_empty_text(mapping.get("action_type")) or _non_empty_text(state.get("action_type")),
        "work_unit_id": _work_unit_identity(mapping.get("work_unit_id"))
        or _work_unit_identity(mapping.get("next_work_unit"))
        or _work_unit_identity(state.get("next_work_unit"))
        or _work_unit_identity(state.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(mapping.get("work_unit_fingerprint"))
        or _non_empty_text(mapping.get("action_fingerprint"))
        or _non_empty_text(state.get("work_unit_fingerprint"))
        or _non_empty_text(state.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(mapping.get("action_fingerprint"))
        or _non_empty_text(mapping.get("work_unit_fingerprint"))
        or _non_empty_text(state.get("action_fingerprint"))
        or _non_empty_text(state.get("work_unit_fingerprint")),
        "route_identity_key": _non_empty_text(mapping.get("route_identity_key"))
        or _non_empty_text(identity.get("route_identity_key"))
        or _non_empty_text(source_refs.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(mapping.get("attempt_idempotency_key"))
        or _non_empty_text(identity.get("attempt_idempotency_key"))
        or _non_empty_text(source_refs.get("attempt_idempotency_key")),
        "idempotency_key": _non_empty_text(mapping.get("idempotency_key"))
        or _non_empty_text(identity.get("idempotency_key"))
        or _non_empty_text(source_refs.get("idempotency_key")),
        "stage_packet_ref": _non_empty_text(mapping.get("stage_packet_ref"))
        or _non_empty_text(source_refs.get("stage_packet_ref")),
        "stage_packet_refs": _stage_ref_items(mapping.get("stage_packet_refs"))
        or _stage_ref_items(source_refs.get("stage_packet_refs")),
        "provider_admission_identity": identity,
        "source_refs": source_refs,
    }
    return {key: value for key, value in action.items() if value not in (None, "", [], {})}


def _provider_admission_terminal_closeout_consumed(
    *,
    terminal: Mapping[str, Any],
    matching_provider_admission: Mapping[str, Any] | None,
) -> dict[str, Any]:
    admission = _observability_mapping(matching_provider_admission)
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    next_forced_delta = _observability_mapping(paper_stage_log.get("next_forced_delta"))
    owner_action = _observability_mapping(next_forced_delta.get("owner_action"))
    consumed = {
        "surface_kind": "provider_admission_terminal_closeout_consumed",
        "source": "opl_current_control_state_handoff.latest_terminal_stage_log",
        "stage_attempt_id": _non_empty_text(terminal.get("stage_attempt_id")),
        "action_type": _non_empty_text(admission.get("action_type"))
        or _non_empty_text(terminal.get("action_type"))
        or _non_empty_text(owner_action.get("action_type")),
        "closeout_action_type": _non_empty_text(terminal.get("action_type")),
        "work_unit_id": _work_unit_identity(terminal.get("work_unit_id"))
        or _work_unit_identity(admission.get("work_unit_id"))
        or _work_unit_identity(admission.get("next_work_unit"))
        or _work_unit_identity(next_forced_delta.get("work_unit_id"))
        or _work_unit_identity(owner_action.get("work_unit_id"))
        or _work_unit_identity(owner_action.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(terminal.get("work_unit_fingerprint"))
        or _non_empty_text(admission.get("work_unit_fingerprint"))
        or _non_empty_text(admission.get("action_fingerprint"))
        or _non_empty_text(admission.get("fingerprint"))
        or _non_empty_text(owner_action.get("work_unit_fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(terminal.get("action_fingerprint"))
        or _non_empty_text(admission.get("action_fingerprint"))
        or _non_empty_text(admission.get("work_unit_fingerprint"))
        or _non_empty_text(admission.get("fingerprint"))
        or _non_empty_text(owner_action.get("action_fingerprint"))
        or _non_empty_text(owner_action.get("work_unit_fingerprint")),
        "owner_receipt_ref": _non_empty_text(terminal.get("owner_receipt_ref")),
        "typed_blocker_ref": _non_empty_text(terminal.get("typed_blocker_ref")),
        "route_identity_key": _non_empty_text(terminal.get("route_identity_key"))
        or _non_empty_text(admission.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(terminal.get("attempt_idempotency_key"))
        or _non_empty_text(admission.get("attempt_idempotency_key")),
        "closeout_receipt_status": _non_empty_text(terminal.get("closeout_receipt_status")),
        "authority_boundary": {
            "projection_only": True,
            "runtime_owner": "one-person-lab",
            "domain_truth_owner": "med-autoscience",
            "can_authorize_provider_admission": False,
            "can_start_provider_attempt": False,
            "provider_completion_is_domain_completion": False,
        },
    }
    return {key: value for key, value in consumed.items() if value not in (None, "", [], {})}


def _apply_terminal_closeout_owner_answer_gate(projection: dict[str, Any]) -> dict[str, Any]:
    terminal = _observability_mapping(projection.get("latest_terminal_stage_log"))
    if not terminal or _terminal_closeout_has_owner_answer(terminal, projection):
        return projection
    action_queue = [dict(item) for item in projection.get("action_queue") or [] if isinstance(item, Mapping)]
    matching_actions = [
        item
        for item in action_queue
        if _terminal_closeout_matches_handoff_action(terminal=terminal, action=item)
    ]
    if action_queue and not matching_actions:
        return projection
    updated = dict(projection)
    blocker = _terminal_closeout_owner_answer_blocker(
        terminal=terminal,
        matching_action=matching_actions[0] if matching_actions else None,
    )
    updated["typed_blocker"] = blocker
    updated["blocked_reason"] = blocker["blocker_id"]
    updated["next_owner"] = blocker["owner"]
    updated["external_supervisor_required"] = True
    updated["terminal_closeout_consumed"] = True
    why_not_applied = _string_list(updated.get("why_not_applied"))
    if blocker["blocker_id"] not in why_not_applied:
        why_not_applied.append(blocker["blocker_id"])
    updated["why_not_applied"] = why_not_applied
    if matching_actions:
        source_ref = _non_empty_text(terminal.get("record_path")) or _non_empty_text(terminal.get("source_path"))
        updated["consumed_action_queue"] = [
            {
                **dict(item),
                "consumption": {
                    **_observability_mapping(item.get("consumption")),
                    "state": "consumed_by_terminal_stage_closeout",
                    "typed_blocker_ref": source_ref,
                },
            }
            for item in matching_actions
        ]
        updated["action_queue"] = [
            dict(item)
            for item in action_queue
            if item not in matching_actions
        ]
    return updated


def _terminal_closeout_has_owner_answer(
    terminal: Mapping[str, Any],
    projection: Mapping[str, Any],
) -> bool:
    if _observability_mapping(projection.get("latest_typed_default_executor_closeout")):
        return True
    if _non_empty_text(terminal.get("closeout_receipt_status")) == "accepted_typed_closeout":
        return True
    if _observability_mapping(projection.get("typed_blocker")):
        return True
    if _observability_mapping(terminal.get("typed_blocker")):
        return True
    if _non_empty_text(terminal.get("typed_blocker_ref")) or _non_empty_text(terminal.get("owner_receipt_ref")):
        return True
    if _string_list(terminal.get("typed_blocker_refs")) or _string_list(terminal.get("owner_receipt_refs")):
        return True
    if _non_empty_text(terminal.get("route_outcome")) == "owner_receipt":
        return True
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    if _terminal_stage_log_has_next_owner_handoff(terminal=terminal, paper_stage_log=paper_stage_log):
        return True
    if _string_list(paper_stage_log.get("changed_paper_surfaces")):
        return True
    outcome = _non_empty_text(paper_stage_log.get("outcome"))
    return outcome in {
        "blocked_with_domain_typed_blocker",
        "owner_receipt",
        "owner_receipt_recorded",
        "handoff_ready",
        "next_handoff",
    }


def _terminal_stage_log_has_next_owner_handoff(
    *,
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> bool:
    next_forced_delta = _observability_mapping(terminal.get("next_forced_delta")) or _observability_mapping(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _observability_mapping(next_forced_delta.get("owner_action"))
    if (
        _non_empty_text(owner_action.get("action_type")) is not None
        and (
            _non_empty_text(owner_action.get("next_owner")) is not None
            or _non_empty_text(owner_action.get("owner")) is not None
        )
        and (
            _non_empty_text(owner_action.get("work_unit_id")) is not None
            or _non_empty_text(owner_action.get("next_work_unit")) is not None
            or _non_empty_text(next_forced_delta.get("work_unit_id")) is not None
        )
    ):
        return True
    if _non_empty_text(terminal.get("status")) != "closed_with_domain_owner_refs":
        return False
    domain_refs = _observability_mapping(terminal.get("domain_owner_refs"))
    return any(
        _non_empty_text(domain_refs.get(key)) is not None
        for key in (
            "next_dispatch_ref",
            "next_request_ref",
            "next_owner_ref",
            "route_back_evidence_ref",
        )
    )


def _terminal_closeout_matches_handoff_action(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if _action_requires_identity_bound_terminal_closeout(action):
        return _terminal_closeout_matches_action_bound_identity(terminal=terminal, action=action)
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    action_attempt_id = _non_empty_text(action.get("stage_attempt_id")) or _non_empty_text(
        action.get("active_stage_attempt_id")
    )
    if terminal_attempt_id and action_attempt_id:
        return terminal_attempt_id == action_attempt_id
    terminal_action_type = _non_empty_text(terminal.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if terminal_action_type and action_type and terminal_action_type != action_type:
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit and action_work_unit:
        return terminal_work_unit == action_work_unit
    return terminal_action_type is not None and terminal_action_type == action_type


def _action_requires_identity_bound_terminal_closeout(action: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(action):
        return True
    if _non_empty_text(action.get("status")) not in {
        "provider_admission_pending",
        "transition_request_pending",
    }:
        return False
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    if not identity:
        identity_sources = (action, source_refs)
    else:
        identity_sources = (action, identity, source_refs)
    return any(
        _non_empty_text(source.get(key)) is not None
        for source in identity_sources
        for key in (
            "stage_run_id",
            "stage_attempt_id",
            "active_stage_attempt_id",
            "route_identity_key",
            "attempt_idempotency_key",
            "idempotency_key",
            "stage_packet_ref",
            "stage_packet_path",
            "dispatch_ref",
            "dispatch_path",
        )
    ) or bool(_stage_packet_refs(action))


def _terminal_closeout_matches_action_bound_identity(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if (
        provider_admission_opl_transition_readback(action)
        and not _terminal_closeout_action_identity_matches_candidate(
            terminal=terminal,
            action=action,
        )
    ):
        return False
    if _terminal_closeout_request_wrapper_identity_matches_candidate(terminal=terminal, action=action):
        return True
    if not _terminal_closeout_action_identity_matches_candidate(
        terminal=terminal,
        action=action,
    ):
        return False
    terminal_stage_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if terminal_stage_attempt_id is not None and terminal_stage_attempt_id in _action_stage_run_ids(action):
        return True
    terminal_route_identity_key = _non_empty_text(terminal.get("route_identity_key"))
    if terminal_route_identity_key is not None and terminal_route_identity_key in _action_route_identity_keys(action):
        return True
    terminal_attempt_idempotency_key = _non_empty_text(terminal.get("attempt_idempotency_key"))
    if (
        terminal_attempt_idempotency_key is not None
        and terminal_attempt_idempotency_key in _action_attempt_idempotency_keys(action)
    ):
        return True
    terminal_idempotency_key = _non_empty_text(terminal.get("idempotency_key"))
    if terminal_idempotency_key is not None and terminal_idempotency_key in _action_idempotency_keys(action):
        return True
    terminal_stage_packet_refs = _stage_packet_refs(terminal)
    if terminal_stage_packet_refs and terminal_stage_packet_refs.intersection(_stage_packet_refs(action)):
        return True
    # Identity-bound admissions are backed by OPL runtime readback or explicit
    # dispatch identity; weak action/work-unit/fingerprint matching is legacy-only.
    return False


def _action_stage_run_ids(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    stage_run_identity = _observability_mapping(
        _observability_mapping(readback.get("identity")).get("stage_run_identity")
    )
    identity = _observability_mapping(action.get("provider_admission_identity"))
    return {
        value
        for value in (
            _non_empty_text(action.get("stage_run_id")),
            _non_empty_text(action.get("stage_attempt_id")),
            _non_empty_text(action.get("active_stage_attempt_id")),
            _non_empty_text(identity.get("stage_run_id")),
            _non_empty_text(identity.get("stage_attempt_id")),
            _non_empty_text(identity.get("active_stage_attempt_id")),
            _non_empty_text(stage_run_identity.get("stage_run_id")),
        )
        if value is not None
    }


def _action_route_identity_keys(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    stage_run_identity = _observability_mapping(
        _observability_mapping(readback.get("identity")).get("stage_run_identity")
    )
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    return {
        value
        for value in (
            _non_empty_text(action.get("route_identity_key")),
            _non_empty_text(identity.get("route_identity_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(stage_run_identity.get("route_identity_key")),
        )
        if value is not None
    }


def _action_attempt_idempotency_keys(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    stage_run_identity = _observability_mapping(
        _observability_mapping(readback.get("identity")).get("stage_run_identity")
    )
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    return {
        value
        for value in (
            _non_empty_text(action.get("attempt_idempotency_key")),
            _non_empty_text(identity.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(stage_run_identity.get("attempt_idempotency_key")),
        )
        if value is not None
    }


def _action_idempotency_keys(action: Mapping[str, Any]) -> set[str]:
    readback = candidate_opl_transition_readback(action)
    readback_identity = _observability_mapping(readback.get("identity"))
    idempotency_readback = _observability_mapping(readback.get("idempotency_readback"))
    identity = _observability_mapping(action.get("provider_admission_identity"))
    source_refs = _observability_mapping(action.get("source_refs"))
    return {
        value
        for value in (
            _non_empty_text(action.get("idempotency_key")),
            _non_empty_text(action.get("route_identity_key")),
            _non_empty_text(action.get("attempt_idempotency_key")),
            _non_empty_text(identity.get("idempotency_key")),
            _non_empty_text(identity.get("route_identity_key")),
            _non_empty_text(identity.get("attempt_idempotency_key")),
            _non_empty_text(source_refs.get("idempotency_key")),
            _non_empty_text(source_refs.get("route_identity_key")),
            _non_empty_text(source_refs.get("attempt_idempotency_key")),
            _non_empty_text(readback_identity.get("idempotency_key")),
            _non_empty_text(idempotency_readback.get("idempotency_key")),
        )
        if value is not None
    }


def _stage_packet_refs(payload: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in ("stage_packet_ref", "stage_packet_path", "dispatch_ref", "dispatch_path"):
        if text := _non_empty_text(payload.get(key)):
            refs.add(text)
    for key in ("stage_packet_refs", "checkpoint_refs"):
        refs.update(_string_list(payload.get(key)))
    identity = _observability_mapping(payload.get("provider_admission_identity"))
    for key in ("stage_packet_ref", "stage_packet_path", "dispatch_ref", "dispatch_path"):
        if text := _non_empty_text(identity.get(key)):
            refs.add(text)
    for key in ("stage_packet_refs", "checkpoint_refs"):
        refs.update(_string_list(identity.get(key)))
    return refs


def _terminal_closeout_action_identity_matches_candidate(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    terminal_action_type = _non_empty_text(terminal.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if terminal_action_type is None or action_type is None or terminal_action_type != action_type:
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit is not None and action_work_unit is not None and terminal_work_unit != action_work_unit:
        return False
    terminal_fingerprint = _non_empty_text(terminal.get("work_unit_fingerprint")) or _non_empty_text(
        terminal.get("action_fingerprint")
    )
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if terminal_fingerprint is not None and action_fingerprint is not None and terminal_fingerprint != action_fingerprint:
        return False
    return True


def _terminal_closeout_request_wrapper_identity_matches_candidate(
    *,
    terminal: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("action_type")) != "request_opl_stage_attempt":
        return False
    if not _request_wrapper_action_has_opl_transition_identity(action):
        return False
    terminal_work_unit = _work_unit_identity(terminal.get("work_unit_id")) or _work_unit_identity(
        terminal.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    if terminal_work_unit is None or action_work_unit is None or terminal_work_unit != action_work_unit:
        return False
    terminal_fingerprint = _non_empty_text(terminal.get("work_unit_fingerprint")) or _non_empty_text(
        terminal.get("action_fingerprint")
    )
    action_fingerprint = _non_empty_text(action.get("work_unit_fingerprint")) or _non_empty_text(
        action.get("action_fingerprint")
    )
    if terminal_fingerprint is not None and action_fingerprint is not None:
        return terminal_fingerprint == action_fingerprint
    return _terminal_closeout_has_request_wrapper_domain_owner_delta(terminal)


def _request_wrapper_action_has_opl_transition_identity(action: Mapping[str, Any]) -> bool:
    return (
        bool(_action_route_identity_keys(action) or _action_attempt_idempotency_keys(action) or _action_idempotency_keys(action))
        and (candidate_opl_transition_readback(action) or provider_admission_opl_transition_readback(action))
    )


def _terminal_closeout_has_request_wrapper_domain_owner_delta(terminal: Mapping[str, Any]) -> bool:
    status = _non_empty_text(terminal.get("status"))
    if status not in {
        "closed_with_domain_owner_refs",
        "blocked_with_domain_owner_refs",
        "completed",
    }:
        return False
    if _non_empty_text(terminal.get("closeout_receipt_status")) == "accepted_typed_closeout":
        return True
    return _terminal_closeout_has_domain_delta(terminal)


def _terminal_closeout_owner_answer_blocker(
    *,
    terminal: Mapping[str, Any],
    matching_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    action = _observability_mapping(matching_action)
    source_ref = _non_empty_text(terminal.get("record_path")) or _non_empty_text(terminal.get("source_path"))
    blocker = {
        "blocker_id": "typed_closeout_packet_required",
        "blocker_type": "typed_closeout_packet_required",
        "owner": "MedAutoScience",
        "source": "terminal_stage_closeout_missing_owner_answer",
        "summary": (
            "Terminal provider closeout must include a MAS owner receipt, typed blocker, or next handoff "
            "before the current work unit can continue."
        ),
        "required_input": "MAS owner receipt, typed blocker, or next handoff",
        "stage_attempt_id": _non_empty_text(terminal.get("stage_attempt_id")),
        "action_type": _non_empty_text(terminal.get("action_type")) or _non_empty_text(action.get("action_type")),
        "work_unit_id": _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
            action.get("next_work_unit")
        ),
        "work_unit_fingerprint": _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "action_fingerprint": _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "source_ref": source_ref,
        "typed_blocker_ref": source_ref,
        "closeout_refs": _string_list(terminal.get("closeout_refs")),
    }
    return {key: value for key, value in blocker.items() if value not in (None, "", [], {})}


def _apply_typed_default_executor_closeout_to_handoff(
    projection: dict[str, Any],
    *,
    allow_stale_identity_override: bool = False,
) -> dict[str, Any]:
    typed_closeout = _observability_mapping(projection.get("latest_typed_default_executor_closeout"))
    if not typed_closeout:
        return projection
    if _handoff_has_complete_current_transition_readback(projection) and not allow_stale_identity_override:
        return projection
    matching_actions = [
        item
        for item in projection.get("action_queue") or []
        if isinstance(item, Mapping)
        and _typed_closeout_matches_handoff_action(typed_closeout=typed_closeout, action=item)
    ]
    if projection.get("action_queue") and not matching_actions and not allow_stale_identity_override:
        return projection
    typed_blocker = _typed_closeout_blocker_projection(
        typed_closeout=typed_closeout,
        matching_action=matching_actions[0] if matching_actions else None,
    )
    if not typed_blocker:
        return projection
    updated = dict(projection)
    if matching_actions:
        consumed = [
            {
                **dict(item),
                "consumption": {
                    **_observability_mapping(item.get("consumption")),
                    "state": "consumed_by_typed_default_executor_closeout",
                    "typed_blocker_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
                    or _non_empty_text(typed_closeout.get("source_path")),
                },
            }
            for item in matching_actions
        ]
        updated["consumed_action_queue"] = consumed
        updated["action_queue"] = [
            dict(item)
            for item in updated.get("action_queue") or []
            if isinstance(item, Mapping) and item not in matching_actions
        ]
    updated["typed_blocker"] = typed_blocker
    updated["blocked_reason"] = _non_empty_text(typed_blocker.get("blocker_type")) or updated.get("blocked_reason")
    updated["next_owner"] = _non_empty_text(typed_blocker.get("owner")) or updated.get("next_owner")
    updated["running_provider_attempt"] = False
    updated["runtime_owner"] = None
    updated["provider_attempt_owner"] = None
    updated["queue_owner"] = None
    if allow_stale_identity_override:
        updated["provider_admission_pending_count"] = 0
        updated["provider_admission_candidates"] = []
        updated["transition_request_pending_count"] = 0
        updated["transition_request_candidates"] = []
        updated["current_executable_owner_action"] = None
        updated["current_work_unit"] = _typed_closeout_current_work_unit(
            typed_blocker=typed_blocker,
            typed_closeout=typed_closeout,
        )
        updated["current_execution_envelope"] = {
            "state_kind": "typed_blocker",
            "owner": _non_empty_text(typed_blocker.get("owner")),
            "action_type": _non_empty_text(typed_blocker.get("action_type")),
            "work_unit_id": _work_unit_identity(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(typed_blocker.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(typed_blocker.get("action_fingerprint")),
            "source": "latest_typed_default_executor_closeout",
            "typed_blocker": typed_blocker,
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
            },
        }
        updated["provider_admission_terminal_closeout_consumed"] = _provider_admission_terminal_closeout_consumed(
            terminal={
                **typed_closeout,
                "typed_blocker_ref": _non_empty_text(typed_closeout.get("typed_blocker_ref"))
                or _non_empty_text(typed_closeout.get("receipt_ref"))
                or _non_empty_text(typed_closeout.get("source_path")),
            },
            matching_provider_admission=None,
        )
        updated["provider_admission_terminal_closeout_consumed"]["typed_blocker"] = typed_blocker
        updated["provider_admission_terminal_closeout_consumed"]["currentness_precedence"] = (
            "newer_terminal_typed_closeout_supersedes_stale_provider_admission"
        )
    return updated


def _newer_typed_closeout_blocks_stale_current_control(
    *,
    typed_closeout: Mapping[str, Any],
    projection: Mapping[str, Any],
    handoff_path: Path,
) -> bool:
    if not typed_closeout:
        return False
    embedded = _observability_mapping(typed_closeout.get("typed_blocker"))
    if not embedded and _non_empty_text(typed_closeout.get("status")) != "typed_blocker":
        return False
    if _terminal_closeout_has_domain_delta(typed_closeout):
        return False
    if _handoff_has_complete_current_transition_readback(projection):
        return False
    has_stale_provider_admission = (
        int(projection.get("provider_admission_pending_count") or 0) > 0
        or bool(_handoff_candidate_list(projection.get("provider_admission_candidates")))
        or any(
            _action_queue_item_has_provider_admission_readback(item)
            for item in projection.get("action_queue") or []
            if isinstance(item, Mapping)
        )
    )
    if not has_stale_provider_admission:
        return False
    closeout_observed_at = _closeout_observed_timestamp(typed_closeout)
    current_control_observed_at = _current_control_observed_timestamp(
        projection=projection,
        handoff_path=handoff_path,
    )
    if closeout_observed_at <= current_control_observed_at:
        return False
    closeout_study = _non_empty_text(typed_closeout.get("study_id"))
    projection_study = _non_empty_text(projection.get("study_id"))
    return closeout_study is None or projection_study is None or closeout_study == projection_study


def _closeout_observed_timestamp(typed_closeout: Mapping[str, Any]) -> float:
    return max(
        _number_value(typed_closeout.get("source_mtime"))
        or _source_path_mtime(Path(_non_empty_text(typed_closeout.get("source_path")) or "")),
        _epoch_seconds(_non_empty_text(typed_closeout.get("generated_at"))),
    )


def _current_control_observed_timestamp(
    *,
    projection: Mapping[str, Any],
    handoff_path: Path,
) -> float:
    generated_at = _epoch_seconds(_non_empty_text(projection.get("generated_at")))
    if generated_at:
        return generated_at
    return _source_path_mtime(handoff_path)


def _epoch_seconds(value: str | None) -> float:
    if value is None:
        return 0.0
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return 0.0
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.timestamp()


def _action_queue_item_has_provider_admission_readback(item: Mapping[str, Any]) -> bool:
    candidate = _action_with_handoff_packet_readback(item)
    if provider_admission_opl_transition_readback(candidate):
        return True
    readback = candidate_opl_transition_readback(candidate)
    outcome = _observability_mapping(readback.get("exactly_one_outcome"))
    return _non_empty_text(outcome.get("outcome_kind")) == LIVE_READBACK_PROVIDER_ADMISSION_OUTCOME


def _typed_closeout_current_work_unit(
    *,
    typed_blocker: Mapping[str, Any],
    typed_closeout: Mapping[str, Any],
) -> dict[str, Any]:
    owner = _non_empty_text(typed_blocker.get("owner")) or _non_empty_text(typed_closeout.get("next_owner"))
    action = _non_empty_text(typed_blocker.get("action_type")) or _non_empty_text(typed_closeout.get("action_type"))
    work_unit = _work_unit_identity(typed_blocker.get("work_unit_id")) or _work_unit_identity(
        typed_closeout.get("work_unit_id")
    )
    fingerprint = _non_empty_text(typed_blocker.get("work_unit_fingerprint")) or _non_empty_text(
        typed_closeout.get("work_unit_fingerprint")
    )
    action_fingerprint = _non_empty_text(typed_blocker.get("action_fingerprint")) or fingerprint
    blocker_type = _non_empty_text(typed_blocker.get("blocker_type")) or _non_empty_text(
        typed_blocker.get("blocked_reason")
    )
    return {
        key: value
        for key, value in {
            "surface_kind": "current_work_unit",
            "schema_version": 1,
            "status": "typed_blocker",
            "study_id": _non_empty_text(typed_closeout.get("study_id")),
            "quest_id": _non_empty_text(typed_closeout.get("study_id")),
            "owner": owner,
            "action_type": action,
            "work_unit_id": work_unit,
            "work_unit_fingerprint": fingerprint,
            "action_fingerprint": action_fingerprint,
            "blocker_type": blocker_type,
            "typed_blocker_ref": _non_empty_text(typed_blocker.get("typed_blocker_ref"))
            or _non_empty_text(typed_closeout.get("receipt_ref"))
            or _non_empty_text(typed_closeout.get("source_path")),
            "state": {
                "state_kind": "typed_blocker",
                "source": "latest_typed_default_executor_closeout",
                "typed_blocker": dict(typed_blocker),
                "stage_attempt_id": _non_empty_text(typed_closeout.get("stage_attempt_id")),
                "stale_queue_or_handoff_can_override": False,
                "provider_completion_is_domain_completion": False,
            },
            "required_output_contract": {
                "owner_receipt_required": True,
                "typed_blocker_allowed": True,
                "provider_completion_is_domain_completion": False,
            },
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_completion_is_domain_completion": False,
            },
        }.items()
        if value not in (None, "", [], {})
    }


def _handoff_has_complete_current_transition_readback(projection: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(projection):
        return True
    non_advancing = _observability_mapping(
        projection.get("domain_progress_transition_non_advancing_apply_readback")
    )
    if non_advancing and candidate_opl_transition_readback(
        {
            **non_advancing,
            "opl_domain_progress_transition_runtime_live_readback": _observability_mapping(
                non_advancing.get("runtime_live_readback")
            ),
        }
    ):
        return True
    return any(
        candidate_opl_transition_readback(candidate)
        or provider_admission_opl_transition_readback(candidate)
        for candidate in projection.get("provider_admission_candidates") or []
        if isinstance(candidate, Mapping)
    )


def _terminal_closeout_has_domain_delta(terminal: Mapping[str, Any]) -> bool:
    if _non_empty_text(terminal.get("closeout_receipt_status")) == "accepted_typed_closeout":
        return True
    if _non_empty_text(terminal.get("owner_receipt_ref")):
        return True
    if _string_list(terminal.get("owner_receipt_refs")):
        return True
    if _non_empty_text(terminal.get("route_outcome")) == "owner_receipt":
        return True
    domain_refs = _observability_mapping(terminal.get("domain_owner_refs"))
    if _non_empty_text(domain_refs.get("route_back_evidence_ref")):
        return True
    paper_stage_log = _observability_mapping(terminal.get("paper_stage_log"))
    if _string_list(paper_stage_log.get("changed_paper_surfaces")):
        return True
    outcome = _non_empty_text(paper_stage_log.get("outcome"))
    if outcome in {"owner_receipt", "owner_receipt_recorded", "handoff_ready", "next_handoff"}:
        return True
    return False


def _typed_closeout_matches_handoff_action(
    *,
    typed_closeout: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    closeout_attempt_id = _non_empty_text(typed_closeout.get("execution_id")) or _non_empty_text(
        typed_closeout.get("stage_attempt_id")
    )
    action_attempt_id = _non_empty_text(action.get("stage_attempt_id")) or _non_empty_text(
        action.get("active_stage_attempt_id")
    )
    if closeout_attempt_id and action_attempt_id:
        return closeout_attempt_id == action_attempt_id
    projection_attempt_id = _non_empty_text(action.get("active_stage_attempt_id")) or _stage_attempt_id_from_active_run_id(
        action.get("active_run_id")
    )
    if closeout_attempt_id and projection_attempt_id:
        return closeout_attempt_id == projection_attempt_id
    closeout_action_type = _non_empty_text(typed_closeout.get("action_type"))
    action_type = _non_empty_text(action.get("action_type"))
    if (
        closeout_action_type is not None
        and action_type == closeout_action_type
        and is_anti_loop_stop_loss_closeout(typed_closeout)
    ):
        return True
    closeout_fingerprints = _identity_values(
        typed_closeout,
        ("work_unit_fingerprint", "action_fingerprint", "fingerprint"),
    )
    action_fingerprints = _identity_values(
        action,
        ("work_unit_fingerprint", "action_fingerprint", "fingerprint"),
    )
    if closeout_fingerprints and action_fingerprints:
        return bool(closeout_fingerprints.intersection(action_fingerprints))
    closeout_work_unit = _work_unit_identity(typed_closeout.get("work_unit_id")) or _work_unit_identity(
        typed_closeout.get("next_work_unit")
    )
    action_work_unit = _work_unit_identity(action.get("work_unit_id")) or _work_unit_identity(
        action.get("next_work_unit")
    )
    return (
        closeout_work_unit is not None
        and action_work_unit == closeout_work_unit
        and closeout_action_type is not None
        and action_type == closeout_action_type
    )


def _identity_values(value: Mapping[str, Any], keys: tuple[str, ...]) -> set[str]:
    return {
        text
        for key in keys
        if (text := _non_empty_text(value.get(key))) is not None
    }


def _typed_closeout_blocker_projection(
    *,
    typed_closeout: Mapping[str, Any],
    matching_action: Mapping[str, Any] | None,
) -> dict[str, Any]:
    embedded = _observability_mapping(typed_closeout.get("typed_blocker"))
    blocked_reason = (
        _non_empty_text(typed_closeout.get("blocked_reason"))
        or _non_empty_text(embedded.get("blocker_type"))
        or _non_empty_text(embedded.get("blocker_kind"))
        or _non_empty_text(embedded.get("reason"))
        or _non_empty_text(embedded.get("blocked_reason"))
        or _non_empty_text(embedded.get("blocker_id"))
    )
    if blocked_reason is None:
        return {}
    owner = (
        _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(embedded.get("required_next_owner"))
        or _non_empty_text(embedded.get("phase_owner"))
        or _non_empty_text(typed_closeout.get("next_owner"))
    )
    if blocked_reason in OPL_RUNTIME_TERMINAL_BLOCKERS:
        owner = "one-person-lab"
    action = _observability_mapping(matching_action)
    blocker = {
        **embedded,
        "blocker_type": blocked_reason,
        "blocked_reason": blocked_reason,
        "owner": owner or "med-autoscience",
        "action_type": _non_empty_text(typed_closeout.get("action_type"))
        or _non_empty_text(action.get("action_type")),
        "work_unit_id": _work_unit_identity(typed_closeout.get("work_unit_id"))
        or _work_unit_identity(_mapping_copy(typed_closeout.get("next_forced_delta")).get("work_unit_id"))
        or _work_unit_identity(action.get("work_unit_id"))
        or _work_unit_identity(action.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(typed_closeout.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "action_fingerprint": _non_empty_text(typed_closeout.get("action_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint")),
        "source_fingerprint": _non_empty_text(typed_closeout.get("source_fingerprint"))
        or _non_empty_text(action.get("source_fingerprint")),
        "idempotency_key": _non_empty_text(typed_closeout.get("idempotency_key"))
        or _non_empty_text(action.get("idempotency_key")),
        "stage_attempt_id": _non_empty_text(typed_closeout.get("stage_attempt_id"))
        or _non_empty_text(action.get("stage_attempt_id"))
        or _non_empty_text(action.get("active_stage_attempt_id")),
        "source_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
        or _non_empty_text(typed_closeout.get("source_path")),
        "typed_blocker_ref": _non_empty_text(typed_closeout.get("receipt_ref"))
        or _non_empty_text(typed_closeout.get("source_path")),
        "closeout_refs": _string_list(typed_closeout.get("closeout_refs")),
    }
    owner_route = _observability_mapping(typed_closeout.get("owner_route"))
    source_refs = _observability_mapping(owner_route.get("source_refs"))
    currentness_basis = _observability_mapping(source_refs.get("owner_route_currentness_basis"))
    if currentness_basis:
        blocker["currentness_basis"] = currentness_basis
    return {key: value for key, value in blocker.items() if value not in (None, "", [], {})}


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _observability_mapping(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _non_empty_text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    if active_attempt_id is None and not _handoff_has_terminal_matching_pending_candidate(
        handoff=handoff,
        terminal=terminal,
    ) and _terminal_closeout_consumed_current_action_projection(
        terminal=terminal,
        projection=handoff,
    ) is None:
        return False
    status = _non_empty_text(terminal.get("status"))
    if status in TERMINAL_STAGE_LOG_STATUSES:
        return True
    return (
        _non_empty_text(terminal.get("source_path")) is not None
        and _non_empty_text(terminal.get("record_path")) is not None
    )


def _handoff_has_terminal_matching_pending_candidate(
    *,
    handoff: Mapping[str, Any],
    terminal: Mapping[str, Any],
) -> bool:
    candidates = [
        *_handoff_candidate_list(handoff.get("provider_admission_candidates")),
        *_handoff_candidate_list(handoff.get("transition_request_candidates")),
    ]
    return bool(
        candidates
        and _terminal_matching_handoff_candidates(
            terminal=terminal,
            candidates=candidates,
        )
    )


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _non_empty_text(handoff.get("active_stage_attempt_id")):
        return text
    return _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))


def _stage_attempt_id_from_active_run_id(value: object) -> str | None:
    active_run_id = _non_empty_text(value)
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _handoff_live_attempt_identity_stale(
    *,
    handoff: Mapping[str, Any],
    live_attempt_handoff: Mapping[str, Any],
) -> bool:
    live_stage_attempt_id = _non_empty_text(live_attempt_handoff.get("active_stage_attempt_id"))
    if live_stage_attempt_id is None:
        return False
    handoff_stage_attempt_id = _non_empty_text(handoff.get("active_stage_attempt_id"))
    if handoff_stage_attempt_id in {None, live_stage_attempt_id}:
        return False
    handoff_run_attempt_id = _stage_attempt_id_from_active_run_id(handoff.get("active_run_id"))
    live_run_attempt_id = _stage_attempt_id_from_active_run_id(live_attempt_handoff.get("active_run_id"))
    return live_stage_attempt_id in {handoff_run_attempt_id, live_run_attempt_id}


def _live_attempt_supersedes_handoff_blocker(handoff: Mapping[str, Any]) -> bool:
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    if blocked_reason in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS:
        return True
    why_not_applied = set(_string_list(handoff.get("why_not_applied")))
    if why_not_applied.intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS):
        return True
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_blockers = set(_string_list(runtime_health.get("blocking_reasons")))
    return bool(runtime_blockers.intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS))
