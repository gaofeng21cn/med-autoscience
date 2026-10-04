"""Shared surface values used by AuthorityRecordFactory test fixtures."""

from __future__ import annotations

ANALYSIS_ROLES = (
    "source_input_digest",
    "data_release",
    "denominator_definitions",
    "analysis_script",
    "analysis_output",
)
MANUSCRIPT_ROLES = ANALYSIS_ROLES + (
    "candidate_admission_receipt",
    "canonical_manuscript",
    "claim_evidence_map",
    "citation_ledger",
    "numeric_trace",
    "reference_library",
    "table_catalog",
    "table_file",
    "figure_catalog",
    "figure_file",
    "render_environment_and_font_manifest",
)
FIRST_DRAFT_QUALITY_ROLES = (
    "medical_initial_draft_preflight_candidate",
    "clinical_analysis_input_identity",
    "citation_source_coverage",
    "validation_partition_integrity",
    "endpoint_analysis_set_reconciliation",
    "model_complexity_sparse_event",
    "fixed_horizon_risk_semantics",
    "competing_risk",
    "decision_curve_validity",
    "baseline_table_traceability",
    "document_display_scope_coverage",
    "claim_guardrail",
    "author_stance_integrity",
)
LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD = {
    "medical_initial_draft_preflight_candidate_ref": (
        "medical_initial_draft_preflight_candidate"
    ),
    "clinical_analysis_input_identity_ref": "clinical_analysis_input_identity",
    "citation_source_coverage_ref": "citation_source_coverage",
    "validation_partition_integrity_ref": "validation_partition_integrity",
    "endpoint_analysis_set_reconciliation_ref": (
        "endpoint_analysis_set_reconciliation"
    ),
    "model_complexity_sparse_event_ref": "model_complexity_sparse_event",
    "fixed_horizon_risk_semantics_ref": "fixed_horizon_risk_semantics",
    "competing_risk_ref": "competing_risk",
    "decision_curve_validity_ref": "decision_curve_validity",
    "baseline_table_traceability_ref": "baseline_table_traceability",
    "document_display_scope_coverage_ref": "document_display_scope_coverage",
    "claim_guardrail_ref": "claim_guardrail",
    "external_transportability_ref": "external_transportability",
}
SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD = {
    "active_reference_currentness_ref": "active_reference_currentness",
    "linked_prediction_performance_ref": "linked_prediction_performance",
    "display_render_integrity_ref": "display_render_integrity",
    "author_stance_integrity_ref": "author_stance_integrity",
}
FIRST_DRAFT_ROLE_BY_REF_FIELD = {
    **LEGACY_FIRST_DRAFT_ROLE_BY_REF_FIELD,
    **SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD,
}
SELECTED_BUILD_ROLE_BY_REF_FIELD = {
    "selected_archive_manifest_ref": "selected_archive_manifest",
    "selected_build_receipt_ref": "selected_build_receipt",
    "dependency_manifest_ref": "build_dependency_manifest",
    "root_reader_output_ref": "root_reader_output",
    "selected_reader_output_ref": "selected_reader_output",
}
REVIEWER_RESPONSE_ROLE_BY_REF_FIELD = {
    "response_ref": "reviewer_response",
    "action_matrix_ref": "reviewer_action_matrix",
    "artifact_inventory_ref": "reviewer_artifact_inventory",
    "external_synthesis_ref": "reviewer_external_synthesis",
    "new_revision_ref": "reviewer_new_revision",
}
SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL = {
    "medical-manuscript-writing": {
        "policy_id": "scholarskills_medical_initial_draft_preflight.v3",
        "validator_id": "validate_medical_initial_draft_preflight_candidate_v3",
        "candidate_ref_field": "medical_initial_draft_preflight_candidate_ref",
        "candidate_surface_kind": "medical_initial_draft_preflight_candidate_ref",
    },
    "medical-statistical-review": {
        "policy_id": "scholarskills_linked_prediction_performance.v3",
        "validator_id": "validate_linked_prediction_performance_v2",
        "candidate_ref_field": "linked_prediction_performance_ref",
        "candidate_surface_kind": "linked_prediction_performance_ref",
    },
    "medical-reference-integrity-auditor": {
        "policy_id": "scholarskills_medical_initial_draft_preflight.v2",
        "validator_id": "audit_active_reference_currentness",
        "candidate_ref_field": "active_reference_currentness_ref",
        "candidate_surface_kind": "active_reference_currentness_ref",
    },
    "medical-display-qc": {
        "policy_id": "scholarskills_medical_initial_draft_preflight.v2",
        "validator_id": "validate_display_render_integrity",
        "candidate_ref_field": "display_render_integrity_ref",
        "candidate_surface_kind": "display_render_integrity_ref",
    },
}
PUBLICATION_ROLES = MANUSCRIPT_ROLES + (
    "docx",
    "pdf",
    "supplementary_output",
    "final_zip_allowlist",
    "final_zip_member",
    "submission_status",
    "publication_evaluation",
    "next_action_envelope",
    "submission_projection_manifest",
)
ROLES_BY_SCOPE = {
    "analysis_generation": ANALYSIS_ROLES,
    "manuscript_generation": MANUSCRIPT_ROLES,
    "publication_generation": PUBLICATION_ROLES,
}
LANES_BY_SCOPE = {
    "analysis_generation": ("statistical",),
    "manuscript_generation": ("medical", "statistical", "reference", "display"),
    "publication_generation": (
        "medical",
        "statistical",
        "reference",
        "display",
        "publication",
        "exact_byte_package",
    ),
}
AUTHORITY_ROLE_BY_LANE = {
    "medical": "mas_independent_medical_reviewer",
    "statistical": "mas_independent_statistical_reviewer",
    "reference": "mas_independent_reference_reviewer",
    "display": "mas_independent_display_reviewer",
    "publication": "mas_independent_publication_reviewer",
    "exact_byte_package": "mas_independent_exact_byte_package_reviewer",
}
