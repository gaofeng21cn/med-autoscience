from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.provider_admission_parts import (
    provider_admission_current_control_receipts as current_control_receipts,
)
from med_autoscience.controllers.provider_admission_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
    weak_provider_admission_identity as _weak_provider_admission_identity,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_current_control_readback_overrides import (
    provider_admission_readback_overrides_blocking_closeout,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.provider_admission_parts.provider_admission_report_closeout_identity import (
    closeout_core_identity_matches_candidate as _closeout_core_identity_matches_candidate,
)

STALE_STAGE_PACKET_BLOCKER = "stage_packet_not_current_selected_dispatch"


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
    expected_fingerprint = _non_empty_text(
        identity.get("work_unit_fingerprint")
    ) or _non_empty_text(identity.get("action_fingerprint"))
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
    receipts = [
        receipt
        for receipt in _accepted_closeout_receipts(study)
        if current_control_receipts.receipt_is_accepted_closeout(receipt)
        and not _receipt_has_provider_admission_authorization_blocker(receipt)
    ]
    for receipt in receipts:
        if current_control_receipts.accepted_closeout_matches_candidate_identity(
            receipt,
            identity=identity,
        ):
            return False
        if _exact_owner_refs_closeout_matches_candidate(receipt, identity=identity):
            return False
    for receipt in receipts:
        if not current_control_receipts.receipt_is_accepted_closeout(receipt):
            continue
        if _receipt_has_provider_admission_authorization_blocker(receipt):
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


def _provider_admission_readback_overrides_blocking_closeout(
    candidate: Mapping[str, Any],
    *,
    closeout: Mapping[str, Any],
) -> bool:
    return provider_admission_readback_overrides_blocking_closeout(
        candidate,
        closeout=closeout,
    )
