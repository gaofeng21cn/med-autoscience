from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RUNTIME_ID = "opl_domain_progress_transition_runtime"
RUNTIME_OWNER = "one-person-lab"
RUNTIME_KIND = "DomainProgressTransitionRuntime"
LIVE_READBACK_SURFACE = "opl_domain_progress_transition_runtime_live_readback"
LIVE_READBACK_COMPLETE_STATUS = "complete_transaction"
PROVIDER_ADMISSION_OUTCOME = "provider_admission_enqueued_or_blocked"
NON_ADVANCING_APPLY_OUTCOME = "non_advancing_apply_typed_blocker_ref"
CONTRACT_REF = "contracts/opl_domain_progress_transition_runtime_contract.json"
OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_OUTPUT_KIND = "opl_domain_route_transition_receipt"
NEXT_ACTION_IDENTITY_FIELDS = (
    "action_id",
    "idempotency_key",
    "action_family",
    "expected_output_contract.output_kind",
)

TRANSITION_KINDS = (
    "ConsumeOwnerReceipt",
    "StartProviderAttempt",
    "ConsumeTerminalCloseout",
    "RecordTypedBlocker",
    "OpenHumanGate",
    "MaterializeOwnerAction",
    "AdoptPaperDelta",
    "AdoptRouteBackEvidence",
    "StopLoss",
    "NonAdvancingApply",
)

REQUIRED_READBACK_SECTIONS = (
    "identity",
    "causality",
    "authority_boundary",
    "exactly_one_outcome",
    "projection_metadata",
)

REQUIRED_RUNTIME_REFS = (
    "event_id",
    "outbox_item_id",
    "stage_run_identity",
)

LIVE_READBACK_IDENTITY_TRANSACTION_REFS = (
    "latest_event_id",
    "latest_outbox_item_id",
    "latest_transaction_id",
)

LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS = (
    "command_present",
    "event_present",
    "outbox_item_present",
    "same_transaction_event_and_outbox",
)

LIVE_READBACK_CAUSALITY_TRANSACTION_REF_FIELDS = (
    "event_id",
    "outbox_item_id",
    "transaction_id",
)

LIVE_READBACK_LATEST_TRANSACTION_REF_FIELDS = (
    "event_id",
    "outbox_item_id",
    "transaction_id",
    "transition_event_id",
    "outbox_transition_event_id",
)

LIVE_READBACK_READ_MODEL_SECTIONS = (
    "identity",
    "causality",
    "authority_boundary",
    "exactly_one_outcome",
    "projection_metadata",
)

LIVE_READBACK_CLAIMABLE_SOURCE_KINDS = (
    "opl_runtime_live_readback",
    "opl_current_control_live_readback",
    "opl_stagerun_live_readback",
)

LIVE_READBACK_NON_CLAIMABLE_SOURCE_KINDS = (
    "fixture_or_replay_readback",
    "unit_test_helper_readback",
    "mas_projection_payload",
    "historical_log_extract",
)

LIVE_READBACK_TRANSACTION_CONSISTENCY = {
    "identity_latest_refs_match_causality": True,
    "identity_latest_refs_match_latest_transaction_readback": True,
    "read_model_rebuild_matches_live_sections": True,
    "projection_metadata_derived_from_event_id_matches_identity_latest_event_id": True,
    "latest_transaction_requires_command_event_outbox": True,
    "same_transaction_event_and_outbox": True,
}

PROVIDER_ADMISSION_READBACK_IDENTITY_FIELDS = (
    "study_id",
    "work_unit_id",
    "work_unit_fingerprint",
    "route_identity_key",
    "attempt_idempotency_key",
)

PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD = "request_idempotency_key"

FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS = (
    "current_control_command",
    "current_control_command_outbox_record",
    "opl_domain_progress_command",
    "opl_domain_progress_command_outbox_record",
    "opl_domain_progress_transition_event",
    "opl_domain_progress_transition_outbox_item",
    "opl_event_log_record",
    "opl_outbox_record",
    "projection_metadata",
    "read_model_generation_metadata",
    "stage_run",
    "stage_run_identity",
    "fixed_point_reconciler_state",
)

MAS_PROJECTION_CANNOT_REPLACE = (
    "opl_command",
    "opl_event",
    "opl_transactional_outbox",
    "opl_stage_run",
    "opl_provider_admission",
    "opl_fixed_point_reconcile",
)

TRANSITION_SPINE_BOUNDARIES = (
    "DomainIntent",
    "OPL Command",
    "OPL Event",
    "TransactionalOutbox",
    "StageRun",
    "MAS OwnerAnswer",
    "DerivedProjection",
)

TRANSITION_SPINE_FIELD_FAMILIES = (
    "identity",
    "causality",
    "authority_boundary",
    "exactly_one_outcome",
    "projection_metadata",
)

TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS = {
    "event_present_is_paper_progress": False,
    "outbox_emitted_is_paper_progress": False,
    "provider_completion_is_paper_progress": False,
    "provider_completion_is_mas_owner_answer": False,
    "projection_fresh_is_paper_progress": False,
    "queue_empty_is_paper_progress": False,
    "trace_visible_is_paper_progress": False,
    "stage_run_terminal_is_mas_owner_answer": False,
}

TRANSITION_SPINE_BOUNDARY_ABI: dict[str, dict[str, Any]] = {
    "DomainIntent": {
        "boundary": "DomainIntent",
        "owner": "med-autoscience",
        "role": "MAS declares current medical research intent and forbidden authority.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "study_id",
                "quest_id",
                "stage_id",
                "current_owner_action_id",
                "intent_idempotency_key",
            ],
            "causality": [
                "source_generation",
                "policy_result_ref",
                "required_refs",
            ],
            "authority_boundary": [
                "intent_owner",
                "target_runtime_owner",
                "forbidden_authority",
            ],
            "exactly_one_outcome": [
                "accepted_owner_answer_shape",
                "expected_runtime_receipt_kind",
            ],
            "projection_metadata": [
                "projection_role",
                "authority",
                "contract_ref",
            ],
        },
        "authority_boundary": {
            "domain_intent_owner": "med-autoscience",
            "runtime_execution_owner": RUNTIME_OWNER,
            "mas_can_create_opl_command": False,
            "mas_can_create_opl_event": False,
            "mas_can_create_opl_outbox_item": False,
            "mas_can_create_stage_run": False,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
    "OPL Command": {
        "boundary": "OPL Command",
        "owner": RUNTIME_OWNER,
        "role": "OPL normalizes MAS intent into an idempotent command.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "aggregate_id",
                "command_id",
                "expected_version",
                "idempotency_key",
            ],
            "causality": [
                "domain_intent_ref",
                "source_generation",
                "precondition_refs",
            ],
            "authority_boundary": [
                "command_owner",
                "domain_authority_owner",
                "allowed_side_effect_target",
            ],
            "exactly_one_outcome": [
                "transition_kind",
                "expected_event_type",
                "expected_outbox_effect",
            ],
            "projection_metadata": [
                "not_a_projection",
                "read_model_authority",
                "contract_ref",
            ],
        },
        "authority_boundary": {
            "command_owner": RUNTIME_OWNER,
            "can_sign_mas_owner_answer": False,
            "can_claim_paper_progress": False,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
    "OPL Event": {
        "boundary": "OPL Event",
        "owner": RUNTIME_OWNER,
        "role": "OPL records the committed transition fact in append-only history.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "aggregate_id",
                "event_id",
                "aggregate_version",
                "transition_kind",
            ],
            "causality": [
                "command_id",
                "causal_event_id",
                "transaction_id",
            ],
            "authority_boundary": [
                "event_owner",
                "event_is_runtime_fact_only",
                "domain_completion_owner",
            ],
            "exactly_one_outcome": [
                "outcome_kind",
                "outcome_ref",
                "non_advancing_apply_allowed",
            ],
            "projection_metadata": [
                "append_only",
                "replayable",
                "projection_source",
            ],
        },
        "authority_boundary": {
            "event_owner": RUNTIME_OWNER,
            "event_is_paper_progress": False,
            "mas_owner_answer_required_for_domain_completion": True,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
    "TransactionalOutbox": {
        "boundary": "TransactionalOutbox",
        "owner": RUNTIME_OWNER,
        "role": "OPL stores transition side effects in the same transaction as the event.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "outbox_item_id",
                "aggregate_id",
                "transaction_id",
                "idempotency_key",
            ],
            "causality": [
                "event_id",
                "command_id",
                "side_effect_target",
            ],
            "authority_boundary": [
                "outbox_owner",
                "side_effect_transport_owner",
                "domain_authority_owner",
            ],
            "exactly_one_outcome": [
                "side_effect_kind",
                "dispatch_status",
                "terminal_or_pending_ref",
            ],
            "projection_metadata": [
                "derived_from_event_id",
                "outbox_generation",
                "authority",
            ],
        },
        "authority_boundary": {
            "outbox_owner": RUNTIME_OWNER,
            "outbox_emitted_is_paper_progress": False,
            "mas_can_create_outbox_item": False,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
    "StageRun": {
        "boundary": "StageRun",
        "owner": RUNTIME_OWNER,
        "role": "OPL owns provider attempt, tool invocation, lease, retry, and closeout transport.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "stage_run_id",
                "route_identity_key",
                "attempt_idempotency_key",
                "selected_packet_ref",
            ],
            "causality": [
                "outbox_item_id",
                "event_id",
                "provider_attempt_ref",
            ],
            "authority_boundary": [
                "stage_run_owner",
                "provider_transport_owner",
                "domain_answer_owner",
            ],
            "exactly_one_outcome": [
                "running_proof_ref",
                "terminal_closeout_ref",
                "human_gate_transport_ref",
            ],
            "projection_metadata": [
                "currentness_identity",
                "observed_generation",
                "authority",
            ],
        },
        "authority_boundary": {
            "stage_run_owner": RUNTIME_OWNER,
            "provider_completion_is_mas_owner_answer": False,
            "stage_run_terminal_is_paper_progress": False,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
    "MAS OwnerAnswer": {
        "boundary": "MAS OwnerAnswer",
        "owner": "med-autoscience",
        "role": "MAS consumes closeout, tool output, or human answer into domain authority.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "study_id",
                "quest_id",
                "owner_answer_id",
                "current_owner_action_id",
            ],
            "causality": [
                "stage_run_closeout_ref",
                "tool_output_ref",
                "human_answer_ref",
            ],
            "authority_boundary": [
                "owner_answer_owner",
                "domain_authority_ref",
                "forbidden_runtime_write_boundary",
            ],
            "exactly_one_outcome": [
                "owner_receipt_ref",
                "typed_blocker_ref",
                "human_gate_ref",
                "route_back_evidence_ref",
                "paper_or_artifact_delta_ref",
            ],
            "projection_metadata": [
                "accepted_event_id",
                "accepted_stage_run_id",
                "authority",
            ],
        },
        "authority_boundary": {
            "owner_answer_owner": "med-autoscience",
            "can_claim_paper_progress_when_receipt_or_delta_accepted": True,
            "can_create_opl_event": False,
            "can_create_opl_outbox_item": False,
            "can_mark_provider_running": False,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
    "DerivedProjection": {
        "boundary": "DerivedProjection",
        "owner": "derived-projection-plane",
        "role": "Status, diagnostic, workbench, trace, and lineage are rebuildable projections.",
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "required_minimal_fields": {
            "identity": [
                "projection_id",
                "study_id",
                "quest_id",
                "current_owner_action_id",
            ],
            "causality": [
                "derived_from_event_id",
                "derived_from_owner_answer_id",
                "source_generation",
            ],
            "authority_boundary": [
                "projection_owner",
                "authority",
                "cannot_select_next_action",
            ],
            "exactly_one_outcome": [
                "projected_outcome_kind",
                "projected_outcome_ref",
                "non_authoritative_status",
            ],
            "projection_metadata": [
                "derived_from_event_id",
                "observed_generation",
                "lag_status",
                "authority",
            ],
        },
        "authority_boundary": {
            "projection_owner": "derived-projection-plane",
            "authority": False,
            "can_select_next_action": False,
            "can_claim_paper_progress": False,
            "rebuildable_from_event_and_owner_answer": True,
        },
        "forbidden_authority_flags": dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS),
    },
}


def opl_transition_receipt_expected_output_contract() -> dict[str, Any]:
    return {
        "output_kind": OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_OUTPUT_KIND,
        "accepted_refs": [
            "domain_route_handoff_ref",
            "domain_route_transaction_ref",
            "domain_route_command_ref",
            "stage_attempt_ref",
            "runtime_closeout_ref",
            "typed_runtime_blocker_ref",
        ],
        "receipt_owner": RUNTIME_OWNER,
        "domain_completion_owner": "MedAutoScience",
    }


def opl_transition_receipt_authority_boundary() -> dict[str, Any]:
    return {
        "runtime_receipt_owner": RUNTIME_OWNER,
        "receipt_is_input_ref_only": True,
        "can_claim_stage_complete": False,
        "can_claim_paper_progress": False,
        "can_claim_submission_ready": False,
        "can_claim_publication_ready": False,
        "queue_terminal_is_paper_progress": False,
        "attempt_terminal_is_paper_progress": False,
        "provider_completion_is_domain_completion": False,
        "provider_completion_is_stage_complete": False,
        "mas_receipt_consumer_required_for_paper_progress": True,
    }


def next_action_identity(next_action: Mapping[str, Any]) -> dict[str, Any]:
    expected_output_contract = _mapping(next_action.get("expected_output_contract"))
    output_kind = _text(expected_output_contract.get("output_kind"))
    identity = {
        "surface_kind": "opl_next_action_identity",
        "identity_source": "NextActionEnvelope",
        "next_action_surface_kind": _text(next_action.get("surface_kind")),
        "action_id": _text(next_action.get("action_id")),
        "idempotency_key": _text(next_action.get("idempotency_key")),
        "action_family": _text(next_action.get("action_family")),
        "expected_output_contract": {
            "output_kind": output_kind,
        }
        if output_kind
        else None,
    }
    return {key: value for key, value in identity.items() if value not in (None, "", {}, [])}


def next_action_identity_complete(next_action: Mapping[str, Any]) -> bool:
    identity = next_action_identity(next_action)
    expected = _mapping(identity.get("expected_output_contract"))
    return (
        _text(identity.get("next_action_surface_kind")) == "mas_next_action_envelope"
        and _text(identity.get("action_id")) is not None
        and _text(identity.get("idempotency_key")) is not None
        and _text(identity.get("action_family")) is not None
        and _text(expected.get("output_kind"))
        == OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_OUTPUT_KIND
    )


def opl_transition_handoff_contract(
    next_action: Mapping[str, Any],
    *,
    provenance: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    identity = next_action_identity(next_action)
    authority_boundary = opl_transition_receipt_authority_boundary()
    result = {
        "surface_kind": "opl_transition_handoff_contract",
        "schema_version": 1,
        "runtime_contract_ref": CONTRACT_REF,
        "target_runtime_owner": RUNTIME_OWNER,
        "target_runtime_kind": RUNTIME_KIND,
        "identity_source": "NextActionEnvelope",
        "required_next_action_identity_fields": list(NEXT_ACTION_IDENTITY_FIELDS),
        "next_action": identity or None,
        "next_action_identity_complete": next_action_identity_complete(next_action),
        "expected_output_contract": opl_transition_receipt_expected_output_contract(),
        "runtime_receipt_authority": authority_boundary,
        "authority_boundary": authority_boundary,
        "legacy_work_unit_identity_role": "provenance_currentness_only",
        "exact_work_unit_id_authority": False,
        "queue_attempt_terminal_is_paper_progress": False,
        "provider_completion_is_domain_completion": False,
        "mas_receipt_consumer_required_for_paper_progress": True,
        "provenance": _mapping(provenance),
    }
    return {key: value for key, value in result.items() if value not in (None, "", {}, [])}


def required_readback_shape() -> dict[str, Any]:
    return {
        "surface_kind": LIVE_READBACK_SURFACE,
        "runtime_id": RUNTIME_ID,
        "runtime_owner": RUNTIME_OWNER,
        "runtime_kind": RUNTIME_KIND,
        "runtime_readback_status": LIVE_READBACK_COMPLETE_STATUS,
        "transaction_complete": True,
        "required_sections": list(REQUIRED_READBACK_SECTIONS),
        "required_runtime_refs": list(REQUIRED_RUNTIME_REFS),
        "identity_transaction_refs": list(LIVE_READBACK_IDENTITY_TRANSACTION_REFS),
        "latest_transaction_required_flags": list(
            LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS
        ),
        "causality_transaction_ref_fields": list(
            LIVE_READBACK_CAUSALITY_TRANSACTION_REF_FIELDS
        ),
        "latest_transaction_ref_fields": list(LIVE_READBACK_LATEST_TRANSACTION_REF_FIELDS),
        "read_model_rebuild_required_sections": list(LIVE_READBACK_READ_MODEL_SECTIONS),
        "transaction_consistency": live_readback_transaction_consistency(),
        "evidence_source_contract": live_readback_evidence_source_contract(),
        "provider_admission_identity_binding": {
            "required_fields": list(PROVIDER_ADMISSION_READBACK_IDENTITY_FIELDS),
            "request_identity_field": PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD,
            "readback_must_match_current_transition_identity": True,
            "same_identity_live_readback_consumes_transition_request_pending": True,
            "stale_or_cross_identity_readback_counts_as_request_pending": True,
            "owner_callable_dispatch_uses_same_identity_binding": True,
            "missing_route_or_attempt_identity_counts_as_missing_opl_authorization": True,
        },
        "accepted_outcome_kind": PROVIDER_ADMISSION_OUTCOME,
        "accepted_outcome_kinds": [
            PROVIDER_ADMISSION_OUTCOME,
            NON_ADVANCING_APPLY_OUTCOME,
        ],
        "provider_admission_outcome_kind": PROVIDER_ADMISSION_OUTCOME,
        "non_advancing_apply_outcome_kind": NON_ADVANCING_APPLY_OUTCOME,
        "non_advancing_apply_consumption": {
            "same_identity_live_readback_consumes_transition_request_pending": True,
            "provider_admission_allowed": False,
            "current_executable_owner_action_allowed": False,
            "paper_progress_delta": False,
            "mas_can_apply_non_advancing_transition": False,
            "mas_consumes_as_typed_blocker_projection": True,
        },
        "deprecated_projection_fields_not_authority": [
            "opl_domain_progress_transition_result.surface_kind",
            "stage_run_id",
            "event_id_without_causality",
            "outbox_item_id_without_authority_boundary",
        ],
        "expected_output_contract": opl_transition_receipt_expected_output_contract(),
        "runtime_receipt_authority": opl_transition_receipt_authority_boundary(),
    }


def runtime_postcondition() -> dict[str, Any]:
    return {
        "surface_kind": "opl_domain_progress_transition_runtime_postcondition",
        "required_owner_surface": f"{RUNTIME_OWNER} {RUNTIME_KIND}",
        "runtime_contract_ref": CONTRACT_REF,
        "mas_surface_role": "domain_intent_and_policy_request_projection",
        "mas_can_satisfy_readback": False,
        "request_projection_only": True,
        "required_readback_shape": {
            "identity": True,
            "causality": True,
            "authority_boundary": True,
            "exactly_one_outcome": True,
            "projection_metadata": True,
            "event_id": True,
            "outbox_item_id": True,
            "stage_run_identity": True,
        },
        "mas_projection_cannot_replace": list(MAS_PROJECTION_CANNOT_REPLACE),
    }


def mas_projection_authority_boundary(value: object = None) -> dict[str, Any]:
    return {
        **_mapping(value),
        "mas_materializes_domain_intent": True,
        "mas_creates_owner_callable_carrier": False,
        "mas_creates_opl_outbox": False,
        "mas_creates_opl_event": False,
        "mas_creates_opl_stage_run": False,
        "mas_dispatch_authority": False,
        "provider_admission_pending": False,
        "can_create_success_outcome": False,
        "can_select_next_action": False,
        "target_runtime_owner": RUNTIME_OWNER,
        "execution_requires_opl_authorization": True,
        "durable_carrier_owner": RUNTIME_OWNER,
        "projection_only": True,
        "runtime_contract_ref": CONTRACT_REF,
        "expected_output_contract": opl_transition_receipt_expected_output_contract(),
        "runtime_receipt_authority": opl_transition_receipt_authority_boundary(),
        "legacy_work_unit_identity_role": "provenance_currentness_only",
    }


def mas_request_authority_boundary(value: object = None) -> dict[str, Any]:
    return {
        **_mapping(value),
        "surface_kind": "mas_domain_progress_transition_request_boundary",
        "authority": "med_autoscience.paper_progress_policy_adapter",
        "target_runtime_owner": RUNTIME_OWNER,
        "target_runtime_kind": RUNTIME_KIND,
        "runtime_contract_ref": CONTRACT_REF,
        "authority_role": "domain_policy_request_only",
        "mas_can_create_opl_outbox_record": False,
        "mas_can_create_opl_event": False,
        "mas_can_create_opl_stage_run": False,
        "mas_can_authorize_provider_admission": False,
        "mas_can_mark_provider_attempt_running": False,
        "provider_completion_is_domain_completion": False,
        "expected_output_contract": opl_transition_receipt_expected_output_contract(),
        "runtime_receipt_authority": opl_transition_receipt_authority_boundary(),
        "legacy_work_unit_identity_role": "provenance_currentness_only",
    }


def mas_request_transport_fields(value: object = None) -> dict[str, Any]:
    return {
        "authority_boundary": mas_request_authority_boundary(value),
        "stage_transition_authority_boundary": {
            "producer_kind": "runtime_provider",
            "intent_kind": "provider_observation",
            "stage_transition_authority": RUNTIME_OWNER,
            "intent_can_write_stage_current_pointer": False,
            "intent_can_write_stage_run_terminal_state": False,
            "intent_can_publish_current_owner_delta": False,
            "intent_can_write_domain_truth": False,
            "intent_can_create_owner_receipt": False,
            "intent_can_create_typed_blocker": False,
            "provider_completion_counts_as_stage_transition": False,
            "read_model_update_counts_as_stage_transition": False,
        },
        "provider_completion_is_domain_completion": False,
    }


def request_forbidden_runtime_fields() -> list[str]:
    return list(FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS)


def live_readback_transaction_consistency() -> dict[str, bool]:
    return dict(LIVE_READBACK_TRANSACTION_CONSISTENCY)


def live_readback_evidence_source_contract() -> dict[str, Any]:
    return {
        "claimable_runtime_evidence_source_kinds": list(
            LIVE_READBACK_CLAIMABLE_SOURCE_KINDS
        ),
        "non_claimable_runtime_evidence_source_kinds": list(
            LIVE_READBACK_NON_CLAIMABLE_SOURCE_KINDS
        ),
        "fresh_live_claim_requires_source_kind": True,
        "missing_source_kind_is_not_fresh_live_claim": True,
        "valid_shape_can_test_projection_rules_without_live_claim": True,
    }


def transition_spine_false_authority_flags() -> dict[str, bool]:
    return dict(TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS)


def transition_spine_abi_contract() -> dict[str, Any]:
    return {
        "surface_kind": "mas_opl_transition_spine_abi_contract",
        "schema_version": 1,
        "state": "active_machine_contract_slice",
        "contract_ref": CONTRACT_REF,
        "source_design_refs": [
            "docs/runtime/designs/mas_opl_progress_runtime_ideal_blueprint.md",
            "docs/runtime/designs/mas_opl_agent_os_target_operating_architecture.md",
        ],
        "spine": list(TRANSITION_SPINE_BOUNDARIES),
        "required_field_families": list(TRANSITION_SPINE_FIELD_FAMILIES),
        "boundary_abi": {
            name: {
                **abi,
                "required_field_families": list(abi["required_field_families"]),
                "required_minimal_fields": {
                    family: list(fields)
                    for family, fields in abi["required_minimal_fields"].items()
                },
                "authority_boundary": dict(abi["authority_boundary"]),
                "forbidden_authority_flags": dict(abi["forbidden_authority_flags"]),
            }
            for name, abi in TRANSITION_SPINE_BOUNDARY_ABI.items()
        },
        "false_authority_flags": transition_spine_false_authority_flags(),
        "acceptance_contract": {
            "all_boundaries_require_all_field_families": True,
            "exactly_one_outcome_required": True,
            "derived_projection_authority": False,
            "mas_owner_answer_required_for_paper_progress": True,
            "opl_runtime_receipt_is_input_ref_only": True,
            "tests_or_docs_do_not_authorize_runtime_or_paper_progress": True,
        },
    }


def live_readback_identity(readback: Mapping[str, Any]) -> dict[str, str | None]:
    identity = _mapping(readback.get("identity"))
    aggregate_identity = _mapping(identity.get("aggregate_identity"))
    stage_run_identity = _mapping(identity.get("stage_run_identity"))
    return {
        "study_id": _text(aggregate_identity.get("study_id")),
        "work_unit_id": _text(aggregate_identity.get("work_unit_id")),
        "work_unit_fingerprint": _text(aggregate_identity.get("work_unit_fingerprint")),
        "route_identity_key": _text(stage_run_identity.get("route_identity_key")),
        "attempt_idempotency_key": _text(stage_run_identity.get("attempt_idempotency_key")),
        PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD: _text(identity.get("idempotency_key")),
    }


def provider_admission_identity_complete(identity: Mapping[str, Any]) -> bool:
    required = (
        *PROVIDER_ADMISSION_READBACK_IDENTITY_FIELDS,
        PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD,
    )
    return all(_text(identity.get(key)) is not None for key in required)


def readback_matches_provider_admission_identity(
    readback: Mapping[str, Any],
    expected_identity: Mapping[str, Any],
) -> bool:
    if not provider_admission_identity_complete(expected_identity):
        return False
    actual_identity = live_readback_identity(readback)
    return all(
        _text(expected_identity.get(key)) == _text(actual_identity.get(key))
        for key in (
            *PROVIDER_ADMISSION_READBACK_IDENTITY_FIELDS,
            PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD,
        )
    )


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


def _text(value: object) -> str | None:
    text = str(value or "").strip()
    return text or None


__all__ = [
    "CONTRACT_REF",
    "FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS",
    "LIVE_READBACK_CAUSALITY_TRANSACTION_REF_FIELDS",
    "LIVE_READBACK_COMPLETE_STATUS",
    "LIVE_READBACK_IDENTITY_TRANSACTION_REFS",
    "LIVE_READBACK_LATEST_TRANSACTION_REF_FIELDS",
    "LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS",
    "LIVE_READBACK_READ_MODEL_SECTIONS",
    "LIVE_READBACK_CLAIMABLE_SOURCE_KINDS",
    "LIVE_READBACK_NON_CLAIMABLE_SOURCE_KINDS",
    "LIVE_READBACK_SURFACE",
    "LIVE_READBACK_TRANSACTION_CONSISTENCY",
    "MAS_PROJECTION_CANNOT_REPLACE",
    "NEXT_ACTION_IDENTITY_FIELDS",
    "NON_ADVANCING_APPLY_OUTCOME",
    "OPL_DOMAIN_ROUTE_TRANSITION_RECEIPT_OUTPUT_KIND",
    "PROVIDER_ADMISSION_READBACK_IDENTITY_FIELDS",
    "PROVIDER_ADMISSION_READBACK_REQUEST_IDENTITY_FIELD",
    "PROVIDER_ADMISSION_OUTCOME",
    "REQUIRED_READBACK_SECTIONS",
    "REQUIRED_RUNTIME_REFS",
    "RUNTIME_ID",
    "RUNTIME_KIND",
    "RUNTIME_OWNER",
    "TRANSITION_KINDS",
    "TRANSITION_SPINE_BOUNDARIES",
    "TRANSITION_SPINE_BOUNDARY_ABI",
    "TRANSITION_SPINE_FALSE_AUTHORITY_FLAGS",
    "TRANSITION_SPINE_FIELD_FAMILIES",
    "live_readback_transaction_consistency",
    "mas_projection_authority_boundary",
    "mas_request_authority_boundary",
    "next_action_identity",
    "next_action_identity_complete",
    "opl_transition_handoff_contract",
    "opl_transition_receipt_authority_boundary",
    "opl_transition_receipt_expected_output_contract",
    "request_forbidden_runtime_fields",
    "live_readback_evidence_source_contract",
    "live_readback_identity",
    "required_readback_shape",
    "provider_admission_identity_complete",
    "readback_matches_provider_admission_identity",
    "runtime_postcondition",
    "transition_spine_abi_contract",
    "transition_spine_false_authority_flags",
]
