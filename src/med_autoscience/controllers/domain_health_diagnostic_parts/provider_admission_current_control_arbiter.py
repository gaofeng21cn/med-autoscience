from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    provider_attempt_matches_identity,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.domain_health_diagnostic_parts import (
    provider_admission_current_control_receipts as current_control_receipts,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
    attempt_idempotency_key as _attempt_idempotency_key,
    missing_identity_fields as _missing_identity_fields,
    route_identity_key as _route_identity_key,
    weak_provider_admission_identity as _weak_provider_admission_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity import (
    closeout_core_identity_matches_candidate as _closeout_core_identity_matches_candidate,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.opl_transition_readback import (
    candidate_opl_transition_readback,
    required_opl_transition_readback_shape,
)
from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
)

ARBITER_SURFACE_KIND = "mas_opl_stage_route_arbiter"
ARBITER_SCHEMA_VERSION = 1
STALE_STAGE_PACKET_BLOCKER = "stage_packet_not_current_selected_dispatch"
ACCEPTED_OWNER_GATE_DECISION_SOURCE = "paper_recovery_state.accepted_owner_gate_decision"
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
        if accepted_closeout and not _dry_run_request_only_transition_request_candidate(candidate):
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
            if _unconsumed_closeout_blocks_weak_identity_suppression(
                scanned_study,
                identity=candidate,
            ):
                decisions.append(
                    _arbiter_decision(
                        candidate,
                        decision="pending_provider_admission",
                        effect="retain_provider_admission_pending",
                        evidence={},
                    )
                )
                continue
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="weak_provider_admission_identity",
                    effect="suppress_provider_admission_pending",
                    evidence=weak_identity,
                )
            )
            continue
        typed_blocker_precedence = _current_typed_blocker_precedence_evidence_for_candidate(
            scanned_study,
            candidate=candidate,
        )
        if typed_blocker_precedence:
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
                        decision="pending_provider_admission",
                        effect="retain_provider_admission_pending",
                        evidence={},
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
                evidence={},
            )
        )
    return decisions


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
        "same_tick_materialization_source": _non_empty_text(
            candidate.get("same_tick_materialization_source")
        ),
        "active_stage_attempt_id": _non_empty_text(evidence.get("active_stage_attempt_id"))
        or _non_empty_text(evidence.get("stage_attempt_id")),
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


def _matching_accepted_closeout(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    for receipt in _accepted_closeout_receipts(study):
        if current_control_receipts.receipt_identity_inferred_from_current_work_unit(receipt):
            continue
        if current_control_receipts.receipt_is_accepted_closeout(
            receipt
        ):
            if _exact_owner_refs_closeout_matches_candidate(receipt, identity=identity):
                return receipt
            if current_control_receipts.accepted_closeout_matches_candidate_identity(
                receipt,
                identity=identity,
            ):
                return receipt
            if _explicit_accepted_closeout_core_identity_matches_without_currentness_conflict(
                receipt,
                identity=identity,
            ):
                return receipt
    return {}


def _explicit_accepted_closeout_core_identity_matches_without_currentness_conflict(
    receipt: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if not current_control_receipts.receipt_is_explicit_accepted_typed_closeout(receipt):
        return False
    if current_control_receipts.receipt_has_opl_execution_authorization_blocker(receipt):
        return False
    if not _closeout_core_identity_matches_candidate(receipt, identity=identity):
        return False
    receipt_basis = _accepted_closeout_currentness_basis(receipt)
    identity_basis = _mapping(identity.get("currentness_basis"))
    if receipt_basis and identity_basis and _currentness_basis_conflicts(
        receipt_basis,
        identity_basis=identity_basis,
    ):
        return False
    receipt_source_eval = _non_empty_text(receipt_basis.get("source_eval_id")) or _non_empty_text(
        receipt.get("source_eval_id")
    )
    identity_source_eval = _non_empty_text(identity_basis.get("source_eval_id")) or _non_empty_text(
        identity.get("source_eval_id")
    )
    return not (
        receipt_source_eval is not None
        and identity_source_eval is not None
        and receipt_source_eval != identity_source_eval
    )


def _exact_owner_refs_closeout_matches_candidate(
    receipt: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    statuses = current_control_receipts.receipt_statuses(receipt)
    if not ("closed_with_domain_owner_refs" in statuses or "executed" in statuses):
        return False
    if _non_empty_text(receipt.get("owner_receipt_ref")) is None and _non_empty_text(
        receipt.get("record_ref")
    ) is None and _non_empty_text(receipt.get("publication_eval_record_ref")) is None:
        owner_result = _mapping(receipt.get("owner_result"))
        owner_receipt = _mapping(receipt.get("owner_receipt"))
        if not any(
            _non_empty_text(value) is not None
            for value in (
                owner_result.get("owner_receipt_ref"),
                owner_result.get("publication_eval_record_ref"),
                owner_receipt.get("owner_receipt_ref"),
                owner_receipt.get("publication_eval_record_ref"),
            )
        ):
            return False
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    receipt_fingerprint = _non_empty_text(receipt.get("work_unit_fingerprint")) or _non_empty_text(
        receipt.get("action_fingerprint")
    )
    if (
        expected_action is None
        or expected_work_unit is None
        or expected_fingerprint is None
        or receipt_fingerprint is None
    ):
        return False
    if _non_empty_text(receipt.get("action_type")) != expected_action:
        return False
    if _non_empty_text(receipt.get("work_unit_id")) != expected_work_unit:
        return False
    if receipt_fingerprint != expected_fingerprint:
        return False
    receipt_basis = _accepted_closeout_currentness_basis(receipt)
    identity_basis = _mapping(identity.get("currentness_basis"))
    receipt_source_eval = _non_empty_text(receipt_basis.get("source_eval_id")) or _non_empty_text(
        receipt.get("source_eval_id")
    )
    identity_source_eval = _non_empty_text(identity_basis.get("source_eval_id")) or _non_empty_text(
        identity.get("source_eval_id")
    )
    return not (
        receipt_source_eval is not None
        and identity_source_eval is not None
        and receipt_source_eval != identity_source_eval
    )


def _accepted_closeout_currentness_basis(receipt: Mapping[str, Any]) -> dict[str, Any]:
    nested_owner_route_basis = _mapping(
        _mapping(_mapping(receipt.get("owner_route")).get("source_refs")).get(
            "owner_route_currentness_basis"
        )
    )
    basis = {
        **nested_owner_route_basis,
        **_mapping(receipt.get("owner_route_currentness_basis")),
        **_mapping(receipt.get("owner_route_basis")),
    }
    for key, value in {
        "source_eval_id": _non_empty_text(receipt.get("source_eval_id"))
        or _non_empty_text(basis.get("source_eval_id")),
        "truth_epoch": _non_empty_text(receipt.get("truth_epoch"))
        or _non_empty_text(basis.get("truth_epoch")),
        "runtime_health_epoch": _non_empty_text(receipt.get("runtime_health_epoch"))
        or _non_empty_text(basis.get("runtime_health_epoch")),
    }.items():
        if value is not None:
            basis[key] = value
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}


def _currentness_basis_conflicts(
    receipt_basis: Mapping[str, Any],
    *,
    identity_basis: Mapping[str, Any],
) -> bool:
    receipt_source_eval = _non_empty_text(receipt_basis.get("source_eval_id"))
    identity_source_eval = _non_empty_text(identity_basis.get("source_eval_id")) or _non_empty_text(
        identity_basis.get("publication_eval_id")
    )
    if (
        receipt_source_eval is not None
        and identity_source_eval is not None
        and receipt_source_eval != identity_source_eval
    ):
        return True
    for key in ("truth_epoch", "runtime_health_epoch"):
        receipt_value = _non_empty_text(receipt_basis.get(key))
        identity_value = _non_empty_text(identity_basis.get(key))
        if receipt_value is not None and identity_value is not None and receipt_value != identity_value:
            return True
    return False


def _terminal_closeout_precedence_evidence(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    precedence_evidence = _mapping(study.get("terminal_closeout_precedence_evidence"))
    if (
        precedence_evidence
        and current_control_receipts.receipt_is_accepted_closeout(precedence_evidence)
        and provider_attempt_matches_identity(precedence_evidence, identity=identity)
    ):
        return precedence_evidence
    live_attempt = _running_attempt_from_study(study)
    if not live_attempt or not provider_attempt_matches_identity(live_attempt, identity=identity):
        return {}
    closeout = _matching_accepted_closeout(study, identity=identity)
    if not closeout:
        return {}
    if current_control_receipts.receipt_matches_live_attempt(closeout, live_attempt):
        return closeout
    return {}


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


def _running_attempt_from_study(study: Mapping[str, Any]) -> dict[str, Any]:
    if study_has_running_provider_attempt(study):
        return _mapping(study.get("opl_provider_attempt")) or dict(study)
    nested = _mapping(study.get("opl_provider_attempt"))
    if study_has_running_provider_attempt(nested):
        return nested
    runtime_health = _live_attempt_from_runtime_health_snapshot(study)
    if runtime_health:
        return runtime_health
    progress_first = _live_attempt_from_progress_first_summary(study)
    if progress_first:
        return progress_first
    current_work_unit = _live_attempt_from_current_work_unit(study)
    if current_work_unit:
        return current_work_unit
    return {}


def _live_attempt_from_runtime_health_snapshot(study: Mapping[str, Any]) -> dict[str, Any]:
    runtime_health = _mapping(study.get("runtime_health_snapshot")) or _mapping(
        study.get("runtime_health")
    )
    worker_liveness = _mapping(runtime_health.get("worker_liveness_state")) or _mapping(
        runtime_health.get("worker_liveness")
    )
    if worker_liveness.get("worker_running") is False:
        return {}
    state = _non_empty_text(worker_liveness.get("state"))
    runtime_liveness = _non_empty_text(worker_liveness.get("runtime_liveness_status"))
    if state not in {None, "live", "running"} and runtime_liveness not in {"live", "running"}:
        return {}
    return _live_attempt_from_mapping(
        {
            **worker_liveness,
            "runtime_health": {
                "health_status": _non_empty_text(runtime_health.get("health_status")) or "running",
                "runtime_liveness_status": runtime_liveness or "live",
                **({"summary": runtime_health.get("summary")} if runtime_health.get("summary") else {}),
            },
        },
        study=study,
        source="runtime_health_snapshot.worker_liveness_state",
    )


def _live_attempt_from_progress_first_summary(study: Mapping[str, Any]) -> dict[str, Any]:
    progress_first = _mapping(study.get("progress_first_monitoring_summary"))
    if progress_first.get("running_provider_attempt") is not True:
        return {}
    attempt = _live_attempt_from_mapping(
        progress_first,
        study=study,
        source="progress_first_monitoring_summary.live_provider_attempt",
    )
    if attempt:
        return attempt
    return {}


def _live_attempt_from_current_work_unit(study: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(study.get("current_work_unit"))
    state = _mapping(current.get("state"))
    proof = _mapping(state.get("provider_attempt_proof"))
    if proof.get("running_provider_attempt") is not True:
        return {}
    return _live_attempt_from_mapping(
        proof,
        study={**dict(study), "current_work_unit": current},
        source="current_work_unit.provider_attempt_proof",
    )


def _live_attempt_from_mapping(
    payload: Mapping[str, Any],
    *,
    study: Mapping[str, Any],
    source: str,
) -> dict[str, Any]:
    active_run_id = _non_empty_text(payload.get("active_run_id"))
    active_stage_attempt_id = _non_empty_text(
        payload.get("active_stage_attempt_id")
    ) or _stage_id_from_run_id(active_run_id)
    active_workflow_id = _non_empty_text(payload.get("active_workflow_id"))
    if (active_stage_attempt_id or active_run_id or active_workflow_id) is None:
        return {}
    runtime_health = _mapping(payload.get("runtime_health")) or _mapping(
        payload.get("worker_liveness")
    )
    if runtime_health:
        runtime_liveness = _non_empty_text(runtime_health.get("runtime_liveness_status"))
        health_status = _non_empty_text(runtime_health.get("health_status"))
        if runtime_liveness not in {None, "live", "running"} and health_status not in {
            "live",
            "running",
        }:
            return {}
    current = _mapping(study.get("current_work_unit"))
    current_state = _mapping(current.get("state"))
    basis = _mapping(current.get("currentness_basis"))
    current_action = _mapping(study.get("current_executable_owner_action"))
    return {
        key: value
        for key, value in {
            "running_provider_attempt": True,
            "active_run_id": active_run_id,
            "active_stage_attempt_id": active_stage_attempt_id,
            "active_workflow_id": active_workflow_id,
            "owner": _non_empty_text(payload.get("owner"))
            or _non_empty_text(study.get("next_owner"))
            or _non_empty_text(current.get("owner")),
            "action_type": _non_empty_text(payload.get("action_type"))
            or _non_empty_text(current.get("action_type"))
            or _non_empty_text(current_action.get("action_type")),
            "work_unit_id": _non_empty_text(payload.get("work_unit_id"))
            or _non_empty_text(payload.get("next_work_unit"))
            or _non_empty_text(current.get("work_unit_id"))
            or _non_empty_text(basis.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(payload.get("work_unit_fingerprint"))
            or _non_empty_text(payload.get("action_fingerprint"))
            or _non_empty_text(current.get("work_unit_fingerprint"))
            or _non_empty_text(current.get("action_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(payload.get("action_fingerprint"))
            or _non_empty_text(payload.get("work_unit_fingerprint"))
            or _non_empty_text(current.get("action_fingerprint"))
            or _non_empty_text(current.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint")),
            "runtime_health": runtime_health
            or _mapping(current_state.get("runtime_health"))
            or {"health_status": "running", "runtime_liveness_status": "live"},
            "source": source,
        }.items()
        if value not in (None, "", [], {})
    }


def _stage_id_from_run_id(run_id: str | None) -> str | None:
    if run_id is None:
        return None
    prefix = "opl-stage-attempt://"
    if run_id.startswith(prefix):
        return _non_empty_text(run_id.removeprefix(prefix))
    return None


def _candidates_not_covered_by_live_attempt(
    candidates: list[dict[str, Any]],
    *,
    live_studies_by_id: Mapping[str, Mapping[str, Any]],
    scanned_studies_by_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    pending: list[dict[str, Any]] = []
    for candidate in candidates:
        request_only_transition = _request_only_transition_request_candidate(candidate)
        study_id = _non_empty_text(candidate.get("study_id"))
        live_study = _mapping(live_studies_by_id.get(study_id)) if study_id is not None else {}
        live_attempt = _running_attempt_from_study(live_study)
        scanned_study = (
            _mapping((scanned_studies_by_id or {}).get(study_id)) if study_id is not None else {}
        )
        if _terminal_closeout_precedence_evidence(scanned_study, identity=candidate):
            continue
        if _matching_accepted_closeout(
            scanned_study,
            identity=candidate,
        ) and not _unconsumed_closeout_blocks_weak_identity_suppression(
            scanned_study,
            identity=candidate,
        ):
            continue
        if live_attempt and _running_attempt_covers_candidate(live_attempt, candidate=candidate):
            continue
        if live_attempt and _strict_running_attempt_owns_current_execution_slot(
            live_attempt,
            candidate=candidate,
        ):
            continue
        paper_recovery_block = _paper_recovery_state_blocks_provider_admission(
            scanned_study,
            identity=candidate,
        )
        if paper_recovery_block:
            if not request_only_transition or _paper_recovery_block_is_hard_blocker(
                paper_recovery_block
            ):
                continue
        weak_identity = _current_control_weak_provider_admission_identity(candidate)
        if weak_identity and _candidate_requires_strong_current_control_identity(candidate):
            if not _unconsumed_closeout_blocks_weak_identity_suppression(
                scanned_study,
                identity=candidate,
            ):
                continue
        elif (
            weak_identity
            and not candidate_opl_transition_readback(candidate)
            and not request_only_transition
        ):
            continue
        if _current_typed_blocker_precedence_evidence_for_candidate(
            scanned_study,
            candidate=candidate,
        ):
            if not request_only_transition or _paper_recovery_block_is_hard_blocker(
                paper_recovery_block
            ) or not _request_only_transition_can_bypass_current_typed_blocker(
                scanned_study,
                candidate=candidate,
            ):
                continue
        pending.append(dict(candidate))
    return pending


def _paper_recovery_block_is_hard_blocker(block: Mapping[str, Any]) -> bool:
    phase = _non_empty_text(block.get("status")) or _non_empty_text(block.get("phase"))
    if phase in {"domain_blocked", "human_gate"}:
        return True
    next_safe_action = _mapping(block.get("next_safe_action"))
    return _non_empty_text(next_safe_action.get("kind")) == "resolve_typed_blocker"


def _request_only_transition_can_bypass_current_typed_blocker(
    study: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> bool:
    for receipt in _accepted_closeout_receipts(study):
        if not current_control_receipts.receipt_is_explicit_accepted_typed_closeout(receipt):
            continue
        if _closeout_core_identity_matches_candidate(receipt, identity=candidate):
            return not current_control_receipts.accepted_closeout_matches_candidate_identity(
                receipt,
                identity=candidate,
            )
    return False


def _request_only_transition_request_candidate(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return False
    transition_request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if not transition_request:
        return False
    if candidate.get("provider_admission_pending") is not False:
        return False
    if candidate.get("provider_admission_requires_opl_runtime_result") is not True:
        return False
    if (
        candidate.get("same_tick_materialized_provider_admission") is True
        and _non_empty_text(candidate.get("dispatch_status")) != "transition_request_pending"
    ):
        return False
    return _non_empty_text(candidate.get("status")) == "transition_request_pending" or _non_empty_text(
        candidate.get("dispatch_status")
    ) == "transition_request_pending"


def _dry_run_request_only_transition_request_candidate(candidate: Mapping[str, Any]) -> bool:
    return (
        _request_only_transition_request_candidate(candidate)
        and candidate.get("same_tick_materialized_provider_admission") is True
        and _non_empty_text(candidate.get("same_tick_materialization_source")) == "dry_run_preview"
    )


def _candidate_requires_strong_current_control_identity(candidate: Mapping[str, Any]) -> bool:
    if candidate_opl_transition_readback(candidate):
        return True
    if (
        candidate.get("same_tick_materialized_provider_admission") is True
        and _non_empty_text(candidate.get("same_tick_materialization_source"))
        != "dry_run_preview"
    ):
        return True
    if (
        _non_empty_text(candidate.get("status")) == "provider_admission_pending"
        and _current_control_weak_provider_admission_identity(candidate)
    ):
        return True
    return _non_empty_text(candidate.get("source")) in {
        "same_tick_materialized_dispatch",
        "opl_current_control_state.action_queue",
        "opl_current_control_state.study_current_executable_owner_action",
    }


def _opl_transition_readback_required_evidence(candidate: Mapping[str, Any]) -> dict[str, Any]:
    if candidate_opl_transition_readback(candidate):
        return {}
    transition_request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if not transition_request:
        return {}
    required_shape = required_opl_transition_readback_shape()
    return {
        "status": "NonAdvancingApply",
        "blocked_reason": "opl_transition_readback_required",
        "required_runtime": _non_empty_text(required_shape.get("runtime_kind"))
        or "DomainProgressTransitionRuntime",
        "required_runtime_owner": _non_empty_text(required_shape.get("runtime_owner"))
        or "one-person-lab",
        "missing_readback_sections": list(required_shape.get("required_sections") or []),
        "missing_runtime_refs": list(required_shape.get("required_runtime_refs") or []),
        "required_readback_surface_kind": _non_empty_text(required_shape.get("surface_kind")),
        "mas_transition_request_idempotency_key": _non_empty_text(
            transition_request.get("idempotency_key")
        ),
        "mas_can_authorize_provider_admission": False,
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "event_or_outbox_fragment_is_provider_admission_authority": False,
        "no_progress_signal": "transition_request_waits_for_opl_runtime",
    }


def _paper_recovery_state_blocks_provider_admission(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    recovery = _mapping(study.get("paper_recovery_state"))
    if not recovery:
        return {}
    supervisor_gate = provider_admission_supervisor_gate(study, paper_recovery_state=recovery)
    supervisor_decision = _mapping(supervisor_gate.get("supervisor_decision"))
    if supervisor_decision and supervisor_gate.get("blocked") is not True:
        return {}
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _provider_admission_candidate_materializes_recovery_action(
        identity,
        recovery=recovery,
        supervisor_decision=supervisor_decision,
    ):
        return {}
    if _non_empty_text(recovery.get("phase")) == "admission_pending" and (
        next_safe_action.get("provider_admission_requires_opl_runtime_result") is False
        or _non_empty_text(next_safe_action.get("kind")) == "admit_provider_attempt"
    ):
        return {}
    if _non_empty_text(recovery.get("phase")) == "human_gate":
        return {}
    if (
        not supervisor_decision
        and next_safe_action.get("provider_admission_allowed") is not False
    ):
        return {}
    if not _paper_recovery_state_matches_identity(study, recovery=recovery, identity=identity):
        return {}
    phase = _non_empty_text(recovery.get("phase")) or "paper_recovery_state_blocks_provider_admission"
    return {
        key: value
        for key, value in {
            **recovery,
            "status": phase,
            "provider_admission_allowed": False,
            "supervisor_decision": supervisor_decision,
            "next_safe_action": next_safe_action,
        }.items()
        if value not in (None, "", [], {})
    }


def _provider_admission_candidate_materializes_recovery_action(
    identity: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
    supervisor_decision: Mapping[str, Any],
) -> bool:
    identity_source = _non_empty_text(identity.get("source"))
    materializes_successor = (
        identity.get("same_tick_materialized_provider_admission") is True
        and identity_source == "same_tick_materialized_dispatch"
    ) or (
        identity_source == "opl_current_control_state.study_current_executable_owner_action"
        and _non_empty_text(identity.get("mas_owner_action_source"))
        == "paper_recovery_state.next_safe_action.successor_owner_action"
    )
    if not materializes_successor:
        return False
    if _non_empty_text(supervisor_decision.get("decision")) != "materialize_recovery_action":
        return False
    if _non_empty_text(recovery.get("phase")) != "owner_action_ready":
        return False
    next_safe_action = _mapping(supervisor_decision.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) != "materialize_recovery_work_unit_or_receipt":
        return False
    source_next_safe_action = _mapping(next_safe_action.get("source_next_safe_action"))
    source_next_kind = _non_empty_text(source_next_safe_action.get("kind"))
    if source_next_kind == "materialize_successor_owner_action":
        successor = _mapping(source_next_safe_action.get("successor_owner_action"))
        if not successor or not _identity_matches(successor, identity=identity):
            return False
    elif source_next_kind != "run_mas_owner_callable":
        return False
    owner = _non_empty_text(identity.get("next_executable_owner")) or _non_empty_text(identity.get("owner"))
    supervisor_owner = _non_empty_text(supervisor_decision.get("next_owner")) or _non_empty_text(
        source_next_safe_action.get("owner")
    ) or _non_empty_text(
        _mapping(source_next_safe_action.get("successor_owner_action")).get("owner")
    )
    return owner is not None and supervisor_owner in {None, owner}


def _running_attempt_covers_candidate(
    live_attempt: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> bool:
    if provider_attempt_matches_identity(live_attempt, identity=candidate):
        return True
    expected_fingerprint = _non_empty_text(candidate.get("work_unit_fingerprint")) or _non_empty_text(
        candidate.get("action_fingerprint")
    )
    if expected_fingerprint is None:
        return False
    if not _running_attempt_has_live_liveness(live_attempt):
        return False
    return _identity_matches(live_attempt, identity=candidate)


def _running_attempt_has_live_liveness(live_attempt: Mapping[str, Any]) -> bool:
    runtime_health = _mapping(live_attempt.get("runtime_health")) or _mapping(
        live_attempt.get("worker_liveness")
    )
    runtime_liveness = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    if runtime_liveness in {"live", "running"} or health_status in {"live", "running"}:
        return True
    return (
        runtime_liveness is None
        and health_status is None
        and _non_empty_text(live_attempt.get("source")) == "runtime_health_snapshot.worker_liveness_state"
    )


def _strict_running_attempt_owns_current_execution_slot(
    live_attempt: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> bool:
    if not _running_attempt_has_live_liveness(live_attempt):
        return False
    live_action = _non_empty_text(live_attempt.get("action_type"))
    live_work_unit = _non_empty_text(live_attempt.get("work_unit_id")) or _non_empty_text(
        live_attempt.get("next_work_unit")
    )
    candidate_action = _non_empty_text(candidate.get("action_type"))
    candidate_work_unit = _non_empty_text(candidate.get("work_unit_id")) or _non_empty_text(
        candidate.get("next_work_unit")
    )
    return bool(
        (
            live_action is not None
            and candidate_action is not None
            and live_action != candidate_action
        )
        or (
            live_work_unit is not None
            and candidate_work_unit is not None
            and live_work_unit != candidate_work_unit
        )
    )


def _paper_recovery_state_matches_identity(
    study: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
    identity: Mapping[str, Any],
) -> bool:
    obligation = _mapping(_mapping(recovery.get("current_authority")).get("obligation"))
    current_work_unit = _mapping(study.get("current_work_unit"))
    sources = [obligation, current_work_unit]
    return any(_identity_matches(source, identity=identity) for source in sources if source)


def _identity_matches(source: Mapping[str, Any], *, identity: Mapping[str, Any]) -> bool:
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    source_action = _non_empty_text(source.get("action_type"))
    source_work_unit = _non_empty_text(source.get("work_unit_id")) or _non_empty_text(source.get("next_work_unit"))
    source_fingerprint = _non_empty_text(source.get("work_unit_fingerprint")) or _non_empty_text(
        source.get("action_fingerprint")
    )
    comparisons = (
        (expected_action, source_action),
        (expected_work_unit, source_work_unit),
        (expected_fingerprint, source_fingerprint),
    )
    matched = False
    for expected, actual in comparisons:
        if expected is None:
            continue
        if actual is None or actual != expected:
            return False
        matched = True
    return matched


def _current_typed_blocker_precedence_evidence_for_candidate(
    study: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    evidence = _current_typed_blocker_precedence_evidence(study, identity=candidate)
    if not evidence:
        return {}
    if (
        _non_empty_text(evidence.get("blocker_type")) == STALE_STAGE_PACKET_BLOCKER
        and _non_empty_text(candidate.get("source"))
        == "opl_current_control_state.study_current_executable_owner_action"
        and _non_empty_text(_mapping(candidate.get("currentness_basis")).get("source"))
        == ACCEPTED_OWNER_GATE_DECISION_SOURCE
    ):
        return {}
    return evidence


def _current_typed_blocker_precedence_evidence(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    blocker = _current_typed_blocker(study)
    if not blocker:
        return {}
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    blocker_action = _non_empty_text(blocker.get("action_type"))
    blocker_work_unit = _non_empty_text(blocker.get("work_unit_id"))
    if expected_action is not None and blocker_action is not None and blocker_action != expected_action:
        return {}
    if expected_work_unit is not None and blocker_work_unit is not None and blocker_work_unit != expected_work_unit:
        return {}
    if expected_action is None and expected_work_unit is None:
        return {}
    if blocker_action is None and blocker_work_unit is None:
        return {}
    return blocker


def _current_typed_blocker(study: Mapping[str, Any]) -> dict[str, Any]:
    current = _mapping(study.get("current_work_unit"))
    current_status = _non_empty_text(current.get("status"))
    if current_status == "typed_blocker":
        state = _mapping(current.get("state"))
        typed_blocker = _mapping(state.get("typed_blocker")) or _mapping(
            current.get("typed_blocker")
        )
        currentness_basis = _mapping(current.get("currentness_basis"))
        return {
            key: value
            for key, value in {
                **typed_blocker,
                "status": "typed_blocker",
                "owner": _non_empty_text(current.get("owner"))
                or _non_empty_text(typed_blocker.get("owner")),
                "action_type": _non_empty_text(current.get("action_type"))
                or _non_empty_text(typed_blocker.get("action_type")),
                "work_unit_id": _non_empty_text(current.get("work_unit_id"))
                or _non_empty_text(typed_blocker.get("work_unit_id"))
                or _non_empty_text(currentness_basis.get("work_unit_id")),
                "work_unit_fingerprint": _non_empty_text(current.get("work_unit_fingerprint"))
                or _non_empty_text(current.get("action_fingerprint"))
                or _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
                or _non_empty_text(typed_blocker.get("action_fingerprint"))
                or _non_empty_text(currentness_basis.get("work_unit_fingerprint"))
                or _non_empty_text(currentness_basis.get("action_fingerprint")),
                "source": "current_work_unit.typed_blocker",
                "blocker_type": _non_empty_text(typed_blocker.get("blocker_type"))
                or _non_empty_text(typed_blocker.get("blocker_id"))
                or _non_empty_text(state.get("blocker_type")),
            }.items()
            if value not in (None, "", [], {})
        }
    if current:
        return {}
    envelope = _mapping(study.get("current_execution_envelope"))
    state_kind = _non_empty_text(envelope.get("state_kind")) or _non_empty_text(
        envelope.get("execution_state_kind")
    )
    if state_kind != "typed_blocker":
        return {}
    typed_blocker = _mapping(envelope.get("typed_blocker"))
    return {
        key: value
        for key, value in {
            **typed_blocker,
            "status": "typed_blocker",
            "owner": _non_empty_text(envelope.get("owner"))
            or _non_empty_text(typed_blocker.get("owner")),
            "action_type": _non_empty_text(typed_blocker.get("action_type")),
            "work_unit_id": _non_empty_text(typed_blocker.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
            or _non_empty_text(typed_blocker.get("action_fingerprint")),
            "source": "current_execution_envelope.typed_blocker",
            "blocker_type": _non_empty_text(typed_blocker.get("blocker_type"))
            or _non_empty_text(typed_blocker.get("blocker_id"))
            or _non_empty_text(typed_blocker.get("reason")),
        }.items()
        if value not in (None, "", [], {})
    }


def _current_control_weak_provider_admission_identity(identity: Mapping[str, Any]) -> dict[str, Any]:
    weak_identity = _weak_provider_admission_identity(identity)
    if not weak_identity:
        return {}
    current_control_missing = [
        field
        for field in weak_identity.get("missing_identity_fields") or []
        if field
        in {
            "study_id",
            "action_type",
            "work_unit_id",
            "work_unit_fingerprint",
            "dispatch_path_or_ref",
            "route_identity_key",
            "attempt_idempotency_key",
            "stage_packet_ref_or_refs",
            "currentness_basis",
        }
    ]
    if not current_control_missing:
        return {}
    return {
        "status": "weak_provider_admission_identity",
        "missing_identity_fields": current_control_missing,
    }


def _unconsumed_closeout_blocks_weak_identity_suppression(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    for receipt in _accepted_closeout_receipts(study):
        if not current_control_receipts.receipt_is_accepted_closeout(receipt):
            continue
        if _receipt_has_provider_admission_authorization_blocker(receipt):
            continue
        if current_control_receipts.accepted_closeout_matches_candidate_identity(
            receipt,
            identity=identity,
        ):
            continue
        if _closeout_core_identity_matches_candidate(receipt, identity=identity):
            return True
    return False


def _receipt_has_provider_admission_authorization_blocker(
    receipt: Mapping[str, Any],
) -> bool:
    if current_control_receipts.receipt_has_opl_execution_authorization_blocker(receipt):
        return True
    typed_blocker = _mapping(receipt.get("typed_blocker"))
    direct_values = (
        receipt.get("blocked_reason"),
        receipt.get("typed_blocker_reason"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("reason"),
        typed_blocker.get("blocked_reason"),
    )
    return any(_non_empty_text(value) == STALE_STAGE_PACKET_BLOCKER for value in direct_values)
