from __future__ import annotations


SUPPORTED_ACTION_TYPES = frozenset(
    {
        "publication_gate_specificity_required",
        "publication_handoff_owner_gate",
        "current_package_freshness_required",
        "artifact_display_surface_materialization_required",
        "return_to_ai_reviewer_workflow",
        "canonical_paper_inputs_rehydrate_required",
        "run_quality_repair_batch",
        "run_gate_clearing_batch",
        "complete_medical_paper_readiness_surface",
        "paper_clean_room_rebuild_required",
        "run_medical_publication_surface_from_clean_room",
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
    "studies/<study_id>/artifacts/supervision/requests/publication_gate_specificity/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/publication_handoff_owner_gate/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/current_package_freshness/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/artifact_display_materialization/latest.json",
    "studies/<study_id>/artifacts/supervision/consumer/default_executor_dispatches/*.json",
    "studies/<study_id>/artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/ai_reviewer/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/quality_repair_batch/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/gate_clearing_batch/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/medical_paper_readiness/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/paper_clean_room_rebuild/latest.json",
    "studies/<study_id>/artifacts/supervision/paper_clean_room_rebuild/**",
    "studies/<study_id>/artifacts/reports/medical_publication_surface/**",
    "studies/<study_id>/artifacts/supervision/requests/analysis_harmonization/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/source_provenance/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/decision/latest.json",
    "studies/<study_id>/artifacts/supervision/requests/provenance_limited_harmonization/latest.json",
]

DEFAULT_EXECUTOR_SEARCH_DISCIPLINE = {
    "surface": "default_executor_search_discipline.v1",
    "policy": "bounded_refs_and_scoped_text_search_only",
    "forbidden_command_patterns": [
        "grep -R",
        "grep -r",
        "find .",
        "find runtime",
        "python rglob('.')",
        "Path('.').rglob('*')",
    ],
    "forbidden_path_globs": [
        "runtime/.ds/**",
        "runtime/**/.ds/**",
        "runtime/**/codex_homes/**",
        "runtime/**/.codex/.tmp/plugins/**",
        "runtime/**/plugins/**/assets/**",
        ".git/**",
        "node_modules/**",
        ".venv/**",
        "__pycache__/**",
    ],
    "recommended_search_commands": [
        "rg --hidden --glob '!runtime/.ds/**' --glob '!runtime/**/.ds/**' --glob '!node_modules/**' <pattern> <scoped-paths>",
        "rg <pattern> paper artifacts/controller artifacts/publication_eval artifacts/supervision/requests",
    ],
    "allowed_search_roots": [
        "paper/",
        "artifacts/controller/",
        "artifacts/publication_eval/",
        "artifacts/eval_hygiene/",
        "artifacts/supervision/requests/",
        "artifacts/supervision/consumer/default_executor_dispatches/",
        "study.yaml",
    ],
    "blocker_on_missing_evidence": "typed_blocker:bounded_search_evidence_ref_missing",
}

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
    "controller_work_unit_id",
    "executable_work_unit",
    "work_unit_fingerprint",
    "route_target",
    "route_key_question",
    "route_rationale",
    "source_ref",
    "source_surface",
    "stale_record_ref",
    "required_currentness_refs",
    "record_only_surface",
    "materialization_decision",
    "publication_eval_latest_write_allowed",
    "controller_decision_write_allowed",
    "reviewer_record_ref",
    "source_eval_id",
    "story_surface_delta_refs",
    "readiness_blocker_followup_superseded",
    "readiness_blocker_ref",
    "publication_eval_gap_ids",
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
    "publication_handoff_owner_gate": "publication_gate_owner",
    "current_package_freshness_required": "artifact_os",
    "artifact_display_surface_materialization_required": "artifact_os",
    "return_to_ai_reviewer_workflow": "ai_reviewer",
    "canonical_paper_inputs_rehydrate_required": "write",
    "run_quality_repair_batch": "write",
    "run_gate_clearing_batch": "gate_clearing_batch",
    "complete_medical_paper_readiness_surface": "MedAutoScience",
    "paper_clean_room_rebuild_required": "MedAutoScience",
    "run_medical_publication_surface_from_clean_room": "MedAutoScience",
    "unit_harmonized_external_validation_rerun": "analysis_harmonization_owner",
    "recover_transport_model_provenance": "source_provenance_owner",
    "methodology_reframe_route_decision": "decision",
    "provenance_limited_harmonization_audit": "provenance_limited_harmonization_owner",
}

REQUEST_OUTPUT_SURFACE_BY_ACTION_TYPE = {
    "publication_gate_specificity_required": "artifacts/publication_eval/latest.json",
    "publication_handoff_owner_gate": (
        "artifacts/stage_outputs/08-publication_package_handoff/handoff_owner_receipt.json "
        "or artifacts/stage_outputs/08-publication_package_handoff/receipts/typed_blocker.json"
    ),
    "current_package_freshness_required": "artifacts/controller/gate_clearing_batch/latest.json",
    "artifact_display_surface_materialization_required": "artifacts/controller/gate_clearing_batch/latest.json",
    "return_to_ai_reviewer_workflow": "artifacts/publication_eval/latest.json",
    "canonical_paper_inputs_rehydrate_required": "paper/medical_manuscript_blueprint_source.json",
    "run_quality_repair_batch": (
        "canonical manuscript story-surface delta or "
        "typed blocker:manuscript_story_surface_delta_missing"
    ),
    "run_gate_clearing_batch": "artifacts/controller/gate_clearing_batch/latest.json",
    "complete_medical_paper_readiness_surface": (
        "artifacts/medical_paper/<surface_key>.json or "
        "typed blocker:medical_paper_readiness_surface_input_required"
    ),
    "paper_clean_room_rebuild_required": "artifacts/supervision/paper_clean_room_rebuild/latest.json",
    "run_medical_publication_surface_from_clean_room": "artifacts/reports/medical_publication_surface/latest.json",
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

REQUEST_OUTPUT_TARGET_SURFACE_BY_ACTION_TYPE = {
    "unit_harmonized_external_validation_rerun": {
        "surface": "analysis_harmonization_owner_target_surface",
        "schema_version": 1,
        "body_free": True,
        "owner": "analysis_harmonization_owner",
        "work_unit": "unit_harmonized_external_validation_rerun",
        "accepted_outputs": [
            "unit_harmonized_external_validation_rerun_evidence",
            "feature_order_and_coefficient_provenance",
            "calibration_or_recalibration_evidence",
            "claim_evidence_map_update_ref",
            "stable_typed_blocker:unit_harmonized_rerun_required",
        ],
        "output_refs": {
            "owner_result": "artifacts/controller/analysis_harmonization/latest.json",
            "rerun_evidence": (
                "artifacts/controller/analysis_harmonization/"
                "unit_harmonized_external_validation_rerun.json"
            ),
            "claim_evidence_map": "paper/claim_evidence_map.json",
            "request_packet": "artifacts/supervision/requests/analysis_harmonization/latest.json",
        },
        "publication_ready_authorized": False,
        "current_package_write_allowed": False,
        "paper_body_write_allowed": False,
    },
}

REQUEST_PACKET_REF_BY_ACTION_TYPE = {
    "publication_gate_specificity_required": "artifacts/supervision/requests/publication_gate_specificity/latest.json",
    "publication_handoff_owner_gate": "artifacts/supervision/requests/publication_handoff_owner_gate/latest.json",
    "current_package_freshness_required": "artifacts/supervision/requests/current_package_freshness/latest.json",
    "artifact_display_surface_materialization_required": "artifacts/supervision/requests/artifact_display_materialization/latest.json",
    "return_to_ai_reviewer_workflow": "artifacts/supervision/requests/ai_reviewer/latest.json",
    "canonical_paper_inputs_rehydrate_required": "artifacts/supervision/requests/canonical_paper_inputs_rehydrate/latest.json",
    "run_quality_repair_batch": "artifacts/supervision/requests/quality_repair_batch/latest.json",
    "run_gate_clearing_batch": "artifacts/supervision/requests/gate_clearing_batch/latest.json",
    "complete_medical_paper_readiness_surface": "artifacts/supervision/requests/medical_paper_readiness/latest.json",
    "paper_clean_room_rebuild_required": "artifacts/supervision/requests/paper_clean_room_rebuild/latest.json",
    "run_medical_publication_surface_from_clean_room": "artifacts/supervision/requests/clean_room_publication_surface/latest.json",
    "unit_harmonized_external_validation_rerun": "artifacts/supervision/requests/analysis_harmonization/latest.json",
    "recover_transport_model_provenance": "artifacts/supervision/requests/source_provenance/latest.json",
    "methodology_reframe_route_decision": "artifacts/supervision/requests/decision/latest.json",
    "provenance_limited_harmonization_audit": "artifacts/supervision/requests/provenance_limited_harmonization/latest.json",
}


def request_owner_for_action_type(action_type: str) -> str:
    return REQUEST_OWNER_BY_ACTION_TYPE.get(action_type, "controller")


def request_output_surface_for_action_type(action_type: str) -> str:
    return REQUEST_OUTPUT_SURFACE_BY_ACTION_TYPE.get(action_type, "artifacts/supervision/requests")


def request_output_target_surface_for_action_type(action_type: str) -> dict[str, object] | None:
    target_surface = REQUEST_OUTPUT_TARGET_SURFACE_BY_ACTION_TYPE.get(action_type)
    return _deep_copy_mapping(target_surface) if target_surface is not None else None


def request_packet_ref_for_action_type(action_type: str) -> str:
    return REQUEST_PACKET_REF_BY_ACTION_TYPE.get(action_type, "artifacts/supervision/requests")


def request_packet_ref_for_dispatch(action_type: str) -> str | None:
    if action_type in SUPPORTED_ACTION_TYPES:
        return request_packet_ref_for_action_type(action_type)
    return None


def default_executor_search_discipline() -> dict[str, object]:
    return {
        **DEFAULT_EXECUTOR_SEARCH_DISCIPLINE,
        "forbidden_command_patterns": list(DEFAULT_EXECUTOR_SEARCH_DISCIPLINE["forbidden_command_patterns"]),
        "forbidden_path_globs": list(DEFAULT_EXECUTOR_SEARCH_DISCIPLINE["forbidden_path_globs"]),
        "recommended_search_commands": list(DEFAULT_EXECUTOR_SEARCH_DISCIPLINE["recommended_search_commands"]),
        "allowed_search_roots": list(DEFAULT_EXECUTOR_SEARCH_DISCIPLINE["allowed_search_roots"]),
    }


def _deep_copy_mapping(payload: dict[str, object]) -> dict[str, object]:
    copied: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, dict):
            copied[key] = _deep_copy_mapping(value)
        elif isinstance(value, list):
            copied[key] = list(value)
        else:
            copied[key] = value
    return copied


__all__ = [
    "ALLOWED_WRITE_SURFACES",
    "DEFAULT_EXECUTOR_SEARCH_DISCIPLINE",
    "FORBIDDEN_SURFACES",
    "REQUEST_OUTPUT_SURFACE_BY_ACTION_TYPE",
    "REQUEST_OUTPUT_TARGET_SURFACE_BY_ACTION_TYPE",
    "REQUEST_OWNER_BY_ACTION_TYPE",
    "REQUEST_PACKET_REF_BY_ACTION_TYPE",
    "RETIRED_ABSENT_SURFACES",
    "SOURCE_ACTION_REF_FIELDS",
    "SOURCE_HANDOFF_REF_FIELDS",
    "SUPPORTED_ACTION_TYPES",
    "request_output_surface_for_action_type",
    "request_output_target_surface_for_action_type",
    "request_owner_for_action_type",
    "default_executor_search_discipline",
    "request_packet_ref_for_action_type",
    "request_packet_ref_for_dispatch",
]
