from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from med_autoscience.action_catalog import build_mas_action_catalog
from med_autoscience.agent_tool_arsenal.runtime_boundary import (
    opl_capability_runtime_boundary,
)
from med_autoscience.opl_domain_pack.agent_pack_refs import (
    AGENT_PROMPT_REFS,
)
from med_autoscience.opl_domain_pack.family_adoption import (
    build_family_stage_control_plane,
)
from med_autoscience.opl_standard_pack import build_standard_pack
from tests.standard_agent_purity_helpers import assert_standard_agent_purity_boundary


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
LIGHT_EXTERNAL_PATTERN_INTAKE_STAGE_IDS = {
    "direction_and_route_selection",
    "manuscript_authoring",
    "review_and_quality_gate",
    "finalize_and_publication_handoff",
}


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


def _assert_root_contract_matches_generated(
    generated: dict[str, object],
    contract_name: str,
) -> None:
    json_ready_generated = json.loads(json.dumps(generated[contract_name], ensure_ascii=False))
    assert _read_contract(contract_name) == json_ready_generated


def _assert_pack_path_is_real(path: str) -> None:
    resolved = REPO_ROOT / path
    assert resolved.exists(), path
    assert resolved.is_file(), path
    text = resolved.read_text(encoding="utf-8").strip()
    assert text, path
    forbidden = {"TODO", "TBD"}
    assert not any(token in text for token in forbidden), path


def test_opl_standard_pack_root_contracts_match_mas_canonical_metadata() -> None:
    generated = build_standard_pack()
    action_catalog = build_mas_action_catalog()
    stage_plane = build_family_stage_control_plane(family_action_catalog=action_catalog)

    _assert_root_contract_matches_generated(generated, "domain_descriptor")
    _assert_root_contract_matches_generated(generated, "action_catalog")
    _assert_root_contract_matches_generated(generated, "pack_compiler_input")
    _assert_root_contract_matches_generated(generated, "stage_control_plane")
    _assert_root_contract_matches_generated(generated, "foundry_agent_series")
    _assert_root_contract_matches_generated(generated, "generated_surface_handoff")
    _assert_root_contract_matches_generated(generated, "functional_privatization_audit")
    _assert_root_contract_matches_generated(generated, "agent_tool_arsenal")
    _assert_root_contract_matches_generated(generated, "hosted_ordinary_path_consumption")

    assert generated["action_catalog"]["actions"] == action_catalog["actions"]
    assert generated["agent_tool_arsenal"]["tool_index_refs"]["action_catalog"] == (
        "contracts/action_catalog.json"
    )
    assert generated["agent_tool_arsenal"]["authority_boundary"] == {
        "mas_owns_domain_truth_and_authority_functions": True,
        "opl_owns_generated_descriptor_projection": True,
        **opl_capability_runtime_boundary(),
        "capability_or_sidecar_can_be_admission_gate": False,
        "missing_capability_blocks_owner_action": False,
        "failed_capability_blocks_owner_action": False,
        "low_confidence_capability_blocks_owner_action": False,
        "sidecar_completion_required_for_stage_closeout": False,
        "tool_arsenal_can_write_domain_truth": False,
        "tool_arsenal_can_authorize_quality_or_export": False,
        "human_operator_manual_composition_required": False,
    }
    assert generated["stage_control_plane"]["stages"] == stage_plane["stages"]
    assert generated["pack_compiler_input"]["generated_surface_owner"] == "one-person-lab"
    assert generated["pack_compiler_input"]["canonical_semantic_pack_root"] == "agent/"
    assert generated["pack_compiler_input"]["canonical_semantic_pack_role"] == (
        "declarative_medical_research_semantics_for_opl_pack_compiler"
    )
    foundry_series = generated["foundry_agent_series"]
    assert foundry_series["surface_kind"] == "opl_foundry_agent_series_contract"
    assert foundry_series["version"] == "foundry-agent-series.v1"
    assert foundry_series["product_layer"] == "foundry_agent"
    assert foundry_series["domain_id"] == "medautoscience"
    assert foundry_series["stage_control_plane_target_domain_id"] == "med-autoscience"
    assert foundry_series["contract_version_policy"] == {
        "current_version": "foundry-agent-series.v1",
        "domain_contract_ref": "contracts/foundry_agent_series.json",
        "exact_version_pin_required": True,
        "compatible_version_range": ["foundry-agent-series.v1"],
        "breaking_change_requires_new_version": True,
        "domain_descriptor_must_reference_domain_contract": True,
    }
    assert foundry_series["shared_release_pin_strategy"] == {
        "owner_release_contract_ref": "contracts/family-release/shared-owner-release.json",
        "owner_commit_pin_required": True,
        "owner_commit_pin": "3a3aaddd0a3e980f86e762ca1ed942bbda6f30d7",
        "domain_dependency_pin_required": True,
        "supported_pin_sources": ["pyproject.toml", "uv.lock"],
        "consumer_alignment_check": "family:shared-release",
        "domain_contract_version_pin_does_not_authorize_domain_truth": True,
    }
    assert foundry_series["shared_policy_release"] == {
        "policy_release_contract_ref": (
            "contracts/opl-framework/foundry-agent-series-policy-release.json"
        ),
        "policy_bundle_fingerprint": (
            "sha256:503f515e8fa08b3f81ce28cac461368c609d4565de239c9f95c3f910cb758ed5"
        ),
        "fingerprint_algorithm": "sha256:stable-json",
        "domain_contract_policy_release_pin_required": True,
        "domain_adapter_must_not_copy_policy_body_as_authority": True,
        "consumer_alignment_check": "foundry:policy-release",
    }
    assert foundry_series["agent_membership_projection_policy"] == {
        "surface_kind": "opl_foundry_agent_membership_projection_policy",
        "version": "foundry-agent-membership-projection.v1",
        "policy_id": "standard_agent_membership_not_surface_origin",
        "default_membership": "standard_domain_agent",
        "public_agent_list_must_not_split_by_generated_surface": True,
        "public_agent_list_must_not_split_by_plugin_transport": True,
        "generated_surface_is_membership_axis": False,
        "generated_surface_is_status_axis": False,
        "plugin_transport_is_membership_axis": False,
        "plugin_transport_is_status_axis": False,
        "generated_surface_only_field_public_default": False,
    }
    assert foundry_series["standard_feedback_self_evolution_trigger_policy"] == {
        "surface_kind": "opl_foundry_agent_standard_feedback_self_evolution_trigger_policy",
        "version": "foundry-agent-feedback-self-evolution-trigger.v1",
        "policy_id": "standard_agent_feedback_self_evolution_trigger.v1",
        "applies_to_series_memberships": [
            "standard_domain_agent",
            "framework_capability_package",
        ],
        "feedbackops_event_kind": "target_agent_feedback_external_suite",
        "accepted_feedback_profile": "target_agent_feedback_external_suite",
        "must_follow_target_domain_mainline": True,
        "must_not_compete_with_target_domain_mainline": True,
        "target_domain_terminal_route": "owner_gate_or_typed_blocker",
        "trigger_chain": [
            "domain_or_package_thin_feedback_adapter",
            "opl_feedbackops_agent_lab_status_projection",
            "opl_meta_agent_oma_agent_evolution_work_order",
            "developer_mode_direct_fix_or_fork_pr_route",
            "target_owner_closeout_readback",
        ],
        "required_trigger_fields": [
            "feedbackops_event_kind",
            "accepted_feedback_profile",
            "target_agent_id",
            "idempotency_key",
            "external_suite_ref",
            "developer_mode_execution_gate_refs",
            "oma_evolution_skill_ref",
            "owner_closeout_readback_refs",
        ],
        "standard_status_projection_ref": (
            "contracts/opl-framework/agent-lab-contract.json#/"
            "domain_feedback_self_evolution_surface"
        ),
        "feedback_capture_requires_developer_mode": False,
        "repo_fix_execution_requires_opl_developer_mode": True,
        "contract_can_trigger_execution": False,
        "developer_mode_execution_gate_refs": [
            "opl-developer-mode:repo-fix-execution",
            "opl-developer-mode:direct-fix-or-fork-pr-route",
        ],
        "developer_route_policy": {
            "feedback_capture_route": "allowed_for_all_users_refs_only",
            "direct_fix_route": (
                "requires_target_repo_direct_write_authority_or_"
                "agent_owner_developer_authority"
            ),
            "manual_enable_without_direct_write_route": "fork_pull_request",
            "official_or_third_party_agent_without_authority_route": (
                "fork_pull_request_or_owner_handoff"
            ),
            "manual_developer_mode_cannot_grant_direct_repo_write": True,
            "auto_developer_mode_can_select_local_checkout_source_when_identity_matches": True,
        },
        "authority_boundary": {
            "refs_only": True,
            "can_write_domain_truth": False,
            "can_mutate_artifact_body": False,
            "can_authorize_quality_or_export": False,
            "can_create_owner_receipt": False,
            "can_create_typed_blocker": False,
            "can_execute_repo_patch_without_developer_mode": False,
        },
    }
    assert generated["domain_descriptor"]["standard_contract_refs"][
        "foundry_agent_series_policy_release"
    ] == "contracts/opl-framework/foundry-agent-series-policy-release.json"
    assert generated["domain_descriptor"]["standard_contract_refs"][
        "hosted_ordinary_path_consumption"
    ] == "contracts/hosted_ordinary_path_consumption.json"
    hosted_consumption = generated["hosted_ordinary_path_consumption"]
    assert hosted_consumption["surface_kind"] == (
        "mas_hosted_ordinary_path_consumption_contract"
    )
    assert hosted_consumption["planning_root"] == "current_owner_delta"
    assert hosted_consumption["required_consumed_surfaces"] == [
        "agent_execution_index",
        "operational_tool_card",
        "capability_invocation_plan",
        "tool_result_envelope_recovery",
        "scientific_capability_resolution",
        "owner_consumption_evidence_packet",
    ]
    assert hosted_consumption["friction_policy"][
        "human_operator_manual_tool_selection_required"
    ] is False
    assert hosted_consumption["friction_policy"]["docker_or_dind_required"] is False
    assert hosted_consumption["authority_boundary"][
        "evidence_packet_can_claim_paper_progress"
    ] is False
    series_profile = foundry_series["series_design_profile"]
    assert series_profile["surface_kind"] == "opl_foundry_agent_series_design_profile"
    assert series_profile["profile_id"] == "opl_foundry_agent_series_design_profile.v1"
    assert series_profile["shared_lifecycle_pipeline"] == [
        "domain_material_intake",
        "domain_pack_interpretation",
        "stage_led_agent_execution",
        "independent_quality_gate_or_owner_review",
        "owner_receipt_or_typed_blocker_closeout",
        "artifact_or_deliverable_handoff",
        "opl_refs_only_projection_and_recovery",
    ]
    assert series_profile["domain_io_profile"]["input_slot"] == (
        "domain_materials_or_task_request"
    )
    assert series_profile["domain_io_profile"]["output_slot"] == (
        "domain_deliverable_or_owner_handoff"
    )
    assert series_profile["stage_pack_sections"] == [
        "prompts",
        "stages",
        "stage_completion_policy",
        "skills",
        "tools",
        "knowledge",
        "quality_gates",
    ]
    assert series_profile["shared_closeout_contract"]["success_shape"] == (
        "domain_owner_receipt_ref"
    )
    assert series_profile["shared_closeout_contract"]["blocked_shape"] == (
        "domain_owned_typed_blocker_ref"
    )
    assert series_profile["shared_closeout_contract"][
        "provider_completion_is_closeout"
    ] is False
    assert series_profile["authority_invariants"] == {
        "opl_can_infer_domain_output": False,
        "opl_can_read_domain_body": False,
        "opl_can_write_domain_truth": False,
        "opl_can_authorize_quality_or_export": False,
        "domain_owns_input_truth_and_output_authority": True,
    }
    workspace_topology = foundry_series["workspace_topology_profile"]
    assert workspace_topology["surface_kind"] == "opl_workspace_topology_profile"
    assert workspace_topology["profile_id"] == "opl.workspace_topology_profile.v1"
    assert workspace_topology["topology_model"] == [
        "workspace_group",
        "project_unit",
        "stage_artifact_unit",
        "owner_receipt_or_typed_blocker",
    ]
    assert workspace_topology["workspace_modes"] == ["one_off", "series", "portfolio"]
    assert workspace_topology["default_profiles"]["one_off"][
        "project_collection_path"
    ] == "projects"
    assert workspace_topology["default_profiles"]["series"][
        "project_collection_path"
    ] == "projects"
    assert workspace_topology["default_profiles"]["portfolio"][
        "project_collection_path"
    ] == "projects"
    assert workspace_topology["default_profiles"]["portfolio"][
        "project_stage_outputs_root"
    ] == "artifacts/stage_outputs"
    assert workspace_topology["default_profiles"]["mas_portfolio"][
        "canonical_profile_id"
    ] == "portfolio"
    assert workspace_topology["default_profiles"]["rca_series"][
        "canonical_profile_id"
    ] == "series"
    assert workspace_topology["workspace_initialization_policy"][
        "default_project_collection_path"
    ] == "projects"
    assert workspace_topology["workspace_initialization_policy"][
        "legacy_project_collection_aliases"
    ] == ["deliverables", "studies"]
    assert "one_off_still_uses_project_collection_path" not in workspace_topology[
        "workspace_initialization_policy"
    ]
    assert workspace_topology["domain_profile_defaults"]["mas"] == "portfolio"
    assert workspace_topology["domain_profile_defaults"]["rca"] == "series"
    assert workspace_topology["legacy_domain_profile_aliases"]["mas_portfolio"][
        "canonical_profile_id"
    ] == "portfolio"
    assert workspace_topology["default_user_inspection_surface"][
        "ordinary_user_default_surface"
    ] == "workspace_local_project_stage_outputs"
    assert workspace_topology["runtime_state_boundary"][
        "runtime_state_can_close_stage"
    ] is False
    assert workspace_topology["authority_boundary"]["opl_can_write_domain_truth"] is False
    domain_profile = foundry_series["domain_specific_profile"]
    assert domain_profile["shared_agent_logic"] == (
        "same_opl_foundry_agent_lifecycle_with_domain_specific_medical_research_inputs_"
        "and_manuscript_outputs"
    )
    assert "disease_specific_study_question" in domain_profile["domain_input_taxonomy"]
    assert "research_evidence_pack_refs" in domain_profile["domain_output_taxonomy"]
    assert domain_profile["authority_invariants"] == {
        "opl_role": "refs_projection_runtime_lifecycle_and_generated_surface_owner",
        "mas_role": (
            "study_truth_publication_quality_artifact_authority_memory_authority_"
            "and_owner_receipt_owner"
        ),
        "opl_can_write_study_truth": False,
        "opl_can_claim_publication_quality": False,
        "opl_can_authorize_artifact_mutation": False,
        "opl_can_accept_or_reject_memory_body": False,
        "mas_owner_receipt_required_for_domain_closeout": True,
    }
    assert domain_profile["progress_currentness_closeout_packets"] == (
        foundry_series["required_stage_packets"]
    )
    assert "stage_packet_hydration" in domain_profile["shared_lifecycle_pipeline"]
    assert "quality_gates" in series_profile["stage_pack_sections"]
    assert foundry_series["domain_progress_aliases"]["deliverable"] == [
        "paper_progress_delta",
        "paper_work_progress",
    ]
    public_projection_policy = foundry_series["standard_public_projection_policy"]
    assert public_projection_policy["surface_kind"] == (
        "opl_foundry_agent_standard_public_projection_policy"
    )
    assert public_projection_policy["standard_public_foundry_surface"] == (
        "opl_generated_hosted_series"
    )
    assert public_projection_policy["canonical_inspect_command_pattern"] == (
        "opl foundry agents inspect <agent_id>"
    )
    assert public_projection_policy["allowed_active_public_foundry_surfaces"] == [
        "opl_foundry_agent_series_spine",
        "opl_family_hosted_surfaces",
    ]
    assert (
        public_projection_policy[
            "active_public_projection_allows_domain_owned_cli_as_standard_surface"
        ]
        is False
    )
    assert (
        public_projection_policy["active_public_projection_allows_compatibility_aliases"]
        is False
    )
    assert (
        public_projection_policy["minimal_authority_functions_are_membership_axis"]
        is False
    )
    assert (
        public_projection_policy["domain_owned_helpers_are_membership_axis"]
        is False
    )
    assert public_projection_policy["allowed_domain_owned_helper_context"] == (
        "minimal_authority_functions_only"
    )
    assert public_projection_policy["non_standard_surface_retention_contexts"] == [
        "history",
        "tombstone",
    ]
    assert foundry_series["domain_adapter_policy"]["no_parallel_progress_schema"] is True
    assert foundry_series["domain_adapter_policy"]["no_parallel_blocker_lineage_schema"] is True
    non_advancing = foundry_series["mission_first_non_advancing_escalation_policy"]
    assert non_advancing["route_back_budget_policy"] == {
        "same_signature_repeat_threshold": 2,
        "ledger_scope": "cross_run_same_study_mission_signature",
        "after_threshold_next_owner": (
            "MedAutoScience.paper_mission_semantic_progress_executor"
        ),
        "after_threshold_action": (
            "mission_executor_continue_same_stage_until_semantic_delta_or_narrow_gate"
        ),
        "opl_redrive_after_worker_ready_allowed": False,
        "queue_or_worker_readiness_can_reset_budget": False,
        "transport_or_observability_fields_can_reset_budget": False,
        "budget_exhausted_can_claim_completion": False,
    }
    assert non_advancing["mas_mission_executor_fallback_projection"][
        "auto_continue_after_synonymous_budget"
    ] is True
    assert {
        "owner_decision_packet_ref",
        "claim_decision_ref",
        "scope_decision_ref",
        "evidence_decision_ref",
        "pivot_decision_ref",
        "carry_forward_decision_ref",
        "mission_executor_continuation_ref",
    } <= set(
        non_advancing["mas_mission_executor_fallback_projection"][
            "required_product_refs"
        ]
    )
    assert non_advancing["ai_owner_decision_product_refs_projection"] == {
        "domain_policy_section_ref": (
            "contracts/mas-paper-study-stage-pack.json"
            "#/mission_first_non_advancing_route_back_policy/"
            "ai_owner_decision_product_refs"
        ),
        "ref_families": [
            "claim_decision_ref",
            "scope_decision_ref",
            "evidence_decision_ref",
            "pivot_decision_ref",
            "carry_forward_decision_ref",
        ],
        "can_authorize_submission_or_publication_ready": False,
        "can_replace_owner_receipt_or_quality_gate": False,
    }
    assert non_advancing["dm002_dm003_canary_acceptance_projection"] == {
        "domain_policy_section_ref": (
            "contracts/mas-paper-study-stage-pack.json"
            "#/mission_first_non_advancing_route_back_policy/"
            "dm002_dm003_canary_acceptance"
        ),
        "success_requires_fresh_readback": True,
        "contract_or_tests_only_can_pass": False,
        "stale_opl_running_row_can_count_as_running_proof": False,
    }
    assert (
        non_advancing["authority_boundary"][
            "opl_can_reset_synonymous_route_back_budget_from_transport"
        ]
        is False
    )
    thinning = foundry_series["purpose_first_adapter_thinning_policy"]
    assert thinning["default_retained_surface_roles"] == [
        "refs_only_adapter",
        "domain_handler_target",
        "minimal_authority_function",
        "migration_input",
        "history_or_tombstone_provenance",
    ]
    assert thinning["default_operator_delta_shape"] == (
        "paper_progress_delta_or_mas_owned_typed_blocker"
    )
    assert thinning["physical_delete_required_gates"] == [
        "replacement_parity",
        "no_active_caller",
        "owner_receipt_or_typed_blocker",
        "no_forbidden_write",
        "tombstone_or_provenance",
    ]
    assert (
        thinning["evidence_tail_boundary"][
            "platform_repair_or_read_model_currentness_is_paper_progress"
        ]
        is False
    )
    assert (
        thinning["evidence_tail_boundary"][
            "missing_paper_research_human_gate_returns"
        ]
        == "mas_owned_typed_blocker"
    )
    assert (
        foundry_series["app_projection_policy"]["app_consumes_shared_progress_projection_only"]
        is True
    )
    assert foundry_series["authority_boundary"]["opl_owns_series_contract"] is True
    assert generated["pack_compiler_input"]["src_role"] == (
        "domain_handler_minimal_authority_functions_and_native_helpers_only"
    )
    assert generated["pack_compiler_input"]["src_must_not_be_canonical_semantic_pack"] is True
    required_paths = generated["pack_compiler_input"]["required_domain_pack_paths"]
    assert "agent/stages/stage_route_contract.yaml" in required_paths
    assert "agent/stages/stage_native_semantic_pack.yaml" in required_paths
    assert "agent/knowledge/hypothesis_portfolio_evidence_pack.md" in required_paths
    assert set(AGENT_PROMPT_REFS.values()) <= set(required_paths)
    assert all(str(path).startswith("agent/") for path in required_paths)
    for path in required_paths:
        _assert_pack_path_is_real(str(path))
    assert generated["pack_compiler_input"]["minimal_authority_semantic_model"] == (
        "ai_first_stage_quality_gate_boundaries_not_script_function_verdicts"
    )
    assert generated["pack_compiler_input"]["allowed_judgment_modes"] == [
        "ai_first_stage_gate",
        "ai_first_record_validator",
        "mechanical_guard",
    ]
    assert generated["pack_compiler_input"]["verdict_function_model_retired"] is True
    assert generated["pack_compiler_input"]["gate_validator_ref"] == (
        "src/med_autoscience/controllers/ai_first_private_authority.py::"
        "validate_ai_first_private_authority_gate"
    )
    assert generated["pack_compiler_input"]["runtime_enforcement_status"] == (
        "contract_validator_landed"
    )
    assert generated["pack_compiler_input"]["program_output_policy"] == (
        "programs_validate_ai_first_stage_gate_records_and_emit_receipts_or_typed_blockers_only"
    )
    assert generated["pack_compiler_input"]["ai_first_stage_gate_function_ids"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
    ]
    assert generated["pack_compiler_input"]["ai_first_record_validator_function_ids"] == [
        "artifact_mutation_authorization"
    ]
    assert generated["pack_compiler_input"]["mechanical_guard_function_ids"] == [
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert generated["pack_compiler_input"]["minimal_authority_functions"][:5] == [
        "publication_quality_stage_gate_boundary",
        "ai_reviewer_quality_stage_gate_boundary",
        "artifact_mutation_stage_gate_boundary",
        "publication_route_memory_accept_reject_stage_gate_boundary",
        "source_readiness_stage_gate_boundary",
    ]
    assert generated["pack_compiler_input"]["requires_ai_first_record"] is True
    hypothesis_pack = generated["pack_compiler_input"][
        "hypothesis_portfolio_evidence_pack_contract"
    ]
    assert hypothesis_pack["owner"] == "MedAutoScience"
    assert hypothesis_pack["knowledge_ref"] == (
        "agent/knowledge/hypothesis_portfolio_evidence_pack.md"
    )
    assert {
        "hypothesis_candidate_ref",
        "assumption_ref",
        "sub_assumption_ref",
        "supporting_evidence_ref",
        "contradicting_evidence_ref",
        "novelty_ref",
        "source_provenance_ref",
        "testability_ref",
        "safety_risk_ref",
        "negative_failed_path_ref",
        "independent_reviewer_or_auditor_receipt_ref",
        "human_gate_receipt_ref",
    } <= set(hypothesis_pack["candidate_required_ref_families"])
    assert {"ranking_ref", "proximity_ref"} <= set(hypothesis_pack["advisory_ref_families"])
    assert hypothesis_pack["validator_ref"] == (
        "src/med_autoscience/opl_domain_pack/hypothesis_portfolio_pack.py::"
        "validate_hypothesis_portfolio_candidate_refs"
    )
    assert hypothesis_pack["candidate_promotion_requires_validator"] is True
    assert hypothesis_pack["advisory_refs_are_authority"] is False
    assert hypothesis_pack["candidate_validation_output_contract"] == {
        "success_status": "validated",
        "blocked_status": "typed_blocker",
        "can_promote_candidate_requires": "all_required_ref_families_present",
        "missing_required_ref_blocker_id": "missing_hypothesis_portfolio_ref_family",
        "route_back_owner_required_when_blocked": True,
    }
    assert hypothesis_pack["authority_boundary"]["ranking_and_proximity_authority"] == (
        "advisory_only"
    )
    assert hypothesis_pack["authority_boundary"]["opl_can_write_hypothesis_truth"] is False
    assert hypothesis_pack["authority_boundary"]["opl_can_authorize_route_by_ranking"] is False
    assert (
        hypothesis_pack["authority_boundary"]["opl_can_close_independent_review_gate"]
        is False
    )
    independent_policy = generated["pack_compiler_input"][
        "independent_executor_reviewer_agent_policy"
    ]
    assert independent_policy["required"] is True
    assert independent_policy["separate_invocation_required"] is True
    assert independent_policy["separate_context_record_required"] is True
    assert independent_policy["separate_task_record_required"] is True
    assert independent_policy["separate_receipt_required"] is True
    assert independent_policy["self_review_closes_quality_gate"] is False
    assert {
        item["program_role"]
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
    } == {"validator", "materializer", "guard"}
    assert {
        item["judgment_mode"]
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
    } == {"ai_first_stage_gate", "ai_first_record_validator"}
    assert all(
        item["program_may_emit_pass_ready_verdict"] is False
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
    )
    assert {
        key
        for item in generated["pack_compiler_input"]["stage_quality_gate_boundaries"]
        for key in item
    } == {
        "boundary_id",
        "program_role",
        "judgment_mode",
        "decision_output_owner",
        "program_may_emit_pass_ready_verdict",
        "requires_ai_first_record",
        "trace_refs",
        "required_record_refs",
        "route_back_semantics",
        "typed_blocker_semantics",
    }
    policy = generated["private_functional_surface_policy"]
    assert policy["allowed_private_surface_classes"] == [
        "ai_first_stage_quality_gate_boundary",
        "domain_native_helper_implementation",
        "owner_receipt_signer",
    ]
    assert "domain_truth_verdict_authorizer" not in policy["allowed_private_surface_classes"]
    assert not any(
        item.endswith("_authorizer") for item in policy["allowed_private_surface_classes"]
    )
    assert policy["forbidden_primary_allowed_private_surface_models"] == [
        "domain_truth_verdict_authorizer",
        "*_authorizer",
    ]
    assert policy["allowed_judgment_modes"] == generated["pack_compiler_input"][
        "allowed_judgment_modes"
    ]
    assert policy["verdict_function_model_retired"] is True
    assert policy["gate_validator_ref"] == generated["pack_compiler_input"]["gate_validator_ref"]
    assert policy["runtime_enforcement_status"] == generated["pack_compiler_input"][
        "runtime_enforcement_status"
    ]
    assert policy["program_output_policy"] == generated["pack_compiler_input"][
        "program_output_policy"
    ]
    assert policy["requires_ai_first_record"] is True
    assert policy["independent_executor_reviewer_agent_policy"] == independent_policy
    assert generated["generated_surface_handoff"]["domain_repo_can_own_generated_surface"] is False
    assert generated["generated_surface_handoff"]["consumes_agent_pack_refs"] is True
    assert generated["generated_surface_handoff"]["agent_pack_ref_source"] == (
        "contracts/pack_compiler_input.json#/required_domain_pack_paths"
    )
    handoff_policy = generated["generated_surface_handoff"]["generated_surface_policy"]
    assert handoff_policy["must_read_semantics_from"] == "agent/"
    assert "MAS study truth" in handoff_policy["must_not_write"]
    assert "publication verdict" in handoff_policy["must_not_write"]
    assert "current_package" in handoff_policy["must_not_write"]
    oma_handoff = generated["generated_surface_handoff"]["oma_agent_evidence_handoff"]
    assert oma_handoff["consumer_id"] == "opl-meta-agent.agent:evidence"
    assert oma_handoff["production_acceptance_ref"] == {
        "ref": "contracts/production_acceptance/mas-production-acceptance.json",
        "role": "mas_domain_owned_production_acceptance",
        "body_included": False,
    }
    assert oma_handoff["agent_lab_handoff_ref"]["ref"] == "contracts/agent_lab_handoff.json"
    assert oma_handoff["owner_receipt_authority_ref"]["ref"] == "contracts/owner_receipt_contract.json"
    assert oma_handoff["quality_authority_ref"]["role"] == "mas_quality_publication_authority"
    assert oma_handoff["artifact_authority_ref"]["ref"] == "contracts/artifact_locator_contract.json"
    assert oma_handoff["memory_authority_ref"]["ref"] == "contracts/memory_descriptor.json"
    assert {
        hint["ref"]
        for hint in oma_handoff["editable_surface_hints"]
    } >= {
        "agent/prompts",
        "agent/skills",
        "agent/knowledge",
        "agent/quality_gates",
        "contracts/generated_surface_handoff.json",
        "contracts/agent_lab_handoff.json",
    }
    assert all(hint["body_included"] is False for hint in oma_handoff["editable_surface_hints"])
    assert oma_handoff["consumer_policy"] == {
        "oma_may_consume_refs": True,
        "oma_may_emit_candidate_patch_work_order": True,
        "oma_may_sign_owner_receipt": False,
        "oma_may_write_quality_verdict": False,
        "oma_may_write_artifact_body": False,
        "oma_may_write_memory_body": False,
    }
    assert "skill" in generated["pack_compiler_input"]["generated_surfaces_requested"]
    assert generated["action_catalog"]["catalog_role"] == (
        "domain_action_intent_and_handler_target_input_for_opl_generated_descriptors"
    )


def test_opl_standard_pack_runtime_guard_stages_declare_runtime_event_refs() -> None:
    generated = build_standard_pack()

    for stage in generated["stage_control_plane"]["stages"]:
        launch_packet = stage["codex_cli_launch_packet"]
        assert launch_packet["surface_kind"] == "mas_codex_cli_stage_launch_packet"
        assert launch_packet["stage_id"] == stage["stage_id"]
        assert launch_packet["executor_requirements"] == "Codex CLI default"
        assert launch_packet["prompt_ref"] == stage["prompt_refs"][0]
        assert set(launch_packet["tool_refs"]["allowed_action_refs"]) == set(stage["allowed_action_refs"])
        assert launch_packet["skill_refs"] == stage["skills"]
        assert launch_packet["knowledge_refs"] == stage["knowledge_refs"]
        assert launch_packet["quality_gate_refs"] == stage["evaluation"]
        assert launch_packet["quality_pack_refs"] == stage["quality_pack_refs"]
        assert launch_packet["expected_receipt_refs"]["owner_receipt_contract_ref"] == (
            "/product_entry_manifest/owner_receipt_contract"
        )
        assert launch_packet["expected_receipt_refs"]["stage_status_ref"] == "/progress_projection"
        assert launch_packet["expected_receipt_refs"]["runtime_event_refs"] == (
            stage["stage_contract"]["runtime_event_refs"]
        )
        assert set(launch_packet["expected_receipt_refs"]["valid_outcomes"]) == {
            "owner_receipt",
            "typed_blocker",
            "route_back_request",
            "human_gate_request",
            "no_op_with_currentness_proof",
        }
        assert launch_packet["ai_first_boundary"]["contract_role"] == "boundary_and_evidence_refs_only"
        assert launch_packet["ai_first_boundary"]["script_verdict_authority"] is False
        assert launch_packet["ai_first_boundary"]["self_review_closes_quality_gate"] is False
        assert "quality_verdict" in launch_packet["forbidden_authority"]
        assert "publication_readiness" in launch_packet["forbidden_authority"]
        assert "script_exit_code_as_publication_quality_verdict" in launch_packet[
            "forbidden_authority"
        ]
        prompt_refs = stage["prompt_refs"]
        assert len(prompt_refs) == 1
        prompt_ref = prompt_refs[0]
        assert prompt_ref["role"] == "stage_prompt"
        assert prompt_ref["ref_kind"] == "repo_path"
        assert prompt_ref["ref"] == AGENT_PROMPT_REFS[stage["stage_id"]]
        assert str(prompt_ref["ref"]).startswith("agent/prompts/")
        _assert_pack_path_is_real(str(prompt_ref["ref"]))
        assert any(ref["role"] == "stage_domain_policy" for ref in stage["policy_refs"])
        assert any(ref["role"] == "stage_native_semantic_pack" for ref in stage["source_refs"])
        assert all(
            str(ref["ref"]).startswith("agent/") or ref["role"] in {"route_contract", "stage_led_policy"}
            for ref in stage["policy_refs"]
        )
        assert any(ref["role"] == "domain_pack_skill_policy" for ref in stage["skills"])
        assert any(ref["role"] == "domain_pack_knowledge" for ref in stage["knowledge_refs"])
        assert any(ref["role"] == "agent_quality_gate" for ref in stage["evaluation"])
        if not stage["trust_boundary"]["runtime_guard_required"]:
            continue
        refs = stage["trust_boundary"].get("runtime_event_refs")
        assert refs
        assert refs == stage["stage_contract"].get("runtime_event_refs")
        assert all(str(ref).startswith("runtime_event:") for ref in refs)
        assert stage["stage_contract"]["source_scope_refs"]
        assert stage["stage_contract"]["cohort_query_refs"]
        assert stage["stage_contract"]["trigger_refs"]
        assert stage["stage_contract"]["monitor_refs"]
        assert stage["stage_contract"]["dashboard_metric_refs"]
        assert any(ref["role"] == "opl_provider_stage_launch_trigger" for ref in stage["stage_contract"]["trigger_refs"])
        user_stage_log = stage["stage_contract"]["user_stage_log_contract"]
        assert user_stage_log["surface_kind"] == "opl_standard_agent_user_stage_log_contract"
        assert user_stage_log["standard_agent_requirement"] == (
            "domain_stage_closeout_must_return_user_readable_stage_semantics_or_typed_blocker"
        )
        assert user_stage_log["opl_projection_surface"] == "stage_progress_log.user_stage_log"
        assert set(user_stage_log["required_domain_semantic_fields"]) >= {
            "problem_summary",
            "stage_work_done",
            "changed_stage_surfaces",
            "remaining_blockers",
        }
        assert set(user_stage_log["required_observability_fields"]) >= {"duration", "token_usage"}
        assert user_stage_log["mas_paper_alias_fields"] == {
            "stage_work_done_alias": "paper_work_done",
            "changed_stage_surfaces_alias": "changed_paper_surfaces",
        }
        assert user_stage_log["authority_boundary"]["opl_can_infer_domain_semantics"] is False
        assert user_stage_log["authority_boundary"]["mas_retains_publication_quality_authority"] is True
        stage_completion_policy = stage["stage_contract"]["stage_completion_policy"]
        assert stage_completion_policy["surface_kind"] == "domain_stage_completion_policy"
        assert stage_completion_policy["completion_judgment_owner"] == "domain_stage"
        assert stage_completion_policy["closeout_packet_required"] is True
        assert stage_completion_policy["provider_completion_is_domain_completion"] is False
        assert stage_completion_policy["opl_content_judgment_allowed"] is False
        assert stage_completion_policy["next_stage_transition_owner"] == "opl_runtime"
        assert set(stage_completion_policy["required_closeout_outcomes"]) >= {
            "completed_and_continue",
            "completed_and_wait_owner",
            "route_back",
            "blocked",
            "rejected",
        }
        assert set(stage_completion_policy["accepted_closeout_ref_fields"]) >= {
            "owner_receipt_ref",
            "typed_blocker_ref",
            "human_gate_ref",
            "route_back_ref",
        }
        assert stage_completion_policy["authority_boundary"] == {
            "opl_can_decide_domain_completion": False,
            "provider_completion_counts_as_stage_complete": False,
            "file_presence_counts_as_stage_complete": False,
            "suite_pass_counts_as_stage_complete": False,
            "conformance_pass_counts_as_stage_complete": False,
        }
        progress_delta_policy = stage["stage_contract"]["progress_delta_policy"]
        assert progress_delta_policy["surface_kind"] == "opl_stage_progress_delta_policy"
        assert set(progress_delta_policy["required_fields"]) >= {
            "progress_delta_classification",
            "deliverable_progress_delta",
            "platform_repair_delta",
            "next_forced_delta",
        }
        assert progress_delta_policy["platform_only_is_not_deliverable_progress"] is True
        assert progress_delta_policy["deliverable_delta_aliases"]["paper_progress_delta"] == (
            "deliverable_progress_delta"
        )
        typed_blocker_lineage_policy = stage["stage_contract"]["typed_blocker_lineage_policy"]
        assert typed_blocker_lineage_policy["surface_kind"] == "family-stall-lineage.v1"
        assert set(typed_blocker_lineage_policy["required_fields"]) >= {
            "blocker_family",
            "repeat_count",
            "next_forced_delta",
            "escalation_owner",
        }
        assert typed_blocker_lineage_policy["repeat_budget"] == {
            "mechanism_repair_after_repeat_count": 2,
            "human_gate_or_stop_loss_after_repeat_count": 3,
        }
        hypothesis_pack = stage["stage_contract"]["hypothesis_portfolio_evidence_pack"]
        assert hypothesis_pack["validator_ref"] == (
            "src/med_autoscience/opl_domain_pack/hypothesis_portfolio_pack.py::"
            "validate_hypothesis_portfolio_candidate_refs"
        )
        assert hypothesis_pack["candidate_promotion_requires_validator"] is True
        assert hypothesis_pack["advisory_refs_are_authority"] is False
        assert hypothesis_pack["ranking_and_proximity_authority"] == "advisory_only"
        assert hypothesis_pack["fail_closed_output_shape"] == {
            "status": "typed_blocker",
            "blocker_id": "missing_hypothesis_portfolio_ref_family",
            "route_back_owner": "required",
        }
    assert generated["action_catalog"]["descriptor_projection_owner"] == "one-person-lab"
    assert generated["action_catalog"]["domain_handler_target_owner"] == "MedAutoScience"
    assert generated["functional_privatization_audit"]["functional_followthrough_gap_summary"][
        "classification_gap_count"
    ] == 0
    followthrough = generated["functional_privatization_audit"]["functional_followthrough_gap_summary"]
    assert followthrough["functional_structure_gap_count"] == 0
    assert followthrough["remaining_gap_classification"] == "live_provider_paper_line_evidence_gates"
    assert followthrough["remaining_items_are_evidence_gates"] is True
    assert followthrough["remaining_functional_followthrough_gate_ids"] == []
    assert followthrough["closed_functional_structure_gate_ids"] == [
        "generated_surface_default_owner_cutover",
        "domain_authority_refs_thinning",
        "standard_agent_purity_guard",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
        "domain_ref_consumer_physical_thinning",
    ]
    assert followthrough["remaining_evidence_gate_ids"] == [
        "live_provider_paper_apply_scaleout",
        "publication_route_memory_receipt_scaleout",
        "artifact_lifecycle_receipt_scaleout",
        "provider_slo_long_soak",
    ]
    owner_followthrough = followthrough["owner_followthrough_evidence"][0]
    assert owner_followthrough["surface_kind"] == (
        "mas_memory_artifact_lifecycle_owner_followthrough"
    )
    assert owner_followthrough["status"] == "typed_blocker_followthrough_recorded_not_ready"
    assert owner_followthrough["source_lane_id"] == "memory_artifact_lifecycle_apply"
    assert owner_followthrough["source_readiness_status"] == (
        "typed_blocker_work_order_required_not_ready"
    )
    assert owner_followthrough["typed_blocker_ref_count"] == 25
    assert len(owner_followthrough["typed_blocker_refs"]) == 25
    assert owner_followthrough["closes_work_order_followthrough"] is True
    assert owner_followthrough["closes_artifact_lifecycle_receipt_scaleout"] is False
    assert owner_followthrough["closes_memory_or_artifact_ready"] is False
    assert owner_followthrough["ready_claim_authorized"] is False
    assert "domain_ready" in owner_followthrough["forbidden_claims"]
    audit = generated["functional_privatization_audit"]
    assert audit["classification_buckets"] == [
        "declarative_pack_generated_surface",
        "domain_authority_refs",
        "minimal_authority_function",
    ]
    assert audit["standard_agent_purity_policy"] == (
        "default_surfaces_must_remain_standard_agent_purity_guarded"
    )
    functional_boundary = audit["functional_consumer_boundary"]
    assert_standard_agent_purity_boundary(functional_boundary)
    runtime_role = functional_boundary["domain_authority_refs_index_role"]
    assert runtime_role["classification"] == "domain_authority_refs"
    assert runtime_role["authority"] == (
        "refs_only_domain_authority_index_not_generic_runtime_lifecycle_engine"
    )
    assert runtime_role["body_policy"] == "refs_receipts_blockers_only"
    assert runtime_role["generic_owner_claim_allowed"] is False
    assert runtime_role["mas_may_claim_generic_persistence_engine"] is False
    assert runtime_role["mas_may_write_domain_truth"] is False

    inventory = {
        item["module_id"]: item
        for item in functional_boundary["functional_module_inventory"]
    }
    private_runtime_domain_authority_ref_modules = {
        "domain_authority_refs_index": {
            "boundary": "refs_only_owner_receipt_locator_index_not_generic_runtime_owner",
            "must_not_emit": "generic_runtime_verdict",
        },
        "runtime_storage_maintenance": {
            "boundary": "opl_storage_substrate_mas_refs_only_projection_no_generic_cleanup_policy_owner",
            "must_not_emit": "generic_cleanup_policy",
        },
    }
    for module_id, expected in private_runtime_domain_authority_ref_modules.items():
        item = inventory[module_id]
        assert item["classification"] == "domain_authority_refs"
        assert item["authority_boundary"] == expected["boundary"]
        provenance_boundary = item["provenance_boundary"]
        assert provenance_boundary["generic_owner_claim_allowed"] is False
        assert provenance_boundary["body_policy"].endswith("_only")
        assert expected["must_not_emit"] in provenance_boundary["must_not_emit"]
        assert "paper_closure_verdict" in provenance_boundary["must_not_emit"]
    storage_adapter = inventory["runtime_storage_maintenance"]
    assert storage_adapter["owner"] == "one-person-lab"
    assert storage_adapter["migration_class"] == (
        "opl_storage_substrate_mas_refs_projection"
    )
    assert storage_adapter["current_ref_status"] == (
        "opl_owned_storage_substrate_mas_refs_only_projection"
    )
    assert (
        "src/med_autoscience/controllers/restore_proof_compaction_helpers.py"
        in storage_adapter["code_paths"]
    )
    assert not any("runtime_storage_maintenance" in path for path in storage_adapter["code_paths"])
    storage_thinning = storage_adapter["latest_thinning_evidence"]
    assert storage_thinning["status"] == "runtime_storage_physical_modules_retired"
    assert storage_thinning["retired_physical_modules"] == [
        "legacy_mas_storage_maintenance_python_namespace"
    ]
    live_boundary = storage_thinning["live_report_boundary_payload"]
    assert live_boundary["surface_kind"] == "mas_runtime_storage_refs_only_adapter_boundary"
    assert live_boundary["report_modes"] == [
        "workspace_storage_audit",
        "study_runtime_storage_maintenance",
        "orphan_quest_runtime_storage_maintenance",
    ]
    assert live_boundary["can_write_publication_eval"] is False
    assert "artifact_mutation_authorization" in live_boundary["must_not_emit"]
    assert storage_thinning["does_not_claim_physical_delete"] is True
    assert storage_thinning["does_not_claim_generic_cleanup_policy_owner"] is True
    assert storage_thinning["does_not_touch_publication_or_package_authority"] is True
    owner_dispatch_thinning = inventory["paper_mission_owner_surface_materialize_dispatch_shell"][
        "latest_thinning_evidence"
    ]
    assert owner_dispatch_thinning["status"] == (
        "owner_callable_action_policy_single_source_landed"
    )
    assert owner_dispatch_thinning["policy_module"] == (
        "src/med_autoscience/controllers/owner_callable_action_policy.py"
    )
    assert owner_dispatch_thinning["domain_repo_physical_delete_authorized"] is False
    assert "current_package" in owner_dispatch_thinning["does_not_write"]
    assert "publication_ready" in owner_dispatch_thinning["does_not_claim"]
    workbench_thinning = inventory["workbench_portal_generic_shell"]["latest_thinning_evidence"]
    assert workbench_thinning["status"] == "mas_local_progress_portal_physical_delete_landed"
    materializer_boundary = workbench_thinning["read_model_materializer_boundary"]
    assert materializer_boundary["status"] == "retired_local_materializer_replaced_by_opl_hosted_workbench"
    assert materializer_boundary["hosted_package_role"] == "opl_owned_read_model_projection_package"
    assert materializer_boundary["hosted_package_truth_role"] == "projection_only_no_workspace_runtime_truth"
    assert materializer_boundary["physical_module"] is None
    assert materializer_boundary["active_callers"] == []
    assert materializer_boundary["domain_repo_physical_delete_authorized"] is True
    assert "local_http_service_owner" in materializer_boundary["does_not_claim"]
    assert "runtime_control_owner" in materializer_boundary["does_not_claim"]
    assert materializer_boundary["writes_only"] == []
    assert "current_package" in materializer_boundary["does_not_write"]
    assert "workspace_carrier_boundary" not in workbench_thinning
    followthrough = functional_boundary["functional_followthrough_gap_summary"]
    assert "standard_agent_purity_guard" not in followthrough[
        "remaining_functional_followthrough_gate_ids"
    ]
    assert "standard_agent_purity_guard" in followthrough[
        "closed_functional_structure_gate_ids"
    ]


from tests.test_opl_standard_pack_cases.generated_interface_cases import *  # noqa: F403,F401
from tests.test_opl_standard_pack_cases.stage_contract_cases import *  # noqa: F403,F401
