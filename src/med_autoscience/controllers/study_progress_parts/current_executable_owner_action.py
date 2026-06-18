from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.domain_health_diagnostic_parts.current_ai_reviewer_gate_replay import (
    current_ai_reviewer_gate_replay_fingerprint,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.current_work_unit_parts.repair_progress_precedence import (
    gate_replay_action_supersedes_stage_packet_blocker,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)
from med_autoscience.controllers.owner_route_reconcile_parts.stage_artifact_owner_actions import (
    READINESS_GATE_REPAIR_WORK_UNIT,
)

from .current_executable_owner_action_parts.action_types import (
    AI_REVIEWER_OWNER,
    AI_REVIEWER_WORK_UNIT,
    GATE_CLEARING_ACTION,
    GATE_CLEARING_OWNER,
    GATE_CLEARING_WORK_UNIT,
    QUALITY_REPAIR_ACTION,
    REPAIR_PROGRESS_SOURCE,
    TERMINAL_NEXT_FORCED_DELTA_ACTIONS,
)
from .current_executable_owner_action_parts.ai_reviewer_followup import (
    ai_reviewer_eval_receipt_consumes_repair_followup,
    consumed_ai_reviewer_followup_allows_publication_repair,
    terminal_stage_closeout_consumes_repair_followup,
)
from .current_executable_owner_action_parts.domain_transition import (
    consumed_closeout_typed_blocker_allows_domain_transition_successor,
    owner_action_from_domain_transition,
)
from .current_executable_owner_action_parts.gate_followthrough import (
    GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES,
    owner_action_from_gate_followthrough_current_work_unit,
)
from .current_executable_owner_action_parts import gate_replay_identity
from .current_executable_owner_action_parts.non_advancing_terminal_closeout import (
    canonical_current_work_unit_has_non_advancing_apply,
    without_same_identity_non_advancing_apply,
    without_same_identity_terminal_typed_blocker,
)
from .current_executable_owner_action_parts.paper_recovery import (
    owner_action_from_paper_recovery_state,
    paper_recovery_successor_action_ready,
    paper_recovery_successor_supersedes_gate_replay_blocker,
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
GATE_REPLAY_WORK_UNITS = PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS | frozenset({READINESS_GATE_REPAIR_WORK_UNIT})


def build_current_executable_owner_action(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    repair_progress_action = _without_canonical_terminal_blocker(
        payload,
        _from_repair_progress_projection(payload),
    )
    gate_followthrough_action = _without_canonical_terminal_blocker(
        payload,
        _from_gate_followthrough_current_work_unit(payload),
    )
    paper_recovery_action = _without_canonical_terminal_blocker(
        payload,
        _from_paper_recovery_state(payload),
    )
    domain_transition_action = _without_canonical_terminal_blocker(
        payload,
        _from_domain_transition(payload),
    )
    if _repair_progress_consumes_paper_recovery_successor(
        repair_progress_action=repair_progress_action,
        paper_recovery_action=paper_recovery_action,
        payload=payload,
    ):
        return repair_progress_action
    if paper_recovery_successor_supersedes_gate_replay_blocker(
        paper_recovery_action=paper_recovery_action,
        payload=payload,
    ):
        return paper_recovery_action
    if paper_recovery_successor_action_ready(paper_recovery_action):
        return paper_recovery_action
    if (
        domain_transition_action is not None
        and consumed_closeout_typed_blocker_allows_domain_transition_successor(
            payload=payload,
            domain_transition_action=domain_transition_action,
            repair_progress_action=repair_progress_action,
        )
    ):
        return domain_transition_action
    if _ai_reviewer_transition_supersedes_consumed_write_followthrough(
        payload=payload,
        domain_transition_action=domain_transition_action,
        gate_followthrough_action=gate_followthrough_action,
        repair_progress_action=repair_progress_action,
    ):
        return domain_transition_action
    if _gate_followthrough_supersedes_repair_progress(
        gate_followthrough_action=gate_followthrough_action,
        repair_progress_action=repair_progress_action,
        payload=payload,
    ):
        return gate_followthrough_action
    if _canonical_current_work_unit_has_terminal_stop_loss(
        payload,
        repair_progress_action=repair_progress_action,
    ):
        return None
    publication_repair_action = _from_publication_eval_readiness_blocker_repair(payload)
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
            and consumed_ai_reviewer_followup_allows_publication_repair(payload)
        ):
            return publication_repair_action
        next_forced_delta_action = _from_current_next_forced_delta(payload)
        if _next_forced_delta_supersedes_gate_followthrough(
            next_forced_delta_action=next_forced_delta_action,
            gate_followthrough_action=gate_followthrough_action,
        ):
            return next_forced_delta_action
        if _terminal_gate_closeout_blocks_repair_followup(
            action=repair_progress_action,
            payload=payload,
        ):
            if publication_repair_action is not None:
                return publication_repair_action
            return None
        if gate_followthrough_action is not None:
            return gate_followthrough_action
        if _stage_kernel_readiness_stable_typed_blocker_answer(payload):
            if _next_forced_delta_is_terminal_routeback_action(next_forced_delta_action):
                return next_forced_delta_action
            if (
                publication_repair_action is not None
                and (
                    not repair_progress_consumes_publication_repair
                    or consumed_ai_reviewer_followup_allows_publication_repair(payload)
                )
            ):
                return publication_repair_action
            if next_forced_delta_action is not None:
                return next_forced_delta_action
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
    return next_forced_delta_action or domain_transition_action or paper_recovery_action


def _canonical_current_work_unit_has_terminal_stop_loss(
    payload: Mapping[str, Any],
    *,
    repair_progress_action: Mapping[str, Any] | None,
) -> bool:
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
    if _repair_progress_supersedes_terminal_stop_loss(
        repair_progress_action=repair_progress_action,
        blocker={**typed_blocker, **closeout_like},
    ):
        return False
    if canonical_current_work_unit_has_non_advancing_apply(payload):
        return True
    return is_anti_loop_stop_loss_closeout(closeout_like)


def _without_canonical_terminal_blocker(
    payload: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    return without_same_identity_terminal_typed_blocker(
        payload,
        without_same_identity_non_advancing_apply(payload, action),
    )


def _repair_progress_consumes_paper_recovery_successor(
    *,
    repair_progress_action: Mapping[str, Any] | None,
    paper_recovery_action: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> bool:
    repair_action = _mapping_copy(repair_progress_action)
    paper_action = _mapping_copy(paper_recovery_action)
    if not repair_action or not paper_action:
        return False
    if not paper_recovery_successor_action_ready(paper_action):
        return False
    if _non_empty_text(repair_action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    repair_progress = _mapping_copy(payload.get("repair_progress_projection"))
    if repair_progress.get("paper_delta_observed") is not True:
        return False
    if repair_progress.get("accepted_owner_receipt") is not True:
        return False
    if repair_progress.get("gate_replay_done") is not True:
        return False
    current_work_unit = _mapping_copy(payload.get("current_work_unit"))
    if _non_empty_text(current_work_unit.get("status")) != "executable_owner_action":
        return False
    current_source = _non_empty_text(_mapping_copy(current_work_unit.get("state")).get("source"))
    if current_source != "paper_recovery_state.next_safe_action.successor_owner_action":
        return False
    source_work_unit = _non_empty_text(
        _mapping_copy(repair_action.get("repair_progress_precedence")).get("source_work_unit_id")
    ) or _non_empty_text(repair_progress.get("work_unit_id"))
    if source_work_unit is None or source_work_unit != _non_empty_text(paper_action.get("work_unit_id")):
        return False
    if source_work_unit != _non_empty_text(current_work_unit.get("work_unit_id")):
        return False
    repair_eval = _non_empty_text(repair_progress.get("source_eval_id")) or _non_empty_text(
        repair_action.get("source_eval_id")
    )
    paper_eval = _non_empty_text(paper_action.get("source_eval_id"))
    if repair_eval is not None and paper_eval is not None and repair_eval != paper_eval:
        return False
    followthrough = _mapping_copy(payload.get("gate_clearing_batch_followthrough"))
    if not followthrough:
        return False
    currentness = _mapping_copy(followthrough.get("work_unit_currentness"))
    if _non_empty_text(currentness.get("current_actionability_status")) != "actionable":
        return False
    if currentness.get("lacks_specific_blocker_object") is True:
        return False
    followthrough_work_unit = (
        _non_empty_text(followthrough.get("work_unit_id"))
        or _non_empty_text(currentness.get("current_publication_work_unit_id"))
        or _non_empty_text(_mapping_copy(followthrough.get("current_publication_work_unit")).get("unit_id"))
    )
    if followthrough_work_unit != source_work_unit:
        return False
    paper_fingerprint = _non_empty_text(paper_action.get("work_unit_fingerprint")) or _non_empty_text(
        paper_action.get("action_fingerprint")
    )
    current_fingerprint = _non_empty_text(current_work_unit.get("work_unit_fingerprint")) or _non_empty_text(
        current_work_unit.get("action_fingerprint")
    )
    if paper_fingerprint is None or current_fingerprint != paper_fingerprint:
        return False
    followthrough_fingerprint = (
        _non_empty_text(followthrough.get("work_unit_fingerprint"))
        or _non_empty_text(currentness.get("current_work_unit_fingerprint"))
        or _non_empty_text(currentness.get("explicit_work_unit_fingerprint"))
    )
    if followthrough_fingerprint != paper_fingerprint:
        return False
    return True


def _repair_progress_supersedes_terminal_stop_loss(
    *,
    repair_progress_action: Mapping[str, Any] | None,
    blocker: Mapping[str, Any],
) -> bool:
    action = _mapping_copy(repair_progress_action)
    if not action:
        return False
    return gate_replay_action_supersedes_stage_packet_blocker(
        action=action,
        blocker=blocker,
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    )


def _ai_reviewer_transition_supersedes_consumed_write_followthrough(
    *,
    payload: Mapping[str, Any],
    domain_transition_action: Mapping[str, Any] | None,
    gate_followthrough_action: Mapping[str, Any] | None,
    repair_progress_action: Mapping[str, Any] | None,
) -> bool:
    transition_action = _mapping_copy(domain_transition_action)
    gate_action = _mapping_copy(gate_followthrough_action)
    repair_action = _mapping_copy(repair_progress_action)
    if not transition_action or not gate_action or not repair_action:
        return False
    if _non_empty_text(transition_action.get("source")) != "domain_transition":
        return False
    if _non_empty_text(transition_action.get("next_owner")) != AI_REVIEWER_OWNER:
        return False
    if _non_empty_text(transition_action.get("action_type")) != "return_to_ai_reviewer_workflow":
        return False
    if _non_empty_text(transition_action.get("domain_transition_decision_type")) != "ai_reviewer_re_eval":
        return False
    transition_work_unit = _non_empty_text(transition_action.get("work_unit_id"))
    if transition_work_unit is None:
        return False
    transition_fingerprint = (
        _non_empty_text(transition_action.get("work_unit_fingerprint"))
        or _non_empty_text(transition_action.get("action_fingerprint"))
    )
    if transition_fingerprint != f"domain-transition::ai_reviewer_re_eval::{transition_work_unit}":
        return False

    if _non_empty_text(gate_action.get("source")) != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    if _non_empty_text(gate_action.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    if _non_empty_text(repair_action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False

    repair_progress = _mapping_copy(payload.get("repair_progress_projection"))
    if repair_progress.get("accepted_owner_receipt") is not True:
        return False
    if repair_progress.get("gate_replay_done") is not True:
        return False
    if repair_progress.get("ai_reviewer_recheck_required") is not True and (
        repair_progress.get("ai_reviewer_recheck_done") is not True
    ):
        return False

    repair_source_work_unit = _non_empty_text(
        _mapping_copy(repair_action.get("repair_progress_precedence")).get("source_work_unit_id")
    ) or _non_empty_text(repair_progress.get("work_unit_id"))
    if repair_source_work_unit is None:
        return False
    if repair_source_work_unit != _non_empty_text(gate_action.get("work_unit_id")):
        return False

    gate_currentness = _mapping_copy(
        _mapping_copy(payload.get("gate_clearing_batch_followthrough")).get("work_unit_currentness")
    )
    current_gate_work_unit = (
        _non_empty_text(gate_currentness.get("current_publication_work_unit_id"))
        or _non_empty_text(gate_action.get("work_unit_id"))
    )
    if repair_source_work_unit != current_gate_work_unit:
        return False

    completion = _mapping_copy(_mapping_copy(payload.get("domain_transition")).get("completion_receipt_consumption"))
    if _non_empty_text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    consumed_work_unit = _non_empty_text(completion.get("work_unit_id"))
    if consumed_work_unit not in {None, repair_source_work_unit, transition_work_unit, AI_REVIEWER_WORK_UNIT}:
        return False

    repair_fingerprint = (
        _non_empty_text(repair_progress.get("work_unit_fingerprint"))
        or _non_empty_text(repair_progress.get("action_fingerprint"))
        or _non_empty_text(repair_progress.get("source_fingerprint"))
    )
    gate_fingerprint = (
        _non_empty_text(gate_action.get("work_unit_fingerprint"))
        or _non_empty_text(gate_action.get("action_fingerprint"))
        or _non_empty_text(gate_currentness.get("current_work_unit_fingerprint"))
        or _non_empty_text(gate_currentness.get("explicit_work_unit_fingerprint"))
    )
    consumed_fingerprint = (
        _non_empty_text(completion.get("work_unit_fingerprint"))
        or _non_empty_text(completion.get("action_fingerprint"))
    )
    if repair_fingerprint is not None and gate_fingerprint is not None and repair_fingerprint != gate_fingerprint:
        return False
    if (
        consumed_work_unit == repair_source_work_unit
        and consumed_fingerprint is not None
        and repair_fingerprint is not None
            and consumed_fingerprint != repair_fingerprint
    ):
        return False
    if (
        consumed_work_unit == transition_work_unit
        and consumed_fingerprint is not None
        and transition_fingerprint is not None
        and consumed_fingerprint != transition_fingerprint
    ):
        return False
    return True


def _from_current_next_forced_delta(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    terminal_action = owner_action_from_terminal_next_forced_delta(
        payload,
        surface_kind=SURFACE_KIND,
    )
    if terminal_action is not None:
        return terminal_action
    return _from_next_forced_delta(payload)


def _from_gate_followthrough_current_work_unit(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_gate_followthrough_current_work_unit(
        payload,
        surface_kind=SURFACE_KIND,
    )


def _from_paper_recovery_state(payload: Mapping[str, Any]) -> dict[str, Any] | None:
    return owner_action_from_paper_recovery_state(payload, surface_kind=SURFACE_KIND)


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


def _gate_followthrough_supersedes_repair_progress(
    *,
    gate_followthrough_action: Mapping[str, Any] | None,
    repair_progress_action: Mapping[str, Any] | None,
    payload: Mapping[str, Any],
) -> bool:
    gate_action = _mapping_copy(gate_followthrough_action)
    repair_action = _mapping_copy(repair_progress_action)
    if not gate_action or not repair_action:
        return False
    if _non_empty_text(gate_action.get("source")) != "gate_clearing_batch_followthrough.actionable_current_work_unit":
        return False
    if _non_empty_text(repair_action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(gate_action.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    if _non_empty_text(repair_action.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    if _terminal_gate_closeout_blocks_repair_followup(
        action=repair_action,
        payload=payload,
    ):
        return False
    if _repair_progress_consumes_gate_followthrough_work_unit(
        gate_action=gate_action,
        repair_action=repair_action,
        payload=None,
    ):
        return False
    repair_precedence = _mapping_copy(repair_action.get("repair_progress_precedence"))
    source_work_unit = _non_empty_text(repair_precedence.get("source_work_unit_id"))
    if source_work_unit is not None and source_work_unit != _non_empty_text(gate_action.get("work_unit_id")):
        return False
    gate_eval = _non_empty_text(gate_action.get("source_eval_id"))
    repair_eval = _non_empty_text(repair_action.get("source_eval_id"))
    if gate_eval is not None and repair_eval is not None and gate_eval != repair_eval:
        return False
    return _ref_sets_intersect(
        _gate_followthrough_action_refs(gate_action),
        _repair_followup_gate_action_refs(repair_action),
    )


def _repair_progress_consumes_gate_followthrough_work_unit(
    *,
    gate_action: Mapping[str, Any],
    repair_action: Mapping[str, Any],
    payload: Mapping[str, Any] | None,
) -> bool:
    repair_precedence = _mapping_copy(repair_action.get("repair_progress_precedence"))
    source_work_unit = _non_empty_text(repair_precedence.get("source_work_unit_id"))
    if source_work_unit is None or source_work_unit != _non_empty_text(gate_action.get("work_unit_id")):
        return False
    gate_eval = _non_empty_text(gate_action.get("source_eval_id"))
    repair_eval = _non_empty_text(repair_action.get("source_eval_id"))
    if gate_eval is None or repair_eval is None or gate_eval != repair_eval:
        return False
    if _non_empty_text(gate_action.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    repair_fingerprint = (
        _non_empty_text(repair_precedence.get("work_unit_fingerprint"))
        or _non_empty_text(repair_precedence.get("action_fingerprint"))
        or gate_replay_identity.action_fingerprint(repair_action)
        or _non_empty_text(repair_precedence.get("source_fingerprint"))
    )
    gate_fingerprint = gate_replay_identity.action_fingerprint(gate_action)
    if (
        gate_replay_identity.canonical_gate_replay_typed_blocker_matches_repair_progress(
            payload=payload,
            repair_action=repair_action,
            repair_fingerprint=repair_fingerprint,
            gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
        )
        and gate_fingerprint is not None
        and repair_fingerprint is not None
        and gate_fingerprint != repair_fingerprint
    ):
        return False
    if _non_empty_text(repair_action.get("action_type")) == GATE_CLEARING_ACTION:
        return (
            gate_fingerprint is not None
            and repair_fingerprint is not None
            and gate_fingerprint == repair_fingerprint
        )
    return True


def _gate_followthrough_action_refs(action: Mapping[str, Any]) -> set[str]:
    target_surface = _mapping_copy(action.get("target_surface"))
    return _ref_set(
        [
            target_surface.get("gate_clearing_batch_ref"),
            action.get("source_ref"),
            *list(action.get("acceptance_refs") or []),
        ]
    )


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
    if terminal_stage_closeout_consumes_repair_followup(action=action, payload=payload):
        return True
    if _terminal_gate_closeout_consumes_repair_followup(action=action, payload=payload):
        return True
    if _gate_followthrough_consumes_repair_progress_gate_replay(action=action, payload=payload):
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
    return ai_reviewer_eval_receipt_consumes_repair_followup(
        action=action,
        consumption=consumption,
    )


def _gate_followthrough_consumes_repair_progress_gate_replay(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    if _non_empty_text(action.get("work_unit_id")) != GATE_CLEARING_WORK_UNIT:
        return False
    followthrough = _mapping_copy(payload.get("gate_clearing_batch_followthrough"))
    if _non_empty_text(followthrough.get("status")) not in GATE_CLEARING_FOLLOWTHROUGH_CONSUMED_STATUSES:
        return False
    if _non_empty_text(followthrough.get("gate_replay_status")) != "blocked":
        return False
    gate_followthrough_action = _from_gate_followthrough_current_work_unit(payload)
    if _non_empty_text(gate_followthrough_action.get("source")) != (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    ):
        return False
    if _non_empty_text(gate_followthrough_action.get("action_type")) != QUALITY_REPAIR_ACTION:
        return False
    if _repair_progress_consumes_gate_followthrough_work_unit(
        gate_action=gate_followthrough_action,
        repair_action=action,
        payload=payload,
    ):
        return False
    return _ref_sets_intersect(
        _repair_followup_gate_action_refs(action),
        _gate_followthrough_record_refs(
            followthrough,
            gate_followthrough_action=gate_followthrough_action,
        ),
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
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("work_unit_fingerprint"))
        or _non_empty_text(_mapping_copy(action.get("repair_progress_precedence")).get("action_fingerprint"))
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


def _terminal_gate_closeout_blocks_repair_followup(
    *,
    action: Mapping[str, Any],
    payload: Mapping[str, Any],
) -> bool:
    if _non_empty_text(action.get("source")) != REPAIR_PROGRESS_SOURCE:
        return False
    if _non_empty_text(action.get("action_type")) != GATE_CLEARING_ACTION:
        return False
    terminal = _latest_gate_replay_terminal_stage(payload)
    if not terminal:
        return False
    if _non_empty_text(terminal.get("status")) != "blocked":
        return False
    outcome = _non_empty_text(terminal.get("outcome"))
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    if outcome is None:
        outcome = _non_empty_text(paper_stage_log.get("outcome"))
    if outcome != "blocked:publication_gate_replay_blocked":
        return False
    remaining = [
        item
        for item in _text_items(terminal.get("remaining_blockers"))
        if item != "publication_gate_replay_blocked"
    ]
    if not remaining:
        remaining = [
            item
            for item in _text_items(paper_stage_log.get("remaining_blockers"))
            if item != "publication_gate_replay_blocked"
        ]
    if not remaining:
        return False
    return _terminal_gate_closeout_consumes_repair_followup(action=action, payload=payload)


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


def _repair_followup_gate_request_refs(action: Mapping[str, Any]) -> set[str]:
    target_surface = _mapping_copy(action.get("target_surface"))
    return _ref_set([target_surface.get("request_ref")])


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


def _gate_followthrough_record_refs(
    followthrough: Mapping[str, Any],
    *,
    gate_followthrough_action: Mapping[str, Any],
) -> set[str]:
    target_surface = _mapping_copy(gate_followthrough_action.get("target_surface"))
    return _ref_set(
        [
            followthrough.get("latest_record_path"),
            followthrough.get("source_ref"),
            followthrough.get("record_path"),
            target_surface.get("gate_clearing_batch_ref"),
            *list(gate_followthrough_action.get("acceptance_refs") or []),
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
    return owner_action_from_domain_transition(payload, surface_kind=SURFACE_KIND)


def _mapping_items(value: object) -> list[dict[str, Any]]:
    if not isinstance(value, list | tuple):
        return []
    return [dict(item) for item in value if isinstance(item, Mapping)]


def _authority_boundary() -> dict[str, bool]:
    return {
        "authority": False,
        "refs_only": True,
        "projection_owner": "med-autoscience",
        "fixed_point_runtime_owner": "one-person-lab",
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
