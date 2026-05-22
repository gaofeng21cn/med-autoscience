from __future__ import annotations

from pathlib import Path


SURFACE_KIND = "mas_agent_lab_medical_manuscript_quality_suite"
SUITE_RELATIVE_PATH = Path("artifacts") / "agent_lab" / "medical_manuscript_quality" / "latest_suite.json"
AUTHORITY_BOUNDARY = {
    "opl": "agent_lab_eval_improvement_control_plane_refs_only",
    "mas": "publication_quality_and_artifact_authority",
    "can_write_domain_truth": False,
    "can_write_memory_body": False,
    "can_authorize_domain_ready": False,
    "can_authorize_quality_verdict": False,
    "can_authorize_submission_readiness": False,
    "can_mutate_domain_artifact": False,
    "can_promote_default_agent_without_gate": False,
}
SELF_EVOLUTION_TARGET_REFS = [
    "stage_policy_ref:mas/write/pre_draft_prediction_model_reporting",
    "mechanism-edit-ref:mas/ai-native-expert-judgment-first-quality-boundary",
    "mechanism-edit-ref:mas/cross-stage-vulnerability-audit-routing",
    "mechanism-edit-ref:mas/internal-error-debug-history-paper-story-exclusion",
    "mechanism-edit-ref:mas/internal-methodology-repair-story-boundary",
    "mechanism-edit-ref:mas/research-wiki-failed-route-memory",
    "mechanism-edit-ref:mas/ai-reviewer-direct-evidence-gate",
    "mechanism-edit-ref:mas/analysis-campaign-queue-routing",
    "mechanism-edit-ref:mas/analysis-harmonization-owner-routing",
    "mechanism-edit-ref:mas/source-provenance-owner-recovery",
    "mechanism-edit-ref:mas/source-provenance-terminal-blocker-route-back",
    "mechanism-edit-ref:mas/methodology-reframe-decision-owner-route",
    "mechanism-edit-ref:mas/domain-route-analysis-harmonization-owner-result-consumption",
    "mechanism-edit-ref:mas/ai-reviewer-output-readiness-currentness-consumption",
    "mechanism-edit-ref:mas/quality-repair-blocked-evidence-dispatch-rejection",
    "mechanism-edit-ref:mas/ai-reviewer-record-production-handoff",
    "mechanism-edit-ref:mas/ai-reviewer-record-current-manuscript-binding",
    "mechanism-edit-ref:mas/runtime-event-ledger-body-free-projection",
    "mechanism-edit-ref:mas/provider-switch-hygiene-body-free-projection",
    "mechanism-edit-ref:mas/claim-assurance-map-body-free-projection",
    "mechanism-edit-ref:mas/assurance-contract-body-free-projection",
    "mechanism-edit-ref:mas/adversarial-review-gate-body-free-projection",
    "mechanism-edit-ref:mas/experiment-queue-recovery-body-free-projection",
    "mechanism-edit-ref:mas/publication-aftercare-plan-body-free-projection",
    "mechanism-edit-ref:mas/citation-audit-body-free-projection",
    "mechanism-edit-ref:mas/kill-argument-counterargument-body-free-projection",
    "mechanism-edit-ref:mas/submission-assurance-five-layer-gate-body-free-projection",
    "mechanism-edit-ref:mas/effort-assurance-axes-body-free-projection",
    "mechanism-edit-ref:mas/invalid-analysis-history-body-free-projection",
    "skill_ref:medical-research-write",
    "rubric_ref:ai_reviewer/high_quality_medical_manuscript",
    "prompt_ref:ai_reviewer_medical_prose_quality_review",
    "quality_contract_ref:prediction_model_first_draft_quality",
    "policy_ref:mas/ai-first-quality-boundary/contracts-floor-not-ceiling",
    "regression-suite:mas/hard-methodology-unit-harmonization-route",
    "regression-suite:mas/ai-reviewer-output-readiness-currentness",
    "regression-suite:mas/ai-reviewer-record-current-manuscript-binding",
    "regression-suite:mas/medical-prose-write-repair-story-surface-delta",
    "regression_suite_ref:mas/agent_lab_medical_manuscript_self_evolution",
]
QUALITY_JUDGMENT_BOUNDARY = {
    "judgment_priority": "ai_native_expert_judgment_first",
    "primary_judgment_owner": "mas_ai_reviewer",
    "contract_rubric_role": "floor_and_route_baseline_not_ceiling",
    "contracts_can_block_below_floor": True,
    "contracts_can_authorize_quality_ready": False,
    "rubric_can_authorize_quality_ready": False,
    "opl_meta_agent_can_patch_mas_repo": True,
    "opl_meta_agent_can_write_study_truth": False,
    "opl_meta_agent_can_authorize_quality_verdict": False,
    "requires_independent_ai_reviewer_receipt_for_quality_closure": True,
}
CROSS_STAGE_VULNERABILITY_AUDIT = {
    "audit_kind": "cross_stage_quality_vulnerability_scan",
    "route_role": "mechanism_gap_detection_and_repo_patch_work_order",
    "must_scan_stage_refs": [
        "stage:mas/review",
        "stage:mas/analysis-campaign",
        "stage:mas/write",
        "stage:mas/write/pre_draft_prediction_model_reporting",
        "stage:mas/figure-polish/high_quality_medical_journal_figures",
        "stage:mas/publication-gate",
    ],
    "vulnerability_classes": [
        "reviewer_feedback_lost_between_stages",
        "methodology_blocker_downgraded_to_prose_repair",
        "mechanical_gate_overrides_ai_reviewer_judgment",
        "package_or_delivery_state_preempts_quality_route_back",
        "internal_error_history_leaks_into_public_manuscript_story",
        "internal_methodology_repair_becomes_manuscript_contribution",
    ],
    "can_authorize_quality_ready": False,
}
PAPER_STORY_EXCLUSION_POLICY = {
    "surface_kind": "internal_error_debug_history_paper_story_exclusion",
    "internal_error_debug_history_role": "runtime_diagnostics_and_mechanism_learning_only",
    "allowed_projection": "refs_metadata_and_incident_learning",
    "forbidden_projection": "paper_main_story_or_medical_claim_support",
    "paper_story_can_use_debug_history": False,
    "paper_story_can_use_internal_methodology_repair_as_contribution": False,
    "methodology_repair_belongs_in_methods_or_provenance": True,
    "debug_history_can_authorize_quality_ready": False,
}
DEVELOPER_PATCH_WORK_ORDER_ID = "oma_developer_patch_work_order_99fdc0d34111"
