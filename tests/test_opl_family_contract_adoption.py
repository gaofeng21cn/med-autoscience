from __future__ import annotations

import json
from pathlib import Path

import pytest


pytestmark = pytest.mark.meta

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = "contracts/opl-framework/family-contract-adoption.json"


def _read(relative_path: str) -> str:
    return (REPO_ROOT / relative_path).read_text(encoding="utf-8")


def _contract() -> dict[str, object]:
    return json.loads(_read(CONTRACT_PATH))


def test_mas_declares_thin_opl_family_contract_adoption() -> None:
    contract = _contract()

    assert contract["contract_kind"] == "mas_opl_family_contract_adoption.v1"
    assert contract["domain_id"] == "med-autoscience"
    assert contract["opl_role"] == (
        "Codex-first stage-led provider-backed runtime framework and family-level projection consumer"
    )
    framework = contract["opl_framework_contract"]
    assert framework["owner"] == "one-person-lab"
    assert framework["framework_role"] == "codex_first_stage_led_provider_backed_runtime_framework"
    assert framework["stage_semantics"] == "human_expert_large_task_stage"
    assert framework["minimal_executor"] == "Codex CLI"
    assert framework["provider_abstraction"] == "opl_family_runtime_provider"
    assert framework["target_production_provider"] == "Temporal"
    assert "legacy_optional_providers" not in framework
    assert framework["optional_executor_adapters"] == [
        {
            "adapter_id": "hermes_agent",
            "display_name": "Hermes-Agent",
            "classification": "explicit_optional_executor_adapter",
            "default_provider": False,
        }
    ]
    assert set(framework["allowed_framework_authority"]) == {
        "stage_attempt",
        "queue",
        "wakeup",
        "retry",
        "dead_letter",
        "human_gate_signal",
        "attempt_receipt",
        "projection",
        "cross_domain_skeleton",
    }
    assert set(framework["forbidden_framework_authority"]) == {
        "study_truth",
        "publication_quality",
        "quality_gate",
        "artifact_authority",
        "paper_package",
    }


def test_mas_runtime_projection_maps_to_existing_runtime_truth_surfaces() -> None:
    contract = _contract()
    attempt = contract["attempt_projection"]

    for surface in ("progress_projection", "domain_health_diagnostic", "controller_decisions/latest.json"):
        assert surface in attempt["source_surfaces"]
    assert attempt["maps_to_opl_contract"] == "opl_family_runtime_attempt_contract.v1"
    assert "study runtime truth" in attempt["owner_boundary"]
    assert attempt["stability_projection_fields"] == [
        "control_loop_summary",
        "usage_projection",
        "resource_pressure",
        "observability_export",
    ]
    assert attempt["stability_projection_authority_boundary"] == {
        "projection_role": "read_only_operator_stability_projection",
        "can_execute_domain_action": False,
        "can_change_executor": False,
        "can_auto_degrade": False,
        "can_write_domain_truth": False,
        "can_write_domain_memory_body": False,
        "can_authorize_domain_ready": False,
        "can_authorize_quality_verdict": False,
        "provider_completion_is_domain_ready": False,
    }


def test_mas_quality_projection_keeps_medical_quality_owner_and_blocks_claim_only_ready() -> None:
    contract = _contract()
    quality = contract["quality_projection"]

    for surface in (
        "study_charter",
        "evidence_ledger",
        "review_ledger",
        "publication_eval/latest.json",
    ):
        assert surface in quality["source_surfaces"]
    assert quality["maps_to_opl_contract"] == "opl_family_domain_quality_projection_contract.v1"
    assert quality["claim_only_ready_forbidden"] is True


def test_mas_operator_and_incident_projection_require_source_refs_and_mas_closure() -> None:
    contract = _contract()
    incident = contract["incident_projection"]
    operator = contract["operator_projection"]

    assert incident["maps_to_opl_contract"] == "opl_family_incident_learning_loop.v1"
    assert "MAS-owned closure ref" in incident["closure_rule"]
    assert "ai_doctor_request" in incident["ai_doctor_boundary"]
    for surface in (
        "artifacts/autonomy/slo_status/latest.json",
        "artifacts/autonomy/ai_doctor_requests/*.json",
        "artifacts/autonomy/ai_doctor_diagnoses/*.json",
        "artifacts/autonomy/repair_actions/*.json",
    ):
        assert surface in incident["source_surfaces"]
    for field in (
        "source_refs",
        "freshness",
        "owner_split",
        "next_surface_ref",
        "human_gate_reason",
        "autonomy_slo",
        "ai_doctor_state",
        "repair_recommendation",
        "control_loop_summary",
        "usage_projection",
        "resource_pressure",
        "observability_export",
    ):
        assert field in operator["required_fields"]
    observability_export = operator["runtime_observability_export"]
    assert observability_export["opl_command"] == "opl runtime observability-export"
    assert observability_export["accepted_formats"] == ["json", "openmetrics"]
    assert observability_export["authority"] == "read_only_non_authoritative"
    assert set(observability_export["mas_consumes"]) == {
        "source_refs",
        "freshness",
        "owner_split",
        "domain_owned_projection_refs",
        "owner_receipt_refs",
        "typed_blocker_refs",
    }
    assert set(observability_export["forbidden_mas_interpretations"]) == {
        "domain_action_authorization",
        "executor_switch_authorization",
        "auto_degrade_authorization",
        "domain_truth_write",
        "memory_body_write",
        "publication_quality_verdict",
        "paper_or_artifact_closure",
    }
    for non_goal in contract["non_goals"]:
        assert non_goal not in ("", None)


def test_mas_persistence_lifecycle_owner_route_projection_is_refs_payload_only() -> None:
    contract = _contract()
    projection = contract["persistence_lifecycle_owner_route_projection"]

    assert projection["adoption_surface_kind"] == (
        "mas_opl_family_persistence_lifecycle_owner_route_adoption"
    )
    assert projection["required_shape"] == ["refs", "payload"]
    assert projection["maps_to_opl_contracts"] == {
        "persistence": "opl_family_persistence_contract.v1",
        "lifecycle": "opl_family_lifecycle_contract.v1",
        "owner_route": "opl_family_owner_route_contract.v1",
    }
    assert "runtime/artifacts/domain_authority_refs.sqlite" in projection["source_surfaces"]
    assert "owner_route_receipts" in projection["sqlite_tables"]
    assert "surface_refs" in projection["sqlite_tables"]
    assert projection["authority_boundary"] == (
        "OPL may discover and index MAS refs/payload; MAS keeps study, publication, AI reviewer, and paper package authority"
    )
    assert projection["forbidden_opl_authority_surfaces"] == [
        "publication_eval/latest.json",
        "AI reviewer workflow",
        "paper/manuscript/current_package",
        "current_package.zip",
    ]


def test_mas_domain_memory_projection_declares_domain_owned_migration_surface() -> None:
    contract = _contract()
    memory = contract["domain_memory_projection"]

    assert memory["descriptor_surface"] == "product-entry-manifest.domain_memory_descriptor"
    assert memory["memory_ref_id"] == "mas_publication_route_memory"
    assert memory["migration_plan_ref"] == (
        "docs/policies/study-workflow/publication_route_memory_policy.md#migration-plan"
    )
    assert memory["canonical_body_ref"] == "docs/policies/study-workflow/publication_route_memory_library.md"
    assert memory["seed_corpus_ref"] == (
        "docs/policies/study-workflow/publication_route_memory_seed_fixture.json"
    )
    assert memory["writeback_receipt_locator_ref"] == (
        "memory/portfolio/research_memory/publication_route_memory/writeback_receipts"
    )
    assert memory["workspace_apply_surface"] == {
        "seed_apply_receipt_surface": "publication_route_memory_apply_receipt",
        "memory_pack_surface": "publication_route_memory_pack",
        "memory_pack_locator": "memory/portfolio/research_memory/publication_route_memory/memory_pack.json",
        "migration_receipt_locator": "memory/portfolio/research_memory/publication_route_memory/migration_receipts",
        "repo_tracks_real_pack_or_receipts": False,
    }
    assert memory["migration_readiness"] == {
        "status": "workspace_apply_closure_ready",
        "canonical_body_status": "markdown_source_available",
        "seed_index_status": "repo_source_index_available",
        "memory_body_migration": "domain_owned_workspace_apply_available",
        "opl_apply_allowed": False,
    }
    assert "memory_store_owner" in memory["forbidden_opl_authority"]
    assert "publication_route_decision_owner" in memory["forbidden_opl_authority"]


def test_mas_generic_substrate_adapter_projection_is_opaque_index_only() -> None:
    contract = _contract()
    substrate = contract["generic_substrate_adapter_projection"]

    assert substrate["descriptor_surface"] == "medautosci domain-handler export.opl_substrate_adapter"
    assert substrate["surface_kind"] == "mas_opl_generic_substrate_adapter"
    assert substrate["mode"] == "opaque_index_only_refs"
    assert substrate["source_ref_families"] == [
        "workspace_refs",
        "source_refs",
        "artifact_refs",
        "memory_refs",
    ]
    assert substrate["maps_to_opl_contracts"] == {
        "workspace_locator": "opl_family_workspace_locator_contract.v1",
        "source_index": "opl_family_source_index_contract.v1",
        "artifact_locator": "opl_family_artifact_locator_contract.v1",
        "memory_locator": "opl_family_memory_locator_contract.v1",
        "lifecycle_projection": "opl_family_lifecycle_contract.v1",
    }
    assert substrate["projection_policy"] == {
        "body_included": False,
        "refs_are_opaque_to_opl": True,
        "opl_may_index": True,
        "opl_may_resolve_locator": True,
        "opl_may_manage_lifecycle": True,
        "opl_may_project_status": True,
        "opl_may_write_mas_truth": False,
        "opl_may_write_memory_body": False,
        "opl_may_write_evidence_ledger": False,
        "opl_may_write_review_ledger": False,
        "opl_may_write_publication_or_artifact_authority": False,
    }
    assert substrate["authority_boundary"]["mas_owns"] == [
        "study_truth",
        "memory_body",
        "evidence_ledger",
        "review_ledger",
        "publication_authority",
        "artifact_authority",
    ]
    assert substrate["authority_boundary"]["opl_owns"] == [
        "locator",
        "index",
        "lifecycle",
        "projection",
    ]
    assert set(substrate["authority_boundary"]["forbidden_opl_authority_surfaces"]) >= {
        "publication_eval/latest.json",
        "controller_decisions/latest.json",
        "paper/evidence/evidence_ledger.json",
        "paper/review/review_ledger.json",
        "manuscript/current_package",
        "current_package.zip",
        "publication_route_memory_body",
    }


def test_mas_pack_compiler_adoption_declares_generated_surface_handoff() -> None:
    contract = _contract()
    adoption = contract["pack_compiler_adoption"]

    assert adoption["surface_kind"] == "mas_opl_pack_compiler_adoption"
    assert adoption["owner"] == "med-autoscience"
    assert adoption["compiler_owner"] == "one-person-lab"
    assert adoption["status"] == "functional_structure_closed_evidence_gates_remaining"
    assert adoption["declarative_pack_input_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.declarative_pack_compiler_input"
    )
    assert adoption["generated_surface_handoff_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.generated_surface_handoff"
    )
    assert adoption["minimal_authority_function_manifest_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.minimal_authority_function_manifest"
    )
    assert adoption["functional_followthrough_gap_summary_ref"] == (
        "product_entry_manifest.functional_consumer_boundary.functional_followthrough_gap_summary"
    )
    assert adoption["classification_gap_count"] == 0
    assert adoption["functional_structure_gap_count"] == 0
    assert adoption["active_private_generic_residue_count"] == 0
    assert adoption["repo_local_wrapper_tail_count"] == 0
    assert adoption["source_purity_cutover_status"] == "standard_agent_source_shape_landed"
    assert adoption["remaining_gap_classification"] == (
        "live_provider_paper_line_evidence_gates"
    )
    assert adoption["remaining_functional_followthrough_gate_ids"] == []
    assert set(adoption["closed_functional_structure_gate_ids"]) == {
        "generated_surface_default_owner_cutover",
        "domain_authority_refs_thinning",
        "standard_agent_purity_guard",
        "opl_app_workbench_drilldown",
        "lifecycle_locator_retention_restore_ledger_reconciliation",
        "domain_ref_consumer_physical_thinning",
    }
    assert adoption["source_surfaces"] == [
        "product_entry_manifest.standard_domain_agent_skeleton",
        "product_entry_manifest.family_stage_control_plane_descriptor",
        "product_entry_manifest.family_action_catalog",
        "product_entry_manifest.family_transition_spec_descriptor",
        "product_entry_manifest.domain_memory_descriptor",
        "product_entry_manifest.lifecycle_guarded_apply_proof",
        "product_entry_manifest.domain_owner_receipt_contract",
        "product_entry_manifest.functional_consumer_boundary.functional_followthrough_gap_summary",
        "contracts/test-lane-manifest.json#focused_lanes/mas-functional-consumer-followthrough",
    ]
    assert adoption["generated_or_hosted_surfaces"] == [
        "CLI",
        "MCP",
        "Skill",
        "product-entry",
        "product-status",
        "product-session",
        "domain_handler",
        "status",
        "workbench",
        "projection shell",
        "test-lane harness",
    ]
    assert adoption["current_mas_shell_role"] == "domain_handler_and_refs_projection_source"
    assert adoption["mas_handwritten_shell_expansion_allowed"] is False
    assert adoption["minimal_authority_functions"] == [
        "publication_quality_verdict",
        "ai_reviewer_quality_decision",
        "artifact_mutation_authorization",
        "publication_route_memory_accept_reject",
        "source_readiness_verdict",
        "owner_receipt_signer",
        "medical_helper_implementation",
    ]
    assert adoption["forbidden_long_term_mas_shell_owners"] == [
        "cli",
        "mcp",
        "skill",
        "product_entry",
        "product_status",
        "product_session",
        "domain_handler",
        "status",
        "workbench",
        "projection_shell",
        "test_lane_harness",
    ]
    assert adoption["authority_boundary"] == {
        "opl_pack_compiler_may_generate_shells": True,
        "opl_pack_compiler_may_claim_domain_authority": False,
        "mas_keeps_medical_authority_functions": True,
        "mas_keeps_generic_shell_owner": False,
    }


def test_mas_ars_learning_projection_declares_external_patterns_without_boundary_drift() -> None:
    contract = _contract()
    projection = contract["academic_research_skills_learning_projection"]

    assert projection["surface_kind"] == "mas_ars_learning_projection"
    assert projection["descriptor_surfaces"] == [
        "product_entry_manifest.ars_learning_projection",
        "product_entry_manifest.family_stage_control_plane_descriptor.ars_learning_projection",
        "domain_handler_export.ars_learning_projection",
    ]
    assert projection["source_repository"] == "https://github.com/Imbad0202/academic-research-skills"
    assert projection["observed_head"] == "d564d26da39de039ba71d9b51f43e6a25fe9b149"
    assert projection["intake_doc_ref"] == "docs/references/mainline/ars_learning_intake.md"
    assert projection["dependency_introduced"] is False
    assert projection["absorbed_pattern_ids"] == [
        "claim_citation_support_audit",
        "data_access_and_oversight_metadata",
        "evidence_handoff_passport",
        "medical_material_passport_source_handoff",
    ]
    assert projection["maps_to_opl_shared_primitive"] == "family-stage-integrity-metadata.v1"
    assert projection["mas_role"] == "domain_projection_and_thin_adapter_only"
    assert projection["allowed_export"] == [
        "refs",
        "metadata",
        "freshness",
        "typed_blockers",
        "owner_boundary",
    ]
    assert set(projection["forbidden_export"]) >= {
        "memory_body",
        "evidence_ledger_body",
        "review_ledger_body",
        "publication_verdict_body",
        "paper_or_package_blob",
    }
    assert projection["source_adapter_contract"] == {
        "surface_kind": "mas_source_adapter_output",
        "schema_version": "mas-source-adapter-output.v1",
        "contract_ref": "med_autoscience.medical_material_passport.build_source_adapter_output",
        "records_write_mas_truth": False,
        "always_emit_rejection_log": True,
        "closed_reasons": [
            "missing_required_field",
            "invalid_field_format",
            "duplicate_citation_key",
            "unresolvable_source_pointer",
            "year_unparseable",
            "authors_unparseable",
            "adapter_error",
            "other",
        ],
        "entry_level_reject_continues": True,
        "adapter_level_failure_loud": True,
    }
    assert projection["authority_boundary"] == {
        "ars_role": "external_pattern_source_only",
        "opl_owner": "one-person-lab",
        "mas_domain_truth_owner": "MedAutoScience",
        "mas_publication_verdict_owner": "MedAutoScience",
        "mas_artifact_authority_owner": "MedAutoScience",
        "can_write_domain_truth": False,
        "can_write_evidence_ledger": False,
        "can_write_review_ledger": False,
        "can_write_publication_eval": False,
        "can_write_controller_decisions": False,
        "can_authorize_publication_quality": False,
        "can_authorize_submission_readiness": False,
        "can_authorize_artifact_authority": False,
    }


def test_mas_autosci_learning_projection_declares_contract_first_absorption() -> None:
    contract = _contract()
    projection = contract["autosci_learning_projection"]

    assert projection["surface_kind"] == "mas_autosci_learning_projection"
    assert projection["descriptor_surfaces"] == [
        "product_entry_manifest.autosci_learning_projection",
        "product_entry_manifest.family_stage_control_plane_descriptor.autosci_learning_projection",
        "domain_handler_export.autosci_learning_projection",
    ]
    assert projection["source_repository"] == "https://github.com/skyllwt/AutoSci"
    assert projection["observed_head"] == "d89cc72a884a2d091b6fac5719f30b4c64d2c6bd"
    assert projection["intake_doc_ref"] == "docs/references/mainline/autosci_learning_intake.md"
    assert projection["dependency_introduced"] is False
    assert projection["absorbed_pattern_ids"] == [
        "typed_research_knowledge_graph",
        "proposal_action_source_discovery_split",
        "negative_research_memory",
        "experiment_deploy_collect_eval_lifecycle",
        "independent_reviewer_verdict_mapping",
        "source_dag_render_qa_artifact_projection",
    ]
    assert projection["maps_to_opl_shared_primitive"] == "family-research-lifecycle-metadata.v1"
    assert projection["mas_role"] == (
        "domain_projection_quality_pack_and_refs_only_contract_owner"
    )
    assert set(projection["target_quality_pack_contracts"]) == {
        "ai_native_expert_judgment_pack.independent_reviewer_verdict_mapping_contract",
        "life_science_source_discovery_pack.proposal_action_source_discovery_contract",
        "life_science_source_discovery_pack.typed_knowledge_graph_edge_contract",
        "route_memory_pack.negative_research_memory_contract",
        "statistical_analysis_pack.experiment_lifecycle_receipt_contract",
        "paper_presentation_pack.source_dag_render_qa_artifact_contract",
    }
    assert set(projection["forbidden_export"]) >= {
        "external_runtime",
        "slash_command_runner",
        "prompt_only_permission_model",
        "publication_verdict_body",
        "artifact_body",
    }
    assert projection["authority_boundary"]["source_project_role"] == (
        "external_pattern_source_only"
    )
    assert projection["authority_boundary"]["can_write_domain_truth"] is False
    assert projection["authority_boundary"]["can_write_evidence_ledger"] is False
    assert projection["authority_boundary"]["can_write_review_ledger"] is False
    assert projection["authority_boundary"]["can_write_publication_eval"] is False
    assert projection["authority_boundary"]["can_write_controller_decisions"] is False
    assert projection["authority_boundary"]["can_authorize_source_readiness"] is False
    assert projection["authority_boundary"]["can_authorize_publication_quality"] is False
    assert projection["authority_boundary"]["can_authorize_artifact_authority"] is False


def test_mas_evo_scientist_learning_projection_declares_progress_first_absorption() -> None:
    contract = _contract()
    projection = contract["evo_scientist_learning_projection"]

    assert projection["surface_kind"] == "mas_evo_scientist_progress_accelerator_projection"
    assert projection["descriptor_surfaces"] == [
        "product_entry_manifest.evo_scientist_learning_projection",
        "product_entry_manifest.family_stage_control_plane_descriptor.evo_scientist_learning_projection",
        "domain_handler_export.evo_scientist_learning_projection",
    ]
    assert projection["source_repository"] == "https://github.com/EvoScientist/EvoScientist"
    assert projection["observed_release"] == "v0.1.4"
    assert projection["skills_repository"] == "https://github.com/EvoScientist/EvoSkills"
    assert projection["skills_release"] == "v1.0.0"
    assert projection["dependency_introduced"] is False
    assert projection["maps_to_opl_shared_primitive"] == "progress-first-learning-sidecar.v1"
    assert projection["mas_role"] == (
        "domain_projection_progress_accelerator_and_refs_only_contract_owner"
    )
    sidecar_architecture = projection["target_sidecar_execution_architecture"]
    assert sidecar_architecture["architecture_state"] == "repo_callable_worker_landed"
    assert sidecar_architecture["remaining_learning_plan"] is False
    assert sidecar_architecture["future_work_role"] == (
        "implementation_scaleout_under_this_contract_only"
    )
    assert sidecar_architecture["execution_model"] == "nonblocking_current_owner_following_sidecar"
    assert sidecar_architecture["critical_path_waits_for_sidecar"] is False
    assert sidecar_architecture["runs_parallel_to_ordinary_progress"] is True
    assert sidecar_architecture["sidecar_failure_policy"] == (
        "drop_sidecar_ref_and_continue_current_owner_action"
    )
    assert sidecar_architecture["sidecar_completion_required_for_dispatch"] is False
    assert sidecar_architecture["sidecar_completion_required_for_stage_transition"] is False
    assert sidecar_architecture["sidecar_completion_required_for_quality_gate"] is False
    assert sidecar_architecture["sidecar_completion_required_for_artifact_mutation"] is False
    assert sidecar_architecture[
        "hard_gate_candidate_requires_owner_or_reviewer_materialization"
    ] is True
    runtime_surface = projection["runtime_sidecar_execution_surface"]
    assert runtime_surface["surface_kind"] == "mas_evo_scientist_runtime_sidecar_execution_surface"
    assert runtime_surface["implementation_status"] == "repo_callable_worker_landed"
    assert runtime_surface["writer_ref"] == (
        "med_autoscience.runtime_protocol.evo_scientist_sidecar_refs."
        "write_evo_scientist_sidecar_observation"
    )
    assert runtime_surface["runtime_ref_root"] == "artifacts/runtime/evo_scientist_sidecar"
    assert runtime_surface["latest_ref"] == "artifacts/runtime/evo_scientist_sidecar/latest.json"
    assert runtime_surface["refs_only_state_index_family"] == "evo_scientist_sidecar_ref"
    assert runtime_surface["mainline_waits_for_sidecar"] is False
    assert runtime_surface["failure_blocks_current_owner_action"] is False
    assert runtime_surface["sidecar_completion_required_for_dispatch"] is False
    assert runtime_surface["sidecar_completion_required_for_quality_gate"] is False
    assert runtime_surface["can_write_publication_eval"] is False
    assert runtime_surface["can_write_controller_decisions"] is False
    assert runtime_surface["can_write_owner_receipt"] is False
    assert runtime_surface["can_write_typed_blocker"] is False
    assert "evo_scientist_sidecar_ref" in projection["allowed_export"]
    assert projection["absorbed_pattern_ids"] == [
        "auxiliary_background_model",
        "fire_and_forget_observation_memory",
        "conditional_tool_selection",
        "skill_routing_eval",
        "ive_failed_path_memory_taxonomy",
        "attempt_budget_stop_loss",
    ]
    assert projection["watch_only_pattern_ids"] == [
        "idea_tournament_as_default_gate",
        "full_research_lifecycle_pipeline_as_mas_default",
    ]
    assert set(projection["forbidden_export"]) >= {
        "external_runtime",
        "foreign_agent_memory_body",
        "tool_selector_hard_gate",
        "self_review_quality_closure",
        "full_pipeline_preflight_gate",
    }
    assert projection["authority_boundary"]["source_project_role"] == (
        "external_pattern_source_only"
    )
    assert projection["authority_boundary"]["can_write_domain_truth"] is False
    assert projection["authority_boundary"]["can_write_evidence_ledger"] is False
    assert projection["authority_boundary"]["can_authorize_publication_quality"] is False
    assert projection["authority_boundary"]["can_authorize_artifact_authority"] is False
    assert projection["authority_boundary"]["can_close_stage"] is False
