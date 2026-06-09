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
    assert boundary["can_require_full_research_lifecycle_preflight"] is False
    assert boundary["can_require_full_readiness_inventory"] is False
    assert boundary["missing_learning_sidecar_blocks_dispatch"] is False


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
    assert contract["ordinary_progress_policy"]["missing_learning_sidecar_blocks_dispatch"] is False
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
