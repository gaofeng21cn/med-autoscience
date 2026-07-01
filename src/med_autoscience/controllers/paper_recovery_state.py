from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_execution_boundary import (
    OPL_EXECUTION_AUTHORIZATION_BLOCKER,
    OPL_EXECUTION_AUTHORIZATION_OWNER,
    OPL_EXECUTION_AUTHORIZATION_REQUIRED_INPUT,
)
from med_autoscience.controllers.paper_autonomy_supervisor import (
    build_supervisor_decision as _build_supervisor_decision,
)
from med_autoscience.controllers.paper_recovery_state_parts.obligation_matching import (
    action_matches_obligation as _current_action_matches_obligation,
)
from med_autoscience.controllers.paper_recovery_state_parts.obligation_projection import (
    obligation as _obligation,
)
from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    supervisor_decision_for_projection as _supervisor_decision_for_projection,
)
from med_autoscience.controllers.opl_transition_readback import (
    opl_transition_readback_source_claimability as _opl_transition_readback_source_claimability,
)
from med_autoscience.controllers.paper_recovery_state_parts.owner_gate_decision import (
    accepted_owner_gate_decision as _accepted_owner_gate_decision,
    matching_owner_gate_decision_event as _matching_owner_gate_decision_event,
    owner_gate_decision_matches_obligation as _owner_gate_decision_matches_obligation,
    owner_gate_decision_refs as _owner_gate_decision_refs,
)
from med_autoscience.controllers.paper_recovery_state_parts.owner_receipt_progress import (
    owner_receipt_recorded_current_work_unit as _owner_receipt_recorded_current_work_unit,
    repair_progress_owner_receipt_superseding_terminal_stop_loss as _repair_progress_owner_receipt_superseding_terminal_stop_loss,
    same_work_unit_owner_receipt as _same_work_unit_owner_receipt,
    successor_owner_action_from_consumed_owner_receipt as _successor_owner_action_from_consumed_owner_receipt,
)
from med_autoscience.controllers.paper_recovery_state_parts.provider_admission_state import (
    admission_blocked_condition as _admission_blocked_condition,
    provider_admission_pending as _provider_admission_pending,
    transition_request_pending as _transition_request_pending,
)
from med_autoscience.controllers.paper_recovery_state_parts.state_diagnostics import (
    clean_conditions as _clean_conditions,
    current_work_unit_status as _current_work_unit_status,
    first_text as _first_text,
    has_running_provider_attempt as _has_running_provider_attempt,
    mapping as _mapping,
    provider_admission_readback as _provider_admission_readback,
    runtime_recovery_blocking_reason as _runtime_recovery_blocking_reason,
    study_id as _study_id,
    text as _text,
    text_items as _text_items,
)
from med_autoscience.controllers.paper_recovery_state_parts.owner_callable_readiness import (
    current_mas_owner_callable as _current_mas_owner_callable,
)
from med_autoscience.controllers.paper_recovery_state_parts.successor_owner_resolution import (
    current_executable_owner_action as _current_executable_owner_action,
    current_owner_successor_action as _current_owner_successor_action,
    paper_recovery_successor_action_ready as _paper_recovery_successor_action_ready,
    successor_owner_action_from_current_action as _successor_owner_action_from_current_action,
    successor_owner_action_from_terminal_blocker as _successor_owner_action_from_terminal_blocker,
    successor_owner_gate_from_terminal_blocker as _successor_owner_gate_from_terminal_blocker,
)
from med_autoscience.controllers.paper_recovery_state_parts.terminal_closeout_projection import (
    closeout_refs as _closeout_refs,
    matching_provider_admission_terminal_closeout_consumed as _matching_provider_admission_terminal_closeout_consumed,
    matching_terminal_closeout as _matching_terminal_closeout,
    projection_contradiction as _projection_contradiction,
    suppressed_surfaces_for_owner_gate_decision as _suppressed_surfaces_for_owner_gate_decision,
    suppressed_surfaces_for_typed_blocker as _suppressed_surfaces_for_typed_blocker,
)
from med_autoscience.controllers.paper_recovery_state_parts.typed_blocker_payload import (
    current_typed_blocker as _current_typed_blocker,
    typed_blocker_from_closeout as _typed_blocker_from_closeout,
    typed_blocker_has_stable_outcome_ref as _typed_blocker_has_stable_outcome_ref,
    typed_blocker_reason as _typed_blocker_reason,
)
from med_autoscience.controllers.paper_recovery_state_parts.typed_blocker_recovery import (
    typed_blocker_next_action as _typed_blocker_next_action,
    typed_blocker_phase as _typed_blocker_phase,
    typed_blocker_recovery_owner as _typed_blocker_recovery_owner,
)
from med_autoscience.controllers.paper_recovery_state_parts.typed_blocker_supersession import (
    current_action_supersedes_typed_blocker as _current_action_supersedes_typed_blocker,
)


SURFACE_KIND = "paper_recovery_state"
SCHEMA_VERSION = 1
AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_paper_recovery_state_reducer",
    "top_level_truth": "phase",
    "source_of_truth": "MAS current owner obligation and owner receipt or typed blocker",
    "derived_surfaces": [
        "current_work_unit",
        "current_execution_envelope",
        "provider_admission_candidates",
        "operator_status_card",
    ],
    "opl_authority": "generic_obligation_execution_substrate_only",
    "opl_can_issue_mas_owner_receipt": False,
    "opl_can_authorize_publication_ready": False,
    "provider_completion_is_domain_completion": False,
    "manual_foreground_file_edit_is_domain_completion": False,
}


def build_paper_recovery_state(
    payload: Mapping[str, Any],
    *,
    diagnostic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    progress = _mapping(payload)
    diagnostic = _mapping(diagnostic_report)
    current_work_unit = _mapping(progress.get("current_work_unit"))
    obligation = _obligation(progress, current_work_unit=current_work_unit)
    current_action = _current_executable_owner_action(progress)

    owner_gate_event = _matching_owner_gate_decision_event(progress, obligation=obligation)
    if owner_gate_event is not None:
        owner_gate_payload = _mapping(owner_gate_event.get("payload"))
        if _owner_gate_decision_matches_obligation(owner_gate_payload, obligation=obligation):
            owner_receipt = _same_work_unit_owner_receipt(
                progress,
                current_work_unit=current_work_unit,
                current_action=current_action,
                obligation=obligation,
            )
            if owner_receipt is not None:
                owner_receipt_state = _owner_receipt_state(
                    progress,
                    obligation=obligation,
                    owner_receipt=owner_receipt,
                    diagnostic_report=diagnostic,
                )
                if owner_receipt_state is not None:
                    return owner_receipt_state
        decision = _text(owner_gate_payload.get("decision"))
        phase = "human_gate"
        next_action_kind = "resolve_owner_gate_decision"
        current_owner = "MedAutoScience"
        provider_admission_allowed = False
        accepted_owner_gate_decision: dict[str, Any] | None = None
        if decision == "route_back_to_mas_packet_materialization_bug":
            phase = "owner_action_ready"
            next_action_kind = "route_back_to_owner_or_repair_materialization"
            provider_admission_allowed = False
            accepted_owner_gate_decision = _accepted_owner_gate_decision(owner_gate_payload)
        elif decision == "wait_for_owner_with_resume_token":
            accepted_owner_gate_decision = _accepted_owner_gate_decision(owner_gate_payload)
        elif decision == "admit_identity_bound_stage_packet":
            phase = "admission_pending"
            next_action_kind = "admit_identity_bound_stage_packet"
            current_owner = _text(obligation.get("owner")) or current_owner
            provider_admission_allowed = True
        elif decision == "deny_and_stable_typed_blocker":
            phase = "domain_blocked"
            next_action_kind = "honor_stable_typed_blocker"
            accepted_owner_gate_decision = _accepted_owner_gate_decision(owner_gate_payload)
        return _state(
            progress,
            obligation=obligation,
            phase=phase,
            conditions=[
                {
                    "condition": "accepted_owner_gate_decision",
                    "decision": decision,
                }
            ],
            next_safe_action=_next_action(
                next_action_kind,
                provider_admission_allowed=provider_admission_allowed,
                owner=current_owner,
                accepted_owner_gate_decision=accepted_owner_gate_decision,
            ),
            current_owner=current_owner,
            suppressed_surfaces=_suppressed_surfaces_for_owner_gate_decision(progress),
            evidence_refs=_owner_gate_decision_refs(owner_gate_payload),
            diagnostic_report=diagnostic,
        )

    typed_blocker = _current_typed_blocker(current_work_unit)
    consumed_terminal_closeout = _matching_provider_admission_terminal_closeout_consumed(
        progress,
        obligation=obligation,
    )
    if consumed_terminal_closeout is not None:
        owner_receipt = _repair_progress_owner_receipt_superseding_terminal_stop_loss(
            progress,
            closeout=consumed_terminal_closeout,
        )
        if owner_receipt is not None:
            owner_receipt_state = _owner_receipt_state(
                progress,
                obligation=obligation,
                owner_receipt=owner_receipt,
                diagnostic_report=diagnostic,
            )
            if owner_receipt_state is not None:
                return owner_receipt_state
        closeout_typed_blocker = _typed_blocker_from_closeout(
            consumed_terminal_closeout,
            obligation=obligation,
        )
        if closeout_typed_blocker:
            blocker_reason = _typed_blocker_reason(closeout_typed_blocker)
            owner = _typed_blocker_recovery_owner(
                closeout_typed_blocker,
                current_work_unit=current_work_unit,
                obligation=obligation,
                blocker_reason=blocker_reason,
            )
            return _state(
                progress,
                obligation=obligation,
                phase=_typed_blocker_phase(closeout_typed_blocker),
                conditions=[
                    {
                        "condition": "accepted_closeout_typed_blocker",
                        "blocker_type": blocker_reason,
                    }
                ],
                next_safe_action=_typed_blocker_next_action(
                    closeout_typed_blocker,
                    blocker_reason=blocker_reason,
                    owner=owner,
                ),
                current_owner=owner,
                evidence_refs=_closeout_refs(consumed_terminal_closeout),
                diagnostic_report=diagnostic,
            )
    owner_receipt = _owner_receipt_recorded_current_work_unit(
        current_work_unit,
        obligation=obligation,
    ) or _same_work_unit_owner_receipt(
        progress,
        current_work_unit=current_work_unit,
        current_action=current_action,
        obligation=obligation,
    )
    if owner_receipt is not None:
        owner_receipt_state = _owner_receipt_state(
            progress,
            obligation=obligation,
            owner_receipt=owner_receipt,
            diagnostic_report=diagnostic,
        )
        if owner_receipt_state is not None:
            return owner_receipt_state
    typed_blocker_superseded_by_current_action = bool(
        typed_blocker
        and current_action
        and _current_action_supersedes_typed_blocker(
            action=current_action,
            blocker=typed_blocker,
            progress=progress,
        )
    )
    if (
        typed_blocker
        and typed_blocker_superseded_by_current_action
        and _paper_recovery_successor_action_ready(current_action)
    ):
        blocker_reason = _typed_blocker_reason(typed_blocker)
        successor_action = _successor_owner_action_from_current_action(current_action)
        successor_owner = _text(successor_action.get("owner")) or _text(
            successor_action.get("next_owner")
        )
        return _state(
            progress,
            obligation=obligation,
            phase="owner_action_ready",
            conditions=[
                {
                    "condition": "current_owner_action_supersedes_typed_blocker",
                    "blocker_type": blocker_reason,
                }
            ],
            next_safe_action=_next_action(
                "materialize_successor_owner_action",
                provider_admission_allowed=True,
                owner=successor_owner,
                successor_owner_action=successor_action,
            ),
            current_owner=successor_owner,
            suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
            diagnostic_report=diagnostic,
        )
    if typed_blocker and not typed_blocker_superseded_by_current_action:
        blocker_reason = _typed_blocker_reason(typed_blocker)
        owner_receipt = _repair_progress_owner_receipt_superseding_terminal_stop_loss(
            progress,
            closeout=typed_blocker,
        )
        if owner_receipt is not None:
            owner_receipt_state = _owner_receipt_state(
                progress,
                obligation=obligation,
                owner_receipt=owner_receipt,
                diagnostic_report=diagnostic,
            )
            if owner_receipt_state is not None:
                return owner_receipt_state
        owner = _typed_blocker_recovery_owner(
            typed_blocker,
            current_work_unit=current_work_unit,
            blocker_reason=blocker_reason,
        )
        successor_action = _successor_owner_action_from_terminal_blocker(
            progress,
            typed_blocker=typed_blocker,
            blocker_reason=blocker_reason,
        )
        if successor_action is not None:
            successor_owner = _text(successor_action.get("owner")) or _text(
                successor_action.get("next_owner")
            )
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "terminal_typed_blocker_successor_evidence",
                        "blocker_type": blocker_reason,
                    }
                ],
                next_safe_action=_next_action(
                    "materialize_successor_owner_action",
                    provider_admission_allowed=True,
                    owner=successor_owner,
                    successor_owner_action=successor_action,
                ),
                current_owner=successor_owner,
                suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
                diagnostic_report=diagnostic,
            )
        owner_callable = _current_mas_owner_callable(progress, obligation=obligation)
        if owner_callable is not None:
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "current_mas_owner_callable_ready",
                        "reason": blocker_reason,
                    }
                ],
                next_safe_action=_next_action(
                    "run_mas_owner_callable",
                    provider_admission_allowed=False,
                    owner=owner,
                    owner_callable=owner_callable,
                ),
                current_owner=owner,
                diagnostic_report=diagnostic,
            )
        owner_gate = None
        if not _typed_blocker_has_stable_outcome_ref(typed_blocker):
            owner_gate = _successor_owner_gate_from_terminal_blocker(
                progress,
                typed_blocker=typed_blocker,
                blocker_reason=blocker_reason,
                owner=owner,
            )
        if owner_gate is not None:
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "terminal_typed_blocker_owner_gate_required",
                        "blocker_type": blocker_reason,
                    }
                ],
                next_safe_action=_next_action(
                    "materialize_successor_owner_gate",
                    provider_admission_allowed=False,
                    owner=owner,
                    required_input=_text(owner_gate.get("required_input")),
                    successor_owner_gate=owner_gate,
                ),
                current_owner=owner,
                suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
                evidence_refs=_text_items(owner_gate.get("evidence_refs")),
                diagnostic_report=diagnostic,
            )
        if current_action and _current_action_supersedes_typed_blocker(
            action=current_action,
            blocker=typed_blocker,
            progress=progress,
        ):
            successor_action = _successor_owner_action_from_current_action(current_action)
            successor_owner = _text(successor_action.get("owner")) or _text(
                successor_action.get("next_owner")
            )
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "current_owner_action_supersedes_terminal_typed_blocker",
                        "blocker_type": blocker_reason,
                    }
                ],
                next_safe_action=_next_action(
                    "materialize_successor_owner_action",
                    provider_admission_allowed=True,
                    owner=successor_owner,
                    successor_owner_action=successor_action,
                ),
                current_owner=successor_owner,
                suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
                diagnostic_report=diagnostic,
            )
        owner_callable = _current_mas_owner_callable(progress, obligation=obligation)
        if owner_callable is not None:
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "current_mas_owner_callable_ready",
                        "reason": blocker_reason,
                    }
                ],
                next_safe_action=_next_action(
                    "run_mas_owner_callable",
                    provider_admission_allowed=False,
                    owner=owner,
                    owner_callable=owner_callable,
                ),
                current_owner=owner,
                diagnostic_report=diagnostic,
            )
        return _state(
            progress,
            obligation=obligation,
            phase=_typed_blocker_phase(typed_blocker),
            conditions=[
                {
                    "condition": "current_work_unit_typed_blocker",
                    "blocker_type": blocker_reason,
                }
            ],
            next_safe_action=_typed_blocker_next_action(
                typed_blocker,
                blocker_reason=blocker_reason,
                owner=owner,
            ),
            current_owner=owner,
            suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
            diagnostic_report=diagnostic,
        )

    contradiction = _projection_contradiction(progress, obligation=obligation)
    if contradiction is not None:
        return _state(
            progress,
            obligation=obligation,
            phase="projection_inconsistent",
            conditions=[contradiction],
            next_safe_action=_next_action(
                "repair_projection_before_admission",
                provider_admission_allowed=False,
                owner="MedAutoScience",
            ),
            current_owner="MedAutoScience",
            diagnostic_report=diagnostic,
        )

    terminal_closeout = _matching_terminal_closeout(progress, obligation=obligation)
    if terminal_closeout is not None:
        closeout_typed_blocker = _typed_blocker_from_closeout(terminal_closeout, obligation=obligation)
        if closeout_typed_blocker:
            blocker_reason = _typed_blocker_reason(closeout_typed_blocker)
            owner = _typed_blocker_recovery_owner(
                closeout_typed_blocker,
                current_work_unit=current_work_unit,
                obligation=obligation,
                blocker_reason=blocker_reason,
            )
            return _state(
                progress,
                obligation=obligation,
                phase=_typed_blocker_phase(closeout_typed_blocker),
                conditions=[
                    {
                        "condition": "accepted_closeout_typed_blocker",
                        "blocker_type": blocker_reason,
                    }
                ],
                next_safe_action=_typed_blocker_next_action(
                    closeout_typed_blocker,
                    blocker_reason=blocker_reason,
                    owner=owner,
                ),
                current_owner=owner,
                evidence_refs=_closeout_refs(terminal_closeout),
                diagnostic_report=diagnostic,
            )
        return _state(
            progress,
            obligation=obligation,
            phase="terminal_closeout_ready",
            conditions=[
                {
                    "condition": "terminal_closeout_matches_recovery_obligation",
                    "stage_attempt_id": _text(terminal_closeout.get("stage_attempt_id")),
                }
            ],
            next_safe_action=_next_action(
                "consume_terminal_closeout",
                provider_admission_allowed=False,
                owner="MedAutoScience",
            ),
            evidence_refs=_closeout_refs(terminal_closeout),
            diagnostic_report=diagnostic,
        )

    manual_delta = _mapping(progress.get("manual_foreground_delta"))
    if manual_delta.get("changed") is True and _text(manual_delta.get("owner_receipt_ref")) is None:
        return _state(
            progress,
            obligation=obligation,
            phase="manual_foreground_unadopted",
            conditions=[
                {
                    "condition": "foreground_delta_missing_mas_owner_receipt",
                    "path_count": len(_text_items(manual_delta.get("paths"))),
                }
            ],
            next_safe_action=_next_action(
                "adopt_manual_delta_through_mas_owner_receipt",
                provider_admission_allowed=False,
                owner="MedAutoScience",
            ),
            current_owner="MedAutoScience",
            diagnostic_report=diagnostic,
        )

    if _has_running_provider_attempt(progress, current_work_unit=current_work_unit):
        owner = _text(current_work_unit.get("owner")) or _text(obligation.get("owner"))
        return _state(
            progress,
            obligation=obligation,
            phase="attempt_running",
            conditions=[{"condition": "running_attempt_identity_bound"}],
            next_safe_action=_next_action(
                "watch_running_attempt",
                provider_admission_allowed=False,
                owner=owner,
            ),
            current_owner=owner,
            diagnostic_report=diagnostic,
        )

    successor_action = _current_owner_successor_action(progress, current_action=current_action)
    if successor_action is not None:
        successor_owner = _text(successor_action.get("owner")) or _text(
            successor_action.get("next_owner")
        )
        return _state(
            progress,
            obligation=obligation,
            phase="owner_action_ready",
            conditions=[{"condition": "current_owner_action_successor_materialization"}],
            next_safe_action=_next_action(
                "materialize_successor_owner_action",
                provider_admission_allowed=True,
                owner=successor_owner,
                successor_owner_action=successor_action,
            ),
            current_owner=successor_owner,
            diagnostic_report=diagnostic,
        )

    admission_blocked = _admission_blocked_condition(progress, diagnostic)
    if admission_blocked is not None:
        owner = _text(obligation.get("owner"))
        owner_callable = _current_mas_owner_callable(progress, obligation=obligation)
        if owner_callable is not None:
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "current_mas_owner_callable_ready",
                        "reason": _text(admission_blocked.get("reason")),
                    }
                ],
                next_safe_action=_next_action(
                    "run_mas_owner_callable",
                    provider_admission_allowed=False,
                    owner=owner,
                    owner_callable=owner_callable,
                ),
                current_owner=owner,
                diagnostic_report=diagnostic,
            )
        return _state(
            progress,
            obligation=obligation,
            phase="admission_blocked",
            conditions=[admission_blocked],
            next_safe_action=_next_action(
                "authorize_opl_transport_recovery_or_stable_typed_blocker",
                provider_admission_allowed=False,
                owner=owner,
                required_input="OPL transport recovery authorization, current identity-bound provider start, or stable typed blocker",
            ),
            current_owner=owner,
            diagnostic_report=diagnostic,
        )

    if _provider_admission_pending(progress):
        owner = _text(obligation.get("owner"))
        admission_readback = _provider_admission_readback(progress)
        readback_claimability = _opl_transition_readback_source_claimability(admission_readback)
        return _state(
            progress,
            obligation=obligation,
            phase="admission_pending",
            conditions=[
                {
                    "condition": "opl_provider_admission_readback_consumable",
                    "source_kind": readback_claimability.get("source_kind"),
                    "fresh_live_claim_allowed": readback_claimability.get(
                        "fresh_live_claim_allowed"
                    ),
                }
            ],
            next_safe_action=_next_action(
                "consume_opl_provider_admission_readback",
                provider_admission_allowed=True,
                mas_can_authorize_provider_admission=False,
                provider_admission_requires_opl_runtime_result=True,
                requires_claimable_live_readback_source=True,
                fresh_live_claim_allowed=readback_claimability.get("fresh_live_claim_allowed"),
                owner=owner,
                required_input=(
                    "Complete same-transition OPL provider-admission runtime readback; "
                    "MAS consumes the projection and cannot authorize or start provider attempts"
                ),
            ),
            current_owner=owner,
            diagnostic_report=diagnostic,
        )

    if _transition_request_pending(progress):
        owner = _text(obligation.get("owner"))
        return _state(
            progress,
            obligation=obligation,
            phase="transition_request_pending",
            conditions=[
                {
                    "condition": "mas_transition_request_pending_opl_readback",
                    "required_runtime": "DomainProgressTransitionRuntime",
                }
            ],
            next_safe_action=_next_action(
                "await_opl_transition_readback_or_non_advancing_apply",
                provider_admission_allowed=False,
                provider_admission_requires_opl_runtime_result=True,
                owner=owner,
                required_input="OPL command/event/outbox or StageRun readback for the same transition request",
            ),
            current_owner=owner,
            diagnostic_report=diagnostic,
        )

    if (
        typed_blocker_superseded_by_current_action
        and current_action
        and not _current_action_matches_obligation(current_action, obligation=obligation)
    ):
        successor_action = _successor_owner_action_from_current_action(current_action)
        successor_owner = _text(successor_action.get("owner")) or _text(
            successor_action.get("next_owner")
        )
        return _state(
            progress,
            obligation=obligation,
            phase="owner_action_ready",
            conditions=[
                {
                    "condition": "current_owner_action_supersedes_terminal_typed_blocker",
                    "blocker_type": _typed_blocker_reason(typed_blocker),
                }
            ],
            next_safe_action=_next_action(
                "materialize_successor_owner_action",
                provider_admission_allowed=True,
                owner=successor_owner,
                successor_owner_action=successor_action,
            ),
            current_owner=successor_owner,
            suppressed_surfaces=_suppressed_surfaces_for_typed_blocker(progress),
            diagnostic_report=diagnostic,
        )

    if _current_work_unit_status(current_work_unit) == "executable_owner_action" or (
        typed_blocker_superseded_by_current_action
        and _current_action_matches_obligation(current_action, obligation=obligation)
    ):
        owner = _text(obligation.get("owner"))
        owner_callable = _current_mas_owner_callable(progress, obligation=obligation)
        if owner_callable is not None:
            return _state(
                progress,
                obligation=obligation,
                phase="owner_action_ready",
                conditions=[
                    {
                        "condition": "current_mas_owner_callable_ready",
                        "reason": _runtime_recovery_blocking_reason(progress),
                    }
                ],
                next_safe_action=_next_action(
                    "run_mas_owner_callable",
                    provider_admission_allowed=False,
                    owner=owner,
                    owner_callable=owner_callable,
                ),
                current_owner=owner,
                diagnostic_report=diagnostic,
            )
        return _state(
            progress,
            obligation=obligation,
            phase="owner_action_ready",
            conditions=[{"condition": "current_owner_action_ready"}],
            next_safe_action=_next_action(
                "materialize_mas_transition_request_or_owner_callable",
                provider_admission_allowed=True,
                owner=owner,
            ),
            current_owner=owner,
            diagnostic_report=diagnostic,
        )

    return _state(
        progress,
        obligation=obligation,
        phase="human_gate",
        conditions=[{"condition": "no_current_machine_executable_recovery_obligation"}],
        next_safe_action=_next_action(
            "record_human_or_owner_gate",
            provider_admission_allowed=False,
            owner="MedAutoScience",
        ),
        current_owner="MedAutoScience",
        diagnostic_report=diagnostic,
    )


def _state(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
    phase: str,
    conditions: list[dict[str, Any]],
    next_safe_action: Mapping[str, Any],
    current_owner: str | None = None,
    suppressed_surfaces: list[str] | None = None,
    evidence_refs: list[str] | None = None,
    diagnostic_report: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    owner = current_owner or _text(obligation.get("owner")) or "MedAutoScience"
    payload = {
        "surface_kind": SURFACE_KIND,
        "schema_version": SCHEMA_VERSION,
        "study_id": _study_id(progress),
        "quest_id": _text(progress.get("quest_id")),
        "recovery_obligation_id": _text(obligation.get("recovery_obligation_id")),
        "phase": phase,
        "current_authority": {
            "owner": owner,
            "authority": "med-autoscience" if owner != "one-person-lab" else "one-person-lab",
            "obligation": dict(obligation),
        },
        "conditions": _clean_conditions(conditions),
        "next_safe_action": dict(next_safe_action),
        "suppressed_surfaces": list(suppressed_surfaces or []),
        "evidence_refs": list(evidence_refs or []),
        "authority_boundary": dict(AUTHORITY_BOUNDARY),
    }
    cleaned = {key: value for key, value in payload.items() if value not in (None, "", [], {})}
    cleaned["supervisor_decision"] = _supervisor_decision_for_state(
        progress,
        paper_recovery_state=cleaned,
        diagnostic_report=diagnostic_report,
    )
    return cleaned


def _supervisor_decision_for_state(
    progress: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any],
    diagnostic_report: Mapping[str, Any] | None,
) -> dict[str, Any]:
    if _mas_policy_projection_can_supersede_stale_supervisor_decision(
        progress,
        paper_recovery_state=paper_recovery_state,
    ):
        return _build_supervisor_decision(
            progress,
            paper_recovery_state=paper_recovery_state,
            diagnostic_report=diagnostic_report,
        )
    projection = _supervisor_decision_for_projection(
        progress,
        paper_recovery_state=paper_recovery_state,
        diagnostic_report=diagnostic_report,
    )
    if _text(projection.get("decision")) == "stop_with_stable_typed_blocker" and projection.get(
        "opl_supervisor_decision_engine_readback_consumed"
    ) is True:
        return _supervisor_decision_for_projection(
            {
                **progress,
                "paper_autonomy_supervisor_decision": {
                    "decision": "opl_supervisor_decision_readback_required",
                    "requires_opl_supervisor_decision_engine_readback": True,
                },
            },
            paper_recovery_state=paper_recovery_state,
            diagnostic_report=diagnostic_report,
            materialize_recovery_action=True,
        )
    return projection


def _mas_policy_projection_can_supersede_stale_supervisor_decision(
    progress: Mapping[str, Any],
    *,
    paper_recovery_state: Mapping[str, Any],
) -> bool:
    phase = _text(paper_recovery_state.get("phase"))
    if phase in {"owner_receipt_recorded", "terminal_closeout_ready"}:
        return True
    next_action_kind = _text(_mapping(paper_recovery_state.get("next_safe_action")).get("kind"))
    if phase != "owner_action_ready":
        return False
    if next_action_kind == "run_mas_owner_callable":
        return True
    current_action = _current_executable_owner_action(progress)
    if (
        next_action_kind == "materialize_mas_transition_request_or_owner_callable"
        and _text(current_action.get("source_surface"))
        == "gate_clearing_batch_followthrough.actionable_current_work_unit"
        and _text(current_action.get("source"))
        == "paper_recovery_state.next_safe_action.successor_owner_action"
    ):
        return True
    if next_action_kind != "materialize_successor_owner_action":
        return False
    conditions = _paper_recovery_condition_names(paper_recovery_state)
    if "current_owner_action_supersedes_typed_blocker" in conditions:
        return False
    successor = _mapping(_mapping(paper_recovery_state.get("next_safe_action")).get("successor_owner_action"))
    if _text(successor.get("source_surface")) == (
        "gate_clearing_batch_followthrough.actionable_current_work_unit"
    ):
        return True
    return bool(
        conditions
        & {
            "terminal_typed_blocker_successor_evidence",
            "current_owner_action_supersedes_terminal_typed_blocker",
            "consumed_owner_receipt_routeback_successor",
        }
    )


def _paper_recovery_condition_names(paper_recovery_state: Mapping[str, Any]) -> set[str]:
    return {
        condition_name
        for condition in paper_recovery_state.get("conditions") or []
        if isinstance(condition, Mapping)
        if (condition_name := _text(condition.get("condition"))) is not None
    }


def _owner_receipt_state(
    progress: Mapping[str, Any],
    *,
    obligation: Mapping[str, Any],
    owner_receipt: Mapping[str, Any],
    diagnostic_report: Mapping[str, Any],
) -> dict[str, Any] | None:
    successor_action = _successor_owner_action_from_consumed_owner_receipt(
        progress,
        owner_receipt=owner_receipt,
    )
    source_condition = _text(owner_receipt.get("condition")) or "same_work_unit_owner_receipt_recorded"
    condition = "consumed_owner_receipt_routeback_successor"
    if successor_action is not None:
        successor_owner = _text(successor_action.get("owner")) or _text(
            successor_action.get("next_owner")
        )
        return _state(
            progress,
            obligation=obligation,
            phase="owner_action_ready",
            conditions=[
                {
                    "condition": condition,
                    "source_condition": source_condition,
                }
            ],
            next_safe_action=_next_action(
                "materialize_successor_owner_action",
                provider_admission_allowed=True,
                owner=successor_owner,
                successor_owner_action=successor_action,
            ),
            current_owner=successor_owner,
            diagnostic_report=diagnostic_report,
        )
    owner = _text(obligation.get("owner"))
    owner_receipt_ref = _text(owner_receipt.get("owner_receipt_ref"))
    return _state(
        progress,
        obligation=obligation,
        phase="owner_receipt_recorded",
        conditions=[
            {
                "condition": source_condition,
                "action_type": _text(obligation.get("action_type")),
            }
        ],
        next_safe_action=_next_action(
            "consume_owner_receipt",
            provider_admission_allowed=False,
            owner=owner,
            owner_receipt_ref=owner_receipt_ref,
        ),
        current_owner=owner,
        evidence_refs=[owner_receipt_ref] if owner_receipt_ref is not None else [],
        diagnostic_report=diagnostic_report,
    )


def _next_action(
    kind: str,
    *,
    provider_admission_allowed: bool,
    provider_admission_requires_opl_runtime_result: bool | None = None,
    mas_can_authorize_provider_admission: bool | None = None,
    requires_claimable_live_readback_source: bool | None = None,
    fresh_live_claim_allowed: bool | None = None,
    owner: str | None = None,
    required_input: str | None = None,
    owner_receipt_ref: str | None = None,
    accepted_owner_gate_decision: Mapping[str, Any] | None = None,
    owner_callable: Mapping[str, Any] | None = None,
    successor_owner_action: Mapping[str, Any] | None = None,
    successor_owner_gate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = {
        "kind": kind,
        "owner": owner,
        "provider_admission_allowed": provider_admission_allowed,
        "provider_admission_requires_opl_runtime_result": provider_admission_requires_opl_runtime_result,
        "mas_can_authorize_provider_admission": mas_can_authorize_provider_admission,
        "requires_claimable_live_readback_source": requires_claimable_live_readback_source,
        "fresh_live_claim_allowed": fresh_live_claim_allowed,
        "required_input": required_input,
        "owner_receipt_ref": owner_receipt_ref,
        "accepted_owner_gate_decision": dict(accepted_owner_gate_decision or {}),
        "owner_callable": dict(owner_callable or {}),
        "successor_owner_action": dict(successor_owner_action or {}),
        "successor_owner_gate": dict(successor_owner_gate or {}),
    }
    return {key: value for key, value in payload.items() if value not in (None, "", [], {})}
