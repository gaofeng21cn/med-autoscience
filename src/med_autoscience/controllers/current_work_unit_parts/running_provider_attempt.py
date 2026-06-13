from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.current_work_unit_parts.action_projection_fields import (
    action_fingerprint,
    action_type,
    work_unit_fingerprint,
    work_unit_id,
)
from med_autoscience.controllers.current_work_unit_parts.policy_constants import (
    LIVE_ATTEMPT_SUPERSEDED_BLOCKERS,
    OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE,
    RUNNING_HEALTH_VALUES,
    TERMINAL_CLOSEOUT_STATUSES,
)
from med_autoscience.controllers.current_work_unit_parts.primitives import (
    mapping,
    text,
    text_items,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)


def strict_running_provider_attempt(
    *,
    live_provider_attempt: Mapping[str, Any] | None,
    provider_running_proof: Mapping[str, Any] | None,
    runtime_health: Mapping[str, Any],
    owner: str | None,
) -> dict[str, Any] | None:
    attempt = mapping(provider_running_proof) or mapping(live_provider_attempt)
    if attempt.get("running_provider_attempt") is not True:
        return None
    if attempt_has_matching_terminal_closeout(attempt):
        return None
    active_stage_attempt_id = text(attempt.get("active_stage_attempt_id"))
    active_run_id = text(attempt.get("active_run_id"))
    active_workflow_id = text(attempt.get("active_workflow_id"))
    if active_stage_attempt_id is None and active_run_id is None and active_workflow_id is None:
        return None
    health = mapping(attempt.get("runtime_health")) or runtime_health
    if health.get("strict_live") is False:
        return None
    if not has_running_health(health):
        return None
    return {
        **attempt,
        "owner": text(owner) or text(attempt.get("next_owner")) or text(attempt.get("owner")),
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_run_id": active_run_id,
        "active_workflow_id": active_workflow_id,
        "runtime_health": health,
    }


def has_running_health(health: Mapping[str, Any]) -> bool:
    values = {
        text(health.get("health_status")),
        text(health.get("runtime_liveness_status")),
        text(health.get("provider_status")),
        text(health.get("attempt_state")),
        text(health.get("status")),
    }
    return bool(values.intersection(RUNNING_HEALTH_VALUES))


def running_work_unit_id(
    running_attempt: Mapping[str, Any],
    *,
    currentness_basis: Mapping[str, Any] | None = None,
    action: Mapping[str, Any] | None = None,
) -> str | None:
    health = mapping(running_attempt.get("runtime_health"))
    basis = mapping(currentness_basis)
    action_payload = mapping(action)
    action_source = text(action_payload.get("source")) or text(action_payload.get("source_surface"))
    action_work_unit = (
        None
        if action_source == OPL_CURRENT_CONTROL_ACTION_QUEUE_SOURCE
        else work_unit_id(basis.get("work_unit_id"))
    )
    return (
        work_unit_id(running_attempt.get("work_unit_id"))
        or work_unit_id(running_attempt.get("next_work_unit"))
        or work_unit_id(health.get("work_unit_id"))
        or action_work_unit
        or text(running_attempt.get("action_type"))
    )


def provider_attempt_proof_state(running_attempt: Mapping[str, Any]) -> dict[str, Any]:
    health = mapping(running_attempt.get("runtime_health"))
    return {
        "running_provider_attempt": True,
        "active_stage_attempt_id": text(running_attempt.get("active_stage_attempt_id")),
        "active_run_id": text(running_attempt.get("active_run_id")),
        "active_workflow_id": text(running_attempt.get("active_workflow_id")),
        "work_unit_id": work_unit_id(running_attempt.get("work_unit_id"))
        or work_unit_id(health.get("work_unit_id")),
        "next_work_unit": work_unit_id(running_attempt.get("next_work_unit"))
        or work_unit_id(health.get("next_work_unit")),
        "runtime_health": mapping(running_attempt.get("runtime_health")) or None,
    }


def running_required_output_contract(running_attempt: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "accepted_terminal_results": ["owner_receipt", "typed_blocker", "provider_closeout"],
        "provider_attempt_running_proof_required": True,
        "strict_running_proof_observed": True,
        "owner_receipt_or_typed_blocker_required_for_completion": True,
        "active_stage_attempt_id": text(running_attempt.get("active_stage_attempt_id")),
        "active_workflow_id": text(running_attempt.get("active_workflow_id")),
    }


def running_attempt_can_supersede_blocker(blocker: Mapping[str, Any] | None) -> bool:
    payload = mapping(blocker)
    if not payload:
        return True
    return bool(blocker_reason_values(payload).intersection(LIVE_ATTEMPT_SUPERSEDED_BLOCKERS))


def typed_blocker_is_terminal_stop_loss(blocker: Mapping[str, Any]) -> bool:
    payload = mapping(blocker)
    if not payload:
        return False
    closeout_like = {
        "typed_blocker": payload,
        "blocked_reason": text(payload.get("blocked_reason"))
        or text(payload.get("blocker_type"))
        or text(payload.get("blocker_kind"))
        or text(payload.get("reason")),
        "typed_blocker_reason": text(payload.get("blocker_type"))
        or text(payload.get("blocker_kind"))
        or text(payload.get("reason")),
        "stage_closeout_status": text(payload.get("terminal_closeout_status")),
        "stage_closeout_outcome": text(payload.get("terminal_closeout_outcome")),
        "paper_stage_log": mapping(payload.get("paper_stage_log")),
    }
    return is_anti_loop_stop_loss_closeout(closeout_like)


def blocker_reason_values(blocker: Mapping[str, Any]) -> set[str]:
    values = {
        item
        for value in (
            blocker.get("blocker_type"),
            blocker.get("blocker_id"),
            blocker.get("blocked_reason"),
            blocker.get("reason"),
            blocker.get("terminal_closeout_status"),
            blocker.get("terminal_closeout_outcome"),
            blocker.get("progress_delta_classification"),
        )
        if (item := text(value)) is not None
    }
    return values | {
        superseded
        for value in values
        for superseded in LIVE_ATTEMPT_SUPERSEDED_BLOCKERS
        if superseded in value
    }


def running_attempt_satisfies_stage_owner_answer(
    *,
    running_attempt: Mapping[str, Any],
    owner_answer_action: Mapping[str, Any],
) -> bool:
    expected_stage_id = text(owner_answer_action.get("stage_id"))
    expected_work_unit = text(owner_answer_action.get("work_unit_id"))
    expected_fingerprint = text(owner_answer_action.get("work_unit_fingerprint"))
    expected_owner_answer_ref = text(owner_answer_action.get("latest_owner_answer_ref"))
    expected_lineage_ref = text(
        mapping(owner_answer_action.get("owner_route_currentness_basis")).get("lineage_ref")
    )
    attempt_stage_id = text(running_attempt.get("stage_id"))
    if expected_stage_id is not None and attempt_stage_id != expected_stage_id:
        return False
    attempt_lineage_ref = text(running_attempt.get("lineage_ref")) or text(
        mapping(running_attempt.get("runtime_health")).get("lineage_ref")
    )
    if expected_lineage_ref is not None and attempt_lineage_ref != expected_lineage_ref:
        return False
    attempt_work_unit = (
        text(running_attempt.get("work_unit_id"))
        or text(running_attempt.get("next_work_unit"))
        or text(mapping(running_attempt.get("runtime_health")).get("work_unit_id"))
    )
    if expected_work_unit is not None and attempt_work_unit != expected_work_unit:
        return False
    if expected_fingerprint is not None:
        attempt_fingerprints = {
            item
            for value in (
                running_attempt.get("work_unit_fingerprint"),
                running_attempt.get("action_fingerprint"),
                running_attempt.get("lineage_ref"),
                mapping(running_attempt.get("runtime_health")).get("work_unit_fingerprint"),
            )
            if (item := text(value)) is not None
        }
        if expected_fingerprint not in attempt_fingerprints:
            return False
    observed_answer_refs = stage_owner_answer_refs(running_attempt)
    if expected_owner_answer_ref is None:
        return False
    if expected_owner_answer_ref not in observed_answer_refs:
        return False
    return any(
        ref in observed_answer_refs
        for ref in text_items(owner_answer_action.get("acceptance_refs")) + [expected_owner_answer_ref]
    )


def running_attempt_matches_current_action(
    *,
    running_attempt: Mapping[str, Any],
    action: Mapping[str, Any] | None,
) -> bool:
    action_payload = mapping(action)
    if not action_payload:
        return True
    expected_action_type = action_type(action_payload)
    expected_work_unit = work_unit_id(action_payload.get("work_unit_id")) or work_unit_id(
        action_payload.get("next_work_unit")
    )
    action_source_refs = mapping(action_payload.get("source_refs"))
    action_basis = (
        mapping(action_payload.get("owner_route_currentness_basis"))
        or mapping(action_payload.get("currentness_basis"))
        or mapping(action_source_refs.get("owner_route_currentness_basis"))
    )
    expected_fingerprint = work_unit_fingerprint(action_payload, currentness_basis=action_basis)
    running_health = mapping(running_attempt.get("runtime_health"))
    comparable_identity_observed = False
    if expected_action_type is not None:
        running_action_types = {
            item
            for value in (
                running_attempt.get("action_type"),
                running_health.get("action_type"),
            )
            if (item := text(value)) is not None
        }
        comparable_identity_observed = comparable_identity_observed or bool(running_action_types)
        if running_action_types and expected_action_type not in running_action_types:
            return False
    if expected_work_unit is not None:
        running_work_units = {
            item
            for value in (
                running_attempt.get("work_unit_id"),
                running_attempt.get("next_work_unit"),
                running_health.get("work_unit_id"),
                running_health.get("next_work_unit"),
            )
            if (item := work_unit_id(value)) is not None
        }
        comparable_identity_observed = comparable_identity_observed or bool(running_work_units)
        if running_work_units and expected_work_unit not in running_work_units:
            return False
    if expected_fingerprint is not None:
        running_fingerprints = {
            item
            for value in (
                running_attempt.get("work_unit_fingerprint"),
                running_attempt.get("action_fingerprint"),
                running_attempt.get("lineage_ref"),
                running_health.get("work_unit_fingerprint"),
                running_health.get("action_fingerprint"),
                running_health.get("lineage_ref"),
            )
            if (item := text(value)) is not None
        }
        comparable_identity_observed = comparable_identity_observed or bool(running_fingerprints)
        if running_fingerprints and expected_fingerprint not in running_fingerprints:
            return False
    if (
        expected_action_type is not None
        or expected_work_unit is not None
        or expected_fingerprint is not None
    ) and not comparable_identity_observed:
        return False
    return True


def stage_owner_answer_refs(payload: Mapping[str, Any]) -> set[str]:
    refs: set[str] = set()
    for key in (
        "domain_owner_receipt_ref",
        "quality_gate_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_evidence_ref",
    ):
        if ref := text(payload.get(key)):
            refs.add(ref)
    for key in (
        "domain_owner_receipt_refs",
        "quality_gate_receipt_refs",
        "typed_blocker_refs",
        "human_gate_refs",
        "route_back_evidence_refs",
    ):
        refs.update(text_items(payload.get(key)))
    runtime_health = mapping(payload.get("runtime_health"))
    if runtime_health:
        refs.update(stage_owner_answer_refs(runtime_health))
    return refs


def running_attempt_invalidated_by_progress(progress: Mapping[str, Any]) -> bool:
    runtime_refs = mapping(progress.get("opl_runtime_refs"))
    if runtime_refs.get("strict_live") is not False:
        return False
    if text(runtime_refs.get("active_run_id")) is not None:
        return False
    auto_parked = mapping(progress.get("auto_runtime_parked"))
    if auto_parked.get("superseded_by_current_owner_action") is not True:
        return False
    return text(runtime_refs.get("runtime_liveness_status")) in {
        "unknown",
        "none",
        "not_live",
        "stale",
        "parked",
    }


def attempt_has_matching_terminal_closeout(attempt: Mapping[str, Any]) -> bool:
    terminal = mapping(attempt.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = stage_attempt_id_from_handoff(attempt)
    terminal_attempt_id = text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = text(terminal.get("status"))
    if status in TERMINAL_CLOSEOUT_STATUSES:
        return True
    return text(terminal.get("source_path")) is not None and text(terminal.get("record_path")) is not None


def stage_attempt_id_from_handoff(handoff: Mapping[str, Any]) -> str | None:
    if value := text(handoff.get("active_stage_attempt_id")):
        return value
    active_run_id = text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


__all__ = [
    "provider_attempt_proof_state",
    "running_attempt_can_supersede_blocker",
    "running_attempt_invalidated_by_progress",
    "running_attempt_matches_current_action",
    "running_attempt_satisfies_stage_owner_answer",
    "running_required_output_contract",
    "running_work_unit_id",
    "strict_running_provider_attempt",
    "typed_blocker_is_terminal_stop_loss",
]
