"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_text,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)


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
        "policy_id": "scholarskills_linked_prediction_performance.v2",
        "validator_id": "validate_linked_prediction_performance",
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
STAGE_MINIMUM_SCOPE = {
    "direction_and_route_selection": "analysis_generation",
    "baseline_and_evidence_setup": "analysis_generation",
    "bounded_analysis_campaign": "analysis_generation",
    "manuscript_authoring": "manuscript_generation",
    "review_and_quality_gate": "manuscript_generation",
    "finalize_and_publication_handoff": "publication_generation",
}
STAGE_FIXED_REVIEW_LANE = {
    "bounded_analysis_campaign": "statistical",
}
_SCOPE_RANK = {
    "analysis_generation": 0,
    "manuscript_generation": 1,
    "publication_generation": 2,
}
