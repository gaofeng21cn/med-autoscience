from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.current_work_unit_parts.stage_packet_blockers import (
    is_selected_dispatch_stage_packet_blocker as _is_selected_dispatch_stage_packet_blocker,
)
from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    provider_admission_opl_transition_readback,
    required_opl_transition_readback_shape,
)
from med_autoscience.controllers.provider_admission_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission_parts.provider_admission import (
    provider_attempt_matches_identity,
    study_has_running_provider_attempt,
)
from med_autoscience.controllers.provider_admission_parts import (
    provider_admission_current_control_receipts as current_control_receipts,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_actions import (
    accepted_owner_gate_admission_matches_selected_dispatch_blocker,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_arbiter_typed_blocker_evidence import (
    _accepted_closeout_currentness_basis,
    _current_control_weak_provider_admission_identity,
    _current_typed_blocker_precedence_evidence,
    _currentness_basis_conflicts,
    _exact_owner_refs_closeout_matches_candidate,
    _provider_admission_readback_overrides_blocking_closeout,
    _request_only_transition_can_bypass_current_typed_blocker,
    _unconsumed_closeout_blocks_weak_identity_suppression,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_report_closeout_identity import (
    closeout_core_identity_matches_candidate as _closeout_core_identity_matches_candidate,
)
from med_autoscience.controllers.study_progress_parts.paper_autonomy_supervisor_decision import (
    provider_admission_supervisor_gate,
)

ACCEPTED_OWNER_GATE_DECISION_SOURCE = "paper_recovery_state.accepted_owner_gate_decision"


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
        ) and not _accepted_owner_gate_transition_request_candidate(
            candidate
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
            if not _request_only_transition_can_bypass_paper_recovery_block(
                candidate,
                block=paper_recovery_block,
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
            if (
                not request_only_transition
                or _paper_recovery_block_is_hard_blocker(paper_recovery_block)
                or not (
                    _request_only_transition_can_bypass_current_typed_blocker(
                        scanned_study,
                        candidate=candidate,
                    )
                    or _request_only_transition_materializes_accepted_owner_gate_admission(
                        scanned_study,
                        identity=candidate,
                        recovery=_mapping(scanned_study.get("paper_recovery_state")),
                    )
                )
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


def _paper_recovery_block_requires_supervisor_decision_readback(block: Mapping[str, Any]) -> bool:
    supervisor_decision = _mapping(block.get("supervisor_decision"))
    next_safe_action = _mapping(supervisor_decision.get("next_safe_action"))
    return (
        _non_empty_text(supervisor_decision.get("decision"))
        == "opl_supervisor_decision_readback_required"
        or _non_empty_text(next_safe_action.get("kind"))
        == "opl_supervisor_decision_readback_required"
    )


def _request_only_transition_can_bypass_paper_recovery_block(
    candidate: Mapping[str, Any],
    *,
    block: Mapping[str, Any],
) -> bool:
    if not _request_only_transition_request_candidate(candidate):
        return False
    if _paper_recovery_block_is_hard_blocker(block):
        return False
    if _accepted_owner_gate_transition_request_candidate(candidate):
        return True
    next_safe_action = _mapping(block.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) == "materialize_successor_owner_action":
        return any(
            _identity_matches(source, identity=candidate)
            for source in _recovery_successor_identity_sources(block)
        )
    return _provider_admission_candidate_materializes_recovery_action(
        candidate,
        recovery=block,
        supervisor_decision=_mapping(block.get("supervisor_decision")),
    )


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


def _accepted_owner_gate_transition_request_candidate(candidate: Mapping[str, Any]) -> bool:
    if not _request_only_transition_request_candidate(candidate):
        return False
    if (
        _non_empty_text(candidate.get("source"))
        != "opl_current_control_state.study_current_executable_owner_action"
    ):
        return False
    basis = _mapping(candidate.get("currentness_basis"))
    return (
        _non_empty_text(basis.get("source")) == ACCEPTED_OWNER_GATE_DECISION_SOURCE
        or _non_empty_text(basis.get("mas_owner_action_source"))
        == ACCEPTED_OWNER_GATE_DECISION_SOURCE
        or _non_empty_text(candidate.get("mas_owner_action_source"))
        == ACCEPTED_OWNER_GATE_DECISION_SOURCE
        or _non_empty_text(candidate.get("authority")) == ACCEPTED_OWNER_GATE_DECISION_SOURCE
    )


def _dry_run_request_only_transition_request_candidate(candidate: Mapping[str, Any]) -> bool:
    return (
        _request_only_transition_request_candidate(candidate)
        and candidate.get("same_tick_materialized_provider_admission") is True
        and _non_empty_text(candidate.get("same_tick_materialization_source")) == "dry_run_preview"
    )


def _candidate_requires_strong_current_control_identity(candidate: Mapping[str, Any]) -> bool:
    if provider_admission_opl_transition_readback(candidate):
        return False
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


def _opl_transition_readback_required_evidence(
    candidate: Mapping[str, Any],
    *,
    weak_identity: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if provider_admission_opl_transition_readback(candidate):
        return {}
    transition_request = _mapping(candidate.get("opl_domain_progress_transition_request"))
    if not transition_request:
        transition_request = _mapping(
            _mapping(candidate.get("paper_progress_policy_result")).get(
                "opl_domain_progress_transition_request"
            )
        )
    if not transition_request and not weak_identity:
        return {}
    required_shape = required_opl_transition_readback_shape()
    return {
        "status": "NonAdvancingApply",
        "blocked_reason": "opl_transition_readback_required",
        "candidate_has_opl_transition_readback": bool(candidate_opl_transition_readback(candidate)),
        "candidate_has_provider_bound_opl_transition_readback": False,
        "weak_provider_admission_identity": dict(weak_identity) if weak_identity else None,
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
    if provider_admission_opl_transition_readback(identity):
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
    if _request_only_transition_materializes_accepted_owner_gate_admission(
        study,
        identity=identity,
        recovery=recovery,
    ):
        return {}
    if _request_only_transition_request_candidate(
        identity
    ) and _request_only_transition_matches_recovery_successor(
        identity,
        recovery={
            **dict(recovery),
            "current_work_unit": _mapping(study.get("current_work_unit")),
        },
    ):
        return {}
    if _non_empty_text(recovery.get("phase")) == "admission_pending" and (
        next_safe_action.get("provider_admission_requires_opl_runtime_result") is True
        and next_safe_action.get("mas_can_authorize_provider_admission") is False
        and _non_empty_text(next_safe_action.get("kind"))
        == "consume_opl_provider_admission_readback"
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


def _request_only_transition_materializes_accepted_owner_gate_admission(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
    recovery: Mapping[str, Any],
) -> bool:
    if not _accepted_owner_gate_transition_request_candidate(identity):
        return False
    if not accepted_owner_gate_admission_matches_selected_dispatch_blocker(
        study=study,
        recovery=recovery,
    ):
        return False
    return _paper_recovery_state_matches_identity(study, recovery=recovery, identity=identity)


def _request_only_transition_matches_recovery_successor(
    identity: Mapping[str, Any],
    *,
    recovery: Mapping[str, Any],
) -> bool:
    if _non_empty_text(recovery.get("phase")) != "owner_action_ready":
        return False
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    if _non_empty_text(next_safe_action.get("kind")) != "materialize_successor_owner_action":
        return False
    successor = _mapping(next_safe_action.get("successor_owner_action"))
    if successor:
        return _identity_matches(successor, identity=identity)
    return any(
        _identity_matches(source, identity=identity)
        for source in _recovery_successor_identity_sources(recovery)
    )


def _recovery_successor_identity_sources(recovery: Mapping[str, Any]) -> list[Mapping[str, Any]]:
    next_safe_action = _mapping(recovery.get("next_safe_action"))
    sources: list[Mapping[str, Any]] = []
    successor = _mapping(next_safe_action.get("successor_owner_action"))
    if successor:
        sources.append(successor)
    current_work_unit = _mapping(recovery.get("current_work_unit"))
    if current_work_unit:
        sources.append(current_work_unit)
    recovery_identity = {
        "action_type": _non_empty_text(recovery.get("action_type"))
        or _non_empty_text(next_safe_action.get("action_type")),
        "work_unit_id": _non_empty_text(recovery.get("work_unit_id"))
        or _non_empty_text(next_safe_action.get("work_unit_id"))
        or _non_empty_text(next_safe_action.get("next_work_unit")),
        "work_unit_fingerprint": _non_empty_text(recovery.get("work_unit_fingerprint"))
        or _non_empty_text(next_safe_action.get("work_unit_fingerprint"))
        or _non_empty_text(recovery.get("action_fingerprint"))
        or _non_empty_text(next_safe_action.get("action_fingerprint")),
    }
    if any(recovery_identity.values()):
        sources.append(recovery_identity)
    return sources


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
        _is_selected_dispatch_stage_packet_blocker(_non_empty_text(evidence.get("blocker_type")))
        and _accepted_owner_gate_transition_request_candidate(candidate)
    ):
        return {}
    if _request_only_transition_materializes_accepted_owner_gate_admission(
        study,
        identity=candidate,
        recovery=_mapping(study.get("paper_recovery_state")),
    ):
        return {}
    return evidence
