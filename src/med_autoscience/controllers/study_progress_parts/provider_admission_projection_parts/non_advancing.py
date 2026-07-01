from __future__ import annotations

from typing import Any, Mapping

from ..shared import _mapping_copy, _non_empty_text


def non_advancing_apply_consumption_projection(
    candidate: Mapping[str, Any],
    *,
    readback: Mapping[str, Any],
) -> dict[str, Any]:
    identity = _mapping_copy(readback.get("identity"))
    aggregate_identity = _mapping_copy(identity.get("aggregate_identity"))
    stage_run_identity = _mapping_copy(identity.get("stage_run_identity"))
    latest_transaction = _mapping_copy(readback.get("latest_transaction_readback"))
    return {
        key: value
        for key, value in {
            "surface_kind": "opl_transition_non_advancing_apply_consumed",
            "source": "opl_domain_progress_transition_runtime_live_readback",
            "blocker_type": "non_advancing_apply",
            "blocked_reason": "opl_transition_request_missing_for_authorized_stage_packet",
            "study_id": _non_empty_text(candidate.get("study_id"))
            or _non_empty_text(aggregate_identity.get("study_id")),
            "action_type": _non_empty_text(candidate.get("action_type")),
            "work_unit_id": _non_empty_text(candidate.get("work_unit_id"))
            or _non_empty_text(aggregate_identity.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(candidate.get("work_unit_fingerprint"))
            or _non_empty_text(candidate.get("action_fingerprint"))
            or _non_empty_text(aggregate_identity.get("work_unit_fingerprint")),
            "route_identity_key": _non_empty_text(candidate.get("route_identity_key"))
            or _non_empty_text(stage_run_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(candidate.get("attempt_idempotency_key"))
            or _non_empty_text(stage_run_identity.get("attempt_idempotency_key")),
            "event_id": _non_empty_text(identity.get("latest_event_id"))
            or _non_empty_text(latest_transaction.get("event_id")),
            "outbox_item_id": _non_empty_text(identity.get("latest_outbox_item_id"))
            or _non_empty_text(latest_transaction.get("outbox_item_id")),
            "transaction_id": _non_empty_text(identity.get("latest_transaction_id"))
            or _non_empty_text(latest_transaction.get("transaction_id")),
            "provider_admission_allowed": False,
            "current_executable_owner_action_allowed": False,
            "paper_progress_delta": False,
            "provider_completion_is_domain_completion": False,
            "authority_boundary": {
                "projection_only": True,
                "runtime_owner": "one-person-lab",
                "domain_truth_owner": "med-autoscience",
                "can_authorize_provider_admission": False,
                "can_start_provider_attempt": False,
                "provider_running_is_paper_progress": False,
                "provider_completion_is_domain_completion": False,
                "paper_progress_delta": False,
            },
        }.items()
        if value not in (None, "", [], {})
    }
