from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)

from .current_executable_owner_action_parts.action_types import (
    AI_REVIEWER_ACTION,
    AI_REVIEWER_OWNER,
    AI_REVIEWER_WORK_UNIT,
    GATE_CLEARING_ACTION,
    GATE_CLEARING_OWNER,
    GATE_CLEARING_WORK_UNIT,
    QUALITY_REPAIR_ACTION,
    REPAIR_PROGRESS_SOURCE,
    TERMINAL_NEXT_FORCED_DELTA_ACTIONS,
)
from .current_executable_owner_action_parts.gate_followthrough import (
    owner_action_from_gate_followthrough_current_work_unit,
)
from .current_executable_owner_action_parts.publication_repair import (
    owner_action_from_publication_eval_readiness_blocker_repair,
)
from .current_executable_owner_action_parts.repair_progress import (
    owner_action_from_repair_progress_projection,
    repair_progress_consumes_publication_repair,
)
from .current_executable_owner_action_parts.stage_artifact_index import (
    owner_action_from_stage_artifact_index,
)
from .current_executable_owner_action_parts.stage_kernel_readiness import (
    READINESS_ACTION,
    current_owner_delta as _current_owner_delta,
    owner_action_from_stage_kernel_readiness_followup,
    stage_kernel_owner_answer_recorded_without_next_action as _stage_kernel_owner_answer_recorded_without_next_action,
    stage_kernel_readiness_answer_without_followup as _stage_kernel_readiness_answer_without_followup,
    stage_kernel_readiness_stable_typed_blocker_answer as _stage_kernel_readiness_stable_typed_blocker_answer,
)
from .current_executable_owner_action_parts.terminal_next_forced_delta import (
    owner_action_from_terminal_next_forced_delta,
)
from .current_action_identity import action_matches_canonical_executable_work_unit
from .shared import _mapping_copy, _non_empty_text

SURFACE_KIND = "current_executable_owner_action"


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    if _canonical_current_work_unit_has_terminal_stop_loss(payload):
        return None
    domain_transition_action = _from_domain_transition(payload)
    publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
    repair_progress_action = _from_repair_progress_projection(payload)
    repair_progress_consumes_publication_repair = _repair_progress_consumes_publication_repair(
        repair_progress_action=repair_progress_action,
        publication_repair_action=publication_repair_action,
        payload=payload,
    )
    if (
        repair_progress_consumes_publication_repair
        and repair_progress_action is not None
        and not _action_consumed_by_dispatch_receipt(
            action=repair_progress_action,
            payload=payload,
        )
    ):
        return repair_progress_action
    if (
        not repair_progress_consumes_publication_repair
        and action_matches_canonical_executable_work_unit(
            action=publication_repair_action,
            current_work_unit=_mapping_copy(payload.get("current_work_unit")),
        )
    ):
        return publication_repair_action
    if repair_progress_action is not None:
        if not _action_consumed_by_dispatch_receipt(action=repair_progress_action, payload=payload):
            return repair_progress_action
        if (
            publication_repair_action is not None
            and _consumed_ai_reviewer_followup_allows_publication_repair(payload)
        ):
            return publication_repair_action
        gate_followthrough_action = _from_gate_followthrough_current_work_unit(payload)
        next_forced_delta_action = _from_current_next_forced_delta(payload)
        if _next_forced_delta_supersedes_gate_followthrough(
            next_forced_delta_action=next_forced_delta_action,
            gate_followthrough_action=gate_followthrough_action,
        ):
            return next_forced_delta_action
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
            if _next_forced_delta_is_terminal_routeback_action(next_forced_delta_action):
                return next_forced_delta_action
            if (
                publication_repair_action is not None
                and (
                    not repair_progress_consumes_publication_repair
                    or _consumed_ai_reviewer_followup_allows_publication_repair(payload)
                )
            ):
                return publication_repair_action
            if next_forced_delta_action is not None:
                return next_forced_delta_action
    gate_followthrough_action = _from_gate_followthrough_current_work_unit(payload)
    next_forced_delta_action = _from_current_next_forced_delta(payload)
    stage_native_action = _from_stage_native_current_owner_action(payload)
    if _next_forced_delta_supersedes_gate_followthrough(
        next_forced_delta_action=next_forced_delta_action,
        gate_followthrough_action=gate_followthrough_action,
    ):
        return next_forced_delta_action
    if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
        publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
        if publication_repair_action is not None:
            return publication_repair_action
    if _stage_kernel_owner_answer_recorded_without_next_action(payload):
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        return stage_native_action or domain_transition_action
    if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        next_forced_delta_action = _from_current_next_forced_delta(payload)
        if _next_forced_delta_supersedes_stale_readiness_blocker(next_forced_delta_action):
            return next_forced_delta_action
        if _next_forced_delta_is_terminal_routeback_action(next_forced_delta_action):
            return next_forced_delta_action
        publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
        if publication_repair_action is not None:
            return publication_repair_action
        return (
            stage_native_action
            or domain_transition_action
            or _from_stage_kernel_readiness_followup(payload)
        )
    readiness_followup = _from_stage_kernel_readiness_followup(payload)
    if readiness_followup is not None:
        return readiness_followup
    if _stage_kernel_readiness_answer_without_followup(payload):
        return stage_native_action or domain_transition_action
    artifact_action = _from_stage_artifact_index(payload)
    if artifact_action is not None and domain_transition_action is None:
        return artifact_action
    if gate_followthrough_action is not None:
        return gate_followthrough_action
    return next_forced_delta_action or domain_transition_action


def _canonical_current_work_unit_has_terminal_stop_loss(payload: Mapping[str, Any]) -> bool:
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    closeout_like = {
        "typed_blocker": typed_blocker,
        "blocked_reason": _non_empty_text(state.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocked_reason"))
        or _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocker_kind"))
        or _non_empty_text(typed_blocker.get("reason")),
        "typed_blocker_reason": _non_empty_text(typed_blocker.get("blocker_type"))
        or _non_empty_text(typed_blocker.get("blocker_kind"))
        or _non_empty_text(typed_blocker.get("reason")),
        "stage_closeout_status": _non_empty_text(typed_blocker.get("terminal_closeout_status")),
        "stage_closeout_outcome": _non_empty_text(typed_blocker.get("terminal_closeout_outcome")),
    }
    return is_anti_loop_stop_loss_closeout(closeout_like)


def _from_current_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    terminal_action = owner_action_from_terminal_next_forced_delta(
        payload,
        surface_kind=SURFACE_KIND,
    )
    if terminal_action is not None:
        return terminal_action
    return _from_next_forced_delta(payload)


def _consumed_ai_reviewer_followup_routes_to_write_repair(payload: Mapping[str, Any]) -> bool:
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    if _terminal_stage_semantically_consumes_ai_reviewer_followup(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
    ):
        return True
    return _record_only_ai_reviewer_closeout_routes_to_write_repair(
        terminal=terminal,
        next_forced_delta=next_forced_delta,
    )


def _consumed_ai_reviewer_followup_allows_publication_repair(payload: Mapping[str, Any]) -> bool:
    return _consumed_ai_reviewer_followup_routes_to_write_repair(
        payload
    ) or _record_only_ai_reviewer_closeout_routes_to_publication_repair(payload)


def _record_only_ai_reviewer_closeout_routes_to_publication_repair(payload: Mapping[str, Any]) -> bool:
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status not in {
        "closed_with_domain_owner_refs",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "record_only_archive_materialized",
    } and outcome not in {"closed_with_domain_owner_refs"}:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    next_owner = (
        _non_empty_text(next_forced_delta.get("owner"))
        or _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
    )
    next_action_type = _non_empty_text(owner_action.get("action_type")) or _non_empty_text(
        next_forced_delta.get("action_type")
    )
    if next_owner != "mas_controller":
        return False
    if next_action_type != "consume_record_only_ai_reviewer_closeout_or_route_next_owner":
        return False
    if _non_empty_text(next_forced_delta.get("required_delta_kind")) != (
        "mas_owner_route_reconcile_or_typed_blocker_consumption"
    ):
        return False
    reviewer_record_ref = _non_empty_text(next_forced_delta.get("reviewer_record_ref"))
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    return (reviewer_record_ref is not None and "publication_eval" in reviewer_record_ref) or (
        source_eval_id is not None and "publication-eval" in source_eval_id
    )


def _from_gate_followthrough_current_work_unit(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_gate_followthrough_current_work_unit(
        payload,
        surface_kind=SURFACE_KIND,
    )


def _from_stage_kernel_readiness_followup(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_stage_kernel_readiness_followup(payload, surface_kind=SURFACE_KIND)


def _from_repair_progress_projection(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_repair_progress_projection(payload, surface_kind=SURFACE_KIND)


def _repair_progress_consumes_publication_repair(
    *,
    repair_progress_action: Mapping[str, Any] | None,
    publication_repair_action: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> bool:
    return repair_progress_consumes_publication_repair(
        repair_progress_action=repair_progress_action,
        publication_repair_action=publication_repair_action,
        payload=payload,
    )


def _from_publication_eval_readiness_blocker_repair(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_publication_eval_readiness_blocker_repair(
        payload,
        surface_kind=SURFACE_KIND,
    )


def _from_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    next_forced_delta = _mapping_copy(payload.get("next_forced_delta"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    study_id = _non_empty_text(payload.get("study_id"))
    owner = _non_empty_text(owner_action.get("next_owner")) or _non_empty_text(
        next_forced_delta.get("next_owner")
    )
    work_unit_id = _non_empty_text(owner_action.get("work_unit_id")) or _non_empty_text(
        next_forced_delta.get("work_unit_id")
    )
    allowed_actions = _text_items(owner_action.get("allowed_actions")) or _text_items(
        next_forced_delta.get("allowed_actions")
    )
    action_type = (
        _non_empty_text(owner_action.get("action_type"))
        or _non_empty_text(next_forced_delta.get("action_type"))
        or (allowed_actions[0] if len(allowed_actions) == 1 else None)
    )
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    source_eval_id = _next_forced_delta_source_eval_id(
        next_forced_delta=next_forced_delta,
        owner_action=owner_action,
        payload=payload,
    )
    eval_bound_fingerprint = current_ai_reviewer_gate_replay_fingerprint(
        study_id=study_id,
        action_type=action_type,
        work_unit_id=work_unit_id,
        source_eval_id=source_eval_id,
    )
    if (
        action_type == GATE_CLEARING_ACTION
        and eval_bound_fingerprint is None
        and not _consumed_repair_followup_allows_unbound_gate_replay(payload)
    ):
        return None
    owner_route_currentness_basis = (
        _compact(
            {
                "source_eval_id": source_eval_id,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": eval_bound_fingerprint,
                "source": "study_progress.next_forced_delta.owner_action",
            }
        )
        if eval_bound_fingerprint is not None
        else {}
    )
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "study_progress.next_forced_delta.owner_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": eval_bound_fingerprint,
            "action_fingerprint": eval_bound_fingerprint,
            "source_eval_id": source_eval_id,
            "owner_route_currentness_basis": owner_route_currentness_basis or None,
            "action_type": action_type,
            "allowed_actions": allowed_actions,
            "owner_receipt_required": owner_action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(next_forced_delta.get("required_delta_kind")),
            "target_surface": _mapping_copy(next_forced_delta.get("target_surface")) or None,
            "target_surface_specificity": _non_empty_text(
                next_forced_delta.get("target_surface_specificity")
            ),
            "acceptance_refs": _text_items(next_forced_delta.get("acceptance_refs")),
            "authority_boundary": _authority_boundary(),
        }
    )


def _next_forced_delta_source_eval_id(
    *,
    next_forced_delta: Mapping[str, Any],
    owner_action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> str | None:
    publication_eval = _mapping_copy(payload.get("publication_eval"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    dispatch_consumption = _mapping_copy(progress_first.get("dispatch_consumption"))
    canonical_identity = _mapping_copy(dispatch_consumption.get("canonical_work_unit_identity"))
    owner_route_basis = _mapping_copy(dispatch_consumption.get("owner_route_currentness_basis"))
    canonical_owner_route_basis = _mapping_copy(canonical_identity.get("owner_route_currentness_basis"))
    return (
        _non_empty_text(owner_action.get("source_eval_id"))
        or _non_empty_text(owner_action.get("eval_id"))
        or _non_empty_text(next_forced_delta.get("source_eval_id"))
        or _non_empty_text(next_forced_delta.get("eval_id"))
        or _non_empty_text(publication_eval.get("eval_id"))
        or _non_empty_text(dispatch_consumption.get("source_eval_id"))
        or _non_empty_text(canonical_identity.get("source_eval_id"))
        or _non_empty_text(owner_route_basis.get("source_eval_id"))
        or _non_empty_text(canonical_owner_route_basis.get("source_eval_id"))
    )


def _consumed_repair_followup_allows_unbound_gate_replay(payload: Mapping[str, Any]) -> bool:
    repair_progress_action = _from_repair_progress_projection(payload)
    return repair_progress_action is not None and _action_consumed_by_dispatch_receipt(
        action=repair_progress_action,
        payload=payload,
    )


def _next_forced_delta_supersedes_stale_readiness_blocker(
    action: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping_copy(action)
    if _non_empty_text(payload.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    if _non_empty_text(payload.get("required_delta_kind")) != "review_current_paper_delta":
        return False
    values = {
        _non_empty_text(payload.get("action_type")),
        _non_empty_text(payload.get("work_unit_id")),
        *_text_items(payload.get("allowed_actions")),
    }
    if READINESS_ACTION in values:
        return False
    return bool(
        values.intersection(
            {
                "return_to_ai_reviewer_workflow",
                "run_gate_clearing_batch",
                "run_quality_repair_batch",
            }
        )
    )


def _next_forced_delta_is_terminal_routeback_action(
    action: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping_copy(action)
    if _non_empty_text(payload.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    if payload.get("terminal_stage_next_forced_delta") is not True:
        return False
    if _non_empty_text(payload.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    if _non_empty_text(payload.get("next_owner")) != "write":
        return False
    return _non_empty_text(payload.get("work_unit_id")) is not None


def _next_forced_delta_supersedes_gate_followthrough(
    *,
    next_forced_delta_action: Mapping[str, Any] | None,
    gate_followthrough_action: Mapping[str, Any] | None,
) -> bool:
    next_action = _mapping_copy(next_forced_delta_action)
    gate_action = _mapping_copy(gate_followthrough_action)
    if not next_action or not gate_action:
        return False
    if _non_empty_text(gate_action.get("source")) != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    if _non_empty_text(next_action.get("source")) != "study_progress.next_forced_delta.owner_action":
        return False
    next_action_type = _non_empty_text(next_action.get("action_type"))
    if next_action_type not in TERMINAL_NEXT_FORCED_DELTA_ACTIONS:
        return False
    if _non_empty_text(gate_action.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    next_source_eval_id = _non_empty_text(next_action.get("source_eval_id"))
    gate_source_eval_id = _non_empty_text(gate_action.get("source_eval_id"))
    if next_action.get("terminal_stage_next_forced_delta") is True:
        return _terminal_stage_next_delta_supersedes_gate_followthrough(
            next_action=next_action,
            gate_action=gate_action,
        )
    if next_action_type != GATE_CLEARING_ACTION:
        return False
    if next_source_eval_id is None or gate_source_eval_id is None:
        return False
    if next_source_eval_id == gate_source_eval_id:
        return False
    if _non_empty_text(next_action.get("work_unit_id")) == _non_empty_text(gate_action.get("work_unit_id")):
        return False
    return True


def _terminal_stage_next_delta_supersedes_gate_followthrough(
    *,
    next_action: Mapping[str, Any],
    gate_action: Mapping[str, Any],
) -> bool:
    next_work_unit = _non_empty_text(next_action.get("work_unit_id"))
    if next_work_unit is None:
        return False
    if next_work_unit == _non_empty_text(gate_action.get("work_unit_id")):
        return False
    if _non_empty_text(next_action.get("action_type")) == QUALITY_REPAIR_ACTION:
        return True
    return False


def _action_consumed_by_dispatch_receipt(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _terminal_stage_closeout_consumes_repair_followup(action=action, payload=payload):
        return True
    if _terminal_gate_closeout_consumes_repair_followup(action=action, payload=payload):
        return True
    consumption = _mapping_copy(_mapping_copy(payload.get("progress_first_monitoring_summary")).get("dispatch_consumption"))
    if not consumption:
        consumption = _mapping_copy(_mapping_copy(payload.get("domain_transition")).get("completion_receipt_consumption"))
    if not consumption:
        consumption = _mapping_copy(
            _mapping_copy(payload.get("domain_transition")).get("default_executor_execution_receipt_consumption")
        )
    consumption_status = _non_empty_text(consumption.get("consumption_status")) or _non_empty_text(
        consumption.get("status")
    )
    if consumption_status != "consumed":
        return False
    action_work_unit = _non_empty_text(action.get("work_unit_id"))
    consumed_work_unit = _non_empty_text(consumption.get("work_unit_id"))
    if action_work_unit is None or consumed_work_unit != action_work_unit:
        return False
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(action.get("fingerprint"))
    )
    consumed_fingerprint = (
        _non_empty_text(consumption.get("work_unit_fingerprint"))
        or _non_empty_text(consumption.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(consumption.get("canonical_work_unit_identity")).get("work_unit_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == consumed_fingerprint:
        return True
    return _ai_reviewer_eval_receipt_consumes_repair_followup(
        action=action,
        consumption=consumption,
    )


def _terminal_gate_closeout_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    action_work_unit = _non_empty_text(action.get("work_unit_id"))
    if action_work_unit != GATE_CLEARING_WORK_UNIT:
        return False
    terminal = _latest_gate_replay_terminal_stage(payload)
    if not terminal:
        return False
    if _non_empty_text(terminal.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    if _non_empty_text(terminal.get("status")) not in {
        "blocked",
        "closed",
        "completed",
        "executed",
        "typed_blocked",
    }:
        return False
    terminal_work_unit = _non_empty_text(terminal.get("work_unit_id"))
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    terminal_work_unit = terminal_work_unit or _non_empty_text(next_forced_delta.get("work_unit_id"))
    if terminal_work_unit != action_work_unit:
        return False
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("source_fingerprint"))
    )
    terminal_fingerprint = (
        _non_empty_text(terminal.get("work_unit_fingerprint"))
        or _non_empty_text(terminal.get("action_fingerprint"))
        or _non_empty_text(paper_stage_log.get("work_unit_fingerprint"))
        or _non_empty_text(paper_stage_log.get("action_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == terminal_fingerprint:
        return True
    if _ref_sets_intersect(
        _repair_followup_gate_action_refs(action),
        _terminal_gate_closeout_refs(terminal, paper_stage_log=paper_stage_log),
    ):
        return True
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "typed_blocker":
        return False
    if _non_empty_text(current_work_unit.get("work_unit_id")) != action_work_unit:
        return False
    current_fingerprint = (
        _non_empty_text(current_work_unit.get("work_unit_fingerprint"))
        or _non_empty_text(current_work_unit.get("action_fingerprint"))
    )
    if action_fingerprint is not None and action_fingerprint == current_fingerprint:
        return True
    state = _mapping_copy(current_work_unit.get("state"))
    typed_blocker = _mapping_copy(state.get("typed_blocker")) or _mapping_copy(
        current_work_unit.get("typed_blocker")
    )
    blocker_fingerprint = (
        _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
        or _non_empty_text(typed_blocker.get("action_fingerprint"))
    )
    return action_fingerprint is not None and action_fingerprint == blocker_fingerprint


def _repair_followup_gate_action_refs(action: Mapping[str, Any]) -> set[str]:
    target_surface = _mapping_copy(action.get("target_surface"))
    return _ref_set(
        [
            action.get("source_ref"),
            target_surface.get("request_ref"),
            target_surface.get("surface_ref"),
            *list(action.get("acceptance_refs") or []),
        ]
    )


def _terminal_gate_closeout_refs(
    terminal: Mapping[str, Any],
    *,
    paper_stage_log: Mapping[str, Any],
) -> set[str]:
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    target_surface = _mapping_copy(next_forced_delta.get("target_surface"))
    return _ref_set(
        [
            terminal.get("source_path"),
            terminal.get("source_ref"),
            terminal.get("record_path"),
            terminal.get("closeout_ref"),
            target_surface.get("request_ref"),
            target_surface.get("surface_ref"),
            *list(terminal.get("closeout_refs") or []),
            *list(terminal.get("evidence_refs") or []),
            *list(paper_stage_log.get("closeout_refs") or []),
            *list(paper_stage_log.get("evidence_refs") or []),
        ]
    )


def _ref_set(values: list[object]) -> set[str]:
    refs: set[str] = set()
    for value in values:
        text = _non_empty_text(value)
        if text is None:
            continue
        refs.add(text)
        if text.startswith("/"):
            refs.add(text.lstrip("/"))
        for marker in ("/studies/", "/runtime/quests/"):
            if marker in text:
                refs.add(f"{marker[1:]}{text.split(marker, 1)[1]}")
        if "/artifacts/" in text:
            refs.add(f"artifacts/{text.split('/artifacts/', 1)[1]}")
    return refs


def _ref_sets_intersect(left: set[str], right: set[str]) -> bool:
    return bool(left and right and left.intersection(right))


def _terminal_stage_closeout_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    terminal = _latest_ai_reviewer_terminal_stage(payload)
    if _non_empty_text(terminal.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status not in {
        "closed_with_domain_owner_refs",
        "completed_with_domain_owner_record_only_archive",
        "completed_with_record_only_artifact_delta",
        "executed",
        "executed_record_only",
        "executed_record_only_archive_materialized",
        "executed_with_owner_receipt",
        "record_only_archive_materialized",
    } and outcome not in {"owner_receipt", "closed_with_domain_owner_refs"}:
        return False
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    next_forced_delta = _mapping_copy(terminal.get("next_forced_delta")) or _mapping_copy(
        paper_stage_log.get("next_forced_delta")
    )
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    next_owner = (
        _non_empty_text(next_forced_delta.get("owner"))
        or _non_empty_text(owner_action.get("next_owner"))
        or _non_empty_text(owner_action.get("owner"))
    )
    next_action_type = _non_empty_text(owner_action.get("action_type")) or _non_empty_text(
        next_forced_delta.get("action_type")
    )
    if _terminal_stage_semantically_consumes_ai_reviewer_followup(
        terminal=terminal,
        paper_stage_log=paper_stage_log,
        next_forced_delta=next_forced_delta,
    ):
        return next_action_type in TERMINAL_NEXT_FORCED_DELTA_ACTIONS or next_action_type in {
            "return_to_write",
        }
    if next_owner != "mas_controller":
        return False
    if next_action_type not in {
        "consume_record_only_ai_reviewer_closeout_or_route_next_owner",
        "return_to_write",
    }:
        return False
    action_stage_attempt = _stage_attempt_id_from_refs(action.get("acceptance_refs"))
    terminal_stage_attempt = _non_empty_text(terminal.get("stage_attempt_id")) or _stage_attempt_id_from_refs(
        [terminal.get("source_path")]
    )
    if action_stage_attempt is not None and terminal_stage_attempt is not None:
        return action_stage_attempt == terminal_stage_attempt
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    if terminal_stage_attempt is not None and source_eval_id is not None:
        return terminal_stage_attempt in source_eval_id
    action_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("source_fingerprint"))
    )
    terminal_refs = [terminal.get("source_path"), *_text_items(terminal.get("closeout_refs"))]
    return action_fingerprint is not None and any(
        action_fingerprint in ref for ref in terminal_refs if isinstance(ref, str)
    )


def _terminal_stage_semantically_consumes_ai_reviewer_followup(
    *,
    terminal: Mapping[str, Any],
    paper_stage_log: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> bool:
    required_delta_kind = _non_empty_text(next_forced_delta.get("required_delta_kind"))
    if required_delta_kind not in {
        "same_line_write_repair_or_gate_replay_route",
        "same_line_write_repair_or_typed_blocker_consumption",
    }:
        return False
    next_work_unit = _non_empty_text(next_forced_delta.get("work_unit_id"))
    owner_action = _mapping_copy(next_forced_delta.get("owner_action"))
    if _non_empty_text(owner_action.get("work_unit_id")) not in {next_work_unit, None}:
        return False
    if next_work_unit in {None, AI_REVIEWER_WORK_UNIT}:
        return False
    progress_delta_classification = (
        _non_empty_text(paper_stage_log.get("progress_delta_classification"))
        or _non_empty_text(terminal.get("progress_delta_classification"))
    )
    if progress_delta_classification not in {"deliverable_progress", "paper_progress", "mixed"}:
        return False
    refs = _dedupe_text(
        [
            terminal.get("source_path"),
            *list(terminal.get("closeout_refs") or []),
            *list(terminal.get("changed_paper_surfaces") or []),
            *list(paper_stage_log.get("changed_paper_surfaces") or []),
            _mapping_copy(next_forced_delta.get("target_surface")).get("surface_ref"),
            _mapping_copy(next_forced_delta.get("target_surface")).get("publication_eval_latest_ref"),
        ]
    )
    return any("publication_eval/ai_reviewer_responses" in ref for ref in refs)


def _record_only_ai_reviewer_closeout_routes_to_write_repair(
    *,
    terminal: Mapping[str, Any],
    next_forced_delta: Mapping[str, Any],
) -> bool:
    status = _non_empty_text(terminal.get("status"))
    outcome = _non_empty_text(terminal.get("outcome"))
    if status != "closed_with_domain_owner_refs" and outcome != "closed_with_domain_owner_refs":
        return False
    if _non_empty_text(next_forced_delta.get("required_delta_kind")) != "mas_owner_route_reconcile_or_typed_blocker_consumption":
        return False
    next_owner = _non_empty_text(next_forced_delta.get("owner"))
    if next_owner != "mas_controller":
        return False
    if _non_empty_text(next_forced_delta.get("action_type")) != "consume_record_only_ai_reviewer_closeout_or_route_next_owner":
        return False
    terminal_stage_attempt = _non_empty_text(terminal.get("stage_attempt_id")) or _stage_attempt_id_from_refs(
        [terminal.get("source_path")]
    )
    source_eval_id = _non_empty_text(next_forced_delta.get("source_eval_id"))
    if terminal_stage_attempt is None or source_eval_id is None or terminal_stage_attempt not in source_eval_id:
        return False
    if "ai-reviewer-record" in source_eval_id:
        return True
    reviewer_record_ref = _non_empty_text(next_forced_delta.get("reviewer_record_ref"))
    return reviewer_record_ref is not None and "publication_eval/ai_reviewer_responses" in reviewer_record_ref


def _latest_ai_reviewer_terminal_stage(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if _non_empty_text(terminal.get("action_type")) == AI_REVIEWER_ACTION:
            return terminal
    return {}


def _latest_gate_replay_terminal_stage(payload: Mapping[str, Any]) -> dict[str, Any]:
    handoff = _mapping_copy(payload.get("opl_current_control_state_handoff"))
    progress_first = _mapping_copy(payload.get("progress_first_monitoring_summary"))
    for value in (
        progress_first.get("latest_terminal_stage"),
        progress_first.get("latest_terminal_stage_log"),
        handoff.get("latest_terminal_stage_log"),
        payload.get("latest_terminal_stage"),
        payload.get("latest_terminal_stage_log"),
    ):
        terminal = _mapping_copy(value)
        if _non_empty_text(terminal.get("action_type")) == GATE_CLEARING_ACTION:
            return terminal
    return {}


def _stage_attempt_id_from_refs(value: object) -> str | None:
    for ref in _text_items(value):
        for part in ref.replace("#", "/").replace(".", "/").split("/"):
            if part.startswith("sat_"):
                return part
    return None


def _ai_reviewer_eval_receipt_consumes_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != AI_REVIEWER_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    if _non_empty_text(consumption.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    receipt_ref = _non_empty_text(consumption.get("receipt_ref"))
    if receipt_ref is None or "publication_eval" not in receipt_ref:
        return False
    if _non_empty_text(consumption.get("work_unit_id")) != AI_REVIEWER_WORK_UNIT:
        return False
    return _ai_reviewer_eval_receipt_binds_repair_followup(
        action=action,
        consumption=consumption,
    )


def _ai_reviewer_eval_receipt_binds_repair_followup(
    *,
    action: Mapping[str, Any],
    consumption: Mapping[str, Any],
) -> bool:
    repair_precedence = _mapping_copy(action.get("repair_progress_precedence"))
    target_surface = _mapping_copy(action.get("target_surface"))
    expected_source_fingerprint = (
        _non_empty_text(action.get("work_unit_fingerprint"))
        or _non_empty_text(action.get("action_fingerprint"))
        or _non_empty_text(repair_precedence.get("source_fingerprint"))
    )
    binding_mappings = _ai_reviewer_consumption_binding_mappings(consumption)
    if expected_source_fingerprint is not None:
        explicit_fingerprints = {
            text
            for mapping in binding_mappings
            for key in (
                "repair_source_fingerprint",
                "repair_progress_source_fingerprint",
                "repair_execution_source_fingerprint",
            )
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_source_fingerprint in explicit_fingerprints:
            return True
    expected_refs = set(
        _dedupe_text(
            [
                action.get("source_ref"),
                target_surface.get("request_ref"),
                target_surface.get("gate_replay_request_ref"),
                *list(action.get("acceptance_refs") or []),
            ]
        )
    )
    if expected_refs:
        explicit_refs = {
            text
            for mapping in binding_mappings
            for key in (
                "repair_execution_evidence_ref",
                "owner_receipt_ref",
                "ai_reviewer_recheck_request_ref",
                "request_ref",
                "gate_replay_request_ref",
            )
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_refs.intersection(explicit_refs):
            return True
    expected_source_eval_id = _non_empty_text(repair_precedence.get("source_eval_id"))
    if expected_source_eval_id is not None:
        explicit_source_eval_ids = {
            text
            for mapping in binding_mappings
            for key in ("repair_source_eval_id", "repair_progress_source_eval_id")
            if (text := _non_empty_text(mapping.get(key))) is not None
        }
        if expected_source_eval_id in explicit_source_eval_ids:
            return True
    return False


def _ai_reviewer_consumption_binding_mappings(consumption: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    canonical = _mapping_copy(consumption.get("canonical_work_unit_identity"))
    owner_route_basis = _mapping_copy(consumption.get("owner_route_currentness_basis"))
    canonical_owner_route_basis = _mapping_copy(canonical.get("owner_route_currentness_basis"))
    source_refs = _mapping_copy(consumption.get("source_refs"))
    source_refs_basis = _mapping_copy(source_refs.get("owner_route_currentness_basis"))
    return [
        consumption,
        canonical,
        owner_route_basis,
        canonical_owner_route_basis,
        source_refs,
        source_refs_basis,
    ]


def owner_action_next_step(action: Mapping[str, Any]) -> str | None:
    owner = _non_empty_text(action.get("next_owner"))
    actions = _text_items(action.get("allowed_actions"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    if owner is None and not actions and work_unit_id is None:
        return None
    owner_text = f"{owner} owner" if owner is not None else "当前 owner"
    action_text = f"执行 {actions[0]}" if actions else "处理当前 owner action"
    work_unit_text = f"，处理 work unit {work_unit_id}" if work_unit_id is not None else ""
    return f"等待 {owner_text} {action_text}{work_unit_text}，产出 owner receipt、typed blocker 或下一 owner handoff。"


def _from_stage_artifact_index(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_stage_artifact_index(payload, surface_kind=SURFACE_KIND)


def _from_stage_native_current_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    action = _mapping_copy(payload.get("stage_native_current_owner_action"))
    if _non_empty_text(action.get("source")) != "stage_native_workspace_next_action":
        return None
    owner = _non_empty_text(action.get("next_owner"))
    work_unit_id = _non_empty_text(action.get("work_unit_id"))
    allowed_actions = _text_items(action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "stage_native_workspace_next_action",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "action_type": _non_empty_text(action.get("action_type")),
            "allowed_actions": allowed_actions,
            "owner_receipt_required": action.get("owner_receipt_required") is not False,
            "required_delta_kind": _non_empty_text(action.get("required_delta_kind")),
            "target_surface": _mapping_copy(action.get("target_surface")) or None,
            "source_ref": _non_empty_text(action.get("source_ref")),
            "authority_boundary": _mapping_copy(action.get("authority_boundary"))
            or _authority_boundary(),
        }
    )


def _from_domain_transition(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    transition = _mapping_copy(payload.get("domain_transition"))
    next_work_unit = _mapping_copy(transition.get("next_work_unit"))
    owner = _non_empty_text(transition.get("owner")) or _non_empty_text(transition.get("route_target"))
    work_unit_id = _non_empty_text(next_work_unit.get("unit_id"))
    action = _non_empty_text(transition.get("controller_action"))
    if owner is None and work_unit_id is None and action is None:
        return None
    return _compact(
        {
            "surface_kind": SURFACE_KIND,
            "schema_version": 1,
            "status": "ready",
            "source": "domain_transition",
            "next_owner": owner,
            "work_unit_id": work_unit_id,
            "allowed_actions": [action] if action is not None else [],
            "owner_receipt_required": True,
            "authority_boundary": _authority_boundary(),
        }
    )


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _authority_boundary() -> dict[str, bool]:
    return {
        "refs_only": True,
        "can_write_runtime_owned_surfaces": False,
        "can_write_paper_or_package": False,
        "can_authorize_quality_verdict": False,
        "can_authorize_publication_ready": False,
    }


def _text_items(value: object) -> list[str]:
    if isinstance(value, str):
        text = _non_empty_text(value)
        return [text] if text is not None else []
    if not isinstance(value, list | tuple | set):
        return []
    result: list[str] = []
    for item in value:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _dedupe_text(items: list[str | None]) -> list[str]:
    result: list[str] = []
    for item in items:
        text = _non_empty_text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _compact(payload: Mapping[str, Any]) -> dict[str, Any]:
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}


__all__ = [
    "SURFACE_KIND",
    "build_current_executable_owner_action",
    "owner_action_next_step",
]
