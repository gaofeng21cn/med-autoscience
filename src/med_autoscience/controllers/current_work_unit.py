from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from med_autoscience.controllers import carry_forward_risk
from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    consumed_gate_replay_blocker_for_action,
    terminal_closeout_blocker_for_action,
)
from med_autoscience.controllers.current_work_unit_parts.terminal_routeback_currentness import (
    gate_followthrough_actionable_repair_action as _gate_followthrough_actionable_repair_action,
    gate_followthrough_action_supersedes_publication_gate_replay_blocker as _gate_followthrough_supersedes_publication_gate_replay_blocker,
    gate_followthrough_action_supersedes_transport_or_execution_residue as _gate_followthrough_supersedes_transport_or_execution_residue,
    terminal_routeback_action_from_gate_closeout as _terminal_routeback_action_from_gate_closeout,
    terminal_routeback_action_supersedes_gate_replay_blocker as _terminal_routeback_action_supersedes_gate_replay_blocker,
)
from med_autoscience.controllers.gate_clearing_batch_work_units import (
    PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS,
)
from med_autoscience.controllers.paper_mission_owner_surface_parts.stage_artifact_owner_actions import (
    READINESS_GATE_REPAIR_WORK_UNIT,
)
from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_fingerprint as _action_fingerprint,
    action_type as _action_type,
    work_unit_fingerprint as _work_unit_fingerprint,
    work_unit_id as _work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.action_identity import (
    provider_handoff_matches_action as _provider_handoff_matches_action,
    provider_handoff_matches_transition_request_action as _provider_handoff_matches_transition_request_action,
    same_action_identity as _same_action_identity,
)
from med_autoscience.controllers.current_work_unit_parts.current_action_selection import (
    selected_current_action as _selected_current_action,
)
from med_autoscience.controllers.current_work_unit_parts.currentness_basis import (
    currentness_basis as _currentness_basis,
    minimal_blocker as _minimal_blocker,
    typed_blocker as _typed_blocker,
)
from med_autoscience.controllers.current_work_unit_parts.currentness_identity import (
    action_has_strong_currentness_identity as _action_has_strong_currentness_identity,
    action_matches_next_forced_delta as _action_matches_next_forced_delta,
    action_with_derived_currentness_identity as _action_with_derived_currentness_identity,
)
from med_autoscience.controllers.current_work_unit_parts.contract import (
    ALLOWED_STATUSES,
    SURFACE_KIND,
)
from med_autoscience.controllers.current_work_unit_parts.dispatch_consumption import (
    action_consumed_by_dispatch_receipt as _action_consumed_by_dispatch_receipt,
)
from med_autoscience.controllers.current_work_unit_parts.domain_transition import (
    domain_transition_supersedes_provider_completion_blocker as _domain_transition_supersedes_provider_completion_blocker,
)
from med_autoscience.controllers.current_work_unit_parts.paper_recovery_successor import (
    action_supersedes_terminal_selector_residue as _action_supersedes_terminal_selector_residue,
    paper_recovery_successor_action_ready as _paper_recovery_successor_action_ready,
    paper_recovery_successor_supersedes_publication_gate_replay_blocker as _paper_recovery_successor_supersedes_publication_gate_replay_blocker,
)
from med_autoscience.controllers.current_work_unit_parts.paper_recovery_projection import (
    owner_receipt_recorded_recovery as _owner_receipt_recorded_recovery,
    paper_recovery_successor_action as _paper_recovery_successor_action,
    paper_recovery_successor_consumes_terminal_stop_loss as _safe_paper_recovery_successor_consumes_terminal_stop_loss,
    repair_progress_proves_safe_successor_delta as _repair_progress_proves_safe_successor_delta,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    CURRENT_ACTION_SUPERSEDED_PRIOR_ACTION_BLOCKERS,
    CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS,
    MEDICAL_READINESS_BLOCKERS,
    OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE,
    PAPER_DELTA_PRIOR_BLOCKER_SUPERSEDING_ACTION_SOURCES,
    PUBLICATION_EVAL_READINESS_REPAIR_SOURCE,
    PROVIDER_ADMISSION_AUTHORITIES,
    PROVIDER_ADMISSION_REPAIR_ACTIONS,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping as _mapping,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.controllers.current_work_unit_parts.repair_progress_precedence import (
    gate_replay_action_supersedes_stage_packet_blocker,
    repair_progress_gate_replay_action_supersedes_gate_replay_blocker,
)
from med_autoscience.controllers.current_work_unit_parts.repair_progress_action import (
    repair_progress_action_consuming_current_action as _repair_progress_action_consuming_current_action,
)
from med_autoscience.controllers.current_work_unit_parts.running_provider_attempt import (
    running_attempt_can_supersede_blocker,
    running_attempt_invalidated_by_progress,
    running_attempt_matches_current_action,
    running_attempt_satisfies_stage_owner_answer,
    running_work_unit_id,
    strict_running_provider_attempt,
    typed_blocker_is_terminal_stop_loss,
)
from med_autoscience.controllers.current_work_unit_parts.stage_owner_answer import (
    stage_owner_answer_identity_typed_blocker as _stage_owner_answer_identity_typed_blocker,
    stage_owner_answer_missing_action as _stage_owner_answer_missing_action,
    stage_owner_answer_typed_blocker as _stage_owner_answer_typed_blocker,
)
from med_autoscience.controllers.current_work_unit_parts.stage_packet_identity import (
    terminal_action_blocker_has_fresher_identity as _terminal_action_blocker_has_fresher_identity,
)
from med_autoscience.controllers.current_work_unit_parts.projection import (
    action_work_unit as _action_work_unit,
    owner_receipt_work_unit as _owner_receipt_work_unit,
    running_provider_attempt_work_unit as _running_provider_attempt_work_unit,
    typed_blocker_work_unit as _typed_blocker_work_unit,
)
from med_autoscience.controllers.current_work_unit_parts.typed_blocker_owner_answer import (
    typed_blocker_has_owner_answer_currentness as _typed_blocker_has_owner_answer_currentness,
    typed_blocker_is_stage_owner_answer as _typed_blocker_is_stage_owner_answer,
    typed_blocker_precedes_stage_owner_answer as _typed_blocker_precedes_stage_owner_answer,
)
from med_autoscience.controllers.current_work_unit_parts.work_unit_fields import (
    action_owner as _action_owner,
    delta_count as _delta_count,
    source_refs as _source_refs,
)
from med_autoscience.controllers.study_progress_parts.canonical_next_action_gate import (
    has_canonical_next_action,
)


GATE_REPLAY_WORK_UNITS = PUBLICATION_GATE_REPLAY_WORK_UNIT_IDS | frozenset({READINESS_GATE_REPAIR_WORK_UNIT})


def build_current_work_unit(
    *,
    status: Mapping[str, Any] | None = None,
    progress: Mapping[str, Any] | None = None,
    actions: Sequence[Mapping[str, Any]] | None = None,
    current_executable_owner_action: Mapping[str, Any] | None = None,
    current_execution_envelope: Mapping[str, Any] | None = None,
    owner_route: Mapping[str, Any] | None = None,
    provider_admission: Mapping[str, Any] | None = None,
    provider_running_proof: Mapping[str, Any] | None = None,
    live_provider_attempt: Mapping[str, Any] | None = None,
    typed_blocker: Mapping[str, Any] | None = None,
    blocked_reason: str | None = None,
    next_owner: str | None = None,
    runtime_health: Mapping[str, Any] | None = None,
    source_refs: Sequence[str] | None = None,
) -> dict[str, Any]:
    status_payload = _mapping(status)
    progress_payload = _mapping(progress)
    if has_canonical_next_action(progress_payload):
        return {}
    route_payload = _mapping(owner_route)
    runtime_health_payload = _mapping(runtime_health)
    resolved_source_refs = _source_refs(status_payload, progress_payload, source_refs)
    stage_owner_answer_action = _stage_owner_answer_missing_action(progress_payload)
    paper_recovery_successor = _paper_recovery_successor_action(progress_payload)
    progress_first_current_action = _mapping(
        _mapping(progress_payload.get("progress_first_monitoring_summary")).get(
            "current_executable_owner_action"
        )
    )
    action = paper_recovery_successor or _selected_current_action(
        actions=actions,
        current_executable_owner_action=current_executable_owner_action
        or progress_first_current_action,
    )
    current_action_owner_receipt_recovery = None
    if not _provider_handoff_matches_action(
        provider_admission=provider_admission,
        action=action,
    ):
        current_action_owner_receipt_recovery = _repair_progress_owner_receipt_recovery(
            progress=progress_payload,
            action=action,
        )
    if current_action_owner_receipt_recovery is None:
        repair_progress_action = _repair_progress_action_consuming_current_action(
            progress=progress_payload,
            current_action=action,
            provider_admission=provider_admission,
            surface_kind="current_executable_owner_action",
        )
        if repair_progress_action is not None:
            action = repair_progress_action
    carry_forward_successor = carry_forward_risk.carry_forward_successor_action(progress_payload)
    if action is None and carry_forward_successor is not None:
        action = carry_forward_successor
    if stage_owner_answer_action is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        action = stage_owner_answer_action
    elif (
        action is not None
        and not _domain_transition_successor_consumes_owner_receipt(
            action=action,
            status=status_payload,
            progress=progress_payload,
        )
        and _action_consumed_by_dispatch_receipt(action=action, progress=progress_payload)
    ):
        action = None
    if action is not None:
        action = _action_with_derived_currentness_identity(
            action=action,
            progress=progress_payload,
            gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
        )
        if not _action_has_strong_currentness_identity(
            action,
            gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
        ):
            action = None
    resolved_typed_blocker = _typed_blocker(
        typed_blocker,
        blocked_reason=blocked_reason,
        owner=next_owner,
    ) or carry_forward_risk.fatal_budget_exhausted_blocker(progress_payload)
    terminal_action_blocker = terminal_closeout_blocker_for_action(
        progress_payload,
        action=action,
        mapping=_mapping,
        text=_text,
        text_items=_text_items,
        action_type=_action_type,
        work_unit_id=_work_unit_id,
        work_unit_fingerprint=_work_unit_fingerprint,
        action_fingerprint=_action_fingerprint,
    )
    terminal_action_blocker_selected = False
    if terminal_action_blocker is not None and (
        not _typed_blocker_has_owner_answer_currentness(resolved_typed_blocker)
        or _typed_blocker_is_stage_owner_answer(resolved_typed_blocker)
        or _terminal_action_blocker_has_fresher_identity(
            terminal_action_blocker,
            existing_blocker=resolved_typed_blocker,
        )
    ):
        resolved_typed_blocker = terminal_action_blocker
        terminal_action_blocker_selected = True
    running_attempt = strict_running_provider_attempt(
        live_provider_attempt=live_provider_attempt,
        provider_running_proof=provider_running_proof,
        runtime_health=runtime_health_payload,
        owner=next_owner,
    )
    if running_attempt is None:
        running_attempt = strict_running_provider_attempt(
            live_provider_attempt=provider_admission,
            provider_running_proof=None,
            runtime_health=runtime_health_payload,
            owner=next_owner,
        )
    if running_attempt is not None and running_attempt_invalidated_by_progress(progress_payload):
        running_attempt = None
    if running_attempt is not None and not running_attempt_matches_current_action(
        running_attempt=running_attempt,
        action=action,
    ):
        running_attempt = None
    if (
        running_attempt is not None
        and stage_owner_answer_action is not None
        and not running_attempt_satisfies_stage_owner_answer(
            running_attempt=running_attempt,
            owner_answer_action=stage_owner_answer_action,
        )
    ):
        running_attempt = None
    stage_owner_identity_blocker = _stage_owner_answer_identity_typed_blocker(progress_payload)
    basis = _currentness_basis(
        owner_route=route_payload,
        action=action,
        progress=progress_payload,
        runtime_health=runtime_health_payload,
        running_attempt=running_attempt,
    )
    fallback_owner_receipt_recovery = None
    if not _provider_handoff_matches_action(
        provider_admission=provider_admission,
        action=action,
    ):
        fallback_owner_receipt_recovery = _repair_progress_owner_receipt_recovery(
            progress=progress_payload,
            action=action,
        )
    owner_receipt_recovery = (
        _owner_receipt_recorded_recovery(progress_payload)
        or current_action_owner_receipt_recovery
        or fallback_owner_receipt_recovery
    )
    if (
        action is not None
        and resolved_typed_blocker is not None
        and typed_blocker_is_terminal_stop_loss(resolved_typed_blocker)
        and (
            _safe_next_forced_delta_action_supersedes_terminal_stop_loss(
                action=action,
                blocker=resolved_typed_blocker,
                progress=progress_payload,
            )
            or _action_supersedes_typed_blocker(
                action=action,
                blocker=resolved_typed_blocker,
                progress=progress_payload,
            )
        )
    ):
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    if owner_receipt_recovery is not None and not _owner_receipt_consumed_by_actionable_successor(
        action=action,
        status=status_payload,
        progress=progress_payload,
    ):
        return _owner_receipt_work_unit(
            recovery=owner_receipt_recovery,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
        )
    gate_replay_blocker = consumed_gate_replay_blocker_for_action(
        progress=progress_payload,
        action=action,
        currentness_basis=basis,
        mapping=_mapping,
        text=_text,
        text_items=_text_items,
    )
    if (
        gate_replay_blocker is not None
        and not (
            running_attempt is not None
            and running_attempt_can_supersede_blocker(gate_replay_blocker)
        )
    ):
        return _typed_blocker_work_unit(
            blocker=gate_replay_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="gate_clearing_batch_followthrough",
        )
    if running_attempt is not None and running_attempt_can_supersede_blocker(resolved_typed_blocker):
        return _running_provider_attempt_work_unit(
            owner=_text(running_attempt.get("owner")) or _text(next_owner),
            action_type=_text(running_attempt.get("action_type")),
            work_unit_id=running_work_unit_id(running_attempt, currentness_basis=basis, action=action),
            work_unit_fingerprint=_text(running_attempt.get("work_unit_fingerprint")),
            action_fingerprint=_text(running_attempt.get("action_fingerprint")),
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            running_attempt=running_attempt,
            status_payload=status_payload,
            progress_payload=progress_payload,
            action=action,
        )
    if action is not None and _current_control_transition_request_supersedes_budget_blocker(
        action=action,
        blocker=resolved_typed_blocker,
        provider_admission=provider_admission,
    ):
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    if running_attempt is not None:
        if resolved_typed_blocker is not None:
            if action is not None and _action_supersedes_typed_blocker(
                action=action,
                blocker=resolved_typed_blocker,
                progress=progress_payload,
            ):
                return _action_work_unit(
                    action=action,
                    owner=_action_owner(action, next_owner=next_owner),
                    status_payload=status_payload,
                    progress_payload=progress_payload,
                    source_refs=resolved_source_refs,
                    currentness_basis=basis,
                    provider_admission=provider_admission,
                )
            return _typed_blocker_work_unit(
                blocker=resolved_typed_blocker,
                action=action,
                status_payload=status_payload,
                progress_payload=progress_payload,
                source_refs=resolved_source_refs,
                currentness_basis=basis,
                source="typed_blocker",
            )
    if resolved_typed_blocker is not None and typed_blocker_is_terminal_stop_loss(resolved_typed_blocker):
        if action is not None and (
            _safe_next_forced_delta_action_supersedes_terminal_stop_loss(
                action=action,
                blocker=resolved_typed_blocker,
                progress=progress_payload,
            )
            or _action_supersedes_typed_blocker(
                action=action,
                blocker=resolved_typed_blocker,
                progress=progress_payload,
            )
        ):
            return _action_work_unit(
                action=action,
                owner=_action_owner(action, next_owner=next_owner),
                status_payload=status_payload,
                progress_payload=progress_payload,
                source_refs=resolved_source_refs,
                currentness_basis=basis,
                provider_admission=provider_admission,
            )
        return _typed_blocker_work_unit(
            blocker=resolved_typed_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="typed_blocker",
        )
    if terminal_action_blocker_selected and not (
        action is not None
        and _action_supersedes_typed_blocker(
            action=action,
            blocker=terminal_action_blocker,
            progress=progress_payload,
        )
    ):
        return _typed_blocker_work_unit(
            blocker=terminal_action_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="terminal_closeout_typed_blocker",
        )
    if stage_owner_identity_blocker is not None:
        if action is not None and _domain_transition_successor_consumes_owner_receipt(
            action=action,
            status=status_payload,
            progress=progress_payload,
        ):
            return _action_work_unit(
                action=action,
                owner=_action_owner(action, next_owner=next_owner),
                status_payload=status_payload,
                progress_payload=progress_payload,
                source_refs=resolved_source_refs,
                currentness_basis=basis,
                provider_admission=provider_admission,
            )
        return _typed_blocker_work_unit(
            blocker=stage_owner_identity_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="stage_owner_answer_identity",
            status_kind="blocked_current_work_unit",
        )
    if _typed_blocker_precedes_stage_owner_answer(
        blocker=resolved_typed_blocker,
        action=action,
        progress=progress_payload,
        action_supersedes_typed_blocker=_action_supersedes_typed_blocker,
    ):
        return _typed_blocker_work_unit(
            blocker=resolved_typed_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="typed_blocker",
        )
    stage_owner_answer_blocker = _stage_owner_answer_typed_blocker(progress_payload)
    if stage_owner_answer_blocker is not None and not _action_supersedes_stage_owner_answer(
        action=action,
        progress=progress_payload,
    ):
        return _typed_blocker_work_unit(
            blocker=stage_owner_answer_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="stage_owner_answer",
        )
    if action is not None and _action_supersedes_typed_blocker(
        action=action,
        blocker=resolved_typed_blocker,
        progress=progress_payload,
    ):
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    if resolved_typed_blocker is not None:
        return _typed_blocker_work_unit(
            blocker=resolved_typed_blocker,
            action=action,
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            source="typed_blocker",
        )
    if action is not None:
        return _action_work_unit(
            action=action,
            owner=_action_owner(action, next_owner=next_owner),
            status_payload=status_payload,
            progress_payload=progress_payload,
            source_refs=resolved_source_refs,
            currentness_basis=basis,
            provider_admission=provider_admission,
        )
    blocker = _minimal_blocker(blocked_reason or "current_work_unit_unresolved", owner=next_owner)
    return _typed_blocker_work_unit(
        blocker=blocker,
        action=None,
        status_payload=status_payload,
        progress_payload=progress_payload,
        source_refs=resolved_source_refs,
        currentness_basis=basis,
        source="blocked_current_work_unit",
        status_kind="blocked_current_work_unit",
    )


def _action_supersedes_stage_owner_answer(
    *,
    action: Mapping[str, Any] | None,
    progress: Mapping[str, Any],
) -> bool:
    payload = _mapping(action)
    if not payload:
        return False
    if _paper_recovery_successor_supersedes_publication_gate_replay_blocker(
        action=payload,
        blocker={"blocker_type": "medical_paper_readiness_missing"},
    ):
        return True
    if _paper_recovery_successor_action_ready(payload):
        return True
    if _provider_admission_repair_action_supersedes_readiness_blocker(payload):
        return True
    if _gate_consumption_action_supersedes_readiness_blocker(payload):
        return True
    if _publication_eval_repair_action_supersedes_readiness_blocker(payload):
        return True
    if _terminal_routeback_action_from_gate_closeout(
        action=payload,
        progress=progress,
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    ):
        return True
    return _paper_delta_current_action_supersedes_prior_blocker(
        action=payload,
        progress=progress,
    )


def _current_control_transition_request_supersedes_budget_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    provider_admission: Mapping[str, Any] | None,
) -> bool:
    payload = _mapping(action)
    typed_blocker = _mapping(blocker)
    if payload.get("transition_request_pending") is not True:
        return False
    source = _text(payload.get("source_surface")) or _text(payload.get("source"))
    if source not in {
        "opl_current_control_state.transition_request_candidates",
        "paper_recovery_state.next_safe_action.successor_owner_action",
    }:
        return False
    if not _provider_handoff_matches_transition_request_action(
        provider_admission=provider_admission,
        action=payload,
    ):
        return False
    blocker_type = (
        _text(typed_blocker.get("blocker_type"))
        or _text(typed_blocker.get("blocker_id"))
        or _text(typed_blocker.get("blocked_reason"))
        or _text(typed_blocker.get("reason"))
    )
    if blocker_type in {
        "anti_loop_budget_exhausted",
        "repeat_suppressed_after_opl_execution_authorization_required",
    }:
        return True
    if _text(typed_blocker.get("blocker_id")) == "anti_loop_budget_exhausted":
        return True
    return _text(typed_blocker.get("blocked_reason")) == "anti_loop_budget_exhausted"


def _repair_progress_owner_receipt_recovery(
    *,
    progress: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> dict[str, Any] | None:
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return None
    if repair.get("accepted_owner_receipt") is not True:
        return None
    if repair.get("gate_replay_done") is not True:
        return None
    if not _mapping(action) and _current_work_unit_is_terminal_anti_loop_blocker(progress):
        return None
    if _gate_followthrough_actionable_repair_action(_mapping(action)) and not _repair_progress_matches_action(
        repair=repair,
        action=_mapping(action),
    ):
        return None
    payload = _mapping(action)
    same_work_unit_receipt = _repair_progress_matches_action(repair=repair, action=payload)
    if _progress_has_gate_followthrough_actionable_repair(progress) and not same_work_unit_receipt:
        return None
    owner_receipt_ref = _text(repair.get("owner_receipt_ref")) if same_work_unit_receipt else _repair_progress_gate_replay_receipt_ref(repair)
    if owner_receipt_ref is None:
        return None
    action_type = _action_type(payload) if payload else "run_gate_clearing_batch"
    work_unit_id = _work_unit_id(payload.get("work_unit_id")) if payload else "publication_gate_replay"
    if payload:
        if same_work_unit_receipt:
            if action_type != "run_quality_repair_batch" or work_unit_id != _work_unit_id(repair.get("work_unit_id")):
                return None
        elif action_type != "run_gate_clearing_batch" or work_unit_id not in GATE_REPLAY_WORK_UNITS:
            return None
    work_unit_fingerprint = (
        _text(payload.get("work_unit_fingerprint"))
        or _text(payload.get("action_fingerprint"))
        or _text(repair.get("work_unit_fingerprint"))
        or _text(repair.get("action_fingerprint"))
        or _text(repair.get("source_fingerprint"))
    )
    return {
        "surface_kind": "paper_recovery_state",
        "schema_version": 1,
        "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
        "phase": "owner_receipt_recorded",
        "current_authority": {
            "owner": _text(payload.get("next_owner")) or _text(payload.get("owner")) or "gate_clearing_batch",
            "authority": "med-autoscience",
            "obligation": {
                "study_id": _text(progress.get("study_id")),
                "quest_id": _text(progress.get("quest_id")),
                "owner": _text(payload.get("next_owner")) or _text(payload.get("owner")) or "gate_clearing_batch",
                "action_type": action_type,
                "work_unit_id": work_unit_id,
                "work_unit_fingerprint": work_unit_fingerprint,
                "source": "repair_progress_projection.mas_owner_repair_execution_evidence",
            },
        },
        "next_safe_action": {
            "kind": "consume_owner_receipt",
            "owner": _text(payload.get("next_owner")) or _text(payload.get("owner")) or "gate_clearing_batch",
            "provider_admission_allowed": False,
            "owner_receipt_ref": owner_receipt_ref,
        },
        "evidence_refs": [owner_receipt_ref],
        "owner_receipt_ref": owner_receipt_ref,
        "supervisor_decision": {"decision": "stop_with_owner_receipt"},
        "repair_progress_projection": dict(repair),
        "condition": "repair_progress_owner_receipt_recorded",
    }


def _repair_progress_matches_action(
    *,
    repair: Mapping[str, Any],
    action: Mapping[str, Any],
) -> bool:
    action_type = _action_type(action)
    if action_type is not None and action_type != "run_quality_repair_batch":
        return False
    repair_work_unit = _work_unit_id(repair.get("work_unit_id"))
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if repair_work_unit is None or action_work_unit is None or repair_work_unit != action_work_unit:
        return False
    action_fingerprint = _work_unit_fingerprint(
        action,
        currentness_basis=_mapping(action.get("owner_route_currentness_basis"))
        or _mapping(action.get("currentness_basis")),
    )
    repair_fingerprint = (
        _text(repair.get("work_unit_fingerprint"))
        or _text(repair.get("action_fingerprint"))
        or _text(repair.get("source_fingerprint"))
    )
    if action_fingerprint is None or repair_fingerprint != action_fingerprint:
        return False
    action_eval = _text(action.get("source_eval_id"))
    repair_eval = _text(repair.get("source_eval_id"))
    if action_eval is not None and repair_eval is not None and action_eval != repair_eval:
        return False
    return True


def _repair_progress_gate_replay_receipt_ref(repair: Mapping[str, Any]) -> str | None:
    for ref in _text_items(repair.get("gate_replay_refs")):
        if "gate_clearing_batch" in ref:
            return ref
    return None


def _progress_has_gate_followthrough_actionable_repair(progress: Mapping[str, Any]) -> bool:
    followthrough = _mapping(progress.get("gate_clearing_batch_followthrough"))
    if _text(followthrough.get("status")) != "executed":
        return False
    work_unit_currentness = _mapping(followthrough.get("work_unit_currentness"))
    if _text(work_unit_currentness.get("current_actionability_status")) != "actionable":
        return False
    publication_work_unit = _mapping(followthrough.get("current_publication_work_unit"))
    unit_id = _work_unit_id(publication_work_unit.get("unit_id")) or _work_unit_id(
        followthrough.get("work_unit_id")
    )
    if unit_id in {None, "publication_gate_replay", "complete_medical_paper_readiness_surface"}:
        return False
    return True


def _owner_receipt_consumed_by_actionable_successor(
    *,
    action: Mapping[str, Any] | None,
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    payload = _mapping(action)
    if not payload:
        return False
    if _paper_recovery_owner_action_ready_successor_consumes_receipt(payload, progress=progress):
        return True
    recovery = _mapping(progress.get("paper_recovery_state"))
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    if _same_action_identity(obligation, payload):
        if not _route_back_successor_consumes_prior_owner_receipt(
            action=payload,
            status=status,
            progress=progress,
        ):
            return False
    repair = _mapping(progress.get("repair_progress_projection"))
    if repair and _repair_progress_matches_action(repair=repair, action=payload):
        if not _route_back_successor_consumes_prior_owner_receipt(
            action=payload,
            status=status,
            progress=progress,
        ):
            return False
    if _domain_transition_successor_consumes_owner_receipt(
        action=payload,
        status=status,
        progress=progress,
    ):
        return True
    if _safe_next_forced_delta_action_consumes_repair_progress(
        action=payload,
        progress=progress,
    ):
        return True
    if not _gate_followthrough_actionable_repair_action(payload):
        return False
    if not _progress_has_gate_followthrough_actionable_repair(progress):
        return False
    return _action_supersedes_typed_blocker(
        action=payload,
        blocker={"blocker_type": "publication_gate_replay_blocked"},
        progress=progress,
    )


def _paper_recovery_owner_action_ready_successor_consumes_receipt(
    action: Mapping[str, Any],
    *,
    progress: Mapping[str, Any],
) -> bool:
    if not _paper_recovery_successor_action_ready(action):
        return False
    recovery = _mapping(progress.get("paper_recovery_state"))
    if _text(recovery.get("phase")) != "owner_action_ready":
        return False
    next_action = _mapping(recovery.get("next_safe_action"))
    if _text(next_action.get("kind")) != "materialize_successor_owner_action":
        return False
    successor = _mapping(next_action.get("successor_owner_action"))
    if not successor or not _same_action_identity(successor, action):
        return False
    return _text(successor.get("source_surface")) in {
        "domain_transition",
        "gate_clearing_batch_followthrough.actionable_current_work_unit",
    }


def _paper_recovery_successor_supersedes_terminal_closeout_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if _text(blocker.get("terminal_closeout_consumption_source")) == "provider_admission_terminal_closeout_consumed":
        return False
    if not _paper_recovery_owner_action_ready_successor_consumes_receipt(action, progress=progress):
        return False
    if not _same_action_identity(blocker, action):
        return False
    if _text(blocker.get("terminal_closeout_outcome")) != "blocked:unsupported_dispatch_surface":
        return False
    return (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocked_reason"))
        or _text(blocker.get("blocker_id"))
    ) is not None


def _domain_transition_successor_consumes_owner_receipt(
    *,
    action: Mapping[str, Any],
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    recovery = _mapping(progress.get("paper_recovery_state"))
    next_action = _mapping(recovery.get("next_safe_action"))
    recovery_conditions = {
        _text(_mapping(item).get("condition"))
        for item in recovery.get("conditions") or []
        if isinstance(item, Mapping)
    }
    if not (
        (
            _text(recovery.get("phase")) == "owner_receipt_recorded"
            and _text(next_action.get("kind")) == "consume_owner_receipt"
        )
        or (
            _text(recovery.get("phase")) == "owner_action_ready"
            and _text(next_action.get("kind")) == "materialize_successor_owner_action"
            and bool(
                recovery_conditions
                & {
                    "consumed_owner_receipt_domain_transition_successor",
                    "consumed_owner_receipt_routeback_successor",
                }
            )
        )
    ):
        return False
    transition = _mapping(status.get("domain_transition")) or _mapping(progress.get("domain_transition"))
    if _text(transition.get("decision_type")) != "ai_reviewer_re_eval":
        return _route_back_successor_consumes_prior_owner_receipt(
            action=action,
            status=status,
            progress=progress,
        )
    if _text(transition.get("controller_action")) != "return_to_ai_reviewer_workflow":
        return False
    if _text(transition.get("owner")) not in {None, "ai_reviewer"}:
        return False
    if _action_type(action) != "return_to_ai_reviewer_workflow":
        return False
    if _text(action.get("domain_transition_decision_type")) != "ai_reviewer_re_eval":
        return False
    next_work_unit = _work_unit_id(_mapping(transition.get("next_work_unit")).get("unit_id"))
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(action.get("next_work_unit"))
    if next_work_unit is None or action_work_unit != next_work_unit:
        return False
    expected_fingerprint = f"domain-transition::ai_reviewer_re_eval::{next_work_unit}"
    action_fingerprint = _work_unit_fingerprint(
        action,
        currentness_basis=_mapping(action.get("owner_route_currentness_basis"))
        or _mapping(action.get("currentness_basis")),
    )
    return action_fingerprint == expected_fingerprint


def _route_back_successor_consumes_prior_owner_receipt(
    *,
    action: Mapping[str, Any],
    status: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    transition = _mapping(status.get("domain_transition")) or _mapping(progress.get("domain_transition"))
    if _text(transition.get("decision_type")) != "route_back_same_line":
        return False
    if _text(transition.get("owner")) not in {None, "write", "analysis-campaign", "finalize"}:
        return False
    controller_action = _text(transition.get("controller_action"))
    if controller_action not in {None, "request_opl_stage_attempt"}:
        return False
    completion = _mapping(transition.get("completion_receipt_consumption"))
    if _text(completion.get("status")) not in {"consumed", "receipt_consumed", "completed"}:
        return False
    if _text(completion.get("receipt_kind")) != "ai_reviewer_publication_eval":
        return False
    if _action_type(action) != "run_quality_repair_batch":
        return False
    next_work_unit = _work_unit_id(_mapping(transition.get("next_work_unit")).get("unit_id"))
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    if next_work_unit is None or action_work_unit != next_work_unit:
        return False
    action_owner = _text(action.get("next_owner")) or _text(action.get("owner"))
    transition_owner = _text(transition.get("owner")) or _text(transition.get("route_target"))
    if action_owner is not None and transition_owner is not None and action_owner != transition_owner:
        return False
    return _work_unit_fingerprint(
        action,
        currentness_basis=_mapping(action.get("owner_route_currentness_basis"))
        or _mapping(action.get("currentness_basis")),
    ) is not None


def _action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    payload = _mapping(blocker)
    if not payload:
        return True
    blocker_type = (
        _text(payload.get("blocker_type"))
        or _text(payload.get("blocker_id"))
        or _text(payload.get("blocked_reason"))
        or _text(payload.get("reason"))
    )
    if blocker_type == "opl_execution_authorization_required" and _gate_consumption_action_supersedes_readiness_blocker(action):
        return False
    if gate_replay_action_supersedes_stage_packet_blocker(
        action=action,
        blocker=payload,
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    ):
        return True
    if repair_progress_gate_replay_action_supersedes_gate_replay_blocker(
        action=action,
        blocker=payload,
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    ):
        return True
    if _terminal_routeback_action_supersedes_gate_replay_blocker(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
        gate_replay_work_units=GATE_REPLAY_WORK_UNITS,
    ):
        return True
    if _publication_eval_repair_action_supersedes_gate_replay_blocker(
        action=action,
        blocker=payload,
    ):
        return True
    if _gate_followthrough_supersedes_publication_gate_replay_blocker(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
    ):
        return True
    if _gate_followthrough_supersedes_transport_or_execution_residue(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
    ):
        return True
    if _paper_recovery_successor_supersedes_publication_gate_replay_blocker(
        action=action,
        blocker=payload,
    ):
        return True
    if _action_supersedes_terminal_selector_residue(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
    ):
        return True
    if _paper_recovery_successor_supersedes_terminal_closeout_blocker(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
    ):
        return True
    if _domain_transition_supersedes_provider_completion_blocker(
        action=action,
        blocker=payload,
        progress=_mapping(progress),
    ):
        return True
    if _domain_transition_successor_consumes_owner_receipt(
        action=action,
        status=_mapping(progress),
        progress=_mapping(progress),
    ):
        return True
    if blocker_type in CURRENT_ACTION_SUPERSEDED_RUNTIME_BLOCKERS:
        return (
            _action_is_stage_current_owner_delta(action)
            or _provider_admission_repair_action_supersedes_readiness_blocker(action)
            or _publication_eval_repair_action_supersedes_readiness_blocker(action)
            or _paper_delta_current_action_supersedes_prior_blocker(
                action=action,
                progress=_mapping(progress),
            )
        )
    if blocker_type in CURRENT_ACTION_SUPERSEDED_PRIOR_ACTION_BLOCKERS:
        return (
            _gate_followthrough_actionable_repair_action(action)
            or _publication_eval_repair_action_supersedes_readiness_blocker(action)
            or _paper_delta_current_action_supersedes_prior_blocker(
                action=action,
                progress=_mapping(progress),
            )
        )
    if blocker_type not in MEDICAL_READINESS_BLOCKERS:
        return False
    if _readiness_action_without_current_authority_binding(action):
        return False
    if _text(action.get("action_type")) == "complete_medical_paper_readiness_surface":
        return True
    if "complete_medical_paper_readiness_surface" in _text_items(action.get("allowed_actions")):
        return True
    if _provider_admission_repair_action_supersedes_readiness_blocker(action):
        return True
    if _gate_consumption_action_supersedes_readiness_blocker(action):
        return True
    if _publication_eval_repair_action_supersedes_readiness_blocker(action):
        return True
    return _paper_delta_current_action_supersedes_prior_blocker(
        action=action,
        progress=_mapping(progress),
    )


def _safe_next_forced_delta_action_supersedes_terminal_stop_loss(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    blocker_type = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocked_reason"))
        or _text(blocker.get("reason"))
    )
    if blocker_type not in {
        "anti_loop_budget_exhausted",
        "repeat_suppressed_after_opl_execution_authorization_required",
    }:
        return False
    if _paper_recovery_successor_action_ready(action):
        if not _safe_paper_recovery_successor_consumes_terminal_stop_loss(
            action=action,
            blocker=blocker,
            progress=progress,
        ):
            return False
        return True
    if not _paper_delta_current_action_supersedes_prior_blocker(
        action=action,
        progress=progress,
    ):
        return False
    if not _action_matches_next_forced_delta(action=action, progress=progress):
        return False
    if not _safe_next_forced_delta_action_consumes_repair_progress(
        action=action,
        progress=progress,
    ):
        return False
    blocker_work_unit = _work_unit_id(blocker.get("work_unit_id"))
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    return action_work_unit is not None and action_work_unit == blocker_work_unit


def _current_work_unit_is_terminal_anti_loop_blocker(progress: Mapping[str, Any]) -> bool:
    current = _mapping(progress.get("current_work_unit"))
    if _text(current.get("status")) != "typed_blocker":
        return False
    state = _mapping(current.get("state"))
    blocker = _mapping(state.get("typed_blocker")) or _mapping(current.get("typed_blocker")) or current
    blocker_markers = {
        _text(blocker.get("reason")),
        _text(blocker.get("blocker_id")),
        _text(blocker.get("blocker_kind")),
        _text(blocker.get("blocked_reason")),
        _text(blocker.get("blocker_type")),
    }
    return (
        "anti_loop_budget_exhausted" in blocker_markers
        or "repeat_suppressed_after_opl_execution_authorization_required" in blocker_markers
    )


def _safe_next_forced_delta_action_consumes_repair_progress(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    if _text(action.get("action_type")) != "run_gate_clearing_batch":
        return False
    action_work_unit = _work_unit_id(action.get("work_unit_id")) or _work_unit_id(
        action.get("next_work_unit")
    )
    next_delta = _mapping(progress.get("next_forced_delta"))
    if action_work_unit is None:
        return False
    if action_work_unit != _work_unit_id(next_delta.get("work_unit_id")):
        return False
    if _text(next_delta.get("required_delta_kind")) != "review_current_paper_delta":
        return False
    if _text(next_delta.get("reason")) != "paper_progress_delta_observed":
        return False
    repair = _mapping(progress.get("repair_progress_projection"))
    if _text(repair.get("source")) != "mas_owner_repair_execution_evidence":
        return False
    return _repair_progress_proves_safe_successor_delta(repair)


def action_supersedes_typed_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any] | None,
    progress: Mapping[str, Any] | None = None,
) -> bool:
    return _action_supersedes_typed_blocker(
        action=action,
        blocker=blocker,
        progress=progress,
    )


def _readiness_action_without_current_authority_binding(action: Mapping[str, Any]) -> bool:
    action_types = {_text(action.get("action_type")), *_text_items(action.get("allowed_actions"))}
    if "complete_medical_paper_readiness_surface" not in action_types:
        return False
    source = _text(action.get("source_surface")) or _text(action.get("source"))
    if source == "stage_kernel_projection.current_owner_delta":
        return False
    if source == "study_progress.next_forced_delta.owner_action":
        return _mapping(action.get("terminal_closeout_dispatch")) == {}
    if _text(action.get("authority")) in PROVIDER_ADMISSION_AUTHORITIES:
        return False
    return True


def _action_is_stage_current_owner_delta(action: Mapping[str, Any]) -> bool:
    return (
        _text(action.get("source_surface"))
        or _text(action.get("source"))
    ) == "stage_kernel_projection.current_owner_delta"


def _paper_delta_current_action_supersedes_prior_blocker(
    *,
    action: Mapping[str, Any],
    progress: Mapping[str, Any],
) -> bool:
    progress_first = _mapping(progress.get("progress_first_sprint_state"))
    paper_delta = _mapping(progress.get("paper_progress_delta"))
    if progress_first.get("paper_progress_delta_counted") is not True and _delta_count(paper_delta) <= 0:
        return False
    action_source = _text(action.get("source_surface")) or _text(action.get("source"))
    if _text(action.get("action_type")) not in {
        "request_opl_stage_attempt",
        "return_to_ai_reviewer_workflow",
        "run_gate_clearing_batch",
        "run_quality_repair_batch",
    }:
        return False
    if _text(action.get("work_unit_id")) == "complete_medical_paper_readiness_surface":
        return False
    if action_source == "study_progress.next_forced_delta.owner_action":
        if _mapping(_mapping(progress.get("next_forced_delta")).get("owner_action")):
            return _action_matches_next_forced_delta(action=action, progress=progress)
        return True
    if action_source in PAPER_DELTA_PRIOR_BLOCKER_SUPERSEDING_ACTION_SOURCES:
        return True
    if action_source == OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE:
        return _action_matches_next_forced_delta(action=action, progress=progress)
    return False


def _provider_admission_repair_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_type = _text(action.get("action_type"))
    action_types = {action_type, *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection(PROVIDER_ADMISSION_REPAIR_ACTIONS):
        return False
    if _text(action.get("work_unit_id")) == "complete_medical_paper_readiness_surface":
        return False
    if _text(action.get("next_work_unit")) == "complete_medical_paper_readiness_surface":
        return False
    if _mapping(action.get("repair_progress_followup")).get("accepted_owner_receipt") is True:
        return True
    authority = _text(action.get("authority"))
    if authority in PROVIDER_ADMISSION_AUTHORITIES:
        return True
    if _mapping(action.get("repair_progress_precedence")).get("accepted_owner_receipt") is True:
        return True
    if _gate_followthrough_actionable_repair_action(action):
        return True
    action_id = _text(action.get("action_id"))
    if action_id is not None and action_id.startswith("provider-admission::"):
        return True
    for key in ("action_fingerprint", "work_unit_fingerprint", "fingerprint"):
        text = _text(action.get(key))
        if text is not None and text.startswith("study-progress-current-owner-ticket::"):
            return True
    return False


def _publication_eval_repair_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    if (_text(action.get("source_surface")) or _text(action.get("source"))) != PUBLICATION_EVAL_READINESS_REPAIR_SOURCE:
        return False
    action_type = _text(action.get("action_type"))
    action_types = {action_type, *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection({"run_quality_repair_batch", "run_gate_clearing_batch"}):
        return False
    if _text(action.get("work_unit_id")) in {None, "complete_medical_paper_readiness_surface"}:
        return False
    if "run_gate_clearing_batch" in action_types:
        target = _mapping(action.get("target_surface"))
        if _text(target.get("route_target")) != "finalize":
            return False
        if _text(target.get("surface_ref")) != "artifacts/controller/gate_clearing_batch/latest.json":
            return False
    return bool(_mapping(action.get("target_surface")).get("next_work_unit"))


def _publication_eval_repair_action_supersedes_gate_replay_blocker(
    *,
    action: Mapping[str, Any],
    blocker: Mapping[str, Any],
) -> bool:
    blocker_reason = (
        _text(blocker.get("blocker_type"))
        or _text(blocker.get("blocked_reason"))
        or _text(blocker.get("blocker_id"))
    )
    if blocker_reason != "publication_gate_replay_blocked":
        return False
    blocker_action_type = _text(blocker.get("action_type"))
    if blocker_action_type not in {None, "run_gate_clearing_batch"}:
        return False
    blocker_work_unit = _text(blocker.get("work_unit_id"))
    if blocker_work_unit not in {None, *GATE_REPLAY_WORK_UNITS}:
        return False
    if not _publication_eval_repair_action_supersedes_readiness_blocker(action):
        return False
    if _text(action.get("next_owner")) not in {"write", "analysis-campaign"}:
        return False
    action_work_unit = _text(action.get("work_unit_id"))
    if action_work_unit in {None, *GATE_REPLAY_WORK_UNITS}:
        return False
    return _text(action.get("action_type")) == "run_quality_repair_batch"


def _gate_consumption_action_supersedes_readiness_blocker(action: Mapping[str, Any]) -> bool:
    action_types = {_text(action.get("action_type")), *_text_items(action.get("allowed_actions"))}
    if not action_types.intersection({"request_opl_stage_attempt", "run_gate_clearing_batch", "run_quality_repair_batch"}):
        return False
    work_unit = _text(action.get("work_unit_id")) or _text(action.get("next_work_unit"))
    if work_unit not in GATE_REPLAY_WORK_UNITS:
        return False
    target = _mapping(action.get("target_surface"))
    return _text(target.get("surface_ref")) == "artifacts/controller/gate_clearing_batch/latest.json"


__all__ = [
    "ALLOWED_STATUSES",
    "SURFACE_KIND",
    "action_supersedes_typed_blocker",
    "build_current_work_unit",
]
