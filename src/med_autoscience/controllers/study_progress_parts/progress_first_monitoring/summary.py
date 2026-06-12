from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.progress_first_receipt_identity import (
    canonical_work_unit_identity_from_completion,
    consumed_ai_reviewer_receipt_matches_transition_work_unit,
    gate_clearing_batch_receipt_consumption_for_transition,
)

from ..current_executable_owner_action import build_current_executable_owner_action
from ..owner_action_admission import (
    build_owner_action_admission_projection,
    provider_attempt_proof_for_current_action,
)
from ...current_work_unit import action_supersedes_typed_blocker
from .artifact_first import (
    artifact_first_owner_action as _artifact_first_owner_action,
    current_action_from_stage_artifact_index as _current_action_from_stage_artifact_index,
    stage_artifact_index_has_precedence_evidence as _stage_artifact_index_has_precedence_evidence,
    stage_artifact_index_monitoring_projection as _stage_artifact_index_monitoring_projection,
    terminal_publication_gate_action as _terminal_publication_gate_action,
)
from .primitives import (
    _bool_or_none,
    _compact_mapping,
    _dedupe_text,
    _first_text,
    _mapping,
    _numeric,
    _sequence,
    _text,
)
from .terminal_closeout import (
    NEXT_FORCED_DELTA_SUMMARY_KEYS,
    _latest_terminal_stage_summary,
    _terminal_closeout_typed_blocker_projection,
    _terminal_progress_delta_classification,
)


def build_progress_first_monitoring_summary(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping(payload.get("opl_current_control_state_handoff"))
    launch_policy = _mapping(payload.get("product_entry_launch_policy"))
    execution = _mapping(payload.get("current_execution_envelope"))
    domain_transition = _mapping(payload.get("domain_transition"))
    supervision = _mapping(payload.get("supervision"))
    runtime_health = _mapping(payload.get("runtime_health_snapshot"))
    next_forced_delta = _mapping(payload.get("next_forced_delta"))
    stage_artifact_action = _current_action_from_stage_artifact_index(payload)
    progress_state = _mapping(payload.get("progress_first_sprint_state"))
    latest_terminal_stage_log = _mapping(handoff.get("latest_terminal_stage_log"))
    paper_stage_log = _mapping(latest_terminal_stage_log.get("paper_stage_log"))
    stage_progress_log = _mapping(handoff.get("stage_progress_log"))
    raw_running_provider_attempt = _bool_or_none(handoff.get("running_provider_attempt"))
    strict_running_provider_liveness = _strict_running_provider_liveness(handoff)
    running_provider_attempt = (
        True
        if strict_running_provider_liveness
        else False
        if raw_running_provider_attempt is True
        else raw_running_provider_attempt
    )
    active_run_id = _running_provider_attempt_ref(
        running_provider_attempt=running_provider_attempt,
        handoff=handoff,
        key="active_run_id",
    )
    active_stage_attempt_id = _running_provider_attempt_ref(
        running_provider_attempt=running_provider_attempt,
        handoff=handoff,
        key="active_stage_attempt_id",
    )
    active_workflow_id = _running_provider_attempt_ref(
        running_provider_attempt=running_provider_attempt,
        handoff=handoff,
        key="active_workflow_id",
    )
    hydration_work_unit = _explicit_wakeup_hydration_work_unit(launch_policy)
    transition_consumed_owner_action = _transition_consumed_owner_action(domain_transition)
    transition_consumed_same_work_unit = _transition_consumed_same_ai_reviewer_work_unit(domain_transition)
    gate_clearing_dispatch_consumption = _gate_clearing_batch_dispatch_consumption(payload)
    receipt_consumed = _transition_receipt_consumed(domain_transition) or gate_clearing_dispatch_consumption is not None
    handoff_owner_action = _first_current_action_queue_item(handoff.get("action_queue"))
    terminal_closeout_blocker = _terminal_closeout_typed_blocker_projection(
        latest_terminal_stage_log=latest_terminal_stage_log,
        paper_stage_log=paper_stage_log,
    )
    canonical_current_work_unit = _mapping(payload.get("current_work_unit"))
    canonical_work_unit_state = _mapping(canonical_current_work_unit.get("state"))
    canonical_typed_blocker = _mapping(canonical_work_unit_state.get("typed_blocker"))
    raw_typed_blocker = (
        canonical_typed_blocker
        or _mapping(execution.get("typed_blocker"))
        or _mapping(domain_transition.get("typed_blocker"))
        or _mapping(handoff.get("typed_blocker"))
        or terminal_closeout_blocker
    )
    terminal_domain_blocker = _terminal_closeout_domain_typed_blocker(
        latest_terminal_stage_log=latest_terminal_stage_log,
        paper_stage_log=paper_stage_log,
    )
    if terminal_domain_blocker and not raw_typed_blocker:
        raw_typed_blocker = terminal_domain_blocker
    payload_current_action = _mapping(payload.get("current_executable_owner_action"))
    non_artifact_current_action = _mapping(
        build_current_executable_owner_action({**payload, "stage_artifact_index": {}})
    )
    stage_kernel_current_action = (
        payload_current_action
        if _stage_kernel_owner_action(payload_current_action)
        else (
            non_artifact_current_action
            if _stage_kernel_owner_action(non_artifact_current_action)
            else {}
        )
    )
    repair_progress_current_action = (
        payload_current_action
        if _repair_progress_owner_action(payload_current_action)
        else (
            non_artifact_current_action
            if _repair_progress_owner_action(non_artifact_current_action)
            else {}
        )
    )
    gate_followthrough_current_action = (
        payload_current_action
        if _gate_followthrough_owner_action(payload_current_action)
        else (
            non_artifact_current_action
            if _gate_followthrough_owner_action(non_artifact_current_action)
            else {}
        )
    )
    publication_eval_current_action = (
        payload_current_action
        if _publication_eval_readiness_blocker_repair_action(payload_current_action)
        else (
            non_artifact_current_action
            if _publication_eval_readiness_blocker_repair_action(non_artifact_current_action)
            else {}
        )
    )
    terminal_blocks_owner_actions = bool(terminal_domain_blocker) or _canonical_current_work_unit_terminal_blocker(
        canonical_current_work_unit
    )
    artifact_first_supersedes_blocker = (
        bool(stage_artifact_action)
        and not terminal_blocks_owner_actions
        and not _terminal_publication_gate_action(stage_artifact_action)
        and (
        not stage_kernel_current_action
        and not repair_progress_current_action
        and not publication_eval_current_action
        and (
            not raw_typed_blocker
            or _stage_artifact_index_has_precedence_evidence(
                payload.get("stage_artifact_index"),
                typed_blocker=raw_typed_blocker,
            )
        )
        )
    )
    if _artifact_first_owner_action(payload_current_action) and not artifact_first_supersedes_blocker:
        payload_current_action = {}
    effective_stage_artifact_action = stage_artifact_action if artifact_first_supersedes_blocker else {}
    current_action = (
        stage_kernel_current_action
        or repair_progress_current_action
        or gate_followthrough_current_action
        or publication_eval_current_action
        or effective_stage_artifact_action
        or payload_current_action
        or non_artifact_current_action
    )
    current_work_unit_status = _text(canonical_current_work_unit.get("status"))
    canonical_typed_blocker_blocks_liveness = _canonical_typed_blocker_blocks_liveness(
        current_work_unit=canonical_current_work_unit,
        execution=execution,
        domain_transition=domain_transition,
        transition_consumed_owner_action=transition_consumed_owner_action,
        transition_consumed_same_work_unit=transition_consumed_same_work_unit,
        gate_clearing_dispatch_consumption=gate_clearing_dispatch_consumption,
    )
    if canonical_typed_blocker_blocks_liveness:
        running_provider_attempt = False
        active_run_id = None
        active_stage_attempt_id = None
        active_workflow_id = None
    current_action_supersedes_canonical_typed_blocker = _current_action_supersedes_canonical_typed_blocker(
        current_action=current_action,
        canonical_current_work_unit=canonical_current_work_unit,
        canonical_work_unit_state=canonical_work_unit_state,
        progress=payload,
    )
    if (
        current_work_unit_status in {"typed_blocker", "blocked_current_work_unit"}
        and _next_forced_delta_owner_action(current_action)
        and not current_action_supersedes_canonical_typed_blocker
    ):
        current_action = {}
    owner_action_supersedes_envelope_blocker = (
        handoff_owner_action is not None
        or _gate_followthrough_owner_action(current_action)
        or _publication_eval_readiness_blocker_repair_action(current_action)
        or _consumed_ai_reviewer_receipt_supersedes_envelope_blocker(
            domain_transition=domain_transition,
            raw_typed_blocker=raw_typed_blocker,
        )
        or (
            _next_forced_delta_owner_action(current_action)
            and transition_consumed_owner_action
            and not transition_consumed_same_work_unit
            and gate_clearing_dispatch_consumption is None
        )
    )
    envelope_blocks_current_action = _envelope_typed_blocker_blocks_current_action(
        execution=execution,
        raw_typed_blocker=raw_typed_blocker,
        artifact_first_supersedes_blocker=artifact_first_supersedes_blocker,
        current_action=current_action,
    ) and not (
        owner_action_supersedes_envelope_blocker
    )
    if envelope_blocks_current_action:
        current_action = {}
        handoff_owner_action = None
        handoff_for_admission = {**handoff, "action_queue": []}
    else:
        handoff_for_admission = handoff
    current_action_provider_attempt_proof = provider_attempt_proof_for_current_action(
        handoff=handoff_for_admission,
        current_action=current_action,
    )
    current_action_running_provider_attempt = bool(
        strict_running_provider_liveness and current_action_provider_attempt_proof
    )
    artifact_first_owner_action = _artifact_first_owner_action(current_action)
    canonical_work_unit_for_aliases = (
        {}
        if current_action_supersedes_canonical_typed_blocker
        else canonical_current_work_unit
    )
    next_work_unit = (
        hydration_work_unit
        or _work_unit_projection(canonical_work_unit_for_aliases.get("work_unit_id"))
        or _work_unit_from_current_action(current_action)
        or _work_unit_from_action(handoff_owner_action)
        or (
            _work_unit_id(domain_transition.get("next_work_unit"))
            if (
                transition_consumed_owner_action
                and not envelope_blocks_current_action
                and gate_clearing_dispatch_consumption is None
            )
            else None
        )
        or _work_unit_projection(execution.get("next_work_unit"))
        or _work_unit_projection(raw_typed_blocker.get("work_unit_id"))
        or (
            _work_unit_projection(domain_transition.get("next_work_unit"))
            if not envelope_blocks_current_action
            else None
        )
        or _work_unit_from_action_queue(handoff.get("action_queue"))
        or _work_unit_projection(next_forced_delta.get("work_unit_id"))
    )
    typed_blocker = (
        {}
        if running_provider_attempt is True
        or artifact_first_supersedes_blocker
        or _repair_progress_owner_action(current_action)
        or _gate_followthrough_owner_action(current_action)
        or _publication_eval_readiness_blocker_repair_action(current_action)
        or _next_forced_delta_owner_action(current_action)
        or handoff_owner_action is not None
        or (
            transition_consumed_owner_action
            and not envelope_blocks_current_action
            and not transition_consumed_same_work_unit
            and gate_clearing_dispatch_consumption is None
        )
        else raw_typed_blocker
    )
    if terminal_domain_blocker and not canonical_typed_blocker:
        typed_blocker = terminal_domain_blocker
    progress_delta_classification = (
        _text(payload.get("progress_delta_classification"))
        or _text(progress_state.get("classification"))
        or _terminal_progress_delta_classification(paper_stage_log)
    )
    owner_action_admission = build_owner_action_admission_projection(
        payload=payload,
        current_action=current_action,
        handoff=handoff_for_admission,
        stage_progress_log=stage_progress_log,
        latest_terminal_stage_log=latest_terminal_stage_log,
    )
    owner_action_visible = (
        artifact_first_owner_action
        or _stage_kernel_owner_action(current_action)
        or _stage_native_owner_action(current_action)
        or _repair_progress_owner_action(current_action)
        or _gate_followthrough_owner_action(current_action)
        or _publication_eval_readiness_blocker_repair_action(current_action)
        or _next_forced_delta_owner_action(current_action)
        or handoff_owner_action is not None
        or (
            transition_consumed_owner_action
            and not envelope_blocks_current_action
            and gate_clearing_dispatch_consumption is None
        )
    )
    current_blockers = (
        []
        if running_provider_attempt is True or (owner_action_visible and not typed_blocker)
        else _canonical_typed_blocker_current_blockers(canonical_typed_blocker)
        if canonical_typed_blocker
        else _current_blockers(
            payload=payload,
            typed_blocker=typed_blocker,
            paper_stage_log=paper_stage_log,
        )
    )
    if current_action_running_provider_attempt:
        state_kind = "running_provider_attempt"
    elif owner_action_visible:
        state_kind = "executable_owner_action"
    else:
        state_kind = _text(execution.get("state_kind"))
    if (
        current_work_unit_status in {"executable_owner_action", "running_provider_attempt", "typed_blocker"}
        and not current_action_supersedes_canonical_typed_blocker
    ):
        state_kind = current_work_unit_status
    if state_kind is None:
        if receipt_consumed:
            state_kind = "receipt_consumed"
        else:
            state_kind = "running_provider_attempt" if running_provider_attempt else "observability_only"
    summary_next_forced_delta = _next_forced_delta_from_current_work_unit(
        canonical_current_work_unit,
        fallback=next_forced_delta,
    )
    return {
        "surface": "progress_first_monitoring_summary",
        "schema_version": 1,
        "authority": "refs_only_observability",
        "study_id": _text(payload.get("study_id")),
        "generated_at": _text(payload.get("generated_at")),
        "current_stage": _text(payload.get("current_stage")),
        "paper_stage": _text(payload.get("paper_stage")),
        "active_run_id": active_run_id,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_workflow_id": active_workflow_id,
        "running_provider_attempt": running_provider_attempt,
        "worker_liveness": {
            "health_status": _text(supervision.get("health_status"))
            or _text(_mapping(handoff.get("runtime_health")).get("health_status"))
            or _text(runtime_health.get("attempt_state"))
            or _text(runtime_health.get("worker_liveness_state")),
            "runtime_liveness_status": _text(_mapping(handoff.get("runtime_health")).get("runtime_liveness_status")),
            "worker_liveness_state": _text(runtime_health.get("worker_liveness_state")),
            "supervisor_tick_status": _text(supervision.get("supervisor_tick_status")),
            "stale_active_run_id": _stale_active_run_id(
                running_provider_attempt=running_provider_attempt,
                payload=payload,
                supervision=supervision,
                handoff=handoff,
            ),
        },
        "execution_state_kind": "owner_handoff_hydration" if hydration_work_unit is not None else state_kind,
        "owner_action_current": _current_work_unit_owner_action_current(
            canonical_current_work_unit,
            state_kind=state_kind,
            current_action=current_action,
            action_supersedes_canonical_typed_blocker=current_action_supersedes_canonical_typed_blocker,
        ),
        "next_owner": (
            _explicit_wakeup_hydration_owner(launch_policy)
            or (
                None
                if _publication_eval_readiness_blocker_repair_action(current_action)
                else _text(canonical_current_work_unit.get("owner"))
            )
            or _text(current_action.get("next_owner"))
            or _owner_from_action(handoff_owner_action)
            or (
                _text(domain_transition.get("owner"))
                if (
                    transition_consumed_owner_action
                    and not envelope_blocks_current_action
                    and gate_clearing_dispatch_consumption is None
                )
                else None
            )
            or _text(execution.get("owner"))
            or _text(domain_transition.get("owner"))
            or _text(typed_blocker.get("owner"))
            or _text(handoff.get("next_owner"))
            or _text(progress_state.get("next_owner"))
        ),
        "route_target": (
            _text(canonical_current_work_unit.get("route_target"))
            or _text(current_action.get("route_target"))
            or (
                _text(handoff_owner_action.get("route_target"))
                if handoff_owner_action is not None
                else (
                    _text(domain_transition.get("route_target"))
                    if not envelope_blocks_current_action
                    else None
                )
            )
        ),
        "controller_action": (
            (
                None
                if _publication_eval_readiness_blocker_repair_action(current_action)
                else _text(canonical_current_work_unit.get("action_type"))
            )
            or _first_text(current_action.get("allowed_actions"))
            or _text(current_action.get("action_type"))
            or (
                _text(handoff_owner_action.get("action_type"))
                if handoff_owner_action is not None
                else None
            )
            or (
                _text(domain_transition.get("controller_action"))
                if not envelope_blocks_current_action
                or _domain_transition_has_current_owner_route(domain_transition=domain_transition)
                else None
            )
            or _text(payload.get("runtime_decision"))
        ),
        "next_work_unit": next_work_unit,
        "current_work_unit": canonical_current_work_unit or None,
        "current_executable_owner_action": current_action or None,
        "owner_action_admission": owner_action_admission,
        "owner_handoff_hydration": _owner_handoff_hydration_projection(launch_policy),
        "typed_blocker": typed_blocker or None,
        "current_blockers": current_blockers,
        "stage_artifact_index": _stage_artifact_index_monitoring_projection(payload.get("stage_artifact_index")),
        "progress_delta_classification": progress_delta_classification,
        "paper_progress_delta_counted": bool(progress_state.get("paper_progress_delta_counted")),
        "platform_repair_delta_counted": bool(progress_state.get("platform_repair_delta_counted")),
        "next_forced_delta": _compact_mapping(summary_next_forced_delta, NEXT_FORCED_DELTA_SUMMARY_KEYS),
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
        "dispatch_consumption": gate_clearing_dispatch_consumption or _dispatch_consumption_summary(
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


def _current_work_unit_owner_action_current(
    current_work_unit: Mapping[str, Any],
    *,
    state_kind: str | None,
    current_action: Mapping[str, Any],
    action_supersedes_canonical_typed_blocker: bool = False,
) -> bool:
    if action_supersedes_canonical_typed_blocker:
        return state_kind == "executable_owner_action" and bool(current_action)
    if current_work_unit:
        return _text(current_work_unit.get("status")) == "executable_owner_action"
    return state_kind == "executable_owner_action" and bool(current_action)


def _current_action_supersedes_canonical_typed_blocker(
    *,
    current_action: Mapping[str, Any],
    canonical_current_work_unit: Mapping[str, Any],
    canonical_work_unit_state: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if _text(canonical_current_work_unit.get("status")) not in {"typed_blocker", "blocked_current_work_unit"}:
        return False
    if not (
        _next_forced_delta_owner_action(current_action)
        or _publication_eval_readiness_blocker_repair_action(current_action)
    ):
        return False
    blocker = _mapping(canonical_work_unit_state.get("typed_blocker"))
    if not blocker:
        blocker = {
            "blocker_type": _text(canonical_work_unit_state.get("blocker_type")),
            "blocker_id": _text(canonical_work_unit_state.get("blocker_id")),
            "blocked_reason": _text(canonical_work_unit_state.get("blocked_reason")),
            "work_unit_id": _text(canonical_current_work_unit.get("work_unit_id")),
            "work_unit_fingerprint": _text(canonical_current_work_unit.get("work_unit_fingerprint")),
        }
    return action_supersedes_typed_blocker(
        action=current_action,
        blocker=blocker,
        progress=progress,
    )


def _canonical_current_work_unit_terminal_blocker(current_work_unit: Mapping[str, Any]) -> bool:
    state = _mapping(current_work_unit.get("state"))
    blocker = _mapping(state.get("typed_blocker"))
    values = {
        _text(blocker.get("terminal_closeout_status")),
        _text(blocker.get("terminal_closeout_outcome")),
        _text(blocker.get("progress_delta_classification")),
        _text(state.get("source")),
    }
    return bool(values.intersection({"blocked", "typed_blocker", "blocked_with_domain_typed_blocker"}))


def _terminal_closeout_domain_typed_blocker(
    *,
    latest_terminal_stage_log: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
) -> dict[str, Any]:
    if not latest_terminal_stage_log:
        return {}
    classification = _terminal_progress_delta_classification(paper_stage_log)
    outcome = _text(paper_stage_log.get("outcome"))
    status = _text(latest_terminal_stage_log.get("status"))
    if classification != "typed_blocker" and outcome not in {
        "blocked_with_domain_typed_blocker",
        "typed_blocker",
    }:
        return {}
    next_forced_delta = _mapping(paper_stage_log.get("next_forced_delta"))
    owner_action = _mapping(next_forced_delta.get("owner_action"))
    remaining = _dedupe_text(paper_stage_log.get("remaining_blockers") or [])
    blocker_type = (
        _text(owner_action.get("reason"))
        or _text(next_forced_delta.get("blocker_type"))
        or _text(next_forced_delta.get("blocked_reason"))
        or (remaining[0] if remaining else _text(latest_terminal_stage_log.get("typed_blocker_reason")))
    )
    if blocker_type is None:
        return {}
    owner = (
        _text(owner_action.get("next_owner"))
        or _text(owner_action.get("owner"))
        or _text(latest_terminal_stage_log.get("owner"))
        or "med-autoscience"
    )
    return {
        "blocker_type": blocker_type,
        "blocker_id": blocker_type,
        "blocked_reason": blocker_type,
        "owner": owner,
        "action_type": _text(latest_terminal_stage_log.get("action_type")),
        "work_unit_id": _text(next_forced_delta.get("work_unit_id")) or _text(paper_stage_log.get("stage_name")),
        "source_ref": _text(latest_terminal_stage_log.get("source_path")),
        "acceptance_refs": _source_refs(
            None,
            handoff={},
            latest_terminal_stage_log=latest_terminal_stage_log,
        ),
        "terminal_closeout_status": status,
        "terminal_closeout_outcome": outcome,
        "progress_delta_classification": classification,
    }


def _canonical_typed_blocker_blocks_liveness(
    *,
    current_work_unit: Mapping[str, Any],
    execution: Mapping[str, Any],
    domain_transition: Mapping[str, Any],
    transition_consumed_owner_action: bool,
    transition_consumed_same_work_unit: bool,
    gate_clearing_dispatch_consumption: Mapping[str, Any] | None,
) -> bool:
    if _text(current_work_unit.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return True
    if (
        transition_consumed_owner_action
        and not transition_consumed_same_work_unit
        and gate_clearing_dispatch_consumption is None
    ):
        return False
    if _domain_transition_has_current_owner_route(domain_transition=domain_transition):
        return False
    if _text(execution.get("state_kind")) == "typed_blocker" and _mapping(execution.get("typed_blocker")):
        return True
    return False


def _domain_transition_has_current_owner_route(*, domain_transition: Mapping[str, Any]) -> bool:
    if _mapping(domain_transition.get("typed_blocker")):
        return False
    return (
        _text(domain_transition.get("owner")) is not None
        or _text(domain_transition.get("route_target")) is not None
        or _text(domain_transition.get("controller_action")) is not None
        or _work_unit_projection(domain_transition.get("next_work_unit")) is not None
    )


def _consumed_ai_reviewer_receipt_supersedes_envelope_blocker(
    *,
    domain_transition: Mapping[str, Any],
    raw_typed_blocker: Mapping[str, Any],
) -> bool:
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _text(completion.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    if _text(completion.get("next_action")) != "honor_ai_reviewer_publication_eval_authority":
        return False
    if _text(domain_transition.get("decision_type")) != "route_back_same_line":
        return False
    if _text(domain_transition.get("route_target")) is None:
        return False
    blocker_values = {
        _text(raw_typed_blocker.get("owner")),
        _text(raw_typed_blocker.get("blocker_id")),
        _text(raw_typed_blocker.get("blocker_type")),
        _text(raw_typed_blocker.get("blocked_reason")),
    }
    return any(value is not None and value.startswith("ai_reviewer") for value in blocker_values)


def _next_forced_delta_from_current_work_unit(
    current_work_unit: Mapping[str, Any],
    *,
    fallback: Mapping[str, Any],
) -> dict[str, Any]:
    if _text(current_work_unit.get("status")) != "executable_owner_action":
        return dict(fallback)
    work_unit_id = _text(current_work_unit.get("work_unit_id"))
    action_type = _text(current_work_unit.get("action_type"))
    owner = _text(current_work_unit.get("owner"))
    if work_unit_id is None and action_type is None and owner is None:
        return dict(fallback)
    contract = _mapping(current_work_unit.get("required_output_contract"))
    target_surface = _mapping(contract.get("target_surface"))
    required_output_surface = _text(contract.get("required_output_surface"))
    if not target_surface and required_output_surface is not None:
        target_surface = {
            "ref_kind": "route_obligation",
            "route_target": owner,
            "surface_ref": required_output_surface,
        }
    payload = dict(fallback)
    payload.update(
        {
            "required_delta_kind": _text(contract.get("required_delta_kind"))
            or _text(fallback.get("required_delta_kind"))
            or "current_work_unit_owner_action",
            "work_unit_id": work_unit_id or _text(fallback.get("work_unit_id")),
            "next_owner": owner or _text(fallback.get("next_owner")),
            "allowed_outcomes": contract.get("accepted_terminal_results")
            or fallback.get("allowed_outcomes"),
            "target_surface": target_surface or _mapping(fallback.get("target_surface")) or None,
            "target_surface_specificity": (
                "explicit_owner_route_target"
                if target_surface
                else _text(fallback.get("target_surface_specificity"))
            ),
            "acceptance_refs": current_work_unit.get("acceptance_refs") or fallback.get("acceptance_refs"),
            "owner_action": {
                key: value
                for key, value in {
                    "next_owner": owner,
                    "work_unit_id": work_unit_id,
                    "allowed_actions": [action_type] if action_type is not None else None,
                    "owner_receipt_required": contract.get("owner_receipt_required"),
                }.items()
                if value not in (None, "", [], {})
            },
        }
    )
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


def _strict_running_provider_liveness(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if _text(handoff.get("active_run_id")) is None:
        return False
    if _handoff_has_matching_terminal_closeout(handoff):
        return False
    runtime_health = _mapping(handoff.get("runtime_health"))
    runtime_liveness_status = _text(runtime_health.get("runtime_liveness_status"))
    health_status = _text(runtime_health.get("health_status"))
    return runtime_liveness_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } or health_status in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _mapping(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _text(terminal.get("status"))
    if status in {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }:
        return True
    return _text(terminal.get("source_path")) is not None and _text(terminal.get("record_path")) is not None


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _text(handoff.get("active_stage_attempt_id")):
        return text
    active_run_id = _text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


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
        identity = canonical_work_unit_identity_from_completion(completion_receipt or execution_receipt)
        return {
            "consumption_status": status,
            "receipt_ref": _text(completion_receipt.get("receipt_ref")) or _text(execution_receipt.get("receipt_ref")),
            "receipt_kind": _text(completion_receipt.get("receipt_kind")) or _text(execution_receipt.get("receipt_kind")),
            "execution_status": _text(execution_receipt.get("execution_status")),
            "action_fingerprint": _text(completion_receipt.get("action_fingerprint"))
            or _text(execution_receipt.get("action_fingerprint")),
            "work_unit_id": _text(identity.get("work_unit_id")),
            "work_unit_fingerprint": _text(identity.get("work_unit_fingerprint")),
            "canonical_work_unit_identity": identity or None,
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


def _gate_clearing_batch_dispatch_consumption(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    domain_transition = _mapping(payload.get("domain_transition"))
    followthrough = _mapping(payload.get("gate_clearing_batch_followthrough"))
    if followthrough:
        record = {
            "status": _text(followthrough.get("status")),
            "source_eval_id": _text(followthrough.get("source_eval_id")),
            "work_unit_id": _text(followthrough.get("work_unit_id")),
            "work_unit_fingerprint": _text(followthrough.get("work_unit_fingerprint")),
            "owner_route_currentness_basis": _mapping(followthrough.get("owner_route_currentness_basis")),
            "work_unit_currentness": _mapping(followthrough.get("work_unit_currentness")),
            "explicit_publication_work_unit": _mapping(followthrough.get("explicit_publication_work_unit")),
        }
        if record.get("source_eval_id") is None:
            record["source_eval_id"] = _text(
                _mapping(_mapping(domain_transition.get("source_refs")).get("owner_route_currentness_basis")).get(
                    "source_eval_id"
                )
            )
        receipt = gate_clearing_batch_receipt_consumption_for_transition(
            transition=domain_transition,
            record=record,
            receipt_ref=_text(followthrough.get("latest_record_path"))
            or "artifacts/controller/gate_clearing_batch/latest.json",
        )
        if receipt is not None:
            return receipt
    return None


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


def _transition_consumed_same_ai_reviewer_work_unit(domain_transition: Mapping[str, Any]) -> bool:
    completion = _mapping(domain_transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    return _consumed_receipt_matches_transition_work_unit(
        domain_transition=domain_transition,
        completion=completion,
    )


def _consumed_receipt_matches_transition_work_unit(
    *,
    domain_transition: Mapping[str, Any],
    completion: Mapping[str, Any],
) -> bool:
    return consumed_ai_reviewer_receipt_matches_transition_work_unit(
        transition=domain_transition,
        completion=completion,
    )


def _first_action_queue_item(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if isinstance(item, Mapping):
            return dict(item)
    return None


def _first_current_action_queue_item(value: object) -> dict[str, Any] | None:
    if not isinstance(value, list):
        return None
    for item in value:
        if not isinstance(item, Mapping):
            continue
        payload = dict(item)
        consumption = _mapping(payload.get("consumption"))
        status = _text(payload.get("consumption_status")) or _text(consumption.get("status"))
        if status in {"consumed", "receipt_consumed", "completed"}:
            continue
        return payload
    return None






























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


def _stage_kernel_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "stage_kernel_projection.current_owner_delta"
        and bool(_sequence(action.get("allowed_actions")))
    )


def _stage_native_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "stage_native_workspace_next_action"
        and bool(_sequence(action.get("allowed_actions")))
    )


def _repair_progress_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "repair_progress_projection.mas_owner_repair_execution_evidence"
        and bool(_sequence(action.get("allowed_actions")))
    )


def _gate_followthrough_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "gate_clearing_batch_followthrough.actionable_current_work_unit"
        and bool(_sequence(action.get("allowed_actions")))
    )


def _publication_eval_readiness_blocker_repair_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "publication_eval.recommended_actions.readiness_blocker_repair"
        and bool(_sequence(action.get("allowed_actions")))
    )


def _next_forced_delta_owner_action(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source")) == "study_progress.next_forced_delta.owner_action"
        and bool(_sequence(action.get("allowed_actions")))
    )


def _envelope_typed_blocker_blocks_current_action(
    *,
    execution: Mapping[str, Any],
    raw_typed_blocker: Mapping[str, Any],
    artifact_first_supersedes_blocker: bool,
    current_action: Mapping[str, Any],
) -> bool:
    if artifact_first_supersedes_blocker:
        return False
    if _stage_native_owner_action(current_action):
        return False
    if _repair_progress_owner_action(current_action):
        return False
    if _gate_followthrough_owner_action(current_action):
        return False
    if _publication_eval_readiness_blocker_repair_action(current_action):
        return False
    if _next_forced_delta_owner_action(current_action):
        return _text(execution.get("state_kind")) == "typed_blocker" and bool(raw_typed_blocker)
    if _text(execution.get("state_kind")) != "typed_blocker":
        return False
    return bool(raw_typed_blocker)


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


def _canonical_typed_blocker_current_blockers(typed_blocker: Mapping[str, Any]) -> list[str]:
    return _dedupe_text(
        [
            typed_blocker.get("blocker_type"),
            typed_blocker.get("blocked_reason"),
            typed_blocker.get("reason"),
            typed_blocker.get("blocker_kind"),
            typed_blocker.get("summary"),
        ]
    )[:12]


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


def _work_unit_from_action(action: Mapping[str, Any] | None) -> dict[str, Any] | str | None:
    if action is None:
        return None
    unit = _work_unit_projection(action.get("next_work_unit"))
    if unit is not None:
        return unit
    for key in ("controller_work_unit_id", "work_unit_id", "action_type"):
        text = _text(action.get(key))
        if text is not None:
            return text
    return None


def _work_unit_from_current_action(action: Mapping[str, Any]) -> dict[str, Any] | str | None:
    work_unit_id = _text(action.get("work_unit_id"))
    if work_unit_id is None:
        return None
    if _artifact_first_owner_action(action):
        return {"unit_id": work_unit_id}
    return work_unit_id


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


def _work_unit_id(value: object) -> str | None:
    if isinstance(value, Mapping):
        return _text(value.get("unit_id"))
    return _text(value)


def _owner_from_action(action: Mapping[str, Any] | None) -> str | None:
    if action is None:
        return None
    return (
        _text(action.get("owner"))
        or _text(action.get("request_owner"))
        or _text(action.get("recommended_owner"))
    )


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


def _running_provider_attempt_ref(
    *,
    running_provider_attempt: bool | None,
    handoff: Mapping[str, Any],
    key: str,
) -> str | None:
    if key == "active_run_id":
        return _text(handoff.get(key))
    if running_provider_attempt is not True:
        return None
    return _text(handoff.get(key))


def _stale_active_run_id(
    *,
    running_provider_attempt: bool | None,
    payload: Mapping[str, Any],
    supervision: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> str | None:
    if running_provider_attempt is True:
        return None
    return (
        _text(supervision.get("active_run_id"))
        or _text(payload.get("active_run_id"))
        or _text(handoff.get("active_run_id"))
    )




















__all__ = ["build_progress_first_monitoring_summary"]
