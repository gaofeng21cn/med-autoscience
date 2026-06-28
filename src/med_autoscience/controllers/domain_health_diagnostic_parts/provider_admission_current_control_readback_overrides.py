from __future__ import annotations

from typing import Any, Mapping

from med_autoscience.controllers.domain_health_diagnostic_parts.managed_wakeup import _non_empty_text
from med_autoscience.controllers.domain_health_diagnostic_parts import (
    provider_admission_current_control_receipts as current_control_receipts,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_current_control_identity import (
    accepted_closeout_receipts as _accepted_closeout_receipts,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_helpers import (
    mapping as _mapping,
)
from med_autoscience.controllers.domain_health_diagnostic_parts.provider_admission_report_closeout_identity import (
    closeout_core_identity_matches_candidate as _closeout_core_identity_matches_candidate,
)
from med_autoscience.controllers.opl_transition_readback import (
    provider_admission_opl_transition_readback,
)

UNSUPPORTED_DISPATCH_SURFACE_BLOCKER = "unsupported_dispatch_surface"


def provider_admission_readback_overrides_blocking_closeout(
    candidate: Mapping[str, Any],
    *,
    closeout: Mapping[str, Any],
) -> bool:
    return bool(
        provider_admission_opl_transition_readback(candidate)
        and _receipt_has_unsupported_dispatch_surface_blocker(closeout)
    )


def weak_identity_is_opl_authorization_stage_packet_gap(
    candidate: Mapping[str, Any],
    *,
    scanned_study: Mapping[str, Any],
    weak_identity: Mapping[str, Any],
) -> bool:
    if (
        _non_empty_text(candidate.get("source"))
        != "opl_current_control_state.study_current_executable_owner_action"
    ):
        return False
    missing = {
        _non_empty_text(field)
        for field in weak_identity.get("missing_identity_fields") or []
        if _non_empty_text(field) is not None
    }
    if missing != {"stage_packet_ref_or_refs"}:
        return False
    return any(
        current_control_receipts.receipt_is_accepted_closeout(receipt)
        and current_control_receipts.receipt_has_opl_execution_authorization_blocker(receipt)
        and (
            _closeout_core_identity_matches_candidate(receipt, identity=candidate)
            or _opl_authorization_blocker_observed_work_unit_matches_candidate(
                receipt,
                candidate=candidate,
            )
        )
        for receipt in _accepted_closeout_receipts(scanned_study)
    )


def _receipt_has_unsupported_dispatch_surface_blocker(receipt: Mapping[str, Any]) -> bool:
    typed_blocker = _mapping(receipt.get("typed_blocker"))
    values = (
        receipt.get("blocked_reason"),
        receipt.get("typed_blocker_reason"),
        receipt.get("outcome"),
        typed_blocker.get("blocker_id"),
        typed_blocker.get("blocker_type"),
        typed_blocker.get("blocker_kind"),
        typed_blocker.get("blocked_reason"),
        typed_blocker.get("reason"),
    )
    return any(_text_is_unsupported_dispatch_surface_blocker(value) for value in values)


def _text_is_unsupported_dispatch_surface_blocker(value: Any) -> bool:
    text = _non_empty_text(value)
    if text is None:
        return False
    if text == UNSUPPORTED_DISPATCH_SURFACE_BLOCKER:
        return True
    return text.startswith("blocked:") and (
        text.removeprefix("blocked:") == UNSUPPORTED_DISPATCH_SURFACE_BLOCKER
    )


def _opl_authorization_blocker_observed_work_unit_matches_candidate(
    receipt: Mapping[str, Any],
    *,
    candidate: Mapping[str, Any],
) -> bool:
    context = _mapping(receipt.get("blocker_context"))
    observed_work_unit = _non_empty_text(
        context.get("observed_stage_attempt_work_unit_id")
    )
    candidate_work_unit = _non_empty_text(candidate.get("work_unit_id")) or _non_empty_text(
        candidate.get("next_work_unit")
    )
    return observed_work_unit is not None and observed_work_unit == candidate_work_unit
