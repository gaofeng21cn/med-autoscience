from __future__ import annotations

from typing import Any

from med_autoscience.runtime_protocol.evo_scientist_sidecar_refs import (
    build_evo_scientist_sidecar_execution_surface,
)


SURFACE_KIND = "mas_evo_scientist_progress_accelerator_projection"
SOURCE_REPOSITORY = "https://github.com/EvoScientist/EvoScientist"
SKILLS_REPOSITORY = "https://github.com/EvoScientist/EvoSkills"
SOURCE_RELEASE = "v0.1.4"
SOURCE_RELEASE_PUBLISHED_AT = "2026-06-06T23:57:20Z"
SKILLS_RELEASE = "v1.0.0"
CONTRACT_REF = "contracts/evo_scientist_progress_accelerator.json"
PROJECTION_BUILDER_REF = (
    "med_autoscience.evo_scientist_learning_projection."
    "build_evo_scientist_learning_projection"
)
DOC_REF = "docs/runtime/designs/evo_scientist_progress_first_intake.md"


def build_evo_scientist_learning_projection() -> dict[str, Any]:
    return {
        "surface_kind": SURFACE_KIND,
        "version": "mas-evo-scientist-progress-accelerator.v1",
        "status": "repo_callable_sidecar_execution_surface_projected",
        "contract_ref": CONTRACT_REF,
        "progress_accelerator_contract_ref": CONTRACT_REF,
        "projection_builder_ref": PROJECTION_BUILDER_REF,
        "source_snapshot": {
            "source_project": "EvoScientist/EvoScientist + EvoScientist/EvoSkills",
            "repository": SOURCE_REPOSITORY,
            "skills_repository": SKILLS_REPOSITORY,
            "observed_release": SOURCE_RELEASE,
            "observed_release_published_at": SOURCE_RELEASE_PUBLISHED_AT,
            "skills_release": SKILLS_RELEASE,
            "intake_doc_ref": DOC_REF,
            "dependency_introduced": False,
        },
        "absorbed_patterns": [
            {
                "pattern_id": "auxiliary_background_model",
                "classification": "adopt_contract",
                "source_pattern": "co_pilot_auxiliary_model_for_memory_workers_and_tool_selector",
                "mas_mapping": "auxiliary_helper_for_background_selection_prefetch_and_memory_distill",
                "owner_surface": "runtime_os_and_operator_projection",
                "target_surfaces": [
                    "tool_selection_advisory",
                    "observation_memory_sidecar",
                    "opportunistic_knowledge_prefetch",
                    "operator_context_compaction",
                ],
                "source_refs": [
                    "EvoScientist v0.1.4 release: Co-Pilot Auxiliary Model",
                    "EvoScientist/EvoScientist::EvoScientist._ensure_auxiliary_chat_model",
                    "EvoScientist/EvoScientist::middleware.tool_selector",
                ],
                "authority": "advisory_background_only",
            },
            {
                "pattern_id": "fire_and_forget_observation_memory",
                "classification": "adopt_contract",
                "source_pattern": "turn_and_subagent_memory_workers_record_observations_after_completion",
                "mas_mapping": "async_learning_sidecar_with_refs_only_observations",
                "owner_surface": "route_memory_and_audit_sidecar",
                "target_surfaces": [
                    "publication_route_memory_pack",
                    "stage_memory_closeout_packet",
                    "memory_write_router_receipt",
                    "failed_path_observation_refs",
                ],
                "source_refs": [
                    "EvoScientist v0.1.4 release: Self-Evolving Observation Memory",
                    "EvoScientist/EvoScientist::middleware.memory_lifecycle",
                ],
                "authority": "refs_only_memory_hint_until_mas_router_receipt",
            },
            {
                "pattern_id": "conditional_tool_selection",
                "classification": "adopt_contract",
                "source_pattern": "LLM_tool_selector_runs_only_above_threshold_and_falls_back_to_all_tools",
                "mas_mapping": "generated_surface_tool_visibility_fail_open_policy",
                "owner_surface": "generated_default_caller_and_operator_projection",
                "target_surfaces": [
                    "product_entry_manifest",
                    "domain_handler_export",
                    "default_executor_handoff",
                ],
                "source_refs": [
                    "EvoScientist/EvoScientist::middleware.tool_selector",
                ],
                "authority": "fail_open_tool_visibility",
            },
            {
                "pattern_id": "skill_routing_eval",
                "classification": "adopt_template",
                "source_pattern": "EvoSkills routing optimized through evals",
                "mas_mapping": "stage_action_skill_route_meta_eval",
                "owner_surface": "generated_default_caller_surfaces",
                "target_surfaces": [
                    "agent/stages/stage_route_contract.yaml",
                    "contracts/stage_control_plane.json",
                    "test-lane manifests",
                ],
                "source_refs": [
                    "EvoSkills v1.0.0 release: routing-optimized skills",
                ],
                "authority": "meta_release_gate_only",
            },
            {
                "pattern_id": "ive_failed_path_memory_taxonomy",
                "classification": "adopt_contract",
                "source_pattern": "IDE_IVE_ESE_memory_evolution_and_failure_classification",
                "mas_mapping": "typed_failed_path_memory_and_stop_loss_route_hints",
                "owner_surface": "publication_route_memory",
                "target_surfaces": [
                    "failed_path_memory_refs",
                    "typed_blocker_context",
                    "route_back_refs",
                    "stop_loss_candidate_refs",
                ],
                "source_refs": [
                    "EvoSkills v1.0.0 release: evo-memory IDE IVE ESE",
                    "EvoSkills/skills/evo-memory/SKILL.md",
                ],
                "authority": "memory_hint_requires_evidence_and_router_receipt",
            },
            {
                "pattern_id": "attempt_budget_stop_loss",
                "classification": "adopt_template",
                "source_pattern": "experiment_attempt_budgets_and_early_termination",
                "mas_mapping": "stop_loss_candidate_without_blocking_known_next_delta",
                "owner_surface": "runtime_os_and_stage_route",
                "target_surfaces": [
                    "current_owner_delta",
                    "ProgressDeltaReceipt",
                    "TypedBlocker",
                    "stop_loss_memo",
                ],
                "source_refs": [
                    "EvoSkills/skills/experiment-pipeline/SKILL.md",
                    "EvoSkills/skills/experiment-iterative-coder/SKILL.md",
                ],
                "authority": "route_hint_not_attempt_hard_stop",
            },
        ],
        "ordinary_progress_boundary": {
            "surface_kind": "mas_progress_first_learning_sidecar_boundary",
            "ordinary_progress_spine": [
                "current_owner_delta",
                "concrete_delta",
                "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
                "next_current_owner_delta",
            ],
            "learning_sidecar_role": "accelerate_selection_memory_prefetch_and_failure_reuse",
            "can_generate_default_next_action": False,
            "can_block_current_owner_action": False,
            "critical_path_waits_for_sidecar": False,
            "can_require_full_research_lifecycle_preflight": False,
            "can_require_full_readiness_inventory": False,
            "platform_repair_or_prefetch_counts_as_paper_progress": False,
            "missing_learning_sidecar_blocks_dispatch": False,
        },
        "target_sidecar_execution_architecture": {
            "surface_kind": "mas_evo_scientist_target_sidecar_execution_architecture",
            "architecture_state": "repo_callable_worker_landed",
            "remaining_learning_plan": False,
            "future_work_role": "implementation_scaleout_under_this_contract_only",
            "execution_model": "nonblocking_current_owner_following_sidecar",
            "ordinary_progress_critical_path": [
                "current_owner_delta",
                "concrete_delta",
                "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
                "next_current_owner_delta",
            ],
            "sidecar_launch_points": [
                "after_current_owner_delta_materialized",
                "after_tool_surface_hydrated",
                "after_executor_turn_or_subagent_completion",
                "after_receipt_or_typed_blocker_recorded",
            ],
            "sidecar_inputs": [
                "current_owner_delta_ref",
                "owner_policy_ref",
                "allowed_tool_manifest_ref",
                "executor_turn_summary_ref",
                "subagent_summary_ref",
                "receipt_or_typed_blocker_ref",
                "prior_failed_path_memory_refs",
            ],
            "sidecar_outputs": [
                "tool_affordance_ref",
                "observation_memory_ref",
                "failed_path_memory_ref",
                "reviewer_briefing_ref",
                "route_hint_ref",
                "stop_loss_candidate_ref",
            ],
            "scheduling_contract": {
                "owner": "one-person-lab",
                "mas_role": "declare_domain_boundaries_and_accept_refs_only_candidates",
                "runs_parallel_to_ordinary_progress": True,
                "mainline_waits_for_sidecar": False,
                "sidecar_failure_policy": "drop_sidecar_ref_and_continue_current_owner_action",
                "sidecar_timeout_policy": "record_diagnostic_if_available_and_continue",
                "sidecar_conflict_policy": "owner_policy_wins",
            },
            "budget_contract": {
                "budget_source": "owner_route_budget_envelope",
                "budget_exhaustion_policy": "stop_sidecar_not_owner_action",
                "sidecar_retry_policy": "bounded_retry_or_skip",
                "budget_exhaustion_can_emit_typed_blocker": False,
            },
            "admission_contract": {
                "sidecar_completion_required_for_dispatch": False,
                "sidecar_completion_required_for_stage_transition": False,
                "sidecar_completion_required_for_quality_gate": False,
                "sidecar_completion_required_for_artifact_mutation": False,
                "sidecar_may_submit_hard_gate_candidate_ref": True,
                "hard_gate_candidate_requires_owner_or_reviewer_materialization": True,
            },
            "implementation_slots": [
                {
                    "slot": "tool_selector_helper",
                    "status": "repo_callable_sidecar_output_ref_landed",
                    "trigger": "tool_surface_noise_exceeds_threshold",
                    "output_ref": "tool_affordance_ref",
                    "failure_policy": "fail_open_to_owner_required_tools",
                },
                {
                    "slot": "observation_memory_sidecar",
                    "status": "repo_callable_sidecar_output_ref_landed",
                    "trigger": "turn_or_subagent_completion",
                    "output_ref": "observation_memory_ref",
                    "failure_policy": "fire_and_forget_no_mainline_wait",
                },
                {
                    "slot": "failed_path_taxonomy",
                    "status": "repo_callable_sidecar_output_ref_landed",
                    "trigger": "receipt_typed_blocker_or_failed_attempt_recorded",
                    "output_ref": "failed_path_memory_ref",
                    "failure_policy": "no_loop_hint_only",
                },
                {
                    "slot": "routing_eval",
                    "status": "repo_callable_sidecar_output_ref_landed",
                    "trigger": "release_or_meta_regression_gate",
                    "output_ref": "route_regression_ref",
                    "failure_policy": "meta_gate_only_not_live_delta_gate",
                },
                {
                    "slot": "attempt_budget_stop_loss",
                    "status": "repo_callable_sidecar_output_ref_landed",
                    "trigger": "repeated_failed_attempt_signature",
                    "output_ref": "stop_loss_candidate_ref",
                    "failure_policy": "candidate_ref_only_until_owner_decision",
                },
            ],
        },
        "runtime_sidecar_execution_surface": build_evo_scientist_sidecar_execution_surface(),
        "auxiliary_helper_contract": {
            "surface_kind": "mas_auxiliary_helper_contract",
            "allowed_roles": [
                "tool_selection_advisory",
                "observation_memory_distillation",
                "subagent_execution_summary",
                "opportunistic_prefetch_summary",
                "routing_eval_draft",
            ],
            "forbidden_roles": [
                "study_truth_writer",
                "publication_quality_verdict",
                "artifact_authority",
                "owner_receipt_signer",
                "typed_blocker_replacer",
                "default_owner_action_authorizer",
            ],
            "main_agent_keeps_reasoning_authority": True,
            "fallback_to_main_model_or_no_helper": True,
        },
        "tool_selector_contract": {
            "surface_kind": "mas_tool_selector_fail_open_contract",
            "activation_policy": "only_when_tool_surface_noise_exceeds_threshold",
            "fail_open_to_all_tools": True,
            "selector_failure_is_not_task_failure": True,
            "owner_required_tools_always_include": True,
            "can_hide_current_owner_required_tool": False,
            "can_authorize_or_deny_owner_action": False,
            "selection_trace_role": "operator_diagnostic_only",
        },
        "observation_memory_contract": {
            "surface_kind": "mas_async_observation_memory_contract",
            "worker_mode": "fire_and_forget_after_turn_or_subagent_completion",
            "mainline_waits_for_memory_worker": False,
            "memory_body_authority_owner": "MedAutoScience",
            "writeback_requires_router_receipt": True,
            "can_write_domain_truth": False,
            "can_write_evidence_ledger": False,
            "can_write_review_ledger": False,
            "can_authorize_quality_verdict": False,
            "can_authorize_publication_readiness": False,
            "memory_refs_can_hint_future_route": True,
            "memory_refs_can_close_current_stage": False,
        },
        "failed_path_memory_contract": {
            "surface_kind": "mas_failed_path_memory_taxonomy_contract",
            "taxonomy": [
                "implementation_failure",
                "fundamental_risk",
                "stale_runtime_or_currentness_drift",
                "authority_boundary_drift",
                "evidence_or_source_gap",
                "human_gate_or_policy_gap",
            ],
            "classification_output_role": "route_hint_or_typed_blocker_context",
            "fundamental_failure_requires_reviewer_or_owner_evidence": True,
            "implementation_failure_stays_retryable": True,
            "can_prune_current_owner_action_without_receipt": False,
            "can_replace_publication_eval": False,
            "can_mark_study_direction_dead_without_owner_decision": False,
        },
        "routing_eval_contract": {
            "surface_kind": "mas_stage_skill_routing_eval_contract",
            "eval_role": "meta_release_gate_and_regression_guard",
            "live_path_runs_eval_each_delta": False,
            "can_block_known_current_owner_delta": False,
            "allowed_outputs": [
                "route_regression_ref",
                "skill_trigger_gap_ref",
                "generated_surface_mismatch_ref",
                "typed_blocker_context_ref",
            ],
        },
        "watch_only_patterns": [
            {
                "pattern_id": "idea_tournament_as_default_gate",
                "reason": "ranking is useful only as advisory next-delta prioritization; it cannot gate writing, analysis, review, or owner-action dispatch",
            },
            {
                "pattern_id": "full_research_lifecycle_pipeline_as_mas_default",
                "reason": "MAS default path stays ordinary progress spine with just-in-time readiness, not a mandatory end-to-end EvoSkills pipeline",
            },
        ],
        "rejected_patterns": [
            "external_deepagents_runtime_as_mas_runtime",
            "foreign_langgraph_dev_worker_as_opl_substrate",
            "evo_memory_body_as_mas_truth",
            "tool_selector_as_hard_gate",
            "self_review_as_independent_quality_gate",
            "mandatory_full_literature_grounding_before_each_delta",
            "full_evoskills_pipeline_as_live_preflight",
        ],
        "authority_boundary": {
            "domain_truth_owner": "MedAutoScience",
            "quality_verdict_owner": "MedAutoScience",
            "source_readiness_owner": "MedAutoScience",
            "publication_artifact_authority_owner": "MedAutoScience",
            "generic_runtime_owner": "one-person-lab",
            "source_project_role": "external_pattern_source_only",
            "can_write_domain_truth": False,
            "can_write_evidence_ledger": False,
            "can_write_review_ledger": False,
            "can_write_publication_eval": False,
            "can_write_controller_decisions": False,
            "can_authorize_source_readiness": False,
            "can_authorize_publication_quality": False,
            "can_authorize_submission_readiness": False,
            "can_authorize_artifact_authority": False,
            "can_close_stage": False,
        },
    }


__all__ = [
    "CONTRACT_REF",
    "DOC_REF",
    "PROJECTION_BUILDER_REF",
    "SKILLS_RELEASE",
    "SKILLS_REPOSITORY",
    "SOURCE_RELEASE",
    "SOURCE_RELEASE_PUBLISHED_AT",
    "SOURCE_REPOSITORY",
    "SURFACE_KIND",
    "build_evo_scientist_learning_projection",
]
