"""Validate one canonical MAS generation and its exact review receipts."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from ._record_validation import (
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
        "policy_id": "scholarskills_medical_initial_draft_preflight.v2",
        "validator_id": "validate_medical_initial_draft_preflight_candidate_v2",
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


def normalize_generation_manifest(
    value: Any,
    field: str = "generation_manifest",
) -> dict[str, Any]:
    """Normalize a manifest and recompute every executable identity."""

    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    keys = {
        "surface_kind",
        "schema_version",
        "generation_id",
        "manifest_scope",
        "generation_manifest_sha256",
        "artifacts",
        "independent_review_receipts",
    }
    if schema_version == 2:
        keys.add("review_scopes")
        if "professional_skill_invocations" in payload:
            keys.add("professional_skill_invocations")
        if "first_draft_quality_application" in payload:
            keys.add("first_draft_quality_application")
        if "clinical_analysis_identity_admission" in payload:
            keys.add("clinical_analysis_identity_admission")
        if "selected_build_binding" in payload:
            keys.add("selected_build_binding")
        if "reviewer_response_sync" in payload:
            keys.add("reviewer_response_sync")
    exact_keys(payload, keys, field)
    if payload.get("surface_kind") != "mas_evidence_generation_manifest":
        raise RequestShapeError(
            f"{field}.surface_kind must be mas_evidence_generation_manifest"
        )
    generation_id = text(payload.get("generation_id"), f"{field}.generation_id")
    scope = enum_text(
        payload.get("manifest_scope"),
        f"{field}.manifest_scope",
        set(REQUIRED_ROLES_BY_SCOPE),
    )
    artifacts = _normalize_generation_artifact_inventory(
        payload.get("artifacts"),
        f"{field}.artifacts",
        manifest_scope=scope,
        schema_version=schema_version,
    )

    manifest_core: dict[str, Any] = {
        "surface_kind": "mas_evidence_generation_manifest",
        "schema_version": schema_version,
        "generation_id": generation_id,
        "manifest_scope": scope,
        "artifacts": artifacts,
    }
    review_scopes: list[dict[str, Any]] = []
    if schema_version == 2:
        supplied_scopes = [
            _normalize_review_scope(
                item,
                f"{field}.review_scopes[{index}]",
                artifacts=artifacts,
            )
            for index, item in enumerate(
                sequence(payload.get("review_scopes"), f"{field}.review_scopes")
            )
        ]
        scope_lanes = [item["review_lane"] for item in supplied_scopes]
        if len(scope_lanes) != len(set(scope_lanes)):
            raise RequestShapeError(f"{field}.review_scopes contains duplicate lanes")
        required_lanes = REVIEW_LANES_BY_SCOPE[scope]
        if set(scope_lanes) != required_lanes:
            raise RequestShapeError(
                f"{field}.review_scopes must equal required lanes: "
                + ", ".join(sorted(required_lanes))
            )
        review_scopes = sorted(supplied_scopes, key=lambda item: item["review_lane"])
        manifest_core["review_scopes"] = review_scopes
        if "professional_skill_invocations" in payload:
            manifest_core["professional_skill_invocations"] = (
                _normalize_professional_skill_invocations(
                    payload.get("professional_skill_invocations"),
                    f"{field}.professional_skill_invocations",
                    artifacts=artifacts,
                )
            )
        if "first_draft_quality_application" in payload:
            if scope == "analysis_generation":
                raise RequestShapeError(
                    f"{field}.first_draft_quality_application is not allowed for "
                    "analysis_generation"
                )
            manifest_core["first_draft_quality_application"] = (
                _normalize_first_draft_quality_application(
                    payload.get("first_draft_quality_application"),
                    f"{field}.first_draft_quality_application",
                    artifacts=artifacts,
                    require_scholar_v2_semantics=(
                        "selected_build_binding" in payload
                    ),
                )
            )
        if "clinical_analysis_identity_admission" in payload:
            if scope != "analysis_generation":
                raise RequestShapeError(
                    f"{field}.clinical_analysis_identity_admission is allowed only "
                    "for analysis_generation"
                )
            manifest_core["clinical_analysis_identity_admission"] = (
                _normalize_clinical_analysis_identity_admission(
                    payload.get("clinical_analysis_identity_admission"),
                    f"{field}.clinical_analysis_identity_admission",
                    artifacts=artifacts,
                )
            )
        if "selected_build_binding" in payload:
            if scope == "analysis_generation":
                raise RequestShapeError(
                    f"{field}.selected_build_binding is not allowed for "
                    "analysis_generation"
                )
            manifest_core["selected_build_binding"] = _normalize_selected_build_binding(
                payload.get("selected_build_binding"),
                f"{field}.selected_build_binding",
                artifacts=artifacts,
            )
        if "reviewer_response_sync" in payload:
            if scope == "analysis_generation":
                raise RequestShapeError(
                    f"{field}.reviewer_response_sync is not allowed for "
                    "analysis_generation"
                )
            manifest_core["reviewer_response_sync"] = _normalize_reviewer_response_sync(
                payload.get("reviewer_response_sync"),
                f"{field}.reviewer_response_sync",
                artifacts=artifacts,
            )
        if "selected_build_binding" in manifest_core:
            _validate_scholar_v2_semantic_policy_invocations(
                manifest_core,
                f"{field}.first_draft_quality_application",
            )
    expected_fingerprint = fingerprint(manifest_core)
    supplied_fingerprint = sha256(
        payload.get("generation_manifest_sha256"),
        f"{field}.generation_manifest_sha256",
    )
    if supplied_fingerprint != expected_fingerprint:
        raise RequestShapeError(
            f"{field}.generation_manifest_sha256 does not match canonical members"
        )

    reviews = [
        _normalize_review_receipt(
            item,
            f"{field}.independent_review_receipts[{index}]",
            generation_id=generation_id,
            manifest_sha256=expected_fingerprint,
            artifacts=artifacts,
            manifest_version=schema_version,
            review_scopes=review_scopes,
        )
        for index, item in enumerate(
            sequence(
                payload.get("independent_review_receipts"),
                f"{field}.independent_review_receipts",
            )
        )
    ]
    lanes = [item["receipt"]["review_lane"] for item in reviews]
    if len(lanes) != len(set(lanes)):
        raise RequestShapeError(
            f"{field}.independent_review_receipts contains duplicate lanes"
        )
    reviews.sort(key=lambda item: item["receipt"]["review_lane"])
    if "reviewer_response_sync" in manifest_core:
        _validate_reviewer_response_evidence_refs(
            manifest_core["reviewer_response_sync"],
            reviews,
            f"{field}.reviewer_response_sync",
        )
    normalized = {
        **manifest_core,
        "generation_manifest_sha256": expected_fingerprint,
        "generation_manifest_size_bytes": len(canonical_json_bytes(manifest_core)),
        "independent_review_receipts": reviews,
    }
    return normalized


def _normalize_generation_artifact_inventory(
    value: Any,
    field: str,
    *,
    manifest_scope: str,
    schema_version: int,
) -> list[dict[str, Any]]:
    artifacts = [
        _normalize_artifact(
            item,
            f"{field}[{index}]",
            allowed_roles=ALLOWED_ROLES_BY_SCOPE[manifest_scope],
            schema_version=schema_version,
        )
        for index, item in enumerate(sequence(value, field))
    ]
    identities = [(item["role"], item["ref"]) for item in artifacts]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate role refs")
    if schema_version == 2:
        _require_unique_member_ids(artifacts, field)
    roles = {item["role"] for item in artifacts}
    missing_roles = sorted(REQUIRED_ROLES_BY_SCOPE[manifest_scope] - roles)
    if missing_roles:
        raise RequestShapeError(
            f"{field} missing required roles: " + ", ".join(missing_roles)
        )
    if sum(item["role"] == "source_input_digest" for item in artifacts) != 1:
        raise RequestShapeError(f"{field} requires exactly one source_input_digest")
    for role in sorted(PUBLICATION_SINGLETON_ROLES & roles):
        if sum(item["role"] == role for item in artifacts) != 1:
            raise RequestShapeError(f"{field} requires exactly one {role}")
    artifacts.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    return artifacts


def build_generation_manifest_v2(
    *,
    artifacts: list[dict[str, Any]],
    generation_id: str,
    manifest_scope: str,
    professional_skill_invocations: list[dict[str, Any]] | None = None,
    first_draft_quality_application: dict[str, Any] | None = None,
    clinical_analysis_identity_admission: dict[str, Any] | None = None,
    selected_build_binding: dict[str, Any] | None = None,
    reviewer_response_sync: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a canonical receipt-free v2 manifest from exact artifact records."""

    normalized_scope = enum_text(
        manifest_scope,
        "generation_manifest.manifest_scope",
        set(REQUIRED_ROLES_BY_SCOPE),
    )
    normalized_artifacts = _normalize_generation_artifact_inventory(
        artifacts,
        "generation_manifest.artifacts",
        manifest_scope=normalized_scope,
        schema_version=2,
    )
    core = {
        "surface_kind": "mas_evidence_generation_manifest",
        "schema_version": 2,
        "generation_id": text(generation_id, "generation_manifest.generation_id"),
        "manifest_scope": normalized_scope,
        "artifacts": normalized_artifacts,
        "review_scopes": build_review_scopes(
            normalized_artifacts,
            normalized_scope,
        ),
    }
    if professional_skill_invocations is not None:
        core["professional_skill_invocations"] = (
            _normalize_professional_skill_invocations(
                professional_skill_invocations,
                "generation_manifest.professional_skill_invocations",
                artifacts=normalized_artifacts,
            )
        )
    if first_draft_quality_application is not None:
        if normalized_scope == "analysis_generation":
            raise RequestShapeError(
                "first_draft_quality_application is not allowed for analysis_generation"
            )
        core["first_draft_quality_application"] = (
            _normalize_first_draft_quality_application(
                first_draft_quality_application,
                "generation_manifest.first_draft_quality_application",
                artifacts=normalized_artifacts,
                require_scholar_v2_semantics=selected_build_binding is not None,
            )
        )
    if clinical_analysis_identity_admission is not None:
        if normalized_scope != "analysis_generation":
            raise RequestShapeError(
                "clinical_analysis_identity_admission is allowed only for "
                "analysis_generation"
            )
        core["clinical_analysis_identity_admission"] = (
            _normalize_clinical_analysis_identity_admission(
                clinical_analysis_identity_admission,
                "generation_manifest.clinical_analysis_identity_admission",
                artifacts=normalized_artifacts,
            )
        )
    if selected_build_binding is not None:
        if normalized_scope == "analysis_generation":
            raise RequestShapeError(
                "selected_build_binding is not allowed for analysis_generation"
            )
        core["selected_build_binding"] = _normalize_selected_build_binding(
            selected_build_binding,
            "generation_manifest.selected_build_binding",
            artifacts=normalized_artifacts,
        )
    if reviewer_response_sync is not None:
        if normalized_scope == "analysis_generation":
            raise RequestShapeError(
                "reviewer_response_sync is not allowed for analysis_generation"
            )
        core["reviewer_response_sync"] = _normalize_reviewer_response_sync(
            reviewer_response_sync,
            "generation_manifest.reviewer_response_sync",
            artifacts=normalized_artifacts,
        )
    manifest = {
        **core,
        "generation_manifest_sha256": fingerprint(core),
        "independent_review_receipts": [],
    }
    normalize_generation_manifest(manifest)
    return manifest


def _manifest_artifact_ref(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
    expected_role: str,
) -> dict[str, Any]:
    normalized = _exact_ref(value, field, "mas_artifact")
    matches = [
        item
        for item in artifacts
        if item["role"] == expected_role
        and item["ref"] == normalized["ref"]
        and item["size_bytes"] == normalized["size_bytes"]
        and item["sha256"] == normalized["sha256"]
    ]
    if len(matches) != 1:
        raise RequestShapeError(
            f"{field} must match exactly one current {expected_role} artifact"
        )
    return normalized


def _normalize_no_authority_boundary(value: Any, field: str) -> dict[str, bool]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {"authorizes_publication", "authorizes_submission"},
        field,
    )
    if payload.get("authorizes_publication") is not False:
        raise RequestShapeError(f"{field}.authorizes_publication must be false")
    if payload.get("authorizes_submission") is not False:
        raise RequestShapeError(f"{field}.authorizes_submission must be false")
    return {"authorizes_publication": False, "authorizes_submission": False}


def _normalize_clinical_analysis_identity_admission(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "status",
            "clinical_analysis_input_identity_ref",
            "reason_codes",
            "unresolved_items",
            "next_owner",
            "human_gate_refs",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_clinical_analysis_identity_admission":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    status = enum_text(
        payload.get("status"),
        f"{field}.status",
        {"adjudicator_required", "open_human_gate", "route_back"},
    )
    reason_codes = text_list(payload.get("reason_codes"), f"{field}.reason_codes")
    unresolved_items = text_list(
        payload.get("unresolved_items"), f"{field}.unresolved_items"
    )
    next_owner = optional_text(payload.get("next_owner"), f"{field}.next_owner")
    human_gate_refs = _typed_ref_list(
        payload.get("human_gate_refs"),
        f"{field}.human_gate_refs",
        "mas_human_gate",
    )
    if status == "adjudicator_required" and (
        unresolved_items or next_owner is not None or human_gate_refs
    ):
        raise RequestShapeError(
            f"{field} adjudicator_required cannot carry unresolved or gate state"
        )
    if status == "open_human_gate" and (
        not reason_codes
        or not unresolved_items
        or next_owner is None
        or not human_gate_refs
    ):
        raise RequestShapeError(
            f"{field} open_human_gate requires reasons, unresolved items, owner, and refs"
        )
    if status == "route_back" and (
        not reason_codes
        or not unresolved_items
        or next_owner != "baseline_and_evidence_setup"
        or human_gate_refs
    ):
        raise RequestShapeError(
            f"{field} route_back requires baseline owner and no human-gate refs"
        )
    return {
        "surface_kind": "mas_clinical_analysis_identity_admission",
        "schema_version": 1,
        "status": status,
        "clinical_analysis_input_identity_ref": _manifest_artifact_ref(
            payload.get("clinical_analysis_input_identity_ref"),
            f"{field}.clinical_analysis_input_identity_ref",
            artifacts=artifacts,
            expected_role="clinical_analysis_input_identity",
        ),
        "reason_codes": reason_codes,
        "unresolved_items": unresolved_items,
        "next_owner": next_owner,
        "human_gate_refs": human_gate_refs,
        "authority_boundary": _normalize_no_authority_boundary(
            payload.get("authority_boundary"), f"{field}.authority_boundary"
        ),
    }


def _normalize_selected_build_binding(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "selected_archive_label",
            *SELECTED_BUILD_ROLE_BY_REF_FIELD,
            "dependency_currentness",
            "dependency_currentness_receipt_ref",
            "dependency_currentness_receipt",
            "root_matches_selected_bytes",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_selected_build_binding":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    refs = {
        ref_field: _manifest_artifact_ref(
            payload.get(ref_field),
            f"{field}.{ref_field}",
            artifacts=artifacts,
            expected_role=role,
        )
        for ref_field, role in SELECTED_BUILD_ROLE_BY_REF_FIELD.items()
    }
    root_matches_selected_bytes = payload.get("root_matches_selected_bytes")
    if not isinstance(root_matches_selected_bytes, bool):
        raise RequestShapeError(
            f"{field}.root_matches_selected_bytes must be boolean"
        )
    exact_bytes_match = (
        refs["root_reader_output_ref"]["size_bytes"]
        == refs["selected_reader_output_ref"]["size_bytes"]
        and refs["root_reader_output_ref"]["sha256"]
        == refs["selected_reader_output_ref"]["sha256"]
    )
    if root_matches_selected_bytes != exact_bytes_match:
        raise RequestShapeError(
            f"{field}.root_matches_selected_bytes does not match exact reader bytes"
        )
    return {
        "surface_kind": "mas_selected_build_binding",
        "schema_version": 1,
        "selected_archive_label": text(
            payload.get("selected_archive_label"),
            f"{field}.selected_archive_label",
        ),
        **refs,
        "dependency_currentness": enum_text(
            payload.get("dependency_currentness"),
            f"{field}.dependency_currentness",
            {"current", "stale", "open"},
        ),
        "dependency_currentness_receipt_ref": _exact_ref(
            payload.get("dependency_currentness_receipt_ref"),
            f"{field}.dependency_currentness_receipt_ref",
            "mas_build_dependency_currentness_receipt",
        ),
        "dependency_currentness_receipt": _normalize_dependency_currentness_receipt(
            payload.get("dependency_currentness_receipt"),
            f"{field}.dependency_currentness_receipt",
            dependency_manifest_ref=refs["dependency_manifest_ref"],
            dependency_currentness=enum_text(
                payload.get("dependency_currentness"),
                f"{field}.dependency_currentness",
                {"current", "stale", "open"},
            ),
            receipt_ref=payload.get("dependency_currentness_receipt_ref"),
        ),
        "root_matches_selected_bytes": root_matches_selected_bytes,
        "authority_boundary": _normalize_no_authority_boundary(
            payload.get("authority_boundary"), f"{field}.authority_boundary"
        ),
    }


def _normalize_dependency_currentness_receipt(
    value: Any,
    field: str,
    *,
    dependency_manifest_ref: Mapping[str, Any],
    dependency_currentness: str,
    receipt_ref: Any,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "owner",
            "authority_role",
            "authority_ref",
            "dependency_manifest_ref",
            "dependency_currentness",
            "receipt_id",
            "receipt_size_bytes",
            "receipt_fingerprint",
        },
        field,
    )
    if payload.get("receipt_kind") != "mas_build_dependency_currentness_receipt":
        raise RequestShapeError(f"{field}.receipt_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("owner") != "MedAutoScience":
        raise RequestShapeError(f"{field}.owner must be MedAutoScience")
    if payload.get("authority_role") != "build_dependency_currentness_owner":
        raise RequestShapeError(f"{field}.authority_role is invalid")
    authority_ref = _exact_ref(
        payload.get("authority_ref"),
        f"{field}.authority_ref",
        "mas_build_dependency_currentness_authority",
    )
    normalized_dependency_ref = _exact_ref(
        payload.get("dependency_manifest_ref"),
        f"{field}.dependency_manifest_ref",
        "mas_artifact",
    )
    if normalized_dependency_ref != dict(dependency_manifest_ref):
        raise RequestShapeError(
            f"{field}.dependency_manifest_ref does not match selected build binding"
        )
    normalized_status = enum_text(
        payload.get("dependency_currentness"),
        f"{field}.dependency_currentness",
        {"current", "stale", "open"},
    )
    if normalized_status != dependency_currentness:
        raise RequestShapeError(
            f"{field}.dependency_currentness does not match selected build binding"
        )
    core = {
        "receipt_kind": "mas_build_dependency_currentness_receipt",
        "schema_version": 1,
        "owner": "MedAutoScience",
        "authority_role": "build_dependency_currentness_owner",
        "authority_ref": authority_ref,
        "dependency_manifest_ref": normalized_dependency_ref,
        "dependency_currentness": normalized_status,
    }
    expected_fingerprint = fingerprint(core)
    supplied_fingerprint = sha256(
        payload.get("receipt_fingerprint"), f"{field}.receipt_fingerprint"
    )
    if supplied_fingerprint != expected_fingerprint:
        raise RequestShapeError(f"{field}.receipt_fingerprint is invalid")
    expected_size = len(canonical_json_bytes(core))
    if (
        integer(payload.get("receipt_size_bytes"), f"{field}.receipt_size_bytes")
        != expected_size
    ):
        raise RequestShapeError(f"{field}.receipt_size_bytes is invalid")
    receipt_id = text(payload.get("receipt_id"), f"{field}.receipt_id")
    normalized_ref = _exact_ref(
        receipt_ref,
        f"{field}.receipt_ref",
        "mas_build_dependency_currentness_receipt",
    )
    if normalized_ref != {
        "kind": "mas_build_dependency_currentness_receipt",
        "ref": receipt_id,
        "size_bytes": expected_size,
        "sha256": expected_fingerprint,
    }:
        raise RequestShapeError(f"{field}.receipt_ref does not match sealed receipt")
    return {
        **core,
        "receipt_id": receipt_id,
        "receipt_size_bytes": expected_size,
        "receipt_fingerprint": expected_fingerprint,
    }


def _normalize_affected_artifact_binding(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"member_id", "ref", "size_bytes", "sha256"}, field)
    normalized = {
        "member_id": text(payload.get("member_id"), f"{field}.member_id"),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    if sum(
        all(item[key] == normalized[key] for key in normalized)
        for item in artifacts
    ) != 1:
        raise RequestShapeError(
            f"{field} must match exactly one current manifest artifact member"
        )
    return normalized


def _normalize_reviewer_response_sync(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "response_ref",
            "action_matrix_ref",
            "action_matrix_item_ids",
            "artifact_inventory_ref",
            "candidate_state",
            "sync_status",
            "items",
            "external_synthesis_ref",
            "new_revision_ref",
            "post_freeze_disposition",
            "authority_boundary",
        },
        field,
    )
    if payload.get("surface_kind") != "mas_reviewer_response_sync":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    refs = {
        ref_field: _manifest_artifact_ref(
            payload.get(ref_field),
            f"{field}.{ref_field}",
            artifacts=artifacts,
            expected_role=REVIEWER_RESPONSE_ROLE_BY_REF_FIELD[ref_field],
        )
        for ref_field in ("response_ref", "action_matrix_ref", "artifact_inventory_ref")
    }
    action_matrix_item_ids = text_list(
        payload.get("action_matrix_item_ids"),
        f"{field}.action_matrix_item_ids",
    )
    if not action_matrix_item_ids:
        raise RequestShapeError(f"{field}.action_matrix_item_ids must not be empty")
    optional_refs: dict[str, dict[str, Any] | None] = {}
    for ref_field in ("external_synthesis_ref", "new_revision_ref"):
        raw_ref = payload.get(ref_field)
        optional_refs[ref_field] = (
            None
            if raw_ref is None
            else _manifest_artifact_ref(
                raw_ref,
                f"{field}.{ref_field}",
                artifacts=artifacts,
                expected_role=REVIEWER_RESPONSE_ROLE_BY_REF_FIELD[ref_field],
            )
        )
    items: list[dict[str, Any]] = []
    for index, raw_item in enumerate(sequence(payload.get("items"), f"{field}.items")):
        item_field = f"{field}.items[{index}]"
        item_payload = mapping(raw_item, item_field)
        exact_keys(
            item_payload,
            {
                "comment_id",
                "status",
                "affected_artifact_bindings",
                "evidence_refs",
                "remaining_gap_or_not_applicable_reason",
            },
            item_field,
        )
        status = enum_text(
            item_payload.get("status"),
            f"{item_field}.status",
            {
                "planned",
                "implemented_candidate",
                "independently_reviewed_candidate",
                "not_applicable_with_reason",
            },
        )
        affected = [
            _normalize_affected_artifact_binding(
                binding,
                f"{item_field}.affected_artifact_bindings[{binding_index}]",
                artifacts=artifacts,
            )
            for binding_index, binding in enumerate(
                sequence(
                    item_payload.get("affected_artifact_bindings"),
                    f"{item_field}.affected_artifact_bindings",
                )
            )
        ]
        affected.sort(key=lambda item: item["member_id"])
        if len({item["member_id"] for item in affected}) != len(affected):
            raise RequestShapeError(
                f"{item_field}.affected_artifact_bindings contains duplicate members"
            )
        reason = optional_text(
            item_payload.get("remaining_gap_or_not_applicable_reason"),
            f"{item_field}.remaining_gap_or_not_applicable_reason",
        )
        evidence_refs = _normalize_reviewer_response_evidence_refs(
            item_payload.get("evidence_refs"),
            f"{item_field}.evidence_refs",
        )
        if status in {
            "implemented_candidate",
            "independently_reviewed_candidate",
        } and not affected:
            raise RequestShapeError(
                f"{item_field}.{status} requires affected artifact bindings"
            )
        if status in {
            "implemented_candidate",
            "independently_reviewed_candidate",
        } and not evidence_refs:
            raise RequestShapeError(
                f"{item_field}.{status} requires exact evidence refs"
            )
        if status == "not_applicable_with_reason" and reason is None:
            raise RequestShapeError(
                f"{item_field}.not_applicable_with_reason requires a reason"
            )
        items.append(
            {
                "comment_id": text(
                    item_payload.get("comment_id"), f"{item_field}.comment_id"
                ),
                "status": status,
                "affected_artifact_bindings": affected,
                "evidence_refs": evidence_refs,
                "remaining_gap_or_not_applicable_reason": reason,
            }
        )
    if not items or len({item["comment_id"] for item in items}) != len(items):
        raise RequestShapeError(f"{field}.items must be non-empty with unique comment_id")
    comment_ids = {item["comment_id"] for item in items}
    if comment_ids != set(action_matrix_item_ids):
        raise RequestShapeError(
            f"{field}.items must exactly cover action_matrix_item_ids"
        )
    candidate_state = enum_text(
        payload.get("candidate_state"),
        f"{field}.candidate_state",
        {"pre_freeze", "frozen"},
    )
    post_freeze_disposition = enum_text(
        payload.get("post_freeze_disposition"),
        f"{field}.post_freeze_disposition",
        {
            "not_started",
            "external_synthesis_bound",
            "scientific_change_requires_new_revision",
        },
    )
    if candidate_state == "pre_freeze" and (
        post_freeze_disposition != "not_started"
        or any(optional_refs.values())
    ):
        raise RequestShapeError(
            f"{field} pre_freeze sync cannot carry post-freeze refs or disposition"
        )
    if post_freeze_disposition == "external_synthesis_bound" and (
        optional_refs["external_synthesis_ref"] is None
        or optional_refs["new_revision_ref"] is not None
    ):
        raise RequestShapeError(
            f"{field} external synthesis disposition requires only external_synthesis_ref"
        )
    if post_freeze_disposition == "scientific_change_requires_new_revision" and (
        optional_refs["new_revision_ref"] is None
    ):
        raise RequestShapeError(
            f"{field} scientific response change requires new_revision_ref"
        )
    if candidate_state == "frozen" and post_freeze_disposition == "not_started" and any(
        optional_refs.values()
    ):
        raise RequestShapeError(
            f"{field} frozen not_started disposition cannot carry post-freeze refs"
        )
    return {
        "surface_kind": "mas_reviewer_response_sync",
        "schema_version": 1,
        **refs,
        "action_matrix_item_ids": sorted(action_matrix_item_ids),
        "candidate_state": candidate_state,
        "sync_status": enum_text(
            payload.get("sync_status"),
            f"{field}.sync_status",
            {"synchronized", "route_back_required"},
        ),
        "items": sorted(items, key=lambda item: item["comment_id"]),
        **optional_refs,
        "post_freeze_disposition": post_freeze_disposition,
        "authority_boundary": _normalize_no_authority_boundary(
            payload.get("authority_boundary"), f"{field}.authority_boundary"
        ),
    }


def _normalize_reviewer_response_evidence_refs(
    value: Any,
    field: str,
) -> list[dict[str, Any]]:
    refs: list[dict[str, Any]] = []
    for index, raw_ref in enumerate(sequence(value, field)):
        ref_field = f"{field}[{index}]"
        payload = mapping(raw_ref, ref_field)
        kind = enum_text(
            payload.get("kind"),
            f"{ref_field}.kind",
            {"mas_evidence", "mas_reviewer_receipt"},
        )
        refs.append(_exact_ref(payload, ref_field, kind))
    identities = [
        (item["kind"], item["ref"], item["size_bytes"], item["sha256"])
        for item in refs
    ]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate exact refs")
    return refs


def _validate_reviewer_response_evidence_refs(
    response_sync: Mapping[str, Any],
    reviews: list[dict[str, Any]],
    field: str,
) -> None:
    current_review_refs = {
        (
            wrapper["receipt_ref"]["ref"],
            wrapper["receipt_ref"]["size_bytes"],
            wrapper["receipt_ref"]["sha256"],
        )
        for wrapper in reviews
    }
    for index, item in enumerate(response_sync["items"]):
        item_field = f"{field}.items[{index}]"
        evidence_refs = item["evidence_refs"]
        if item["status"] == "independently_reviewed_candidate":
            if any(ref["kind"] != "mas_reviewer_receipt" for ref in evidence_refs):
                raise RequestShapeError(
                    f"{item_field}.independently_reviewed_candidate requires "
                    "current independent reviewer receipt refs"
                )
            for ref in evidence_refs:
                identity = (ref["ref"], ref["size_bytes"], ref["sha256"])
                if identity not in current_review_refs:
                    raise RequestShapeError(
                        f"{item_field}.evidence_refs must bind a current manifest "
                        "independent reviewer receipt"
                    )
        elif any(ref["kind"] != "mas_evidence" for ref in evidence_refs):
            raise RequestShapeError(
                f"{item_field}.{item['status']} accepts only mas_evidence exact refs"
            )


def _normalize_first_draft_quality_application(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
    require_scholar_v2_semantics: bool = False,
) -> dict[str, Any]:
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    require_scholar_v2_semantics = (
        require_scholar_v2_semantics and schema_version == 2
    )
    keys = {
        "surface_kind",
        "schema_version",
        "paper_type",
        "validation_design",
        "triggers",
        "candidate_refs",
    }
    if schema_version == 2:
        keys.add("candidate_dispositions")
        if require_scholar_v2_semantics:
            keys.add("scholar_v2_semantic_policy_bindings")
    exact_keys(
        payload,
        keys,
        field,
    )
    if payload.get("surface_kind") != "mas_first_draft_quality_application_candidate":
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    paper_type = enum_text(
        payload.get("paper_type"),
        f"{field}.paper_type",
        {"prediction_model", "other"},
    )
    validation_design = enum_text(
        payload.get("validation_design"),
        f"{field}.validation_design",
        set(FIRST_DRAFT_VALIDATION_DESIGNS),
    )
    if paper_type == "prediction_model" and validation_design == "not_applicable":
        raise RequestShapeError(
            f"{field}.validation_design must classify prediction-model validation"
        )
    if paper_type == "other" and validation_design != "not_applicable":
        raise RequestShapeError(
            f"{field}.validation_design must be not_applicable for other paper types"
        )

    triggers_field = f"{field}.triggers"
    trigger_payload = mapping(payload.get("triggers"), triggers_field)
    trigger_keys = {
        "reports_fixed_horizon_risk",
        "competing_risk_relevant",
        "reports_decision_curve_analysis",
        "includes_table_one",
        "requires_reader_pdf",
    }
    if schema_version == 2:
        trigger_keys.add("uses_clinical_or_registry_data")
    exact_keys(trigger_payload, trigger_keys, triggers_field)
    triggers: dict[str, bool] = {}
    for key in sorted(trigger_keys):
        trigger = trigger_payload.get(key)
        if not isinstance(trigger, bool):
            raise RequestShapeError(f"{triggers_field}.{key} must be boolean")
        triggers[key] = trigger
    if schema_version == 2 and paper_type == "prediction_model" and not triggers[
        "uses_clinical_or_registry_data"
    ]:
        raise RequestShapeError(
            f"{triggers_field}.uses_clinical_or_registry_data must be true for "
            "prediction-model manuscripts"
        )

    refs_field = f"{field}.candidate_refs"
    refs_payload = mapping(payload.get("candidate_refs"), refs_field)
    role_by_ref_field = (
        FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD
        if require_scholar_v2_semantics
        else LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD
    )
    exact_keys(refs_payload, set(role_by_ref_field), refs_field)
    candidate_refs: dict[str, dict[str, Any] | None] = {}
    for ref_field, role in role_by_ref_field.items():
        raw_ref = refs_payload.get(ref_field)
        if raw_ref is None:
            candidate_refs[ref_field] = None
            continue
        candidate_ref = _exact_ref(raw_ref, f"{refs_field}.{ref_field}", "mas_artifact")
        if schema_version == 2 and candidate_ref["size_bytes"] == 0:
            raise RequestShapeError(
                f"{refs_field}.{ref_field}.size_bytes must be greater than zero "
                "for a current first-draft candidate"
            )
        matching_artifacts = [
            artifact
            for artifact in artifacts
            if artifact["role"] == role
            and all(
                candidate_ref[key] == artifact[key]
                for key in ("ref", "size_bytes", "sha256")
            )
        ]
        if len(matching_artifacts) != 1:
            raise RequestShapeError(
                f"{refs_field}.{ref_field} must bind the exact {role} artifact"
            )
        candidate_refs[ref_field] = candidate_ref
    if validation_design != "external_validation" and candidate_refs[
        "external_transportability_ref"
    ] is not None:
        raise RequestShapeError(
            f"{refs_field}.external_transportability_ref is external-validation-only"
        )

    normalized = {
        "surface_kind": "mas_first_draft_quality_application_candidate",
        "schema_version": schema_version,
        "paper_type": paper_type,
        "validation_design": validation_design,
        "triggers": triggers,
        "candidate_refs": candidate_refs,
    }
    if schema_version == 2:
        dispositions_field = f"{field}.candidate_dispositions"
        dispositions_payload = mapping(
            payload.get("candidate_dispositions"), dispositions_field
        )
        exact_keys(
            dispositions_payload,
            set(role_by_ref_field),
            dispositions_field,
        )
        applicable_fields = first_draft_applicable_ref_fields(
            normalized,
            include_scholar_v2_semantics=require_scholar_v2_semantics,
        )
        dispositions = {}
        for ref_field in role_by_ref_field:
            disposition = _normalize_first_draft_candidate_disposition(
                dispositions_payload.get(ref_field),
                f"{dispositions_field}.{ref_field}",
                candidate_ref=candidate_refs[ref_field],
            )
            if ref_field in applicable_fields:
                if disposition["status"] == "not_applicable_with_reason":
                    raise RequestShapeError(
                        f"{dispositions_field}.{ref_field} is required by the "
                        "declared paper type and triggers"
                    )
            elif disposition["status"] != "not_applicable_with_reason":
                raise RequestShapeError(
                    f"{dispositions_field}.{ref_field} must be "
                    "not_applicable_with_reason for the declared paper type and triggers"
                )
            dispositions[ref_field] = disposition
        normalized["candidate_dispositions"] = dispositions
        if require_scholar_v2_semantics:
            normalized["scholar_v2_semantic_policy_bindings"] = (
                _normalize_scholar_v2_semantic_policy_bindings(
                    payload.get("scholar_v2_semantic_policy_bindings"),
                    f"{field}.scholar_v2_semantic_policy_bindings",
                    required_skill_ids={
                        skill_id
                        for skill_id, policy in SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL.items()
                        if candidate_refs[policy["candidate_ref_field"]] is not None
                    },
                )
            )
            for binding in normalized["scholar_v2_semantic_policy_bindings"]:
                if candidate_refs[binding["candidate_ref_field"]] != binding[
                    "candidate_ref"
                ]:
                    raise RequestShapeError(
                        f"{field}.scholar_v2_semantic_policy_bindings must bind the "
                        "current first-draft candidate artifact bytes"
                    )
    return normalized


def _normalize_scholar_v2_semantic_policy_bindings(
    value: Any,
    field: str,
    *,
    required_skill_ids: set[str],
) -> list[dict[str, Any]]:
    bindings: list[dict[str, Any]] = []
    for index, raw in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        payload = mapping(raw, item_field)
        exact_keys(
            payload,
            {
                "skill_id",
                "semantic_policy_id",
                "validator_id",
                "semantic_policy_ref",
                "candidate_ref_field",
                "candidate_surface_kind",
                "candidate_ref",
                "invocation_ref",
                "receipt_ref",
            },
            item_field,
        )
        skill_id = enum_text(
            payload.get("skill_id"),
            f"{item_field}.skill_id",
            set(SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL),
        )
        policy = SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL[skill_id]
        if payload.get("semantic_policy_id") != policy["policy_id"]:
            raise RequestShapeError(
                f"{item_field}.semantic_policy_id must bind the current Scholar v2 policy"
            )
        if payload.get("validator_id") != policy["validator_id"]:
            raise RequestShapeError(
                f"{item_field}.validator_id must bind the current Scholar validator"
            )
        if payload.get("candidate_ref_field") != policy["candidate_ref_field"]:
            raise RequestShapeError(
                f"{item_field}.candidate_ref_field is not the current first-draft gate"
            )
        if payload.get("candidate_surface_kind") != policy["candidate_surface_kind"]:
            raise RequestShapeError(
                f"{item_field}.candidate_surface_kind is not the Scholar candidate family"
            )
        bindings.append(
            {
                "skill_id": skill_id,
                "semantic_policy_id": policy["policy_id"],
                "validator_id": policy["validator_id"],
                "candidate_ref_field": policy["candidate_ref_field"],
                "candidate_surface_kind": policy["candidate_surface_kind"],
                "semantic_policy_ref": _exact_ref(
                    payload.get("semantic_policy_ref"),
                    f"{item_field}.semantic_policy_ref",
                    "scholarskills_semantic_policy",
                ),
                "candidate_ref": _exact_ref(
                    payload.get("candidate_ref"),
                    f"{item_field}.candidate_ref",
                    "mas_artifact",
                ),
                "invocation_ref": _exact_ref(
                    payload.get("invocation_ref"),
                    f"{item_field}.invocation_ref",
                    "mas_professional_skill_invocation",
                ),
                "receipt_ref": _exact_ref(
                    payload.get("receipt_ref"),
                    f"{item_field}.receipt_ref",
                    "scholarskills_professional_skill_receipt",
                ),
            }
        )
    skills = [item["skill_id"] for item in bindings]
    if set(skills) != required_skill_ids or len(skills) != len(set(skills)):
        raise RequestShapeError(
            f"{field} must contain exactly one current binding for each applicable Scholar v2 policy"
        )
    return sorted(bindings, key=lambda item: item["skill_id"])


def _validate_scholar_v2_semantic_policy_invocations(
    manifest_core: Mapping[str, Any],
    field: str,
) -> None:
    application = manifest_core.get("first_draft_quality_application")
    if application is None or application["schema_version"] != 2:
        return
    invocations = {
        item["skill_id"]: item
        for item in manifest_core.get("professional_skill_invocations", [])
        if item["surface_kind"]
        == "mas_professional_manuscript_skill_invocation_candidate"
    }
    for binding in application["scholar_v2_semantic_policy_bindings"]:
        invocation = invocations.get(binding["skill_id"])
        if invocation is None:
            raise RequestShapeError(
                f"{field} Scholar v2 policy binding requires one exact professional invocation"
            )
        if invocation["schema_version"] != 2:
            raise RequestShapeError(
                f"{field} current Scholar v2 semantic policy requires a v2 professional invocation"
            )
        if (
            invocation.get("invocation_ref") != binding["invocation_ref"]
            or invocation.get("receipt_ref") != binding["receipt_ref"]
            or invocation.get("semantic_policy_id")
            != binding["semantic_policy_id"]
            or invocation.get("semantic_validator_id") != binding["validator_id"]
            or invocation.get("semantic_policy_ref")
            != binding["semantic_policy_ref"]
            or invocation.get("semantic_candidate_ref") != binding["candidate_ref"]
        ):
            raise RequestShapeError(
                f"{field} Scholar v2 policy binding does not match exact invocation and receipt refs"
            )


def first_draft_applicable_ref_fields(
    application: Mapping[str, Any],
    *,
    include_scholar_v2_semantics: bool | None = None,
) -> frozenset[str]:
    fields = {
        "medical_initial_draft_preflight_candidate_ref",
        "citation_source_coverage_ref",
        "claim_guardrail_ref",
    }
    uses_scholar_v2_semantics = (
        "scholar_v2_semantic_policy_bindings" in application
        if include_scholar_v2_semantics is None
        else include_scholar_v2_semantics
    )
    if uses_scholar_v2_semantics:
        fields.add("active_reference_currentness_ref")
    if application["triggers"]["uses_clinical_or_registry_data"]:
        fields.add("clinical_analysis_input_identity_ref")
    if application["paper_type"] == "prediction_model":
        fields.update(
            {
                "validation_partition_integrity_ref",
                "endpoint_analysis_set_reconciliation_ref",
                "model_complexity_sparse_event_ref",
            }
        )
        if uses_scholar_v2_semantics:
            fields.add("linked_prediction_performance_ref")
    triggers = application["triggers"]
    if triggers["reports_fixed_horizon_risk"]:
        fields.add("fixed_horizon_risk_semantics_ref")
    if triggers["competing_risk_relevant"]:
        fields.add("competing_risk_ref")
    if triggers["reports_decision_curve_analysis"]:
        fields.add("decision_curve_validity_ref")
    if triggers["includes_table_one"]:
        fields.add("baseline_table_traceability_ref")
    if triggers["requires_reader_pdf"]:
        fields.add("document_display_scope_coverage_ref")
        if uses_scholar_v2_semantics:
            fields.add("display_render_integrity_ref")
    if application["validation_design"] == "external_validation":
        fields.add("external_transportability_ref")
    return frozenset(fields)


def _normalize_first_draft_candidate_disposition(
    value: Any,
    field: str,
    *,
    candidate_ref: Mapping[str, Any] | None,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "status",
            "earliest_route_back_owner",
            "reason_codes",
            "unresolved_items",
            "not_applicable_reason",
        },
        field,
    )
    status = enum_text(
        payload.get("status"),
        f"{field}.status",
        set(FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES),
    )
    owner = optional_text(
        payload.get("earliest_route_back_owner"),
        f"{field}.earliest_route_back_owner",
    )
    if owner is not None and owner not in FIRST_DRAFT_QUALITY_ROUTE_PRIORITY:
        raise RequestShapeError(
            f"{field}.earliest_route_back_owner must be a canonical first-draft Stage"
        )
    reason_codes = text_list(payload.get("reason_codes"), f"{field}.reason_codes")
    unresolved_items = text_list(
        payload.get("unresolved_items"), f"{field}.unresolved_items"
    )
    not_applicable_reason = optional_text(
        payload.get("not_applicable_reason"),
        f"{field}.not_applicable_reason",
    )

    if status == "satisfied":
        if candidate_ref is None:
            raise RequestShapeError(f"{field} satisfied status requires its exact candidate ref")
        if owner is not None or reason_codes or unresolved_items or not_applicable_reason:
            raise RequestShapeError(f"{field} satisfied status is contradictory")
    elif status == "route_back_required":
        if candidate_ref is None:
            raise RequestShapeError(
                f"{field} route_back_required status requires its exact candidate ref"
            )
        if owner is None or not reason_codes or not unresolved_items:
            raise RequestShapeError(
                f"{field} route_back_required status requires owner, reason codes, "
                "and unresolved items"
            )
        if not_applicable_reason is not None:
            raise RequestShapeError(
                f"{field} route_back_required status cannot carry a not-applicable reason"
            )
    else:
        if candidate_ref is not None:
            raise RequestShapeError(
                f"{field} not_applicable_with_reason status cannot carry a candidate ref"
            )
        if owner is not None or reason_codes or unresolved_items:
            raise RequestShapeError(
                f"{field} not_applicable_with_reason status is contradictory"
            )
        if not_applicable_reason is None:
            raise RequestShapeError(
                f"{field} not_applicable_with_reason status requires a reason"
            )

    return {
        "status": status,
        "earliest_route_back_owner": owner,
        "reason_codes": reason_codes,
        "unresolved_items": unresolved_items,
        "not_applicable_reason": not_applicable_reason,
    }


def _normalize_professional_skill_invocations(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    artifact_by_member_id = {
        item["member_id"]: item for item in artifacts if "member_id" in item
    }
    invocations = []
    for index, item in enumerate(sequence(value, field)):
        item_field = f"{field}[{index}]"
        if mapping(item, item_field).get("surface_kind") == (
            "mas_professional_manuscript_skill_invocation_candidate"
        ):
            normalized = _normalize_professional_manuscript_skill_invocation(
                item,
                item_field,
                artifact_by_member_id=artifact_by_member_id,
            )
        else:
            normalized = _normalize_professional_skill_invocation(
                item,
                item_field,
                artifact_by_member_id=artifact_by_member_id,
            )
        invocations.append(normalized)
    identities = [
        (item["surface_kind"], item.get("figure_id"), item["skill_id"])
        for item in invocations
    ]
    if len(identities) != len(set(identities)):
        raise RequestShapeError(f"{field} contains duplicate target/skill receipts")
    member_owner: dict[str, str] = {}
    for invocation in invocations:
        if "figure_id" not in invocation:
            continue
        for binding in invocation["output_artifact_bindings"]:
            member_id = binding["member_id"]
            prior_figure = member_owner.setdefault(member_id, invocation["figure_id"])
            if prior_figure != invocation["figure_id"]:
                raise RequestShapeError(
                    f"{field} binds figure artifact {member_id} to multiple figures"
                )
    invocations.sort(
        key=lambda item: (
            item["surface_kind"],
            item.get("figure_id", ""),
            item["skill_id"],
        )
    )
    return invocations


def _normalize_professional_manuscript_skill_invocation(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    keys = {
        "surface_kind",
        "schema_version",
        "receipt_id",
        "skill_id",
        "package_id",
        "package_version",
        "package_source_ref",
        "package_source_sha256",
        "skill_source_ref",
        "skill_source_sha256",
        "invocation_id",
        "input_contract_ref",
        "input_sha256",
        "consumed_rule_refs",
        "output_artifact_bindings",
        "template_substitution",
        "status",
        "refs_only",
        "authority",
        "publication_ready",
    }
    semantic_fields = {
        "semantic_policy_id",
        "semantic_validator_id",
        "semantic_policy_ref",
        "semantic_candidate_ref",
    }
    has_semantic_binding = any(field_name in payload for field_name in semantic_fields)
    if schema_version == 2:
        keys.update({"invocation_ref", "receipt_ref", "input_artifact_bindings"})
        if has_semantic_binding:
            keys.update(
                semantic_fields
            )
    if (
        payload.get("skill_id") == "medical-table-design"
        and "table_quality_application" in payload
    ):
        keys.add("table_quality_application")
    exact_keys(payload, keys, field)
    skill_id = enum_text(
        payload.get("skill_id"),
        f"{field}.skill_id",
        set(PROFESSIONAL_MANUSCRIPT_SKILL_ROLES),
    )
    if payload.get("surface_kind") != (
        "mas_professional_manuscript_skill_invocation_candidate"
    ):
        raise RequestShapeError(f"{field}.surface_kind is invalid")
    if payload.get("package_id") != "mas-scholar-skills":
        raise RequestShapeError(f"{field}.package_id must be mas-scholar-skills")
    if payload.get("template_substitution") is not False:
        raise RequestShapeError(f"{field}.template_substitution must be false")
    if payload.get("status") != "completed" or payload.get("refs_only") is not True:
        raise RequestShapeError(f"{field} must be completed refs-only evidence")
    if (
        payload.get("authority") is not False
        or payload.get("publication_ready") is not False
    ):
        raise RequestShapeError(
            f"{field} cannot grant authority or publication readiness"
        )
    bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}.output_artifact_bindings[{index}]",
            artifact_by_member_id=artifact_by_member_id,
            allowed_roles=PROFESSIONAL_MANUSCRIPT_SKILL_ROLES[skill_id],
        )
        for index, item in enumerate(
            sequence(
                payload.get("output_artifact_bindings"),
                f"{field}.output_artifact_bindings",
            )
        )
    ]
    if not bindings:
        raise RequestShapeError(f"{field}.output_artifact_bindings must not be empty")
    rules = text_list(payload.get("consumed_rule_refs"), f"{field}.consumed_rule_refs")
    if not rules:
        raise RequestShapeError(f"{field}.consumed_rule_refs must not be empty")
    normalized = {
        "surface_kind": "mas_professional_manuscript_skill_invocation_candidate",
        "schema_version": schema_version,
        "receipt_id": text(payload.get("receipt_id"), f"{field}.receipt_id"),
        "skill_id": skill_id,
        "package_id": "mas-scholar-skills",
        "package_version": text(
            payload.get("package_version"), f"{field}.package_version"
        ),
        "package_source_ref": text(
            payload.get("package_source_ref"), f"{field}.package_source_ref"
        ),
        "package_source_sha256": sha256(
            payload.get("package_source_sha256"), f"{field}.package_source_sha256"
        ),
        "skill_source_ref": text(
            payload.get("skill_source_ref"), f"{field}.skill_source_ref"
        ),
        "skill_source_sha256": sha256(
            payload.get("skill_source_sha256"), f"{field}.skill_source_sha256"
        ),
        "invocation_id": text(payload.get("invocation_id"), f"{field}.invocation_id"),
        "input_contract_ref": text(
            payload.get("input_contract_ref"), f"{field}.input_contract_ref"
        ),
        "input_sha256": sha256(payload.get("input_sha256"), f"{field}.input_sha256"),
        "consumed_rule_refs": rules,
        "output_artifact_bindings": sorted(
            bindings, key=lambda item: item["member_id"]
        ),
        "template_substitution": False,
        "status": "completed",
        "refs_only": True,
        "authority": False,
        "publication_ready": False,
    }
    if has_semantic_binding and (
        schema_version != 2 or skill_id not in SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL
    ):
        raise RequestShapeError(
            f"{field} semantic fields require a Scholar v2 policy-bearing invocation"
        )
    if has_semantic_binding:
        policy = SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL[skill_id]
        if payload.get("semantic_policy_id") != policy["policy_id"]:
            raise RequestShapeError(
                f"{field}.semantic_policy_id must bind the current Scholar v2 policy"
            )
        if payload.get("semantic_validator_id") != policy["validator_id"]:
            raise RequestShapeError(
                f"{field}.semantic_validator_id must bind the current Scholar validator"
            )
        required_rules = {
            policy["policy_id"],
            f"validator:{policy['validator_id']}",
        }
        if not required_rules.issubset(set(rules)):
            raise RequestShapeError(
                f"{field}.consumed_rule_refs must consume the exact semantic policy and validator"
            )
        semantic_candidate_ref = _exact_ref(
            payload.get("semantic_candidate_ref"),
            f"{field}.semantic_candidate_ref",
            "mas_artifact",
        )
        expected_role = FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD[
            policy["candidate_ref_field"]
        ]
        if not any(
            binding["role"] == expected_role
            and all(
                semantic_candidate_ref[key] == binding[key]
                for key in ("ref", "size_bytes", "sha256")
            )
            for binding in bindings
        ):
            raise RequestShapeError(
                f"{field}.semantic_candidate_ref must bind the current output candidate member"
            )
        normalized.update(
            {
                "semantic_policy_id": policy["policy_id"],
                "semantic_validator_id": policy["validator_id"],
                "semantic_policy_ref": _exact_ref(
                    payload.get("semantic_policy_ref"),
                    f"{field}.semantic_policy_ref",
                    "scholarskills_semantic_policy",
                ),
                "semantic_candidate_ref": semantic_candidate_ref,
            }
        )
    if skill_id == "medical-table-design" and payload.get(
        "table_quality_application"
    ) is not None:
        normalized["table_quality_application"] = (
            _normalize_table_quality_application(
                payload["table_quality_application"],
                f"{field}.table_quality_application",
            )
        )
    if schema_version == 2:
        receipt_ref = _exact_ref(
            payload.get("receipt_ref"),
            f"{field}.receipt_ref",
            "scholarskills_professional_skill_receipt",
        )
        if normalized["receipt_id"] != receipt_ref["ref"]:
            raise RequestShapeError(f"{field}.receipt_id must equal receipt_ref.ref")
        input_bindings = _normalize_professional_skill_input_bindings(
            payload.get("input_artifact_bindings"),
            f"{field}.input_artifact_bindings",
            artifact_by_member_id=artifact_by_member_id,
        )
        normalized["receipt_ref"] = receipt_ref
        normalized["input_artifact_bindings"] = input_bindings
        if has_semantic_binding:
            semantic_receipt_core = {
                "skill_id": skill_id,
                "skill_source_sha256": normalized["skill_source_sha256"],
                "input_artifact_bindings": input_bindings,
                "output_artifact_bindings": normalized[
                    "output_artifact_bindings"
                ],
                "consumed_rule_refs": normalized["consumed_rule_refs"],
                "semantic_policy_id": normalized["semantic_policy_id"],
                "semantic_validator_id": normalized["semantic_validator_id"],
                "semantic_policy_ref": normalized["semantic_policy_ref"],
                "semantic_candidate_ref": normalized[
                    "semantic_candidate_ref"
                ],
                "status": "completed",
            }
            receipt_fingerprint = fingerprint(semantic_receipt_core)
            expected_receipt_ref = {
                "kind": "scholarskills_professional_skill_receipt",
                "ref": (
                    "scholarskills-professional-skill-receipt:"
                    f"{receipt_fingerprint.removeprefix('sha256:')}"
                ),
                "size_bytes": len(canonical_json_bytes(semantic_receipt_core)),
                "sha256": receipt_fingerprint,
            }
            if receipt_ref != expected_receipt_ref:
                raise RequestShapeError(
                    f"{field}.receipt_ref does not bind the Scholar v2 semantic receipt bytes"
                )
        normalized["invocation_ref"] = _normalize_professional_invocation_ref(
            payload.get("invocation_ref"),
            f"{field}.invocation_ref",
            invocation_core=normalized,
        )
    return normalized


def _normalize_table_quality_application(
    value: Any,
    field: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "schema_version",
            "policy_ref",
            "template_policy",
            "coverage_status",
            "main_tables",
        },
        field,
    )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 1")
    if payload.get("policy_ref") != (
        "medical-table-design#main-table-information-budget"
    ):
        raise RequestShapeError(f"{field}.policy_ref is invalid")
    if payload.get("template_policy") != "reference_floor_not_required":
        raise RequestShapeError(
            f"{field}.template_policy must be reference_floor_not_required"
        )
    if payload.get("coverage_status") != "all_main_tables_assessed":
        raise RequestShapeError(
            f"{field}.coverage_status must be all_main_tables_assessed"
        )
    main_tables = [
        _normalize_main_table_quality_assessment(
            item,
            f"{field}.main_tables[{index}]",
        )
        for index, item in enumerate(sequence(payload.get("main_tables"), f"{field}.main_tables"))
    ]
    if not main_tables:
        raise RequestShapeError(f"{field}.main_tables must not be empty")
    table_ids = [item["table_id"] for item in main_tables]
    if len(table_ids) != len(set(table_ids)):
        raise RequestShapeError(f"{field}.main_tables contains duplicate table ids")
    return {
        "schema_version": 1,
        "policy_ref": "medical-table-design#main-table-information-budget",
        "template_policy": "reference_floor_not_required",
        "coverage_status": "all_main_tables_assessed",
        "main_tables": sorted(main_tables, key=lambda item: item["table_id"]),
    }


def _normalize_main_table_quality_assessment(
    value: Any,
    field: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "table_id",
            "role",
            "reader_question",
            "row_count",
            "column_count",
            "body_word_count",
            "max_cell_word_count",
            "footnote_word_count",
            "supplementary_detail_refs",
            "budget_status",
            "exception_reason",
            "final_embedding_status",
            "final_embedding_page_span",
            "standalone_notes_heading_present",
        },
        field,
    )
    budget_status = enum_text(
        payload.get("budget_status"),
        f"{field}.budget_status",
        {"within_default_budget", "documented_exception"},
    )
    exception_reason = payload.get("exception_reason")
    if budget_status == "documented_exception":
        exception_reason = text(exception_reason, f"{field}.exception_reason")
    elif exception_reason is not None:
        raise RequestShapeError(
            f"{field}.exception_reason is allowed only for documented_exception"
        )
    if not isinstance(payload.get("standalone_notes_heading_present"), bool):
        raise RequestShapeError(
            f"{field}.standalone_notes_heading_present must be boolean"
        )
    return {
        "table_id": text(payload.get("table_id"), f"{field}.table_id"),
        "role": enum_text(payload.get("role"), f"{field}.role", {"main_text"}),
        "reader_question": text(
            payload.get("reader_question"), f"{field}.reader_question"
        ),
        "row_count": integer(payload.get("row_count"), f"{field}.row_count"),
        "column_count": integer(
            payload.get("column_count"), f"{field}.column_count"
        ),
        "body_word_count": integer(
            payload.get("body_word_count"), f"{field}.body_word_count"
        ),
        "max_cell_word_count": integer(
            payload.get("max_cell_word_count"), f"{field}.max_cell_word_count"
        ),
        "footnote_word_count": integer(
            payload.get("footnote_word_count"), f"{field}.footnote_word_count"
        ),
        "supplementary_detail_refs": text_list(
            payload.get("supplementary_detail_refs"),
            f"{field}.supplementary_detail_refs",
        ),
        "budget_status": budget_status,
        "exception_reason": exception_reason,
        "final_embedding_status": enum_text(
            payload.get("final_embedding_status"),
            f"{field}.final_embedding_status",
            {"pending", "passed"},
        ),
        "final_embedding_page_span": integer(
            payload.get("final_embedding_page_span"),
            f"{field}.final_embedding_page_span",
        ),
        "standalone_notes_heading_present": payload[
            "standalone_notes_heading_present"
        ],
    }


def _normalize_professional_skill_invocation(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    schema_version = integer(payload.get("schema_version"), f"{field}.schema_version")
    if schema_version not in {1, 2}:
        raise RequestShapeError(f"{field}.schema_version must be integer 1 or 2")
    skill_id = enum_text(
        payload.get("skill_id"),
        f"{field}.skill_id",
        {
            "medical-figure-design",
            "medical-figure-style",
            "medical-figure-composer",
        },
    )
    keys = {
        "surface_kind",
        "schema_version",
        "receipt_id",
        "figure_id",
        "figure_kind",
        "composition_mode",
        "skill_id",
        "package_id",
        "package_version",
        "package_source_ref",
        "package_source_sha256",
        "skill_source_ref",
        "skill_source_sha256",
        "invocation_id",
        "input_contract_ref",
        "input_sha256",
        "consumed_rule_refs",
        "output_artifact_bindings",
        "status",
        "refs_only",
        "authority",
        "publication_ready",
    }
    if schema_version == 2:
        keys.update({"invocation_ref", "receipt_ref", "input_artifact_bindings"})
    if skill_id == "medical-figure-design":
        keys.update({"template_usage", "figure_text_policy"})
    exact_keys(payload, keys, field)
    if (
        payload.get("surface_kind")
        != "mas_professional_figure_skill_invocation_candidate"
    ):
        raise RequestShapeError(
            f"{field}.surface_kind must be "
            "mas_professional_figure_skill_invocation_candidate"
        )
    if payload.get("package_id") != "mas-scholar-skills":
        raise RequestShapeError(f"{field}.package_id must be mas-scholar-skills")
    if payload.get("status") != "completed":
        raise RequestShapeError(f"{field}.status must be completed")
    if payload.get("refs_only") is not True:
        raise RequestShapeError(f"{field}.refs_only must be true")
    for key in ("authority", "publication_ready"):
        if payload.get(key) is not False:
            raise RequestShapeError(f"{field}.{key} must be false")
    consumed_rule_refs = text_list(
        payload.get("consumed_rule_refs"), f"{field}.consumed_rule_refs"
    )
    if not consumed_rule_refs:
        raise RequestShapeError(f"{field}.consumed_rule_refs must not be empty")
    output_bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}.output_artifact_bindings[{index}]",
            artifact_by_member_id=artifact_by_member_id,
        )
        for index, item in enumerate(
            sequence(
                payload.get("output_artifact_bindings"),
                f"{field}.output_artifact_bindings",
            )
        )
    ]
    if not output_bindings:
        raise RequestShapeError(
            f"{field}.output_artifact_bindings must bind at least one final figure artifact"
        )
    member_ids = [item["member_id"] for item in output_bindings]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(
            f"{field}.output_artifact_bindings contains duplicate members"
        )
    normalized = {
        "surface_kind": "mas_professional_figure_skill_invocation_candidate",
        "schema_version": schema_version,
        "receipt_id": text(payload.get("receipt_id"), f"{field}.receipt_id"),
        "figure_id": text(payload.get("figure_id"), f"{field}.figure_id"),
        "figure_kind": enum_text(
            payload.get("figure_kind"),
            f"{field}.figure_kind",
            {"evidence_figure", "graphical_abstract"},
        ),
        "composition_mode": enum_text(
            payload.get("composition_mode"),
            f"{field}.composition_mode",
            {"single_canvas_direct", "assembled_panels"},
        ),
        "skill_id": skill_id,
        "package_id": "mas-scholar-skills",
        "package_version": text(
            payload.get("package_version"), f"{field}.package_version"
        ),
        "package_source_ref": text(
            payload.get("package_source_ref"), f"{field}.package_source_ref"
        ),
        "package_source_sha256": sha256(
            payload.get("package_source_sha256"),
            f"{field}.package_source_sha256",
        ),
        "skill_source_ref": text(
            payload.get("skill_source_ref"), f"{field}.skill_source_ref"
        ),
        "skill_source_sha256": sha256(
            payload.get("skill_source_sha256"), f"{field}.skill_source_sha256"
        ),
        "invocation_id": text(payload.get("invocation_id"), f"{field}.invocation_id"),
        "input_contract_ref": text(
            payload.get("input_contract_ref"), f"{field}.input_contract_ref"
        ),
        "input_sha256": sha256(payload.get("input_sha256"), f"{field}.input_sha256"),
        "consumed_rule_refs": consumed_rule_refs,
        "output_artifact_bindings": sorted(
            output_bindings, key=lambda item: item["member_id"]
        ),
        "status": "completed",
        "refs_only": True,
        "authority": False,
        "publication_ready": False,
    }
    if skill_id == "medical-figure-design":
        normalized["template_usage"] = _normalize_figure_template_usage(
            payload.get("template_usage"), f"{field}.template_usage"
        )
        normalized["figure_text_policy"] = _normalize_figure_text_policy(
            payload.get("figure_text_policy"),
            f"{field}.figure_text_policy",
            figure_kind=normalized["figure_kind"],
        )
    if schema_version == 2:
        receipt_ref = _exact_ref(
            payload.get("receipt_ref"),
            f"{field}.receipt_ref",
            "scholarskills_professional_skill_receipt",
        )
        if normalized["receipt_id"] != receipt_ref["ref"]:
            raise RequestShapeError(f"{field}.receipt_id must equal receipt_ref.ref")
        normalized["receipt_ref"] = receipt_ref
        normalized["input_artifact_bindings"] = (
            _normalize_professional_skill_input_bindings(
                payload.get("input_artifact_bindings"),
                f"{field}.input_artifact_bindings",
                artifact_by_member_id=artifact_by_member_id,
            )
        )
        normalized["invocation_ref"] = _normalize_professional_invocation_ref(
            payload.get("invocation_ref"),
            f"{field}.invocation_ref",
            invocation_core=normalized,
        )
    return normalized


def _normalize_professional_skill_artifact_binding(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
    allowed_roles: frozenset[str] = frozenset({"figure_file"}),
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(payload, {"member_id", "role", "ref", "size_bytes", "sha256"}, field)
    member_id = text(payload.get("member_id"), f"{field}.member_id")
    normalized = {
        "member_id": member_id,
        "role": enum_text(payload.get("role"), f"{field}.role", set(allowed_roles)),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    expected = artifact_by_member_id.get(member_id)
    if expected is None or expected.get("role") not in allowed_roles:
        raise RequestShapeError(f"{field} must name an allowed generation artifact")
    return normalized


def _normalize_professional_skill_input_bindings(
    value: Any,
    field: str,
    *,
    artifact_by_member_id: Mapping[str, Mapping[str, Any]],
) -> list[dict[str, Any]]:
    allowed_roles = frozenset(
        item["role"] for item in artifact_by_member_id.values()
    )
    bindings = [
        _normalize_professional_skill_artifact_binding(
            item,
            f"{field}[{index}]",
            artifact_by_member_id=artifact_by_member_id,
            allowed_roles=allowed_roles,
        )
        for index, item in enumerate(sequence(value, field))
    ]
    if not bindings:
        raise RequestShapeError(f"{field} must not be empty")
    member_ids = [item["member_id"] for item in bindings]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(f"{field} contains duplicate members")
    for binding in bindings:
        expected = artifact_by_member_id[binding["member_id"]]
        if any(
            binding[key] != expected[key]
            for key in ("role", "ref", "size_bytes", "sha256")
        ):
            raise RequestShapeError(
                f"{field} does not match the exact generation input artifacts"
            )
    return sorted(bindings, key=lambda item: item["member_id"])


def _normalize_professional_invocation_ref(
    value: Any,
    field: str,
    *,
    invocation_core: Mapping[str, Any],
) -> dict[str, Any]:
    invocation_ref = _exact_ref(
        value,
        field,
        "mas_professional_skill_invocation",
    )
    expected_sha256 = fingerprint(invocation_core)
    expected_size = len(canonical_json_bytes(invocation_core))
    expected_ref = (
        "mas-professional-skill-invocation:"
        f"{expected_sha256.removeprefix('sha256:')}"
    )
    if invocation_ref != {
        "kind": "mas_professional_skill_invocation",
        "ref": expected_ref,
        "size_bytes": expected_size,
        "sha256": expected_sha256,
    }:
        raise RequestShapeError(f"{field} does not match canonical invocation bytes")
    return invocation_ref


def _normalize_figure_template_usage(value: Any, field: str) -> dict[str, Any]:
    payload = mapping(value, field)
    if payload.get("used") is False:
        exact_keys(payload, {"used", "decision_reason"}, field)
        return {
            "used": False,
            "decision_reason": text(
                payload.get("decision_reason"), f"{field}.decision_reason"
            ),
        }
    if payload.get("used") is not True:
        raise RequestShapeError(f"{field}.used must be boolean")
    exact_keys(
        payload,
        {
            "used",
            "template_id",
            "template_ref",
            "adaptation_mode",
            "semantic_match_ref",
            "transform_delta_ref",
        },
        field,
    )
    return {
        "used": True,
        "template_id": text(payload.get("template_id"), f"{field}.template_id"),
        "template_ref": text(payload.get("template_ref"), f"{field}.template_ref"),
        "adaptation_mode": enum_text(
            payload.get("adaptation_mode"),
            f"{field}.adaptation_mode",
            {
                "declared_template",
                "schema_adapted_template",
                "reference_guided_new_render",
            },
        ),
        "semantic_match_ref": text(
            payload.get("semantic_match_ref"), f"{field}.semantic_match_ref"
        ),
        "transform_delta_ref": text(
            payload.get("transform_delta_ref"), f"{field}.transform_delta_ref"
        ),
    }


def _normalize_figure_text_policy(
    value: Any,
    field: str,
    *,
    figure_kind: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "embedded_title",
            "embedded_subtitle",
            "embedded_prose_footer",
            "allowed_text_roles",
        },
        field,
    )
    for key in ("embedded_title", "embedded_subtitle", "embedded_prose_footer"):
        if not isinstance(payload.get(key), bool):
            raise RequestShapeError(f"{field}.{key} must be boolean")
    allowed_text_roles = text_list(
        payload.get("allowed_text_roles"), f"{field}.allowed_text_roles"
    )
    evidence_roles = {
        "panel_label",
        "axis_label",
        "tick_label",
        "legend",
        "necessary_statistical_annotation",
    }
    allowed_roles = evidence_roles | {"graphical_abstract_copy"}
    if not set(allowed_text_roles).issubset(allowed_roles):
        raise RequestShapeError(
            f"{field}.allowed_text_roles contains unsupported roles"
        )
    if figure_kind == "evidence_figure":
        for key in ("embedded_title", "embedded_subtitle", "embedded_prose_footer"):
            if payload.get(key) is not False:
                raise RequestShapeError(
                    f"{field}.{key} must be false for evidence figures"
                )
        if set(allowed_text_roles) != evidence_roles:
            raise RequestShapeError(
                f"{field}.allowed_text_roles must equal the evidence-figure text policy"
            )
    return {
        "embedded_title": payload["embedded_title"],
        "embedded_subtitle": payload["embedded_subtitle"],
        "embedded_prose_footer": payload["embedded_prose_footer"],
        "allowed_text_roles": allowed_text_roles,
    }


def require_stage_scope(stage_id: str, manifest_scope: str) -> None:
    minimum = STAGE_MINIMUM_SCOPE.get(stage_id)
    if minimum is None:
        raise RequestShapeError(f"mission.stage_id is unsupported: {stage_id}")
    if _SCOPE_RANK[manifest_scope] < _SCOPE_RANK[minimum]:
        raise RequestShapeError(
            f"mission.stage_id {stage_id} requires at least {minimum}"
        )


def source_input_digest(manifest: dict[str, Any]) -> dict[str, Any]:
    artifact = next(
        artifact
        for artifact in manifest["artifacts"]
        if artifact["role"] == "source_input_digest"
    )
    # Candidate admission's established exact-ref contract predates v2 member_id.
    return {name: artifact[name] for name in ("role", "ref", "size_bytes", "sha256")}


def review_scope_inventory(
    lane: str,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return the canonical MAS-owned member inventory for one review lane."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    roles = REVIEW_SCOPE_ROLES_BY_LANE[lane]
    members = [item for item in artifacts if item["role"] in roles]
    members = [dict(item) for item in members]
    members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if not members:
        raise RequestShapeError(f"review scope {lane} has no canonical members")
    return members


def build_epistemic_review_scope(
    lane: str,
    members: list[dict[str, Any]],
) -> dict[str, Any]:
    """Build the MAS-owned dependency declaration consumed by OPL currentness."""

    if lane not in EPISTEMIC_SCOPE_KIND_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    _require_unique_member_ids(members, f"epistemic review scope {lane} members")
    role_map = EPISTEMIC_NODE_ROLE_BY_LANE[lane]
    if any(item["role"] not in role_map for item in members):
        raise RequestShapeError(
            f"epistemic review scope {lane} contains undeclared artifact roles"
        )
    nodes = [
        {
            "node_ref": item["member_id"],
            "node_kind": role_map[item["role"]][0],
            "role": role_map[item["role"]][1],
            "locator": {"ref": item["ref"], "sha256": item["sha256"]},
        }
        for item in members
    ]
    nodes.sort(key=lambda item: item["node_ref"])
    members_by_role: dict[str, list[dict[str, Any]]] = {}
    for item in members:
        members_by_role.setdefault(item["role"], []).append(item)
    edges: list[dict[str, str]] = []
    for source_roles, dependent_roles, relation in EPISTEMIC_EDGE_RULES_BY_LANE[lane]:
        sources = [
            item
            for role in sorted(source_roles)
            for item in members_by_role.get(role, [])
        ]
        dependents = [
            item
            for role in sorted(dependent_roles)
            for item in members_by_role.get(role, [])
        ]
        edges.extend(
            {
                "source_ref": source["member_id"],
                "dependent_ref": dependent["member_id"],
                "relation": relation,
            }
            for source in sources
            for dependent in dependents
            if source["member_id"] != dependent["member_id"]
        )
    edges.sort(
        key=lambda item: (
            item["source_ref"],
            item["dependent_ref"],
            item["relation"],
        )
    )
    reviewed_roles = EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE[lane]
    reviewed_node_refs = sorted(
        item["member_id"] for item in members if item["role"] in reviewed_roles
    )
    if not reviewed_node_refs:
        raise RequestShapeError(
            f"epistemic review scope {lane} has no reviewed domain nodes"
        )
    return {
        "surface_kind": "opl_epistemic_review_scope",
        "version": EPISTEMIC_REVIEW_SCOPE_VERSION,
        "scope_id": f"mas:{lane}",
        "scope_kind": EPISTEMIC_SCOPE_KIND_BY_LANE[lane],
        "evidence_profile": EPISTEMIC_EVIDENCE_PROFILE,
        "trust_model": EPISTEMIC_TRUST_MODEL,
        "reviewed_node_refs": reviewed_node_refs,
        "nodes": nodes,
        "dependency_edges": edges,
        "authority_boundary": dict(EPISTEMIC_AUTHORITY_BOUNDARY),
    }


def epistemic_review_scope_identity(scope: Mapping[str, Any]) -> dict[str, Any]:
    """Project scope topology without promoting locator hashes to content truth."""

    return {
        "surface_kind": scope["surface_kind"],
        "version": scope["version"],
        "scope_id": scope["scope_id"],
        "scope_kind": scope["scope_kind"],
        "evidence_profile": scope["evidence_profile"],
        "trust_model": scope["trust_model"],
        "reviewed_node_refs": list(scope["reviewed_node_refs"]),
        "nodes": [
            {
                "node_ref": item["node_ref"],
                "node_kind": item["node_kind"],
                "role": item["role"],
            }
            for item in scope["nodes"]
        ],
        "dependency_edges": [dict(item) for item in scope["dependency_edges"]],
        "authority_boundary": dict(scope["authority_boundary"]),
    }


def epistemic_review_dependency_refs(scope: Mapping[str, Any]) -> list[str]:
    """Return the declared dependency closure for Framework-evaluation binding."""

    sources_by_dependent: dict[str, list[str]] = {}
    for edge in scope["dependency_edges"]:
        sources_by_dependent.setdefault(edge["dependent_ref"], []).append(
            edge["source_ref"]
        )
    closure = set(scope["reviewed_node_refs"])
    pending = list(scope["reviewed_node_refs"])
    while pending:
        dependent = pending.pop()
        for source in sources_by_dependent.get(dependent, []):
            if source not in closure:
                closure.add(source)
                pending.append(source)
    return sorted(closure)


def review_scope_sha256(lane: str, members: list[dict[str, Any]]) -> str:
    """Hash dependency topology as a locator; artifact bytes are not authority."""

    if lane not in REVIEW_AUTHORITY_ROLE_BY_LANE:
        raise RequestShapeError(f"unsupported review lane: {lane}")
    scope = build_epistemic_review_scope(lane, members)
    return fingerprint(epistemic_review_scope_identity(scope))


def review_scope_member_projection(
    members: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Project MAS review members onto the domain currentness identity."""

    projected = [
        {
            "member_id": item["member_id"],
            "role": item["role"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in members
    ]
    projected.sort(
        key=lambda item: (
            item["role"],
            item["member_id"],
            item["sha256"],
            item["size_bytes"],
        )
    )
    return projected


def _normalize_review_input_snapshot_authority_issuer(
    value: Any,
    field: str = "authority_issuer",
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {
        "agent_id",
        "domain_id",
        "package_id",
        "stage_attempt_ref",
        "execution_content_binding_sha256",
        "package_use_boundary_id",
        "root_package_content_digest",
    }
    exact_keys(payload, keys, field)
    if payload.get("agent_id") != "mas":
        raise RequestShapeError(f"{field}.agent_id must be mas")
    if payload.get("domain_id") != "medautoscience":
        raise RequestShapeError(f"{field}.domain_id must be medautoscience")
    if payload.get("package_id") != "mas":
        raise RequestShapeError(f"{field}.package_id must be mas")
    stage_attempt_ref = text(
        payload.get("stage_attempt_ref"),
        f"{field}.stage_attempt_ref",
    )
    if not stage_attempt_ref.startswith("opl://stage_attempts/"):
        raise RequestShapeError(
            f"{field}.stage_attempt_ref must reference one OPL Stage Attempt"
        )
    return {
        "agent_id": "mas",
        "domain_id": "medautoscience",
        "package_id": "mas",
        "stage_attempt_ref": stage_attempt_ref,
        "execution_content_binding_sha256": sha256(
            payload.get("execution_content_binding_sha256"),
            f"{field}.execution_content_binding_sha256",
        ),
        "package_use_boundary_id": text(
            payload.get("package_use_boundary_id"),
            f"{field}.package_use_boundary_id",
        ),
        "root_package_content_digest": sha256(
            payload.get("root_package_content_digest"),
            f"{field}.root_package_content_digest",
        ),
    }


def _review_input_snapshot_authority_record(
    *,
    generation_ref: str,
    review_lane: str,
    review_scope_sha256_value: str,
    members: list[dict[str, Any]],
    authority_issuer: Mapping[str, Any],
) -> dict[str, Any]:
    member_projection = [
        {
            "member_id": item["member_id"],
            "role": item["role"],
            "owner_ref": item["owner_ref"],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in members
    ]
    return {
        "surface_kind": "mas_review_input_snapshot_authority",
        "schema_version": 2,
        "issuer": _normalize_review_input_snapshot_authority_issuer(
            authority_issuer
        ),
        "generation_ref": generation_ref,
        "review_lane": review_lane,
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_scope_sha256": review_scope_sha256_value,
        "members": member_projection,
    }


def _review_input_snapshot_authority_record_ref(
    authority_record: dict[str, Any],
) -> dict[str, Any]:
    authority_sha256 = fingerprint(authority_record)
    return {
        "kind": "mas_review_input_snapshot_authority",
        "ref": (
            "mas-review-input-snapshot-authority:"
            f"{authority_sha256.removeprefix('sha256:')}"
        ),
        "size_bytes": len(canonical_json_bytes(authority_record)),
        "sha256": authority_sha256,
    }


def build_review_input_snapshot_materialization_request(
    *,
    generation_manifest: dict[str, Any],
    review_lane: str,
    generation_ref: str,
    workspace_root: str,
    source_refs_by_member_id: Mapping[str, str],
    authority_issuer: Mapping[str, Any],
) -> dict[str, Any]:
    """Project one MAS-owned review scope into the generic OPL transport request."""

    manifest = normalize_generation_manifest(generation_manifest)
    if manifest["schema_version"] != 2:
        raise RequestShapeError(
            "generation_manifest.schema_version must be integer 2 for snapshot materialization"
        )
    lane = enum_text(
        review_lane,
        "review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    scope = next(
        (item for item in manifest["review_scopes"] if item["review_lane"] == lane),
        None,
    )
    if scope is None:
        raise RequestShapeError(
            f"review_lane {lane} is not declared by generation_manifest.review_scopes"
        )

    supplied_source_refs = mapping(
        source_refs_by_member_id,
        "source_refs_by_member_id",
    )
    normalized_source_refs: dict[str, str] = {}
    for index, (member_id_value, source_ref_value) in enumerate(
        supplied_source_refs.items()
    ):
        member_id = text(
            member_id_value,
            f"source_refs_by_member_id key[{index}]",
        )
        if member_id in normalized_source_refs:
            raise RequestShapeError(
                "source_refs_by_member_id contains duplicate normalized member_id values"
            )
        normalized_source_refs[member_id] = text(
            source_ref_value,
            f"source_refs_by_member_id.{member_id}",
        )

    reviewed_members = review_scope_member_projection(scope["reviewed_members"])
    expected_member_ids = {item["member_id"] for item in reviewed_members}
    supplied_member_ids = set(normalized_source_refs)
    missing_member_ids = sorted(expected_member_ids - supplied_member_ids)
    extra_member_ids = sorted(supplied_member_ids - expected_member_ids)
    if missing_member_ids or extra_member_ids:
        mismatch_parts = []
        if missing_member_ids:
            mismatch_parts.append("missing: " + ", ".join(missing_member_ids))
        if extra_member_ids:
            mismatch_parts.append("extra: " + ", ".join(extra_member_ids))
        raise RequestShapeError(
            "source_refs_by_member_id must exactly match the MAS-owned review scope; "
            + "; ".join(mismatch_parts)
        )

    members = [
        {
            "member_id": item["member_id"],
            "source_ref": normalized_source_refs[item["member_id"]],
            "sha256": item["sha256"],
            "size_bytes": item["size_bytes"],
        }
        for item in reviewed_members
    ]
    normalized_generation_ref = text(generation_ref, "generation_ref")
    normalized_authority_issuer = _normalize_review_input_snapshot_authority_issuer(
        authority_issuer
    )
    authority_record = _review_input_snapshot_authority_record(
        generation_ref=normalized_generation_ref,
        review_lane=lane,
        review_scope_sha256_value=scope["review_scope_sha256"],
        members=[
            {
                "member_id": item["member_id"],
                "role": item["role"],
                "owner_ref": item["ref"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
            }
            for item in scope["reviewed_members"]
        ],
        authority_issuer=normalized_authority_issuer,
    )
    return {
        "surface_kind": "opl_reviewer_input_snapshot_materialization_request",
        "schema_version": 2,
        "owner_authority_ref": _review_input_snapshot_authority_record_ref(
            authority_record
        ),
        "producer_attempt_ref": normalized_authority_issuer["stage_attempt_ref"],
        "execution_content_binding_sha256": normalized_authority_issuer[
            "execution_content_binding_sha256"
        ],
        "workspace_root": text(workspace_root, "workspace_root"),
        "members": members,
    }


def build_stage_review_input_snapshot_bundle(
    *,
    stage_id: str,
    artifacts: list[dict[str, Any]],
    generation_id: str,
    generation_ref: str,
    workspace_root: str,
    source_refs_by_member_id: Mapping[str, str],
    authority_issuer: Mapping[str, Any],
    review_lane: str | None = None,
    professional_skill_invocations: list[dict[str, Any]] | None = None,
    first_draft_quality_application: dict[str, Any] | None = None,
    clinical_analysis_identity_admission: dict[str, Any] | None = None,
    selected_build_binding: dict[str, Any] | None = None,
    reviewer_response_sync: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build one stage-bound generation manifest and immutable review request."""

    normalized_stage_id = text(stage_id, "stage_id")
    manifest_scope = STAGE_MINIMUM_SCOPE.get(normalized_stage_id)
    if manifest_scope is None:
        raise RequestShapeError(f"stage_id is unsupported: {normalized_stage_id}")

    allowed_lanes = REVIEW_LANES_BY_SCOPE[manifest_scope]
    fixed_lane = STAGE_FIXED_REVIEW_LANE.get(normalized_stage_id)
    if fixed_lane is not None:
        if review_lane is not None:
            supplied_lane = enum_text(
                review_lane,
                "review_lane",
                set(REVIEW_AUTHORITY_ROLE_BY_LANE),
            )
            if supplied_lane != fixed_lane:
                raise RequestShapeError(
                    f"stage_id {normalized_stage_id} binds review_lane {fixed_lane}"
                )
        lane = fixed_lane
    else:
        if review_lane is None:
            raise RequestShapeError(
                f"stage_id {normalized_stage_id} requires an explicit controller-bound review_lane"
            )
        lane = enum_text(
            review_lane,
            "review_lane",
            set(REVIEW_AUTHORITY_ROLE_BY_LANE),
        )
    if lane not in allowed_lanes:
        raise RequestShapeError(
            f"review_lane {lane} is not allowed for stage_id {normalized_stage_id}"
        )

    generation_manifest = build_generation_manifest_v2(
        artifacts=artifacts,
        generation_id=generation_id,
        manifest_scope=manifest_scope,
        professional_skill_invocations=professional_skill_invocations,
        first_draft_quality_application=first_draft_quality_application,
        clinical_analysis_identity_admission=clinical_analysis_identity_admission,
        selected_build_binding=selected_build_binding,
        reviewer_response_sync=reviewer_response_sync,
    )
    request = build_review_input_snapshot_materialization_request(
        generation_manifest=generation_manifest,
        review_lane=lane,
        generation_ref=generation_ref,
        workspace_root=workspace_root,
        source_refs_by_member_id=source_refs_by_member_id,
        authority_issuer=authority_issuer,
    )
    return {
        "surface_kind": "mas_stage_review_input_snapshot_bundle",
        "schema_version": 1,
        "stage_id": normalized_stage_id,
        "manifest_scope": manifest_scope,
        "review_lane": lane,
        "generation_ref": text(generation_ref, "generation_ref"),
        "generation_manifest": generation_manifest,
        "review_input_snapshot_materialization_request": request,
        "required_closeout_ref_metadata": [dict(request["owner_authority_ref"])],
    }


def build_review_scopes(
    artifacts: list[dict[str, Any]],
    manifest_scope: str,
) -> list[dict[str, Any]]:
    """Build every required deterministic lane scope for one manifest scope."""

    if manifest_scope not in REVIEW_LANES_BY_SCOPE:
        raise RequestShapeError(f"unsupported manifest scope: {manifest_scope}")
    _require_unique_member_ids(artifacts, "artifacts")
    scopes = []
    for lane in sorted(REVIEW_LANES_BY_SCOPE[manifest_scope]):
        members = review_scope_inventory(lane, artifacts)
        scopes.append(
            {
                "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
                "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
                "review_lane": lane,
                "review_scope_sha256": review_scope_sha256(lane, members),
                "reviewed_members": members,
                "epistemic_scope": build_epistemic_review_scope(lane, members),
            }
        )
    return scopes


def _normalize_review_scope(
    value: Any,
    field: str,
    *,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "scope_policy_id",
            "scope_policy_version",
            "review_lane",
            "review_scope_sha256",
            "reviewed_members",
            "epistemic_scope",
        },
        field,
    )
    if payload.get("scope_policy_id") != REVIEW_SCOPE_POLICY_ID:
        raise RequestShapeError(
            f"{field}.scope_policy_id must be {REVIEW_SCOPE_POLICY_ID}"
        )
    if payload.get("scope_policy_version") != REVIEW_SCOPE_POLICY_VERSION or isinstance(
        payload.get("scope_policy_version"), bool
    ):
        raise RequestShapeError(
            f"{field}.scope_policy_version must be integer {REVIEW_SCOPE_POLICY_VERSION}"
        )
    lane = enum_text(
        payload.get("review_lane"),
        f"{field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    expected_members = review_scope_inventory(lane, artifacts)
    supplied_members = [
        _normalize_artifact(
            item,
            f"{field}.reviewed_members[{index}]",
            allowed_roles=frozenset(artifact["role"] for artifact in artifacts),
            schema_version=2,
        )
        for index, item in enumerate(
            sequence(payload.get("reviewed_members"), f"{field}.reviewed_members")
        )
    ]
    _require_unique_member_ids(supplied_members, f"{field}.reviewed_members")
    supplied_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if supplied_members != expected_members:
        raise RequestShapeError(
            f"{field}.reviewed_members must equal the MAS-owned lane inventory"
        )
    expected_sha256 = review_scope_sha256(lane, expected_members)
    if (
        sha256(payload.get("review_scope_sha256"), f"{field}.review_scope_sha256")
        != expected_sha256
    ):
        raise RequestShapeError(
            f"{field}.review_scope_sha256 does not match the dependency declaration"
        )
    expected_epistemic_scope = build_epistemic_review_scope(lane, expected_members)
    if payload.get("epistemic_scope") != expected_epistemic_scope:
        raise RequestShapeError(
            f"{field}.epistemic_scope must equal the MAS-owned dependency declaration"
        )
    return {
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_lane": lane,
        "review_scope_sha256": expected_sha256,
        "reviewed_members": expected_members,
        "epistemic_scope": expected_epistemic_scope,
    }


def _normalize_artifact(
    value: Any,
    field: str,
    *,
    allowed_roles: frozenset[str],
    schema_version: int = 1,
) -> dict[str, Any]:
    payload = mapping(value, field)
    keys = {"role", "ref", "size_bytes", "sha256"}
    if schema_version == 2:
        keys.add("member_id")
    exact_keys(payload, keys, field)
    normalized = {
        "role": enum_text(payload.get("role"), f"{field}.role", set(allowed_roles)),
        "ref": text(payload.get("ref"), f"{field}.ref"),
        "size_bytes": integer(payload.get("size_bytes"), f"{field}.size_bytes"),
        "sha256": sha256(payload.get("sha256"), f"{field}.sha256"),
    }
    if schema_version == 2:
        normalized["member_id"] = text(payload.get("member_id"), f"{field}.member_id")
    return normalized


def _require_unique_member_ids(
    members: list[dict[str, Any]],
    field: str,
) -> None:
    member_ids = [
        text(item.get("member_id"), f"{field}[{index}].member_id")
        for index, item in enumerate(members)
    ]
    if len(member_ids) != len(set(member_ids)):
        raise RequestShapeError(f"{field} contains duplicate member_id values")


def _normalize_review_receipt(
    value: Any,
    field: str,
    *,
    generation_id: str,
    manifest_sha256: str,
    artifacts: list[dict[str, Any]],
    manifest_version: int,
    review_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = mapping(value, field)
    receipt = mapping(wrapper.get("receipt"), f"{field}.receipt")
    receipt_version = integer(
        receipt.get("schema_version"), f"{field}.receipt.schema_version"
    )
    if receipt_version != manifest_version:
        raise RequestShapeError(
            f"{field}.receipt.schema_version must match generation manifest"
        )
    if receipt_version == 1:
        return _normalize_review_receipt_v1(
            value,
            field,
            generation_id=generation_id,
            manifest_sha256=manifest_sha256,
            artifacts=artifacts,
        )
    if receipt_version == 2:
        return _normalize_review_receipt_v2(
            value,
            field,
            review_scopes=review_scopes,
        )
    raise RequestShapeError(f"{field}.receipt.schema_version must be integer 1 or 2")


def _normalize_review_receipt_v1(
    value: Any,
    field: str,
    *,
    generation_id: str,
    manifest_sha256: str,
    artifacts: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = mapping(value, field)
    exact_keys(wrapper, {"receipt_ref", "receipt"}, field)
    receipt_ref = _exact_ref(
        wrapper.get("receipt_ref"),
        f"{field}.receipt_ref",
        "mas_reviewer_receipt",
    )
    receipt_field = f"{field}.receipt"
    payload = mapping(wrapper.get("receipt"), receipt_field)
    exact_keys(
        payload,
        {
            "receipt_kind",
            "schema_version",
            "issuer",
            "authority_role",
            "authority_epoch",
            "review_lane",
            "verdict",
            "review_request_ref",
            "producer_output_ref",
            "reviewer_attempt_ref",
            "rubric_ref",
            "generation_id",
            "generation_manifest_sha256",
            "reviewed_members",
            "accepted_candidate_receipt_refs",
            "defect_refs",
            "quality_debt_codes",
        },
        receipt_field,
    )
    if payload.get("receipt_kind") != "mas_independent_review_receipt":
        raise RequestShapeError(
            f"{receipt_field}.receipt_kind must be mas_independent_review_receipt"
        )
    if payload.get("schema_version") != 1 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{receipt_field}.schema_version must be integer 1")
    if payload.get("issuer") != "MedAutoScience":
        raise RequestShapeError(f"{receipt_field}.issuer must be MedAutoScience")
    lane = enum_text(
        payload.get("review_lane"),
        f"{receipt_field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    expected_role = REVIEW_AUTHORITY_ROLE_BY_LANE[lane]
    if payload.get("authority_role") != expected_role:
        raise RequestShapeError(
            f"{receipt_field}.authority_role must be {expected_role}"
        )
    receipt_generation = text(
        payload.get("generation_id"), f"{receipt_field}.generation_id"
    )
    if receipt_generation != generation_id:
        raise RequestShapeError(
            f"{receipt_field}.generation_id does not match generation_manifest"
        )
    receipt_manifest = sha256(
        payload.get("generation_manifest_sha256"),
        f"{receipt_field}.generation_manifest_sha256",
    )
    if receipt_manifest != manifest_sha256:
        raise RequestShapeError(f"{receipt_field}.generation_manifest_sha256 is stale")
    reviewed_members = [
        _normalize_artifact(
            item,
            f"{receipt_field}.reviewed_members[{index}]",
            allowed_roles=frozenset(item["role"] for item in artifacts),
        )
        for index, item in enumerate(
            sequence(
                payload.get("reviewed_members"),
                f"{receipt_field}.reviewed_members",
            )
        )
    ]
    reviewed_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    if reviewed_members != artifacts:
        raise RequestShapeError(
            f"{receipt_field}.reviewed_members must equal the canonical manifest inventory"
        )

    candidate_receipt_refs = _exact_ref_list(
        payload.get("accepted_candidate_receipt_refs"),
        f"{receipt_field}.accepted_candidate_receipt_refs",
        "mas_candidate_admission_receipt",
    )
    manifest_candidate_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in artifacts
        if item["role"] == "candidate_admission_receipt"
    }
    supplied_candidate_receipts = {
        (item["ref"], item["size_bytes"], item["sha256"])
        for item in candidate_receipt_refs
    }
    if supplied_candidate_receipts != manifest_candidate_receipts:
        raise RequestShapeError(
            f"{receipt_field}.accepted_candidate_receipt_refs must equal the manifest receipt inventory"
        )

    core = {
        "receipt_kind": "mas_independent_review_receipt",
        "schema_version": 1,
        "issuer": "MedAutoScience",
        "authority_role": expected_role,
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{receipt_field}.authority_epoch"
        ),
        "review_lane": lane,
        "verdict": enum_text(
            payload.get("verdict"),
            f"{receipt_field}.verdict",
            {"passed", "revision_required", "rejected"},
        ),
        "review_request_ref": _exact_ref(
            payload.get("review_request_ref"),
            f"{receipt_field}.review_request_ref",
            "opl_action_output",
        ),
        "producer_output_ref": _exact_ref(
            payload.get("producer_output_ref"),
            f"{receipt_field}.producer_output_ref",
            "opl_action_output",
        ),
        "reviewer_attempt_ref": _typed_ref(
            payload.get("reviewer_attempt_ref"),
            f"{receipt_field}.reviewer_attempt_ref",
            "opl_stage_attempt",
        ),
        "rubric_ref": _typed_ref(
            payload.get("rubric_ref"),
            f"{receipt_field}.rubric_ref",
            "mas_quality_rubric",
        ),
        "generation_id": generation_id,
        "generation_manifest_sha256": manifest_sha256,
        "reviewed_members": reviewed_members,
        "accepted_candidate_receipt_refs": candidate_receipt_refs,
        "defect_refs": _typed_ref_list(
            payload.get("defect_refs"),
            f"{receipt_field}.defect_refs",
            "mas_review_defect",
        ),
        "quality_debt_codes": text_list(
            payload.get("quality_debt_codes"),
            f"{receipt_field}.quality_debt_codes",
        ),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_ref = (
        "mas-independent-review-receipt:"
        f"{lane}:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if (
        receipt_ref["ref"] != expected_ref
        or receipt_ref["sha256"] != expected_fingerprint
        or receipt_ref["size_bytes"] != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_ref identity/size/hash does not match canonical receipt bytes"
        )
    return {"receipt_ref": receipt_ref, "receipt": core}


def _normalize_review_receipt_v2(
    value: Any,
    field: str,
    *,
    review_scopes: list[dict[str, Any]],
) -> dict[str, Any]:
    wrapper = mapping(value, field)
    exact_keys(wrapper, {"receipt_ref", "receipt"}, field)
    receipt_ref = _exact_ref(
        wrapper.get("receipt_ref"),
        f"{field}.receipt_ref",
        "mas_reviewer_receipt",
    )
    receipt_field = f"{field}.receipt"
    payload = mapping(wrapper.get("receipt"), receipt_field)
    receipt_keys = {
        "receipt_kind",
        "schema_version",
        "issuer",
        "authority_role",
        "authority_epoch",
        "review_lane",
        "verdict",
        "review_request_ref",
        "producer_output_ref",
        "reviewer_attempt_ref",
        "rubric_ref",
        "issued_generation_id",
        "issued_generation_manifest_sha256",
        "scope_policy_id",
        "scope_policy_version",
        "review_scope_sha256",
        "reviewed_members",
        "review_input_snapshot_binding",
        "accepted_candidate_receipt_refs",
        "defect_refs",
        "quality_debt_codes",
    }
    exact_keys(payload, receipt_keys, receipt_field)
    if payload.get("receipt_kind") != "mas_independent_review_receipt":
        raise RequestShapeError(
            f"{receipt_field}.receipt_kind must be mas_independent_review_receipt"
        )
    if payload.get("schema_version") != 2 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{receipt_field}.schema_version must be integer 2")
    if payload.get("issuer") != "MedAutoScience":
        raise RequestShapeError(f"{receipt_field}.issuer must be MedAutoScience")
    if payload.get("scope_policy_id") != REVIEW_SCOPE_POLICY_ID:
        raise RequestShapeError(
            f"{receipt_field}.scope_policy_id must be {REVIEW_SCOPE_POLICY_ID}"
        )
    if payload.get("scope_policy_version") != REVIEW_SCOPE_POLICY_VERSION or isinstance(
        payload.get("scope_policy_version"), bool
    ):
        raise RequestShapeError(
            f"{receipt_field}.scope_policy_version must be integer {REVIEW_SCOPE_POLICY_VERSION}"
        )
    lane = enum_text(
        payload.get("review_lane"),
        f"{receipt_field}.review_lane",
        set(REVIEW_AUTHORITY_ROLE_BY_LANE),
    )
    expected_role = REVIEW_AUTHORITY_ROLE_BY_LANE[lane]
    if payload.get("authority_role") != expected_role:
        raise RequestShapeError(
            f"{receipt_field}.authority_role must be {expected_role}"
        )
    scope = next(
        (item for item in review_scopes if item["review_lane"] == lane),
        None,
    )
    if scope is None:
        raise RequestShapeError(
            f"{receipt_field}.review_lane has no manifest review scope"
        )
    allowed_receipt_roles = REVIEW_SCOPE_ROLES_BY_LANE[lane]
    reviewed_members = [
        _normalize_artifact(
            item,
            f"{receipt_field}.reviewed_members[{index}]",
            allowed_roles=allowed_receipt_roles,
            schema_version=2,
        )
        for index, item in enumerate(
            sequence(
                payload.get("reviewed_members"),
                f"{receipt_field}.reviewed_members",
            )
        )
    ]
    _require_unique_member_ids(reviewed_members, f"{receipt_field}.reviewed_members")
    reviewed_members.sort(key=lambda item: (item["role"], item["ref"], item["sha256"]))
    expected_scope_sha256 = review_scope_sha256(lane, reviewed_members)
    supplied_scope_sha256 = sha256(
        payload.get("review_scope_sha256"),
        f"{receipt_field}.review_scope_sha256",
    )
    if supplied_scope_sha256 != expected_scope_sha256:
        raise RequestShapeError(
            f"{receipt_field}.review_scope_sha256 does not match reviewed members"
        )
    candidate_receipt_refs = _exact_ref_list(
        payload.get("accepted_candidate_receipt_refs"),
        f"{receipt_field}.accepted_candidate_receipt_refs",
        "mas_candidate_admission_receipt",
    )
    snapshot_binding = _normalize_review_input_snapshot_binding(
        payload.get("review_input_snapshot_binding"),
        f"{receipt_field}.review_input_snapshot_binding",
    )
    core = {
        "receipt_kind": "mas_independent_review_receipt",
        "schema_version": 2,
        "issuer": "MedAutoScience",
        "authority_role": expected_role,
        "authority_epoch": text(
            payload.get("authority_epoch"), f"{receipt_field}.authority_epoch"
        ),
        "review_lane": lane,
        "verdict": enum_text(
            payload.get("verdict"),
            f"{receipt_field}.verdict",
            {"passed", "revision_required", "rejected"},
        ),
        "review_request_ref": _exact_ref(
            payload.get("review_request_ref"),
            f"{receipt_field}.review_request_ref",
            "opl_action_output",
        ),
        "producer_output_ref": _exact_ref(
            payload.get("producer_output_ref"),
            f"{receipt_field}.producer_output_ref",
            "opl_action_output",
        ),
        "reviewer_attempt_ref": _typed_ref(
            payload.get("reviewer_attempt_ref"),
            f"{receipt_field}.reviewer_attempt_ref",
            "opl_stage_attempt",
        ),
        "rubric_ref": _typed_ref(
            payload.get("rubric_ref"),
            f"{receipt_field}.rubric_ref",
            "mas_quality_rubric",
        ),
        "issued_generation_id": text(
            payload.get("issued_generation_id"),
            f"{receipt_field}.issued_generation_id",
        ),
        "issued_generation_manifest_sha256": sha256(
            payload.get("issued_generation_manifest_sha256"),
            f"{receipt_field}.issued_generation_manifest_sha256",
        ),
        "scope_policy_id": REVIEW_SCOPE_POLICY_ID,
        "scope_policy_version": REVIEW_SCOPE_POLICY_VERSION,
        "review_scope_sha256": supplied_scope_sha256,
        "reviewed_members": reviewed_members,
        "review_input_snapshot_binding": snapshot_binding,
        "accepted_candidate_receipt_refs": candidate_receipt_refs,
        "defect_refs": _typed_ref_list(
            payload.get("defect_refs"),
            f"{receipt_field}.defect_refs",
            "mas_review_defect",
        ),
        "quality_debt_codes": text_list(
            payload.get("quality_debt_codes"),
            f"{receipt_field}.quality_debt_codes",
        ),
    }
    expected_fingerprint = fingerprint(core)
    expected_size = len(canonical_json_bytes(core))
    expected_ref = (
        "mas-independent-review-receipt:"
        f"{lane}:{expected_fingerprint.removeprefix('sha256:')}"
    )
    if (
        receipt_ref["ref"] != expected_ref
        or receipt_ref["sha256"] != expected_fingerprint
        or receipt_ref["size_bytes"] != expected_size
    ):
        raise RequestShapeError(
            f"{field}.receipt_ref identity/size/hash does not match canonical receipt bytes"
        )
    return {"receipt_ref": receipt_ref, "receipt": core}


def _normalize_review_input_snapshot_binding(
    value: Any,
    field: str,
) -> dict[str, Any]:
    payload = mapping(value, field)
    exact_keys(
        payload,
        {
            "surface_kind",
            "schema_version",
            "snapshot_manifest_ref",
            "owner_authority_ref",
            "producer_attempt_ref",
            "execution_content_binding_sha256",
        },
        field,
    )
    if payload.get("surface_kind") != "opl_reviewer_input_snapshot_binding":
        raise RequestShapeError(
            f"{field}.surface_kind must be opl_reviewer_input_snapshot_binding"
        )
    if payload.get("schema_version") != 3 or isinstance(
        payload.get("schema_version"), bool
    ):
        raise RequestShapeError(f"{field}.schema_version must be integer 3")
    producer_attempt_ref = text(
        payload.get("producer_attempt_ref"), f"{field}.producer_attempt_ref"
    )
    if not producer_attempt_ref.startswith("opl://stage_attempts/"):
        raise RequestShapeError(
            f"{field}.producer_attempt_ref must reference one OPL Stage Attempt"
        )
    owner_authority_ref = _exact_ref(
        payload.get("owner_authority_ref"),
        f"{field}.owner_authority_ref",
        "mas_review_input_snapshot_authority",
    )
    expected_authority_ref = (
        "mas-review-input-snapshot-authority:"
        f"{owner_authority_ref['sha256'].removeprefix('sha256:')}"
    )
    if (
        owner_authority_ref["ref"] != expected_authority_ref
        or owner_authority_ref["size_bytes"] < 1
    ):
        raise RequestShapeError(
            f"{field}.owner_authority_ref must bind canonical MAS authority bytes"
        )
    normalized = {
        "surface_kind": "opl_reviewer_input_snapshot_binding",
        "schema_version": 3,
        "snapshot_manifest_ref": _exact_ref(
            payload.get("snapshot_manifest_ref"),
            f"{field}.snapshot_manifest_ref",
            "opl_reviewer_input_snapshot_manifest",
        ),
        "owner_authority_ref": owner_authority_ref,
        "producer_attempt_ref": producer_attempt_ref,
        "execution_content_binding_sha256": sha256(
            payload.get("execution_content_binding_sha256"),
            f"{field}.execution_content_binding_sha256",
        ),
    }
    return normalized


__all__ = [
    "ALLOWED_ROLES_BY_SCOPE",
    "EPISTEMIC_AUTHORITY_BOUNDARY",
    "REQUIRED_ROLES_BY_SCOPE",
    "REVIEW_AUTHORITY_ROLE_BY_LANE",
    "REVIEW_LANE_ORDER",
    "REVIEW_LANES_BY_SCOPE",
    "REVIEW_SCOPE_ROLES_BY_LANE",
    "REVIEW_SCOPE_POLICY_ID",
    "REVIEW_SCOPE_POLICY_VERSION",
    "STAGE_FIXED_REVIEW_LANE",
    "STAGE_MINIMUM_SCOPE",
    "build_epistemic_review_scope",
    "build_generation_manifest_v2",
    "build_review_input_snapshot_materialization_request",
    "build_stage_review_input_snapshot_bundle",
    "build_review_scopes",
    "epistemic_review_dependency_refs",
    "normalize_generation_manifest",
    "require_stage_scope",
    "review_scope_inventory",
    "review_scope_member_projection",
    "review_scope_sha256",
    "source_input_digest",
]
