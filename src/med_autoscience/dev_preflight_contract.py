from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import shlex
from typing import Iterable, Sequence


PYTEST_CLEAN_RUNNER = "scripts/run-pytest-clean.sh"
PYTHON_CLEAN_RUNNER = "scripts/run-python-clean.sh"
BUILD_CLEAN_RUNNER = "scripts/run-build-clean.sh"


@dataclass(frozen=True)
class PreflightCategorySpec:
    category_id: str
    exact_paths: tuple[str, ...]
    prefix_paths: tuple[str, ...]
    commands: tuple[str, ...]


@dataclass(frozen=True)
class ClassificationResult:
    matched_categories: tuple[str, ...]
    unclassified_changes: tuple[str, ...]


@dataclass(frozen=True)
class PreflightCoveragePathFamily:
    family_id: str
    exact_paths: tuple[str, ...]
    prefix_paths: tuple[str, ...]


@dataclass(frozen=True)
class PreflightCoverageFamilyAudit:
    family_id: str
    explicit_categories: tuple[str, ...]
    explicit_classified_paths: tuple[str, ...]
    generic_python_regression_paths: tuple[str, ...]
    fail_closed_paths: tuple[str, ...]


@dataclass(frozen=True)
class PreflightCoverageAudit:
    family_audits: tuple[PreflightCoverageFamilyAudit, ...]
    explicit_classified_paths: tuple[str, ...]
    generic_python_regression_paths: tuple[str, ...]
    fail_closed_paths: tuple[str, ...]
    generic_python_regression_families: tuple[str, ...]
    fail_closed_families: tuple[str, ...]


GENERIC_PYTHON_SMOKE_CATEGORY = "generic_python_smoke_surface"
GENERIC_PYTHON_REGRESSION_CATEGORY = GENERIC_PYTHON_SMOKE_CATEGORY
DOCUMENTATION_REVIEW_CATEGORY = "documentation_review_only"

_DOC_ONLY_PREFIX_PATHS = ("docs/", "bootstrap/", "assets/branding/")
_DOC_ONLY_ROOT_FILE_PATTERNS = ("README*.md",)


_CATEGORY_SPECS: tuple[PreflightCategorySpec, ...] = (
    PreflightCategorySpec(
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
            f"{PYTEST_CLEAN_RUNNER} tests/test_release_workflow.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_release_metadata.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_release_installer.py -q",
            f"{BUILD_CLEAN_RUNNER}",
        ),
    ),
    PreflightCategorySpec(
        category_id="codex_plugin_surface",
        exact_paths=(
            ".agents/plugins/marketplace.json",
            "scripts/install-codex-plugin.sh",
            "plugins/mas/.mcp.json",
            "plugins/mas/.codex-plugin/plugin.json",
            "plugins/mas/.mcp.json",
            "plugins/mas/skills/mas/SKILL.md",
            "src/med_autoscience/codex_plugin_installer.py",
            "tests/test_codex_plugin.py",
            "tests/test_codex_plugin_installer.py",
            "tests/test_codex_plugin_installer_script.py",
            "tests/test_codex_plugin_scaffold.py",
        ),
        prefix_paths=(),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_codex_plugin.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_codex_plugin_installer.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_codex_plugin_installer_script.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_codex_plugin_scaffold.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="display_publication_surface",
        exact_paths=(
            "src/med_autoscience/display_registry.py",
            "src/med_autoscience/display_schema_contract.py",
            "src/med_autoscience/display_template_catalog.py",
            "src/med_autoscience/controllers/medical_publication_surface.py",
            "src/med_autoscience/controllers/publication_gate.py",
            "tests/test_display_layout_qc.py",
            "tests/test_display_schema_contract.py",
            "tests/test_display_surface_materialization.py",
            "tests/test_medical_publication_surface.py",
            "tests/test_publication_gate.py",
        ),
        prefix_paths=(
            "src/med_autoscience/display_layout_qc/",
            "src/med_autoscience/controllers/display_surface_materialization/",
        ),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_display_schema_contract.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_display_surface_materialization.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_display_layout_qc.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_publication_gate.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_medical_publication_surface.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="display_pack_v2_contract_surface",
        exact_paths=(
            "contracts/display-pack-contract.v2.json",
            "contracts/figure_polish_lifecycle_contract.json",
            "contracts/medical_figure_spec_contract.json",
            "contracts/publication_figure_quality_contract.json",
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
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_display_pack_v2_contract.py "
                "tests/test_display_pack_v2_figure_quality_refs.py "
                "tests/test_figure_polish_lifecycle_contract.py "
                "tests/test_medical_figure_spec_contract.py "
                "tests/test_publication_figure_quality_contract.py -q"
            ),
        ),
    ),
    PreflightCategorySpec(
        category_id="data_asset_operating_surface",
        exact_paths=(
            "contracts/data_asset_operating_contract.json",
            "src/med_autoscience/cli_parts/workspace_data_commands.py",
            "src/med_autoscience/controllers/data_assets.py",
            "src/med_autoscience/controllers/data_assets_parts/layout.py",
            "src/med_autoscience/controllers/data_assets_parts/public_registry.py",
            "src/med_autoscience/controllers/data_assets_parts/release_inventory.py",
            "tests/test_cli_cases/workspace_and_data_asset_commands.py",
            "tests/test_data_asset_operating_contract.py",
            "tests/test_data_assets.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_data_asset_operating_contract.py "
                "tests/test_data_assets.py "
                "tests/test_cli_cases/workspace_and_data_asset_commands.py -q"
            ),
        ),
    ),
    PreflightCategorySpec(
        category_id="runtime_contract_surface",
        exact_paths=(
            "src/med_autoscience/controllers/study_outer_loop.py",
            "src/med_autoscience/controllers/domain_health_diagnostic.py",
            "src/med_autoscience/controllers/study_runtime_decision.py",
            "src/med_autoscience/controllers/study_runtime_resolution.py",
            "src/med_autoscience/controllers/domain_status_projection.py",
            "src/med_autoscience/controllers/study_runtime_startup.py",
            "src/med_autoscience/controllers/progress_projection.py",
            "profiles/workspace.profile.template.toml",
            "src/med_autoscience/profiles.py",
            "tests/test_adapter_retirement_boundary.py",
            "tests/test_profiles.py",
            "tests/test_opl_runtime_contract.py",
            "tests/test_runtime_protocol_layout.py",
            "tests/test_runtime_protocol_domain_health_diagnostic.py",
            "tests/test_runtime_protocol_study_runtime.py",
            "tests/test_opl_runtime_contract_no_provider_backend.py",
            "tests/test_domain_health_diagnostic.py",
            "tests/test_study_runtime_router.py",
        ),
        prefix_paths=(
            "src/med_autoscience/runtime_protocol/",
        ),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_opl_runtime_contract.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_profiles.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_runtime_protocol_layout.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_domain_health_diagnostic.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_study_runtime_router.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_opl_runtime_contract_no_provider_backend.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_adapter_retirement_boundary.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_runtime_protocol_study_runtime.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_runtime_protocol_domain_health_diagnostic.py -q",
            "make test-meta",
        ),
    ),
    PreflightCategorySpec(
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
            f"{PYTEST_CLEAN_RUNNER} tests/test_med_deepscientist_repo_manifest.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_workspace_contracts.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_backend_audit.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="integration_harness_surface",
        exact_paths=(
            "scripts/prepare-sentrux-gitstats-clone.sh",
            "scripts/run-parallel-test-lanes.sh",
            "src/med_autoscience/controllers/workspace_init.py",
            "tests/test_sentrux_gitstats_helper.py",
            "tests/test_workspace_init.py",
        ),
        prefix_paths=(),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_dev_preflight_contract.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_dev_preflight.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_workspace_init.py -q",
            "make test-meta",
        ),
    ),
    PreflightCategorySpec(
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
            "tests/test_test_command_surfaces.py",
        ),
        prefix_paths=(
            "contracts/modules/",
            "contracts/opl-framework/",
            "contracts/schemas/",
        ),
        commands=(
            (
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/controller_charter/test_controller_charter_module_contract.py "
                "tests/runtime/test_runtime_module_contract.py "
                "tests/eval_hygiene/test_eval_hygiene_module_contract.py "
                "tests/integration/test_monorepo_scaffold_boundaries.py -q"
            ),
            f"{PYTEST_CLEAN_RUNNER} tests/test_opl_family_contract_adoption.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_opl_family_persistence_adapter.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_test_command_surfaces.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="standard_agent_pack_surface",
        exact_paths=(
            "contracts/action_catalog.json",
            "contracts/artifact_locator_contract.json",
            "contracts/authority_kernel_inventory.json",
            "contracts/domain_descriptor.json",
            "contracts/functional_privatization_audit.json",
            "contracts/generated_surface_handoff.json",
            "contracts/foundry_agent_series.json",
            "contracts/golden_path_profile.json",
            "contracts/hosted_ordinary_path_consumption.json",
            "contracts/mas-paper-study-stage-pack.json",
            "contracts/memory_descriptor.json",
            "contracts/owner_receipt_contract.json",
            "contracts/pack_compiler_input.json",
            "contracts/private_functional_surface_policy.json",
            "contracts/progress_first_safety_envelope.json",
            "contracts/standard_agent_completion_acceptance.json",
            "contracts/standard_agent_completion_evidence_status.json",
            "contracts/stage_artifact_kernel_adoption.json",
            "contracts/stage_route_reconcile_contract.json",
            "contracts/stage_run_kernel_profile.json",
            "src/med_autoscience/overlay/templates/medical-research-baseline.SKILL.md",
            "src/med_autoscience/overlay/templates/medical-research-experiment.SKILL.md",
            "src/med_autoscience/overlay/templates/medical-research-citation-locator-audit.template.md",
            "src/med_autoscience/overlay/templates/medical-research-figure-integrity.template.md",
            "src/med_autoscience/overlay/templates/medical-research-prisma-flow.template.md",
            "src/med_autoscience/overlay/templates/medical-research-skill-content-patterns.block.md",
            "src/med_autoscience/hosted_ordinary_path_consumption.py",
            "src/med_autoscience/resources/stage_route_contract.yaml",
            "templates/codex/medautoscience-entry.SKILL.md",
            "templates/openclaw/medautoscience-entry.prompt.md",
            "tests/test_agent_tool_arsenal_hosted_consumption_mcp.py",
            "tests/test_hosted_ordinary_path_preflight_contract.py",
            "tests/test_hosted_ordinary_path_consumption.py",
            "templates/stage_route_contract.yaml",
        ),
        prefix_paths=(
            "agent/knowledge/",
            "agent/prompts/",
            "agent/quality_gates/",
            "agent/skills/",
            "agent/stages/",
        ),
        commands=(
            (
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_opl_family_contract_adoption.py "
                "tests/test_progress_first_safety_envelope_contract.py "
                "tests/test_standard_agent_completion_acceptance_contract.py "
                "tests/test_test_lane_governance.py "
                "tests/test_stage_quality_contract.py "
                "tests/test_stage_route_contract.py "
                "tests/test_stage_route_reconcile_contract.py "
                "tests/test_overlay_installer.py -q"
            ),
            f"{PYTEST_CLEAN_RUNNER} tests/test_product_entry.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="external_learning_sidecar_surface",
        exact_paths=(
            "contracts/opl-framework/family-contract-adoption.json",
            "contracts/progress_first_safety_envelope.json",
            "src/med_autoscience/external_learning_adoption_closure.py",
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
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_external_learning_adoption_closure.py "
                "tests/test_opl_family_contract_adoption.py "
                "tests/test_progress_first_safety_envelope_contract.py -q"
            ),
            "make test-meta",
        ),
    ),
    PreflightCategorySpec(
        category_id="evo_scientist_progress_accelerator_surface",
        exact_paths=(
            "contracts/evo_scientist_progress_accelerator.json",
            "src/med_autoscience/evo_scientist_learning_projection.py",
            "tests/test_evo_scientist_learning_projection.py",
        ),
        prefix_paths=(),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_evo_scientist_learning_projection.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="domain_action_materializer_surface",
        exact_paths=(
            "src/med_autoscience/controllers/domain_action_request_materializer.py",
            "src/med_autoscience/controllers/domain_action_request_materializer_parts/publication_owner_materialization.py",
            "tests/domain_action_request_materializer_cases/test_dm002_effective_eval_gate_sprint.py",
        ),
        prefix_paths=(
            "tests/fixtures/dm002_20260529T095414Z_effective_eval_sprint_canary/",
        ),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/domain_action_request_materializer_cases/test_dm002_effective_eval_gate_sprint.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_domain_action_request_materializer.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="paper_autonomy_supervisor_surface",
        exact_paths=(
            "contracts/paper_autonomy_supervisor_contract.json",
            "src/med_autoscience/controllers/paper_autonomy_supervisor.py",
            "tests/test_paper_autonomy_supervisor.py",
            "tests/test_paper_autonomy_supervisor_contract.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_paper_autonomy_supervisor.py "
                "tests/test_paper_autonomy_supervisor_contract.py -q"
            ),
        ),
    ),
    PreflightCategorySpec(
        category_id="production_acceptance_surface",
        exact_paths=(
            "contracts/agent_lab_handoff.json",
            "contracts/production_acceptance/mas-production-acceptance.json",
            "tests/test_mas_production_acceptance.py",
            "tests/test_opl_standard_pack.py",
        ),
        prefix_paths=(
            "contracts/production_acceptance/",
        ),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_mas_production_acceptance.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_opl_standard_pack.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="family_shared_surface",
        exact_paths=(
            "Makefile",
            "pyproject.toml",
            "scripts/run-build-clean.sh",
            "scripts/run-python-clean.sh",
            "scripts/run-pytest-clean.sh",
            "scripts/run-structure-quality-gate.sh",
            "scripts/verify.sh",
            "src/med_autoscience/editable_shared_bootstrap.py",
            "src/med_autoscience/dev_preflight.py",
            "src/med_autoscience/dev_preflight_contract.py",
            "src/med_autoscience/family_shared_release.py",
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
    PreflightCategorySpec(
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
    PreflightCategorySpec(
        category_id="control_plane_surface",
        exact_paths=(
            "contracts/stage_control_plane.json",
            "scripts/real-paper-autonomy-soak-inventory.py",
            "src/med_autoscience/controllers/opl_provider_ready_adapter.py",
            "src/med_autoscience/controllers/owner_route_handoff.py",
            "src/med_autoscience/controllers/artifact_lifecycle_inventory.py",
            "src/med_autoscience/controllers/artifact_lifecycle_operations_report.py",
            "src/med_autoscience/controllers/control_identity.py",
            "src/med_autoscience/controllers/control_intent.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance.py",
            "src/med_autoscience/cli.py",
            "src/med_autoscience/mcp_server.py",
            "src/med_autoscience/controllers/runtime_storage_maintenance_parts/dataset_retention.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/control_plane_gate.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/managed_wakeup.py",
            "src/med_autoscience/controllers/domain_authority_snapshot.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_orchestration.py",
            "src/med_autoscience/controllers/study_delivery_sync_parts/sync_cli.py",
            "src/med_autoscience/controllers/study_progress_parts/projection.py",
            "src/med_autoscience/controllers/study_progress_parts/projection_quality_surfaces.py",
            "src/med_autoscience/controllers/study_progress_parts/projection_runtime_surfaces.py",
            "src/med_autoscience/runtime_protocol/paper_artifacts.py",
            "tests/control_plane_fixtures.py",
            "tests/test_artifact_lifecycle_inventory.py",
            "tests/test_artifact_lifecycle_operations_report.py",
            "tests/test_cli_cases/public_entry_commands.py",
            "tests/test_workspace_authority_migration_audit.py",
            "tests/test_mcp_server.py",
            "tests/test_runtime_protocol_paper_artifacts.py",
            "tests/test_runtime_storage_maintenance.py",
            "tests/test_cli_cases/owner_route_handoff_command.py",
            "tests/test_autonomy_state_surface.py",
            "tests/test_study_delivery_sync.py",
            "tests/test_truth_projection_surfaces.py",
            "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_managed_recovery_redrive.py",
        ),
        prefix_paths=(
            "src/med_autoscience/controllers/control_plane_",
        ),
        commands=(
            "make test-control-plane",
        ),
    ),
    PreflightCategorySpec(
        category_id="cli_parser_surface",
        exact_paths=(
            "src/med_autoscience/cli_parts/parser.py",
        ),
        prefix_paths=(),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_runtime_lifecycle_payload_retention.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="runtime_lifecycle_payload_retention_surface",
        exact_paths=(
            "src/med_autoscience/cli_parts/retention_commands.py",
            "src/med_autoscience/controllers/runtime_lifecycle_payload_retention.py",
            "tests/test_runtime_lifecycle_payload_retention.py",
        ),
        prefix_paths=(),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_runtime_lifecycle_payload_retention.py -q",
        ),
    ),
    PreflightCategorySpec(
        category_id="paper_progress_transition_boundary_surface",
        exact_paths=(
            "contracts/opl_domain_progress_transition_runtime_contract.json",
            "contracts/paper_progress_replay_live_evidence_status.json",
            "contracts/paper_progress_transition_runtime_completion_audit.json",
            "contracts/runtime/mas-runtime-surface-retirement-inventory.json",
            "src/med_autoscience/controllers/opl_domain_progress_transition_contract.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/obligation_actuator.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control_actions.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control_arbiter.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_current_control_identity.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_scan.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/runtime_scan_support.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_transition_request.py",
            "src/med_autoscience/controllers/domain_health_diagnostic_parts/provider_admission_report.py",
            "src/med_autoscience/controllers/paper_recovery_state_parts/provider_admission_state.py",
            "src/med_autoscience/controllers/paper_progress_policy_adapter.py",
            "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/provider_admission_current_control_cases.py",
            "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/provider_admission_current_control_same_tick_cases.py",
            "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/test_obligation_actuator_outcomes.py",
            "tests/test_opl_domain_progress_transition_runtime_contract.py",
            "tests/test_paper_progress_policy_adapter.py",
            "tests/test_paper_recovery_provider_admission_state.py",
            "tests/test_provider_admission_current_control_arbiter.py",
        ),
        prefix_paths=(),
        commands=(
            (
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_paper_progress_policy_adapter.py "
                "tests/test_provider_admission_current_control_arbiter.py "
                "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
                "provider_admission_current_control_cases.py "
                "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
                "provider_admission_current_control_same_tick_cases.py "
                "tests/test_domain_health_diagnostic_cases/supervisor_and_progress_cases_cases/"
                "test_obligation_actuator_outcomes.py -q"
            ),
            (
                f"{PYTEST_CLEAN_RUNNER} "
                "tests/test_opl_domain_progress_transition_runtime_contract.py "
                "tests/test_paper_recovery_provider_admission_state.py -q"
            ),
        ),
    ),
    PreflightCategorySpec(
        category_id="publication_route_memory_surface",
        exact_paths=(
            "docs/policies/study-workflow/publication_route_memory_seed_fixture.json",
            "src/med_autoscience/controllers/stage_knowledge_plane.py",
            "src/med_autoscience/stage_knowledge_contract.py",
            "src/med_autoscience/stage_surface_contract.py",
            "tests/test_stage_knowledge_plane.py",
        ),
        prefix_paths=(
            "src/med_autoscience/controllers/stage_knowledge_plane_parts/",
        ),
        commands=(
            f"{PYTEST_CLEAN_RUNNER} tests/test_stage_knowledge_plane.py -q",
            f"{PYTEST_CLEAN_RUNNER} tests/test_opl_family_contract_adoption.py -q",
        ),
    ),
)

_GENERIC_PYTHON_PREFIXES = (
    "src/med_autoscience/",
    "tests/",
)

_GENERIC_PYTHON_SMOKE_COMMANDS = (
    "make test-smoke",
)
_GENERIC_PYTHON_REGRESSION_COMMANDS = _GENERIC_PYTHON_SMOKE_COMMANDS

_MATCHED_CATEGORY_FAIL_POLICY = "matched_paths_run_planned_commands"
_GENERIC_PYTHON_SMOKE_FAIL_POLICY = "unknown_python_and_test_paths_route_to_smoke"
_GENERIC_PYTHON_FAIL_POLICY = _GENERIC_PYTHON_SMOKE_FAIL_POLICY
_UNKNOWN_PATH_POLICY = {
    "python_and_test_paths": "smoke",
    "documentation_paths": "review-only",
    "workflow_config_paths": "fail-closed",
}
_UNKNOWN_DOCUMENTATION_SUGGESTION = (
    "Review documentation manually; no pytest command is planned for doc prose."
)
_UNKNOWN_WORKFLOW_CONFIG_SUGGESTION = (
    "Add workflow/config paths to a reviewed owner surface before preflight can run commands."
)

_DEFAULT_COVERAGE_PATH_FAMILIES: tuple[PreflightCoveragePathFamily, ...] = (
    PreflightCoveragePathFamily(
        family_id="source_root",
        exact_paths=(),
        prefix_paths=("src/med_autoscience/",),
    ),
    PreflightCoveragePathFamily(
        family_id="test_root",
        exact_paths=(),
        prefix_paths=("tests/",),
    ),
    PreflightCoveragePathFamily(
        family_id="runtime_docs",
        exact_paths=(),
        prefix_paths=("docs/runtime/",),
    ),
    PreflightCoveragePathFamily(
        family_id="program_docs",
        exact_paths=(),
        prefix_paths=("docs/active/",),
    ),
    PreflightCoveragePathFamily(
        family_id="policy_docs",
        exact_paths=(),
        prefix_paths=("docs/policies/",),
    ),
    PreflightCoveragePathFamily(
        family_id="reference_docs",
        exact_paths=(),
        prefix_paths=("docs/references/",),
    ),
    PreflightCoveragePathFamily(
        family_id="history_docs",
        exact_paths=(),
        prefix_paths=("docs/history/",),
    ),
    PreflightCoveragePathFamily(
        family_id="capability_docs",
        exact_paths=(),
        prefix_paths=("docs/delivery/",),
    ),
    PreflightCoveragePathFamily(
        family_id="agent_root",
        exact_paths=(),
        prefix_paths=("agent/",),
    ),
    PreflightCoveragePathFamily(
        family_id="contract_root",
        exact_paths=("contracts/README.md",),
        prefix_paths=(
            "contracts/modules/",
            "contracts/opl-framework/",
            "contracts/runtime/",
            "contracts/schemas/",
        ),
    ),
    PreflightCoveragePathFamily(
        family_id="runtime_artifact_locator_root",
        exact_paths=(),
        prefix_paths=("runtime/artifact_locator/",),
    ),
    PreflightCoveragePathFamily(
        family_id="workflow_config",
        exact_paths=(
            ".sentrux/baseline.json",
            ".sentrux/rules.toml",
            "Makefile",
            "pyproject.toml",
            "uv.lock",
        ),
        prefix_paths=(
            ".github/workflows/",
            "scripts/",
        ),
    ),
)


def _normalize_changed_file(path: str) -> str:
    return path.strip().replace("\\", "/").removeprefix("./")


def _matches_spec(*, normalized_path: str, spec: PreflightCategorySpec) -> bool:
    if normalized_path in spec.exact_paths:
        return True
    return any(normalized_path.startswith(prefix) for prefix in spec.prefix_paths)


def _matches_path_family(*, normalized_path: str, family: PreflightCoveragePathFamily) -> bool:
    if normalized_path in family.exact_paths:
        return True
    return any(normalized_path.startswith(prefix) for prefix in family.prefix_paths)


def classify_changed_files(changed_files: Sequence[str]) -> ClassificationResult:
    matched_categories: list[str] = []
    unclassified_changes: list[str] = []

    for changed_file in changed_files:
        normalized_path = _normalize_changed_file(str(changed_file))
        if not normalized_path:
            continue
        matched_here = False
        for spec in _CATEGORY_SPECS:
            if not _matches_spec(normalized_path=normalized_path, spec=spec):
                continue
            matched_here = True
            if spec.category_id not in matched_categories:
                matched_categories.append(spec.category_id)
        if not matched_here and is_generic_python_change(normalized_path):
            matched_here = True
            if GENERIC_PYTHON_REGRESSION_CATEGORY not in matched_categories:
                matched_categories.append(GENERIC_PYTHON_REGRESSION_CATEGORY)
        if not matched_here and is_documentation_review_only_change(normalized_path):
            matched_here = True
            if DOCUMENTATION_REVIEW_CATEGORY not in matched_categories:
                matched_categories.append(DOCUMENTATION_REVIEW_CATEGORY)
        if not matched_here and normalized_path not in unclassified_changes:
            unclassified_changes.append(normalized_path)

    return ClassificationResult(
        matched_categories=tuple(matched_categories),
        unclassified_changes=tuple(unclassified_changes),
    )


def is_generic_python_change(path: str) -> bool:
    normalized_path = _normalize_changed_file(path)
    return normalized_path.endswith(".py") and normalized_path.startswith(_GENERIC_PYTHON_PREFIXES)


def is_documentation_review_only_change(path: str) -> bool:
    normalized_path = _normalize_changed_file(path)
    if "/" not in normalized_path and normalized_path.startswith("README") and normalized_path.endswith(".md"):
        return True
    if normalized_path.startswith("assets/branding/"):
        return True
    return normalized_path.startswith(_DOC_ONLY_PREFIX_PATHS) and normalized_path.endswith(".md")


def _explicit_categories_for_path(normalized_path: str) -> tuple[str, ...]:
    categories = [
        spec.category_id
        for spec in _CATEGORY_SPECS
        if _matches_spec(normalized_path=normalized_path, spec=spec)
    ]
    if not categories and is_documentation_review_only_change(normalized_path):
        categories.append(DOCUMENTATION_REVIEW_CATEGORY)
    return tuple(categories)


def _append_unique(values: list[str], candidates: Iterable[str]) -> None:
    for candidate in candidates:
        if candidate not in values:
            values.append(candidate)


def audit_preflight_contract_coverage(
    repo_tracked_paths: Sequence[str],
    *,
    path_families: Sequence[PreflightCoveragePathFamily] = _DEFAULT_COVERAGE_PATH_FAMILIES,
) -> PreflightCoverageAudit:
    normalized_paths = tuple(
        normalized_path
        for path in repo_tracked_paths
        if (normalized_path := _normalize_changed_file(str(path)))
    )
    family_audits: list[PreflightCoverageFamilyAudit] = []
    all_explicit_classified_paths: list[str] = []
    all_generic_python_regression_paths: list[str] = []
    all_fail_closed_paths: list[str] = []
    generic_python_regression_families: list[str] = []
    fail_closed_families: list[str] = []

    for family in path_families:
        family_paths = tuple(
            path for path in normalized_paths if _matches_path_family(normalized_path=path, family=family)
        )
        explicit_categories: list[str] = []
        explicit_classified_paths: list[str] = []
        generic_python_regression_paths: list[str] = []
        fail_closed_paths: list[str] = []

        for path in family_paths:
            categories = _explicit_categories_for_path(path)
            if categories:
                _append_unique(explicit_categories, categories)
                explicit_classified_paths.append(path)
            elif is_generic_python_change(path):
                generic_python_regression_paths.append(path)
            elif is_documentation_review_only_change(path):
                _append_unique(explicit_categories, (DOCUMENTATION_REVIEW_CATEGORY,))
                explicit_classified_paths.append(path)
            else:
                fail_closed_paths.append(path)

        if generic_python_regression_paths:
            generic_python_regression_families.append(family.family_id)
        if fail_closed_paths:
            fail_closed_families.append(family.family_id)
        _append_unique(all_explicit_classified_paths, explicit_classified_paths)
        _append_unique(all_generic_python_regression_paths, generic_python_regression_paths)
        _append_unique(all_fail_closed_paths, fail_closed_paths)
        family_audits.append(
            PreflightCoverageFamilyAudit(
                family_id=family.family_id,
                explicit_categories=tuple(explicit_categories),
                explicit_classified_paths=tuple(explicit_classified_paths),
                generic_python_regression_paths=tuple(generic_python_regression_paths),
                fail_closed_paths=tuple(fail_closed_paths),
            )
        )

    return PreflightCoverageAudit(
        family_audits=tuple(family_audits),
        explicit_classified_paths=tuple(all_explicit_classified_paths),
        generic_python_regression_paths=tuple(all_generic_python_regression_paths),
        fail_closed_paths=tuple(all_fail_closed_paths),
        generic_python_regression_families=tuple(generic_python_regression_families),
        fail_closed_families=tuple(fail_closed_families),
    )


def plan_commands_for_categories(categories: Iterable[str]) -> list[str]:
    selected_categories: list[str] = []
    for category in categories:
        if category not in selected_categories:
            selected_categories.append(category)

    planned_commands: list[str] = []
    for spec in _CATEGORY_SPECS:
        if spec.category_id not in selected_categories:
            continue
        for command in spec.commands:
            if command not in planned_commands:
                planned_commands.append(command)
    if GENERIC_PYTHON_REGRESSION_CATEGORY in selected_categories:
        for command in _GENERIC_PYTHON_REGRESSION_COMMANDS:
            if command not in planned_commands:
                planned_commands.append(command)
    return planned_commands


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _planned_pytest_paths(command: str) -> tuple[str, ...]:
    parts = shlex.split(command)
    if not parts:
        return ()
    if parts[:1] == [PYTEST_CLEAN_RUNNER]:
        return tuple(part for part in parts[1:] if part.startswith("tests/"))
    if len(parts) < 3 or parts[:3] != ["uv", "run", "pytest"]:
        return ()
    return tuple(part for part in parts[3:] if part.startswith("tests/"))


def _planned_pytest_path_existence(commands: Sequence[str]) -> list[dict[str, object]]:
    repo_root = _repo_root()
    return [
        {
            "command": command,
            "path": path,
            "exists": (repo_root / path).exists(),
        }
        for command in commands
        for path in _planned_pytest_paths(command)
    ]


def _missing_planned_pytest_paths(categories: Sequence[dict[str, object]]) -> list[dict[str, str]]:
    missing: list[dict[str, str]] = []
    for category in categories:
        for status in category["planned_pytest_path_existence"]:
            if status["exists"] is True:
                continue
            missing.append(
                {
                    "category": str(category["category"]),
                    "command": str(status["command"]),
                    "path": str(status["path"]),
                }
            )
    return missing


def _owner_surface(*, exact_paths: Sequence[str], prefix_paths: Sequence[str]) -> dict[str, object]:
    return {
        "exact_paths": list(exact_paths),
        "prefix_paths": list(prefix_paths),
    }


def _unknown_path_suggestions_for_category(spec: PreflightCategorySpec) -> list[str]:
    suggestions = [
        f"Review unknown docs paths manually. {_UNKNOWN_DOCUMENTATION_SUGGESTION}",
    ]
    if any(path.startswith("tests/") for path in (*spec.exact_paths, *spec.prefix_paths)):
        suggestions.append(
            "Unknown tests/*.py paths route to generic_python_smoke_surface unless added to an owner surface."
        )
    if any(path.startswith("src/med_autoscience/") for path in (*spec.exact_paths, *spec.prefix_paths)):
        suggestions.append(
            "Unknown src/med_autoscience/*.py paths route to generic_python_smoke_surface unless added to an owner surface."
        )
    return suggestions


def _contract_hygiene(categories: Sequence[dict[str, object]]) -> dict[str, object]:
    missing_pytest_paths = _missing_planned_pytest_paths(categories)
    return {
        "planned_pytest_paths_exist": not missing_pytest_paths,
        "missing_planned_pytest_paths": missing_pytest_paths,
        "unknown_python_and_test_paths": {
            "category": GENERIC_PYTHON_REGRESSION_CATEGORY,
            "planned_commands": list(_GENERIC_PYTHON_REGRESSION_COMMANDS),
            "fail_policy": _GENERIC_PYTHON_FAIL_POLICY,
        },
        "unknown_documentation_paths": {
            "planned_commands": [],
            "fail_policy": "review-only",
            "suggestion": _UNKNOWN_DOCUMENTATION_SUGGESTION,
        },
        "unknown_workflow_config_paths": {
            "planned_commands": [],
            "fail_policy": "fail-closed",
            "suggestion": _UNKNOWN_WORKFLOW_CONFIG_SUGGESTION,
        },
    }


def build_preflight_contract_report() -> dict[str, object]:
    categories: list[dict[str, object]] = []
    for spec in _CATEGORY_SPECS:
        commands = list(spec.commands)
        owner_surface = _owner_surface(exact_paths=spec.exact_paths, prefix_paths=spec.prefix_paths)
        pytest_path_existence = _planned_pytest_path_existence(commands)
        unknown_path_suggestions = _unknown_path_suggestions_for_category(spec)
        categories.append(
            {
                "category": spec.category_id,
                "category_id": spec.category_id,
                "exact_paths": list(spec.exact_paths),
                "prefix_paths": list(spec.prefix_paths),
                "owner_surface": owner_surface,
                "fail_policy": _MATCHED_CATEGORY_FAIL_POLICY,
                "commands": commands,
                "planned_commands": commands,
                "pytest_path_existence": pytest_path_existence,
                "planned_pytest_path_existence": pytest_path_existence,
                "unknown_path_suggestion": unknown_path_suggestions[0],
                "unknown_path_suggestions": unknown_path_suggestions,
            }
        )
    generic_commands = list(_GENERIC_PYTHON_REGRESSION_COMMANDS)
    generic_unknown_path_suggestions = [
        "Unknown src/med_autoscience/*.py paths route to generic_python_smoke_surface and run make test-smoke.",
        "Unknown tests/*.py paths route to generic_python_smoke_surface and run make test-smoke.",
        f"Unknown docs paths are review-only. {_UNKNOWN_DOCUMENTATION_SUGGESTION}",
        f"Unknown workflow/config paths remain fail-closed. {_UNKNOWN_WORKFLOW_CONFIG_SUGGESTION}",
    ]
    generic_pytest_path_existence = _planned_pytest_path_existence(generic_commands)
    categories.append(
        {
            "category": GENERIC_PYTHON_REGRESSION_CATEGORY,
            "category_id": GENERIC_PYTHON_REGRESSION_CATEGORY,
            "exact_paths": [],
            "prefix_paths": list(_GENERIC_PYTHON_PREFIXES),
            "owner_surface": _owner_surface(exact_paths=(), prefix_paths=_GENERIC_PYTHON_PREFIXES),
            "fail_policy": _GENERIC_PYTHON_FAIL_POLICY,
            "commands": generic_commands,
            "planned_commands": generic_commands,
            "pytest_path_existence": generic_pytest_path_existence,
            "planned_pytest_path_existence": generic_pytest_path_existence,
            "unknown_path_suggestion": generic_unknown_path_suggestions[0],
            "unknown_path_suggestions": generic_unknown_path_suggestions,
        }
    )
    documentation_commands: list[str] = []
    categories.append(
        {
            "category": DOCUMENTATION_REVIEW_CATEGORY,
            "category_id": DOCUMENTATION_REVIEW_CATEGORY,
            "exact_paths": [],
            "prefix_paths": list(_DOC_ONLY_PREFIX_PATHS),
            "root_file_patterns": list(_DOC_ONLY_ROOT_FILE_PATTERNS),
            "owner_surface": _owner_surface(
                exact_paths=(),
                prefix_paths=_DOC_ONLY_PREFIX_PATHS,
            ),
            "fail_policy": "documentation_review_only_no_pytest",
            "commands": documentation_commands,
            "planned_commands": documentation_commands,
            "pytest_path_existence": [],
            "planned_pytest_path_existence": [],
            "unknown_path_suggestion": _UNKNOWN_DOCUMENTATION_SUGGESTION,
            "unknown_path_suggestions": [_UNKNOWN_DOCUMENTATION_SUGGESTION],
        }
    )
    return {
        "surface_kind": "preflight_contract_report",
        "unknown_path_policy": dict(_UNKNOWN_PATH_POLICY),
        "contract_hygiene": _contract_hygiene(categories),
        "categories": categories,
        "fail_closed_families": [
            {
                "family_id": family.family_id,
                "exact_paths": list(family.exact_paths),
                "prefix_paths": list(family.prefix_paths),
            }
            for family in _DEFAULT_COVERAGE_PATH_FAMILIES
        ],
    }
