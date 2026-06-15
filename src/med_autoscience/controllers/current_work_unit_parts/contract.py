from __future__ import annotations


SURFACE_KIND = "current_work_unit"
SCHEMA_VERSION = 1
ALLOWED_STATUSES = (
    "executable_owner_action",
    "running_provider_attempt",
    "owner_receipt_recorded",
    "typed_blocker",
    "blocked_current_work_unit",
)
AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_current_work_unit_reducer",
    "top_level_truth": "status",
    "stage_transition_authority": "OPL Stage Transition Authority",
    "stage_authority_role": "non_authoritative_observation_and_intent_producer",
    "allowed_statuses": list(ALLOWED_STATUSES),
    "mas_owner_authority_preserved": True,
    "can_write_stage_current_pointer": False,
    "can_write_current_owner_delta": False,
    "can_write_stage_terminal_state": False,
    "can_write_runtime_owned_surfaces": False,
    "can_write_paper_or_package": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_publication_ready": False,
}


__all__ = [
    "ALLOWED_STATUSES",
    "AUTHORITY_BOUNDARY",
    "SCHEMA_VERSION",
    "SURFACE_KIND",
]
