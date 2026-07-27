"""Public compatibility surface for _generation_manifest."""

from __future__ import annotations

from ._generation_manifest_parts.constants import (
    ALLOWED_ROLES_BY_SCOPE,
    ANALYSIS_GENERATION_ROLES,
    EPISTEMIC_AUTHORITY_BOUNDARY,
    EPISTEMIC_EDGE_RULES_BY_LANE,
    EPISTEMIC_EVIDENCE_PROFILE,
    EPISTEMIC_NODE_ROLE_BY_LANE,
    EPISTEMIC_REVIEWED_ARTIFACT_ROLES_BY_LANE,
    EPISTEMIC_REVIEW_SCOPE_VERSION,
    EPISTEMIC_SCOPE_KIND_BY_LANE,
    EPISTEMIC_TRUST_MODEL,
    FIRST_DRAFT_QUALITY_DISPOSITION_STATUSES,
    FIRST_DRAFT_QUALITY_ROLES,
    FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    FIRST_DRAFT_QUALITY_ROUTE_PRIORITY,
    FIRST_DRAFT_VALIDATION_DESIGNS,
    LEGACY_FIRST_DRAFT_QUALITY_ROLE_BY_REF_FIELD,
    MANUSCRIPT_GENERATION_ROLES,
    OPTIONAL_GENERATION_ROLES,
    OPTIONAL_ROLES_BY_SCOPE,
    PROFESSIONAL_MANUSCRIPT_SKILL_INPUT_ROLES,
    PROFESSIONAL_MANUSCRIPT_SKILL_ROLES,
    PUBLICATION_GENERATION_ROLES,
    PUBLICATION_SINGLETON_ROLES,
    REQUIRED_ROLES_BY_SCOPE,
    REVIEWER_RESPONSE_ROLES,
    REVIEWER_RESPONSE_ROLE_BY_REF_FIELD,
    REVIEW_AUTHORITY_ROLE_BY_LANE,
    REVIEW_LANES_BY_SCOPE,
    REVIEW_LANE_ORDER,
    REVIEW_SCOPE_POLICY_ID,
    REVIEW_SCOPE_POLICY_VERSION,
    REVIEW_SCOPE_ROLES_BY_LANE,
    REVISION_GENERATION_ROLES,
    SCHOLAR_V2_FIRST_DRAFT_ROLE_BY_REF_FIELD,
    SCHOLAR_V2_SEMANTIC_POLICY_BY_SKILL,
    SELECTED_BUILD_ROLES,
    SELECTED_BUILD_ROLE_BY_REF_FIELD,
    STAGE_FIXED_REVIEW_LANE,
    STAGE_MINIMUM_SCOPE,
    _SCOPE_RANK,
)
from ._generation_manifest_parts.manifest import (
    _normalize_generation_artifact_inventory,
    build_generation_manifest_v2,
    normalize_generation_manifest,
)
from ._generation_manifest_parts.records import (
    _manifest_artifact_ref,
    _normalize_artifact,
    _require_unique_member_ids,
)
from ._generation_manifest_parts.currentness import (
    _normalize_affected_artifact_binding,
    _normalize_clinical_analysis_identity_admission,
    _normalize_dependency_currentness_receipt,
    _normalize_no_authority_boundary,
    _normalize_reviewer_response_evidence_refs,
    _normalize_reviewer_response_sync,
    _normalize_selected_build_binding,
    _validate_reviewer_response_evidence_refs,
)
from ._generation_manifest_parts.first_draft import (
    _normalize_first_draft_candidate_disposition,
    _normalize_first_draft_quality_application,
    _normalize_scholar_v2_semantic_policy_bindings,
    _validate_scholar_v2_semantic_policy_invocations,
    first_draft_applicable_ref_fields,
)
from ._generation_manifest_parts.professional_manuscript import (
    _normalize_professional_manuscript_skill_invocation,
    _normalize_professional_skill_invocations,
)
from ._generation_manifest_parts.professional_table import (
    _normalize_main_table_quality_assessment,
    _normalize_table_quality_application,
)
from ._generation_manifest_parts.professional_skill import (
    _normalize_figure_template_usage,
    _normalize_figure_text_policy,
    _normalize_professional_invocation_ref,
    _normalize_professional_skill_artifact_binding,
    _normalize_professional_skill_input_bindings,
    _normalize_professional_skill_invocation,
)
from ._generation_manifest_parts.review_scope import (
    build_epistemic_review_scope,
    build_review_scopes,
    epistemic_review_dependency_refs,
    epistemic_review_scope_identity,
    require_stage_scope,
    review_scope_inventory,
    review_scope_member_projection,
    review_scope_sha256,
    source_input_digest,
)
from ._generation_manifest_parts.review_snapshot import (
    _normalize_review_input_snapshot_authority_issuer,
    _review_input_snapshot_authority_record,
    _review_input_snapshot_authority_record_ref,
    build_review_input_snapshot_materialization_request,
    build_stage_review_input_snapshot_bundle,
)
from ._generation_manifest_parts.review_receipts import (
    _normalize_review_input_snapshot_binding,
    _normalize_review_receipt,
    _normalize_review_receipt_v1,
    _normalize_review_receipt_v2,
    _normalize_review_scope,
)

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
