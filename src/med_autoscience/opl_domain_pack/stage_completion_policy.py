from __future__ import annotations

from typing import Any


STAGE_COMPLETION_POLICY: dict[str, Any] = {
    "surface_kind": "domain_stage_completion_policy",
    "version": "domain-stage-completion-policy.v1",
    "owner": "one-person-lab",
    "standard_agent_requirement": (
        "domain_stage_owns_completion_judgment_and_emits_standard_closeout_packet"
    ),
    "completion_judgment_owner": "domain_stage",
    "closeout_packet_required": True,
    "provider_completion_is_domain_completion": False,
    "opl_content_judgment_allowed": False,
    "next_stage_transition_owner": "opl_runtime",
    "required_closeout_outcomes": [
        "completed_and_continue",
        "completed_and_wait_owner",
        "route_back",
        "blocked",
        "rejected",
    ],
    "accepted_closeout_ref_fields": [
        "owner_receipt_ref",
        "typed_blocker_ref",
        "human_gate_ref",
        "route_back_ref",
    ],
    "authority_boundary": {
        "opl_can_decide_domain_completion": False,
        "provider_completion_counts_as_stage_complete": False,
        "file_presence_counts_as_stage_complete": False,
        "suite_pass_counts_as_stage_complete": False,
        "conformance_pass_counts_as_stage_complete": False,
    },
}
