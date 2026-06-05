from __future__ import annotations

from typing import Any


SURFACE_KIND = "mas_ark_progress_first_learning_contract"
VERSION = "mas-ark-progress-first-learning-contract.v1"
OWNER = "MedAutoScience"
ARK_SOURCE_COMMIT = "01cab1048cc78fa4d33e8274e4f963a44d70dc48"

MICRO_STUDY_CANARY_STEPS: tuple[str, ...] = ("plan", "experiment", "write", "review")
HUMAN_DECISION_REQUEST_FIELDS: tuple[str, ...] = (
    "decision_request_id",
    "requester_stage",
    "blocked_action_ref",
    "blocker_kind",
    "hard_gate_ref",
    "evidence_refs",
    "options",
    "default_option_id",
    "consequence_by_option",
    "timeout_or_expiry",
    "resume_owner",
)
OPERATOR_MESSAGE_PREVIEW_FIELDS: tuple[str, ...] = (
    "message_preview_id",
    "event_kind",
    "stage_ref",
    "study_ref",
    "title",
    "body",
    "action_refs",
    "rendered_preview_text",
    "redaction_state",
    "currentness",
    "source_refs",
)
FIGURE_DATA_LINEAGE_QA_FIELDS: tuple[str, ...] = (
    "lineage_check_id",
    "experiment_result_ref",
    "result_digest",
    "display_artifact_manifest_ref",
    "rendered_artifact_ref",
    "claim_refs",
    "statistical_value_refs",
    "sampled_value_checks",
    "visual_qa_receipt_ref",
    "artifact_qa_work_unit_ref",
)
EXECUTOR_REAL_RUN_CLOSEOUT_FIELDS: tuple[str, ...] = (
    "closeout_id",
    "stage_ref",
    "attempt_ref",
    "claimed_action_ref",
    "real_command_or_tool_refs",
    "exit_status_refs",
    "output_artifact_refs",
    "failure_evidence_refs",
    "blocked_resource_refs",
    "fallback_or_substitute_used",
    "owner_receipt_ref",
)
COMPILED_VISUAL_REGION_QA_FIELDS: tuple[str, ...] = (
    "visual_region_check_id",
    "compiled_artifact_ref",
    "compiled_artifact_digest",
    "page_region_refs",
    "template_spec_ref",
    "text_overlap_check_ref",
    "figure_overflow_check_ref",
    "table_overflow_check_ref",
    "layout_work_unit_ref",
)
SEMANTIC_NO_PROGRESS_EVIDENCE_FIELDS: tuple[str, ...] = (
    "no_progress_evidence_id",
    "previous_artifact_ref",
    "current_artifact_ref",
    "semantic_delta_ref",
    "material_change_summary_ref",
    "reviewer_issue_ref",
    "next_bounded_work_unit_ref",
    "checked_at",
)
CITATION_LIFECYCLE_QUEUE_FIELDS: tuple[str, ...] = (
    "queue_item_id",
    "claim_segment_id",
    "citation_ref",
    "issue_kind",
    "lifecycle_state",
    "source_family",
    "currentness_digest_ref",
    "source_refresh_work_unit_ref",
    "reviewer_route_ref",
    "checked_at",
)


def build_ark_progress_first_learning_contract() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "version": VERSION,
        "owner": OWNER,
        "contract_ref": (
            "med_autoscience.progress_first_external_learning_contract."
            "build_ark_progress_first_learning_contract"
        ),
        "clean_room_absorption": {
            "source_project": "kaust-ark/ARK",
            "source_commit": ARK_SOURCE_COMMIT,
            "source_files": [
                "README.md",
                "TODO.md",
                "skills/builtin/human-intervention/SKILL.md",
                "skills/builtin/figure-integrity/SKILL.md",
                "tests/_preview_telegram.py",
            ],
            "absorbed_as": "mas_native_progress_first_contract_pattern",
            "runtime_dependency": False,
            "vendor_dependency": False,
            "foreign_authority": False,
        },
        "authority_boundary": {
            "truth_owner": OWNER,
            "surface_role": "progress_first_external_learning_descriptor",
            "publication_readiness_authority": False,
            "quality_verdict_authority": False,
            "source_readiness_authority": False,
            "artifact_mutation_authority": False,
            "runtime_control_authority": False,
            "human_approval_authority": False,
            "operator_message_transport_authority": False,
            "opl_role": "refs_index_projection_and_work_order_transport_only",
            "opl_can_write_mas_truth": False,
        },
        "progress_first_policy": {
            "may_block_unrelated_agent_progress": False,
            "non_hard_gate_gap_behavior": "typed_work_unit_or_route_back",
            "hard_gate_blockers": [
                "source_readiness_gate",
                "publication_gate",
                "artifact_mutation_authority_gate",
                "human_or_expert_gate",
                "forbidden_write_guard",
            ],
            "quality_gap_default": "continue_with_bounded_repair_work_unit",
            "operator_preview_gap_default": "projection_repair_work_unit",
        },
        "micro_study_canary_contract": _micro_study_canary_contract(),
        "human_decision_request_contract": _human_decision_request_contract(),
        "operator_message_preview_contract": _operator_message_preview_contract(),
        "figure_data_lineage_qa_contract": _figure_data_lineage_qa_contract(),
        "executor_real_run_closeout_contract": _executor_real_run_closeout_contract(),
        "compiled_visual_region_qa_contract": _compiled_visual_region_qa_contract(),
        "semantic_no_progress_evidence_contract": _semantic_no_progress_evidence_contract(),
        "citation_lifecycle_queue_contract": _citation_lifecycle_queue_contract(),
        "forbidden_adoptions": [
            "foreign_runtime_state_as_mas_truth",
            "telegram_or_webapp_transport_as_authority",
            "sqlite_project_db_as_mas_source_of_truth",
            "score_or_stagnation_threshold_as_publication_readiness",
            "fallback_experiment_or_fabricated_result",
            "layout_or_caption_edit_that_changes_data_or_claim_truth",
        ],
        "outputs": [
            "platform_repair_work_unit_ref",
            "human_decision_request_ref",
            "operator_message_preview_ref",
            "artifact_qa_work_unit_ref",
            "layout_work_unit_ref",
            "executor_closeout_evidence_ref",
            "source_refresh_work_unit_ref",
            "semantic_no_progress_evidence_ref",
            "reviewer_route_back_ref",
            "typed_blocker_ref",
            "owner_receipt_ref",
        ],
    }


def _micro_study_canary_contract() -> dict[str, object]:
    return {
        "role": "short_end_to_end_platform_regression_canary",
        "study_authority_role": "synthetic_fixture_only",
        "target_runtime_budget_minutes": 5,
        "required_steps": list(MICRO_STUDY_CANARY_STEPS),
        "required_refs": [
            "synthetic_study_fixture_ref",
            "plan_output_ref",
            "experiment_receipt_ref",
            "writer_output_ref",
            "reviewer_record_ref",
            "owner_receipt_ref",
        ],
        "failure_behavior": "platform_repair_work_unit",
        "failure_required_fields": [
            "failed_step",
            "reproducer_ref",
            "observed_output_ref",
            "expected_contract_ref",
            "repair_owner",
            "acceptance_test_ref",
        ],
        "may_block_real_studies": False,
        "may_authorize_publication_readiness": False,
    }


def _human_decision_request_contract() -> dict[str, object]:
    return {
        "role": "typed_hard_gate_human_decision_request",
        "required_fields": list(HUMAN_DECISION_REQUEST_FIELDS),
        "option_required_fields": ["option_id", "title", "consequence", "resumable_action_ref"],
        "hard_gate_only": True,
        "ordinary_quality_gap_behavior": "owner_work_unit_not_human_block",
        "after_request_behavior": {
            "dependent_work": "stop_until_decision_receipt",
            "unrelated_work": "may_continue",
            "fallback_or_degraded_completion_allowed": False,
            "decision_receipt_required_before_retry": True,
        },
        "may_authorize_human_approval": False,
        "may_authorize_publication_readiness": False,
    }


def _operator_message_preview_contract() -> dict[str, object]:
    return {
        "role": "operator_projection_preview_harness",
        "required_fields": list(OPERATOR_MESSAGE_PREVIEW_FIELDS),
        "preview_scope": "readability_redaction_and_action_ref_integrity",
        "network_side_effects_allowed": False,
        "transport_dependency": False,
        "allowed_preview_outputs": [
            "rendered_preview_text",
            "redaction_warning_ref",
            "missing_action_ref_projection_work_unit",
        ],
        "forbidden_preview_outputs": [
            "study_truth_write",
            "owner_route_decision",
            "publication_readiness",
            "operator_transport_delivery_receipt",
        ],
        "preview_gap_behavior": "projection_repair_work_unit",
        "may_block_agent_progress": False,
    }


def _figure_data_lineage_qa_contract() -> dict[str, object]:
    return {
        "role": "result_to_figure_to_claim_lineage_qa",
        "required_fields": list(FIGURE_DATA_LINEAGE_QA_FIELDS),
        "lineage_chain": [
            "experiment_result_ref",
            "result_digest",
            "display_artifact_manifest_ref",
            "rendered_artifact_ref",
            "claim_refs",
        ],
        "sampled_value_check_policy": {
            "minimum_sampled_values": 2,
            "sample_basis": "statistical_value_refs",
            "source_of_truth": "result_file_or_dataset_manifest",
        },
        "page_adjustment_priority_ladder": [
            "lossless_layout_adjustment",
            "minimally_lossy_presentation_adjustment",
            "manifest_gated_lossy_adjustment",
        ],
        "page_adjustment_policy": {
            "lossless_allowed_changes": ["placement", "width", "height", "float_position"],
            "minimally_lossy_requires": ["caption_accuracy_check", "visual_region_qa_ref"],
            "manifest_gated_lossy_requires": ["artifact_mutation_authority_ref", "claim_impact_review_ref"],
            "data_or_claim_changes_without_mas_authority": "typed_blocker",
        },
        "missing_or_mismatch_behavior": "artifact_qa_work_unit",
        "hard_gate_only_when": [
            "artifact_mutation_requested_without_mas_authority",
            "publication_gate_claim_depends_on_missing_result_ref",
            "figure_value_conflicts_with_source_result",
        ],
        "may_block_unrelated_agent_progress": False,
        "may_authorize_artifact_mutation": False,
    }


def _executor_real_run_closeout_contract() -> dict[str, object]:
    return {
        "role": "real_execution_closeout_evidence",
        "required_fields": list(EXECUTOR_REAL_RUN_CLOSEOUT_FIELDS),
        "blocked_not_degraded_policy": {
            "missing_resource_status": "blocked",
            "fallback_completion_status_allowed": False,
            "llm_substitute_for_real_experiment_allowed": False,
            "failed_command_evidence_required": True,
        },
        "dependent_work_behavior": "stop_until_resource_or_decision_receipt",
        "unrelated_work_behavior": "may_continue",
        "missing_closeout_behavior": "owner_work_unit_or_typed_blocker_for_hard_gate",
        "may_authorize_publication_readiness": False,
        "may_authorize_quality_verdict": False,
    }


def _compiled_visual_region_qa_contract() -> dict[str, object]:
    return {
        "role": "compiled_pdf_region_and_template_visual_qa",
        "required_fields": list(COMPILED_VISUAL_REGION_QA_FIELDS),
        "qa_checks": [
            "page_region_bounds",
            "text_overlap",
            "figure_overflow",
            "table_overflow",
            "template_width_compliance",
        ],
        "missing_or_failed_check_behavior": "layout_work_unit",
        "hard_gate_only_when": [
            "publication_gate_requires_compiled_artifact",
            "compiled_region_hides_or_changes_scientific_claim",
            "artifact_mutation_authority_required",
        ],
        "may_block_unrelated_agent_progress": False,
        "may_authorize_publication_readiness": False,
        "may_authorize_artifact_mutation": False,
    }


def _semantic_no_progress_evidence_contract() -> dict[str, object]:
    return {
        "role": "semantic_manuscript_delta_evidence_for_stagnation_review",
        "required_fields": list(SEMANTIC_NO_PROGRESS_EVIDENCE_FIELDS),
        "no_progress_signal_role": "reviewer_issue_evidence_only",
        "empty_or_trivial_delta_behavior": "next_bounded_work_unit_or_reviewer_route_back",
        "score_or_stagnation_threshold_authority": False,
        "may_block_unrelated_agent_progress": False,
        "may_authorize_quality_verdict": False,
        "may_authorize_publication_readiness": False,
    }


def _citation_lifecycle_queue_contract() -> dict[str, object]:
    return {
        "role": "source_citation_lifecycle_repair_queue",
        "required_fields": list(CITATION_LIFECYCLE_QUEUE_FIELDS),
        "issue_kinds": [
            "unused_citation_cleanup",
            "stale_citation_refresh",
            "claim_citation_mismatch",
            "metadata_only_candidate_review",
            "preprint_published_version_refresh",
        ],
        "allowed_lifecycle_states": [
            "queued",
            "source_refresh_requested",
            "reviewer_route_back_requested",
            "resolved_with_source_receipt",
            "blocked_by_hard_source_gate",
        ],
        "queue_behavior": {
            "unused_citation": "cleanup_work_unit",
            "stale_citation": "source_refresh_work_unit",
            "claim_citation_mismatch": "reviewer_route_back_or_source_refresh",
            "metadata_only_candidate": "manual_or_source_api_verification_required",
            "critical_claim_without_source": "typed_blocker",
        },
        "may_block_unrelated_agent_progress": False,
        "may_authorize_source_readiness": False,
        "may_authorize_publication_readiness": False,
    }


__all__ = [
    "ARK_SOURCE_COMMIT",
    "CITATION_LIFECYCLE_QUEUE_FIELDS",
    "COMPILED_VISUAL_REGION_QA_FIELDS",
    "EXECUTOR_REAL_RUN_CLOSEOUT_FIELDS",
    "FIGURE_DATA_LINEAGE_QA_FIELDS",
    "HUMAN_DECISION_REQUEST_FIELDS",
    "MICRO_STUDY_CANARY_STEPS",
    "OPERATOR_MESSAGE_PREVIEW_FIELDS",
    "OWNER",
    "SEMANTIC_NO_PROGRESS_EVIDENCE_FIELDS",
    "SURFACE_KIND",
    "VERSION",
    "build_ark_progress_first_learning_contract",
]
