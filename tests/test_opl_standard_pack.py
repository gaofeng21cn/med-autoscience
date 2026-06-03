from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

import pytest

from med_autoscience.action_catalog import build_mas_action_catalog
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


def _read_contract(name: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / "contracts" / f"{name}.json").read_text(encoding="utf-8"))


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

    assert _read_contract("domain_descriptor") == generated["domain_descriptor"]
    assert _read_contract("action_catalog") == generated["action_catalog"]
    assert _read_contract("stage_control_plane") == generated["stage_control_plane"]
    assert _read_contract("foundry_agent_series") == generated["foundry_agent_series"]
    assert _read_contract("functional_privatization_audit") == generated["functional_privatization_audit"]

    assert generated["action_catalog"]["actions"] == action_catalog["actions"]
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
        "owner_commit_pin": "c5d4a93bd4bb64adf1228ecf7f2a9038c7dce278",
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
            "sha256:5d77102e99e6e49acd88714cd94dcafe0969b8f2a5529928d753002ac3d4619d"
        ),
        "fingerprint_algorithm": "sha256:stable-json",
        "domain_contract_policy_release_pin_required": True,
        "domain_adapter_must_not_copy_policy_body_as_authority": True,
        "consumer_alignment_check": "foundry:policy-release",
    }
    assert generated["domain_descriptor"]["standard_contract_refs"][
        "foundry_agent_series_policy_release"
    ] == "contracts/opl-framework/foundry-agent-series-policy-release.json"
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
        "skills",
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
    assert foundry_series["domain_adapter_policy"]["no_parallel_progress_schema"] is True
    assert foundry_series["domain_adapter_policy"]["no_parallel_blocker_lineage_schema"] is True
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
            "boundary": "domain_authority_refs_no_generic_cleanup_policy_owner",
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
    assert (
        "src/med_autoscience/controllers/runtime_storage_maintenance_parts/cache_cleanup.py"
        in storage_adapter["code_paths"]
    )
    assert (
        "src/med_autoscience/controllers/runtime_storage_maintenance_parts/authority_boundary.py"
        in storage_adapter["code_paths"]
    )
    storage_thinning = storage_adapter["latest_thinning_evidence"]
    assert storage_thinning["status"] == "runtime_storage_live_report_boundary_payload_landed"
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
    owner_dispatch_thinning = inventory["owner_route_reconcile_materialize_dispatch_shell"][
        "latest_thinning_evidence"
    ]
    assert owner_dispatch_thinning["status"] == (
        "default_executor_action_policy_single_source_landed"
    )
    assert owner_dispatch_thinning["policy_module"] == (
        "src/med_autoscience/controllers/default_executor_action_policy.py"
    )
    assert owner_dispatch_thinning["domain_repo_physical_delete_authorized"] is False
    assert "current_package" in owner_dispatch_thinning["does_not_write"]
    assert "publication_ready" in owner_dispatch_thinning["does_not_claim"]
    workbench_thinning = inventory["workbench_portal_generic_shell"]["latest_thinning_evidence"]
    assert workbench_thinning["status"] == (
        "opl_hosted_workbench_projection_and_read_model_materializer_landed"
    )
    materializer_boundary = workbench_thinning["read_model_materializer_boundary"]
    assert materializer_boundary["status"] == "domain_owned_read_model_materializer_no_active_workspace_helper"
    assert materializer_boundary["hosted_package_role"] == "read_model_projection_package"
    assert materializer_boundary["hosted_package_truth_role"] == "projection_only_no_workspace_runtime_truth"
    assert materializer_boundary["physical_module"] == (
        "src/med_autoscience/controllers/progress_portal_parts/read_model_materializer.py"
    )
    assert materializer_boundary["active_callers"] == []
    assert materializer_boundary["domain_repo_physical_delete_authorized"] is False
    assert "local_http_service_owner" in materializer_boundary["does_not_claim"]
    assert "runtime_control_owner" in materializer_boundary["does_not_claim"]
    assert materializer_boundary["writes_only"] == [
        "artifacts/runtime/progress_portal/latest.json",
        "artifacts/runtime/progress_portal/hosted_package.json",
        "artifacts/runtime/progress_portal/studies/<study_id>/latest.json",
        "ops/mas/progress/index.html",
        "ops/mas/progress/studies/<study_id>/index.html",
    ]
    assert "current_package" in materializer_boundary["does_not_write"]
    assert "workspace_carrier_boundary" not in workbench_thinning
    followthrough = functional_boundary["functional_followthrough_gap_summary"]
    assert "standard_agent_purity_guard" not in followthrough[
        "remaining_functional_followthrough_gate_ids"
    ]
    assert "standard_agent_purity_guard" in followthrough[
        "closed_functional_structure_gate_ids"
    ]


def test_opl_generated_interfaces_compile_mas_standard_pack() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "interfaces", "--repo-dir", str(REPO_ROOT), "--json"],
        cwd=opl_root,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    bundle = payload["generated_agent_interfaces"]

    assert bundle["source_kind"] == "standard_agent_repo_contracts"
    assert bundle["status"] == "ready"
    assert bundle["owner"] == "one-person-lab"
    assert bundle["domain_repo_can_own_generated_surface"] is False
    assert bundle["blocker_reasons"] == []
    assert bundle["cli"]["status"] == "ready"
    assert bundle["mcp"]["status"] == "ready"
    assert bundle["skill"]["status"] == "ready"
    assert bundle["product_entry"]["status"] == "ready"
    assert bundle["openai_tool"]["status"] == "ready"
    assert bundle["ai_sdk"]["status"] == "ready"
    generated = build_standard_pack()
    assert {item["stage_id"] for item in bundle["stage_routes"]} == {
        stage["stage_id"] for stage in generated["stage_control_plane"]["stages"]
    }


def test_opl_default_callers_have_mas_deletion_evidence_without_authorizing_delete() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [
            str(opl_bin),
            "agents",
            "default-callers",
            "--agent",
            f"mas={REPO_ROOT}",
            "--json",
        ],
        cwd=opl_root,
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stderr or result.stdout
    readiness = json.loads(result.stdout)["agent_default_caller_readiness"]
    assert readiness["status"] == "ready_domain_evidence_required"
    assert readiness["summary"]["generated_default_caller_surface_count"] == 8
    assert readiness["summary"]["missing_domain_owner_receipt_or_typed_blocker_count"] == 0
    assert readiness["summary"]["missing_no_forbidden_write_proof_count"] == 0
    assert readiness["summary"]["missing_tombstone_or_provenance_ref_count"] == 0
    assert readiness["migration_gate_policy"]["physical_delete_authorized_by_this_report"] is False
    assert readiness["authority_boundary"]["report_can_authorize_domain_repo_physical_delete"] is False

    report = readiness["reports"][0]
    assert report["deletion_gate"]["physical_delete_authorized"] is False
    by_surface = {gate["surface_id"]: gate for gate in report["surface_gates"]}
    assert by_surface["product_status"]["active_caller_module_id"] == "workbench_portal_generic_shell"
    assert by_surface["domain_handler"]["active_caller_module_id"] == (
        "owner_route_reconcile_materialize_dispatch_shell"
    )
    assert by_surface["domain_handler"]["canonical_target_surface_ids"] == [
        "domain_action_adapter_export_dispatch",
        "domain_action_adapter",
        "domain_handler",
    ]
    for gate in report["surface_gates"]:
        worklist = gate["deletion_evidence_worklist"]
        assert worklist["domain_owner_receipt_or_typed_blocker"]["status"] == "observed"
        assert worklist["no_forbidden_write_proof"]["status"] == "observed"
        assert worklist["tombstone_or_provenance_ref"]["status"] == "observed"
        assert worklist["physical_delete_authorized"] is False


def test_opl_standard_scaffold_validates_mas_pack() -> None:
    opl_bin = Path(os.environ.get("OPL_BIN", "/Users/gaofeng/workspace/one-person-lab/bin/opl"))
    if not opl_bin.exists():
        pytest.skip(f"OPL binary missing: {opl_bin}")
    opl_root = opl_bin.parents[1]

    result = subprocess.run(
        [str(opl_bin), "agents", "scaffold", "--validate", str(REPO_ROOT), "--json"],
        cwd=opl_root,
        check=True,
        text=True,
        capture_output=True,
    )
    payload = json.loads(result.stdout)
    validation = payload["standard_domain_agent_scaffold"]["validation"]

    assert validation["status"] == "passed"
    assert validation["blockers"] == []
    assert validation["missing_contract_files"] == []
    assert validation["missing_forbidden_role_guards"] == []
