from __future__ import annotations

from typing import Any


def default_executor_typed_closeout_contract(*, action_type: str) -> dict[str, Any]:
    return {
        "typed_closeout_required_for_completion": True,
        "free_text_closeout_accepted": False,
        "accepted_surface_kinds": [
            "stage_attempt_closeout_packet",
            "stage_memory_closeout_packet",
            "domain_stage_closeout_packet",
        ],
        "required_ref_field": "closeout_refs",
        "minimum_closeout_refs": 1,
        "completion_boundary": {
            "provider_completion": "typed_closeout_packet_observed",
            "domain_ready_verdict": "read_from_mas_publication_or_gate_surface",
            "provider_completion_is_domain_ready": False,
        },
        "authority_boundary": {
            "opl": "closeout_transport_only",
            "mas": "truth_quality_artifact_gate_owner",
        },
        "terminal_output_instruction": (
            "After completing the MAS owner-authorized work or identifying a typed blocker, "
            "end the response with exactly one JSON object whose surface_kind is one of "
            "stage_attempt_closeout_packet, stage_memory_closeout_packet, or "
            "domain_stage_closeout_packet. Include closeout_refs with the owner receipt, "
            "artifact delta, or typed blocker evidence refs. Do not use prose as the final "
            "completion signal."
        ),
        "action_type": action_type,
    }


__all__ = ["default_executor_typed_closeout_contract"]
