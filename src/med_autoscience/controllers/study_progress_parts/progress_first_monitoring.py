from __future__ import annotations

from collections.abc import Mapping
from typing import Any


TERMINAL_CLOSEOUT_REQUIRED_USER_STAGE_LOG_FIELDS = (
    "stage_work_done",
    "paper_work_done",
    "changed_stage_surfaces",
    "changed_paper_surfaces",
    "progress_delta_classification",
)
TERMINAL_CLOSEOUT_TELEMETRY_FIELDS = ("duration", "token_usage", "cost")
NEXT_FORCED_DELTA_SUMMARY_KEYS = (
    "required_delta_kind",
    "reason",
    "work_unit_id",
    "eval_id",
    "next_owner",
    "allowed_outcomes",
    "target_surface",
    "target_surface_specificity",
    "missing_explicit_target_surface",
    "target_surface_fallback_reason",
    "target_surface_diagnostic",
    "acceptance_refs",
    "owner_action",
)


def build_progress_first_monitoring_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    launch_policy = _mapping(payload.get("product_entry_launch_policy"))
    execution = _mapping(payload.get("current_execution_envelope"))
    domain_transition = _mapping(payload.get("domain_transition"))
    supervision = _mapping(payload.get("supervision"))
    runtime_health = _mapping(payload.get("runtime_health_snapshot"))
    next_forced_delta = _mapping(payload.get("next_forced_delta"))
    progress_state = _mapping(payload.get("progress_first_sprint_state"))
    latest_terminal_stage_log = _mapping(handoff.get("latest_terminal_stage_log"))
    paper_stage_log = _mapping(latest_terminal_stage_log.get("paper_stage_log"))
    stage_progress_log = _mapping(handoff.get("stage_progress_log"))
    active_run_id = (
        _text(supervision.get("active_run_id"))
        or _text(payload.get("active_run_id"))
        or _text(handoff.get("active_run_id"))
    )
    hydration_work_unit = _explicit_wakeup_hydration_work_unit(launch_policy)
    transition_consumed_owner_action = _transition_consumed_owner_action(domain_transition)
    receipt_consumed = _transition_receipt_consumed(domain_transition)
    next_work_unit = (
        hydration_work_unit
        or (
            _work_unit_projection(domain_transition.get("next_work_unit"))
            if transition_consumed_owner_action
            else None
        )
        or _work_unit_projection(execution.get("next_work_unit"))
        or _work_unit_projection(domain_transition.get("next_work_unit"))
        or _work_unit_from_action_queue(handoff.get("action_queue"))
        or _work_unit_projection(next_forced_delta.get("work_unit_id"))
    )
    typed_blocker = (
        {}
        if transition_consumed_owner_action
        else _mapping(execution.get("typed_blocker"))
        or _mapping(domain_transition.get("typed_blocker"))
        or _terminal_closeout_typed_blocker_projection(
            latest_terminal_stage_log=latest_terminal_stage_log,
            paper_stage_log=paper_stage_log,
        )
    )
    current_blockers = (
        []
        if transition_consumed_owner_action
        else _current_blockers(payload=payload, typed_blocker=typed_blocker, paper_stage_log=paper_stage_log)
    )
    running_provider_attempt = _bool_or_none(handoff.get("running_provider_attempt"))
    state_kind = "executable_owner_action" if transition_consumed_owner_action else _text(execution.get("state_kind"))
    if state_kind is None:
        if receipt_consumed:
            state_kind = "receipt_consumed"
        else:
            state_kind = "running_provider_attempt" if running_provider_attempt else "observability_only"
    return {
        "surface": "progress_first_monitoring_summary",
        "schema_version": 1,
        "authority": "refs_only_observability",
        "study_id": _text(payload.get("study_id")),
        "generated_at": _text(payload.get("generated_at")),
        "current_stage": _text(payload.get("current_stage")),
        "paper_stage": _text(payload.get("paper_stage")),
        "active_run_id": active_run_id,
        "active_stage_attempt_id": _text(handoff.get("active_stage_attempt_id")),
        "active_workflow_id": _text(handoff.get("active_workflow_id")),
        "running_provider_attempt": running_provider_attempt,
        "worker_liveness": {
            "health_status": _text(supervision.get("health_status"))
            or _text(_mapping(handoff.get("runtime_health")).get("health_status"))
            or _text(runtime_health.get("attempt_state"))
            or _text(runtime_health.get("worker_liveness_state")),
            "runtime_liveness_status": _text(_mapping(handoff.get("runtime_health")).get("runtime_liveness_status")),
            "worker_liveness_state": _text(runtime_health.get("worker_liveness_state")),
            "supervisor_tick_status": _text(supervision.get("supervisor_tick_status")),
        },
        "execution_state_kind": "owner_handoff_hydration" if hydration_work_unit is not None else state_kind,
        "next_owner": (
            _explicit_wakeup_hydration_owner(launch_policy)
            or (_text(domain_transition.get("owner")) if transition_consumed_owner_action else None)
            or _text(execution.get("owner"))
            or _text(domain_transition.get("owner"))
            or _text(handoff.get("next_owner"))
            or _text(progress_state.get("next_owner"))
        ),
        "route_target": _text(domain_transition.get("route_target")),
        "controller_action": _text(domain_transition.get("controller_action")) or _text(payload.get("runtime_decision")),
        "next_work_unit": next_work_unit,
        "owner_handoff_hydration": _owner_handoff_hydration_projection(launch_policy),
        "typed_blocker": typed_blocker or None,
        "current_blockers": current_blockers,
        "progress_delta_classification": _text(payload.get("progress_delta_classification"))
        or _text(progress_state.get("classification")),
        "paper_progress_delta_counted": bool(progress_state.get("paper_progress_delta_counted")),
        "platform_repair_delta_counted": bool(progress_state.get("platform_repair_delta_counted")),
        "next_forced_delta": _compact_mapping(
            next_forced_delta,
            NEXT_FORCED_DELTA_SUMMARY_KEYS,
        ),
        "stage_progress_log": _compact_mapping(
            stage_progress_log,
            (
                "attempt_count",
                "completed_attempt_count",
                "blocked_attempt_count",
                "activity_event_count",
                "runner_progress_event_count",
                "missing_usage_telemetry_attempt_count",
                "temporal_attempt_count",
                "temporal_webui_ref_count",
                "attempt_refs",
            ),
        ),
        "latest_terminal_stage": _latest_terminal_stage_summary(
            latest_terminal_stage_log=latest_terminal_stage_log,
            paper_stage_log=paper_stage_log,
            next_forced_delta=next_forced_delta,
        ),
        "dispatch_consumption": _dispatch_consumption_summary(
            handoff=handoff,
            execution=execution,
            domain_transition=domain_transition,
        ),
        "foreground_write_policy": _foreground_write_policy(payload.get("execution_owner_guard")),
        "source_refs": _source_refs(payload.get("refs"), handoff=handoff, latest_terminal_stage_log=latest_terminal_stage_log),
        "authority_boundary": {
            "refs_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _dispatch_consumption_summary(
    *,
    handoff: Mapping[str, Any],
    execution: Mapping[str, Any],
    domain_transition: Mapping[str, Any],
) -> dict[str, Any] | None:
    explicit = _mapping(handoff.get("dispatch_consumption")) or _mapping(execution.get("dispatch_consumption"))
    if explicit:
        return explicit
    completion_receipt = _mapping(domain_transition.get("completion_receipt_consumption"))
    execution_receipt = _mapping(domain_transition.get("default_executor_execution_receipt_consumption"))
    if completion_receipt or execution_receipt:
        status = (
            _text(completion_receipt.get("consumption_status"))
            or _text(completion_receipt.get("status"))
            or _text(execution_receipt.get("consumption_status"))
            or _text(execution_receipt.get("status"))
            or "receipt_consumed"
        )
        return {
            "consumption_status": status,
            "receipt_ref": _text(completion_receipt.get("receipt_ref")) or _text(execution_receipt.get("receipt_ref")),
            "execution_status": _text(execution_receipt.get("execution_status")),
            "action_fingerprint": _text(completion_receipt.get("action_fingerprint"))
            or _text(execution_receipt.get("action_fingerprint")),
        }
    queue_item = _first_action_queue_item(handoff.get("action_queue"))
    if queue_item is None:
        return None
    return {
        "consumption_status": _text(queue_item.get("consumption_status")) or "unconsumed",
        "action_fingerprint": _text(queue_item.get("action_fingerprint"))
        or _text(queue_item.get("work_unit_fingerprint"))
        or _text(queue_item.get("source_fingerprint")),
        "receipt_ref": _text(queue_item.get("receipt_ref")),
        "execution_status": _text(queue_item.get("execution_status")),
        "unconsumed_duration_hours": _numeric(queue_item.get("queue_age_hours"))
        or _numeric(queue_item.get("unconsumed_duration_hours")),
    }


def _transition_consumed_owner_action(domain_transition: Mapping[str, Any]) -> bool:
    if _mapping(domain_transition.get("typed_blocker")):
        return False
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _consumed_receipt_matches_transition_work_unit(domain_transition=domain_transition, completion=completion):
        return False
    return (
        _text(domain_transition.get("owner")) is not None
        or _text(domain_transition.get("controller_action")) is not None
        or _work_unit_projection(domain_transition.get("next_work_unit")) is not None
    )


def _transition_receipt_consumed(domain_transition: Mapping[str, Any]) -> bool:
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    execution = _mapping(domain_transition.get("default_executor_execution_receipt_consumption"))
    status = (
        _text(completion.get("consumption_status"))
        or _text(completion.get("status"))
        or _text(execution.get("consumption_status"))
        or _text(execution.get("status"))
    )
    return status in {"consumed", "receipt_consumed", "completed"}


def _consumed_receipt_matches_transition_work_unit(
    *,
    domain_transition: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> bool:
    if _text(completion.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    if _text(domain_transition.get("decision_type")) != "ai_reviewer_re_eval":
        return False
    if _text(domain_transition.get("controller_action")) != "return_to_ai_reviewer_workflow":
        return False
    work_unit = _work_unit_projection(domain_transition.get("next_work_unit"))
    work_unit_id = _text(_mapping(work_unit).get("unit_id"))
    return bool(work_unit_id and work_unit_id.startswith("produce_ai_reviewer_publication_eval_record"))


def _first_action_queue_item(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if isinstance(item, Mapping):
            return dict(item)
    return None


def _latest_terminal_stage_summary(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> dict[str, Any] | None:
    if not latest_terminal_stage_log:
        return None
    semantic_completeness = _stage_semantic_completeness(paper_stage_log)
    telemetry_completeness = _stage_telemetry_completeness(latest_terminal_stage_log)
    progress_delta_classification = _text(paper_stage_log.get("progress_delta_classification"))
    missing_user_fields = _missing_user_stage_log_fields(
        latest_terminal_stage_log=latest_terminal_stage_log,
        paper_stage_log=paper_stage_log,
    )
    missing_telemetry_fields = _missing_telemetry_fields(latest_terminal_stage_log)
    return {
        "stage_attempt_id": _text(latest_terminal_stage_log.get("stage_attempt_id")),
        "stage_id": _text(latest_terminal_stage_log.get("stage_id")),
        "action_type": _text(latest_terminal_stage_log.get("action_type")),
        "status": _text(latest_terminal_stage_log.get("status")),
        "stage_name": _text(paper_stage_log.get("stage_name")),
        "problem_summary": _text(paper_stage_log.get("problem_summary")),
        "stage_goal": _text(paper_stage_log.get("stage_goal")),
        "outcome": _text(paper_stage_log.get("outcome")),
        "progress_delta_classification": progress_delta_classification,
        "stage_work_done": _text_list(paper_stage_log.get("stage_work_done")),
        "paper_work_done": _text_list(paper_stage_log.get("paper_work_done")),
        "changed_stage_surfaces": _text_list(paper_stage_log.get("changed_stage_surfaces")),
        "changed_paper_surfaces": _text_list(paper_stage_log.get("changed_paper_surfaces")),
        "remaining_blockers": _text_list(paper_stage_log.get("remaining_blockers")),
        "evidence_refs": _text_list(paper_stage_log.get("evidence_refs")),
        "missing_user_stage_log_fields": missing_user_fields,
        "observability_status": _text(latest_terminal_stage_log.get("observability_status"))
        or ("observed" if not missing_telemetry_fields else "missing"),
        "missing_observability_fields": missing_telemetry_fields,
        "semantic_completeness": semantic_completeness,
        "duration": _mapping(latest_terminal_stage_log.get("duration")) or None,
        "token_usage": _mapping(latest_terminal_stage_log.get("token_usage")) or None,
        "cost": _mapping(latest_terminal_stage_log.get("cost")) or None,
        "telemetry_completeness": telemetry_completeness,
        "closeout_refs": _text_list(latest_terminal_stage_log.get("closeout_refs")),
        "terminal_closeout_semantic_completeness": _terminal_closeout_semantic_completeness(
            latest_terminal_stage_log=latest_terminal_stage_log,
            paper_stage_log=paper_stage_log,
            next_forced_delta=next_forced_delta,
            progress_delta_classification=progress_delta_classification,
            missing_user_fields=missing_user_fields,
            missing_telemetry_fields=missing_telemetry_fields,
        ),
        "source_path": _text(latest_terminal_stage_log.get("source_path")),
    }


def _terminal_closeout_semantic_completeness(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
    progress_delta_classification: str | None,
    missing_user_fields: list[str],
    missing_telemetry_fields: list[str],
) -> dict[str, Any]:
    changed_stage_status = _field_presence_status(paper_stage_log, "changed_stage_surfaces")
    changed_paper_status = _field_presence_status(paper_stage_log, "changed_paper_surfaces")
    changed_surfaces_status = (
        "missing"
        if changed_stage_status == "missing" and changed_paper_status == "missing"
        else "present"
    )
    typed_blocker = _terminal_closeout_typed_blocker(
        latest_terminal_stage_log=latest_terminal_stage_log,
        missing_user_fields=missing_user_fields,
        missing_telemetry_fields=missing_telemetry_fields,
        changed_surfaces_status=changed_surfaces_status,
        progress_delta_classification=progress_delta_classification,
    )
    return {
        "status": "complete" if typed_blocker is None else "typed_blocker",
        "required_user_stage_log_fields": "complete" if not missing_user_fields else "missing",
        "missing_user_stage_log_fields": missing_user_fields,
        "changed_surfaces": changed_surfaces_status,
        "changed_stage_surfaces": changed_stage_status,
        "changed_paper_surfaces": changed_paper_status,
        "progress_delta_classification": progress_delta_classification or "missing",
        "telemetry": "complete" if not missing_telemetry_fields else "missing",
        "missing_telemetry_fields": missing_telemetry_fields,
        "typed_blocker": typed_blocker,
        "typed_blocker_diagnostic": _text(latest_terminal_stage_log.get("diagnostic")),
        "next_forced_delta": (
            _compact_mapping(next_forced_delta, NEXT_FORCED_DELTA_SUMMARY_KEYS) or None
            if typed_blocker is not None
            else None
        ),
    }


def _terminal_closeout_typed_blocker(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    missing_user_fields: list[str],
    missing_telemetry_fields: list[str],
    changed_surfaces_status: str,
    progress_delta_classification: str | None,
) -> str | None:
    explicit = _text(latest_terminal_stage_log.get("typed_blocker_reason"))
    if explicit is not None:
        return explicit
    if (
        missing_user_fields
        or missing_telemetry_fields
        or changed_surfaces_status == "missing"
        or progress_delta_classification is None
    ):
        return "typed_closeout_packet_required"
    return None


def _terminal_closeout_typed_blocker_projection(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> dict[str, Any]:
    if not latest_terminal_stage_log:
        return {}
    missing_user_fields = _missing_user_stage_log_fields(
        latest_terminal_stage_log=latest_terminal_stage_log,
        paper_stage_log=paper_stage_log,
    )
    missing_telemetry_fields = _missing_telemetry_fields(latest_terminal_stage_log)
    changed_stage_status = _field_presence_status(paper_stage_log, "changed_stage_surfaces")
    changed_paper_status = _field_presence_status(paper_stage_log, "changed_paper_surfaces")
    changed_surfaces_status = (
        "missing"
        if changed_stage_status == "missing" and changed_paper_status == "missing"
        else "present"
    )
    blocker_id = _terminal_closeout_typed_blocker(
        latest_terminal_stage_log=latest_terminal_stage_log,
        missing_user_fields=missing_user_fields,
        missing_telemetry_fields=missing_telemetry_fields,
        changed_surfaces_status=changed_surfaces_status,
        progress_delta_classification=_text(paper_stage_log.get("progress_delta_classification")),
    )
    if blocker_id is None:
        return {}
    return {
        "blocker_id": blocker_id,
        "blocker_type": "provider_completed_without_typed_closeout",
        "owner": "one-person-lab",
        "summary": "Provider completion needs a typed closeout packet.",
    }


def _missing_user_stage_log_fields(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> list[str]:
    explicit = _text_list(latest_terminal_stage_log.get("missing_user_stage_log_fields"))
    if explicit:
        return explicit
    return [
        field
        for field in TERMINAL_CLOSEOUT_REQUIRED_USER_STAGE_LOG_FIELDS
        if _user_stage_log_field_missing(paper_stage_log, field)
    ]


def _missing_telemetry_fields(latest_terminal_stage_log: Mapping[str, Any]) -> list[str]:
    explicit = _text_list(latest_terminal_stage_log.get("missing_observability_fields"))
    if explicit:
        return explicit
    return [
        field
        for field in TERMINAL_CLOSEOUT_TELEMETRY_FIELDS
        if not _mapping(latest_terminal_stage_log.get(field))
    ]


def _user_stage_log_field_missing(paper_stage_log: Mapping[str, Any], field: str) -> bool:
    if field not in paper_stage_log:
        return True
    if field in {"changed_stage_surfaces", "changed_paper_surfaces"}:
        return False
    value = paper_stage_log.get(field)
    return value in (None, "", [], {})


def _field_presence_status(paper_stage_log: Mapping[str, Any], field: str) -> str:
    if field not in paper_stage_log:
        return "missing"
    values = _text_list(paper_stage_log.get(field))
    return "present" if values else "present_empty"


def _stage_semantic_completeness(paper_stage_log: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = (
        "stage_name",
        "problem_summary",
        "stage_goal",
        "stage_work_done",
        "changed_stage_surfaces",
        "outcome",
        "remaining_blockers",
        "evidence_refs",
    )
    aliases = {
        "stage_work_done": ("stage_work_done", "paper_work_done"),
        "changed_stage_surfaces": ("changed_stage_surfaces", "changed_paper_surfaces"),
    }
    missing = [
        field
        for field in required_fields
        if not _has_stage_semantic_field(paper_stage_log, aliases.get(field, (field,)))
    ]
    return {
        "status": "complete" if not missing else "missing_required_fields",
        "required_fields": list(required_fields),
        "missing_fields": missing,
    }


def _stage_telemetry_completeness(latest_terminal_stage_log: Mapping[str, Any]) -> dict[str, Any]:
    required_fields = ("duration", "token_usage", "cost")
    missing = [field for field in required_fields if not _mapping(latest_terminal_stage_log.get(field))]
    return {
        "status": "complete" if not missing else "missing_required_fields",
        "required_fields": list(required_fields),
        "missing_fields": missing,
    }


def _has_stage_semantic_field(payload: Mapping[str, Any], keys: tuple[str, ...]) -> bool:
    for key in keys:
        value = payload.get(key)
        if _text(value) is not None:
            return True
        if _text_list(value):
            return True
    return False


def _foreground_write_policy(value: object) -> dict[str, Any]:
    guard = _mapping(value)
    supervisor_only = bool(guard.get("supervisor_only"))
    return {
        "supervisor_only": supervisor_only,
        "foreground_can_write_runtime_owned_surfaces": False if supervisor_only else None,
        "rule": (
            "supervisor_only_no_runtime_owned_writes"
            if supervisor_only
            else "follow_mas_owner_controller_runtime_path"
        ),
    }


def _current_blockers(
    *,
    payload: Mapping[str, Any],
    typed_blocker: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> list[str]:
    values: list[object] = []
    values.extend(payload.get("current_blockers") or [])
    values.extend(paper_stage_log.get("remaining_blockers") or [])
    for key in ("blocker_id", "blocker_type", "summary"):
        if key in typed_blocker:
            values.append(typed_blocker[key])
    return _dedupe_text(values)[:12]


def _work_unit_from_action_queue(value: object) -> dict[str, Any] | str | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if not isinstance(item, Mapping):
            continue
        unit = _work_unit_projection(item.get("next_work_unit"))
        if unit is not None:
            return unit
        for key in ("controller_work_unit_id", "work_unit_id", "action_type"):
            text = _text(item.get(key))
            if text is not None:
                return text
    return None


def _work_unit_projection(value: object) -> dict[str, Any] | str | None:
    if isinstance(value, Mapping):
        return _compact_mapping(
            value,
            (
                "unit_id",
                "lane",
                "summary",
                "owner",
                "route_target",
                "action_type",
            ),
        ) or dict(value)
    text = _text(value)
    return text


def _explicit_wakeup_hydration_work_unit(launch_policy: Mapping[str, Any]) -> str | None:
    if launch_policy.get("explicit_user_wakeup_recorded") is not True:
        return None
    if launch_policy.get("owner_handoff_hydration_required") is not True:
        return None
    return _text(launch_policy.get("owner_handoff_hydration_action")) or "hydrate_opl_owner_route_from_explicit_resume"


def _explicit_wakeup_hydration_owner(launch_policy: Mapping[str, Any]) -> str | None:
    if _explicit_wakeup_hydration_work_unit(launch_policy) is None:
        return None
    return _text(launch_policy.get("owner_handoff_hydration_owner")) or "one-person-lab"


def _owner_handoff_hydration_projection(launch_policy: Mapping[str, Any]) -> dict[str, Any] | None:
    work_unit = _explicit_wakeup_hydration_work_unit(launch_policy)
    if work_unit is None:
        return None
    return {
        "required": True,
        "owner": _explicit_wakeup_hydration_owner(launch_policy),
        "action": work_unit,
        "explicit_user_wakeup_ref": _text(launch_policy.get("explicit_user_wakeup_ref")),
        "study_truth_snapshot_ref": _text(launch_policy.get("study_truth_snapshot_ref")),
    }


def _source_refs(
    value: object,
    *,
    handoff: Mapping[str, Any],
    latest_terminal_stage_log: Mapping[str, Any],
) -> list[str]:
    refs: list[object] = []
    if isinstance(value, Mapping):
        refs.extend(value.values())
    refs.append(handoff.get("source_path"))
    refs.append(latest_terminal_stage_log.get("source_path"))
    refs.extend(latest_terminal_stage_log.get("closeout_refs") or [])
    return _dedupe_text(refs)[:20]


def _compact_mapping(value: object, keys: tuple[str, ...]) -> dict[str, Any]:
    if not isinstance(value, Mapping):
        return {}
    return {key: value[key] for key in keys if key in value}


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _numeric(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return _dedupe_text(value)


def _dedupe_text(values: list[object] | tuple[object, ...] | set[object]) -> list[str]:
    result: list[str] = []
    for item in values:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


def _bool_or_none(value: object) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    return bool(value)


__all__ = ["build_progress_first_monitoring_summary"]
