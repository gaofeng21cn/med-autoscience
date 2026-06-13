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

ARBITER_SURFACE_KIND = "mas_opl_stage_route_arbiter"
ARBITER_SCHEMA_VERSION = 1
STALE_STAGE_PACKET_BLOCKER = "stage_packet_not_current_selected_dispatch"
ARBITER_AUTHORITY_BOUNDARY = {
    "arbiter_surface": "currentness_projection_only",
    "can_write_domain_truth": False,
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
        if current_control_receipts.accepted_closeout_matches_identity(
            scanned_study,
            identity=candidate,
        ):
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="accepted_closeout_consumed_pending",
                    effect="suppress_provider_admission_pending",
                    evidence=_matching_accepted_closeout(scanned_study, identity=candidate),
                )
            )
            continue
        live_study = _mapping(live_studies_by_id.get(study_id)) if study_id is not None else {}
        live_attempt = _running_attempt_from_study(live_study)
        if live_attempt and provider_attempt_matches_identity(live_attempt, identity=candidate):
            decisions.append(
                _arbiter_decision(
                    candidate,
                    decision="running_identity_observed",
                    effect="suppress_provider_admission_pending",
                    evidence=live_attempt,
                )
            )
            continue
        weak_identity = _current_control_weak_provider_admission_identity(candidate)
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
        typed_blocker_precedence = _current_typed_blocker_precedence_evidence(
            scanned_study,
            identity=candidate,
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
        "active_stage_attempt_id": _non_empty_text(evidence.get("active_stage_attempt_id"))
        or _non_empty_text(evidence.get("stage_attempt_id")),
        "active_run_id": _non_empty_text(evidence.get("active_run_id")),
        "active_workflow_id": _non_empty_text(evidence.get("active_workflow_id")),
        "missing_identity_fields": _missing_identity_fields(evidence),
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
        ) and current_control_receipts.accepted_closeout_matches_candidate_identity(
            receipt,
            identity=identity,
        ):
            return receipt
    return {}


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
    progress_first = _live_attempt_from_progress_first_summary(study)
    if progress_first:
        return progress_first
    current_work_unit = _live_attempt_from_current_work_unit(study)
    if current_work_unit:
        return current_work_unit
    return {}


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
        study_id = _non_empty_text(candidate.get("study_id"))
        live_study = _mapping(live_studies_by_id.get(study_id)) if study_id is not None else {}
        live_attempt = _running_attempt_from_study(live_study)
        scanned_study = (
            _mapping((scanned_studies_by_id or {}).get(study_id)) if study_id is not None else {}
        )
        if _terminal_closeout_precedence_evidence(scanned_study, identity=candidate):
            continue
        if current_control_receipts.accepted_closeout_matches_identity(
            scanned_study,
            identity=candidate,
        ):
            continue
        if live_attempt and provider_attempt_matches_identity(live_attempt, identity=candidate):
            continue
        if _current_control_weak_provider_admission_identity(
            candidate
        ) and not _unconsumed_closeout_blocks_weak_identity_suppression(
            scanned_study,
            identity=candidate,
        ):
            continue
        if _current_typed_blocker_precedence_evidence(scanned_study, identity=candidate):
            continue
        pending.append(dict(candidate))
    return pending


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
                or _non_empty_text(typed_blocker.get("work_unit_id")),
                "work_unit_fingerprint": _non_empty_text(current.get("work_unit_fingerprint"))
                or _non_empty_text(current.get("action_fingerprint"))
                or _non_empty_text(typed_blocker.get("work_unit_fingerprint"))
                or _non_empty_text(typed_blocker.get("action_fingerprint")),
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
