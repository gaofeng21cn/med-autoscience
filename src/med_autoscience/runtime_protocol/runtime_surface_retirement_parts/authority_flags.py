from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any


FORBIDDEN_TRUE_AUTHORITY_FLAGS = frozenset(
    {
        "can_create_opl_command",
        "can_create_opl_event",
        "can_create_opl_outbox",
        "can_create_opl_stage_run",
        "can_generate_next_action_authority",
        "can_authorize_provider_admission",
        "can_authorize_quality_verdict",
        "can_authorize_publication_ready",
        "can_authorize_generic_cleanup_policy",
        "can_authorize_artifact_mutation",
        "can_claim_runtime_currentness",
        "can_claim_paper_progress",
        "can_write_domain_truth",
        "can_write_publication_eval",
        "can_write_controller_decision",
        "started_worker",
        "outbox_record",
        "stores_body",
        "stores_domain_truth",
        "mas_can_authorize_provider_admission",
        "mas_can_create_opl_outbox_event_or_stage_run",
        "mas_can_create_opl_command_event_or_outbox",
        "mas_can_choose_supervisor_decision",
        "mas_can_mutate_recovery_obligation_store",
        "mas_can_run_supervisor_decision_engine",
        "paper_recovery_state_can_build_decision",
        "read_model_can_run_supervisor_decision_engine",
        "study_progress_supervisor_projection_can_build_decision",
        "actuator_can_write_private_blocker_surface",
        "active_caller_retains_authority",
        "active_caller_retains_runtime_authority",
        "can_write_fail_closed_typed_control_blocker",
        "closeout_binding_authorizes_execution",
        "actuator_private_write_authority",
        "stage_closeout_packets_can_authorize_provider_admission",
        "stage_closeout_packets_can_authorize_execution",
        "stage_closeout_packets_can_create_provider_attempt",
        "stage_closeout_packets_can_create_opl_event_outbox_or_stage_run",
        "stage_closeout_packets_can_claim_running_or_progress",
        "stage_closeout_packets_can_satisfy_current_receipt_without_owner_result",
        "dispatch_ref_stage_packet_identity_recovery_is_authority",
        "latest_wire_surface_is_stage_run_abi",
        "mas_selector_authority",
        "mas_tool_invocation_runtime_authority",
        "polluted_source_payload_can_authorize_provider_admission",
        "polluted_source_payload_can_create_opl_event_outbox_or_stage_run",
        "polluted_source_payload_can_satisfy_opl_readback",
        "wildcard_action_triggers_auto_select",
        "wildcard_action_triggers_can_select_without_explicit_capability_request",
        "missing_explicit_capability_request_can_auto_select_wildcard_sidecar",
        "wildcard_sidecar_can_block_current_owner_action",
        "body_authority",
        "owner_callable_adapter_counts_authority",
        "transition_request_projection_body_authority",
        "mas_can_create_stage_run",
        "provider_admission_pending",
        "request_only_carrier_can_authorize_provider_admission",
    }
)


def truthy_authority_flags(value: Any, path: tuple[str, ...] = ()) -> list[str]:
    matches: list[str] = []
    if isinstance(value, Mapping):
        for key, nested_value in value.items():
            key_text = str(key)
            nested_path = (*path, key_text)
            if key_text in FORBIDDEN_TRUE_AUTHORITY_FLAGS and nested_value is True:
                matches.append(".".join(nested_path))
            matches.extend(truthy_authority_flags(nested_value, nested_path))
    elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        for index, nested_value in enumerate(value):
            matches.extend(truthy_authority_flags(nested_value, (*path, str(index))))
    return matches
