"""Evaluate exact MAS paper-mission records without transport or I/O."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .._generation_manifest import (
    EPISTEMIC_AUTHORITY_BOUNDARY,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    REVIEW_LANE_ORDER,
    REVIEW_LANES_BY_SCOPE,
    epistemic_review_dependency_refs,
    first_draft_applicable_ref_fields,
    normalize_generation_manifest,
    require_stage_scope,
    review_scope_member_projection,
    source_input_digest,
)
from .._record_validation import (
    RequestShapeError,
    canonical_json_bytes,
    dedupe,
    enum_text,
    exact_ref as _exact_ref,
    exact_ref_list as _exact_ref_list,
    exact_keys,
    fingerprint,
    integer,
    mapping,
    optional_sha256,
    optional_text,
    optional_typed_ref as _optional_typed_ref,
    sequence,
    sha256,
    text,
    text_list,
    typed_ref as _typed_ref,
    typed_ref_list as _typed_ref_list,
)
from ..candidate_admission import normalize_candidate_admission_receipt


REQUEST_KIND = "mas_paper_mission_authority_request"
RESULT_KIND = "mas_paper_mission_authority_result"
SCHEMA_VERSION = 2

_HARD_GATE_KINDS = frozenset(
    {
        "medical_safety",
        "source_identity",
        "source_currentness",
        "domain_authority",
        "credential",
        "irreversible_action",
    }
)
_AUTHORITY_BOUNDARY = {
    "owner": "MedAutoScience",
    "handler_role": "validate_exact_candidate_and_review_receipts_and_return_owner_result",
    "opl_role": "verify_exact_ref_bytes_inject_typed_records_and_persist_exact_result_bytes",
    "program_originates_medical_quality_verdict": False,
    "host_completion_counts_as_domain_completion": False,
    "selects_next_stage": False,
    "owns_profile_or_path_discovery": False,
    "owns_workspace_or_source_discovery": False,
    "owns_queue_session_dag_or_attempt_lifecycle": False,
    "owns_runtime_ledger": False,
    "performs_filesystem_io": False,
    "performs_network_io": False,
    "spawns_process_or_executor": False,
    "invokes_opl_or_codex": False,
    "authorizes_publication_or_submission": False,
}
_REVISION_CONSUMPTION_AUTHORITY_BOUNDARY = {
    "receipt_can_authorize_review_verdict": False,
    "receipt_can_authorize_owner_receipt": False,
    "receipt_can_authorize_publication": False,
    "receipt_can_authorize_submission": False,
    "receipt_can_create_typed_blocker": False,
}
_BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY = {
    "authorizes_publication": False,
    "authorizes_submission": False,
}
_EPISTEMIC_CHANGE_CLASSES = {
    "data",
    "context",
    "analysis_code",
    "analysis_parameters",
    "analysis_result",
    "claim",
    "reference_source",
    "citation_linkage",
    "limitation",
    "visual_content",
    "layout",
    "render_template",
    "package_composition",
    "package_wrapper",
    "governance_metadata",
    "review_receipt",
    "locator_only",
}
_EPISTEMIC_IGNORED_REASONS = {
    "outside_declared_evidence_graph",
    "locator_or_non_semantic_change_only",
    "governance_or_review_metadata_is_not_content_evidence",
    "outside_reviewed_dependency_closure",
}
_EPISTEMIC_CHANGE_CLASS_BY_NODE_ROLE = {
    "source_data": "data",
    "context": "context",
    "analysis_code": "analysis_code",
    "analysis_parameters": "analysis_parameters",
    "analysis_result": "analysis_result",
    "claim": "claim",
    "reference_source": "reference_source",
    "citation_linkage": "citation_linkage",
    "limitation": "limitation",
    "reproduction_instruction": None,
    "visual_content": "visual_content",
    "layout": "layout",
    "render_template": "render_template",
    "package_content": "package_composition",
    "package_wrapper": "package_wrapper",
    "governance_metadata": "governance_metadata",
    "review_receipt": "review_receipt",
}
_DEFAULT_MAIN_TABLE_INFORMATION_BUDGET = {
    "row_count": 15,
    "column_count": 8,
    "body_word_count": 350,
    "max_cell_word_count": 24,
    "footnote_word_count": 45,
    "final_embedding_page_span": 1,
}
