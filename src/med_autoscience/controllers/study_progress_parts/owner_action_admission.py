from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .paper_autonomy_supervisor_decision import provider_admission_supervisor_gate


def build_owner_action_admission_projection(
    *,
    payload: Mapping[str, Any],
    current_action: Mapping[str, Any],
    handoff: Mapping[str, Any],
    stage_progress_log: Mapping[str, Any],
    latest_terminal_stage_log: Mapping[str, Any],
) -> dict[str, Any] | None:
    owner = _text(current_action.get("next_owner"))
    work_unit_id = _text(current_action.get("work_unit_id"))
    allowed_actions = _text_list(current_action.get("allowed_actions"))
    if owner is None and work_unit_id is None and not allowed_actions:
        return None
    blocked_by = _hard_gate_blockers(payload)
    hard_gate_reasons = _hard_gate_reasons(blocked_by)
    hard_gate_blocked = bool(hard_gate_reasons)
    provider_attempt_proof = provider_attempt_proof_for_current_action(
        handoff=handoff,
        current_action=current_action,
    )
    running_proven = bool(provider_attempt_proof)
    candidate_present = _provider_admission_candidate_present(
        payload=payload,
        handoff=handoff,
        current_action=current_action,
    )
    admission_requested = not hard_gate_blocked
    start_requested = admission_requested and (candidate_present or running_proven)
    blocked_reason = blocked_by or None
    if admission_requested and not start_requested:
        blocked_reason = "provider_admission_candidate_absent"
    return {
        "surface_kind": "current_executable_owner_action_admission",
        "schema_version": 1,
        "source": "progress_first_monitoring.current_executable_owner_action",
        "admission_requested": admission_requested,
        "admission_pending": start_requested and not running_proven,
        "provider_attempt_start_requested": start_requested,
        "provider_attempt_started": running_proven,
        "provider_attempt_running_proven": running_proven,
        "provider_attempt_proof": provider_attempt_proof,
        "candidate_present": candidate_present,
        "hard_gate_blocked": hard_gate_blocked,
        "hard_gate_reasons": hard_gate_reasons,
        "blocked_by": blocked_reason,
        "next_owner": owner,
        "work_unit_id": work_unit_id,
        "allowed_actions": allowed_actions,
        "admission_policy": "hard_gate_only_progress_first",
        "provider_attempt_owner": _text(handoff.get("next_owner")) or owner or "one-person-lab",
        "observability_diagnostics": _observability_diagnostics(
            stage_progress_log=stage_progress_log,
            latest_terminal_stage_log=latest_terminal_stage_log,
        ),
        "authority_boundary": {
            "projection_only": True,
            "can_write_runtime_owned_surfaces": False,
            "can_write_paper_or_package": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_ready": False,
        },
    }


def _provider_admission_candidate_present(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    if provider_attempt_proof_for_current_action(
        handoff=handoff,
        current_action=current_action,
    ):
        return True
    if _matching_provider_admission_candidates(
        payload.get("provider_admission_candidates"),
        current_action=current_action,
    ):
        return True
    if _matching_provider_admission_candidates(
        handoff.get("provider_admission_candidates"),
        current_action=current_action,
    ):
        return True
    return any(
        _action_queue_item_is_provider_admission_candidate(item)
        and _candidate_matches_current_action(item, current_action=current_action)
        for item in handoff.get("action_queue") or []
        if isinstance(item, Mapping)
    )


def _action_queue_item_is_provider_admission_candidate(item: Mapping[str, Any]) -> bool:
    if _text(item.get("authority")) == "mas_provider_admission_identity":
        return True
    if item.get("provider_attempt_or_lease_required") is True:
        return True
    if _text(item.get("execution_status")) == "handoff_ready":
        return True
    return _text(item.get("source_surface")) == "mas_opl_runtime_owner_handoff.provider_admission_identity"


def _matching_provider_admission_candidates(
    value: object,
    *,
    current_action: Mapping[str, Any],
) -> list[dict[str, Any]]:
    return [
        dict(item)
        for item in value or []
        if isinstance(item, Mapping)
        and _candidate_matches_current_action(item, current_action=current_action)
    ]


def _candidate_matches_current_action(
    candidate: Mapping[str, Any],
    *,
    current_action: Mapping[str, Any],
) -> bool:
    current_owner = _text(current_action.get("next_owner")) or _text(current_action.get("owner"))
    candidate_owner = (
        _text(candidate.get("next_executable_owner"))
        or _text(candidate.get("next_owner"))
        or _text(candidate.get("owner"))
    )
    if current_owner is not None and candidate_owner is not None and candidate_owner != current_owner:
        return False
    current_actions = set(_text_list(current_action.get("allowed_actions")))
    if action_type := _text(current_action.get("action_type")):
        current_actions.add(action_type)
    candidate_action = _text(candidate.get("action_type"))
    if current_actions and candidate_action is not None and candidate_action not in current_actions:
        return False
    current_work_unit = _work_unit_text(current_action.get("work_unit_id")) or _work_unit_text(
        current_action.get("next_work_unit")
    )
    candidate_work_unit = _work_unit_text(candidate.get("work_unit_id")) or _work_unit_text(
        candidate.get("next_work_unit")
    )
    if (
        current_work_unit is not None
        and candidate_work_unit is not None
        and candidate_work_unit != current_work_unit
    ):
        return False
    current_identity = _current_action_identity_values(current_action)
    candidate_identity = _current_action_identity_values(candidate)
    for key in ("work_unit_fingerprint", "action_fingerprint"):
        current_value = current_identity.get(key)
        candidate_value = candidate_identity.get(key)
        if current_value is not None and candidate_value is not None and candidate_value != current_value:
            return False
    return True


def provider_attempt_proof_for_current_action(
    *,
    handoff: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> dict[str, Any] | None:
    provider_attempt_proof = _provider_attempt_proof(handoff)
    if provider_attempt_proof is None:
        return None
    if not _provider_attempt_matches_current_action(handoff=handoff, current_action=current_action):
        return None
    return provider_attempt_proof


def _provider_attempt_proof(handoff: Mapping[str, Any]) -> dict[str, Any] | None:
    if handoff.get("running_provider_attempt") is not True:
        return None
    if _handoff_has_matching_terminal_closeout(handoff):
        return None
    active_stage_attempt_id = _text(handoff.get("active_stage_attempt_id"))
    active_run_id = _text(handoff.get("active_run_id"))
    active_workflow_id = _text(handoff.get("active_workflow_id"))
    if active_stage_attempt_id is None and active_run_id is None and active_workflow_id is None:
        return None
    return {
        "running_provider_attempt": True,
        "active_stage_attempt_id": active_stage_attempt_id,
        "active_run_id": active_run_id,
        "active_workflow_id": active_workflow_id,
    }


def _provider_attempt_matches_current_action(
    *,
    handoff: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    queue_item = _first_action_queue_item(handoff.get("action_queue"))
    current_owner = _text(current_action.get("next_owner")) or _text(current_action.get("owner"))
    current_actions = set(_text_list(current_action.get("allowed_actions")))
    if action_type := _text(current_action.get("action_type")):
        current_actions.add(action_type)
    current_work_unit = _work_unit_text(current_action.get("work_unit_id")) or _work_unit_text(
        current_action.get("next_work_unit")
    )

    owner_candidates = set(
        _dedupe_text(
            [
                handoff.get("next_owner"),
                handoff.get("owner"),
                queue_item.get("next_owner"),
                queue_item.get("owner"),
                queue_item.get("recommended_owner"),
                _mapping(queue_item.get("owner_pickup")).get("owner"),
            ]
        )
    )
    action_candidates = set(
        _dedupe_text(
            [
                handoff.get("controller_action"),
                handoff.get("action_type"),
                *_text_list(handoff.get("allowed_actions")),
                queue_item.get("controller_action"),
                queue_item.get("action_type"),
                *_text_list(queue_item.get("allowed_actions")),
            ]
        )
    )
    work_unit_candidates = set(
        _dedupe_text(
            [
                _work_unit_text(handoff.get("work_unit_id")),
                _work_unit_text(handoff.get("next_work_unit")),
                _work_unit_text(queue_item.get("work_unit_id")),
                _work_unit_text(queue_item.get("next_work_unit")),
            ]
        )
    )

    if current_owner is not None and current_owner not in owner_candidates:
        return False
    if current_actions and not current_actions.intersection(action_candidates):
        return False
    if current_work_unit is not None and current_work_unit not in work_unit_candidates:
        return False
    if not _provider_attempt_currentness_matches_current_action(
        handoff=handoff,
        queue_item=queue_item,
        current_action=current_action,
    ):
        return False
    return True


def _provider_attempt_currentness_matches_current_action(
    *,
    handoff: Mapping[str, Any],
    queue_item: Mapping[str, Any],
    current_action: Mapping[str, Any],
) -> bool:
    current_identity = _current_action_identity_values(current_action)
    attempt_identities = [
        _current_action_identity_values(handoff),
        _current_action_identity_values(queue_item),
    ]
    for key in ("work_unit_fingerprint", "action_fingerprint"):
        current_value = current_identity.get(key)
        if current_value is None:
            continue
        if current_value not in {
            attempt_identity.get(key)
            for attempt_identity in attempt_identities
            if attempt_identity.get(key) is not None
        }:
            return False
    current_basis = current_identity.get("owner_route_currentness_basis")
    if current_basis:
        matching_basis = [
            attempt_identity.get("owner_route_currentness_basis")
            for attempt_identity in attempt_identities
            if attempt_identity.get("owner_route_currentness_basis")
        ]
        if not any(_currentness_basis_matches(current_basis, basis) for basis in matching_basis):
            return False
    return True


def _current_action_identity_values(value: Mapping[str, Any]) -> dict[str, Any]:
    basis = _mapping(value.get("owner_route_currentness_basis"))
    return {
        "work_unit_fingerprint": _text(value.get("work_unit_fingerprint"))
        or _text(value.get("fingerprint"))
        or _text(basis.get("work_unit_fingerprint")),
        "action_fingerprint": _text(value.get("action_fingerprint"))
        or _text(value.get("fingerprint"))
        or _text(basis.get("action_fingerprint")),
        "owner_route_currentness_basis": basis,
    }


def _currentness_basis_matches(
    current_basis: Mapping[str, Any],
    attempt_basis: Mapping[str, Any],
) -> bool:
    keys = (
        "work_unit_fingerprint",
        "action_fingerprint",
        "truth_epoch",
        "runtime_health_epoch",
        "epoch",
    )
    for key in keys:
        current_value = _text(current_basis.get(key))
        if current_value is not None and _text(attempt_basis.get(key)) != current_value:
            return False
    return True


def _first_action_queue_item(value: object) -> dict[str, Any]:
    if not isinstance(value, list | tuple):
        return {}
    for item in value:
        if isinstance(item, Mapping):
            return dict(item)
    return {}


def _work_unit_text(value: object) -> str | None:
    if isinstance(value, Mapping):
        return (
            _text(value.get("unit_id"))
            or _text(value.get("work_unit_id"))
            or _text(value.get("id"))
            or _text(value.get("ref"))
        )
    return _text(value)


def _handoff_has_matching_terminal_closeout(handoff: Mapping[str, Any]) -> bool:
    terminal = _mapping(handoff.get("latest_terminal_stage_log"))
    if not terminal:
        return False
    active_attempt_id = _handoff_stage_attempt_id(handoff)
    terminal_attempt_id = _text(terminal.get("stage_attempt_id"))
    if active_attempt_id is not None and terminal_attempt_id != active_attempt_id:
        return False
    if active_attempt_id is None and terminal_attempt_id is None:
        return False
    status = _text(terminal.get("status"))
    if status in {
        "blocked",
        "closed",
        "closed_with_domain_owner_refs",
        "completed",
        "failed",
        "terminal",
        "typed_blocked",
    }:
        return True
    return _text(terminal.get("source_path")) is not None and _text(terminal.get("record_path")) is not None


def _handoff_stage_attempt_id(handoff: Mapping[str, Any]) -> str | None:
    if text := _text(handoff.get("active_stage_attempt_id")):
        return text
    active_run_id = _text(handoff.get("active_run_id"))
    prefix = "opl-stage-attempt://"
    if active_run_id is not None and active_run_id.startswith(prefix):
        attempt_id = active_run_id[len(prefix) :].strip()
        return attempt_id or None
    return None


def _hard_gate_blockers(payload: Mapping[str, Any]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    supervisor_decision = _blocking_supervisor_decision(payload)
    if supervisor_decision:
        result["paper_autonomy_supervisor_decision"] = supervisor_decision
    interaction = _mapping(payload.get("interaction_arbitration"))
    if interaction.get("requires_user_input") is True or _text(interaction.get("classification")) == "human_gate":
        result["human_gate"] = {
            "requires_user_input": interaction.get("requires_user_input") is True,
            "blocked_reason": _text(interaction.get("blocked_reason"))
            or _text(interaction.get("reason")),
        }
    guard = _mapping(payload.get("execution_owner_guard"))
    forbidden_refs = _text_list(guard.get("forbidden_write_refs"))
    if forbidden_refs:
        result["forbidden_write_refs"] = forbidden_refs
    owner_callable_missing = _owner_callable_surface_missing_blocker(payload)
    if owner_callable_missing:
        result["owner_callable_surface"] = owner_callable_missing
    source_readiness = _mapping(payload.get("source_readiness")) or _mapping(payload.get("startup_data_readiness"))
    missing_sources = _text_list(source_readiness.get("missing_required_sources")) or _text_list(
        source_readiness.get("missing_required_data")
    )
    if missing_sources:
        result["missing_required_source_or_data"] = missing_sources
    current_work_unit_barrier = _mapping(payload.get("owner_action_admission_barrier"))
    if current_work_unit_barrier:
        result["current_work_unit_typed_blocker"] = current_work_unit_barrier
    irreversible = _mapping(payload.get("irreversible_operation_gate"))
    if _text(irreversible.get("status")) == "blocked":
        result["irreversible_operation"] = {
            "status": "blocked",
            "reason": _text(irreversible.get("reason")) or _text(irreversible.get("blocked_reason")),
        }
    return result


def _blocking_supervisor_decision(payload: Mapping[str, Any]) -> dict[str, Any]:
    gate = provider_admission_supervisor_gate(payload)
    if gate.get("blocked") is not True:
        return {}
    supervisor_decision = _mapping(gate.get("supervisor_decision"))
    return {
        "decision": _text(supervisor_decision.get("decision")),
        "reason": _text(gate.get("reason"))
        or "paper_autonomy_supervisor_decision_blocks_provider_admission",
        "supervisor_decision": supervisor_decision,
    }


def _owner_callable_surface_missing_blocker(payload: Mapping[str, Any]) -> dict[str, Any]:
    explicit = _mapping(payload.get("owner_callable_surface"))
    if _text(explicit.get("status")) == "missing":
        return {
            "status": "missing",
            "reason_code": _text(explicit.get("reason_code")) or "owner_callable_surface_missing",
        }
    sources: list[str] = []
    interaction = _mapping(payload.get("interaction_arbitration"))
    if _text(interaction.get("blocked_reason")) == "owner_callable_surface_missing":
        sources.append("interaction_arbitration.blocked_reason")
    if _text(interaction.get("reason_code")) == "owner_callable_surface_missing":
        sources.append("interaction_arbitration.reason_code")
    for surface, key in (
        ("current_execution_envelope", "typed_blocker"),
        ("domain_transition", "typed_blocker"),
        ("domain_transition", "dispatch_result"),
    ):
        if _owner_callable_surface_missing_value(_mapping(payload.get(surface)).get(key)):
            sources.append(f"{surface}.{key}")
    if _owner_callable_surface_missing_value(payload.get("current_blockers")):
        sources.append("current_blockers")
    if not sources:
        return {}
    return {
        "status": "missing",
        "reason_code": "owner_callable_surface_missing",
        "sources": _dedupe_text(sources),
    }


def _owner_callable_surface_missing_value(value: object) -> bool:
    if _text(value) == "owner_callable_surface_missing":
        return True
    if isinstance(value, Mapping):
        for key in ("blocker_id", "blocker_type", "typed_blocker", "blocked_reason", "reason_code"):
            if _text(value.get(key)) == "owner_callable_surface_missing":
                return True
        return False
    return "owner_callable_surface_missing" in _text_list(value)


def _hard_gate_reasons(blocked_by: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    reason_by_surface = {
        "paper_autonomy_supervisor_decision": "paper_autonomy_supervisor_decision",
        "human_gate": "human_gate_required",
        "forbidden_write_refs": "forbidden_write_refs",
        "owner_callable_surface": "owner_callable_surface_missing",
        "missing_required_source_or_data": "missing_required_source_or_data",
        "current_work_unit_typed_blocker": "current_work_unit_typed_blocker",
        "irreversible_operation": "irreversible_operation",
    }
    for key in blocked_by:
        reason = reason_by_surface.get(key)
        if reason is not None:
            reasons.append(reason)
    return reasons


def _observability_diagnostics(
    *,
    stage_progress_log: Mapping[str, Any],
    latest_terminal_stage_log: Mapping[str, Any],
) -> list[dict[str, Any]]:
    diagnostics: list[dict[str, Any]] = []
    missing_usage = _numeric(stage_progress_log.get("missing_usage_telemetry_attempt_count")) or 0
    if missing_usage > 0:
        diagnostics.append(
            {
                "diagnostic": "missing_usage_telemetry",
                "authority": "observability_only",
                "attempt_count": _numeric(stage_progress_log.get("attempt_count")),
                "attempt_refs": _text_list(stage_progress_log.get("attempt_refs")),
            }
        )
    missing_user = _text_list(latest_terminal_stage_log.get("missing_user_stage_log_fields"))
    missing_observability = _text_list(latest_terminal_stage_log.get("missing_observability_fields"))
    if missing_user or missing_observability:
        diagnostics.append(
            {
                "diagnostic": "terminal_closeout_observability_incomplete",
                "authority": "observability_only",
                "stage_attempt_id": _text(latest_terminal_stage_log.get("stage_attempt_id")),
                "missing_user_stage_log_fields": missing_user,
                "missing_observability_fields": missing_observability,
            }
        )
    return diagnostics


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _numeric(value: object) -> int | float | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int | float):
        return value
    return None


def _text_list(value: object) -> list[str]:
    if isinstance(value, str):
        text = value.strip()
        return [text] if text else []
    if not isinstance(value, list | tuple | set):
        return []
    return _dedupe_text(value)


def _dedupe_text(values: list[object] | tuple[object, ...] | set[object]) -> list[str]:
    result: list[str] = []
    for item in values:
        text = _text(item)
        if text is not None and text not in result:
            result.append(text)
    return result


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "build_owner_action_admission_projection",
    "provider_attempt_proof_for_current_action",
]
