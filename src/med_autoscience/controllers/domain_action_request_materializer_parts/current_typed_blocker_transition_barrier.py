from __future__ import annotations

import hashlib
from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.default_executor_action_policy import (
    request_output_surface_for_action_type,
)
from med_autoscience.controllers.domain_action_request_materializer_parts import (
    repair_progress_currentness,
)
from med_autoscience.runtime_control import owner_route as owner_route_part


READINESS_ACTION_TYPE = "complete_medical_paper_readiness_surface"
READINESS_BLOCKER_REASONS = frozenset(
    {
        "medical_paper_readiness_missing",
        "medical_paper_readiness_not_ready",
    }
)


def current_typed_blocker_barrier_for_consumed_transition(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any] | None,
    transition_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    return current_typed_blocker_barrier_for_actions(
        study=study,
        fresh_action=fresh_action,
        candidate_actions=transition_actions,
    )


def current_typed_blocker_barrier_for_actions(
    *,
    study: Mapping[str, Any],
    fresh_action: Mapping[str, Any] | None,
    candidate_actions: list[dict[str, Any]],
) -> dict[str, Any] | None:
    if not candidate_actions:
        return None
    if fresh_action is not None and (
        _text(fresh_action.get("action_type")) or ""
    ).startswith("current_execution_envelope_"):
        return dict(fresh_action)
    current_action = _mapping(study.get("current_executable_owner_action"))
    envelope = _mapping(study.get("current_execution_envelope"))
    if repair_progress_currentness.typed_blocker_allows_repair_progress_followup(
        envelope=envelope,
        current_action=current_action,
    ):
        return None
    current_work_unit = _mapping(study.get("current_work_unit"))
    work_unit_state = _mapping(current_work_unit.get("state"))
    stale_override = work_unit_state.get("stale_queue_or_handoff_can_override")
    if stale_override is True or _text(stale_override) == "true":
        return None
    work_unit_status = _text(current_work_unit.get("status"))
    state_kind = _text(work_unit_state.get("state_kind"))
    envelope_state_kind = _text(envelope.get("state_kind")) or _text(envelope.get("execution_state_kind"))
    if not (
        work_unit_status == "typed_blocker"
        or state_kind == "typed_blocker"
        or envelope_state_kind == "typed_blocker"
    ):
        return None
    blocker = (
        _mapping(work_unit_state.get("typed_blocker"))
        or _mapping(envelope.get("typed_blocker"))
        or current_work_unit
    )
    reason = (
        _text(blocker.get("blocker_id"))
        or _text(blocker.get("blocker_type"))
        or _text(blocker.get("reason"))
        or "typed_blocker"
    )
    owner = (
        _text(envelope.get("owner"))
        or _text(current_work_unit.get("owner"))
        or _text(blocker.get("owner"))
        or "MedAutoScience"
    )
    study_id = _text(study.get("study_id"))
    readiness_action = _readiness_blocker_owner_action(
        study=study,
        current_work_unit=current_work_unit,
        blocker=blocker,
        reason=reason,
        owner=owner,
        study_id=study_id,
    )
    if readiness_action is not None:
        return readiness_action
    return {
        "study_id": study_id,
        "quest_id": _text(study.get("quest_id")),
        "action_type": "current_execution_envelope_typed_blocker",
        "action_id": f"study-progress-current-execution-envelope::{study_id}::typed_blocker",
        "reason": reason,
        "owner": owner,
        "request_owner": owner,
        "recommended_owner": owner,
        "authority": "current_work_unit.typed_blocker",
        "source_surface": "current_work_unit",
        "source_ref": _text(blocker.get("source_ref")),
        "work_unit_id": _text(blocker.get("work_unit_id")) or _text(current_work_unit.get("work_unit_id")),
    }


def _readiness_blocker_owner_action(
    *,
    study: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    blocker: Mapping[str, Any],
    reason: str,
    owner: str,
    study_id: str | None,
) -> dict[str, Any] | None:
    if study_id is None:
        return None
    if owner != "MedAutoScience":
        return None
    if reason not in READINESS_BLOCKER_REASONS:
        return None
    action_type = _text(current_work_unit.get("action_type")) or _text(blocker.get("action_type"))
    work_unit_id = _text(blocker.get("work_unit_id")) or _text(current_work_unit.get("work_unit_id"))
    if action_type not in {READINESS_ACTION_TYPE, None} and work_unit_id != READINESS_ACTION_TYPE:
        return None
    if work_unit_id != READINESS_ACTION_TYPE:
        return None
    source_ref = (
        _text(blocker.get("source_ref"))
        or _text(blocker.get("typed_blocker_ref"))
        or _text(blocker.get("latest_owner_answer_ref"))
        or _text(current_work_unit.get("source_ref"))
        or "current_work_unit.typed_blocker"
    )
    owner_route = _readiness_owner_route(
        study=study,
        current_work_unit=current_work_unit,
        blocker=blocker,
        reason=reason,
        study_id=study_id,
        source_ref=source_ref,
    )
    payload = {
        "study_id": study_id,
        "quest_id": _text(study.get("quest_id")),
        "action_type": READINESS_ACTION_TYPE,
        "action_id": f"current-readiness-typed-blocker::{study_id}",
        "reason": reason,
        "owner": "MedAutoScience",
        "request_owner": "MedAutoScience",
        "recommended_owner": "MedAutoScience",
        "next_executable_owner": "MedAutoScience",
        "authority": "current_work_unit.typed_blocker",
        "required_output_surface": request_output_surface_for_action_type(READINESS_ACTION_TYPE),
        "source_surface": "current_work_unit",
        "source_ref": source_ref,
        "work_unit_id": READINESS_ACTION_TYPE,
        "next_work_unit": READINESS_ACTION_TYPE,
        "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "action_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
        "owner_route": owner_route,
        "handoff_packet": {
            "action_type": READINESS_ACTION_TYPE,
            "request_owner": "MedAutoScience",
            "recommended_owner": "MedAutoScience",
            "next_executable_owner": "MedAutoScience",
            "source_surface": "current_work_unit",
            "source_ref": source_ref,
            "work_unit_id": READINESS_ACTION_TYPE,
            "work_unit_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
            "action_fingerprint": _text(owner_route.get("work_unit_fingerprint")),
            "owner_route": owner_route,
            "idempotency_key": _text(owner_route.get("idempotency_key")),
        },
    }
    return {key: value for key, value in payload.items() if value is not None}


def _readiness_owner_route(
    *,
    study: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    blocker: Mapping[str, Any],
    reason: str,
    study_id: str,
    source_ref: str,
) -> dict[str, Any]:
    currentness = _readiness_currentness_basis(
        study=study,
        current_work_unit=current_work_unit,
        blocker=blocker,
        study_id=study_id,
        source_ref=source_ref,
    )
    work_unit_fingerprint = str(currentness["work_unit_fingerprint"])
    truth_epoch = str(currentness["truth_epoch"])
    runtime_health_epoch = str(currentness["runtime_health_epoch"])
    source_fingerprint = _source_fingerprint(
        study_id=study_id,
        reason=reason,
        source_ref=source_ref,
        truth_epoch=truth_epoch,
        runtime_health_epoch=runtime_health_epoch,
    )
    route = {
        "surface": "domain_route_owner_route",
        "schema_version": 2,
        "study_id": study_id,
        "quest_id": _text(study.get("quest_id")),
        "truth_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_fingerprint": work_unit_fingerprint,
        "failure_signature": reason,
        "trace_id": f"owner-route-trace::{study_id}::{READINESS_ACTION_TYPE}::{_short_digest(source_fingerprint)}",
        "route_epoch": truth_epoch,
        "source_fingerprint": source_fingerprint,
        "current_owner": "mas_controller",
        "next_owner": "MedAutoScience",
        "owner_reason": reason,
        "active_run_id": _text(study.get("active_run_id")),
        "allowed_actions": [READINESS_ACTION_TYPE],
        "blocked_actions": [],
        "idempotency_scope": "study_quest_owner_route",
        "source_refs": {
            "study_truth_epoch": truth_epoch,
            "runtime_health_epoch": runtime_health_epoch,
            "work_unit_id": READINESS_ACTION_TYPE,
            "work_unit_fingerprint": work_unit_fingerprint,
            "blocked_reason": reason,
            "source_ref": source_ref,
            "owner_route_currentness_basis": currentness,
        },
        "idempotency_key": (
            f"owner-route::{study_id}::{truth_epoch}::MedAutoScience::{reason}::"
            f"{_short_digest(work_unit_fingerprint)}"
        ),
    }
    return owner_route_part.ensure_owner_route_v2(route)


def _readiness_currentness_basis(
    *,
    study: Mapping[str, Any],
    current_work_unit: Mapping[str, Any],
    blocker: Mapping[str, Any],
    study_id: str,
    source_ref: str,
) -> dict[str, str]:
    existing_basis = _mapping(current_work_unit.get("currentness_basis"))
    truth = _mapping(study.get("study_truth_snapshot"))
    runtime = _mapping(study.get("runtime_health_snapshot"))
    truth_epoch = (
        _text(current_work_unit.get("truth_epoch"))
        or _text(existing_basis.get("truth_epoch"))
        or _text(study.get("truth_epoch"))
        or _text(truth.get("truth_epoch"))
        or f"current-readiness-typed-blocker::{study_id}"
    )
    runtime_health_epoch = (
        _text(current_work_unit.get("runtime_health_epoch"))
        or _text(existing_basis.get("runtime_health_epoch"))
        or _text(study.get("runtime_health_epoch"))
        or _text(runtime.get("runtime_health_epoch"))
        or truth_epoch
    )
    basis_work_unit_id = _text(existing_basis.get("work_unit_id"))
    reusable_fingerprint = (
        _text(current_work_unit.get("work_unit_fingerprint"))
        or _text(blocker.get("work_unit_fingerprint"))
        or (
            _text(existing_basis.get("work_unit_fingerprint"))
            if basis_work_unit_id == READINESS_ACTION_TYPE
            else None
        )
    )
    work_unit_fingerprint = reusable_fingerprint or (
        "current-readiness-typed-blocker::"
        f"{study_id}::{_short_digest(source_ref, truth_epoch, runtime_health_epoch)}"
    )
    return {
        "truth_epoch": truth_epoch,
        "runtime_health_epoch": runtime_health_epoch,
        "work_unit_id": READINESS_ACTION_TYPE,
        "work_unit_fingerprint": work_unit_fingerprint,
    }


def _source_fingerprint(
    *,
    study_id: str,
    reason: str,
    source_ref: str,
    truth_epoch: str,
    runtime_health_epoch: str,
) -> str:
    return (
        f"current-readiness-typed-blocker-source::{study_id}::{reason}::"
        f"{_short_digest(source_ref, truth_epoch, runtime_health_epoch)}"
    )


def _short_digest(*values: object) -> str:
    joined = "\n".join(str(value) for value in values)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "current_typed_blocker_barrier_for_actions",
    "current_typed_blocker_barrier_for_consumed_transition",
]
