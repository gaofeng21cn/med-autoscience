from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission import (
    provider_attempt_matches_identity,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_closeout_semantics import (
    is_anti_loop_stop_loss_closeout,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
    attempt_idempotency_key as _attempt_idempotency_key,
    basis_conflicts_with_identity as _basis_conflicts_with_identity,
    closeout_owner_route_basis as _closeout_owner_route_basis,
    route_identity_key as _route_identity_key,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.opl_execution_boundary import OPL_EXECUTION_AUTHORIZATION_BLOCKER


def accepted_closeout_matches_identity(
    study: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if not _identity_has_match_key(identity):
        return False
    for receipt in _accepted_closeout_receipts(study):
        if receipt_is_accepted_closeout(receipt) and accepted_closeout_matches_candidate_identity(
            receipt,
            identity=identity,
        ):
            return True
    return False


def accepted_closeout_matches_candidate_identity(
    receipt: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if receipt_identity_inferred_from_current_work_unit(receipt):
        return False
    if receipt_has_opl_execution_authorization_blocker(receipt):
        return False
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    if expected_action is None or expected_work_unit is None or expected_fingerprint is None:
        return False
    receipt_fingerprint = _non_empty_text(receipt.get("work_unit_fingerprint")) or _non_empty_text(
        receipt.get("action_fingerprint")
    )
    if _receipt_had_no_raw_fingerprint(receipt):
        receipt_fingerprint = None
    action_and_work_unit_match = (
        _non_empty_text(receipt.get("action_type")) == expected_action
        and _non_empty_text(receipt.get("work_unit_id")) == expected_work_unit
    )
    if action_and_work_unit_match and _stage_packet_identity_conflicts(receipt, identity=identity):
        return False
    if (
        action_and_work_unit_match
        and receipt_fingerprint == expected_fingerprint
        and receipt_is_explicit_accepted_typed_closeout(receipt)
    ):
        if _source_eval_conflicts(receipt, identity=identity):
            return False
        if _receipt_declares_currentness_basis(receipt):
            return not _source_currentness_precludes_consumption(receipt, identity=identity)
        return True
    if _source_currentness_precludes_consumption(receipt, identity=identity):
        return False
    if provider_attempt_matches_identity(receipt, identity=identity):
        return _receipt_has_current_admission_consumption_authority(receipt, identity=identity)
    if (
        action_and_work_unit_match
        and receipt_fingerprint is None
        and _receipt_is_record_only_owner_refs_closeout(
            receipt,
            statuses=receipt_statuses(receipt),
        )
    ):
        return _source_currentness_matches(receipt, identity=identity)
    if (
        action_and_work_unit_match
        and receipt_fingerprint is None
        and _receipt_is_executed_owner_refs_closeout(
            receipt,
            statuses=receipt_statuses(receipt),
        )
    ):
        return _source_currentness_matches(receipt, identity=identity)
    if (
        action_and_work_unit_match
        and receipt_fingerprint is None
        and is_anti_loop_stop_loss_closeout(receipt)
    ):
        return _source_currentness_matches(receipt, identity=identity)
    return (
        action_and_work_unit_match
        and receipt_fingerprint == expected_fingerprint
        and _receipt_has_current_admission_consumption_authority(receipt, identity=identity)
    )


def receipt_identity_inferred_from_current_work_unit(receipt: Mapping[str, Any]) -> bool:
    return _non_empty_text(receipt.get("identity_binding_status")) == "inferred_from_current_work_unit"


def receipt_has_opl_execution_authorization_blocker(receipt: Mapping[str, Any]) -> bool:
    if is_anti_loop_stop_loss_closeout(receipt) and not _receipt_has_explicit_opl_execution_authorization_blocker(
        receipt
    ):
        return False
    return _receipt_has_explicit_opl_execution_authorization_blocker(receipt)


def receipt_is_accepted_closeout(receipt: Mapping[str, Any]) -> bool:
    statuses = receipt_statuses(receipt)
    if receipt_is_explicit_accepted_typed_closeout(receipt):
        return True
    if _receipt_is_record_only_owner_refs_closeout(receipt, statuses=statuses):
        return True
    if _receipt_is_executed_owner_refs_closeout(receipt, statuses=statuses):
        return True
    if receipt_surface_kind(receipt) in {
        "stage_attempt_closeout_packet",
        "domain_stage_closeout_packet",
    } and (
        "blocked" in statuses
        or "closed_with_typed_domain_blocker" in statuses
        or "blocked_with_domain_owner_refs" in statuses
        or _mapping(receipt.get("typed_blocker"))
        or _non_empty_text(receipt.get("typed_blocker_ref")) is not None
        or _non_empty_text(receipt.get("typed_blocker_reason")) is not None
    ):
        return True
    if _non_empty_text(receipt.get("outcome")) != "typed_blocker":
        return False
    if _non_empty_text(receipt.get("execution_status")) != "executed":
        return False
    return _non_empty_text(receipt.get("typed_blocker_ref")) is not None or _non_empty_text(
        receipt.get("typed_blocker_reason")
    ) is not None


def receipt_statuses(receipt: Mapping[str, Any]) -> set[str | None]:
    return {
        _non_empty_text(receipt.get("status")),
        _non_empty_text(receipt.get("execution_status")),
        _non_empty_text(receipt.get("closeout_receipt_status")),
        _non_empty_text(receipt.get("current_attempt_state")),
        _non_empty_text(receipt.get("reconciliation_status")),
        _non_empty_text(receipt.get("stage_closeout_status")),
    }


def receipt_is_explicit_accepted_typed_closeout(receipt: Mapping[str, Any]) -> bool:
    return "accepted_typed_closeout" in receipt_statuses(receipt)


def receipt_surface_kind(receipt: Mapping[str, Any]) -> str | None:
    return _non_empty_text(receipt.get("surface_kind")) or _non_empty_text(
        receipt.get("stage_closeout_surface_kind")
    )


def receipt_matches_live_attempt(
    receipt: Mapping[str, Any],
    live_attempt: Mapping[str, Any],
) -> bool:
    receipt_stage_attempt_id = _stage_attempt_id(receipt)
    live_stage_attempt_id = _stage_attempt_id(live_attempt)
    if receipt_stage_attempt_id is not None and live_stage_attempt_id is not None:
        return receipt_stage_attempt_id == live_stage_attempt_id
    receipt_run_id = _active_run_id(receipt)
    live_run_id = _active_run_id(live_attempt)
    if receipt_run_id is not None and live_run_id is not None:
        return receipt_run_id == live_run_id
    if not _identity_has_match_key(live_attempt):
        return False
    return provider_attempt_matches_identity(receipt, identity=live_attempt)


def _receipt_has_current_admission_consumption_authority(
    receipt: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    if receipt_is_explicit_accepted_typed_closeout(receipt):
        return True
    if _receipt_is_record_only_owner_refs_closeout(
        receipt,
        statuses=receipt_statuses(receipt),
    ):
        return True
    if _receipt_route_identity_matches(receipt, identity=identity):
        return True
    return _source_currentness_matches(receipt, identity=identity)


def _receipt_has_explicit_opl_execution_authorization_blocker(receipt: Mapping[str, Any]) -> bool:
    typed_blocker = _mapping(receipt.get("typed_blocker"))
    direct_values = (
        receipt.get("blocked_reason"),
        receipt.get("typed_blocker_reason"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocker_kind"),
        typed_blocker.get("blocked_reason"),
        typed_blocker.get("reason"),
    )
    if any(_non_empty_text(value) == OPL_EXECUTION_AUTHORIZATION_BLOCKER for value in direct_values):
        return True
    text_values = (
        receipt.get("outcome"),
        receipt.get("problem_summary"),
        receipt.get("semantic_gap"),
        *list(receipt.get("remaining_blockers") or []),
    )
    return any(
        OPL_EXECUTION_AUTHORIZATION_BLOCKER in text
        for value in text_values
        if (text := _non_empty_text(value)) is not None
    )


def _identity_has_match_key(identity: Mapping[str, Any]) -> bool:
    expected_action = _non_empty_text(identity.get("action_type"))
    expected_work_unit = _non_empty_text(identity.get("work_unit_id"))
    expected_fingerprint = _non_empty_text(identity.get("work_unit_fingerprint")) or _non_empty_text(
        identity.get("action_fingerprint")
    )
    return (
        _non_empty_text(identity.get("study_id")) is not None
        and expected_action is not None
        and expected_work_unit is not None
        and expected_fingerprint is not None
    )


def _receipt_is_record_only_owner_refs_closeout(
    receipt: Mapping[str, Any],
    *,
    statuses: set[str | None],
) -> bool:
    if receipt_surface_kind(receipt) not in {
        "stage_attempt_closeout_packet",
        "domain_stage_closeout_packet",
    }:
        return False
    if "closed_with_domain_owner_refs" not in statuses:
        return False
    if receipt_has_opl_execution_authorization_blocker(receipt):
        return False
    return _receipt_has_current_owner_ref(receipt)


def _receipt_is_executed_owner_refs_closeout(
    receipt: Mapping[str, Any],
    *,
    statuses: set[str | None],
) -> bool:
    if receipt_surface_kind(receipt) not in {
        "stage_attempt_closeout_packet",
        "domain_stage_closeout_packet",
    }:
        return False
    if "executed" not in statuses:
        return False
    if receipt_has_opl_execution_authorization_blocker(receipt):
        return False
    return _receipt_has_current_owner_ref(receipt)


def _receipt_had_no_raw_fingerprint(receipt: Mapping[str, Any]) -> bool:
    if receipt.get("raw_closeout_work_unit_fingerprint_present") is False:
        return receipt.get("raw_closeout_action_fingerprint_present") is False
    return False


def _receipt_has_current_owner_ref(receipt: Mapping[str, Any]) -> bool:
    owner_result = _mapping(receipt.get("owner_result"))
    owner_receipt = _mapping(receipt.get("owner_receipt"))
    return any(
        _non_empty_text(value) is not None
        for value in (
            receipt.get("owner_receipt_ref"),
            receipt.get("record_ref"),
            receipt.get("publication_eval_record_ref"),
            owner_result.get("owner_receipt_ref"),
            owner_result.get("publication_eval_record_ref"),
            owner_receipt.get("owner_receipt_ref"),
            owner_receipt.get("publication_eval_record_ref"),
        )
    )


def _receipt_route_identity_matches(receipt: Mapping[str, Any], *, identity: Mapping[str, Any]) -> bool:
    receipt_route_identity_key = _non_empty_text(receipt.get("route_identity_key")) or _non_empty_text(
        receipt.get("idempotency_key")
    )
    identity_route_identity_key = _route_identity_key(identity)
    if receipt_route_identity_key is not None and identity_route_identity_key is not None:
        return receipt_route_identity_key == identity_route_identity_key
    receipt_attempt_idempotency_key = _non_empty_text(receipt.get("attempt_idempotency_key"))
    identity_attempt_idempotency_key = _attempt_idempotency_key(identity)
    return (
        receipt_attempt_idempotency_key is not None
        and identity_attempt_idempotency_key is not None
        and receipt_attempt_idempotency_key == identity_attempt_idempotency_key
    )


def _source_currentness_matches(receipt: Mapping[str, Any], *, identity: Mapping[str, Any]) -> bool:
    receipt_basis = _receipt_currentness_basis(receipt)
    identity_basis = _identity_currentness_basis(identity)
    if not receipt_basis or not identity_basis:
        return False
    if _basis_conflicts_with_identity(receipt_basis, identity=identity):
        return False
    if _basis_conflicts_with_identity(identity_basis, identity=identity):
        return False
    receipt_source_eval = _non_empty_text(receipt_basis.get("source_eval_id"))
    identity_source_eval = _non_empty_text(identity_basis.get("source_eval_id"))
    if receipt_source_eval is not None or identity_source_eval is not None:
        if receipt_source_eval is not None and identity_source_eval is not None:
            return receipt_source_eval == identity_source_eval
        return _legacy_currentness_basis_matches(receipt_basis, identity_basis)
    return _legacy_currentness_basis_matches(receipt_basis, identity_basis)


def _source_currentness_precludes_consumption(
    receipt: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    receipt_basis = _receipt_currentness_basis(receipt)
    identity_basis = _identity_currentness_basis(identity)
    if not receipt_basis or not identity_basis:
        return False
    if _basis_conflicts_with_identity(receipt_basis, identity=identity):
        return True
    if _basis_conflicts_with_identity(identity_basis, identity=identity):
        return True
    identity_source_eval = _non_empty_text(identity_basis.get("source_eval_id"))
    receipt_source_eval = _non_empty_text(receipt_basis.get("source_eval_id"))
    if identity_source_eval is not None:
        if receipt_source_eval is None:
            return not _legacy_currentness_basis_matches(receipt_basis, identity_basis)
        return receipt_source_eval != identity_source_eval
    if receipt_source_eval is not None:
        return False
    if _identity_currentness_requires_strict_receipt(identity_basis):
        return not _legacy_currentness_basis_matches(receipt_basis, identity_basis)
    return False


def _source_eval_conflicts(receipt: Mapping[str, Any], *, identity: Mapping[str, Any]) -> bool:
    receipt_source_eval = _non_empty_text(_receipt_currentness_basis(receipt).get("source_eval_id"))
    identity_source_eval = _non_empty_text(_identity_currentness_basis(identity).get("source_eval_id"))
    return (
        receipt_source_eval is not None
        and identity_source_eval is not None
        and receipt_source_eval != identity_source_eval
    )


def _receipt_declares_currentness_basis(receipt: Mapping[str, Any]) -> bool:
    owner_route = _mapping(receipt.get("owner_route"))
    source_refs = _mapping(owner_route.get("source_refs"))
    return any(
        _mapping(value)
        for value in (
            receipt.get("owner_route_basis"),
            receipt.get("owner_route_currentness"),
            source_refs.get("owner_route_currentness_basis"),
            source_refs,
            receipt.get("canonical_work_unit_identity"),
            receipt.get("owner_route_currentness_basis"),
        )
    )


def _identity_currentness_requires_strict_receipt(identity_basis: Mapping[str, Any]) -> bool:
    return any(
        _non_empty_text(identity_basis.get(key)) is not None
        for key in ("truth_epoch", "runtime_health_epoch", "source_eval_id")
    )


def _receipt_currentness_basis(receipt: Mapping[str, Any]) -> dict[str, Any]:
    basis = dict(_closeout_owner_route_basis(receipt))
    nested_owner_route_basis = _mapping(
        _mapping(_mapping(receipt.get("owner_route")).get("source_refs")).get(
            "owner_route_currentness_basis"
        )
    )
    direct_owner_route_basis = _mapping(receipt.get("owner_route_currentness_basis"))
    owner_route_basis = _mapping(receipt.get("owner_route_basis"))
    for candidate_basis in (nested_owner_route_basis, direct_owner_route_basis, owner_route_basis):
        for key, value in candidate_basis.items():
            if basis.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
                basis[key] = value
    for key, value in {
        "work_unit_id": _non_empty_text(receipt.get("work_unit_id"))
        or _non_empty_text(basis.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(receipt.get("work_unit_fingerprint"))
        or _non_empty_text(receipt.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(receipt.get("action_fingerprint"))
        or _non_empty_text(receipt.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
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


def _stage_packet_identity_conflicts(
    receipt: Mapping[str, Any],
    *,
    identity: Mapping[str, Any],
) -> bool:
    identity_refs = _stage_packet_refs(identity)
    if not identity_refs:
        return False
    receipt_refs = _stage_packet_refs(receipt)
    if not receipt_refs:
        return False
    return not any(
        _refs_equivalent(receipt_ref, identity_ref)
        for receipt_ref in receipt_refs
        for identity_ref in identity_refs
    )


def _stage_packet_refs(payload: Mapping[str, Any]) -> tuple[str, ...]:
    refs: list[str] = []
    for candidate in (
        payload.get("stage_packet_ref"),
        payload.get("stage_packet_path"),
        payload.get("stage_packet"),
    ):
        text = _non_empty_text(candidate)
        if text is not None:
            refs.append(text)
    for key in ("stage_packet_refs", "stage_packet_paths"):
        for candidate in payload.get(key) or []:
            text = _non_empty_text(candidate)
            if text is not None:
                refs.append(text)
    for nested in (
        _mapping(payload.get("source_refs")),
        _mapping(payload.get("refs")),
        _mapping(payload.get("handoff_packet")),
        _mapping(payload.get("owner_route")).get("source_refs"),
    ):
        nested_payload = _mapping(nested)
        for candidate in (
            nested_payload.get("stage_packet_ref"),
            nested_payload.get("stage_packet_path"),
        ):
            text = _non_empty_text(candidate)
            if text is not None:
                refs.append(text)
        for key in ("stage_packet_refs", "stage_packet_paths"):
            for candidate in nested_payload.get(key) or []:
                text = _non_empty_text(candidate)
                if text is not None:
                    refs.append(text)
    return tuple(dict.fromkeys(refs))


def _refs_equivalent(left: str, right: str) -> bool:
    if left == right:
        return True
    left_norm = left.rstrip("/")
    right_norm = right.rstrip("/")
    if left_norm == right_norm:
        return True
    return left_norm.endswith(f"/{right_norm}") or right_norm.endswith(f"/{left_norm}")


def _identity_currentness_basis(identity: Mapping[str, Any]) -> dict[str, Any]:
    basis = dict(_mapping(identity.get("currentness_basis")))
    nested_basis = _mapping(basis.get("owner_route_currentness_basis"))
    for key, value in nested_basis.items():
        if basis.get(key) in (None, "", [], {}) and value not in (None, "", [], {}):
            basis[key] = value
    for key, value in {
        "work_unit_id": _non_empty_text(identity.get("work_unit_id"))
        or _non_empty_text(basis.get("work_unit_id")),
        "work_unit_fingerprint": _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("action_fingerprint")),
        "action_fingerprint": _non_empty_text(identity.get("action_fingerprint"))
        or _non_empty_text(identity.get("work_unit_fingerprint"))
        or _non_empty_text(basis.get("action_fingerprint"))
        or _non_empty_text(basis.get("work_unit_fingerprint")),
        "source_eval_id": _non_empty_text(identity.get("source_eval_id"))
        or _non_empty_text(basis.get("source_eval_id")),
        "truth_epoch": _non_empty_text(identity.get("truth_epoch"))
        or _non_empty_text(basis.get("truth_epoch"))
        or _non_empty_text(basis.get("study_truth_epoch")),
        "runtime_health_epoch": _non_empty_text(identity.get("runtime_health_epoch"))
        or _non_empty_text(basis.get("runtime_health_epoch")),
    }.items():
        if value is not None:
            basis[key] = value
    return {key: value for key, value in basis.items() if value not in (None, "", [], {})}


def _legacy_currentness_basis_matches(
    receipt_basis: Mapping[str, Any],
    identity_basis: Mapping[str, Any],
) -> bool:
    for key in ("work_unit_id", "truth_epoch", "runtime_health_epoch"):
        receipt_value = _non_empty_text(receipt_basis.get(key))
        identity_value = _non_empty_text(identity_basis.get(key))
        if receipt_value is None or identity_value is None or receipt_value != identity_value:
            return False
    receipt_fingerprint = _non_empty_text(receipt_basis.get("work_unit_fingerprint")) or _non_empty_text(
        receipt_basis.get("action_fingerprint")
    )
    identity_fingerprint = _non_empty_text(identity_basis.get("work_unit_fingerprint")) or _non_empty_text(
        identity_basis.get("action_fingerprint")
    )
    return (
        receipt_fingerprint is not None
        and identity_fingerprint is not None
        and receipt_fingerprint == identity_fingerprint
    )


def _stage_attempt_id(payload: Mapping[str, Any]) -> str | None:
    return _non_empty_text(payload.get("active_stage_attempt_id")) or _non_empty_text(
        payload.get("stage_attempt_id")
    )


def _active_run_id(payload: Mapping[str, Any]) -> str | None:
    return _non_empty_text(payload.get("active_run_id")) or _non_empty_text(payload.get("run_id"))


__all__ = [
    "accepted_closeout_matches_candidate_identity",
    "accepted_closeout_matches_identity",
    "receipt_identity_inferred_from_current_work_unit",
    "receipt_is_accepted_closeout",
    "receipt_matches_live_attempt",
]
