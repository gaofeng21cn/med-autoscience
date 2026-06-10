from __future__ import annotations

import importlib
import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_evo_scientist_learning_projection_absorbs_progress_accelerators_only() -> None:
    module = importlib.import_module("med_autoscience.evo_scientist_learning_projection")

    projection = module.build_evo_scientist_learning_projection()

    assert projection["surface_kind"] == "mas_evo_scientist_progress_accelerator_projection"
    assert projection["version"] == "mas-evo-scientist-progress-accelerator.v1"
    assert projection["status"] == "repo_callable_sidecar_execution_surface_projected"
    assert projection["contract_ref"] == "contracts/evo_scientist_progress_accelerator.json"
    assert projection["progress_accelerator_contract_ref"] == (
        "contracts/evo_scientist_progress_accelerator.json"
    )
    assert projection["projection_builder_ref"] == (
        "med_autoscience.evo_scientist_learning_projection."
        "build_evo_scientist_learning_projection"
    )
    assert projection["source_snapshot"] == {
        "source_project": "EvoScientist/EvoScientist + EvoScientist/EvoSkills",
        "repository": "https://github.com/EvoScientist/EvoScientist",
        "skills_repository": "https://github.com/EvoScientist/EvoSkills",
        "observed_release": "v0.1.4",
        "observed_release_published_at": "2026-06-06T23:57:20Z",
        "skills_release": "v1.0.0",
        "intake_doc_ref": "docs/runtime/designs/evo_scientist_progress_first_intake.md",
        "dependency_introduced": False,
    }

    absorbed = {pattern["pattern_id"]: pattern for pattern in projection["absorbed_patterns"]}
    assert set(absorbed) == {
        "auxiliary_background_model",
        "fire_and_forget_observation_memory",
        "conditional_tool_selection",
        "skill_routing_eval",
        "ive_failed_path_memory_taxonomy",
        "attempt_budget_stop_loss",
    }
    assert absorbed["auxiliary_background_model"]["classification"] == "adopt_contract"
    assert absorbed["auxiliary_background_model"]["authority"] == "advisory_background_only"
    assert absorbed["fire_and_forget_observation_memory"]["authority"] == (
        "refs_only_memory_hint_until_mas_router_receipt"
    )
    assert absorbed["conditional_tool_selection"]["authority"] == "fail_open_tool_visibility"
    assert absorbed["skill_routing_eval"]["authority"] == "meta_release_gate_only"
    assert absorbed["attempt_budget_stop_loss"]["authority"] == "route_hint_not_attempt_hard_stop"

    boundary = projection["ordinary_progress_boundary"]
    assert boundary["ordinary_progress_spine"] == [
        "current_owner_delta",
        "concrete_delta",
        "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
        "next_current_owner_delta",
    ]
    assert boundary["can_block_current_owner_action"] is False
    assert boundary["critical_path_waits_for_sidecar"] is False
    assert boundary["can_require_full_research_lifecycle_preflight"] is False
    assert boundary["can_require_full_readiness_inventory"] is False
    assert boundary["missing_learning_sidecar_blocks_dispatch"] is False


def test_evo_scientist_learning_projection_lands_complete_target_sidecar_architecture() -> None:
    module = importlib.import_module("med_autoscience.evo_scientist_learning_projection")

    projection = module.build_evo_scientist_learning_projection()
    architecture = projection["target_sidecar_execution_architecture"]

    assert architecture["surface_kind"] == (
        "mas_evo_scientist_target_sidecar_execution_architecture"
    )
    assert architecture["architecture_state"] == "repo_callable_worker_landed"
    assert architecture["remaining_learning_plan"] is False
    assert architecture["future_work_role"] == "implementation_scaleout_under_this_contract_only"
    assert architecture["execution_model"] == "nonblocking_current_owner_following_sidecar"
    assert architecture["ordinary_progress_critical_path"] == [
        "current_owner_delta",
        "concrete_delta",
        "ProgressDeltaReceipt_or_OwnerReceipt_or_TypedBlocker",
        "next_current_owner_delta",
    ]
    assert architecture["sidecar_launch_points"] == [
        "after_current_owner_delta_materialized",
        "after_tool_surface_hydrated",
        "after_executor_turn_or_subagent_completion",
        "after_receipt_or_typed_blocker_recorded",
    ]
    assert set(architecture["sidecar_outputs"]) == {
        "tool_affordance_ref",
        "observation_memory_ref",
        "failed_path_memory_ref",
        "reviewer_briefing_ref",
        "route_hint_ref",
        "stop_loss_candidate_ref",
    }

    scheduling = architecture["scheduling_contract"]
    assert scheduling["owner"] == "one-person-lab"
    assert scheduling["mas_role"] == "declare_domain_boundaries_and_accept_refs_only_candidates"
    assert scheduling["runs_parallel_to_ordinary_progress"] is True
    assert scheduling["mainline_waits_for_sidecar"] is False
    assert scheduling["sidecar_failure_policy"] == (
        "drop_sidecar_ref_and_continue_current_owner_action"
    )
    assert scheduling["sidecar_timeout_policy"] == (
        "record_diagnostic_if_available_and_continue"
    )
    assert scheduling["sidecar_conflict_policy"] == "owner_policy_wins"

    budget = architecture["budget_contract"]
    assert budget["budget_exhaustion_policy"] == "stop_sidecar_not_owner_action"
    assert budget["sidecar_retry_policy"] == "bounded_retry_or_skip"
    assert budget["budget_exhaustion_can_emit_typed_blocker"] is False

    admission = architecture["admission_contract"]
    assert admission["sidecar_completion_required_for_dispatch"] is False
    assert admission["sidecar_completion_required_for_stage_transition"] is False
    assert admission["sidecar_completion_required_for_quality_gate"] is False
    assert admission["sidecar_completion_required_for_artifact_mutation"] is False
    assert admission["sidecar_may_submit_hard_gate_candidate_ref"] is True
    assert admission["hard_gate_candidate_requires_owner_or_reviewer_materialization"] is True

    slots = {slot["slot"]: slot for slot in architecture["implementation_slots"]}
    assert set(slots) == {
        "tool_selector_helper",
        "observation_memory_sidecar",
        "failed_path_taxonomy",
        "routing_eval",
        "attempt_budget_stop_loss",
    }
    assert all(
        slot["status"] == "repo_callable_sidecar_output_ref_landed"
        for slot in slots.values()
    )
    assert slots["tool_selector_helper"]["failure_policy"] == "fail_open_to_owner_required_tools"
    assert slots["observation_memory_sidecar"]["failure_policy"] == (
        "fire_and_forget_no_mainline_wait"
    )
    assert slots["routing_eval"]["failure_policy"] == "meta_gate_only_not_live_delta_gate"

    runtime_surface = projection["runtime_sidecar_execution_surface"]
    assert runtime_surface["surface_kind"] == "mas_evo_scientist_runtime_sidecar_execution_surface"
    assert runtime_surface["implementation_status"] == "repo_callable_worker_landed"
    assert runtime_surface["execution_model"] == "nonblocking_refs_only_sidecar_writer"
    assert runtime_surface["writer_ref"] == (
        "med_autoscience.runtime_protocol.evo_scientist_sidecar_refs."
        "write_evo_scientist_sidecar_observation"
    )
    assert runtime_surface["runtime_ref_root"] == "artifacts/runtime/evo_scientist_sidecar"
    assert runtime_surface["latest_ref"] == "artifacts/runtime/evo_scientist_sidecar/latest.json"
    assert runtime_surface["refs_only_state_index_family"] == "evo_scientist_sidecar_ref"
    assert set(runtime_surface["implemented_outputs"]) == {
        "tool_affordance_ref",
        "observation_memory_ref",
        "failed_path_memory_ref",
        "reviewer_briefing_ref",
        "route_hint_ref",
        "stop_loss_candidate_ref",
    }
    assert runtime_surface["nonblocking_contract"]["mainline_waits_for_sidecar"] is False
    assert runtime_surface["nonblocking_contract"]["failure_blocks_current_owner_action"] is False
    assert runtime_surface["authority_boundary"]["can_write_publication_eval"] is False
    assert runtime_surface["authority_boundary"]["can_write_controller_decisions"] is False
    assert runtime_surface["authority_boundary"]["can_write_owner_receipt"] is False
    assert runtime_surface["authority_boundary"]["can_write_typed_blocker"] is False


def test_evo_scientist_learning_projection_fails_open_and_preserves_authority() -> None:
    module = importlib.import_module("med_autoscience.evo_scientist_learning_projection")

    projection = module.build_evo_scientist_learning_projection()

    helper = projection["auxiliary_helper_contract"]
    assert "tool_selection_advisory" in helper["allowed_roles"]
    assert "owner_receipt_signer" in helper["forbidden_roles"]
    assert helper["main_agent_keeps_reasoning_authority"] is True
    assert helper["fallback_to_main_model_or_no_helper"] is True

    selector = projection["tool_selector_contract"]
    assert selector["fail_open_to_all_tools"] is True
    assert selector["selector_failure_is_not_task_failure"] is True
    assert selector["owner_required_tools_always_include"] is True
    assert selector["can_hide_current_owner_required_tool"] is False
    assert selector["can_authorize_or_deny_owner_action"] is False

    memory = projection["observation_memory_contract"]
    assert memory["mainline_waits_for_memory_worker"] is False
    assert memory["writeback_requires_router_receipt"] is True
    assert memory["can_write_domain_truth"] is False
    assert memory["can_authorize_quality_verdict"] is False
    assert memory["memory_refs_can_close_current_stage"] is False

    failed_path = projection["failed_path_memory_contract"]
    assert failed_path["fundamental_failure_requires_reviewer_or_owner_evidence"] is True
    assert failed_path["implementation_failure_stays_retryable"] is True
    assert failed_path["can_prune_current_owner_action_without_receipt"] is False
    assert failed_path["can_replace_publication_eval"] is False

    assert {pattern["pattern_id"] for pattern in projection["watch_only_patterns"]} == {
        "idea_tournament_as_default_gate",
        "full_research_lifecycle_pipeline_as_mas_default",
    }
    assert set(projection["rejected_patterns"]) >= {
        "external_deepagents_runtime_as_mas_runtime",
        "tool_selector_as_hard_gate",
        "self_review_as_independent_quality_gate",
        "full_evoskills_pipeline_as_live_preflight",
    }

    authority = projection["authority_boundary"]
    assert authority["source_project_role"] == "external_pattern_source_only"
    assert authority["can_write_domain_truth"] is False
    assert authority["can_write_evidence_ledger"] is False
    assert authority["can_write_review_ledger"] is False
    assert authority["can_authorize_publication_quality"] is False
    assert authority["can_authorize_artifact_authority"] is False
    assert authority["can_close_stage"] is False


def test_evo_scientist_progress_accelerator_contract_matches_projection_boundary() -> None:
    module = importlib.import_module("med_autoscience.evo_scientist_learning_projection")

    projection = module.build_evo_scientist_learning_projection()
    contract = json.loads(
        (REPO_ROOT / "contracts" / "evo_scientist_progress_accelerator.json").read_text(
            encoding="utf-8"
        )
    )

    assert contract["surface_kind"] == "mas_evo_scientist_progress_accelerator"
    assert contract["version"] == "evo-scientist-progress-accelerator.v1"
    assert contract["role"] == "advisory_progress_accelerator_not_control_surface"
    assert contract["projection_builder_ref"] == projection["projection_builder_ref"]
    assert projection["progress_accelerator_contract_ref"] == (
        "contracts/evo_scientist_progress_accelerator.json"
    )
    assert contract["ordinary_progress_policy"]["ordinary_progress_spine"] == projection[
        "ordinary_progress_boundary"
    ]["ordinary_progress_spine"]
    assert contract["ordinary_progress_policy"]["can_block_current_owner_action"] is False
    assert contract["ordinary_progress_policy"]["critical_path_waits_for_sidecar"] is False
    assert contract["ordinary_progress_policy"]["missing_learning_sidecar_blocks_dispatch"] is False
    assert contract["target_sidecar_execution_architecture"]["architecture_state"] == (
        projection["target_sidecar_execution_architecture"]["architecture_state"]
    )
    assert contract["target_sidecar_execution_architecture"]["remaining_learning_plan"] is False
    assert contract["target_sidecar_execution_architecture"][
        "future_work_role"
    ] == "implementation_scaleout_under_this_contract_only"
    assert contract["target_sidecar_execution_architecture"]["scheduling_contract"][
        "mainline_waits_for_sidecar"
    ] is False
    assert contract["target_sidecar_execution_architecture"]["admission_contract"][
        "sidecar_completion_required_for_dispatch"
    ] is False
    assert contract["target_sidecar_execution_architecture"]["admission_contract"][
        "sidecar_completion_required_for_quality_gate"
    ] is False
    assert contract["runtime_sidecar_execution_surface"] == projection[
        "runtime_sidecar_execution_surface"
    ]
    assert contract["tool_selector_policy"]["fail_open_to_all_tools"] is True
    assert contract["tool_selector_policy"]["owner_required_tools_always_include"] is True
    assert contract["observation_memory_policy"]["mainline_waits_for_memory_worker"] is False
    assert contract["failed_path_memory_policy"][
        "fundamental_failure_requires_reviewer_or_owner_evidence"
    ] is True
    assert contract["tournament_ranking_policy"][
        "tournament_or_ranking_can_become_hard_gate"
    ] is False
    assert contract["quality_gate_policy"]["self_review_closes_quality_gate"] is False
    assert contract["authority_boundary"]["can_write_domain_truth"] is False
    assert contract["authority_boundary"]["can_close_stage"] is False
    assert set(contract["rejected_patterns"]) >= {
        "auxiliary_model_as_mas_owner",
        "tool_selector_as_owner_required_tool_filter",
        "observation_memory_as_domain_truth",
        "ide_ive_ese_as_current_owner_action_gate",
        "tournament_or_ranking_as_hard_gate",
        "self_review_as_independent_quality_gate",
        "full_evoskills_pipeline_as_live_preflight",
    }
