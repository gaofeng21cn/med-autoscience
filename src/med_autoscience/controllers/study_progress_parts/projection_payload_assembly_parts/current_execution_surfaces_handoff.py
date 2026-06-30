from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.current_work_unit_parts.terminal_closeout_currentness import (
    OPL_RUNTIME_TERMINAL_BLOCKERS,
)
from med_autoscience.controllers.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)
from med_autoscience.runtime_control.owner_route_attempt_protocol import (
    currentness_basis as owner_route_currentness_basis,
    owner_reason_contract,
)

from .current_execution_alignment import text_list
from ..current_owner_action_projection_reconcile import (
    current_execution_handoff_consumes_current_action,
)
from ..shared import _mapping_copy, _non_empty_text


def _canonical_current_control_typed_blocker_work_unit(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    current = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(current.get("status")) in {"typed_blocker", "blocked_current_work_unit"}:
        return current
    return {}


def _canonical_current_control_owner_receipt_work_unit(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    if not _handoff_current_work_unit_is_owner_receipt(handoff):
        return {}
    return _mapping_copy(handoff.get("current_work_unit"))


def _canonical_current_control_typed_blocker(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    current = _mapping_copy(handoff.get("current_work_unit"))
    state = _mapping_copy(current.get("state"))
    current_blocker = _mapping_copy(state.get("typed_blocker"))
    if current_blocker:
        return current_blocker
    envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    envelope_blocker = _mapping_copy(envelope.get("typed_blocker"))
    if envelope_blocker:
        return envelope_blocker
    return {}


def _canonical_typed_blocker_for_execution_refresh(handoff: Mapping[str, Any]) -> dict[str, Any]:
    if _handoff_current_work_unit_is_owner_receipt(handoff):
        return _consumed_terminal_typed_blocker_for_execution_refresh(handoff)
    return _canonical_typed_blocker_from_handoff(handoff)


def _canonical_typed_blocker_from_handoff(handoff: Mapping[str, Any]) -> dict[str, Any]:
    typed_blocker = _mapping_copy(handoff.get("typed_blocker"))
    if typed_blocker:
        return typed_blocker
    if not current_execution_handoff_consumes_current_action(handoff):
        return {}
    handoff_blocker = _typed_blocker_from_current_control_blocked_reason(handoff)
    if handoff_blocker:
        return handoff_blocker
    latest_closeout = _mapping_copy(handoff.get("latest_typed_owner_callable_closeout"))
    embedded = _mapping_copy(latest_closeout.get("typed_blocker"))
    blocked_reason = (
        _non_empty_text(embedded.get("blocker_type"))
        or _non_empty_text(embedded.get("blocked_reason"))
        or _non_empty_text(embedded.get("reason"))
        or _non_empty_text(embedded.get("blocker_id"))
        or _non_empty_text(latest_closeout.get("blocked_reason"))
    )
    if blocked_reason is None:
        return {}
    owner = (
        "one-person-lab"
        if blocked_reason in OPL_RUNTIME_TERMINAL_BLOCKERS
        else _non_empty_text(embedded.get("owner"))
        or _non_empty_text(embedded.get("next_owner"))
        or _non_empty_text(handoff.get("next_owner"))
        or "med-autoscience"
    )
    return {
        key: value
        for key, value in {
            **embedded,
            "blocker_type": blocked_reason,
            "blocked_reason": blocked_reason,
            "owner": owner,
            "action_type": _non_empty_text(latest_closeout.get("action_type")),
            "work_unit_id": _non_empty_text(latest_closeout.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(latest_closeout.get("work_unit_fingerprint")),
            "action_fingerprint": _non_empty_text(latest_closeout.get("action_fingerprint")),
            "source_fingerprint": _non_empty_text(latest_closeout.get("source_fingerprint")),
            "idempotency_key": _non_empty_text(latest_closeout.get("idempotency_key")),
            "stage_attempt_id": _non_empty_text(latest_closeout.get("stage_attempt_id")),
            "source_ref": _non_empty_text(latest_closeout.get("receipt_ref"))
            or _non_empty_text(latest_closeout.get("source_path")),
            "typed_blocker_ref": _non_empty_text(latest_closeout.get("receipt_ref"))
            or _non_empty_text(latest_closeout.get("source_path")),
        }.items()
        if value not in (None, "", [], {})
    }


def _consumed_terminal_typed_blocker_for_execution_refresh(
    handoff: Mapping[str, Any],
    *,
    payload: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    if handoff.get("running_provider_attempt") is True:
        return {}
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if _non_empty_text(consumed.get("typed_blocker_ref")) is None and not _mapping_copy(
        consumed.get("typed_blocker")
    ):
        return {}
    typed_blocker = _mapping_copy(consumed.get("typed_blocker")) or _canonical_typed_blocker_from_handoff(handoff)
    if not typed_blocker:
        return {}
    typed_blocker = _with_consumed_terminal_closeout_marker(
        typed_blocker,
        consumed=consumed,
    )
    if not _identity_overlaps_without_conflict(consumed, typed_blocker):
        return {}
    current = _mapping_copy(handoff.get("current_work_unit"))
    if current and not _identity_overlaps_without_conflict(current, typed_blocker):
        current_identity = _identity_values(current)
        consumed_identity = _identity_values(consumed)
        if not _identities_conflict(current_identity, consumed_identity):
            return {}
    return typed_blocker


def _with_consumed_terminal_closeout_marker(
    typed_blocker: Mapping[str, Any],
    *,
    consumed: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: value
        for key, value in {
            **typed_blocker,
            "terminal_closeout_consumption_source": "provider_admission_terminal_closeout_consumed",
            "typed_blocker_ref": _non_empty_text(typed_blocker.get("typed_blocker_ref"))
            or _non_empty_text(consumed.get("typed_blocker_ref")),
            "source_ref": _non_empty_text(typed_blocker.get("source_ref"))
            or _non_empty_text(consumed.get("typed_blocker_ref")),
            "stage_attempt_id": _non_empty_text(typed_blocker.get("stage_attempt_id"))
            or _non_empty_text(consumed.get("stage_attempt_id")),
        }.items()
        if value not in (None, "", [], {})
    }


def _identity_overlaps_without_conflict(left: Mapping[str, Any], right: Mapping[str, Any]) -> bool:
    left_identity = _identity_values(left)
    right_identity = _identity_values(right)
    if _identities_conflict(left_identity, right_identity):
        return False
    return any(
        left_identity.get(key) is not None and right_identity.get(key) is not None
        for key in ("action_type", "work_unit_id", "fingerprint")
    )


def _typed_blocker_from_current_control_blocked_reason(handoff: Mapping[str, Any]) -> dict[str, Any]:
    blocked_reason = _non_empty_text(handoff.get("blocked_reason"))
    if blocked_reason is None:
        return {}
    contract = owner_reason_contract(
        reason=blocked_reason,
        owner=_non_empty_text(handoff.get("next_owner")),
    )
    if contract.get("registered") is not True:
        return {}
    if _non_empty_text(contract.get("owner")) != "one-person-lab":
        return {}
    if any(_non_empty_text(action) is not None for action in contract.get("allowed_actions") or []):
        return {}
    owner_route = _mapping_copy(handoff.get("owner_route"))
    source_refs = _mapping_copy(owner_route.get("source_refs"))
    basis = owner_route_currentness_basis(owner_route) if owner_route else {}
    owner = _non_empty_text(handoff.get("next_owner")) or _non_empty_text(contract.get("owner")) or "one-person-lab"
    return {
        key: value
        for key, value in {
            "blocker_type": blocked_reason,
            "blocker_id": blocked_reason,
            "blocked_reason": blocked_reason,
            "owner": owner,
            "work_unit_id": _non_empty_text(source_refs.get("work_unit_id"))
            or _non_empty_text(owner_route.get("work_unit_id"))
            or _non_empty_text(basis.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(owner_route.get("work_unit_fingerprint"))
            or _non_empty_text(source_refs.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint"))
            or _non_empty_text(handoff.get("source_fingerprint")),
            "action_fingerprint": _non_empty_text(owner_route.get("action_fingerprint"))
            or _non_empty_text(source_refs.get("action_fingerprint"))
            or _non_empty_text(owner_route.get("work_unit_fingerprint"))
            or _non_empty_text(source_refs.get("work_unit_fingerprint"))
            or _non_empty_text(basis.get("work_unit_fingerprint"))
            or _non_empty_text(handoff.get("source_fingerprint")),
            "source_fingerprint": _non_empty_text(owner_route.get("source_fingerprint"))
            or _non_empty_text(source_refs.get("source_fingerprint"))
            or _non_empty_text(handoff.get("source_fingerprint")),
            "source_eval_id": _non_empty_text(source_refs.get("source_eval_id"))
            or _non_empty_text(basis.get("source_eval_id")),
            "source_ref": _non_empty_text(handoff.get("source_ref")) or _non_empty_text(handoff.get("source_path")),
            "required_output": _non_empty_text(contract.get("required_output")),
        }.items()
        if value not in (None, "", [], {})
    }


def _handoff_current_work_unit_is_owner_receipt(handoff: Mapping[str, Any]) -> bool:
    current = _mapping_copy(handoff.get("current_work_unit"))
    if _non_empty_text(current.get("status")) != "owner_receipt_recorded":
        return False
    state = _mapping_copy(current.get("state"))
    if _non_empty_text(state.get("state_kind")) != "owner_receipt_recorded":
        return False
    receipt_ref = _non_empty_text(state.get("owner_receipt_ref")) or _non_empty_text(
        _mapping_copy(current.get("required_output_contract")).get("owner_receipt_ref")
    )
    if receipt_ref is None:
        return False
    envelope = _mapping_copy(handoff.get("current_execution_envelope"))
    envelope_kind = _non_empty_text(envelope.get("state_kind"))
    if envelope_kind not in {None, "owner_receipt_recorded"}:
        return False
    return True


def _handoff_has_bound_running_provider_attempt(handoff: Mapping[str, Any]) -> bool:
    if handoff.get("running_provider_attempt") is not True:
        return False
    if not provider_admission_opl_transition_readback(handoff):
        return False
    if _non_empty_text(handoff.get("active_stage_attempt_id")) is None and _non_empty_text(
        handoff.get("active_run_id")
    ) is None and _non_empty_text(handoff.get("active_workflow_id")) is None:
        return False
    runtime_health = _mapping_copy(handoff.get("runtime_health"))
    runtime_liveness_status = _non_empty_text(runtime_health.get("runtime_liveness_status"))
    health_status = _non_empty_text(runtime_health.get("health_status"))
    if runtime_liveness_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    } and health_status not in {
        "attempt_running",
        "provider_admitted",
        "running",
        "live",
    }:
        return False
    return any(
        _non_empty_text(value) is not None
        for value in (
            handoff.get("action_type"),
            handoff.get("work_unit_id"),
            handoff.get("work_unit_fingerprint"),
            handoff.get("action_fingerprint"),
            runtime_health.get("action_type"),
            runtime_health.get("work_unit_id"),
            runtime_health.get("work_unit_fingerprint"),
            runtime_health.get("action_fingerprint"),
        )
    )


def _provider_admission_supersedes_request_action(
    provider_action: Mapping[str, Any],
    *,
    request_action: Mapping[str, Any] | None,
) -> bool:
    if provider_action.get("provider_admission_pending") is not True:
        return False
    if _non_empty_text(provider_action.get("opl_transition_readback_source")) != (
        "opl_domain_progress_transition_runtime_live_readback"
    ):
        return False
    request_payload = _mapping_copy(request_action)
    if not request_payload:
        return True
    provider_identity = _identity_values(provider_action)
    request_identity = _identity_values(request_payload)
    return not _identities_conflict(provider_identity, request_identity)


def _running_handoff_conflicts_current_surface(
    *,
    payload: Mapping[str, Any],
    handoff: Mapping[str, Any],
) -> bool:
    if not _handoff_has_bound_running_provider_attempt(handoff):
        return False
    handoff_identity = _identity_values(handoff)
    for surface in (
        _mapping_copy(payload.get("current_work_unit")),
        _mapping_copy(payload.get("current_execution_envelope")),
        _mapping_copy(payload.get("current_executable_owner_action")),
    ):
        if not surface:
            continue
        if _non_empty_text(surface.get("status")) not in {
            "executable_owner_action",
            "running_provider_attempt",
            "typed_blocker",
            "blocked_current_work_unit",
        } and _non_empty_text(surface.get("state_kind")) not in {
            "executable_owner_action",
            "running_provider_attempt",
            "typed_blocker",
            "blocked_current_work_unit",
        } and _non_empty_text(surface.get("surface_kind")) != "current_executable_owner_action":
            continue
        surface_identity = _identity_values(surface)
        if _identities_conflict(handoff_identity, surface_identity):
            return True
    return False


def _identity_values(value: Mapping[str, Any]) -> dict[str, str | None]:
    basis = _mapping_copy(value.get("owner_route_currentness_basis")) or _mapping_copy(
        value.get("currentness_basis")
    )
    state = _mapping_copy(value.get("state"))
    runtime_health = _mapping_copy(value.get("runtime_health"))
    return {
        "action_type": _non_empty_text(value.get("action_type"))
        or _non_empty_text(runtime_health.get("action_type")),
        "work_unit_id": _non_empty_text(value.get("work_unit_id"))
        or _non_empty_text(value.get("next_work_unit"))
        or _non_empty_text(runtime_health.get("work_unit_id"))
        or _non_empty_text(runtime_health.get("next_work_unit"))
        or _non_empty_text(state.get("next_work_unit"))
        or _non_empty_text(basis.get("work_unit_id")),
        "fingerprint": _non_empty_text(value.get("work_unit_fingerprint"))
        or _non_empty_text(value.get("action_fingerprint"))
        or _non_empty_text(runtime_health.get("work_unit_fingerprint"))
        or _non_empty_text(runtime_health.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
        "route_identity_key": _non_empty_text(value.get("route_identity_key"))
        or _non_empty_text(runtime_health.get("route_identity_key"))
        or _non_empty_text(basis.get("route_identity_key")),
        "attempt_idempotency_key": _non_empty_text(value.get("attempt_idempotency_key"))
        or _non_empty_text(runtime_health.get("attempt_idempotency_key"))
        or _non_empty_text(basis.get("attempt_idempotency_key")),
    }


def _paper_recovery_owner_callable_action(action: Mapping[str, Any]) -> bool:
    if _non_empty_text(action.get("source")) != "paper_recovery_state.next_safe_action.successor_owner_action":
        return False
    successor = _mapping_copy(action.get("paper_recovery_successor"))
    return (
        _non_empty_text(successor.get("source_next_safe_action_kind")) == "run_mas_owner_callable"
        and _non_empty_text(successor.get("owner_callable_surface")) is not None
    )


def _identities_conflict(left: Mapping[str, str | None], right: Mapping[str, str | None]) -> bool:
    return any(
        left.get(key) is not None and right.get(key) is not None and left.get(key) != right.get(key)
        for key in (
            "action_type",
            "work_unit_id",
            "fingerprint",
            "route_identity_key",
            "attempt_idempotency_key",
        )
    )


def _handoff_has_consumed_terminal_typed_blocker(handoff: Mapping[str, Any]) -> bool:
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return False
    if _non_empty_text(consumed.get("typed_blocker_ref")) is not None:
        return True
    if _mapping_copy(consumed.get("typed_blocker")):
        return True
    latest = _mapping_copy(handoff.get("latest_typed_owner_callable_closeout"))
    if _non_empty_text(latest.get("status")) == "typed_blocker":
        return True
    terminal = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    return (
        _non_empty_text(terminal.get("route_outcome")) == "typed_blocker"
        or _non_empty_text(terminal.get("typed_blocker_ref")) is not None
    )


def _provider_admission_terminal_closeout_consumed_domain_delta(
    handoff: Mapping[str, Any],
) -> bool:
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return False
    terminal = _mapping_copy(handoff.get("latest_terminal_stage_log"))
    if _non_empty_text(consumed.get("owner_receipt_ref")) is not None:
        return True
    if _non_empty_text(terminal.get("owner_receipt_ref")) is not None:
        return True
    if text_list(terminal.get("owner_receipt_refs")):
        return True
    if _non_empty_text(terminal.get("route_outcome")) == "owner_receipt":
        return True
    paper_stage_log = _mapping_copy(terminal.get("paper_stage_log"))
    if text_list(paper_stage_log.get("changed_paper_surfaces")):
        return True
    if _non_empty_text(paper_stage_log.get("progress_delta_classification")) in {
        "deliverable_progress",
        "paper_progress",
        "mixed",
    }:
        return True
    return False


def _provider_admission_terminal_closeout_consumed_current_work_unit(
    handoff: Mapping[str, Any],
) -> bool:
    consumed = _mapping_copy(handoff.get("provider_admission_terminal_closeout_consumed"))
    if not consumed:
        return False
    if _non_empty_text(consumed.get("owner_receipt_ref")) is None and _non_empty_text(
        consumed.get("typed_blocker_ref")
    ) is None:
        return False
    current = _mapping_copy(handoff.get("current_work_unit"))
    if not current:
        return False
    consumed_identity = _identity_values(consumed)
    current_identity = _identity_values(current)
    return not _identities_conflict(consumed_identity, current_identity)
