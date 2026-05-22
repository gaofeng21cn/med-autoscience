from __future__ import annotations

from typing import Any

from .quality_boundary import (
    CROSS_STAGE_VULNERABILITY_AUDIT,
    DEVELOPER_PATCH_WORK_ORDER_ID,
    PAPER_STORY_EXCLUSION_POLICY,
    QUALITY_JUDGMENT_BOUNDARY,
    SELF_EVOLUTION_TARGET_REFS,
)
from .study_quality_targets import (
    study_quality_contract_profile,
    study_quality_target_profile,
)


def target_editable_surface_refs(*, study_id: str) -> list[str]:
    quality_contract = study_quality_contract_profile(study_id=study_id)
    refs = [
        ref
        for ref in SELF_EVOLUTION_TARGET_REFS
        if not ref.startswith("quality_contract_ref:")
    ]
    refs.append(quality_contract["quality_contract_ref"])
    return refs


def developer_patch_work_order(*, study_id: str, evidence_refs: list[str]) -> dict[str, Any]:
    profile = study_quality_target_profile(study_id=study_id)
    quality_contract = study_quality_contract_profile(study_id=study_id)
    return {
        "work_order_id": DEVELOPER_PATCH_WORK_ORDER_ID,
        "owner_agent": "opl-meta-agent",
        "role": "developer_direct_repo_patch",
        "target_repo": "med-autoscience",
        "status": "blocked_until_repo_patch",
        "trigger": "agent_lab_blocked_medical_manuscript_quality_suite",
        "target_editable_surface_refs": target_editable_surface_refs(study_id=study_id),
        "required_patch_scopes": [
            "analysis_harmonization_owner_callable",
            "source_provenance_owner_recovery",
            "source_provenance_terminal_blocker_route_back",
            "methodology_reframe_decision_owner_route",
            "hard_methodology_unit_harmonization_route",
            "domain_route_analysis_harmonization_owner_result_consumption",
            "ai_reviewer_output_readiness_currentness_consumption",
            "ai_reviewer_record_production_handoff",
            "ai_reviewer_record_current_manuscript_binding",
            "ai_native_expert_judgment_first_quality_boundary",
            "cross_stage_vulnerability_audit_routing",
            "internal_error_debug_history_paper_story_exclusion",
            quality_contract["required_patch_scope"],
            "ai_reviewer_high_quality_medical_manuscript_rubric",
            "write_stage_pre_draft_prediction_model_reporting",
            "quality_repair_blocked_evidence_dispatch_rejection",
            "regression_tests_and_docs",
        ],
        "study_quality_target_family": profile["family"],
        "study_quality_targets": profile["targets"],
        "quality_judgment_boundary": dict(QUALITY_JUDGMENT_BOUNDARY),
        "cross_stage_vulnerability_audit": dict(CROSS_STAGE_VULNERABILITY_AUDIT),
        "paper_story_exclusion_policy": dict(PAPER_STORY_EXCLUSION_POLICY),
        "evidence_refs": evidence_refs,
        "forbidden_writes": [
            "publication_eval/latest.json",
            "controller_decisions/latest.json",
            "paper/submission_minimal",
            "manuscript/current_package",
            "submission readiness verdict",
        ],
        "can_modify_mas_repo": True,
        "can_write_study_truth": False,
        "can_authorize_quality_verdict": False,
        "can_mutate_paper_package": False,
    }
