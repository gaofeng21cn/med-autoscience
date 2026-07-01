from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from med_autoscience.controllers.opl_transition_readback import (
    candidate_opl_transition_readback,
    non_advancing_apply_opl_transition_readback,
)

from ..opl_current_control_state_handoff_values import _observability_mapping, _work_unit_identity
from ..shared_base import _non_empty_text


def copy_opl_transition_readback_fields(
    projection: dict[str, Any],
    source: Mapping[str, Any],
) -> None:
    readback = candidate_opl_transition_readback(source)
    if not readback:
        return
    projection["opl_domain_progress_transition_runtime_live_readback"] = readback
    projection["provider_admission_identity"] = provider_admission_identity_from_readback(readback)
    apply_non_advancing_apply_readback_to_handoff(projection, source=source, readback=readback)


def apply_non_advancing_apply_readback_to_handoff(
    projection: dict[str, Any],
    *,
    source: Mapping[str, Any],
    readback: Mapping[str, Any],
) -> None:
    readback_container = _observability_mapping(
        source.get("domain_progress_transition_non_advancing_apply_readback")
    )
    non_advancing = non_advancing_apply_opl_transition_readback(
        {
            **readback_container,
            "opl_domain_progress_transition_runtime_live_readback": readback,
        }
    )
    if not non_advancing:
        return
    readback_identity = provider_admission_identity_from_readback(non_advancing)
    study_id = (
        _non_empty_text(projection.get("study_id"))
        or _non_empty_text(readback_identity.get("study_id"))
    )
    action_type = (
        _non_empty_text(readback_container.get("action_type"))
        or _non_empty_text(projection.get("action_type"))
        or _non_empty_text(_observability_mapping(non_advancing.get("identity")).get("transition_kind"))
    )
    work_unit_id = _work_unit_identity(readback_container.get("work_unit_id")) or _work_unit_identity(
        readback_identity.get("work_unit_id")
    )
    work_unit_fingerprint = (
        _non_empty_text(readback_container.get("work_unit_fingerprint"))
        or _non_empty_text(readback_identity.get("work_unit_fingerprint"))
    )
    typed_blocker = {
        key: value
        for key, value in {
            "surface_kind": "mas_current_control_typed_blocker_projection",
            "blocker_type": "non_advancing_apply",
            "blocked_reason": _non_empty_text(readback_container.get("reason"))
            or "opl_transition_request_missing_for_authorized_stage_packet",
            "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
            "owner": "one-person-lab",
            "study_id": study_id,
            "quest_id": study_id,
            "action_type": action_type,
            "work_unit_id": work_unit_id,
            "work_unit_fingerprint": work_unit_fingerprint,
            "action_fingerprint": work_unit_fingerprint,
            "route_identity_key": _non_empty_text(readback_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(readback_identity.get("attempt_idempotency_key")),
            "request_idempotency_key": _non_empty_text(readback_identity.get("request_idempotency_key")),
            "stage_run_id": _non_empty_text(readback_identity.get("stage_run_id")),
            "event_id": _non_empty_text(readback_identity.get("event_id")),
            "outbox_item_id": _non_empty_text(readback_identity.get("outbox_item_id")),
            "transaction_id": _non_empty_text(readback_identity.get("transaction_id")),
            "non_advancing_apply": True,
            "provider_admission_allowed": False,
            "current_executable_owner_action_allowed": False,
            "paper_progress_delta": False,
            "provider_completion_is_domain_completion": False,
            "authority_boundary": non_advancing_apply_authority_boundary(readback_container),
        }.items()
        if value not in (None, "", [], {})
    }
    projection["running_provider_attempt"] = False
    projection["active_run_id"] = None
    projection["active_workflow_id"] = None
    projection["current_executable_owner_action"] = None
    projection["provider_admission_pending_count"] = 0
    projection["provider_admission_candidates"] = []
    projection["transition_request_pending_count"] = 0
    projection["transition_request_candidates"] = []
    projection["blocked_reason"] = typed_blocker["blocked_reason"]
    projection["next_owner"] = "one-person-lab"
    projection["typed_blocker"] = typed_blocker
    projection["current_work_unit"] = {
        "surface_kind": "current_work_unit",
        "schema_version": 1,
        "status": "typed_blocker",
        "study_id": study_id,
        "quest_id": study_id,
        "owner": "one-person-lab",
        "action_type": action_type,
        "work_unit_id": work_unit_id,
        "work_unit_fingerprint": work_unit_fingerprint,
        "action_fingerprint": work_unit_fingerprint,
        "state": {
            "state_kind": "typed_blocker",
            "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
            "typed_blocker": typed_blocker,
        },
    }
    projection["current_execution_envelope"] = {
        "state_kind": "typed_blocker",
        "owner": "one-person-lab",
        "source": "opl_current_control_state.domain_progress_transition_non_advancing_apply_readback",
        "typed_blocker": typed_blocker,
    }
    projection["domain_progress_transition_non_advancing_apply_readback"] = dict(readback_container)
    projection["domain_progress_transition_projection_metadata"] = _observability_mapping(
        source.get("domain_progress_transition_projection_metadata")
    )


def non_advancing_apply_authority_boundary(readback_container: Mapping[str, Any]) -> dict[str, Any]:
    boundary = _observability_mapping(readback_container.get("authority_boundary"))
    return {
        **boundary,
        "projection_only": True,
        "runtime_owner": "one-person-lab",
        "domain_truth_owner": "med-autoscience",
        "can_authorize_provider_admission": False,
        "can_start_provider_attempt": False,
        "provider_running_is_paper_progress": False,
        "provider_completion_is_domain_completion": False,
        "paper_progress_delta": False,
    }


def provider_admission_identity_from_readback(readback: Mapping[str, Any]) -> dict[str, Any]:
    identity = _observability_mapping(readback.get("identity"))
    aggregate_identity = _observability_mapping(identity.get("aggregate_identity"))
    stage_run_identity = _observability_mapping(identity.get("stage_run_identity"))
    return {
        key: value
        for key, value in {
            "study_id": _non_empty_text(aggregate_identity.get("study_id")),
            "work_unit_id": _work_unit_identity(aggregate_identity.get("work_unit_id")),
            "work_unit_fingerprint": _non_empty_text(
                aggregate_identity.get("work_unit_fingerprint")
            ),
            "route_identity_key": _non_empty_text(stage_run_identity.get("route_identity_key")),
            "attempt_idempotency_key": _non_empty_text(
                stage_run_identity.get("attempt_idempotency_key")
            ),
            "request_idempotency_key": _non_empty_text(identity.get("idempotency_key"))
            or _non_empty_text(identity.get("request_idempotency_key")),
            "stage_run_id": _non_empty_text(stage_run_identity.get("stage_run_id")),
            "event_id": _non_empty_text(identity.get("latest_event_id"))
            or _non_empty_text(identity.get("event_id")),
            "outbox_item_id": _non_empty_text(identity.get("latest_outbox_item_id"))
            or _non_empty_text(identity.get("outbox_item_id")),
            "transaction_id": _non_empty_text(identity.get("latest_transaction_id"))
            or _non_empty_text(identity.get("transaction_id")),
        }.items()
        if value is not None
    }


__all__ = [
    "apply_non_advancing_apply_readback_to_handoff",
    "copy_opl_transition_readback_fields",
    "non_advancing_apply_authority_boundary",
    "provider_admission_identity_from_readback",
]
