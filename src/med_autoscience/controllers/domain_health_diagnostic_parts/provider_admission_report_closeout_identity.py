from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity import (
    basis_conflicts_with_identity as _basis_conflicts_with_identity,
    closeout_owner_route_basis as _closeout_owner_route_basis,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER


def terminal_stage_closeout_evidence(
    terminal: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    status = _non_empty_text(terminal.get("status"))
    classification = _non_empty_text(terminal.get("progress_delta_classification"))
    blocker_id = _terminal_stage_blocker_id(terminal)
    payload = {
        **dict(terminal),
        "surface_kind": _non_empty_text(terminal.get("surface_kind")) or "stage_attempt_closeout_packet",
        "status": status,
        "stage_closeout_status": status,
        "execution_status": status,
        "outcome": "typed_blocker"
        if classification == "typed_blocker"
        else _non_empty_text(terminal.get("outcome")),
        "blocked_reason": blocker_id,
        "typed_blocker_reason": blocker_id,
        "typed_blocker_ref": _non_empty_text(terminal.get("source_path")),
        "typed_blocker": {
            "blocker_id": blocker_id,
            "blocker_type": blocker_id,
            "owner": "one-person-lab",
            "write_permitted": False,
        },
    }
    return closeout_evidence_with_identity(payload, identity=identity)


def closeout_evidence_with_identity(
    closeout: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> dict[str, Any]:
    result = dict(closeout)
    basis = _closeout_owner_route_basis(result)
    for key, value in {
        "work_unit_id": _non_empty_text(basis.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(basis.get("work_unit_fingerprint")),
        "action_fingerprint": _non_empty_text(basis.get("action_fingerprint")),
        "source_eval_id": _non_empty_text(basis.get("source_eval_id")),
        "truth_epoch": _non_empty_text(basis.get("truth_epoch")),
        "runtime_health_epoch": _non_empty_text(basis.get("runtime_health_epoch")),
    }.items():
        if value is not None and result.get(key) in (None, "", [], {}):
            result[key] = value
    had_native_identity = _closeout_has_native_current_identity(result)
    for key, value in {
        "surface_kind": _non_empty_text(result.get("surface_kind"))
        or _non_empty_text(result.get("stage_closeout_surface_kind")),
        "status": _non_empty_text(result.get("status"))
        or _non_empty_text(result.get("stage_closeout_status")),
        "outcome": _non_empty_text(result.get("outcome"))
        or _non_empty_text(result.get("stage_closeout_outcome")),
    }.items():
        if value is not None:
            result[key] = value
    if (
        _closeout_has_opl_execution_authorization_blocker(result)
        and not is_anti_loop_stop_loss_closeout(result)
    ):
        result["identity_binding_status"] = "mismatch"
        return result
    identity_fill_keys = (
        (
            "action_type",
            "work_unit_id",
            "source_eval_id",
            "truth_epoch",
            "runtime_health_epoch",
        )
        if had_native_identity
        else ("action_type", "work_unit_id")
    )
    for key in identity_fill_keys:
        if result.get(key) in (None, "", [], {}) and identity.get(key) not in (None, "", [], {}):
            result[key] = identity[key]
    if not had_native_identity:
        result["identity_binding_status"] = "inferred_from_current_work_unit"
    basis = _mapping(result.get("owner_route_currentness_basis"))
    if not basis:
        basis = {
            key: result.get(key)
            for key in (
                "work_unit_id",
                "work_unit_fingerprint",
                "action_fingerprint",
                "source_eval_id",
                "truth_epoch",
                "runtime_health_epoch",
            )
            if result.get(key) not in (None, "", [], {})
        }
        if basis:
            result["owner_route_currentness_basis"] = basis
    return result


def closeout_identity_matches_current(
    closeout: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if closeout.get("identity_binding_status") in {
        "mismatch",
        "inferred_from_current_work_unit",
    }:
        return False
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    if expected_action is not None and _non_empty_text(closeout.get("action_type")) != expected_action:
        return False
    if expected_work_unit is not None and _non_empty_text(closeout.get("work_unit_id")) != expected_work_unit:
        return False
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    closeout_fingerprint = _non_empty_text(closeout.get("work_unit_fingerprint")) or _non_empty_text(
        closeout.get("action_fingerprint")
    )
    if expected_fingerprint is None:
        return True
    if closeout_fingerprint == expected_fingerprint:
        return True
    if closeout_fingerprint is None and _closeout_source_currentness_matches_current(
        closeout,
        identity=identity,
    ):
        return True
    return closeout_fingerprint is None and is_anti_loop_stop_loss_closeout(closeout)


def _terminal_stage_blocker_id(terminal: Mapping[str, Any]) -> str:
    typed_blocker = _mapping(terminal.get("typed_blocker"))
    semantic = _mapping(terminal.get("terminal_closeout_semantic_completeness"))
    for value in (
        terminal.get("blocked_reason"),
        terminal.get("typed_blocker_reason"),
        terminal.get("blocker_id"),
        terminal.get("blocker_type"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("reason"),
        semantic.get("typed_blocker"),
    ):
        text = _non_empty_text(value)
        if text is not None:
            return text
    if _non_empty_text(terminal.get("status")) == "repeat_suppressed":
        return "anti_loop_budget_exhausted"
    return _non_empty_text(terminal.get("status")) or "terminal_closeout_observed"


def _closeout_has_native_current_identity(closeout: Mapping[str, Any]) -> bool:
    basis = _closeout_owner_route_basis(closeout)
    if _basis_has_native_currentness_identity(basis):
        return True
    work_unit = _non_empty_text(closeout.get("work_unit_id"))
    fingerprint = _non_empty_text(closeout.get("work_unit_fingerprint")) or _non_empty_text(
        closeout.get("action_fingerprint")
    )
    source_eval_id = _non_empty_text(closeout.get("source_eval_id"))
    return work_unit is not None and (fingerprint is not None or source_eval_id is not None)


def _basis_has_native_currentness_identity(basis: Mapping[str, Any]) -> bool:
    if not basis:
        return False
    if _non_empty_text(basis.get("work_unit_id")) is None:
        return False
    if _non_empty_text(basis.get("work_unit_fingerprint")) is not None:
        return True
    if _non_empty_text(basis.get("action_fingerprint")) is not None:
        return True
    if _non_empty_text(basis.get("source_eval_id")) is not None:
        return True
    return _non_empty_text(basis.get("truth_epoch")) is not None and _non_empty_text(
        basis.get("runtime_health_epoch")
    ) is not None


def _closeout_source_currentness_matches_current(
    closeout: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    closeout_basis = _closeout_owner_route_basis(closeout)
    identity_basis = _mapping(identity.get("currentness_basis"))
    if not closeout_basis or not identity_basis:
        return False
    if _basis_conflicts_with_identity(closeout_basis, identity=identity):
        return False
    if _basis_conflicts_with_identity(identity_basis, identity=identity):
        return False
    closeout_source_eval = _non_empty_text(closeout_basis.get("source_eval_id"))
    identity_source_eval = _non_empty_text(identity_basis.get("source_eval_id"))
    if closeout_source_eval is not None or identity_source_eval is not None:
        return closeout_source_eval is not None and closeout_source_eval == identity_source_eval
    compared = False
    for key in ("truth_epoch", "runtime_health_epoch"):
        closeout_value = _non_empty_text(closeout_basis.get(key))
        identity_value = _non_empty_text(identity_basis.get(key))
        if closeout_value is None or identity_value is None:
            continue
        compared = True
        if closeout_value != identity_value:
            return False
    return compared


def _closeout_has_opl_execution_authorization_blocker(closeout: Mapping[str, Any]) -> bool:
    typed_blocker = _mapping(closeout.get("typed_blocker"))
    direct_values = (
        closeout.get("blocked_reason"),
        closeout.get("typed_blocker_reason"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocked_reason"),
    )
    if any(_non_empty_text(value) == OPL_EXECUTION_AUTHORIZATION_BLOCKER for value in direct_values):
        return True
    text_values = (
        closeout.get("outcome"),
        closeout.get("problem_summary"),
        closeout.get("semantic_gap"),
        *list(closeout.get("remaining_blockers") or []),
    )
    return any(
        OPL_EXECUTION_AUTHORIZATION_BLOCKER in text
        for value in text_values
        if (text := _non_empty_text(value)) is not None
    )


__all__ = [
    "closeout_evidence_with_identity",
    "closeout_identity_matches_current",
    "terminal_stage_closeout_evidence",
]
