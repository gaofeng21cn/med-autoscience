from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Any


Text = Callable[[object], str | None]
AsMapping = Callable[[object], dict[str, Any]]


def transition_request_record_extra_fields(
    dispatch: Mapping[str, Any],
    *,
    text: Text,
    mapping: AsMapping,
) -> dict[str, Any]:
    return {
        "adapter_kind": text(dispatch.get("adapter_kind")),
        "executor_kind": text(dispatch.get("executor_kind")),
        "executor_name": text(dispatch.get("executor_name")),
        "executor_mode": text(dispatch.get("executor_mode")),
        "default_model_policy": text(dispatch.get("default_model_policy")),
        "default_reasoning_effort_policy": text(dispatch.get("default_reasoning_effort_policy")),
        "chat_completion_only_executor_forbidden": dispatch.get(
            "chat_completion_only_executor_forbidden"
        ),
        "owner_callable_adapter_contract": mapping(dispatch.get("owner_callable_adapter_contract")) or None,
        "dispatch_ready_for_execution_authority": dispatch.get(
            "dispatch_ready_for_execution_authority"
        ),
        "repeat_suppressed": dispatch.get("repeat_suppressed"),
        "why_not_applied": text(dispatch.get("why_not_applied")),
        "repeat_suppression": mapping(dispatch.get("repeat_suppression")) or None,
        "mas_local_dispatch_carrier_persistence": text(
            dispatch.get("mas_local_dispatch_carrier_persistence")
        ),
        "owner_callable_adapter_diagnostic_only": dispatch.get(
            "owner_callable_adapter_diagnostic_only"
        ),
        "owner_callable_adapter_readiness_authority": dispatch.get(
            "owner_callable_adapter_readiness_authority"
        ),
        "owner_callable_adapter_can_create_success_outcome": dispatch.get(
            "owner_callable_adapter_can_create_success_outcome"
        ),
        "owner_callable_carrier_projection_only": dispatch.get(
            "owner_callable_carrier_projection_only"
        ),
        "projection_only": dispatch.get("projection_only"),
        "mas_materializes_domain_intent": dispatch.get("mas_materializes_domain_intent"),
        "surface_key": text(dispatch.get("surface_key")),
        "required_output_target_surface": mapping(dispatch.get("required_output_target_surface")) or None,
        "operator_payload_present": dispatch.get("operator_payload_present"),
        "operator_payload_ref": text(dispatch.get("operator_payload_ref")),
        "operator_payload": mapping(dispatch.get("operator_payload")) or None,
        "payload_authoring_target": mapping(dispatch.get("payload_authoring_target")) or None,
        "readiness_surface_identity": mapping(dispatch.get("readiness_surface_identity")) or None,
        "record_production_satisfaction": mapping(dispatch.get("record_production_satisfaction")) or None,
        "owner_route_attempt_envelope": mapping(dispatch.get("owner_route_attempt_envelope")) or None,
        "medical_claim_authoring_allowed": dispatch.get("medical_claim_authoring_allowed"),
        "paper_package_mutation_allowed": dispatch.get("paper_package_mutation_allowed"),
        "quality_gate_relaxation_allowed": dispatch.get("quality_gate_relaxation_allowed"),
        "manual_study_patch_allowed": dispatch.get("manual_study_patch_allowed"),
        "source_action_runtime_completion_fields_omitted": dispatch.get(
            "source_action_runtime_completion_fields_omitted"
        ),
    }


__all__ = ["transition_request_record_extra_fields"]
