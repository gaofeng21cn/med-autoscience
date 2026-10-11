"""Generation role vocabulary and first-draft policy values."""

from __future__ import annotations

ANALYSIS_GENERATION_ROLES = frozenset(
    {
        "source_input_digest",
        "data_release",
        "denominator_definitions",
        "analysis_script",
        "analysis_output",
    }
)
MANUSCRIPT_GENERATION_ROLES = ANALYSIS_GENERATION_ROLES | frozenset(
    {
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
    }
)
PUBLICATION_GENERATION_ROLES = MANUSCRIPT_GENERATION_ROLES | frozenset(
    {
        "docx",
        "pdf",
        "supplementary_output",
        "final_zip_allowlist",
        "final_zip_member",
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    }
)
PUBLICATION_SINGLETON_ROLES = frozenset(
    {
        "submission_status",
        "publication_evaluation",
        "next_action_envelope",
        "submission_projection_manifest",
    }
)
OPTIONAL_GENERATION_ROLES = frozenset({"candidate_artifact", "evidence_record"})
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
SELECTED_BUILD_ROLES = frozenset(SELECTED_BUILD_ROLE_BY_REF_FIELD.values())
REVIEWER_RESPONSE_ROLES = frozenset(REVIEWER_RESPONSE_ROLE_BY_REF_FIELD.values())
REVISION_GENERATION_ROLES = SELECTED_BUILD_ROLES | REVIEWER_RESPONSE_ROLES
LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD = {
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
FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD = {
    **LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    **SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD,
}
FIRST_DRAFT_QUALITY_ROLES = frozenset(
    FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD.values()
)
FIRST_DRAFT_QUALITY_ROUTE_PRIORITY = (
    "baseline_and_evidence_setup",
    "bounded_analysis_campaign",
    "manuscript_authoring",
    "review_and_quality_gate",
)
FIRST_DRAFT_VALIDATION_DESIGNS = frozenset(
    {
        "not_applicable",
        "development_only",
        "internal_validation",
        "internal_external",
        "external_validation",
    }
)
FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES = frozenset(
    {"satisfied", "route_back_required", "not_applicable_with_reason"}
)
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
PROFESSIONAL_MANUSCRIPT_SKILL_ROLES = {
    "medical-manuscript-writing": frozenset(
        {
            "canonical_manuscript",
            "claim_evidence_map",
            "claim_guardrail",
            "medical_initial_draft_preflight_candidate",
            "author_stance_integrity",
        }
    ),
    "medical-registry-atlas-story-architect": frozenset(
        {"canonical_manuscript", "claim_evidence_map"}
    ),
    "medical-data-freeze-and-analysis-readiness-reviewer": frozenset(
        {"clinical_analysis_input_identity"}
    ),
    "medical-reference-integrity-auditor": frozenset(
        {"citation_source_coverage", "active_reference_currentness"}
    ),
    "medical-statistical-review": frozenset(
        {
            "analysis_output",
            "numeric_trace",
            "validation_partition_integrity",
            "endpoint_analysis_set_reconciliation",
            "model_complexity_sparse_event",
            "linked_prediction_performance",
            "decision_curve_validity",
        }
    ),
    "medical-survival-analysis-plan": frozenset(
        {"fixed_horizon_risk_semantics", "competing_risk"}
    ),
    "medical-risk-model-transportability-reviewer": frozenset(
        {"external_transportability"}
    ),
    "medical-table-design": frozenset(
        {"table_catalog", "table_file", "baseline_table_traceability"}
    ),
    "medical-display-qc": frozenset(
        {"document_display_scope_coverage", "display_render_integrity", "pdf"}
    ),
    "medical-submission-prep": frozenset(
        {
            "canonical_manuscript",
            "docx",
            "pdf",
            "supplementary_output",
            "final_zip_allowlist",
            "final_zip_member",
        }
    ),
}
PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES = {
    "medical-manuscript-writing": frozenset(
        {
            "medical_initial_draft_preflight_candidate",
            "clinical_analysis_input_identity",
            "citation_source_coverage",
            "claim_guardrail",
        }
    ),
    "medical-registry-atlas-story-architect": frozenset(
        {"claim_evidence_map"}
    ),
    "medical-data-freeze-and-analysis-readiness-reviewer": frozenset(
        {"source_input_digest", "data_release", "denominator_definitions"}
    ),
    "medical-reference-integrity-auditor": frozenset(
        {"citation_ledger", "reference_library"}
    ),
    "medical-statistical-review": frozenset(
        {"data_release", "denominator_definitions", "analysis_output", "numeric_trace"}
    ),
    "medical-survival-analysis-plan": frozenset(
        {"denominator_definitions", "analysis_output", "numeric_trace"}
    ),
    "medical-risk-model-transportability-reviewer": frozenset(
        {"data_release", "denominator_definitions", "analysis_output"}
    ),
    "medical-table-design": frozenset({"analysis_output", "numeric_trace"}),
    "medical-display-qc": frozenset({"canonical_manuscript", "pdf"}),
    "medical-submission-prep": frozenset({"canonical_manuscript"}),
}
REQUIRED_ROLES_BY_SCOPE = {
    "analysis_generation": ANALYSIS_GENERATION_ROLES,
    "manuscript_generation": MANUSCRIPT_GENERATION_ROLES,
    "publication_generation": PUBLICATION_GENERATION_ROLES,
}
OPTIONAL_ROLES_BY_SCOPE = {
    "analysis_generation": OPTIONAL_GENERATION_ROLES
    | {"clinical_analysis_input_identity"},
    "manuscript_generation": (
        OPTIONAL_GENERATION_ROLES
        | FIRST_DRAFT_QUALITY_ROLES
        | REVISION_GENERATION_ROLES
        | {"pdf"}
    ),
    "publication_generation": (
        OPTIONAL_GENERATION_ROLES
        | FIRST_DRAFT_QUALITY_ROLES
        | REVISION_GENERATION_ROLES
    ),
}
ALLOWED_ROLES_BY_SCOPE = {
    scope: roles | OPTIONAL_ROLES_BY_SCOPE[scope]
    for scope, roles in REQUIRED_ROLES_BY_SCOPE.items()
}

