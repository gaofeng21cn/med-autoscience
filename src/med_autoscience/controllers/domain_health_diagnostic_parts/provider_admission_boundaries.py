from __future__ import annotations

from collections.abc import Mapping
from typing import Any


PROVIDER_ADMISSION_AUTHORITY_BOUNDARY = {
    "surface_kind": "opl_provider_admission_candidate",
    "authority": "mas_provider_admission_identity",
    "stage_transition_authority": "OPL Stage Transition Authority",
    "stage_authority_role": "non_authoritative_observation_and_intent_producer",
    "can_write_stage_current_pointer": False,
    "can_write_current_owner_delta": False,
    "can_write_stage_terminal_state": False,
    "can_write_runtime_owned_surfaces": False,
    "can_mark_provider_attempt_running": False,
    "provider_completion_is_domain_completion": False,
}

STAGE_TRANSITION_AUTHORITY_BOUNDARY = {
    "producer_kind": "runtime_provider",
    "intent_kind": "provider_observation",
    "stage_transition_authority": "one-person-lab",
    "intent_can_write_stage_current_pointer": False,
    "intent_can_write_stage_run_terminal_state": False,
    "intent_can_publish_current_owner_delta": False,
    "intent_can_write_domain_truth": False,
    "intent_can_create_owner_receipt": False,
    "intent_can_create_typed_blocker": False,
    "provider_completion_counts_as_stage_transition": False,
    "read_model_update_counts_as_stage_transition": False,
    "worklist_update_counts_as_stage_transition": False,
    "evidence_event_counts_as_stage_transition": False,
    "agent_lab_output_counts_as_stage_transition": False,
}


def provider_admission_authority_boundary(value: object = None) -> dict[str, Any]:
    return {
        **_mapping(value),
        **PROVIDER_ADMISSION_AUTHORITY_BOUNDARY,
    }


def stage_transition_authority_boundary(value: object = None) -> dict[str, Any]:
    return {
        **_mapping(value),
        **STAGE_TRANSITION_AUTHORITY_BOUNDARY,
    }


def provider_admission_candidate_with_authority_boundaries(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        **dict(candidate),
        "authority_boundary": provider_admission_authority_boundary(
            candidate.get("authority_boundary")
        ),
        "stage_transition_authority_boundary": stage_transition_authority_boundary(
            candidate.get("stage_transition_authority_boundary")
        ),
        "provider_completion_is_domain_completion": False,
    }


def provider_admission_authority_transport_fields(
    candidate: Mapping[str, Any],
) -> dict[str, Any]:
    normalized = provider_admission_candidate_with_authority_boundaries(candidate)
    return {
        "authority_boundary": normalized["authority_boundary"],
        "stage_transition_authority_boundary": normalized[
            "stage_transition_authority_boundary"
        ],
        "provider_completion_is_domain_completion": False,
    }


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}
