from __future__ import annotations


SUPPORTED_ACTION_TYPES = frozenset(
    {
        "publication_gate_specificity_required",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "return_to_ai_reviewer_workflow",
        "canonical_paper_inputs_rehydrate_required",
        "run_quality_repair_batch",
        "unit_harmonized_external_validation_rerun",
        "recover_transport_model_provenance",
        "methodology_reframe_route_decision",
        "provenance_limited_harmonization_audit",
    }
)

FORBIDDEN_SURFACES = [
    "paper/**",
    "manuscript/**",
    "current_package/**",
    "paper/current_package/**",
    "manuscript/current_package/**",
    "src/med_autoscience/platform/**",
]

RETIRED_ABSENT_SURFACES = [
    "src/med_autoscience/runtime_transport/",
]

ALLOWED_WRITE_SURFACES = [
    "artifacts/supervision/consumer/latest.json",
    "artifacts/supervision/consumer/history.jsonl",
    "studies/<study_id>/artifacts/supervision/consumer/publication_gate_specificity_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/current_package_freshness_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/artifact_display_surface_materialization_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/return_to_ai_reviewer_workflow.json",
    "studies/<study_id>/artifacts/supervision/consumer/canonical_paper_inputs_rehydrate_required.json",
    "studies/<study_id>/artifacts/supervision/consumer/run_quality_repair_batch.json",
    "studies/<study_id>/artifacts/supervision/consumer/unit_harmonized_external_validation_rerun.json",
    "studies/<study_id>/artifacts/supervision/consumer/recover_transport_model_provenance.json",
    "studies/<study_id>/artifacts/supervision/consumer/methodology_reframe_route_decision.json",
    "studies/<study_id>/artifacts/supervision/consumer/provenance_limited_harmonization_audit.json",
    "studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/*.json",
    "studies/<study_id>/artifacts/supervision/requests/ai_reviewer/latest.json",
]

SOURCE_ACTION_REF_FIELDS = (
    "surface",
    "study_id",
    "quest_id",
    "action_type",
    "action_id",
    "reason",
    "owner",
    "request_owner",
    "recommended_owner",
    "authority",
    "required_output_surface",
    "next_work_unit",
    "work_unit_fingerprint",
    "route_target",
    "route_key_question",
    "route_rationale",
    "source_ref",
    "stale_record_ref",
    "required_currentness_refs",
    "record_only_surface",
    "publication_eval_latest_write_allowed",
    "controller_decision_write_allowed",
    "terminal_source_provenance_blocker",
    "hard_methodology_target",
)

SOURCE_HANDOFF_REF_FIELDS = (
    "surface",
    "request_kind",
    "authority",
    "owner",
    "request_owner",
    "recommended_owner",
    "next_executable_owner",
    "required_output_surface",
    "next_work_unit",
    "work_unit_fingerprint",
    "route_target",
    "route_key_question",
    "route_rationale",
    "source_ref",
    "terminal_source_provenance_blocker",
    "hard_methodology_target",
)

REQUEST_OWNER_BY_ACTION_TYPE = {
    "publication_gate_specificity_required": "publication_gate",
    "current_package_freshness_required": "artifact_os",
    "artifact_display_surface_materialization_required": "artifact_os",
    "return_to_ai_reviewer_workflow": "ai_reviewer",
    "canonical_paper_inputs_rehydrate_required": "write",
    "run_quality_repair_batch": "write",
    "unit_harmonized_external_validation_rerun": "analysis_harmonization_owner",
    "recover_transport_model_provenance": "source_provenance_owner",
    "methodology_reframe_route_decision": "decision",
    "provenance_limited_harmonization_audit": "provenance_limited_harmonization_owner",
}

REQUEST_OUTPUT_SURFACE_BY_ACTION_TYPE = {
    "publication_gate_specificity_required": "artifacts/publication_eval/latest.json",
    "current_package_freshness_required": "artifacts/controller/gate_clearing_batch/latest.json",
    "artifact_display_surface_materialization_required": "artifacts/controller/gate_clearing_batch/latest.json",
    "return_to_ai_reviewer_workflow": "artifacts/publication_eval/latest.json",
    "canonical_paper_inputs_rehydrate_required": "paper/medical_manuscript_blueprint_source.json",
    "run_quality_repair_batch": (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    ),
    "unit_harmonized_external_validation_rerun": (
        "unit-harmonized external-validation rerun evidence or "
        "typed blocker:unit_harmonized_rerun_required"
    ),
    "recover_transport_model_provenance": (
        "canonical transport model provenance bundle or "
        "typed blocker:transport_model_provenance_recovery_required"
    ),
    "methodology_reframe_route_decision": (
        "controller route decision for a provenance-limited reframe, reproducible-model restart, "
        "stop-loss, or human gate"
    ),
    "provenance_limited_harmonization_audit": (
        "provenance-limited harmonization audit or "
        "typed blocker:provenance_limited_harmonization_audit_required"
    ),
}

REQUEST_PACKET_REF_BY_ACTION_TYPE = {
    "publication_gate_specificity_required": "artifacts/supervision/requests/publication_gate_specificity/latest.json",
    "current_package_freshness_required": "artifacts/supervision/requests/current_package_freshness/latest.json",
    "artifact_display_surface_materialization_required": "artifacts/supervision/requests/artifact_display_materialization/latest.json",
    "return_to_ai_reviewer_workflow": "artifacts/supervision/requests/ai_reviewer/latest.json",
    "canonical_paper_inputs_rehydrate_required": "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json",
    "run_quality_repair_batch": "artifacts/supervision/requests/quality_repair_batch/latest.json",
    "unit_harmonized_external_validation_rerun": "artifacts/supervision/requests/analysis_harmonization/latest.json",
    "recover_transport_model_provenance": "artifacts/supervision/requests/source_provenance/latest.json",
    "methodology_reframe_route_decision": "artifacts/supervision/requests/decision/latest.json",
    "provenance_limited_harmonization_audit": "artifacts/supervision/requests/provenance_limited_harmonization/latest.json",
}


def request_owner_for_action_type(action_type: str) -> str:
    return REQUEST_OWNER_BY_ACTION_TYPE.get(action_type, "controller")


def request_output_surface_for_action_type(action_type: str) -> str:
    return REQUEST_OUTPUT_SURFACE_BY_ACTION_TYPE.get(action_type, "artifacts/supervision/requests")


def request_packet_ref_for_action_type(action_type: str) -> str:
    return REQUEST_PACKET_REF_BY_ACTION_TYPE.get(action_type, "artifacts/supervision/requests")


def request_packet_ref_for_dispatch(action_type: str) -> str | None:
    if action_type in SUPPORTED_ACTION_TYPES:
        return request_packet_ref_for_action_type(action_type)
    return None


__all__ = [
    "ALLOWED_WRITE_SURFACES",
    "FORBIDDEN_SURFACES",
    "REQUEST_OUTPUT_SURFACE_BY_ACTION_TYPE",
    "REQUEST_OWNER_BY_ACTION_TYPE",
    "REQUEST_PACKET_REF_BY_ACTION_TYPE",
    "RETIRED_ABSENT_SURFACES",
    "SOURCE_ACTION_REF_FIELDS",
    "SOURCE_HANDOFF_REF_FIELDS",
    "SUPPORTED_ACTION_TYPES",
    "request_output_surface_for_action_type",
    "request_owner_for_action_type",
    "request_packet_ref_for_action_type",
    "request_packet_ref_for_dispatch",
]
