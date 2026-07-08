from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers import (
    opl_domain_progress_transition_contract as transition_contract,
)
from med_autoscience.controllers.provider_admission.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission.provider_admission_current_control_arbiter_candidate_evidence import (
    _accepted_owner_gate_transition_request_candidate,
    _candidate_requires_strong_current_control_identity,
    _candidates_not_covered_by_live_attempt,
    _current_control_weak_provider_admission_identity,
    _current_typed_blocker_precedence_evidence_for_candidate,
    _dry_run_request_only_transition_request_candidate,
    _matching_accepted_closeout,
    _opl_transition_readback_required_evidence,
    _paper_recovery_block_is_hard_blocker,
    _paper_recovery_block_requires_supervisor_decision_readback,
    _paper_recovery_state_blocks_provider_admission,
    _provider_admission_readback_overrides_blocking_closeout,
    _request_only_transition_can_bypass_paper_recovery_block,
    _request_only_transition_request_candidate,
    _running_attempt_covers_candidate,
    _running_attempt_from_study,
    _strict_running_attempt_owns_current_execution_slot,
    _terminal_closeout_precedence_evidence,
    _unconsumed_closeout_blocks_weak_identity_suppression,
)
from med_autoscience.controllers.provider_admission.provider_admission_current_control_identity import (
    attempt_idempotency_key as _attempt_idempotency_key,
    missing_identity_fields as _missing_identity_fields,
    route_identity_key as _route_identity_key,
)
from med_autoscience.controllers.provider_admission.provider_admission_current_control_readback_overrides import (
    weak_identity_is_opl_authorization_stage_packet_gap,
)
from med_autoscience.controllers.provider_admission.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)

ARBITER_SURFACE_KIND = "mas_opl_stage_route_arbiter"
ARBITER_SCHEMA_VERSION = 1
ARBITER_AUTHORITY_BOUNDARY = {
    "arbiter_surface": "currentness_projection_only",
    "authority": False,
    "projection_owner": "med-autoscience",
    "transition_runtime_owner": "one-person-lab",
    "runtime_kind": "DomainProgressTransitionRuntime",
    "can_write_domain_truth": False,
    "can_authorize_provider_admission": False,
    "provider_admission_requires_mas_transition_request": True,
    "provider_admission_readback_requires_opl_live_readback": True,
    "event_or_outbox_fragment_is_provider_admission_authority": False,
    "can_own_generic_event_log_or_outbox": False,
    "can_run_fixed_point_runtime": False,
    "can_authorize_publication_ready": False,
    "provider_completion_is_domain_ready": False,
}


def _stage_route_arbiter_decisions(
    candidates: list[dict[str, Any]],
    *,
    live_studies_by_id: Mapping[str, Mapping[str, Any]],
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    decisions: list[dict[str, Any]] = []
    for candidate in candidates:
        study_id = _non_empty_text(candidate.get("study_id"))
        scanned_study = (
            _mapping(scanned_studies_by_id.get(study_id)) if study_id is not None else {}
        )
        terminal_precedence = _terminal_closeout_precedence_evidence(
            scanned_study,
            identity=candidate,
        )
        if terminal_precedence:
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="terminal_closeout_precedes_live_projection",
                    effect="suppress_provider_admission_pending",
                    evidence=terminal_precedence,
                )
            )
            continue
        readback_required = _opl_transition_readback_required_evidence(candidate)
        accepted_closeout = _matching_accepted_closeout(scanned_study, identity=candidate)
        if (
            accepted_closeout
            and not _provider_admission_readback_overrides_blocking_closeout(
                candidate,
                closeout=accepted_closeout,
            )
            and not _dry_run_request_only_transition_request_candidate(candidate)
            and not _accepted_owner_gate_transition_request_candidate(candidate)
        ):
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="accepted_closeout_consumed_pending",
                    effect="suppress_provider_admission_pending",
                    evidence=accepted_closeout,
                )
            )
            continue
        live_study = _mapping(live_studies_by_id.get(study_id)) if study_id is not None else {}
        live_attempt = _running_attempt_from_study(live_study)
        if live_attempt and (
            _running_attempt_covers_candidate(live_attempt, candidate=candidate)
            or _strict_running_attempt_owns_current_execution_slot(
                live_attempt,
                candidate=candidate,
            )
        ):
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="running_identity_observed",
                    effect="suppress_provider_admission_pending",
                    evidence=live_attempt,
                )
            )
            continue
        paper_recovery_block = _paper_recovery_state_blocks_provider_admission(
            scanned_study,
            identity=candidate,
        )
        if paper_recovery_block:
            if (
                readback_required
                and _request_only_transition_request_candidate(candidate)
                and (
                    not _paper_recovery_block_requires_supervisor_decision_readback(paper_recovery_block)
                    or _accepted_owner_gate_transition_request_candidate(candidate)
                )
                and not _paper_recovery_block_is_hard_blocker(paper_recovery_block)
            ):
                decisions.append(
                    _arbiter_decision(
                        candidate,
                        decision="opl_transition_readback_required",
                        effect="suppress_provider_admission_pending",
                        evidence={
                            **readback_required,
                            "paper_recovery_state": dict(paper_recovery_block),
                        },
                    )
                )
                continue
            if not _request_only_transition_can_bypass_paper_recovery_block(
                candidate,
                block=paper_recovery_block,
            ):
                decisions.append(
                    _arbiter_decision(
                        candidate,
                        decision="paper_recovery_state_blocks_provider_admission",
                        effect="suppress_provider_admission_pending",
                        evidence=paper_recovery_block,
                    )
                )
                continue
        weak_identity = (
            _current_control_weak_provider_admission_identity(candidate)
            if _candidate_requires_strong_current_control_identity(candidate)
            else {}
        )
        if weak_identity:
            if _weak_identity_is_opl_authorization_stage_packet_gap(
                candidate,
                scanned_study=scanned_study,
                weak_identity=weak_identity,
            ):
                decisions.append(_weak_provider_admission_identity_decision(candidate, weak_identity))
                continue
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="opl_transition_readback_required",
                    effect="suppress_provider_admission_pending",
                    evidence=_opl_transition_readback_required_evidence(
                        candidate,
                        weak_identity=weak_identity,
                    ),
                )
            )
            continue
        typed_blocker_precedence = _current_typed_blocker_precedence_evidence_for_candidate(
            scanned_study,
            candidate=candidate,
        )
        if typed_blocker_precedence:
            if not provider_admission_opl_transition_readback(candidate):
                decisions.append(
                    _arbiter_decision(
                        candidate,
                        decision="current_typed_blocker_precedes_provider_admission",
                        effect="suppress_provider_admission_pending",
                        evidence=typed_blocker_precedence,
                    )
                )
                continue
        if readback_required:
            if _unconsumed_closeout_blocks_weak_identity_suppression(
                scanned_study,
                identity=candidate,
            ) and not _dry_run_request_only_transition_request_candidate(candidate):
                decisions.append(
                    _arbiter_decision(
                        candidate,
                        decision="opl_transition_readback_required",
                        effect="suppress_provider_admission_pending",
                        evidence=readback_required,
                    )
                )
                continue
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="opl_transition_readback_required",
                    effect="suppress_provider_admission_pending",
                    evidence=readback_required,
                )
            )
            continue
        decisions.append(
            _arbiter_decision(
                candidate,
                decision="pending_provider_admission",
                effect="retain_provider_admission_pending",
                evidence=_provider_admission_readback_consumption_evidence(candidate),
            )
        )
    return decisions


def _weak_provider_admission_identity_decision(
    candidate: Mapping[str, Any],
    weak_identity: Mapping[str, Any],
) -> dict[str, Any]:
    return _arbiter_decision(
        candidate,
        decision="weak_provider_admission_identity",
        effect="suppress_provider_admission_pending",
        evidence=weak_identity,
    )


def _weak_identity_is_opl_authorization_stage_packet_gap(
    candidate: Mapping[str, Any],
    *,
    scanned_study: Mapping[str, Any],
    weak_identity: Mapping[str, Any],
) -> bool:
    return weak_identity_is_opl_authorization_stage_packet_gap(
        candidate,
        scanned_study=scanned_study,
        weak_identity=weak_identity,
    )


def _arbiter_decision(
    candidate: Mapping[str, Any],
    *,
    decision: str,
    effect: str,
    evidence: Mapping[str, Any],
) -> dict[str, Any]:
    evidence_status = _evidence_status(evidence)
    no_progress_signal = _arbiter_no_progress_signal(
        decision=decision,
        evidence_status=evidence_status,
    )
    payload: dict[str, Any] = {
        "surface_kind": "mas_opl_stage_route_arbiter_decision",
        "schema_version": ARBITER_SCHEMA_VERSION,
        "decision": decision,
        "effect": effect,
        "study_id": _non_empty_text(candidate.get("study_id")),
        "quest_id": _non_empty_text(candidate.get("quest_id")),
        "action_type": _non_empty_text(candidate.get("action_type")),
        "work_unit_id": _non_empty_text(candidate.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
        or _non_empty_text(candidate.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(candidate.get("action_fingerprint")),
        "route_identity_key": _route_identity_key(candidate),
        "attempt_idempotency_key": _attempt_idempotency_key(candidate),
        "dispatch_path": _non_empty_text(candidate.get("dispatch_path")),
        "dispatch_ref": _non_empty_text(candidate.get("dispatch_ref")),
        "mas_owner_action_source": _non_empty_text(candidate.get("mas_owner_action_source")),
        "currentness_basis": dict(_mapping(candidate.get("currentness_basis"))) or None,
        "same_tick_materialization_source": _non_empty_text(
            candidate.get("same_tick_materialization_source")
        ),
        "active_stage_attempt_id": _non_empty_text(evidence.get("active_stage_attempt_id"))
        or _non_empty_text(evidence.get("stage_attempt_id"))
        or _non_empty_text(evidence.get("terminal_stage_attempt_id")),
        "active_run_id": _non_empty_text(evidence.get("active_run_id")),
        "active_workflow_id": _non_empty_text(evidence.get("active_workflow_id")),
        "missing_identity_fields": _missing_identity_fields(evidence),
        "evidence": dict(evidence) if evidence else None,
        "evidence_status": evidence_status,
        "no_progress_signal": no_progress_signal,
        "anti_loop_classification": _arbiter_anti_loop_classification(no_progress_signal),
        "authority_boundary": dict(ARBITER_AUTHORITY_BOUNDARY),
    }
    return {key: value for key, value in payload.items() if value is not None}


def _arbiter_no_progress_signal(
    *,
    decision: str,
    evidence_status: str | None,
) -> str | None:
    if decision == "opl_transition_readback_required" and evidence_status == "NonAdvancingApply":
        return "transition_request_waits_for_opl_runtime"
    if decision not in {
        "accepted_closeout_consumed_pending",
        "terminal_closeout_precedes_live_projection",
    }:
        return None
    if evidence_status == "repeat_suppressed":
        return "same_work_unit_repeat_suppressed_terminal_stage"
    if evidence_status in {
        "owner_output_already_current",
        "record_only_archive",
    }:
        return "idempotent_noop_without_new_owner_delta"
    return None


def _arbiter_anti_loop_classification(no_progress_signal: str | None) -> str | None:
    if no_progress_signal == "same_work_unit_repeat_suppressed_terminal_stage":
        return "provider_admission_echo"
    if no_progress_signal == "idempotent_noop_without_new_owner_delta":
        return "same_work_unit_no_delta"
    if no_progress_signal == "transition_request_waits_for_opl_runtime":
        return "non_advancing_apply_required"
    return None


def _stage_route_arbiter_summary(
    *,
    decisions: list[dict[str, Any]],
    candidate_count: int,
    pending_count: int,
) -> dict[str, Any]:
    decision_counts: dict[str, int] = {}
    for decision in decisions:
        key = _non_empty_text(decision.get("decision"))
        if key is None:
            continue
        decision_counts[key] = decision_counts.get(key, 0) + 1
    return {
        "surface_kind": ARBITER_SURFACE_KIND,
        "schema_version": ARBITER_SCHEMA_VERSION,
        "candidate_count": candidate_count,
        "pending_count": pending_count,
        "decision_counts": decision_counts,
        "ordinary_planning_root": "current_owner_delta",
        "authority_boundary": dict(ARBITER_AUTHORITY_BOUNDARY),
    }


def _provider_admission_readback_consumption_evidence(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    readback = provider_admission_opl_transition_readback(candidate)
    if not readback:
        return {}
    consumption = _opl_transition_event_consumption(readback)
    if not consumption:
        return {}
    return {
        "status": "opl_transition_consumed",
        "opl_transition_event_consumption": consumption,
    }


def _opl_transition_event_consumption(readback: Mapping[str, Any]) -> dict[str, Any]:
    identity = _mapping(readback.get("identity"))
    causality = _mapping(readback.get("causality"))
    latest_transaction = _mapping(readback.get("latest_transaction_readback"))
    stage_identity = _mapping(identity.get("stage_run_identity"))

    event_id = _non_empty_text(identity.get("latest_event_id"))
    outbox_item_id = _non_empty_text(identity.get("latest_outbox_item_id"))
    transaction_id = _non_empty_text(identity.get("latest_transaction_id"))
    if not (
        event_id
        and outbox_item_id
        and transaction_id
        and event_id == _non_empty_text(causality.get("event_id"))
        and event_id == _non_empty_text(latest_transaction.get("event_id"))
        and outbox_item_id == _non_empty_text(causality.get("outbox_item_id"))
        and outbox_item_id == _non_empty_text(latest_transaction.get("outbox_item_id"))
        and transaction_id == _non_empty_text(causality.get("transaction_id"))
        and transaction_id == _non_empty_text(latest_transaction.get("transaction_id"))
    ):
        return {}
    return {
        "surface_kind": "mas_opl_transition_event_consumption",
        "status": "opl_transition_consumed",
        "runtime_owner": transition_contract.RUNTIME_OWNER,
        "runtime_kind": transition_contract.RUNTIME_KIND,
        "readback_surface_kind": transition_contract.LIVE_READBACK_SURFACE,
        "event_id": event_id,
        "outbox_item_id": outbox_item_id,
        "transaction_id": transaction_id,
        "stage_run_id": _non_empty_text(stage_identity.get("stage_run_id")),
        "stage_run_identity_ref": _non_empty_text(
            stage_identity.get("stage_run_identity_ref")
        ),
        "route_identity_key": _non_empty_text(stage_identity.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(
            stage_identity.get("attempt_idempotency_key")
        ),
        "request_idempotency_key": _non_empty_text(identity.get("idempotency_key")),
        "same_transaction_event_and_outbox": True,
        "transaction_complete": True,
        "mas_can_authorize_provider_admission": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_stage_run": False,
        "event_or_outbox_fragment_is_provider_admission_authority": False,
    }


def _evidence_status(evidence: Mapping[str, Any]) -> str | None:
    return (
        _non_empty_text(evidence.get("status"))
        or _non_empty_text(evidence.get("execution_status"))
        or _non_empty_text(evidence.get("closeout_receipt_status"))
        or _non_empty_text(evidence.get("current_attempt_state"))
        or _non_empty_text(evidence.get("reconciliation_status"))
        or _non_empty_text(evidence.get("stage_closeout_status"))
        or _non_empty_text(_mapping(evidence.get("runtime_health")).get("runtime_liveness_status"))
    )
