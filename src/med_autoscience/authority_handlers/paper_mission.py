"""Public compatibility surface for paper_mission."""

from __future__ import annotations

from .paper_mission_parts.constants import (
    REQUEST_KIND,
    RESULT_KIND,
    SCHEMA_VERSION,
    _AUTHORITY_BOUNDARY,
    _BUILD_DEPENDENCY_CURRENTNESS_AUTHORITY_BOUNDARY,
    _DEFAULT_MAIN_TABLE_INFORMATION_BUDGET,
    _EPISTEMIC_CHANGE_CLASSES,
    _EPISTEMIC_CHANGE_CLASS_BY_NODE_ROLE,
    _EPISTEMIC_IGNORED_REASONS,
    _HARD_GATE_KINDS,
    _REVISION_CONSUMPTION_AUTHORITY_BOUNDARY,
)
from .paper_mission_parts.orchestration import (
    evaluate_paper_mission_authority,
)
from .paper_mission_parts.request import (
    _is_reviewer_revision,
    _normalize_candidate_admissions,
    _normalize_consumed_revision_refs,
    _normalize_host_context,
    _normalize_medical_evidence,
    _normalize_mission,
    _normalize_opl_finding_lineage,
    _normalize_request,
    _normalize_review_authority,
    _normalize_revision_consumption,
    _normalize_revision_consumption_receipt,
    _normalize_revision_finding_closures,
)
from .paper_mission_parts.currentness import (
    _normalize_epistemic_change,
    _normalize_epistemic_currentness,
    _normalize_hard_gate,
    _normalize_lane_currentness,
    _normalize_repair,
    _normalize_reuse_provenance,
    _normalize_review_currentness_receipt,
    _normalize_review_currentness_receipt_v1,
    _normalize_review_currentness_receipt_v2,
    _normalize_reviewer_response_authority_currentness,
    _normalize_selected_build_currentness_authority,
)
from .paper_mission_parts.validation import (
    _candidate_admission_issue,
    _epistemic_evaluation_matches_scope,
    _exact_ref_identity,
    _review_currentness_issue,
    _review_currentness_issue_v2,
    _review_member_semantic_identities,
    _revision_consumption_issue,
    _validate_cross_record_lineage,
    _validate_review_currentness_receipt_ref,
    _validate_selected_build_currentness_authority,
)
from .paper_mission_parts.quality import (
    _aggregate_review_status,
    _first_draft_quality_issue,
    _professional_figure_skill_quality_debt,
    _professional_manuscript_skill_quality_debt,
    _professional_table_quality_debt,
    _review_quality_debt,
    _reviewer_revision_generation_issue,
)
from .paper_mission_parts.result import (
    _finalize,
    _first_draft_quality_debt_result,
    _human_gate,
    _invalid_host_input,
    _professional_skill_debt_result,
    _quality_debt,
    _route_back,
    _route_result,
    _stage_outcome,
    _typed_blocker,
)
from .paper_mission_parts.receipt import (
    _artifact_projection_transport,
    _generation_artifact_identity,
    _generation_identity,
    _host_refs,
    _owner_receipt,
    _professional_skill_receipt_projection,
    _revision_consumption_projection,
)

__all__ = ["evaluate_paper_mission_authority"]
