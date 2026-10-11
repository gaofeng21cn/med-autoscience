"""Review lane and scope policy values."""

from __future__ import annotations

from .generation_roles import (
    ANALYSIS_GENERATION_ROLES,
    REVIEWER_RESPONSE_ROLES,
    SELECTED_BUILD_ROLES,
)

REVIEW_LANES_BY_SCOPE = {
    "analysis_generation": frozenset({"statistical"}),
    "manuscript_generation": frozenset(
        {"medical", "statistical", "reference", "display"}
    ),
    "publication_generation": frozenset(
        {
            "medical",
            "statistical",
            "reference",
            "display",
            "publication",
            "exact_byte_package",
        }
    ),
}
REVIEW_AUTHORITY_ROLE_BY_LANE = {
    "medical": "mas_independent_medical_reviewer",
    "statistical": "mas_independent_statistical_reviewer",
    "reference": "mas_independent_reference_reviewer",
    "display": "mas_independent_display_reviewer",
    "publication": "mas_independent_publication_reviewer",
    "exact_byte_package": "mas_independent_exact_byte_package_reviewer",
}
REVIEW_LANE_ORDER = (
    "medical",
    "statistical",
    "reference",
    "display",
    "publication",
    "exact_byte_package",
)
REVIEW_SCOPE_POLICY_ID = "mas_review_scope_dependency_map"
REVIEW_SCOPE_POLICY_VERSION = 2
# MAS owns this map. Hosts may materialize these inventories, but they may not
# choose or narrow review members.
REVIEW_SCOPE_ROLES_BY_LANE = {
    "medical": frozenset(
        {
            "data_release",
            "denominator_definitions",
            "analysis_output",
            "candidate_artifact",
            "evidence_record",
            "canonical_manuscript",
            "claim_evidence_map",
            "numeric_trace",
            "medical_initial_draft_preflight_candidate",
            "clinical_analysis_input_identity",
            "citation_source_coverage",
            "validation_partition_integrity",
            "endpoint_analysis_set_reconciliation",
            "model_complexity_sparse_event",
            "fixed_horizon_risk_semantics",
            "competing_risk",
            "decision_curve_validity",
            "claim_guardrail",
            "external_transportability",
        }
    )
    | REVIEWER_RESPONSE_ROLES,
    "statistical": (ANALYSIS_GENERATION_ROLES - {"source_input_digest"})
    | frozenset(
        {
            "candidate_artifact",
            "evidence_record",
            "canonical_manuscript",
            "claim_evidence_map",
            "numeric_trace",
            "table_catalog",
            "table_file",
            "clinical_analysis_input_identity",
            "validation_partition_integrity",
            "endpoint_analysis_set_reconciliation",
            "model_complexity_sparse_event",
            "fixed_horizon_risk_semantics",
            "competing_risk",
            "decision_curve_validity",
            "baseline_table_traceability",
            "external_transportability",
        }
    ),
    "reference": frozenset(
        {
            "canonical_manuscript",
            "claim_evidence_map",
            "citation_ledger",
            "reference_library",
            "evidence_record",
            "citation_source_coverage",
            "claim_guardrail",
        }
    ),
    "display": frozenset(
        {
            "analysis_output",
            "canonical_manuscript",
            "claim_evidence_map",
            "table_catalog",
            "table_file",
            "figure_catalog",
            "figure_file",
            "render_environment_and_font_manifest",
            "baseline_table_traceability",
            "document_display_scope_coverage",
            "docx",
            "pdf",
            "supplementary_output",
        }
    )
    | SELECTED_BUILD_ROLES,
    "publication": frozenset(
        {
            "canonical_manuscript",
            "claim_evidence_map",
            "citation_ledger",
            "reference_library",
            "table_catalog",
            "table_file",
            "figure_catalog",
            "figure_file",
            "render_environment_and_font_manifest",
            "docx",
            "pdf",
            "supplementary_output",
            "final_zip_allowlist",
            "final_zip_member",
        }
    )
    | SELECTED_BUILD_ROLES,
    "exact_byte_package": frozenset(
        {
            "docx",
            "pdf",
            "supplementary_output",
            "final_zip_allowlist",
            "final_zip_member",
        }
    )
    | SELECTED_BUILD_ROLES,
}

