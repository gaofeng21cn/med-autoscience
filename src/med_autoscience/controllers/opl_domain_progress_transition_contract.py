from __future__ import annotations

from collections.abc import Mapping
from typing import Any

RUNTIME_ID = "opl_domain_progress_transition_runtime"
RUNTIME_OWNER = "one-person-lab"
RUNTIME_KIND = "DomainProgressTransitionRuntime"
LIVE_READBACK_SURFACE = "opl_domain_progress_transition_runtime_live_readback"
LIVE_READBACK_COMPLETE_STATUS = "complete_transaction"
PROVIDER_ADMISSION_OUTCOME = "provider_admission_enqueued_or_blocked"
CONTRACT_REF = "contracts/opl_domain_progress_transition_runtime_contract.json"

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

LIVE_READBACK_TRANSACTION_CONSISTENCY = {
    "identity_latest_refs_match_causality": True,
    "identity_latest_refs_match_latest_transaction_readback": True,
    "projection_metadata_derived_from_event_id_matches_identity_latest_event_id": True,
    "latest_transaction_requires_command_event_outbox": True,
    "same_transaction_event_and_outbox": True,
}

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
        "transaction_consistency": live_readback_transaction_consistency(),
        "accepted_outcome_kind": PROVIDER_ADMISSION_OUTCOME,
        "deprecated_projection_fields_not_authority": [
            "opl_domain_progress_transition_result.surface_kind",
            "stage_run_id",
            "event_id_without_causality",
            "outbox_item_id_without_authority_boundary",
        ],
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
    }


def request_forbidden_runtime_fields() -> list[str]:
    return list(FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS)


def live_readback_transaction_consistency() -> dict[str, bool]:
    return dict(LIVE_READBACK_TRANSACTION_CONSISTENCY)


def _mapping(value: object) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}


__all__ = [
    "CONTRACT_REF",
    "FORBIDDEN_MAS_REQUEST_RUNTIME_FIELDS",
    "LIVE_READBACK_CAUSALITY_TRANSACTION_REF_FIELDS",
    "LIVE_READBACK_COMPLETE_STATUS",
    "LIVE_READBACK_IDENTITY_TRANSACTION_REFS",
    "LIVE_READBACK_LATEST_TRANSACTION_REF_FIELDS",
    "LIVE_READBACK_LATEST_TRANSACTION_REQUIRED_FLAGS",
    "LIVE_READBACK_SURFACE",
    "LIVE_READBACK_TRANSACTION_CONSISTENCY",
    "MAS_PROJECTION_CANNOT_REPLACE",
    "PROVIDER_ADMISSION_OUTCOME",
    "REQUIRED_READBACK_SECTIONS",
    "REQUIRED_RUNTIME_REFS",
    "RUNTIME_ID",
    "RUNTIME_KIND",
    "RUNTIME_OWNER",
    "TRANSITION_KINDS",
    "live_readback_transaction_consistency",
    "mas_projection_authority_boundary",
    "mas_request_authority_boundary",
    "request_forbidden_runtime_fields",
    "required_readback_shape",
    "runtime_postcondition",
]
