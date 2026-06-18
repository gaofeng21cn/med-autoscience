from __future__ import annotations

from collections.abc import Mapping
from typing import Any


SURFACE_KIND = "paper_progress_policy_result_projection"
LEGACY_DECISION_SURFACE_KIND = "paper_autonomy_supervisor_decision"
OBLIGATION_SURFACE_KIND = "paper_autonomy_obligation"
POLICY_RESULT_PROJECTION_SURFACE_KIND = "paper_progress_policy_result_projection"
SCHEMA_VERSION = 1
SOURCE_OF_TRUTH_CHAIN = (
    "DomainIntent",
    "OPL Command/Event/Outbox/StageRun",
    "MAS OwnerAnswer",
    "Derived Projection",
)

ALLOWED_DECISIONS = {
    "execute_current_owner_delta",
    "consume_terminal_closeout",
    "materialize_recovery_action",
    "wait_for_owner_with_resume_token",
    "stop_with_stable_typed_blocker",
    "stop_with_owner_receipt",
}

FORBIDDEN_TERMINAL_INTERPRETATIONS = [
    "operator_decision_required",
    "human_gate",
    "typed_blocker",
    "provider_admission_pending_count=0",
    "action_queue=[]",
    "queue_empty",
    "idle",
    "observe_only",
    "read_model_refreshed",
]

AUTHORITY_BOUNDARY = {
    "surface_kind": SURFACE_KIND,
    "authority": "mas_paper_progress_policy_projection",
    "authority_role": "paper_policy_projection_only_opl_transition_runtime_consumer",
    "adapter_kind": "mas_policy_adapter",
    "policy_result_role": "mas_paper_progress_policy_result_projection",
    "projection_role": "derived_policy_adapter_projection",
    "decision_authority": False,
    "supervisor_decision_engine_owner": "one-person-lab",
    "recovery_obligation_store_owner": "one-person-lab",
    "opl_transition_runtime_owner": "one-person-lab",
    "opl_recovery_obligation_store_owner": "one-person-lab",
    "opl_supervisor_decision_engine_owner": "one-person-lab",
    "opl_human_gate_transport_owner": "one-person-lab",
    "opl_stage_run_owner": "one-person-lab",
    "top_level_truth": "decision",
    "allowed_decisions": sorted(ALLOWED_DECISIONS),
    "read_models_can_create_decision": False,
    "can_store_recovery_obligation": False,
    "can_generate_supervisor_decision_authority": False,
    "provider_admission_requires_execute_decision": True,
    "provider_admission_requires_opl_stage_run_readback": True,
    "provider_completion_is_paper_progress": False,
    "can_write_study_truth": False,
    "can_authorize_publication_ready": False,
    "can_write_paper_or_package": False,
    "can_own_generic_event_log_or_outbox": False,
    "can_create_opl_command_event_or_outbox": False,
    "can_own_stage_run": False,
    "can_generate_human_gate_resume_token": False,
    "can_run_fixed_point_runtime": False,
    "can_run_supervisor_decision_engine": False,
    "can_apply_non_advancing_transition": False,
    "can_replay_obligation": False,
    "can_persist_obligation_store": False,
}

OPL_SUPERVISOR_DECISION_ENGINE_READBACK_REQUIREMENT = {
    "surface_kind": "opl_supervisor_decision_engine_readback_requirement",
    "runtime_owner": "one-person-lab",
    "runtime_kind": "RecoveryObligationStore/SupervisorDecisionEngine",
    "required_sections": [
        "identity",
        "causality",
        "authority_boundary",
        "exactly_one_outcome",
        "projection_metadata",
    ],
    "identity_required_fields": [
        "study_id",
        "quest_id",
        "stage_id",
        "action_type",
        "work_unit_id",
        "work_unit_fingerprint",
        "route_identity_key",
        "attempt_idempotency_key",
    ],
    "authority_boundary_required": {
        "runtime_owner": "one-person-lab",
        "domain_state_owner": "med-autoscience",
        "mas_can_store_recovery_obligation": False,
        "mas_can_run_supervisor_decision_engine": False,
        "mas_can_run_fixed_point_runtime": False,
        "mas_can_replay_obligation": False,
    },
    "mas_policy_projection_can_satisfy_readback": False,
    "mas_decision_field_is_authority": False,
}

POLICY_RECOMMENDATION_SEMANTICS = {
    "surface_kind": "mas_paper_policy_recommendation_semantics",
    "decision_field_role": "policy_recommendation_label",
    "decision_field_is_authority": False,
    "can_authorize_provider_admission": False,
    "can_authorize_fixed_point_replay": False,
    "can_mutate_recovery_obligation_store": False,
    "requires_opl_supervisor_decision_engine_readback": True,
}


def build_paper_progress_policy_result_projection(
    *,
    policy_recommendation_label: str,
    obligation: Mapping[str, Any],
    evidence_refs: list[str],
    missing_evidence_refs: list[str],
    next_owner: str,
    next_safe_action: Mapping[str, Any],
    paper_progress_classification: str,
    platform_repair_classification: str,
) -> dict[str, Any]:
    """Return the canonical MAS-owned policy result projection shape."""
    return _clean_mapping(
        {
            "surface_kind": POLICY_RESULT_PROJECTION_SURFACE_KIND,
            "schema_version": SCHEMA_VERSION,
            "adapter_kind": "mas_policy_adapter",
            "projection_role": "mas_paper_progress_policy_result_projection",
            "policy_result_role": "mas_paper_progress_policy_result_projection",
            "authority": "mas_paper_progress_policy_adapter",
            "authority_boundary": dict(AUTHORITY_BOUNDARY),
            "policy_recommendation_label": policy_recommendation_label,
            "policy_recommendation_label_is_authority": False,
            "legacy_decision_surface_kind": LEGACY_DECISION_SURFACE_KIND,
            "legacy_decision_field": policy_recommendation_label,
            "legacy_decision_field_role": "policy_recommendation_label",
            "legacy_decision_field_is_authority": False,
            "decision_authority": False,
            "decision_semantics": dict(POLICY_RECOMMENDATION_SEMANTICS),
            "opl_supervisor_decision_engine_readback_requirement": dict(
                OPL_SUPERVISOR_DECISION_ENGINE_READBACK_REQUIREMENT
            ),
            "source_of_truth_chain": list(SOURCE_OF_TRUTH_CHAIN),
            "runtime_substrate_owner": "one-person-lab",
            "supervisor_decision_engine_owner": "one-person-lab",
            "recovery_obligation_store_owner": "one-person-lab",
            "mas_can_run_supervisor_decision_engine": False,
            "mas_can_store_recovery_obligation": False,
            "mas_can_create_opl_command_event_or_outbox": False,
            "mas_can_authorize_provider_admission": False,
            "paper_autonomy_obligation_ref": _text(
                obligation.get("paper_autonomy_obligation_id")
            ),
            "paper_autonomy_obligation_identity": _identity(obligation),
            "evidence_refs": list(evidence_refs),
            "missing_evidence_refs": list(missing_evidence_refs),
            "next_owner": next_owner,
            "next_safe_action": dict(next_safe_action),
            "paper_progress_classification": paper_progress_classification,
            "platform_repair_classification": platform_repair_classification,
        },
        keep_empty_keys={"evidence_refs", "missing_evidence_refs"},
    )


def _identity(obligation: Mapping[str, Any]) -> dict[str, Any]:
    return _clean_mapping(
        {
            key: obligation.get(key)
            for key in (
                "study_id",
                "quest_id",
                "stage_id",
                "action_type",
                "work_unit_id",
                "work_unit_fingerprint",
                "route_identity_key",
                "attempt_idempotency_key",
            )
        }
    )


def _clean_mapping(
    value: Mapping[str, Any],
    *,
    keep_empty_keys: set[str] | None = None,
) -> dict[str, Any]:
    keep = keep_empty_keys or set()
    return {
        key: item
        for key, item in dict(value).items()
        if key in keep or item not in (None, "", [], {})
    }


def _text(value: Any) -> str | None:
    if isinstance(value, str):
        value = value.strip()
        return value or None
    return None


__all__ = [
    "ALLOWED_DECISIONS",
    "AUTHORITY_BOUNDARY",
    "FORBIDDEN_TERMINAL_INTERPRETATIONS",
    "LEGACY_DECISION_SURFACE_KIND",
    "OBLIGATION_SURFACE_KIND",
    "OPL_SUPERVISOR_DECISION_ENGINE_READBACK_REQUIREMENT",
    "POLICY_RECOMMENDATION_SEMANTICS",
    "POLICY_RESULT_PROJECTION_SURFACE_KIND",
    "SCHEMA_VERSION",
    "SOURCE_OF_TRUTH_CHAIN",
    "SURFACE_KIND",
    "build_paper_progress_policy_result_projection",
]
