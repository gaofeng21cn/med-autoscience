"""Epistemic review node, artifact, and edge policy values."""

from __future__ import annotations

EPISTEMIC_REVIEW_SCOPE_VERSION = "opl-epistemic-review-scope.v2"
EPISTEMIC_EVIDENCE_PROFILE = "epistemic_provenance"
EPISTEMIC_TRUST_MODEL = "trusted_local_workspace"
EPISTEMIC_SCOPE_KIND_BY_LANE = {
    "medical": "content",
    "statistical": "content",
    "reference": "reference",
    "display": "display",
    "publication": "package",
    "exact_byte_package": "package",
}
EPISTEMIC_AUTHORITY_BOUNDARY = {
    "hash_is_locator_or_stale_hint_only": True,
    "hash_is_content_authority": False,
    "release_integrity_is_separate": True,
    "framework_can_issue_domain_verdict": False,
}
EPISTEMIC_NODE_ROLE_BY_LANE = {
    "medical": {
        "data_release": ("provenance", "source_data"),
        "denominator_definitions": ("provenance", "analysis_parameters"),
        "analysis_output": ("artifact", "analysis_result"),
        "candidate_artifact": ("artifact", "analysis_result"),
        "evidence_record": ("provenance", "context"),
        "canonical_manuscript": ("claim", "claim"),
        "claim_evidence_map": ("provenance", "citation_linkage"),
        "numeric_trace": ("artifact", "analysis_result"),
        "medical_initial_draft_preflight_candidate": (
            "provenance",
            "context",
        ),
        "author_stance_integrity": ("provenance", "context"),
        "clinical_analysis_input_identity": (
            "provenance",
            "analysis_parameters",
        ),
        "citation_source_coverage": ("provenance", "citation_linkage"),
        "validation_partition_integrity": ("provenance", "analysis_parameters"),
        "endpoint_analysis_set_reconciliation": (
            "provenance",
            "analysis_parameters",
        ),
        "model_complexity_sparse_event": ("provenance", "analysis_result"),
        "fixed_horizon_risk_semantics": ("provenance", "analysis_parameters"),
        "competing_risk": ("provenance", "analysis_parameters"),
        "decision_curve_validity": ("provenance", "analysis_parameters"),
        "claim_guardrail": ("provenance", "context"),
        "external_transportability": ("provenance", "analysis_result"),
        "reviewer_response": ("artifact", "context"),
        "reviewer_action_matrix": ("provenance", "context"),
        "reviewer_artifact_inventory": ("provenance", "context"),
        "reviewer_external_synthesis": ("provenance", "context"),
        "reviewer_new_revision": ("claim", "claim"),
    },
    "statistical": {
        "data_release": ("provenance", "source_data"),
        "denominator_definitions": ("provenance", "analysis_parameters"),
        "analysis_script": ("provenance", "analysis_code"),
        "analysis_output": ("artifact", "analysis_result"),
        "candidate_artifact": ("artifact", "analysis_result"),
        "evidence_record": ("provenance", "context"),
        "canonical_manuscript": ("claim", "claim"),
        "claim_evidence_map": ("provenance", "citation_linkage"),
        "numeric_trace": ("artifact", "analysis_result"),
        "table_catalog": ("provenance", "context"),
        "table_file": ("artifact", "analysis_result"),
        "clinical_analysis_input_identity": (
            "provenance",
            "analysis_parameters",
        ),
        "validation_partition_integrity": ("provenance", "analysis_parameters"),
        "endpoint_analysis_set_reconciliation": (
            "provenance",
            "analysis_parameters",
        ),
        "model_complexity_sparse_event": ("provenance", "analysis_result"),
        "fixed_horizon_risk_semantics": ("provenance", "analysis_parameters"),
        "competing_risk": ("provenance", "analysis_parameters"),
        "decision_curve_validity": ("provenance", "analysis_parameters"),
        "baseline_table_traceability": ("provenance", "analysis_result"),
        "external_transportability": ("provenance", "analysis_result"),
    },
    "reference": {
        "canonical_manuscript": ("claim", "claim"),
        "claim_evidence_map": ("provenance", "citation_linkage"),
        "citation_ledger": ("provenance", "citation_linkage"),
        "reference_library": ("artifact", "reference_source"),
        "evidence_record": ("provenance", "context"),
        "citation_source_coverage": ("provenance", "citation_linkage"),
        "claim_guardrail": ("provenance", "context"),
    },
    "display": {
        "analysis_output": ("artifact", "analysis_result"),
        "canonical_manuscript": ("claim", "claim"),
        "claim_evidence_map": ("provenance", "citation_linkage"),
        "table_catalog": ("provenance", "context"),
        "table_file": ("artifact", "visual_content"),
        "figure_catalog": ("provenance", "context"),
        "figure_file": ("artifact", "visual_content"),
        "render_environment_and_font_manifest": ("provenance", "render_template"),
        "baseline_table_traceability": ("provenance", "analysis_result"),
        "document_display_scope_coverage": ("provenance", "render_template"),
        "docx": ("artifact", "visual_content"),
        "pdf": ("artifact", "visual_content"),
        "supplementary_output": ("artifact", "visual_content"),
        "selected_archive_manifest": ("provenance", "context"),
        "selected_build_receipt": ("provenance", "context"),
        "build_dependency_manifest": ("provenance", "render_template"),
        "root_reader_output": ("artifact", "visual_content"),
        "selected_reader_output": ("artifact", "visual_content"),
    },
    "publication": {
        "canonical_manuscript": ("claim", "claim"),
        "claim_evidence_map": ("provenance", "citation_linkage"),
        "citation_ledger": ("provenance", "citation_linkage"),
        "reference_library": ("artifact", "reference_source"),
        "table_catalog": ("provenance", "context"),
        "table_file": ("artifact", "visual_content"),
        "figure_catalog": ("provenance", "context"),
        "figure_file": ("artifact", "visual_content"),
        "render_environment_and_font_manifest": ("provenance", "render_template"),
        "docx": ("artifact", "package_content"),
        "pdf": ("artifact", "package_content"),
        "supplementary_output": ("artifact", "package_content"),
        "final_zip_allowlist": ("artifact", "package_wrapper"),
        "final_zip_member": ("artifact", "package_content"),
        "selected_archive_manifest": ("artifact", "package_wrapper"),
        "selected_build_receipt": ("provenance", "context"),
        "build_dependency_manifest": ("provenance", "render_template"),
        "root_reader_output": ("artifact", "package_content"),
        "selected_reader_output": ("artifact", "package_content"),
    },
    "exact_byte_package": {
        "docx": ("artifact", "package_content"),
        "pdf": ("artifact", "package_content"),
        "supplementary_output": ("artifact", "package_content"),
        "final_zip_allowlist": ("artifact", "package_wrapper"),
        "final_zip_member": ("artifact", "package_content"),
        "selected_archive_manifest": ("artifact", "package_wrapper"),
        "selected_build_receipt": ("provenance", "context"),
        "build_dependency_manifest": ("provenance", "render_template"),
        "root_reader_output": ("artifact", "package_content"),
        "selected_reader_output": ("artifact", "package_content"),
    },
}
EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE = {
    "medical": frozenset(
        {
            "canonical_manuscript",
            "claim_evidence_map",
            "reviewer_response",
            "reviewer_external_synthesis",
            "reviewer_new_revision",
        }
    ),
    "statistical": frozenset(
        {
            "analysis_output",
            "numeric_trace",
            "table_file",
            "canonical_manuscript",
            "claim_evidence_map",
        }
    ),
    "reference": frozenset({"canonical_manuscript", "claim_evidence_map"}),
    "display": frozenset(
        {
            "table_file",
            "figure_file",
            "docx",
            "pdf",
            "supplementary_output",
            "root_reader_output",
            "selected_reader_output",
        }
    ),
    "publication": frozenset(
        {
            "docx",
            "pdf",
            "supplementary_output",
            "final_zip_allowlist",
            "selected_archive_manifest",
            "root_reader_output",
            "selected_reader_output",
        }
    ),
    "exact_byte_package": frozenset(
        {
            "final_zip_allowlist",
            "selected_archive_manifest",
            "root_reader_output",
            "selected_reader_output",
        }
    ),
}
EPISTEMIC_EDGE_RULES_BY_LANE = {
    "medical": (
        (
            frozenset(
                {
                    "data_release",
                    "denominator_definitions",
                    "clinical_analysis_input_identity",
                    "validation_partition_integrity",
                    "endpoint_analysis_set_reconciliation",
                    "model_complexity_sparse_event",
                    "fixed_horizon_risk_semantics",
                    "competing_risk",
                    "decision_curve_validity",
                    "external_transportability",
                }
            ),
            frozenset({"analysis_output"}),
            "derived_from",
        ),
        (
            frozenset(
                {
                    "analysis_output",
                    "candidate_artifact",
                    "evidence_record",
                    "numeric_trace",
                    "medical_initial_draft_preflight_candidate",
                    "citation_source_coverage",
                    "claim_guardrail",
                    "author_stance_integrity",
                }
            ),
            frozenset({"claim_evidence_map", "canonical_manuscript"}),
            "supports",
        ),
        (
            frozenset({"claim_evidence_map"}),
            frozenset({"canonical_manuscript"}),
            "supports",
        ),
        (
            frozenset(
                {
                    "reviewer_response",
                    "reviewer_action_matrix",
                    "reviewer_artifact_inventory",
                    "reviewer_external_synthesis",
                }
            ),
            frozenset({"canonical_manuscript", "reviewer_new_revision"}),
            "supports",
        ),
    ),
    "statistical": (
        (
            frozenset(
                {
                    "data_release",
                    "denominator_definitions",
                    "analysis_script",
                    "clinical_analysis_input_identity",
                    "validation_partition_integrity",
                    "endpoint_analysis_set_reconciliation",
                    "model_complexity_sparse_event",
                    "fixed_horizon_risk_semantics",
                    "competing_risk",
                    "decision_curve_validity",
                    "external_transportability",
                }
            ),
            frozenset({"analysis_output"}),
            "derived_from",
        ),
        (
            frozenset(
                {
                    "analysis_output",
                    "evidence_record",
                    "baseline_table_traceability",
                }
            ),
            frozenset(
                {
                    "numeric_trace",
                    "candidate_artifact",
                    "table_file",
                    "claim_evidence_map",
                    "canonical_manuscript",
                }
            ),
            "supports",
        ),
        (
            frozenset({"table_catalog"}),
            frozenset({"table_file"}),
            "derived_from",
        ),
        (
            frozenset({"claim_evidence_map"}),
            frozenset({"canonical_manuscript"}),
            "supports",
        ),
    ),
    "reference": (
        (
            frozenset({"reference_library"}),
            frozenset({"citation_ledger"}),
            "cites",
        ),
        (
            frozenset(
                {
                    "citation_ledger",
                    "evidence_record",
                    "citation_source_coverage",
                    "claim_guardrail",
                }
            ),
            frozenset({"claim_evidence_map", "canonical_manuscript"}),
            "supports",
        ),
        (
            frozenset({"claim_evidence_map"}),
            frozenset({"canonical_manuscript"}),
            "supports",
        ),
    ),
    "display": (
        (
            frozenset(
                {
                    "analysis_output",
                    "canonical_manuscript",
                    "claim_evidence_map",
                    "table_catalog",
                    "figure_catalog",
                    "render_environment_and_font_manifest",
                    "baseline_table_traceability",
                    "document_display_scope_coverage",
                }
            ),
            frozenset({"table_file", "figure_file"}),
            "renders",
        ),
        (
            frozenset(
                {
                    "canonical_manuscript",
                    "table_file",
                    "figure_file",
                    "render_environment_and_font_manifest",
                }
            ),
            frozenset({"docx", "pdf", "supplementary_output"}),
            "renders",
        ),
        (
            frozenset(
                {
                    "selected_archive_manifest",
                    "selected_build_receipt",
                    "build_dependency_manifest",
                }
            ),
            frozenset({"root_reader_output", "selected_reader_output"}),
            "renders",
        ),
    ),
    "publication": (
        (
            frozenset({"reference_library"}),
            frozenset({"citation_ledger"}),
            "cites",
        ),
        (
            frozenset({"citation_ledger", "claim_evidence_map"}),
            frozenset({"canonical_manuscript"}),
            "supports",
        ),
        (
            frozenset(
                {
                    "canonical_manuscript",
                    "table_catalog",
                    "table_file",
                    "figure_catalog",
                    "figure_file",
                    "render_environment_and_font_manifest",
                }
            ),
            frozenset({"docx", "pdf", "supplementary_output"}),
            "packages",
        ),
        (
            frozenset(
                {"docx", "pdf", "supplementary_output", "final_zip_member"}
            ),
            frozenset({"final_zip_allowlist"}),
            "packages",
        ),
        (
            frozenset(
                {
                    "selected_archive_manifest",
                    "selected_build_receipt",
                    "build_dependency_manifest",
                }
            ),
            frozenset({"root_reader_output", "selected_reader_output"}),
            "packages",
        ),
    ),
    "exact_byte_package": (
        (
            frozenset(
                {"docx", "pdf", "supplementary_output", "final_zip_member"}
            ),
            frozenset({"final_zip_allowlist"}),
            "packages",
        ),
        (
            frozenset(
                {
                    "selected_archive_manifest",
                    "selected_build_receipt",
                    "build_dependency_manifest",
                }
            ),
            frozenset({"root_reader_output", "selected_reader_output"}),
            "packages",
        ),
    ),
}

