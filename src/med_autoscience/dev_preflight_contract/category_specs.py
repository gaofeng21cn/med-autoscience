from __future__ import annotations

from typing import Any


def build_category_specs(
    spec_type: type[Any],
    *,
    pytest_clean_runner: str,
    build_clean_runner: str,
) -> tuple[Any, ...]:
    return (
    spec_type(
        category_id="workflow_surface",
        exact_paths=(
            ".github/workflows/advisory.yml",
            ".github/workflows/ci.yml",
            "MANIFEST.in",
            ".github/workflows/release.yml",
            ".github/workflows/sentrux-advisory.yml",
            "pyproject.toml",
            "scripts/install-macos.sh",
            "setup.py",
            "tests/test_release_metadata.py",
            "tests/test_release_installer.py",
            "tests/test_release_workflow.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_release_workflow.py -q",
            f"{pytest_clean_runner} tests/test_release_metadata.py -q",
            f"{pytest_clean_runner} tests/test_release_installer.py -q",
            f"{build_clean_runner}",
        ),
    ),
    spec_type(
        category_id="codex_plugin_surface",
        exact_paths=(
            ".agents/plugins/marketplace.json",
            "plugins/med-autoscience/.codex-plugin/plugin.json",
            "plugins/med-autoscience/bin/medautosci-mcp",
            "plugins/med-autoscience/skills/med-autoscience/SKILL.md",
            "tests/test_codex_plugin.py",
            "tests/test_codex_plugin_installer.py",
            "tests/test_codex_plugin_scaffold.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_codex_plugin.py -q",
            f"{pytest_clean_runner} tests/test_codex_plugin_installer.py -q",
            f"{pytest_clean_runner} tests/test_codex_plugin_scaffold.py -q",
        ),
    ),
    spec_type(
        category_id="display_publication_surface",
        exact_paths=(
            "config/display_packs.toml",
            "src/med_autoscience/display_registry.py",
            "src/med_autoscience/display_schema_contract/__init__.py",
            "src/med_autoscience/display_template_catalog.py",
            "tests/test_display_layout_qc.py",
            "tests/test_display_surface_materialization.py",
        ),
        prefix_paths=(
            "src/med_autoscience/display_layout_qc/",
            "src/med_autoscience/controllers/display_surface_materialization/",
            "tests/display_schema_contract_cases/",
            "tests/medical_publication_surface_cases/",
            "tests/test_publication_gate_cases/",
        ),
        commands=(
            f"{pytest_clean_runner} tests/display_schema_contract_cases -q",
            f"{pytest_clean_runner} tests/test_display_surface_materialization.py -q",
            f"{pytest_clean_runner} tests/test_display_layout_qc.py -q",
            f"{pytest_clean_runner} tests/test_publication_gate_cases -q",
            f"{pytest_clean_runner} tests/medical_publication_surface_cases -q",
        ),
    ),
    spec_type(
        category_id="display_pack_v2_contract_surface",
        exact_paths=(
            "contracts/display-pack-contract.v2.json",
            "contracts/figure_polish_lifecycle_contract.json",
            "contracts/medical_figure_spec_contract.json",
            "contracts/publication_figure_quality_contract.json",
            "docs/delivery/medical-display/contracts/display_dependency_environment_os_target.md",
            "src/med_autoscience/display_pack_dependency_environment.py",
            "src/med_autoscience/display_pack_v2_contract.py",
            "src/med_autoscience/figure_polish_lifecycle_contract.py",
            "src/med_autoscience/medical_figure_spec_contract.py",
            "src/med_autoscience/publication_figure_quality_contract.py",
            "tests/test_display_pack_v2_contract.py",
            "tests/test_display_pack_v2_figure_quality_refs.py",
            "tests/test_figure_polish_lifecycle_contract.py",
            "tests/test_medical_figure_spec_contract.py",
            "tests/test_publication_figure_quality_contract.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/test_display_pack_v2_contract.py "
                "tests/test_display_pack_v2_figure_quality_refs.py "
                "tests/test_figure_polish_lifecycle_contract.py "
                "tests/test_medical_figure_spec_contract.py "
                "tests/test_publication_figure_quality_contract.py -q"
            ),
        ),
    ),
    spec_type(
        category_id="data_asset_operating_surface",
        exact_paths=(
            "contracts/data_asset_operating_contract.json",
            "src/med_autoscience/controllers/data_assets/__init__.py",
            "src/med_autoscience/controllers/data_assets/layout.py",
            "src/med_autoscience/controllers/data_assets/public_registry.py",
            "src/med_autoscience/controllers/data_assets/release_inventory.py",
            "tests/test_data_asset_operating_contract.py",
            "tests/test_data_assets.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/test_data_asset_operating_contract.py "
                "tests/test_data_assets.py -q"
            ),
        ),
    ),
    spec_type(
        category_id="runtime_contract_surface",
        exact_paths=(
            "contracts/runtime/mas-live-runtime-evidence-rollup.json",
            "contracts/runtime/mas-live-runtime-gap-work-orders.json",
            "contracts/runtime/mas-runtime-live-tail-work-orders.json",
            "contracts/runtime/mas-root-cause-depth-gate.json",
            "contracts/runtime_environment_requirements.json",
            "src/med_autoscience/controllers/study_outer_loop/__init__.py",
            "src/med_autoscience/controllers/study_runtime_decision/__init__.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/domain_status_projection.py",
            "src/med_autoscience/controllers/study_runtime_startup.py",
            "profiles/workspace.profile.template.toml",
            "src/med_autoscience/profiles.py",
            "tests/test_adapter_retirement_boundary.py",
            "tests/test_profiles.py",
            "tests/test_opl_runtime_contract.py",
            "tests/test_workspace_runtime_layout.py",
            "tests/test_report_store.py",
            "tests/test_runtime_protocol_study_runtime.py",
            "tests/test_opl_runtime_contract_no_provider_backend.py",
            "tests/test_study_runtime_router.py",
            "tests/test_runtime_root_cause_depth_gate.py",
        ),
        prefix_paths=(
            "src/med_autoscience/runtime_protocol/",
        ),
        commands=(
            f"{pytest_clean_runner} tests/test_runtime_root_cause_depth_gate.py -q",
            f"{pytest_clean_runner} tests/test_opl_runtime_contract.py -q",
            f"{pytest_clean_runner} tests/test_profiles.py -q",
            f"{pytest_clean_runner} tests/test_workspace_runtime_layout.py -q",
            f"{pytest_clean_runner} tests/test_study_runtime_router.py -q",
            f"{pytest_clean_runner} tests/test_opl_runtime_contract_no_provider_backend.py -q",
            f"{pytest_clean_runner} tests/test_adapter_retirement_boundary.py -q",
            f"{pytest_clean_runner} tests/test_runtime_protocol_study_runtime.py -q",
            f"{pytest_clean_runner} tests/test_report_store.py -q",
            "make test-meta",
        ),
    ),
    spec_type(
        category_id="optional_provider_archive_audit_surface",
        exact_paths=(
            "src/med_autoscience/controllers/backend_audit.py",
            "src/med_autoscience/doctor.py",
            "src/med_autoscience/med_deepscientist_repo_manifest.py",
            "src/med_autoscience/workspace_contracts.py",
            "tests/test_backend_audit.py",
            "tests/test_med_deepscientist_repo_manifest.py",
            "tests/test_workspace_contracts.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_med_deepscientist_repo_manifest.py -q",
            f"{pytest_clean_runner} tests/test_workspace_contracts.py -q",
            f"{pytest_clean_runner} tests/test_backend_audit.py -q",
        ),
    ),
    spec_type(
        category_id="integration_harness_surface",
        exact_paths=(
            "scripts/prepare-sentrux-gitstats-clone.sh",
            "tests/test_sentrux_gitstats_helper.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_dev_preflight_contract.py -q",
            f"{pytest_clean_runner} tests/test_dev_preflight.py -q",
            "make test-meta",
        ),
    ),
    spec_type(
        category_id="root_governance_contract_surface",
        exact_paths=(
            "AGENTS.md",
            "TASTE.md",
            "agent/standard-domain-agent-anchor.json",
            "contracts/README.md",
            "contracts/test-lane-manifest.json",
            "contracts/runtime/legacy-active-path-tombstones.json",
            "contracts/runtime/standard-domain-agent-anchor.json",
            "runtime/artifact_locator/workspace-runtime-artifact-root.locator.json",
            "tests/controller_charter/test_controller_charter_module_contract.py",
            "tests/eval_hygiene/test_eval_hygiene_module_contract.py",
            "tests/integration/test_monorepo_scaffold_boundaries.py",
            "tests/runtime/test_runtime_module_contract.py",
            "tests/test_opl_family_contract_adoption.py",
            "tests/test_opl_family_persistence_adapter.py",
            "tests/test_test_lane_governance.py",
        ),
        prefix_paths=(
            "contracts/modules/",
            "contracts/opl-framework/",
            "contracts/schemas/",
        ),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/controller_charter/test_controller_charter_module_contract.py "
                "tests/runtime/test_runtime_module_contract.py "
                "tests/eval_hygiene/test_eval_hygiene_module_contract.py "
                "tests/integration/test_monorepo_scaffold_boundaries.py -q"
            ),
            f"{pytest_clean_runner} tests/test_opl_family_contract_adoption.py -q",
            f"{pytest_clean_runner} tests/test_opl_family_persistence_adapter.py -q",
            f"{pytest_clean_runner} tests/test_test_lane_governance.py -q",
        ),
    ),
    spec_type(
        category_id="standard_agent_pack_surface",
        exact_paths=(
            "contracts/action_catalog.json",
            "contracts/agent_tool_arsenal.json",
            "contracts/artifact_locator_contract.json",
            "contracts/authority_kernel_inventory.json",
            "contracts/capability_map.json",
            "contracts/domain_projection_profile.json",
            "contracts/domain_descriptor.json",
            "contracts/domain_route_profile.json",
            "contracts/functional_privatization_audit.json",
            "contracts/generated_surface_handoff.json",
            "contracts/foundry_agent_series.json",
            "contracts/golden_path_profile.json",
            "contracts/mas-paper-study-stage-pack.json",
            "contracts/memory_descriptor.json",
            "contracts/owner_receipt_contract.json",
            "contracts/pack_compiler_input.json",
            "contracts/paper_mission_run_contract.json",
            "contracts/private_functional_surface_policy.json",
            "contracts/progress_first_safety_envelope.json",
            "contracts/standard_agent_completion_acceptance.json",
            "contracts/standard_agent_completion_evidence_status.json",
            "contracts/standard-agent-principles-adoption.json",
            "contracts/stage_artifact_kernel_adoption.json",
            "contracts/stage_route_reconcile_contract.json",
            "contracts/stage_run_kernel_profile.json",
            "src/med_autoscience/overlay/templates/medical-research-baseline.SKILL.md",
            "src/med_autoscience/overlay/templates/medical-research-experiment.SKILL.md",
            "src/med_autoscience/overlay/templates/medical-research-citation-locator-audit.template.md",
            "src/med_autoscience/overlay/templates/medical-research-figure-integrity.template.md",
            "src/med_autoscience/overlay/templates/medical-research-prisma-flow.template.md",
            "src/med_autoscience/overlay/templates/medical-research-skill-content-patterns.block.md",
            "src/med_autoscience/resources/stage_route_contract.yaml",
            "templates/codex/medautoscience-entry.SKILL.md",
            "templates/openclaw/medautoscience-entry.prompt.md",
        ),
        prefix_paths=(
            "agent/knowledge/",
            "agent/primary_skill/",
            "agent/prompts/",
            "agent/quality_gates/",
            "agent/skills/",
            "agent/stages/",
        ),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/test_opl_family_contract_adoption.py "
                "tests/test_progress_first_safety_envelope_contract.py "
                "tests/test_standard_agent_completion_acceptance_contract.py "
                "tests/test_test_lane_governance.py "
                "tests/test_stage_quality_contract.py "
                "tests/test_stage_route_contract.py "
                "tests/test_stage_route_reconcile_contract.py "
                "tests/test_overlay_installer.py -q"
            ),
            (
                f"{pytest_clean_runner} "
                "tests/test_domain_route_profile.py -q"
            ),
            f"{pytest_clean_runner} tests/test_mas_workspace_domain_projection.py -q",
        ),
    ),
    spec_type(
        category_id="external_learning_sidecar_surface",
        exact_paths=(
            "contracts/opl-framework/family-contract-adoption.json",
            "contracts/progress_first_safety_envelope.json",
            "src/med_autoscience/external_learning_adoption_closure/__init__.py",
            "src/med_autoscience/external_learning_authoring_advisory.py",
            "src/med_autoscience/external_learning_progress_workers.py",
            "src/med_autoscience/external_learning_review_advisory.py",
            "tests/test_external_learning_adoption_closure.py",
            "tests/test_opl_family_contract_adoption.py",
            "tests/test_progress_first_safety_envelope_contract.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/test_external_learning_adoption_closure.py "
                "tests/test_opl_family_contract_adoption.py "
                "tests/test_progress_first_safety_envelope_contract.py -q"
            ),
            "make test-meta",
        ),
    ),
    spec_type(
        category_id="evo_scientist_progress_accelerator_surface",
        exact_paths=(
            "contracts/evo_scientist_progress_accelerator.json",
            "src/med_autoscience/evo_scientist_learning_projection.py",
            "tests/test_evo_scientist_learning_projection.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_evo_scientist_learning_projection.py -q",
        ),
    ),
    spec_type(
        category_id="research_integrity_surface",
        exact_paths=(
            "contracts/research-integrity-layer.json",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/test_research_integrity_stage_hooks.py "
                "tests/test_research_integrity_domain_entry.py "
                "tests/test_research_integrity_provider_lookup.py -q"
            ),
        ),
    ),
    spec_type(
        category_id="production_acceptance_surface",
        exact_paths=(
            "contracts/agent_lab_handoff.json",
            "contracts/hosted_ordinary_path_consumption.json",
            "contracts/production_acceptance/mas-production-acceptance.json",
            "tests/test_mas_production_acceptance.py",
            "tests/test_opl_standard_pack_cases/test_generated_interface_cases.py",
            "tests/test_opl_standard_pack_cases/test_stage_contract_cases.py",
        ),
        prefix_paths=(
            "contracts/production_acceptance/",
        ),
        commands=(
            f"{pytest_clean_runner} tests/test_mas_production_acceptance.py -q",
            f"{pytest_clean_runner} tests/test_opl_standard_pack_cases -q",
        ),
    ),
    spec_type(
        category_id="family_shared_surface",
        exact_paths=(
            "Makefile",
            "pyproject.toml",
            "scripts/run-build-clean.sh",
            "scripts/run-python-clean.sh",
            "scripts/run-pytest-clean.sh",
            "scripts/run-structure-quality-gate.sh",
            "scripts/verify.sh",
            "scripts/opl-module-healthcheck.sh",
            "src/med_autoscience/dev_preflight.py",
            "src/med_autoscience/dev_preflight_contract/__init__.py",
            "tests/test_dev_preflight.py",
            "tests/test_dev_preflight_contract.py",
            "tests/test_editable_shared_bootstrap.py",
            "tests/fixtures/opl_agent_lab_longline.json",
            "tests/test_family_shared_release.py",
            "tests/test_opl_agent_lab_longline_migration.py",
            "uv.lock",
        ),
        prefix_paths=(),
        commands=(
            "make test-family",
        ),
    ),
    spec_type(
        category_id="structure_quality_surface",
        exact_paths=(
            ".sentrux/baseline.json",
            ".sentrux/rules.toml",
            "scripts/run-structure-quality-gate.sh",
            "scripts/line_budget.py",
        ),
        prefix_paths=(),
        commands=(
            "make test-structure",
        ),
    ),
    spec_type(
        category_id="control_plane_surface",
        exact_paths=(
            "contracts/stage_control_plane.json",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "src/med_autoscience/controllers/opl_provider_ready_adapter/__init__.py",
            "src/med_autoscience/controllers/owner_route_handoff/domain_handler_export.py",
            "src/med_autoscience/controllers/owner_route_handoff/dispatch_orchestration.py",
            "src/med_autoscience/controllers/delivery_artifact_authority.py",
            "src/med_autoscience/controllers/delivery_authority_backfill_apply.py",
            "src/med_autoscience/controllers/control_identity.py",
            "src/med_autoscience/controllers/control_intent.py",
            "src/med_autoscience/controllers/restore_proof_compaction_helpers.py",
            "src/med_autoscience/controllers/domain_authority_snapshot.py",
            "src/med_autoscience/controllers/study_outer_loop_work_units.py",
            "src/med_autoscience/controllers/study_delivery_sync/sync_orchestration.py",
            "src/med_autoscience/controllers/study_delivery_sync/sync_cli.py",
            "src/med_autoscience/controllers/study_progress/projection.py",
            "src/med_autoscience/controllers/study_progress/projection_quality_surfaces.py",
            "src/med_autoscience/controllers/study_progress/projection_runtime_surfaces.py",
            "src/med_autoscience/controllers/paper_artifacts.py",
            "tests/control_plane_fixtures.py",
            "tests/test_delivery_artifact_authority.py",
            "tests/test_delivery_authority_backfill_apply.py",
            "tests/test_delivery_artifact_resolution.py",
            "tests/test_autonomy_state_surface.py",
            "tests/test_study_delivery_sync.py",
            "tests/test_truth_projection_surfaces.py",
        ),
        prefix_paths=(
            "src/med_autoscience/controllers/control_plane_",
        ),
        commands=(
            "make test-control-plane",
        ),
    ),
    spec_type(
        category_id="owner_answer_candidate_intake_surface",
        exact_paths=(
            "src/med_autoscience/controllers/owner_answer_candidate_intake.py",
            "tests/test_owner_answer_candidate_intake.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_owner_answer_candidate_intake.py -q",
        ),
    ),
    spec_type(
        category_id="study_owner_gate_decision_surface",
        exact_paths=(
            "src/med_autoscience/controllers/study_interventions.py",
            "tests/test_study_interventions.py",
        ),
        prefix_paths=(),
        commands=(
            f"{pytest_clean_runner} tests/test_study_interventions.py -q",
        ),
    ),
    spec_type(
        category_id="paper_progress_transition_boundary_surface",
        exact_paths=(
            "contracts/live_stage_run_progress_evidence.json",
            "contracts/opl_domain_progress_transition_runtime_contract.json",
            "contracts/paper_autonomy_live_supervisor_canary_contract.json",
            "contracts/paper_autonomy_supervisor_contract.json",
            "contracts/paper_progress_replay_live_evidence_status.json",
            "contracts/paper_progress_transition_runtime_completion_audit.json",
            "contracts/runtime/mas-runtime-surface-retirement-inventory.json",
            "src/med_autoscience/controllers/opl_domain_progress_transition_contract.py",
            "src/med_autoscience/controllers/opl_transition_readback.py",
            "src/med_autoscience/controllers/paper_progress_policy_adapter.py",
            "tests/test_opl_domain_progress_transition_runtime_contract.py",
            "tests/test_opl_transition_readback_contract.py",
            "tests/test_mas_workspace_domain_projection.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{pytest_clean_runner} "
                "tests/test_opl_transition_readback_contract.py "
                "tests/test_mas_workspace_domain_projection.py "
                "tests/test_live_stage_run_progress_evidence.py -q"
            ),
            (
                f"{pytest_clean_runner} "
                "tests/test_opl_domain_progress_transition_runtime_contract.py -q"
            ),
        ),
    ),
    spec_type(
        category_id="publication_route_memory_surface",
        exact_paths=(
            "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
            "src/med_autoscience/controllers/stage_knowledge_plane/__init__.py",
            "src/med_autoscience/stage_knowledge_contract.py",
            "src/med_autoscience/stage_surface_contract.py",
            "tests/test_stage_knowledge_plane.py",
        ),
        prefix_paths=(
            "src/med_autoscience/controllers/stage_knowledge_plane/",
        ),
        commands=(
            f"{pytest_clean_runner} tests/test_stage_knowledge_plane.py -q",
            f"{pytest_clean_runner} tests/test_opl_family_contract_adoption.py -q",
        ),
    ),
)


__all__ = ["build_category_specs"]
